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
import time

from test_utils import TestProcessorBase, skip_if_ci

from open_vp_cal.framework.identify_separation import IdentifySeparation
from open_vp_cal.framework.processing import Processing


class TestIdentifySeparation(TestProcessorBase):
    def test_identify_separation(self):
        self.led_wall.roi = self.recalc_old_roi(self.led_wall.roi)
        identify_sep = IdentifySeparation(self.led_wall)
        results = identify_sep.run()
        self.assertEqual(results.first_red_frame.frame_num, 72)
        self.assertEqual(results.first_green_frame.frame_num, 77)
        self.assertEqual(results.first_blue_frame.frame_num, 82)
        self.assertEqual(results.first_grey_frame.frame_num, 87)
        self.assertEqual(results.second_red_frame.frame_num, 92)
        self.assertEqual(results.separation, 5)

    def test_set_separation_results(self):
        """Test that preset separation results can be set directly."""
        # Set preset separation results
        self.led_wall.set_separation_results(first_red_frame_num=72, separation=5)

        # Verify results are set correctly
        results = self.led_wall.separation_results
        self.assertTrue(results.is_valid)
        self.assertEqual(results.first_red_frame.frame_num, 72)
        self.assertEqual(results.first_green_frame.frame_num, 77)
        self.assertEqual(results.first_blue_frame.frame_num, 82)
        self.assertEqual(results.first_grey_frame.frame_num, 87)
        self.assertEqual(results.second_red_frame.frame_num, 92)
        self.assertEqual(results.separation, 5)

    def test_set_separation_results_skips_detection(self):
        """Test that preset separation results skip automatic detection."""
        self.led_wall.roi = self.recalc_old_roi(self.led_wall.roi)

        # Set preset separation results before running identify_separation
        self.led_wall.set_separation_results(first_red_frame_num=72, separation=5)

        # Running identify_separation should return the preset results
        # Note: IdentifySeparation.run() always runs _find_frame_peaks(),
        # but Processing.identify_separation() checks if results are valid first
        processing = Processing(self.led_wall)
        results = processing.identify_separation()

        # Should return the preset results
        self.assertTrue(results.is_valid)
        self.assertEqual(results.first_red_frame.frame_num, 72)
        self.assertEqual(results.separation, 5)

    @skip_if_ci()
    def test_preset_separation_performance_with_auto_roi(self):
        """
        Integration test comparing performance of auto separation detection vs preset.

        This test demonstrates the time savings when using preset separation results
        with auto ROI detection. The preset approach should be significantly faster
        because it skips the slow frame peak detection.
        """
        # --- Run 1: Without preset (full auto: separation detection + auto ROI) ---
        # Clear ROI to force auto-detection
        self.led_wall.roi = []
        self.led_wall.separation_results = None

        start_time_auto = time.time()

        # run_auto_detect sets ROI to full image, runs separation detection, then auto ROI
        separation_results_auto, roi_results_auto = Processing.run_auto_detect(self.led_wall)

        time_auto = time.time() - start_time_auto
        roi_auto = self.led_wall.roi

        # Verify auto detection worked
        self.assertTrue(separation_results_auto.is_valid)
        self.assertIsNotNone(roi_results_auto)
        self.assertTrue(roi_results_auto.is_valid)

        # Store the detected values for preset
        detected_first_red = separation_results_auto.first_red_frame.frame_num
        detected_separation = separation_results_auto.separation

        # --- Run 2: With preset (preset separation + auto ROI) ---
        # Reset the sequence loader and clear results
        self.led_wall.sequence_loader.reset()
        self.led_wall.sequence_loader.load_sequence(self.led_wall.input_sequence_folder)
        self.led_wall.roi = []
        self.led_wall.separation_results = None

        start_time_preset = time.time()

        # Set preset separation results BEFORE running auto detect
        # This should skip the slow _find_frame_peaks() step
        self.led_wall.set_separation_results(
            first_red_frame_num=detected_first_red,
            separation=detected_separation
        )

        # Now run auto detect - should skip separation detection since results are already set
        separation_results_preset, roi_results_preset = Processing.run_auto_detect(self.led_wall)

        time_preset = time.time() - start_time_preset
        roi_preset = self.led_wall.roi

        # Verify preset approach worked
        self.assertTrue(separation_results_preset.is_valid)
        self.assertIsNotNone(roi_results_preset)
        self.assertTrue(roi_results_preset.is_valid)

        # Verify both approaches produce the same ROI
        self.assertEqual(roi_auto, roi_preset)

        # Verify preset is faster (should skip _find_frame_peaks)
        time_saved = time_auto - time_preset
        speedup_percent = (time_saved / time_auto) * 100 if time_auto > 0 else 0

        print("\n--- Preset Separation Performance Test ---")
        print(f"Auto detection time:   {time_auto:.3f}s")
        print(f"Preset detection time: {time_preset:.3f}s")
        print(f"Time saved:            {time_saved:.3f}s ({speedup_percent:.1f}%)")
        print(f"Detected separation:   first_red={detected_first_red}, separation={detected_separation}")
        print(f"ROI detected:          {roi_preset}")

        # Assert that preset is faster (allow some margin for test variability)
        self.assertGreater(
            time_auto, time_preset,
            f"Preset approach ({time_preset:.3f}s) should be faster than auto ({time_auto:.3f}s)"
        )

