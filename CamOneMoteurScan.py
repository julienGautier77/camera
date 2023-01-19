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
from oneMotorSimple import ONEMOTOR
from scanMotor import SCAN
class CAMERAONEMOTOR(QWidget):

    def __init__(self,cam='choose',confFile='confCamera.ini',mot0="testMot1",motorType="test",parent=None):
        super(CAMERAONEMOTOR, self).__init__(parent)
        self.parent=parent
        self.CAM=CAMERA(cam=cam,configFile=confFile,separate=True)
         
        self.MOTWidget=ONEMOTOR(mot0=mot0,motorTypeName0=motorType,nomWin='motorSimple',unit=1,jogValue=100)
        self.MOTWidget.startThread2()
        
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




if __name__ == "__main__":
     appli = QApplication(sys.argv) 
     appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
     e = CAMERAONEMOTOR(cam='mako1')
     e.show()
     appli.exec_()