"""
Create a shortcut of createnewcamera pgr on desktop
"""

import win32com.client  # pip install pywin32
import os,sys
import pathlib
p = pathlib.Path(__file__)
target_path = str(p.parent) + "/" + 'createNewCam.py'
icon_path = str(p.parent)+"/"  + "icons" + "/" + 'video.ico'
desktop = os.path.join(os.environ['USERPROFILE'], 'Desktop')
shortcutName = 'Add new camera' + ".lnk"
shorcutPath = os.path.join(desktop,shortcutName )
shell = win32com.client.Dispatch("WScript.Shell")
shortcut = shell.CreateShortCut(shorcutPath)
shortcut.Targetpath = target_path
shortcut.WorkingDirectory = os.path.dirname(target_path)
shortcut.IconLocation = icon_path
shortcut.save() 