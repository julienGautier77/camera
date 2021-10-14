# -*- coding: utf-8 -*-
"""
Created on Mon Nov 21 09:44:40 2016

@author: Daniel Vassmer, Stefan_Geissler
"""
from enum import Enum

import ctypes as C
import os
import sys,time

import numpy as np

class CallBackUser(C.Structure):
    def __init__(self):
        print('call')
        
    

gr=C.POINTER(CallBackUser)
GrabberHandlePtr = gr  
C_FRAME_READY_CALLBACK = C.CFUNCTYPE(None, GrabberHandlePtr, C.POINTER(C.c_ubyte), C.c_ulong, C.c_void_p)




class SinkFormats(Enum):
   Y800 = 0
   RGB24 = 1 
   RGB32 = 2
   UYVY = 3  
   Y16 = 4

ImageFileTypes = {'BMP':0, 'JPEG':1}


class GrabberHandle(C.Structure):
    pass
GrabberHandle._fields_ = [('unused', C.c_int)]



class TIS_GrabberDLL(object):
    import pathlib
    p = pathlib.Path(__file__)
    sepa=os.sep
    
    if sys.maxsize > 2**32 :
        __tisgrabber = C.windll.LoadLibrary(str(p.parent)+sepa+"tisgrabber_x64.dll")
    else:
        __tisgrabber = C.windll.LoadLibrary(str(p.parent)+sepa+"tisgrabber.dll")
    
    def __init__(self, **keyargs):
        """Initialize the Albatross from the keyword arguments."""
        self.__dict__.update(keyargs)


    GrabberHandlePtr = C.POINTER(GrabberHandle)
    
#     Initialize the ICImagingControl class library. This function must be called
#	only once before any other functions of this library are called.
#	@param szLicenseKey IC Imaging Control license key or NULL if only a trial version is available.
#	@retval IC_SUCCESS on success.
#	@retval IC_ERROR on wrong license key or other errors.
#	@sa IC_CloseLibrary
    InitLibrary = __tisgrabber.IC_InitLibrary(None)
    
#     Get the number of the currently available devices. This function creates an
#	internal array of all connected video capture devices. With each call to this 
#	function, this array is rebuild. The name and the unique name can be retrieved 
#	from the internal array using the functions IC_GetDevice() and IC_GetUniqueNamefromList.
#	They are usefull for retrieving device names for opening devices.
#	
#	@retval >= 0 Success, count of found devices.
#	@retval IC_NO_HANDLE Internal Error.
#
#	@sa IC_GetDevice
#	@sa IC_GetUniqueNamefromList
    get_devicecount =  __tisgrabber.IC_GetDeviceCount
    get_devicecount.restype = C.c_int
    get_devicecount.argtypes = None
    
#     Get unique device name of a device specified by iIndex. The unique device name
#	consist from the device name and its serial number. It allows to differ between 
#	more then one device of the same type connected to the computer. The unique device name
#	is passed to the function IC_OpenDevByUniqueName
#
#	@param iIndex The number of the device whose name is to be returned. It must be
#				in the range from 0 to IC_GetDeviceCount(),
#	@return Returns the string representation of the device on success, NULL
#				otherwise.
#
#	@sa IC_GetDeviceCount
#	@sa IC_GetUniqueNamefromList
#	@sa IC_OpenDevByUniqueName

    get_unique_name_from_list = __tisgrabber.IC_GetUniqueNamefromList
    get_unique_name_from_list.restype = C.c_char_p
    get_unique_name_from_list.argtypes = (C.c_int,)
    
#     Creates a new grabber handle and returns it. A new created grabber should be
#	release with a call to IC_ReleaseGrabber if it is no longer needed.
#	@sa IC_ReleaseGrabber
    create_grabber = __tisgrabber.IC_CreateGrabber
    create_grabber.restype = GrabberHandlePtr
    create_grabber.argtypes = None

#    Open a video capture by using its UniqueName. Use IC_GetUniqueName() to
#    retrieve the unique name of a camera.
#
#	@param hGrabber       Handle to a grabber object
#	@param szDisplayName  Memory that will take the display name.
#
#	@sa IC_GetUniqueName
#	@sa IC_ReleaseGrabber
    open_device_by_unique_name = __tisgrabber.IC_OpenDevByUniqueName
    open_device_by_unique_name.restype = C.c_int
    open_device_by_unique_name.argtypes = (GrabberHandlePtr,
                                           C.c_char_p)   
                                           

    set_videoformat = __tisgrabber.IC_SetVideoFormat
    set_videoformat.restype = C.c_int
    set_videoformat.argtypes = (GrabberHandlePtr,
                                           C.c_char_p)   

    set_framerate = __tisgrabber.IC_SetFrameRate
    set_framerate.restype = C.c_int
    set_framerate.argtypes = (GrabberHandlePtr,
                                           C.c_float)   
                                          
    get_framerate = __tisgrabber.IC_GetFrameRate
    get_framerate.restype = C.c_int
    get_framerate.argtypes = (GrabberHandlePtr,) 


                                     
