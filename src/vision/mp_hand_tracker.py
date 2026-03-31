from PyQt6.QtCore import QThread, pyqtSignal
import cv2
import numpy as np
import mediapipe as mp
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
from queue import Queue, Empty

mp_hands = mp.tasks.vision.HandLandmarksConnections
mp_drawing = mp.tasks.vision.drawing_utils
mp_drawing_styles = mp.tasks.vision.drawing_styles

MARGIN = 10  # pixels
FONT_SIZE = 1
FONT_THICKNESS = 1
HANDEDNESS_TEXT_COLOR = (88, 205, 54) # vibrant green

class MediaPipeThread(QThread):
    frame_ready = pyqtSignal(np.ndarray)

    def __init__(self, frame_queue : Queue):
        super().__init__()
        self.frame_queue = frame_queue
        self._running = True


        #Create HandLandmarker object
        base_options = python.BaseOptions(model_asset_path='./data/model/hand_landmarker.task')
        options = vision.HandLandmarkerOptions(base_options=base_options,
                                                running_mode=vision.RunningMode.IMAGE,  # ← async mode
                                                num_hands=2)
        self.detector = vision.HandLandmarker.create_from_options(options)
            
    def run(self): #When thread is created (started), then call this
        while self._running:
            #Flush frame until queue empty --> no stale frame
            try:
                frame = None
                while True:
                    frame = self.frame_queue.get_nowait()
            except Empty:
                pass

            #Process frame
            if frame is not None:
                
                rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                mp_image = mp.Image(image_format= mp.ImageFormat.SRGB,data=rgb)
                detection_result  = self.detector.detect(mp_image)
                annotated_image_rgb =  draw_landmarks_on_image(rgb,detection_result)
                self.frame_ready.emit(annotated_image_rgb) 

    def stop(self):
        self._running = False
        self.wait()

    def process_hand(self):
        pass


def draw_landmarks_on_image(rgb_image, detection_result):
  hand_landmarks_list = detection_result.hand_landmarks
  handedness_list = detection_result.handedness
  annotated_image = np.copy(rgb_image)

  # Loop through the detected hands to visualize.
  for idx in range(len(hand_landmarks_list)):
    hand_landmarks = hand_landmarks_list[idx]
    handedness = handedness_list[idx]

    # Draw the hand landmarks.
    mp_drawing.draw_landmarks(
      annotated_image,
      hand_landmarks,
      mp_hands.HAND_CONNECTIONS,
      mp_drawing_styles.get_default_hand_landmarks_style(),
      mp_drawing_styles.get_default_hand_connections_style())

    # Get the top left corner of the detected hand's bounding box.
    height, width, _ = annotated_image.shape
    x_coordinates = [landmark.x for landmark in hand_landmarks]
    y_coordinates = [landmark.y for landmark in hand_landmarks]
    text_x = int(min(x_coordinates) * width)
    text_y = int(min(y_coordinates) * height) - MARGIN

    # Draw handedness (left or right hand) on the image.
    cv2.putText(annotated_image, f"{handedness[0].category_name}",
                (text_x, text_y), cv2.FONT_HERSHEY_DUPLEX,
                FONT_SIZE, HANDEDNESS_TEXT_COLOR, FONT_THICKNESS, cv2.LINE_AA)

  return annotated_image