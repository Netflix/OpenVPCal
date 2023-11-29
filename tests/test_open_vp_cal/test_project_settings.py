import json
import os
import tempfile

import open_vp_cal
from open_vp_cal.led_wall_settings import LedWallSettings
from open_vp_cal.project_settings import ProjectSettings
from open_vp_cal.core import constants
from test_utils import TestBase


class TestProjectSettings(TestBase):
    """Test cases for ProjectSettings."""

    def setUp(self):
        """Set up test case."""
        super(TestProjectSettings, self).setUp()
        self.settings = ProjectSettings()
        self.test_settings = {
            constants.VERSION: open_vp_cal.__version__,
            "project_settings":
                {
                    constants.ProjectSettingsKeys.FILE_FORMAT: "exr",
                    constants.ProjectSettingsKeys.RESOLUTION_WIDTH: 3840,
                    constants.ProjectSettingsKeys.RESOLUTION_HEIGHT: 2160,
                    constants.ProjectSettingsKeys.OUTPUT_FOLDER: "",
                    constants.ProjectSettingsKeys.CUSTOM_LOGO_PATH: "",
                    constants.ProjectSettingsKeys.OCIO_CONFIG_PATH: "test",
                    constants.ProjectSettingsKeys.FRAMES_PER_PATCH: 1,
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
                            constants.LedWallSettingsKeys.USE_EXTERNAL_WHITE_POINT: False,
                            constants.LedWallSettingsKeys.EXTERNAL_WHITE_POINT_FILE: "",
                            constants.LedWallSettingsKeys.VERIFICATION_WALL: "",
                            constants.LedWallSettingsKeys.IS_VERIFICATION_WALL: False,
                            constants.LedWallSettingsKeys.AVOID_CLIPPING: True
                        }
                    ]
                }
            }

        self._led_json_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        with open(self._led_json_file, "w") as handle:
            json.dump(
                self.test_settings[constants.ProjectSettingsKeys.PROJECT_SETTINGS]
                [constants.ProjectSettingsKeys.LED_WALLS][0], handle)
        self.led_wall = LedWallSettings.from_json_file(self.settings, self._led_json_file)



    def tearDown(self):
        os.remove(self._led_json_file)

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

    def test_led_walls(self):
        self.settings.led_walls = [self.led_wall]
        self.assertEqual(self.settings.led_walls, [self.led_wall])

    def test_from_json_to_json(self):
        """Test creating a ProjectSettings object from a JSON file and saving it back."""
        self.maxDiff = None
        test_json_file = "test_settings.json"
        with open(test_json_file, 'w') as file:
            json.dump(self.test_settings, file, indent=4)

        # Load settings from file
        loaded_settings = ProjectSettings.from_json(test_json_file)
        for key in self.test_settings[constants.ProjectSettingsKeys.PROJECT_SETTINGS]:
            if key == constants.ProjectSettingsKeys.LED_WALLS:
                led_walls = getattr(loaded_settings, key)
                for led_wall in led_walls:
                    self.assertIsInstance(led_wall, LedWallSettings)
            else:
                self.assertEqual(
                    self.test_settings[constants.ProjectSettingsKeys.PROJECT_SETTINGS][key], getattr(loaded_settings, key))

        # Save settings to file and compare
        loaded_settings.to_json(test_json_file)
        with open(test_json_file, 'r') as file:
            saved_settings = json.load(file)

        self.assertEqual(self.test_settings, saved_settings)

    def test_invalid_json_params(self):
        # Create a temporary json file with a setting not supported

        with open(self.get_test_project_settings(), 'r') as file:
            json_data = json.load(file)

        ps = ProjectSettings()
        for key in json_data[constants.ProjectSettingsKeys.PROJECT_SETTINGS]:
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
        verification_wall = self.settings.add_verification_wall(new_wall.name)
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






