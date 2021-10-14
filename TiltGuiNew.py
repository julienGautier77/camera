# -*- coding: utf-8 -*-


"""
Interface Graphique pour le pilotage de deux moteurs tilt
Controleurs possible : A2V RSAI NewFocus SmartAct ,newport, Polulu
Thread secondaire pour afficher les positions
import files : moteurRSAI.py smartactmot.py moteurNewFocus.py  moteurA2V.py newportMotors.py servo.py
memorisation de 5 positions
python 3.X PyQt5 
System 32 bit (at least python MSC v.1900 32 bit (Intel)) 
@author: Gautier julien loa
Created on Tue Jan 4 10:42:10 2018
Modified on Tue july 17  10:49:32 2018
"""



from PyQt5 import QtCore
from PyQt5.QtWidgets import QApplication
from PyQt5.QtWidgets import QWidget
from PyQt5.QtGui import QIcon
from PyQt5.QtWidgets import QVBoxLayout,QHBoxLayout,QPushButton,QGridLayout,QDoubleSpinBox
from PyQt5.QtWidgets import QComboBox,QLabel
import qdarkstyle
import pathlib
import time
import sys,os
PY = sys.version_info[0]
if PY<3:
    print('wrong version of python : Python 3.X must be used')

import __init__

__version__=__init__.__version__




