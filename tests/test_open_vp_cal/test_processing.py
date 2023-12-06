from open_vp_cal.framework.processing import Processing
from test_open_vp_cal.test_utils import TestProject


class Test_Processing(TestProject):
    def test_swatch_analysis_generation(self):
        self.led_wall.sequence_loader.load_sequence(
            self.led_wall.input_sequence_folder, file_type=self.project_settings.file_format)
        processing = Processing(self.led_wall)
        processing.run_sampling()

        self.assertNotEqual(self.led_wall.processing_results, None)
        self.assertNotEqual(self.led_wall.processing_results.sample_buffers, [])
        self.assertNotEqual(self.led_wall.processing_results.sample_reference_buffers, [])
        self.assertEqual(
            len(self.led_wall.processing_results.sample_buffers), len(self.led_wall.processing_results.sample_reference_buffers)
        )

        sample_bufs_stitched, sample_reference_bufs_stitched = processing.generate_sample_swatches(
        )

        self.assertNotEqual(sample_bufs_stitched, None)
        self.assertNotEqual(sample_reference_bufs_stitched, None)
