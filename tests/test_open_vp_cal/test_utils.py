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

import json
import math
import os
import platform
import shutil
import tempfile
import unittest

import open_vp_cal.imaging.imaging_utils
from open_vp_cal.core import constants
from open_vp_cal.imaging import imaging_utils
from open_vp_cal.project_settings import ProjectSettings
from open_vp_cal.main import run_cli

import OpenImageIO as Oiio


class TestUtils(unittest.TestCase):
    def setUp(self):
        super(TestUtils, self).setUp()
        os.environ[constants.OPEN_VP_CAL_UNIT_TESTING] = "1"

        test_output_folder = self.get_test_output_folder()
        if os.path.exists(test_output_folder):
            shutil.rmtree(test_output_folder)

        os.makedirs(test_output_folder)

    def tearDown(self):
        super(TestUtils, self).tearDown()
        del os.environ[constants.OPEN_VP_CAL_UNIT_TESTING]

    @classmethod
    def get_folder_for_this_file(cls):
        return os.path.dirname(__file__)

    @classmethod
    def get_test_resources_folder(cls):
        return os.path.join(
            cls.get_folder_for_this_file(),
            "resources",
        )

    @classmethod
    def get_test_output_folder(cls):
        return os.path.join(
            cls.get_folder_for_this_file(),
            "output",
        )

    def compare_image_files(self, expected_image_file, actual_image_file, ext):
        expected_image = Oiio.ImageBuf(expected_image_file)
        image_buffer = Oiio.ImageBuf(actual_image_file)
        self.compare_image_buffers(expected_image, image_buffer, ext)

    def compare_image_buffers(self, expected_image, image_buffer, ext):
        # Compare The Format
        expected_spec = expected_image.spec()
        image_buffer_spec = image_buffer.spec()
        self.assertEqual(expected_spec.format, image_buffer_spec.format)

        # Compare The Bits Per Sample
        expected_bps = expected_spec.get_int_attribute(constants.OIIO_BITS_PER_SAMPLE, defaultval=0)
        actual_bps = image_buffer_spec.get_int_attribute(constants.OIIO_BITS_PER_SAMPLE, defaultval=0)
        self.assertEqual(expected_bps, actual_bps)

        comp_results = Oiio.ImageBufAlgo.compare(expected_image, image_buffer, 1.0e-3, 1.0e-5)
        num_allowed_failed_pixels = 0
        if comp_results.nfail > num_allowed_failed_pixels:
            file_name = "_".join([self.__class__.__name__, self._testMethodName])
            diff = Oiio.ImageBufAlgo.absdiff(expected_image, image_buffer)

            self.write_test_image_result(diff, file_name.replace("test", "result_diff"), ext, expected_bps)
            self.write_test_image_result(image_buffer, file_name.replace("test", "result"), ext, expected_bps)
            self.fail(file_name + ": Images did not match")

    def files_are_equal(self, file1_path, file2_path):
        with open(file1_path, 'r', encoding="utf8") as file1, open(file2_path, 'r', encoding="utf8") as file2:
            if file1_path.endswith(".ocio") and file2_path.endswith(".ocio"):
                if platform.system() != "Darwin":
                    with self.subTest("OCIO Config Compare Only Works On Osx, Needs More Than Text File Compare"):
                        self.assertTrue(True)
                else:
                    self.assertEqual(file1.readlines(), file2.readlines(), msg=f"Files {file1_path} and {file2_path} are not equal.")
            else:
                self.assertEqual(file1.readlines(), file2.readlines(),
                                 msg=f"Files {file1_path} and {file2_path} are not equal.")


    @classmethod
    def write_test_image_result(cls, image, image_name, ext, bit_depth):
        if not bit_depth:
            bit_depth = "half"
        output_folder = cls.get_test_output_folder()
        file_name = os.path.join(output_folder, image_name + "." + ext)
        open_vp_cal.imaging.imaging_utils.write_image(image, file_name, bit_depth)
        return file_name

    def recalc_old_roi(self, roi):
        """
        Convert an ROI given as [x, y, width, height] as described in version 1.x
        and convert it to a list of four corners for 2.x

        Args:
            roi (list): A list of four numbers [x, y, width, height]

        Returns:
            list: A list of four tuples representing the corners in the following order:
                  top left, top right, bottom right, bottom left.
        """
        if not roi:
            return []
        left, right, top, bottom = roi
        top_left = [left, top]
        top_right = [right, top]
        bottom_right = [right, bottom]
        bottom_left = [left, bottom]

        corners =  [top_left, top_right, bottom_right, bottom_left]
        return corners

    def pre_process_vp_cal_1x(self, project_settings, output_folder, input_colour_space="ACES2065-1"):
        """ For all unit tests which where created using v1.x we need to double the
            overall exposure of the plates to account for the fact that in 2.x we force
            the camera to be exposed a full stop up

        """
        project_settings.content_max_lum = constants.PQ.PQ_MAX_NITS

        temp_folders = []
        for led_wall in project_settings.led_walls:
            led_wall.roi = self.recalc_old_roi(led_wall.roi)
            input = led_wall.input_sequence_folder

            # create temp folder
            temp_folder = os.path.join(output_folder,
                                       f"{led_wall.name}_temp")
            temp_folders.append(temp_folder)
            if not os.path.exists(temp_folder):
                os.makedirs(temp_folder)

            for _file in os.listdir(input):
                file_path = os.path.join(input, _file)
                output_file = os.path.join(temp_folder, _file)
                buffer = imaging_utils.load_image(file_path)
                np_array = imaging_utils.image_buf_to_np_array(buffer)

                if input_colour_space != "ACES2065-1":
                    imaging_utils.apply_color_converstion_to_np_array(np_array, input_colour_space, "ACES2065-1")

                # Increase the exposure by 1 stop
                np_array = np_array * 2.0

                if input_colour_space != "ACES2065-1":
                    imaging_utils.apply_color_converstion_to_np_array(np_array, "ACES2065-1", input_colour_space)

                new_buffer = imaging_utils.img_buf_from_numpy_array(np_array)
                # Save the image to the temp folder
                imaging_utils.write_image(new_buffer, output_file, "float")
            led_wall.input_sequence_folder = temp_folder
        return temp_folders

    def cleanup_pre_process_vp1(self, temp_folders):
        for temp_folder in temp_folders:
            if os.path.exists(temp_folder):
                shutil.rmtree(temp_folder)


