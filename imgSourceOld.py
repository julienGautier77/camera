# -*- coding: utf-8 -*-
"""
Created on Wed Nov  28 13:13:26 2018
Modified on Thu Sep 26 15:40:14 2019
Camera Imaging sources 
Gui for imangingsource camera use IC_ImagingControl 
PyQT5 and PyQtgraph
Pyhton 3.x
@author: LOA Julien Gautier
"""


from PyQt5.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QWidget,QPushButton,QSpinBox
from PyQt5.QtWidgets import QComboBox,QSlider,QLabel,QInputDialog
from pyqtgraph.Qt import QtCore
from PyQt5.QtCore import Qt

from PyQt5.QtGui import QIcon

import sys,time
 
import numpy as np
try :
    import IC_ImagingControl 
except :
    pass
from scipy.ndimage.filters import gaussian_filter
try :
    from visu import SEE
except:
    print ('No visu module installed :see' )


import qdarkstyle # pip install qdakstyle https://github.com/ColinDuquesnoy/QDarkStyleSheet  sur conda
import pathlib,os


class CameraAcqD(QWidget) :

    def __init__(self,name=None,visuGauche=False,confVisu=None):
        super(CameraAcqD, self).__init__()
        self.visuGauche=visuGauche
        
        self.seuil=1
        self.confVisu=confVisu
        if name==None:
            self.nbcam='camTest'
        else:   
            self.nbcam=name
        self.confCCD = QtCore.QSettings('confCameras.ini', QtCore.QSettings.IniFormat)
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5()) # dark style 
        self.bloqHandle=1 # bloque la taille du cercle
        self.camType=self.confCCD.value(self.nbcam+"/camType")
        
