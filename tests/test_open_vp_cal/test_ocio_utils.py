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
import tempfile

from open_vp_cal.core import constants
from open_vp_cal.main import run_cli
from test_utils import TestProject


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
                "Calibrated Output - AOTO_Wall2 - AOTO_Acheivable - REDWideGamutRGB - EOTF_CS",
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
