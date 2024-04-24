#!/usr/bin/env python3
# -*- coding: utf-8 -*-
from PyQt6 import QtCore
from PyQt6.QtWidgets import QApplication
from PyQt6.QtWidgets import QWidget
from PyQt6.QtWidgets import QVBoxLayout,QHBoxLayout
from PyQt6.QtWidgets import QComboBox,QLabel
from PyQt6.QtGui import QIcon
import qdarkstyle
import sys
import moteurRSAIFDB 
from oneMotorGuiFBCamera import ONEMOTORGUI
import time
import numpy as np

class MAINMOTOR(QWidget):
    """  widget 
    list of ip adress and list of motors
    """
    def __init__(self, parent=None):
        super(MAINMOTOR, self).__init__()
        self.isWinOpen = False
        self.parent = parent
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
        self.setWindowIcon(QIcon('./icons/LOA.png'))
        self.setWindowTitle('Main Motors')
        self.listRack = moteurRSAIFDB.rEquipmentList()
        self.IPadress = self.listRack[0]
        self.rackName = []
        self.motorCreatedId = []
        self.motorCreated = []

        for IP in self.listRack:
            self.rackName.append(moteurRSAIFDB.nameEquipment(IP))
        
        rack =dict(zip(self.rackName,self.listRack)) # dictionnaire key name of the rack values IPadress
        self.listMotor = moteurRSAIFDB.listMotorName(self.IPadress) # liste des nom des moteur i+1= numero de l'axe
        self.SETUP()
        #self.actionButton()
        
    def SETUP(self):

        self.vbox = QVBoxLayout()
        hboxRack = QHBoxLayout()
        LabelRack = QLabel('RACK NAME')
        hboxRack.addWidget(LabelRack)
        self.rackChoise = QComboBox()
        hboxRack.addWidget(self.rackChoise)
        i=0
        
        for rack in self.listRack: #
            self.rackChoise.addItem( str(moteurRSAIFDB.nameEquipment(rack))+ '  (' + rack +')')
            i+=1
                
        LabelMotor = QLabel('Motor NAME')
        hboxRack.addWidget(LabelMotor)
        self.motorChoise=QComboBox()
        hboxRack.addWidget(self.motorChoise)
        self.motorChoise.addItem('Choose a motor')
        self.motorChoise.addItems(self.listMotor)
        self.vbox.addLayout(hboxRack)
        self.setLayout(self.vbox)
        
    def actionButton(self):
        self.motorChoise.currentIndexChanged.connect(self.createMotor)
        self.rackChoise.currentIndexChanged.connect(self.ChangeIPRack)
    
    def createMotor(self):
        #  print('create Motor')
        if self.motorChoise.currentIndex() != 0 :
            self.numMotor = self.motorChoise.currentIndex() # car indice 0 = 'choose o motor'
            self.IPadress = self.listRack [self.rackChoise.currentIndex()]
            motorID = str(self.IPadress)+'M'+str(self.numMotor)
            if motorID in self.motorCreatedId: 
                #  print('moteur already created')
                index=self.motorCreatedId.index(motorID)
                self.open_widget(self.motorCreated[index])
            else :
                self.motorWidget = ONEMOTORGUI(self.IPadress,self.numMotor,parent=self)
                time.sleep(0.1)
                self.open_widget(self.motorWidget)
                self.motorCreatedId.append(motorID)
                self.motorCreated.append(self.motorWidget)
        
    def ChangeIPRack(self):
        self.motorChoise.clear()
        self.IPadress = str( self.listRack[self.rackChoise.currentIndex()])
        #print('ip',self.IPadress)
        self.listMotor = moteurRSAIFDB.listMotorName(self.IPadress)
        self.rackName = moteurRSAIFDB.nameEquipment(self.IPadress)
        self.motorChoise.addItem('Choose a motor')
        self.motorChoise.addItems(self.listMotor)
        #print('chage Ip')

    def open_widget(self,fene):
        
        """ open new widget 
        """
        if fene.isWinOpen is False:
            #New widget"
            fene.show()
            fene.startThread2()
            fene.isWinOpen = True
        else:
            #fene.activateWindow()
            fene.raise_()
            fene.showNormal()

    def closeEvent(self, event):
        """ 
        When closing the window
        """
        self.fini()
        time.sleep(0.1)
        event.accept()
        
    def fini(self): 
        '''
        at the end we close all the thread 
        '''
        self.isWinOpen = False
        for mot in self.motorCreated:
            mot.close()
        time.sleep(0.1)    
        moteurRSAIFDB.closeConnection()

if __name__=='__main__':
    appli=QApplication(sys.argv)
    s = MAINMOTOR()
    s.show()
    appli.exec_()