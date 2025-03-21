#!/home/upx/loaenv/bin/python3.12
# -*- coding: utf-8 -*-

"""
Created on Tue Mar 24 10:59:16 2020

a Python user interface for camera allied vison, ImgingSource, Balser ,pixelink ,ids 
Scan with RSAI Motors motRSAI = True
check if confserver.ini file is good in visu folder and in camera foldser



on conda prompt :

pip install git+https//github.com/julienGautier77/visu

    for allied vision camera :
    install aliiedVision SDK (https://www.alliedvision.com/en/products/software.html)
    if vimbaX installed  pip install https://github.com/alliedvision/VmbPy   or pip install D:\install\vmbpy-1.0.4-py3-none-any.whl
    if vimba installed : pip install git+https://github.com/alliedvision/VimbaPython

    for Basler camera :
        pip install pypylon: https://github.com/basler/pypylon 
    
    for imagingSource:
        all is the dll folder
    
    for IdS camera :
        pip install pyueye
    
    for pixelink 
        all is the dll folder


@author: juliengautier
"""

try :
    from PyQt6.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QWidget,QLayout,QDoubleSpinBox,QMainWindow
    from PyQt6.QtWidgets import QComboBox,QSlider,QLabel,QSpinBox,QToolButton,QMenu,QInputDialog,QDockWidget,QProgressBar
    from PyQt6 import QtCore
    from PyQt6.QtGui import QIcon
    from PyQt6.QtCore import Qt,QTimer
    from PyQt6 import QtGui 
    from PyQt6.QtCore import pyqtSlot
except ImportError:
    print('error import PyQt6 you can try to use pyQt5 branch')

import sys,time
import pathlib,os
import qdarkstyle
import __init__

__version__ = __init__.__version__
__author__ = __init__.__author__


