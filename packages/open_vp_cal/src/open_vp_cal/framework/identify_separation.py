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
import numpy as np
from open_vp_cal.framework.frame import Frame
from scipy.signal import find_peaks

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
        self.first_grey_frame = None
        self.first_red_frame = None
        self.first_green_frame = None
        self.first_blue_frame = None
        self.second_red_frame = None

    @property
    def is_valid(self) -> bool:
        """ Returns if the separation results are valid or not, if we have not found red or green frames its failure,
        also we know red frames come before green frames.

        Returns: Returns if the separation results are valid or not
        """
        if None in (
                self.first_red_frame,
                self.first_green_frame,
                self.first_blue_frame,
                self.first_grey_frame,
                self.second_red_frame):
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
        frames = (
            self.first_red_frame,
            self.first_green_frame,
            self.first_blue_frame,
            self.first_grey_frame,
            self.second_red_frame,
        )

        # 1) Bail out if any frame is missing
        if any(f is None for f in frames):
            return -1

        # 2) Extract their frame_nums
        nums = [f.frame_num for f in frames]

        # 3) Make sure they’re non-decreasing
        if any(b < a for a, b in zip(nums, nums[1:])):
            return -1

        green_to_red = self.first_green_frame.frame_num - self.first_red_frame.frame_num
        green_to_blue = self.first_blue_frame.frame_num - self.first_green_frame.frame_num
        blue_to_grey = self.first_grey_frame.frame_num - self.first_blue_frame.frame_num
        grey_to_second_red = self.second_red_frame.frame_num - self.first_grey_frame.frame_num
        separation = round((green_to_red + green_to_blue + blue_to_grey + grey_to_second_red) / 4.0)
        return separation


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
        self._find_frame_peaks()
        self.led_wall.separation_results = self.separation_results
        return self.separation_results

    def _find_frame_peaks(self) -> None:
        """
        Iterates over all frames in the sequence loader, convert the images to ACES2065-1, computes the mean colour of each
        patch, and we detect the peaks

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
            img_array = imaging_utils.image_buf_to_np_array(image)
            mean_color = np.mean(img_array, axis=(0, 1)).tolist()
            distance = 0
            if previous_mean_frame:
                distance = imaging_utils.calculate_distance(
                    mean_color, previous_mean_frame)

            # Store the frame number and distance
            frame_numbers.append(frame.frame_num)
            distances.append(distance)
            previous_mean_frame = mean_color

            # Calculate the peaks
            distances_array = np.array(distances)
            peaks, _ = find_peaks(distances_array, height=1)
            if len(peaks) >= 8:
                    peak_frame = self.get_frame_for_peak(frame_numbers, peaks, 0)
                    self.separation_results.first_red_frame = peak_frame

                    peak_frame = self.get_frame_for_peak(frame_numbers, peaks, 1)
                    self.separation_results.first_green_frame = peak_frame

                    peak_frame = self.get_frame_for_peak(frame_numbers, peaks, 2)
                    self.separation_results.first_blue_frame = peak_frame

                    peak_frame = self.get_frame_for_peak(frame_numbers, peaks, 3)
                    self.separation_results.first_grey_frame = peak_frame

                    peak_frame = self.get_frame_for_peak(frame_numbers, peaks, 4)
                    self.separation_results.second_red_frame = peak_frame
                    break

    def get_frame_for_peak(self, frame_numbers: list[int], peaks: np.ndarray, peak_idx: int) -> Frame:
        """ Gets the frame for the given peak index so we can get the frame for the detected patches

        Args:
            frame_numbers (list[int]): The list of frame numbers
            peaks (np.ndarray): The peaks detected in the image sequence
            peak_idx (int): The index of the peak we want to get the frame for

        """
        first_peak_frame_num = frame_numbers[peaks[peak_idx]]
        first_peak_frame = self.led_wall.sequence_loader.get_frame(
            first_peak_frame_num
        )
        return first_peak_frame
