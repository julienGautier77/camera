#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat 18 10 2024

@author: juliengautier
"""

from PyQt6 import QtCore
from PyQt6.QtWidgets import QWidget
from PyQt6.QtWidgets import QApplication, QVBoxLayout, QHBoxLayout
from PyQt6.QtWidgets import QPushButton, QDoubleSpinBox, QToolButton
from PyQt6.QtWidgets import QComboBox, QLabel
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QIcon
import sys
import time
import os
import qdarkstyle
import pathlib
import moteurRSAISERVER


class ONEMOTOR(QWidget):

    def __init__(self, IpAdress, NoMotor, nomWin='', unit=2,jogValue=1):

        super(ONEMOTOR, self).__init__()
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(p.parent) + sepa + 'icons' + sepa
        self.IpAdress = IpAdress
        self.NoMotor = NoMotor
        self.nomWin = nomWin
        self.isWinOpen = False
        self.indexUnit = unit
        self.configPath = "./fichiersConfig/"
        self.isWinOpen = False
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt6())
        self.jogValue = jogValue
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.MOT = moteurRSAISERVER.MOTORRSAI(self.IpAdress, self.NoMotor)
        self.name = str(self.MOT.getName())
        self.setWindowTitle(self.nomWin + str(self.MOT.getEquipementName()) + ' ('+ str(self.IpAdress)+ ')  '+ ' [M'+ str(self.NoMotor) + ']  ' + self.name[0] )
        self.stepmotor = float(1/(self.MOT.getStepValue()))
        self.butePos = float(self.MOT.getButLogPlusValue())
        self.buteNeg = float(self.MOT.getButLogMoinsValue())

        self.thread2 = PositionThread(mot=self.MOT, parent =self) # thread pour afficher position
        self.thread2.POS.connect(self.Position)

        self.setup()
        # initialisation of the jog value
        if self.indexUnit == 0:  # step
            self.unitChange = 1
            self.unitName = 'step'

        if self.indexUnit == 1:  # micron
            self.unitChange = float((1*self.stepmotor))
            self.unitName = 'um'
        if self.indexUnit == 2:  #  mm
            self.unitChange = float((1000*self.stepmotor))
            self.unitName = 'mm'
        if self.indexUnit == 3:  # ps  double passage : 1 microns=6fs
            self.unitChange = float(1*self.stepmotor/0.0066666666)
            self.unitName = 'ps'
        if self.indexUnit == 4:  # en degres
            self.unitChange = 1 * float(self.stepmotor)
            self.unitName = '°'
        self.actionButton()
        self.unit()

    def startThread2(self):
        self.thread2.ThreadINIT()
        self.thread2.start()

    def setup(self):
        vbox1 = QVBoxLayout()
        hbox1 = QHBoxLayout()
        # pos=QLabel('Pos:')
        # pos.setMaximumHeight(20)
        nameBox = QLabel(self)
        nameBox.setText(self.name)
        nameBox.setAlignment(Qt.AlignmentFlag.AlignCenter)
        nameBox.setStyleSheet('font: bold 15px;color: purple')
        self.position = QLabel('1234567')
        self.position.setMaximumHeight(50)
        self.position.setStyleSheet("font: bold 10pt")
        self.unitButton = QComboBox()
        self.unitButton.addItem('Step')
        self.unitButton.addItem('um')
        self.unitButton.addItem('mm')
        self.unitButton.addItem('ps')
        self.unitButton.setMinimumWidth(80)
        self.unitButton.setMaximumWidth(80)
        self.unitButton.setStyleSheet("font: bold 8pt")
        self.unitButton.setCurrentIndex(self.indexUnit)
        size = 20
        self.zeroButton = QToolButton()
        self.zeroButton.setText('zero')
        self.zeroButton.setStyleSheet("font: bold 6pt")
        self.zeroButton.setMaximumWidth(2*size)
        self.zeroButton.setStyleSheet('background-color: gray;border-color: gray')
        vbox1.addWidget(nameBox)
        hbox1.addWidget(self.position)
        hbox1.addWidget(self.unitButton)
        hbox1.addWidget(self.zeroButton)
        vbox1.addLayout(hbox1)
        
        hbox2 = QHBoxLayout()

        self.moins = QToolButton()
        self.moins.setText('-')
        self.moins.setMinimumWidth(size)
        self.moins.setMaximumWidth(size)
        self.moins.setMinimumHeight(size)
        self.moins.setMaximumHeight(size)
        self.moins.setStyleSheet('background-color: gray;border-color: gray')
        hbox2.addWidget(self.moins)

        self.jogStep = QDoubleSpinBox()
        self.jogStep.setMaximum(10000)
        self.jogStep.setMinimumWidth(size*4)
        self.jogStep.setMaximumWidth(size*4)
        self.jogStep.setMinimumHeight(size)
        self.jogStep.setMaximumHeight(size)
        self.jogStep.setValue(self.jogValue)
        hbox2.addWidget(self.jogStep)
        self.plus = QToolButton()
        self.plus.setText('+')
        self.plus.setMinimumWidth(size)
        self.plus.setMinimumHeight(size)
        self.plus.setStyleSheet('background-color: gray;border-color: gray')
        hbox2.addWidget(self.plus)
        vbox1.addLayout(hbox2)
        hbox3 = QHBoxLayout()
        self.stopButton = QPushButton('STOP')
        self.stopButton.setMaximumWidth(size*4)
        self.stopButton.setStyleSheet("background-color: red")
        hbox3.addWidget(self.stopButton)
        vbox1.addLayout(hbox3)
        self.hbox3 = hbox3
        self.vbox1 = vbox1

        self.setLayout(self.vbox1)

    def actionButton(self):
        self.plus.clicked.connect(self.pMove)  # jog +
        self.plus.setAutoRepeat(True)
        self.moins.clicked.connect(self.mMove)  # jog -
        self.moins.setAutoRepeat(True)
        self.zeroButton.clicked.connect(self.Zero)
        self.stopButton.clicked.connect(self.StopMot)
        self.unitButton.currentIndexChanged.connect(self.unit)

    def StopMot(self):
        '''
        stop all motors
        '''
        self.MOT.stopMotor()

    def pMove(self):  # action jog +
        print('jog+')
        a = float(self.jogStep.value())
        a = float(a*self.unitChange)
        b = self.MOT.position()
        if b+a < self.buteNeg:
            print("STOP : Butée Positive")
            self.MOT.stopMotor()
        elif b+a > self.butePos:
            print("STOP : Butée Négative")
            self.MOT.stopMotor()
        else:
            self.MOT.rmove(a)

    def mMove(self):  # action jog -
        a = float(self.jogStep.value())
        a = float(a*self.unitChange)
        b = self.MOT.position()
        if b-a < self.buteNeg:
            print("STOP : Butée Positive")
            self.MOT.stopMotor()
        elif b-a > self.butePos:
            print("STOP : Butée Négative")
            self.MOT.stopMotor()
        else:
            self.MOT.rmove(-a)

    def Zero(self):  # remet le compteur a zero
        self.MOT.setzero()

    def unit(self):
        '''
        unit change mot foc
        '''
        self.indexUnit = self.unitButton.currentIndex()
        valueJog = self.jogStep.value()*self.unitChange
        if self.indexUnit == 0:  # step
            self.unitChange = 1
            self.unitName = 'step'

        if self.indexUnit == 1:  # micron
            self.unitChange = float((1*self.stepmotor))
            self.unitName = 'um'
        if self.indexUnit == 2:  # mm 
            self.unitChange = float((1000*self.stepmotor))
            self.unitName = 'mm'
        if self.indexUnit == 3:  # ps  double passage : 1 microns=6fs
            self.unitChange = float(1*self.stepmotor/0.0066666666)
            self.unitName = 'ps'
        if self.indexUnit == 4:  # en degres
            self.unitChange = 1 * self.stepmotor
            self.unitName = '°'
        if self.unitChange == 0:
            self.unitChange = 1  # avoid 0
            
        self.jogStep.setSuffix(" %s" % self.unitName)
        self.jogStep.setValue(valueJog/self.unitChange)

    def Position(self, Posi):
        '''
        Position  display read from the second thread
        '''
        Pos = Posi[0]
        self.etat = str(Posi[1])
        a = float(Pos)
        a = a/self.unitChange  # value with unit changed
        if self.etat == 'FDC-':
            self.position.setText(self.etat)
            self.position.setStyleSheet('font: bold 15pt;color:red')
        elif self.etat == 'FDC+':
            self.position.setText('FDC +')
            self.position.setStyleSheet('font: bold 15pt;color:red')
        elif self.etat == 'Poweroff':
            self.position.setText('Power Off')
            self.position.setStyleSheet('font: bold 15pt;color:red')
        elif self.etat == 'mvt':
            self.position.setText('Mvt...')
            self.position.setStyleSheet('font: bold 15pt;color:white')
        elif self.etat == 'notconnected':
            self.position.setText('python server Not connected')
            self.position.setStyleSheet('font: bold 8pt;color:red')
        elif self.etat == 'errorConnect':
            self.position.setText('equip Not connected')
            self.position.setStyleSheet('font: bold 8pt;color:red')
        else:
            self.position.setText(str(round(a, 2))) 
            self.position.setStyleSheet('font: bold 15pt;color:white')

    def closeEvent(self, event):
        """
        When closing the window
        """
        self.fini()
        time.sleep(0.1)
        event.accept()

    def fini(self):  # a la fermeture de la fenetre on arrete le thread secondaire
        self.thread2.stopThread()
        self.isWinOpen = False
        time.sleep(0.1)


class PositionThread(QtCore.QThread):
    '''
    Second thread  to display the position
    '''
    POS = QtCore.pyqtSignal(object)  # signal of the second thread to main thread  to display motors position
    ETAT = QtCore.pyqtSignal(str)

    def __init__(self, parent=None, mot=''):
        super(PositionThread, self).__init__(parent)
        self.MOT = mot
        self.parent = parent
        self.stop = False

    def run(self):
        while True:
            if self.stop is True:
                break
            else:
                
                Posi = (self.MOT.position())
                time.sleep(0.1)
                
                try:
                    etat = self.MOT.etatMotor()
                    # print(etat)
                    time.sleep(0.1)
                    self.POS.emit([Posi, etat])
                    time.sleep(0.1)
                except:
                    print('error emit')
                  
    def ThreadINIT(self):
        self.stop = False
                        
    def stopThread(self):
        self.stop = True
        time.sleep(0.1)


if __name__ == '__main__':
    appli = QApplication(sys.argv)
    mot5 = ONEMOTOR(IpAdress="10.0.6.31", NoMotor=3, unit=1, jogValue=100)
    mot5.show()
    mot5.startThread2()
    appli.exec_()
