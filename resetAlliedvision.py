
import time 


try :
    import vmbpy #https://github.com/alliedvision/VmbPy    or vimba  ## pip install git+https://github.com/alliedvision/VimbaPython
    print('VimbaX is used')
    with vmbpy.VmbSystem.get_instance() as vmb:
        cameraIds = vmb.get_all_cameras()
        nbCamera=len(cameraIds)
        print( nbCamera,"Alliedvision Cameras available:")
        for i in range (0,nbCamera):
            print(cameraIds[i])
except :
    print('vimbaX not installed')
    try :
        import vimba as vimba
        with vimba.Vimba.get_instance() as vmb:
            cameraIds = vmb.get_all_cameras()
            nbCamera = len(cameraIds)
            print( nbCamera,"Alliedvision Cameras available:")
        for i in range (0,nbCamera):
            print(cameraIds[i])
            print('vimba used')
    except:
        print('vimba not installed ')


for camID in cameraIds :
    with vmb:
        
        cam=vmb.get_camera_by_id(camID.get_id())
        with cam :
            a=cam.DeviceReset.run()
        print('reset cam ',camID.get_id(),' in progress (8s)...')
        time.sleep(8)
        print('reset cam ',camID.get_id(),' done')
        