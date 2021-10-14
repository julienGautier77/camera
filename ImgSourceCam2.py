# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 10:23:01 2020

@author: Julien Gautier (LOA)

camAvailable:

    return list of all camera

getCamID(index)

    return the ID of the camera 

class Imaging :
    
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
from PyQt5.QtWidgets import QApplication,QWidget

from pyqtgraph.Qt import QtCore

import sys,time
import numpy as np
import pathlib,os

#https://github.com/TheImagingSource/IC-Imaging-Control-Samples

try :
    from dll import tisgrabber as IC 
    print('import imgSource dll : ok')
    Camera = IC.TIS_CAM()
    Devices = Camera.GetDevices()
except :
    print ('librairy imaging source not found')
    #add path ...\camera\dll\ in environement variable path
    # in windows :parametres system/infosysteme/inrformationsytem/parametre systeme avance/variable d'environement
    pass
    
def camAvailable():
    print(Devices)
    DeviceDecode=[x.decode() for x in Devices]
    return DeviceDecode

def getCamID(index):
    return(Devices[index]) 
    
class IMGSOURCE (QWidget):
    newData=QtCore.pyqtSignal(object)
    
    def __init__(self,cam='camDefault',conf=None):
        '''
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
                where file is the ini file where camera parameters are saved
                usefull to set init parameters (expTime and gain)
            The default is None.
        Returns
        -------
        None.

        '''
        
        super(IMGSOURCE,self).__init__()
        p = pathlib.Path(__file__)
        self.nbcam=cam
        self.itrig='off'
        if conf==None:
            self.conf=QtCore.QSettings('confCamera.ini', QtCore.QSettings.IniFormat)
        else:
            self.conf=conf
        self.camParameter=dict()
        self.camIsRunnig=False
        self.nbShot=1
    
        self.cam0=Camera
    
        
    def openMenuCam(self):
        '''create a message box to choose a camera
        '''
        self.cam0.ShowDeviceSelectionDialog()
        if self.cam0IsDevValid() == 1:
            self.isConnected==True
            self.setCamParameter()
        else:
            self.isConnected==False
        return self.isConnected
    
    def openFirstCam(self):
        try :
            self.cam0.open(Devices[0])
            self.isConnected=True
            self.camID=Devices[0]
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
            self.cam0.open(self.camID)
            self.isConnected=True
            print('connected@ ID:',self.camID)
        except:# if id number doesn't work we take the first one
            try:
                print('Id not valid open the fisrt camera')
                self.cam0.open(Devices[0])
                self.isConnected=True
                self.camID=Devices[0]
                self.nbcam='camDefault'
            except:
                    print('not ccd connected')
                    self.isConnected=False
                    self.ccdName='no camera'            
        if self.isConnected==True:
            self.setCamParameter()
            
    def setCamParameter(self):
        
        
        '''initialisation of camera parameter : 
        '''
            
        print( 'connected @:'  ,self.camID )
         #self.cam0.SetFrameRate(10)   
        # self.cam0.SetFormat(IC.SinkFormats.RGB24)
        # self.cam0.SetVideoFormat("RGB32 (640x480)")
        # self.camParameter["format"]=self.cam0.GetFormat()
        
        print('trigger',self.cam0.is_triggerable())
        
        self.camParameter["gainMax"]=self.cam0.GetPropertyValueRange("Gain","Value")[1]
        self.camParameter["gainMin"]=self.cam0.GetPropertyValueRange("Gain","Value")[0]
        #self.camParameter["trigger"]=self.cam0.is_triggerable
        
        self.camParameter["expMax"]=self.cam0.GetPropertyAbsoluteRange("Exposure","Value")[1]*1000
        self.camParameter["expMin"]=self.cam0.GetPropertyAbsoluteRange("Exposure","Value")[0]*1000
        

        
        self.cam0.SetPropertySwitch("Exposure","Auto",0)
        sh=float(self.conf.value(self.nbcam+"/shutter") )/ 1000
        #if exposure time save in the ini file is not in the range we put the minimum
        if self.camParameter["expMin"] <=int(self.conf.value(self.nbcam+"/shutter"))<=self.camParameter["expMax"]:
            
            self.cam0.SetPropertyAbsoluteValue("Exposure","Value",sh)
        else :
            self.cam0.SetPropertyAbsoluteValue("Exposure","Value",float(self.camParameter["expMin"]))
       
        print(self.cam0.GetPropertyAbsoluteValue("Exposure","Value"))
        
        self.cam0.SetPropertySwitch("Gain","Auto",0)
        
        if float(self.conf.value(self.nbcam+"/gain"))< self.camParameter["gainMin"] or float(self.conf.value(self.nbcam+"/gain"))>self.camParameter["gainMax"]:
            print('gain error: gain set to minimum value')
            self.cam0.SetPropertyValue("Gain","Value",self.camParameter["gainMin"])
        else :
            self.cam0.SetPropertyValue("Gain","Value",int(self.conf.value(self.nbcam+"/gain")))
        self.camParameter["exposureTime"]=(self.cam0.GetPropertyAbsoluteValue("Exposure","Value")*1000)
        
        #self.cam0.enable_trigger(False)
       
        self.camParameter["gain"]=self.cam0.GetPropertyValue("Gain","Value")
        
        print(self.camParameter)
        
        # self.cam0.feature('Height').value=self.cam0.feature('HeightMax').value
        # self.cam0.feature('Height').value=self.cam0.feature('HeightMax').value
        # self.cam0.feature('Width').value=self.cam0.feature('WidthMax').value
        # self.cam0.feature('Width').value=self.cam0.feature('WidthMax').value
        
    
        
        self.threadRunAcq=ThreadRunAcq(self,cam0=self.cam0,LineTrigger='self.LineTrigger')
        self.threadRunAcq.newDataRun.connect(self.newImageReceived)
        
        self.threadOneAcq=ThreadOneAcq(self,cam0=self.cam0,LineTrigger='self.LineTrigger')
        self.threadOneAcq.newDataRun.connect(self.newImageReceived)
        self.threadOneAcq.newStateCam.connect(self.stateCam)
            
            
    def setExposure(self,sh):
        ''' 
            set exposure time in ms
        '''
        self.cam0.SetPropertyAbsoluteValue("Exposure","Value",float(sh/1000)) # in imagingSource ccd exposure time is second
         
        print("exposure time is set to",(self.cam0.GetPropertyAbsoluteValue("Exposure","Value")*1000),' ms')
        
    def setGain(self,g):
        ''' 
            set gain 
        '''
        self.cam0.SetPropertyValue("Gain","Value",int(g) )# 
        print("gain is set to",self.cam0.GetPropertyValue("Gain","Value"))
    
    def softTrigger(self):
        '''to have a sofware trigger
        '''
        print('trig soft')
        self.cam0.send_trigger()
         

    def setTrigger(self,trig='off'):
        '''
            set trigger mode on/off
        '''
        
        if trig=='on':
            self.cam0.enable.trigger(True)
            self.itrig='on'
        else:
            self.cam0.enable.trigger(False)
            self.itrig='off'
            
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
    
    def __init__(self, parent,cam0=None,itrig=None,LineTrigger='Line2'):
        
        super(ThreadRunAcq,self).__init__(parent)
        self.parent=parent
        self.cam0 = cam0
        self.stopRunAcq=False
        self.itrig= self.parent.itrig
        self.LineTrigger=LineTrigger
        
    def newRun(self):
        self.stopRunAcq=False
        
    def run(self):
        def handle_frame(handle_ptr, p_data, frame_num, data):
            print ('callback called!', frame_num)
            print ('time.time()')
    
        self.cam0.enable_trigger(True) 
        self.cam0.SetContinuousMode(0)
        self.cam0.reset_frame_ready()
        self.cam0.StartLive(0)
        
        if not self.cam0.callback_registered:
            
            self.cam0.SetFrameReadyCallback()
                    
        while self.stopRunAcq is not True : 
           
            self.cam0.enable_trigger(True)     
            self.cam0.reset_frame_ready()
            self.cam0.send_trigger()
            self.cam0.wait_til_frame_ready(2000)
            dat1=0
            while np.max(dat1)==0:
                a=self.cam0.SnapImage()
                dat1=self.cam0.GetImageEx()
                print(a)
            print(dat1.max())
            if dat1 is not None:
                
                dat1 = np.array(dat1)#, dtype=np.double)
                dat1.squeeze()
                dat1=dat1[:,:,0]
                print(dat1)
                self.data=np.rot90(dat1,1)
                print('start8')
                if self.stopRunAcq==True:
                    break
                else :
                    self.newDataRun.emit(self.data)
            
        self.cam0.StopLive() 
            
    def stopThreadRunAcq(self):
        
        #self.cam0.send_trigger()
        
        self.stopRunAcq=True
        
        if self.itrig=='off' : # si cam pas en mode trig externe on envoi un trig soft...
                self.cam0.send_trigger()
        
