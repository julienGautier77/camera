# -*- coding: utf-8
""" Control des moteurs NewFocus
protocole TC/IP
python 3.X and PyQt5
@author: Gautier julien loa
Created on Wed Feb 28 11:59:41 2018
"""
#%% import
import socket
import time
from PyQt5.QtCore import QSettings
from PyQt5 import QtCore
mutexA=QtCore.QMutex()
#%% initialisation and connexion
IP='10.0.2.60' # controleur 0
IP1='10.0.2.61' # controleur 1
Port=23
Port1=23
bufferSize=1024
s0=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s1=socket.socket(socket.AF_INET, socket.SOCK_STREAM)

# try :
#     s0.connect((IP,Port))
# except:
#     print('connexion newFocus error IP',IP)

time.sleep(0.1)
try :
    s1.connect((IP1,Port1))
except:
    print('connexion newFocus error IP',IP1)
       
time.sleep(0.1)
# try :
#     s0.send(('*IDN?'+'\n').encode())
#     nameFocus=s0.recv(bufferSize)
#     nameFocus=s0.recv(bufferSize)
# #    print(nameFocus.decode())
# except:
#     print('connexion newFocus0 error: swtich off/on the controller')
try :
    s1.send(('*IDN?'+'\n').encode())
    nameFocus1=s1.recv(bufferSize)
    nameFocus1=s1.recv(bufferSize)
#    print(nameFocus.decode())
except:
    print('connexion newFocus1 error : swtich off/on the controller')
#try:    
#    s0.send(('IPADDR?'+'\r' +'\n').encode())
#    IP_Focus=s0.recv(bufferSize)
#    print (nameFocus.decode(), "connected @ :",IP_Focus.decode())
#except:
#    print('connexion newFocus0 error')
#try:    
#    s1.send(('IPADDR?'+'\r' +'\n').encode())
#    IP_Focus=s1.recv(bufferSize)
#    print (nameFocus1.decode(), "connected @ :",IP_Focus.decode())
#except:
#    print('connexion newFocus0 error')   
    
    
def stopConnexion0():
    print('stop new Focus')
    s0.close()
def stopConnexion1():
    print('stop new Focus')
    s1.close()
confNewFocus=QSettings('fichiersConfig/configMoteurNewFocus.ini',QSettings.IniFormat)

#%%  class motorNewfocus

class MOTORNEWFOCUS():
    
    def __init__(self, mot1='',parent=None):
        #super(MOTORNEWFOCUS, self).__init__()
        self.moteurname=mot1
        self.numMoteur=str(confNewFocus.value(self.moteurname+'/numMoteur'))
        
        self.numControleur=int(confNewFocus.value(self.moteurname+'/numControleur'))
        
        if self.numControleur==0:
            self.s=s0
        if self.numControleur==1:
            
            self.s=s1  
            
    def position (self):
        """
        position (motor) : donne la position de motor
        """
        mutexA.lock()
        self.s.send((self.numMoteur+'TP?'+'\n').encode())
        pos=self.s.recv(bufferSize)
        #pos1=pos.decode('utf-8')#.upper()
        mutexA.unlock()
        return int(pos)

    def stopMotor(self): # stop le moteur motor
        """stopMotor(motor): stop le moteur motor
        """
        mutexA.lock()
        self.s.send((self.numMoteur+'ST'+'\n').encode())
        mutexA.unlock()
        print ("stop", self.moteurname )
        print (self.moteurname, "stopped @", self.position())

    def move(self,pos,vitesse=10000): 
        """
        move(motor,pos): mouvement absolu du moteur (motor) a la position pos 
        """
        # print (self.moteurname,"position before ",self.position(),"(step)")
        mutexA.lock()
        self.s.send((self.numMoteur+'PA'+str(pos) +'\n').encode())
        mutexA.unlock()
        # print (self.moteurname, "absolu move  to",pos,"(step)")

    def rmove(self,posrelatif,vitesse=10000):
        """
        rmove(motor,posrelatife): : mouvement relatif du moteur (motor) a la position posrelatif 
        """
        posActuel=self.position()
        # print (time.strftime("%A %d %B %Y %H:%M:%S"))
        # print (self.moteurname,"position before ",posActuel,"(step)")
        mutexA.lock()
        self.s.send((self.numMoteur+'PR'+str(int(posrelatif)) +'\n').encode())
        # print (self.moteurname , "relative move of",posrelatif,"(step)")
        mutexA.unlock()
    def setzero(self):
        """
        setzero(motor):Set Zero
        """
        
        self.s.send((self.numMoteur+'DH'+'\n').encode())
        print (time.strftime("%A %d %B %Y %H:%M:%S"))
        print (self.moteurname,"set to zero")

    def setvelocity(self,v=2000):
        """
        setvelocity(motor,velocity): Set Velocity en step/s
        """
        
        
        if v>2001:
            print ("speed Too Hight !!!")
        else:
            v1=int(v)
            self.s.send((self.numMoteur+'VA'+str(v)+'\n')).encode()
            print ("velocity of",self.moteurname,"set to",str(v))
        return v1

#%%
if __name__ == "__main__":
    print("test")
    #startConnexion()
