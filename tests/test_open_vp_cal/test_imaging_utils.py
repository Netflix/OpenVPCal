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

import os

from test_open_vp_cal.test_utils import TestProject
from open_vp_cal.imaging import imaging_utils


class TestProjectExternalWhite(TestProject):
    project_name = "SampleProject2_External_White_NoLens"

    def test_standard_deviation(self):
        file_path = self.get_external_white_plates()
        result = imaging_utils.get_decoupled_white_samples_from_file(file_path)
        self.assertEqual([7.411064147949219, 7.411818027496338, 7.6257829666137695], result)

    def get_external_white_plates(self):
        result = super().get_sample_project_plates()
        return os.path.join(result, "A102_C016_102752_001.R3D", "Render.918947.exr")

    def get_sample_project_plates(self):
        result = super().get_sample_project_plates()
        return os.path.join(result, "A102_C015_1027M2_001.R3D")