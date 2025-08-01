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
import json
from typing import List
from open_vp_cal.framework.identify_separation import SeparationResults
from open_vp_cal.led_wall_settings import LedWallSettings, LedWallSettingsBaseModel, ProcessingResults
from open_vp_cal.core import constants

from test_utils import TestBase


def upgrade_legacy_roi(roi:List[int]) -> List[List[int]]:
    """
    Upgrade logic to convert roi from v1.x to v2.x.
    This was directly copied from <test_utils.recalc_old_roi>
    """
    if not roi:
        return []
    left, right, top, bottom = roi
    top_left = [left, top]
    top_right = [right, top]
    bottom_right = [right, bottom]
    bottom_left = [left, bottom]
    return [top_left, top_right, bottom_right, bottom_left]


class TestLedWallSettings(TestBase):

    def setUp(self):
        """Called before every test case."""
        super().setUp()
        self.wall = LedWallSettings(self.project_settings, name="TestWall")
        self.json_path = "test.json"

        self.sample = {
            constants.LedWallSettingsKeys.NAME: "Wall1",
            constants.LedWallSettingsKeys.ENABLE_EOTF_CORRECTION: True,
            constants.LedWallSettingsKeys.ENABLE_GAMUT_COMPRESSION: True,
            constants.LedWallSettingsKeys.AUTO_WB_SOURCE: True,
            constants.LedWallSettingsKeys.INPUT_SEQUENCE_FOLDER: "filepath",
            constants.LedWallSettingsKeys.CALCULATION_ORDER: constants.CalculationOrder.CO_CS_EOTF,
            constants.LedWallSettingsKeys.PRIMARIES_SATURATION: 0.7,
            constants.LedWallSettingsKeys.INPUT_PLATE_GAMUT: constants.ColourSpace.CS_ACES,
            constants.LedWallSettingsKeys.NUM_GREY_PATCHES: 30,
            constants.LedWallSettingsKeys.REFERENCE_TO_TARGET_CAT: constants.CAT.CAT_CAT02,
            constants.LedWallSettingsKeys.ROI: [342, 685, 119, 470],
            constants.LedWallSettingsKeys.SHADOW_ROLLOFF: 0.008,
            constants.LedWallSettingsKeys.TARGET_MAX_LUM_NITS: 1000,
            constants.LedWallSettingsKeys.TARGET_GAMUT: constants.ColourSpace.CS_BT2020,
            constants.LedWallSettingsKeys.TARGET_EOTF: constants.EOTF.EOTF_ST2084,
            constants.LedWallSettingsKeys.TARGET_TO_SCREEN_CAT: constants.CAT.CAT_CAT02,
            constants.LedWallSettingsKeys.NATIVE_CAMERA_GAMUT: constants.CameraColourSpace.RED_WIDE_GAMUT,
            constants.LedWallSettingsKeys.MATCH_REFERENCE_WALL: False,
            constants.LedWallSettingsKeys.REFERENCE_WALL: "",
            constants.LedWallSettingsKeys.USE_WHITE_POINT_OFFSET: False,
            constants.LedWallSettingsKeys.WHITE_POINT_OFFSET_SOURCE: "",
            constants.LedWallSettingsKeys.IS_VERIFICATION_WALL: False,
            constants.LedWallSettingsKeys.VERIFICATION_WALL: "",
            constants.LedWallSettingsKeys.AVOID_CLIPPING: True
        }

        self.sample_expected = self.sample.copy()
        self.sample_expected[constants.LedWallSettingsKeys.ROI] = upgrade_legacy_roi(
            self.sample_expected[constants.LedWallSettingsKeys.ROI])

        self.legacy_default = {
            constants.LedWallSettingsKeys.NAME: "Wall1",
            constants.LedWallSettingsKeys.ENABLE_EOTF_CORRECTION: True,
            constants.LedWallSettingsKeys.ENABLE_GAMUT_COMPRESSION: True,
            constants.LedWallSettingsKeys.AUTO_WB_SOURCE: False,
            constants.LedWallSettingsKeys.INPUT_SEQUENCE_FOLDER: '',
            constants.LedWallSettingsKeys.NUM_GREY_PATCHES: 30,
            constants.LedWallSettingsKeys.PRIMARIES_SATURATION: 0.7,
            constants.LedWallSettingsKeys.CALCULATION_ORDER: constants.CalculationOrder.default(),
            constants.LedWallSettingsKeys.INPUT_PLATE_GAMUT: constants.ColourSpace.default_ref(),
            constants.LedWallSettingsKeys.NATIVE_CAMERA_GAMUT: constants.CameraColourSpace.default(),
            constants.LedWallSettingsKeys.REFERENCE_TO_TARGET_CAT: constants.CAT.CAT_BRADFORD,
            constants.LedWallSettingsKeys.ROI: [],
            constants.LedWallSettingsKeys.SHADOW_ROLLOFF: 0.008,
            constants.LedWallSettingsKeys.TARGET_MAX_LUM_NITS: 1000,
            constants.LedWallSettingsKeys.TARGET_GAMUT: constants.ColourSpace.default_target(),
            constants.LedWallSettingsKeys.TARGET_EOTF: constants.EOTF.default(),
            constants.LedWallSettingsKeys.TARGET_TO_SCREEN_CAT: constants.CAT.CAT_NONE,
            constants.LedWallSettingsKeys.MATCH_REFERENCE_WALL: False,
            constants.LedWallSettingsKeys.REFERENCE_WALL: "",
            constants.LedWallSettingsKeys.USE_WHITE_POINT_OFFSET: False,
            constants.LedWallSettingsKeys.WHITE_POINT_OFFSET_SOURCE: "",
            constants.LedWallSettingsKeys.IS_VERIFICATION_WALL: False,
            constants.LedWallSettingsKeys.VERIFICATION_WALL: "",
            constants.LedWallSettingsKeys.AVOID_CLIPPING: False
        }

    def tearDown(self):
        """Called after every test case."""
        if os.path.exists(self.json_path):
            os.remove(self.json_path)

    def test_default_values(self):
        # Test for refactoring
        # Check the number of legacy fields is the same as the number of fields in the new model
        # We can remove this test once we add more fields to the new model in future.
        self.assertEqual(len(self.legacy_default), len(LedWallSettingsBaseModel.model_fields))

        # Test for refactoring
        # Check the default values are the same as the legacy default values
        # We can remove this test once we update the default values in future.
        newWall: LedWallSettings = LedWallSettings(self.project_settings)
        new_default_values = newWall._led_settings
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.NAME], new_default_values.name)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.AVOID_CLIPPING], new_default_values.avoid_clipping)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.ENABLE_EOTF_CORRECTION], new_default_values.enable_eotf_correction)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.ENABLE_GAMUT_COMPRESSION], new_default_values.enable_gamut_compression)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.AUTO_WB_SOURCE], new_default_values.auto_wb_source)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.INPUT_SEQUENCE_FOLDER], new_default_values.input_sequence_folder)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.NUM_GREY_PATCHES], new_default_values.num_grey_patches)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.PRIMARIES_SATURATION], new_default_values.primaries_saturation)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.CALCULATION_ORDER], new_default_values.calculation_order)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.INPUT_PLATE_GAMUT], new_default_values.input_plate_gamut)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.NATIVE_CAMERA_GAMUT], new_default_values.native_camera_gamut)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.REFERENCE_TO_TARGET_CAT], new_default_values.reference_to_target_cat)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.ROI], new_default_values.roi)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.SHADOW_ROLLOFF], new_default_values.shadow_rolloff)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.TARGET_MAX_LUM_NITS], new_default_values.target_max_lum_nits)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.TARGET_GAMUT], new_default_values.target_gamut)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.TARGET_EOTF], new_default_values.target_eotf)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.TARGET_TO_SCREEN_CAT], new_default_values.target_to_screen_cat)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.MATCH_REFERENCE_WALL], new_default_values.match_reference_wall)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.REFERENCE_WALL], new_default_values.reference_wall)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.USE_WHITE_POINT_OFFSET], new_default_values.use_white_point_offset)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.WHITE_POINT_OFFSET_SOURCE], new_default_values.white_point_offset_source)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.IS_VERIFICATION_WALL], new_default_values.is_verification_wall)
        self.assertEqual(self.legacy_default[constants.LedWallSettingsKeys.VERIFICATION_WALL], new_default_values.verification_wall)

    def test_reset_defaults(self):
        self.wall.use_white_point_offset = True
        self.assertEqual(self.wall.use_white_point_offset, True)
        self.assertEqual(self.wall._led_settings.use_white_point_offset, True)

        self.wall.reset_defaults()
        self.assertEqual(self.wall.use_white_point_offset, False)
        self.assertEqual(self.wall._led_settings.use_white_point_offset, False)
        self.assertEqual(self.wall._led_settings, LedWallSettingsBaseModel(name=self.wall.name))

    def test_clear(self):
        self.wall.roi = upgrade_legacy_roi([1, 2, 3, 4])
        self.wall.processing_results.sample_buffers = ['dummy']  # Overwrite for test
        self.wall.separation_results = SeparationResults()
        self.wall.clear()
        self.assertEqual(self.wall.roi, [])
        self.assertEqual(self.wall._led_settings.roi, [])
        self.assertEqual(self.wall.processing_results.__dict__, ProcessingResults().__dict__)
        self.assertIsNone(self.wall.separation_results)

    def test_clear_led_settings(self):
        self.wall.target_eotf = constants.EOTF.EOTF_SRGB
        self.wall.clear_led_settings()
        self.assertEqual(self.wall._led_settings, LedWallSettingsBaseModel(name=self.wall.name))

    def test_fields_all_included_in_test(self):
        sample_keys = list(self.sample.keys())
        sample_keys.sort()

        constants_all = constants.LedWallSettingsKeys.all().copy()
        constants_all.sort()
        self.assertEqual(sample_keys, constants_all)

        default_keys = list(LedWallSettingsBaseModel.model_fields.keys())
        default_keys.sort()
        self.assertEqual(sample_keys, default_keys)

    def test_led_wall_settings_keys(self):
        constants_all = constants.LedWallSettingsKeys.all().copy()
        constants_all.sort()
        led_settings_keys = list(LedWallSettingsBaseModel.model_fields.keys())
        led_settings_keys.sort()
        self.assertEqual(constants_all, led_settings_keys, "LedWallSettingsKeys should reflect all fields in the model. Add new keys to LedWallSettingsKeys.")

    def test_initialization(self):
        self.assertEqual(self.wall.name, "TestWall")
        self.assertEqual(self.wall._led_settings.name, "TestWall")
        self.assertEqual(self.wall._led_settings.avoid_clipping, False)
        self.assertEqual(self.wall._led_settings.enable_eotf_correction, True)
        self.assertEqual(self.wall._led_settings.enable_gamut_compression, True)
        self.assertEqual(self.wall._led_settings.auto_wb_source, False)
        self.assertEqual(self.wall._led_settings.input_sequence_folder, "")
        self.assertEqual(self.wall._led_settings.num_grey_patches, 30)
        self.assertEqual(self.wall._led_settings.primaries_saturation, 0.7)
        self.assertEqual(self.wall._led_settings.calculation_order, constants.CalculationOrder(constants.CalculationOrder.default()))
        self.assertEqual(self.wall._led_settings.input_plate_gamut, constants.ColourSpace(constants.ColourSpace.default_ref()))
        self.assertEqual(self.wall._led_settings.native_camera_gamut, constants.CameraColourSpace(constants.CameraColourSpace.default()))
        self.assertEqual(self.wall._led_settings.reference_to_target_cat, constants.CAT(constants.CAT.CAT_BRADFORD))
        self.assertEqual(self.wall._led_settings.roi, [])
        self.assertEqual(self.wall._led_settings.shadow_rolloff, 0.008)
        self.assertEqual(self.wall._led_settings.target_max_lum_nits, 1000)
        self.assertEqual(self.wall._led_settings.target_gamut, constants.LedColourSpace(constants.LedColourSpace.default_target()))
        self.assertEqual(self.wall._led_settings.target_eotf, constants.EOTF(constants.EOTF.default()))
        self.assertEqual(self.wall._led_settings.target_to_screen_cat, constants.CAT.CAT_NONE)
        self.assertEqual(self.wall._led_settings.match_reference_wall, False)
        self.assertEqual(self.wall._led_settings.reference_wall, "")
        self.assertEqual(self.wall._led_settings.white_point_offset_source, "")
        self.assertEqual(self.wall._led_settings.use_white_point_offset, False)
        self.assertEqual(self.wall._led_settings.is_verification_wall, False)
        self.assertEqual(self.wall._led_settings.verification_wall, "")

    def test_name(self):
        self.wall.name = "NewName"
        self.assertEqual(self.wall.name, "NewName")
        self.assertEqual(self.wall._led_settings.name, "NewName")

    def test_avoid_clipping(self):
        self.wall.avoid_clipping = True
        self.assertEqual(self.wall.avoid_clipping, True)
        self.assertEqual(self.wall._led_settings.avoid_clipping, True)

    # <test_custom_primaries> is removed

    def test_enable_eotf_correction(self):
        self.wall.enable_eotf_correction = False
        self.assertEqual(self.wall.enable_eotf_correction, False)
        self.assertEqual(self.wall._led_settings.enable_eotf_correction, False)

    def test_enable_gamut_compression(self):
        self.wall.enable_gamut_compression = False
        self.assertEqual(self.wall.enable_gamut_compression, False)
        self.assertEqual(self.wall._led_settings.enable_gamut_compression, False)

    def test_auto_wb_source(self):
        self.wall.auto_wb_source = False
        self.assertEqual(self.wall.auto_wb_source, False)
        self.assertEqual(self.wall._led_settings.auto_wb_source, False)

    def test_input_sequence_folder(self):
        self.wall.input_sequence_folder = "/new/path"
        self.assertEqual(self.wall.input_sequence_folder, "/new/path")
        self.assertEqual(self.wall._led_settings.input_sequence_folder, "/new/path")

    def test_calculation_order(self):
        self.wall.calculation_order = constants.CalculationOrder.CO_EOTF_CS
        self.assertEqual(self.wall.calculation_order, constants.CalculationOrder.CO_EOTF_CS)
        self.assertEqual(self.wall._led_settings.calculation_order, constants.CalculationOrder.CO_EOTF_CS)

    def test_primaries_saturation(self):
        self.wall.primaries_saturation = 0.1
        self.assertAlmostEqual(self.wall.primaries_saturation, 0.1)
        self.assertAlmostEqual(self.wall._led_settings.primaries_saturation, 0.1)

    def test_input_plate_gamut(self):
        self.wall.input_plate_gamut = constants.ColourSpace.CS_SRGB
        self.assertEqual(self.wall.input_plate_gamut, constants.ColourSpace.CS_SRGB)
        self.assertEqual(self.wall._led_settings.input_plate_gamut, constants.ColourSpace.CS_SRGB)

    def test_native_camera_gamut(self):
        self.wall.native_camera_gamut = constants.CameraColourSpace.ARRI_WIDE_GAMUT_3
        self.assertEqual(self.wall.native_camera_gamut, constants.CameraColourSpace.ARRI_WIDE_GAMUT_3)
        self.assertEqual(self.wall._led_settings.native_camera_gamut, constants.CameraColourSpace.ARRI_WIDE_GAMUT_3)

    def test_num_grey_patches(self):
        self.wall.num_grey_patches = 25
        self.assertEqual(self.wall.num_grey_patches, 25)
        self.assertEqual(self.wall._led_settings.num_grey_patches, 25)

    def test_reference_to_target_cat(self):
        self.wall.reference_to_target_cat = constants.CAT.CAT_BRADFORD
        self.assertEqual(self.wall.reference_to_target_cat, constants.CAT.CAT_BRADFORD)
        self.assertEqual(self.wall._led_settings.reference_to_target_cat, constants.CAT.CAT_BRADFORD)

    # <test_saturation_cat> is removed

    def test_roi(self):
        legacy_roi = [1, 2, 3, 4]
        self.assertEqual(upgrade_legacy_roi(legacy_roi),
            LedWallSettingsBaseModel.upgrade_roi(legacy_roi))

        roi = upgrade_legacy_roi(legacy_roi)
        self.wall.roi = roi
        self.assertEqual(self.wall.roi, roi)
        self.assertEqual(self.wall._led_settings.roi, roi)

    def test_empty_roi(self):
        self.wall.roi = []
        self.assertFalse(self.wall.roi, "Empty roi should return False")

    def test_shadow_rolloff(self):
        self.wall.shadow_rolloff = 0.1
        self.assertEqual(self.wall.shadow_rolloff, 0.1)
        self.assertEqual(self.wall._led_settings.shadow_rolloff, 0.1)

    def test_target_gamut(self):
        self.wall.target_gamut = constants.ColourSpace.CS_BT2020
        self.assertEqual(self.wall.target_gamut, constants.ColourSpace.CS_BT2020)
        self.assertEqual(self.wall._led_settings.target_gamut, constants.ColourSpace.CS_BT2020)

    def test_target_eotf(self):
        self.wall.target_eotf = constants.EOTF.EOTF_ST2084
        self.wall.target_max_lum_nits = 30
        self.assertEqual(self.wall.target_eotf, constants.EOTF.EOTF_ST2084)
        self.assertEqual(self.wall._led_settings.target_eotf, constants.EOTF.EOTF_ST2084)
        self.assertEqual(self.wall.target_max_lum_nits, 30)
        self.assertEqual(self.wall._led_settings.target_max_lum_nits, 30)

        # target_max_lum_nits should be set to <TARGET_MAX_LUM_NITS_NONE_PQ> when target_eotf is not ST2084
        self.wall.target_eotf = constants.EOTF.EOTF_BT1886
        self.assertEqual(self.wall.target_eotf, constants.EOTF.EOTF_BT1886)
        self.assertEqual(self.wall._led_settings.target_eotf, constants.EOTF.EOTF_BT1886)
        self.assertEqual(self.wall.target_max_lum_nits, constants.TARGET_MAX_LUM_NITS_NONE_PQ)
        self.assertEqual(self.wall._led_settings.target_max_lum_nits, constants.TARGET_MAX_LUM_NITS_NONE_PQ)

    def test_target_max_lum_nits(self):
        self.wall.target_eotf = constants.EOTF.EOTF_ST2084
        self.wall.target_max_lum_nits = 2000
        self.assertEqual(self.wall.target_max_lum_nits, 2000)
        self.assertEqual(self.wall._led_settings.target_max_lum_nits, 2000)

        # target_max_lum_nits should be set to <TARGET_MAX_LUM_NITS_NONE_PQ> when target_eotf is not ST2084
        self.wall.target_eotf = constants.EOTF.EOTF_BT1886
        self.wall.target_max_lum_nits = 2000
        self.assertEqual(self.wall.target_max_lum_nits, constants.TARGET_MAX_LUM_NITS_NONE_PQ)
        self.assertEqual(self.wall._led_settings.target_max_lum_nits, constants.TARGET_MAX_LUM_NITS_NONE_PQ)

    def test_target_to_screen_cat(self):
        self.wall.target_to_screen_cat = constants.CAT.CAT_BIANCO2010
        self.assertEqual(self.wall.target_to_screen_cat, constants.CAT.CAT_BIANCO2010)
        self.assertEqual(self.wall._led_settings.target_to_screen_cat, constants.CAT.CAT_BIANCO2010)

    # <test_wall_calibration_file> is removed

    def test_match_reference_wall(self):
        self.wall.match_reference_wall = True
        self.assertEqual(self.wall.match_reference_wall, True)
        self.assertEqual(self.wall._led_settings.match_reference_wall, True)

    def test_reference_wall(self):
        # Check we can set a new wall by instance
        new_wall = self.project_settings.add_led_wall("NewWall")
        self.wall.reference_wall = new_wall
        self.assertEqual(self.wall.reference_wall, new_wall.name)
        self.assertEqual(self.wall.reference_wall_as_wall.name, new_wall.name) # type: ignore
        self.assertEqual(self.wall._led_settings.reference_wall, new_wall.name)

        # Check we can set a new wall by name
        another_wall = self.project_settings.add_led_wall("AnotherWall")
        self.wall.reference_wall = another_wall.name
        self.assertEqual(self.wall.reference_wall, another_wall.name)
        self.assertEqual(self.wall.reference_wall_as_wall.name, another_wall.name) # type: ignore
        self.assertEqual(self.wall._led_settings.reference_wall, another_wall.name)

        # Setting reference_wall to itself should raise ValueError (by instance)
        with self.assertRaises(ValueError):
            self.wall.reference_wall = self.wall
        # Setting reference_wall to itself should raise ValueError (by name)
        with self.assertRaises(ValueError):
            self.wall.reference_wall = self.wall.name

        # Setting reference_wall to a non-existent wall should raise ValueError (by instance)
        with self.assertRaises(ValueError):
            self.wall.reference_wall = LedWallSettings(self.project_settings, "NonExistentWall")

        # Setting reference_wall to a non-existent wall should raise ValueError (by name)
        with self.assertRaises(ValueError):
            self.wall.reference_wall = "NonExistentWall"

    def test_reference_wall_as_wall_none(self):
        """Test that reference_wall_as_wall returns None when no reference wall is set."""
        self.assertIsNone(self.wall.reference_wall_as_wall)
        with self.assertRaises(ValueError):
            self.wall.reference_wall = "NonExistentWall"
        self.assertIsNone(self.wall.reference_wall_as_wall)

    def test_remove_reference_wall(self):
        new_wall = self.project_settings.add_led_wall("NewWall")
        new_wall2 = self.project_settings.add_led_wall("NewWall2")

        new_wall.reference_wall = new_wall2.name
        new_wall.match_reference_wall = True

        self.project_settings.remove_led_wall(new_wall2.name)
        self.assertEqual(new_wall.reference_wall, "")
        self.assertEqual(new_wall.match_reference_wall, False)

    def test_use_white_point_offset(self):
        self.wall.use_white_point_offset = True
        self.assertEqual(self.wall.use_white_point_offset, True)
        self.assertEqual(self.wall._led_settings.use_white_point_offset, True)

    def test_white_point_offset_source(self):
        self.wall.white_point_offset_source = "new_file.exr"
        self.assertEqual(self.wall.white_point_offset_source, "new_file.exr")
        self.assertEqual(self.wall._led_settings.white_point_offset_source, "new_file.exr")

    def test_verification_wall(self):
        new_wall = self.project_settings.add_led_wall("NewWall")
        verification_wall = self.project_settings.add_verification_wall(new_wall.name)
        self.assertEqual(verification_wall.is_verification_wall, True)
        self.assertEqual(verification_wall._led_settings.is_verification_wall, True)
        self.assertEqual(new_wall.is_verification_wall, False)
        self.assertEqual(new_wall._led_settings.is_verification_wall, False)

        self.assertEqual(new_wall.verification_wall, verification_wall.name)
        self.assertEqual(new_wall._led_settings.verification_wall, verification_wall.name)
        self.assertEqual(verification_wall.verification_wall, new_wall.name)
        self.assertEqual(verification_wall._led_settings.verification_wall, new_wall.name)

        # Test That Changing A Param On The Main Wall Changes On The Verification Wall
        new_wall.input_plate_gamut = constants.ColourSpace.CS_SRGB
        self.assertEqual(verification_wall.input_plate_gamut, constants.ColourSpace.CS_SRGB)

        # Test That Changing A Param On The Verification Wall Changes Neither
        verification_wall.input_plate_gamut = constants.ColourSpace.CS_P3
        self.assertEqual(verification_wall.input_plate_gamut, constants.ColourSpace.CS_SRGB)
        self.assertEqual(new_wall.input_plate_gamut, constants.ColourSpace.CS_SRGB)
        self.assertEqual(new_wall._led_settings.input_plate_gamut, constants.ColourSpace.CS_SRGB)

        new_wall.target_eotf = constants.EOTF.EOTF_GAMMA_1_8
        self.assertEqual(verification_wall.target_eotf, constants.EOTF.EOTF_GAMMA_1_8)

        new_wall.reference_wall = self.led_wall
        self.assertEqual(verification_wall.reference_wall, self.led_wall.name)

        # Ensure we set back to 2084 so that we avoid the fixing of the peak lum being set to 100
        new_wall.target_eotf = constants.EOTF.EOTF_ST2084
        other_linked_properties = [
            constants.LedWallSettingsKeys.ENABLE_EOTF_CORRECTION,
            constants.LedWallSettingsKeys.ENABLE_GAMUT_COMPRESSION,
            constants.LedWallSettingsKeys.AUTO_WB_SOURCE,
            constants.LedWallSettingsKeys.CALCULATION_ORDER,
            constants.LedWallSettingsKeys.PRIMARIES_SATURATION,
            constants.LedWallSettingsKeys.INPUT_PLATE_GAMUT,
            constants.LedWallSettingsKeys.NATIVE_CAMERA_GAMUT,
            constants.LedWallSettingsKeys.NUM_GREY_PATCHES,
            constants.LedWallSettingsKeys.REFERENCE_TO_TARGET_CAT,
            constants.LedWallSettingsKeys.SHADOW_ROLLOFF,
            constants.LedWallSettingsKeys.TARGET_GAMUT,
            constants.LedWallSettingsKeys.TARGET_MAX_LUM_NITS,
            constants.LedWallSettingsKeys.TARGET_TO_SCREEN_CAT,
            constants.LedWallSettingsKeys.MATCH_REFERENCE_WALL,
            constants.LedWallSettingsKeys.USE_WHITE_POINT_OFFSET,
            constants.LedWallSettingsKeys.WHITE_POINT_OFFSET_SOURCE]

        # We test all the other linked params with false data
        for count, linked_prop in enumerate(other_linked_properties):
            setattr(new_wall, linked_prop, count)
            self.assertEqual(getattr(verification_wall, linked_prop), count)

    def test_add_verification_wall_to_verification_wall(self):
        new_wall = self.project_settings.add_led_wall("NewWall")
        verification_wall = self.project_settings.add_verification_wall(new_wall.name)
        with self.assertRaises(ValueError):
            self.project_settings.add_verification_wall(verification_wall.name)

    def test_remove_verification_wall(self):
        new_wall = self.project_settings.add_led_wall("NewWall")
        verification_wall = self.project_settings.add_verification_wall(new_wall.name)

        self.project_settings.remove_led_wall(verification_wall.name)
        self.assertEqual(new_wall.verification_wall, "")

    def test_remove_verification_wall2(self):
        new_wall = self.project_settings.add_led_wall("NewWall")
        verification_wall = self.project_settings.add_verification_wall(new_wall.name)

        self.project_settings.remove_led_wall(new_wall.name)
        self.assertEqual(verification_wall.verification_wall, "")

    def test_set_property_on_verification_wall_does_not_propagate(self):
        new_wall = self.project_settings.add_led_wall("NewWall")
        verification_wall = self.project_settings.add_verification_wall(new_wall.name)
        verification_wall.input_plate_gamut = constants.ColourSpace.CS_SRGB
        self.assertNotEqual(new_wall.input_plate_gamut, None)

    def test_get_property_on_verification_wall_raises_if_parent_removed(self):
        new_wall = self.project_settings.add_led_wall("NewWall")
        verification_wall = self.project_settings.add_verification_wall(new_wall.name)
        self.project_settings.remove_led_wall(new_wall.name)
        with self.assertRaises(ValueError):
            _ = verification_wall._get_property(constants.LedWallSettingsKeys.INPUT_PLATE_GAMUT)


    def test_verification_wall_edge_cases(self):
        """Test edge cases for verification wall functionality."""
        new_wall = self.project_settings.add_led_wall("NewWall")
        verification_wall = self.project_settings.add_verification_wall(new_wall.name)

        # Setting a property on verification wall should not affect main wall
        verification_wall.input_plate_gamut = constants.ColourSpace.CS_SRGB
        self.assertNotEqual(new_wall.input_plate_gamut, constants.ColourSpace.CS_SRGB)  # Should not change

        # Setting verification wall to itself should raise ValueError
        with self.assertRaises(ValueError):
            verification_wall.verification_wall = verification_wall

        # Setting reference wall to itself should raise ValueError
        with self.assertRaises(ValueError):
            new_wall.reference_wall = new_wall

        # Removing parent wall should clear verification wall link
        self.project_settings.remove_led_wall(new_wall.name)
        self.assertEqual(verification_wall.verification_wall, "")

    def test_verification_wall_as_wall_none(self):
        """Test that verification_wall_as_wall returns None when no verification wall is set."""
        self.assertIsNone(self.wall.verification_wall_as_wall)

        # Test with a non-existent verification wall name
        self.wall._led_settings.verification_wall = "NonExistentWall"
        with self.assertRaises(ValueError):
            _ = self.wall.verification_wall_as_wall

        # Test with empty string
        self.wall._led_settings.verification_wall = ""
        self.assertIsNone(self.wall.verification_wall_as_wall)

    def test_has_valid_white_balance_options(self):
        self.wall.auto_wb_source = True
        self.wall.match_reference_wall = False
        self.wall.use_white_point_offset = False
        self.assertTrue(self.wall.has_valid_white_balance_options())
        self.wall.match_reference_wall = True
        self.assertFalse(self.wall.has_valid_white_balance_options())
        self.wall.auto_wb_source = False
        self.assertTrue(self.wall.has_valid_white_balance_options())
        self.wall.use_white_point_offset = True
        self.assertFalse(self.wall.has_valid_white_balance_options())

    def test_json_conversion(self):
        with open(self.json_path, 'w', encoding="utf-8") as file:
            file.write(json.dumps(self.sample))

        new_wall2 = LedWallSettings.from_json_file(self.project_settings, self.json_path)
        for key in self.sample:
            self.assertEqual(getattr(new_wall2._led_settings, key), self.sample_expected[key])

    def test_from_json_string(self):
        json_str = json.dumps(self.sample)

        new_wall = LedWallSettings.from_json_string(self.project_settings, json_str)
        for key in self.sample:
            self.assertEqual(getattr(new_wall._led_settings, key), self.sample_expected[key])

    def test_from_dict(self):
        new_wall = LedWallSettings.from_dict(self.project_settings, self.sample)
        for key in self.sample:
            self.assertEqual(getattr(new_wall._led_settings, key), self.sample_expected[key])

    def test_to_dict(self):
        json_str = json.dumps(self.sample)
        new_wall = LedWallSettings.from_json_string(self.project_settings, json_str)
        dict = new_wall.to_dict()

        self.assertEqual(len(dict), len(self.sample))

        # Type of key changed from <constants.LedWallSettingsKeys> to <str>
        # Order of dict changed
        for key in self.sample:
            self.assertTrue(key in dict)
            self.assertEqual(dict[key], self.sample_expected[key])

    def test_to_json(self):
        """Test the to_json method saves the LED wall settings to a JSON file."""
        self.wall.name = "CustomWall"
        self.wall.avoid_clipping = True
        self.wall.enable_eotf_correction = False
        self.wall.target_max_lum_nits = 2000
        self.wall.input_sequence_folder = "/custom/path"
        self.wall.to_json(self.json_path)

        self.assertTrue(os.path.exists(self.json_path))

        with open(self.json_path, 'r', encoding='utf-8') as file:
            saved_data = json.load(file)

        self.assertEqual(saved_data[constants.LedWallSettingsKeys.NAME], "CustomWall")
        self.assertEqual(saved_data[constants.LedWallSettingsKeys.AVOID_CLIPPING], True)
        self.assertEqual(saved_data[constants.LedWallSettingsKeys.ENABLE_EOTF_CORRECTION], False)
        self.assertEqual(saved_data[constants.LedWallSettingsKeys.TARGET_MAX_LUM_NITS], 2000)
        self.assertEqual(saved_data[constants.LedWallSettingsKeys.INPUT_SEQUENCE_FOLDER], "/custom/path")

    def test_sequence_loader(self):
        """Test the sequence_loader property returns a valid SequenceLoader instance with proper caching behavior."""
        # Test that sequence_loader returns a valid instance
        loader = self.wall.sequence_loader
        self.assertIsNotNone(loader)
        self.assertIsInstance(loader, self.wall._sequence_loader_class)

        # Test that it returns the same instance on subsequent calls (caching behavior)
        self.assertIs(loader, self.wall.sequence_loader)

        # Test that the loader is properly initialized with the wall settings
        self.assertEqual(loader.led_wall_settings, self.wall)

        # Test that the loader starts with default values
        self.assertEqual(loader.folder_path, None)
        self.assertEqual(loader.file_name, None)
        self.assertEqual(loader.padding, None)
        self.assertEqual(loader.file_type, constants.FileFormats.FF_EXR)
        self.assertEqual(loader.frames, [])
        self.assertEqual(loader._current_frame, -1)
        self.assertEqual(loader._start_frame, -1)
        self.assertEqual(loader._end_frame, -1)

    def test_sequence_loader_edge_cases(self):
        """Test sequence_loader behavior with edge cases and error conditions."""
        # Test that sequence_loader is properly reset when wall is cleared
        loader = self.wall.sequence_loader

        # Clear the wall settings
        self.wall.clear()

        # The sequence_loader should still be the same instance (cached)
        self.assertIs(loader, self.wall.sequence_loader)

        # But the loader should be reset internally
        self.assertEqual(loader.folder_path, None)
        self.assertEqual(loader.file_name, None)
        self.assertEqual(loader.frames, [])

        # Test that sequence_loader works with verification walls
        new_wall = self.project_settings.add_led_wall("NewWall")
        verification_wall = self.project_settings.add_verification_wall(new_wall.name)

        # Verification wall should have its own sequence loader
        verif_loader = verification_wall.sequence_loader
        self.assertIsNotNone(verif_loader)
        self.assertIsInstance(verif_loader, verification_wall._sequence_loader_class)
        self.assertEqual(verif_loader.led_wall_settings, verification_wall)

        # Test that different walls have different sequence loaders
        self.assertIsNot(loader, verif_loader)

    def test_roi_upgrade(self):
        led_wall = LedWallSettings.from_dict(self.project_settings, self.sample)
        self.assertEqual(led_wall._led_settings.roi, self.sample_expected[constants.LedWallSettingsKeys.ROI])

    def test_all_sample_project_json(self):
        for project_settings_path in self.get_all_test_project_settings_path():
            with open(project_settings_path, 'r', encoding='utf-8') as file:
                loaded_data:dict = json.load(file)
                led_walls = loaded_data[constants.OpenVPCalSettingsKeys.PROJECT_SETTINGS][constants.ProjectSettingsKeys.LED_WALLS]
                for led_wall in led_walls:
                    self.assertIsNotNone(led_wall)
                    # Check no throw
                    try:
                        led_wall_settings = LedWallSettings.from_dict(self.project_settings, led_wall)
                    except Exception as e:
                        self.fail(f"Failed to load LedWallSettings from {project_settings_path}: {e}")
                    self.assertIsInstance(led_wall_settings, LedWallSettings)
