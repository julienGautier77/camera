# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 10:59:16 2020

a Python user interface for camera allied vison ImgingSource Balser 


install aliiedVision SDK (https://www.alliedvision.com/en/products/software.html)

on conda prompt 
pip install pymba (https://github.com/morefigs/pymba.git )
pip install pypylon: https://github.com/basler/pypylon 
pip install qdarkstyle (https://github.com/ColinDuquesnoy/QDarkStyleSheet.git)
pip install pyqtgraph (https://github.com/pyqtgraph/pyqtgraph.git)
pip install visu
modify vimba.camera :acquire_frame(self) : self._single_frame.wait_for_capture(1000000)
and comment the line (?)(?)

@author: juliengautier
version : 2019.3
"""

__author__='julien Gautier'
__version__='2020.03'
version=__version__

from PyQt5.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QWidget,QPushButton
from PyQt5.QtWidgets import QComboBox,QSlider,QLabel,QSpinBox,QGridLayout,QToolButton,QMenu,QInputDialog
from pyqtgraph.Qt import QtCore
from PyQt5.QtCore import Qt,QSize
from PyQt5.QtGui import QIcon,QSizePolicy
import sys,time
import numpy as np
import pathlib,os
import qdarkstyle



class CAMERA(QWidget):
    
    def __init__(self,cam='camDefault',confFile='confCamera.ini',light=False):
        
        super(CAMERA, self).__init__()
        p = pathlib.Path(__file__)
        self.nbcam=cam
        self.light=light
        
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.conf=QtCore.QSettings(str(p.parent / confFile), QtCore.QSettings.IniFormat) # ini file 
        self.confPath=str(p.parent / confFile) # ini file path
        sepa=os.sep
        self.icon=str(p.parent) + sepa+'icons'+sepa
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        
        self.iconPlay=self.icon+'Play.png'
        self.iconSnap=self.icon+'Snap.png'
        self.iconStop=self.icon+'Stop.png'
        self.iconPlay=pathlib.Path(self.iconPlay)
        self.iconPlay=pathlib.PurePosixPath(self.iconPlay)
        self.iconStop=pathlib.Path(self.iconStop)
        self.iconStop=pathlib.PurePosixPath(self.iconStop)
        self.iconSnap=pathlib.Path(self.iconSnap)
        self.iconSnap=pathlib.PurePosixPath(self.iconSnap)
        
        
        self.nbShot=1
        self.ccdName=self.conf.value(self.nbcam+"/nameCDD")
        self.cameraType=self.conf.value(self.nbcam+"/camType")
        self.version=__version__
        
        
        
        if self.nbcam=="choose":
            try :
                from guppyCam import GUPPY
                self.CAM=GUPPY(cam=self.nbcam,conf=self.conf)
                self.itemsGuppy=self.CAM.camAvailable()
                print(self.itemsGuppy)
                lenGuppy=len(self.itemsGuppy)
                print(lenGuppy)
            except:
                print('No allied vision camera connected')
                pass
            try :
                from baslerCam import BASLER
                self.CAM=BASLER(cam=self.nbcam,conf=self.conf)
                self.itemsBasler=self.CAM.camAvailable()
                print(self.itemsBasler)
                lenBasler=len(self.itemsBasler)
                print(lenBasler)
            except:
                print('No Basler camera connected')
                pass   
            items=self.itemsGuppy+self.itemsBasler
            print(items)
            self.nbcam='camDefault'
            self.cameraType=" "
            self.ccdName=" "
            
        if self.cameraType=="guppy" :
            from guppyCam import GUPPY
            self.CAM=GUPPY(cam=self.nbcam,conf=self.conf)
            self.CAM.initCam()
            print(self.CAM.camParameter)
            self.isConnected=self.CAM.isConnected
        
        elif self.cameraType=="imagingSource":
            from ImgSourceCam2 import IMGSOURCE
            self.CAM=IMGSOURCE(cam=self.nbcam,conf=self.conf)
            print(self.CAM.camParameter)
            self.isConnected=self.CAM.isConnected
        elif self.cameraType=="basler":
            from baslerCam import BASLER
            self.CAM=BASLER(cam=self.nbcam,conf=self.conf)
            self.CAM.initCam()
            print(self.CAM.camParameter)
            self.isConnected=self.CAM.isConnected
        else :
            self.isConnected=False
                
        if self.light==False:
            try :
                from visu import SEE
                self.visualisation=SEE(confpath=self.confPath,name=self.nbcam) ## Widget for visualisation and tools  self.confVisu permet d'avoir plusieurs camera et donc plusieurs fichier ini de visualisation
       
            except:
                from visualLight import SEELIGHT
                self.visualisation=SEELIGHT(confpath=self.confPath,name=self.nbcam)
                print ('No visu module installed :see' )
        else :
            from visualLight import SEELIGHT
            self.visualisation=SEELIGHT(confpath=self.confPath,name=self.nbcam)
        
        self.setup()
         
        
        if self.isConnected==True: # if camera is connected we address min and max value  and value to the shutter and gain box
            
            self.hSliderShutter.setValue(self.CAM.camParameter["exposureTime"])
            self.shutterBox.setValue(self.CAM.camParameter["exposureTime"])
            self.hSliderShutter.setMinimum(self.CAM.camParameter["expMin"]+1)
            self.shutterBox.setMinimum(self.CAM.camParameter["expMin"]+1)
            
            if self.CAM.camParameter["expMax"] >1500: # we limit exposure time at 1500ms
                self.hSliderShutter.setMaximum(1500)
                self.shutterBox.setMaximum(1500)
            else :
                self.hSliderShutter.setMaximum(self.CAM.camParameter["expMax"])
                self.shutterBox.setMaximum(self.CAM.camParameter["expMax"])
            
            
            self.hSliderGain.setMinimum(self.CAM.camParameter["gainMin"])
            self.hSliderGain.setMaximum(self.CAM.camParameter["gainMax"])
            self.hSliderGain.setValue(self.CAM.camParameter["gain"])
            self.gainBox.setMinimum(self.CAM.camParameter["gainMin"])
            self.gainBox.setMaximum(self.CAM.camParameter["gainMax"])
            self.gainBox.setValue(self.CAM.camParameter["gain"])
            
            self.actionButton()
            
    def setup(self):  
        
            """ user interface definition: 
            """
            
            self.cameraWidget=QWidget()
            self.setWindowTitle('Visualization    '+ self.cameraType+"   " + self.ccdName+'       v.'+ self.version)
            
            
            self.vbox1=QVBoxLayout() 
            
            self.camName=QLabel(self.ccdName,self)
            self.camName.setAlignment(Qt.AlignCenter)
            
            self.camName.setStyleSheet('font :bold  14pt;color: white')
            self.vbox1.addWidget(self.camName)
            
            hbox1=QHBoxLayout() # horizontal layout pour run snap stop
            
            
            self.runButton=QToolButton(self)
            
            self.runButton.setMaximumWidth(40)
            self.runButton.setMinimumWidth(20)
            self.runButton.setMaximumHeight(60)
            self.runButton.setMinimumHeight(20)
            
            self.runButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: rgb(0, 0, 0,0) ;border-color: green;}""QToolButton:pressed{image: url(%s);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0)}""QToolButton:!hover{border-image: url(%s);background-color: rgb(0, 0, 0,0) ""QToolButton:hover{border-image: url(%s);background-color: blue "% (self.iconPlay,self.iconPlay,self.iconPlay,self.iconPlay) )
            
            
            self.snapButton=QToolButton(self)
            self.snapButton.setPopupMode(0)
            menu=QMenu()
            #menu.addAction('acq',self.oneImage)
            menu.addAction('set nb of shot',self.nbShotAction)
            self.snapButton.setMenu(menu)
            self.snapButton.setMaximumWidth(40)
            self.snapButton.setMinimumWidth(20)
            self.snapButton.setMaximumHeight(60)
            self.snapButton.setMinimumHeight(20)
            self.snapButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: rgb(0, 0, 0,0) ;border-color: green;}""QToolButton:pressed{image: url(%s);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0)}"% (self.iconSnap,self.iconSnap) )
            
            
            self.stopButton=QToolButton(self)
            
            self.stopButton.setMaximumWidth(40)
            self.stopButton.setMinimumWidth(20)
            self.stopButton.setMaximumHeight(60)
            self.stopButton.setMinimumHeight(20)
            self.stopButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0,0);}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0)}"% (self.iconStop,self.iconStop) )
            self.stopButton.setEnabled(False)
          
            
            hbox1.addWidget(self.runButton)
            hbox1.addWidget(self.snapButton)
            hbox1.addWidget(self.stopButton)
            
            
            self.vbox1.addLayout(hbox1)
            
            
            self.trigg=QComboBox()
            self.trigg.setMaximumWidth(80)
            self.trigg.addItem('OFF')
            self.trigg.addItem('ON')
            self.labelTrigger=QLabel('Trigger')
            self.labelTrigger.setMaximumWidth(50)
            self.itrig=self.trigg.currentIndex()
            hbox2=QHBoxLayout()
            hbox2.addWidget(self.labelTrigger)
            hbox2.addWidget(self.trigg)
            self.vbox1.addLayout(hbox2)
            
            self.labelExp=QLabel('Exposure (ms)')
            self.labelExp.setMaximumWidth(120)
            self.labelExp.setAlignment(Qt.AlignCenter)
            self.vbox1.addWidget(self.labelExp)
            self.hSliderShutter=QSlider(Qt.Horizontal)
            
            
           
            self.hSliderShutter.setMaximumWidth(80)
            self.shutterBox=QSpinBox()
            
            
            self.shutterBox.setMaximumWidth(60)
            
            hboxShutter=QHBoxLayout()
            hboxShutter.addWidget(self.hSliderShutter)
            hboxShutter.addWidget(self.shutterBox)
            self.vbox1.addLayout(hboxShutter)
            
            self.labelGain=QLabel('Gain')
            self.labelGain.setMaximumWidth(120)
            self.labelGain.setAlignment(Qt.AlignCenter)
            self.vbox1.addWidget(self.labelGain)
            hboxGain=QHBoxLayout()
            self.hSliderGain=QSlider(Qt.Horizontal)
            self.hSliderGain.setMaximumWidth(80)
            
            self.gainBox=QSpinBox()
            self.gainBox.setMaximumWidth(60)
            hboxGain.addWidget(self.hSliderGain)
            hboxGain.addWidget(self.gainBox)
            self.vbox1.addLayout(hboxGain)
            
            # self.TrigSoft=QPushButton('Trig Soft',self)
            # self.TrigSoft.setMaximumWidth(100)
            # self.vbox1.addWidget(self.TrigSoft)
            
            self.vbox1.addStretch(1)
            self.cameraWidget.setLayout(self.vbox1)
            self.cameraWidget.setMinimumSize(150,200)
            self.cameraWidget.setMaximumSize(200,900)
            
            hMainLayout=QHBoxLayout()
            
            if self.light==False:
                self.vbox2=QVBoxLayout() 
                self.vbox2.addWidget(self.visualisation)
                
                hMainLayout.addWidget(self.cameraWidget)
                hMainLayout.addLayout(self.vbox2)
                self.setLayout(hMainLayout)
            else:
                self.visualisation.hbox0.addWidget(self.cameraWidget)
                hMainLayout.addWidget(self.visualisation)
                self.setLayout(hMainLayout)
                
            self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint)
                
    def actionButton(self): 
        '''action when button are pressed
        '''
        self.runButton.clicked.connect(self.acquireMultiImage)
        self.snapButton.clicked.connect(self.acquireOneImage)
        self.stopButton.clicked.connect(self.stopAcq)      
        self.shutterBox.editingFinished.connect(self.shutter)    
        self.hSliderShutter.sliderReleased.connect(self.mSliderShutter)
        
        self.gainBox.editingFinished.connect(self.gain)    
        self.hSliderGain.sliderReleased.connect(self.mSliderGain)
        self.trigg.currentIndexChanged.connect(self.trigger)
        self.CAM.newData.connect(self.Display)
        # self.TrigSoft.clicked.connect(self.softTrigger)
    
    
    def oneImage(self):
        #self.nbShot=1
        self.acquireOneImage()
        
    def nbShotAction(self):
        '''
        number of snapShot
        '''
        nbShot, ok=QInputDialog.getInt(self,'Number of SnapShot ','Enter the number of snapShot ')
        if ok:
            self.nbShot=int(nbShot)
            if self.nbShot<=0:
               self.nbShot=1
            
    def Display(self,data):
        '''Display data with visualisation module
        
        '''
        self.data=data
        self.visualisation.newDataReceived(self.data)
        if self.CAM.camIsRunnig==False:
            self.stopAcq()
            
    def shutter (self):
        '''
        set exposure time 
        '''
        
        sh=self.shutterBox.value() # 
        self.hSliderShutter.setValue(sh) # set value of slider
        time.sleep(0.1)
        self.CAM.setExposure(sh) # Set shutter CCD in ms
        self.conf.setValue(self.nbcam+"/shutter",float(sh))
        self.conf.sync()
    
    def mSliderShutter(self): # for shutter slider 
        sh=self.hSliderShutter.value() 
        self.shutterBox.setValue(sh) # 
        self.CAM.setExposure(sh) # Set shutter CCD in ms
        self.conf.setValue(self.nbcam+"/shutter",float(sh))
        
    def gain (self):
        '''
        set gain
        '''
        g=self.gainBox.value() # 
        self.hSliderGain.setValue(g) # set slider value
        time.sleep(0.1)
        self.CAM.setGain(g)
        self.conf.setValue(self.nbcam+"/gain",float(g))
        self.conf.sync()
    
    def mSliderGain(self):
        '''
        set slider

        '''
        g=self.hSliderGain.value()
        self.gainBox.setValue(g) # set valeur de la box
        time.sleep(0.1)
        self.CAM.setGain(g)
        self.conf.setValue(self.nbcam+"/gain",float(g))
        self.conf.sync()
        
    def trigger(self):
        
        ''' select trigger mode
         trigger on
         trigger off
        '''
        self.itrig=self.trigg.currentIndex()
        
        if self.itrig==1:
            self.CAM.setTrigger("on")
        else :
            self.CAM.setTrigger("off")
            
    def acquireOneImage(self):
        
        
        self.runButton.setEnabled(False)
        self.runButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0,0);}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0)}"%(self.iconPlay,self.iconPlay))
        self.snapButton.setEnabled(False)
        self.snapButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0,0);}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0)}"%(self.iconSnap,self.iconSnap))
        self.stopButton.setEnabled(True)
        self.stopButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0,0);}""QToolButton:pressed{image: url(%s);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0)}"%(self.iconStop,self.iconStop) )
        self.trigg.setEnabled(False)
        
        
        
        self.CAM.startOneAcq(self.nbShot)
        
        
    def acquireMultiImage(self):    
        
        ''' 
            start the acquisition thread
        '''
        self.runButton.setEnabled(False)
        self.runButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0,0);}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0)}"%(self.iconPlay,self.iconPlay))
        self.snapButton.setEnabled(False)
        self.snapButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0,0);}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0)}"%(self.iconSnap,self.iconSnap))
        
        self.stopButton.setEnabled(True)
        self.stopButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0,0);}""QToolButton:pressed{image: url(%s);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0)}"%(self.iconStop,self.iconStop) )
        self.trigg.setEnabled(False)
        
        self.CAM.startAcq() # start mutli image acquisition thread 
        
    def stopAcq(self):
        
        '''Stop     acquisition
        '''
        self.CAM.stopAcq()
        
        self.runButton.setEnabled(True)
        self.runButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0,0);}""QToolButton:pressed{image: url(%s);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0)}"%(self.iconPlay,self.iconPlay))
        self.snapButton.setEnabled(True)
        self.snapButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0,0);}""QToolButton:pressed{image: url(%s);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0)}"%(self.iconSnap,self.iconSnap))
        
        self.stopButton.setEnabled(False)
        self.stopButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0,0);}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: rgb(0, 0, 0)}"%(self.iconStop,self.iconStop) )
        self.trigg.setEnabled(True)  
     

if __name__ == "__main__":       
    
    appli = QApplication(sys.argv) 
    # appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    pathVisu='C:/Users/loa/Desktop/Python/guppyCam/guppyCam/confVisuFootPrint.ini'
    e = CAMERA("choose")  
    e.show()
    appli.exec_()       