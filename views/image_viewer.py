from PyQt5.QtWidgets import QWidget, QApplication
from PyQt5.QtCore import QPoint, Qt
from PyQt5.QtGui import QPainter, QImage
import cv2
import numpy as np

from utils.detection import Detection, Bbox
from core.state import State
from Easysort.easysort.common.logger import EasySortLogger
logger = EasySortLogger()

class ImageViewer(QWidget):
    def __init__(self, central_widget: QWidget, state: State):
        super().__init__()
        self._state = state
        self.central_widget = central_widget

        screen = QApplication.primaryScreen().geometry()
        self.fixed_width = int(screen.width() * 0.7)
        self.fixed_height = int(self.fixed_width * 0.75)
        self.setFixedSize(self.fixed_width, self.fixed_height)

        self.setFocusPolicy(Qt.StrongFocus)
        self.setFocus()

        self.setMouseTracking(True)

        self.img = None
        self.zoom = 1
        self.offset = QPoint(0, 0)

        self.is_creating_detection = False
        self.start_pos = None
        self.current_pos = None

        self.canvas = None

    def on_video_change(self):
        # Should save detections before changing video
        self.on_current_frame_change()

    def on_current_frame_change(self):
        self.current_frame = self._state.current_frame
        self.current_video = self._state.current_video
        if self._state.file_names: image_file = self._state.file_names[self._state.current_frame]
        else: return logger.critical("No image file found!")
        self.central_widget.update_frame_number(self._state.current_frame, len(self._state.file_names) - 1)
        self.img = cv2.imread(image_file)
        self.img = cv2.cvtColor(self.img, cv2.COLOR_BGR2RGB)
        self.img_scale = float(self.fixed_width) / float(self.img.shape[1])
        M = np.float32([
            [self.zoom * self.img_scale, 0, self.offset.x()],
            [0, self.zoom * self.img_scale, self.offset.y()]
        ])
        self.canvas: np.ndarray = cv2.warpAffine(self.img, M, (self.fixed_width, self.fixed_height))
        self.update()

    def mousePressEvent(self, event):
        self.setFocus()
        if event.button() == Qt.LeftButton:
            if not self.is_creating_detection:
                self.is_creating_detection = True
                self.start_pos = event.pos()
                self.current_pos = event.pos()
            else:
                self.is_creating_detection = False
                bbox = self.get_bbox_from_points(self.start_pos, self.current_pos)
                detection = Detection(
                    frame=self._state.current_frame,
                    class_id=0,  # Default class # TODO: Add class selection
                    track_id=self._state.get_next_track_id(),
                    bbox=bbox
                )
                self._state.add_detection(detection)
                self.start_pos = None
                self.current_pos = None
            self.update()

    def mouseMoveEvent(self, event):
        if self.is_creating_detection:
            self.current_pos = event.pos()
            self.update()

    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape and self.is_creating_detection:
            self.is_creating_detection = False
            self.start_pos = None
            self.current_pos = None
            self.update()

    def get_bbox_from_points(self, start, end):
        scale = 1 / (self.zoom * self.img_scale)
        x1 = min(start.x(), end.x()) * scale
        y1 = min(start.y(), end.y()) * scale
        x2 = max(start.x(), end.x()) * scale
        y2 = max(start.y(), end.y()) * scale
        return Bbox(x1, y1, x2-x1, y2-y1)

    def paintEvent(self, event):
        qp = QPainter()
        qp.begin(self)

        if self.canvas is not None:
            height, width, bpc = self.canvas.shape
            bpl = bpc * width
            img = QImage(self.canvas.data, width, height, bpl, QImage.Format_RGB888)
            qp.drawImage(QPoint(0, 0), img)

            qp.setPen(Qt.blue)
            for detection in self._state.get_frame_detections(self._state.current_frame):
                scale = self.zoom * self.img_scale
                x, y, w, h = detection.bbox.xywh() * scale
                x += self.offset.x()
                y += self.offset.y()
                qp.drawRect(int(x), int(y), int(w), int(h))

            if self.is_creating_detection and self.start_pos and self.current_pos:
                qp.setPen(Qt.red)
                x = min(self.start_pos.x(), self.current_pos.x())
                y = min(self.start_pos.y(), self.current_pos.y())
                w = abs(self.current_pos.x() - self.start_pos.x())
                h = abs(self.current_pos.y() - self.start_pos.y())
                qp.drawRect(x, y, w, h)

        qp.end()