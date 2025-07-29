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
import os

from open_vp_cal.core import constants
from test_utils import TestProject
from open_vp_cal.core.ocio_config import OcioConfigWriter


class TestCalibrate(TestProject):

    def setUp(self):
        super().setUp()
        self.config_writer = OcioConfigWriter(self.project_settings.output_folder)
        self.maxDiff = None

    def get_pre_calibration_ocio_config(self):
        return os.path.join(
            os.path.join(self.get_test_resources_folder(), "TestCalibrate"),
            constants.ProjectFolders.EXPORT,
            constants.ProjectFolders.CALIBRATION,
            f"Pre_Calibration_OpenVPCal_{self.project_settings.project_id}.ocio")

    def get_post_calibration_ocio_config(self):
        return os.path.join(
            os.path.join(self.get_test_resources_folder(), "TestCalibrate"),
            constants.ProjectFolders.EXPORT,
            constants.ProjectFolders.CALIBRATION,
            f"Post_Calibration_OpenVPCal_{self.project_settings.project_id}.ocio")

    def test_pre_calibration_ocio_config_generation(self):
        self.project_settings.project_id = "test_ocio"
        actual_file_path = self.config_writer.generate_pre_calibration_ocio_config(self.led_walls)
        expected_file_path = self.get_pre_calibration_ocio_config()
        self.files_are_equal(actual_file_path, expected_file_path)

    def test_post_calibration_ocio_config_generation(self):
        for led_wall in self.led_walls:
            led_wall.processing_results.calibration_results = self.get_results(self.led_wall)
            led_wall.processing_results.samples = self.get_samples(self.led_wall)
            led_wall.processing_results.reference_samples = self.get_reference_samples(self.led_wall)

        self.project_settings.project_id = "test2_ocio"
        actual_file_path = self.config_writer.generate_post_calibration_ocio_config(self.led_walls)
        expected_file_path = self.get_post_calibration_ocio_config()
        self.files_are_equal(actual_file_path, expected_file_path)
