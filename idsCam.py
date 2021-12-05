# -*- coding: utf-8 -*-
"""
Created on Thu Oct 28 09:41:18 2021

@author: Julien Gautier (LOA)

IDS camera control : 
    use pyueye (pip install pyueye)
    
    manual :
file:///C:/Program%20Files/IDS/uEye/help/uEye_Manual/index.html#index.html?&_suid=163540684054707250791231363218

"""


from PyQt5.QtWidgets import QApplication,QWidget
from pyqtgraph.Qt import QtCore
import time,sys
import numpy as np
from PyQt5 import QtGui 


from pyueye import ueye  ## 

       
    
class IDS (QWidget):
    
    newData=QtCore.pyqtSignal(object)
    endAcq=QtCore.pyqtSignal(bool)
    
    
    def __init__(self,cam='camDefault',**kwds):
        
        super(IDS,self).__init__()
        
        self.nbcam=cam
        self.itrig='off'
        if "conf"  in kwds :
            self.conf=kwds["conf"]
        else :
            self.conf=QtCore.QSettings('confCamera.ini', QtCore.QSettings.IniFormat)
        self.camParameter=dict()
        self.camIsRunnig=False
        self.nbShot=1
        self.items=2
  
    def openMenuCam(self):
        '''create a message box to choose a camera
        '''
        #to do 
    
    def openFirstCam(self,ID=0):
        
        try :
            self.hCam = ueye.HIDS(0)
            nRet = ueye.is_InitCamera(self.hCam, None)
            if nRet != ueye.IS_SUCCESS:
                print("is_InitCamera ERROR")
                self.isConnected=False
            else :
                self.isConnected=True             #0: first available camera;  1-254: The camera with the specified camera ID
            sInfo = ueye.SENSORINFO()
            cInfo = ueye.CAMINFO()
            ueye.is_GetCameraInfo(self.hCam, cInfo)
            ueye.is_GetSensorInfo(self.hCam, sInfo)
            print('---- yEye IDS camera ----')
            print("Camera model:\t\t", sInfo.strSensorName.decode('utf-8'))
            print("Camera serial no.:\t", cInfo.SerNo.decode('utf-8'))
            
            self.nbcam='camDefault'
            
        except:
                self.isConnected=False
                self.ccdName='no camera'
                
        if self.isConnected==True:
            self.setCamParameter()
            
            
        return self.isConnected
        
    
    def openCamByID(self,camID=0): 
                
        ''' read cam serial number to do 
        '''
        self.camID=camID
        print('cam ID',self.camID)
        try :
            self.hCam = ueye.HIDS(int(self.camID))  #0: first available camera;  1-254: The camera with the specified camera ID
            nRet = ueye.is_InitCamera(self.hCam, None)
            if nRet != ueye.IS_SUCCESS:
                print("is_InitCamera ERROR")
                self.isConnected=False
            else :
                self.isConnected=True            
            sInfo = ueye.SENSORINFO()
            cInfo = ueye.CAMINFO()
            ueye.is_GetCameraInfo(self.hCam, cInfo)
            ueye.is_GetSensorInfo(self.hCam, sInfo)
            print('---- yEye IDS camera ----')
            print("Camera model:\t\t", sInfo.strSensorName.decode('utf-8'))
            print("Camera serial no.:\t", cInfo.SerNo.decode('utf-8'))
            
            self.nbcam=self.nbcam
            
        except:
                self.isConnected=False
                self.ccdName='no camera'
                
        if self.isConnected==True:
            self.setCamParameter()
            
            
        return self.isConnected
            
    def setCamParameter(self):
        """Open camera
        
        
        Set initial parameters
    
        """
       
        nRet = ueye.is_ResetToDefault( self.hCam)
        if nRet != ueye.IS_SUCCESS:
            print("is_ResetToDefault ERROR")
            
        self.camLanguage=dict()
        # nTriggerMode=0
        # ueye.is_SetExternalTrigger(self.hCam, nTriggerMode) 
        # print('trig off')
            
        
        self.pcImageMemory= ueye.c_mem_p()
        self.MemID = ueye.int()
        self.rectAOI = ueye.IS_RECT()
        self.pitch = ueye.INT()
        self.nBitsPerPixel = ueye.INT(8)    #24: bits per pixel for color mode; take 8 bits per pixel for monochrome
        self.channels = 3                    #3: channels for color mode(RGB); take 1 channel for monochrome
        self.m_nColorMode = ueye.INT()		# Y8/RGB16/RGB24/REG32
        self.bytes_per_pixel = int(self.nBitsPerPixel / 8)
        
        # # Reads out the data hard-coded in the non-volatile camera memory and writes it to the data structure that cInfo points to
        # nRet = ueye.is_GetCameraInfo(self.hCam, cInfo)
        # if nRet != ueye.IS_SUCCESS:
        #     print("is_GetCameraInfo ERROR")
        
        # # You can query additional information about the sensor type used in the camera
        # nRet = ueye.is_GetSensorInfo(self.hCam, sInfo)
        # if nRet != ueye.IS_SUCCESS:
        #     print("is_GetSensorInfo ERROR")
        
        # Set display mode to DIB
        nRet = ueye.is_SetDisplayMode(self.hCam, ueye.IS_SET_DM_DIB)
        # for monochrome camera models use Y8 mode
        self.m_nColorMode= ueye.IS_CM_MONO8
        self.nBitsPerPixel = ueye.INT(8)
        self.bytes_per_pixel= int(self.nBitsPerPixel / 8)
        
        # Can be used to set the size and position of an "area of interest"(AOI) within an image
        nRet = ueye.is_AOI(self.hCam, ueye.IS_AOI_IMAGE_GET_AOI, self.rectAOI, ueye.sizeof(self.rectAOI))
        if nRet != ueye.IS_SUCCESS:
            print("AOI ERROR")
        
        self.width = self.rectAOI.s32Width
        self.height = self.rectAOI.s32Height
        
        
        # Allocates an image memory for an image having its dimensions defined by width and height and its color depth defined by nBitsPerPixel
        nRet = ueye.is_AllocImageMem(self.hCam, self.width, self.height, self.nBitsPerPixel, self.pcImageMemory, self.MemID)
        if nRet != ueye.IS_SUCCESS:
            print("is_AllocImageMem ERROR")
        else:
            # Makes the specified image memory the active memory
            nRet = ueye.is_SetImageMem(self.hCam, self.pcImageMemory, self.MemID)
            if nRet != ueye.IS_SUCCESS:
                print("is_SetImageMem ERROR")
            else:
                # Set the desired color mode
                nRet = ueye.is_SetColorMode(self.hCam, self.m_nColorMode)
        
        
        
        ## set auto exp and Gain off
        value = ueye.c_double(0)
        value_to_return = ueye.c_double()
        ueye.is_SetAutoParameter(self.hCam,
                                        ueye.IS_SET_ENABLE_AUTO_SHUTTER,
                                        value,
                                        value_to_return)
        
        ueye.is_SetAutoParameter(self.hCam,
                                        ueye.IS_SET_ENABLE_AUTO_GAIN,
                                        value,
                                        value_to_return)
        
        
        
        # exposure init value
        exposureMin=ueye.c_double()
        ueye.is_Exposure(self.hCam, ueye.IS_EXPOSURE_CMD_GET_LONG_EXPOSURE_RANGE_MIN,
                                exposureMin,  8)
        
        self.camParameter["expMin"]=exposureMin
        exposureMax=ueye.c_double()
        ueye.is_Exposure(self.hCam, ueye.IS_EXPOSURE_CMD_GET_LONG_EXPOSURE_RANGE_MAX,
                                exposureMax,  8)
        self.camParameter["expMax"]=exposureMax
        print('Exposure min :' ,exposureMin)
        print('Exposure max :' ,exposureMax)
        # set long range exposure time
        setEnable=ueye.c_uint(int(1))
        nRet=ueye.is_Exposure(self.hCam, ueye.IS_EXPOSURE_CMD_SET_LONG_EXPOSURE_ENABLE,
                               setEnable,4)
        if nRet != ueye.IS_SUCCESS:
            print('error long range exp set')
        
        #if exposure time save in the ini file is out of range we put the minimum
        if self.camParameter["expMin"] <=float(self.conf.value(self.nbcam+"/shutter"))<=self.camParameter["expMax"]:
            exposure=ueye.c_double(int(self.conf.value(self.nbcam+"/shutter")))
            
            nRet=ueye.is_Exposure(self.hCam, ueye.IS_EXPOSURE_CMD_SET_EXPOSURE,
                                exposure,  8)
            if nRet != ueye.IS_SUCCESS:
                print('error exp set')
                
        else :
              exposure=ueye.c_double(self.camParameter["expMin"])
              ueye.is_Exposure(self.hCam, ueye.IS_EXPOSURE_CMD_SET_EXPOSURE,
                                exposure,  8)
              
        exposureGet=ueye.c_double()
        nRet=ueye.is_Exposure(self.hCam, ueye.IS_EXPOSURE_CMD_GET_EXPOSURE,
                                exposureGet,  8)
        if nRet != ueye.IS_SUCCESS:
                print('exposure error get')
        self.camParameter["exposureTime"]=round(float(exposureGet))
        
        
        #gain init
        self.camParameter["gainMax"]=100
        self.camParameter["gainMin"]=0
        
        if self.camParameter["gainMin"] <=int(self.conf.value(self.nbcam+"/gain"))<=self.camParameter["gainMax"]:
            gain=ueye.c_int(int(self.conf.value(self.nbcam+"/gain")))
                          
            ueye.is_SetHardwareGain(self.hCam,gain,ueye.IS_IGNORE_PARAMETER,ueye.IS_IGNORE_PARAMETER,ueye.IS_IGNORE_PARAMETER)
        else:
            print('gain error: gain set to minimum value')
            gain=ueye.c_int(int(0))
                          
            ueye.is_SetHardwareGain(self.hCam,gain,ueye.IS_IGNORE_PARAMETER,ueye.IS_IGNORE_PARAMETER,ueye.IS_IGNORE_PARAMETER)
        value_to_return = ueye.is_SetHardwareGain(self.hCam,ueye.IS_GET_MASTER_GAIN,ueye.IS_IGNORE_PARAMETER,ueye.IS_IGNORE_PARAMETER,ueye.IS_IGNORE_PARAMETER)
        self.camParameter["gain"]=value_to_return
        
        
        self.threadRunAcq=ThreadRunAcq(self)
        self.threadRunAcq.newDataRun.connect(self.newImageReceived)
        
        self.threadOneAcq=ThreadOneAcq(self)
        self.threadOneAcq.newDataRun.connect(self.newImageReceived)#,QtCore.Qt.DirectConnection)
        self.threadOneAcq.newStateCam.connect(self.stateCam)
        self.threadOneAcq.endAcq.connect(self.endAcquisition)
            
    def setExposure(self,sh):
        ''' 
            set exposure time in ms
            
        '''
        
        exposure=ueye.c_double(sh)
        ueye.is_Exposure(self.hCam, ueye.IS_EXPOSURE_CMD_SET_EXPOSURE,
                               exposure,  8)
        
        exposureGet=ueye.c_double()
        ueye.is_Exposure(self.hCam, ueye.IS_EXPOSURE_CMD_GET_EXPOSURE,
                               exposureGet,  8)
        self.camParameter["exposureTime"]=exposureGet
        print('exposure set to',exposureGet)
    
    def setGain(self,g):
        ''' 
            set gain 
        '''
        gain=ueye.c_int(int(g))
                          
        ueye.is_SetHardwareGain(self.hCam,gain,ueye.IS_IGNORE_PARAMETER,ueye.IS_IGNORE_PARAMETER,ueye.IS_IGNORE_PARAMETER)
        value_to_return =ueye.is_SetHardwareGain(self.hCam,ueye.IS_GET_MASTER_GAIN,ueye.IS_IGNORE_PARAMETER,ueye.IS_IGNORE_PARAMETER,ueye.IS_IGNORE_PARAMETER)
        self.camParameter["gain"]=value_to_return
        #print("Gain is set to",self.camParameter["gain"])   
        
        
    # def softTrigger(self):
    #     '''to have a sofware trigger
    #     '''
    #     print('trig soft')
    #     

    def setTrigger(self,trig='off'):
        '''
            set trigger mode on/off
        '''
        if trig=='on':
            nTriggerMode=0     
        else:
            nTriggerMode=1
        
        ueye.is_SetExternalTrigger(self.hCam, nTriggerMode) 
                
        
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
        
    def endAcquisition(self):
        self.endAcq.emit(True) # emit signal when acquisition is done
        
    def closeCamera(self):
        self.stopAcq()
        # Releases an image memory that was allocated using is_AllocImageMem() and removes it from the driver management
        ueye.is_FreeImageMem(self.hCam, self.pcImageMemory, self.MemID)
        ueye.is_ExitCamera(self.hCam)



        
    
