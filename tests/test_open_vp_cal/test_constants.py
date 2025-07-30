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
import colour

from open_vp_cal.core import constants
from test_utils import TestBase


class TestConstants(TestBase):
    def test_camera_colour_space_enum(self):
        for item in constants.CameraColourSpace:
            cs = colour.RGB_COLOURSPACES[item]
            self.assertNotEqual(cs, None)

    def test_colour_space_enum(self):
        for item in constants.ColourSpace:
            cs = colour.RGB_COLOURSPACES[item]
            self.assertNotEqual(cs, None)

    def test_patches(self):
        LEGACY_PATCH_ORDER = [
            constants.PATCHES.SLATE, constants.PATCHES.RED_PRIMARY_DESATURATED, constants.PATCHES.GREEN_PRIMARY_DESATURATED, constants.PATCHES.BLUE_PRIMARY_DESATURATED, constants.PATCHES.GREY_18_PERCENT,
            constants.PATCHES.RED_PRIMARY, constants.PATCHES.GREEN_PRIMARY, constants.PATCHES.BLUE_PRIMARY, constants.PATCHES.MAX_WHITE, constants.PATCHES.MACBETH, constants.PATCHES.SATURATION_RAMP,
            constants.PATCHES.DISTORT_AND_ROI, constants.PATCHES.FLAT_FIELD, constants.PATCHES.EOTF_RAMPS, constants.PATCHES.END_SLATE
        ]

        for patch, legacy_patch in zip(constants.PATCHES.patch_order(), LEGACY_PATCH_ORDER):
            self.assertEqual(patch, legacy_patch)

    def test_cat(self):
        self.assertTrue(constants.CAT.CAT_NONE in constants.CAT.all_with_none())
        self.assertFalse(constants.CAT.CAT_NONE in constants.CAT.all())
