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
try :
    from PyQt6.QtWidgets import QWidget,QInputDialog,QApplication
    from PyQt6 import QtCore,QtGui
except ImportError:

    from PyQt5.QtWidgets import QApplication,QWidget
    from PyQt5.QtCore import Qt,QMutex
    from pyqtgraph.Qt import QtCore

import sys,time
import numpy as np
import pathlib,os

#https://github.com/TheImagingSource/IC-Imaging-Control-Samples
try:
    from dll import tisgrabber as IC 
except:
    print("")
try :
    
    # print('import imgSource dll : ok')
    Camera = IC.TIS_CAM()
    Devices = Camera.GetDevices()
except :
    print ('librairy imaging source not found')
    print('add path ...\camera\dll\ in environement variable path and reboot spyder ')
    print('in windows :parametres system/infosysteme/inrformationsytem/parametre systeme avance/variable d environement')
    pass
    
def camAvailable():
    # print(Devices)
    DeviceDecode=[x.decode() for x in Devices]
    print(DeviceDecode)
    return DeviceDecode

def getCamID(index):
    return(Devices[index]) 
    
class IMGSOURCE (QtCore.QThread):
    newData=QtCore.pyqtSignal(object)
    
    def __init__(self,cam='camDefault',**kwds):
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
        # print('callback')
        p = pathlib.Path(__file__)
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
        self.Camera = IC.TIS_CAM()
        self.cam0=self.Camera
    
        
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
            self.cam0.open(Devices[0].decode())
           
            self.isConnected=True
            self.camID=Devices[0].decode()
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
            # print('ICI connected@ ID:',self.camID)
        except:# if id number doesn't work we take the first one
            try:
                print('Id not valid open the fisrt camera')
                self.cam0.open(Devices[0].decode())
                self.isConnected=True
                self.camID=Devices[0].decode()
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
        
        print('trigger available :',self.cam0.is_triggerable())
        self.camParameter["triggerAvailable"]=self.cam0.is_triggerable()
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
       
        # print(self.cam0.GetPropertyAbsoluteValue("Exposure","Value"))
        
        self.cam0.SetPropertySwitch("Gain","Auto",0)
        
        if float(self.conf.value(self.nbcam+"/gain"))< self.camParameter["gainMin"] or float(self.conf.value(self.nbcam+"/gain"))>self.camParameter["gainMax"]:
            print('gain error: gain set to minimum value')
            self.cam0.SetPropertyValue("Gain","Value",self.camParameter["gainMin"])
        else :
            self.cam0.SetPropertyValue("Gain","Value",int(self.conf.value(self.nbcam+"/gain")))
        self.camParameter["exposureTime"]=(self.cam0.GetPropertyAbsoluteValue("Exposure","Value")*1000)
        
        #self.cam0.enable_trigger(False)
       
        self.camParameter["gain"]=self.cam0.GetPropertyValue("Gain","Value")
        
        #print(self.camParameter)
        
        # self.cam0.feature('Height').value=self.cam0.feature('HeightMax').value
        # self.cam0.feature('Height').value=self.cam0.feature('HeightMax').value
        # self.cam0.feature('Width').value=self.cam0.feature('WidthMax').value
        # self.cam0.feature('Width').value=self.cam0.feature('WidthMax').value
        
    
        
        self.threadRunAcq=ThreadRunAcq(self)
        if self.multi==True:
            self.threadRunAcq.newDataRun.connect(self.newImageReceived,QtCore.Qt.DirectConnection)
        else:  
            self.threadRunAcq.newDataRun.connect(self.newImageReceived)
        
        self.threadOneAcq=ThreadOneAcq(self)
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
            self.cam0.enable_trigger(True)
            self.itrig='on'
        else:
            self.cam0.enable_trigger(False)
            self.itrig='off'
            
    def startAcq(self):
        
        self.camIsRunnig=True
        self.threadRunAcq.newRun()# to set stopRunAcq=False
        self.threadRunAcq.start()
        
        
    def startOneAcq(self,nbShot):
        self.nbShot=nbShot 
        self.camIsRunnig=True
        self.threadOneAcq.newRun() # to set stopRunAcq=False
        self.threadOneAcq.start()
        
    def stopAcq(self):
        
        self.threadRunAcq.stopThreadRunAcq()
        if self.threadRunAcq.isRunning():
            self.threadRunAcq.terminate()
            
        self.threadOneAcq.stopThreadOneAcq()
        self.camIsRunnig=False  
            
    def newImageReceived(self,data):
        
        self.data=data
        self.newData.emit(self.data) # emit data to main program
        
        
    def stateCam(self,state):
        self.camIsRunnig=state
    
    def closeCamera(self):
        self.cam0.close()