#    Returns the width of the video format.                                          
    get_video_format_width = __tisgrabber.IC_GetVideoFormatWidth
    get_video_format_width.restype = C.c_int
    get_video_format_width.argtypes = (GrabberHandlePtr,)                                          
    
#    returns the height of the video format.
    get_video_format_height = __tisgrabber.IC_GetVideoFormatHeight
    get_video_format_height.restype = C.c_int
    get_video_format_height.argtypes = (GrabberHandlePtr,)                            
    
    
#    Get the number of the available video formats for the current device. 
#	A video capture device must have been opened before this call.
#	
#	@param hGrabber The handle to the grabber object.
#
#	@retval >= 0 Success
#	@retval IC_NO_DEVICE No video capture device selected.
#	@retval IC_NO_HANDLE No handle to the grabber object.
#
#	@sa IC_GetVideoFormat
    GetVideoFormatCount = __tisgrabber.IC_GetVideoFormatCount
    GetVideoFormatCount.restype = C.c_int
    GetVideoFormatCount.argtypes = (GrabberHandlePtr,)

#     Get a string representation of the video format specified by iIndex. 
#	iIndex must be between 0 and IC_GetVideoFormatCount().
#	IC_GetVideoFormatCount() must have been called before this function,
#	otherwise it will always fail.	
#
#	@param hGrabber The handle to the grabber object.
#	@param iIndex Number of the video format to be used.
#
#	@retval Nonnull The name of the specified video format.
#	@retval NULL An error occured.
#	@sa IC_GetVideoFormatCount
    GetVideoFormat = __tisgrabber.IC_GetVideoFormat
    GetVideoFormat.restype = C.c_char_p
    GetVideoFormat.argtypes = (GrabberHandlePtr,
                               C.c_int,) 

#    Get the number of the available input channels for the current device.
#    A video	capture device must have been opened before this call.
#
#	@param hGrabber The handle to the grabber object.
#
#	@retval >= 0 Success
#	@retval IC_NO_DEVICE No video capture device selected.
#	@retval IC_NO_HANDLE No handle to the grabber object.
#
#	@sa IC_GetInputChannel                               
    GetInputChannelCount = __tisgrabber.IC_GetInputChannelCount
    GetInputChannelCount.restype = C.c_int
    GetInputChannelCount.argtypes = (GrabberHandlePtr,)
    
#     Get a string representation of the input channel specified by iIndex. 
#	iIndex must be between 0 and IC_GetInputChannelCount().
#	IC_GetInputChannelCount() must have been called before this function,
#	otherwise it will always fail.		
#	@param hGrabber The handle to the grabber object.
#	@param iIndex Number of the input channel to be used..
#
#	@retval Nonnull The name of the specified input channel
#	@retval NULL An error occured.
#	@sa IC_GetInputChannelCount
    GetInputChannel = __tisgrabber.IC_GetInputChannel
    GetInputChannel.restype = C.c_char_p
    GetInputChannel.argtypes = (GrabberHandlePtr,
                               C.c_int,)     
    
    
#     Get the number of the available video norms for the current device. 
#	A video capture device must have been opened before this call.
#	
#	@param hGrabber The handle to the grabber object.
#
#	@retval >= 0 Success
#	@retval IC_NO_DEVICE No video capture device selected.
#	@retval IC_NO_HANDLE No handle to the grabber object.
#	
#	@sa IC_GetVideoNorm
    GetVideoNormCount = __tisgrabber.IC_GetVideoNormCount
    GetVideoNormCount.restype = C.c_int
    GetVideoNormCount.argtypes = (GrabberHandlePtr,)
    
    
#     Get a string representation of the video norm specified by iIndex. 
#	iIndex must be between 0 and IC_GetVideoNormCount().
#	IC_GetVideoNormCount() must have been called before this function,
#	otherwise it will always fail.		
#	
#	@param hGrabber The handle to the grabber object.
#	@param iIndex Number of the video norm to be used.
#
#	@retval Nonnull The name of the specified video norm.
#	@retval NULL An error occured.
#	@sa IC_GetVideoNormCount
    GetVideoNorm = __tisgrabber.IC_GetVideoNorm
    GetVideoNorm.restype = C.c_char_p
    GetVideoNorm.argtypes = (GrabberHandlePtr,
                               C.c_int,)  


    SetFormat = __tisgrabber.IC_SetFormat
    SetFormat.restype = C.c_int
    SetFormat.argtypes = (GrabberHandlePtr,
                               C.c_int,)  
    GetFormat = __tisgrabber.IC_GetFormat
    GetFormat.restype = C.c_int
    GetFormat.argtypes = (GrabberHandlePtr,)  


