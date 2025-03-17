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

import sys
from typing import List, Tuple

from open_vp_cal.core.utils import clamp
from open_vp_cal.led_wall_settings import LedWallSettings

from open_vp_cal.imaging import imaging_utils
from open_vp_cal.framework.sample_patch import BaseSamplePatch
from open_vp_cal.framework.identify_separation import SeparationResults
from open_vp_cal.core import constants


class AutoROIResults:
    """
    Class to store the results of the ROI detection.
    Now the ROI is stored as a list of four (x, y) tuples in the order:
    top-left, top-right, bottom-right, bottom-left.
    """
    def __init__(self):
        self.red_value = -1
        self.red_pixel = None

        self.green_value = -1
        self.green_pixel = None

        self.blue_value = -1
        self.blue_pixel = None

        self.white_value = -1
        self.white_pixel = None

    @property
    def is_valid(self) -> bool:
        # Check that we have at least one valid detection on each edge.
        if not self.red_pixel and not self.green_pixel:
            return False
        if not self.blue_pixel and not self.white_pixel:
            return False
        if not self.red_pixel and not self.blue_pixel:
            return False
        if not self.green_pixel and not self.white_pixel:
            return False
        return True

    @property
    def roi(self) -> List[Tuple[int, int]]:
        """
        Returns the ROI as a list of four (x, y) tuples:
        top-left, top-right, bottom-right, bottom-left.
        These coordinates are computed from the detected edge pixels.
        If the results are not valid, an empty list is returned.
        """
        if self.is_valid:
            return [
                (self.left, self.top),
                (self.right, self.top),
                (self.right, self.bottom),
                (self.left, self.bottom)
            ]
        else:
            return []

    @property
    def left(self) -> int:
        return self._check(self.red_pixel, self.blue_pixel, 0)

    @property
    def right(self) -> int:
        return self._check(self.green_pixel, self.white_pixel, 0)

    @property
    def top(self) -> int:
        return self._check(self.red_pixel, self.green_pixel, 1)

    @property
    def bottom(self) -> int:
        return self._check(self.blue_pixel, self.white_pixel, 1)

    @staticmethod
    def _check(pixel_a, pixel_b, index):
        """
        Returns a value based on the two detected pixels.
        If only one is valid, that value is returned.
        If both are valid, the average is returned.
        """
        if pixel_a and not pixel_b:
            return pixel_a[index]
        if not pixel_a and pixel_b:
            return pixel_b[index]
        if pixel_a and pixel_b:
            return int(((pixel_a[index] + pixel_b[index]) * 0.5))
        return 0


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

    def run(self) -> AutoROIResults:
        """
        Run the auto ROI detection and return the results.

        Returns:
            AutoROIResults: The results of the ROI detection.
        """
        results = AutoROIResults()
        first_patch_frame, _ = self.calculate_first_and_last_patch_frame()

        if first_patch_frame > self.led_wall.sequence_loader.end_frame:
            return results

        frame = self.led_wall.sequence_loader.get_frame(
            first_patch_frame + self.trim_frames)

        image_plate_gamut = frame.image_buf
        pixel_buffer = 5
        detection_threshold = 1.7

        # Create the white balance matrix.
        white_balance_matrix = self.get_white_balance_matrix_from_slate()

        # Ensure the image is in reference space (ACES2065-1).
        frame_image = imaging_utils.apply_color_conversion(
            image_plate_gamut,
            str(self.led_wall.input_plate_gamut),
            str(self.led_wall.project_settings.reference_gamut)
        )

        # Apply the white balance matrix to the frame.
        balanced_image = imaging_utils.apply_matrix_to_img_buf(
            frame_image, white_balance_matrix
        )
        for y_pos in range(balanced_image.spec().height):
            for x_pos in range(balanced_image.spec().width):
                pixel = balanced_image.getpixel(x_pos, y_pos)
                red = clamp(pixel[0], 0, sys.float_info.max)
                green = clamp(pixel[1], 0, sys.float_info.max)
                blue = clamp(pixel[2], 0, sys.float_info.max)

                if red > results.red_value:
                    if red > max(green, blue) * detection_threshold:
                        results.red_pixel = (x_pos + pixel_buffer, y_pos + pixel_buffer)
                        results.red_value = red

                if green > results.green_value:
                    if green > max(red, blue) * detection_threshold:
                        results.green_pixel = (x_pos - pixel_buffer, y_pos + pixel_buffer)
                        results.green_value = green

                if blue > results.blue_value:
                    if blue > max(red, green) * detection_threshold:
                        results.blue_pixel = (x_pos + pixel_buffer, y_pos - pixel_buffer)
                        results.blue_value = blue

                white = (red + green + blue) / 3
                if white > results.white_value:
                    results.white_pixel = (x_pos - pixel_buffer, y_pos - pixel_buffer)
                    results.white_value = white

        return results
