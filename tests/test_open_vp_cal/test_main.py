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

import shutil
from pathlib import Path
from argparse import ArgumentTypeError
import json
import os
import tempfile
from json import JSONDecodeError

from open_vp_cal.core import constants, ocio_config
from open_vp_cal.main import validate_file_path, validate_folder_path, \
    validate_project_settings, generate_patterns, generate_spg_patterns
from test_open_vp_cal.test_utils import TestBase, TestProject


class TestArgparseFunctions(TestBase):
    def test_validate_file_path_valid(self):
        with tempfile.NamedTemporaryFile() as temp:
            self.assertEqual(temp.name, validate_file_path(temp.name))

    def test_validate_file_path_invalid(self):
        with self.assertRaises(ArgumentTypeError):
            validate_file_path("nonexistentfile")

    def test_validate_folder_path_valid(self):
        with tempfile.TemporaryDirectory() as tempdir:
            self.assertEqual(tempdir, validate_folder_path(tempdir))

    def test_validate_folder_path_invalid(self):
        with self.assertRaises(ArgumentTypeError):
            validate_folder_path("nonexistentfolder")

    def test_validate_project_settings_valid(self):
        # Create a temporary file
        fd, path = tempfile.mkstemp(suffix=".json")
        try:
            # Write JSON content to the file
            with open(path, 'w') as temp:
                json.dump({"key": "value"}, temp)

            # Test that the validate_project_settings function returns the correct path
            self.assertEqual(path, validate_project_settings(path))
        finally:
            # Clean up: close and remove the temporary file
            os.close(fd)
            os.remove(path)

    def test_validate_project_settings_invalid(self):
        fd, path = tempfile.mkstemp(suffix=".json")
        try:
            with open(path, 'w+') as temp:
                with self.assertRaises(JSONDecodeError):
                    validate_project_settings(path)
        finally:
            os.close(fd)
            os.remove(path)

    def test_validate_project_settings_nonjson(self):
        # Create a temporary file
        fd, path = tempfile.mkstemp(suffix=".txt")
        try:
            # Write non-JSON content to the file
            with open(path, 'w') as temp:
                temp.write("not a json file")

            # Test that JSONDecodeError is raised
            with self.assertRaises(JSONDecodeError):
                validate_project_settings(path)
        finally:
            # Clean up: close and remove the temporary file
            os.close(fd)
            os.remove(path)


class TestProjectCli(TestProject):

    def test_run_cli(self):
        expected_file = self.get_results_file(self.led_wall)

        # Override the roi so we have to run the auto detection
        self.project_settings.led_walls[0].roi = None

        results = self.run_cli(self.project_settings)

        with open(expected_file, "r", encoding="utf-8") as handle:
            expected_results = json.load(handle)

        for led_wall_name, led_wall in results.items():
            if led_wall.is_verification_wall:
                continue

            self.assertTrue(os.path.exists(led_wall.processing_results.ocio_config_output_file))
            self.assertTrue(os.path.exists(led_wall.processing_results.lut_output_file))
            self.assertTrue(os.path.exists(led_wall.processing_results.calibration_results_file))
            self.compare_data(expected_results, led_wall.processing_results.calibration_results)

    def test_run_cli_multi_wall(self):
        # Add A Second Wall
        self.project_settings.copy_led_wall(self.project_settings.led_walls[0].name, "LedWall2")

        # Override the roi so we have to run the auto detection
        self.project_settings.led_walls[0].roi = None
        self.project_settings.led_walls[1].roi = None

        # Set the new wall to the same sequence as the first wall for testing
        original_sequence = self.project_settings.led_walls[0].input_sequence_folder
        self.project_settings.led_walls[1].input_sequence_folder = original_sequence

        # Set the second wall as a reference wall for execution testing
        self.project_settings.led_walls[1].reference_wall = self.led_wall
        self.project_settings.led_walls[1].match_reference_wall = True
        self.project_settings.led_walls[1].auto_wb_source = False

        results = self.run_cli(self.project_settings)
        for led_wall_name, led_wall in results.items():
            if led_wall.is_verification_wall:
                continue

            expected_file = self.get_results_file(led_wall)
            with open(expected_file, "r", encoding="utf-8") as handle:
                expected_results = json.load(handle)

            self.assertTrue(os.path.exists(led_wall.processing_results.ocio_config_output_file))
            self.assertTrue(os.path.exists(led_wall.processing_results.lut_output_file))
            self.assertTrue(os.path.exists(led_wall.processing_results.calibration_results_file))
            self.compare_data(expected_results, led_wall.processing_results.calibration_results)


