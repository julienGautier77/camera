from PyQt6.QtWidgets import QMessageBox
cam="'nameCam'"

strCam="     e = CAMERA(cam="+cam+")"
lines=['# import','from PyQt6.QtWidgets import QApplication','from camera import CAMERA','import sys','import qdarkstyle','']

lines2=['if __name__ == "__main__":','     appli = QApplication(sys.argv) ',"     appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))",""]
lines3=[strCam,"     e.show()","     appli.exec_()"]

cam="nameCam"

with open("data.py", "w") as fichier:
    fichier.write('\n'.join(lines))

    fichier.write('\n'.join(lines2))
    fichier.write('\n'.join(lines3))






# if __name__ == "__main__":       
    
#     appli = QApplication(sys.argv) 
#     appli.setStyleSheet(qdarkstyle.load_stylesheet(qt_api='pyqt6'))
#     path='/home/gautier/Documents/confCamera.ini'
#     e = CAMERA(cam='menu',fft='off',meas='on',affLight=True,aff='right',separate=True,multi=False)#,confpath=path  )
#     e.show()
    
#     appli.exec_()      