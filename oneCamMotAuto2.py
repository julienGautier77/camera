# -*- coding: utf-8 -*-
"""
Created on Wed Sep 11 16:51:01 2019

@author: SALLEJAUNE
"""

from PyQt5.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QWidget,QPushButton
from PyQt5 import QtCore
import sys

from TiltGuiLight import TILTMOTORGUI
import qdarkstyle
import pathlib,os,time
from PyQt5.QtGui import QIcon
from scipy.ndimage.filters import gaussian_filter

from baslerVisionLight import CAMERABASLERACQ
import numpy as np
import pyqtgraph as pg
from scipy import ndimage

from pypylon import pylon

class CAMMOT(QWidget) :
    
    def __init__(self,name=None,motOn=False,motLat=None,motorTypeName0=None, motVert=None,motorTypeName1=None,nomWin='',nomTilt='',unit=1,jogValue=1,visuGauche=False,parent=None):
        super(CAMMOT, self).__init__(parent)
        self.parent=parent
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        
        self.unit=unit
        self.jogValue=jogValue
        self.nomWin=nomWin
        p = pathlib.Path(__file__)
        sepa=os.sep
        self.icon=str(p.parent) + sepa + 'icons' +sepa
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.confCCD = QtCore.QSettings('confCameras.ini', QtCore.QSettings.IniFormat)
        if name==None:
            self.nbcam='camTest'
        else:   
            self.nbcam=name
        self.camType=self.confCCD.value(self.nbcam+"/camType")
        
        if self.camType == 'basler':
            #print('Basler ccd')
            print(name)
            self.cam=CAMERABASLERACQ(name=name,conf=self.confCCD)
        
        self.xlim=int(self.confCCD.value(self.nbcam+"/rx"))/2
        self.ylim=int(self.confCCD.value(self.nbcam+"/ry"))/2
        
        if motLat==None and motOn==True:
            motLat=str(self.cam.confCCD.value(self.cam.nbcam+"/motLat"))
            print(motLat)
        if motVert==None and motOn==True:
            motVert=str(self.cam.confCCD.value(self.cam.nbcam+"/motVert")   ) 
        
        if motorTypeName0==None and motOn==True:
            motorTypeName0=str(self.cam.confCCD.value(self.cam.nbcam+"/motorTypeNameLat"))
        
        if motorTypeName1==None and motOn==True:
            motorTypeName1=str(self.cam.confCCD.value(self.cam.nbcam+"/motorTypeNameVert"))
            
            
        self.motLat=motLat
        self.motorTypeName0=motorTypeName0
        self.motVert=motVert
        self.motorTypeName1=motorTypeName1
        
        self.motor=TILTMOTORGUI(motLat=self.motLat,motorTypeName0=self.motorTypeName0, motVert=self.motVert,motorTypeName1=self.motorTypeName1,nomWin=self.nomWin,nomTilt='',unit=self.unit,jogValue=self.jogValue)
        
        if motOn==True:
            
            self.motor.startThread2()
        
            self.motor.haut.setAutoRepeat(True)
            self.motor.bas.setAutoRepeat(True)
            self.motor.gauche.setAutoRepeat(True)
            self.motor.droite.setAutoRepeat(True)
            self.pasY=float(self.confCCD.value(self.nbcam+"/pasY"))
            self.pasX=float(self.confCCD.value(self.nbcam+"/pasX"))
            
        if motOn==False:  
            self.motor.setEnabled(False)

            
        self.setup()
        self.actionButton()
       
    
    def setup(self):    
        
        vbox=QVBoxLayout() 
        self.hbox=QHBoxLayout()
        
        self.cam.vbox1.addWidget(self.motor)
        self.cam.vbox1.addStretch(2)
        vbox.addWidget(self.cam)
        
        self.align=QPushButton('Alignement')
        self.hbox.addWidget(self.align)
        self.closeLoop=QPushButton('Close Loop')
        self.hbox.addWidget(self.closeLoop)
        self.stopAlign=QPushButton('Stop Auto align')
        self.stopAlign.setStyleSheet("background-color: red")
        self.hbox.addWidget(self.stopAlign)
        vbox.addLayout(self.hbox)
        #vbox.addStretch(1)
        self.setLayout(vbox)
        self.setWindowTitle(self.cam.cameName)
        
    def actionButton(self):
        self.align.clicked.connect(self.Align)
        self.closeLoop.clicked.connect(self.CloseLoop)
        self.stopAlign.clicked.connect(self.STOPAlign)
    
    def Align(self):
        self.align.setEnabled(False)
        self.closeLoop.setEnabled(False)
        self.xr=int(self.cam.confCCD.value(self.cam.nbcam+"/xc"))
        self.yr=int(self.cam.confCCD.value(self.cam.nbcam+"/yc"))
        self.cam.stopAcq()
        time.sleep(0.5)
        self.xlim=int(self.confCCD.value(self.nbcam+"/rx"))/2
        self.ylim=int(self.confCCD.value(self.nbcam+"/ry"))/2
        self.threadalign=ThreadALIGNEMENT(self)
        self.threadalign.newDataRun.connect(self.Display)#cam0=self.cam.cam0,xr=self.xr,yr=self.yr,motor=self.motor,cam=self.cam)
        self.threadalign.start() 
    
    
    
    def Display(self,data):
        self.dataAlign=data
        self.cam.Display(self.dataAlign)
    
    def CloseLoop(self):
        self.closeLoop.setEnabled(False)
        self.align.setEnabled(False)
        self.xr=int(self.cam.confCCD.value(self.cam.nbcam+"/xc"))
        self.yr=int(self.cam.confCCD.value(self.cam.nbcam+"/yc"))
        self.cam.stopAcq()
        time.sleep(0.1)
        self.threadCloseLoop=ThreadCLOSELOOP(self)
        self.threadCloseLoop.start() 
   
    def closeEvent(self,event):
        self.STOPAlign()
        event.accept()
        
    def STOPAlign(self):
        self.motor.StopMot()
        self.align.setEnabled(True)
        self.closeLoop.setEnabled(True)
        self.cam.stopAcq()
        try :
            self.threadalign.stopThreadALIGNEMENT()
            
        except :
            print('error')
            pass
        try :
            self.threadCloseLoop.stopThreadCLOSELOOP() 
        except :
            print('error CL')
            pass 
        
        
        
        