class TestBase(TestUtils):
    def setUp(self) -> None:
        super(TestBase, self).setUp()
        self.project_settings = ProjectSettings.from_json(self.get_test_project_settings())
        self.project_settings.output_folder = self.get_test_output_folder()
        self.led_walls = self.project_settings.led_walls
        self.led_wall = self.project_settings.led_walls[0]
        self.led_wall.input_sequence_folder = self.get_test_balanced_sequence_folder()

    @classmethod
    def get_test_sequence_folder(cls):
        return os.path.join(
            cls.get_test_resources_folder(),
            "TEST_EXR_OPENVPCAL_UNBALANCED_WHITE"
        )

    @classmethod
    def get_test_balanced_sequence_folder(cls):
        return os.path.join(
            cls.get_test_resources_folder(),
            "TEST_EXR_OPENVPCAL_balanced"
        )

    @classmethod
    def get_test_project_settings(cls):
        return os.path.join(cls.get_test_resources_folder(), "settings.json")


class TestProcessorBase(TestBase):
    def setUp(self):
        super(TestProcessorBase, self).setUp()
        self.led_wall.sequence_loader.load_sequence(self.led_wall.input_sequence_folder)


class TestProject(TestUtils):
    project_name = "SampleProject1_PreTest"

    def setUp(self):
        super(TestProject, self).setUp()
        self.project_settings = ProjectSettings.from_json(self.get_sample_project_settings())
        self.project_settings.output_folder = self.get_output_folder()
        if os.path.exists(self.project_settings.output_folder):
            shutil.rmtree(self.project_settings.output_folder)

        os.makedirs(self.project_settings.output_folder)

        self.led_walls = self.project_settings.led_walls
        self.led_wall = self.project_settings.led_walls[0]
        self.led_wall.input_sequence_folder = self.get_sample_project_plates()

    def run_cli_with_v1_fixes(self, input_colour_space="ACES2065-1"):
        temp_folders = self.pre_process_vp_cal_1x(
            self.project_settings, self.get_output_folder(), input_colour_space=input_colour_space
        )
        try:
            results = self.run_cli(self.project_settings)
            self.cleanup_pre_process_vp1(temp_folders)
            return results
        except Exception as e:
            self.cleanup_pre_process_vp1(temp_folders)
            raise e

    def run_cli(self, project_settings, force=False, error_log=None, export_analysis_swatches=False):
        self.maxDiff = None

        temp_project_settings = tempfile.NamedTemporaryFile(suffix=".json", mode='w', delete=False).name
        project_settings.to_json(temp_project_settings)
        processed_led_walls = run_cli(
            temp_project_settings,
            project_settings.output_folder, ocio_config_path=None,
            force=force,
            error_log=error_log,
            export_analysis_swatches=export_analysis_swatches
        )
        os.remove(temp_project_settings)
        return processed_led_walls

    def get_results_file(self, led_wall):
        file_name = f"{led_wall.name}_calibration_results.json"
        results_file = os.path.join(
            self.get_sample_project_folder(),
            constants.ProjectFolders.EXPORT,
            constants.ProjectFolders.RESULTS,
            file_name)
        return results_file

    def get_results(self, led_wall):
        results_file = self.get_results_file(led_wall)
        with open(results_file, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def get_samples(self, led_wall):
        file_name = f"{led_wall.name}_samples.json"
        results_file = os.path.join(
            self.get_sample_project_folder(),
            constants.ProjectFolders.EXPORT,
            constants.ProjectFolders.RESULTS,
            file_name)
        with open(results_file, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def get_reference_samples(self, led_wall):
        file_name = f"{led_wall.name}_reference_samples.json"
        results_file = os.path.join(
            self.get_sample_project_folder(),
            constants.ProjectFolders.EXPORT,
            constants.ProjectFolders.RESULTS,
            file_name)
        with open(results_file, "r", encoding="utf-8") as handle:
            return json.load(handle)

    def get_sample_project_folder(self):
        return os.path.join(self.get_test_resources_folder(), self.project_name)

    def get_sample_project_settings(self):
        return os.path.join(self.get_sample_project_folder(), "project_settings.json")

    def get_sample_plates(self):
        return os.path.join(self.get_test_resources_folder(), "Plates")

    def get_sample_project_plates(self):
        return os.path.join(self.get_test_resources_folder(), self.project_name, "Plates")

    def get_output_folder(self):
        return os.path.join(self.get_test_output_folder(), self.project_name)

    def get_post_calibration_ocio_config(self):
        return os.path.join(
            self.get_sample_project_folder(),
            constants.ProjectFolders.EXPORT,
            constants.ProjectFolders.CALIBRATION,
            f"Post_Calibration_OpenVPCal_{self.project_settings.project_id}.ocio")

    def get_pre_calibration_ocio_config(self):
        return os.path.join(
            self.get_sample_project_folder(),
            constants.ProjectFolders.EXPORT,
            constants.ProjectFolders.CALIBRATION,
            f"Pre_Calibration_OpenVPCal_{self.project_settings.project_id}.ocio")

    def are_close(self, a, b, rel_tol=1e-8):
        return math.isclose(a, b, rel_tol=rel_tol)

    def compare_lut_cubes(self, file1, file2, tolerance=1e-4):
        """
        Compares two files to ensure they match. Raises an assertion error if they don't.

        Args:
        - file1: Path to the first file.
        - file2: Path to the second file.
        - tolerance: Float tolerance for comparing float values.
        """
        self.assertEqual(os.path.basename(file1), os.path.basename(file2))
        with open(file1, 'r') as f1, open(file2, 'r') as f2:
            # Compare the first line (header)
            self.assertEqual(f1.readline(), f2.readline(), "Header lines do not match.")

            # Compare the remaining lines
            for line_num, (line1, line2) in enumerate(zip(f1, f2), start=1):
                values1 = [float(val) for val in line1.split()]
                values2 = [float(val) for val in line2.split()]

                self.assertEqual(
                    len(values1), 3, f"Line {line_num} in file1 does not have 3 values.")
                self.assertEqual(
                    len(values2), 3, f"Line {line_num} in file2 does not have 3 values.")

                for val1, val2 in zip(values1, values2):
                    self.assertAlmostEqual(
                        val1, val2, delta=tolerance,
                        msg=f"Line {line_num} values do not match within tolerance.")

    def compare_data(self,
                     expected,
                     actual,
                     rel_tol=0,
                     abs_tol=2e-3,
                     path="root"):
        """
        Recursively compare two data structures (dicts, lists/tuples, scalars).
        - Floats are compared with math.isclose(rel_tol=rel_tol, abs_tol=abs_tol).
        - Other types use exact equality.
        - `path` indicates location within the structure for clear error messages.
        """
        # 1) Dictionaries
        if isinstance(expected, dict):
            self.assertIsInstance(actual, dict,
                                  f"{path}: expected dict, got {type(actual)}")
            for key, exp_val in expected.items():
                if key == "DELTA_E_MACBETH": # Delta_E is a totally different scale so needs its own abs total
                    abs_tol = 0.2
                self.assertIn(key, actual, f"{path}: missing key {key!r}")
                self.compare_data(exp_val,
                                  actual[key],
                                  rel_tol=rel_tol,
                                  abs_tol=abs_tol,
                                  path=f"{path}.{key}")
            return

        # 2) Lists or tuples
        if isinstance(expected, (list, tuple)):
            self.assertIsInstance(actual, type(expected),
                                  f"{path}: expected {type(expected).__name__}, got {type(actual).__name__}")
            self.assertEqual(len(expected), len(actual),
                             f"{path}: length mismatch, expected {len(expected)} got {len(actual)}")
            for idx, (exp_item, act_item) in enumerate(zip(expected, actual)):
                self.compare_data(exp_item,
                                  act_item,
                                  rel_tol=rel_tol,
                                  abs_tol=abs_tol,
                                  path=f"{path}[{idx}]")
            return

        # 3) Floats
        if isinstance(expected, float):
            try:
                act_float = float(actual)
            except Exception:
                self.fail(f"{path}: expected float {expected!r}, but actual is not convertible to float: {actual!r}")
            self.assertTrue(
                math.isclose(expected,
                             act_float,
                             rel_tol=rel_tol,
                             abs_tol=abs_tol),
                f"{path}: float mismatch, expected {expected!r}, got {act_float!r} (rel_tol={rel_tol}, abs_tol={abs_tol})"
            )
            return

        # 4) Everything else (int, str, bool, None, etc.)
        self.assertEqual(expected, actual,
                         f"{path}: value mismatch, expected {expected!r}, got {actual!r}")


def skip_if_ci(reason="Skipped in CI"):
    """
    Skip a test when running under CI (i.e. CI=true in the environment).
    """
    return unittest.skipIf(os.getenv("CI") == "true", reason)
