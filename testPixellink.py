# -*- coding: utf-8 -*-
"""
Created on Mon May 18 17:52:05 2020

@author: loa
"""

import pixelinkWrapper as pixelink


class PIXELINK_CAM(object):
    
    def __init__(self,id):
        self.id=id
        
    def open(self):
        
        ret=pixelink.PxLApi.initialize(self.id)
        if pixelink.PxLApi.apiSuccess(ret[0]):
            self.hCamera=ret[1]
        else : 
            print ('no camera pixelink found') 
    
            
    
    def getExposureRange(self):
        ret = pixelink.PxLApi.getCameraFeatures(self.hCamera, pixelink.PxLApi.FeatureId.EXPOSURE)
        if not pixelink.PxLApi.apiSuccess(ret[0]):
            print ("  Could not getCameraFeatuers exposure, ret: %d!" % ret[0])
            return
        else:
            print (ret)
            cameraFeatures = ret[1]
            params = cameraFeatures.Features[0].Params
            minExp=format(params[0].fMaxValue)*1000
            maxExp=format(params[0].fMaxValue)*1000
            return [minExp,maxExp]
      
    def getExposure(self):
        ret = pixelink.PxLApi.getFeature(self.hCamera, pixelink.PxLApi.FeatureId.EXPOSURE)
        if not pixelink.PxLApi.apiSuccess(ret[0]):
            print ("  Could not getCameraFeatuers exposure, ret: %d!" % ret[0])
            return
        else:
            print (ret)
            param = ret[2]
            print('exposure (ms)',param[0]*1000)
            flags = ret[1]
            if flags & pixelink.PxLApi.FeatureFlags.AUTO:
                adjustmentType = "Continuous  "
            else:
                if flags & pixelink.PxLApi.FeatureFlags.ONEPUSH:
                    adjustmentType = "One-time    "
                else:
                    adjustmentType = "Manual      "
                print('flag exp',adjustmentType)
            return param[0]
        
    def setExposure(self,exp):
        exp=exp/1000 #♠plx is in second
        ret = pixelink.PxLApi.getFeature(self.hCamera, pixelink.PxLApi.FeatureId.EXPOSURE)
        params = ret[2]
        print('para',params,pixelink.PxLApi.apiSuccess(ret[0]),ret[1])
        params[0] = float(exp)
        ret = pixelink.PxLApi.setFeature(self.hCamera, pixelink.PxLApi.FeatureId.EXPOSURE, pixelink.PxLApi.FeatureFlags.MANUAL, params)
        print('exp',pixelink.PxLApi.apiSuccess(ret[0]),len(params),ret[0])
    
    
    def get_snapshot(self, imageFormat, fileName):
    
        assert 0 != self.hCamer 
        assert fileName
        
        # Determine the size of buffer we'll need to hold an image from the camera
        rawImageSize = determine_raw_image_size(self.hCamera)
        if 0 == rawImageSize:
            return pixelink.FAILURE
    
        # Create a buffer to hold the raw image
        rawImage = pixelink.create_string_buffer(rawImageSize)
    
        if 0 != len(rawImage):
            # Capture a raw image. The raw image buffer will contain image data on success. 
            ret = get_raw_image(self.hCamera, rawImage)
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
    
    def getPixelType():

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
        newPixelFormat = PxLApi.PixelFormat.MONO8
        params = [newPixelFormat,]
        ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.PIXEL_FORMAT, PxLApi.FeatureFlags.MANUAL, params)
        if not PxLApi.apiSuccess(ret[0]):
            # Nope, so is it color?
            newPixelFormat = PxLApi.PixelFormat.BAYER8
            params = [newPixelFormat,]
            ret = PxLApi.setFeature(hCamera, PxLApi.FeatureId.PIXEL_FORMAT, PxLApi.FeatureFlags.MANUAL, params)
            if PxLApi.apiSuccess(ret[0]):
                # Yes, it IS color
                pixelType = PT_COLOR
        else:
            # Yes, it IS mono
            pixelType = PT_MONO
    
        # Restore the saved pixel format
        params = [savedPixelFormat,]
        PxLApi.setFeature(hCamera, PxLApi.FeatureId.PIXEL_FORMAT, PxLApi.FeatureFlags.MANUAL, params)
    
        return pixelType
    
if __name__ == "__main__":           

    cameras=pixelink.PxLApi.getNumberCameras()  
    cameras=cameras[1]
    id=cameras[0].CameraSerialNum
    a=PIXELINK_CAM(id)
    a.open()
    a.setExposure(50)
    exp=a.getExposure()
    a.getExposureRange()
    print(exp)