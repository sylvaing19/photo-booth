import sys
import os
import cv2
from PyQt5.QtWidgets import (QMainWindow, QApplication, QWidget, QHBoxLayout,
                             QPushButton, QVBoxLayout, QFrame,
                             QGraphicsDropShadowEffect, QLabel, QGridLayout)
from PyQt5.QtCore import Qt, pyqtSignal, QSize, QTimer, QProcess, QThread
from PyQt5.QtGui import QImage, QPixmap, QIcon
from os.path import join, dirname, splitext
from random import randrange
from PIL import Image
from config import (WEBCAM_ID, COUNTDOWN_DURATION, INACTIVITY_TIMEOUT,
                    ERROR_MSG_TIMEOUT, CAMERA_MAX_RETRY, CAMERA_PICTURE_SIZE,
                    CAMERA_OUT_FILENAME, PREVIEW_SIZE, FRAME_DIRECTORY,
                    FRAMED_PICTURE_SIZE, FRAME_IMAGE_POS, FRAME_OUT_FILENAME)

# How to disable edge-of-touchscreen gestures:
# https://sps-support.honeywell.com/s/article/How-to-disable-touchscreen-edge-swipes-in-Windows-10
# Add the registry entry:
# HKEY_LOCAL_MACHINE\SOFTWARE\Policies\Microsoft\Windows\EdgeUI
# Create new 32-bit DWORD entry with value 0


def apply_shadow(widget: QWidget, radius: float):
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(radius)
    shadow.setColor(Qt.black)
    shadow.setOffset(0, 0)
    widget.setGraphicsEffect(shadow)


def apply_font(widget: QWidget, size: int, bold: bool = False,
               italic: bool = False):
    f = widget.font()
    f.setFamily("Century Gothic")
    f.setBold(bold)
    f.setItalic(italic)
    f.setPixelSize(size)
    widget.setFont(f)


