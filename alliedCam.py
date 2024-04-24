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

try :
    from PyQt6.QtWidgets import QWidget,QInputDialog,QApplication
    from PyQt6 import QtCore
    from PyQt6.QtCore import pyqtSlot
except ImportError:
    print('error import pyQt6')
    
import time,sys
import numpy as np

try :
    import vmbpy #https://github.com/alliedvision/VmbPy   
    print('VimbaX is used')
    with vmbpy.VmbSystem.get_instance() as vmb:
        cameraIds = vmb.get_all_cameras()
        nbCamera = len(cameraIds)
        print( nbCamera,"Alliedvision Cameras available :")
        for i in range (0,nbCamera):
            print(cameraIds[i])
except :
    print('vimbaX not installed')
    try :
        import vimba as vimba # vimba  ## pip install git+https://github.com/alliedvision/VimbaPython
        print('vimba used')
        with vimba.Vimba.get_instance() as vmb:
            cameraIds = vmb.get_all_cameras()
            nbCamera = len(cameraIds)
            print( nbCamera,"Alliedvision Cameras available :")
        for i in range (0,nbCamera):
            print(cameraIds[i])  
    except:
        print('vimba not installed ')   
        
def getCamID(index):
    a = cameraIds[index].get_id()
    return a

def print_feature(feature):
    try:
        value = feature.get()
    except :
        value = None

    print('/// Feature name   : {}'.format(feature.get_name()))
    print('/// Display name   : {}'.format(feature.get_display_name()))
    print('/// Tooltip        : {}'.format(feature.get_tooltip()))
    print('/// Description    : {}'.format(feature.get_description()))
    print('/// SFNC Namespace : {}'.format(feature.get_sfnc_namespace()))
    print('/// Unit           : {}'.format(feature.get_unit()))
    print('/// Value          : {}\n'.format(str(value)))

def cameraFeatures(nbCam=1):
    camID = getCamID(nbCam)
    with vmb:
       cam=vmb.get_camera_by_id(camID)
       #print(cam)
       with cam:
           for feature in cam.get_all_features():
                    print_feature(feature) 
           modelCam = cam.get_model()
           nameCam = cam.get_name()
           print(modelCam,nameCam)
           time = cam.ExposureTime.get()
           trig = cam.TriggerMode.set('Off')
           print(time,trig)
    
def camAvailable(): 
    nbCamera = len(cameraIds)
    camA = []
    for i in range (0,nbCamera):
        camA.append (cameraIds[i].get_id())
    return camA    
    
