from open_vp_cal.core.structures import ProcessingResults
from test_utils import TestProject
from open_vp_cal.core.ocio_config import OcioConfigWriter


class TestCalibrate(TestProject):

    def setUp(self):
        super().setUp()
        self.config_writer = OcioConfigWriter(self.project_settings.output_folder)

    def test_pre_calibration_ocio_config_generation(self):
        actual_file_path = self.config_writer.generate_pre_calibration_ocio_config(self.led_walls)
        expected_file_path = self.get_pre_calibration_ocio_config()
        self.files_are_equal(actual_file_path, expected_file_path)

    def test_post_calibration_ocio_config_generation(self):
        for led_wall in self.led_walls:
            led_wall.processing_results.calibration_results = self.get_results(self.led_wall)
            led_wall.processing_results.samples = self.get_samples(self.led_wall)
            led_wall.processing_results.reference_samples = self.get_reference_samples(self.led_wall)

        actual_file_path = self.config_writer.generate_post_calibration_ocio_config(self.led_walls)
        expected_file_path = self.get_post_calibration_ocio_config()
        self.files_are_equal(actual_file_path, expected_file_path)