class TestProjectExternalWhite(TestProject):
    project_name = "SampleProject2_External_White_NoLens"

    def test_external_white_no_lens(self):
        results = self.run_cli(self.project_settings)
        for led_wall_name, led_wall in results.items():
            if led_wall.is_verification_wall:
                continue

            expected_file = self.get_results_file(led_wall)
            with open(expected_file, "r", encoding="utf-8") as handle:
                expected_results = json.load(handle)

            self.assertTrue(os.path.exists(led_wall.processing_results.ocio_config_output_file))
            self.assertTrue(os.path.exists(led_wall.processing_results.lut_output_file))
            self.assertTrue(os.path.exists(led_wall.processing_results.calibration_results_file))
            self.compare_data(expected_results, led_wall.processing_results.calibration_results)

    def get_sample_project_plates(self):
        result = super().get_sample_project_plates()
        return os.path.join(result, "A102_C015_1027M2_001.R3D")


class TestCLIGeneratePatterns(TestProject):
    project_name = "SampleProject2_External_White_NoLens"

    def test_cli_pattern_generation(self):
        temp_project_settings = tempfile.NamedTemporaryFile(suffix=".json", mode='w', delete=False).name
        self.project_settings.to_json(temp_project_settings)
        result = generate_patterns(
            temp_project_settings,
            self.project_settings.output_folder
        )
        os.remove(temp_project_settings)

        patches_folder = os.path.join(
            self.project_settings.output_folder, constants.ProjectFolders.EXPORT, constants.ProjectFolders.PATCHES)
        walls = os.listdir(patches_folder)
        self.assertTrue(len(walls), 1)
        images = os.listdir(
            os.path.join(
                patches_folder, walls[0],
                self.project_settings.file_format.replace(".", "")
            )
        )
        self.assertEqual(len(images), 45)
        self.assertTrue(os.path.exists(result))
        shutil.rmtree(patches_folder)
        os.remove(result)

    def test_cli_spg_pattern_generation(self):
        temp_project_settings = tempfile.NamedTemporaryFile(suffix=".json", mode='w', delete=False).name
        self.project_settings.to_json(temp_project_settings)
        generate_spg_patterns(
            temp_project_settings,
            self.project_settings.output_folder
        )
        os.remove(temp_project_settings)

        patches_folder = os.path.join(
            self.project_settings.output_folder, constants.ProjectFolders.EXPORT, constants.ProjectFolders.SPG)

        raster_folder = os.path.join(patches_folder, "RasterMaps")
        self.assertTrue(os.path.exists(raster_folder))

        walls = os.listdir(raster_folder)
        self.assertTrue(len(walls), 1)
        images = os.listdir(
            os.path.join(
                raster_folder, walls[0]
            )
        )
        self.assertEqual(len(images), 67)
        shutil.rmtree(patches_folder)

    def test_cli_force_error_log(self):
        error_log = Path(os.path.join(self.get_test_output_folder(),'filename.txt'))
        self.project_settings.led_walls[0].input_sequence_folder = ""
        with self.assertRaises(IOError):
            self.run_cli(self.project_settings, force=True, error_log=str(error_log))

        with open(str(error_log), 'r') as f:
            result = json.load(f)

        self.assertEqual(len(result["errors"]), 1)
