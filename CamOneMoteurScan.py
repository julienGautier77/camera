# -*- coding: utf-8 -*-
"""
Created on 2023/01/19 
Scan one motor with camera acquisition

@author: juliengautier
version : 2023.01
"""

from PyQt6.QtWidgets import QApplication,QWidget,QVBoxLayout,QDockWidget,QToolButton
from PyQt6.QtCore import Qt
from camera import CAMERA
import sys
import qdarkstyle 
from PyQt6 import QtCore
from PyQt6.QtGui import QIcon
from oneMotorSimple import ONEMOTOR
from scanMotor import SCAN
import os
import pathlib
class CAMERAONEMOTOR(QWidget):
    signalAcqDoneONEMOTOR=QtCore.pyqtSignal(object)

    def __init__(self,cam='choose',confFile='confCamera.ini',mot0="mot1",motorType="SmartAct",parent=None):
        """
        Parameters
        cam:name of the camera 
        configFile= ini file of the camera
        mot0= name of the motor to control
        motorType : type of motor ('RSAI','SmartAct','A2V','NewFocus','newport','Servo','Arduino','Apt','test')

        
        """

        super(CAMERAONEMOTOR, self).__init__(parent)
        self.parent=parent
        self.CAM=CAMERA(cam=cam,configFile=confFile,separate=True)
         
        self.MOTWidget=ONEMOTOR(mot0=mot0,motorTypeName0=motorType,nomWin='motorSimple',unit=1,jogValue=100)
        self.MOTWidget.startThread2()
        sepa=os.sep
        p = pathlib.Path(__file__)
        self.icon=str(p.parent) + sepa+'icons'+sepa
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.scanWidget=SCAN(MOT=self.MOTWidget.MOT,motor=self.MOTWidget.motor,configMotName=self.MOTWidget.configMotName,parent=self)
        self.setup()
        self.actButton()


    def setup(self):
        vbox=QVBoxLayout()
        self.dockMotor=QDockWidget(self)
        self.dockMotor.setTitleBarWidget(QWidget())
        self.dockMotor.setWidget(self.MOTWidget)

        self.CAM.visualisation.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,self.dockMotor)
        self.buttonScan=QToolButton()
        self.buttonScan.setText("Scan")
        self.buttonScan.setMinimumWidth(30)
        self.buttonScan.setMinimumHeight(30)
        self.buttonScan.setMaximumWidth(30)
        self.buttonScan.setMaximumHeight(30)
        self.MOTWidget.hbox3.addWidget(self.buttonScan)
        vbox.addWidget(self.CAM)
        self.setLayout(vbox)

    def actButton(self):
        self.buttonScan.clicked.connect(lambda:self.open_widget(self.scanWidget) )
        self.scanWidget.acqMain.connect(self.acquireScan)
        #self.CAM.signalAcqDone.connect(self.CamOneAcqDone)

    # def CamOneAcqDone(self):
    #     self.signalAcqDoneONEMOTOR.emit(True)

    def acquireScan(self):
        self.CAM.acquireOneImage()


    def open_widget(self,fene):
        
        """ open new widget 
        """
        
        if fene.isWinOpen==False:
            #New widget"
            fene.show()
            fene.isWinOpen=True
    
        else:
            #fene.activateWindow()
            fene.raise_()
            fene.showNormal()

    def closeEvent(self,event):
        ''' closing window event (cross button)
        '''
        self.MOTWidget.fini()
        self.MOTWidget.stopConnexion()
        if self.scanWidget.isWinOpen==True:
            self.scanWidget.close()


if __name__ == "__main__":
     appli = QApplication(sys.argv) 
     appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
     e = CAMERAONEMOTOR(cam='testCam')
     e.show()
     appli.exec_()