#        if self.camType != 'imgSource':
#            print('error camera type')
            
        self.cameName=self.confCCD.value(self.nbcam+"/name")
        self.setWindowTitle(self.cameName)
        p = pathlib.Path(__file__)
        sepa=os.sep
        self.icon=str(p.parent) + sepa + 'icons' +sepa
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        #pg.setConfigOptions(antialias=True)
        
        try :
            ic_ic = IC_ImagingControl.IC_ImagingControl()
            ic_ic.init_library()
        except :
            print('IC control Library not found')
            pass
        
        self.bloqq=1
        self.id=self.confCCD.value(self.nbcam+"/camId")
        self.camName=self.confCCD.value(self.nbcam+"/name")
        
        self.setup()
        
        
        self.actionButton()
        try :
            self.cam0= ic_ic.get_device((self.id.encode()))#cam_names[0])
            self.connected=1
            print(self.nbcam,"connected @",self.confCCD.value(self.nbcam+"/name"),'id:',self.id)
        except:
            self.connected=0
            print ('not connected')
            self.nbcam='camTest'
            self.runButton.setEnabled(False)
            self.runButton.setStyleSheet("background-color:gray")
            self.runButton.setStyleSheet("QPushButton:!pressed{image: url(./icons/Circled Play-595b40b65ba036ed117d436f.svg);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0,0)}""QPushButton:pressed{image: url(./icons/Circled Play-595b40b65ba036ed117d436f.svg);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0)}")
            
            self.hSliderShutter.setEnabled(False)
            self.trigg.setEnabled(False)
            self.hSliderGain.setEnabled(False)
            self.stopButton.setEnabled(False)
            self.stopButton.setStyleSheet("background-color:gray")
            self.stopButton.setStyleSheet("QPushButton:!pressed{border-image: url(./icons/Stop.svg);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0,0);}""QPushButton:pressed{image: url(./icons/Stop.svg);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0)}")

            
        if self.connected==1:
            self.cam0.open()
            #print(self.cam0.list_property_names())
           
            self.cam0.enable_continuous_mode(True)
            self.cam0.gain.auto=False
            self.cam0.exposure.auto=False
            self.cam0.set_frame_rate=float(25)
            frameRate=self.cam0.get_frame_rate()
            print('frame rate : ',frameRate)
            self.rangeExp=self.cam0.getPropertyRange('Exposure','Value')
            
            self.hSliderShutter.setMinimum(self.rangeExp[0]*1000)
            self.hSliderShutter.setMaximum(5000)#self.rangeExp[1]
            self.shutterBox.setMinimum(self.rangeExp[0]*1000)
            self.shutterBox.setMaximum(5000)
            sh=float(self.confCCD.value(self.nbcam+"/shutter"))
            self.hSliderShutter.setValue(sh)
            self.shutterBox.setValue(sh)
            self.cam0.setExposure(sh/1000)
            
            self.hSliderGain.setMinimum(self.cam0.gain.min)
            self.hSliderGain.setMaximum(self.cam0.gain.max)
            self.gainBox.setMinimum(self.cam0.gain.min)
            self.gainBox.setMaximum(self.cam0.gain.max)
            g=float(self.confCCD.value(self.nbcam+"/gain"))
            self.hSliderGain.setValue(g)
            self.gainBox.setValue(g)
            self.cam0.gain.value=int(g)
            
            self.dimy=self.cam0.get_video_format_height()
            self.dimx=self.cam0.get_video_format_width()
            print("number of pixels :",self.dimx,'*',self.dimy)
            
        else :
            self.dimy=960
            self.dimx=1240
            
        
        def twoD_Gaussian(x,y, amplitude, xo, yo, sigma_x, sigma_y, theta, offset):
            xo = float(xo)
            yo = float(yo)    
            a = (np.cos(theta)**2)/(2*sigma_x**2) + (np.sin(theta)**2)/(2*sigma_y**2)
            b = -(np.sin(2*theta))/(4*sigma_x**2) + (np.sin(2*theta))/(4*sigma_y**2)
            c = (np.sin(theta)**2)/(2*sigma_x**2) + (np.cos(theta)**2)/(2*sigma_y**2)
            return offset + amplitude*np.exp( - (a*((x-xo)**2) + 2*b*(x-xo)*(y-yo) + c*((y-yo)**2)))

        # Create x and y indices
        x = np.arange(0,self.dimx)
        y = np.arange(0,self.dimy)
        y,x = np.meshgrid(y, x)

        self.data=twoD_Gaussian(x, y,250, 300, 600, 40, 40, 0, 10)+(50*np.random.rand(self.dimx,self.dimy)).round() 
        #self.data=(50*np.random.rand(self.dimx,self.dimy)).round() + 150
        
        
        #self.p1.setGeometry(1,1,self.dimx,self.dimy)
        #self.winImage.setGeometry(1,1,self.dimx,self.dimy)
        self.Display(self.data)
        
        
    def setup(self):    
        
        vbox1=QVBoxLayout() 
        
        
        self.camNameLabel=QLabel('nomcam',self)
        
        self.camNameLabel.setText(self.confCCD.value(self.nbcam+"/name"))

        self.camNameLabel.setAlignment(Qt.AlignCenter)
        self.camNameLabel.setStyleSheet('font: bold 20px')
        self.camNameLabel.setStyleSheet('color: yellow')
        vbox1.addWidget(self.camNameLabel)
        
        hbox1=QHBoxLayout() # horizontal layout pour run et stop
        self.runButton=QPushButton(self)
        self.runButton.setMaximumWidth(60)
        self.runButton.setMinimumHeight(60)
        self.runButton.setStyleSheet("QPushButton:!pressed{border-image: url(./icons/Circled Play-595b40b65ba036ed117d436f.svg);background-color: rgb(0, 0, 0,0) ;border-color: green;}""QPushButton:pressed{image: url(./icons/Circled Play-595b40b65ba036ed117d436f.svg);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0)}")
        self.stopButton=QPushButton(self)
        
        self.stopButton.setMaximumWidth(60)
        self.stopButton.setMinimumHeight(50)
        self.stopButton.setStyleSheet("QPushButton:!pressed{border-image: url(./icons/Stop.svg);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0,0);}""QPushButton:pressed{image: url(./icons/Stop.svg);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0)}")
        
        
        hbox1.addWidget(self.runButton)
        hbox1.addWidget(self.stopButton)