#    Start the live video. 
#	@param hGrabber The handle to the grabber object.
#	@param iShow The parameter indicates:   @li 1 : Show the video	@li 0 : Do not show the video, but deliver frames. (For callbacks etc.)
#	@retval IC_SUCCESS on success
#	@retval IC_ERROR if something went wrong.
#	@sa IC_StopLive

    StartLive = __tisgrabber.IC_StartLive
    StartLive.restype = C.c_int
    StartLive.argtypes = (GrabberHandlePtr,
                               C.c_int,) 

    StopLive = __tisgrabber.IC_StopLive
    StopLive.restype = C.c_int
    StopLive.argtypes = (GrabberHandlePtr,) 


    SetHWND = __tisgrabber.IC_SetHWnd
    SetHWND.restype = C.c_int
    SetHWND.argtypes = (GrabberHandlePtr,
                               C.c_int,) 


#    Snaps an image. The video capture device must be set to live mode and a 
#	sink type has to be set before this call. The format of the snapped images depend on
#	the selected sink type. 
#
#	@param hGrabber The handle to the grabber object.
#	@param iTimeOutMillisek The Timeout time is passed in milli seconds. A value of -1 indicates, that
#							no time out is set.
#
#	
#	@retval IC_SUCCESS if an image has been snapped
#	@retval IC_ERROR if something went wrong.
#	@retval IC_NOT_IN_LIVEMODE if the live video has not been started.
#
#	@sa IC_StartLive 
#	@sa IC_SetFormat
    
    SnapImage=__tisgrabber.IC_SnapImage
    SnapImage.restype = C.c_int
    SnapImage.argtypes = (GrabberHandlePtr,
                               C.c_int,) 
 
 
#    Retrieve the properties of the current video format and sink type 
#	@param hGrabber The handle to the grabber object.
#	@param *lWidth  This recieves the width of the image buffer.
#	@param *lHeight  This recieves the height of the image buffer.
#	@param *iBitsPerPixel  This recieves the count of bits per pixel.
#	@param *format  This recieves the current color format.
#	@retval IC_SUCCESS on success
#	@retval IC_ERROR if something went wrong.
                           
    GetImageDescription = __tisgrabber.IC_GetImageDescription
    GetImageDescription.restype = C.c_int     
    GetImageDescription.argtypes = (GrabberHandlePtr,
                                    C.POINTER(C.c_long),
                                    C.POINTER(C.c_long),
                                    C.POINTER(C.c_int),
                                    C.POINTER(C.c_int),)
                      
     
     

    GetImagePtr = __tisgrabber.IC_GetImagePtr
    GetImagePtr.restype = C.c_void_p
    GetImagePtr.argtypes = (GrabberHandlePtr,) 
    
    
# ############################################################################
    ShowDeviceSelectionDialog = __tisgrabber.IC_ShowDeviceSelectionDialog
    ShowDeviceSelectionDialog.restype = GrabberHandlePtr
    ShowDeviceSelectionDialog.argtypes = (GrabberHandlePtr,)

# ############################################################################
    
    ShowPropertyDialog = __tisgrabber.IC_ShowPropertyDialog
    ShowPropertyDialog.restype = GrabberHandlePtr
    ShowPropertyDialog.argtypes = (GrabberHandlePtr,)
    
# ############################################################################
    IsDevValid = __tisgrabber.IC_IsDevValid
    IsDevValid.restype = C.c_int     
    IsDevValid.argtypes = (GrabberHandlePtr,)

# ############################################################################

    LoadDeviceStateFromFile = __tisgrabber.IC_LoadDeviceStateFromFile
    LoadDeviceStateFromFile.restype = GrabberHandlePtr     
    LoadDeviceStateFromFile.argtypes = (GrabberHandlePtr,C.c_char_p)
    
