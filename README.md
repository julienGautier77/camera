# camera


Data acquistion with different type of camera based on pyQtgraph  
It use visu module to display the data received  
  
  
Works with :

-Basler (pip install pypylon: https://github.com/basler/pypylon )  
-Pixelink (pip install pixelinkWrapper: https://github.com/pixelink-support/pixelinkPythonWrapper.  
-The imaging source (https://github.com/TheImagingSource/IC-Imaging-Control-Samples).  
-Allied technology (pip install pymba https://github.com/morefigs/pymba.git).  or pip instal git+https://github.com/alliedvision/VimbaPython (official library works with vimba 2.5.)
if you use pymba you have to cameraType="guppy" if you use vimba cameraType==allied"
-IDS camera 

  
  
  
  
![captureTot](https://user-images.githubusercontent.com/29065484/82903692-9cd3ed00-9f61-11ea-98ff-865e0a1cf0ac.png)
## Requirements
*   python 3.x
*   Numpy
*   PyQt5
*   pyqtgraph (https://github.com/pyqtgraph/pyqtgraph.git) 
    * pip intall pyqtgraph=O.11.1
*   qdarkstyle (https://github.com/ColinDuquesnoy/QDarkStyleSheet.git)
    * pip install qdarkstyle. 
 * visu
   * pip install git+https://github.com/julieGautier77/visu
  
  ## Usages   
  appli = QApplication(sys.argv)    
  appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())    
  #pathVisu='C:/Users/loa/Desktop/Python/guppyCam/guppyCam/confVisuFootPrint.ini'    
  e = CAMERA("cam='FirstALlied'",fft='off',meas='on',affLight=False)    
  e.show()   
  appli.exec_()    
  
  ## Parameters   
          
        cam : TYPE str, optional  
            DESCRIPTION.   
                cam='choose' : generate a input dialog box which the list of all the camera connected (allied,basler,imagingSource)   
                cam='cam1' : open the camera by the ID and type save in the confFile.ini  
                ncam='menu': generate a input dialog box with a menu with all the camera name present in the .ini file   
                cam='firstAllied' open the first allied vision camera  
                cam='firstBasler' open the first Basler camera  
                cam='firstImgSource' open the first ImagingSource camera  
            The default is 'choose'.  
        confFile : TYPE str, optional  
            DESCRIPTION.  
                confFile= path to file.initr  
                The default is 'confCamera.ini'.  
        **kwds:  
            affLight : TYPE boolean, optional  
                DESCRIPTION.  
                    affLight=False all the option are show for the visualisation  
                    affLight= True only few option (save  open cross)  
                    The default is True.  
            multi add time sleep to access QApplication.processEvents()   
            + all kwds of VISU class  
              
