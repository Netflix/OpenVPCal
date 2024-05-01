"""
Copyright 2024 Netflix Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from test_open_vp_cal.test_utils import TestProcessorBase

from open_vp_cal.framework.sequence_loader import FrameRangeException


class TestSequenceLoader(TestProcessorBase):
    def test_set_start_frame(self):
        """Test that set_start_frame updates the start frame value."""
        self.led_wall.sequence_loader.set_start_frame(5)
        self.assertEqual(self.led_wall.sequence_loader.start_frame, 5)

    def test_set_end_frame(self):
        """Test that set_end_frame updates the end frame value."""
        self.led_wall.sequence_loader.set_end_frame(10)
        self.assertEqual(self.led_wall.sequence_loader.end_frame, 10)

    def test_set_current_frame(self):
        """Test that set_current_frame updates the current frame value."""
        self.led_wall.sequence_loader.set_start_frame(0)
        self.led_wall.sequence_loader.set_end_frame(310)
        frame_changed, frame = self.led_wall.sequence_loader.set_current_frame(5)
        self.assertTrue(frame_changed)
        self.assertEqual(self.led_wall.sequence_loader.current_frame, 5)

    def test_frame_range_exception(self):
        """Test that FrameRangeException is raised when the frame is out of range."""
        self.led_wall.sequence_loader.set_start_frame(0)
        self.led_wall.sequence_loader.set_end_frame(10)
        with self.assertRaises(FrameRangeException):
            self.led_wall.sequence_loader.set_current_frame(20)

    def test_load_sequence(self):
        """Test that load_sequence correctly updates instance attributes."""
        self.assertEqual(self.led_wall.sequence_loader.start_frame, 0)
        self.assertEqual(self.led_wall.sequence_loader.end_frame, 295)
        self.assertEqual(self.led_wall.sequence_loader.file_name, "A012C004_220203_ROTI_balanced")

    def test_frame_iteration(self):
        """Test that the sequence can be iterated over."""
        self.led_wall.sequence_loader.set_start_frame(0)
        self.led_wall.sequence_loader.set_end_frame(10)
        frames = list(self.led_wall.sequence_loader)
        self.assertEqual(len(frames), 11)

    def test_detect_padding(self):
        """Test the detect_padding function with different amounts of padding."""
        self.assertEqual(self.led_wall.sequence_loader.detect_padding('test.1.png'), 1)
        self.assertEqual(self.led_wall.sequence_loader.detect_padding('test.01.png'), 2)
        self.assertEqual(self.led_wall.sequence_loader.detect_padding('test.001.png'), 3)
        self.assertEqual(self.led_wall.sequence_loader.detect_padding('test.0001.png'), 4)
        self.assertEqual(self.led_wall.sequence_loader.detect_padding('test.00000001.png'), 8)

        # Testing for a filename without padding
        self.assertEqual(self.led_wall.sequence_loader.detect_padding('test.png'), 0)


