from PyQt6.QtCore import QObject, QThread, pyqtSignal
import cv2
import numpy as np
from queue import Queue

class CaptureThread(QThread):
    frame_ready = pyqtSignal(np.ndarray)

    def __init__(self, frame_queue : Queue):
        super().__init__()
        self._running = True
        self.frame_queue = frame_queue


    def run(self): #When thread is created (started), then call this
        cap = cv2.VideoCapture(0)
        while self._running:
            ret, frame = cap.read()
            # if ret:
            #     self.frame_ready.emit(frame)  # generate signal for main thread to catch (only display, no process)
            if ret and not self.frame_queue.full():
                self.frame_queue.put(frame) # queue frame to be processed 

        cap.release()
    
    def stop(self):
        self._running = False
        self.wait()  # blocks until thread finishes