#! /usr/bin/python3
# -*- coding: utf-8 -*-

"""
Created on Tue Mar 22 11:24:01 2022

Create a message with the list of camera connected (Basler allied vision imaging source, pixelink)
Add in the config file the parameter for the cam choosed
Generate a .py to run the new camera and a shortcut on the desktop
@author: gautier
"""

from PyQt6.QtWidgets import QApplication,QWidget,QMessageBox
from PyQt6.QtWidgets import QInputDialog
from PyQt6 import QtCore
from PyQt6.QtGui import QIcon
import sys
import pathlib
import os
import subprocess
import time
import qdarkstyle


class NEWCAM(QWidget):
    
    def __init__(self):
        
        super(NEWCAM, self).__init__()
        p = pathlib.Path(__file__)
        sepa = os.sep
        self.icon = str(p.parent) + sepa+'icons'+sepa
        self.setWindowIcon(QIcon(self.icon+'LOA.png'))
        self.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))

        try :
            import alliedCam
            self.itemsGuppy = alliedCam.camAvailable()
            # print(self.itemsGuppy)
            self.lenGuppy = len(self.itemsGuppy)
            
        except:
            #print('No allied vision camera connected')
            self.itemsGuppy = []
            self.lenGuppy = 0
            pass
        try :
            import baslerCam
            self.itemsBasler = baslerCam.camAvailable()
            self.lenBasler = len(self.itemsBasler)
            
        except:
            #print('No Basler camera connected')
            self.itemsBasler = []
            self.lenBasler = 0
            pass 
        
        try :
            import ImgSourceCamCallBack
            self.itemsImgSource = ImgSourceCamCallBack.camAvailable()
            self.lenImgSource = len(self.itemsImgSource)
            
        except:
            #print('No ImagingSource camera connected')
            self.itemsImgSource = []
            self.lenImgSource = 0
            pass 
        
        try :
            import pixelinkCam
            self.itemsPixelink = pixelinkCam.PIXELINK.camAvailable()
            self.lenImgPixelink = len(self.itemsPixelink)
            
        except:
            #print('No pixelink camera connected')
            self.itemsPixelink = []
            self.lenPixelink = 0
            pass 
        
        items = self.itemsGuppy+list(self.itemsBasler)+self.itemsImgSource+self.itemsPixelink
        
        item, ok = QInputDialog.getItem(self, "Select a camera","List of avaible camera", items, 0, False,flags=QtCore.Qt.WindowType.WindowStaysOnTopHint)
        
        if ok and item:
            
            indexItem = items.index(item)
        
            if indexItem < self.lenGuppy :
                indexItem = indexItem
                self.cameraType = "allied"
                self.camID = alliedCam.getCamID(indexItem)
                self.isConnected = True
            elif indexItem >= self.lenGuppy  and indexItem<self.lenBasler+self.lenGuppy:
                indexItem = indexItem-self.lenGuppy
                self.cameraType = "basler"
                self.camID = baslerCam.getCamID(indexItem)
                self.isConnected = True
                
            elif indexItem >= self.lenBasler + self.lenGuppy  and indexItem < self.lenBasler + self.lenGuppy + self.lenImgSource:
                indexItem = indexItem - self.lenGuppy - self.lenBasler
                self.cameraType = "imgSource"
                self.camID = ImgSourceCamCallBack.getCamID(indexItem)
                self.camID = self.camID.decode()
                self.isConnected = True
                
            elif indexItem >= self.lenBasler+self.lenGuppy + self.lenImgSource and indexItem < self.lenBasler + self.lenGuppy + self.lenImgSource + self.lenPixelink:
                indexItem = indexItem - self.lenGuppy - self.lenBasler  -self.lenImgSource
                self.cameraType = "pixelink"
                self.camID = pixelinkCam.getCamID(indexItem)
                self.isConnected = True

            else:
                self.isConnected = False
                print('No camera choosen')
                self.ccdName = "no camera"
                self.nbcam = 'camDefault'
                messError = QMessageBox()
                messError.setWindowIcon(QIcon(self.icon+'LOA.png'))
                messError.setIcon(QMessageBox.Icon.Critical)
                messError.setText(' No camera connected or choosed')
                messError.setWindowTitle(" Warning ")
                messError.exec()
        else :
            self.isConnected = False
            print('No camera choose')
            self.ccdName = "no camera"
            self.cameraType = ""
            self.camID = ""
            self.nbcam = 'camDefault'
            messError = QMessageBox()
            messError.setWindowIcon(QIcon(self.icon+'LOA.png'))
            messError.setIcon(QMessageBox.Icon.Critical)
            messError.setText(' No camera connected or choosed')
            messError.setWindowTitle(" Warning ")
            messError.exec()
            
        if self.isConnected is True :
            item, ok = QInputDialog.getText(self, "Choose a camera name","Name ?: ",flags=QtCore.Qt.WindowType.WindowStaysOnTopHint)
            p = pathlib.Path(__file__)
            self.nbcam = item
            self.confpath = str(p.parent / 'confCamera.ini') # ini file with global path
            self.conf = QtCore.QSettings(self.confpath, QtCore.QSettings.Format.IniFormat) # ini file 
        
            # create a new camera in the config file 

            self.conf.setValue(self.nbcam+"/LineTrigger","InputLines")
            self.conf.setValue(self.nbcam+"/bgPath","C:/Users/loa/Dropbox (LOA)/Programmes Python/acquisitionPrinceton/data")
            self.conf.setValue(self.nbcam+"/bloqKeyboard","true")
            self.conf.setValue(self.nbcam+"/camId",self.camID)
            self.conf.setValue(self.nbcam+"/camType",self.cameraType)
            self.conf.setValue(self.nbcam+"/gain",float(0))
            self.conf.setValue(self.nbcam+"/lastFichier"," ")
            self.conf.setValue(self.nbcam+"/loqKeyboard","false")

            self.conf.setValue(self.nbcam+"/nameBg","bg")
            
            self.conf.setValue(self.nbcam+"/nameCDD",self.nbcam)
            
            self.conf.setValue(self.nbcam+"/nameFile","Tir")
            self.conf.setValue(self.nbcam+"/pathAutoSave"," ")
                               
            self.conf.setValue(self.nbcam+"/pathBg","")

            self.conf.setValue(self.nbcam+"/rotation",0)
            self.conf.setValue(self.nbcam+"/rx",50)
            self.conf.setValue(self.nbcam+"/ry",50)
            self.conf.setValue(self.nbcam+"/shutter",10)
            self.conf.setValue(self.nbcam+"/stepX",1)
            self.conf.setValue(self.nbcam+"/stepY",1)
            self.conf.setValue(self.nbcam+"/tirNumber",1)
            self.conf.setValue(self.nbcam+"/xc",1)
            self.conf.setValue(self.nbcam+"/yc",2)
            
            self.conf.setValue(self.nbcam+"/r1x",10)
            self.conf.setValue(self.nbcam+"/r1y",11)
            self.conf.setValue(self.nbcam+"/r2x",20)
            self.conf.setValue(self.nbcam+"/r2y",20)
            
            self.conf.setValue(self.nbcam+"/xec",10)
            self.conf.setValue(self.nbcam+"/yec",10)
            self.conf.sync()      
        
            # create a .py file named namecamera.py to run the camera 
            path = pathlib.Path(__file__)
            path = str(path.parent)
            fichierName = path + '/' + self.nbcam + '.py'
            print(fichierName)
            #strCam="     e = CAMERA(cam='" +self.nbcam + "')"
            strCam = "     e = CAMERA(cam='" +self.nbcam + "',scan=False,motRSAI = False)"
            top = '#! /usr/bin/python3' #   '#! '+ str(pathlib.Path(__file__).parent.parent.parent.parent)+ '/miniforge3/bin/python3.10'

            lines = [top,'from PyQt6.QtWidgets import QApplication','from camera import CAMERA','import sys','import qdarkstyle','']
            lines2 = ['if __name__ == "__main__":','     appli = QApplication(sys.argv) ',"     appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))",""]
            lines3 = [strCam,"     e.show()","     appli.exec_()"]
            
            with open(fichierName, "w") as fichier:
                print('ii')
                fichier.write('\n'.join(lines))
                fichier.write('\n'.join(lines2))
                fichier.write('\n'.join(lines3))
                fichier.write('\n')
                fichier.close()

            messError = QMessageBox(self)
            messError.setWindowIcon(QIcon(self.icon+'LOA.png'))
            messError.setWindowTitle("Python file created ")
            messError.setText("The python file to run the camera has been created:   click right on desktop file to autoriser execution")#+str(p.parent)+"/"+fichierName+"   double click on it to run ")
            messError.exec()

            # creation de raccourcci

            if sys.platform == 'linux': 
                print('linux sytem')

                # creation racourci linux
                fichierRacourci =  path + '/' + self.nbcam + '.desktop'
                print('fichierRacourci ',fichierRacourci )
                with open(fichierRacourci, "w") as fichierR:
                    l = ['[Desktop Entry]']
                    fichierR.write('\n'.join(l))
                    fichierR.write('\n')
                    ll = ['Version=1.0']
                    fichierR.write('\n'.join(ll))
                    fichierR.write('\n')
                    l2 = ['Type=Application']
                    fichierR.write('\n'.join(l2))
                    fichierR.write('\n')
                    l6 = ['Terminal=false']
                    fichierR.write('\n'.join(l6))
                    fichierR.write('\n')
                    path = pathlib.Path(__file__)
                    path = str(path.parent)
                    l3 = ['Exec='+fichierName]
                    fichierR.write('\n'.join(l3))
                    fichierR.write('\n')
                    l4 = ['Name='+ self.nbcam]
                    fichierR.write('\n'.join(l4))
                    fichierR.write('\n')
                    lll = ['StartupNotify=true']
                    fichierR.write('\n'.join(lll))
                    fichierR.write('\n')
                    l5 = ['Icon='+path+'/icons/camera.png']
                    fichierR.write('\n'.join(l5))
                    fichierR.write('\n')
                    
                    fichierR.close()
                    
                    cmd = 'chmod +x %s'% fichierName # autorisation fichier.py
                    subprocess.run(cmd,shell=True, executable="/bin/bash")
                    print(cmd)
                    bureauPath = str(pathlib.Path(__file__).parent.parent.parent.parent)+'/'+'Bureau'
                    cmd = 'cp %s '%fichierRacourci +str(bureauPath)
                    subprocess.run(cmd,shell=True, executable="/bin/bash")
                    print(cmd)
                    cmd = 'chmod +x %s'%fichierRacourci
                    subprocess.run(cmd,shell=True, executable="/bin/bash")
                    print(cmd)
            else : 
                print('system' , sys.platform)
                import win32com.client  # pip install pywin32
                target_path = str(p.parent) + "/" + fichierName
                icon_path = str(p.parent)+"/" + 'icons' + "/" + 'camera.ico'
                desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
                shortcutName = self.nbcam + ".lnk"
                shorcutPath = os.path.join(desktop,shortcutName )
                shell = win32com.client.Dispatch("WScript.Shell")
                shortcut = shell.CreateShortCut(shorcutPath)
                shortcut.Targetpath = target_path
                shortcut.WorkingDirectory = os.path.dirname(target_path)
                shortcut.IconLocation = icon_path
                shortcut.save() 

        # else :
        #     messError = QMessageBox()
        #     messError.setWindowIcon(QIcon(self.icon+'LOA.png'))
        #     messError.setIcon(QMessageBox.Icon.Critical)
        #     messError.setText(' No camera connected')
        #     messError.setWindowTitle(" Warning ")
        #     messError.exec()
        
if __name__ == "__main__":       
    appli = QApplication(sys.argv) 
    appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
    e = NEWCAM()
    # e.show()
    # appli.exec_()       