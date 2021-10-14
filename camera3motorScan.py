# -*- coding: utf-8 -*-
"""
Created on Mon Jul  6 13:56:12 2020

@author: LOA
"""



import qdarkstyle
import sys,time
from camera2 import CAMERA
from PyQt5.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QWidget,QToolButton
import pathlib,os
from pyqtgraph.Qt import QtCore
from PyQt5.QtGui import QIcon
from TiltGuiLight import TILTMOTORGUI
from oneMotorSimple import ONEMOTOR
from scanMotorCamera import SCAN

class CAMERAMOTOR(QWidget):
    
    def __init__(self,cam='choose',confFile='confCamera.ini',motLat='camLat',motorTypeName0='RSAI',motVert='camVert',motorTypeName1='RSAI',configMotorPath="./fichiersConfig/",**kwds):
        super(CAMERAMOTOR, self).__init__()
        self.cam=cam
        
        p = pathlib.Path(__file__)
        self.nbcam=cam
        self.kwds=kwds
        
        if "affLight" in kwds:
            self.light=kwds["affLight"]
        else:
            self.light=True
        if "multi" in kwds:
            self.multi=kwds["multi"]
        else:
            self.multi=False    
        # self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5()) # qdarkstyle :  black windows style
        
        if "confPath" in kwds:
            self.conf=QtCore.QSettings(kwds["confPath"], QtCore.QSettings.IniFormat)
        
        else : 
            self.conf=QtCore.QSettings(str(p.parent / confFile), QtCore.QSettings.IniFormat) # ini file 
        # self.confPath=str(p.parent / confFile) # ini file path
        
        if "conf" in kwds:
            self.conf=kwds["conf"]
        
        
        self.kwds["conf"]=self.conf
        sepa=os.sep
        
        self.configPathMotor=configMotorPath#str(p.parent)+"/fichiersConfig/"
        self.configMotName='configMoteurRSAI.ini'
        self.confMotorPath=self.configPathMotor+self.configMotName
        print(self.confMotorPath)
        self.confMot=QtCore.QSettings(str(p.parent / self.confMotorPath), QtCore.QSettings.IniFormat)
        
        
        self.icon=str(p.parent) + sepa+'icons'+sepa
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        
        self.setup()
        self.actionButton()

    def setup(self):
        
        
        
        hMainLayout=QHBoxLayout()
        
        self.camWidget=CAMERA(cam=self.cam,confMot=self.confMot,**self.kwds)
        
        motorTilt=TILTMOTORGUI(motLat='CAM_Lat',motorTypeName0='RSAI',motVert='CAM_Vert',motorTypeName1='RSAI',configMotorPath=self.configPathMotor)
        
        motorTilt.startThread2()
        
        self.motorFoc=ONEMOTOR(mot0='CAM_Foc',motorTypeName0='RSAI',nomWin='Foc',unit=1,jogValue=100)
        self.motorFoc.startThread2()
        
        self.scanWidget=SCAN(self,mot0='CAM_Foc',motorTypeName0='RSAI',confMot=self.confMot)
        self.scanWidget.acqMain.connect(self.camWidget.acquireOneImage)
        self.scanButton=QToolButton()
        self.scanButton.setText('Scan Foc')
        self.scanButton.setMinimumWidth(40)
        self.scanButton.setMinimumHeight(30)
        self.scanButton.setStyleSheet('background-color: gray ;border-color: gray')
        
        
        
        hMainLayout.addWidget(self.camWidget)
        
        vmainLayout=QVBoxLayout()
        vmainLayout.addStretch(2)
        vmainLayout.addWidget(motorTilt)
        vmainLayout.addWidget(self.motorFoc)
        vmainLayout.addWidget(self.scanButton)
        vmainLayout.addStretch(1)
        hMainLayout.addLayout(vmainLayout)
        
        self.setLayout(hMainLayout)
        self.setGeometry(100, 30, 1500, 800)
    
    def actionButton(self):
        self.scanButton.clicked.connect((lambda:self.open_widget(self.scanWidget)))
                                        
                               
    def open_widget(self,fene):
        """ ouverture widget suplementaire 
        """

        if fene.isWinOpen==False:
            fene.setup
            fene.isWinOpen=True
           
            fene.show()
        else:
            fene.activateWindow()
            fene.raise_()
            fene.showNormal()    


if __name__ == "__main__":       
    
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    p = pathlib.Path(__file__)
    sepa=os.sep
    pathVisu=str(p.parent) + sepa +'confCamera.ini'
    e = CAMERAMOTOR(cam='firstGuppy',affLight=False,multi=False,fft='off',confPath=pathVisu,separate=False)
    e.show()
   
    appli.exec_()       