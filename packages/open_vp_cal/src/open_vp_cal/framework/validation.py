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

This module contains the validation class and validation results class, which are used to run validation checks based
on the calibration results from the analysis phase. This allows us to detect if the user has shot the plates correctly
or not prior to attempting a calibration
"""
import math
from typing import List, Dict

import numpy as np

from open_vp_cal.core.constants import Results, ValidationStatus
from open_vp_cal.core.structures import ValidationResult


class Validation:
    """
    Class to hold the validation checks and run them
    """
    def __init__(self):
        self._validation = [
            self.check_macbeth_chart_detected,
            self.exposure_validation,
            self.check_max_screen_white_vs_max_eotf_ramp,
            self.check_measured_peak_vs_target_peak,
            self.eotf_validation,
            self.eotf_clamping_validation,
            self.check_gamut_delta_E
        ]

    def run_validations(self, calibration_results: Dict) -> List[ValidationResult]:
        """ For the given calibration results, we run all the registered validation checks and return the results

        Args:
            calibration_results: The results of the calibration

        Returns: The results of the validation checks

        """
        results = []
        for validation in self._validation:
            validation_result = validation(calibration_results)
            results.append(validation_result)
        return results

    @staticmethod
    def check_measured_peak_vs_target_peak(calibration_results: Dict):
        result = ValidationResult()
        result.name = "Measured EOTF Peak vs Target Peak Failed"
        result.status = ValidationStatus.PASS

        measured_peak = calibration_results[Results.MEASURED_MAX_LUM_NITS][2]
        target_peak = calibration_results[Results.TARGET_MAX_LUM_NITS]
        delta = abs(measured_peak - target_peak) / target_peak

        if delta > 0.1:  # If the delta exceeds 10%, throw an error
            result.status = ValidationStatus.FAIL
            result.message = (
                f"The measured peak luminance ({measured_peak} nits) deviates significantly from the target peak luminance "
                f"({target_peak} nits) by {round(delta * 100, 2)}%. Please check your imaging chain and re-shoot the plates."
            )
        elif delta > 0.05:  # If the delta exceeds 5%, throw a warning
            result.status = ValidationStatus.WARNING
            result.message = (
                f"The measured peak luminance ({measured_peak} nits) deviates from the target peak luminance "
                f"({target_peak} nits) by {round(delta * 100, 2)}%. This may affect calibration accuracy."
            )

        return result



    @staticmethod
    def check_macbeth_chart_detected(calibration_results: Dict):
        result = ValidationResult()
        result.name = "ColourChecker Detection Failed"
        result.status = ValidationStatus.PASS
        pre_macbeth_samples = calibration_results[Results.PRE_MACBETH_SAMPLES_XY]
        if np.allclose(pre_macbeth_samples, 0.0, atol=1e-6):
            result.status = ValidationStatus.INFO
            result.message = (
                "It appears that we were unable to detect the colour checker chart; this is not a "
                "major concern as it will not affect the calibration process. However, it is likely "
                "that you have over-defocussed the first patch. If you want to see the colour "
                "checker data, try again with slightly less defocus.\n"
            )
            return result

        return result


    @staticmethod
    def exposure_validation(calibration_results: Dict) -> ValidationResult:
        """ This validation checks that the exposure scaling factor is within a reasonable range

        Args:
            calibration_results: The calibration results

        Returns: The result of the validation check

        """
        result = ValidationResult()
        result.name = "Measured Exposure Validation"

        measured_18_percent = calibration_results[Results.MEASURED_18_PERCENT_SAMPLE]
        quarter_stop_down_18_percent = 0.144
        quarter_stop_up_18_percent = 0.225
        if measured_18_percent < quarter_stop_down_18_percent or measured_18_percent > quarter_stop_up_18_percent:
            result.status = ValidationStatus.FAIL
            result.message = (
                f"The Exposure of the 18% Patch is measured at {round(measured_18_percent, 2) * 100}%\n"
                "It seems that you have not exposed the calibration patches correctly. "
                "Please ensure to expose the first 18% patch correctly using the camera false colour or light meter."
            )
            return result

        one_tenth_stop_down_18_percent = 0.163
        one_tenth_stop_up_18_percent = 0.198
        if one_tenth_stop_down_18_percent < measured_18_percent < one_tenth_stop_up_18_percent:
            result.status = ValidationStatus.PASS
        else:
            result.status = ValidationStatus.WARNING
            result.message = (
                f"The Exposure of the 18% Patch is measured at {round(measured_18_percent, 2) * 100}%, this is not ideal.\n"
                "Please ensure to expose the first 18% patch correctly using the camera false colour or light meter."
            )

        return result

    @staticmethod
    def eotf_validation(calibration_results: Dict) -> ValidationResult:
        """ This validation checks that the EOTF is within a reasonable range, if not, we recommend re-shooting the
        plates

        Args:
            calibration_results: The calibration results

        Returns: The result of the validation check

        """
        result = ValidationResult()
        result.name = "EOTF Validation"
        delta_e_grey_ramp = calibration_results[Results.DELTA_E_EOTF_RAMP]

        valid_sample_threshold = int(len(delta_e_grey_ramp) / 3)
        valid_samples = delta_e_grey_ramp[valid_sample_threshold:-1]

        num_deltas = len(valid_samples)
        total_delta = sum(valid_samples)
        average_delta = total_delta / num_deltas

        if average_delta > 5:
            result.message = ("The EOTF detected is not within a tolerable range, please check your imaging chain from "
                              "content engine to LED processor, and re shoot the plates")
            result.status = ValidationStatus.FAIL

        return result

    @staticmethod
    def check_gamut_delta_E(calibration_results: Dict) -> ValidationResult:
        """ This validation checks that the gamut delta E and flags if the wall needs to be calibrated or not

        Args:
            calibration_results: The calibration results

        Returns: The result of the validation check

        """
        result = ValidationResult()
        result.name = "Gamut Delta Validation"
        delta_e_rgbw = calibration_results[Results.DELTA_E_RGBW]

        perceivable_calibration_limit = 3
        needs_calibration = False
        for value in delta_e_rgbw:
            if value > perceivable_calibration_limit:
                needs_calibration = True
                break

        if not needs_calibration:
            result.status = ValidationStatus.WARNING
            result.message = ("The LED wall a viewed by the camera view is within a tolerable perceivable range, "
                              "you may not need to calibrate this wall")
        return result

    @staticmethod
    def check_max_screen_white_vs_max_eotf_ramp(calibration_results: Dict) -> ValidationResult:
        """ This validation checks that the difference between the max white of the screen and the max white of the eotf
        ramp is within a reasonable range

        Args:
            calibration_results: The calibration results

        Returns: The result of the validation check

        """
        result = ValidationResult()
        result.name = "Max White vs EOTF Validation"
        max_white_delta = abs(calibration_results[Results.MAX_WHITE_DELTA])

        ten_percent_tolerance = 0.1

        if not math.isclose(max_white_delta, 1, abs_tol=ten_percent_tolerance):
            result.status = ValidationStatus.FAIL
            result.message = (
                "It appears that the EOTF ramp does not match the max peak luminance of your LED wall."
                " Please check that the wall settings match the actual peak luminance of your wall also check your "
                "imaging chain from content engine to LED processor and re shoot the plates"
                )
        return result

    @staticmethod
    def eotf_clamping_validation(calibration_results: Dict) -> ValidationResult:
        """ This validation checks that the EOTF is not being clamped by checking that the last few samples of the eotf
            are not all close to each other. If they are it suggests there is clamping happening

        Args:
            calibration_results: The calibration results

        Returns: The result of the validation check

        """
        result = ValidationResult()
        result.name = "EOTF Clamping Validation"

        eotf_ramps = np.array(calibration_results[Results.PRE_EOTF_RAMPS])
        eotf_sample_selection = 4
        last_samples = eotf_ramps[-eotf_sample_selection:]

        message = ""

        def check_too_close(samples, tolerance=0.01):
            for i in range(samples.size):
                for j in range(i + 1, samples.size):
                    if np.isclose(samples[i], samples[j], atol=tolerance):
                        return True
            return False

        # Check for each color channel if any of the values are close to each other
        for i, color in enumerate(['red', 'green', 'blue']):
            channel_samples = last_samples[:, i]
            if check_too_close(channel_samples):
                result.status = ValidationStatus.FAIL
                message += (
                    f"The last {eotf_sample_selection} of the eotf in the {color} channel have values "
                    f"which all seem to be the same, which suggests they are being clamped\n"
                )

        result.message = message
        return result
