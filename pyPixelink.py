# -*- coding: utf-8 -*-
"""
Created on Mon May 18 17:52:05 2020

@author: loa
"""

import pixelinkWrapper # pip install pixelinkWrapper: https://github.com/pixelink-support/pixelinkPythonWrapper
import ctypes 
import numpy

class PIXELINK_CAM(object):
    # a easer way to use pixelinkWrapper
    def __init__(self,idNb):
        self.id=idNb
        self.PT_COLOR = 0
        self.PT_MONO = 1
    def Open(self):
        
        ret=pixelinkWrapper.PxLApi.initialize(self.id)
        if pixelinkWrapper.PxLApi.apiSuccess(ret[0]):
            self.hCamera=ret[1]
            
            # Figure out if this is a mono or color camera, so that we know the type of
            # image we will be working with.
            self.pixelType = self.getPixelType()
            
             # Just going to declare a very large buffer here
             # One that's large enough for any PixeLINK 4.0 camera
            self.rawFrame = ctypes.create_string_buffer(5000 * 5000 * 2)
            
        else : 
            print ('no camera pixelink found') 
            
    def Close(self):
        pixelinkWrapper.PxLApi.uninitialize(self.hCamera)
            
    
    def getExposureRange(self):
        ret = pixelinkWrapper.PxLApi.getCameraFeatures(self.hCamera, pixelinkWrapper.PxLApi.FeatureId.EXPOSURE)
        if not pixelinkWrapper.PxLApi.apiSuccess(ret[0]):
            print ("  Could not getCameraFeatuers exposure, ret: %d!" % ret[0])
            return
        else:
            cameraFeatures = ret[1]
            params = cameraFeatures.Features[0].Params
            minExp=(params[0].fMinValue)*1000
            maxExp=(params[0].fMaxValue)*1000
            return [minExp,maxExp] # in ms 
        
    def getGainRange(self):
        ret = pixelinkWrapper.PxLApi.getCameraFeatures(self.hCamera, pixelinkWrapper.PxLApi.FeatureId.GAIN)
        if not pixelinkWrapper.PxLApi.apiSuccess(ret[0]):
            print ("  Could not getCameraFeatuers gain, ret: %d!" % ret[0])
            return
        else:
            cameraFeatures = ret[1]
            params = cameraFeatures.Features[0].Params
            minGain=(params[0].fMinValue)
            maxGain=(params[0].fMaxValue)
            
            return [minGain,maxGain]
           
    def getExposure(self):
        ret = pixelinkWrapper.PxLApi.getFeature(self.hCamera, pixelinkWrapper.PxLApi.FeatureId.EXPOSURE)
        if not pixelinkWrapper.PxLApi.apiSuccess(ret[0]):
            print ("  Could not getCameraFeatuers exposure, ret: %d!" % ret[0])
            return
        else:
            
            param = ret[2]
            return param[0]*1000 # in ms 
        
    def getGain(self):
        ret = pixelinkWrapper.PxLApi.getFeature(self.hCamera, pixelinkWrapper.PxLApi.FeatureId.GAIN)
        if not pixelinkWrapper.PxLApi.apiSuccess(ret[0]):
            print ("  Could not getCameraFeatuers exposure, ret: %d!" % ret[0])
            return
        else:
            
            param = ret[2]
            return param[0]
        
    def setExposure(self,exp):
        ## exp in ms
        exp=exp/1000 #♠plx is in second
        ret = pixelinkWrapper.PxLApi.getFeature(self.hCamera, pixelinkWrapper.PxLApi.FeatureId.EXPOSURE)
        params = ret[2]
        
        params[0] = float(exp)
        ret = pixelinkWrapper.PxLApi.setFeature(self.hCamera, pixelinkWrapper.PxLApi.FeatureId.EXPOSURE,pixelinkWrapper.PxLApi.FeatureFlags.MANUAL, params)
        
    def setGain(self,gain):
        
        ret = pixelinkWrapper.PxLApi.getFeature(self.hCamera, pixelinkWrapper.PxLApi.FeatureId.GAIN)
        params = ret[2]
        
        params[0] = float(gain)
        ret = pixelinkWrapper.PxLApi.setFeature(self.hCamera, pixelinkWrapper.PxLApi.FeatureId.GAIN, pixelinkWrapper.PxLApi.FeatureFlags.MANUAL, params)
        
    
    def is_triggering_supported(self):

    # Read the trigger feature information
        ret = pixelinkWrapper.PxLApi.getCameraFeatures(self.hCamera, pixelinkWrapper.PxLApi.FeatureId.TRIGGER)
        assert pixelinkWrapper.PxLApi.apiSuccess(ret[0])

        cameraFeatures = ret[1]
        # Check the sanity of the return information
        assert 1 == cameraFeatures.uNumberOfFeatures                                # We only asked about one feature...
        assert pixelinkWrapper.PxLApi.FeatureId.TRIGGER == cameraFeatures.Features[0].uFeatureId    # ... and that feature is triggering
        
        self.isSupported = ((cameraFeatures.Features[0].uFlags & pixelinkWrapper.PxLApi.FeatureFlags.PRESENCE) != 0)
        if self.isSupported:
            # While we're here, check an assumption about the number of parameters
            assert pixelinkWrapper.PxLApi.TriggerParams.NUM_PARAMS == cameraFeatures.Features[0].uNumberOfParameters
        
        return self.isSupported
    
    def setTriggering(self, value='off'):
        
        # set trigger in different mode 
        if self.is_triggering_supported()==True :
            
            mode=pixelinkWrapper.PxLApi.TriggerModes.MODE_0
            polarity=pixelinkWrapper.PxLApi.Polarity.ACTIVE_LOW
            delay=0.0
            param=0
            
            if value=='on' and self.isSupported==True : 
                triggerType=pixelinkWrapper.PxLApi.TriggerTypes.HARDWARE
                # Read current settings
                ret = pixelinkWrapper.PxLApi.getFeature(self.hCamera, pixelinkWrapper.PxLApi.FeatureId.TRIGGER)
                assert pixelinkWrapper.PxLApi.apiSuccess(ret[0])
                flags = ret[1]
                params = ret[2]
                assert 5 == len(params)
                
                # Very important step: Enable triggering by clearing the FEATURE_FLAG_OFF bit
                flags = ~pixelinkWrapper.PxLApi.FeatureFlags.MOD_BITS | pixelinkWrapper.PxLApi.FeatureFlags.MANUAL
            
                # Assign the new values...
                params[pixelinkWrapper.PxLApi.TriggerParams.MODE] = mode
                params[pixelinkWrapper.PxLApi.TriggerParams.TYPE] = triggerType
                params[pixelinkWrapper.PxLApi.TriggerParams.POLARITY] = polarity
                params[pixelinkWrapper.PxLApi.TriggerParams.DELAY] = delay
                params[pixelinkWrapper.PxLApi.TriggerParams.PARAMETER] = param
            
                # ... and write them to the camera
                ret = pixelinkWrapper.PxLApi.setFeature(self.hCamera, pixelinkWrapper.PxLApi.FeatureId.TRIGGER, flags, params)
                assert pixelinkWrapper.PxLApi.apiSuccess(ret[0])
                
            if value=='off':
                # Read current settings
                ret = pixelinkWrapper.PxLApi.getFeature(self.hCamera, pixelinkWrapper.PxLApi.FeatureId.TRIGGER)
                assert pixelinkWrapper.PxLApi.apiSuccess(ret[0])
                flags = ret[1]
                params = ret[2]
                assert 5 == len(params)
    
                # Disable triggering
                flags = ~pixelinkWrapper.PxLApi.FeatureFlags.MOD_BITS | pixelinkWrapper.PxLApi.FeatureFlags.OFF
                triggerType=pixelinkWrapper.PxLApi.TriggerTypes.FREE_RUNNING
                params[pixelinkWrapper.PxLApi.TriggerParams.MODE] = mode
                params[pixelinkWrapper.PxLApi.TriggerParams.TYPE] = triggerType
                params[pixelinkWrapper.PxLApi.TriggerParams.POLARITY] = polarity
                params[pixelinkWrapper.PxLApi.TriggerParams.DELAY] = delay
                params[pixelinkWrapper.PxLApi.TriggerParams.PARAMETER] = param
                ret = pixelinkWrapper.PxLApi.setFeature(self.hCamera, pixelinkWrapper.PxLApi.FeatureId.TRIGGER, flags, params)
                assert pixelinkWrapper.PxLApi.apiSuccess(ret[0])
                
            if value=='software':
                # Read current settings
                ret = pixelinkWrapper.PxLApi.getFeature(self.hCamera, pixelinkWrapper.PxLApi.FeatureId.TRIGGER)
                assert pixelinkWrapper.PxLApi.apiSuccess(ret[0])
                flags = ret[1]
                params = ret[2]
                assert 5 == len(params)
    
                flags = ~pixelinkWrapper.PxLApi.FeatureFlags.MOD_BITS | pixelinkWrapper.PxLApi.FeatureFlags.MANUAL
                triggerType=pixelinkWrapper.PxLApi.TriggerTypes.SOFTWARE
                params[pixelinkWrapper.PxLApi.TriggerParams.MODE] = mode
                params[pixelinkWrapper.PxLApi.TriggerParams.TYPE] = triggerType
                params[pixelinkWrapper.PxLApi.TriggerParams.POLARITY] = polarity
                params[pixelinkWrapper.PxLApi.TriggerParams.DELAY] = delay
                params[pixelinkWrapper.PxLApi.TriggerParams.PARAMETER] = param
                ret = pixelinkWrapper.PxLApi.setFeature(self.hCamera, pixelinkWrapper.PxLApi.FeatureId.TRIGGER, flags, params)
                assert pixelinkWrapper.PxLApi.apiSuccess(ret[0])
        else :
            print('triggering is not supported')
            
    def getTriggering(self):
        
        ret = pixelinkWrapper.PxLApi.getFeature(self.hCamera, pixelinkWrapper.PxLApi.FeatureId.TRIGGER)
        params=ret[2]
        triggerType=params[pixelinkWrapper.PxLApi.TriggerParams.TYPE] 
        if triggerType==pixelinkWrapper.PxLApi.TriggerTypes.HARDWARE:
            return 'on'
        if triggerType==pixelinkWrapper.PxLApi.TriggerTypes.FREE_RUNNING :
            return 'off'
        if triggerType==pixelinkWrapper.PxLApi.TriggerTypes.SOFTWARE:
            return 'software'
    
    def startStream(self):
        ret = pixelinkWrapper.PxLApi.setStreamState(self.hCamera, pixelinkWrapper.PxLApi.StreamState.START)
        if not pixelinkWrapper.PxLApi.apiSuccess(ret[0]):
            print("Error: Unable to start the stream on the camera")
    
    
    def stopStream(self):
        ret = pixelinkWrapper.PxLApi.setStreamState(self.hCamera, pixelinkWrapper.PxLApi.StreamState.SOP)
        if not pixelinkWrapper.PxLApi.apiSuccess(ret[0]):
            print("Error: Unable to stop the stream on the camera")
    
    
    def getNextFrame(self):
        ret = pixelinkWrapper.PxLApi.getNextFrame(self.hCamera, self.rawFrame)
        frameDesc = ret[1]
        if pixelinkWrapper.PxLApi.apiSuccess(ret[0]):
            # Convert it to a formatedImage. Note that frame can be in any one of a large number of pixel
            # formats, so we will simplify things by converting all mono to mono8, and all color to rgb24
            if self.PT_MONO == self.pixelType:
                ret = pixelinkWrapper.PxLApi.formatImage(self.rawFrame, frameDesc, pixelinkWrapper.PxLApi.ImageFormat.RAW_MONO8)
            else:
                ret = pixelinkWrapper.PxLApi.formatImage(self.rawFrame, frameDesc, pixelinkWrapper.PxLApi.ImageFormat.RAW_RGB24)
            if pixelinkWrapper.PxLApi.apiSuccess(ret[0]):
                formatedImage = ret[1]
            
                # Step 4
                # 'convert' the formatedImage buffer to a numpy ndarray that OpenCV can manipulate
                npFormatedImage = numpy.full_like(formatedImage, formatedImage, order="C") # a numpy ndarray
                npFormatedImage.dtype = numpy.uint8
                # Reshape the numpy ndarray into multidimensional array
                imageHeight = int(frameDesc.Roi.fHeight)
                imageWidth = int(frameDesc.Roi.fWidth)
                # color has 3 channels, mono just 1
                if self.PT_MONO == self.pixelType:
                    newShape = (imageHeight, imageWidth)
                else:
                    newShape = (imageHeight, imageWidth, 3)
                npFormatedImage= numpy.reshape(npFormatedImage, newShape)
                return npFormatedImage
    
    def getPixelType(self):
        
        pixelType =2 # PT_OTHERWISE
        # Take a simple minded approach; All Pixelink monochrome cameras support PxLApi.PixelFormat.MONO8, and all
        # Pixelink color cameas support PxLApi.PixelFormat.BAYER8. So, try setting each of these to see if it 
        # works.
        
        # However, we should take care to restore the current pixel format.
        savedPixelFormat = 0
        newPixelFormat = 0
        ret = pixelinkWrapper.PxLApi.getFeature(self.hCamera, pixelinkWrapper.PxLApi.FeatureId.PIXEL_FORMAT)
        if not pixelinkWrapper.PxLApi.apiSuccess(ret[0]):
            return pixelType
    
        params = ret[2]
        savedPixelFormat = int(params[0])
    
        # Is it mono?
        newPixelFormat = pixelinkWrapper.PxLApi.PixelFormat.MONO8
        params = [newPixelFormat,]
        ret = pixelinkWrapper.PxLApi.setFeature(self.hCamera, pixelinkWrapper.PxLApi.FeatureId.PIXEL_FORMAT, pixelinkWrapper.PxLApi.FeatureFlags.MANUAL, params)
        if not pixelinkWrapper.PxLApi.apiSuccess(ret[0]):
            # Nope, so is it color?
            newPixelFormat = pixelinkWrapper.PxLApi.PixelFormat.BAYER8
            params = [newPixelFormat,]
            ret = pixelinkWrapper.PxLApi.setFeature(self.hCamera, pixelinkWrapper.PxLApi.FeatureId.PIXEL_FORMAT, pixelinkWrapper.PxLApi.FeatureFlags.MANUAL, params)
            if pixelinkWrapper.PxLApi.apiSuccess(ret[0]):
                # Yes, it IS color
                pixelType = self.PT_COLOR
        else:
            # Yes, it IS mono
            pixelType = self.PT_MONO
    
        # Restore the saved pixel format
        params = [savedPixelFormat,]
        pixelinkWrapper.PxLApi.setFeature(self.hCamera, pixelinkWrapper.PxLApi.FeatureId.PIXEL_FORMAT, pixelinkWrapper.PxLApi.FeatureFlags.MANUAL, params)
    
        return pixelType
    
if __name__ == "__main__":           

    cameras=pixelinkWrapper.PxLApi.getNumberCameras()  
    cameras=cameras[1]
    id=cameras[0].CameraSerialNum
    a=PIXELINK_CAM(id)
    a.Open()
    a.setExposure(50)
    exp=a.getExposure()
    a.setGain(10)
    e=a.getGain()
    a
    print(e)