class TILTMOTORGUI(QWidget) :
    """
    User interface Motor class : 
    MOTOGUI(str(mot1), str(motorTypeName),str(mot2), str(motorTypeName), nomWin,nomTilt,unit )
    mot0= lat  'name of the motor ' (child group of the ini file)
    mot1 =vert
    motorTypeName= Controler name  : 'RSAI' or 'A2V' or 'NewFocus' or 'SmartAct' or 'Newport' , Servo,Arduino
    nonWin= windows name
    nonTilt =windows tilt name
    unit=0 step 1 micron 2 mm 3 ps 

    fichier de config des moteurs : 'configMoteurRSAI.ini' 'configMoteurA2V.ini' 'configMoteurNewFocus.ini' 'configMoteurSmartAct.ini'
    """
  
    def __init__(self, motLat='',motorTypeName0='', motVert='',motorTypeName1='',nomWin='',nomTilt='',unit=1,jogValue=1,background='gray',parent=None):
        
        super(TILTMOTORGUI, self).__init__()
        p = pathlib.Path(__file__)
        sepa=os.sep
        self.icon=str(p.parent) + sepa + 'icons' +sepa
        self.motor=[str(motLat),str(motVert)]
        self.motorTypeName=[motorTypeName0,motorTypeName1]
        
        self.motorType=[0,0]
        self.MOT=[0,0]
        self.configMotName=[0,0]
        self.conf=[0,0]
        self.configPath="./fichiersConfig/"
        self.isWinOpen=False
        self.setStyleSheet(qdarkstyle.load_stylesheet_pyqt5())
        self.indexUnit=unit
        self.jogValue=jogValue
        self.nomTilt=nomTilt
        
        self.setStyleSheet("background-color:"+background)
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.version=__version__
        
        
        for zi in range (0,2): #• creation list configuration et type de moteurs
            if self.motorTypeName[zi]=='RSAI':
                self.configMotName[zi]=self.configPath+'configMoteurRSAI.ini'
                import moteurRSAI as RSAI
                self.motorType[zi]=RSAI
                self.MOT[zi]=self.motorType[zi].MOTORRSAI(self.motor[zi])
                
            elif self.motorTypeName[zi]=='SmartAct':
                 
                 self.configMotName[zi]=self.configPath+'configMoteurSmartAct.ini'
                 import smartactmot as SmartAct
                 self.motorType[zi]=SmartAct
                 self.MOT[zi]=self.motorType[zi].MOTORSMART(self.motor[zi])
                 
            elif self.motorTypeName[zi]=='A2V':
                 self.configMotName[zi]=self.configPath+'configMoteurA2V.ini'
                 import moteurA2V  as A2V
                 self.motorType[zi]=A2V
                 self.MOT[zi]=self.motorType[zi].MOTORA2V(self.motor[zi])
                 
            elif self.motorTypeName[zi]=='NewFocus':
                 self.configMotName[zi]=self.configPath+'configMoteurNewFocus.ini'
                 import moteurNewFocus as NewFoc
                 self.motorType[zi]=NewFoc
                 self.MOT[zi]=self.motorType[zi].MOTORNEWFOCUS(self.motor[zi])
                 
                 
            elif self.motorTypeName[zi]=='newport':
                 self.configMotName[zi]=self.configPath+'confNewport.ini'
                 import newportMotors as Newport
                 self.motorType[zi]=Newport
                 self.MOT[zi]=self.motorType[zi].MOTORNEWPORT(self.motor[zi])
                 
            elif self.motorTypeName[zi]=='Servo':
                 self.configMotName[zi]=self.configPath+'configMoteurServo.ini'
                 import servo as servo
                 self.motorType[zi]=servo
                 self.MOT[zi]=self.motorType[zi].MOTORSERVO(self.motor[zi])
            else:
                print('Error config motor Type name')
                self.configMotName[zi]=self.configPath+'configMoteurTest.ini'
                import moteurtest as test
                self.motorType[zi]=test
                self.MOT[zi]=self.motorType[zi].MOTORTEST(self.motor[zi])
                
            self.conf[zi]=QtCore.QSettings(self.configMotName[zi], QtCore.QSettings.IniFormat) # fichier config motor fichier .ini
        
        
        self.stepmotor=[0,0]
        self.butePos=[0,0]
        self.buteNeg=[0,0]
        self.name=[0,0,0]
        
        for zzi in range(0,2):
            self.stepmotor[zzi]=float(self.conf[zzi].value(self.motor[zzi]+"/stepmotor")) #list of stepmotor values for unit conversion
            self.butePos[zzi]=float(self.conf[zzi].value(self.motor[zzi]+"/buteePos")) # list 
            self.buteNeg[zzi]=float(self.conf[zzi].value(self.motor[zzi]+"/buteeneg"))
            self.name[zzi]=str(self.conf[zzi].value(self.motor[zzi]+"/Name"))
        
        self.unitChangeLat=self.indexUnit
        self.unitChangeVert=self.indexUnit
        self.setWindowTitle(nomWin+' : '+'                     V.'+str(self.version))
        self.threadLat=PositionThread(mot=self.MOT[0],motorType=self.motorType[0]) # thread pour afficher position Lat
        self.threadLat.POS.connect(self.PositionLat)
        time.sleep(0.1)
        
        self.threadVert=PositionThread(mot=self.MOT[1],motorType=self.motorType[1]) # thread pour afficher position Vert
        self.threadVert.POS.connect(self.PositionVert)
        
        
        self.setup()
        
        if self.indexUnit==0: #  step
            self.unitChangeLat=1
            self.unitName='step'
            
        if self.indexUnit==1: # micron
            self.unitChangeLat=float((1*self.stepmotor[0])) 
            self.unitName='um'
        if self.indexUnit==2: #  mm 
            self.unitChangeLat=float((1000*self.stepmotor[0]))
            self.unitName='mm'
        if self.indexUnit==3: #  ps  double passage : 1 microns=6fs
            self.unitChangeLat=float(1*self.stepmotor[0]/0.0066666666) 
            self.unitName='ps'
        if self.indexUnit==4: #  en degres
            self.unitChangeLat=1 *self.stepmotor[0]
            self.unitName='°'
        self.unitTrans()
        
        
    def setup(self):
        
        vbox1=QVBoxLayout() 
        
        hbox1=QHBoxLayout()
        hboxTitre=QHBoxLayout()
        self.nomTilt=QLabel(self.nomTilt)
        self.nomTilt.setStyleSheet("font: bold 20pt;color:yellow")
        hboxTitre.addWidget(self.nomTilt)
        
        self.unitTransBouton=QComboBox()
        self.unitTransBouton.setMaximumWidth(100)
        self.unitTransBouton.setMinimumWidth(100)
        self.unitTransBouton.setStyleSheet("font: bold 12pt")
        self.unitTransBouton.addItem('Step')
        self.unitTransBouton.addItem('um')
        self.unitTransBouton.addItem('mm')
        self.unitTransBouton.addItem('ps')
        self.unitTransBouton.setCurrentIndex(self.indexUnit)
        
        
        hboxTitre.addWidget(self.unitTransBouton)
        hboxTitre.addStretch(1)
        
        vbox1.addLayout(hboxTitre)
        
        
        grid_layout = QGridLayout()
        grid_layout.setVerticalSpacing(0)
        grid_layout.setHorizontalSpacing(10)
        self.haut=QPushButton()
        self.haut.setStyleSheet("QPushButton:!pressed{border-image: url(./Iconeslolita/flechehaut.png) ;background-color: transparent;border-color: green;}""QPushButton:pressed{image: url(./IconesLolita/flechehaut.png) ;background-color: transparent;border-color: blue}")
        
        self.haut.setMaximumHeight(70)
        self.haut.setMinimumWidth(70)
        self.haut.setMaximumWidth(70)
        self.haut.setMinimumHeight(70)
        
        self.bas=QPushButton()
        self.bas.setStyleSheet("QPushButton:!pressed{border-image: url(./Iconeslolita/flechebas.png) ;background-color: transparent;border-color: green;}""QPushButton:pressed{image: url(./IconesLolita/flechebas.png) ;background-color: transparent;border-color: blue}")
        self.bas.setMaximumHeight(70)
        self.bas.setMinimumWidth(70)
        self.bas.setMaximumWidth(70)
        self.bas.setMinimumHeight(70)
        
        self.droite=QPushButton()
        self.droite.setStyleSheet("QPushButton:!pressed{border-image: url(./Iconeslolita/flechedroite.png);background-color: transparent;border-color: green;}""QPushButton:pressed{image: url(./IconesLolita/flechedroite.png) ;background-color: transparent;border-color: blue}")
        self.droite.setMaximumHeight(70)
        self.droite.setMinimumWidth(70)
        self.droite.setMaximumWidth(70)
        self.droite.setMinimumHeight(70)
        
        self.gauche=QPushButton()
        self.gauche.setStyleSheet("QPushButton:!pressed{border-image: url(./Iconeslolita/flechegauche.png);background-color: transparent;border-color: green;}""QPushButton:pressed{image: url(./IconesLolita/flechegauche.png) ;background-color: transparent;border-color: blue}")
        
        self.gauche.setMaximumHeight(70)
        self.gauche.setMinimumWidth(70)
        self.gauche.setMaximumWidth(70)
        self.gauche.setMinimumHeight(70)
        
        
        
        self.jogStep=QDoubleSpinBox()
        self.jogStep.setMaximum(1000)
        self.jogStep.setStyleSheet("font: bold 12pt")
        self.jogStep.setValue(self.jogValue)
        self.jogStep.setMaximumWidth(120)
        
        
        center=QHBoxLayout()
        center.addWidget(self.jogStep)
        self.hautLayout=QHBoxLayout()
        self.hautLayout.addWidget(self.haut)
        self.basLayout=QHBoxLayout()
        self.basLayout.addWidget(self.bas)
        grid_layout.setAlignment(QtCore.Qt.AlignHCenter | QtCore.Qt.AlignVCenter)
        grid_layout.addLayout(self.hautLayout, 0, 1)
        grid_layout.addLayout(self.basLayout,2,1)
        grid_layout.addWidget(self.gauche, 1, 0)
        grid_layout.addWidget(self.droite, 1, 2)
        grid_layout.addLayout(center,1,1)
        
        hbox1.addLayout(grid_layout)
        
        vbox1.addLayout(hbox1)
        
        posLAT=QLabel('Lateral:')
        posLAT.setMaximumHeight(20)
        posVERT=QLabel('Vertical :')
        posVERT.setMaximumHeight(20)
        hbox2=QHBoxLayout()
        hbox2.addWidget(posLAT)
        hbox2.addWidget(posVERT)
        vbox1.addLayout(hbox2)
        
        self.position_Lat=QLabel('pos')
        self.position_Lat.setMaximumHeight(20)
        self.position_Vert=QLabel('pos')
        self.position_Vert.setMaximumHeight(20)
        hbox3=QHBoxLayout()
        hbox3.addWidget(self.position_Lat)
        
        hbox3.addWidget(self.position_Vert)
        vbox1.addLayout(hbox3)
        
        hbox4=QHBoxLayout()
        self.zeroButtonLat=QPushButton('Zero Lat')
        self.zeroButtonVert=QPushButton('Zero Vert')
        
        hbox4.addWidget(self.zeroButtonLat)
        hbox4.addWidget(self.zeroButtonVert)
        vbox1.addLayout(hbox4)
        
        self.stopButton=QPushButton('STOP')
        self.stopButton.setStyleSheet("background-color: red")
        hbox5=QHBoxLayout()
        hbox5.addWidget(self.stopButton)
        vbox1.addLayout(hbox5)
        self.setLayout(vbox1)       
        
        self.actionButton()
        
    
    def startThread2(self):
        self.threadLat.ThreadINIT()
        self.threadLat.start()
        time.sleep(0.5)
        self.threadVert.ThreadINIT()
        self.threadVert.start()
        
      
    def actionButton(self):
        '''
           Definition des boutons 
        '''
        self.unitTransBouton.currentIndexChanged.connect(self.unitTrans) # Trans unit change
        
        self.haut.clicked.connect(self.hMove) # jog haut
        self.haut.setAutoRepeat(False)
        self.bas.clicked.connect(self.bMove) # jog bas
        self.bas.setAutoRepeat(False)
        self.gauche.clicked.connect(self.gMove)
        self.gauche.setAutoRepeat(False)
        self.droite.clicked.connect(self.dMove)
        self.droite.setAutoRepeat(False)
                
        self.zeroButtonLat.clicked.connect(self.ZeroLat)# remet a zero l'affichage
        self.zeroButtonVert.clicked.connect(self.ZeroVert)
        
        #self.refZeroButton.clicked.connect(self.RefMark) # va en butée et fait un zero

        self.stopButton.clicked.connect(self.StopMot)# arret moteur
    
    def closeEvent(self, event):
        """ 
        When closing the window
        """
        self.fini()
        time.sleep(0.1)
        event.accept()
            

    def gMove(self):
        '''
        action bouton left
        '''
        a=float(self.jogStep.value())
        a=float(a*self.unitChangeLat)
        b=self.MOT[0].position()
        if b-a<self.buteNeg[0] :
            print( "STOP : Butée Positive")
            self.MOT[0].stopMotor()
        elif b-a>self.butePos[0] :
            print( "STOP : Butée Négative")
            self.MOT[0].stopMotor()
        else :
            self.MOT[0].rmove(-a)
            
    def dMove(self):
        '''
        action bouton left
        '''
        a=float(self.jogStep.value())
        a=float(a*self.unitChangeLat)
        b=self.MOT[0].position()
        if b-a<self.buteNeg[0] :
            print( "STOP : Butée Positive")
            self.MOT[0].stopMotor()
        elif b-a>self.butePos[0] :
            print( "STOP : Butée Négative")
            self.MOT[0].stopMotor()
        else :
            self.MOT[0].rmove(a)
        
    def hMove(self): 
        '''
        action bouton up
        '''
        a=float(self.jogStep.value())
        a=float(a*self.unitChangeVert)
        b=self.MOT[1].position()
        if b-a<self.buteNeg[1] :
            print( "STOP : Butée Positive")
            self.MOT[1].stopMotor()
        elif b-a>self.butePos[1] :
            print( "STOP : Butée Négative")
            self.MOT[1].stopMotor()
        else :
            self.MOT[1].rmove(a)   
        
        
    def bMove(self):
        '''
        action bouton up
        '''
        a=float(self.jogStep.value())
        a=float(a*self.unitChangeVert)
        b=self.MOT[1].position()
        if b-a<self.buteNeg[1] :
            print( "STOP : Butée Positive")
            self.MOT[1].stopMotor()
        elif b-a>self.butePos[1] :
            print( "STOP : Butée Négative")
            self.MOT[1].stopMotor()
        else :
            self.MOT[1].rmove(-a)           
        
    def ZeroLat(self): # remet le compteur a zero 
        self.MOT[0].setzero()
    def ZeroVert(self): # remet le compteur a zero 
        self.MOT[1].setzero()
 

    def RefMark(self): # Va en buttée et fait un zero
        """
            a faire ....
        """
        #self.motorType.refMark(self.motor)
   
    def unitTrans(self):
        '''
         unit change mot foc
        '''
        self.indexUnit=self.unitTransBouton.currentIndex()
        valueJog=self.jogStep.value()*self.unitChangeLat
        if self.indexUnit==0: # step
            self.unitChangeLat=1
            self.unitChangeVert=1
            self.unitNameTrans='step'
        if self.indexUnit==1: # micron
            self.unitChangeLat=float((1*self.stepmotor[0]))  
            self.unitChangeVert=float((1*self.stepmotor[1]))  
            self.unitNameTrans='um'
        if self.indexUnit==2: 
            self.unitChangeLat=float((1000*self.stepmotor[0]))
            self.unitChangeVert=float((1000*self.stepmotor[1]))
            self.unitNameTrans='mm'
        if self.indexUnit==3: #  ps  en compte le double passage : 1 microns=6fs
            self.unitChangeLat=float(1*self.stepmotor[0]/0.0066666666)  
            self.unitChangeVert=float(1*self.stepmotor[1]/0.0066666666)  
            self.unitNameTrans='ps'
        if self.unitChangeLat==0:
            self.unitChangeLat=1 # if / par 0
        if self.unitChangeVert==0:
            self.unitChangeVert=1 #if / 0
        
       
        self.jogStep.setSuffix(" %s" % self.unitNameTrans)
        self.jogStep.setValue(valueJog/self.unitChangeLat)
        
    def StopMot(self):
        '''
        stop les moteurs
        '''
        for zzi in range(0,2):
            self.MOT[zzi].stopMotor();

    def PositionLat(self,Posi):
        ''' 
        affichage de la position a l aide du second thread
        '''
        a=float(Posi)
       
        a=a/self.unitChangeLat # valeur tenant compte du changement d'unite
        self.position_Lat.setText(str(round(a,2))) 
       
    def PositionVert(self,Posi): 
        ''' 
        affichage de la position a l aide du second thread
        '''
        a=float(Posi)
    
        a=a/self.unitChangeVert # valeur tenant compte du changement d'unite
        self.position_Vert.setText(str(round(a,2))) 
      
    def fini(self): 
        '''
        a la fermeture de la fenetre on arrete le thread secondaire
        '''
        self.threadLat.stopThread()
        self.threadVert.stopThread()
        self.isWinOpen=False
        time.sleep(0.1)    






class PositionThread(QtCore.QThread):
    '''
    thread secondaire pour afficher la position
    '''
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
                time.sleep(0.3)
                try :
                    
                    self.POS.emit(Posi)
                    time.sleep(0.2)
                except:
                    print('error emit')
                  
                
    def ThreadINIT(self):
        self.stop=False         
                    
    def stopThread(self):
        self.stop=True
        time.sleep(0.1)
        self.terminate()
        
    

if __name__ =='__main__':
    motor0='PinholeLat'
    motor1='PinholeVert'
    appli=QApplication(sys.argv)
    mot5=TILTMOTORGUI( motLat=motor0,motorTypeName0='SmartAct' , motVert=motor1,motorTypeName1='SmartAct',nomWin='Tilts Pinhole')
    mot5.show()
    mot5.startThread2()
    appli.exec_()
    

