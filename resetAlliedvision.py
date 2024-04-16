try :
    import vimba 
except:
    print('vimba not installed')

try :
    import vmbpy #https://github.com/alliedvision/VmbPy    or vimba  ## pip install git+https://github.com/alliedvision/VimbaPython
except :
    print('vimbaX not installed')
import time 

with vmbpy.VmbSystem.get_instance() as vmb:
    cameraIds=vmb.get_all_cameras()
    nbCamera=len(cameraIds)
    print( nbCamera,"Alliedvision Cameras available:")
    for i in range (0,nbCamera):
        print(cameraIds[i])

for camID in cameraIds :
    with vmb:
        
        cam=vmb.get_camera_by_id(camID.get_id())
        with cam :
            a=cam.DeviceReset.run()
        print('reset cam',camID.get_id())
        time.sleep(8)