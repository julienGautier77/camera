# -*- coding: utf-8 -*-
"""
Created on Thu Apr 15 11:58:23 2021

@author: loa
"""


from PyQt5.QtWidgets import QApplication
import sys,os,pathlib
import qdarkstyle
from CameraMotorLoop import CAMERAMOTOR
if __name__ == "__main__":       
    
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    p = pathlib.Path(__file__)
    sepa=os.sep
    pathVisu=str(p.parent) + sepa +'confCamera.ini'
    
    e = CAMERAMOTOR(cam="cam2",fft='off',meas='on',affLight=False,loop=True,separate=True)  
    e.show()#
    # x= CAMERA(cam="cam2",fft='off',meas='on',affLight=True,multi=False)  
    # x.show()
    appli.exec_()       