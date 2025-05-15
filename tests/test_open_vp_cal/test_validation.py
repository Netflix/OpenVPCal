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
"""

import json
import os.path

from open_vp_cal.core import constants
from open_vp_cal.framework.validation import Validation
from test_utils import TestBase


class Test_Validation(TestBase):

    def setUp(self) -> None:
        super().setUp()

        self.calibration_results = self.get_test_calibration_results()

    def get_test_calibration_results(self):
        folder = self.get_test_resources_folder()
        file_name = "Wall1_calibration_results.json"
        full_file_name = os.path.join(folder, file_name)
        with open(full_file_name, encoding="utf-8") as handle:
            return json.load(handle)

    def test_exposure_validation(self):
        result = Validation().exposure_validation(self.calibration_results)
        self.assertEqual(constants.ValidationStatus.PASS, result.status)

    def test_eotf_validation(self):
        result = Validation().eotf_validation(self.calibration_results)
        self.assertEqual(constants.ValidationStatus.PASS, result.status)

    def test_eotf_validation_fail(self):
        mock_eotf = [item * 50 for item in self.calibration_results[constants.Results.DELTA_E_EOTF_RAMP]]
        self.calibration_results[constants.Results.DELTA_E_EOTF_RAMP] = mock_eotf

        result = Validation().eotf_validation(self.calibration_results)
        self.assertEqual(constants.ValidationStatus.FAIL, result.status)

    def test_check_gamut_delta_E(self):
        result = Validation().check_gamut_delta_E(self.calibration_results)
        self.assertEqual(constants.ValidationStatus.PASS, result.status)

    def test_check_gamut_delta_E_warn(self):
        mock_deltaE = [item * 0.01 for item in self.calibration_results[constants.Results.DELTA_E_RGBW]]
        self.calibration_results[constants.Results.DELTA_E_RGBW] = mock_deltaE
        result = Validation().check_gamut_delta_E(self.calibration_results)
        self.assertEqual(constants.ValidationStatus.WARNING, result.status)
