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
from test_open_vp_cal.test_utils import TestBase

import open_vp_cal
from open_vp_cal.framework.generation import PatchGeneration
from open_vp_cal.core import constants


class TestGeneration(TestBase):
    def test_generation(self):
        """Test The Calibration Pattern Generation"""
        # We force the version so that the slate always gets the same version to bake into the image
        # else the hash will change and the test will fail
        open_vp_cal.__version__ = "0.1.0a"
        project_id = "123456"
        self.project_settings.project_id = project_id

        patch_generator = PatchGeneration(self.led_wall)
        file_paths = patch_generator.generate_patches(constants.PATCHES.PATCH_ORDER)
        expected_root_folder = os.path.join(
            self.get_test_output_folder(),
            constants.ProjectFolders.EXPORT,
            constants.ProjectFolders.PATCHES,
            "OpenVPCal_Wall1_ITU_R_BT_2020_ST_2084",
            self.project_settings.file_format.replace(".", ""),
        )
        reference_root_folder = os.path.join(
            self.get_test_resources_folder(),
            constants.ProjectFolders.EXPORT,
            constants.ProjectFolders.PATCHES,
            "OpenVPCal_Wall1_ITU_R_BT_2020_ST_2084"
        )
        for file_path in file_paths:
            base_name = os.path.basename(file_path)
            expected_file_name = os.path.join(expected_root_folder, base_name)
            self.assertTrue(os.path.exists(expected_file_name))

            comparison_image = os.path.join(reference_root_folder, base_name)
            self.compare_image_files(comparison_image, file_path, self.project_settings.file_format)