#        self.oneButton=QPushButton(self)
#        hbox1.addWidget(self.oneButton)
        
        vbox1.addLayout(hbox1)
        
        self.trigg=QComboBox()
        self.trigg.setMaximumWidth(60)
        self.trigg.addItem('OFF')
        self.trigg.addItem('ON')
        self.trigg.addItem('Threshold')
        self.labelTrigger=QLabel('Trigger')
        self.labelTrigger.setMaximumWidth(60)
        self.itrig=self.trigg.currentIndex()
        hbox2=QHBoxLayout()
        hbox2.addWidget(self.labelTrigger)
        hbox2.addWidget(self.trigg)
        vbox1.addLayout(hbox2)
        
        self.labelExp=QLabel('Exposure (ms)')
        self.labelExp.setMaximumWidth(120)
        self.labelExp.setAlignment(Qt.AlignCenter)
        vbox1.addWidget(self.labelExp)
        self.hSliderShutter=QSlider(Qt.Horizontal)
       
        self.hSliderShutter.setMaximumWidth(120)
        self.shutterBox=QSpinBox()
        
        self.shutterBox.setMaximumWidth(60)
    
        self.hSliderShutter.setMaximumWidth(120)
        hboxShutter=QHBoxLayout()
        hboxShutter.addWidget(self.hSliderShutter)
        hboxShutter.addWidget(self.shutterBox)
        vbox1.addLayout(hboxShutter)
        
        hboxGain=QHBoxLayout()
        self.labelGain=QLabel('Gain')
        self.labelGain.setMaximumWidth(120)
        self.labelGain.setAlignment(Qt.AlignCenter)
        vbox1.addWidget(self.labelGain)
        self.hSliderGain=QSlider(Qt.Horizontal)
        self.hSliderGain.setMaximumWidth(120)
        
        self.gainBox=QSpinBox()
        
           
        self.gainBox.setMaximumWidth(60)
        hboxGain.addWidget(self.hSliderGain)
        hboxGain.addWidget(self.gainBox)
        vbox1.addLayout(hboxGain)
        
        
        
        vbox1.setContentsMargins(0,0,0,0)
        vbox1.addStretch(1)
        self.vbox1=vbox1
        
        ### affichage image###
        
        cameraWidget=QWidget()
        cameraWidget.setLayout(vbox1)
        cameraWidget.setMinimumSize(150,200)
        cameraWidget.setMaximumSize(200,900)
        hMainLayout=QHBoxLayout()
        hMainLayout.addWidget(cameraWidget)
        
        self.visualisation=SEE(confpath=self.confVisu,confMot=None) ## Widget for visualisation and tools  self.confVisu permet d'avoir plusieurs camera et donc plusieurs fichier ini de visualisation
        
        vbox2=QVBoxLayout() 
        vbox2.addWidget(self.visualisation)
        hMainLayout.addLayout(vbox2)
        
        self.setLayout(hMainLayout)
        
        
    def actionButton(self):
        self.runButton.clicked.connect(self.acquireMultiImage)
        self.stopButton.clicked.connect(self.stopAcq)
        self.hSliderShutter.sliderMoved.connect(self.mSliderShutter)
        self.shutterBox.editingFinished.connect(self.shutter)
        self.hSliderGain.sliderMoved.connect(self.mSliderGain)
        self.gainBox.editingFinished.connect(self.gain)
        self.trigg.currentIndexChanged.connect(self.Trig)
#       self.oneButton.clicked.connect(self.acquireOneImage)
        
    def shutter(self):
        sh=self.shutterBox.value() # 
        self.hSliderShutter.setValue(sh) # set value of slider
        time.sleep(0.1)
        self.cam0.exposure.auto=False
        self.cam0.setExposure(sh/1000)
#        self.cam0.setExposure(int(1000))
        
        self.confCCD.setValue(self.nbcam+"/shutter",int(sh))
        self.confCCD.sync()
        
    def mSliderShutter(self): # for shutter slider 
        sh=self.hSliderShutter.value() 
        self.shutterBox.setValue(sh) # 
        time.sleep(0.1)
        self.cam0.setExposure(sh/1000) # Set shutter CCD in microseconde
        self.confCCD.setValue(self.nbcam+"/shutter",float(sh))   
       


    
         
    def gain(self):
        g=self.gainBox.value() # 
        self.hSliderGain.setValue(g) # set slider value
        time.sleep(0.1)
        self.cam0.gain.value=int(g)
        self.confCCD.setValue(self.nbcam+"/gain",float(g))
#        print("gain:",self.cam0.gain.value)
        
    def mSliderGain(self):
        g=self.hSliderGain.value()
        self.gainBox.setValue(g) # set valeur de la box
        time.sleep(0.1)
        self.cam0.gain.value=int(g)
        self.confCCD.setValue(self.nbcam+"/gain",float(g))
        self.confCCD.sync()   
        
    def Trig(self):
        self.itrig=self.trigg.currentIndex()
        
        if self.itrig==0:
            self.cam0.enable.trigger(False)
#            print ("trigger OFF")
        if self.itrig==1:
            self.cam0.enable_trigger(True)