class ThreadALIGNEMENT(QtCore.QThread):
    newDataRun=QtCore.Signal(object)
    
    def __init__(self,parent=None):
        
        super(ThreadALIGNEMENT,self).__init__(parent)
        self.parent=parent
        self.cam0 = self.parent.cam.cam0   
        self.motor=self.parent.motor
        self.pasY=self.parent.pasY#1 pixel 2 pas motor
        self.pasX=self.parent.pasX
        self.xr=self.parent.xr
        self.yr=self.parent.yr
        self.cam=self.parent.cam #le widget
        self.vLine = pg.InfiniteLine(angle=90, movable=False,pen='r')
        self.hLine = pg.InfiniteLine(angle=0, movable=False,pen='r')
#        self.ro1=pg.EllipseROI([10,10],[2,2],pen='r')
        self.cam.p1.addItem(self.vLine)
        self.cam.p1.addItem(self.hLine)
#        self.cam.p1.addItem(self.ro1)
        self.stopAlignment=False
        self.camType= self.parent.camType
        
        
    def acquireOneImage(self):
        
        if self.camType == 'imgSource':
            self.cam0.reset_frame_ready()
            self.cam0.start_live(show_display=False)
            self.cam0.enable_trigger(True)
            if not self.cam0.callback_registered:
                self.cam0.register_frame_ready_callback()  
            self.cam0.reset_frame_ready()
         
            self.itrig=1
            if self.itrig==0: # si cam pas en mode trig externe on envoi un trig soft...
                self.cam0.send_trigger()
               # print('trigg')
            self.cam0.wait_til_frame_ready(2000)
            data1 = self.cam0.get_image_data() 
            data1 = np.array(data1)#, dtype=np.double)
            data1.squeeze()
            data=data1[:,:,0]
            self.dataAlign=np.rot90(data,1)
            self.cam0.stop_live()
        
        if self.camType == 'basler':
            self.converter=pylon.ImageFormatConverter()
            data=self.cam0.GrabOne(200000)

            data1=self.converter.Convert(data)
            
            data1 = data1.GetArray()#, dtype=np.double)
            data1.squeeze()
