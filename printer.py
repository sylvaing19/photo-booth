import win32con
import win32ui
import win32print
from PIL import Image, ImageWin
import datetime
import shutil
import os
import sys
from os.path import join, splitext
from config import PRINTER_NAME, PRINTER_OUT_DIRECTORY, FRAME_OUT_FILENAME


def save_picture() -> str:
    index = len(next(os.walk(PRINTER_OUT_DIRECTORY))[2])
    _, ext = splitext(FRAME_OUT_FILENAME)
    filename = str(index) + datetime.datetime.now().strftime("-%H-%M-%S") + ext
    shutil.copy(FRAME_OUT_FILENAME, join(PRINTER_OUT_DIRECTORY, filename))
    return filename


def check_printer():
    # https://stackoverflow.com/questions/12041648/python-win32print-printer-status-confusion
    printer_handler = win32print.OpenPrinter(PRINTER_NAME)
    try:
        printer_info = win32print.GetPrinter(printer_handler)[13]
        if (printer_info & 0x00000400) >> 10:
            raise RuntimeError("Printer not connected or turned off")
    finally:
        win32print.ClosePrinter(printer_handler)


def print_picture(name: str):
    # https://stackoverflow.com/questions/54522120/python3-print-landscape-image-file-with-specified-printer

    # Open image to be printed
    img = Image.open(FRAME_OUT_FILENAME)
    img_width, img_height = img.size

    # Create Device Context (DC)
    hdc = win32ui.CreateDC()
    hdc.CreatePrinterDC(PRINTER_NAME)

    # Read printer capabilities
    h_res = hdc.GetDeviceCaps(win32con.HORZRES)
    v_res = hdc.GetDeviceCaps(win32con.VERTRES)
    h_phy_res = hdc.GetDeviceCaps(win32con.PHYSICALWIDTH)
    v_phy_res = hdc.GetDeviceCaps(win32con.PHYSICALHEIGHT)

    # Check that the printable area is the full physical area (no margins)
    if h_res < h_phy_res or v_res < v_phy_res:
        raise RuntimeError("Printer has margins, change this setting in the "
                           "Windows control panel.")

    # Rotate the image if needed
    landscape = h_res > v_res
    if landscape:
        if img_height > img_width:
            # Printer in landscape mode, tall image: rotate bitmap.
            img = img.rotate(90, expand=True)
    else:
        if img_height < img_width:
            # Printer in portrait mode, wide image: rotate bitmap.
            img = img.rotate(90, expand=True)
    img_width, img_height = img.size

    if landscape:
        # We want the image width to match the page width (potentially cropping
        # the top and bottom of the image)
        max_width = img_width
        max_height = round(img_width * v_res / h_res)
    else:
        # We want the image height to match the page height (potentially
        # cropping the left and right of the image)
        max_height = img_height
        max_width = round(max_height * h_res / v_res)

    # Map image size to page size
    hdc.SetMapMode(win32con.MM_ISOTROPIC)
    hdc.SetViewportExt((h_res, v_res))
    hdc.SetWindowExt((img_width, img_height))

    # Offset image so it is centered
    offset_x = round((max_width - img_width) / 2)
    offset_y = round((max_height - img_height) / 2)
    hdc.SetWindowOrg((-offset_x, -offset_y))

    # Make new document and write the image
    hdc.StartDoc(name)
    hdc.StartPage()
    dib = ImageWin.Dib(img)
    dib.draw(hdc.GetHandleOutput(), (0, 0, img_width, img_height))
    hdc.EndPage()
    hdc.EndDoc()

    # Delete the Device Context
    hdc.DeleteDC()


def available_printer_names():
    flags = win32print.PRINTER_ENUM_LOCAL | win32print.PRINTER_ENUM_CONNECTIONS
    printers = win32print.EnumPrinters(flags)
    for _, _, name, _ in printers:
        print(name)


if __name__ == "__main__":
    try:
        n = save_picture()
        check_printer()
        print_picture(n)
    except Exception as e:
        print(str(e), file=sys.stderr)
        exit(-1)
