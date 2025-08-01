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

The Module has classes dedicated to identifying the region of interest within the image sequence
which we want to extract to analyze.
"""
from typing import List, Tuple

import numpy as np
from open_vp_cal.led_wall_settings import LedWallSettings

from open_vp_cal.imaging import imaging_utils
from open_vp_cal.framework.sample_patch import BaseSamplePatch
from open_vp_cal.framework.identify_separation import SeparationResults
from open_vp_cal.core import constants


class AutoROIResults:
    """
    Class to store the results of the ROI detection.
    The ROI is returned as a list of four (x, y) tuples in the order:
    red (top-left), green (top-right), white (bottom-right), blue (bottom-left).
    """
    def __init__(self):
        self.red_pixel: Tuple[int, int] = None
        self.green_pixel: Tuple[int, int] = None
        self.blue_pixel: Tuple[int, int] = None
        self.white_pixel: Tuple[int, int] = None

    @property
    def is_valid(self) -> bool:
        """
        Validates that all four color pixels are detected and follow the correct spatial layout:
          - Red (top-left) is above the bottom points and to the left of green.
          - Green (top-right) is above the bottom points and to the right of red.
          - White (bottom-right) is below the top points and to the left of blue.
          - Blue (bottom-left) is below the top points and to the right of white.
        """
        pixels = [self.red_pixel, self.green_pixel, self.white_pixel, self.blue_pixel]
        if any(p is None for p in pixels):
            return False

        r_x, r_y = self.red_pixel
        g_x, g_y = self.green_pixel
        w_x, w_y = self.white_pixel
        b_x, b_y = self.blue_pixel

        cond1 = (r_y < w_y and r_y < b_y and r_x < g_x)
        cond2 = (g_y < w_y and g_y < b_y and g_x > r_x)
        cond3 = (w_y > r_y and w_y > g_y and w_x > b_x)
        cond4 = (b_y > r_y and b_y > g_y and b_x < w_x)

        return cond1 and cond2 and cond3 and cond4

    @property
    def roi(self) -> List[List[int]]:
        """
        Returns the ROI as a list of four (x, y) tuples in the order:
        red, green, white, blue.
        If the results are not valid, returns an empty list.
        """
        if not self.is_valid:
            return []

        return [
            list(self.red_pixel),
            list(self.green_pixel),
            list(self.white_pixel),
            list(self.blue_pixel)
        ]


class AutoROI(BaseSamplePatch):
    """
    The main class which deals with identifying the region of interest (ROI) within the
    image sequence which we want to extract.
    The auto-detection uses the red, green, blue, and white pixels to determine the edges.
    The resulting ROI is returned as a list of four (x, y) tuples.
    """

    def __init__(self, led_wall_settings: LedWallSettings,
                 separation_results: SeparationResults):
        """ Initialize an instance of AutoROI

        Args:
            led_wall_settings: The LED wall we want to detect the ROI for.
            separation_results: The results of the separation detection for the LED wall sequence.
        """
        super().__init__(led_wall_settings, separation_results,
                         constants.PATCHES.DISTORT_AND_ROI)

    def detect_control_points(self, image: np.ndarray) -> dict:
        """
        Detect the most red, green, blue, and white pixel in the image.

        Returns a dict mapping color names to (x, y) coordinates.
        """
        # Separate channels as floats
        R = image[:, :, 0].astype(float)
        G = image[:, :, 1].astype(float)
        B = image[:, :, 2].astype(float)

        # Compute simple scores
        red_score = R - (G + B) / 2
        green_score = G - (R + B) / 2
        blue_score = B - (R + G) / 2
        white_score = np.minimum(np.minimum(R, G), B)  # high, balanced channels

        coords = {}
        y, x = np.unravel_index(np.argmax(red_score), red_score.shape)
        coords['red'] = (int(x), int(y))

        y, x = np.unravel_index(np.argmax(green_score), green_score.shape)
        coords['green'] = (int(x), int(y))

        y, x = np.unravel_index(np.argmax(blue_score), blue_score.shape)
        coords['blue'] = (int(x), int(y))

        y, x = np.unravel_index(np.argmax(white_score), white_score.shape)
        coords['white'] = (int(x), int(y))

        return coords

    def run(self) -> AutoROIResults:
        """
        Run the auto ROI detection and return the results.

        Returns:
            AutoROIResults: The results of the ROI detection.
        """
        results = AutoROIResults()
        frames_to_sample = self.calculate_frames_to_sample()
        first_patch_frame = frames_to_sample[0]

        if first_patch_frame > self.led_wall.sequence_loader.end_frame:
            return results

        frame = self.led_wall.sequence_loader.get_frame(
            first_patch_frame)

        frame_buffer = frame.image_buf
        # Create the white balance matrix.
        white_balance_matrix = self.get_white_balance_matrix_from_slate()

        # Ensure the image is in reference space (ACES2065-1).
        frame_image = imaging_utils.apply_color_conversion(
            frame_buffer,
            str(self.led_wall.input_plate_gamut),
            str(self.led_wall.project_settings.reference_gamut)
        )

        # Apply the white balance matrix to the frame.
        balanced_image = imaging_utils.apply_matrix_to_img_buf(
            frame_image, white_balance_matrix
        )
        image_np = imaging_utils.image_buf_to_np_array(
            balanced_image)
        co_ords = self.detect_control_points(image_np)

        results.red_pixel = co_ords['red']
        results.green_pixel = co_ords['green']
        results.blue_pixel = co_ords['blue']
        results.white_pixel = co_ords['white']
        return results
