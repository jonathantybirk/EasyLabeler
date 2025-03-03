import unittest
from PyQt5.QtWidgets import QApplication
import sys
from main import CentralWidget
from utils.detection import Detection
from core.state import State
import os
from config import DATA_DIR
import numpy as np
from PIL import Image

class TestState(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.app = QApplication(sys.argv)
        cls.central_widget = CentralWidget()
        cls.state: State = cls.central_widget.state
        cls.state.current_video = "new/test"

    @classmethod
    def tearDownClass(cls):
        cls.app.quit()

    def setUp(self):
        self.state.reset_annotations()

    def test_init_state(self):
        self.state.load_annotations()
        self.assertEqual(len(self.state.detections), 2)
        self.state.reset_annotations()
        self.assertEqual(len(self.state.detections), 0)

    def test_add_detection(self):
        self.assertEqual(len(self.state.detections), 0)
        self.state.add_detection(Detection(frame=0, class_id=0, track_id=0, bbox=[0, 0, 100, 100]))
        self.assertEqual(len(self.state.detections), 1)

    def test_delete_detection(self):
        self.state.add_detection(Detection(frame=0, class_id=0, track_id=4, bbox=[0, 0, 100, 100]))
        self.assertEqual(len(self.state.detections), 1)
        self.state.delete_detection([4])
        self.assertEqual(len(self.state.detections), 0)

    def test_update_detection(self):
        self.state.add_detection(Detection(frame=0, class_id=0, track_id=4, bbox=[0, 0, 100, 100]))
        self.assertEqual(len(self.state.detections), 1)
        print(self.state.detections)
        self.state.update_detection(Detection(frame=0, class_id=0, track_id=4, bbox=[0, 0, 200, 200]))
        self.assertEqual(len(self.state.detections), 1)
        print(self.state.detections)
        self.assertEqual(self.state.detections[4].bbox.xywh().tolist(), [0, 0, 200, 200])

    def test_asserts(self):
        self.state.add_detection(Detection(frame=0, class_id=0, track_id=4, bbox=[0, 0, 100, 100]))
        with self.assertRaises(AssertionError):
            self.state.add_detection(Detection(frame=0, class_id=0, track_id=4, bbox=[0, 0, 100, 100]))
        with self.assertRaises(AssertionError):
            self.state.update_detection(Detection(frame=0, class_id=0, track_id=5, bbox=[0, 0, 100, 100]))
        with self.assertRaises(AssertionError):
            self.state.delete_detection([5])

    def test_get_frame_detections(self):
        self.state.add_detection(Detection(frame=0, class_id=0, track_id=4, bbox=[0, 0, 100, 100]))
        self.assertEqual(len(self.state.get_frame_detections(0)), 1)
        self.assertEqual(len(self.state.get_frame_detections(1)), 0)

    def test_get_next_track_id(self):
        self.assertEqual(self.state.get_next_track_id(), 0)
        self.state.add_detection(Detection(frame=0, class_id=0, track_id=0, bbox=[0, 0, 100, 100]))
        self.assertEqual(self.state.get_next_track_id(), 1)
        self.state.add_detection(Detection(frame=0, class_id=0, track_id=1, bbox=[0, 0, 100, 100]))
        self.assertEqual(self.state.get_next_track_id(), 2)
        self.state.add_detection(Detection(frame=0, class_id=0, track_id=2, bbox=[0, 0, 100, 100]))
        self.assertEqual(self.state.get_next_track_id(), 3)
        self.state.delete_detection([1])
        self.assertEqual(self.state.get_next_track_id(), 1)
        self.state.delete_detection([0, 2])
        self.assertEqual(self.state.get_next_track_id(), 0)

    def test_empty_folder_handling(self):
        noise = np.random.randint(0, 255, (100, 100, 3), dtype=np.uint8)
        img = Image.fromarray(noise)

        initial_video_count = len(self.state.video_list)

        os.makedirs(os.path.join(DATA_DIR, 'new/empty'), exist_ok=True)
        os.makedirs(os.path.join(DATA_DIR, 'new/full'), exist_ok=True)
        img.save(os.path.join(DATA_DIR, 'new/full', 'random_noise.jpg'))

        os.makedirs(os.path.join(DATA_DIR, 'verified/empty'), exist_ok=True)
        os.makedirs(os.path.join(DATA_DIR, 'verified/full'), exist_ok=True)
        img.save(os.path.join(DATA_DIR, 'verified/full', 'random_noise.jpg'))

        self.state.load_videos()

        added_video_count = len(self.state.video_list) - initial_video_count

        self.assertEqual(added_video_count, 2)

        # Clean up test files and directories
        for base in ['new', 'verified']:
            empty_folder = os.path.join(DATA_DIR, base, "empty")
            full_folder = os.path.join(DATA_DIR, base, "full")

            assert len(os.listdir(empty_folder)) == 0
            assert len(os.listdir(full_folder)) == 1

            os.remove(os.path.join(full_folder, 'random_noise.jpg'))

            os.rmdir(os.path.join(DATA_DIR, base, 'empty'))
            os.rmdir(os.path.join(DATA_DIR, base, 'full'))


if __name__ == "__main__":
    unittest.main()