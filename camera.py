import win32com.client
import pywintypes
import time
import shutil
import sys
import os
from os.path import join
from config import (CAMERA_MANUFACTURER, CAMERA_DEVICE_NAME,
                    CAMERA_OUT_FILENAME, CAMERA_OUT_DIRNAME)


def to_hex(val, nbits):
    return hex((val + (1 << nbits)) % (1 << nbits))


def wia_err_to_str(e) -> str:
    return e.excepinfo[2].strip() + " (" + to_hex(e.args[0], 32) + ")"


def find_device(manager):
    print("Scan devices...")
    for device_info in manager.DeviceInfos:
        p_manufacturer = str(device_info.Properties["Manufacturer"])
        p_name = str(device_info.Properties["Name"])
        print("  - " + p_manufacturer + " (" + p_name + ")")
        if (p_manufacturer == CAMERA_MANUFACTURER and
                p_name == CAMERA_DEVICE_NAME):
            print("Target found")
            return device_info
    raise RuntimeError("Target device not found")


def take_picture(device) -> int:
    try:
        d = device.Connect()
        picture_count = d.Items.count
        d.ExecuteCommand("{AF933CAC-ACAD-11D2-A093-00C04F72DC3C}")
        return picture_count
    except pywintypes.com_error as e:
        raise RuntimeError("[take_picture] Camera error: " + wia_err_to_str(e))
    except Exception as e:
        raise RuntimeError("[take_picture] Unexpected error: " + str(e))


def wait_for_picture(device, picture_count: int):
    for _ in range(15):
        time.sleep(1)
        d = device.Connect()
        if d.Items.count > picture_count:
            return
    raise RuntimeError("Timeout while waiting for picture")


def get_picture(device):
    try:
        os.remove(CAMERA_OUT_FILENAME)
        d = device.Connect()
        last_pic = d.Items(d.Items.count)
        name = str(last_pic.Properties["Item Name"].Value) + ".jpg"
        wia_img = last_pic.Transfer()
        wia_img.SaveFile(CAMERA_OUT_FILENAME)
        shutil.copy(CAMERA_OUT_FILENAME, join(CAMERA_OUT_DIRNAME, name))
    except pywintypes.com_error as e:
        raise RuntimeError("[get_picture] WIA error: " + wia_err_to_str(e))
    except Exception as e:
        raise RuntimeError("[get_picture] Unexpected error: " + str(e))


if __name__ == "__main__":
    try:
        camera = find_device(win32com.client.Dispatch("WIA.DeviceManager"))
        pc = take_picture(camera)
        wait_for_picture(camera, pc)
        get_picture(camera)
    except RuntimeError as error:
        print(str(error), file=sys.stderr)
        exit(-1)
