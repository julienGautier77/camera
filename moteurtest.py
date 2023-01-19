
from PyQt6.QtCore import QSettings
import logging
import time
confTest=QSettings('./fichiersConfig/configMoteurTest.ini', QSettings.Format.IniFormat)

class MOTORTEST():
    
    def __init__(self, mot1='test',parent=None):
        
        super(MOTORTEST, self).__init__()
        self.moteurname=mot1
        # print(self.moteurname)
        date=time.strftime("%Y_%m_%d")
        fileNameLog='logMotor_'+date+'.log'
        logging.basicConfig(filename=fileNameLog, encoding='utf-8', level=logging.INFO,format='%(asctime)s %(message)s')
        try: 
            self.numMoteur=int(confTest.value(self.moteurname+'/numMoteur'))
        except:
            self.moteurname='test'
            self.numMoteur=int(confTest.value(self.moteurname+'/numMoteur'))
        logging.info('Test moteur class used')
 
    def rmove(self,pas,vitesse=1000):
        posi=self.position()+pas
        confTest.setValue(self.moteurname+'/Pos',posi)
        tx='motor ' +self.moteurname +' rmove  of ' + str(pas) + ' step  ' + '  position is :  ' + str(self.position())

        print(tx)

        logging.info(tx)
        #return recuS

    def move(self,position,vitesse=1000):
        
        confTest.setValue(self.moteurname+'/Pos',position)
        print('motor',self.moteurname,'move',position)
        tx='motor ' +self.moteurname +'  absolute move to ' + str(position) + ' step  ' + '  position is :  ' + str(self.position())
        logging.info(tx)
    
    def position(self):
        pos=confTest.value(self.moteurname+'/Pos')
        return float(pos)
        
    
    def setzero(self):
        confTest.setValue(self.moteurname+"/Pos",0)
        tx='motor '+ self.moteurname + 'set to :  ' + '  '+ str(0)

        logging.info(tx)

    def stopMotor(self):
        print('stop motor')
