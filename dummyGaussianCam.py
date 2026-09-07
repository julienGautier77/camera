#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 10:23:01 2020
Adapted : dummy camera générant une tache gaussienne 2D aléatoire

@author: Julien Gautier (LOA)

Caméra factice qui génère, à chaque acquisition, une image contenant une
tache gaussienne 2D dont la position, l'amplitude, la largeur (sigma_x,
sigma_y) et l'orientation (theta) varient aléatoirement d'une image à
l'autre (simulation de fluctuations de pointé). Un léger bruit de fond est
ajouté pour se rapprocher d'une image caméra réelle.

Interface strictement identique à dummyCam.py (DUMMYCAM, ThreadRunAcq,
ThreadOneAcq) : remplacement direct possible pour tester winMeas/visu avec
un vrai signal (tache) plutôt que du bruit pur.

camAvailable:
    return list of all camera

getCamID(index)
    return the ID of the camera
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
    print(nbCamera, "dummy Gaussian Cameras available :")
    for i in range(0, nbCamera):
        print(cameraIds[i])
except Exception as e:
    print(f'error loading dummy gaussian camera  {e}')


# Taille de l'image générée (mêmes dimensions que dummyCam.py)
IMG_SHAPE = (2048, 1024)  # (nb lignes, nb colonnes)


def getCamID(index):
    a = 1
    return a


def print_feature(feature):
    pass


def cameraFeatures(nbCam=1):
    pass


def camAvailable():
    return [1]


def twoD_Gaussian(x, y, amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
    xo = float(xo)
    yo = float(yo)
    a = ((np.cos(theta)**2)/(2*sigma_x**2) +
         (np.sin(theta)**2)/(2*sigma_y**2))
    b = (-(np.sin(2*theta))/(4*sigma_x**2) +
         (np.sin(2*theta))/(4*sigma_y**2))
    c = ((np.sin(theta)**2)/(2*sigma_x**2) +
         (np.cos(theta)**2)/(2*sigma_y**2))
    gauss = (offset + amplitude*np.exp(- (a*((x-xo)**2) + 2*b*(x-xo)*(y-yo) +
                                          c*((y-yo)**2))))
    return gauss


def generate_gaussian_frame(shape=IMG_SHAPE, margin_factor=3, patch_sigma=5):
    """
    Génère une image (uint8) contenant une tache gaussienne 2D avec des
    paramètres tirés aléatoirement (position, amplitude, largeur,
    orientation), sur un fond légèrement bruité.

    Pour rester rapide, le calcul de la gaussienne (cos/sin/exp) n'est
    fait que sur un petit patch local autour du centre (au-delà de
    quelques sigma, la contribution de la gaussienne est négligeable),
    au lieu de toute l'image ; le bruit de fond est généré avec
    np.random.randint (rapide), comme dans dummyCam.py.
    """
    ny, nx = shape

    # Largeur de la tache (pixels), tirée aléatoirement
    sigma_x = np.random.uniform(15, 60)
    sigma_y = np.random.uniform(15, 60)

    # Position aléatoire, avec une marge pour garder la tache bien visible
    # (évite qu'elle soit systématiquement coupée en bord d'image)
    margin_x = min(margin_factor * sigma_x, nx / 2 - 1)
    margin_y = min(margin_factor * sigma_y, ny / 2 - 1)
    xo = np.random.uniform(margin_x, nx - margin_x)
    yo = np.random.uniform(margin_y, ny - margin_y)

    theta = np.random.uniform(0, np.pi)
    amplitude = np.random.uniform(120, 200)   # reste sous 255 avec le fond+bruit
    offset = np.random.uniform(5, 15)          # niveau de fond

    # Fond bruité sur toute l'image (rapide, comme dans dummyCam.py)
    offsetInt = int(offset)
    frame = np.random.randint(offsetInt, offsetInt + 6, shape).astype(np.int16)

    # Patch local autour du centre : au-delà de patch_sigma*sigma, la
    # gaussienne est quasi nulle, inutile de la calculer sur toute l'image
    half = int(patch_sigma * max(sigma_x, sigma_y))
    x0 = max(0, int(xo - half))
    x1 = min(nx, int(xo + half))
    y0 = max(0, int(yo - half))
    y1 = min(ny, int(yo + half))

    yy, xx = np.mgrid[y0:y1, x0:x1]
    patch = twoD_Gaussian(xx, yy, amplitude, xo, yo, sigma_x, sigma_y, theta, 0)
    frame[y0:y1, x0:x1] += patch.astype(np.int16)

    frame = np.clip(frame, 0, 255).astype(np.uint8)
    return frame


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
        # On lit le temps d'exposition sauvegardé dans le fichier de config
        # (comme le font les vraies caméras), avec un repli à 100 ms si la
        # clé n'existe pas encore (première utilisation).
        self.camParameter["exposureTime"] = float(self.conf.value(str(self.nbcam) + "/shutter", 100))
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

        self.modelCam = "dummy gaussian camera"
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
        self.stopRunAcq = False

    def newRun(self):
        self.stopRunAcq = False

    @pyqtSlot()
    def run(self):

        self.newStateCam.emit(True)

        while self.stopRunAcq is not True:
            try:
                self.newStateCam.emit(True)
                data = generate_gaussian_frame()
                time.sleep(self.parent.exp/1000)
                self.newDataRun.emit(data)
                self.newStateCam.emit(False)  # cam is not reading
            except Exception as e:
                print(f'error during acquisition {e}')
                pass

        if self.stopRunAcq is True:
            pass

    def stopThreadRunAcq(self):
        self.stopRunAcq = True


class ThreadOneAcq(QtCore.QThread):
    '''Second thread for controling one or more  acquisition independtly
    '''
    newDataRun = QtCore.pyqtSignal(object)
    newStateCam = QtCore.pyqtSignal(bool)

    def __init__(self, parent):

        super(ThreadOneAcq, self).__init__(parent)
        self.parent = parent
        self.stopRunAcq = False

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
                    data = generate_gaussian_frame()
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