# ############################################################################
    SaveDeviceStateToFile = __tisgrabber.IC_SaveDeviceStateToFile
    SaveDeviceStateToFile.restype = C.c_int     
    SaveDeviceStateToFile.argtypes = (GrabberHandlePtr,C.c_char_p)
    
    
    GetCameraProperty = __tisgrabber.IC_GetCameraProperty
    GetCameraProperty.restype = C.c_int
    GetCameraProperty.argtypes = (GrabberHandlePtr,
                                                 C.c_int,
                                                 C.POINTER(C.c_long),)

    SetCameraProperty = __tisgrabber.IC_SetCameraProperty
    SetCameraProperty.restype = C.c_int
    SetCameraProperty.argtypes = (GrabberHandlePtr,
                                                 C.c_int,
                                                 C.c_long,)


    SetPropertyValue = __tisgrabber.IC_SetPropertyValue
    SetPropertyValue.restype = C.c_int
    SetPropertyValue.argtypes = (GrabberHandlePtr,
                            C.c_char_p,
                            C.c_char_p,
                            C.c_int, )


    GetPropertyValue = __tisgrabber.IC_GetPropertyValue
    GetPropertyValue.restype = C.c_int
    GetPropertyValue.argtypes = (GrabberHandlePtr,
                            C.c_char_p,
                            C.c_char_p,
                            C.POINTER(C.c_long), )


# ############################################################################
    SetPropertySwitch = __tisgrabber.IC_SetPropertySwitch
    SetPropertySwitch.restype = C.c_int
    SetPropertySwitch.argtypes= (GrabberHandlePtr,
                                 C.c_char_p,
                                 C.c_char_p,
                                  C.c_int,)

    GetPropertySwitch = __tisgrabber.IC_GetPropertySwitch
    GetPropertySwitch.restype = C.c_int
    GetPropertySwitch.argtypes= (GrabberHandlePtr,
                                 C.c_char_p,
                                 C.c_char_p,
                                 C.POINTER(C.c_long),)
# ############################################################################

    IsPropertyAvailable =  __tisgrabber.IC_IsPropertyAvailable
    IsPropertyAvailable.restype =  C.c_int
    IsPropertyAvailable.argtypes=  (GrabberHandlePtr,
                                 C.c_char_p,
                                 C.c_char_p,)

    PropertyOnePush = __tisgrabber.IC_PropertyOnePush
    PropertyOnePush.restype = C.c_int
    PropertyOnePush.argtypes = (GrabberHandlePtr,
                            C.c_char_p,
                            C.c_char_p, )


    SetPropertyAbsoluteValue = __tisgrabber.IC_SetPropertyAbsoluteValue
    SetPropertyAbsoluteValue.restype = C.c_int
    SetPropertyAbsoluteValue.argtypes = (GrabberHandlePtr,
                            C.c_char_p,
                            C.c_char_p,
                            C.c_float, )

    GetPropertyAbsoluteValue = __tisgrabber.IC_GetPropertyAbsoluteValue
    GetPropertyAbsoluteValue.restype = C.c_int
    GetPropertyAbsoluteValue.argtypes = (GrabberHandlePtr,
                            C.c_char_p,
                            C.c_char_p,
                            C.POINTER(C.c_float), )
# ############################################################################
    EnableCameraAutoProperty = __tisgrabber.IC_EnableAutoCameraProperty
    EnableCameraAutoProperty.restype = C.c_int
    EnableCameraAutoProperty.argtypes = (GrabberHandlePtr,
                            C.c_int,
                            C.c_int)
    EnableVideoAutoProperty = __tisgrabber.IC_EnableAutoVideoProperty
    EnableVideoAutoProperty.restype = C.c_int
    EnableVideoAutoProperty.argtypes = (GrabberHandlePtr,
                            C.c_int,
                            C.c_int)