class ThreadRunAcq(QtCore.QThread):
    
    '''Second thread for controling continus acquisition independtly
    '''
    newDataRun=QtCore.pyqtSignal(object)
    
    def __init__(self, parent):
        
        super(ThreadRunAcq,self).__init__(parent)
        self.parent=parent
        self.cam0 = self.parent.cam0
        self.stopRunAcq=False
        # self.itrig= self.parent.itrig
        self.mutex=QtCore.QMutex()
    def __del__(self):
        self.wait()   
        
    def newRun(self):
        
        self.stopRunAcq=False
        
    def run(self):
        self.itrig= self.parent.itrig
        self.cam0.reset_frame_ready()
        self.cam0.SetContinuousMode(0)
        self.cam0.StartLive(0)
        
        self.cam0.enable_trigger(True)
        
        
        if not self.cam0.callback_registered:
            self.cam0.SetFrameReadyCallback()
            
        
        while self.stopRunAcq is not True :
            self.mutex.lock()
            self.cam0.reset_frame_ready()
            if self.stopRunAcq:
                break
            if self.itrig=="off": # if no harware trigger we send a soft trigger
                self.cam0.send_trigger()
                # print('soft trig send')
            # self.cam0.SnapImage()
            
            self.cam0.wait_til_frame_ready(20000000)
            
            data1 = self.cam0.GetImage() 
            #data1 = np.array(data1)#☻, dtype=np.double)
            data1.squeeze()
            data=data1[:,:,0]
            
            self.data=np.rot90(data,1)
            
            if np.max(self.data)>0:
                self.newDataRun.emit(self.data)
               
            self.mutex.unlock()  
         
            
    def stopThreadRunAcq(self):
        
        self.stopRunAcq=True
        self.cam0.StopLive()
        self.cam0.send_trigger()   
        
        
class ThreadOneAcq(QtCore.QThread):
    
    '''Second thread for controling one acquisition independtly
    '''
    newDataRun=QtCore.pyqtSignal(object) # signal to send data 
    newStateCam=QtCore.pyqtSignal(bool) #signal to send the state of the camera (running or not)
    
    def __init__(self, parent):
        
        super(ThreadOneAcq,self).__init__(parent)
        self.parent=parent
        self.cam0 = self.parent.cam0
        self.stopRunAcq=False
        self.itrig= self.parent.itrig
        
        
    def newRun(self):
        self.stopRunAcq=False
        
    def run(self):
        
        self.newStateCam.emit(True)
        self.cam0.reset_frame_ready()
        self.cam0.SetContinuousMode(0)
        self.cam0.StartLive(0)
        self.cam0.enable_trigger(True)
        if not self.cam0.callback_registered:
            self.cam0.SetFrameReadyCallback()
            
        for i in range (self.parent.nbShot):
            if self.stopRunAcq:
                break
            if self.stopRunAcq is not True :
                
                if self.itrig=='off' : # si cam pas en mode trig externe on envoi un trig soft...
                    self.cam0.send_trigger()
               
                self.cam0.wait_til_frame_ready(2000000)
                data1 = self.cam0.GetImage() 
                data1 = np.array(data1, dtype=np.double)
                data1.squeeze()
                data=data1[:,:,0]
                self.data=np.rot90(data,1)
                
                
                if i<self.parent.nbShot-1:
                    self.newStateCam.emit(True)
                else:
                    self.newStateCam.emit(False)
                    time.sleep(0.1)
                if np.max(self.data)>0:
                    self.newDataRun.emit(self.data)
                time.sleep(0.5)
            self.newStateCam.emit(False)
        
        
        
    def stopThreadOneAcq(self):
        
        self.stopRunAcq=True
        self.cam0.StopLive()
        self.cam0.send_trigger()       
        
      
if __name__ == "__main__":       
    
    appli = QApplication(sys.argv) 
    # appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    pathVisu='C:/Users/loa/Desktop/Python/guppyCam/guppyCam/confVisuFootPrint.ini'
    e = IMGSOURCE(cam='cam0')  
    camAvailable()
    
   
        
        