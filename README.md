# Photo-booth app
This is a PyQt GUI application for an automated photo-booth.

## Software requirements
* Windows operating system
* Python 3.11
* PyQt5
* opencv-python
* pywin32
* pillow
> :information_source: For Python dependencies, you can use
> `python.exe -r requirements.txt` to install them automatically.

## Hardware requirements
* Nikon D70s digital camera
* USB webcam
* Touchscreen
* Canon SELPHY CP1500 printer
> :information_source: Other hardware can be used but wasn't tested.

## Hardware configuration
The application will not alter the configuration of the camera or the printer.
It may detect some improper configuration but not always.  
All the camera configuration will usually be done on the camera itself, the
application will just trigger the picture capture.  
The printer configuration will usually be done in the Windows settings, the
application will just send a new document to the printer that uses all the
available printing space.
> :warning: Margins must be disabled in the printer settings in Windows.

## Application configuration
All the configuration for the application is set in the file `config.py`

## Custom picture frames
The folder `frames` must be populated with `.png` images that will be merged
with the picture taken by the camera before printing. Each image in this folder
must have the following characteristics:
* Resolution of the image: `FRAMED_PICTURE_SIZE`
* Transparent rectangle in the image, of size: `CAMERA_PICTURE_SIZE`
* Top-left coordinates of the transparent rectangle: `FRAME_IMAGE_POS`

## Usage
`python.exe main.py`

## License
The software is released under the GPLv3 license.
