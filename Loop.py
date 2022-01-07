
# -*- coding: utf-8 -*-
"""
Created on Mon May  4 14:58:50 2020

@author: LOA
"""


from PyQt5.QtWidgets import QGridLayout,QHBoxLayout,QVBoxLayout,QWidget,QApplication,QGroupBox,QTabWidget,QMainWindow
from PyQt5.QtWidgets import QSizePolicy,QDockWidget
from pyqtgraph.Qt import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import sys,time
import pathlib,os
import qdarkstyle
from CameraMotorLoop import CAMERAMOTOR
from PyQt5 import QtGui 

class MULTICAM(QWidget):
    """
        Qwidget for opening many camera in a same window

    """
    def __init__(self,names=['cam2','cam5'],**kwds):
        super(MULTICAM, self).__init__()
        
        self.kwds=kwds
        self.numerOfCam=len(names)
        if self.numerOfCam%2 != 0: # if cam number is not odd we add one
            names.append('cam=None')
        self.numerOfCam=len(names)    
        
        self.names=names
        
        
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint) # set window on the top   
        
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        p = pathlib.Path(__file__)
        sepa=os.sep
        self.icon=str(p.parent) + sepa + 'icons' +sepa
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.cam=[]
        self.setWindowTitle('Focal Spot & P1')
        
           
        self.cam0=CAMERAMOTOR(cam=names[0],aff='right',separate=False,loop=True,nbLoop=1,**self.kwds)
        self.cam1=CAMERAMOTOR(cam=names[1],aff='right',separate=False,loop=True,**self.kwds)
               
        
        self.setup()
        
        self.actionButton()
        
    def setup(self):

       
        self.dock0=QDockWidget(self)
        self.dock0.setWindowTitle(self.cam0.ccdName)
        self.dock0.setStyleSheet("QDockWidget::title { color: purple;}")
        self.dock0.setWidget(self.cam0)
        self.dock0.setFeatures(QDockWidget.DockWidgetFloatable)
        
        self.dock1=QDockWidget(self)
        self.dock1.setWindowTitle(self.cam1.ccdName)
        self.dock1.setStyleSheet("QDockWidget::title { color: purple;}")
        self.dock1.setWidget(self.cam1)
        self.dock1.setFeatures(QDockWidget.DockWidgetFloatable)
        # self.dock0.setWindowState(Qt::WindowFullScreen)
        
        grid_layout = QGridLayout()
        grid_layout.setVerticalSpacing(1)
        grid_layout.setHorizontalSpacing(1)
        grid_layout.setContentsMargins(0,0,0,0)
        grid_layout.addWidget(self.dock0,0,0)
        grid_layout.addWidget(self.dock1,0,1)
        
        self.horizontalGroupBox=QGroupBox()
        self.horizontalGroupBox.setLayout(grid_layout)
        self.horizontalGroupBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        windowLayout=QVBoxLayout()
        windowLayout.addWidget(self.horizontalGroupBox)
#        windowLayout.addWidget(self.resetButton)
        windowLayout.setContentsMargins(1,1,1,1)
        
        self.setContentsMargins(1,1,1,1)
        self.setLayout(windowLayout)
        
    def actionButton(self):
        
        
        self.dock0.topLevelChanged.connect(lambda :self.DockChanged(self.dock0))
        self.dock1.topLevelChanged.connect(lambda :self.DockChanged(self.dock1))
        
    def DockChanged(self,dock):
        self.wait(0.01)
        # dock.setFloating(True)
        dock.showMaximized()
        
        # dock.showFullScreen()
        
    def wait(self,seconds):
        time_end=time.time()+seconds
        while time.time()<time_end:
            QtGui.QApplication.processEvents()    
        
    def stopRun(self):
       
        self.cam0.stopAcq()
        self.cam1.stopAcq()
        
    def closeAll(self):
        self.cam0.close()
        self.cam1.close()
            
    def closeEvent(self,event):
        self.stopRun()
        self.closeAll()
        # sys.exit(0)
        event.accept()
        
        

        


if __name__ == "__main__":       
    
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    p = pathlib.Path(__file__)
    sepa=os.sep
    pathVisu=str(p.parent) + sepa +'confCamera.ini'
    
    e = MULTICAM()#CAMERAMOTOR(cam="cam5",fft='off',meas='on',affLight=False,loop=True,separate=False)#,confpath=pathVisu)#,motLat='NF_Lat_P1',motorTypeName0='NewFocus', motVert='Lolita_P1_Vert',motorTypeName1='RSAI',loop=True)  
    e.show()
    # e2 = CAMERAMOTOR(cam="cam2",fft='off',meas='on',affLight=False,loop=True,separate=False)#,confpath=pathVisu)#,motLat='NF_Lat_P1',motorTypeName0='NewFocus', motVert='Lolita_P1_Vert',motorTypeName1='RSAI',loop=True)  
    # e2.show()#
    # x= CAMERA(cam="cam2",fft='off',meas='on',affLight=True,multi=False)  
    # x.show()
    appli.exec_()       
    
      