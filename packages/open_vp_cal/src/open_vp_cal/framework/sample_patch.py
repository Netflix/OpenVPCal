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

Module that contains classes who are responsible for sampling and analysing the patches in the image sequence
"""
from concurrent.futures import ThreadPoolExecutor, as_completed
import numpy as np
from colour_checker_detection.detection.segmentation import (
    detect_colour_checkers_segmentation)

from open_vp_cal.core.utils import find_factors_pairs
from open_vp_cal.imaging import imaging_utils
from open_vp_cal.core.structures import SamplePatchResults, OpenVPCalException
from open_vp_cal.framework.identify_separation import SeparationResults
from open_vp_cal.led_wall_settings import LedWallSettings
from open_vp_cal.core import constants


class BaseSamplePatch:
    """
    Base class for sampling a patch, contains functions for identifying a given patch within a sequence and the
    range of frames we want to use for sampling.
    """

    def __init__(self, led_wall_settings: LedWallSettings,
                 separation_results: SeparationResults,
                 patch: str):
        self.led_wall = led_wall_settings
        self.separation_results = separation_results
        self.patch = patch
        self.required_sample_frames = 3
        self.min_required_sample_frames = 2

    def get_num_patches_relative_to_red(self, red_patch_index) -> int:
        """ Returns the number of patches relative to the red patch index, accounting
        for if the patch occurs before or after the eotf ramp patches

        Args:
            red_patch_index (int): The index of the red patch.

        Returns:
            int: The number of patches relative to the red patch index.
        """
        eotf_ramp_index = constants.PATCHES.get_patch_index(
            constants.PATCHES.EOTF_RAMPS)
        patch_index = constants.PATCHES.get_patch_index(self.patch)
        if patch_index > eotf_ramp_index:
            return patch_index - red_patch_index + self.led_wall.num_grey_patches
        return patch_index - red_patch_index

    def get_sample_range(self, first_frame, last_frame, num_frames):
        """
        Returns a list of frame numbers sampled evenly around the centre frame,
        which is automatically calculated as the midpoint of the range.

        Args:
            first_frame (int): The first frame in the sequence.
            last_frame (int): The last frame in the sequence.
            num_frames (int): The total number of frames to return.

        Returns:
            List[int]: A list of frame numbers sampled symmetrically around the centre frame.
        """
        # We trim by one frame to remove any chance of multi plexing
        first_frame +=1
        last_frame -=1

        if num_frames < 1:
            raise ValueError("num_frames must be at least 1")
        if last_frame < first_frame:
            raise ValueError("last_frame must be >= first_frame")

        total_frames = last_frame - first_frame + 1
        if num_frames > total_frames:
            raise ValueError("Requested more frames than available in the range")

        # Calculate the centre frame
        centre_frame = (first_frame + last_frame) // 2

        # Special case: only one frame requested
        if num_frames == 1:
            return [centre_frame]

        half = (num_frames - 1) / 2

        # Determine how far to go left and right
        if num_frames % 2 == 1:
            left_count = right_count = int(half)
        else:
            left_count = int(half)
            right_count = int(half)

        max_left = centre_frame - first_frame
        max_right = last_frame - centre_frame

        # Adjust to stay within bounds
        left_count = min(left_count, max_left)
        right_count = min(right_count, max_right)

        # Balance the window if needed
        while left_count + right_count < num_frames - 1:
            if left_count < max_left:
                left_count += 1
            elif right_count < max_right:
                right_count += 1
            else:
                break

        # Generate frame list
        left_frames = [centre_frame - i for i in range(left_count, 0, -1)]
        right_frames = [centre_frame + i for i in range(1, right_count + 1)]
        return left_frames + [centre_frame] + right_frames

    def calculate_frames_to_sample(self) -> list[int]:
        """
        Calculates the frames which we should sample based on the predicted first and last frames
        of each patch, by remving the first and last frames of each patch to reduce the chance of
        multiplexing, and then isolating a number of frames from around the centre frame of each
        patch, we need to ensure that we have a minimum of 2 samples from each patch

        Returns:
            tuple[int, int]: The first and last frame of the patch.
        """
        first_patch_frame, last_patch_frame = self.calculate_first_and_last_patch_frame()

        sample_frames = self.get_sample_range(
            first_patch_frame, last_patch_frame, self.required_sample_frames
        )
        return sample_frames

    def calculate_first_and_last_patch_frame(self):
        red_patch_index = constants.PATCHES.get_patch_index(
            constants.PATCHES.RED_PRIMARY_DESATURATED)
        number_of_patches_relative_to_red = self.get_num_patches_relative_to_red(
            red_patch_index
        )

        if not self.separation_results.is_valid:
            raise OpenVPCalException("Separation results are not valid")

        number_of_frames = number_of_patches_relative_to_red * self.separation_results.separation
        # We get the predicted first frame and last frame of the patch assuming we remove the first and last frames to account for multiplexing
        first_patch_frame = number_of_frames + self.separation_results.first_red_frame.frame_num
        last_patch_frame = first_patch_frame + self.separation_results.separation
        return first_patch_frame, last_patch_frame

    def get_white_balance_matrix_from_slate(self) -> np.ndarray:
        """ Get the white balance matrix from the slate frame

        Returns:
            np.ndarray: The white balance matrix

        """
        slate_frame_plate_gamut = self.led_wall.sequence_loader.get_frame(
            self.led_wall.sequence_loader.start_frame
        )

        # Ensure the slate frame is in reference gamut (ACES2065-1)
        slate_frame = imaging_utils.apply_color_conversion(
            slate_frame_plate_gamut.image_buf,
            str(self.led_wall.input_plate_gamut),
            str(self.led_wall.project_settings.reference_gamut)
        )
        white_balance_matrix = imaging_utils.calculate_white_balance_matrix_from_img_buf(
            slate_frame)
        return white_balance_matrix


class SamplePatch(BaseSamplePatch):
    """
    Class to sample a patch in an image sequence.
    """

    def __init__(self, led_wall_settings: LedWallSettings,
                 separation_results: SeparationResults,
                 patch: str):
        """
        Initialize an instance of SamplePatch.

        Args:
            led_wall_settings (LedWallSettings): The LED wall settings we want to sample
            separation_results (SeparationResults): The results of the separation.
            patch (str): The patch to sample.
        """
        super().__init__(led_wall_settings, separation_results, patch)
        self.sample_results = [None]

    def run(self) -> list:
        """
        Run the patch sampling.

        Returns:
            list[open_vp_cal.core.structures.SamplePatchResults]: The results of the patch sampling.
        """
        self._sample_patch()
        return self.sample_results

    def _sample_patch(self) -> None:
        """
        Sample the patch.

        Returns:
            None
        """
        sample_frames = self.calculate_frames_to_sample()
        self.analyse_patch_frames(0, self.sample_results, sample_frames)

    def get_mixed_tol_outlier_indices(
            self,
            samples: list[list[float]],
            rtol: float = 0.1,
            atol: float = 1e-4
    ) -> list[int]:
        """
        Identify indices of RGB samples where, for any channel,
        |value - median(channel)| > atol + rtol * |median(channel)|.

        This combines an absolute floor (atol) with a relative fraction (rtol).

        Args:
            samples: List of [R, G, B] samples.
            rtol: Relative tolerance (fraction of the channel’s median).
            atol: Minimum absolute tolerance.

        Returns:
            A list of sample-indices to remove.
        """
        arr = np.array(samples, dtype=float)  # shape (N, 3)
        med = np.median(arr, axis=0)  # [med_R, med_G, med_B]
        # Compute allowed tolerance per channel:
        tol = atol + rtol * np.abs(med)  # shape (3,)

        # Compute absolute differences:
        diffs = np.abs(arr - med)  # shape (N, 3)

        # A sample is an outlier if any channel’s diff exceeds tol:
        mask = np.any(diffs > tol, axis=1)  # shape (N,)
        return list(np.nonzero(mask)[0])

    def analyse_patch_frames(self, idx: int, results: list, frames_to_sample: list[int]) -> None:
        """
        Analyse the frames of the patch.

        Args:
            idx (int): The index to store the results.
            results (list[open_vp_cal.core.structures.SamplePatchResults]): The list to store the results.
            frames_to_sample (list): The frame numbers to sample
        Returns:
            None
        """
        sample_results = SamplePatchResults()
        sample_frames = []
        samples = []
        for frame_num in frames_to_sample:
            frame = self.led_wall.sequence_loader.get_frame(frame_num)
            section_input = frame.extract_roi(self.led_wall.roi)

            # Convert the patch from into reference gamut from the input plate gamut
            # so all samples are sampled as reference space (ACES2065-1)
            section_aces = imaging_utils.apply_color_conversion(
                section_input,
                str(self.led_wall.input_plate_gamut),
                str(self.led_wall.project_settings.reference_gamut)
            )
            mean_color = imaging_utils.sample_image(section_aces)

            samples.append(mean_color)
            sample_frames.append(frame)

        # Now we have our samples we need to filter out any major outliers
        indices_to_remove = self.get_mixed_tol_outlier_indices(samples, rtol=0.1, atol=1e-4)
        for index in sorted(indices_to_remove, reverse=True):
            del samples[index]
            del sample_frames[index]

        if len(samples) < self.min_required_sample_frames:
            error_msg = (f"Samples from frames {frames_to_sample} for Patch {self.patch}_{idx} all have significant differences.\nThis typically indicates a problem with the playback, either missing genlock, frame blending from the media player, inconsistent playback from the media player, or extreme multiplexing."
             f"Ensure your setup is correct and re record your samples")
            raise OpenVPCalException(
                error_msg
            )

        sample_results.frames = sample_frames
        sample_results.samples = [sum(channel) / len(channel) for channel in
                                  zip(*samples)]
        results[idx] = sample_results


class SampleRampPatches(SamplePatch):
    """
    Class to sample the ramp patches in an image sequence.
    """

    def __init__(self, led_wall_settings: LedWallSettings,
                 separation_results: SeparationResults,
                 patch: str):
        """
        Initialize an instance of SampleRampPatches.

        Args:
            sequence_loader (SequenceLoader): The loader for the sequence.
            project_settings (ProjectSettings): The settings for the project.
            separation_results (SeparationResults): The results of the separation.
            patch (str): The patch to sample.
        """
        super().__init__(led_wall_settings, separation_results, patch)
        self.patch = constants.PATCHES.EOTF_RAMPS
        self.sample_results = []

    def _sample_patch(self) -> None:
        """
        Sample the ramp patches.

        Returns:
            None
        """
        # Get the first and last frame of the first patch in the ramp
        first_patch_frame, _ = self.calculate_first_and_last_patch_frame()

        # We have x number of grey patches and one black frame at the beginning of the ramp
        grey_patches = self.led_wall.num_grey_patches + 1
        results = [None] * grey_patches
        # You can choose max_workers to tune parallelism; leaving it None lets Python decide.
        with ThreadPoolExecutor() as executor:
            futures = []
            for patch_count in range(grey_patches):
                patch_start_frame = first_patch_frame + (
                        patch_count * self.separation_results.separation
                )
                patch_last_frame = patch_start_frame + (
                    self.separation_results.separation
                )
                sample_frames = self.get_sample_range(
                    patch_start_frame,
                    patch_last_frame,
                    self.required_sample_frames
                )

                fut = executor.submit(
                    self.analyse_patch_frames,
                    patch_count,
                    results,
                    sample_frames
                )
                futures.append(fut)

            # iterate over completed futures, raising any exceptions
            for fut in as_completed(futures):
                fut.result()

        # at this point either all patches succeeded, or the first exception has bubbled up
        self.sample_results = results


class MacBethSample(BaseSamplePatch):
    """
    Class to sample a patch in an image sequence.
    """

    def __init__(self, led_wall_settings: LedWallSettings,
                 separation_results: SeparationResults):
        """
        Initialize an instance of SamplePatch.

        Args:
            led_wall_settings (LedWallSettings): The LED wall settings we want to sample
            separation_results (SeparationResults): The results of the separation.
        """
        super().__init__(led_wall_settings, separation_results,
                         constants.PATCHES.MACBETH)
        self.sample_results = [None]

    def run(self) -> list:
        """
        Run the patch sampling.

        Returns:
            list[SamplePatchResults]: The results of the patch sampling.
        """
        self._sample_patch()
        return self.sample_results

    def _sample_patch(self) -> None:
        """
        Detect the macbeth chart in the patch and extract the samples for each of the swatches on the macbeth chart
        """
        frames_to_sample = self.calculate_frames_to_sample()
        sample_results = SamplePatchResults()
        samples = []
        white_balance_matrix = self.get_white_balance_matrix_from_slate()
        for frame_num in frames_to_sample:
            frame = self.led_wall.sequence_loader.get_frame(frame_num)
            sample_results.frames.append(frame)

            # Extract our region
            section_orig = frame.extract_roi(self.led_wall.roi)

            # White balance the images so we increase the detection likelihood of
            # success
            section_orig = imaging_utils.apply_matrix_to_img_buf(
                section_orig, white_balance_matrix
            )

            section_display_np_array = imaging_utils.image_buf_to_np_array(section_orig)
            imaging_utils.apply_color_converstion_to_np_array(
                section_display_np_array,
                str(self.led_wall.input_plate_gamut),
                "ACEScct",
            )

            # Run the detections
            detections = detect_colour_checkers_segmentation(
                section_display_np_array, additional_data=True)

            for colour_checker_swatches_data in detections:
                # Get the swatch colours
                swatch_colours, _, _, _ = colour_checker_swatches_data.values
                swatch_colours = np.array(swatch_colours, dtype=np.float32)

                # Reshape the number of swatches from a 24, 3 array to an x, y, 3 array
                num_swatches = swatch_colours.shape[0]
                factor_pairs = find_factors_pairs(num_swatches)
                x, y = factor_pairs[0]
                array_x_y_3 = swatch_colours.reshape(x, y, 3)

                # Convert the colours back to the input plate gamut
                imaging_utils.apply_color_converstion_to_np_array(
                    array_x_y_3,
                    "ACEScct",
                    str(self.led_wall.input_plate_gamut))

                # Inverse the white balance back to the original values
                inv_wb_matrix = np.linalg.inv(white_balance_matrix)
                array_x_y_3 = array_x_y_3 @ inv_wb_matrix


                # Convert From Input To reference gamut So all our samples are in ACES
                imaging_utils.apply_color_converstion_to_np_array(
                    array_x_y_3,
                    str(self.led_wall.input_plate_gamut),
                    str(self.led_wall.project_settings.reference_gamut)
                )

                # Reshape the array back to a 24, 3 array
                swatch_colours = array_x_y_3.reshape(num_swatches, 3)
                samples.append(swatch_colours)

        # Compute the mean for each tuple index across all tuples, if the
        # detection fails, and we get nans, then we replace the nans with black patches
        # as these are not used in the calibration directly
        averaged_tuple = np.mean(np.array(samples), axis=0)
        if not np.isnan(averaged_tuple).any():
            sample_results.samples = averaged_tuple.tolist()
        else:
            list_of_zeros = [[0.0, 0.0, 0.0] for _ in range(24)]
            sample_results.samples = list_of_zeros
        self.sample_results = [sample_results]