class CentralWidget(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("CentralWidget")
        self._size = QSize(*PREVIEW_SIZE)
        apply_shadow(self, 100)
        self._img = QLabel(self)
        self._img.setAlignment(Qt.AlignCenter)
        self._img.setFixedSize(self._size)
        grid = QVBoxLayout()
        grid.setContentsMargins(5, 5, 5, 5)
        grid.addWidget(self._img)
        self.setLayout(grid)


class WebcamWidget(CentralWidget):
    def __init__(self, parent):
        super().__init__(parent)
        self._frame_timer = QTimer(self)
        self._frame_timer.setSingleShot(False)
        self._frame_timer.setInterval(20)
        self._frame_timer.timeout.connect(self._frame_update)
        QTimer.singleShot(0, self._init_webcam)

    def _init_webcam(self):
        self._img.setText("Connection à la webcam...")
        self.repaint()
        self._capture = cv2.VideoCapture(WEBCAM_ID)
        if self._capture.isOpened():
            self._img.setText("")
            self._frame_timer.start()
        else:
            self._img.setText("Echec de connection à la webcam")

    def _frame_update(self):
        is_reading, frame = self._capture.read()
        if is_reading:
            image = self._convert_image(frame)
            self._img.setPixmap(QPixmap.fromImage(image))
        else:
            self._frame_timer.stop()

    def _convert_image(self, image):
        image = cv2.resize(image, (self._size.width(), self._size.height()),
                           interpolation=cv2.INTER_AREA)
        image = cv2.flip(image, 1)
        image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        image = QImage(image, image.shape[1], image.shape[0],
                       QImage.Format_RGB888)
        return image


class Cheese(CentralWidget):
    take_picture = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self._icon = QIcon(join("assets", "cheese.svg"))
        self._err_icon = QIcon(join("assets", "error.svg"))
        apply_font(self._img, 500)
        apply_shadow(self._img, 50)

    def start(self):
        self._img.setPixmap(QPixmap())
        self._img.setText("2")
        QTimer.singleShot(1000, self._one_second)

    def error(self):
        self._img.setText("")
        self._img.setPixmap(self._err_icon.pixmap(self._img.size()))

    def _one_second(self):
        self._img.setText("1")
        QTimer.singleShot(1000, self._cheese)

    def _cheese(self):
        self._img.setText("")
        self._img.setPixmap(self._icon.pixmap(self._img.size()))
        self.take_picture.emit()


class Preview(CentralWidget):
    preview_ready = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self._bg_thread = QThread(self)
        self._bg_thread.run = self._make_montage
        self._bg_thread.finished.connect(self._on_montage_done)
        self._icon = QIcon(join("assets", "wait.svg"))
        self._pixmap = QPixmap()
        self._current_frame = 0
        self._frames = []

    def _new_frame(self):
        self._frames = [join(FRAME_DIRECTORY, f)
                        for f in next(os.walk(FRAME_DIRECTORY))[2]
                        if splitext(f)[1].lower() == ".png"]
        self._current_frame = randrange(len(self._frames))

    def _next_frame(self):
        self._current_frame += 1
        if self._current_frame >= len(self._frames):
            self._current_frame = 0

    def compute(self, randomized):
        if randomized:
            self._new_frame()
        else:
            self._next_frame()
        self._img.setPixmap(self._icon.pixmap(self._img.size() / 2))
        self._bg_thread.start()

    def _make_montage(self):
        frame = Image.open(self._frames[self._current_frame])
        picture = Image.open(CAMERA_OUT_FILENAME)
        if frame.size != FRAMED_PICTURE_SIZE:
            print("Warning: frame has unexpected resolution")
        if picture.size != CAMERA_PICTURE_SIZE:
            print("Warning: picture from camera has unexpected resolution")
        output = Image.new('RGBA', frame.size)
        output.paste(picture, FRAME_IMAGE_POS)
        output.paste(frame, (0, 0), frame)
        output.save(FRAME_OUT_FILENAME)
        pixmap = QPixmap(FRAME_OUT_FILENAME)
        cropped_w = round(pixmap.height() *
                          self._size.width() / self._size.height())
        pixmap = pixmap.copy((pixmap.width() - cropped_w) // 2, 0,
                             cropped_w, pixmap.height())
        self._pixmap = pixmap.scaled(
            self._size, Qt.KeepAspectRatio, Qt.SmoothTransformation)

    def _on_montage_done(self):
        self._img.setPixmap(self._pixmap)
        self.preview_ready.emit()


class AbstractButton(QFrame):
    clicked = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("AbstractButton")
        self._button = QPushButton(self)
        self._button.setIconSize(QSize(120, 120))
        apply_shadow(self._button, 100)
        self._button.clicked.connect(self.clicked.emit)
        self._label = QLabel(self)
        apply_font(self._label, 20)
        self._label.setAlignment(Qt.AlignTop | Qt.AlignHCenter)
        grid = QVBoxLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.setSpacing(20)
        btn_grid = QHBoxLayout()
        btn_grid.addStretch(1)
        btn_grid.addWidget(self._button)
        btn_grid.addStretch(1)
        grid.addStretch(1)
        grid.addLayout(btn_grid)
        grid.addWidget(self._label, stretch=1)
        self.setLayout(grid)


class PhotoWidget(AbstractButton):
    def __init__(self, parent):
        super().__init__(parent)
        self._button.setIcon(QIcon(join("assets", "photo.svg")))
        self._label.setText("Prendre une photo")


class PrinterWidget(AbstractButton):
    def __init__(self, parent):
        super().__init__(parent)
        self._button.setIcon(QIcon(join("assets", "printer.svg")))
        self._label.setText("Imprimer la photo")


class ChangeQuoteWidget(AbstractButton):
    def __init__(self, parent):
        super().__init__(parent)
        self._button.setIcon(QIcon(join("assets", "quote.svg")))
        self._label.setText("Changer de citation")


class BottomLabel(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self._title = QLabel(self)
        self._subtitle = QLabel(self)
        apply_font(self._title, 120)
        apply_font(self._subtitle, 60)
        apply_shadow(self._title, 25)
        apply_shadow(self._subtitle, 25)
        self._title.setAlignment(Qt.AlignCenter)
        self._subtitle.setAlignment(Qt.AlignCenter)
        grid = QVBoxLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.addStretch(1)
        grid.addWidget(self._title)
        grid.addWidget(self._subtitle)
        grid.addStretch(1)
        self.setLayout(grid)

    def set_welcome(self):
        self._title.setText("Bienvenue au stand photo !")
        self._subtitle.setText(
            "Appuyez sur le bouton, prenez la pose, souriez...")

    def set_look_up(self):
        self._title.setText("Regardez l'objectif")
        self._subtitle.setText("")

    def set_review_picture(self):
        self._title.setText("Magnifique ! On imprime ?")
        self._subtitle.setText("")

    def set_pre_printing(self):
        self._title.setText("Démarrage de l'impression...")
        self._subtitle.setText("")

    def set_printing(self):
        self._title.setText("Impression en cours")
        self._subtitle.setText("La photo sera prête dans 45 secondes")

    def set_photo_error(self):
        self._title.setText("Echec de prise de vue")
        self._subtitle.setText("Si le problème persiste, appelez Sylvain")

    def set_printer_error(self):
        self._title.setText("Echec d'impression")
        self._subtitle.setText("La photo est quand même sauvegardée")


class Countdown(QFrame):
    last_second = pyqtSignal()

    def __init__(self, parent):
        super().__init__(parent)
        self._duration = 0
        self._label = QLabel(self)
        apply_font(self._label, 300)
        apply_shadow(self._label, 25)
        self._label.setAlignment(Qt.AlignCenter)
        grid = QVBoxLayout()
        grid.setContentsMargins(0, 0, 0, 0)
        grid.addWidget(self._label, stretch=1)
        self.setLayout(grid)

    def start(self, duration: int):
        self._duration = duration
        self._label.setText(str(duration))
        QTimer.singleShot(1000, self._decrement)

    def _decrement(self):
        self._duration -= 1
        if self._duration > 2:
            self._label.setText(str(self._duration))
            QTimer.singleShot(1000, self._decrement)
        else:
            self._label.setText("")
            self.last_second.emit()


class MainWidget(QFrame):
    def __init__(self, parent):
        super().__init__(parent)
        self.setObjectName("MainWidget")

        # Widgets
        self._img = WebcamWidget(self)
        self._btn_photo = PhotoWidget(self)
        self._btn_printer = PrinterWidget(self)
        self._btn_quote = ChangeQuoteWidget(self)
        self._label = BottomLabel(self)
        self._countdown = Countdown(self)
        self._cheese = Cheese(self)
        self._preview = Preview(self)

        # Inactivity timer
        self._inactivity = QTimer(self)
        self._inactivity.setSingleShot(True)
        self._inactivity.setInterval(INACTIVITY_TIMEOUT)
        self._inactivity.timeout.connect(self._on_reset)

        # Process
        self._camera_task = QProcess(self)
        self._camera_task.finished.connect(self._on_picture_taken)
        self._printer_task = QProcess(self)
        self._printer_task.finished.connect(self._on_print_sent)

        # Signals
        self._btn_photo.clicked.connect(self._on_photo_clicked)
        self._btn_printer.clicked.connect(self._on_printer_clicked)
        self._btn_quote.clicked.connect(self._on_make_preview)
        self._countdown.last_second.connect(self._on_cheese)
        self._cheese.take_picture.connect(self._on_take_picture)
        self._preview.preview_ready.connect(self._on_preview_ready)

        # Variables
        self._camera_retry_count = 0

        # Init
        self._on_reset()

        # Layout
        grid = QGridLayout()
        grid.addWidget(self._img, 0, 1)
        grid.addWidget(self._btn_photo, 0, 2)
        v_grid = QVBoxLayout()
        v_grid.addWidget(self._btn_printer)
        v_grid.addWidget(self._btn_quote)
        grid.addLayout(v_grid, 0, 0)
        grid.addWidget(self._label, 1, 0, 1, 3)
        grid.addWidget(self._countdown, 1, 1)
        grid.addWidget(self._cheese, 0, 1)
        grid.addWidget(self._preview, 0, 1)
        grid.setColumnStretch(0, 1)
        grid.setColumnStretch(2, 1)
        grid.setRowStretch(1, 1)
        self.setLayout(grid)

    def _on_reset(self):
        self._img.show()
        self._show_buttons(True)
        self._enable_buttons(photo_only=True)
        self._label.show()
        self._label.set_welcome()
        self._countdown.hide()
        self._cheese.hide()
        self._preview.hide()

    def _on_photo_clicked(self):
        self._inactivity.stop()
        self._img.show()
        self._enable_buttons(False)
        self._label.hide()
        self._countdown.show()
        self._countdown.start(COUNTDOWN_DURATION)
        self._cheese.hide()
        self._preview.hide()

    def _on_cheese(self):
        self._img.hide()
        self._show_buttons(False)
        self._countdown.hide()
        self._label.show()
        self._label.set_look_up()
        self._cheese.show()
        self._cheese.start()

    def _on_take_picture(self, retry=False):
        if not retry:
            self._camera_retry_count = 0
        self._camera_task.start(sys.executable, ["camera.py"])

    def _on_picture_taken(self, ret_code: int):
        if ret_code == 0:
            self._on_make_preview(new_picture=True)
        else:
            print(str(self._camera_task.readAllStandardError(), 'utf-8'))
            self._camera_retry_count += 1
            if self._camera_retry_count < CAMERA_MAX_RETRY:
                self._on_take_picture(retry=True)
            else:
                self._on_error(photo_error=True)

    def _on_error(self, photo_error):
        self._show_buttons(True)
        self._enable_buttons(photo_only=True)
        self._label.show()
        if photo_error:
            self._label.set_photo_error()
        else:
            self._label.set_printer_error()
        self._cheese.show()
        self._cheese.error()
        self._inactivity.start(ERROR_MSG_TIMEOUT)

    def _on_make_preview(self, new_picture=False):
        self._inactivity.stop()
        self._show_buttons(True)
        self._enable_buttons(False)
        self._label.hide()
        self._cheese.hide()
        self._preview.show()
        self._preview.compute(randomized=new_picture)

    def _on_preview_ready(self):
        self._enable_buttons(True)
        self._label.show()
        self._label.set_review_picture()
        self._inactivity.start(INACTIVITY_TIMEOUT)

    def _on_printer_clicked(self):
        self._inactivity.stop()
        self._enable_buttons(False)
        self._label.set_pre_printing()
        self._printer_task.start(sys.executable, ["printer.py"])

    def _on_print_sent(self, ret_code: int):
        if ret_code == 0:
            self._label.set_printing()
            self._enable_buttons(photo_only=True)
            self._inactivity.start(7000)
        else:
            print(str(self._printer_task.readAllStandardError(), 'utf-8'))
            self._on_error(photo_error=False)

    def _show_buttons(self, show):
        self._btn_photo.setVisible(show)
        self._btn_printer.setVisible(show)
        self._btn_quote.setVisible(show)

    def _enable_buttons(self, enable=False, photo_only=False):
        if photo_only:
            self._btn_photo.setEnabled(True)
            self._btn_printer.setEnabled(False)
            self._btn_quote.setEnabled(False)
        else:
            self._btn_photo.setEnabled(enable)
            self._btn_printer.setEnabled(enable)
            self._btn_quote.setEnabled(enable)


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        w = MainWidget(self)
        self.setCentralWidget(w)
        self.setCursor(Qt.BlankCursor)


def except_hook(t, value, traceback):
    sys.__excepthook__(t, value, traceback)


if __name__ == '__main__':
    sys.excepthook = except_hook
    root = dirname(__file__)
    os.chdir(root)
    with open("stylesheet.css") as css_file:
        stylesheet = css_file.read()
    app = QApplication(sys.argv)
    win = MainWindow()
    win.setStyleSheet(stylesheet)
    win.showFullScreen()
    ret = app.exec()
    sys.exit(ret)
