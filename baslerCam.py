# -*- coding: utf-8 -*-
'''
Created on Mon Mar 30 10:23:01 2020
BASLER class : class to control basler camera
        
        Parameters
        ----------
        cam : TYPE, optional
            DESCRIPTION. 
                cam='None' : Choose a camera in a list
                cam='camDefault : the first camera is chossen
                cam='cam1'"' : Take the camId in the confCamera.ini file
            The default is 'camDefault'.
        conf : TYPE, optional
            DESCRIPTION.a QtCore.QSettings  objet : 
                conf=QtCore.QSettings('file.ini', QtCore.QSettings.IniFormat)
                where file is the ini file where camera paremetesr are saved
            The default is None.
        

@author: Julien Gautier (LOA)
'''

from PyQt5.QtWidgets import QApplication,QWidget
from PyQt5.QtWidgets import QInputDialog
from pyqtgraph.Qt import QtCore
import sys,time
import numpy as np
from PyQt5.QtCore import Qt,QMutex
try :   
    from pypylon import pylon # pip install pypylon: https://github.com/basler/pypylon

    tlFactory = pylon.TlFactory.GetInstance()
    devices = tlFactory.EnumerateDevices()
    cameras = pylon.InstantCameraArray(min(len(devices), 12))
except:
    print('pyplon is not installed')

def camAvailable() :
    '''list of camera avialable
    '''
    items=()
    for i, cam in enumerate(cameras):
        cam.Attach(tlFactory.CreateDevice(devices[i]))
        items=items+(str(cam.GetDeviceInfo().GetFriendlyName()),)
    return items
    
def getCamID (index):
    '''get serial number
    '''
    id=cameras[index].GetDeviceInfo().GetSerialNumber()
    return(id)
    

