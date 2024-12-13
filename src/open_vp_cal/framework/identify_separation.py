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

Module which has classes dedicated to identifying the separation between the images within the sequence, which
is done through identifying the first red frame and first green frame in the image sequence
"""
from typing import List

import numpy as np
from scipy.signal import find_peaks

from open_vp_cal.core import constants
from open_vp_cal.imaging import imaging_utils
from open_vp_cal.led_wall_settings import LedWallSettings


class SeparationResults:
    """
    Class to store the results of the separation detection
    """

    def __init__(self):
        """
        Initialize an instance of SeparationResults.
        """
        self.first_red_frame = None
        self.first_green_frame = None

    @property
    def is_valid(self) -> bool:
        """ Returns if the separation results are valid or not, if we have not found red or green frames its failure,
        also we know red frames come before green frames.

        Returns: Returns if the separation results are valid or not
        """
        if not self.first_green_frame:
            return False
        if not self.first_green_frame:
            return False
        if self.separation < 1:
            return False
        return True

    @property
    def separation(self) -> int:
        """ Returns the separation value between the first red and green frames if both have been found, and the
        green frame was found after the red frame, otherwise returns -1

        Returns: The separation value between the first red and green frames if both have been found

        """
        if not self.first_red_frame or not self.first_green_frame:
            return -1
        if self.first_green_frame.frame_num < self.first_red_frame.frame_num:
            return -1
        return self.first_green_frame.frame_num - self.first_red_frame.frame_num


class IdentifySeparation:
    """
    The main class which deals with identifying the separation of the patches within the image sequence
    """

    def __init__(self, led_wall_settings: LedWallSettings):
        """
        Initialize an instance of IdentifySeparation.

        Args:
            led_wall_settings (LedWallSettings): The LED wall settings we want to identify the separation
        """
        self.led_wall = led_wall_settings
        self.separation_results = SeparationResults()

    def run(self):
        """
        Run the separation identification

        Returns:
            SeparationResults: The results of the separation identification.
        """
        self._find_first_red_and_green_frames()
        self.led_wall.separation_results = self.separation_results
        return self.separation_results

    @staticmethod
    def check_red(mean_color: List[float]) -> bool:
        """ We check if the mean colour is red or not

        Args:
            mean_color: The mean colour of the roi for an image

        Returns: True or False depending on if the mean colour is red or not

        """
        return imaging_utils.detect_red(mean_color)

    @staticmethod
    def check_green(mean_color: List[float]) -> bool:
        """ We check if the mean colour is green or not

        Args:
            mean_color: The mean colour of the roi for an image

        Returns: True or False depending on if the mean colour is green or not
        """
        return imaging_utils.detect_green(mean_color)

    def _find_first_red_and_green_frames(self) -> None:
        """
        Iterates over all frames in the sequence loader, computes the mean colour of each frame, and finds the first
        frame that is red and the first frame that is green.

        The results are stored in the separation_results attribute.
        """
        frame_numbers = []
        distances = []

        previous_mean_frame = None

        slate_frame_plate_gamut = self.led_wall.sequence_loader.get_frame(
            self.led_wall.sequence_loader.start_frame
        )

        # Ensure the slate frame is in reference gamut
        slate_frame = imaging_utils.apply_color_conversion(
            slate_frame_plate_gamut.image_buf,
            str(self.led_wall.input_plate_gamut),
            str(self.led_wall.project_settings.reference_gamut)
        )
        white_balance_matrix = imaging_utils.calculate_white_balance_matrix_from_img_buf(
            slate_frame)

        for frame in self.led_wall.sequence_loader:
            # Load the image from the frame and ensure it is in reference gamut
            image_plate_gamut = frame.extract_roi(self.led_wall.roi)
            image = imaging_utils.apply_color_conversion(
                image_plate_gamut,
                str(self.led_wall.input_plate_gamut),
                str(self.led_wall.project_settings.reference_gamut)
            )

            # Apply the white balance matrix to the frame
            image = imaging_utils.apply_matrix_to_img_buf(
                image, white_balance_matrix
            )

            # Compute the average for all the values which are above the initial average
            mean_color, _ = imaging_utils.get_average_value_above_average(image)
            distance = 0
            if previous_mean_frame:
                distance = imaging_utils.calculate_distance(
                    mean_color, previous_mean_frame)

            # Store the frame number and distance
            frame_numbers.append(frame.frame_num)
            distances.append(distance)
            previous_mean_frame = mean_color

            # Check if the image is red or we detect a significant change in the mean
            if self.check_red(mean_color):
                if self.separation_results.first_red_frame is None:
                    self.separation_results.first_red_frame = frame
                    continue

            # Check if the image is green or if we detect a significant change in the
            # mean colour
            if self.check_green(mean_color):
                if self.separation_results.first_green_frame is None:
                    self.separation_results.first_green_frame = frame
                    continue

            distances_array = np.array(distances)
            peaks, _ = find_peaks(distances_array, height=1)
            if len(peaks) >= 4:

                first_peak_frame_num = frame_numbers[peaks[0]]
                first_peak_frame = self.led_wall.sequence_loader.get_frame(
                    first_peak_frame_num
                )
                # If we didn't find a red frame, set the first red frame to the first
                # peak
                if self.separation_results.first_red_frame is None:
                    self.separation_results.first_red_frame = first_peak_frame

                # If the detected red frame is not within 3 frames of the first peak
                # we detected the second red patch so we should use the first peak as
                # the first red frame
                if not imaging_utils.is_within_range(
                        self.separation_results.first_red_frame.frame_num,
                        first_peak_frame_num, 3):
                    self.separation_results.first_red_frame = first_peak_frame

                second_peak_frame_num = frame_numbers[peaks[1]]
                second_peak_frame = self.led_wall.sequence_loader.get_frame(
                    second_peak_frame_num
                )
                # If we didn't find a green frame, set the first green frame to the
                # second peak
                if self.separation_results.first_green_frame is None:
                    self.separation_results.first_green_frame = second_peak_frame

                # If the detected green frame is not within 3 frames of the second peak
                # we detected the second green patch so we should use the first peak as
                # the first red frame
                if not imaging_utils.is_within_range(
                        self.separation_results.first_green_frame.frame_num,
                        second_peak_frame_num, 3):
                    self.separation_results.first_green_frame = second_peak_frame

                if (self.separation_results.first_red_frame is not None
                        and self.separation_results.first_green_frame is not None):
                    break
