# -*- coding: utf-8 -*-
'''
Created on Mon Mar 30 10:23:01 2020
pixelink class : an easer class to control basler camera
        
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
try :
    from PyQt6.QtWidgets import QWidget,QInputDialog,QApplication
    from PyQt6 import QtCore
except ImportError:
    print('import error PyQt6')
import sys,time
import numpy as np

try :   
    import pixelinkWrapper as pixelink # pip install pixelinkWrapper: https://github.com/pixelink-support/pixelinkPythonWrapper
    from pyPixelink import PIXELINK_CAM
    cameras=pixelink.PxLApi.getNumberCameras()
    cameras=cameras[1]
except:
    print('pixelinkWrapper is not installed')

def camAvailable() :
    '''list of camera avialable
    '''
    items=()
    for i ,  cam in enumerate(cameras):
        items=items+(str(cameras[i].CameraSerialNum),)
    print(items)
    return items
    
def getCamID (index=0):
    '''get serial number
    '''
    idnb=cameras[index].CameraSerialNum
    return(idnb)
    

class PIXELINK (QtCore.QThread):
    
    newData=QtCore.pyqtSignal(object) # signal emited when receive image 
    
    def __init__(self,cam='camDefault',**kwds):
        
        super(PIXELINK,self).__init__()
        
        self.nbcam=cam
        self.itrig='off'
        
        if "conf"  in kwds :
            self.conf=kwds["conf"]
        else :
            self.conf=QtCore.QSettings('confCamera.ini', QtCore.QSettings.Format.IniFormat)
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
        
        
        items=camAvailable()
           
        item, ok = QInputDialog.getItem(self, "Select Pixelink camera","List of avaible camera", items, 0, False,flags=QtCore.Qt.WindowType.WindowStaysOnTopHint)
            
        if ok and item:
            items=list(items)
            index = items.index(item)
            self.id=getCamID(index)
            
            self.cam0=PIXELINK_CAM(self.id)
            self.ccdName="CamDefault"
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
            self.id=getCamID(index=0)
            print('id first camera',self.id)
            self.cam0=PIXELINK_CAM(self.id)
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
        self.id=int(camID)
        # print('id to open:',self.id)
        try:
            self.cam0=PIXELINK_CAM(self.id)
            
            self.isConnected=True
        
                
        except: 
            self.isConnected=False
                
        if self.isConnected==True:
            self.setCamParameter()          
            
            
            
    def setCamParameter(self): 
        """Set initial parameters
        """
               
        self.cam0.Open()
        
        print(' connected@: ',self.id )
                
        
        self.LineTrigger=str('None') # for 
        
        self.cam0.setTriggering(value='off')
        
        self.camParameter["expMax"]=self.cam0.getExposureRange()[1]
        
        self.camParameter["expMin"]=self.cam0.getExposureRange()[0]
        
        self.camParameter["gainMax"]=self.cam0.getGainRange()[1]
        self.camParameter["gainMin"]=self.cam0.getGainRange()[0]
        
        #if exposure time save in the ini file is not in the range we put the minimum
        if self.camParameter["expMin"] <=float(self.conf.value(self.nbcam+"/shutter"))<=self.camParameter["expMax"]:
            self.cam0.setExposure(float(self.conf.value(self.nbcam+"/shutter")))
        else:
            self.cam0.setExposure(self.camParameter["expMin"]*1000)
    
        self.camParameter["exposureTime"]=self.cam0.getExposure()
        
        
        if self.camParameter["gainMin"] <=int(self.conf.value(self.nbcam+"/gain"))<=self.camParameter["gainMax"]:
            self.cam0.setGain(float(self.conf.value(self.nbcam+"/gain")))
        else:
            print('gain error: gain set to minimum value')
            self.cam0.setGain(self.camParameter["gainMin"])
        
        self.camParameter["gain"]=self.cam0.getGain()
        
        
        
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
        
        self.cam0.setExposure(sh) # in balser ccd exposure time is microsecond
        self.camParameter["exposureTime"]=float(self.cam0.getExposure())
        print("exposure time is set to",float(self.cam0.getExposure()),' ms')
        
    def setGain(self,g):
        ''' set gain 
        '''
        
        self.cam0.setGain(g) # 
        print("Gain is set to",self.cam0.getGain())   
        self.camParameter["gain"]=self.cam0.getGain()
    
    def softTrigger(self):
        '''to have a sofware trigger
        '''
        print('trig soft')

    def setTrigger(self,trig='off'):
        '''set trigger mode on/off
        '''
        
        if trig=='on':
            self.cam0.setTriggering(value='on')
            self.itrig='on'
        else:
            self.cam0.setTriggering(value='off')
            self.itrig='off'
        
        self.camParameter["trigger"]=self.cam0.getTriggering()
        
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
        self.threadOneAcq.stopThreadOneAcq()
        if self.threadRunAcq.isRunning():
            self.threadRunAcq.terminate()
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
        print('close pixelink')
        self.cam0.setTriggering('off')
        self.cam0.Close()
    
        
        
        
class ThreadRunAcq(QtCore.QThread):
    '''Second thread for controling continus acquisition independtly
    '''
    newDataRun=QtCore.pyqtSignal(object)
    
    def __init__(self, parent):
        
        super(ThreadRunAcq,self).__init__(parent)
        self.parent=parent
        self.cam0 = parent.cam0
        self.stopRunAcq=False
        self.itrig= parent.itrig
        self.LineTrigger=parent.LineTrigger
        
        
    def newRun(self):
        self.stopRunAcq=False
        
    def run(self):
        self.cam0.startStream()
        while self.stopRunAcq is not True :
            if self.stopRunAcq==True:
                    break
            self.data=self.cam0.getNextFrame()
            
            self.data=np.rot90(self.data,1)
            
            if np.max(self.data)>0: # send data if not zero 
                
                if self.stopRunAcq==True:
                    break
                else :
                    self.newDataRun.emit(self.data)
                    # print(self.cam0.DeviceTemperature.GetValue())
            
    def stopThreadRunAcq(self):
        
        try :
            trig=self.cam0.getTriggering()    
            if trig=='on':
                self.cam0.setTriggering('software')
                print('send software trigger')
                self.cam0.getNextFrame()
                time.sleep(0.1)
                self.cam0.setTriggering('on')
            self.cam0.stopStream()
        except :
            pass
        self.stopRunAcq=True
        
    
        
        
        
class ThreadOneAcq(QtCore.QThread):
    '''Second thread for controling one or anumber of  acquisition independtly
    '''
    newDataRun=QtCore.pyqtSignal(object)
    newStateCam=QtCore.pyqtSignal(bool) # signal to emit the state (running or not) of the camera
    
    def __init__(self, parent):
        
        super(ThreadOneAcq,self).__init__(parent)
        self.parent=parent
        self.cam0 = parent.cam0
        self.stopRunAcq=False
        self.itrig= parent.itrig
        self.LineTrigger=parent.LineTrigger
        
   
    
    def newRun(self):
        self.stopRunAcq=False
        
    def run(self):
        self.newStateCam.emit(True)
        self.cam0.startStream()
        for i in range (self.parent.nbShot):
            if self.stopRunAcq is not True :
                self.data=self.cam0.getNextFrame()
            
                self.data=np.rot90(self.data,1)
                
                if i<self.parent.nbShot-1:
                    self.newStateCam.emit(True)
                else:
                    self.newStateCam.emit(False)
                    time.sleep(0.1)
                    
                if np.max(self.data)>0 : 
                    self.newDataRun.emit(self.data)
                    print('newdata')
            else:
                break
            
        self.newStateCam.emit(False)
       
    def stopThreadOneAcq(self):
        
        try :
            trig=self.cam0.getTriggering()    
            if trig=='on':
                self.cam0.setTriggering('software')
                print('send software trigger')
                self.cam0.getNextFrame()
                time.sleep(0.1)
                self.cam0.setTriggering('on')
            self.cam0.stopStream()
        except :
            pass
        self.stopRunAcq=True
        
    
        
    
        
if __name__ == "__main__":       
    
    appli = QApplication(sys.argv) 
    e = PIXELINK(cam=None)
    appli.exec_()              
        
        
        
        