class BASLER (QtCore.QThread):
    
    newData=QtCore.pyqtSignal(object) # signal emited when receive image 
    
    def __init__(self,cam='camDefault',conf=None,**kwds):
        
        super(BASLER,self).__init__()
        
        self.nbcam=cam
        self.itrig='off'
        
        if conf==None:
            self.conf=QtCore.QSettings('confCamera.ini', QtCore.QSettings.IniFormat)
        else:
            self.conf=conf
        if "multi"in kwds :
            self.multi=kwds["multi"]
        else:
            self.multi=False   
            
        self.camParameter=dict()
        self.camIsRunnig=False
        self.nbShot=1
        self.isConnected=False
        
    
   
    def openMenuCam(self):
        '''create a message box to choose a camera
        '''
        
        items=()
        for i, cam in enumerate(cameras):
            cam.Attach(tlFactory.CreateDevice(devices[i]))
            items=items+(str(cam.GetDeviceInfo().GetFriendlyName()),)
           
        item, ok = QInputDialog.getItem(self, "Select Basler camera","List of avaible camera", items, 0, False,flags=QtCore.Qt.WindowStaysOnTopHint)
            
        if ok and item:
            items=list(items)
            index = items.index(item)
            self.id=cameras[index].GetDeviceInfo().GetSerialNumber()
            for i in devices:
                if i.GetSerialNumber()==self.id:
                    camConnected=i
            self.cam0= pylon.InstantCamera(tlFactory.CreateDevice(camConnected))
            self.ccdName=self.cam0.GetDeviceInfo().GetFriendlyName()
            self.isConnected=True
            self.nbcam='camDefault'
        else:
            self.isConnected=False
            self.nbcam='camDefault'
        
        if self.isConnected==True:
            self.setCamParameter()   
             
            
    def openFirstCam(self):
        '''we take the fisrt one
        '''
        
        self.nbcam='camDefault' #
        
        try:
            self.cam0=pylon.InstantCamera(tlFactory.CreateFirstDevice())
            self.ccdName='CamDefault'
            self.isConnected=True
        except:
            self.isConnected=False
            self.ccdName='no camera'
        
        if self.isConnected==True:
            self.setCamParameter()       
            
    def openCamByID(self,camID=0): 
        '''connect to a serial number
        '''
        
        # if
        # self.camID=self.conf.value(self.nbcam+"/camID") ## read cam serial number
        # self.ccdName=self.conf.value(self.nbcam+"/nameCDD")
        self.camID=camID
        
        for i in devices:
            if i.GetSerialNumber()==self.camID:
                camConnected=i
                self.cam0= pylon.InstantCamera(tlFactory.CreateDevice(camConnected))
                self.isConnected=True
            else: 
                self.isConnected=False
                
        if self.isConnected==True:
            self.setCamParameter()          
        
            
            
    def setCamParameter(self): 
        """Set initial parameters
        """
               
        self.cam0.Open()
        self.camID=self.cam0.GetDeviceInfo().GetSerialNumber()
        print(' connected@IP: ',self.cam0.GetDeviceInfo().GetIpAddress() )
                
        
        self.LineTrigger=str('None') # for 
        
        self.cam0.TriggerMode.SetValue('Off')
        self.cam0.TriggerActivation.SetValue('RisingEdge')

        self.cam0.TriggerSource.SetValue('Line1')
        self.cam0.ExposureAuto.SetValue('Off')
        
        
        self.cam0.GainAuto.SetValue('Off')
        
        self.cam0.Width=self.cam0.Width.Max  # set camera width at maximum
        self.cam0.Height=self.cam0.Height.Max
        
        
        self.camParameter["expMax"]=float(self.cam0.ExposureTimeAbs.GetMax()/1000)
        self.camParameter["expMin"]=float(self.cam0.ExposureTimeAbs.GetMin()/1000)
        
        self.camParameter["gainMax"]=self.cam0.GainRaw.GetMax()
        self.camParameter["gainMin"]=self.cam0.GainRaw.GetMin()
        
        #if exposure time save in the ini file is not in the range we put the minimum
        if self.camParameter["expMin"] <=float(self.conf.value(self.nbcam+"/shutter"))<=self.camParameter["expMax"]:
            self.cam0.ExposureTimeAbs.SetValue(float(self.conf.value(self.nbcam+"/shutter"))*1000)
        else:
            self.cam0.ExposureTimeAbs.SetValue(self.camParameter["expMin"]*1000)
    
        self.camParameter["exposureTime"]=int(self.cam0.ExposureTimeAbs.GetValue())/1000
        
        
        if self.camParameter["gainMin"] <=int(self.conf.value(self.nbcam+"/gain"))<=self.camParameter["gainMax"]:
            self.cam0.GainRaw.SetValue(int(self.conf.value(self.nbcam+"/gain")))
        else:
            print('gain error: gain set to minimum value')
            self.cam0.GainRaw.SetValue(int(self.camParameter["gainMin"]))
        
        self.camParameter["gain"]=self.cam0.GainRaw.GetValue()
        
        
        self.camParameter["trigger"]=self.cam0.TriggerMode.GetValue()
        
        self.threadRunAcq=ThreadRunAcq(self)
        
        
        if self.multi==True:
            self.threadRunAcq.newDataRun.connect(self.newImageReceived,QtCore.Qt.DirectConnection)
        else:
            self.threadRunAcq.newDataRun.connect(self.newImageReceived)
           
            
        self.threadOneAcq=ThreadOneAcq(self)
        self.threadOneAcq.newDataRun.connect(self.newImageReceived)
        self.threadOneAcq.newStateCam.connect(self.stateCam)
            
            
    def setExposure(self,sh):
        ''' set exposure time in ms
        '''
        
        self.cam0.ExposureTimeAbs.SetValue(float (sh*1000))# in balser ccd exposure time is microsecond
        self.camParameter["exposureTime"]=float(self.cam0.ExposureTimeAbs.GetValue())/1000
        print("exposure time is set to",float(self.cam0.ExposureTimeAbs.GetValue()),' micro s')
        
    def setGain(self,g):
        ''' set gain 
        '''
        
        self.cam0.GainRaw.SetValue(int(g)) # 
        print("Gain is set to",self.cam0.GainRaw.GetValue())   
        self.camParameter["gain"]=self.cam0.GainRaw.GetValue()
    
    def softTrigger(self):
        '''to have a sofware trigger
        '''
        print('trig soft')
        self.cam0.ExecuteSoftwareTrigger()

    def setTrigger(self,trig='off'):
        '''set trigger mode on/off
        '''
        
        if trig=='on':
            self.cam0.TriggerMode.SetValue('On')
            self.itrig='on'
        else:
            self.cam0.TriggerMode.SetValue('Off')
            
            self.itrig='off'
        
        self.camParameter["trigger"]=self.cam0.TriggerMode.GetValue()
        
    def startAcq(self):
        '''Acquistion in live mode
        '''
        
        self.camIsRunnig=True
        self.threadRunAcq.newRun() # to set stopRunAcq=False
        self.threadRunAcq.start()
    
    def startOneAcq(self,nbShot):
        '''Acquisition of a number (nbShot) of image 
        '''
        
        self.nbShot=nbShot 
        self.camIsRunnig=True
        self.threadOneAcq.newRun() # to set stopRunAcq=False
        self.threadOneAcq.start()
        
    def stopAcq(self):
        
        self.threadRunAcq.stopThreadRunAcq()
        # if self.threadRunAcq.isRunning():
        #     self.threadRunAcq.terminate()
        self.threadOneAcq.stopThreadOneAcq()
        self.camIsRunnig=False  
            
    def newImageReceived(self,data):
        '''Emit the data when receive a data from the thread threadRunAcq threadOneAcq
        '''
        
        self.data=data
        self.newData.emit(self.data)
    
        
    def stateCam(self,state):
        '''state of camera : True is running False : is stopped
        '''
        
        self.camIsRunnig=state
    
    def closeCamera(self):
        print('close basler')
        self.cam0.Close()
        
        
        
        
