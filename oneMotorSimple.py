#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 16 15:49:41 2019

@author: juliengautier
"""


#%%Import
from PyQt6 import QtCore
from PyQt6.QtWidgets import QWidget
from PyQt6.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QPushButton,QDoubleSpinBox
from PyQt6.QtWidgets import QComboBox,QLabel
from PyQt6.QtGui import QIcon
import sys,time,os
import qdarkstyle
import pathlib
from PyQt6.QtCore import Qt
import __init__

__version__=__init__.__version__

class ONEMOTOR(QWidget) :

    def __init__(self, mot0='',motorTypeName0='',nomWin='',unit=2,jogValue=1):
                 
        super(ONEMOTOR, self).__init__()
        p = pathlib.Path(__file__)
        sepa=os.sep
        self.icon=str(p.parent) + sepa + 'icons' +sepa
        self.motor=str(mot0)
        self.isWinOpen=False
        self.motorTypeName=motorTypeName0
        self.indexUnit=unit
        self.configPath=str(p.parent)+sepa+"fichiersConfig"+sepa
        self.isWinOpen=False
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.jogValue=jogValue
        self.version=__version__
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        
        if self.motorTypeName=='RSAI':
            self.configMotName='configMoteurRSAI.ini'
            import moteurRSAI as RSAI
            self.motorType=RSAI
            self.MOT=self.motorType.MOTORRSAI(self.motor)
            
        elif self.motorTypeName=='SmartAct':
             self.configMotName='configMoteurSmartAct.ini'
             import smartactmot as SmartAct
             self.motorType=SmartAct
             self.MOT=self.motorType.MOTORSMART(self.motor)
             
        elif self.motorTypeName=='A2V':
             self.configMotName='configMoteurA2V.ini'
             import moteurA2V  as A2V
             self.motorType=A2V
             self.MOT=self.motorType.MOTORA2V(self.motor)
             
        elif self.motorTypeName=='NewFocus':
             self.configMotName='configMoteurNewFocus.ini'
             import moteurNewFocus as NewFoc
             self.motorType=NewFoc
             self.MOT=self.motorType.MOTORNEWFOCUS(self.motor)
             
        elif self.motorTypeName=='newport':
             self.configMotName='confNewport.ini'
             import newportMotors as Newport
             self.motorType=Newport
             self.MOT=self.motorType.MOTORNEWPORT(self.motor)
             
        elif self.motorTypeName=='Servo':
             self.configMotName='configMoteurServo.ini'
             import servo as servo
             self.motorType=servo
             self.MOT=self.motorType.MOTORSERVO(self.motor)
             
        elif self.motorTypeName=='Arduino':
             self.configMotName='configMoteurArduino.ini'
             import moteurArduino as arduino
             self.motorType=arduino
             self.MOT=self.motorType.MOTORARDUINO(self.motor)
        
        elif self.motorTypeName=='Apt':
             self.configMotName='configMoteurApt.ini'
             import moteurApt as apt
             self.motorType=apt
             self.MOT=self.motorType.MOTORAPT(self.motor)
             
        else:
            print('Error config motor Type name: Motor Test used')
            self.configMotName='configMoteurTest.ini'
            import moteurtest as test
            self.motorType=test
            self.MOT=self.motorType.MOTORTEST(self.motor)
            
        self.configMotName=self.configPath+ self.configMotName  
        
        self.conf=QtCore.QSettings(self.configMotName, QtCore.QSettings.Format.IniFormat) # fichier config motor fichier .ini
        
        self.name=str(self.conf.value(self.motor+"/Name"))
        self.setWindowTitle(nomWin+' : '+ self.name+'                     V.'+str(self.version))
        
        self.stepmotor=float(self.conf.value(self.motor+"/stepmotor"))
        self.butePos=float(self.conf.value(self.motor+"/buteePos"))
        self.buteNeg=float(self.conf.value(self.motor+"/buteeneg"))
    
    
        self.thread2=PositionThread(mot=self.MOT,motorType=self.motorType) # thread pour afficher position
        self.thread2.POS.connect(self.Position)
        
        self.setup()
        ## initialisation of the jog value 
        if self.indexUnit==0: #  step
            self.unitChange=1
            self.unitName='step'
            
        if self.indexUnit==1: # micron
            self.unitChange=float((1*self.stepmotor)) 
            self.unitName='um'
        if self.indexUnit==2: #  mm 
            self.unitChange=float((1000*self.stepmotor))
            self.unitName='mm'
        if self.indexUnit==3: #  ps  double passage : 1 microns=6fs
            self.unitChange=float(1*self.stepmotor/0.0066666666) 
            self.unitName='ps'
        if self.indexUnit==4: #  en degres
            self.unitChange=1 *self.stepmotor
            self.unitName='°'    
        self.actionButton()
        self.unit()
        
    def startThread2(self):
        self.thread2.ThreadINIT()
        self.thread2.start()
        
    def setup(self):
        
        vbox1=QVBoxLayout()
        hbox1=QHBoxLayout()
        title=QLabel(self.motor)
        title.setStyleSheet("font: bold 14pt" )
        title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        
        self.position=QLabel('123455')
        self.position.setMaximumHeight(40)
        self.position.setStyleSheet("font: bold 12pt" )
        
        self.unitButton=QComboBox()
        self.unitButton.addItem('Step')
        self.unitButton.addItem('um')
        self.unitButton.addItem('mm')
        self.unitButton.addItem('ps')
        self.unitButton.setMinimumWidth(50)
        self.unitButton.setMaximumWidth(50)
        self.unitButton.setCurrentIndex(self.indexUnit)
        
        self.zeroButton=QPushButton('Zero')
        
        vbox1.addWidget(title)
        hbox1.addWidget(self.position)
        hbox1.addWidget(self.unitButton)
        hbox1.addWidget(self.zeroButton)
        vbox1.addLayout(hbox1)
        
        
        hbox2=QHBoxLayout()
        self.moins=QPushButton(' - ')
        self.moins.setMinimumWidth(30)
        self.moins.setMinimumHeight(30)
        self.moins.setMaximumWidth(30)
        self.moins.setMaximumHeight(30)
        hbox2.addWidget(self.moins)
        self.jogStep=QDoubleSpinBox()
        self.jogStep.setMaximum(10000)
        self.jogStep.setMinimumWidth(60)
        self.jogStep.setMinimumHeight(0)
        self.jogStep.setMaximumWidth(60)
        self.jogStep.setMaximumHeight(50)
        
        self.jogStep.setValue(self.jogValue)
            
        hbox2.addWidget(self.jogStep)
         
        
        self.plus=QPushButton(' + ')
        self.plus.setMinimumWidth(30)
        self.plus.setMinimumHeight(30)
        self.plus.setMaximumWidth(30)
        self.plus.setMaximumHeight(30)
        hbox2.addWidget(self.plus)
        vbox1.addLayout(hbox2)
        
        self.hbox3=QHBoxLayout()
        
        self.stopButton=QPushButton('STOP')
        self.stopButton.setStyleSheet("background-color: red")
        self.stopButton.setMinimumWidth(30)
        self.stopButton.setMinimumHeight(30)
        self.stopButton.setMaximumWidth(30)
        self.stopButton.setMaximumHeight(30)
        self.hbox3.addWidget(self.stopButton)
        vbox1.addLayout(self.hbox3)
        
        self.setLayout(vbox1)
        
        
    def actionButton(self):
        
        self.plus.clicked.connect(self.pMove) # jog +
        self.plus.setAutoRepeat(True)
        self.moins.clicked.connect(self.mMove)# jog -
        self.moins.setAutoRepeat(True) 
        self.zeroButton.clicked.connect(self.Zero)
        self.stopButton.clicked.connect(self.StopMot)
        self.unitButton.currentIndexChanged.connect(self.unit)
    
    def StopMot(self):
        '''
        stop all motors
        '''
        
        self.MOT.stopMotor()
    
    
    def pMove(self):# action jog +
        print('jog+')
        a=float(self.jogStep.value())
        print(a)
        a=float(a*self.unitChange)
        b=self.MOT.position()
        if b+a<self.buteNeg :
            print( "STOP : Butée Positive")
            self.MOT.stopMotor()
        elif b+a>self.butePos :
            print( "STOP : Butée Négative")
            self.MOT.stopMotor()
        else :
            self.MOT.rmove(a)



    def mMove(self): # action jog -
        a=float(self.jogStep.value())
        a=float(a*self.unitChange)
        b=self.MOT.position()
        if b-a<self.buteNeg :
            print( "STOP : Butée Positive")
            self.MOT.stopMotor()
        elif b-a>self.butePos :
            print( "STOP : Butée Négative")
            self.MOT.stopMotor()
        else :
            self.MOT.rmove(-a)
     
    def Zero(self): # remet le compteur a zero 
        self.MOT.setzero()    
        
    def unit(self):
        '''
        unit change mot foc
        '''
        self.indexUnit=self.unitButton.currentIndex()
        valueJog=self.jogStep.value()*self.unitChange
        if self.indexUnit==0: #  step
            self.unitChange=1
            self.unitName='step'
            
        if self.indexUnit==1: # micron
            self.unitChange=float((1*self.stepmotor)) 
            self.unitName='um'
        if self.indexUnit==2: #  mm 
            self.unitChange=float((1000*self.stepmotor))
            self.unitName='mm'
        if self.indexUnit==3: #  ps  double passage : 1 microns=6fs
            self.unitChange=float(1*self.stepmotor/0.0066666666) 
            self.unitName='ps'
        if self.indexUnit==4: #  en degres
            self.unitChange=1 *self.stepmotor
            self.unitName='°'    
            
        if self.unitChange==0:
            self.unitChange=1 #avoid 0 
            
        self.jogStep.setSuffix(" %s" % self.unitName)
        self.jogStep.setValue(valueJog/self.unitChange)

    def Position(self,Posi): # affichage de la position a l aide du second thread
        
        a=float(Posi)
        #b=a # valeur en pas moteur pour sauvegarder en pas 
        a=round(a/self.unitChange,3) # valeur tenant compte du changement d'unite
        self.position.setText(str(a)) 
    
    def closeEvent(self, event):
        """ 
        When closing the window
        """
        self.fini()
        time.sleep(0.1)
        event.accept() 
        
    def fini(self): # a la fermeture de la fenetre on arrete le thread secondaire
        self.thread2.stopThread()
        self.isWinOpen=False
        time.sleep(0.1)      
        

#%%#################################################################################       
class PositionThread(QtCore.QThread):
    ### thread secondaire pour afficher la position
    
    POS=QtCore.pyqtSignal(float) # signal transmit par le second thread au thread principal pour aff la position
    def __init__(self,parent=None,mot='',motorType=''):
        super(PositionThread,self).__init__(parent)
        self.MOT=mot
        self.motorType=motorType
        self.stop=False
        
    def run(self):
        while True:
            if self.stop==True:
                break
            else:
                
                Posi=(self.MOT.position())
                time.sleep(1)
                try :
                    self.POS.emit(Posi)
                    
                    time.sleep(0.1)
                except:
                    print('error emit')
                    
    def ThreadINIT(self):
        self.stop=False    
                         
    def stopThread(self):
        self.stop=True
        time.sleep(0.1)
        self.terminate()


        
if __name__ =='__main__':
    motor0="testMot1"
    motorType="test"
    appli=QApplication(sys.argv)
    mot5=ONEMOTOR(mot0=motor0,motorTypeName0=motorType,nomWin='motorSimple',unit=1,jogValue=100)
    mot5.show()
    mot5.startThread2()
    appli.exec_()        
        
