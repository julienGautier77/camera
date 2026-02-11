#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 10:23:01 2020

@author: Julien Gautier (LOA)

camAvailable:

    return list of all camera

getCamID(index)

    return the ID of the camera

class ALLIEDVISION :

    Parameters
        ----------
        cam : TYPE, optional
            DESCRIPTION.
            None : Choose a camera in a list
            camDefault : the first camera is chossen
            "cam1" : Take the camId in the confCamera.ini file
            The default is 'camDefault'.
        conf : TYPE, optional
            DESCRIPTION.a QtCore.QSettings  objet :
            QtCore.QSettings('file.ini', QtCore.QSettings.IniFormat)
            where file is the ini file where camera parameters are saved
            usefull to set init parameters (expTime and gain)
            The default is None.
"""

try:
    from PyQt6.QtWidgets import QWidget, QApplication
    from PyQt6 import QtCore
    from PyQt6.QtCore import pyqtSlot
except ImportError:
    print('error import pyQt6')

import time
import sys
import numpy as np

try:
    cameraIds = [1]
    nbCamera = len(cameraIds)
    print(nbCamera, "dummy Cameras available :")
    for i in range(0, nbCamera):
        print(cameraIds[i])
except Exception as e:
    print(f'error loading dummy camera  {e}')


def getCamID(index):
    a = 1
    return a


def print_feature(feature):
    pass


def cameraFeatures(nbCam=1):
    pass


def camAvailable():
    return [1]


class DUMMYCAM(QWidget):
    newData = QtCore.pyqtSignal(object)
    endAcq = QtCore.pyqtSignal(bool)
    signalRunning = QtCore.pyqtSignal(bool)

    def __init__(self, cam='camDefault', **kwds):
        super(DUMMYCAM, self).__init__()

        self.nbcam = cam
        self.itrig = 'off'
        if "conf" in kwds:
            self.conf = kwds["conf"]
        else:
            self.conf = QtCore.QSettings('confCamera.ini', QtCore.QSettings.Format.IniFormat)
        self.camParameter = dict()
        self.camParameter["exposureTime"] = 1
        self.camParameter["expMin"] = 0
        self.camParameter["expMax"] = 1000
        self.camParameter["gainMin"] = 0
        self.camParameter["gainMax"] = 10
        self.camParameter["gain"] = 0
        self.camIsRunning = False
        self.nbShot = 1
        self.items = cameraIds

    def openMenuCam(self):
        '''create a message box to choose a camera
        '''
        pass

    def openFirstCam(self, ID=0):
        self.get_frame()  # DeviceReset.run()
        self.isConnected = True
        self.nbcam = 'camDefault'

    def openCamByID(self, camID):

        ''' read cam serial number
        '''
        self.camID = camID
        self.isConnected = True
        self.setCamParameter()

    def setCamParameter(self):
        """
        Set initial parameters

        """
        self.camLanguage = dict()

        self.modelCam = "dummy camera"
        print(f'Max height {self.height}')
        print('connected @:', self.camID, 'model : ', self.modelCam)
        print("Done")

        # init cam parameter## different command name depend on camera type
        print(f'model {self.modelCam}')
        self.exp = self.camParameter["exposureTime"]
        self.threadRunAcq = ThreadRunAcq(self)
        self.threadRunAcq.newDataRun.connect(self.newImageReceived)
        self.threadRunAcq.newStateCam.connect(self.stateCam)
        self.threadOneAcq = ThreadOneAcq(self)
        self.threadOneAcq.newDataRun.connect(self.newImageReceived)  # ,QtCore.Qt.DirectConnection)
        self.threadOneAcq.newStateCam.connect(self.stateCam)

    def setExposure(self, sh):
        '''
            set exposure time in ms

        '''
        self.exp = sh
        pass

    def setGain(self, g):
        '''
            set gain
        '''
        pass

    def setTrigger(self, trig='off'):
        '''
            set trigger mode on/off
        '''
        pass

    def startAcq(self):
        self.camIsRunning = True
        self.threadRunAcq.newRun()  # to set stopRunAcq=False
        self.threadRunAcq.start()

    def startOneAcq(self, nbShot):
        self.nbShot = nbShot
        self.camIsRunning = True
        self.threadOneAcq.newRun()  # to set stopRunAcq=False
        self.threadOneAcq.start()

    def stopAcq(self):
        self.threadRunAcq.stopThreadRunAcq()
        self.threadOneAcq.stopThreadOneAcq()
        self.camIsRunning = False

    def newImageReceived(self, data):
        self.data = data
        self.newData.emit(self.data)

    def stateCam(self, state):
        self.camIsRunning = state
        self.signalRunning.emit(state)

    def closeCamera(self):
        self.stopAcq()

    def endAcquisition(self):
        self.endAcq.emit(True)


class ThreadRunAcq(QtCore.QThread):
    '''Second thread for controling continus acquisition independtly
    '''
    newDataRun = QtCore.pyqtSignal(object)
    newStateCam = QtCore.pyqtSignal(bool)

    def __init__(self, parent):

        super(ThreadRunAcq, self).__init__(parent)
        self.parent = parent
        #self.cam0 = self.parent.cam0
        self.stopRunAcq = False
        #self.itrig = parent.itrig
        #self.LineTrigger = parent.LineTrigger

    def newRun(self):
        self.stopRunAcq = False

#    def frame_handler(self, cam, frame):
#        cam.queue_frame(frame)

    @pyqtSlot()
    def run(self):

        self.newStateCam.emit(True)

        while self.stopRunAcq is not True:
            try:
                self.newStateCam.emit(True)
                data = np.random.randint(0, 255, (2048, 1024))
                time.sleep(self.parent.exp/1000)
                self.newDataRun.emit(data)
                self.newStateCam.emit(False)  # cam is not reading
            except Exception as e:
                print(f'error during acquisition {e}')
                pass

        if self.stopRunAcq is True:
            pass

    def stopThreadRunAcq(self):
        # self.cam0.send_trigger()
        self.stopRunAcq = True


class ThreadOneAcq(QtCore.QThread):
    '''Second thread for controling one or more  acquisition independtly
    '''
    newDataRun = QtCore.pyqtSignal(object)
    newStateCam = QtCore.pyqtSignal(bool)

    def __init__(self, parent):

        super(ThreadOneAcq, self).__init__(parent)
        self.parent = parent
#        self.cam0 = self.parent.cam0
        self.stopRunAcq = False
#       self.itrig = parent.itrig
#        self.LineTrigger = parent.LineTrigger

    def wait(self, seconds):
        time_end = time.time() + seconds
        while time.time() < time_end:
            QApplication.processEvents()

    def newRun(self):
        self.stopRunAcq = False

    def run(self):
        self.newStateCam.emit(True)

        for i in range(100):
            if self.stopRunAcq is not True:

                try:
                    data = np.random.randint(0, 255, (2048, 1024))
                    if i < self.parent.nbShot - 1:
                        self.newStateCam.emit(True)
                        time.sleep(0.01)
                    else:
                        self.newStateCam.emit(False)
                    self.newDataRun.emit(data)

                except Exception as e:
                    print(f'error during acquisition {e}')
                    pass
            else:
                break
        self.newStateCam.emit(False)

    def stopThreadOneAcq(self):
        self.stopRunAcq = True


if __name__ == "__main__":
    # appli = QApplication(sys.argv)
    e = DUMMYCAM(cam=None)
    # appli.exec_()