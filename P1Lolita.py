# -*- coding: utf-8 -*-
"""
Created on Thu Apr 15 10:23:53 2021

@author: loa
"""

from PyQt5.QtWidgets import QApplication
import sys
import os
import pathlib
import qdarkstyle
from camera2 import CAMERA

if __name__ == "__main__":       
    
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    p = pathlib.Path(__file__)
    sepa=os.sep
    confCameraPath=str(p.parent) + sepa +'confCamera.ini'
    
  
    e = CAMERA(cam="cam5",fft='off',meas='on',affLight=False,aff='right',separate=False,multi=False)#,confPath=confCameraPath)  
    e.show()
   
    appli.exec_()      