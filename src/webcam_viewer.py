import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QPushButton, QLabel, QComboBox, QStatusBar
)
from PyQt6.QtCore import QTimer, Qt, pyqtSlot
from PyQt6.QtGui import QImage, QPixmap, QFont
import cv2
 
 
class WebcamViewer(QMainWindow):
    def __init__(self):
        super().__init__()
        self.capture = None
        self.current_source = 0
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_frame)
 
        self.setWindowTitle("Webcam Viewer")
        self.setMinimumSize(800, 600)
        self._apply_stylesheet()
        self._build_ui()
        self._detect_cameras()
        self._start_camera(self.current_source)
 
    # ------------------------------------------------------------------ UI --
 
    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        root = QVBoxLayout(central)
        root.setContentsMargins(16, 16, 16, 8)
        root.setSpacing(12)
 
        # --- video frame ---
        self.video_label = QLabel(alignment=Qt.AlignmentFlag.AlignCenter)
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setObjectName("videoLabel")
        root.addWidget(self.video_label, stretch=1)
 
        # --- controls bar ---
        controls = QHBoxLayout()
        controls.setSpacing(10)
 
        lbl = QLabel("Source:")
        lbl.setFont(QFont("Segoe UI", 10))
        controls.addWidget(lbl)
 
        self.source_combo = QComboBox()
        self.source_combo.setMinimumWidth(180)
        self.source_combo.currentIndexChanged.connect(self._on_source_changed)
        controls.addWidget(self.source_combo)
 
        controls.addStretch()
 
        self.switch_btn = QPushButton("⏭  Next Camera")
        self.switch_btn.setObjectName("switchBtn")
        self.switch_btn.clicked.connect(self._cycle_source)
        controls.addWidget(self.switch_btn)
 
        self.toggle_btn = QPushButton("⏸  Pause")
        self.toggle_btn.setObjectName("toggleBtn")
        self.toggle_btn.setCheckable(True)
        self.toggle_btn.clicked.connect(self._toggle_feed)
        controls.addWidget(self.toggle_btn)
 
        root.addLayout(controls)
 
        # --- status bar ---
        self.status = QStatusBar()
        self.setStatusBar(self.status)
        self.status.showMessage("Initialising…")
 
    def _apply_stylesheet(self):
        self.setStyleSheet("""
            QMainWindow, QWidget {
                background-color: #1a1a2e;
                color: #e0e0f0;
            }
            QLabel {
                color: #c8c8e0;
                font-family: 'Segoe UI', sans-serif;
            }
            QLabel#videoLabel {
                background-color: #0d0d1a;
                border: 2px solid #3a3a6e;
                border-radius: 8px;
            }
            QComboBox {
                background-color: #2a2a4e;
                color: #e0e0f0;
                border: 1px solid #4a4a8e;
                border-radius: 6px;
                padding: 6px 10px;
                font-size: 13px;
            }
            QComboBox::drop-down { border: none; }
            QComboBox QAbstractItemView {
                background-color: #2a2a4e;
                color: #e0e0f0;
                selection-background-color: #4a4aae;
            }
            QPushButton {
                background-color: #2a2a4e;
                color: #e0e0f0;
                border: 1px solid #4a4a8e;
                border-radius: 6px;
                padding: 7px 18px;
                font-size: 13px;
            }
            QPushButton:hover  { background-color: #3a3a6e; }
            QPushButton:pressed { background-color: #1e1e3e; }
            QPushButton#switchBtn {
                background-color: #3a2a6e;
                border-color: #6a4aae;
            }
            QPushButton#switchBtn:hover { background-color: #4a3a8e; }
            QPushButton#toggleBtn:checked {
                background-color: #6e2a2a;
                border-color: #ae4a4a;
            }
            QStatusBar {
                background-color: #0d0d1a;
                color: #8888aa;
                font-size: 12px;
            }
        """)
 
    # --------------------------------------------------------- Camera logic --
 
    def _detect_cameras(self):
        """Probe indices 0-9 for available cameras and populate combo box."""
        self.source_combo.blockSignals(True)
        self.source_combo.clear()
        available = []
 
        for idx in range(10):
            cap = cv2.VideoCapture(idx, cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_V4L2)
            if cap.isOpened():
                available.append(idx)
                self.source_combo.addItem(f"Camera {idx}", userData=idx)
                cap.release()
 
        self.source_combo.blockSignals(False)
 
        if not available:
            self.status.showMessage("⚠  No cameras detected.")
            self.video_label.setText("No camera found.\nConnect a webcam and restart.")
        else:
            self.status.showMessage(f"Found {len(available)} camera(s).")
 
    def _start_camera(self, index: int):
        self._stop_camera()
        backend = cv2.CAP_DSHOW if sys.platform == "win32" else cv2.CAP_V4L2
        self.capture = cv2.VideoCapture(index, backend)
 
        if not self.capture.isOpened():
            self.status.showMessage(f"⚠  Could not open camera {index}.")
            return
 
        w = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
        h = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
        self.current_source = index
        self.status.showMessage(f"Camera {index}  •  {w}×{h}")
        self.timer.start(30)           # ~33 fps
 
        # Sync combo without re-triggering slot
        self.source_combo.blockSignals(True)
        for i in range(self.source_combo.count()):
            if self.source_combo.itemData(i) == index:
                self.source_combo.setCurrentIndex(i)
                break
        self.source_combo.blockSignals(False)
 
    def _stop_camera(self):
        self.timer.stop()
        if self.capture and self.capture.isOpened():
            self.capture.release()
        self.capture = None
 
    # ------------------------------------------------------- Frame display --
 
    @pyqtSlot()
    def update_frame(self):
        if not self.capture or not self.capture.isOpened():
            return
 
        ok, frame = self.capture.read()
        if not ok:
            return
 
        frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        h, w, ch = frame.shape
        image = QImage(frame.data, w, h, ch * w, QImage.Format.Format_RGB888)
        pixmap = QPixmap.fromImage(image).scaled(
            self.video_label.size(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.video_label.setPixmap(pixmap)
 
    # ------------------------------------------------------------ Slots --
 
    @pyqtSlot(int)
    def _on_source_changed(self, combo_index: int):
        cam_index = self.source_combo.itemData(combo_index)
        if cam_index is not None and cam_index != self.current_source:
            self._start_camera(cam_index)
 
    @pyqtSlot()
    def _cycle_source(self):
        count = self.source_combo.count()
        if count < 2:
            self.status.showMessage("Only one camera available.")
            return
        next_idx = (self.source_combo.currentIndex() + 1) % count
        self.source_combo.setCurrentIndex(next_idx)   # triggers _on_source_changed
 
    @pyqtSlot(bool)
    def _toggle_feed(self, paused: bool):
        if paused:
            self.timer.stop()
            self.toggle_btn.setText("▶  Resume")
            self.status.showMessage(f"Camera {self.current_source}  •  Paused")
        else:
            self.timer.start(30)
            self.toggle_btn.setText("⏸  Pause")
            w = int(self.capture.get(cv2.CAP_PROP_FRAME_WIDTH))
            h = int(self.capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
            self.status.showMessage(f"Camera {self.current_source}  •  {w}×{h}")
 
    # ----------------------------------------------------------- Cleanup --
 
    def closeEvent(self, event):
        self._stop_camera()
        super().closeEvent(event)
 
 
# --------------------------------------------------------------------------- #
 
def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    win = WebcamViewer()
    win.show()
    sys.exit(app.exec())
 
 
if __name__ == "__main__":
    main()