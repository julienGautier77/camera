# -*- coding: utf-8 -*-
"""
Created on Mon May  4 14:58:50 2020

@author: LOA
"""


from PyQt5.QtWidgets import QGridLayout,QVBoxLayout,QWidget,QApplication,QGroupBox,QTabWidget,QMainWindow
from PyQt5.QtWidgets import QSizePolicy,QDockWidget
from pyqtgraph.Qt import QtCore
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon
import sys,time
import pathlib,os
import qdarkstyle
import camera

class MULTICAM(QWidget):
    def __init__(self,numberOfCam=2,names=['cam1','cam2'],**kwds):
        super(MULTICAM, self).__init__()
        
        self.kwds=kwds
        self.numerOfCam=numberOfCam
        self.names=names
        
        
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint) # set window on the top   
        
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        p = pathlib.Path(__file__)
        sepa=os.sep
        self.icon=str(p.parent) + sepa + 'icons' +sepa
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.cam=[]
        
        for cams in self.names:
            print(cams)
            self.cam.append(camera.CAMERA(cam=cams,**self.kwds))
        
        
        self.setup()
        
        #self.actionButton()
        
    def setup(self):

        grid_layout = QGridLayout()
        grid_layout.setVerticalSpacing(1)
        grid_layout.setHorizontalSpacing(1)
        
        
        self.dock0=QDockWidget(self)
        self.dock0.setWindowTitle(self.cam[0].ccdName)
        self.dock0.setStyleSheet("QDockWidget::title { color: purple;}")
        self.dock0.setWidget(self.cam[0])
        self.dock0.setFeatures(QDockWidget.DockWidgetFloatable)
#        self.dock0.setWindowState(Qt::WindowFullScreen)
        
        self.dock1=QDockWidget(self)
        self.dock1.setWindowTitle(self.cam[1].ccdName)
        self.dock1.setWidget(self.cam[1])
        self.dock1.setFeatures(QDockWidget.DockWidgetFloatable)
        
        
        
        grid_layout.addWidget(self.dock0, 0, 0)
        grid_layout.addWidget(self.dock1, 0, 1)
       
        grid_layout.setContentsMargins(0,0,0,0)
        self.horizontalGroupBox=QGroupBox()
        self.horizontalGroupBox.setLayout(grid_layout)
        self.horizontalGroupBox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        #self.setCentralWidget(self.horizontalGroupBox)
        windowLayout=QVBoxLayout()
        windowLayout.addWidget(self.horizontalGroupBox)
        windowLayout.setContentsMargins(1,1,1,1)
        self.setContentsMargins(1,1,1,1)
        self.setLayout(windowLayout)
        
    def actionButton(self):
        self.dock0.topLevelChanged.connect(self.Dock0Changed)
        self.dock1.topLevelChanged.connect(self.Dock1Changed)
        self.dock2.topLevelChanged.connect(self.Dock2Changed)
        self.dock3.topLevelChanged.connect(self.Dock3Changed)
        self.dock4.topLevelChanged.connect(self.Dock4Changed)
        self.dock5.topLevelChanged.connect(self.Dock5Changed)
        
    def Dock0Changed(self):
        self.dock0.showMaximized()
    def Dock0Maximisize(self):
        self.dock0.setFloating(True)
        self.dock0.showMaximized()
    def Dock1Changed(self):
        self.dock1.showMaximized()
    def Dock1Maximisize(self):
        self.dock1.setFloating(True)
        self.dock1.showMaximized()
    def Dock2Changed(self):
        self.dock2.showMaximized()
    def Dock2Maximisize(self):
        self.dock2.setFloating(True)
        self.dock2.showMaximized()
    def Dock3Changed(self):
        self.dock3.showMaximized()
    def Dock3Maximisize(self):
        self.dock3.setFloating(True)
        self.dock3.showMaximized()
    def Dock4Changed(self):
        self.dock4.showMaximized() 
    def Dock4Maximisize(self):
        self.dock4.setFloating(True)
        self.dock4.showMaximized()
    def Dock5Changed(self):
        self.dock5.showMaximized()
    def Dock5Maximisize(self):
        self.dock5.setFloating(True)
        self.dock5.showMaximized()
        
    def stopRun(self):
        self.cam0.cam.stopAcq()
        self.cam1.cam.stopAcq()
        self.cam2.cam.stopAcq()
        self.cam3.cam.stopAcq()
        self.cam4.cam.stopAcq()
        self.cam5.cam.stopAcq()
        
    def closeEvent(self,event):
        self.stopRun()
        sys.exit(0)
        event.accept()
        
        
if __name__=='__main__':
    
    app=QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    multicam=MULTICAM(numberOfCam=2,names=['cam1','cam0'],affLight=True,multi=True) 
    multicam.show()
    sys.exit(app.exec_() )