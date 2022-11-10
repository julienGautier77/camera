# -*- coding: utf-8 -*-
#!usr/bin/python
"""
Created on Wed Nov  28 15:15:26 2018
Camera Imaging sources
Modified on Fri March  11:06:56 2020
@author: loa Julien Gautier

4 cameras in a main tab and a windows with 3 tab = 12 cameras control  
"""

import camera# class lecture 1 camera

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
        self.height=200
        self.setGeometry(self.left,self.top,self.width,self.height)
        self.setWindowTitle('Lolita CAMERAS' )
       
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        p = pathlib.Path(__file__)
        sepa=os.sep
        self.icon=str(p.parent) + sepa + 'icons' +sepa
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        pathVisu='C:/Users/loa/Desktop/Python/camera/confCamera.ini'
        self.cam0 = camera.CAMERA(cam="cam2",fft='off',meas='on',affLight=False,aff='left',separate=False,multi=False,confpath=pathVisu)  
        self.cam1 =camera.CAMERA(cam="cam3",fft='off',meas='on',affLight=False,aff='left',separate=False,multi=False,confpath=pathVisu)  
        self.cam2 = camera.CAMERA(cam="cam1",fft='off',meas='on',affLight=False,aff='left',separate=False,multi=False,confpath=pathVisu)  
        self.cam3 =camera.CAMERA(cam='firstPixelink',fft='off',meas='on',affLight=False,aff='left',separate=False,multi=False,confpath=pathVisu)  
   
        self.cam=[self.cam0,self.cam1,self.cam2,self.cam3]
        self.setup()
        self.setContentsMargins(1,1,1,1)
        self.actionButton()
        
    def setup(self):

        grid_layout = QGridLayout()
        grid_layout.setVerticalSpacing(1)
        grid_layout.setHorizontalSpacing(1)
        
        
        self.dock0=QDockWidget(self)
        self.dock0.setWindowTitle(self.cam0.ccdName)
        self.dock0.setWidget(self.cam0)
        self.dock0.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable)
#        self.dock0.setWindowState(Qt::WindowFullScreen)
        
        self.dock1=QDockWidget(self)
        self.dock1.setWindowTitle(self.cam1.ccdName)
        self.dock1.setWidget(self.cam1)
        self.dock1.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        
        self.dock2=QDockWidget(self)
        self.dock2.setWindowTitle(self.cam2.ccdName)
        self.dock2.setWidget(self.cam2)
        self.dock2.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        
        self.dock3=QDockWidget(self)
        self.dock3.setWindowTitle(self.cam3.ccdName)
        self.dock3.setWidget(self.cam3)
        self.dock3.setFeatures(QDockWidget.DockWidgetFeature.DockWidgetFloatable)
        
        grid_layout.addWidget(self.dock0, 0, 0)
        grid_layout.addWidget(self.dock1, 0, 1)
        grid_layout.addWidget(self.dock2, 1, 0)
        grid_layout.addWidget(self.dock3, 1,1)
        
        grid_layout.setContentsMargins(1,1,1,1)
        self.horizontalGroupBox=QGroupBox()
        self.horizontalGroupBox.setLayout(grid_layout)
        self.horizontalGroupBox.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Expanding)

        windowLayout=QVBoxLayout()
        windowLayout.addWidget(self.horizontalGroupBox)
        windowLayout.setContentsMargins(1,1,1,1)
        self.setLayout(windowLayout)


    def actionButton(self):
        self.dock0.topLevelChanged.connect(self.Dock0Changed)
        self.dock1.topLevelChanged.connect(self.Dock1Changed)
        self.dock2.topLevelChanged.connect(self.Dock2Changed)
        self.dock3.topLevelChanged.connect(self.Dock3Changed)
    
    def Dock0Changed(self):
        self.dock0.showMaximized()
    def Dock1Changed(self):
        self.dock1.showMaximized()
    def Dock2Changed(self):
        self.dock2.showMaximized()
    def Dock3Changed(self):
        self.dock3.showMaximized()
        
    def stopRun(self):
        self.cam0.cam.stopAcq()
        self.cam1.cam.stopAcq()
        self.cam2.cam.stopAcq()
        self.cam3.cam.stopAcq()

    def closeEvent(self,event):
        
        event.accept()

class MainWindows(QWidget):
    ## Main class 4 tabs :  cameras
    def __init__(self):
        super().__init__()

        self.left=100
        self.top=30
        self.width=1400
        self.height=1700
        self.setGeometry(self.left,self.top,self.width,self.height)
        self.setWindowTitle('Lolita Cameras' )
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        p = pathlib.Path(__file__)
        sepa=os.sep
        self.icon=str(p.parent) + sepa + 'icons' +sepa
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        
        self.setup()
        self.actionButton()
        
        
    def setup(self):
        
        self.layout=QVBoxLayout(self)
        self.layout.setContentsMargins(1,1,1,1)
        self.setContentsMargins(1,1,1,1)
        self.tabs=QTabWidget()
        self.tabs.setContentsMargins(1,1,1,1)
        pathVisu='C:/Users/loa/Desktop/Python/camera/confCamera.ini'
        self.tab0=camera.CAMERA(cam="cam2",fft='off',meas='on',affLight=False,aff='left',separate=False,multi=False,confpath=pathVisu)
        self.tab1=camera.CAMERA(cam="cam3",fft='off',meas='on',affLight=False,aff='left',separate=False,multi=False,confpath=pathVisu)  
        self.tab2=camera.CAMERA(cam="cam1",fft='off',meas='on',affLight=False,aff='left',separate=False,multi=False,confpath=pathVisu)  
        self.tab3=camera.CAMERA(cam='cam4',fft='off',meas='on',affLight=False,aff='left',separate=False,multi=False,confpath=pathVisu)  
        self.tab4=camera.CAMERA(cam='cam5',fft='off',meas='on',affLight=False,aff='left',separate=False,multi=False,confpath=pathVisu)
#        self.tab2=App4Cam()

        self.tabs.addTab(self.tab0,self.tab0.ccdName)
        self.tabs.addTab(self.tab1,self.tab1.ccdName)
        self.tabs.addTab(self.tab2,self.tab2.ccdName)
        self.tabs.addTab(self.tab3,self.tab3.ccdName)
        self.tabs.addTab(self.tab4,self.tab4.ccdName)
        

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
        


    def changeTab(self):
        print('tab change', 'tab is',self.tabs.currentIndex())
        # self.tab=[self.tab0,self.tab1]
        # self.tab0.stopRun()
        # self.tab1.stopRun()
        #self.tab2.stopRun()
        
        
    def actionButton(self):
        self.tabs.currentChanged.connect(self.changeTab)

    def closeEvent(self,event):
        # exit
        event.accept()





if __name__=='__main__':
    
    app=QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    multiTab=App4Cam()
    multiTab.show()
    sys.exit(app.exec_() )


