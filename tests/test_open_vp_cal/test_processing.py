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

from open_vp_cal.framework.processing import Processing
from test_utils import TestProject, skip_if_ci


class Test_Processing(TestProject):

    @skip_if_ci
    def test_swatch_analysis_generation(self):
        self.led_wall.sequence_loader.load_sequence(
            self.led_wall.input_sequence_folder)
        self.led_wall.roi = self.recalc_old_roi(self.led_wall.roi)
        processing = Processing(self.led_wall)
        processing.run_sampling()
        processing.analyse()
        processing.generate_sample_buffers()
        processing.generate_sample_swatches()

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
