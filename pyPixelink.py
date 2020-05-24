# -*- coding: utf-8 -*-
"""
Created on Mon May 18 17:52:05 2020

@author: loa
"""

import pixelinkWrapper 


class PIXELINK_CAM(object):
    
    def __init__(self,idNb):
        self.id=idNb
        
    def open(self):
        
        ret=pixelinkWrapper.PxLApi.initialize(self.id)
        if pixelinkWrapper.PxLApi.apiSuccess(ret[0]):
            self.hCamera=ret[1]
        else : 
            print ('no camera pixelink found') 
    
            
    
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
        self.is_triggering_supported()
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
    
    
    def get_snapshot(self, imageFormat, fileName):
    
        assert 0 != self.hCamer 
        assert fileName
        
        # Determine the size of buffer we'll need to hold an image from the camera
        rawImageSize = self.determine_raw_image_size(self.hCamera)
        if 0 == rawImageSize:
            return pixelink.FAILURE
    
        # Create a buffer to hold the raw image
        rawImage = pixelink.create_string_buffer(rawImageSize)
    
        if 0 != len(rawImage):
            # Capture a raw image. The raw image buffer will contain image data on success. 
            ret = self.get_raw_image(self.hCamera, rawImage)
            if pixelink.PxLApi.apiSuccess(ret[0]):
                frameDescriptor = ret[1]
                
                assert 0 != len(rawImage)
                assert frameDescriptor
                #
                # Do any image processing here
                #
                
                # Encode the raw image into something displayable
                ret = pixelink.PxLApi.formatImage(rawImage, frameDescriptor, imageFormat)
                if pixelink.SUCCESS == ret[0]:
                    formatedImage = ret[1]
                    # Save formated image into a file
                    
                
        return pixelink.FAILURE

    """
    Query the camera for region of interest (ROI), decimation, and pixel format
    Using this information, we can calculate the size of a raw image
    Returns 0 on failure
    """
    def determine_raw_image_size(self):
    
        assert 0 != self.hCamera
    
        # Get region of interest (ROI)
        ret = pixelink.PxLApi.getFeature(self.hCamera, pixelink.PxLApi.FeatureId.ROI)
        params = ret[2]
        roiWidth = pixelink.params[pixelink.PxLApi.RoiParams.WIDTH]
        roiHeight = pixelink.params[pixelink.PxLApi.RoiParams.HEIGHT]
    
        # Query pixel addressing
            # assume no pixel addressing (in case it is not supported)
        pixelAddressingValueX = 1
        pixelAddressingValueY = 1
    
        ret = pixelink.PxLApi.getFeature(self.hCamera, pixelink.PxLApi.FeatureId.PIXEL_ADDRESSING)
        if pixelink.PxLApi.apiSuccess(ret[0]):
            params = ret[2]
            if pixelink.PxLApi.PixelAddressingParams.NUM_PARAMS == len(params):
                # Camera supports symmetric and asymmetric pixel addressing
                pixelAddressingValueX = params[pixelink.PxLApi.PixelAddressingParams.X_VALUE]
                pixelAddressingValueY = params[pixelink.PxLApi.PixelAddressingParams.Y_VALUE]
            else:
                # Camera supports only symmetric pixel addressing
                pixelAddressingValueX = params[pixelink.PxLApi.PixelAddressingParams.VALUE]
                pixelAddressingValueY = params[pixelink.PxLApi.PixelAddressingParams.VALUE]
    
        # We can calulate the number of pixels now.
        numPixels = (roiWidth / pixelAddressingValueX) * (roiHeight / pixelAddressingValueY)
        ret = pixelink.PxLApi.getFeature(self.hCamera, pixelink.PxLApi.FeatureId.PIXEL_FORMAT)
    
        # Knowing pixel format means we can determine how many bytes per pixel.
        params = ret[2]
        pixelFormat = int(params[0])
    
        # And now the size of the frame
        pixelSize = pixelink.PxLApi.getBytesPerPixel(pixelFormat)
    
        return int(numPixels * pixelSize)
    
    """
    Capture an image from the camera.
     
    NOTE: PxLApi.getNextFrame is a blocking call. 
    i.e. PxLApi.getNextFrame won't return until an image is captured.
    So, if you're using hardware triggering, it won't return until the camera is triggered.
    Returns a return code with success and frame descriptor information or API error
    """
    def get_raw_image(self, rawImage):
    
        assert 0 != self.hCamera
        assert 0 != len(rawImage)
    
        MAX_NUM_TRIES = 4
    
        # Put camera into streaming state so we can capture an image
        ret = pixelink.PxLApi.setStreamState(self.hCamera, pixelink.PxLApi.StreamState.START)
        if not pixelink.PxLApi.apiSuccess(ret[0]):
            return pixelink.FAILURE
          
        # Get an image
        # NOTE: pixelink.PxLApi.getNextFrame can return ApiCameraTimeoutError on occasion.
        # How you handle this depends on your situation and how you use your camera. 
        # For this sample app, we'll just retry a few times.
        ret = (pixelink.PxLApi.ReturnCode.ApiUnknownError,)
    
        for i in range(MAX_NUM_TRIES):
            ret = pixelink.PxLApi.getNextFrame(self.hCamera, rawImage)
            if pixelink.PxLApi.apiSuccess(ret[0]):
                break
    
        # Done capturing, so no longer need the camera streaming images.
        # Note: If ret is used for this call, it will lose frame descriptor information.
        pixelink.PxLApi.setStreamState(self.hCamera, pixelink.PxLApi.StreamState.STOP)
    
        return ret
    
    def getPixelType(self):

        pixelType =PT_OTHERWISE
        # Take a simple minded approach; All Pixelink monochrome cameras support PxLApi.PixelFormat.MONO8, and all
        # Pixelink color cameas support PxLApi.PixelFormat.BAYER8. So, try setting each of these to see if it 
        # works.
        
        # However, we should take care to restore the current pixel format.
        savedPixelFormat = 0
        newPixelFormat = 0
        ret = pixelink.PxLApi.getFeature(self.hCamera, pixelink.PxLApi.FeatureId.PIXEL_FORMAT)
        if not pixelink.PxLApi.apiSuccess(ret[0]):
            return pixelType
    
        params = ret[2]
        savedPixelFormat = int(params[0])
    
        # Is it mono?
        newPixelFormat = pixelink.PxLApi.PixelFormat.MONO8
        params = [newPixelFormat,]
        ret = pixelink.PxLApi.setFeature(self.hCamera, pixelink.PxLApi.FeatureId.PIXEL_FORMAT, pixelink.PxLApi.FeatureFlags.MANUAL, params)
        if not pixelink.PxLApi.apiSuccess(ret[0]):
            # Nope, so is it color?
            newPixelFormat = pixelink.PxLApi.PixelFormat.BAYER8
            params = [newPixelFormat,]
            ret = pixelink.PxLApi.setFeature(self.hCamera, pixelink.PxLApi.FeatureId.PIXEL_FORMAT, pixelink.PxLApi.FeatureFlags.MANUAL, params)
            if pixelink.PxLApi.apiSuccess(ret[0]):
                # Yes, it IS color
                pixelType = PT_COLOR
        else:
            # Yes, it IS mono
            pixelType = PT_MONO
    
        # Restore the saved pixel format
        params = [savedPixelFormat,]
        pixelink.PxLApi.setFeature(self.hCamera, pixelink.PxLApi.FeatureId.PIXEL_FORMAT, pixelink.PxLApi.FeatureFlags.MANUAL, params)
    
        return pixelType
    
if __name__ == "__main__":           

    cameras=pixelinkWrapper.PxLApi.getNumberCameras()  
    cameras=cameras[1]
    id=cameras[0].CameraSerialNum
    a=PIXELINK_CAM(id)
    a.open()
    a.setExposure(50)
    exp=a.getExposure()
    a.setGain(10)
    e=a.getGain()
    
    print(e)