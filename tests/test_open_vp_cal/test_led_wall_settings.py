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
from open_vp_cal.led_wall_settings import LedWallSettings
from open_vp_cal.core import constants

from test_utils import TestBase


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

    def tearDown(self):
        """Called after every test case."""
        if os.path.exists(self.json_path):
            os.remove(self.json_path)

    def test_fields_all_included_in_test(self):
        sample_keys = list(self.sample.keys())
        sample_keys.sort()

        constants_all = constants.LedWallSettingsKeys.all().copy()
        constants_all.sort()
        self.assertEqual(sample_keys, constants_all)

        default_keys = list(self.wall._default_led_settings.keys())
        default_keys.sort()
        self.assertEqual(sample_keys, default_keys)


    def test_initialization(self):
        self.assertEqual(self.wall.name, "TestWall")
        self.assertEqual(self.wall._led_settings['name'], "TestWall")
        self.assertEqual(self.wall._led_settings['calculation_order'], constants.CalculationOrder.CO_EOTF_CS)
        self.assertEqual(self.wall._led_settings['input_plate_gamut'], constants.ColourSpace.CS_ACES)

    def test_name(self):
        self.wall.name = "NewName"
        self.assertEqual(self.wall.name, "NewName")
        self.assertEqual(self.wall._led_settings['name'], "NewName")

    def test_custom_primaries(self):
        self.wall.custom_primaries = ([0.64, 0.33], "test")
        self.assertEqual(self.wall.custom_primaries, ([0.64, 0.33], "test"))

    def test_enable_eotf_correction(self):
        self.wall.enable_eotf_correction = False
        self.assertEqual(self.wall.enable_eotf_correction, False)

    def test_enable_gamut_compression(self):
        self.wall.enable_gamut_compression = False
        self.assertEqual(self.wall.enable_gamut_compression, False)

    def test_auto_wb_source(self):
        self.wall.auto_wb_source = False
        self.assertEqual(self.wall.auto_wb_source, False)

    def test_input_sequence_folder(self):
        self.wall.input_sequence_folder = "/new/path"
        self.assertEqual(self.wall.input_sequence_folder, "/new/path")

    def test_calculation_order(self):
        self.wall.calculation_order = constants.CalculationOrder.CO_EOTF_CS
        self.assertEqual(self.wall.calculation_order, constants.CalculationOrder.CO_EOTF_CS)

    def test_input_plate_gamut(self):
        self.wall.input_plate_gamut = constants.ColourSpace.CS_SRGB
        self.assertEqual(self.wall.input_plate_gamut, constants.ColourSpace.CS_SRGB)

    def test_reference_to_target_cat(self):
        self.wall.reference_to_target_cat = constants.CAT.CAT_BRADFORD
        self.assertEqual(self.wall.reference_to_target_cat, constants.CAT.CAT_BRADFORD)

    def test_roi(self):
        roi = [1, 2, 3, 4]
        self.wall.roi = roi
        self.assertEqual(self.wall.roi, roi)

    def test_saturation_cat(self):
        self.wall.saturation_cat = constants.CAT.CAT_BRADFORD
        self.assertEqual(self.wall.saturation_cat, constants.CAT.CAT_BRADFORD)

    def test_shadow_rolloff(self):
        self.wall.shadow_rolloff = 0.1
        self.assertEqual(self.wall.shadow_rolloff, 0.1)

    def test_target_gamut(self):
        self.wall.target_gamut = constants.ColourSpace.CS_BT2020
        self.assertEqual(self.wall.target_gamut, constants.ColourSpace.CS_BT2020)

    def test_target_eotf(self):
        self.wall.target_eotf = constants.EOTF.EOTF_BT1886
        self.assertEqual(self.wall.target_eotf, constants.EOTF.EOTF_BT1886)

    def test_target_max_lum_nits(self):
        self.wall.target_max_lum_nits = 2000
        self.assertEqual(self.wall.target_max_lum_nits, 2000)

    def test_wall_calibration_file(self):
        self.wall.wall_calibration_file = "new_file.txt"
        self.assertEqual(self.wall.wall_calibration_file, "new_file.txt")

    def test_clear_led_settings(self):
        self.wall.clear_led_settings()
        self.assertEqual(self.wall._led_settings, self.wall._default_led_settings)

    def test_match_reference_wall(self):
        self.wall.match_reference_wall = True
        self.assertEqual(self.wall.match_reference_wall, True)

    def test_use_external_white_point(self):
        self.wall.use_white_point_offset = True
        self.assertEqual(self.wall.use_white_point_offset, True)

    def test_external_white_point_file(self):
        self.wall.white_point_offset_source = "new_file.exr"
        self.assertEqual(self.wall.white_point_offset_source, "new_file.exr")


    def test_reference_wall(self):
        # Check we can set a new wall
        new_wall = self.project_settings.add_led_wall("NewWall")
        self.wall.reference_wall = new_wall
        self.assertEqual(self.wall.reference_wall, new_wall.name)
        self.assertEqual(self.wall.reference_wall_as_wall.name, new_wall.name)

        # Set we cant set ourselves as a reference
        self.assertRaises(ValueError, setattr, self.wall, constants.LedWallSettingsKeys.REFERENCE_WALL, self.wall)

    def test_json_conversion(self):
        with open(self.json_path, 'w', encoding="utf-8") as file:
            file.write(json.dumps(self.sample))

        new_wall = LedWallSettings.from_json_file(self.project_settings, self.json_path)
        for key in self.sample:
            self.assertEqual(getattr(new_wall, key), self.sample[key])

    def test_verification_wall(self):
        new_wall = self.project_settings.add_led_wall("NewWall")
        verification_wall = self.project_settings.add_verification_wall(new_wall.name)
        self.assertEqual(verification_wall.is_verification_wall, True)
        self.assertEqual(new_wall.is_verification_wall, False)
        self.assertEqual(new_wall.verification_wall, verification_wall.name)
        self.assertEqual(verification_wall.verification_wall, new_wall.name)

        # Test That Changing A Param On The Main Wall Changes On The Verification Wall
        new_wall.input_plate_gamut = constants.ColourSpace.CS_SRGB
        self.assertEqual(verification_wall.input_plate_gamut, constants.ColourSpace.CS_SRGB)

        # Test That Changing A Param On The Verification Wall Changes Neither
        verification_wall.input_plate_gamut = constants.ColourSpace.CS_SRGB
        self.assertEqual(verification_wall.input_plate_gamut, constants.ColourSpace.CS_SRGB)
        self.assertEqual(new_wall.input_plate_gamut, constants.ColourSpace.CS_SRGB)

        new_wall.target_eotf = constants.EOTF.EOTF_SRGB
        self.assertEqual(verification_wall.target_eotf, constants.EOTF.EOTF_SRGB)

        new_wall.reference_wall = self.led_wall
        self.assertEqual(verification_wall.reference_wall, self.led_wall.name)

        # Ensure we set back to 2084 so that we avoid the fixing of the peak lum being set to 100
        new_wall.target_eotf = constants.EOTF.EOTF_ST2084
        other_linked_properties = [
            "enable_eotf_correction",
            "enable_gamut_compression",
            "auto_wb_source",
            "calculation_order",
            "primaries_saturation",
            "input_plate_gamut",
            "native_camera_gamut",
            "num_grey_patches",
            "reference_to_target_cat",
            "shadow_rolloff",
            "target_gamut",
            "target_max_lum_nits",
            "target_to_screen_cat",
            "match_reference_wall",
            "use_white_point_offset",
            "white_point_offset_source"]

        # We test all the other linked params with false data
        for count, linked_prop in enumerate(other_linked_properties):
            print (linked_prop)
            setattr(new_wall, linked_prop, count)
            self.assertEqual(getattr(verification_wall, linked_prop), count)

    def test_add_verification_wall_to_verification_wall(self):
        new_wall = self.project_settings.add_led_wall("NewWall")
        verification_wall = self.project_settings.add_verification_wall(new_wall.name)
        self.assertRaises(ValueError, self.project_settings.add_verification_wall, verification_wall.name)

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

    def test_remove_reference_wall(self):
        new_wall = self.project_settings.add_led_wall("NewWall")
        new_wall2 = self.project_settings.add_led_wall("NewWall2")

        new_wall.reference_wall = new_wall2.name
        new_wall.match_reference_wall = True

        self.project_settings.remove_led_wall(new_wall2.name)
        self.assertEqual(new_wall.reference_wall, "")
        self.assertEqual(new_wall.match_reference_wall, False)

    def test_reset_defaults(self):
        self.wall.use_white_point_offset = True
        self.assertEqual(self.wall.use_white_point_offset, True)

        self.wall.reset_defaults()
        self.assertEqual(self.wall.use_white_point_offset, False)

        self.assertEqual(self.wall._default_led_settings, self.wall._led_settings)