class ThreadRunAcq(QtCore.QThread):
    
    '''Second thread for controling continus acquisition independtly
    '''
    newDataRun=QtCore.Signal(object)
    
    def __init__(self, parent):
        
        super(ThreadRunAcq,self).__init__(parent)
        self.parent=parent
        self.hCam = self.parent.hCam
        self.stopRunAcq=False
        self.itrig= parent.itrig
       
        
    
    def newRun(self):
        self.stopRunAcq=False
        
    def run(self):
        
        nRet = ueye.is_CaptureVideo(self.hCam, ueye.IS_DONT_WAIT)
        if nRet != ueye.IS_SUCCESS:
            print("is_CaptureVideo ERROR")
        
        # Enables the queue mode for existing image memory sequences
        nRet = ueye.is_InquireImageMem(self.hCam, self.parent.pcImageMemory, self.parent.MemID, self.parent.width, self.parent.height, self.parent.nBitsPerPixel, self.parent.pitch)
        if nRet != ueye.IS_SUCCESS:
            print("is_InquireImageMem ERROR")
    
        time.sleep(0.5)
        
        while self.stopRunAcq is not True:
            
            array = ueye.get_data(self.parent.pcImageMemory, self.parent.width, self.parent.height, self.parent.nBitsPerPixel, self.parent.pitch, copy=False)
        
            data = np.reshape(array,(self.parent.height.value, self.parent.width.value, self.parent.bytes_per_pixel))
            data=data[:,:,0]
            data=np.rot90(data,3)
            
            if self.stopRunAcq==True:
                    pass
            else :
                time.sleep(0.01)
                self.newDataRun.emit(data)
            
    def stopThreadRunAcq(self):
        self.stopRunAcq=True
        ueye.is_StopLiveVideo(self.hCam, ueye.IS_FORCE_VIDEO_STOP)
        


