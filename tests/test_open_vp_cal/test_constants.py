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

        for patch, legacy_patch in zip(constants.PATCHES.get_patch_order(), LEGACY_PATCH_ORDER):
            self.assertEqual(patch, legacy_patch)

    def test_cat(self):
        self.assertTrue(constants.CAT.CAT_NONE in constants.CAT.get_all_with_none())
        self.assertFalse(constants.CAT.CAT_NONE in constants.CAT.get_all())

    def test_cached_list(self):
        if hasattr(constants.ProjectSettingsKeys, '_list_all_cache'):
            delattr(constants.ProjectSettingsKeys, '_list_all_cache')
        if hasattr(constants.FrameRates, '_list_all_cache'):
            delattr(constants.FrameRates, '_list_all_cache')
        if hasattr(constants.LedWallSettingsKeys, '_list_all_cache'):
            delattr(constants.LedWallSettingsKeys, '_list_all_cache')
        if hasattr(constants.PATCHES, '_list_all_cache'):
            delattr(constants.PATCHES, '_list_all_cache')
        if hasattr(constants.CAT, '_list_all_cache'):
            delattr(constants.CAT, '_list_all_cache')
        if hasattr(constants.ColourSpace, '_list_all_cache'):
            delattr(constants.ColourSpace, '_list_all_cache')
        if hasattr(constants.CameraColourSpace, '_list_all_cache'):
            delattr(constants.CameraColourSpace, '_list_all_cache')
        if hasattr(constants.EOTF, '_list_all_cache'):
            delattr(constants.EOTF, '_list_all_cache')
        if hasattr(constants.CalculationOrder, '_list_all_cache'):
            delattr(constants.CalculationOrder, '_list_all_cache')
        if hasattr(constants.FileFormats, '_all_read_cache'):
            delattr(constants.FileFormats, '_all_read_cache')
        if hasattr(constants.FileFormats, '_all_write_cache'):
            delattr(constants.FileFormats, '_all_write_cache')
        if hasattr(constants.FileFormats, '_all_convert_cache'):
            delattr(constants.FileFormats, '_all_convert_cache')

        self.assertFalse(hasattr(constants.ProjectSettingsKeys, '_list_all_cache'))
        self.assertEqual(constants.ProjectSettingsKeys.get_all(), constants.ProjectSettingsKeys.get_all())
        self.assertTrue(hasattr(constants.ProjectSettingsKeys, '_list_all_cache'))

        self.assertFalse(hasattr(constants.FrameRates, '_list_all_cache'))
        self.assertEqual(constants.FrameRates.get_all(), constants.FrameRates.get_all())
        self.assertTrue(hasattr(constants.FrameRates, '_list_all_cache'))

        self.assertFalse(hasattr(constants.LedWallSettingsKeys, '_list_all_cache'))
        self.assertEqual(constants.LedWallSettingsKeys.get_all(), constants.LedWallSettingsKeys.get_all())
        self.assertTrue(hasattr(constants.LedWallSettingsKeys, '_list_all_cache'))
    
        self.assertFalse(hasattr(constants.PATCHES, '_list_all_cache'))
        self.assertEqual(constants.PATCHES.get_patch_order(), constants.PATCHES.get_patch_order())
        self.assertTrue(hasattr(constants.PATCHES, '_list_all_cache'))

        self.assertFalse(hasattr(constants.CAT, '_list_all_cache'))
        self.assertEqual(constants.CAT.get_all_with_none(), constants.CAT.get_all_with_none())
        self.assertEqual(constants.CAT.get_all(), constants.CAT.get_all())
        self.assertTrue(hasattr(constants.CAT, '_list_all_cache'))
    
        self.assertFalse(hasattr(constants.ColourSpace, '_list_all_cache'))
        self.assertEqual(constants.ColourSpace.get_all(), constants.ColourSpace.get_all())
        self.assertTrue(hasattr(constants.ColourSpace, '_list_all_cache'))

        self.assertFalse(hasattr(constants.CameraColourSpace, '_list_all_cache'))
        self.assertEqual(constants.CameraColourSpace.get_all(), constants.CameraColourSpace.get_all())
        self.assertTrue(hasattr(constants.CameraColourSpace, '_list_all_cache'))

        self.assertFalse(hasattr(constants.EOTF, '_list_all_cache'))
        self.assertEqual(constants.EOTF.get_all(), constants.EOTF.get_all())
        self.assertTrue(hasattr(constants.EOTF, '_list_all_cache'))

        self.assertFalse(hasattr(constants.CalculationOrder, '_list_all_cache'))
        self.assertEqual(constants.CalculationOrder.get_all(), constants.CalculationOrder.get_all())
        self.assertTrue(hasattr(constants.CalculationOrder, '_list_all_cache'))

        self.assertFalse(hasattr(constants.FileFormats, '_all_read_cache'))
        self.assertEqual(constants.FileFormats.get_all_read(), constants.FileFormats.get_all_read())
        self.assertTrue(hasattr(constants.FileFormats, '_all_read_cache'))

        self.assertFalse(hasattr(constants.FileFormats, '_all_write_cache'))
        self.assertEqual(constants.FileFormats.get_all_write(), constants.FileFormats.get_all_write())
        self.assertTrue(hasattr(constants.FileFormats, '_all_write_cache'))

        self.assertFalse(hasattr(constants.FileFormats, '_all_convert_cache'))
        self.assertEqual(constants.FileFormats.get_all_convert(), constants.FileFormats.get_all_convert())
        self.assertTrue(hasattr(constants.FileFormats, '_all_convert_cache'))
