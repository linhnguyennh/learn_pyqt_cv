import sys
import cv2

from PyQt6.QtWidgets import (
    QApplication, QMainWindow,
    QWidget, QHBoxLayout, QVBoxLayout,
    QPushButton, QLabel, QLineEdit,      # added QLineEdit
    QFileDialog                           # added QFileDialog
)

from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QImage, QPixmap

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Cam control app")
        self.setMinimumSize(800,500)

        #State variable
        self.mirrored = False
        self.save_folder = ""
        self.image_counter = 0
        self.last_frame = None

        #Main widget
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        #2 panels horizontal layout
        main_layout = QHBoxLayout()
        central_widget.setLayout(main_layout)

        #Cam feed placeholder
        self.feed_panel = QWidget()
        self.feed_panel.setStyleSheet("background-color: #222;")

        feed_layout = QVBoxLayout()
        feed_layout.setContentsMargins(0, 0, 0, 0)
        self.feed_panel.setLayout(feed_layout)

        self.feed_label = QLabel("No camera feed")
        self.feed_label.setStyleSheet("color: white;")
        self.feed_label.setAlignment(Qt.AlignmentFlag.AlignCenter)  # center the image/text
        feed_layout.addWidget(self.feed_label)
        #Right panel (buttons)
        self.controls_panel = QWidget()
        self.controls_panel.setStyleSheet("background-color: #444;")
        self.controls_panel.setFixedWidth(180)

        #Buttons layout inside right panel
        controls_layout = QVBoxLayout()
        controls_layout.setSpacing(10) #gap between buttons
        controls_layout.setContentsMargins(10, 20, 10, 20) #left, top, right, bottom
        self.controls_panel.setLayout(controls_layout)
        
        #Save settings section
        settings_label = QLabel("Save settings")
        settings_label.setStyleSheet("color: white; font-weight: bold;")

        self.path_display = QLineEdit()
        self.path_display.setReadOnly(True)
        self.path_display.setPlaceholderText("No folder selected")
        self.path_display.setStyleSheet("background-color: #fff;")

        self.button_browse = QPushButton("Browse Folder")
        self.button_browse.clicked.connect(self.browse_folder)

        # divider line between settings and buttons
        divider = QWidget()
        divider.setFixedHeight(1)
        divider.setStyleSheet("background-color: #666;")

        #Buttons
        self.button_a = QPushButton("Mirror")
        self.button_b = QPushButton("Save image")
        self.button_c = QPushButton("Button C")
        self.button_d = QPushButton("Button D")
        self.button_e = QPushButton("Button E")
        self.button_f = QPushButton("Button F")

        #(The long way)
        self.button_a.setFixedHeight(40)
        self.button_b.setFixedHeight(40)
        self.button_c.setFixedHeight(40)
        self.button_d.setFixedHeight(40)
        self.button_e.setFixedHeight(40)
        self.button_f.setFixedHeight(40)

        controls_layout.addWidget(settings_label)
        controls_layout.addWidget(self.path_display)
        controls_layout.addWidget(self.button_browse)
        controls_layout.addWidget(divider)

        controls_layout.addSpacing(5)

        controls_layout.addWidget(self.button_a)
        controls_layout.addWidget(self.button_b)
        controls_layout.addWidget(self.button_c)
        controls_layout.addWidget(self.button_d)
        controls_layout.addWidget(self.button_e)
        controls_layout.addWidget(self.button_f)

        #(The shortway)
        # for btn in [self.button_a, self.button_b, self.button_c, ...]:
        #       btn.setFixedHeight(40)
        #       controls_layout.addWidget(btn)
        controls_layout.addStretch()

        #Connect the buttons
        self.button_a.clicked.connect(self.toggle_mirror)
        self.button_b.clicked.connect(self.save_image)
        # Add (widget) panels to main layout
        main_layout.addWidget(self.feed_panel)
        main_layout.addWidget(self.controls_panel)


        #Webcam & Timer
        self.cap = cv2.VideoCapture(0)
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
        self.timer.start(30)        #update every 30ms (calls update_frame)

    def update_frame(self):
        ret, frame = self.cap.read() #read 1 frame
        if not ret:
            return #skip if no frame
        
        #flip image if mirror button toggled
        if self.mirrored:
            frame = cv2.flip(frame, 1) # 1 = Horizontal flip

        self.last_frame = frame.copy()

        #openCV BGR to Qt RGB
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h,w,ch = frame.shape

        qt_image = QImage(frame.data, w,h,ch*w, QImage.Format.Format_RGB888)

        #Scale image to fit label, keep aspect ration
        pixmap = QPixmap.fromImage(qt_image)
        scaled = pixmap.scaled(
            self.feed_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation
        )
        
        self.feed_label.setPixmap(scaled)
    
    def closeEvent(self,event):
        #Cleanly release webcam when closed
        self.timer.stop()
        self.cap.release()
        event.accept()

    def toggle_mirror(self):
        self.mirrored = not self.mirrored
        if self.mirrored:
            self.button_a.setText("Mirror: ON")
        else:
            self.button_a.setText("Mirror: OFF")
    
    def browse_folder(self):
        folder = QFileDialog.getExistingDirectory(
            self,
            "Select Save Folder"
        )

        if folder:
            self.save_folder = folder
            self.path_display.setText(folder)
    
    def save_image(self):
        if not self.save_folder:
            print("No folder selected!")
            return
        if self.last_frame is None:
            print("No frame to save!")
            return
    
        filename = f"image_{self.image_counter:03d}.png"
        filepath = f"{self.save_folder}/{filename}"

        cv2.imwrite(filepath, self.last_frame)
        self.image_counter += 1
        print(f"Saved: {filepath}")
    
def main():
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()