class ThreadOneAcq(QtCore.QThread):
    
    '''Second thread for controling one acquisition independtly
    '''
    newDataRun=QtCore.Signal(object) # signal to send data 
    newStateCam=QtCore.Signal(bool) #signal to send the state of the camera (running or not)
    
    def __init__(self, parent,cam0=None,itrig=None,LineTrigger='Line2'):
        
        super(ThreadOneAcq,self).__init__(parent)
        self.parent=parent
        self.cam0 = cam0
        self.stopRunAcq=False
        self.itrig= itrig
        self.LineTrigger=LineTrigger
        
    
    def newRun(self):
        self.stopRunAcq=False
        
    def run(self):
        
        self.cam0.feature('TriggerSource').value='Software'
        self.newStateCam.emit(True)
        
        for i in range (self.parent.nbShot):
            if self.stopRunAcq is not True :
                self.cam0.reset_frame_ready()
                self.cam0.start_live(show_display=False)
                self.cam0.enable_trigger(True)
                if not self.cam0.callback_registered:
                    self.cam0.register_frame_ready_callback()
        
                
                if self.itrig=='off' : # si cam pas en mode trig externe on envoi un trig soft...
                    self.cam0.send_trigger()
               
                self.cam0.wait_til_frame_ready(2000000)
                dat1 = self.cam0.get_image_data() 
                
                
                
                if i<self.parent.nbShot-1:
                    self.newStateCam.emit(True)
                else:
                    self.newStateCam.emit(False)
                    time.sleep(0.1)
                if dat1 is not None:
                    dat1 = np.array(dat1)#, dtype=np.double)
                    dat1.squeeze()
                    dat=dat1[:,:,0]
                    self.data=np.rot90(dat,1)
                    self.newDataRun.emit(self.data)
            
        self.newStateCam.emit(False)
        
        
        
    def stopThreadOneAcq(self):
        
        #self.cam0.send_trigger()
        
        self.stopRunAcq=True
        
        self.cam0.send_trigger()       
        
      
if __name__ == "__main__":       
    
    appli = QApplication(sys.argv) 
    # appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    pathVisu='C:/Users/loa/Desktop/Python/guppyCam/guppyCam/confVisuFootPrint.ini'
    e = IMGSOURCE(cam='camDefault')  
   
        
        