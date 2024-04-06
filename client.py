import sys

import cv2
import socket
import pickle
import struct
import keras_ocr
from PyQt5 import QtGui
from PyQt5.QtWidgets import QWidget, QApplication, QLabel, QVBoxLayout, QPlainTextEdit
from PyQt5.QtGui import QPixmap, QImage, QFont
import sys
import cv2
from PyQt5.QtCore import pyqtSignal, pyqtSlot, Qt, QThread
import numpy as np


class VideoThread(QThread):
    change_pixmap_signal = pyqtSignal(np.ndarray)
    change_text_signal = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self._run_flag = True
        self.client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM, socket.INADDR_ANY)
        self.client_socket.connect(('10.193.166.249', 40005))
        self.payload_size = struct.calcsize("Q")
        self.data = b""
        self.pipeline = keras_ocr.pipeline.Pipeline()

    def run(self):
        # capture from web cam
        while True:
            while len(self.data) < self.payload_size:
                packet = self.client_socket.recv(4 * 1024)
                if not packet:
                    break
                self.data += packet
            if not self.data:
                break
            packed_msg_size = self.data[:self.payload_size]
            self.data = self.data[self.payload_size:]
            msg_size = struct.unpack("Q", packed_msg_size)[0]
            while len(self.data) < msg_size:
                self.data += self.client_socket.recv(4 * 1024)

            frame_data = self.data[:msg_size]
            self.data = self.data[msg_size:]
            frame = pickle.loads(frame_data)
            image = [keras_ocr.tools.read(frame)]
            prediction_groups = self.pipeline.recognize(image)
            text = ''
            for i in prediction_groups[0]:
                if i[0] not in ['container', 'front', 'back', 'side', '08', '081', '082', '083', '084', '085', '086',
                                '087', '088', '089', '090', '091',
                                '092', '093', '094', '095', '096', '097', '098', '099', '09', 'containerfront']:
                    text += i[0] + ' '
            self.change_text_signal.emit(text)
            self.change_pixmap_signal.emit(frame)
            if cv2.waitKey(1) == 13:
                break
        # shut down capture system

    def stop(self):
        """Sets run flag to False and waits for thread to finish"""
        self._run_flag = False
        self.wait()




class Main(QWidget):
    def __init__(self):
        super().__init__()
        self.setGeometry(100, 100, 640, 580)
        self.video = QPlainTextEdit(self)
        self.video.setEnabled(False)
        self.video.setGeometry(0, 0, 640, 100)
        self.video.setFont(QFont("Arial", 20))
        self.pic = QLabel(self)
        self.pic.setGeometry(0, 100, 640, 480)
        self.pic.setScaledContents(True)
        self.thread = VideoThread()
        self.thread.change_pixmap_signal.connect(self.update_image)
        self.thread.change_text_signal.connect(self.update_text)
        self.thread.start()

    def closeEvent(self, event):
        self.thread.stop()
        event.accept()

    @pyqtSlot(np.ndarray)
    def update_image(self, pic):
        image = QImage(pic.data, pic.shape[1], pic.shape[0],
                 QImage.Format_RGB888)
        self.pic.setPixmap(QPixmap.fromImage(QImage(image)))

    @pyqtSlot(str)
    def update_text(self, text):
        self.video.setPlainText('')
        self.video.setPlainText(text)


app = QApplication(sys.argv)
window = Main()
window.show()
sys.exit(app.exec_())