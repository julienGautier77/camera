# -*- coding: utf-8 -*-
"""
Created on Tue Mar 24 10:59:16 2020

a Python user interface for camera allied vison, ImgingSource, Balser 


install aliiedVision SDK (https://www.alliedvision.com/en/products/software.html)

on conda prompt :
    for allied vision camera :
pip install pymba (https://github.com/morefigs/pymba.git ) 
#  Encrease timeout :
  #change in File "C:\ProgramData\Anaconda3\lib\site-packages\pymba\camera.py
  #  def acquire_frame(self, timeout_ms: Optional[int] = 200000000) -> Frame: 

    for Basler camera :
pip install pypylon: https://github.com/basler/pypylon 

pip install qdarkstyle (https://github.com/ColinDuquesnoy/QDarkStyleSheet.git)
pip install pyqtgraph (https://github.com/pyqtgraph/pyqtgraph.git)
Change in pyqtgraph in ImgageItem.py line 462 :
    if bins == 'auto':
            if stepData.dtype.kind in "ui":
                mn = stepData.min()
                mx = stepData.max()
                if mn==mx:                # add to avoid / by zero !!!
                    mx=mx+0.01
                step = np.ceil((mx-mn) / 500.)
                bins = np.arange(mn, mx+1.01*step, step, dtype=np.int)
                if len(bins) == 0:
                    bins = [mn, mx]
            else:
                bins = 500



pip install visu




@author: juliengautier
version : 2019.4
"""

__author__='julien Gautier'
__version__='2020.04'


from PyQt5.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QWidget,QPushButton
from PyQt5.QtWidgets import QComboBox,QSlider,QLabel,QSpinBox,QToolButton,QMenu,QInputDialog,QDockWidget,QCheckBox
from pyqtgraph.Qt import QtCore
from PyQt5.QtCore import Qt,pyqtSlot
from PyQt5.QtGui import QIcon
from PyQt5 import QtGui 
import sys,time
import pathlib,os
import qdarkstyle

from TiltGuiLight import TILTMOTORGUI

import __init__

import pyqtgraph as pg

import numpy as np

# from pypylon import pylon
from scipy.ndimage.filters import gaussian_filter
from scipy import ndimage

import pylab

__version__=__init__.__version__
version=str(__version__)

