"""
Module contains the classes associated with handling the project settings including, loading, saving, getting and
setting
"""
import os
import copy
import json
from pathlib import Path
from typing import Dict, List

import open_vp_cal
from open_vp_cal.core import constants
from open_vp_cal.led_wall_settings import LedWallSettings


class ProjectSettings:
    """A class to handle project settings."""
    def __init__(self):
        """Initialize an empty ProjectSettings object."""
        self._default_project_settings = {
            constants.ProjectSettings.FILE_FORMAT: constants.FileFormats.FF_DEFAULT,
            constants.ProjectSettings.RESOLUTION_WIDTH: 3840,
            constants.ProjectSettings.RESOLUTION_HEIGHT: 2160,
            constants.ProjectSettings.OUTPUT_FOLDER: os.path.join(str(Path.home()), "OpenVPCal_output"),
            constants.ProjectSettings.OCIO_CONFIG_PATH: "",
            constants.ProjectSettings.CUSTOM_LOGO_PATH: "",
            constants.ProjectSettings.FRAMES_PER_PATCH: 1,
            constants.ProjectSettings.LED_WALLS: [],
            constants.ProjectSettings.PROJECT_CUSTOM_PRIMARIES: {},
        }

        self._project_settings = copy.deepcopy(self._default_project_settings)
        self._led_wall_class = LedWallSettings

    def clear_project_settings(self):
        """
        Clear the project settings and restore them to the defaults
        """
        self._project_settings = copy.deepcopy(self._default_project_settings)

    @property
    def custom_logo_path(self) -> str:
        """ The filepath to the custom logo for the pattern generation

        Returns:
            str: The filepath to the custom logo for the pattern generation
        """
        return self._project_settings[constants.ProjectSettings.CUSTOM_LOGO_PATH]

    @custom_logo_path.setter
    def custom_logo_path(self, value: str):
        """Set the filepath to the custom logo for the pattern generation

        Args:
            value (bool): File path to a custom logo
        """
        self._project_settings[constants.ProjectSettings.CUSTOM_LOGO_PATH] = value

    @property
    def project_custom_primaries(self) -> Dict[str, List[float]]:
        """ Gets all the custom primaries for the project

        Returns:
            dict: The dictionary of the custom primaries
        """
        return self._project_settings[constants.ProjectSettings.PROJECT_CUSTOM_PRIMARIES]

    @project_custom_primaries.setter
    def project_custom_primaries(self, value: Dict[str, List[float]]):
        """ Sets the custom primaries to use for the project

        Args:
            value: The dictionary for the custom primaries
        """
        self._project_settings[constants.ProjectSettings.PROJECT_CUSTOM_PRIMARIES] = value

    def add_custom_primary(self, name: str, primaries: List[float]):
        """ Adds a custom primary to the project

        Args:
            name (str): The name of the custom primary
            primaries (List[float]): The list of primaries to add
        """
        if name in self._project_settings[constants.ProjectSettings.PROJECT_CUSTOM_PRIMARIES]:
            raise ValueError(f'Custom primary {name} already exists')

        self._project_settings[constants.ProjectSettings.PROJECT_CUSTOM_PRIMARIES][name] = primaries

    @property
    def file_format(self) -> constants.FileFormats:
        """Get the file format we want to generate patterns to

        Returns:
            constants.FileFormats: The file format we want to generate patterns to
        """
        return self._project_settings[constants.ProjectSettings.FILE_FORMAT]

    @file_format.setter
    def file_format(self, value: constants.FileFormats):
        """Set the file format we want to generate patterns to

        Args:
            value (constants.FileFormats): The file format we want to generate patterns to
        """
        self._project_settings[constants.ProjectSettings.FILE_FORMAT] = value

    @property
    def frames_per_patch(self) -> int:
        """Get the number of frames per patch we want to generate

        Returns:
            int: The number of frames per patch to generate
        """
        return self._project_settings[constants.ProjectSettings.FRAMES_PER_PATCH]

    @frames_per_patch.setter
    def frames_per_patch(self, value: int):
        """ The number of frames per patch we want to generate

        Args:
            value (int): The number of frames per patch we want to generate
        """
        self._project_settings[constants.ProjectSettings.FRAMES_PER_PATCH] = value

    @property
    def led_walls(self) -> list:
        """Return the LED walls in the project

        Returns:
            list: The list of led walls stored in the project
        """
        if not self._project_settings:
            raise ValueError("Project settings not set")
        return self._project_settings[constants.ProjectSettings.LED_WALLS]

    @led_walls.setter
    def led_walls(self, value: list):
        """Set the LED walls config path.

        Args:
            value (list): A list of led walls we want to store in the project
        """
        values = []
        for item in value:
            if isinstance(item, self._led_wall_class):
                values.append(item)
            else:
                values.append(self._led_wall_class.from_json_string(self, json.dumps(item)))
        self._project_settings[constants.ProjectSettings.LED_WALLS] = values

    @property
    def ocio_config_path(self) -> str:
        """ Return the OCIO config path we want to use as a base for the exported ocio config.

        Returns:
            str: The OCIO config path.
        """
        return self._project_settings[constants.ProjectSettings.OCIO_CONFIG_PATH]

    @ocio_config_path.setter
    def ocio_config_path(self, value: str):
        """Set the OCIO config path used as the base for writing out the resulting ocio config. This is not used for
            any internal computation


        Args:
            value (str): The OCIO config path.
        """
        self._project_settings[constants.ProjectSettings.OCIO_CONFIG_PATH] = value

    @property
    def output_folder(self) -> str:
        """Return the output folder we want to write our patches, luts, and configs too.

        Returns:
            str: The folder path
        """
        return self._project_settings[constants.ProjectSettings.OUTPUT_FOLDER]

    @output_folder.setter
    def output_folder(self, value: str):
        """Set the folder path for the output folder

        Args:
            value (str): The folder path for the outputs
        """
        self._project_settings[constants.ProjectSettings.OUTPUT_FOLDER] = value

    @property
    def resolution_width(self) -> int:
        """Returns the resolution width of the patterns we are going to generate

        Returns:
            int: The resolution width of the patterns we are going to generate
        """
        return self._project_settings[constants.ProjectSettings.RESOLUTION_WIDTH]

    @resolution_width.setter
    def resolution_width(self, value: int):
        """Sets the resolution width of the patterns we want to generate

        Args:
            value (int): The resolution width
        """
        self._project_settings[constants.ProjectSettings.RESOLUTION_WIDTH] = value

    @property
    def resolution_height(self) -> int:
        """Returns the resolution height of the patterns we are going to generate

        Returns:
            int: The resolution height of the patterns we are going to generate
        """
        return self._project_settings[constants.ProjectSettings.RESOLUTION_HEIGHT]

    @resolution_height.setter
    def resolution_height(self, value: int):
        """Sets the resolution height of the patterns we want to generate

        Args:
            value (int): The resolution height
        """
        self._project_settings[constants.ProjectSettings.RESOLUTION_HEIGHT] = value

    @classmethod
    def from_json(cls, json_file: str):
        """Create a ProjectSettings object from a JSON file.

        Args:
            json_file (str): The path to the JSON file.

        Returns:
            ProjectSettings: A ProjectSettings object.
        """
        project_settings = cls._settings_from_json_file(json_file)
        if not project_settings:
            raise ValueError(f'No project settings found in {json_file}')
        instance = cls()
        default_ocio = instance.ocio_config_path
        instance._project_settings = project_settings
        walls = []

        # We cant set up the reference walls until all walls are loaded, so we remove it and create a map
        reference_wall_map = {}
        verification_wall_map = {}
        for wall in instance.led_walls:
            reference_wall_map[wall[constants.LedWallSettings.NAME]] = wall[
                constants.LedWallSettings.REFERENCE_WALL
            ]
            verification_wall_map[wall[constants.LedWallSettings.NAME]] = wall[
                constants.LedWallSettings.VERIFICATION_WALL
            ]
            del wall[constants.LedWallSettings.REFERENCE_WALL]
            del wall[constants.LedWallSettings.VERIFICATION_WALL]
            walls.append(instance._led_wall_class.from_dict(instance, wall))
        instance.led_walls = walls

        # Now we have all the walls loaded, we can re set up the reference walls and verification wall links
        for led_wall in instance.led_walls:
            reference_wall = reference_wall_map[led_wall.name]
            if reference_wall:
                led_wall.reference_wall = reference_wall
            verification_wall = verification_wall_map[led_wall.name]
            if verification_wall:
                led_wall.verification_wall = verification_wall
        if not instance.ocio_config_path:
            instance.ocio_config_path = default_ocio
        return instance

    @classmethod
    def _settings_from_json_file(cls, json_file) -> dict:
        """ Load the project settings from a JSON file.

        Args:
            json_file: The path to the JSON file.

        Returns: The project settings

        """
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
            project_settings = data[constants.ProjectSettings.PROJECT_SETTINGS]
            return project_settings

    def to_json(self, json_file: str):
        """Save the ProjectSettings object to a JSON file.

        Args:
            json_file (str): The path to the JSON file.
        """
        data = self.to_dict()
        with open(json_file, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=4)

    def to_dict(self) -> Dict:
        """ Save the ProjectSettings to a dict which can be serialized to JSON

        Returns: Dict

        """
        output = self._project_settings.copy()
        led_wall_serialized = []
        for led_wall in self.led_walls:
            led_wall_serialized.append(led_wall.to_dict())
        output[constants.ProjectSettings.LED_WALLS] = led_wall_serialized
        data = {
            constants.VERSION: open_vp_cal.__version__,
            constants.ProjectSettings.PROJECT_SETTINGS: output
        }
        return data

    def add_led_wall(self, name: str) -> LedWallSettings:
        """ Adds a new LED wall to the project settings

        Args:
            name (str): The name of the LED wall we want to add

        Returns:
            LedWallSettings: The newly created led wall
        """
        existing_names = [led_wall.name for led_wall in self.led_walls]
        if name in existing_names:
            raise ValueError(f'Led wall {name} already exists')

        led_wall = self._led_wall_class(self, name)
        self.led_walls.append(led_wall)
        return led_wall

    def copy_led_wall(self, existing_wall_name, new_name: str) -> LedWallSettings:
        """ Adds a new LED wall to the project settings based on a copy of an existing wall with a new name

        Args:
            existing_wall_name (str): The name of the LED wall we want to copy
            new_name (str): The name of the new LED wall


        Returns:
            LedWallSettings: The newly created led wall
        """
        existing_names = [led_wall.name for led_wall in self.led_walls]
        if new_name in existing_names:
            raise ValueError(f'Led wall {new_name} already exists')

        if existing_wall_name not in existing_names:
            raise ValueError(f'Led wall {existing_wall_name} does not exist')

        existing_led_wall = self.get_led_wall(existing_wall_name)
        new_led_wall_dict = existing_led_wall.to_dict().copy()
        new_led_wall = self._led_wall_class.from_dict(self, new_led_wall_dict)
        new_led_wall.name = new_name
        self.led_walls.append(new_led_wall)
        return new_led_wall

    def add_verification_wall(self, existing_wall_name: str) -> LedWallSettings:
        """ Adds a new LED wall to the project settings which mirrors all the settings from the existing wall,
            and whose settings cannot be changed directly, only via the parent

            The verification wall is prefixed with Verify and is used to verify that when the calibration sequence is 
            recorded with the calibration applied, the results match closely to the expected calibration.

            The original wall and verification wall are linked together, and marked which is the verification wall
            and which is not

        Args:
            existing_wall_name (str): The name of the LED wall we want to add a verification wall for


        Returns:
            LedWallSettings: The newly created led wall
        """
        existing_names = [led_wall.name for led_wall in self.led_walls]
        if existing_wall_name not in existing_names:
            raise ValueError(f'Led wall {existing_wall_name} does not exist')

        new_name = "Verify_" + existing_wall_name
        if new_name in existing_names:
            raise ValueError(f'Verification wall {new_name} already exists')

        existing_led_wall = self.get_led_wall(existing_wall_name)
        if existing_led_wall.is_verification_wall:
            raise ValueError("Can't add Verification wall to a Verification Wall")

        new_led_wall_dict = existing_led_wall.to_dict().copy()
        new_led_wall = self._led_wall_class.from_dict(self, new_led_wall_dict)
        new_led_wall.name = new_name
        self.led_walls.append(new_led_wall)

        # Once
        new_led_wall.is_verification_wall = True
        new_led_wall.verification_wall = existing_led_wall.name
        existing_led_wall.verification_wall = new_led_wall.name
        return new_led_wall

    def remove_led_wall(self, name: str):
        """ Removes a LED wall from the project

        Args:
            name (str): The name of the LED wall we want to remove
        """
        walls = self.led_walls
        for wall in walls:
            if wall.name == name:
                walls.remove(wall)
                break
        self.led_walls = walls

        for led_wall in self.led_walls:
            if led_wall.verification_wall == name:
                led_wall.verification_wall = ""

            if led_wall.reference_wall == name:
                led_wall.reference_wall = ""
                led_wall.match_reference_wall = False

    def get_led_wall(self, name: str) -> LedWallSettings:
        """ Returns a LED wall from the project

        Args:
            name (str): The name of the LED wall we want to get
        """
        for wall in self.led_walls:
            if wall.name == name:
                return wall
        raise ValueError(f'Led wall {name} not found')