class ALLIEDVISION (QWidget):
    
    newData = QtCore.pyqtSignal(object)
    endAcq = QtCore.pyqtSignal(bool)
    signalRunning = QtCore.pyqtSignal(bool)

    def __init__(self,cam='camDefault',**kwds):
        super(ALLIEDVISION,self).__init__()
        
        self.nbcam = cam
        self.itrig = 'off'
        if "conf"  in kwds :
            self.conf=kwds["conf"]
        else :
            self.conf = QtCore.QSettings('confCamera.ini', QtCore.QSettings.Format.IniFormat)
        self.camParameter = dict()
        self.camIsRunning = False
        self.nbShot = 1
        self.items = cameraIds
  
    def openMenuCam(self):
        '''create a message box to choose a camera
        '''
        items=cameraIds
        item, ok = QInputDialog.getItem(self, "Select allied camera","List of avaible camera", items, 0, False,flags=QtCore.Qt.WindowType.WindowStaysOnTopHint)
        
        if ok and item:
            items = list(items)
            index = items.index(item)
            self.camID = getCamID(index)
            with vmb:
                self.cam0 = vmb.get_camera_by_id(self.camID)
            self.isConnected = True
            self.nbcam='camDefault'
            
        if self.isConnected is True:
            self.setCamParameter()
        return self.isConnected
    
    def openFirstCam(self,ID=0):
        with vmb :
            try:
                self.camID = getCamID(ID)
                self.cam0 = vmb.get_camera_by_id(self.camID)
                with self.cam0:
                        self.cam0.get_frame()#DeviceReset.run()
                self.isConnected=True
                self.nbcam='camDefault'
            except:
                self.isConnected=False
                self.ccdName='no camera'
        if self.isConnected is True:
            self.setCamParameter()
        return self.isConnected
    
    def openCamByID(self,camID): 
                
        ''' read cam serial number
        '''
        self.camID=camID
       
        try :
            with vmb:
                self.cam0=vmb.get_camera_by_id(self.camID)
                self.isConnected = True
            
        except:# if id number doesn't work we take the first one
            try:
                with vmb:
                    print('Id not valid open the fisrt camera')
                    self.camID=getCamID(0)
                    self.cam0=vmb.get_camera_by_id(self.camID)
                    # with self.cam0:
                    #     self.cam0.get_frame()
                        #self.cam0.DeviceReset.run()
                        #time.sleep(5)
                    #self.cam0=vmb.get_camera_by_id(self.camID)
                    self.isConnected=True
            except:
                    print('not ccd connected')
                    self.isConnected=False
                    self.ccdName = 'no camera'            
        if self.isConnected is True:
            self.setCamParameter()
            
            
    def setCamParameter(self):
        """
        Set initial parameters
    
        """
        self.camLanguage = dict()
        with vmb:
            with self.cam0:
              self.modelCam = self.cam0.get_name()
              
              print( 'connected @:'  ,self.camID,'model : ',self.modelCam )
              self.cam0.TriggerMode.set('Off')
              self.cam0.TriggerSelector.set('AcquisitionStart')
              self.cam0.TriggerActivation.set('RisingEdge')
