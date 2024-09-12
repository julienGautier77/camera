#! /usr/bin/python3
import sys
import pathlib
import os
import subprocess
path = pathlib.Path(__file__)
path = str(path.parent)

fichierRacourci='createNewCam.desktop'
fichierName = 'createNewCam'

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
                    l3 = ['Exec='+path+"/"+fichierName+".py"]
                    fichierR.write('\n'.join(l3))
                    fichierR.write('\n')
                    l4 = ['Name='+ fichierName]
                    fichierR.write('\n'.join(l4))
                    fichierR.write('\n')
                    lll = ['StartupNotify=true']
                    fichierR.write('\n'.join(lll))
                    fichierR.write('\n')
                    l5 = ['Icon='+path+'/icons/video.png']
                    fichierR.write('\n'.join(l5))
                    fichierR.write('\n')
                    
                    fichierR.close()



fichierName = 'createNewCam.py'

cmd = 'chmod +x %s'%fichierName # autorisation fichier.py
subprocess.run(cmd,shell=True, executable="/bin/bash")
    
bureauPath = str(pathlib.Path(__file__).parent.parent.parent.parent)+'/'+'Bureau'
cmd = 'cp %s '%fichierRacourci + str(bureauPath)
subprocess.run(cmd,shell=True, executable="/bin/bash")

cmd = 'chmod +x '+bureauPath+'/%s'%fichierRacourci
subprocess.run(cmd,shell=True, executable="/bin/bash")
 