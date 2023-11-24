import json
import math
import os
import shutil
import tempfile
import unittest

import open_vp_cal.imaging.imaging_utils
from open_vp_cal.core import constants
from open_vp_cal.project_settings import ProjectSettings
from open_vp_cal.main import run_cli

import OpenImageIO as Oiio


class TestUtils(unittest.TestCase):
    def setUp(self):
        super(TestUtils, self).setUp()
        os.environ[constants.OPEN_VP_CAL_UNIT_TESTING] = "1"

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

        comp_results = Oiio.ImageBufAlgo.compare(expected_image, image_buffer, 1.0e-6, 1.0e-6)
        if comp_results.nfail > 0:
            file_name = "_".join([self.__class__.__name__, self._testMethodName])
            diff = Oiio.ImageBufAlgo.absdiff(expected_image, image_buffer)

            self.write_test_image_result(diff, file_name.replace("test", "result_diff"), ext, expected_bps)
            self.write_test_image_result(image_buffer, file_name.replace("test", "result"), ext, expected_bps)
            self.fail(file_name + ": Images did not match")

    def files_are_equal(self, file1_path, file2_path):
        with open(file1_path, 'r', encoding="utf8") as file1, open(file2_path, 'r', encoding="utf8") as file2:
            self.assertEqual(file1.readlines(), file2.readlines())


    @classmethod
    def write_test_image_result(cls, image, image_name, ext, bit_depth):
        if not bit_depth:
            bit_depth = "half"
        output_folder = cls.get_test_output_folder()
        file_name = os.path.join(output_folder, image_name + "." + ext)
        open_vp_cal.imaging.imaging_utils.write_image(image, file_name, bit_depth)
        return file_name


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

    def run_cli(self, project_settings):
        self.maxDiff = None

        temp_project_settings = tempfile.NamedTemporaryFile(suffix=".json", mode='w', delete=False).name
        project_settings.to_json(temp_project_settings)
        results = run_cli(
            temp_project_settings,
            project_settings.output_folder, ocio_config_path=None
        )
        os.remove(temp_project_settings)
        return results

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
            "Post_Calibration_OpenVPCal.ocio")

    def get_pre_calibration_ocio_config(self):
        return os.path.join(
            self.get_sample_project_folder(),
            constants.ProjectFolders.EXPORT,
            constants.ProjectFolders.CALIBRATION,
            "Pre_Calibration_OpenVPCal.ocio")

    def are_close(self, a, b, rel_tol=1e-8):
        return math.isclose(a, b, rel_tol=rel_tol)

    def compare_data(self, expected, actual):
        for key, expected_value in expected.items():
            if key not in actual:
                return False, f"Key {key} not found in actual data"
            if isinstance(expected_value, list):
                for exp_item, act_item in zip(expected_value, actual[key]):
                    if isinstance(exp_item, list):
                        for exp_subitem, act_subitem in zip(exp_item, act_item):
                            if isinstance(exp_subitem, float):
                                if not self.are_close(exp_subitem, act_subitem):
                                    return False, f"Mismatch in {key}: expected {exp_subitem}, got {act_subitem}"
                            elif exp_subitem != act_subitem:
                                return False, f"Mismatch in {key}: expected {exp_subitem}, got {act_subitem}"
                    elif isinstance(exp_item, float):
                        if not self.are_close(exp_item, act_item):
                            return False, f"Mismatch in {key}: expected {exp_item}, got {act_item}"
                    elif exp_item != act_item:
                        return False, f"Mismatch in {key}: expected {exp_item}, got {act_item}"
            elif isinstance(expected_value, float):
                if not self.are_close(expected_value, actual[key]):
                    return False, f"Mismatch in {key}: expected {expected_value}, got {actual[key]}"
            elif expected_value != actual[key]:
                return False, f"Mismatch in {key}: expected {expected_value}, got {actual[key]}"
        return True, "Success"
