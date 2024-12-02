#!/home/sallejaune/loaenv/bin/python3.12
from PyQt6.QtWidgets import QApplication
from CamMoteurScan import CAMERAONEMOTOR
import sys
import qdarkstyle
if __name__ == "__main__":
     appli = QApplication(sys.argv) 
     appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
     e = CAMERAONEMOTOR(cam='kim')
     e.show()
     appli.exec_()
