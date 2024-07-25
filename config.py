
# --- UI Config ---
# Index of the camera in OpenCV, '0' is usually the integrated webcam
WEBCAM_ID = 1

# Duration of the countdown before taking a picture (in seconds)
COUNTDOWN_DURATION = 7

# Duration showing the picture taken before coming back to the welcome screen
INACTIVITY_TIMEOUT = 60000

# Duration showing the error message in case of failure
ERROR_MSG_TIMEOUT = 15000

# Size of the preview in the GUI
PREVIEW_SIZE = (960, 720)


# --- Printer Config ---
# Identification of the printer
PRINTER_NAME = "Canon SELPHY CP1500"

# Directory to store all the pictures printed
PRINTER_OUT_DIRECTORY = "printed"


# --- Camera Config ---
# Identification of the camera
CAMERA_MANUFACTURER = "Nikon Corporation"
CAMERA_DEVICE_NAME = "D70s"

# Directory to store all the original pictures taken by the camera
CAMERA_OUT_DIRNAME = "pictures"

# Filename of the latest picture taken by the camera
CAMERA_OUT_FILENAME = "latest.jpg"

# Size of the pictures taken by the camera
CAMERA_PICTURE_SIZE = (1504, 1000)

# Number of attempts to take a picture before showing an error
CAMERA_MAX_RETRY = 3


# --- Photo montage config ---
# Directory for the empty frames
FRAME_DIRECTORY = "frames"

# Size of the picture with the frame (to be printed)
FRAMED_PICTURE_SIZE = (1748, 1181)

# Position of the image within the frame
FRAME_IMAGE_POS = (122, 91)

# Filename of the framed picture
FRAME_OUT_FILENAME = "latest-framed.png"
