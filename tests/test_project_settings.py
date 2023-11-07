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
                    constants.ProjectSettings.FILE_FORMAT: "exr",
                    constants.ProjectSettings.RESOLUTION_WIDTH: 3840,
                    constants.ProjectSettings.RESOLUTION_HEIGHT: 2160,
                    constants.ProjectSettings.OUTPUT_FOLDER: "",
                    constants.ProjectSettings.CUSTOM_LOGO_PATH: "",
                    constants.ProjectSettings.OCIO_CONFIG_PATH: "test",
                    constants.ProjectSettings.FRAMES_PER_PATCH: 1,
                    constants.ProjectSettings.PROJECT_CUSTOM_PRIMARIES: {
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
                    constants.ProjectSettings.LED_WALLS: [
                        {
                            constants.LedWallSettings.NAME: "Wall1",
                            constants.LedWallSettings.ENABLE_EOTF_CORRECTION: True,
                            constants.LedWallSettings.ENABLE_GAMUT_COMPRESSION: True,
                            constants.LedWallSettings.AUTO_WB_SOURCE: True,
                            constants.LedWallSettings.INPUT_SEQUENCE_FOLDER: "",
                            constants.LedWallSettings.CALCULATION_ORDER: constants.CalculationOrder.CO_CS_EOTF,
                            constants.LedWallSettings.PRIMARIES_SATURATION: 0.7,
                            constants.LedWallSettings.INPUT_PLATE_GAMUT: constants.ColourSpace.CS_ACES,
                            constants.LedWallSettings.NATIVE_CAMERA_GAMUT: constants.ColourSpace.CS_ACES,
                            constants.LedWallSettings.NUM_GREY_PATCHES: 30,
                            constants.LedWallSettings.REFERENCE_TO_TARGET_CAT: constants.CAT.CAT_CAT02,
                            constants.LedWallSettings.ROI: [342, 685, 119, 470],
                            constants.LedWallSettings.SHADOW_ROLLOFF: 0.008,
                            constants.LedWallSettings.TARGET_MAX_LUM_NITS: 1000,
                            constants.LedWallSettings.TARGET_GAMUT: constants.ColourSpace.CS_BT2020,
                            constants.LedWallSettings.TARGET_EOTF: constants.EOTF.EOTF_ST2084,
                            constants.LedWallSettings.TARGET_TO_SCREEN_CAT: constants.CAT.CAT_CAT02,
                            constants.LedWallSettings.MATCH_REFERENCE_WALL: False,
                            constants.LedWallSettings.REFERENCE_WALL: "",
                            constants.LedWallSettings.USE_EXTERNAL_WHITE_POINT: False,
                            constants.LedWallSettings.EXTERNAL_WHITE_POINT_FILE: "",
                            constants.LedWallSettings.VERIFICATION_WALL: "",
                            constants.LedWallSettings.IS_VERIFICATION_WALL: False,
                            constants.LedWallSettings.AVOID_CLIPPING: True
                        }
                    ]
                }
            }

        self._led_json_file = tempfile.NamedTemporaryFile(suffix=".json", delete=False).name
        with open(self._led_json_file, "w") as handle:
            json.dump(
                self.test_settings[constants.ProjectSettings.PROJECT_SETTINGS]
                [constants.ProjectSettings.LED_WALLS][0], handle)
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
        for key in self.test_settings[constants.ProjectSettings.PROJECT_SETTINGS]:
            if key == constants.ProjectSettings.LED_WALLS:
                led_walls = getattr(loaded_settings, key)
                for led_wall in led_walls:
                    self.assertIsInstance(led_wall, LedWallSettings)
            else:
                self.assertEqual(
                    self.test_settings[constants.ProjectSettings.PROJECT_SETTINGS][key], getattr(loaded_settings, key))

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
        for key in json_data[constants.ProjectSettings.PROJECT_SETTINGS]:
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





