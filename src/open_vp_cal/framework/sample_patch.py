"""
Module that contains classes who are responsible for sampling and analysing the patches in the image sequence
"""
import threading
import numpy as np
from colour_checker_detection.detection.segmentation import detect_colour_checkers_segmentation

from open_vp_cal.imaging import imaging_utils
from open_vp_cal.core.structures import SamplePatchResults
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
        self.trim_frames = 1  # The num frames we trim from the start and end of the patch, so we avoid multiplexing
        self.required_sample_frames = 3

    def calculate_first_and_last_patch_frame(self) -> tuple[int, int]:
        """
        Calculate the first and last frame of the patch.

        Returns:
            tuple[int, int]: The first and last frame of the patch.
        """
        patch_index = constants.PATCHES.get_patch_index(self.patch)
        red_patch_index = constants.PATCHES.get_patch_index(constants.PATCHES.RED_PRIMARY_DESATURATED)
        number_of_patches_relative_to_red = patch_index - red_patch_index
        number_of_frames = number_of_patches_relative_to_red * self.separation_results.separation
        first_patch_frame = number_of_frames + self.separation_results.first_red_frame.frame_num
        last_patch_frame = first_patch_frame + (self.separation_results.separation - 1)
        trim_frames = (last_patch_frame - first_patch_frame) // self.required_sample_frames
        if trim_frames > self.trim_frames:
            self.trim_frames = trim_frames
        return first_patch_frame, last_patch_frame


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
        first_patch_frame, last_patch_frame = self.calculate_first_and_last_patch_frame()
        self.analyse_patch_frames(0, self.sample_results, first_patch_frame, last_patch_frame)

    def analyse_patch_frames(self, idx: int, results: list,
                             first_patch_frame: int, last_patch_frame: int) -> None:
        """
        Analyse the frames of the patch.

        Args:
            idx (int): The index to store the results.
            results (list[open_vp_cal.core.structures.SamplePatchResults]): The list to store the results.
            first_patch_frame (int): The first frame of the patch.
            last_patch_frame (int): The last frame of the patch.
        Returns:
            None
        """
        # We trim a number of frames off either side of the patch to ensure we remove multiplexing
        sample_results = SamplePatchResults()
        samples = []
        for frame_num in range(first_patch_frame + self.trim_frames, (last_patch_frame - self.trim_frames) + 1):
            frame = self.led_wall.sequence_loader.get_frame(frame_num)
            section = frame.extract_roi(self.led_wall.roi)
            mean_color = imaging_utils.sample_image(section)

            samples.append(mean_color)
            sample_results.frames.append(frame)
        sample_results.samples = [sum(channel) / len(channel) for channel in zip(*samples)]
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
        threads = []
        results = [None] * grey_patches
        for patch_count in range(0, grey_patches):
            patch_start_frame = first_patch_frame + (patch_count * self.separation_results.separation)
            patch_last_frame = patch_start_frame + (self.separation_results.separation - 1)

            thread = threading.Thread(target=self.analyse_patch_frames, args=(
                patch_count, results, patch_start_frame, patch_last_frame)
                                      )
            thread.start()
            threads.append(thread)

        for thread in threads:
            thread.join()
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
        super().__init__(led_wall_settings, separation_results, constants.PATCHES.MACBETH)
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
        first_patch_frame, last_patch_frame = self.calculate_first_and_last_patch_frame()
        # We trim a number of frames off either side of the patch to ensure we remove multiplexing
        sample_results = SamplePatchResults()
        samples = []
        for frame_num in range(first_patch_frame + self.trim_frames, (last_patch_frame - self.trim_frames) + 1):
            frame = self.led_wall.sequence_loader.get_frame(frame_num)
            section = frame.extract_roi(self.led_wall.roi)
            sample_results.frames.append(frame)
            section_np_array = imaging_utils.image_buf_to_np_array(section)
            for colour_checker_swatches_data in detect_colour_checkers_segmentation(
                    section_np_array, additional_data=True):
                swatch_colours, _, _ = (
                    colour_checker_swatches_data.values)


                samples.append(swatch_colours)

        # Compute the mean for each tuple index across all tuples, if the detection fails and we get nans, then we
        # replace the nans with black patches as these are not used in the calibration directly
        averaged_tuple = np.mean(np.array(samples), axis=0)
        if not np.isnan(averaged_tuple).any():
            sample_results.samples = averaged_tuple.tolist()
        else:
            list_of_zeros = [[0.0, 0.0, 0.0] for _ in range(24)]
            sample_results.samples = list_of_zeros
        self.sample_results = [sample_results]