#              self.cam0.TriggerSource.set('Software')
              self.cam0.AcquisitionMode.set('SingleFrame')#Continuous
              print('camera tempature',self.cam0.DeviceTemperature.get(),' °C')
            
        ## init cam parameter## different command name depend on camera type 
        if self.modelCam == "GT1290":
            self.camLanguage['exposure'] = 'ExposureTimeAbs'
            self.LineTrigger = 'Line1'#☺str(self.conf.value(self.nbcam+"/LineTrigger")) # line2 for Mako Line 1 for guppy (not tested)
        if self.modelCam == "Manta":
            self.camLanguage['exposure'] = 'ExposureTimeAbs'
            self.LineTrigger = 'Line1'
        if self.modelCam == 'AVT Guppy PRO F031B': 
            self.camLanguage['exposure'] = 'ExposureTime'
            self.LineTrigger = 'InputLines'
        if self.modelCam == 'Allied Vision 1800 U-050m' :
            self.camLanguage['exposure'] = 'ExposureTime'
            self.LineTrigger = 'Line1'
        
        if self.modelCam == 'Allied Vision Mako U-029B' :
            self.camLanguage['exposure'] = 'ExposureTime'
            self.LineTrigger = 'Line1'
        
        if self.modelCam == 'AVT Pike F1600B' :
            self.camLanguage['exposure'] = 'ExposureTime'
            self.LineTrigger = 'InputLines'
            
        with vmb:
            with self.cam0:
                
                self.camParameter["trigger"] = self.cam0.TriggerMode.get()
                if self.modelCam == 'Allied Vision Mako U-029B':
                    pass
                else:
                    self.cam0.ExposureAuto.set('Off')
                    self.cam0.GainAuto.set('Off')
                
                if self.cam0.Height.get() != self.cam0.HeightMax.get():
                    self.cam0.Height.set(self.cam0.HeightMax.get())
               
                if self.cam0.Width.get() != self.cam0.WidthMax.get():
                    self.cam0.Width.set(self.cam0.WidthMax.get())
                
                exp=self.cam0.get_feature_by_name(self.camLanguage['exposure'])
                
                self.camParameter["expMax"] = float(exp.get_range()[1]/1000)
                self.camParameter["expMin"] = float(exp.get_range()[0]/1000)
                
                #if exposure time save in the ini file is not in the range we put the minimum
                if self.camParameter["expMin"] <= float(self.conf.value(self.nbcam+"/shutter")) <= self.camParameter["expMax"]:
                    exp.set(float(self.conf.value(self.nbcam+"/shutter"))*1000)
                else :
                    exp.set(float(self.camParameter["expMin"]))
                
                self.camParameter["exposureTime"] = float(exp.get()/1000)
        
                self.camParameter["gainMax"] = self.cam0.Gain.get_range()[1]
                self.camParameter["gainMin"] = self.cam0.Gain.get_range()[0]
                if self.camParameter["gainMin"] <= int(self.conf.value(self.nbcam+"/gain")) <= self.camParameter["gainMax"]:
                    self.cam0.Gain.set(int(self.conf.value(self.nbcam+"/gain")))
                else:
                    print('gain error: gain set to minimum value')
                    self.cam0.Gain.set(int(self.camParameter["gainMin"]))
                
                self.camParameter["gain"] = self.cam0.Gain.get()
        
        self.threadRunAcq = ThreadRunAcq(self)
        self.threadRunAcq.newDataRun.connect(self.newImageReceived)
        self.threadRunAcq.newStateCam.connect(self.stateCam)
        self.threadOneAcq = ThreadOneAcq(self)
        self.threadOneAcq.newDataRun.connect(self.newImageReceived)#,QtCore.Qt.DirectConnection)
        self.threadOneAcq.newStateCam.connect(self.stateCam)
            
    def setExposure(self,sh):
        ''' 
            set exposure time in ms
        '''
        with vmb:
                with self.cam0:
                    exp=self.cam0.get_feature_by_name(self.camLanguage['exposure'])
                    exp.set(float(sh*1000))
                    # print('exp',exp.get())
                    exp.set(float(sh*1000)) # in gyppy ccd exposure time is microsecond
                    self.camParameter["exposureTime"]=float(exp.get())/1000
                    print("exposure time is set to",self.camParameter["exposureTime"],' micro s')
        
    def setGain(self,g):
        ''' 
            set gain 
        '''
        with vmb:
                with self.cam0:
                    self.cam0.Gain.set(g) 
                    self.camParameter["gain"]=self.cam0.Gain.get()
        print("Gain is set to",self.camParameter["gain"])   
            
    # def softTrigger(self):
    #     '''to have a sofware trigger
    #     '''
    #     print('trig soft')
    #     self.cam0.feature('TriggerSource').value='Software'
    #     self.cam0.run_feature_command('TriggerSoftware') 

    def setTrigger(self,trig='off'):
        '''
            set trigger mode on/off
        '''
        with vmb:
            with self.cam0:
                if trig == 'on':
                    self.cam0.TriggerMode.set('On')
                    self.cam0.TriggerSource.set(self.LineTrigger)
                    self.itrig = 'on'
                else:
                    # self.cam0.TriggerSource.set('Software')
                    # sofTrig=self.cam0.get_feature_by_name('TriggerSoftware')
                    # sofTrig.run()
                    self.cam0.TriggerMode.set('Off')
                    self.itrig = 'off'
        
                self.camParameter["trigger"] = self.cam0.TriggerMode.get()
        
    def startAcq(self):
        self.camIsRunning = True
        self.threadRunAcq.newRun() # to set stopRunAcq=False
        self.threadRunAcq.start()
    
    def startOneAcq(self,nbShot):
        self.nbShot = nbShot 
        self.camIsRunning = True
        self.threadOneAcq.newRun() # to set stopRunAcq=False
        self.threadOneAcq.start()
        
    def stopAcq(self):
        self.threadRunAcq.stopThreadRunAcq()
        self.threadOneAcq.stopThreadOneAcq()
        self.camIsRunning=False  
            
    def newImageReceived(self,data):
        self.data = data
        self.newData.emit(self.data)
        
    def stateCam(self,state):
        self.camIsRunning = state
        self.signalRunning.emit(state)

    def closeCamera(self):
        self.stopAcq()
        with vmb :
            try:
                with self.cam0:
                        self.cam0.AcquisitionStop.run()
                        #self.cam0.DeviceReset.run()
            except:pass

    def endAcquisition(self):
        self.endAcq.emit(True)