#            print("Trigger ON")
        if self.itrig==2:
            
            self.seuil, ok=QInputDialog.getInt(self,'THRESHOLD',' Threshold value(<256)')
            if self.seuil>256:
                self.seuil=256
        
    def acquireMultiImage(self):   
        #print('live...')
        
        self.runButton.setEnabled(False)
        self.runButton.setStyleSheet("QPushButton:!pressed{border-image: url(./icons/Circled Play-595b40b65ba036ed117d436f.svg);background-color: gray ;border-color: rgb(0, 0, 0,0);}""QPushButton:pressed{image: url(./icons/Circled Play-595b40b65ba036ed117d436f.svg);background-color: gray ;border-color: rgb(0, 0, 0)}")
        #self.runButton.setStyleSheet("background-color:gray")
        try:
            self.threadRunAcq=ThreadRunAcq(self)
            self.threadRunAcq.newDataRun.connect(self.Display)
            self.threadRunAcq.start()
        except :
            pass
    
    
    def acquireOneImage(self):   
        
        
        self.runButton.setEnabled(False)
        self.runButton.setStyleSheet("QPushButton:!pressed{border-image: url(./icons/Circled Play-595b40b65ba036ed117d436f.svg);background-color: gray ;border-color: rgb(0, 0, 0,0);}""QPushButton:pressed{image: url(./icons/Circled Play-595b40b65ba036ed117d436f.svg);background-color: gray ;border-color: rgb(0, 0, 0)}")
        #self.runButton.setStyleSheet("background-color:gray")
        try:
            self.threadOneAcq=ThreadOneAcq(self)
            self.threadOneAcq.newDataOne.connect(self.Display)
            self.threadOneAcq.start()
        except :
            print('error')
            pass
        self.runButton.setEnabled(True)
        self.runButton.setStyleSheet("QPushButton:!pressed{border-image: url(./icons/Circled Play-595b40b65ba036ed117d436f.svg);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0,0);}""QPushButton:pressed{image: url(./icons/Circled Play-595b40b65ba036ed117d436f.svg);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0)}")
        
    
    
    def stopAcq(self):
#        print('Stop live')
        try:
            self.threadRunAcq.stopThreadRunAcq()
        except :
            pass
        self.runButton.setEnabled(True)
        #self.runButton.setStyleSheet("background-color: rgb(0, 200, 0)")
        self.runButton.setStyleSheet("QPushButton:!pressed{border-image: url(./icons/Circled Play-595b40b65ba036ed117d436f.svg);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0,0);}""QPushButton:pressed{image: url(./icons/Circled Play-595b40b65ba036ed117d436f.svg);background-color: rgb(0, 0, 0,0) ;border-color: rgb(0, 0, 0)}")
        
        #self.threadAcq.terminate()    
        
    def Display(self,data):
        '''Display data with Visu module
        '''
        self.data=data
        self.visualisation.newDataReceived(self.data) # send data to visualisation widget
    
    
        
    def bloquer(self): # bloque la croix 
        self.bloqq=1
        self.confCCD.setValue(self.nbcam+"/xc",int(self.xc)) # save cross postion in ini file
        self.confCCD.setValue(self.nbcam+"/yc",int(self.yc))
        print('xc',self.xc,'yc',self.yc)
        
        
    def debloquer(self): # deblaoque la croix : elle bouge avec la souris
        self.bloqq=0
    
    def roiChanged(self):
        self.rx=self.ro1.size()[0]
        self.ry=self.ro1.size()[1]
        self.confCCD.setValue(self.nbcam+"/rx",int(self.rx))
        self.confCCD.setValue(self.nbcam+"/ry",int(self.ry))
        
        
    def mouseMoved(self,evt):
        ## pour que la cross suive le mvt de la souris
        if self.bloqq==0: # souris non bloquer
            pos = evt[0]  ## using signal proxy turns original arguments into a tuple
            if self.p1.sceneBoundingRect().contains(pos):
                mousePoint = self.vb.mapSceneToView(pos)
                self.xc = (mousePoint.x())
                self.yc= (mousePoint.y())
                if ((self.xc>0 and self.xc<self.data.shape[0]) and (self.yc>0 and self.yc<self.data.shape[1]) ):
                        self.vLine.setPos(self.xc)
                        self.hLine.setPos(self.yc) # la croix ne bouge que dans le graph       
                        self.ro1.setPos([self.xc-(self.rx/2),self.yc-(self.ry/2)])
                        
    
    
            
    def paletteup(self):
        levels=self.imh.getLevels()
        if levels[0]==None:
            xmax =self.data.max()
            xmin=self.data.min()
        else :
            xmax=levels[1]
            xmin=levels[0]
            
        self.imh.setLevels([xmin, xmax+(xmax- xmin) / 10])
        #hist.setImageItem(imh,clear=True)
        self.hist.setHistogramRange(xmin,xmax)

    def palettedown(self):
        levels=self.imh.getLevels()
        if levels[0]==None:
            xmax=self.data.max()
            xmin=self.data.min()
        else :
            xmax=levels[1]
            xmin=levels[0]
            
        self.imh.setLevels([xmin, xmax- (xmax- xmin) / 10])
        #hist.setImageItem(imh,clear=True)
        self.hist.setHistogramRange(xmin,xmax)
    
    
    def open_widget(self,fene):
        """ open new widget 
        """

        if fene.isWinOpen==False:
            fene.setup
            fene.isWinOpen=True
            
            #fene.Display(self.data)
            fene.show()
        else:
            #fene.activateWindow()
