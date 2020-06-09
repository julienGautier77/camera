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
from PyQt5 import QtGui 

class MULTICAM(QWidget):
    """
        Qwidget for opening many camera in a same window

    """
    def __init__(self,names=['cam1','cam2'],**kwds):
        super(MULTICAM, self).__init__()
        
        self.kwds=kwds
        self.numerOfCam=len(names)
        if self.numerOfCam%2is not 0: # if cam number is not odd we add one
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
        
        for cams in self.names:
            
            self.cam.append(camera.CAMERA(cam=cams,**self.kwds))
        
        
        self.setup()
        
        self.actionButton()
        
    def setup(self):

        grid_layout = QGridLayout()
        grid_layout.setVerticalSpacing(1)
        grid_layout.setHorizontalSpacing(1)
        self.dock=[]
        
        for i in range(0,self.numerOfCam):
            
            self.dock.append(QDockWidget(self))
            self.dock[i].setWindowTitle(self.cam[i].ccdName)
            self.dock[i].setStyleSheet("QDockWidget::title { color: purple;}")
            self.dock[i].setWidget(self.cam[i])
            self.dock[i].setFeatures(QDockWidget.DockWidgetFloatable)
        # self.dock0.setWindowState(Qt::WindowFullScreen)
        
        z=0
        for i in range(0,int(self.numerOfCam/2)):
            for j in range(0,int(self.numerOfCam/2)):
                if z<self.numerOfCam:
                    grid_layout.addWidget(self.dock[z], i, j)
                z+=1
       
        grid_layout.setContentsMargins(0,0,0,0)
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
        
        for dock in self.dock:
            dock.topLevelChanged.connect(lambda :self.DockChanged(dock))
        
        
    def DockChanged(self,dock):
        self.wait(0.01)
        dock.showMaximized()
        
        dock.showFullScreen()
        
    def wait(self,seconds):
        time_end=time.time()+seconds
        while time.time()<time_end:
            QtGui.QApplication.processEvents()    
        
    def stopRun(self):
        for cam in self.cam:
            cam.stopAcq()
        
    def closeAll(self):
        for cam in self.cam:
            cam.close()
    def closeEvent(self,event):
        self.stopRun()
        self.closeAll()
        # sys.exit(0)
        event.accept()
        
        
if __name__=='__main__':
    
    app=QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    multicam=MULTICAM(names=['cam1','firstPixelink','cam2','cam=None','cam=None'],affLight=True,multi=True) 
    multicam.show()
    sys.exit(app.exec_() )