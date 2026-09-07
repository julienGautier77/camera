#!/home/upx/loaenv/bin/python3.12
from PyQt6.QtWidgets import QApplication
from camera import CAMERA
import sys
import qdarkstyle
if __name__ == "__main__":
     appli = QApplication(sys.argv) 
     appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
     e = CAMERA(cam='camShutter',scan=False,motRSAI = False)
     e.show()
     appli.exec_()
