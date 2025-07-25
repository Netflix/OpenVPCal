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
import os
import copy
import tempfile
from pathlib import Path

import open_vp_cal
from open_vp_cal.led_wall_settings import LedWallSettings, LedWallSettingsModel
from open_vp_cal.project_settings import ProjectSettings, ProjectSettingsModel
from open_vp_cal.core import constants, utils
from test_utils import TestBase
from test_led_wall_settings import upgrade_legacy_roi

class TestProjectSettings(TestBase):
    """Test cases for ProjectSettings."""

    def setUp(self):
        """Set up test case."""
        super(TestProjectSettings, self).setUp()
        self.settings = ProjectSettings()
        self.test_json_path = "test_project_settings.json"
        self.test_settings = {
            constants.OpenVPCalSettingsKeys.VERSION: open_vp_cal.__version__,
            constants.OpenVPCalSettingsKeys.PROJECT_SETTINGS:
                {
                    constants.ProjectSettingsKeys.PROJECT_ID: "123456",
                    constants.ProjectSettingsKeys.LUT_SIZE: 66,
                    constants.ProjectSettingsKeys.CONTENT_MAX_LUM: constants.PQ.PQ_MAX_NITS,
                    constants.ProjectSettingsKeys.FILE_FORMAT: constants.FileFormats.FF_EXR,
                    constants.ProjectSettingsKeys.RESOLUTION_WIDTH: 3840,
                    constants.ProjectSettingsKeys.RESOLUTION_HEIGHT: 2160,
                    constants.ProjectSettingsKeys.OUTPUT_FOLDER: "",
                    constants.ProjectSettingsKeys.CUSTOM_LOGO_PATH: "",
                    constants.ProjectSettingsKeys.OCIO_CONFIG_PATH: "test",
                    constants.ProjectSettingsKeys.FRAMES_PER_PATCH: 1,
                    constants.ProjectSettingsKeys.REFERENCE_GAMUT: constants.ColourSpace.CS_ACES,
                    constants.ProjectSettingsKeys.FRAME_RATE: constants.FrameRates.FPS_48,
                    constants.ProjectSettingsKeys.EXPORT_LUT_FOR_ACES_CCT: True,
                    constants.ProjectSettingsKeys.EXPORT_LUT_FOR_ACES_CCT_IN_TARGET_OUT: True,
                    constants.ProjectSettingsKeys.PROJECT_CUSTOM_PRIMARIES: {
                        "TestPrimaries1": [
                            [
                                0.7347,
                                0.265
                            ],
                            [
                                0.0,
                                1.0
                            ],
                            [
                                0.0001,
                                0.0
                            ],
                            [
                                0.32168,
                                0.338
                            ]
                        ]
                    },
                    constants.ProjectSettingsKeys.LED_WALLS: [
                        {
                            constants.LedWallSettingsKeys.NAME: "Wall1",
                            constants.LedWallSettingsKeys.ENABLE_EOTF_CORRECTION: True,
                            constants.LedWallSettingsKeys.ENABLE_GAMUT_COMPRESSION: True,
                            constants.LedWallSettingsKeys.AUTO_WB_SOURCE: True,
                            constants.LedWallSettingsKeys.INPUT_SEQUENCE_FOLDER: "",
                            constants.LedWallSettingsKeys.CALCULATION_ORDER: constants.CalculationOrder.CO_CS_EOTF,
                            constants.LedWallSettingsKeys.PRIMARIES_SATURATION: 0.7,
                            constants.LedWallSettingsKeys.INPUT_PLATE_GAMUT: constants.ColourSpace.CS_ACES,
                            constants.LedWallSettingsKeys.NATIVE_CAMERA_GAMUT: constants.ColourSpace.CS_ACES,
                            constants.LedWallSettingsKeys.NUM_GREY_PATCHES: 30,
                            constants.LedWallSettingsKeys.REFERENCE_TO_TARGET_CAT: constants.CAT.CAT_CAT02,
                            constants.LedWallSettingsKeys.ROI: [342, 685, 119, 470],
                            constants.LedWallSettingsKeys.SHADOW_ROLLOFF: 0.008,
                            constants.LedWallSettingsKeys.TARGET_MAX_LUM_NITS: 1000,
                            constants.LedWallSettingsKeys.TARGET_GAMUT: constants.ColourSpace.CS_BT2020,
                            constants.LedWallSettingsKeys.TARGET_EOTF: constants.EOTF.EOTF_ST2084,
                            constants.LedWallSettingsKeys.TARGET_TO_SCREEN_CAT: constants.CAT.CAT_CAT02,
                            constants.LedWallSettingsKeys.MATCH_REFERENCE_WALL: False,
                            constants.LedWallSettingsKeys.REFERENCE_WALL: "",
                            constants.LedWallSettingsKeys.USE_WHITE_POINT_OFFSET: False,
                            constants.LedWallSettingsKeys.WHITE_POINT_OFFSET_SOURCE: "",
                            constants.LedWallSettingsKeys.VERIFICATION_WALL: "",
                            constants.LedWallSettingsKeys.IS_VERIFICATION_WALL: False,
                            constants.LedWallSettingsKeys.AVOID_CLIPPING: True
                        }
                    ]
                }
            }
        
        self.test_settings_expected = copy.deepcopy(self.test_settings)
        for led_wall in self.test_settings_expected[constants.OpenVPCalSettingsKeys.PROJECT_SETTINGS][constants.ProjectSettingsKeys.LED_WALLS]:
            led_wall[constants.LedWallSettingsKeys.ROI] = upgrade_legacy_roi(led_wall[constants.LedWallSettingsKeys.ROI])

        # Legacy default values for comparison
        self.legacy_default = {
            constants.ProjectSettingsKeys.CONTENT_MAX_LUM: constants.PQ.PQ_MAX_NITS,
            constants.ProjectSettingsKeys.FILE_FORMAT: constants.FileFormats.default(),
            constants.ProjectSettingsKeys.RESOLUTION_WIDTH: constants.DEFAULT_RESOLUTION_WIDTH,
            constants.ProjectSettingsKeys.RESOLUTION_HEIGHT: constants.DEFAULT_RESOLUTION_HEIGHT,
            constants.ProjectSettingsKeys.OUTPUT_FOLDER: os.path.join(str(Path.home()), "OpenVPCal_output"),
            constants.ProjectSettingsKeys.OCIO_CONFIG_PATH: "",
            constants.ProjectSettingsKeys.CUSTOM_LOGO_PATH: "",
            constants.ProjectSettingsKeys.FRAMES_PER_PATCH: 1,
            constants.ProjectSettingsKeys.REFERENCE_GAMUT: constants.ColourSpace.CS_ACES,
            constants.ProjectSettingsKeys.LED_WALLS: [],
            constants.ProjectSettingsKeys.PROJECT_CUSTOM_PRIMARIES: {},
            constants.ProjectSettingsKeys.FRAME_RATE: constants.FrameRates.default(),
            constants.ProjectSettingsKeys.EXPORT_LUT_FOR_ACES_CCT: False,
            constants.ProjectSettingsKeys.EXPORT_LUT_FOR_ACES_CCT_IN_TARGET_OUT: False,
            constants.ProjectSettingsKeys.PROJECT_ID: utils.generate_truncated_hash(),
            constants.ProjectSettingsKeys.LUT_SIZE: constants.DEFAULT_LUZ_SIZE,
        }

    def tearDown(self):
        if os.path.exists(self.test_json_path):
            os.remove(self.test_json_path)
    
    def create_test_settings_json(self):
        """Helper function to create a test settings json file."""
        with open(self.test_json_path, "w") as file:
            json.dump(self.test_settings, file, indent=4)

    def test_fields_all_included_in_test(self):
        """Test that all fields in the model are covered by our test sample."""
        test_settings_keys = list(self.test_settings[constants.OpenVPCalSettingsKeys.PROJECT_SETTINGS].keys())
        test_settings_keys.sort()
        model_keys = list(ProjectSettingsModel.model_fields.keys())
        model_keys.sort()
        self.assertEqual(test_settings_keys, model_keys)
    
    def test_project_settings_keys(self):
        """Test that ProjectSettingsKeys should reflect all fields in the model."""
        constants_all = constants.ProjectSettingsKeys.all().copy()
        constants_all.sort()
        model_keys = list(ProjectSettingsModel.model_fields.keys())
        model_keys.sort()
        self.assertEqual(constants_all, model_keys, "ProjectSettingsKeys should reflect all fields in the model. Add new keys to ProjectSettingsKeys.")

    def test_default_values(self):
        """Test for refactoring - check the number of legacy fields is the same as the number of fields in the new model."""
        # We can remove this test once we add more fields to the new model in future.
        self.assertEqual(len(self.legacy_default), len(ProjectSettingsModel.model_fields))

        # Test for refactoring - check the default values are the same as the legacy default values
        # We can remove this test once we update the default values in future.
        new_settings = ProjectSettingsModel()
        self.assertEqual(self.legacy_default[constants.ProjectSettingsKeys.CONTENT_MAX_LUM], new_settings.content_max_lum)
        self.assertEqual(self.legacy_default[constants.ProjectSettingsKeys.FILE_FORMAT], new_settings.file_format)
        self.assertEqual(self.legacy_default[constants.ProjectSettingsKeys.RESOLUTION_WIDTH], new_settings.resolution_width)
        self.assertEqual(self.legacy_default[constants.ProjectSettingsKeys.RESOLUTION_HEIGHT], new_settings.resolution_height)
        self.assertEqual(self.legacy_default[constants.ProjectSettingsKeys.OUTPUT_FOLDER], new_settings.output_folder)
        self.assertEqual(self.legacy_default[constants.ProjectSettingsKeys.OCIO_CONFIG_PATH], new_settings.ocio_config_path)
        self.assertEqual(self.legacy_default[constants.ProjectSettingsKeys.CUSTOM_LOGO_PATH], new_settings.custom_logo_path)
        self.assertEqual(self.legacy_default[constants.ProjectSettingsKeys.FRAMES_PER_PATCH], new_settings.frames_per_patch)
        self.assertEqual(self.legacy_default[constants.ProjectSettingsKeys.REFERENCE_GAMUT], new_settings.reference_gamut)
        self.assertEqual(self.legacy_default[constants.ProjectSettingsKeys.LED_WALLS], new_settings.led_walls)
        self.assertEqual(self.legacy_default[constants.ProjectSettingsKeys.PROJECT_CUSTOM_PRIMARIES], new_settings.project_custom_primaries)
        self.assertEqual(self.legacy_default[constants.ProjectSettingsKeys.FRAME_RATE], new_settings.frame_rate)
        self.assertEqual(self.legacy_default[constants.ProjectSettingsKeys.EXPORT_LUT_FOR_ACES_CCT], new_settings.export_lut_for_aces_cct)
        self.assertEqual(self.legacy_default[constants.ProjectSettingsKeys.EXPORT_LUT_FOR_ACES_CCT_IN_TARGET_OUT], new_settings.export_lut_for_aces_cct_in_target_out)
        self.assertEqual(self.legacy_default[constants.ProjectSettingsKeys.LUT_SIZE], new_settings.lut_size)
        
        # project_id is generated dynamically, so we just check it's a string
        self.assertIsInstance(new_settings.project_id, str)

    def test_project_settings_init(self):
        settings = ProjectSettings()
        self.assertEqual(settings.content_max_lum, self.legacy_default[constants.ProjectSettingsKeys.CONTENT_MAX_LUM])
        self.assertEqual(settings.file_format, self.legacy_default[constants.ProjectSettingsKeys.FILE_FORMAT])
        self.assertEqual(settings.resolution_width, self.legacy_default[constants.ProjectSettingsKeys.RESOLUTION_WIDTH])
        self.assertEqual(settings.resolution_height, self.legacy_default[constants.ProjectSettingsKeys.RESOLUTION_HEIGHT])
        self.assertEqual(settings.output_folder, self.legacy_default[constants.ProjectSettingsKeys.OUTPUT_FOLDER])
        self.assertEqual(settings.ocio_config_path, self.legacy_default[constants.ProjectSettingsKeys.OCIO_CONFIG_PATH])
        self.assertEqual(settings.custom_logo_path, self.legacy_default[constants.ProjectSettingsKeys.CUSTOM_LOGO_PATH])
        self.assertEqual(settings.frames_per_patch, self.legacy_default[constants.ProjectSettingsKeys.FRAMES_PER_PATCH])
        self.assertEqual(settings.reference_gamut, self.legacy_default[constants.ProjectSettingsKeys.REFERENCE_GAMUT])
        self.assertEqual(settings.led_walls, self.legacy_default[constants.ProjectSettingsKeys.LED_WALLS])
        self.assertEqual(settings.project_custom_primaries, self.legacy_default[constants.ProjectSettingsKeys.PROJECT_CUSTOM_PRIMARIES])
        self.assertEqual(settings.frame_rate, self.legacy_default[constants.ProjectSettingsKeys.FRAME_RATE])
        self.assertEqual(settings.export_lut_for_aces_cct, self.legacy_default[constants.ProjectSettingsKeys.EXPORT_LUT_FOR_ACES_CCT])
        self.assertEqual(settings.export_lut_for_aces_cct_in_target_out, self.legacy_default[constants.ProjectSettingsKeys.EXPORT_LUT_FOR_ACES_CCT_IN_TARGET_OUT])
        self.assertEqual(settings.lut_size, self.legacy_default[constants.ProjectSettingsKeys.LUT_SIZE])
        self.assertIsInstance(settings.project_id, str)
    
    def test_content_max_lum(self):
        """Test content_max_lum field."""
        settings = ProjectSettings()
        settings.content_max_lum = 2000.0
        self.assertEqual(settings.content_max_lum, 2000.0)

    def test_file_format(self):
        """Test file_format field."""
        settings = ProjectSettings()
        settings.file_format = constants.FileFormats.FF_DPX
        self.assertEqual(settings.file_format, constants.FileFormats.FF_DPX)

    def test_resolution_width(self):
        """Test resolution_width field."""
        settings = ProjectSettings()
        settings.resolution_width = 3840
        self.assertEqual(settings.resolution_width, 3840)

    def test_resolution_height(self):
        """Test resolution_height field."""
        settings = ProjectSettings()
        settings.resolution_height = 2160
        self.assertEqual(settings.resolution_height, 2160)

    def test_output_folder(self):
        """Test output_folder field."""
        settings = ProjectSettings()
        settings.output_folder = "/custom/output/path"
        self.assertEqual(settings.output_folder, "/custom/output/path")

    def test_ocio_config_path(self):
        """Test ocio_config_path field."""
        settings = ProjectSettings()
        settings.ocio_config_path = "/custom/ocio.ocio"
        self.assertEqual(settings.ocio_config_path, "/custom/ocio.ocio")

    def test_custom_logo_path(self):
        """Test custom_logo_path field."""
        settings = ProjectSettings()
        settings.custom_logo_path = "/custom/logo.png"
        self.assertEqual(settings.custom_logo_path, "/custom/logo.png")

    def test_frames_per_patch(self):
        """Test frames_per_patch field."""
        settings = ProjectSettings()
        settings.frames_per_patch = 10
        self.assertEqual(settings.frames_per_patch, 10)

    def test_reference_gamut(self):
        """Test reference_gamut field."""
        settings = ProjectSettings()
        settings.reference_gamut = constants.ColourSpace.CS_P3
        self.assertEqual(settings.reference_gamut, constants.ColourSpace.CS_P3)

    def test_led_walls(self):
        """Test led_walls field."""
        settings = ProjectSettings()
        wall1 = LedWallSettings(settings, name="Wall1")
        wall2 = LedWallSettings(settings, name="Wall2")
        led_walls = [wall1, wall2]
        settings.led_walls = led_walls
        self.assertEqual(len(settings.led_walls), len(led_walls))
        self.assertEqual(settings.led_walls, led_walls)

    def test_project_custom_primaries(self):
        """Test project_custom_primaries field."""
        settings = ProjectSettings()
        custom_primaries = {
            "TestPrimary1": [[0.7347, 0.265], [0.0, 1.0], [0.0001, 0.0], [0.32168, 0.338]],
            "TestPrimary2": [[0.64, 0.33], [0.3, 0.6], [0.15, 0.06], [0.3127, 0.329]]
        }
        settings.project_custom_primaries = custom_primaries
        self.assertEqual(settings.project_custom_primaries, custom_primaries)

    def test_add_custom_primary(self):
        """Test adding a custom primary to the project."""
        settings = ProjectSettings()
        custom_primaries = { "TestPrimary1": [[0.7347, 0.265], [0.0, 1.0], [0.0001, 0.0], [0.32168, 0.338]] }
        settings.project_custom_primaries = custom_primaries
        # Test adding a custom primary that already exists
        with self.assertRaises(ValueError):
            settings.add_custom_primary("TestPrimary1", [[0.7347, 0.265], [0.0, 1.0], [0.0001, 0.0], [0.32168, 0.338]])

    def test_frame_rate(self):
        """Test frame_rate field."""
        settings = ProjectSettings()
        settings.frame_rate = constants.FrameRates.FPS_60
        self.assertEqual(settings.frame_rate, constants.FrameRates.FPS_60)

    def test_export_lut_for_aces_cct(self):
        """Test export_lut_for_aces_cct field."""
        settings = ProjectSettings()
        settings.export_lut_for_aces_cct = True
        self.assertEqual(settings.export_lut_for_aces_cct, True)

    def test_export_lut_for_aces_cct_in_target_out(self):
        """Test export_lut_for_aces_cct_in_target_out field."""
        settings = ProjectSettings()
        settings.export_lut_for_aces_cct_in_target_out = True
        self.assertEqual(settings.export_lut_for_aces_cct_in_target_out, True)

    def test_project_id(self):
        """Test project_id field."""
        settings = ProjectSettings()
        settings.project_id = "custom_project_123"
        self.assertEqual(settings.project_id, "custom_project_123")

    def test_lut_size(self):
        """Test lut_size field."""
        settings = ProjectSettings()
        settings.lut_size = 65
        self.assertEqual(settings.lut_size, 65)

    def test_clear_project_settings(self):
        self.project_settings.clear_project_settings()
        settings_default = ProjectSettingsModel().model_dump()
        for key in constants.ProjectSettingsKeys:
            if key == constants.ProjectSettingsKeys.PROJECT_ID:
                continue
            self.assertEqual(getattr(self.project_settings, key), settings_default[key])

    def test_set_get_input_sequence_folder(self):
        """Test setting and getting input sequence folder."""
        test_value = "/new/path/"
        self.settings.input_sequence_folder = test_value
        self.assertEqual(self.settings.input_sequence_folder, test_value)

    def test_set_get_input_sequence_input_transform(self):
        """Test setting and getting input sequence input transform."""
        test_value = "ACES2065-1"
        self.settings.input_sequence_input_transform = test_value
        self.assertEqual(self.settings.input_sequence_input_transform, test_value)

    def test_set_get_ocio_config_path(self):
        """Test setting and getting OCIO config path."""
        test_value = "/new/path/to/ocio_config.ocio"
        self.settings.ocio_config_path = test_value
        self.assertEqual(self.settings.ocio_config_path, test_value)

    def test_set_get_primaries_saturation(self):
        """Test setting and getting primaries saturation."""
        test_value = 0.8
        self.settings.primaries_saturation = test_value
        self.assertEqual(self.settings.primaries_saturation, test_value)

    def test_set_get_num_grey_patches(self):
        """Test setting and getting the num_grey_patches"""
        test_value = 10
        self.settings.num_grey_patches = test_value
        self.assertEqual(self.settings.num_grey_patches, test_value)

    def test_from_json(self):
        """Test creating a ProjectSettings object from a JSON file and saving it back."""
        self.maxDiff = None
        self.create_test_settings_json()

        # Load settings from file
        loaded_settings:ProjectSettings = ProjectSettings.from_json(self.test_json_path)
        test_project_settings = self.test_settings_expected[constants.OpenVPCalSettingsKeys.PROJECT_SETTINGS]
        for key in constants.ProjectSettingsKeys:
            if key == constants.ProjectSettingsKeys.LED_WALLS:
                continue
            self.assertEqual(test_project_settings[key], getattr(loaded_settings, key))

        test_led_walls = test_project_settings[constants.ProjectSettingsKeys.LED_WALLS]
        loaded_led_walls = loaded_settings.led_walls
        self.assertEqual(len(test_led_walls), len(loaded_led_walls))
        for test_led_wall, loaded_led_wall in zip(test_led_walls, loaded_led_walls):
            for test_key in constants.LedWallSettingsKeys:
                self.assertEqual(test_led_wall[test_key], getattr(loaded_led_wall._led_settings, test_key))
            for loaded_led_wall in loaded_led_walls:
                self.assertIsInstance(loaded_led_wall, LedWallSettings)

    def test_to_json(self):
        self.maxDiff = None
        self.create_test_settings_json()
        
        # Load settings from file
        loaded_settings:ProjectSettings = ProjectSettings.from_json(self.test_json_path)
        # Save settings to file
        loaded_settings.to_json(self.test_json_path)
        with open(self.test_json_path, 'r') as file:
            saved_settings = json.load(file)
        self.assertEqual(self.test_settings_expected, saved_settings)

    def test_from_dict(self):
        settings:ProjectSettings = ProjectSettings.from_dict(copy.deepcopy(self.test_settings))
        settings_dict:dict = settings.to_dict()
        self.assertEqual(self.test_settings_expected[constants.OpenVPCalSettingsKeys.VERSION], settings_dict[constants.OpenVPCalSettingsKeys.VERSION])
        test_project_settings = self.test_settings_expected[constants.OpenVPCalSettingsKeys.PROJECT_SETTINGS]
        project_settings = settings_dict[constants.OpenVPCalSettingsKeys.PROJECT_SETTINGS]
        for key in constants.ProjectSettingsKeys:
            if key == constants.ProjectSettingsKeys.LED_WALLS:
                continue
            self.assertEqual(test_project_settings[key], project_settings[key])

        test_led_walls = test_project_settings[constants.ProjectSettingsKeys.LED_WALLS]
        led_walls = project_settings[constants.ProjectSettingsKeys.LED_WALLS]
        self.assertEqual(len(test_led_walls), len(led_walls))
        for test_led_wall, led_wall in zip(test_led_walls, led_walls):
            for key in constants.LedWallSettingsKeys:
                self.assertEqual(test_led_wall[key], led_wall[key])

    def test_to_dict(self):
        self.create_test_settings_json()
        settings:ProjectSettings = ProjectSettings.from_json(self.test_json_path)
        settings_dict:dict = settings.to_dict()
        self.assertEqual(self.test_settings_expected, settings_dict)

    def test_invalid_json_params(self):
        # Create a temporary json file with a setting not supported
        with open(self.get_test_project_settings(), 'r') as file:
            json_data = json.load(file)

        ps = ProjectSettings()
        for key in json_data[constants.OpenVPCalSettingsKeys.PROJECT_SETTINGS]:
            self.assertTrue(hasattr(ps, key), f"Missing Property '{key}' found in the loaded json file")

    def test_add_led_wall(self):
        """Test adding a led wall to the project settings."""
        new_wall = self.settings.add_led_wall("AnotherWall")
        self.assertEqual(self.settings.led_walls, [new_wall])

    def test_copy_led_wall(self):
        """Test copying an led wall to the project settings."""
        new_wall = self.settings.add_led_wall("AnotherWall")
        new_wall2 = self.settings.copy_led_wall(new_wall.name, "AnotherWall2")
        self.assertEqual(self.settings.led_walls, [new_wall, new_wall2])

    def test_remove_led_wall(self):
        """Test adding a led wall to the project settings."""
        walls = [self.settings.add_led_wall("AnotherWall"), self.settings.add_led_wall("AnotherWall2"),
                 self.settings.add_led_wall("AnotherWall3")]

        self.assertEqual(self.settings.led_walls, walls)
        self.settings.remove_led_wall(walls[1].name)
        self.assertEqual(self.settings.led_walls, [walls[0], walls[2]])

    def test_led_walls_not_dict_after_save(self):
        self.settings.add_led_wall("AnotherWall")
        self.settings.add_led_wall("AnotherWall2"),
        self.settings.add_led_wall("AnotherWall3")

        for wall in self.settings.led_walls:
            self.assertIsInstance(wall, LedWallSettings)

        temp_json = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.settings.to_json(temp_json)
        for wall in self.settings.led_walls:
            self.assertIsInstance(wall, LedWallSettings)

    def test_verification_wall(self):
        """Test adding a verification wall to the project settings."""
        new_wall = self.settings.add_led_wall("AnotherWall")
        self.settings.add_verification_wall(new_wall.name)
        temp_json = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        self.settings.to_json(temp_json)

        new_settings = ProjectSettings.from_json(temp_json)
        temp_json2 = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        new_settings.to_json(temp_json2)
        self.files_are_equal(temp_json, temp_json2)

    def test_reset_led_wall(self):
        """Test resetting a led wall to the project settings."""
        new_wall = self.settings.add_led_wall("AnotherWall")

        new_wall2 = self.settings.add_led_wall("AnotherWall2")
        self.settings.add_verification_wall(new_wall.name)

        new_wall.reference_wall = new_wall2.name
        new_wall.match_reference_wall = True

        self.settings.reset_led_wall(new_wall.name)

    def test_all_sample_project_json(self):
        for project_settings_path in self.get_all_test_project_settings_path():
            with open(project_settings_path, 'r', encoding='utf-8') as file:
                loaded_data:dict = json.load(file)
                self.assertIsNotNone(loaded_data)
                # Check no throw
                try:
                   project_settings = ProjectSettings.from_dict(loaded_data)
                except Exception as e:
                    self.fail(f"Failed to load project settings from {project_settings_path}: {e}")
                self.assertIsInstance(project_settings, ProjectSettings)
