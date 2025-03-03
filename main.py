from PyQt5.QtWidgets import QMainWindow, QAction, QApplication, QHBoxLayout, QWidget, QGroupBox, QVBoxLayout, QLabel
from PyQt5.QtCore import Qt, QTimer

from views.image_viewer import ImageViewer
from views.video_list import VideoListWidget
from views.controls import ControlsWidget
from views.recorder import Recorder
from core.keybinds import Keybinds
from core.state import State

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()

        screen = QApplication.primaryScreen().geometry()
        screen_width = screen.width()
        screen_height = screen.height()

        window_width = int(screen_width * 0.7)
        window_height = int(screen_height * 0.7)
        self.setFixedSize(window_width, window_height)

        self.setGeometry(
            (screen_width - window_width) // 2,
            (screen_height - window_height) // 2,
            window_width,
            window_height
        )

        self.setWindowTitle("EasyLabeler")

        self.central_widget = CentralWidget()
        self.central_widget.setFocusPolicy(Qt.StrongFocus)
        self.setFocusProxy(self.central_widget)
        self.central_widget.setFocus(True)

        self.statusBar()

        mainMenu = self.menuBar()
        fileMenu = mainMenu.addMenu('&File')

        close = QAction('Close window', self)
        close.setShortcut('Ctrl+W')
        close.triggered.connect(self.close)
        fileMenu.addAction(close)

        self.setCentralWidget(self.central_widget)

        self.show()

class CentralWidget(QWidget):
    def __init__(self):
        assert QApplication.instance(), "Construct QApplication before QWidget: app = PyQt5.QtWidgets.QApplication([])"
        super().__init__()
        self.state = State(self)
        self.keybinds = Keybinds(self)
        self.keyPressEvent = self.keybinds.keyPressEvent

        self.frame_number_label = QLabel()
        self.frame_number_label.setStyleSheet("color: black;")
        self.frame_number_label.setAlignment(Qt.AlignCenter)
        self.frame_number_label.setContentsMargins(10, 10, 10, 10)

        self.controls = ControlsWidget(self, self.state)
        self.recorder = Recorder(self, self.state)
        self.image_viewer = ImageViewer(self, self.state)
        self.video_list = VideoListWidget(self, self.state)
        self.make_layout()
        self.player = None

        # Avoid keyboard not being triggered when focus on some widgets
        self.video_list.setFocusPolicy(Qt.NoFocus)
        self.setFocusPolicy(Qt.StrongFocus)

    def make_layout(self):
        main_layout = QVBoxLayout()

        content_layout = QHBoxLayout()

        navbar_box = QGroupBox("Videos")
        navbar_layout = QVBoxLayout()
        navbar_layout.addWidget(self.video_list)
        navbar_box.setLayout(navbar_layout)
        content_layout.addWidget(navbar_box)

        image_box = QGroupBox("Image")
        image_layout = QVBoxLayout()
        image_layout.addWidget(self.image_viewer)
        image_box.setLayout(image_layout)
        content_layout.addWidget(image_box)

        control_box = QGroupBox("Control")
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.controls)
        control_layout.addWidget(self.recorder)
        control_layout.addStretch()
        control_box.setLayout(control_layout)
        content_layout.addWidget(control_box)
        main_layout.addWidget(self.frame_number_label)
        main_layout.addLayout(content_layout)
        self.setLayout(main_layout)

    def update_frame_number(self, current_frame, total_frames):
        self.frame_number_label.setText(f"Frame {current_frame} of {total_frames}")

    def reload_video(self):
        self.state.video_list = self.state.find_videos()
        self.video_list.on_video_change()
        self.image_viewer.on_video_change()

    def reload_image(self):
        self.image_viewer.on_current_frame_change()

    ## KEYBINDS ##
    def play(self):
        if self.player is None:
            self.player = QTimer()
            self.player.timeout.connect(lambda: (self.state.change_frame(1), self.image_viewer.on_current_frame_change()))
            self.player.start(100)
        else:
            self.player.stop()
            self.player = None

    def skip1(self):
        self.state.change_frame(1)
        self.image_viewer.on_current_frame_change()

    def skip5(self):
        self.state.change_frame(5)
        self.image_viewer.on_current_frame_change()

    def skip_back1(self):
        self.state.change_frame(-1)
        self.image_viewer.on_current_frame_change()

    def skip_back5(self):
        self.state.change_frame(-5)
        self.image_viewer.on_current_frame_change()

if __name__ == '__main__':
    app = QApplication([])
    main_window = MainWindow()
    app.exec()