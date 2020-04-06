# -*- coding: utf-8 -*-
"""
Created on Mon Mar 30 10:23:01 2020

@author: LOA
"""
from PyQt5.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QWidget,QPushButton
from PyQt5.QtWidgets import QComboBox,QSlider,QLabel,QSpinBox
from pyqtgraph.Qt import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import sys,time
import numpy as np
import pathlib,os

#https://github.com/TheImagingSource/IC-Imaging-Control-Samples
try :
    from dll import tisgrabber as IC 
    print('import ok')
except :
    print ('librairy imaging source not found')
    #add path ...\camera\dll\ in environement variable path
    # in windows :parametres sytem/infosysteme/inrformationsytem/parametre systeme avance/variable d'environement
    pass
    
    
class IMGSOURCE (QWidget):
    newData=QtCore.pyqtSignal(object)
    
    def __init__(self,cam='camDefault',conf=None):
        
        super(IMGSOURCE,self).__init__()
        p = pathlib.Path(__file__)
        self.nbcam=cam
        self.itrig='off'
        self.conf=conf#QtCore.QSettings(str(p.parent / conf), QtCore.QSettings.IniFormat) # ini file
        self.camParameter=dict()
        self.camIsRunnig=False
        self.nbShot=1
        self.initCam()
        
        
        
    def initCam(self):
        
        '''initialisation of camera parameter : 
        '''
        self.cam0 = IC.TIS_CAM()
        if self.nbcam=='camDefault': # camDefaul we take the fisrt one
            try:
                
                a=self.cam0.ShowDeviceSelectionDialog()
                self.ccdName='CAM0'
                
                self.isConnected=True
            except:
                self.isConnected=False
                self.ccdName='no camera'
        else :
            self.camID=self.conf.value(self.nbcam+"/camID") ## read cam serial number
            try :
                self.cam0.open(self.camID)
            
                self.isConnected=True
            except:# if it doesn't work we take the first one
                try:
                   self.cam0.ShowDeviceSelectionDialog()
                   self.ccdName='CAM0'
                   self.isConnected=True
                   
                except:
                    print('not ccd connected')
                    self.isConnected=False
                    self.ccdName='no camera'
                    
        if self.isConnected==True:
            # print(self.ccdName, 'is connected @:'  ,self.camID )
            
            
            ## init cam parameter##
           # self.LineTrigger=str(self.conf.value(self.nbcam+"/LineTrigger")) # line2 for Mako Line 1 for guppy (not tested)
            
            
            self.cam0.SetFormat(IC.SinkFormats.RGB24)
            # self.cam0.ShowPropertyDialog()
            #self.cam0.SetFrameRate(10)
            print('trigger',self.cam0.is_triggerable())
            # self.cam0.SetVideoFormat("RGB32 (640x480)")
            
            self.camParameter["format"]=self.cam0.GetFormat()
            self.camParameter["gainMax"]=self.cam0.GetPropertyValueRange("Gain","Value")[1]
            self.camParameter["gainMin"]=self.cam0.GetPropertyValueRange("Gain","Value")[0]
            #self.camParameter["trigger"]=self.cam0.is_triggerable
            
            self.camParameter["exposureMax"]=self.cam0.GetPropertyAbsoluteRange("Exposure","Value")[1]*1000
            self.camParameter["exposureMin"]=self.cam0.GetPropertyAbsoluteRange("Exposure","Value")[0]*1000
            

            
            self.cam0.SetPropertySwitch("Exposure","Auto",0)
            sh=float(self.conf.value(self.nbcam+"/shutter") )/ 1000
            self.cam0.SetPropertyAbsoluteValue("Exposure","Value",sh)
            print(self.cam0.GetPropertyAbsoluteValue("Exposure","Value"))
            self.cam0.SetPropertySwitch("Gain","Auto",0)
            
            if float(self.conf.value(self.nbcam+"/gain"))< self.camParameter["gainMin"] or float(self.conf.value(self.nbcam+"/gain"))>self.camParameter["gainMax"]:
               
                self.cam0.SetPropertyValue("Gain","Value",self.camParameter["gainMin"])
            else :
                self.cam0.SetPropertyValue("Gain","Value",int(self.conf.value(self.nbcam+"/gain")))
            
            #self.cam0.enable_trigger(False)
           
            self.camParameter["exposureTime"]=(self.cam0.GetPropertyAbsoluteValue("Exposure","Value")*1000)
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
    
        print('start')
        self.cam0.enable_trigger(True) 
        self.cam0.SetContinuousMode(0)
        self.cam0.reset_frame_ready()
        self.cam0.StartLive(0)
        
        if not self.cam0.callback_registered:
            print("callback")
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
                print('start7')
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
    newDataRun=QtCore.Signal(object)
    newStateCam=QtCore.Signal(bool)
    
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
    e = IMGSOURCE(cam='camDefault',conf='confCamera.ini')  
   
        
        