class CAMERAMOTOR(QWidget):
    datareceived=QtCore.pyqtSignal(bool) # signal emited when receive image
    
    def __init__(self,cam=None,confFile='confCamera.ini',**kwds):
        '''
        Parameters
        ----------
        cam : TYPE str, optional
            DESCRIPTION. 
                cam='choose' : generate a input dialog box which the list of all the camera connected (allied,basler,imagingSource) 
                cam='cam1' : open the camera by the ID and type save in the confFile.ini 
                ncam='menu': generate a input dialog box with a menu with all the camera name present in the .ini file
                cam='firstGuppy' open the first allied vision camera
                cam='firstBasler' open the first Basler camera
                cam='firstImgSource' open the first ImagingSource camera
            The default is 'choose'.
        confFile : TYPE str, optional
            DESCRIPTION. 
                confFile= path to file.initr
                The default is 'confCamera.ini'.
        **kwds:
            affLight : TYPE boolean, optional
                DESCRIPTION.
                    affLight=False all the option are show for the visualisation
                    affLight= True only few option (save  open cross)
                    The default is True.
            multi add time sleep to access QApplication.processEvents() 
            + all kwds of VISU class
            
        '''
        
        
        super(CAMERAMOTOR, self).__init__()
        
        p = pathlib.Path(__file__)
        self.nbcam=cam
        self.maxMvtY=500
        self.maxMvtX=500
        self.nbImageMax=3
        self.nbImage=0
        self.kwds=kwds
        
        if "confPath" in kwds:
            self.conf=QtCore.QSettings(kwds["confPath"], QtCore.QSettings.IniFormat)
        
        else : 
            print('path',str(p.parent / confFile))
            self.conf=QtCore.QSettings(str(p.parent / confFile), QtCore.QSettings.IniFormat) # ini file 
        # self.confPath=str(p.parent / confFile) # ini file path
        
        
        if "conf" in kwds:
            self.conf=kwds["conf"]
        
        
        self.kwds["conf"]=self.conf
        
        
        if "affLight" in kwds:
            self.light=kwds["affLight"]
        else:
            self.light=True
        if "multi" in kwds:
            self.multi=kwds["multi"]
        else:
            self.multi=False 
        
        if "separate" in kwds:
            self.separate=kwds["separate"]
        else: 
            self.separate=True
            
        if "aff" in kwds: #  affi of Visu
            self.aff=kwds["aff"]
        else: 
            self.aff="right"
            
        if "loop" in kwds: #  affi of Visu
            self.loop=kwds["loop"]
            self.kwds["roiCross"]=True # set circle on visu cross
        else: 
            self.loop=False   
            
        self.openCam()
        
       
        # Si les moteurs ne sont pas renseignés on prend ceux renseigné dans le fichier ini de la cam
        if "motLat" in kwds:
            self.motLat=kwds["motLat"]
        else :
            self.motLat=(self.conf.value(self.nbcam+"/motLat"))
        if "motVert"in kwds:
            self.motVert=kwds["motVert"]
        else:
            self.motVert=(self.conf.value(self.nbcam+"/motVert")   ) 
        if "motorTypeName0" in kwds:
            self.motorTypeName0=kwds["motorTypeName0"]
        else: 
            self.motorTypeName0=(self.conf.value(self.nbcam+"/motorTypeName0"))
        if "motorTypeName1" in kwds:
            self.motorTypeName1=kwds["motorTypeName1"]
        else:
            self.motorTypeName1=(self.conf.value(self.nbcam+"/motorTypeName1"))
        
        
        self.motor=TILTMOTORGUI(motLat=self.motLat,motorTypeName0=self.motorTypeName0, motVert=self.motVert,motorTypeName1=self.motorTypeName1,nomWin='',nomTilt='',unit=1,jogValue=100)
        self.motor.startThread2()
        
        
        # self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5()) # qdarkstyle :  black windows style
        
        
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
        self.isConnected=False
        self.version=str(__version__)
        self.pasY=float(self.conf.value(self.nbcam+"/pasY"))
        self.pasX=float(self.conf.value(self.nbcam+"/pasX"))
        
        
        self.kwds["name"]=self.nbcam
        self.setup()
        self.setCamPara()
        #self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.xr=int(self.conf.value(self.nbcam+"/xc"))
        self.yr=int(self.conf.value(self.nbcam+"/yc"))
        self.xlim=int(self.conf.value(self.nbcam+"/rx"))/2
        self.ylim=int(self.conf.value(self.nbcam+"/ry"))/2
        self.Xec=[]
        self.Yec=[]
        self.vLine = pg.InfiniteLine(angle=90, movable=True,pen='b')
        self.hLine = pg.InfiniteLine(angle=0, movable=True,pen='b')
        
    def openID(self):
        '''
        open a camera by id camera typ and ID must be known and saved in the ini file 

        '''
        self.ccdName=self.conf.value(self.nbcam+"/nameCDD")
        self.cameraType=self.conf.value(self.nbcam+"/camType")
        self.camID=self.conf.value(self.nbcam+"/camId")
        
        if self.cameraType=="guppy" :
            try :
                import guppyCam
                self.CAM=guppyCam.GUPPY(cam=self.nbcam,conf=self.conf)
                self.CAM.openCamByID(self.camID)
                self.isConnected=self.CAM.isConnected
            except :
                print("no allied vision camera detected or vimba is not installed")
                pass
          
        elif self.cameraType=="basler":
            try:
                import baslerCam
                self.CAM=baslerCam.BASLER(cam=self.nbcam,conf=self.conf,**self.kwds)
                self.CAM.openCamByID(self.camID)
                self.isConnected=self.CAM.isConnected
            except:
                print("no basler camera detected or pypylon is not installed")
                pass
        
        elif self.cameraType=="imgSource":
            
            try :
                import ImgSourceCamCallBack
                self.CAM=ImgSourceCamCallBack.IMGSOURCE(cam=self.nbcam,conf=self.conf,**self.kwds)
                self.CAM.openCamByID(self.camID)
                # print('openID',self.camID)
                self.isConnected=self.CAM.isConnected
            except:
                print("no imaging source camera detected or Tisgrabber is not installed")
                pass
        elif self.cameraType=="pixelink":
            
            try :
                import pixelinkCam
                
                self.CAM=pixelinkCam.PIXELINK(cam=self.nbcam,conf=self.conf,**self.kwds)
                
                self.CAM.openCamByID(self.camID)
                
                self.isConnected=self.CAM.isConnected
            except:
                print("no pixellink camera detected or pillelink dll  is not installed")
                pass
        else:
            print('no camera')
            self.isConnected=False
            self.ccdName="no camera"
            self.cameraType=""
            self.camID=""
            self.nbcam='camDefault'
            
    def openCam(self):
        '''open a camera with different way  
        '''
        
        if self.nbcam=="choose": # create menu widget with all camera present 
        
            self.nbcam='camDefault'
            try :
                import guppyCam 
                self.itemsGuppy=guppyCam.camAvailable()
                # print(self.itemsGuppy)
                self.lenGuppy=len(self.itemsGuppy)
                
            except:
                print('No allied vision camera connected')
                self.itemsGuppy=[]
                self.lenGuppy=0
                pass
            try :
                import baslerCam
                self.itemsBasler=baslerCam.camAvailable()
                self.lenBasler=len(self.itemsBasler)
                
            except:
                print('No Basler camera connected')
                self.itemsBasler=[]
                self.lenBasler=0
                pass 
            
            try :
                import ImgSourceCamCallBack
                self.itemsImgSource=ImgSourceCamCallBack.camAvailable()
                self.lenImgSource=len(self.itemsImgSource)
                
            except:
                print('No ImagingSource camera connected')
                self.itemsImgSource=[]
                self.lenImgSource=0
                pass 
            
            try :
                import pixelinkCam
                self.itemsPixelink=pixelinkCam.PIXELINK.camAvailable()
                self.lenImgPixelink=len(self.itemsPixelink)
                
            except:
                print('No pixelink camera connected')
                self.itemsPixelink=[]
                self.lenPixelink=0
                pass 
            
            items=self.itemsGuppy+list(self.itemsBasler)+self.itemsImgSource+self.itemsPixelink
            
            item, ok = QInputDialog.getItem(self, "Select a camera","List of avaible camera", items, 0, False,flags=QtCore.Qt.WindowStaysOnTopHint)
            
            if ok and item:
                
                indexItem = items.index(item)
            
                if indexItem<self.lenGuppy:
                    indexItem=indexItem
                    self.cameraType="guppy"
                    self.camID=guppyCam.getCamID(indexItem)
                    
                    self.CAM=guppyCam.GUPPY(cam=self.nbcam,**self.kwds)
                    self.CAM.openCamByID(self.camID)
                    self.isConnected=self.CAM.isConnected
                    self.ccdName=self.camID
                elif indexItem>=self.lenGuppy  and indexItem<self.lenBasler+self.lenGuppy:
                    indexItem=indexItem-self.lenGuppy
                    self.cameraType="basler"
                    self.camID=baslerCam.getCamID(indexItem)
                    self.CAM=baslerCam.BASLER(cam=self.nbcam,**self.kwds)
                    self.CAM.openCamByID(self.camID)
                    self.isConnected=self.CAM.isConnected
                    self.ccdName=self.camID
                    
                elif indexItem>=self.lenBasler+self.lenGuppy  and indexItem<self.lenBasler+self.lenGuppy+self.lenImgSource:
                    indexItem=indexItem-self.lenGuppy-self.lenBasler
                    self.cameraType="imgSource"
                    self.camID=ImgSourceCamCallBack.getCamID(indexItem)
                    self.camID=self.camID.decode()
                    self.CAM=ImgSourceCamCallBack.IMGSOURCE(cam=self.nbcam,**self.kwds)
                    self.CAM.openCamByID(self.camID)
                    self.isConnected=self.CAM.isConnected
                    self.ccdName=self.camID
                    
                elif indexItem>=self.lenBasler+self.lenGuppy+ self.lenImgSource and indexItem<self.lenBasler+self.lenGuppy+self.lenImgSource+self.lenPixelink:
                    indexItem=indexItem-self.lenGuppy-self.lenBasler-self.lenImgSource
                    self.cameraType="pixelink"
                    self.camID=pixelinkCam.getCamID(indexItem)
                    
                    self.CAM=pixelinkCam.PIXELINK(cam=self.nbcam,**self.kwds)
                    self.CAM.openCamByID(self.camID)
                    self.isConnected=self.CAM.isConnected
                    self.ccdName=self.camID    
                
                else:
                     self.isconnected=False
                     print('No camera choosen')
                     self.ccdName="no camera"
                     self.nbcam='camDefault'
            else :
                self.isconnected=False
                print('No camera choosen')
                self.ccdName="no camera"
                self.cameraType=""
                self.camID=""
                self.nbcam='camDefault'
            
        elif  self.nbcam==None:
            self.isconnected=False
            print('No camera')
            self.ccdName="no camera"
            self.cameraType=""
            self.camID=""
            self.nbcam='camDefault'
             
        elif self.nbcam=="firstGuppy": # open the first guppy cam in the list
            self.nbcam='camDefault'
            self.cameraType="guppy"
            self.ccdName='First guppy Cam'
            import guppyCam 
            self.CAM=guppyCam.GUPPY(cam=self.nbcam,conf=self.conf)
            self.CAM.openFirstCam()
            self.isConnected=self.CAM.isConnected
            
        elif self.nbcam=="firstBasler": # open the first basler cam in the list
            self.ccdName='First basler Cam'
            self.nbcam='camDefault'
            self.cameraType="basler"
            import baslerCam 
            self.CAM=baslerCam.BASLER(cam=self.nbcam,conf=self.conf,**self.kwds)
            self.CAM.openFirstCam()
            self.isConnected=self.CAM.isConnected   
            
        elif self.nbcam=="firstImgSource": # open the first imgSource cam in the list
            self.ccdName='First ImSource Cam'
            self.nbcam='camDefault'
            self.cameraType="imgSource"
            import ImgSourceCamCallBack 
            self.CAM=ImgSourceCamCallBack.IMGSOURCE(cam=self.nbcam,conf=self.conf,**self.kwds)
            self.CAM.openFirstCam()
            self.isConnected=self.CAM.isConnected 
            
        elif self.nbcam=="firstPixelink": # open the first pixelink cam in the list
            self.ccdName='First Pixelink Cam'
            self.nbcam='camDefault'
            self.cameraType="pixelink"
            import pixelinkCam
            self.CAM=pixelinkCam.PIXELINK(cam=self.nbcam,conf=self.conf,**self.kwds)
            self.CAM.openFirstCam()
            self.isConnected=self.CAM.isConnected      
            
        elif self.nbcam=='menu': # Qdialog with a menu with all the camera name present in the inifile
            self.groupsName=[]
            self.groups=self.conf.childGroups()
            for groups in self.groups:
                self.groupsName.append(self.conf.value(groups+"/nameCDD"))
            item, ok = QInputDialog.getItem(self, "Select a camera","List of avaible camera", self.groupsName, 0, False,flags=QtCore.Qt.WindowStaysOnTopHint)
            if ok and item:
                indexItem = self.groupsName.index(item)
                self.nbcam=self.groups[indexItem]
                self.openID()
        
        else :  #open the camera by ID : nbcam return ID of the ini file
            try : 
                self.openID()
            except :
                self.isConnected=False 
      
        
    def setCamPara(self):
        '''set min max gain and exp value of cam in the widget
        '''
        
        if self.isConnected==True: # if camera is connected we address min and max value  and value to the shutter and gain box
            # print('camshutter',self.CAM.camParameter["exposureTime"])
            if self.CAM.camParameter["expMax"] >1500: # we limit exposure time at 1500ms
                self.hSliderShutter.setMaximum(1500)
                self.shutterBox.setMaximum(1500)
            else :
                self.hSliderShutter.setMaximum(self.CAM.camParameter["expMax"])
                self.shutterBox.setMaximum(self.CAM.camParameter["expMax"])
            self.hSliderShutter.setValue(int(self.CAM.camParameter["exposureTime"]))
            self.shutterBox.setValue(int(self.CAM.camParameter["exposureTime"]))
            self.hSliderShutter.setMinimum(int(self.CAM.camParameter["expMin"]+1))
            self.shutterBox.setMinimum(int(self.CAM.camParameter["expMin"]+1))
            
            
            
            self.hSliderGain.setMinimum(self.CAM.camParameter["gainMin"])
            self.hSliderGain.setMaximum(self.CAM.camParameter["gainMax"])
            self.hSliderGain.setValue(self.CAM.camParameter["gain"])
            self.gainBox.setMinimum(self.CAM.camParameter["gainMin"])
            self.gainBox.setMaximum(self.CAM.camParameter["gainMax"])
            self.gainBox.setValue(self.CAM.camParameter["gain"])
            
            self.actionButton()
            
        if  self.isConnected==False:
            self.setWindowTitle('Visualization         No camera connected      '   +  'v.  '+ self.version)
            self.runButton.setEnabled(False)
            self.snapButton.setEnabled(False)
            self.trigg.setEnabled(False)
            self.hSliderShutter.setEnabled(False)
            self.shutterBox.setEnabled(False)
            self.gainBox.setEnabled(False)
            self.hSliderGain.setEnabled(False)
            self.runButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconPlay,self.iconPlay))
            self.snapButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconSnap,self.iconSnap))
            
            
            
    def setup(self):  
        
            """ user interface definition 
            """
            self.setWindowTitle('Visualization    '+ self.cameraType+"   " + self.ccdName+'       v.'+ self.version)
            
            
            hbox1=QHBoxLayout() # horizontal layout pour run snap stop
            self.sizebuttonMax=30
            self.sizebuttonMin=30
            self.runButton=QToolButton(self)
            self.runButton.setMaximumWidth(self.sizebuttonMax)
            self.runButton.setMinimumWidth(self.sizebuttonMax)
            self.runButton.setMaximumHeight(self.sizebuttonMax)
            self.runButton.setMinimumHeight(self.sizebuttonMax)
            self.runButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: green;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"% (self.iconPlay,self.iconPlay) )
            
            self.snapButton=QToolButton(self)
            self.snapButton.setPopupMode(0)
            menu=QMenu()
            #menu.addAction('acq',self.oneImage)
            menu.addAction('set nb of shot',self.nbShotAction)
            self.snapButton.setMenu(menu)
            self.snapButton.setMaximumWidth(self.sizebuttonMax)
            self.snapButton.setMinimumWidth(self.sizebuttonMax)
            self.snapButton.setMaximumHeight(self.sizebuttonMax)
            self.snapButton.setMinimumHeight(self.sizebuttonMax)
            self.snapButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: green;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"% (self.iconSnap,self.iconSnap) )
            
            self.stopButton=QToolButton(self)
            
            self.stopButton.setMaximumWidth(self.sizebuttonMax)
            self.stopButton.setMinimumWidth(self.sizebuttonMax)
            self.stopButton.setMaximumHeight(self.sizebuttonMax)
            self.stopButton.setMinimumHeight(self.sizebuttonMax)
            self.stopButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"% (self.iconStop,self.iconStop) )
            self.stopButton.setEnabled(False)
          
            
            hbox1.addWidget(self.runButton)
            hbox1.addWidget(self.snapButton)
            hbox1.addWidget(self.stopButton)
            hbox1.setSizeConstraint(QtGui.QLayout.SetFixedSize)
            hbox1.setContentsMargins(0, 10, 0, 10)
            self.widgetControl=QWidget(self)
            
            self.widgetControl.setLayout(hbox1)
            self.dockControl=QDockWidget(self)
            self.dockControl.setWidget(self.widgetControl)
            self.dockControl.resize(80,80)
           
            self.trigg=QComboBox()
            self.trigg.setMaximumWidth(70)
            self.trigg.addItem('OFF')
            self.trigg.addItem('ON')
            self.trigg.setStyleSheet('font :bold  8pt;color: white')
            self.labelTrigger=QLabel('Trig')
            self.labelTrigger.setMaximumWidth(60)
            self.labelTrigger.setStyleSheet('font :bold  10pt')
            self.itrig=self.trigg.currentIndex()
            
            hbox2=QHBoxLayout()
            hbox2.setSizeConstraint(QtGui.QLayout.SetFixedSize)
            hbox2.setContentsMargins(5, 10, 0, 0)
            hbox2.addWidget(self.labelTrigger)
            
            hbox2.addWidget(self.trigg)
            self.widgetTrig=QWidget(self)
            
            self.widgetTrig.setLayout(hbox2)
            self.dockTrig=QDockWidget(self)
            self.dockTrig.setWidget(self.widgetTrig)
            
            self.labelExp=QLabel('Exp(ms)')
            self.labelExp.setStyleSheet('font :bold  10pt')
            self.labelExp.setMaximumWidth(140)
            self.labelExp.setAlignment(Qt.AlignCenter)
            
            self.hSliderShutter=QSlider(Qt.Horizontal)
            self.hSliderShutter.setMaximumWidth(50)
            self.shutterBox=QSpinBox()
            self.shutterBox.setStyleSheet('font :bold  8pt')
            self.shutterBox.setMaximumWidth(120)
            
            hboxShutter=QHBoxLayout()
            hboxShutter.setContentsMargins(5, 0, 0, 0)
            hboxShutter.setSpacing(10)
            vboxShutter=QVBoxLayout()
            vboxShutter.setSpacing(0)
            vboxShutter.addWidget(self.labelExp)#,Qt.AlignLef)
            
            hboxShutter.addWidget(self.hSliderShutter)
            hboxShutter.addWidget(self.shutterBox)
            vboxShutter.addLayout(hboxShutter)
            vboxShutter.setSizeConstraint(QtGui.QLayout.SetFixedSize)
            vboxShutter.setContentsMargins(5, 0, 0, 0)
            
            self.widgetShutter=QWidget(self)
            
            self.widgetShutter.setLayout(vboxShutter)
            self.dockShutter=QDockWidget(self)
            self.dockShutter.setWidget(self.widgetShutter)
            
            
            
            self.labelGain=QLabel('Gain')
            self.labelGain.setStyleSheet('font :bold  10pt')
            self.labelGain.setMaximumWidth(100)
            self.labelGain.setAlignment(Qt.AlignCenter)
            
            self.hSliderGain=QSlider(Qt.Horizontal)
            self.hSliderGain.setMaximumWidth(50)
            self.gainBox=QSpinBox()
            self.gainBox.setMaximumWidth(60)
            self.gainBox.setStyleSheet('font :bold  8pt')
            self.gainBox.setMaximumWidth(60)
            
            hboxGain=QHBoxLayout()
            hboxGain.setContentsMargins(5, 0, 0, 0)
            hboxGain.setSpacing(10)
            vboxGain=QVBoxLayout()
            vboxGain.setSpacing(0)
            vboxGain.addWidget(self.labelGain)
    
            hboxGain.addWidget(self.hSliderGain)
            hboxGain.addWidget(self.gainBox)
            vboxGain.addLayout(hboxGain)
            vboxGain.setSizeConstraint(QtGui.QLayout.SetFixedSize)
            vboxGain.setContentsMargins(5, 5, 0, 0)
            
            self.widgetGain=QWidget(self)
            self.widgetGain.setLayout(vboxGain)
            self.dockGain=QDockWidget(self)
            self.dockGain.setWidget(self.widgetGain)
            
            # self.TrigSoft=QPushButton('Trig Soft',self)
            # self.TrigSoft.setMaximumWidth(100)
            # self.vbox1.addWidget(self.TrigSoft)
        
            # self.vbox1.addStretch(1)
            # self.cameraWidget.setLayout(self.vbox1)
            # self.cameraWidget.setMinimumSize(150,200)
            # self.cameraWidget.setMaximumSize(200,900)
            
            hMainLayout=QHBoxLayout()
            
            if self.light==False:
                #from visu.visual2 import SEE
                from visu import SEE2
                
                
                self.visualisation=SEE2(**self.kwds) ## Widget for visualisation and tools  self.confVisu permet d'avoir plusieurs camera et donc plusieurs fichier ini de visualisation
                
            else:
                from visu import visualLight2
                self.visualisation=visualLight2.SEELIGHT(**self.kwds)
            
            
            self.visualisation.setWindowTitle('Visualization    '+ self.cameraType+"   " + self.ccdName+'       v.'+ self.version)
            
            self.dockControl.setTitleBarWidget(QWidget())
            self.dockTrig.setTitleBarWidget(QWidget())
            self.dockShutter.setTitleBarWidget(QWidget())
            self.dockGain.setTitleBarWidget(QWidget())
            
            
            MotorLayout=QVBoxLayout()
            MotorLayout.addStretch(2)
            MotorLayout.addWidget(self.motor)
            MotorLayout.addStretch(1)    
            
            
            if self.separate==True:
                
                self.dockMotor=QDockWidget(self)
                self.dockMotor.setTitleBarWidget(QWidget())
                self.WidgetMotor=QWidget()
                #self.WidgetMotor.setStyleSheet("border : blue ")
                self.WidgetMotor.setLayout(MotorLayout)
                
                self.dockMotor.setWidget(self.WidgetMotor)
                
                hbox1.setContentsMargins(0, 10, 0, 0)
                hbox2.setContentsMargins(0, 25, 0, 5)
                hboxShutter.setContentsMargins(0, 5, 0, 0)
                hboxGain.setContentsMargins(0, 5, 0, 0)
                
                if self.aff=='left':
                     # to avoid tittle
                #self.dockControl.setFeatures(QDockWidget.DockWidgetMovable)
                    self.visualisation.addDockWidget(Qt.LeftDockWidgetArea,self.dockControl)
                    self.visualisation.addDockWidget(Qt.LeftDockWidgetArea,self.dockTrig)
                    self.visualisation.addDockWidget(Qt.LeftDockWidgetArea,self.dockShutter)
                    self.visualisation.addDockWidget(Qt.LeftDockWidgetArea,self.dockGain)
                    self.visualisation.addDockWidget(Qt.LeftDockWidgetArea,self.dockMotor)
                else :
                    self.visualisation.addDockWidget(Qt.RightDockWidgetArea,self.dockControl)
                    self.visualisation.addDockWidget(Qt.RightDockWidgetArea,self.dockTrig)
                    self.visualisation.addDockWidget(Qt.RightDockWidgetArea,self.dockShutter)
                    self.visualisation.addDockWidget(Qt.RightDockWidgetArea,self.dockGain)
                    self.visualisation.addDockWidget(Qt.RightDockWidgetArea,self.dockMotor)
                    
                hMainLayout.addWidget(self.visualisation)    
            else:
                
                 # to avoid tittle
                #self.dockControl.setFeatures(QDockWidget.DockWidgetMovable)
                self.visualisation.addDockWidget(Qt.TopDockWidgetArea,self.dockControl)
                self.visualisation.addDockWidget(Qt.TopDockWidgetArea,self.dockTrig)
                self.visualisation.addDockWidget(Qt.TopDockWidgetArea,self.dockShutter)
                self.visualisation.addDockWidget(Qt.TopDockWidgetArea,self.dockGain)
                hMainLayout.addWidget(self.visualisation)
                hMainLayout.addLayout(MotorLayout)  
                
                
                
                
                
            
                
            
            
            if self.loop==True:
                self.closeLoop=QCheckBox('Close Loop')
                MotorLayout.addWidget(self.closeLoop)
            
            MotorLayout.setContentsMargins(0, 0, 0, 0)
            
            hMainLayout.setContentsMargins(1, 0, 0, 0)
            self.setLayout(hMainLayout)
            self.setContentsMargins(0, 0, 2, 0)
            
            #self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint) # set window on the top 
            #self.activateWindow()
            #self.raise_()
            #self.showNormal()
            
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
        self.CAM.newData.connect(self.Display)#,QtCore.Qt.DirectConnection)
        # self.TrigSoft.clicked.connect(self.softTrigger)
        if self.loop==True:
            self.closeLoop.stateChanged.connect(self.closeLoopState)
    
    
    
    def closeLoopState(self):
        if self.closeLoop.isChecked():
            self.visualisation.p1.addItem(self.vLine)
            self.visualisation.p1.addItem(self.hLine)
        else :
            self.visualisation.p1.removeItem(self.vLine)
            self.visualisation.p1.removeItem(self.hLine)
    
    
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
    
    def wait(self,seconds):
        time_end=time.time()+seconds
        while time.time()<time_end:
            QtGui.QApplication.processEvents()    
            
    @pyqtSlot (object) 
    def Display(self,data):
        '''Display data with visualisation module
        
        '''
        if self.multi==True:
            self.wait(0.1)
           
        self.data=data
        self.visualisation.newDataReceived(self.data)
        self.imageReceived=True
        self.datareceived.emit(True)
        time.sleep(0.01)
        if self.CAM.camIsRunnig==False:
            self.stopAcq()
        if self.loop==True:    
            if self.closeLoop.isChecked():
                # position de la croix de reference:
                self.xr=self.visualisation.xc#int(self.conf.value(self.CAM.nbcam+"/xc")) # point vise
                self.yr=self.visualisation.yc#int(self.conf.value(self.CAM.nbcam+"/yc"))
                #taille du cercle
                self.xlim=self.visualisation.rx/2#int(self.conf.value(self.nbcam+"/rx"))/2 # taille cercle
                self.ylim=self.visualisation.ry/2#int(self.conf.value(self.nbcam+"/ry"))/2
                self.dimy=np.shape(self.data)[1]
                self.dimx=np.shape(self.data)[0]
                self.summ=round(data.sum(),3)
                self.maxSum=self.dimy*self.dimx*255/3 # si un trier de la camera sature
                self.maxx=round(self.data.max(),3)
                
                dataF=gaussian_filter(self.data,5)
                thresholded_image = np.copy(dataF) 
                threshold=0.1
                # remove possible offset
                minn = thresholded_image.min() # remove any offset        
                thresholded_image -= minn
                
                # remove all values less than threshold*max
                minn = int(self.maxx*threshold)
                np.place(thresholded_image, thresholded_image<minn, 0)
    
                #self.xec, self.yec= ndimage.center_of_mass(thresholded_image)
                (self.xec,self.yec)=pylab.unravel_index(thresholded_image.argmax(),self.data.shape)
                
                self.vLine.setPos(self.xec)
                
                self.hLine.setPos(self.yec)
    
                self.deltaX=int(self.xr)-int(self.xec)
                self.deltaY=int(self.yr)-int(self.yec)
                
                if self.maxx<30 or self.summ>self.maxSum:
                    print('signal too low or too high') 
                    self.nbImage=0
                else:
                    
                    if ( abs(self.deltaX)>=self.xlim or abs(self.deltaY)>self.ylim) and self.nbImage==self.nbImageMax:
                        
                        # print('xec',self.xec,self.yec,self.xr,self.yr)
                        self.deltaXMoy=int(self.xr)-int(np.mean(self.Xec))
                        
                        if abs(self.deltaXMoy)>=self.xlim and (abs(self.deltaXMoy)<self.maxMvtX):
                            
                            print('X move the',time.strftime("%Y %m %d %H %M %S"), 'of ',self.deltaXMoy*self.pasX)
                            if self.motor.inv[0]==True:
                                self.motor.MOT[0].rmove(-self.deltaXMoy*self.pasX)
                            else:
                                self.motor.MOT[0].rmove(self.deltaXMoy*self.pasX)
                        
                        self.deltaYMoy=int(self.yr)-int(np.mean(self.Yec))
                        
                        if abs(self.deltaYMoy)>self.ylim and (abs(self.deltaYMoy)<self.maxMvtY):
                           
                            print('Y move the',time.strftime("%Y %m %d %H %M %S"), 'of',self.deltaYMoy*self.pasY)
                            if self.motor.inv[1]==True:
                                self.motor.MOT[1].rmove(-self.deltaMoy*self.pasY)
                            else :
                                self.motor.MOT[1].rmove(self.deltaYMoy*self.pasY)
                        self.nbImage=0
                        self.Xec=[]
                        self.Yec=[]       
                    elif( abs(self.deltaX)>=self.xlim or abs(self.deltaY)>self.ylim)and self.nbImage<self.nbImageMax:
                        self.Xec.append(self.xec)
                        self.Yec.append(self.yec)
                        
                        self.nbImage=self.nbImage+1
                    else :
                        self.nbImage=0
                        self.Xec=[]
                        self.Yec=[]
                    
        
            
            
            
    def shutter (self):
        '''
        set exposure time 
        '''
        sh=self.shutterBox.value() # 
        self.hSliderShutter.setValue(sh) # set value of slider
        time.sleep(0.1)
        self.CAM.setExposure(sh) # Set shutter CCD in ms
        self.conf.setValue(self.nbcam+"/shutter",float(sh))
        self.CAM.camParameter["exposureTime"]=sh
        self.conf.sync()
    
    
    
    def mSliderShutter(self): # for shutter slider 
        sh=self.hSliderShutter.value() 
        self.shutterBox.setValue(sh) # 
        self.CAM.setExposure(sh) # Set shutter CCD in ms
        self.conf.setValue(self.nbcam+"/shutter",float(sh))
        self.CAM.camParameter["exposureTime"]=sh
        # self.conf.sync()
        
        
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
        '''Start on acquisition
        '''
        self.imageReceived=False
        self.runButton.setEnabled(False)
        self.runButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconPlay,self.iconPlay))
        self.snapButton.setEnabled(False)
        self.snapButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color:gray}"%(self.iconSnap,self.iconSnap))
        self.stopButton.setEnabled(True)
        self.stopButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconStop,self.iconStop) )
        self.trigg.setEnabled(False)
    
        self.CAM.startOneAcq(self.nbShot)
        
    
    def acquireMultiImage(self):    
        ''' 
            start the acquisition thread
        '''
        
        self.runButton.setEnabled(False)
        self.runButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconPlay,self.iconPlay))
        self.snapButton.setEnabled(False)
        self.snapButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconSnap,self.iconSnap))
        self.stopButton.setEnabled(True)
        self.stopButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconStop,self.iconStop) )
        self.trigg.setEnabled(False)
        
        self.CAM.startAcq() # start mutli image acquisition thread 
        
        
    def stopAcq(self):
        '''Stop  acquisition
        '''
        if self.isConnected==True:
            self.CAM.stopAcq()
        
        self.runButton.setEnabled(True)
        self.runButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconPlay,self.iconPlay))
        self.snapButton.setEnabled(True)
        self.snapButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconSnap,self.iconSnap))
        
        self.stopButton.setEnabled(False)
        self.stopButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconStop,self.iconStop) )
        self.trigg.setEnabled(True)  
    
    
   
    def close(self):
        if self.isConnected==True:
            self.CAM.closeCamera()
        # self.motor.close()
        
    def closeEvent(self,event):
        ''' closing window event (cross button)
        '''
        if self.isConnected==True:
             self.stopAcq()
             time.sleep(0.1)
             self.close()
            

if __name__ == "__main__":       
    
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
    p = pathlib.Path(__file__)
    sepa=os.sep
    pathVisu=str(p.parent) + sepa +'confCamera.ini'
    
    e = CAMERAMOTOR(cam='cam5',fft='off',meas='on',affLight=True,loop=True,separate=True)#,confpath=pathVisu)#,motLat='NF_Lat_P1',motorTypeName0='NewFocus', motVert='Lolita_P1_Vert',motorTypeName1='RSAI',loop=True)  
    e.show()#
    # x= CAMERA(cam="cam2",fft='off',meas='on',affLight=True,multi=False)  
    # x.show()
    appli.exec_()       