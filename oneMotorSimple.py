#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Tue Apr 16 15:49:41 2019

@author: juliengautier
"""


#%%Import
from PyQt5 import QtCore
from PyQt5.QtWidgets import QWidget
from PyQt5.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QPushButton,QDoubleSpinBox,QToolButton
from PyQt5.QtWidgets import QComboBox,QLabel
from PyQt5.QtCore import Qt

from PyQt5.QtGui import QIcon
import sys,time,os
import qdarkstyle
import pathlib
import __init__



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
        self.configPath="./fichiersConfig/"
        self.isWinOpen=False
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.jogValue=jogValue
        
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
             
        else:
            print('Error config motor Type name')
            self.configMotName='configMoteurTest.ini'
            import moteurtest as test
            self.motorType=test
            self.MOT=self.motorType.MOTORTEST(self.motor)
            
        configMotName=self.configPath+ self.configMotName  
        
        self.conf=QtCore.QSettings(configMotName, QtCore.QSettings.IniFormat) # fichier config motor fichier .ini
        
        self.name=str(self.conf.value(self.motor+"/Name"))
        self.setWindowTitle(nomWin+' : '+ self.name+'                     V.'+str(" "))
        
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
        print('setup')
        vbox1=QVBoxLayout()
        hbox1=QHBoxLayout()
        #pos=QLabel('Pos:')
        #pos.setMaximumHeight(20)
        nameBox=QLabel(self)
        nameBox.setText("Foc")
        nameBox.setAlignment(Qt.AlignCenter)
        nameBox.setStyleSheet('font: bold 15px;color: purple')
        
        self.position=QLabel('1234567')
        self.position.setMaximumHeight(50)
        
        self.position.setStyleSheet("font: bold 10pt" )
        
        self.unitButton=QComboBox()
        self.unitButton.addItem('Step')
        self.unitButton.addItem('um')
        self.unitButton.addItem('mm')
        self.unitButton.addItem('ps')
        self.unitButton.setMinimumWidth(80)
        self.unitButton.setMaximumWidth(80)
        self.unitButton.setStyleSheet("font: bold 8pt" )
        self.unitButton.setCurrentIndex(self.indexUnit)
        size=20
        self.zeroButton=QToolButton()
        self.zeroButton.setText('zero')
        self.zeroButton.setStyleSheet("font: bold 6pt" )
        self.zeroButton.setMaximumWidth(1.5*size)
        self.zeroButton.setStyleSheet('background-color: gray;border-color: gray')
        
        vbox1.addWidget(nameBox)
        hbox1.addWidget(self.position)
        hbox1.addWidget(self.unitButton)
        hbox1.addWidget(self.zeroButton)
        vbox1.addLayout(hbox1)
        
        
        hbox2=QHBoxLayout()
        
        self.moins=QToolButton()
        self.moins.setText('-')
        self.moins.setMinimumWidth(size)
        self.moins.setMaximumWidth(size)
        self.moins.setMinimumHeight(size)
        self.moins.setMaximumHeight(size)
        self.moins.setStyleSheet('background-color: gray;border-color: gray')
        hbox2.addWidget(self.moins)
        
        self.jogStep=QDoubleSpinBox()
        self.jogStep.setMaximum(10000)
        self.jogStep.setMinimumWidth(size*4)
        self.jogStep.setMaximumWidth(size*4)
        self.jogStep.setMinimumHeight(size)
        self.jogStep.setMaximumHeight(size)
        
        self.jogStep.setValue(self.jogValue)
            
        hbox2.addWidget(self.jogStep)
         
        
        self.plus=QToolButton()
        self.plus.setText('+')
        self.plus.setMinimumWidth(size)
        self.plus.setMinimumHeight(size)
        self.plus.setStyleSheet('background-color: gray;border-color: gray')
    
        hbox2.addWidget(self.plus)
        vbox1.addLayout(hbox2)
        
        hbox3=QHBoxLayout()
        self.stopButton=QPushButton('STOP')
        self.stopButton.setMaximumWidth(size*4)
        
        self.stopButton.setStyleSheet("background-color: red")
        hbox3.addWidget(self.stopButton)
        vbox1.addLayout(hbox3)
        self.hbox3=hbox3
        self.vbox1=vbox1
        self.vbox1.addLayout(self.hbox3)
        self.setLayout(self.vbox1)
        
        
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
        a=round(a/self.unitChange,1) # valeur tenant compte du changement d'unite
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
    import time #?
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
    motor0="camLat"
    motorType="RSAI"
    appli=QApplication(sys.argv)
    mot5=ONEMOTOR(mot0=motor0,motorTypeName0=motorType,nomWin='motorSimple',unit=1,jogValue=100)
    mot5.show()
    mot5.startThread2()
    appli.exec_()        
        