class ThreadRunAcq(QtCore.QThread):
    
    '''Second thread for controling continus acquisition independtly
    '''
    newDataRun = QtCore.pyqtSignal(object)
    newStateCam = QtCore.pyqtSignal(bool)
    def __init__(self, parent):
        
        super(ThreadRunAcq,self).__init__(parent)
        self.parent = parent
        self.cam0 = self.parent.cam0
        self.stopRunAcq = False
        self.itrig = parent.itrig
        self.LineTrigger = parent.LineTrigger
        
    def newRun(self):
        self.stopRunAcq = False
        
    def frame_handler(self,cam, frame):
        cam.queue_frame(frame)

        
    @pyqtSlot()
    def run(self):
        self.newStateCam.emit(True)
        with vmb:
            with self.parent.cam0:
                while self.stopRunAcq is not True :
                    try: 
                        self.newStateCam.emit(True)
                        frame = self.parent.cam0.get_frame(timeout_ms=10000)#00000000
                        data = (frame.as_numpy_ndarray())
                        data = data[:,:,0]
                        data = np.rot90(data,3)
                        #time.sleep(0.01)
                        if str(frame.get_status()) == "FrameStatus.Complete" : #np.max(data)>0 or 
                            self.newDataRun.emit(data)
                            self.newStateCam.emit(False) #cam is not reading
                    except:
                        pass
                    
                if self.stopRunAcq ==True :
                    pass
                    
    def stopThreadRunAcq(self):
        
        #self.cam0.send_trigger()
        self.stopRunAcq=True


class ThreadOneAcq(QtCore.QThread):
    
    '''Second thread for controling one or more  acquisition independtly
    '''
    newDataRun = QtCore.pyqtSignal(object)
    newStateCam = QtCore.pyqtSignal(bool)
    
    def __init__(self, parent):
        
        super(ThreadOneAcq,self).__init__(parent)
        self.parent = parent
        self.cam0 = self.parent.cam0
        self.stopRunAcq = False
        self.itrig = parent.itrig
        self.LineTrigger = parent.LineTrigger
        
    def wait(self,seconds):
        time_end = time.time()+seconds
        while time.time()<time_end:
            QApplication.processEvents()

    def newRun(self):
        self.stopRunAcq = False
     
    def run(self):
        self.newStateCam.emit(True)
        with vmb:
            with self.parent.cam0:
                for i in range (self.parent.nbShot):
                    if self.stopRunAcq is not True :
                        
                        try :    
                            frame = self.parent.cam0.get_frame(timeout_ms=3000)
                            data = (frame.as_numpy_ndarray())
                            data = data[:,:,0]
                            data = np.rot90(data,3)
                            if i<self.parent.nbShot-1:
                                self.newStateCam.emit(True)
                                time.sleep(0.01)
                            else:
                                self.newStateCam.emit(False)
                                
                            if str(frame.get_status()) == "FrameStatus.Complete": #np.max(data)>0 o  
                                self.newDataRun.emit(data)
                    
                        except:
                            pass
                    else: 
                        break
                self.newStateCam.emit(False)
        
    def stopThreadOneAcq(self):
        self.stopRunAcq=True


if __name__ == "__main__":       
    #appli = QApplication(sys.argv) 
    e = ALLIEDVISION(cam=None)
    #appli.exec_()          