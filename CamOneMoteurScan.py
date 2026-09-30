# -*- coding: utf-8 -*-
"""
Created on 2023/01/19 
amera acquisition with one motor selected 

@author: juliengautier
version : 2023.01
"""

from PyQt6.QtWidgets import QApplication,QWidget,QVBoxLayout,QHBoxLayout,QGridLayout,QDockWidget
from PyQt6.QtWidgets import QGroupBox,QPushButton
from PyQt6.QtCore import Qt
from camera import CAMERA
import sys
import qdarkstyle 
from PyQt6 import QtCore
from PyQt6.QtGui import QIcon
from oneMotorSimple import ONEMOTOR
from scanMotorCamera import SCAN
from calibrationMotor import CALIBRATION
from phaseRetrieval import PHASE
import os
import pathlib

class CAMERAONEMOTOR(QWidget):
    """
    Widget combining a camera acquisition window with a single motor
    control dock (ONEMOTOR) and a motor scan window (SCAN).
    """

    signalAcqDoneONEMOTOR=QtCore.pyqtSignal(object)

    def __init__(self,cam=None,confFile='confCamera.ini',IpAdress=None, NoMotor=None,parent=None,**kwds):
        """
        Parameters
        cam:name of the camera 
        configFile= ini file of the camera
        mot0= name of the motor to control
        motorType : type of motor ('RSAI')
        """
        super(CAMERAONEMOTOR, self).__init__(parent)
        self.parent = parent
        self.kwds = kwds
        self.CAM = CAMERA(cam=cam,configFile=confFile,separate=True,motRSAI=True,**self.kwds)
         
        self.MOTWidget = ONEMOTOR(IpAdress, NoMotor,nomWin='motorSimple',unit=1,jogValue=100)
        self.MOTWidget.startThread2()
        sepa = os.sep
        p = pathlib.Path(__file__)
        self.icon = str(p.parent) + sepa+'icons'+sepa
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.scanWidget = SCAN(MOT=self.MOTWidget.MOT,parent=self)
        self.calibWidget = CALIBRATION(CAM=self.CAM,IpAdress=IpAdress,NoMotor=NoMotor,parent=self)
        self.phaseWidget = PHASE(CAM=self.CAM,IpAdress=IpAdress,NoMotor=NoMotor,parent=self)
        self.setup()
        self.actButton()


    def setup(self):
        '''
        One panel at the right of visu with the camera, the motor and the
        tools. The widgets of CAMERA and ONEMOTOR are reused (their own docks
        and layouts are not displayed)
        '''
        vbox = QVBoxLayout()
        CAM = self.CAM
        MOT = self.MOTWidget
        for dock in (CAM.dockControl, CAM.dockTrig, CAM.dockShutter, CAM.dockGain):
            CAM.visualisation.removeDockWidget(dock)

        panel = QWidget()
        panel.setFixedWidth(250)
        vPanel = QVBoxLayout(panel)
        vPanel.setContentsMargins(6, 6, 6, 6)
        vPanel.setSpacing(10)

        # camera
        groupCam = QGroupBox('Camera')
        gridCam = QGridLayout(groupCam)
        gridCam.setVerticalSpacing(8)
        hAcq = QHBoxLayout()
        for but in (CAM.runButton, CAM.snapButton, CAM.stopButton):
            but.setFixedSize(40, 40)
            hAcq.addWidget(but)
        gridCam.addLayout(hAcq, 0, 0, 1, 3)
        CAM.labelTrigger.setText('Trigger')
        CAM.labelTrigger.setMaximumWidth(16777215)
        CAM.labelTrigger.setStyleSheet('')
        CAM.trigg.setMaximumWidth(16777215)
        CAM.trigg.setStyleSheet('')
        gridCam.addWidget(CAM.labelTrigger, 1, 0)
        gridCam.addWidget(CAM.trigg, 1, 1, 1, 2)
        CAM.labelExp.setText('Exposure')
        CAM.labelGain.setText('Gain')
        row = 2
        for lab, box, slider, unit in ((CAM.labelExp, CAM.shutterBox, CAM.hSliderShutter, ' ms'),
                                       (CAM.labelGain, CAM.gainBox, CAM.hSliderGain, '')):
            lab.setStyleSheet('')
            lab.setMaximumWidth(16777215)
            lab.setAlignment(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignVCenter)
            box.setStyleSheet('')
            box.setMaximumWidth(16777215)
            box.setSuffix(unit)
            slider.setMaximumWidth(16777215)
            gridCam.addWidget(lab, row, 0)
            gridCam.addWidget(box, row, 1, 1, 2)
            gridCam.addWidget(slider, row + 1, 0, 1, 3)
            row += 2
        vPanel.addWidget(groupCam)

        # motor
        groupMot = QGroupBox('Motor : ' + MOT.name)
        vMot = QVBoxLayout(groupMot)
        vMot.setSpacing(8)
        MOT.position.setAlignment(Qt.AlignmentFlag.AlignCenter)
        MOT.position.setMinimumHeight(40)
        MOT.position.setMaximumHeight(40)
        vMot.addWidget(MOT.position)
        hUnit = QHBoxLayout()
        MOT.unitButton.setMaximumWidth(16777215)
        MOT.unitButton.setStyleSheet('')
        MOT.zeroButton.setText('Zero')
        MOT.zeroButton.setStyleSheet('')
        MOT.zeroButton.setMaximumWidth(16777215)
        MOT.zeroButton.setMinimumHeight(26)
        hUnit.addWidget(MOT.unitButton, 2)
        hUnit.addWidget(MOT.zeroButton, 1)
        vMot.addLayout(hUnit)
        hJog = QHBoxLayout()
        for but in (MOT.moins, MOT.plus):
            but.setFixedSize(40, 32)
            but.setStyleSheet('font: bold 14pt')
        MOT.jogStep.setMaximumWidth(16777215)
        MOT.jogStep.setMinimumHeight(32)
        MOT.jogStep.setMaximumHeight(32)
        MOT.jogStep.setAlignment(Qt.AlignmentFlag.AlignCenter)
        hJog.addWidget(MOT.moins)
        hJog.addWidget(MOT.jogStep, 1)
        hJog.addWidget(MOT.plus)
        vMot.addLayout(hJog)
        MOT.stopButton.setMaximumWidth(16777215)
        MOT.stopButton.setMinimumHeight(32)
        MOT.stopButton.setStyleSheet('background-color: #d32f2f; color: white; font: bold 11pt; border-radius: 4px')
        vMot.addWidget(MOT.stopButton)
        vPanel.addWidget(groupMot)

        # tools
        groupTools = QGroupBox('Tools')
        gridTools = QGridLayout(groupTools)
        self.buttonScan = QPushButton('Scan')
        self.buttonCalib = QPushButton('Calibration')
        self.buttonPhase = QPushButton('Phase')
        self.buttonPhase.setToolTip('phase retrieval from a focus scan + Zernike')
        for i, but in enumerate((self.buttonScan, self.buttonCalib, self.buttonPhase)):
            but.setMinimumHeight(30)
            gridTools.addWidget(but, i // 2, i % 2)
        vPanel.addWidget(groupTools)
        vPanel.addStretch(1)

        self.dockMotor = QDockWidget(self)
        self.dockMotor.setTitleBarWidget(QWidget())
        self.dockMotor.setWidget(panel)
        CAM.visualisation.addDockWidget(Qt.DockWidgetArea.RightDockWidgetArea, self.dockMotor)
        vbox.addWidget(self.CAM)
        self.setLayout(vbox)

    def actButton(self):
        self.buttonScan.clicked.connect(lambda:self.open_widget(self.scanWidget) )
        self.scanWidget.acqMain.connect(self.acquireScan)
        self.buttonCalib.clicked.connect(lambda:self.open_widget(self.calibWidget) )
        self.calibWidget.acqMain.connect(self.acquireScan)
        self.buttonPhase.clicked.connect(lambda:self.open_widget(self.phaseWidget) )
        self.phaseWidget.acqMain.connect(self.acquireScan)
        #self.CAM.signalAcqDone.connect(self.CamOneAcqDone)

    # def CamOneAcqDone(self):
    #     self.signalAcqDoneONEMOTOR.emit(True)

    def acquireScan(self):
        self.CAM.acquireOneImage()


    def open_widget(self,fene):
        
        """ open new widget 
        """
        
        if fene.isWinOpen is False:
            #New widget"
            fene.show()
            fene.isWinOpen = True
    
        else:
            #fene.activateWindow()
            fene.raise_()
            fene.showNormal()

    def closeEvent(self,event):
        ''' closing window event (cross button)
        '''
        self.MOTWidget.fini()
        # self.MOTWidget.Mot.stopConnexion()
        if self.scanWidget.isWinOpen is True:
            self.scanWidget.close()
        if self.calibWidget.isWinOpen is True:
            self.calibWidget.close()
        if self.phaseWidget.isWinOpen is True:
            self.phaseWidget.close()


if __name__ == "__main__":
     appli = QApplication(sys.argv) 
     appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
     e = CAMERAONEMOTOR(cam='focP1',IpAdress="10.0.1.31", NoMotor=10)
     e.show()
     appli.exec_()