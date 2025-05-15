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

The configuration module comprises the classes and methods which provide recommended settings for the calibration
based on the pre analysis. Each of the calibration checks produces a result of the param name and the recommended value
to be set for that param. The results are then used to update the project settings for the user
"""
from typing import List, Dict

from open_vp_cal.core import constants
from open_vp_cal.core.constants import Results
from open_vp_cal.core.structures import ConfigurationResult


class Configuration:
    """
    Class to hold the configuration checks and run them
    """
    def __init__(self):
        self._configuration_checks = [
            self.decide_if_eotf_correction_needed,
            self.decide_if_we_do_gamut_compression
        ]

    def run_configuration_checks(self, calibration_results: Dict) -> List[ConfigurationResult]:
        """ For the given calibration results, we run all the registered configuration checks and return the results

        Args:
            calibration_results: The results of the calibration

        Returns: The results of the configuration checks

        """
        results = []
        for configuration_check in self._configuration_checks:
            configuration_result = configuration_check(calibration_results)
            results.append(configuration_result)
        return results

    @staticmethod
    def decide_if_eotf_correction_needed(calibration_results: Dict) -> ConfigurationResult:
        """ If the deltaE for the eotf is greater than the threshold, then we recommend enabling eotf correction

        Args:
            calibration_results: The results of the calibration

        Returns: The result of the configuration check

        """
        result = ConfigurationResult()
        result.param = constants.LedWallSettingsKeys.ENABLE_EOTF_CORRECTION
        result.value = False

        eotf_linearity = calibration_results[Results.EOTF_LINEARITY]

        valid_sample_threshold = int(len(eotf_linearity) / 3)
        valid_samples = eotf_linearity[valid_sample_threshold:-1]

        upper_threshold = 1.1
        lower_threshold = 0.9
        for sample in valid_samples:
            for channel in sample:
                if upper_threshold < channel or channel < lower_threshold:
                    result.value = True
                    return result
        return result

    @staticmethod
    def decide_if_we_do_gamut_compression(calibration_results: Dict) -> ConfigurationResult:
        """ If the max distance is greater than the threshold, then we recommend enabling gamut compression

        Args:
            calibration_results: The results of the calibration

        Returns:

        """
        result = ConfigurationResult()
        result.param = constants.LedWallSettingsKeys.ENABLE_GAMUT_COMPRESSION
        result.value = False

        max_distances = calibration_results[Results.MAX_DISTANCES]

        # We say 1.1 is the max-tolerable distance because anything less we are affecting more than we are gaining
        max_distances_limit = 1.1

        for value in max_distances:
            if value > max_distances_limit:
                result.value = True
                break
        return result
