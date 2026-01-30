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
from typing import Dict, List, Union, Any, Type, Optional
from pydantic import (
    BaseModel,
    Field,
    field_validator,
    field_serializer,
    model_validator,
    model_serializer,
    PrivateAttr,
    ConfigDict,
)

import open_vp_cal
from open_vp_cal.core import constants, ocio_utils, utils
from open_vp_cal.led_wall_settings import LedWallSettings
from open_vp_cal.core.resource_loader import ResourceLoader


class ProjectSettings(BaseModel):
    """A pydantic model class to handle project settings with serialization and business logic."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )

    # ===== Serialized Fields (from former ProjectSettingsBaseModel) =====
    openvp_cal_version: str = Field(default=open_vp_cal.__version__)
    content_max_lum: float = Field(default=constants.PQ.PQ_MAX_NITS)
    file_format: constants.FileFormats = Field(default=constants.FileFormats(constants.FileFormats.default()))
    resolution_width: int = Field(default=constants.DEFAULT_RESOLUTION_WIDTH)
    resolution_height: int = Field(default=constants.DEFAULT_RESOLUTION_HEIGHT)
    output_folder: str = Field(default=os.path.join(str(Path.home()), "OpenVPCal_output"))
    ocio_config_path: str = Field(default="")
    custom_logo_path: str = Field(default="")
    frames_per_patch: int = Field(default=1)
    reference_gamut: constants.ColourSpace | str = Field(default=constants.ColourSpace(constants.ColourSpace.CS_ACES))
    led_walls: List[LedWallSettings] = Field(default_factory=list)
    project_custom_primaries: Dict[str, List[List[float]]] = Field(default_factory=dict)
    frame_rate: constants.FrameRates | float = Field(default=constants.FrameRates(constants.FrameRates.default()))
    export_lut_for_aces_cct: bool = Field(default=False)
    export_lut_for_aces_cct_in_target_out: bool = Field(default=False)
    project_id: str = Field(default_factory=utils.generate_truncated_hash)
    lut_size: int = Field(default=constants.DEFAULT_LUZ_SIZE)

    # ===== Private Attributes (not in schema at all) =====
    _led_wall_class: Type[LedWallSettings] = PrivateAttr(default=LedWallSettings)

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
    def try_convert_to_enum_frame_rates(cls, value: Any) -> constants.FrameRates | float:
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

    @model_validator(mode='before')
    @classmethod
    def handle_nested_format(cls, data: Any) -> Any:
        """Handle loading old nested JSON format.

        Old format: {"openvp_cal_version": "...", "project_settings": {...}}
        New format: direct fields
        """
        if isinstance(data, dict) and constants.OpenVPCalSettingsKeys.PROJECT_SETTINGS in data:
            # Old nested format - extract inner project_settings and version
            inner = data[constants.OpenVPCalSettingsKeys.PROJECT_SETTINGS].copy()
            inner['openvp_cal_version'] = data.get(
                constants.OpenVPCalSettingsKeys.VERSION,
                open_vp_cal.__version__
            )
            return inner
        return data

    @model_serializer(mode='wrap')
    def serialize_nested(self, handler) -> dict:
        """Output backwards-compatible nested JSON format."""
        data = handler(self)
        version = data.pop('openvp_cal_version', open_vp_cal.__version__)
        return {
            constants.OpenVPCalSettingsKeys.VERSION: version,
            constants.OpenVPCalSettingsKeys.PROJECT_SETTINGS: data
        }

    def __init__(self, led_wall_class: Optional[Type[LedWallSettings]] = None, **data):
        """Initialize a ProjectSettings object.

        Args:
            led_wall_class: Optional custom LedWallSettings class to use
            **data: Field values to initialize
        """
        super().__init__(**data)
        if led_wall_class is not None:
            self._led_wall_class = led_wall_class
        else:
            self._led_wall_class = LedWallSettings

        # Ensure all led walls have reference to this project
        for wall in self.led_walls:
            wall._project_settings = self

    def clear_project_settings(self):
        """Clear the project settings and restore them to the defaults."""
        defaults = ProjectSettings()

        # Copy all field values from defaults
        for field_name in ProjectSettings.model_fields:
            if field_name != 'openvp_cal_version':
                setattr(self, field_name, getattr(defaults, field_name))

    def add_custom_primary(self, name: str, primaries: List[List[float]]):
        """ Adds a custom primary to the project

        Args:
            name (str): The name of the custom primary
            primaries (List[float]): The list of primaries to add
        """
        if name in self.project_custom_primaries:
            raise ValueError(f'Custom primary {name} already exists')

        self.project_custom_primaries[name] = primaries

    @classmethod
    def from_json(
        cls,
        json_file: str,
        led_wall_class: Type[LedWallSettings] = LedWallSettings
    ) -> ProjectSettings:
        """Create a ProjectSettings object from a JSON file.

        Args:
            json_file (str): The path to the JSON file.
            led_wall_class (Type): The class type of the LedWallSettings
                to use for the project settings

        Returns:
            ProjectSettings: A ProjectSettings object.
        """
        data = cls._settings_from_json_file(json_file)
        return cls.from_dict(data, led_wall_class=led_wall_class)

    @classmethod
    def _settings_from_json_file(cls, json_file: str) -> dict:
        """ Load the project settings from a JSON file.

        Args:
            json_file: The path to the JSON file.

        Returns: The project settings

        """
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data

    def to_json(self, json_file: str):
        """Save the ProjectSettings object to a JSON file.

        Args:
            json_file (str): The path to the JSON file.
        """
        with open(json_file, 'w', encoding='utf-8') as file:
            file.write(self.model_dump_json(indent=4))

    @classmethod
    def from_dict(
        cls,
        data: dict,
        led_wall_class: Type[LedWallSettings] = LedWallSettings
    ) -> ProjectSettings:
        """
        Creates a ProjectSettings object from a dictionary.

        Args:
            data (dict): The dictionary to create the ProjectSettings object from
            led_wall_class (Type): The class type of the LedWallSettings to use for the project settings

        Returns:
            ProjectSettings
        """
        # The model_validator handles nested format conversion
        instance = cls.model_validate(data)
        instance._led_wall_class = led_wall_class

        # Recreate led walls with proper class and project reference
        walls = []
        for wall in instance.led_walls:
            wall_dict = wall.model_dump() if isinstance(wall, BaseModel) else wall
            wall_inst = led_wall_class.from_dict(instance, wall_dict)
            walls.append(wall_inst)

        instance.led_walls = walls
        return instance

    def to_dict(self) -> Dict:
        """ Save the ProjectSettings to a dict which can be serialized to JSON

        Returns: Dict

        """
        return self.model_dump()

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

        led_wall = self._led_wall_class(self, name=name)
        self.led_walls.append(led_wall)
        return led_wall

    def copy_led_wall(self, existing_wall_name: str, new_name: str) -> LedWallSettings:
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

    @property
    def export_folder(self) -> str:
        """ Returns the folder to export the calibration results to

        Returns:
            str: The folder to export the calibration results to
        """
        return os.path.join(self.output_folder, constants.ProjectFolders.EXPORT)

    def reset_led_wall(self, name: str) -> None:
        """ Resets a LED wall to the default settings but preserves the link to the verification wall

        Args:
            name (str): The name of the LED wall we want to reset
        """
        led_wall = self.get_led_wall(name)
        verification_wall = led_wall.verification_wall
        led_wall.verification_wall = ""
        led_wall.reset_defaults()
        led_wall.verification_wall = verification_wall

    def get_ocio_colorspace_names(self) -> list[str]:
        """ Gets the colour space names from either the project ocio config, or the
            default config

        Returns:
            Returns a list of strings for the names of the available colour configs
        """
        config_path = self.ocio_config_path
        if not config_path:
            config_path = ResourceLoader.ocio_config_path()
        return ocio_utils.get_colorspace_names(config_path)
