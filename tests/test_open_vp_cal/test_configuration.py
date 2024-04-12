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
from open_vp_cal.framework.configuraton import Configuration
from test_open_vp_cal.test_utils import TestBase


class Test_Configuration(TestBase):

    def setUp(self) -> None:
        super().setUp()

        self.calibration_results = self.get_test_calibration_results()

    def get_test_calibration_results(self):
        folder = self.get_test_resources_folder()
        file_name = "Wall1_calibration_results.json"
        full_file_name = os.path.join(folder, file_name)
        with open(full_file_name, encoding="utf-8") as handle:
            return json.load(handle)

    def test_decide_if_eotf_correction_needed(self):
        self.calibration_results[constants.Results.EOTF_LINEARITY] = [[1.9, 0.8, 0.9][:] for _ in range(30)]
        result = Configuration().decide_if_eotf_correction_needed(self.calibration_results)
        self.assertEqual(result.value, True)

    def test_decide_if_eotf_correction_needed_false(self):
        self.calibration_results[constants.Results.EOTF_LINEARITY] = [[0.9, 1.1, 1.0][:] for _ in range(30)]
        result = Configuration().decide_if_eotf_correction_needed(self.calibration_results)
        self.assertEqual(result.value, False)

    def test_decide_if_we_do_gamut_compression(self):
        result = Configuration().decide_if_we_do_gamut_compression(self.calibration_results)
        self.assertEqual(result.value, True)

    def test_decide_if_we_do_gamut_compression_false(self):
        self.calibration_results[constants.Results.MAX_DISTANCES] = [1.05, 1.05, 1.05]
        result = Configuration().decide_if_we_do_gamut_compression(self.calibration_results)
        self.assertEqual(result.value, False)