class ThreadOneAcq(QtCore.QThread):
    
    '''Second thread for controling one or more  acquisition independtly
    '''
    newDataRun=QtCore.Signal(object)
    newStateCam=QtCore.Signal(bool)
    endAcq=QtCore.Signal(bool) # for enable the stop button
    def __init__(self, parent):
        
        super(ThreadOneAcq,self).__init__(parent)
        
        self.parent=parent
        self.hCam = self.parent.hCam
        self.stopRunAcq=False
        self.itrig= parent.itrig
       
    def wait(self,seconds):
        time_end=time.time()+seconds
        while time.time()<time_end:
            QtGui.QApplication.processEvents()    
    
    def newRun(self):
        self.stopRunAcq=False
        
    
    def run(self):
        
        print(self.parent.nbShot,'one acquisition')
        self.newStateCam.emit(True)
       
        # Activates the camera's live video mode (free run mode)
        nRet = ueye.is_CaptureVideo (self.hCam, ueye.IS_WAIT)
        if nRet != ueye.IS_SUCCESS:
            print("is_CaptureVideo ERROR")
        
        # Enables the queue mode for existing image memory sequences
        nRet = ueye.is_InquireImageMem(self.hCam, self.parent.pcImageMemory, self.parent.MemID, self.parent.width, self.parent.height, self.parent.nBitsPerPixel, self.parent.pitch)
        if nRet != ueye.IS_SUCCESS:
            print("is_InquireImageMem ERROR")
        ueye.is_SetExternalTrigger(self.hCam, ueye.IS_SET_TRIGGER_SOFTWARE)
        time.sleep(0.5)
        for i in range (self.parent.nbShot):
            if self.stopRunAcq is not True :  
                ueye.is_ForceTrigger(self.hCam)
                array = ueye.get_data(self.parent.pcImageMemory, self.parent.width, self.parent.height, self.parent.nBitsPerPixel, self.parent.pitch, copy=False)
        
                data = np.reshape(array,(self.parent.height.value, self.parent.width.value, self.parent.bytes_per_pixel))
        
                data=data[:,:,0]
        
                data=np.rot90(data,3)
                if i<self.parent.nbShot-1:
                    self.newStateCam.emit(True)
                    
                    time.sleep(0.05)
                else:
                    self.newStateCam.emit(False)
                print('emit')
                time.sleep(0.05)
                self.newDataRun.emit(data)
            else:
                break
            
        self.newStateCam.emit(False)
        ueye.is_StopLiveVideo(self.hCam, ueye.IS_FORCE_VIDEO_STOP)
        
        self.endAcq.emit(True)
        
    def stopThreadOneAcq(self):
       
        self.stopRunAcq=True
        ueye.is_StopLiveVideo(self.hCam, ueye.IS_FORCE_VIDEO_STOP)


if __name__ == "__main__":       
    appli = QApplication(sys.argv) 
    e = IDS(cam=None)
    e.openFirstCam()
    appli.exec_()          