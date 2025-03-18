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

This file contains the base class for the application, this class contains all the methods which are used by the
application to perform the analysis, calibration and export of the LED walls. This class is inherited by the UI and
CLI classes which implement the methods to display the results to the user.
"""
import os
from typing import List, Dict, Tuple, Any

from open_vp_cal.core import constants, utils
from open_vp_cal.core.structures import OpenVPCalWarning, OpenVPCalException
from open_vp_cal.framework.configuraton import Configuration
from open_vp_cal.framework.processing import Processing, SeparationException
from open_vp_cal.framework.utils import (generate_patterns_for_led_walls,
                                         generate_spg_patterns_for_led_walls)
from open_vp_cal.framework.validation import Validation
from open_vp_cal.imaging import imaging_utils
from open_vp_cal.led_wall_settings import LedWallSettings
from open_vp_cal.project_settings import ProjectSettings


class OpenVPCalBase:
    """
    This class contains all the methods which are used by the application to perform the analysis, calibration and
    export of the LED walls. This class is inherited by the UI and used by the CLI or directly via custom python
    scripts
    """

    def __init__(self):
        self._errors = []
        self._warnings = []
        self._infos = []

    def error_messages(self) -> list[Any]:
        """ Returns the list of error messages which have been logged
        """
        return self._errors

    def error_message(self, message) -> None:
        """ Logs an error message and stores it within the class

        Args:
            message: The message to log
        """
        self._errors.append(message)

    def warning_messages(self) -> list[Any]:
        """ Returns the list of warning messages which have been logged
        """
        return self._warnings

    def warning_message(self, message: str, yes_text: str = "Yes", no_text: str = "No") -> bool:
        """ Logs a warning message and stores it within the class

        Args:
            message: The message to log
            yes_text: The text to display on any ui which inherits this class for the yes button
            no_text: The text to display on the no button for any ui which inherits this class

        Returns:
            Whether the user has selected yes or no if implemented in an ui, otherwise returns True
        """
        self._warnings.append(message)
        return True

    def info_messages(self) -> list[Any]:
        """ Returns the list of warning messages which have been logged
        """
        return self._infos

    def info_message(self, message) -> None:
        """ Logs an info message and stores it within the class

        Args:
            message: The message to log
        """
        self._infos.append(message)

    def single_camera_across_all_wall(self, led_walls: List[LedWallSettings]) -> bool:
        """ Checks to see if all the LED walls have the same camera gamut, if they do, we return True, otherwise we
            return False

        Args:
            led_walls: The LED walls we want to check

        Returns:

        """
        camera_gamuts = {led_wall.native_camera_gamut for led_wall in led_walls}
        if len(camera_gamuts) > 1:
            message = "Multiple Camera Gamuts Detected, Would You Like To Continue?"
            if not self.warning_message(message):
                return False
        return True

    def validate_roi(self, roi: List[Tuple[float, float]]) -> bool:
        """
        Validates the control point arrangement for an ROI defined by four (x, y) tuples.

        The following conditions must be satisfied:
          - Red (index 0) must be higher than Blue (index 2) and White (index 3)
            (i.e. its y-value is smaller) and further left than Green (index 1) (i.e. its x-value is smaller).
          - Green (index 1) must be higher than Blue (index 2) and White (index 3)
            (i.e. its y-value is smaller) and further right than Red (index 0) (i.e. its x-value is larger).
          - White (index 3) must be lower than Red (index 0) and Green (index 1)
            (i.e. its y-value is larger) and further left than Blue (index 2) (i.e. its x-value is smaller).
          - Blue (index 2) must be lower than Red (index 0) and Green (index 1)
            (i.e. its y-value is larger) and further right than White (index 3) (i.e. its x-value is larger).

        Parameters:
            roi (List[Tuple[float, float]]): A list of four (x, y) tuples representing the ROI.
                The expected order is: [Red, Green, Blue, White], corresponding to:
                top-left, top-right, bottom-right, bottom-left.

        Returns:
            bool: True if all conditions are satisfied; False otherwise.
        """
        if len(roi) < 4:
            return True

        # Unpack the points.
        r, g, b, w = roi[0], roi[1], roi[2], roi[3]

        cond1 = (r[1] < b[1] and r[1] < w[1] and r[0] < g[
            0])  # Red is higher than blue and white and more left than green.
        cond2 = (g[1] < b[1] and g[1] < w[1] and g[0] > r[
            0])  # Green is higher than blue and white and more right than red.
        cond3 = (w[1] > r[1] and w[1] > g[1] and w[0] < b[
            0])  # White is lower than red and green and more left than blue.
        cond4 = (b[1] > r[1] and b[1] > g[1] and b[0] > w[
            0])  # Blue is lower than red and green and more right than white.

        return cond1 and cond2 and cond3 and cond4

    def run_pre_checks(self, led_walls: List[LedWallSettings]) -> bool:
        """ Runs the pre-checks for the analysis and calibration, we report any warnings or failures to the user.

        Args:
            led_walls: The LED walls we want to run the pre-checks on

        Returns:
            Whether we should continue with the analysis/calibration or not
        """
        led_wall_names = [led_wall.name for led_wall in led_walls]
        for led_wall in led_walls:
            if not led_wall.has_valid_white_balance_options():
                message = f"Only Select 1 option from AutoWB, or Reference Wall or External White {led_wall.name}"
                self.error_message(message)
                return False

            if led_wall.native_camera_gamut == constants.CameraColourSpace.CS_ACES:
                message = f"Native Camera Gamut Should Not Be {constants.CameraColourSpace.CS_ACES} For {led_wall.name}"
                self.error_message(message)
                return False

            if led_wall.use_white_point_offset:
                if not led_wall.white_point_offset_source:
                    self.error_message(f"External White Point Enabled But File Not Set {led_wall.name}")
                    return False

                if not os.path.exists(led_wall.white_point_offset_source):
                    self.error_message(f"External White Point File Set Does Not Exist {led_wall.name}")
                    return False

            if led_wall.match_reference_wall:
                if not led_wall.reference_wall:
                    self.error_message(f"Match Reference Wall Enabled But Not Set {led_wall.name} Not In Selection")
                    return False

                if led_wall.reference_wall not in led_wall_names:
                    self.error_message(f"Reference Wall {led_wall.reference_wall} Not In Selection")
                    return False

            if led_wall.roi:
                if not self.validate_roi(led_wall.roi):
                    self.error_message(f"ROI Set For {led_wall.name} is Invalid")
                    return False

        if not self.single_camera_across_all_wall(led_walls):
            return False

        return True

    def run_auto_detect(self, led_wall: LedWallSettings):
        """ Runs the auto detect for the given LED wall, we report any warnings or failures to the user.

            Args:
                led_wall: The LED wall we want to run the auto detect on

            Returns:
                The results of the separation and auto ROI detection

        """
        sep_results, auto_roi_results = Processing.run_auto_detect(
            led_wall
        )
        if not sep_results or not sep_results.is_valid:
            self.error_message("Unable To Identify Separation")

        if not auto_roi_results or not auto_roi_results.is_valid:
            self.error_message("Unable To Auto Identify ROI")

        return sep_results, auto_roi_results

    def analyse(self, led_walls: List[LedWallSettings]) -> bool:
        """ Runs the analysis for each of the LED walls in the selection, and performs some pre validation checks
        to ensure that the LED walls are correctly setup

        Args:
            led_walls: The LED walls we want to analyse

        Returns:
            Whether the analysis was successful or not
        """
        if not led_walls:
            message = "No Led Walls Provided"
            self.error_message(message)
            return False

        for led_wall in led_walls:
            if led_wall.processing_results:
                if led_wall.processing_results.samples:
                    message = f"Sampling Results Already Exist For {led_wall.name}, Would You Like To Overwrite?"
                    if not self.warning_message(message):
                        return False
                    break

        if not self.run_pre_checks(led_walls):
            return False

        led_walls = utils.led_wall_reference_wall_sort(led_walls)

        # We have to do these sequentially encase we are using a reference wall
        # if the separation fails inform the user to try again or that they have an issue
        for led_wall in led_walls:
            try:
                processing = Processing(led_wall)
                processing.run_sampling()
                processing.analyse()
            except SeparationException as e:
                self.error_message(f"{led_wall.name}\n{e}")
                return False
            except OpenVPCalException as e:
                self.error_message(f"{led_wall.name}\n{e}")
                return False
            except OpenVPCalWarning as e:
                self.error_message(f"{led_wall.name}\n{e}")
                return True
        return True

    def calibrate(self, led_walls: List[LedWallSettings]) -> bool:
        """
        Runs the calibration for each of the LED walls in the selection, and performs some pre validation checks

        Args:
            led_walls: The LED walls we want to calibrate

        Returns:
            Whether the calibration was successful or not
        """
        if not led_walls:
            message = "No Led Walls To Calibrate"
            self.error_message(message)
            return False

        for led_wall in led_walls:
            if not led_wall.processing_results:
                self.error_message(f"No Sampling Results For {led_wall.name}")
                return False

            if not led_wall.has_valid_white_balance_options():
                message = f"Only Select 1 option from AutoWB, or Reference Wall or External White {led_wall.name}"
                self.error_message(message)
                return False

        if not self.run_pre_checks(led_walls):
            return False

        led_walls = utils.led_wall_reference_wall_sort(led_walls)

        # We have to do these sequentially encase we are using a reference wall
        for led_wall in led_walls:
            processing = Processing(led_wall)
            processing.calibrate()
        return True

    def post_analysis_validations(self, led_walls: List[LedWallSettings]) -> bool:
        """ Run the validation checks on the results of the analysis, we report any warnings or failures to the user.

        Args:
            led_walls: A list of led walls we want to validate the calibration results for

        Returns:
            Whether we should continue with the analysis or not

        """
        validation = Validation()
        validation_results = []
        validation_status = constants.ValidationStatus.PASS
        for led_wall in led_walls:
            results = validation.run_validations(led_wall.processing_results.pre_calibration_results)
            for result in results:
                if result.status != constants.ValidationStatus.PASS:
                    validation_status = utils.calculate_validation_status(validation_status, result.status)
                    validation_results.append(f"{led_wall.name} - {result.name}\n{result.message}\n")

        if validation_status == constants.ValidationStatus.FAIL:
            validation_results_message = "\n".join(validation_results)
            self.error_message(f"Validation Failed:\n{validation_results_message}\n"
                               f"We Strongly Suggest To Address These Issues Before Continuing")
            return False

        if validation_status == constants.ValidationStatus.WARNING:
            validation_results_message = "\n".join(validation_results)
            if not self.warning_message(f"Validation Warning:\n{validation_results_message}",
                                        yes_text="Continue", no_text="Abort"):
                return False
        return True

    def apply_post_analysis_configuration(self, led_walls: List[LedWallSettings]) -> Dict:
        """ Runs the configuration checks on the results of the analysis, we can inform the user and from the ui or
        inheriting class apply these settings to the LED walls


        Args:
            led_walls: A list of led walls we want to run the configuration checks on

        Returns:
            A dictionary containing the configuration results for each led wall, the key is the LED wall name and the
            value is a list of tuples containing the configuration parameter and the value we have recommended
        """
        configuration = Configuration()
        configuration_messages = ["Based On The Analysis We Have Recommended The Following Settings:"]
        configuration_results = {}
        for led_wall in led_walls:
            configuration_results[led_wall.name] = []
            results = configuration.run_configuration_checks(led_wall.processing_results.pre_calibration_results)
            configuration_messages.append(f"\n{led_wall.name}")
            for result in results:
                configuration_messages.append(f"{result.param}: {result.value}")
                configuration_results[led_wall.name].append((result.param, result.value))
        self.info_message("\n".join(configuration_messages))
        return configuration_results

    def export(self, project_settings_model: ProjectSettings, led_walls: List[LedWallSettings]) -> Tuple[bool, List]:
        """ Runs the export for the given led walls, we report any warnings or failures to the user.

        Args:
            project_settings_model: The project settings model we want to export
            led_walls: A list of led walls we want to export the calibration for

        Returns:
            Whether the export was successful or not
        """
        # We need to ensure that all the walls have been analysed before we can ex
        for led_wall in led_walls:
            if not led_wall.processing_results:
                self.error_message(f"No Sampling Results For {led_wall.name}")
                return False, []

            if not led_wall.processing_results.calibration_results:
                self.error_message(f"No Analysis Results For {led_wall.name}")
                return False, []

        walls = Processing.run_export(project_settings_model, led_walls)
        return True, walls

    @staticmethod
    def generate_patterns_for_led_walls(project_settings: ProjectSettings, led_walls: List):
        """
        For the given project settings and list of led walls, generate the calibration patterns for the led walls
        """
        generate_patterns_for_led_walls(project_settings, led_walls)

    @staticmethod
    def generate_spg_patterns_for_led_walls(
            project_settings: ProjectSettings, led_walls: List) -> None:
        """ For the given project settings and list of led walls, generate the patterns for SPG which is used to
            evaluate and diagnose issues with the imaging chain

        Args:
            project_settings: The project settings used for the project
            led_walls: the led walls we want to generate patterns from
        """

        generate_spg_patterns_for_led_walls(project_settings, led_walls)

    def export_debug_swatches(self, project_settings) -> None:
        """ Export the Analysis Swatches in their raw format that was sampled from the camera
        """
        swatches_folder = os.path.join(
            project_settings.export_folder, constants.ProjectFolders.SWATCHES)
        if not os.path.exists(swatches_folder):
            os.mkdir(swatches_folder)

        for led_wall in project_settings.led_walls:
            if led_wall.processing_results.sample_buffers:
                led_swatches_output_folder = os.path.join(swatches_folder, led_wall.name)
                if not os.path.exists(led_swatches_output_folder):
                    os.mkdir(led_swatches_output_folder)
                file_name = f"{led_wall.name}_swatches_ACES2065-1.exr"
                output_file_name = os.path.join(led_swatches_output_folder, file_name)
                sample_buffers_stitched, _ = imaging_utils.create_and_stitch_analysis_strips(
                    [], led_wall.processing_results.sample_buffers)
                result = imaging_utils.stitch_images_vertically([sample_buffers_stitched])
                imaging_utils.write_image(result, output_file_name, "float")
