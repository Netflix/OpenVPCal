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

Module contains the classes associated with handling the project settings including, loading, saving, getting and
setting
"""
from __future__ import annotations
import os
import json
import math
from pathlib import Path
from typing import Dict, List, Union, Any, Type
from pydantic import BaseModel, Field, field_validator, field_serializer

import open_vp_cal
from open_vp_cal.core import constants, ocio_utils, utils
from open_vp_cal.led_wall_settings import LedWallSettings, LedWallSettingsBaseModel
from open_vp_cal.core.resource_loader import ResourceLoader


class ProjectSettingsBaseModel(BaseModel):
    """Base model for LedWallSettings with typing."""
    content_max_lum: float = Field(default=constants.PQ.PQ_MAX_NITS)
    file_format: constants.FileFormats = Field(default=constants.FileFormats(constants.FileFormats.default()))
    resolution_width: int = Field(default=constants.DEFAULT_RESOLUTION_WIDTH)
    resolution_height: int = Field(default=constants.DEFAULT_RESOLUTION_HEIGHT)
    output_folder: str = Field(default=os.path.join(str(Path.home()), "OpenVPCal_output"))
    ocio_config_path: str = Field(default="")
    custom_logo_path: str = Field(default="")
    frames_per_patch: int = Field(default=1)
    reference_gamut: constants.ColourSpace|str = Field(default=constants.ColourSpace(constants.ColourSpace.CS_ACES))
    led_walls: List[LedWallSettingsBaseModel] = Field(default=[])
    project_custom_primaries: Dict[str, List[List[float]]] = Field(default={})
    frame_rate: constants.FrameRates|float = Field(default=constants.FrameRates(constants.FrameRates.default()))
    export_lut_for_aces_cct: bool = Field(default=False)
    export_lut_for_aces_cct_in_target_out: bool = Field(default=False)
    project_id: str = Field(default=utils.generate_truncated_hash())
    lut_size: int = Field(default=constants.DEFAULT_LUZ_SIZE)

    @field_validator(
        "ocio_config_path",
        mode="before",
        json_schema_input_type=Union[str, None]
    )
    @classmethod
    def upgrade_ocio_config_path(cls, value: Any) -> str:
        """
        Force ocio_config_path to be a string all the time.
        - version 1.x: str|None
        - version 2.x: str
        Parameters:
            value: The OCIO config path in either str or None.
        Returns:
            str: The OCIO config path as a string.
        """
        if value is None:
            return ""
        return value

    @field_serializer("frame_rate")
    @field_validator(
        "frame_rate",
        mode="before",
        json_schema_input_type=Union[constants.FrameRates, float]
    )
    @classmethod
    def try_convert_to_enum_frame_rates(cls, value:Any) -> constants.FrameRates|float:
        """
        Try to convert a float frame rate to an enum frame rate if possible.
        Precision is 1e-3, for example:
        23.99 != constants.FrameRates.FPS_24
        23.998 != constants.FrameRates.FPS_24
        23.999 == constants.FrameRates.FPS_24
        """
        if isinstance(value, float):
             for frame_rate in constants.FrameRates:
                if math.isclose(value, frame_rate.value, abs_tol=11e-4):
                    return frame_rate
        return value

class OpenVPCalSettingsModel(BaseModel):
    """Base model for OpenVPCalSettings with typing."""
    openvp_cal_version: str = Field(default=open_vp_cal.__version__)
    project_settings: ProjectSettingsBaseModel = Field(default=ProjectSettingsBaseModel())


class ProjectSettings:
    """A class to handle project settings."""
    def __init__(self):
        """Initialize an empty ProjectSettings object."""
        from open_vp_cal.led_wall_settings import LedWallSettings
        self._project_settings: ProjectSettingsBaseModel = ProjectSettingsBaseModel()
        self._led_walls:List[LedWallSettings] = []
        self._led_wall_class = LedWallSettings

    def clear_project_settings(self):
        """
        Clear the project settings and restore them to the defaults
        """
        self._project_settings = ProjectSettingsBaseModel()
        self._led_walls:List[LedWallSettings] = []

    @property
    def custom_logo_path(self) -> str:
        """ The filepath to the custom logo for the pattern generation

        Returns:
            str: The filepath to the custom logo for the pattern generation
        """
        return self._project_settings.custom_logo_path

    @custom_logo_path.setter
    def custom_logo_path(self: ProjectSettings, value: str):
        """Set the filepath to the custom logo for the pattern generation

        Args:
            value (bool): File path to a custom logo
        """
        self._project_settings.custom_logo_path = value

    @property
    def project_custom_primaries(self) -> Dict[str, List[List[float]]]:
        """ Gets all the custom primaries for the project

        Returns:
            dict: The dictionary of the custom primaries
        """
        return self._project_settings.project_custom_primaries

    @project_custom_primaries.setter
    def project_custom_primaries(self: ProjectSettings, value: Dict[str, List[List[float]]]):
        """ Sets the custom primaries to use for the project

        Args:
            value: The dictionary for the custom primaries
        """
        self._project_settings.project_custom_primaries = value

    def add_custom_primary(self: ProjectSettings, name: str, primaries: List[List[float]]):
        """ Adds a custom primary to the project

        Args:
            name (str): The name of the custom primary
            primaries (List[float]): The list of primaries to add
        """
        if name in self._project_settings.project_custom_primaries:
            raise ValueError(f'Custom primary {name} already exists')

        self._project_settings.project_custom_primaries[name] = primaries

    @property
    def project_id(self) -> str:
        """Get the project id for the current project

        Returns:
            str: The project id for the current project
        """
        # project_id will be generated by default if not exists
        return self._project_settings.project_id

    @project_id.setter
    def project_id(self: ProjectSettings, value: str):
        """Set the project id to the given value

        Args:
            value (str): The project id we want to set
        """
        self._project_settings.project_id = value

    @property
    def file_format(self) -> constants.FileFormats:
        """Get the file format we want to generate patterns to

        Returns:
            constants.FileFormats: The file format we want to generate patterns to
        """
        return self._project_settings.file_format

    @file_format.setter
    def file_format(self: ProjectSettings, value: constants.FileFormats):
        """Set the file format we want to generate patterns to

        Args:
            value (constants.FileFormats): The file format we want to generate patterns to
        """
        self._project_settings.file_format = value

    @property
    def frames_per_patch(self) -> int:
        """Get the number of frames per patch we want to generate

        Returns:
            int: The number of frames per patch to generate
        """
        return self._project_settings.frames_per_patch

    @frames_per_patch.setter
    def frames_per_patch(self: ProjectSettings, value: int):
        """ The number of frames per patch we want to generate

        Args:
            value (int): The number of frames per patch we want to generate
        """
        self._project_settings.frames_per_patch = value

    @property
    def led_walls(self) -> List[LedWallSettings]:
        """Return the LED walls in the project

        Returns:
            list: The list of led walls stored in the project
        """
        return self._led_walls

    @led_walls.setter
    def led_walls(self: ProjectSettings, value: List[LedWallSettings]):
        """Set the LED walls config path.

        Args:
            value (list): A list of led walls we want to store in the project
        """
        walls = []
        for wall in value:
            if isinstance(wall, self._led_wall_class):
                walls.append(wall)
            else:
                raise ValueError(f'Wall {wall} is not an instance of {self._led_wall_class.__name__}')
        self._led_walls = walls

    @property
    def ocio_config_path(self) -> str:
        """ Return the OCIO config path we want to use as a base for the exported ocio config.

        Returns:
            str: The OCIO config path.
        """
        return self._project_settings.ocio_config_path

    @ocio_config_path.setter
    def ocio_config_path(self: ProjectSettings, value: str):
        """Set the OCIO config path used as the base for writing out the resulting ocio config. This is not used for
            any internal computation


        Args:
            value (str): The OCIO config path.
        """
        self._project_settings.ocio_config_path = value

    @property
    def output_folder(self) -> str:
        """Return the output folder we want to write our patches, luts, and configs too.

        Returns:
            str: The folder path
        """
        return self._project_settings.output_folder

    @output_folder.setter
    def output_folder(self: ProjectSettings, value: str):
        """Set the folder path for the output folder

        Args:
            value (str): The folder path for the outputs
        """
        self._project_settings.output_folder = value

    @property
    def resolution_width(self) -> int:
        """Returns the resolution width of the patterns we are going to generate

        Returns:
            int: The resolution width of the patterns we are going to generate
        """
        return self._project_settings.resolution_width

    @resolution_width.setter
    def resolution_width(self: ProjectSettings, value: int):
        """Sets the resolution width of the patterns we want to generate

        Args:
            value (int): The resolution width
        """
        self._project_settings.resolution_width = value

    @property
    def resolution_height(self) -> int:
        """Returns the resolution height of the patterns we are going to generate

        Returns:
            int: The resolution height of the patterns we are going to generate
        """
        return self._project_settings.resolution_height

    @resolution_height.setter
    def resolution_height(self: ProjectSettings, value: int):
        """Sets the resolution height of the patterns we want to generate

        Args:
            value (int): The resolution height
        """
        self._project_settings.resolution_height = value

    @property
    def reference_gamut(self) -> constants.ColourSpace|str:
        """ Returns the reference colorspace of the working space

        Returns:
            constants.ColourSpace: Returns the reference colorspace of the working space
        """
        return self._project_settings.reference_gamut

    @reference_gamut.setter
    def reference_gamut(self: ProjectSettings, value: constants.ColourSpace|str):
        """ Set the reference colorspace of the working space, defaults to ACES2065-1
            should only be set with extreme care, as other working spaces
            not fully supported

        Args:
            value (constants.ColourSpace): The colour space we want to set the input too for the plate
        """
        self._project_settings.reference_gamut = value

    @property
    def frame_rate(self) -> constants.FrameRates|float:
        """ The frame rate for the shooting frame rate for the camera, used in certain SPG patterns

        Returns:
            float: The shooting frame rate of the camera
        """
        return self._project_settings.frame_rate

    @frame_rate.setter
    def frame_rate(self: ProjectSettings, value: constants.FrameRates|float):
        """ Sets the frame rate for the shooting frame rate

        Args:
            value (float): The frame rate we want to set
        """
        self._project_settings.frame_rate = value

    @property
    def export_lut_for_aces_cct(self) -> bool:
        """ Get whether we want to export out lut for aces cct

        Returns:
            bool: Whether we want out luts to be exported for aces cct
        """
        return self._project_settings.export_lut_for_aces_cct

    @export_lut_for_aces_cct.setter
    def export_lut_for_aces_cct(self: ProjectSettings, value: bool):
        """ Set whether we want to export out lut for aces cct

        Args:
            value (bool): Set whether we want to export out lut for aces cct
        """
        self._project_settings.export_lut_for_aces_cct = value

    @property
    def export_lut_for_aces_cct_in_target_out(self) -> bool:
        """ Get whether we want to export out lut for aces cct in and target out

        Returns:
            bool: Whether we want our luts to be exported for aces cct, with cct in and target out
        """
        return self._project_settings.export_lut_for_aces_cct_in_target_out

    @export_lut_for_aces_cct_in_target_out.setter
    def export_lut_for_aces_cct_in_target_out(self: ProjectSettings, value: bool):
        """ Set whether we want to export out lut for aces cct with aces cct in and target out

        Args:
            value (bool): Set whether we want to export out lut for aces cct, with cct in and target out
        """
        self._project_settings.export_lut_for_aces_cct_in_target_out = value

    @property
    def content_max_lum(self) -> float:
        """Get the content max luminance for the project

        Returns:
            int: The content max luminance for the project
        """
        # content_max_lum will be set to PQ_MAX_NITS by default when v1.x is loaded
        return self._project_settings.content_max_lum

    @content_max_lum.setter
    def content_max_lum(self: ProjectSettings, value: float):
        """Set the content max luminance for the project

        Args:
            value (int): The content max luminance for the project
        """
        self._project_settings.content_max_lum = value

    @property
    def lut_size(self):
        """Get the size of the lut for the project

        Returns:
            int: The size of the luz for the project
        """
        # lut_size will be set to DEFAULT_LUZ_SIZE by default when v1.x is loaded
        return self._project_settings.lut_size

    @lut_size.setter
    def lut_size(self: ProjectSettings, value: int):
        """Set the size of the lut for the project

        Args:
            value (int): The size of the lut for the project
        """
        self._project_settings.lut_size = value

    @classmethod
    def from_json(cls: Type[ProjectSettings], json_file: str, led_wall_class: Type[LedWallSettings] = LedWallSettings) -> ProjectSettings:
        """Create a ProjectSettings object from a JSON file.

        Args:
            json_file (str): The path to the JSON file.
            led_wall_class (Type): The class type of the LedWallSettings
                to use for the project settings

        Returns:
            ProjectSettings: A ProjectSettings object.
        """
        data = cls._settings_from_json_file(json_file)
        if not data[constants.OpenVPCalSettingsKeys.PROJECT_SETTINGS]:
            raise ValueError(f'No project settings found in {json_file}')
        return cls.from_dict(data, led_wall_class=led_wall_class)

    @classmethod
    def _settings_from_json_file(cls, json_file) -> dict:
        """ Load the project settings from a JSON file.

        Args:
            json_file: The path to the JSON file.

        Returns: The project settings

        """
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data

    def to_json(self: ProjectSettings, json_file: str):
        """Save the ProjectSettings object to a JSON file.

        Args:
            json_file (str): The path to the JSON file.
        """
        with open(json_file, 'w', encoding='utf-8') as file:
            file.write(self.get_open_vp_cal_model().model_dump_json(indent=4))

    @classmethod
    def from_dict(cls, data: dict, led_wall_class: Type[LedWallSettings] = LedWallSettings) -> ProjectSettings:
        """
        Creates a ProjectSettings object from a dictionary.

        Note that input <data> will be modified.

        Args:
            data (dict):from_dict The dictionary to create the ProjectSettings object from
            led_wall_class (Type): The class type of the LedWallSettings to use for the project settings

        Returns:
            ProjectSettings
        """
        instance: ProjectSettings = cls()
        instance._led_wall_class = led_wall_class
        instance._project_settings = ProjectSettingsBaseModel.model_validate(
            data[constants.OpenVPCalSettingsKeys.PROJECT_SETTINGS])

        walls = []
        for wall in instance._project_settings.led_walls:
            wall_inst = led_wall_class.from_dict(instance, wall.model_dump())
            walls.append(wall_inst)

        instance.led_walls = walls
        return instance

    def to_dict(self) -> Dict:
        """ Save the ProjectSettings to a dict which can be serialized to JSON

        Returns: Dict

        """
        return self.get_open_vp_cal_model().model_dump()

    def get_open_vp_cal_model(self) -> OpenVPCalSettingsModel:
        openVpCalSettings = OpenVPCalSettingsModel()
        openVpCalSettings.openvp_cal_version = open_vp_cal.__version__
        openVpCalSettings.project_settings = self._project_settings
        openVpCalSettings.project_settings.led_walls = [led_wall._led_settings for led_wall in self.led_walls]
        return openVpCalSettings

    def add_led_wall(self: ProjectSettings, name: str) -> LedWallSettings:
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

    def copy_led_wall(self: ProjectSettings, existing_wall_name, new_name: str) -> LedWallSettings:
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

    def add_verification_wall(self: ProjectSettings, existing_wall_name: str) -> LedWallSettings:
        """ Adds a new LED wall to the project settings which mirrors all the settings from the existing wall,
            and whose settings cannot be changed directly, only via the parent

            The verification wall is prefixed with Verify and is used to verify that when the calibration sequence is recorded with the calibration applied, the results match closely to the expected calibration.

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

    def remove_led_wall(self: ProjectSettings, name: str):
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

    def get_led_wall(self: ProjectSettings, name: str) -> LedWallSettings:
        """ Returns a LED wall from the project

        Args:
            name (str): The name of the LED wall we want to get
        """
        for wall in self.led_walls:
            if wall.name == name:
                return wall
        raise ValueError(f'Led wall {name} not found')

    @property
    def export_folder(self: ProjectSettings) -> str:
        """ Returns the folder to export the calibration results to

        Returns:
            str: The folder to export the calibration results to
        """
        return os.path.join(self.output_folder, constants.ProjectFolders.EXPORT)

    def reset_led_wall(self: ProjectSettings, name: str) -> None:
        """ Resets a LED wall to the default settings but preserves the link to the verification wall

        Args:
            name (str): The name of the LED wall we want to reset
        """
        led_wall = self.get_led_wall(name)
        verification_wall = led_wall.verification_wall
        led_wall.verification_wall = ""
        led_wall.reset_defaults()
        led_wall.verification_wall = verification_wall

    def get_ocio_colorspace_names(self: ProjectSettings)-> list[str]:
        """ Gets the colour space names from either the project ocio config, or the
            default config

        Returns:
            Returns a list of strings for the names of the available colour configs
        """
        config_path = self.ocio_config_path
        if not config_path:
            config_path = ResourceLoader.ocio_config_path()
        return ocio_utils.get_colorspace_names(config_path)
