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
import camera2 
from PyQt5 import QtGui 

class MULTICAM(QWidget):
    """
        Qwidget for opening many camera in a same window

    """
    def __init__(self,names=['cam1','cam2'],**kwds):
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
        i=1
        for cams in self.names:
            if i%2!= 0:
                self.cam.append(camera2.CAMERA(cam=cams,aff='left',**self.kwds))
            else :
                self.cam.append(camera2.CAMERA(cam=cams,aff='right',**self.kwds))
            i+=1
        
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
        dock.setFloating(True)
        dock.showMaximized()
        print('ici')
        # dock.showFullScreen()
        
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
        
        
class MainWindows(QWidget):
    ## Main class 3 tabs : 12 cameras
    def __init__(self):
        super().__init__()

        self.left=100
        self.top=30
        self.width=1200
        self.height=300
        self.setGeometry(self.left,self.top,self.width,self.height)
        self.setWindowTitle('Lolita Alignment' )
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
        self.tab0=MULTICAM(names=['cam0','cam1','cam2','cam3'])
        self.tab1=MULTICAM(names=['cam6','cam7','cam4','cam5'])
#        self.tab2=App4Cam()

        self.tabs.addTab(self.tab0,'   Lolita centers     ')
        self.tabs.addTab(self.tab1,'    P3 & misc.    ')
        #self.tabs.addTab(self.tab2,'    P3    ')

        self.layout.addWidget(self.tabs)
        self.setLayout(self.layout)
        


    def changeTab(self):
#        print('tab change', 'tab is',self.tabs.currentIndex())
        self.tab=[self.tab0,self.tab1]
        self.tab0.stopRun()
        self.tab1.stopRun()
        #self.tab2.stopRun()
        
        
    def actionButton(self):
        self.tabs.currentChanged.connect(self.changeTab)
        
    def closeEvent(self,event):
        
        event.accept()
        
        
        

if __name__=='__main__':
    
    app=QApplication(sys.argv)
    app.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    multiTab=MainWindows()
    multiTab.show()
    sys.exit(app.exec_() )