class CAMERA(QWidget):
    
    updateBar_signal = QtCore.pyqtSignal(object) # signal for update progressbar
    signalData = QtCore.pyqtSignal(object) # signal emited when receive image*
    signalAcqDone = QtCore.pyqtSignal(object) # signal emited when running cam state change

    def __init__(self,cam='choose',confFile='confCamera.ini',**kwds):
        '''
        Parameters
        ----------
        cam : TYPE str, optional
            DESCRIPTION. 
                cam='choose' : generate a input dialog box which the list of all the camera connected (allied,basler,imagingSource) 
                cam='cam1' : open the camera by the ID and type save in the confFile.ini 
                cam='menu': generate a input dialog box with a menu with all the camera name present in the .ini file
                cam='firstGuppy' open the first allied vision camera
                cam='firstBasler' open the first Basler camera
                cam='firstImgSource' open the first ImagingSource camera
            The default is 'choose'.
        confFile : TYPE str, optional
            DESCRIPTION. 
                confFile = the ini file in lacl path
                confpath = the ini file in global path
                The default is 'confCamera.ini'.
        **kwds:
            affLight : TYPE boolean, optional
                DESCRIPTION.
                    affLight = False all the option are show for the visualisation
                    affLight = True only few option (save  open cross)
                    The default is True.
                    scan = True Add widget moteur
                    default is  False
            multi add time sleep to access QApplication.processEvents() 
            + all kwds of VISU class
            
        '''
        super(CAMERA, self).__init__()

        p = pathlib.Path(__file__)
        self.progressWin = ProgressScreen(parent = self)
        self.progressWin.setWindowFlags(Qt.WindowType.SplashScreen | Qt.WindowType.WindowStaysOnTopHint)
        self.progressWin.show()

        self.nbcam = cam
        sepa = os.sep
        self.icon = str(p.parent) + sepa+'icons'+sepa
        self.Qicon=  QtGui.QIcon()
        self.Qicon.addFile(self.icon +'LOA.png', QtCore.QSize(256,256))
        self.setWindowIcon(self.Qicon)
        self.iconPlay = self.icon+'Play.png'
        self.iconSnap = self.icon+'Snap.png'
        self.iconStop = self.icon+'Stop.png'
        self.iconPlay = pathlib.Path(self.iconPlay)
        self.iconPlay = pathlib.PurePosixPath(self.iconPlay)
        self.iconStop = pathlib.Path(self.iconStop)
        self.iconStop = pathlib.PurePosixPath(self.iconStop)
        self.iconSnap = pathlib.Path(self.iconSnap)
        self.iconSnap = pathlib.PurePosixPath(self.iconSnap)
        self.nbShot = 1
        self.isConnected = False
        self.version = str(__version__)
        print('camera version :',self.version )
        self.kwds = kwds
        
        if "affLight" in kwds:
            self.light = kwds["affLight"]
        else:
            self.light=False

        if "multi" in kwds:
            self.multi = kwds["multi"]
        else:
            self.multi = False 
        
        if "separate" in kwds:
            self.separate = kwds["separate"]
        else: 
            self.separate = False
        if "aff" in kwds : #  affi of Visu right or left 
            self.aff = kwds["aff"]
        else: 
            self.aff = "right"    
        
        if "confpath" in kwds:
            self.confpath = kwds["confpath"]
        else  :
            self.confpath = None
        
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6')) # qdarkstyle :  black windows style
        
        if self.confpath == None:
            self.confpath = str(p.parent / confFile) # ini file with global path
        
        self.conf = QtCore.QSettings(self.confpath, QtCore.QSettings.Format.IniFormat) # ini file 
        self.kwds["confpath"] = self.confpath
        
        text = 'Connect to Camera name  : ' + self.nbcam + ' ...'
        self.updateBar_signal.emit([text,25])
        self.openCam()
        text = 'Set Camera Parameters  ......'
        self.updateBar_signal.emit([text,50])
        self.setup()
        text = 'widget loading  ' + self.nbcam + ' ...'
        self.updateBar_signal.emit([text,75])
        self.setCamPara()
        self.updateBar_signal.emit(['end',100])
        self.progressWin.close()

    def openID(self):
        '''
        open a camera by id camera typ and ID must be known and saved in the ini file 

        '''
        self.ccdName = self.conf.value(self.nbcam+"/nameCDD")
        self.cameraType = self.conf.value(self.nbcam+"/camType")
        self.camID = self.conf.value(self.nbcam+"/camId")
        
        if self.cameraType == "allied" :
            try :
                import alliedCam
                self.CAM = alliedCam.ALLIEDVISION (cam=self.nbcam,conf=self.conf,**self.kwds)
                self.CAM.openCamByID(self.camID)
                self.isConnected=self.CAM.isConnected
            except :
                print("no allied vision camera detected or vimba is not installed")
                self.isconnected = False
                print('No camera choosen')
                self.ccdName = "no camera"
                self.cameraType = ""
                self.camID = ""
                self.nbcam = 'camDefault'
                pass
        
        elif self.cameraType == "basler":
            try:
                import baslerCam
                self.CAM = baslerCam.BASLER(cam=self.nbcam,conf=self.conf,**self.kwds)
                self.CAM.openCamByID(self.camID)
                self.isConnected = self.CAM.isConnected
            except:
                print("no basler camera detected or pypylon is not installed")
                self.isconnected = False
                print('No camera choosen')
                self.ccdName = "no camera"
                self.cameraType = ""
                self.camID = ""
                self.nbcam = 'camDefault'
                pass
        
        elif self.cameraType == "imgSource":
            try :
                import ImgSourceCamCallBack
                self.CAM = ImgSourceCamCallBack.IMGSOURCE(cam=self.nbcam,conf=self.conf,**self.kwds)
                self.CAM.openCamByID(self.camID)
                self.isConnected = self.CAM.isConnected
            except:
                print("no imaging source camera detected or Tisgrabber is not installed")
                self.isconnected = False
                print('No camera choosen')
                self.ccdName = "no camera"
                self.cameraType = ""
                self.camID = ""
                self.nbcam = 'camDefault'
                pass

        elif self.cameraType == "pixelink":
            try :
                import pixelinkCam
                self.CAM = pixelinkCam.PIXELINK(cam=self.nbcam,conf=self.conf,**self.kwds)
                self.CAM.openCamByID(self.camID)
                self.isConnected = self.CAM.isConnected
            except:
                print("no imaging source camera detected or Tisgrabber is not installed")
                self.isconnected = False
                print('No camera choosen')
                self.ccdName = "no camera"
                self.cameraType = ""
                self.camID = ""
                self.nbcam = 'camDefault'
                pass

        elif self.cameraType == "ids":
            try :
                import idsCam
                self.CAM = idsCam.IDS(cam=self.nbcam,conf=self.conf,**self.kwds)
                self.CAM.openCamByID(self.camID)
                self.isConnected = self.CAM.isConnected
            except:
                print("no imaging source camera detected or Tisgrabber is not installed")
                self.isconnected = False
                print('No camera choosen')
                self.ccdName = "no camera"
                self.cameraType = ""
                self.camID = ""
                self.nbcam = 'camDefault'
                pass 
        else:
            print('no camera')
            self.isConnected = False
            self.ccdName = "no camera"
            self.cameraType = ""
            self.camID = ""
            self.nbcam = 'camDefault'
            
    def openCam(self):
        '''open a camera with different way  
        '''
        
        if self.nbcam == "choose": # create menu widget with all camera present 
        
            self.nbcam = 'camDefault'
            try :
                import alliedCam
                self.itemsGuppy = alliedCam.camAvailable()
                # print(self.itemsGuppy)
                self.lenGuppy = len(self.itemsGuppy)
                
            except:
                print('No allied vision camera connected')
                self.itemsGuppy = []
                self.lenGuppy = 0
                pass
            try :
                import baslerCam
                self.itemsBasler = baslerCam.camAvailable()
                self.lenBasler = len(self.itemsBasler)
                
            except:
                print('No Basler camera connected')
                self.itemsBasler = []
                self.lenBasler = 0
                pass 
            
            try :
                import ImgSourceCamCallBack
                self.itemsImgSource = ImgSourceCamCallBack.camAvailable()
                self.lenImgSource = len(self.itemsImgSource)
                
            except:
                print('No ImagingSource camera connected')
                self.itemsImgSource = []
                self.lenImgSource = 0
                pass 
            
            try :
                import pixelinkCam
                self.itemsPixelink = pixelinkCam.PIXELINK.camAvailable()
                self.lenImgPixelink = len(self.itemsPixelink)
                
            except:
                print('No pixelink camera connected')
                self.itemsPixelink = []
                self.lenPixelink = 0
                pass 
            
            items = self.itemsGuppy + list(self.itemsBasler)+self.itemsImgSource+self.itemsPixelink
            item, ok = QInputDialog.getItem(self, "Select a camera","List of avaible camera", items, 0, False,flags=QtCore.Qt.WindowType.WindowStaysOnTopHint)
            if ok and item:
                indexItem = items.index(item)
                if indexItem < self.lenGuppy:
                    indexItem = indexItem
                    self.cameraType = "allied"
                    self.camID = alliedCam.getCamID(indexItem)
                    self.CAM = alliedCam.ALLIEDVISION(cam=self.nbcam,conf=self.conf)
                    self.CAM.openCamByID(self.camID)
                    self.isConnected = self.CAM.isConnected
                    self.ccdName = self.camID
                elif indexItem >= self.lenGuppy  and indexItem<self.lenBasler+self.lenGuppy:
                    indexItem = indexItem-self.lenGuppy
                    self.cameraType = "basler"
                    self.camID = baslerCam.getCamID(indexItem)
                    self.CAM = baslerCam.BASLER(cam=self.nbcam,conf=self.conf,**self.kwds)
                    self.CAM.openCamByID(self.camID)
                    self.isConnected = self.CAM.isConnected
                    self.ccdName = self.camID
                    
                elif indexItem >= self.lenBasler+self.lenGuppy  and indexItem<self.lenBasler+self.lenGuppy+self.lenImgSource:
                    indexItem = indexItem-self.lenGuppy-self.lenBasler
                    self.cameraType = "imgSource"
                    self.camID = ImgSourceCamCallBack.getCamID(indexItem)
                    self.camID = self.camID.decode()
                    self.CAM = ImgSourceCamCallBack.IMGSOURCE(cam=self.nbcam,conf=self.conf,**self.kwds)
                    self.CAM.openCamByID(self.camID)
                    self.isConnected = self.CAM.isConnected
                    self.ccdName = self.camID
                    
                elif indexItem >= self.lenBasler+self.lenGuppy+ self.lenImgSource and indexItem < self.lenBasler+self.lenGuppy+self.lenImgSource+self.lenPixelink:
                    indexItem = indexItem-self.lenGuppy-self.lenBasler-self.lenImgSource
                    self.cameraType = "pixelink"
                    self.camID = pixelinkCam.getCamID(indexItem)
                    self.CAM = pixelinkCam.PIXELINK(cam=self.nbcam,conf=self.conf,**self.kwds)
                    self.CAM.openCamByID(self.camID)
                    self.isConnected = self.CAM.isConnected
                    self.ccdName = self.camID    
                else:
                     self.isconnected = False
                     print('No camera choosen')
                     self.ccdName = "no camera"
                     self.nbcam = 'camDefault'
            else :
                self.isconnected = False
                print('No camera choosen')
                self.ccdName = "no camera"
                self.cameraType = ""
                self.camID = ""
                self.nbcam = 'camDefault'
            
        elif  self.nbcam == None:
            self.isconnected = False
            print('No camera')
            self.ccdName = "no camera"
            self.cameraType = ""
            self.camID = ""
            self.nbcam = 'camDefault'
             
        elif self.nbcam == "firstAllied": # open the first allied camera  cam in the list
            self.nbcam = 'camDefault'
            self.cameraType = "allied"
            self.ccdName = 'First allied Cam'
            import alliedCam
            self.CAM = alliedCam.ALLIEDVISION(cam=self.nbcam,conf=self.conf,**self.kwds)
            self.CAM.openFirstCam()
            self.isConnected = self.CAM.isConnected    
        
        
        elif self.nbcam == "firstBasler": # open the first basler cam in the list
            self.ccdName = 'First basler Cam'
            self.nbcam = 'camDefault'
            self.cameraType = "basler"
            import baslerCam 
            self.CAM = baslerCam.BASLER(cam=self.nbcam,conf=self.conf,**self.kwds)
            self.CAM.openFirstCam()
            self.isConnected = self.CAM.isConnected   
            
        elif self.nbcam == "firstImgSource": # open the first imgSource cam in the list
            self.ccdName = 'First ImSource Cam'
            self.nbcam = 'camDefault'
            self.cameraType = "imgSource"
            import ImgSourceCamCallBack 
            self.CAM = ImgSourceCamCallBack.IMGSOURCE(cam=self.nbcam,conf=self.conf,**self.kwds)
            self.CAM.openFirstCam()
            self.isConnected = self.CAM.isConnected 
            
        elif self.nbcam == "firstPixelink": # open the first pixelink cam in the list
            self.ccdName = 'First Pixelink Cam'
            self.nbcam = 'camDefault'
            self.cameraType = "pixelink"
            import pixelinkCam
            self.CAM = pixelinkCam.PIXELINK(cam=self.nbcam,conf=self.conf,**self.kwds)
            self.CAM.openFirstCam()
            self.isConnected = self.CAM.isConnected      
        
        elif self.nbcam == "firstIds": # open the first ids cam in the list
            self.nbcam = 'camDefault'
            self.cameraType = "ids"
            self.ccdName = 'First ids Cam'
            import idsCam
            self.CAM = idsCam.IDS(cam=self.nbcam,conf=self.conf,**self.kwds)
            self.CAM.openFirstCam()
            self.isConnected = self.CAM.isConnected    
        
        elif self.nbcam == 'menu': # Qdialog with a menu with all the camera name present in the inifile
            self.groupsName = []
            self.groups = self.conf.childGroups()
            for groups in self.groups:
                self.groupsName.append(self.conf.value(groups+"/nameCDD"))
            item, ok = QInputDialog.getItem(self, "Select a camera","List of avaible camera", self.groupsName, 0, False,flags=QtCore.Qt.WindowType.WindowStaysOnTopHint)
            if ok and item:
                indexItem = self.groupsName.index(item)
                self.nbcam = self.groups[indexItem]
                self.openID()
        
        else :  #open the camera by ID : nbcam return ID of the ini file
            try : 
                self.openID()
            except :
                self.isConnected=False 
        
    def setCamPara(self):
        '''
        set min max gain and exp value of cam in the widget
        '''
        if self.isConnected is True : # if camera is connected we address min and max value  and value to the shutter and gain box
           
            if self.CAM.camParameter["expMax"] > 1500 : # we limit exposure time at 1500ms
                self.hSliderShutter.setMaximum(1500)
                self.shutterBox.setMaximum(1500)
            else :
                self.hSliderShutter.setMaximum(int(self.CAM.camParameter["expMax"]))
                self.shutterBox.setMaximum(int(self.CAM.camParameter["expMax"]))
            
            self.hSliderShutter.setValue(int(self.CAM.camParameter["exposureTime"]))
            self.shutterBox.setValue(int(self.CAM.camParameter["exposureTime"]))
            self.hSliderShutter.setMinimum(int(self.CAM.camParameter["expMin"]+1))
            self.shutterBox.setMinimum(int(self.CAM.camParameter["expMin"]))
            
            self.hSliderGain.setMinimum(int(self.CAM.camParameter["gainMin"]))
            self.hSliderGain.setMaximum(int(self.CAM.camParameter["gainMax"]))
            self.hSliderGain.setValue(int(self.CAM.camParameter["gain"]))
            self.gainBox.setMinimum(int(self.CAM.camParameter["gainMin"]))
            self.gainBox.setMaximum(int(self.CAM.camParameter["gainMax"]))
            self.gainBox.setValue(int(self.CAM.camParameter["gain"]))
            
            self.actionButton()
            
        if  self.isConnected is False: # no camera connected 
            self.nbcam = 'camDefault'
            self.setWindowTitle('No camera connected    ' + 'Visu v. ' + self.visualisation.version)   
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
            """
              user interface definition 
            """
            vbox1 = QVBoxLayout() # 
            hbox1 = QHBoxLayout() # horizontal layout pour run snap stop
            self.sizebuttonMax = 30
            self.sizebuttonMin = 30
            self.runButton = QToolButton(self)
            self.runButton.setMaximumWidth(self.sizebuttonMax)
            self.runButton.setMinimumWidth(self.sizebuttonMax)
            self.runButton.setMaximumHeight(self.sizebuttonMax)
            self.runButton.setMinimumHeight(self.sizebuttonMax)
            self.runButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: green;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"% (self.iconPlay,self.iconPlay) )
            
            self.snapButton = QToolButton(self)
            self.snapButton.setPopupMode(QToolButton.ToolButtonPopupMode.MenuButtonPopup)
            menu = QMenu()
            menu.addAction('set nb of shot',self.nbShotAction)
            self.snapButton.setMenu(menu)
            self.snapButton.setMaximumWidth(self.sizebuttonMax)
            self.snapButton.setMinimumWidth(self.sizebuttonMax)
            self.snapButton.setMaximumHeight(self.sizebuttonMax)
            self.snapButton.setMinimumHeight(self.sizebuttonMax)
            self.snapButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: green;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"% (self.iconSnap,self.iconSnap) )
            
            self.stopButton = QToolButton(self)
            self.stopButton.setMaximumWidth(self.sizebuttonMax)
            self.stopButton.setMinimumWidth(self.sizebuttonMax)
            self.stopButton.setMaximumHeight(self.sizebuttonMax)
            self.stopButton.setMinimumHeight(self.sizebuttonMax)
            self.stopButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"% (self.iconStop,self.iconStop) )
            self.stopButton.setEnabled(False)
          
            hbox1.addWidget(self.runButton)
            hbox1.addWidget(self.snapButton)
            hbox1.addWidget(self.stopButton)
            
            hbox1.setSizeConstraint(QLayout.SizeConstraint.SetMaximumSize)#setFixedSize)#
            hbox1.setContentsMargins(0, 0, 0, 0)
            hbox1.setAlignment(Qt.AlignmentFlag.AlignHCenter)
            vbox1.addLayout(hbox1)
            vbox1.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
            vbox1.setContentsMargins(0, 20, 10, 10)
            
            self.widgetControl = QWidget(self)
            self.widgetControl.setLayout(vbox1)
            self.dockControl = QDockWidget(self)
            self.dockControl.setWidget(self.widgetControl)
            # self.dockControl.resize(80,80)
            self.trigg = QComboBox()
            self.trigg.setMaximumWidth(90)
            self.trigg.addItem('OFF')
            self.trigg.addItem('ON')
            self.trigg.setStyleSheet('font :bold 10pt;color: white')
            self.labelTrigger = QLabel('Trig')
            self.labelTrigger.setMaximumWidth(50)
            self.labelTrigger.setStyleSheet('font :bold  10pt')
            self.itrig = self.trigg.currentIndex()
            hbox2 = QHBoxLayout()
            hbox2.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
            hbox2.setContentsMargins(0, 20, 10, 10)
            hbox2.addWidget(self.labelTrigger)
            hbox2.addWidget(self.trigg)
            self.widgetTrig = QWidget(self)
            self.widgetTrig.setLayout(hbox2)
            self.dockTrig = QDockWidget(self)
            self.dockTrig.setWidget(self.widgetTrig)
            
            self.labelExp = QLabel('Exposure (ms)')
            self.labelExp.setStyleSheet('font :bold  10pt')
            self.labelExp.setMaximumWidth(140)
            self.labelExp.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.hSliderShutter = QSlider(Qt.Orientation.Horizontal)
            self.hSliderShutter.setMaximumWidth(60)
            self.shutterBox = QDoubleSpinBox()
            self.shutterBox.setStyleSheet('font :bold  8pt')
            self.shutterBox.setMaximumWidth(120)
            
            hboxShutter = QHBoxLayout()
            hboxShutter.setContentsMargins(0, 0, 0, 5)
            hboxShutter.setSpacing(10)
            vboxShutter = QVBoxLayout()
            vboxShutter.setSpacing(0)
            vboxShutter.addWidget(self.labelExp)#,Qt.AlignLef)
            
            hboxShutter.addWidget(self.hSliderShutter)
            hboxShutter.addWidget(self.shutterBox)
            vboxShutter.addLayout(hboxShutter)
            vboxShutter.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
            vboxShutter.setContentsMargins(0, 0, 10, 0)
            vboxShutter.setSpacing(2)
            
            self.widgetShutter = QWidget(self)
            self.widgetShutter.setLayout(vboxShutter)
            self.dockShutter = QDockWidget(self)
            self.dockShutter.setWidget(self.widgetShutter)
            
            self.labelGain = QLabel('Gain')
            self.labelGain.setStyleSheet('font :bold  10pt')
            self.labelGain.setMaximumWidth(140)
            self.labelGain.setAlignment(Qt.AlignmentFlag.AlignCenter)
            
            self.hSliderGain = QSlider(Qt.Orientation.Horizontal)
            self.hSliderGain.setMaximumWidth(60)
            self.gainBox = QSpinBox()
            self.gainBox.setStyleSheet('font :bold  8pt')
            self.gainBox.setMaximumWidth(120)
            
            hboxGain = QHBoxLayout()
            hboxGain.setContentsMargins(0, 0, 0, 5)
            hboxGain.setSpacing(10)
            vboxGain=QVBoxLayout()
            vboxGain.setSpacing(0)
            vboxGain.addWidget(self.labelGain)
    
            hboxGain.addWidget(self.hSliderGain)
            hboxGain.addWidget(self.gainBox)
            vboxGain.addLayout(hboxGain)
            vboxGain.setSizeConstraint(QLayout.SizeConstraint.SetFixedSize)
            
            vboxGain.setContentsMargins(0, 0, 10, 0)
            vboxGain.setSpacing(2)
            self.widgetGain = QWidget(self)
            self.widgetGain.setLayout(vboxGain)
            self.dockGain = QDockWidget(self)
            self.dockGain.setWidget(self.widgetGain)
            
           
            
            # self.TrigSoft=QPushButton('Trig Soft',self)
            # self.TrigSoft.setMaximumWidth(100)
            # self.vbox1.addWidget(self.TrigSoft)
        
            hMainLayout = QHBoxLayout()
            
            if self.light is False :  # light option : not all the option af visu 
                from visu import SEE
                self.visualisation = SEE(parent=self,name=self.nbcam,spectro=False,**self.kwds) ## Widget for visualisation and tools  self.confVisu permet d'avoir plusieurs camera et donc plusieurs fichier ini de visualisation
            else:
                from visu import SEELIGHT
                self.visualisation = SEELIGHT(parent=self, name=self.nbcam, spectro=False, **self.kwds)
                    
            self.setWindowTitle(self.cameraType+"   " + self.ccdName+ '     v. '+ self.version+"   " +'Visu v. '+ self.visualisation.version)   
            self.dockTrig.setTitleBarWidget(QWidget())        
            self.dockControl.setTitleBarWidget(QWidget())  # to avoid tittle
            self.dockShutter.setTitleBarWidget(QWidget())
            self.dockGain.setTitleBarWidget(QWidget())
            

            if self.separate is True :  # control camera button is not on the menu but in a widget at the left or right of the display screen
                self.dockTrig.setTitleBarWidget(QWidget())
                if self.aff == 'left' :
                    self.visualisation.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea,self.dockControl)
                    self.visualisation.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea,self.dockTrig)
                    self.visualisation.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea,self.dockShutter)
                    self.visualisation.addDockWidget(Qt.DockWidgetArea.LeftDockWidgetArea,self.dockGain)
                    
                else:
                    self.visualisation.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,self.dockControl)
                    self.visualisation.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,self.dockTrig)
                    self.visualisation.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,self.dockShutter)
                    self.visualisation.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea,self.dockGain)
                    
            else:
            #self.dockControl.setFeatures(QDockWidget.DockWidgetMovable)
                self.visualisation.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea,self.dockControl)
                self.visualisation.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea,self.dockTrig)
                self.visualisation.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea,self.dockShutter)
                self.visualisation.addDockWidget(Qt.DockWidgetArea.TopDockWidgetArea,self.dockGain)
                
             
            hMainLayout.addWidget(self.visualisation)
            self.setLayout(hMainLayout)
            self.setContentsMargins(0, 0, 0, 0)
            #self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint) # set window on the top 
            #self.activateWindow()
            #self.raise_()
            #self.showNormal()
            
    def actionButton(self): 
        '''
        action when button are pressed
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
        self.CAM.endAcq.connect(self.stopAcq)
        # self.TrigSoft.clicked.connect(self.softTrigger)
        # self.visualisation.signalDisplayed.connect(self.ImageDisplayed) # receive signal of vis when image displayer
       # self.CAM.signalRunning.connect(self.camIsRunning)
           
    def oneImage(self):
        #self.nbShot=1
        self.acquireOneImage()

    def nbShotAction(self):
        '''
        number of snapShot
        '''
        nbShot, ok = QInputDialog.getInt(self,'Number of SnapShot ','Enter the number of snapShot ')
        if ok:
            self.nbShot = int(nbShot)
            if self.nbShot <=0 :
               self.nbShot = 1
    
    def wait(self,seconds):
        time_end = time.time()+seconds
        while time.time()<time_end:
            QApplication.processEvents()  

    def Display(self,data):
        '''
        Display data with visualisation module
        '''
        if self.multi is True:
            self.wait(0.1)
           
        self.data = data
        self.signalData.emit(self.data)
        
        self.isRunning = False # we receive a data
        #print('data received in camera')
        # self.visualisation.newDataReceived(self.data) # It can be use but is better to use signal than function
        self.imageReceived = True
        # self.datareceived.emit(True)
        if self.CAM.camIsRunning == False:
            self.stopAcq()
    
    def camIsRunning(self):
        self.isCamRunning = self.CAM.camIsRunning
        #self.signalRunning.emit(self.isCamRunning)
        return(self.isCamRunning)
    
    def shutter(self):
        '''
        set exposure time 
        '''
        sh = self.shutterBox.value() #
        time.sleep(0.1)
        self.CAM.setExposure(sh) # Set shutter CCD in ms
        self.conf.setValue(self.nbcam+"/shutter",float(sh))
        self.CAM.camParameter["exposureTime"] = sh
        self.conf.sync()
    
    def mSliderShutter(self): # for shutter slider 
        sh = self.hSliderShutter.value() 
        self.shutterBox.setValue(sh) # 
        self.CAM.setExposure(sh) # Set shutter CCD in ms
        self.conf.setValue(self.nbcam+"/shutter",float(sh))
        self.CAM.camParameter["exposureTime"] = sh
      
    def gain (self):
        '''
        set gain
        '''
        g = self.gainBox.value()
        self.hSliderGain.setValue(g) # set slider value
        time.sleep(0.1)
        self.CAM.setGain(g)
        self.conf.setValue(self.nbcam+"/gain",float(g))
        self.conf.sync()
    
    def mSliderGain(self):
        '''
        set gain slider
        '''
        g = self.hSliderGain.value()
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
        self.itrig = self.trigg.currentIndex()
        
        if self.itrig == 1:
            self.CAM.setTrigger("on")
        else :
            self.CAM.setTrigger("off")
                
    def acquireOneImage(self):
        '''Start on acquisition
        '''
        self.imageReceived = False
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
        if self.isConnected is True:
            self.CAM.stopAcq()
        
        self.runButton.setEnabled(True)
        self.runButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconPlay,self.iconPlay))
        self.snapButton.setEnabled(True)
        self.snapButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconSnap,self.iconSnap))
        
        self.stopButton.setEnabled(False)
        self.stopButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: gray ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconStop,self.iconStop) )
        self.trigg.setEnabled(True)  
    
    def close(self):
        if self.isConnected is True:
            self.CAM.closeCamera()
        
    def closeEvent(self,event):
        ''' closing window event (cross button)
        '''
        if self.isConnected is True:
             self.stopAcq()
             time.sleep(0.1)
             self.close()
        self.visualisation.close()  


class ProgressScreen(QWidget):
    
    def __init__(self,parent=None):

        super().__init__()

        self.parent = parent 
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(p.parent) + sepa+'icons' + sepa
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setWindowTitle(' Loading  ...')
        self.setGeometry(600, 300, 300, 100)
        #self.setWindowFlags(Qt.WindowType.FramelessWindowHint| Qt.WindowType.WindowStaysOnTopHint)
        layout = QVBoxLayout()

        self.label = QLabel('Loading Camera V'+str(__version__))
        self.label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.label2 = QLabel("Laboratoire d'Optique Appliquée")
        self.label2.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        self.label2.setStyleSheet('font :bold 20pt;color: white')
        self.action = QLabel('Load visu')
        layout.addWidget(self.label2)
        layout.addWidget(self.label)
        layout.addWidget(self.action)
        self.progress_bar = QProgressBar()
        layout.addWidget(self.progress_bar)

        self.setLayout(layout)
        if self.parent is not None:
            self.parent.updateBar_signal.connect(self.setLabel)

    def setLabel(self,labels) :
        label = labels[0]
        val = labels[1]
        self.action.setText(str(label))
        self.progress_bar.setValue(int(val))
        QtCore.QCoreApplication.processEvents() # c'est moche mais pas de mise  jour sinon ???
        

if __name__ == "__main__":       
    
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    path = '/home/gautier/Documents/confCamera.ini'
    e = CAMERA(cam='choose',motRSAI=False,aff='right' )#,confpath=path  )
    e.show()
    sys.exit(appli.exec())   
