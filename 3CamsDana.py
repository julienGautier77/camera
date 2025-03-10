# -*- coding: utf-8 -*-
#!usr/bin/python
"""
Created on Wed Nov  28 15:15:26 2018
Camera Imaging sources
Modified on Fri March  11:06:56 2020
@author: loa Julien Gautier

4 cameras imaging source
"""

import camera # class lecture 1 camera

import sys
from PyQt6.QtWidgets import QGridLayout,QVBoxLayout,QWidget,QApplication,QGroupBox,QTabWidget
from PyQt6.QtWidgets import QSizePolicy,QDockWidget
from PyQt6.QtGui import QIcon
import qdarkstyle # pip install qdakstyle https://github.com/ColinDuquesnoy/QDarkStyleSheet a faire dans anaconda prompt
import pathlib,os

class App4Cam(QWidget):
    #class 4 camera
    def __init__(self,camName0=None,camName1=None,camName2=None,camName3=None):
        super().__init__()
        self.left=100
        self.top=30
        self.width=1000
        self.height=800
        self.setGeometry(self.left,self.top,self.width,self.height)
        self.setWindowTitle('Dana Turning box CAMERAS' )
       
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())
        p = pathlib.Path(__file__)
        sepa=os.sep
        self.icon=str(p.parent) + sepa + 'icons' +sepa
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        pathVisu='C:/Users/UPX/Desktop/python/camera/confCamera.ini'
        # self.cam0 = camera2.CAMERA(cam="cam2",fft='off',meas='on',affLight=False,aff='left',separate=False,multi=False,confpath=pathVisu)  
        self.cam1 =camera.CAMERA(cam="cam1",fft='off',meas='on',affLight=True,aff='left',separate=False,multi=False,confpath=pathVisu)  
        self.cam2 = camera.CAMERA(cam="cam2",fft='off',meas='on',affLight=True,aff='left',separate=False,multi=False,confpath=pathVisu)  
        self.cam3 =camera.CAMERA(cam='cam3',fft='off',meas='on',affLight=True,aff='left',separate=False,multi=False,confpath=pathVisu)  
   
        self.cam=[self.cam1,self.cam2,self.cam3]
        self.setup()
        self.setContentsMargins(1,1,1,1)
        self.actionButton()
        
    def setup(self):

        grid_layout = QGridLayout()
        grid_layout.setVerticalSpacing(1)
        grid_layout.setHorizontalSpacing(1)
        
        
        # self.dock0=QDockWidget(self)
        # self.dock0.setWindowTitle(self.cam0.ccdName)
        # self.dock0.setWidget(self.cam0)
        # self.dock0.setFeatures(QDockWidget.DockWidgetFloatable)
#        self.dock0.setWindowState(Qt::WindowFullScreen)
        self.tabs=QTabWidget()
        
        self.tabs.setContentsMargins(1,1,1,1)
        
        self.dock1=QDockWidget(self)
        # self.dock1.setWindowTitle(self.cam1.ccdName)
        self.dock1.setWidget(self.cam1)
        #self.dock1.setFeatures(QDockWidget.DocWidgetFeature.DockWidgetFloatable)
        self.dock1.setTitleBarWidget(QWidget())
        self.dock2=QDockWidget(self)
        self.dock2.setWindowTitle(self.cam2.ccdName)
        self.dock2.setWidget(self.cam2)
        #self.dock2.setFeatures(QDockWidget.DockWidgetFloatable)
        self.dock2.setTitleBarWidget(QWidget())
        self.dock3=QDockWidget(self)
        self.dock3.setWindowTitle(self.cam3.ccdName)
        self.dock3.setWidget(self.cam3)
        #self.dock3.setFeatures(QDockWidget.DockWidgetFloatable)
        self.dock3.setTitleBarWidget(QWidget())
        
        self.tabs.addTab(self.dock1,self.cam1.ccdName)
        self.tabs.addTab(self.dock2,self.cam2.ccdName)
        self.tabs.addTab(self.dock3,self.cam3.ccdName)
       
        self.windowLayout=QVBoxLayout()
        
        self.windowLayout.addWidget(self.tabs)
        self.setLayout(self.windowLayout)
        
    def actionButton(self):
        # self.dock0.topLevelChanged.connect(self.Dock0Changed)
        self.dock1.topLevelChanged.connect(self.Dock1Changed)
        self.dock2.topLevelChanged.connect(self.Dock2Changed)
        self.dock3.topLevelChanged.connect(self.Dock3Changed)
        self.tabs.currentChanged.connect(self.changeTab)
    # def Dock0Changed(self):
    #     self.dock0.showMaximized()
    def Dock1Changed(self):
        self.dock1.showMaximized()
    def Dock2Changed(self):
        self.dock2.showMaximized()
    def Dock3Changed(self):
        self.dock3.showMaximized()
        
    def stopRun(self):
        
        self.cam1.cam.stopAcq()
        self.cam2.cam.stopAcq()
        self.cam3.cam.stopAcq()
    def changeTab(self):
        # print('tab change', 'tab is',self.tabs.currentIndex())
        self.cam1.stopAcq()
        self.cam2.stopAcq()
        self.cam3.stopAcq()
        
        
    
    def closeEvent(self,event):
        event.accept()




if __name__=='__main__':
    
    app=QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())
    multiTab=App4Cam()
    multiTab.show()
    sys.exit(app.exec_() )


