# -*- coding: utf-8 -*-
"""
Created on Wed Apr  1 12:16:58 2020

@author: LOA
"""

from PyQt5.QtWidgets import QApplication,QVBoxLayout,QHBoxLayout,QWidget,QPushButton
from PyQt5.QtWidgets import QComboBox,QSlider,QLabel,QSpinBox,QGridLayout,QToolButton
from pyqtgraph.Qt import QtCore
from PyQt5.QtCore import Qt,QSize
from PyQt5.QtGui import QIcon,QSizePolicy
import sys,time
import numpy as np
import pathlib,os
import qdarkstyle


class testWidget(QWidget):
    def __init__(self):
        super(testWidget, self).__init__()
        self.setup()
        
    def setup(self):
        sizeBox=QSize(10, 50)
        self.vbox1=QVBoxLayout() 
        hbox1=QHBoxLayout()
        self.runButton=QToolButton(self)
        self.runButton.setMaximumWidth(20)
        self.runButton.setMinimumWidth(20)
        print(self.runButton.minimumWidth())
        self.snapButton=QPushButton()
        self.stopButton=QPushButton(self)
        hbox1.addWidget(self.runButton)
        hbox1.addWidget(self.snapButton)
        hbox1.addWidget(self.stopButton)
        self.vbox1.addLayout(hbox1)
        self.setLayout(self.vbox1)
        
if __name__ == "__main__":       
    
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
   
    e = testWidget()  
    e.show()
    appli.exec_()       