#            data=data1[:,:,0]
            self.dataAlign=np.rot90(data1,1)
        
        
        
        self.newDataRun.emit(self.dataAlign)
    
    
    def run(self):
        # self.stopAlignment=False
        self.xlim=self.parent.xlim
        self.ylim=self.parent.ylim
        self.xr=self.parent.xr
        self.yr=self.parent.yr
        print('limit',self.xlim,self.ylim)
        self.cam.stopAcq()
        time.sleep(0.1)
        print('start align')
        
        self.acquireOneImage()
        
        time.sleep(0.1)
        for i in range(50):
            print(i)
            if self.stopAlignment==True:
                break
            dataF=gaussian_filter(self.dataAlign,3)
            self.maxx=round(dataF.max(),3)

            thresholded_image = np.copy(self.dataAlign) 
            threshold=0.1
            # remove possible offset
            minn = thresholded_image.min() # remove any offset        
            thresholded_image -= minn
            
            # remove all values less than threshold*max
            minn = int(self.maxx*threshold)
            np.place(thresholded_image, thresholded_image<minn, 0)

            self.xec, self.yec= ndimage.center_of_mass(thresholded_image)
#            yc, xc, self.dy, self.dx, phi = basic_beam_size(thresholded_image)
            self.vLine.setPos(self.xec)
            self.hLine.setPos(self.yec)
#            self.ro1.setSize([self.dx/2,self.dy/2])
#            self.ro1.setPos([self.xec-(int(self.dx)/4),self.yec-int((self.dy)/4)])
            
            self.deltaX=int(self.xr)-int(self.xec)
            self.deltaY=int(self.yr)-int(self.yec)
            print('delta',self.deltaX,self.deltaY)
            print('xec',self.xec,self.yec,self.xr,self.yr)
            if self.maxx<30 :
                print('signal too low')
                
            else:
                if self.deltaY<self.ylim and self.xlim<self.xlim:
                    print('break')
                    break
                if abs(self.deltaX)>=self.xlim:
                    print('on bouge en X  de ',self.deltaX*self.pasX)
                    if self.motor.inv[0]==True:
                        self.motor.MOT[0].rmove(-self.deltaX*self.pasX)
                       
                    else:
                        self.motor.MOT[0].rmove(self.deltaX*self.pasX)
    #            else : pass
    #                if self.motor.inv[0]==True:
    #                    self.motor.MOT[0].rmove(-1*np.sign(self.deltaX))
    #                else:
    #                    self.motor.MOT[0].rmove(1*np.sign(self.deltaX))
    #            
                
                time.sleep(0.3)
                
                
                if abs(self.deltaY)>self.ylim:
                    print('on bouge en Y  de ',self.deltaY*self.pasY)
                    if self.motor.inv[1]==True:
                        self.motor.MOT[1].rmove(-self.deltaY*self.pasY)
                    else :
                        self.motor.MOT[1].rmove(self.deltaY*self.pasY)
                else : pass
    #                if self.motor.inv[1]==True:
    #                    self.motor.MOT[1].rmove(-1*np.sign(self.deltaY))
    #                else:
    #                    self.motor.MOT[1].rmove(1*np.sign(self.deltaY))
               
                
                time.sleep(0.3)
#            while True:
#                if self.stopAlignment==True:
#                    break
#                print ('wait motor to position')
#                pos0=int(self.motor.MOT[0].position())
#                pos1=int(self.motor.MOT[1].position())
#                print(pos0,pos1,posi0+self.deltaX*self.pasX,posi0-self.deltaX*self.pasX,posi1+self.deltaY*self.pasY,posi1-self.deltaY*self.pasY)
#                if pos0==int(posi0+self.deltaX*self.pasX) and pos1==int(posi1+self.deltaY*self.pasY ):
#                    print('a')
#                    break
#                if pos0==int(posi0-self.deltaX*self.pasX) and pos1==int(posi1-self.deltaY*self.pasY ):
#                    print('b')
#                    break
#                if pos0==int(posi0+self.deltaX*self.pasX )and pos1==int(posi1-self.deltaY*self.pasY) :
#                    break
#                if pos0==int(posi0-self.deltaX*self.pasX) and pos1==int(posi1+self.deltaY*self.pasY ):
#                    break
            
            
            self.acquireOneImage()
            time.sleep(0.3)
            
        self.parent.STOPAlign()
        self.cam.p1.removeItem(self.vLine)
        self.cam.p1.removeItem(self.hLine)
#        self.cam.p1.removeItem(self.ro1)
            
    def stopThreadALIGNEMENT(self):
        
        self.stopAlignment=True
        try :
            self.cam.p1.removeItem(self.vLine)
            self.cam.p1.removeItem(self.hLine)
        except : pass

