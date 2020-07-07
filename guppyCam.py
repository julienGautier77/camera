# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 10:23:01 2020

@author: Julien Gautier (LOA)

camAvailable:

    return list of all camera

getCamID(index)

    return the ID of the camera 

class GUPPY :
    
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


from PyQt5.QtWidgets import QApplication,QWidget,QInputDialog
from pyqtgraph.Qt import QtCore
import time,sys
import numpy as np
from PyQt5 import QtGui 

try:
    from pymba import Vimba  ## pip install pymba https://github.com/morefigs/pymba.git  on conda prompt
    Vimba().startup()
    system=Vimba().system()
    cameraIds=Vimba().camera_ids()
    # print( "Cam available:",cameraIds)
    
  #  Encrease timeout :
  #change in File "C:\ProgramData\Anaconda3\lib\site-packages\pymba\camera.py
  #  def acquire_frame(self, timeout_ms: Optional[int] = 200000000) -> Frame: :
except:
    print ('No pymba module installed see : https://github.com/morefigs/pymba.git ')

    
def camAvailable(): 
    return cameraIds    
def getCamID(index):
    return(cameraIds[index]) 

    
class GUPPY (QWidget):
    
    newData=QtCore.pyqtSignal(object)
    
    def __init__(self,cam='camDefault',conf=None):
        
        super(GUPPY,self).__init__()
        
        self.nbcam=cam
        self.itrig='off'
        if conf==None:
            self.conf=QtCore.QSettings('confCamera.ini', QtCore.QSettings.IniFormat)
        else:
            self.conf=conf
        self.camParameter=dict()
        self.camIsRunnig=False
        self.nbShot=1
        self.items=cameraIds
  
    def openMenuCam(self):
        '''create a message box to choose a camera
        '''
        items=cameraIds
        item, ok = QInputDialog.getItem(self, "Select Guppy camera","List of avaible camera", items, 0, False,flags=QtCore.Qt.WindowStaysOnTopHint)
        
        if ok and item:
            items=list(items)
            index = items.index(item)
            self.cam0=Vimba().camera(cameraIds[index])
            self.isConnected=True
            self.nbcam='camDefault'
            self.camID=cameraIds[index]
        if self.isConnected==True:
            self.setCamParameter()
        return self.isConnected
    
    def openFirstCam(self):
        try :
            self.cam0=Vimba().camera(cameraIds[0])
            self.camID=cameraIds[0]
            self.isConnected=True
            self.nbcam='camDefault'
        except:
            self.isConnected=False
            self.ccdName='no camera'
        if self.isConnected==True:
            self.setCamParameter()
        return self.isConnected
    
    def openCamByID(self,camID): 
                
        ''' read cam serial number
        '''
        self.camID=camID
        
        try :
            self.cam0=Vimba().camera(self.camID)
            self.isConnected=True
            
        except:# if id number doesn't work we take the first one
            try:
                print('Id not valid open the fisrt camera')
                self.cam0=Vimba().camera(cameraIds[0])
                self.camID=cameraIds[0]
                self.isConnected=True
            except:
                    print('not ccd connected')
                    self.isConnected=False
                    self.ccdName='no camera'            
        if self.isConnected==True:
            self.setCamParameter()
            
            
    def setCamParameter(self):
        """Open camera
        
        
        Set initial parameters
    
        """
        
        
        print( 'connected @:'  ,self.camID )
        self.cam0.open()
        
        # for feature_name in self.cam0.feature_names():
        #     feature = self.cam0.feature(feature_name)
        #     print(feature_name)
        #     print(" ")
        #     print(" ")
        ## init cam parameter##
        self.LineTrigger=str(self.conf.value(self.nbcam+"/LineTrigger")) # line2 for Mako Line 1 for guppy (not tested)
        
        self.cam0.feature('TriggerMode').value='Off'
        self.cam0.feature('TriggerActivation').value='RisingEdge'
        #self.cam0.feature('TriggerSelector').value='FrameStart'
        self.cam0.feature('TriggerSource').value='Software'
        self.camParameter["trigger"]=self.cam0.feature('TriggerMode').value
        self.cam0.feature('ExposureAuto').value='Off'
        self.cam0.feature('GainAuto').value='Off'
        
        self.cam0.feature('Height').value=self.cam0.feature('HeightMax').value
        self.cam0.feature('Height').value=self.cam0.feature('HeightMax').value
        self.cam0.feature('Width').value=self.cam0.feature('WidthMax').value
        self.cam0.feature('Width').value=self.cam0.feature('WidthMax').value
        
        
        self.camParameter["expMax"]=float(self.cam0.feature('ExposureTime').range[1])/1000
        self.camParameter["expMin"]=float(self.cam0.feature('ExposureTime').range[0])/1000
        #if exposure time save in the ini file is not in the range we put the minimum
        if self.camParameter["expMin"] <=int(self.conf.value(self.nbcam+"/shutter"))<=self.camParameter["expMax"]:
            self.cam0.feature('ExposureTime').value=float(self.conf.value(self.nbcam+"/shutter"))*1000
        else :
            self.cam0.feature('ExposureTime').value=float(self.camParameter["expMin"])
            
        self.camParameter["exposureTime"]=int(self.cam0.feature('ExposureTime').value)/1000
        
        self.camParameter["gainMax"]=self.cam0.feature('Gain').range[1]
        self.camParameter["gainMin"]=self.cam0.feature('Gain').range[0]
        if self.camParameter["gainMin"] <=int(self.conf.value(self.nbcam+"/gain"))<=self.camParameter["gainMax"]:
            self.cam0.feature('Gain').value=int(self.conf.value(self.nbcam+"/gain"))
        else:
            print('gain error: gain set to minimum value')
            self.cam0.feature('Gain').value=int(self.camParameter["gainMin"])
        
        self.camParameter["gain"]=self.cam0.feature('Gain').value
        
        self.threadRunAcq=ThreadRunAcq(self)
        self.threadRunAcq.newDataRun.connect(self.newImageReceived)
        
        self.threadOneAcq=ThreadOneAcq(self)
        self.threadOneAcq.newDataRun.connect(self.newImageReceived)#,QtCore.Qt.DirectConnection)
        self.threadOneAcq.newStateCam.connect(self.stateCam)
            
            
    def setExposure(self,sh):
        ''' 
            set exposure time in ms
        '''
        self.cam0.feature('ExposureTime').value=float(sh*1000) # in gyppy ccd exposure time is microsecond
        self.camParameter["exposureTime"]=int(self.cam0.feature('ExposureTime').value)/1000
        print("exposure time is set to",self.cam0.feature('ExposureTime').value,' micro s')
        
    def setGain(self,g):
        ''' 
            set gain 
        '''
        self.cam0.feature('Gain').value=g # in gyppy ccd exposure time is microsecond
        print("Gain is set to",self.cam0.feature('Gain').value)   
        self.camParameter["gain"]=self.cam0.feature('Gain').value
    
    def softTrigger(self):
        '''to have a sofware trigger
        '''
        print('trig soft')
        self.cam0.feature('TriggerSource').value='Software'
        self.cam0.run_feature_command('TriggerSoftware') 

    def setTrigger(self,trig='off'):
        '''
            set trigger mode on/off
        '''
        
        if trig=='on':
            self.cam0.feature('TriggerMode').value='On'
            self.cam0.feature('TriggerSource').value=self.LineTrigger
            self.itrig='on'
        else:
            self.cam0.feature('TriggerMode').value='Off'
            self.cam0.feature('TriggerSource').value=self.LineTrigger
            self.itrig='off'
        
        self.camParameter["trigger"]=self.cam0.feature('TriggerMode').value
        
    def startAcq(self):
        self.camIsRunnig=True
        self.threadRunAcq.newRun() # to set stopRunAcq=False
        self.threadRunAcq.start()
    
    def startOneAcq(self,nbShot):
        self.nbShot=nbShot 
        self.camIsRunnig=True
        self.threadOneAcq.newRun() # to set stopRunAcq=False
        self.threadOneAcq.start()
        
    def stopAcq(self):
        
        self.threadRunAcq.stopThreadRunAcq()
        self.threadOneAcq.stopThreadOneAcq()
        self.camIsRunnig=False  
            
    def newImageReceived(self,data):
        
        self.data=data
        self.newData.emit(self.data)
    
        
    def stateCam(self,state):
        self.camIsRunnig=state
    
    def closeCamera(self):
        self.cam0.close()
        
    
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
        
    def newRun(self):
        self.stopRunAcq=False
        
    def run(self):
        while self.stopRunAcq is not True :
            if self.parent.itrig=='off':
                self.cam0.feature('TriggerSource').value='Software'
            else :
                self.cam0.feature('TriggerSource').value='InputLines'
            self.cam0.arm('SingleFrame')
            
            dat1=self.cam0.acquire_frame()  
            if self.parent.itrig=='off':
                
                self.cam0.run_feature_command('TriggerSoftware')
            data=dat1.buffer_data_numpy()    
            if np.max(data)>0:
                
                data=np.rot90(data,3)
                if self.stopRunAcq==True:
                    pass
                else :
                    self.newDataRun.emit(data)
            self.cam0.disarm()
            
    def stopThreadRunAcq(self):
        
        #self.cam0.send_trigger()
        
        self.stopRunAcq=True
