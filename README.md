# camera


Data acquistiion with different type of camera based on pyQtgraph
It use visu module  
  
  
Works with :

-Basler (pip install pypylon: https://github.com/basler/pypylon )  
-pixelink (pip install pixelinkWrapper: https://github.com/pixelink-support/pixelinkPythonWrapper.  
-The imaging source (https://github.com/TheImagingSource/IC-Imaging-Control-Samples).  
-Allied technology (pip install pymba https://github.com/morefigs/pymba.git).  





![captureTot](https://user-images.githubusercontent.com/29065484/82903692-9cd3ed00-9f61-11ea-98ff-865e0a1cf0ac.png)
## Requirements
*   python 3.x
*   Numpy
*   PyQt5
*   pyqtgraph (https://github.com/pyqtgraph/pyqtgraph.git) 
    * pip intall pyqtgraph
*   qdarkstyle (https://github.com/ColinDuquesnoy/QDarkStyleSheet.git)
    * pip install qdarkstyle. 
 * visu
   * pip install visu
  
  ## Usages   
  appli = QApplication(sys.argv)    
  appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())    
  #pathVisu='C:/Users/loa/Desktop/Python/guppyCam/guppyCam/confVisuFootPrint.ini'    
  e = CAMERA("cam='choose'",fft='off',meas='on',affLight=False)    
  e.show()   
  appli.exec_()    
  
  ## Parameters   
          
        cam : TYPE str, optional  
            DESCRIPTION.   
                cam='choose' : generate a input dialog box which the list of all the camera connected (allied,basler,imagingSource)   
                cam='cam1' : open the camera by the ID and type save in the confFile.ini  
                ncam='menu': generate a input dialog box with a menu with all the camera name present in the .ini file   
                cam='firstGuppy' open the first allied vision camera  
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
              