class ThreadCLOSELOOP(QtCore.QThread):
    
    def __init__(self,parent=None):
        super(ThreadCLOSELOOP,self).__init__(parent)
        self.parent=parent
        self.cam0 = self.parent.cam.cam0   
        self.motor=self.parent.motor
        self.pasY=self.parent.pasY#1 pixel 2 pas motor
        self.pasX=self.parent.pasX#166.67
        
        self.xr=self.parent.xr
        self.yr=self.parent.yr
        self.cam=self.parent.cam #le widget
        self.vLine = pg.InfiniteLine(angle=90, movable=False,pen='r')
        self.hLine = pg.InfiniteLine(angle=0, movable=False,pen='r')

        self.cam.p1.addItem(self.vLine)
        self.cam.p1.addItem(self.hLine)
        self.stopCloseLoop=False
        self.camType= self.parent.camType
        
        
    def acquireOneImage(self):
        
        if self.camType == 'imgSource':
            self.cam0.reset_frame_ready()
            self.cam0.start_live(show_display=False)
            self.cam0.enable_trigger(True)
            if not self.cam0.callback_registered:
                self.cam0.register_frame_ready_callback()  
            self.cam0.reset_frame_ready()
         
            self.itrig=1
            if self.itrig==0: # si cam pas en mode trig externe on envoi un trig soft...
                self.cam0.send_trigger()
               # print('trigg')
            self.cam0.wait_til_frame_ready(2000)
            data1 = self.cam0.get_image_data() 
            data1 = np.array(data1)#, dtype=np.double)
            data1.squeeze()
            data=data1[:,:,0]
            self.dataAlign=np.rot90(data,1)
            self.cam0.stop_live()
        
        if self.camType == 'basler':
            self.converter=pylon.ImageFormatConverter()
            data=self.cam0.GrabOne(200000)

            data1=self.converter.Convert(data)
            data1 = data1.GetArray()#, dtype=np.double)
            data1.squeeze()
#            data=data1[:,:,0]
            self.dataAlign=np.rot90(data1,1)
            
        self.cam.Display(self.dataAlign)
    
    
    def run(self):
       
        self.cam.stopAcq()
        print('start close loop')
        
        self.acquireOneImage()
        
        time.sleep(0.1)
        while True:

            if self.stopCloseLoop==True:
                break
            dataF=gaussian_filter(self.dataAlign,3)
            self.maxx=round(dataF.max(),3)

            thresholded_image = np.copy(self.dataAlign) 
            threshold=0.1
            # remove possible offset
            minn = thresholded_image.min() # remove any offset        
            thresholded_image -= minn
            
            # remove all values less than threshold*max
            minn = int(self.maxx*threshold)
            np.place(thresholded_image, thresholded_image<minn, 0)

            self.xec, self.yec= ndimage.center_of_mass(thresholded_image)
#            yc, xc, self.dy, self.dx, phi = basic_beam_size(thresholded_image)
            self.vLine.setPos(self.xec)
            self.hLine.setPos(self.yec)

            self.deltaX=int(self.xr)-int(self.xec)
            self.deltaY=int(self.yr)-int(self.yec)
           
            if self.maxx<30 :
                print('signal too low')
                

#            if abs(self.deltaX*self.pasX)>5 and self.maxx>30 :
#                print('on bouge en X  de ',self.deltaX*self.pasX)
#                if self.motor.inv[0]==True:
#                    self.motor.MOT[0].rmove(-self.deltaX*self.pasX)
#                   
#                else:
#                    self.motor.MOT[0].rmove(self.deltaX*self.pasX)
#            
#            
#            
#            time.sleep(0.3)
#            
#            
#            if abs(self.deltaY*self.pasY)>5 and self.maxx>30:
#                print('on bouge en Y  de ',self.deltaY*self.pasY)
#                if self.motor.inv[1]==True:
#                    self.motor.MOT[1].rmove(-self.deltaY*self.pasY)
#                else :
#                    self.motor.MOT[1].rmove(self.deltaY*self.pasY)
            
           
            
            time.sleep(0.3)

            
            self.acquireOneImage()
            time.sleep(0.3)
            
        self.parent.STOPAlign()    
        self.cam.p1.removeItem(self.vLine)
        self.cam.p1.removeItem(self.hLine)

            
    def stopThreadCLOSELOOP(self):
        
        self.stopCloseLoop=True
        try :
            self.cam.p1.removeItem(self.vLine)
            self.cam.p1.removeItem(self.hLine)
        except :pass




    
        
if __name__ == "__main__":
    appli = QApplication(sys.argv)  
    e = CAMMOT(name="cam11",motOn=True,visuGauche=True,motLat='NF_Lat_P1',motorTypeName0='NewFocus', motVert='Lolita_P1_Vert',motorTypeName1='RSAI',nomWin='Tilts')
    e.show()
   
    appli.exec_()         