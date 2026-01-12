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

Unit tests for ProjectSettingsModel UI interactions.
"""
import json
import os
import tempfile
import unittest

from PySide6.QtCore import QCoreApplication

from open_vp_cal.widgets.project_settings_widget import ProjectSettingsModel
from open_vp_cal.widgets.stage_widget import LedWallTimelineLoader
from open_vp_cal.led_wall_settings import LedWallSettings
from open_vp_cal.core import constants

# QCoreApplication instance needed for Qt signal tests (no display required)
app = QCoreApplication.instance() or QCoreApplication([])


class TestProjectSettingsModel(unittest.TestCase):
    """Tests for ProjectSettingsModel UI interactions."""

    def setUp(self):
        """Set up test fixtures."""
        self.model = ProjectSettingsModel(led_wall_class=LedWallTimelineLoader)

    def tearDown(self):
        """Clean up any walls after each test."""
        for wall in list(self.model.led_walls):
            self.model.remove_led_wall(wall.name)

    def test_add_led_wall(self):
        """Test adding an LED wall emits the correct signal."""
        signal_received = []
        self.model.led_wall_added.connect(lambda wall: signal_received.append(wall))

        wall = self.model.add_led_wall("TestWall")

        self.assertIsNotNone(wall)
        self.assertEqual(wall.name, "TestWall")
        self.assertEqual(len(self.model.led_walls), 1)
        self.assertEqual(len(signal_received), 1)
        self.assertEqual(signal_received[0].name, "TestWall")
        self.assertIsInstance(wall, LedWallTimelineLoader)

    def test_add_led_wall_duplicate_name(self):
        """Test adding a duplicate wall name emits error signal."""
        error_received = []
        self.model.error_occurred.connect(lambda msg: error_received.append(msg))

        self.model.add_led_wall("TestWall")
        result = self.model.add_led_wall("TestWall")

        self.assertIsNone(result)
        self.assertEqual(len(error_received), 1)
        self.assertIn("already exists", error_received[0])

    def test_remove_led_wall(self):
        """Test removing an LED wall emits the correct signal."""
        signal_received = []
        self.model.led_wall_removed.connect(lambda name: signal_received.append(name))

        self.model.add_led_wall("TestWall")
        self.assertEqual(len(self.model.led_walls), 1)

        self.model.remove_led_wall("TestWall")

        self.assertEqual(len(self.model.led_walls), 0)
        self.assertEqual(len(signal_received), 1)
        self.assertEqual(signal_received[0], "TestWall")

    def test_copy_led_wall(self):
        """Test copying an LED wall creates a new wall with different name."""
        self.model.add_led_wall("OriginalWall")
        original = self.model.get_led_wall("OriginalWall")
        original.target_max_lum_nits = 500

        copied = self.model.copy_led_wall("OriginalWall", "CopiedWall")

        self.assertIsNotNone(copied)
        self.assertEqual(copied.name, "CopiedWall")
        self.assertEqual(len(self.model.led_walls), 2)
        self.assertEqual(copied.target_max_lum_nits, 500)

    def test_copy_led_wall_duplicate_name(self):
        """Test copying a wall with an existing name emits error signal."""
        error_received = []
        self.model.error_occurred.connect(lambda msg: error_received.append(msg))

        self.model.add_led_wall("Wall1")
        self.model.add_led_wall("Wall2")

        result = self.model.copy_led_wall("Wall1", "Wall2")

        self.assertIsNone(result)
        self.assertEqual(len(error_received), 1)
        self.assertIn("already exists", error_received[0])

    def test_add_verification_wall(self):
        """Test adding a verification wall links it to the parent wall."""
        self.model.add_led_wall("MainWall")

        verify_wall = self.model.add_verification_wall("MainWall")

        self.assertIsNotNone(verify_wall)
        self.assertEqual(verify_wall.name, "Verify_MainWall")
        self.assertTrue(verify_wall.is_verification_wall)
        self.assertEqual(verify_wall.verification_wall, "MainWall")

        main_wall = self.model.get_led_wall("MainWall")
        self.assertEqual(main_wall.verification_wall, "Verify_MainWall")

    def test_add_verification_wall_to_verification_wall(self):
        """Test that adding a verification wall to a verification wall fails."""
        error_received = []
        self.model.error_occurred.connect(lambda msg: error_received.append(msg))

        self.model.add_led_wall("MainWall")
        self.model.add_verification_wall("MainWall")

        result = self.model.add_verification_wall("Verify_MainWall")

        self.assertIsNone(result)
        self.assertEqual(len(error_received), 1)

    def test_set_current_wall(self):
        """Test setting current wall emits data_changed signals."""
        data_changed_received = []
        self.model.data_changed.connect(lambda key, val: data_changed_received.append((key, val)))

        self.model.add_led_wall("Wall1")
        self.model.add_led_wall("Wall2")
        data_changed_received.clear()

        self.model.set_current_wall("Wall2")

        self.assertEqual(self.model.current_wall.name, "Wall2")
        self.assertGreater(len(data_changed_received), 0)

    def test_set_current_wall_by_object(self):
        """Test setting current wall by LedWallSettings object."""
        self.model.add_led_wall("Wall1")
        wall2 = self.model.add_led_wall("Wall2")

        self.model.set_current_wall(wall2)

        self.assertEqual(self.model.current_wall.name, "Wall2")

    def test_set_data_project_property(self):
        """Test set_data updates project property and emits signal."""
        data_changed_received = []
        self.model.data_changed.connect(lambda key, val: data_changed_received.append((key, val)))

        self.model.set_data(constants.ProjectSettingsKeys.OUTPUT_FOLDER, "/new/output/path")

        self.assertEqual(self.model.output_folder, "/new/output/path")
        self.assertIn((constants.ProjectSettingsKeys.OUTPUT_FOLDER, "/new/output/path"), data_changed_received)

    def test_set_data_wall_property(self):
        """Test set_data updates wall property and emits signal."""
        self.model.add_led_wall("TestWall")
        data_changed_received = []
        self.model.data_changed.connect(lambda key, val: data_changed_received.append((key, val)))

        self.model.set_data(constants.LedWallSettingsKeys.TARGET_MAX_LUM_NITS, 800)

        self.assertEqual(self.model.current_wall.target_max_lum_nits, 800)
        self.assertIn((constants.LedWallSettingsKeys.TARGET_MAX_LUM_NITS, 800), data_changed_received)

    def test_clear_project_settings(self):
        """Test clearing project settings restores defaults."""
        self.model.output_folder = "/custom/path"
        self.model.frames_per_patch = 5

        self.model.clear_project_settings()

        self.assertNotEqual(self.model.output_folder, "/custom/path")
        self.assertEqual(self.model.frames_per_patch, 1)

    def test_reset_led_wall(self):
        """Test resetting an LED wall restores defaults but preserves verification link."""
        self.model.add_led_wall("MainWall")
        self.model.add_verification_wall("MainWall")

        main_wall = self.model.get_led_wall("MainWall")
        main_wall.target_max_lum_nits = 500
        main_wall.primaries_saturation = 0.5

        self.model.reset_led_wall("MainWall")

        main_wall = self.model.get_led_wall("MainWall")
        self.assertEqual(main_wall.target_max_lum_nits, 1000)
        self.assertEqual(main_wall.primaries_saturation, 0.7)
        self.assertEqual(main_wall.verification_wall, "Verify_MainWall")

    def test_save_and_load_json(self):
        """Test saving and loading project settings preserves data."""
        self.model.add_led_wall("Wall1")
        self.model.add_led_wall("Wall2")
        self.model.output_folder = "/test/output"

        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json_path = f.name

        try:
            self.model.to_json(json_path)

            with open(json_path, 'r') as f:
                data = json.load(f)

            self.assertIn(constants.OpenVPCalSettingsKeys.VERSION, data)
            self.assertIn(constants.OpenVPCalSettingsKeys.PROJECT_SETTINGS, data)
            self.assertEqual(len(data[constants.OpenVPCalSettingsKeys.PROJECT_SETTINGS]['led_walls']), 2)
        finally:
            os.unlink(json_path)

    def test_get_led_wall(self):
        """Test getting a wall by name."""
        self.model.add_led_wall("TestWall")

        wall = self.model.get_led_wall("TestWall")

        self.assertIsNotNone(wall)
        self.assertEqual(wall.name, "TestWall")

    def test_get_led_wall_not_found(self):
        """Test getting a non-existent wall raises ValueError."""
        with self.assertRaises(ValueError):
            self.model.get_led_wall("NonExistentWall")

    def test_add_custom_primary(self):
        """Test adding a custom primary."""
        primaries = [[0.7, 0.3], [0.2, 0.7], [0.1, 0.1], [0.3127, 0.329]]

        self.model.add_custom_primary("CustomGamut", primaries)

        self.assertIn("CustomGamut", self.model.project_custom_primaries)
        self.assertEqual(self.model.project_custom_primaries["CustomGamut"], primaries)

    def test_add_custom_primary_duplicate(self):
        """Test adding a duplicate custom primary raises ValueError."""
        primaries = [[0.7, 0.3], [0.2, 0.7], [0.1, 0.1], [0.3127, 0.329]]
        self.model.add_custom_primary("CustomGamut", primaries)

        with self.assertRaises(ValueError):
            self.model.add_custom_primary("CustomGamut", primaries)


class TestPixMapFrameGamut(unittest.TestCase):
    """Tests for PixMapFrame using led_wall_settings for gamut access."""

    def test_pixmap_frame_uses_led_wall_input_plate_gamut(self):
        """Test that PixMapFrame accesses input_plate_gamut from led_wall_settings."""
        from open_vp_cal.widgets.timeline_widget import PixMapFrame

        # Create a wall with specific input_plate_gamut
        model = ProjectSettingsModel(led_wall_class=LedWallTimelineLoader)
        wall = model.add_led_wall("TestWall")
        wall.input_plate_gamut = constants.ColourSpace.CS_ACES

        # Create a PixMapFrame with the wall
        frame = PixMapFrame(wall)

        # Verify the frame has access to the led_wall_settings
        self.assertEqual(frame._led_wall_settings, wall)
        self.assertEqual(frame._led_wall_settings.input_plate_gamut, constants.ColourSpace.CS_ACES)


if __name__ == '__main__':
    unittest.main()
