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
 which we want to extract to analyze
"""
import sys
from typing import List

from docutils.nodes import image

from open_vp_cal.core.utils import clamp
from open_vp_cal.led_wall_settings import LedWallSettings

from open_vp_cal.imaging import imaging_utils
from open_vp_cal.framework.sample_patch import BaseSamplePatch
from open_vp_cal.framework.identify_separation import SeparationResults
from open_vp_cal.core import constants


class AutoROIResults:
    """
    Class to store the results of the roi detection
    """

    def __init__(self):
        """
        Initialize an instance of AutoROIResults.
        """
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
        """ Check if the results are valid
        """
        # Can detect top
        if not self.red_pixel and not self.green_pixel:
            return False

        # Can detect bottom
        if not self.blue_pixel and not self.white_pixel:
            return False

        # Can detect left
        if not self.red_pixel and not self.blue_pixel:
            return False

        # Can detect right
        if not self.green_pixel and not self.white_pixel:
            return False

        return True

    @property
    def roi(self) -> List[int]:
        """ Get the roi from the results

        Returns: The roi detected within the image sequence

        """
        return [self.left, self.right, self.top, self.bottom] if self.is_valid else []

    @property
    def left(self) -> int:
        """ Get the left edge of the roi

        Returns: The left edge of the roi

        """
        return self._check(self.red_pixel, self.blue_pixel, 0)

    @property
    def right(self) -> int:
        """ Get the right value of the roi

        Returns: The right edge of the roi

        """
        return self._check(self.green_pixel, self.white_pixel, 0)

    @property
    def top(self) -> int:
        """ Get the top value of the roi

        Returns: The top edge of the roi

        """
        return self._check(self.red_pixel, self.green_pixel, 1)

    @property
    def bottom(self) -> int:
        """ Get the bottom value of the roi

        Returns: The bottom edge of the roi

        """
        return self._check(self.blue_pixel, self.white_pixel, 1)

    @staticmethod
    def _check(pixel_a, pixel_b, index):
        """ Returns either the value from pixel_a or pixel_b depending on which one is valid, if both are valid then
        it returns the average of the two

        Args:
            pixel_a: The first pixel
            pixel_b: The second pixel
            index: The index of the pixel to return

        Returns: The value of the pixel at the given index
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
    The main class which deals with identifying the region of interest within the image sequence which we want to
    extract
    """

    def __init__(self, led_wall_settings: LedWallSettings,
                 separation_results: SeparationResults):
        """ Initialize an instance of AutoROI

        Args:
            led_wall_settings: The LED wall we want to detect the roi for
            separation_results: The results of the separation detection for the LED wall sequence
        """
        super().__init__(led_wall_settings, separation_results,
                         constants.PATCHES.DISTORT_AND_ROI)

    def run(self) -> AutoROIResults:
        """
        Run the auto roi detection

        Returns:
            AutoROIResults: The results of the roi detection
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

        # Create the white balance matrix
        white_balance_matrix = self.get_white_balance_matrix_from_slate()

        # Ensure the image is in ACES2065-1
        frame_image = imaging_utils.apply_color_conversion(
            image_plate_gamut,
            str(self.led_wall.input_plate_gamut),
            constants.ColourSpace.CS_ACES
        )

        # Apply the white balance matrix to the frame
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
                        results.green_pixel = (
                        x_pos - pixel_buffer, y_pos + pixel_buffer)
                        results.green_value = green

                if blue > results.blue_value:
                    if blue > max(red, green) * detection_threshold:
                        results.blue_pixel = (
                        x_pos + pixel_buffer, y_pos - pixel_buffer)
                        results.blue_value = blue

                white = (red + green + blue) / 3
                if white > results.white_value:
                    results.white_pixel = (x_pos - pixel_buffer, y_pos - pixel_buffer)
                    results.white_value = white
        return results
