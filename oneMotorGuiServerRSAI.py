#! /home/sallejaune/loaenv/bin/python3.12
# -*- coding: utf-8 -*-
"""
Created on 10 December 2023

@author: Julien Gautier (LOA)
#last modified 18 oct 2024
"""

from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QWidget, QMessageBox, QLineEdit, QToolButton
from PyQt6.QtWidgets import QVBoxLayout, QHBoxLayout, QPushButton, QGridLayout, QDoubleSpinBox, QCheckBox
from PyQt6.QtWidgets import QComboBox, QLabel
from PyQt6.QtGui import QIcon
from PyQt6.QtCore import QRect
import moteurRSAISERVER
import sys
import time
import os
import qdarkstyle
import pathlib

import __init__     
from scanMotor import SCAN

#import TirGui
__version__=__init__.__version__


class ONEMOTORGUI(QWidget) :
    """
    User interface Motor class : 
    ONEMOTOGUI(IpAddress, NoMotor,nomWin,showRef,unit,jogValue )
    IpAddress : Ip adress of the RSAI RACK
    NoMoro : Axis number
    optional :
        nomWin Name of the windows
        ShowRef = True see the reference windows
        unit : 0: step 1: um 2: mm 3: ps 4: °
        jogValue : Value in unit of the jog
    database is update when closing
    """

    def __init__(self, IpAdress, NoMotor, nomWin='', showRef=False, unit=1, jogValue=100, parent=None):
       
        super(ONEMOTORGUI, self).__init__()
        
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(p.parent) + sepa + 'icons' +sepa
        self.isWinOpen = False
        self.nomWin = nomWin
        self.refShowId = showRef
        self.indexUnit = unit
        self.jogValue = jogValue
        self.etat = 'ok'
        self.IpAdress = IpAdress
        self.NoMotor = NoMotor
        self.MOT = [0]
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.iconPlay = self.icon + "playGreen.png"
        self.iconPlay = pathlib.Path(self.iconPlay)
        self.iconPlay = pathlib.PurePosixPath(self.iconPlay)

        self.iconMoins = self.icon + "moinsBleu.png"
        self.iconMoins = pathlib.Path(self.iconMoins)
        self.iconMoins = pathlib.PurePosixPath(self.iconMoins)

        self.iconPlus = self.icon + "plusBleu.png"
        self.iconPlus = pathlib.Path(self.iconPlus)
        self.iconPlus = pathlib.PurePosixPath(self.iconPlus)

        self.iconStop = self.icon + "close.png"
        self.iconStop = pathlib.Path(self.iconStop)
        self.iconStop = pathlib.PurePosixPath(self.iconStop)

        self.iconUpdate = self.icon + "recycle.png"
        self.iconUpdate = pathlib.Path(self.iconUpdate)
        self.iconUpdate = pathlib.PurePosixPath(self.iconUpdate)

        self.MOT[0] = moteurRSAISERVER.MOTORRSAI(self.IpAdress,self.NoMotor)
            
        self.scanWidget = SCAN(MOT=self.MOT[0]) # for the scan
        
        self.stepmotor = [0,0,0]
        self.butePos = [0,0,0]
        self.buteNeg = [0,0,0]
        self.name = [0,0,0]
        for zzi in range(0,1):
            self.stepmotor[zzi] = float((1/self.MOT[0].getStepValue())) # list of stepmotor values for unit conversion
            self.butePos[zzi] = float(self.MOT[0].getButLogPlusValue()) # list 
            self.buteNeg[zzi] = float(self.MOT[0].getButLogMoinsValue())
            self.name[zzi] = str(self.MOT[0].getName())
                ## initialisation of the jog value 
        if self.indexUnit == 0: #  step
            self.unitChange = 1
            self.unitName = 'step'
            
        if self.indexUnit == 1: # micron
            self.unitChange = float((1*self.stepmotor[0])) 
            self.unitName = 'um'
        if self.indexUnit == 2: #  mm 
            self.unitChange = float((self.stepmotor[0])/1000)
            self.unitName = 'mm'
        if self.indexUnit == 3: #  ps  double passage : 1 microns=6fs
            self.unitChange = float(self.stepmotor[0]*0.0066666666) 
            self.unitName = 'ps'
        if self.indexUnit == 4: #  en degres
            self.unitChange = 1 *self.stepmotor[0]
            self.unitName = '°'  

        self.thread = PositionThread(self,mot=self.MOT[0]) # thread for displaying position
        self.thread.POS.connect(self.Position)
        #self.thread.ETAT.connect(self.Etat)
        
        self.setup()
        self.update()
        self.unit()
        self.jogStep.setValue(self.jogValue)
        self.actionButton()
        self.setup_event()
        
    def update(self):
        # update from the server RSAI python 
        self.MOT[0].update()
        # to avoid to access to the database 
        for zzi in range(0,1):
            self.stepmotor[zzi] = float(1/(self.MOT[0].step)) # list of stepmotor values for unit conversion
            self.butePos[zzi] = float(self.MOT[0].butPlus) # list 
            self.buteNeg[zzi] = float(self.MOT[0].butMoins)
            self.name[zzi] = str(self.MOT[0].name)
                ## initialisation of the jog value 
        
        self.setWindowTitle(self.nomWin + str(self.MOT[0].getEquipementName()) + ' ('+ str(self.IpAdress)+ ')  '+ ' [M'+ str(self.NoMotor) + ']  ' + self.name[0] )
        
        self.nom.setText(self.name[0])
        self.refValue = self.MOT[0].refValue     # en micron
        self.refValueStep=[] # en step 
        for ref in self.refValue:

            self.refValueStep.append(ref /self.stepmotor[0]  )

        #print('ref debut init step ',self.refValueStep )
        self.refName = self.MOT[0].refName
        
        iii=0
        for saveNameButton in self.posText: # reference name
            saveNameButton.setText(self.refName[iii]) # print  ref name
            iii+=1   
        eee=0
        for absButton in self.absRef: 
            absButton.setValue(float(self.refValueStep[eee]/self.unitChange)) # )/self.unitChange)) # save reference value
            eee+=1

    def updateDB(self):
        #  update the Data base 
        i = 0
        for ref in self.refValueStep: 
            ref = ref * float((self.stepmotor[0])) # en micron
            a = self.MOT[0].setRefValue(i,int(ref))
            i+=1
        i=0
        for ref in self.refName : 
            self.MOT[0].setRefName(i,ref)
            i+=1
   
    def startThread2(self):
        # start position and state thread
        self.thread.ThreadINIT()
        self.thread.start()
        time.sleep(0.1)
        
    def setup(self):
        vbox1 = QVBoxLayout() 
        hboxTitre = QHBoxLayout()
        self.nom = QLabel(self.name[0])
        self.nom.setStyleSheet("font: bold 15pt;color:yellow")
        hboxTitre.addWidget(self.nom)
        
        self.enPosition = QLineEdit()
        self.enPosition.setMaximumWidth(180)
        self.enPosition.setStyleSheet("font: bold 10pt")
        self.enPosition.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
        hboxTitre.addWidget(self.enPosition)
        self.butNegButt = QCheckBox('Log FDC-',self)
        hboxTitre.addWidget(self.butNegButt)
       
        self.butPosButt = QCheckBox('Log FDC+',self)
        hboxTitre.addWidget(self.butPosButt)
        vbox1.addLayout(hboxTitre)
        
        hShoot = QHBoxLayout()
        self.shootCibleButton = QPushButton('Shot')
        self.shootCibleButton.setStyleSheet("font: 12pt;background-color: red")
        self.shootCibleButton.setMaximumWidth(100)
        self.shootCibleButton.setMinimumWidth(100)
        hShoot.addWidget(self.shootCibleButton)
        self.updateButton = QToolButton()
        self.updateButton.setToolTip( "update from DB")
        self.updateButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconUpdate,self.iconUpdate))
        hShoot.addWidget(self.updateButton)
        vbox1.addLayout(hShoot)
        
        hbox0 = QHBoxLayout()
        self.position = QLabel('1234567')
        self.position.setMaximumWidth(300)
        self.position.setStyleSheet("font: bold 12pt" )
        
        self.unitBouton = QComboBox()
        self.unitBouton.addItem('Step')
        self.unitBouton.addItem('um')
        self.unitBouton.addItem('mm')
        self.unitBouton.addItem('ps')
        self.unitBouton.addItem('°')
        self.unitBouton.setMaximumWidth(100)
        self.unitBouton.setMinimumWidth(100)
        self.unitBouton.setStyleSheet("font: bold 12pt")
        self.unitBouton.setCurrentIndex(self.indexUnit)
        
        self.zeroButton = QPushButton('Zero')
        self.zeroButton.setToolTip('set origin')
        self.zeroButton.setMaximumWidth(50)
        
        hbox0.addWidget(self.position)
        hbox0.addWidget(self.unitBouton)
        hbox0.addWidget(self.zeroButton)
        vbox1.addLayout(hbox0)
        
        hboxAbs=QHBoxLayout()
        absolueLabel = QLabel('Absolue mouvement')

        self.MoveStep = QDoubleSpinBox()
        self.MoveStep.setMaximum(1000000)
        self.MoveStep.setMinimum(-1000000)
        
        self.absMvtButton = QToolButton()
        self.absMvtButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconPlay,self.iconPlay))
        
        self.absMvtButton.setMinimumHeight(50)
        self.absMvtButton.setMaximumHeight(50)
        self.absMvtButton.setMinimumWidth(50)
        self.absMvtButton.setMaximumWidth(50)
        
        hboxAbs.addWidget(absolueLabel)
        hboxAbs.addWidget(self.MoveStep)
        hboxAbs.addWidget(self.absMvtButton)
        vbox1.addLayout(hboxAbs)
        vbox1.addSpacing(10)
        hbox1 = QHBoxLayout()
        self.moins = QToolButton()
        self.moins.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconMoins,self.iconMoins))
        
        self.moins.setMinimumHeight(70)
        self.moins.setMaximumHeight(70)
        self.moins.setMinimumWidth(70)
        self.moins.setMaximumWidth(70)
        
        hbox1.addWidget(self.moins)
        
        self.jogStep = QDoubleSpinBox()
        self.jogStep.setMaximum(1000000)
        self.jogStep.setMaximumWidth(130)
        self.jogStep.setStyleSheet("font: bold 12pt")
        self.jogStep.setValue(self.jogValue)
  
        hbox1.addWidget(self.jogStep)
        
        self.plus = QToolButton()
        self.plus.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconPlus,self.iconPlus))
        self.plus.setMinimumHeight(70)
        self.plus.setMaximumHeight(70)
        self.plus.setMinimumWidth(70)
        self.plus.setMaximumWidth(70)
        hbox1.addWidget(self.plus)
        
        vbox1.addLayout(hbox1)
        vbox1.addSpacing(10)
        
        hbox2 = QHBoxLayout()
        self.stopButton = QToolButton()
        self.stopButton.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconStop,self.iconStop))
        
        self.stopButton.setMaximumHeight(70)
        self.stopButton.setMaximumWidth(70)
        self.stopButton.setMinimumHeight(70)
        self.stopButton.setMinimumWidth(70)
        hbox2.addWidget(self.stopButton)
        vbox2 = QVBoxLayout()
        
        self.showRef = QPushButton('Show Ref')
        self.showRef.setMaximumWidth(90)
        vbox2.addWidget(self.showRef)
        self.scan = QPushButton('Scan')
        self.scan.setMaximumWidth(90)
        vbox2.addWidget(self.scan)
        hbox2.addLayout(vbox2)
        
        vbox1.addLayout(hbox2)
        vbox1.addSpacing(10)
        
        self.REF1 = REF1M(num=1)
        self.REF2 = REF1M(num=2)
        self.REF3 = REF1M(num=3)
        self.REF4 = REF1M(num=4)
        self.REF5 = REF1M(num=5)
        self.REF6 = REF1M(num=6)
        
        grid_layoutRef = QGridLayout()
        grid_layoutRef.setVerticalSpacing(4)
        grid_layoutRef.setHorizontalSpacing(4)
        grid_layoutRef.addWidget(self.REF1,0,0)
        grid_layoutRef.addWidget(self.REF2,0,1)
        grid_layoutRef.addWidget(self.REF3,1,0)
        grid_layoutRef.addWidget(self.REF4,1,1)
        grid_layoutRef.addWidget(self.REF5,2,0)
        grid_layoutRef.addWidget(self.REF6,2,1)
        
        self.widget6REF = QWidget()
        self.widget6REF.setLayout(grid_layoutRef)
        vbox1.addWidget(self.widget6REF)
        self.setLayout(vbox1)
        
        self.absRef = [self.REF1.ABSref,self.REF2.ABSref,self.REF3.ABSref,self.REF4.ABSref,self.REF5.ABSref,self.REF6.ABSref] 
        
        self.posText = [self.REF1.posText,self.REF2.posText,self.REF3.posText,self.REF4.posText,self.REF5.posText,self.REF6.posText]
        self.POS = [self.REF1.Pos,self.REF2.Pos,self.REF3.Pos,self.REF4.Pos,self.REF5.Pos,self.REF6.Pos]
        self.Take = [self.REF1.take,self.REF2.take,self.REF3.take,self.REF4.take,self.REF5.take,self.REF6.take]
        self.jogStep.setFocus()
        self.refShow()
        
    def actionButton(self):
        '''
           buttons action setup 
        '''
        self.unitBouton.currentIndexChanged.connect(self.unit) #  unit change
        self.absMvtButton.clicked.connect(self.MOVE)
        self.plus.clicked.connect(self.pMove) # jog + foc
        self.plus.setAutoRepeat(True)
        self.moins.clicked.connect(self.mMove)# jog - foc
        self.moins.setAutoRepeat(True) 
        self.scan.clicked.connect(lambda:self.open_widget(self.scanWidget) )    
        self.zeroButton.clicked.connect(self.Zero) # reset display to 0
        #self.refZeroButton.clicked.connect(self.RefMark) # todo
        self.stopButton.clicked.connect(self.StopMot) #  stop motors 
        self.showRef.clicked.connect(self.refShow) # show references widgets
        self.shootCibleButton.clicked.connect(self.ShootAct)
        iii = 0
        for saveNameButton in self.posText: # reference name
            saveNameButton.textChanged.connect(self.savName)
            saveNameButton.setText(self.refName[iii]) # print  ref name
            iii+=1   

        for posButton in self.POS: # button GO
            posButton.clicked.connect(self.ref)    # go to reference value
        eee = 0  
        for absButton in self.absRef: 
            nbRef = str(eee)
            absButton.setValue(float(self.refValueStep[eee]*self.unitChange) )# save reference value
            absButton.editingFinished.connect(self.savRef) # sauv value
            eee+=1
       
        for takeButton in self.Take:
            takeButton.clicked.connect(self.take) # take the value 
        
        self.updateButton.clicked.connect(self.update)

    def open_widget(self,fene):
        
        """ open new widget 
        """
        if fene.isWinOpen is False:
            #New widget"
            fene.show()
            fene.isWinOpen=True
            fene.startTrigThread()
        else:
            #fene.activateWindow()
            fene.raise_()
            fene.showNormal()
        
    def refShow(self):
        
        if self.refShowId is True:
            #self.resize(368, 345)
            self.widget6REF.show()
            self.refShowId = False
            self.showRef.setText('Hide Ref')
            self.setFixedSize(430,800) 
        else:
            #print(self.geometry()
            self.widget6REF.hide()
            self.refShowId = True
            self.showRef.setText('Show Ref')
            self.setFixedSize(430,380)
    
    def MOVE(self):
        '''
        absolue mouvment
        '''
        a = float(self.MoveStep.value())
        a = float(a/self.unitChange) # changement d unite
        if a<self.buteNeg[0] :
            print( "STOP : Butée Négative")
            self.butNegButt.setChecked(True)
            self.MOT[0].stopMotor()
        elif a>self.butePos[0] :
            print( "STOP : Butée Positive")
            self.butPosButt.setChecked(True)
            self.MOT[0].stopMotor()
        else :
            self.MOT[0].move(a)
            self.butNegButt.setChecked(False)
            self.butPosButt.setChecked(False)
    
    def pMove(self):
        '''
        action jog + foc 
        '''
        a = float(self.jogStep.value())
        a = float(a/self.unitChange)
        b = self.MOT[0].position()
        if b+a>self.butePos[0] :
            print( "STOP :  Positive switch")
            self.MOT[0].stopMotor()
            self.butPosButt.setChecked(True)
        else :
            self.MOT[0].rmove(a)
            self.butNegButt.setChecked(False)
            self.butPosButt.setChecked(False)
            
    def mMove(self): 
        '''
        action jog - foc
        '''
        a = float(self.jogStep.value())
        a = float(a/self.unitChange)
        b = self.MOT[0].position()
        if b-a<self.buteNeg[0] :
            print( "STOP : negative switch")
            self.MOT[0].stopMotor()
            self.butNegButt.setChecked(True)
        else :
            self.MOT[0].rmove(-a)
            self.butNegButt.setChecked(False)
            self.butPosButt.setChecked(False)
  
    def Zero(self): #  zero 
        self.MOT[0].setzero()

    def RefMark(self): # 
        """
            todo ....
        """
        #self.motorType.refMark(self.motor)
   
    def unit(self):
        '''
        unit change mot foc
        '''
        self.indexUnit = self.unitBouton.currentIndex()
        valueJog = self.jogStep.value()/self.unitChange 
        moveVal = self.MoveStep.value()/self.unitChange
        
        if self.indexUnit == 0: #  step
            self.unitChange = 1
            self.unitName = 'step'
            
        if self.indexUnit == 1: # micron
            self.unitChange = float((self.stepmotor[0])) 
            self.unitName = 'um'

        if self.indexUnit == 2: #  mm 
            self.unitChange = float((self.stepmotor[0])/1000)
            self.unitName = 'mm'
        if self.indexUnit == 3: #  ps  double passage : 1 microns=6fs
            self.unitChange = float(1*self.stepmotor[0]*0.0066666666) 
            self.unitName = 'ps'
        if self.indexUnit == 4: #  en degres
            self.unitChange = 1 *self.stepmotor[0]
            self.unitName = '°'    
            
        if self.unitChange == 0:
            self.unitChange = 1 #avoid /0 
            
        self.jogStep.setSuffix(" %s" % self.unitName)
        self.jogStep.setValue(valueJog*self.unitChange)
        self.MoveStep.setValue(moveVal*self.unitChange)
        self.MoveStep.setSuffix(" %s" % self.unitName)

        eee = 0
        for absButton in self.absRef: # change the value of reference 
            nbRef = eee
            
            absButton.setValue(float(self.refValueStep[eee]*self.unitChange))
            absButton.setSuffix(" %s" % self.unitName)
            eee+=1
        
    def StopMot(self):
        '''
        stop all motors
        '''
        self.REF1.show()
        for zzi in range(0,1):
            self.MOT[zzi].stopMotor()

    def Position(self,Posi):
        ''' 
        Position  display read from the second thread
        '''
        Pos = Posi[0]
        self.etat = str(Posi[1])
        a = float(Pos)
        b = a # value in step
        a = a * self.unitChange # value with unit changed
        if self.etat == 'FDC-':
            self.enPosition.setText(self.etat)
            self.enPosition.setStyleSheet('font: bold 15pt;color:red')
        elif self.etat == 'FDC+':
            self.enPosition.setText('FDC +')
            self.enPosition.setStyleSheet('font: bold 15pt;color:red')
        elif self.etat == 'Poweroff' :
            self.enPosition.setText('Power Off')
            self.enPosition.setStyleSheet('font: bold 15pt;color:red')
        elif self.etat == 'mvt' :
            self.enPosition.setText('Mvt...')
            self.enPosition.setStyleSheet('font: bold 15pt;color:white')
        elif self.etat == 'notconnected':
            self.enPosition.setText('python server Not connected')
            self.enPosition.setStyleSheet('font: bold 8pt;color:red')
        elif self.etat == 'errorConnect':
            self.enPosition.setText('equip Not connected')
            self.enPosition.setStyleSheet('font: bold 8pt;color:red')
    
        self.position.setText(str(round(a,2))) 
        self.position.setStyleSheet('font: bold 15pt;color:white')
        
        positionConnue = 0 # 
        precis = 5 # to show position name
        if (self.etat == 'ok' or self.etat == '?'):
            for nbRefInt in range(1,7):
                if positionConnue == 0 :
                    
                    if float(self.refValueStep[nbRefInt-1]) - precis < b < float(self.refValueStep[nbRefInt-1]) + precis: #self.MOT[0].getRefValue
                        self.enPosition.setText(str(self.refName[nbRefInt-1]))
                        positionConnue = 1   
        if positionConnue == 0 and (self.etat == 'ok' or self.etat == '?'):
            self.enPosition.setText(' ' ) 
        
    def Etat(self,etat):
        # return  motor state  
        self.etat = etat
    
    def take (self) : 
        ''' 
        take and save the reference
        '''
        sender = QtCore.QObject.sender(self) # take the name of  the button 
        
        nbRef = str(sender.objectName()[0])
        
        reply = QMessageBox.question(None,'Save Position ?',"Do you want to save this position ?",QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
               tpos = float(self.MOT[0].position())
               self.refValueStep[int(nbRef)-1] = tpos 
               self.absRef[int(nbRef)-1].setValue(tpos*self.unitChange)
               print ("Position saved",tpos)
               
    def ref(self):  
        '''
        Move the motor to the reference value in step : GO button
        '''
        sender = QtCore.QObject.sender(self)
        reply = QMessageBox.question(None,'Go to this Position ?',"Do you want to GO to this position ?",QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No,QMessageBox.StandardButton.No)
        if reply == QMessageBox.StandardButton.Yes:
            nbRef=str(sender.objectName()[0])
            for i in range (0,1):
                vref = int(self.refValueStep[int(nbRef)-1]) # 
                if vref < self.buteNeg[i] :
                    print( "STOP : negative switch")
                    self.butNegButt.setChecked(True)
                    self.MOT[i].stopMotor()
                elif vref > self.butePos[i] :
                    print( "STOP : positive switch")
                    self.butPosButt.setChecked(True)
                    self.MOT[i].stopMotor()
                else :
                    self.MOT[i].move(vref)
                    self.butNegButt.setChecked(False)
                    self.butPosButt.setChecked(False) 

    def savName(self) :
        '''
        Save reference name
        '''
        sender = QtCore.QObject.sender(self)
        nbRef = sender.objectName()[0] #PosTExt1
        vname = self.posText[int(nbRef)-1].text()
        for i in range (0,1):
            self.refName[int(nbRef)-1] = str(vname)

    def savRef (self) :
        '''
        save reference  value
        '''
        sender = QtCore.QObject.sender(self)
        nbRef = sender.objectName()[0] # nom du button ABSref1
        
        vref = int(self.absRef[int(nbRef)-1].value())
        self.refValueStep[int(nbRef)-1] = vref  # on sauvegarde en step 

    def ShootAct(self):
        try: 
            self.tir.TirAct()  
        except: pass
    
    def closeEvent(self, event):
        """ 
        When closing the window
        """
        self.fini()
        time.sleep(0.01)
        event.accept()
        
    def fini(self): 
        '''
        at the end we close all the thread 
        '''
        self.thread.stopThread()
        self.isWinOpen = False
        self.updateDB()

        if self.scanWidget.isWinOpen is True:
            self.scanWidget.close()
            print('close moto widget')
        time.sleep(0.1)


    def eventFilter(self, obj, event):
        if event.type() == event.FocusIn:
            widget_type = obj.__class__.__name__
            print('focus')   
        elif event.type() == event.FocusOut:
            widget_type = obj.__class__.__name__
            print('focus out ')
        return super().eventFilter(obj,event)
    
    def setup_event(self):
        print('')
#        for widget in self.findChild(QPushButton):
            #print('tt')
            #widget.installEventFilter(self)

    # def focusInEvent(self, event):   
    #     print('focus event')
    #     # self.parent.threadLat.ThreadINIT()
    #     # self.parent.threadVert.ThreadINIT()
        
    #     # self.parent.threadLat.start()
    #     time.sleep(0.05)
        
    #     self.parent.threadVert.start()
    #     super().focusInEvent(event)
    #     event.accept()
        
    # def focusOutEvent(self, event):   
    #     print('focus out event')
    #     # self.parent.threadLat.stopThread()
    #     # self.parent.threadVert.stopThread()
    #     super().focusOutEvent(event)
    #     event.accept()      

        
class REF1M(QWidget):
    
    def __init__(self,num=0, parent=None):
        super(REF1M, self).__init__()
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.wid = QWidget()
        self.id = num
        self.vboxPos = QVBoxLayout()
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(p.parent) + sepa + 'icons' +sepa
        self.posText = QLineEdit('ref')
        self.posText.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
        self.posText.setStyleSheet("font: bold 15pt")
        self.posText.setObjectName('%s'%self.id)
#        self.posText.setMaximumWidth(80)
        self.vboxPos.addWidget(self.posText)
        self.iconTake=self.icon+"disquette.png"
        self.iconTake=pathlib.Path(self.iconTake)
        self.iconTake=pathlib.PurePosixPath(self.iconTake)
        self.take=QToolButton()
        self.take.setObjectName('%s'%self.id)
        self.take.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconTake,self.iconTake))
        self.take.setMaximumWidth(30)
        self.take.setMinimumWidth(30)
        self.take.setMinimumHeight(30)
        self.take.setMaximumHeight(30)
        self.takeLayout=QHBoxLayout()
        self.takeLayout.addWidget(self.take)

        self.iconGo = self.icon+"go.png"
        self.iconGo = pathlib.Path(self.iconGo)
        self.iconGo = pathlib.PurePosixPath(self.iconGo)
        self.Pos = QToolButton()
        self.Pos.setStyleSheet("QToolButton:!pressed{border-image: url(%s);background-color: transparent ;border-color: gray;}""QToolButton:pressed{image: url(%s);background-color: gray ;border-color: gray}"%(self.iconGo,self.iconGo))
        self.Pos.setMinimumHeight(30)
        self.Pos.setMaximumHeight(30)
        self.Pos.setMinimumWidth(30)
        self.Pos.setMaximumWidth(30)
        self.PosLayout = QHBoxLayout()
        self.PosLayout.addWidget(self.Pos)
        self.Pos.setObjectName('%s'%self.id)
        #○self.Pos.setStyleSheet("background-color: rgb(85, 170, 255)")
        Labelref = QLabel('Pos :')
        Labelref.setMaximumWidth(30)
        Labelref.setStyleSheet("font: 9pt" )
        self.ABSref=QDoubleSpinBox()
        self.ABSref.setMaximum(500000000)
        self.ABSref.setMinimum(-500000000)
        self.ABSref.setValue(123456)
        self.ABSref.setMaximumWidth(80)
        self.ABSref.setObjectName('%s'%self.id)
        self.ABSref.setStyleSheet("font: 9pt" )
        
        grid_layoutPos = QGridLayout()
        grid_layoutPos.setVerticalSpacing(5)
        grid_layoutPos.setHorizontalSpacing(10)
        grid_layoutPos.setAlignment(QtCore.Qt.AlignmentFlag.AlignHCenter | QtCore.Qt.AlignmentFlag.AlignVCenter)
        grid_layoutPos.addLayout(self.takeLayout,0,0)
        grid_layoutPos.addLayout(self.PosLayout,0,1)
        grid_layoutPos.addWidget(Labelref,1,0)
        grid_layoutPos.addWidget(self.ABSref,1,1)
        
        self.vboxPos.addLayout(grid_layoutPos)
        self.wid.setStyleSheet("background-color: rgb(60, 77, 87);border-radius:10px")
        self.wid.setLayout(self.vboxPos)
        
        mainVert = QVBoxLayout()
        mainVert.addWidget(self.wid)
        mainVert.setContentsMargins(0,0,0,0)
        self.setLayout(mainVert)


class PositionThread(QtCore.QThread):
    '''
    Second thread  to display the position
    '''
    import time 
    POS = QtCore.pyqtSignal(object) # signal of the second thread to main thread  to display motors position
    ETAT = QtCore.pyqtSignal(str)

    def __init__(self,parent=None,mot='',):
        super(PositionThread,self).__init__(parent)
        self.MOT = mot
        self.parent = parent
        self.stop = False

    def run(self):
        while True:
            if self.stop is True:
                break
            else:
                
                Posi = (self.MOT.position())
                time.sleep(0.05)
                etat = self.MOT.etatMotor()
                try :
                    # print(etat)
                    #time.sleep(0.1)
                    self.POS.emit([Posi,etat])
                    
                except:
                    print('error emit')
                  
    def ThreadINIT(self):
        self.stop = False   
                        
    def stopThread(self):
        self.stop = True
        time.sleep(0.1)
        #self.terminate()
        

if __name__ == '__main__':
    appli = QApplication(sys.argv)
    mot1 = ONEMOTORGUI(IpAdress="10.0.2.30", NoMotor = 14, showRef=False, unit=1,jogValue=100)
    mot1.show()
    mot1.startThread2()
    appli.exec_()