#        self.cam0.run_feature_command ('AcquisitionAbort')
#        self.cam0.end_capture()
#        self.cam0.feature('TriggerSource').value='Software'
#        self.cam0.run_feature_command('TriggerSoftware')
#            
            
        #self.cam0.feature('TriggerSource').value=self.LineTrigger
        #self.cam0.run_feature_command ('AcquisitionAbort')
        #self.cam0.disarm()
        # if self.itrig=='on': # in hardward trig mode disarm to get out
             
        #     self.cam0.end_capture()
        #     self.cam0.stop_frame_acquisition()
        
        
class ThreadOneAcq(QtCore.QThread):
    
    '''Second thread for controling one or more  acquisition independtly
    '''
    newDataRun=QtCore.Signal(object)
    newStateCam=QtCore.Signal(bool)
    
    def __init__(self, parent):
        
        super(ThreadOneAcq,self).__init__(parent)
        self.parent=parent
        self.cam0 = parent.cam0
        self.stopRunAcq=False
        self.itrig= parent.itrig
        self.LineTrigger=parent.LineTrigger
        
    def wait(self,seconds):
        time_end=time.time()+seconds
        while time.time()<time_end:
            QtGui.QApplication.processEvents()    
    def newRun(self):
        self.stopRunAcq=False
        
    def run(self):
        
       
        self.newStateCam.emit(True)
        
        for i in range (self.parent.nbShot):
            if self.stopRunAcq is not True :
                if self.parent.itrig=='off':
                    self.cam0.feature('TriggerSource').value='Software'
                else :
                    self.cam0.feature('TriggerSource').value='InputLines'
                self.cam0.revoke_all_frames()
                self.cam0.flush_capture_queue()
                self.cam0.arm('SingleFrame')#
                dat1=self.cam0.acquire_frame() 
                
                if self.parent.itrig=='off':
                    self.cam0.run_feature_command('TriggerSoftware')
                # print(dat1.data.receiveStatus,dat1.data.receiveFlags)# == -1
                if i<self.parent.nbShot-1:
                    self.newStateCam.emit(True)
                    
                    time.sleep(0.1)
                else:
                    self.newStateCam.emit(False)
                    
                    time.sleep(0.1)
                data=dat1.buffer_data_numpy()    
                if np.max(data)>0:
                    
                    data=np.rot90(data,3)    
                    if self.stopRunAcq==True:
                        pass
                    else :
                        
                        self.newDataRun.emit(data)
                time.sleep(0.1)  
                self.cam0.disarm()
                
            else:
                break
        self.newStateCam.emit(False)
        
        
        
    def stopThreadOneAcq(self):
        
        #self.cam0.send_trigger()
        self.stopRunAcq=True
#        self.cam0.run_feature_command ('AcquisitionAbort')
#        self.stopRunAcq=True
#        
#        self.cam0.run_feature_command('TriggerSoftware')       





if __name__ == "__main__":       
    appli = QApplication(sys.argv) 
    e = GUPPY(cam=None)
    appli.exec_()          