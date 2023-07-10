import ctypes
import time
import logging
from PyQt6.QtCore import QSettings

dll_file = 'DLL64/MCSControl'
SMART = ctypes.cdll.LoadLibrary(dll_file)
confSmart = QSettings('./fichiersConfig/configMoteurSmartAct.ini', QSettings.Format.IniFormat) # motor configuration  files

def openCom(ipAdress):
    options = 'sync'.encode('ascii') # synchronus mode 
    controller_index = ctypes.c_ulong()
    status = SMART.SA_OpenSystem(ctypes.byref(controller_index),
            ipAdress.encode('ascii'),options)
    if status != 0:
            raise Exception('SmarAct communication to ', ipAdress,' failed')
    else :
          mode=0# " SA_HCM_DISABLED"
          result=SMART.SA_SetHCMEnabled(controller_index,mode)
          
          return (controller_index.value)
    
def stopConnexion():
     print('stop smaract')


#### Def IP adress or usb usb:id:3118167233
# or usb:ix:<n> where the number <n> selects the nth device in the list of all currently attached MCS with a USB interface. 
# The drawback of identifying an MCS with this method is, that the number and the order of connected MCS 
# can change between sessions

Controller_index=[]
ipAdress0="network:192.168.1.200:5000"
ipList=[ipAdress0]
for ipAdress in ipList :
    controller_index0=openCom(ipAdress)
    Controller_index.append(controller_index0)
    print('controller index', Controller_index, 'connected to',ipAdress)


def stopConnexion():
     i=0
     for index in Controller_index:
        result=SMART.SA_SetHCMEnabled(index,1)
        status = SMART.SA_CloseSystem(ctypes.c_ulong(index))
        if status==0:
            print('stop smarAct',ipList[i],'index controler',index)
            
        i+=1

class MOTORSMART():
    def __init__(self, mot1='',parent=None):
        self.moteurname=mot1
        
        self.numControleur=int(confSmart.value(self.moteurname+'/numControleur'))
        self.numMoteur=int(confSmart.value(self.moteurname+'/numMoteur'))

        date=time.strftime("%Y_%m_%d")
        fileNameLog='logMotor_'+date+'.log'
        #logging.basicConfig(filename=fileNameLog, encoding='utf-8', level=logging.INFO,format='%(asctime)s %(message)s')
        
        self.controller_index=Controller_index[self.numControleur]
        
    
    def position(self):
        """
        position(motor): Get position actuelle
        """
        
        position = ctypes.c_long()

        status = SMART.SA_GetPosition_S(
            ctypes.c_ulong(self.controller_index),
            ctypes.c_ulong(self.numMoteur),
            ctypes.byref(position)
        )
        if status==0:
            return position.value
        
    def stopMotor(self) :
        """
        stopmot(motor) : Stop motor
        """
        SMART.SA_Stop_S(self.controller_index,self.numMoteur)
        print( self.moteurname, "STOP")

    def rmove(self,pos,vitesse=10000):
        """
         rmove(motor,pos):Mouvement relatif en nm
        """
        status = SMART.SA_GotoPositionRelative_S(
            ctypes.c_ulong(self.controller_index),
            ctypes.c_ulong(self.numMoteur),
            ctypes.c_long(int(pos)),
            ctypes.c_ulong(60000))

        if status==0:
            print (time.strftime("%A %d %B %Y %H:%M:%S"))
            print (self.moteurname, "position before moving :", self.position(),"(step)")
            print (self.moteurname, "relative move of :",pos,"(step)")
            tx='motor ' +self.moteurname +' rmove  of ' + str(pos) + ' step  ' + '  position is :  ' + str(self.position())
        else:
            print ('error relative move of ',self.moteurname )
            tx='error relative move of ',self.moteurname
        logging.info(tx)

    def move(self,pos,vitesse=10000):
        """
        ## Mouvement Absolue en nm : move(motor,pos)
        """
        Status=SMART.SA_GotoPositionAbsolute_S(self.controller_index,self.numMoteur,int(pos),0)
        if Status==0:
            print (time.strftime("%A %d %B %Y %H:%M:%S"))
            print (self.moteurname, "position before moving :", self.position(),"(step)")
            print (self.moteurname, "move at :",pos,"(step)")
            tx='motor ' +self.moteurname +'  absolute move to ' + str(pos) + ' step  ' + '  position is :  ' + str(self.position())
        else :
            print ('error absolue move of ',self.moteurname )
            tx='error relative move of ',self.moteurname
        logging.info(tx)
    

    

#e=MOTORSMART(mot1='mot1')
#print(e.position(),e.rmove(100000))
# time.sleep(1)
# print(e.position())
# stopConnexion()