# ############################################################################
    #add by julien Gautier (LOA)
    GetPropertyRange=__tisgrabber.IC_GetPropertyValueRange
    GetPropertyRange.restype= C.c_int
    GetPropertyRange.argtypes = (GrabberHandlePtr,
                                 C.c_char_p,
                                 C.c_char_p,
                                 C.POINTER(C.c_float),
                                 C.POINTER(C.c_float))
    
    GetPropertyAbsoluteRange=__tisgrabber.IC_GetPropertyAbsoluteValueRange
    GetPropertyAbsoluteRange.restype= C.c_int
    GetPropertyAbsoluteRange.argtypes = (GrabberHandlePtr,
                                 C.c_char_p,
                                 C.c_char_p,
                                 C.POINTER(C.c_float),
                                 C.POINTER(C.c_float))
    #
    #@param hGrabber    Handle to a grabber object.
    #    @param Property  The name of the property, e.g. Gain, Exposure
    #    @param Element  The type of the interface, e.g. Value, Auto. If NULL, it is "Value".
    #    @param Min  Receives the min value of the property
    #    @param Max  Receives the max value of the property
    get_property_value_range =__tisgrabber.IC_GetPropertyValueRange
    get_property_value_range.restype = C.c_int
    get_property_value_range.argtypes = (GrabberHandlePtr,
                                         C.c_char_p,
                                         C.c_char_p,
                                         C.POINTER(C.c_int),
                                         C.POINTER(C.c_int))
    
    #//////////////////////////////////////////////////////////////////////////
    #/*!    Enable or disable the external trigger. 
    #    @param hGrabber      Handle to a grabber object.
    #    @param iEnable 1 = enable the trigger, 0 = disable the trigger
    #
    #    @retval IC_SUCCESS    On success. 
    #    @retval IC_ERROR      An error occurred. 
    #
    #    @sa IC_IsTriggerAvailable
    #*/
    #int AC IC_EnableTrigger( HGRABBER hGrabber, int iEnable );
    enable_trigger = __tisgrabber.IC_EnableTrigger
    enable_trigger.restype = C.c_int
    enable_trigger.argtypes = (GrabberHandlePtr,
                               C.c_int)
    
    
    get_trigger_modes = __tisgrabber.IC_GetTriggerModes
    get_trigger_modes.restype = C.c_int
    get_trigger_modes.argtypes = (GrabberHandlePtr,
                                  C.POINTER((C.c_char * 20) * 10),    # hardcoded 10 values, each with 20 characters)
                                  C.c_int)
    
    set_trigger_mode = __tisgrabber.IC_SetTriggerMode
    set_trigger_mode.restype = C.c_int
    set_trigger_mode.argtypes = (GrabberHandlePtr,
                                 C.c_char_p)
    software_trigger = __tisgrabber.IC_SoftwareTrigger
    software_trigger.restype = C.c_int
    software_trigger.argtypes = (GrabberHandlePtr,)
    
    is_trigger_available = __tisgrabber.IC_IsTriggerAvailable
    is_trigger_available.restype = C.c_int
    is_trigger_available.argtypes = (GrabberHandlePtr,)
    
    
    close_device = __tisgrabber.IC_CloseVideoCaptureDevice
    close_device.restype = None
    close_device.argtypes = (GrabberHandlePtr,)
    
# ############################################################################

    # definition of the frameready callback
    FRAMEREADYCALLBACK = C.CFUNCTYPE(C.c_void_p,C.c_int, C.POINTER(C.c_ubyte), C.c_ulong, C.py_object)

    # set callback function
    SetFrameReadyCallback = __tisgrabber.IC_SetFrameReadyCallback
    SetFrameReadyCallback.restype = C.c_int
    SetFrameReadyCallback.argtypes = (GrabberHandlePtr,
                                         C.c_void_p,
                                         C.c_void_p)#, FRAMEREADYCALLBACK, C.py_object]

    SetContinuousMode = __tisgrabber.IC_SetContinuousMode

    SaveImage = __tisgrabber.IC_SaveImage
    SaveImage.restype = C.c_int
    SaveImage.argtypes = [C.c_void_p, C.c_char_p, C.c_int, C.c_int ]

    OpenVideoCaptureDevice = __tisgrabber.IC_OpenVideoCaptureDevice
    OpenVideoCaptureDevice.restype = C.c_int
    OpenVideoCaptureDevice.argtypes = [C.c_void_p, C.c_char_p]
    