#            fene.raise_()
#            fene.showNormal()
            pass
            
    def Measurement(self) :
        self.winM.setFile(self.camName)
        self.open_widget(self.winM)
        self.winM.Display(self.data)
        
    def closeEvent(self,event):
        self.fin()
        event.accept()
    
    
    def fin(self):
        try :
            self.threadRunAcq.stopThreadRunAcq()
        except :
            pass
        try :
            self.cam0.close()
        except :
            pass
        exit  
        
        
class ThreadRunAcq(QtCore.QThread):
    
    newDataRun=QtCore.Signal(object)
    
    def __init__(self, parent=None):
        
        super(ThreadRunAcq,self).__init__(parent)
        self.parent=parent
        self.cam0 = self.parent.cam0
        self.stopRunAcq=False
        self.itrig= self.parent.itrig
        self.seuil=self.parent.seuil
        
        
    def run(self):
        
        global data
        self.cam0.reset_frame_ready()
        self.cam0.start_live(show_display=False)
        self.cam0.enable_trigger(True)
        if not self.cam0.callback_registered:
            self.cam0.register_frame_ready_callback()
            
            
        #print('-----> Start  multi acquisition')
        
        while True :
            self.cam0.reset_frame_ready()
            if self.stopRunAcq:
                break
            
            #print('-----> Acquisition ended')
            
            if self.itrig==0 or self.itrig==2 : # si cam pas en mode trig externe on envoi un trig soft...
                self.cam0.send_trigger()
               # print('trigg')
            self.cam0.wait_til_frame_ready(2000)
            data1 = self.cam0.get_image_data() 
            data1 = np.array(data1)#, dtype=np.double)
            data1.squeeze()
            data=data1[:,:,0]
            self.data=np.rot90(data,1)
            
            if self.itrig==2:
                dataF=gaussian_filter(self.data,3)
                self.maxx=round(dataF.max(),3)
               
                if self.maxx>=self.seuil:
                    self.newDataRun.emit(self.data)   
                else: 
                    pass
                
            else :
                self.newDataRun.emit(self.data)
            
    def stopThreadRunAcq(self):
        #self.cam0.send_trigger()
        try :
            self.stopRunAcq=True
        except : 
            pass
        self.cam0.stop_live()
        
class ThreadOneAcq(QtCore.QThread):
    
    newDataOne=QtCore.Signal(object)
    
    def __init__(self, parent=None):
        
        super(ThreadOneAcq,self).__init__(parent)
        self.parent=parent
        self.cam0 = self.parent.cam0
        self.stopOneAcq=False
        self.itrig= self.parent.itrig
        
    def run(self):
        
        global data
        self.cam0.reset_frame_ready()
        self.cam0.start_live(show_display=False)
        self.cam0.enable_trigger(True)
        if not self.cam0.callback_registered:
            self.cam0.register_frame_ready_callback()
            
      
        
        self.cam0.reset_frame_ready()
     
        
        if self.itrig==0: # si cam pas en mode trig externe on envoi un trig soft...
            self.cam0.send_trigger()
           # print('trigg')
        self.cam0.wait_til_frame_ready(2000)
        data1 = self.cam0.get_image_data() 
        data1 = np.array(data1)#, dtype=np.double)
        data1.squeeze()
        data=data1[:,:,0]
        data=np.rot90(data,1)
        self.newDataOne.emit(data)
        print('send data one acq')
        self.cam0.stop_live()
        print('stop one acq')
        
    def stopThreadOneAcq(self):
        #self.cam0.send_trigger()
        try :
            self.stopOneAcq=True
        except : 
            pass
        self.cam0.stop_live()

if __name__ == "__main__":
    appli = QApplication(sys.argv)  
    e = CameraAcqD(name='cam0',visuGauche=True)  
    e.show()
    appli.exec_()         