class ThreadRunAcq(QtCore.QThread):
    '''Second thread for controling continus acquisition independtly
    '''
    newDataRun=QtCore.Signal(object)
    
    def __init__(self, parent):
        
        super(ThreadRunAcq,self).__init__(parent)
        self.parent=parent
        self.cam0 = parent.cam0
        self.stopRunAcq=False
        self.itrig= parent.itrig
        self.LineTrigger=parent.LineTrigger
        self.converter=pylon.ImageFormatConverter()
        
    def newRun(self):
        self.stopRunAcq=False
        
    def run(self):
        self.mutex=QMutex()
        while self.stopRunAcq is not True :
            # self.mutex.lock()
            try :
                data=self.cam0.GrabOne(20000000)
            except :
                self.cam0.StopGrabbing()
                data=self.cam0.GrabOne(20000000)
            data=self.converter.Convert(data)
            data = data.GetArray()#, dtype=np.double)
            data.squeeze()
            
            self.data=np.rot90(data,1)
            
            if np.max(self.data)>0: # send data if not zero 
                
                if self.stopRunAcq==True:
                    break
                else :
                    self.newDataRun.emit(self.data)
                    # print(self.cam0.DeviceTemperature.GetValue())
            # self.mutex.unlock()
    def stopThreadRunAcq(self):
        
        self.stopRunAcq=True
        
        try :
            self.cam0.ExecuteSoftwareTrigger()
        except :
            pass
        
    def closeCamera(self):
        self.cam0.Close()
        
        
        
class ThreadOneAcq(QtCore.QThread):
    '''Second thread for controling one or anumber of  acquisition independtly
    '''
    newDataRun=QtCore.Signal(object)
    newStateCam=QtCore.Signal(bool) # signal to emit the state (running or not) of the camera
    
    def __init__(self, parent):
        
        super(ThreadOneAcq,self).__init__()
        self.parent=parent
        self.cam0 = parent.cam0
        self.stopRunAcq=False
        self.itrig= parent.itrig
        self.LineTrigger=parent.LineTrigger
        self.converter=pylon.ImageFormatConverter()
   
    
    def newRun(self):
        self.stopRunAcq=False
        
    def run(self):
        self.newStateCam.emit(True)
        
        for i in range (self.parent.nbShot):
            if self.stopRunAcq is not True :
                data=self.cam0.GrabOne(200000)
                data=self.converter.Convert(data)
                data = data.GetArray()#, dtype=np.double)
                data.squeeze()
            
                self.data=np.rot90(data,1)
                
                if i<self.parent.nbShot-1:
                    self.newStateCam.emit(True)
                else:
                    self.newStateCam.emit(False)
                    time.sleep(0.1)
                    
                if np.max(self.data)>0 : 
                    self.newDataRun.emit(self.data)
                    
            else:
                break
            
        self.newStateCam.emit(False)
       
    def stopThreadOneAcq(self):
        
        self.stopRunAcq=True
        
        try :
            self.cam0.ExecuteSoftwareTrigger()
        except :
            pass      
        
    
        
    
        
if __name__ == "__main__":       
    
    
    e = BASLER(cam='cam1')
                 
        
        
        
        