import json
import tempfile

from open_vp_cal.core import constants, utils
from open_vp_cal.main import run_cli
from open_vp_cal.project_settings import ProjectSettings
from test_open_vp_cal.test_utils import TestProject

import os

import open_vp_cal.core.calibrate as calibrate

import open_vp_cal.core.ocio_utils as ocio_utils
import open_vp_cal.core.ocio_config as ocio_config
from open_vp_cal.core.constants import (
    Results,
    EOTF,
    CalculationOrder,
)


class TestCalibrate(TestProject):
    def setUp(self):
        super().setUp()
        self.ocio_config_writer = ocio_config.OcioConfigWriter(self.project_settings.output_folder)

    def test_write_config_with_invEOTF(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            filename = os.path.join(tmp_dir, "openvpcal_test_invEOTF.ocio")
            results = self.get_results(self.led_wall).copy()
            results[Results.TARGET_EOTF] = EOTF.EOTF_ST2084

            self.led_wall.processing_results.calibration_results = results
            self.ocio_config_writer.generate_post_calibration_ocio_config([self.led_wall], output_file=filename)


    def test_write_config_alt_order(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            filename = os.path.join(tmp_dir, "openvpcal_test_alt_order.ocio")

            results = self.get_results(self.led_wall).copy()
            results[Results.CALCULATION_ORDER] = CalculationOrder.CO_EOTF_CS
            self.led_wall.processing_results.calibration_results = results

            self.led_wall.processing_results.calibration_results = results
            self.ocio_config_writer.generate_post_calibration_ocio_config([self.led_wall], output_file=filename)

    def test_write_config_invalid_reference_color_space(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            filename = os.path.join(tmp_dir, "openvpcal_test_alt_order.ocio")

            led_wall_new = self.project_settings.copy_led_wall(self.led_wall.name, "new_copy")
            for led_wall in self.project_settings.led_walls:
                led_wall.processing_results.calibration_results = self.get_results(self.led_wall).copy()
                led_wall.processing_results.calibration_results[Results.CALCULATION_ORDER] = CalculationOrder.CO_EOTF_CS

            led_walls = [led_wall for led_wall in self.project_settings.led_walls]
            aces = constants.ColourSpace.CS_ACES
            rgb = constants.ColourSpace.CS_SRGB
            led_walls[0].processing_results.calibration_results[constants.Results.OCIO_REFERENCE_GAMUT] = aces
            led_walls[1].processing_results.calibration_results[constants.Results.OCIO_REFERENCE_GAMUT] = rgb

            with self.assertRaises(ValueError):
                self.ocio_config_writer.generate_post_calibration_ocio_config(led_walls, output_file=filename)

    def test_write_eotf_lut(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            filename = os.path.join(tmp_dir, "openvpcal_test_pq.clf")

            results = self.get_results(self.led_wall)
            ocio_utils.write_eotf_lut_pq(
                results[Results.EOTF_LUT_R],
                results[Results.EOTF_LUT_G],
                results[Results.EOTF_LUT_B],
                filename
            )

    def test_write_alt_order(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            filename = os.path.join(tmp_dir, "openvpcal_test_alt_order.clf")

            results = self.get_results(self.led_wall)
            ocio_utils.write_eotf_lut_pq(
                results[Results.EOTF_LUT_R],
                results[Results.EOTF_LUT_G],
                results[Results.EOTF_LUT_B],
                filename
            )

    def test_lut_generation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            filename = os.path.join(tmp_dir, "openvpcal_test_alt_order.cube")
            ocio_config_path = self.get_post_calibration_ocio_config()
            result = ocio_utils.bake_3d_lut(
                "AOTO_Acheivable - ST 2084",
                "AOTO_Acheivable - ST 2084 - OpenVPCal LED",
                "OpenVPCal AOTO_Wall2 - REDWideGamutRGB",
                ocio_config_path, filename)

            self.assertTrue(os.path.exists(result))

    def test_pre_calibration_ocio_config_generation(self):
        with tempfile.TemporaryDirectory() as tmp_dir:
            config_writer = ocio_config.OcioConfigWriter(tmp_dir)
            actual_file_path = config_writer.generate_pre_calibration_ocio_config(self.led_walls)
            expected_file_path = self.get_pre_calibration_ocio_config()
            self.files_are_equal(actual_file_path, expected_file_path)

    def run_cli(self, ps):
        self.maxDiff = None
        temp_project_settings = tempfile.NamedTemporaryFile(suffix=".json", mode='w', delete=False).name
        ps.to_json(temp_project_settings)
        results = run_cli(
            temp_project_settings,
            self.get_test_output_folder(), ocio_config_path=None
        )
        os.remove(temp_project_settings)
        return results

    def test_run_cli_ocio_post_config(self):
        expected_file = self.get_post_calibration_ocio_config()
        ps = self.project_settings
        # Override the roi so we have to run the auto detection
        ps.led_walls[0].roi = None

        # We set the sequence for the test project
        ps.led_walls[0].input_sequence_folder = self.get_sample_project_plates()
        results = self.run_cli(ps)

        for led_wall_name, led_wall in results.items():
            if led_wall.is_verification_wall:
                continue
            self.files_are_equal(expected_file, led_wall.processing_results.ocio_config_output_file)