# ############################################################################
    
                        
class TIS_CAM(object):
        @property
        def callback_registered(self):
            return self._callback_registered
      
        def __init__(self):
          
            
            self._handle = TIS_GrabberDLL.create_grabber()
            self._callback_registered = False
            self._frame = {'num'    :   -1,
                           'ready'  :   False}    
                                  
        def s(self,strin):
            if sys.version[0] == "2":
                return strin
            if type(strin) == "byte":
                return strin
            return strin.encode("utf-8")
        
        def _get_callback_func(self):
            def cb_func(handle_ptr, p_data, frame_num, data):
                self._frame['ready'] = True
                self._frame['num'] = frame_num
            return C_FRAME_READY_CALLBACK(cb_func)
        
        def SetFrameReadyCallback(self):#CallbackFunction, data
            """ Set a callback function, which is called, when a new frame arrives. 

            CallbackFunction : The callback function

            data : a self defined class with user data.
            """
            # data=None
            #self._rfrc_func
            self._rfrc_func = self._get_callback_func()
            
            TIS_GrabberDLL.SetFrameReadyCallback( self._handle, self._rfrc_func, None )
            self._callback_registered = True
            
            
            
        def SetContinuousMode(self, Mode):
            ''' Determines, whether new frames are automatically copied into memory.

            :param Mode: If 0, all frames are copied automatically into memory. This is recommened, if the camera runs in trigger mode.
                          If 1, then snapImages must be called to get a frame into memory.  
            :return: None
            '''
            return TIS_GrabberDLL.SetContinuousMode(self._handle, Mode)
            
        def open(self,unique_device_name):
            """ Open a device 
            
            unique_device_name : The name and serial number of the device to be opened. The device name and serial number are separated by a space.
            """
            test = TIS_GrabberDLL.open_device_by_unique_name(self._handle,
                                                       self.s(unique_device_name))

            return test 
                                          
        def close(self):
            """
            Close the camera device.
            """
            TIS_GrabberDLL.close_device(self._handle)
            
            
        def ShowDeviceSelectionDialog(self):
            self._handle = TIS_GrabberDLL.ShowDeviceSelectionDialog(self._handle)
            
        def ShowPropertyDialog(self):
            self._handle = TIS_GrabberDLL.ShowPropertyDialog(self._handle)
            
        def IsDevValid(self):
            return TIS_GrabberDLL.IsDevValid(self._handle)
            
        def SetHWND(self, Hwnd):
            return TIS_GrabberDLL.SetHWND(self._handle, Hwnd)

        def SaveDeviceStateToFile(self, FileName):
            return TIS_GrabberDLL.SaveDeviceStateToFile(self._handle, self.s(FileName))
            
        def LoadDeviceStateFromFile(self,FileName):
            self._handle = TIS_GrabberDLL.LoadDeviceStateFromFile(self._handle,self.s(FileName))
            

        def SetVideoFormat(self,Format):
            return TIS_GrabberDLL.set_videoformat(self._handle, self.s(Format))

        def SetFrameRate(self,FPS):
            return TIS_GrabberDLL.set_framerate(self._handle, FPS)
        
        def GetFrameRate(self):
            return TIS_GrabberDLL.get_frame_rate(self._handle)
        
        def get_video_format_width(self):
            return TIS_GrabberDLL.get_video_format_width(self._handle)
            
        def get_video_format_height(self):    
            return TIS_GrabberDLL.get_video_format_height(self._handle)    


        def GetDevices(self):
            self._Devices=[]         
            iDevices = TIS_GrabberDLL.get_devicecount()
            for i in range(iDevices):
                self._Devices.append(TIS_GrabberDLL.get_unique_name_from_list(i))         
            return self._Devices


        def GetVideoFormats(self):
            self._Properties=[]         
            iVideoFormats = TIS_GrabberDLL.GetVideoFormatCount(self._handle)
            for i in range(iVideoFormats):
                self._Properties.append(TIS_GrabberDLL.GetVideoFormat(self._handle,i))         
            return self._Properties

        def GetInputChannels(self):
            self.InputChannels=[] 
            InputChannelscount = TIS_GrabberDLL.GetInputChannelCount(self._handle)
            for i in range (InputChannelscount):
                self.InputChannels.append(TIS_GrabberDLL.GetInputChannel(self._handle,i))
            return self.InputChannels

        def GetVideoNormCount(self):
            self.GetVideoNorm=[]
            GetVideoNorm_Count=TIS_GrabberDLL.GetVideoNormCount(self._handle)
            for i in range(GetVideoNorm_Count):
                self.GetVideoNorm.append(TIS_GrabberDLL.GetVideoNorm(self._handle, i))
            return self.GetVideoNorm
        

        def SetFormat(self, Format):
            ''' SetFormat 
            Sets the pixel format in memory
            @param Format Sinkformat enumeration
            '''
            
            a=TIS_GrabberDLL.SetFormat(self._handle,Format.value)
            print('format',a)

        def GetFormat(self):
            val = TIS_GrabberDLL.GetFormat(self._handle)
            print('get format',val)
            if val == 0:
                return SinkFormats.Y800
            if val == 2:
                return SinkFormats.RGB32
            if val == 1:
                return SinkFormats.RGB24
            if val == 3:
                return SinkFormats.UYVY
            if val == 4:
                return SinkFormats.Y16
            else :
                return val


        def StartLive(self, showlive = 1):
            """
            Start the live video stream.

            showlive: 1 : a live video is shown, 0 : the live video is not shown.
            """
            Error = TIS_GrabberDLL.StartLive(self._handle, showlive)
            return Error

        def StopLive(self):
            """
            Stop the live video.
            """
            Error = TIS_GrabberDLL.StopLive(self._handle)
            return Error

 
        def SnapImage(self):
            Error = TIS_GrabberDLL.SnapImage(self._handle, 2000)
            return Error
 
 
        def GetImageDescription(self):
            lWidth=C.c_long()
            lHeight= C.c_long()
            iBitsPerPixel=C.c_int()
            COLORFORMAT=C.c_int()
            
            Error = TIS_GrabberDLL.GetImageDescription(self._handle, lWidth,
                                        lHeight,iBitsPerPixel,COLORFORMAT)
            return (lWidth.value,lHeight.value,iBitsPerPixel.value,COLORFORMAT.value)
        
        def GetImagePtr(self):
            ImagePtr = TIS_GrabberDLL.GetImagePtr(self._handle)
            
            return ImagePtr
           
        def GetImage(self):
            BildDaten = self.GetImageDescription()[:4]
            lWidth=BildDaten[0]
            lHeight= BildDaten[1]
            iBitsPerPixel=BildDaten[2]//8

            buffer_size = lWidth*lHeight*iBitsPerPixel*C.sizeof(C.c_uint8)            
            img_ptr = self.GetImagePtr()
            
            Bild = C.cast(img_ptr, C.POINTER(C.c_ubyte * buffer_size))
            
            #,
            img = np.ndarray(buffer = Bild.contents,
                        dtype = np.uint8,
                         shape = (lHeight,
                                  lWidth,iBitsPerPixel))
            img.reshape(lHeight,lWidth,iBitsPerPixel)
            img.squeeze()
            return img

        def GetImageEx(self):
            """ Return a numpy array with the image data tyes
            If the sink is Y16 or RGB64 (not supported yet), the dtype in the array is uint16, othereise it is uint8
            """
            BildDaten = self.GetImageDescription()[:4]
            lWidth=BildDaten[0]
            lHeight= BildDaten[1]
            iBytesPerPixel=BildDaten[2]//8

            buffer_size = lWidth*lHeight*iBytesPerPixel*C.sizeof(C.c_uint8)            
            img_ptr = self.GetImagePtr()
            
            Bild = C.cast(img_ptr, C.POINTER(C.c_ubyte * buffer_size))
            
            pixeltype = np.uint8

            if  BildDaten[3] == 4: #SinkFormats.Y16:
                pixeltype = np.uint16
                iBytesPerPixel = 1
            
            img = np.ndarray(buffer = Bild.contents,
                         dtype = pixeltype,
                         shape = (lHeight,
                                  lWidth,
                                  iBytesPerPixel))
            return img


        def GetCameraProperty(self,iProperty):
            lFocusPos = C.c_long()
            Error = TIS_GrabberDLL.GetCameraProperty(self._handle,iProperty, lFocusPos)
            return (lFocusPos.value)            

        def SetCameraProperty(self,iProperty,iValue):
            Error = TIS_GrabberDLL.SetCameraProperty(self._handle,iProperty, iValue)
            return (Error)            

        def SetPropertyValue(self, Property, Element, Value ):
            error = TIS_GrabberDLL.SetPropertyValue(self._handle,
                                                    self.s(Property),
                                                    self.s(Element),
                                                    Value)
            return error


        def GetPropertyValue(self, Property, Element ):
            Value = C.c_long()
            error = TIS_GrabberDLL.GetPropertyValue(self._handle,
                                                    self.s(Property),
                                                    self.s(Element),
                                                    Value)
            return Value.value
        

       
        def PropertyAvailable(self, Property):
            Null = None
            error = TIS_GrabberDLL.IsPropertyAvailable(self._handle,
                                                            self.s(Property),
                                                            Null)
            return error    
            

        def SetPropertySwitch(self, Property, Element, Value):
            error = TIS_GrabberDLL.SetPropertySwitch(self._handle, 
                                                      self.s(Property), 
                                                      self.s(Element),
                                                      Value)
            return error

        def GetPropertySwitch(self, Property, Element, Value):
            lValue = C.c_long()
            error = TIS_GrabberDLL.GetPropertySwitch(self._handle, 
                                                      self.s(Property), 
                                                      self.s(Element),
                                                      lValue)
            Value[0] = lValue.value
            return error

        def PropertyOnePush(self, Property, Element ):
            error = TIS_GrabberDLL.PropertyOnePush(self._handle,
                                                    self.s(Property),
                                                    self.s(Element ))
            return error

        def SetPropertyAbsoluteValue(self, Property, Element, Value ):
            error = TIS_GrabberDLL.SetPropertyAbsoluteValue(self._handle,
                                                    self.s(Property),
                                                    self.s(Element),
                                                    Value)
            return error

        def GetPropertyAbsoluteValue(self, Property, Element ):#,Value
            """ Get a property value of absolute values interface, e.g. seconds or dB.
            Example code:
            ExposureTime=[0]
            Camera.GetPropertyAbsoluteValue("Exposure","Value", ExposureTime)
            print("Exposure time in secods: ", ExposureTime[0])

            :param Property: Name of the property, e.g. Gain, Exposure
            :param Element: Name of the element, e.g. "Value"
            :param Value: Object, that receives the value of the property
            :returns: 0 on success
            """
            lValue = C.c_float()
            error = TIS_GrabberDLL.GetPropertyAbsoluteValue(self._handle,
                                                    self.s(Property),
                                                    self.s(Element),
                                                    lValue)
            #Value[0] = lValue.value
            return lValue.value

        
        def SaveImage(self,FileName, FileType, Quality=75):
            ''' Saves the last snapped image. Can by of type BMP or JPEG.
            :param FileName : Name of the mage file
            :param FileType : Determines file type, can be "JPEG" or "BMP"
            :param Quality : If file typ is JPEG, the qualitly can be given from 1 to 100. 
            :return: Error code
            '''
            return TIS_GrabberDLL.SaveImage(self._handle, self.s(FileName), IC.ImageFileTypes[self.s(FileType)],Quality)

        def openVideoCaptureDevice(self, DeviceName):
            ''' Open the device specified by DeviceName
            :param DeviceName: Name of the device , e.g. "DFK 72AUC02"
            :returns: 1 on success, 0 otherwise.
            '''
            return TIS_GrabberDLL.OpenVideoCaptureDevice(self._handle, self.s(DeviceName))

        def enableCameraAutoProperty(self, property, onoff):
            return TIS_GrabberDLL.EnableCameraAutoProperty(self._handle,property,onoff)

        def enableVideoAutoProperty(self, property, onoff):
            return TIS_GrabberDLL.EnableVideoAutoProperty(self._handle,property,onoff)
        
        #  add by J.Gautier (LOA)
        def GetPropertyAbsoluteRange(self,Property,Element):
            '''
            get range of the property

           
            '''
            ValueMax = C.c_float()
            ValueMin = C.c_float()
            error = TIS_GrabberDLL.GetPropertyAbsoluteRange(self._handle,
                                                self.s(Property),self.s(Element),
                                               ValueMin,ValueMax)
        
            return (ValueMin.value,ValueMax.value)
        
        def GetPropertyRange(self,Property,Element):
            '''
            get range of the property
.

            '''
            ValueMax = C.c_float()
            ValueMin = C.c_float()
            error = TIS_GrabberDLL.GetPropertyRange(self._handle,
                                                self.s(Property),self.s(Element),
                                               ValueMin,ValueMax)
        
            return (ValueMin.value,ValueMax.value)
        
        def GetPropertyValueRange(self,Property,Element):
            
            ValueMax = C.c_int()
            ValueMin = C.c_int()
            error = TIS_GrabberDLL.get_property_value_range(self._handle,
                                                self.s(Property),self.s(Element),
                                               ValueMin,ValueMax)
            return (ValueMin.value,ValueMax.value)
        
        def reset_frame_ready(self):
            """
        Reset the frame ready flag to False, generally so
        that wait_til_frame_ready() can be called again.
            """
            self._frame['ready'] = False
            self._frame['num'] = -1
        
        def wait_til_frame_ready(self, timeout=0):
            """
            Wait until the devices announces a frame as being ready.
            Requires register_frame_ready_callback() being called.
            
            :param timeout: int -- timeout in milliseconds. Set to 0 for no timeout.
            
            :returns: int -- frame number that was announced as ready.
            """
            if timeout:        
                start = time.time()
                elapsed = (time.time() - start) * 1000
                while not self._frame['ready'] and elapsed < timeout:
                    time.sleep(0.001)
                    elapsed = (time.time() - start) * 1000
            else:
                while not self._frame['ready']:
                    time.sleep(0.001)
    
            return self._frame['num']
        
        
        def is_triggerable(self):
            """
            """
            return bool(TIS_GrabberDLL.is_trigger_available(self._handle))
        
        
        def enable_trigger(self, enable):
            """
                Enable or disable camera triggering.
    
                :param enable: boolean -- True to enable the trigger, False to disable.
            """
            err = TIS_GrabberDLL.enable_trigger(self._handle, C.c_int(int(enable)))
            if err != 1:
                print('error enable trig err:',err)
                pass
        
        def send_trigger(self):
            """
            Send a software trigger to fire the device when in triggered mode.
            """
            err = TIS_GrabberDLL.software_trigger(self._handle)
            if err != 1:
                print('error trig')
                pass
        