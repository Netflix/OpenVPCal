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
import copy
import json
from typing import List, Union, Any

from open_vp_cal.core import constants
from open_vp_cal.core.structures import ProcessingResults
from open_vp_cal.framework.sequence_loader import SequenceLoader


class LedWallSettings:
    """A class to handle led wall settings."""
    def __init__(self, project_settings: "ProjectSettings", name="Wall1"):
        """Initialize an empty LedWallSettings object."""
        self.processing_results = ProcessingResults()
        self.separation_results = None
        self.project_settings = project_settings

        self._sequence_loader = None
        self._sequence_loader_class = SequenceLoader

        self._default_led_settings = {
            constants.LedWallSettingsKeys.NAME: name,
            constants.LedWallSettingsKeys.ENABLE_EOTF_CORRECTION: True,
            constants.LedWallSettingsKeys.ENABLE_GAMUT_COMPRESSION: True,
            constants.LedWallSettingsKeys.AUTO_WB_SOURCE: False,
            constants.LedWallSettingsKeys.INPUT_SEQUENCE_FOLDER: '',
            constants.LedWallSettingsKeys.NUM_GREY_PATCHES: 33,
            constants.LedWallSettingsKeys.PRIMARIES_SATURATION: 0.7,
            constants.LedWallSettingsKeys.CALCULATION_ORDER: constants.CalculationOrder.CO_DEFAULT,
            constants.LedWallSettingsKeys.INPUT_PLATE_GAMUT: constants.ColourSpace.CS_DEFAULT_REF,
            constants.LedWallSettingsKeys.NATIVE_CAMERA_GAMUT: constants.CameraColourSpace.CS_DEFAULT,
            constants.LedWallSettingsKeys.REFERENCE_TO_TARGET_CAT: constants.CAT.CAT_BRADFORD,
            constants.LedWallSettingsKeys.ROI: [],
            constants.LedWallSettingsKeys.SHADOW_ROLLOFF: 0.008,
            constants.LedWallSettingsKeys.TARGET_MAX_LUM_NITS: 1000,
            constants.LedWallSettingsKeys.TARGET_GAMUT: constants.ColourSpace.CS_DEFAULT_TARGET,
            constants.LedWallSettingsKeys.TARGET_EOTF: constants.EOTF.EOTF_DEFAULT,
            constants.LedWallSettingsKeys.TARGET_TO_SCREEN_CAT: constants.CAT.CAT_NONE,
            constants.LedWallSettingsKeys.MATCH_REFERENCE_WALL: False,
            constants.LedWallSettingsKeys.REFERENCE_WALL: "",
            constants.LedWallSettingsKeys.USE_WHITE_POINT_OFFSET: False,
            constants.LedWallSettingsKeys.WHITE_POINT_OFFSET_SOURCE: "",
            constants.LedWallSettingsKeys.IS_VERIFICATION_WALL: False,
            constants.LedWallSettingsKeys.VERIFICATION_WALL: "",
            constants.LedWallSettingsKeys.AVOID_CLIPPING: False
        }

        self._led_settings = copy.deepcopy(self._default_led_settings)

    def reset_defaults(self):
        """Reset the LedWallSettings object to its default values."""
        for key, value in self._default_led_settings.items():
            self._set_property(key, value)

    def _set_property(self, field_name: str, value: Any) -> None:
        """ Sets the internal property data stores for the given field name, and given value.
            If the led wall is a verification wall, it will not set the verification wall's settings
            If the led wall has a verification wall, it will also set the value on the verification wall

        Args:
            field_name: The name of the property to set in the data store
            value: The value we want to set the property to
        """
        if self.is_verification_wall:
            return

        self._led_settings[field_name] = value

        if not self.verification_wall_as_wall:
            return
        self.verification_wall_as_wall._led_settings[field_name] = value

    @property
    def name(self) -> str:
        """The name of the LED wall

        Returns:
            str: A list of custom primaries and a custom name for led wall we are calibrating
        """
        return self._led_settings[constants.LedWallSettingsKeys.NAME]

    @name.setter
    def name(self, value: str):
        """ Sets the name of the LED wall

        Args:
            value (str): The name of the LED wall
        """
        self._led_settings[constants.LedWallSettingsKeys.NAME] = value

    def clear_led_settings(self):
        """
        Clear the LED settings and restore them to the defaults
        """
        self._led_settings = copy.deepcopy(self._default_led_settings)

    @property
    def avoid_clipping(self) -> bool:
        """ Whether we want to avoid clipping by the LED wall.
        Ensures that we scale the results of the calibrations down to ensure that any values pushed above the actual
        peak are scaled back

        Returns:
            bool: Whether we want to avoid clipping or not
        """
        return self._led_settings[constants.LedWallSettingsKeys.AVOID_CLIPPING]

    @avoid_clipping.setter
    def avoid_clipping(self, value: bool):
        """ Set whether we want to avoid clipping on the LED wall or not

        Args:
            value (bool): Whether we want to avoid clipping on the LED wall or not
        """
        self._set_property(constants.LedWallSettingsKeys.AVOID_CLIPPING, value)

    @property
    def enable_eotf_correction(self) -> bool:
        """Whether enable eotf correction is enabled or disabled

        Returns:
            bool: Whether eotf correction is enabled or disabled
        """
        return self._led_settings[constants.LedWallSettingsKeys.ENABLE_EOTF_CORRECTION]

    @enable_eotf_correction.setter
    def enable_eotf_correction(self, value: bool):
        """Set the eotf correction to be enabled or disabled

        Args:
            value (bool): Whether eotf correction is enabled or disabled
        """
        self._set_property(constants.LedWallSettingsKeys.ENABLE_EOTF_CORRECTION, value)

    @property
    def enable_gamut_compression(self) -> bool:
        """Whether enable gamut compression is enabled or disabled

        Returns:
            bool: Whether enable gamut compression is enabled or disabled
        """
        return self._led_settings[constants.LedWallSettingsKeys.ENABLE_GAMUT_COMPRESSION]

    @enable_gamut_compression.setter
    def enable_gamut_compression(self, value: bool):
        """Set the gamut compression to be enabled or disabled

        Args:
            value (bool): Whether enable gamut compression is enabled or disabled
        """
        self._set_property(constants.LedWallSettingsKeys.ENABLE_GAMUT_COMPRESSION, value)

    @property
    def auto_wb_source(self) -> bool:
        """Whether auto-white-balance is enabled or disabled

        Returns:
            bool: Whether auto white balance is enabled or disabled
        """
        return self._led_settings[constants.LedWallSettingsKeys.AUTO_WB_SOURCE]

    @auto_wb_source.setter
    def auto_wb_source(self, value: bool):
        """Set the auto white balance to be enabled or disabled

        Args:
            value (bool): Whether auto white balance is enabled or disabled
        """
        self._set_property(constants.LedWallSettingsKeys.AUTO_WB_SOURCE, value)

    @property
    def input_sequence_folder(self) -> str:
        """ Return the input sequence folder.

        Returns:
            str: The input sequence folder.
        """
        return self._led_settings[constants.LedWallSettingsKeys.INPUT_SEQUENCE_FOLDER]

    @input_sequence_folder.setter
    def input_sequence_folder(self, value: str):
        """Set the input sequence folder. We do not set this on the verification wall as this needs to be unique

        Args:
            value (str): The input sequence folder.
        """
        self._led_settings[constants.LedWallSettingsKeys.INPUT_SEQUENCE_FOLDER] = value

    @property
    def calculation_order(self) -> constants.CalculationOrder:
        """Return the Calculation Order

        Returns:
            constants.CalculationOrder: The calculation order of the calculations
        """
        return self._led_settings[constants.LedWallSettingsKeys.CALCULATION_ORDER]

    @calculation_order.setter
    def calculation_order(self, value: str):
        """Set the Calculation Order

        Args:
            value (constants.CalculationOrder): The calculation order of the calculations
        """
        self._set_property(constants.LedWallSettingsKeys.CALCULATION_ORDER, value)

    @property
    def primaries_saturation(self) -> float:
        """Return the primaries' saturation.

        Returns:
            float: The primaries saturation.
        """
        return self._led_settings[constants.LedWallSettingsKeys.PRIMARIES_SATURATION]

    @primaries_saturation.setter
    def primaries_saturation(self, value: float):
        """Set the primaries' saturation.

        Args:
            value (float): The primaries saturation.
        """
        self._set_property(constants.LedWallSettingsKeys.PRIMARIES_SATURATION, value)

    @property
    def input_plate_gamut(self) -> constants.ColourSpace:
        """Returns the input colorspace of the plate

        Returns:
            constants.ColourSpace: The input colorspace of the plate
        """
        return self._led_settings[constants.LedWallSettingsKeys.INPUT_PLATE_GAMUT]

    @input_plate_gamut.setter
    def input_plate_gamut(self, value: constants.ColourSpace):
        """Set the reference colorspace of the plate

        Args:
            value (constants.ColourSpace): The colour space we want to set the input too for the plate
        """
        self._set_property(constants.LedWallSettingsKeys.INPUT_PLATE_GAMUT, value)

    @property
    def native_camera_gamut(self) -> constants.CameraColourSpace:
        """Returns the native colorspace of the camera the plate was shot with originally

        Returns:
            constants.ColourSpace: The native colorspace of the camera the plate was shot with originally
        """
        return self._led_settings[constants.LedWallSettingsKeys.NATIVE_CAMERA_GAMUT]

    @native_camera_gamut.setter
    def native_camera_gamut(self, value: constants.CameraColourSpace):
        """Set the native colorspace of the camera the plate was shot with originally

        Args:
            value (constants.CameraColourSpace): The native colorspace of the camera the plate was shot with originally
        """
        self._set_property(constants.LedWallSettingsKeys.NATIVE_CAMERA_GAMUT, value)

    @property
    def num_grey_patches(self) -> int:
        """Return the num_grey_patches.

        Returns:
            int: The number of grey patches used to ramp the number of nits
        """
        return self._led_settings[constants.LedWallSettingsKeys.NUM_GREY_PATCHES]

    @num_grey_patches.setter
    def num_grey_patches(self, value: int):
        """Set the num_grey_patches.

        Args:
            value (int): The number of grey patches used to ramp the number of nits
        """
        self._set_property(constants.LedWallSettingsKeys.NUM_GREY_PATCHES, value)

    @property
    def reference_to_target_cat(self) -> constants.CAT:
        """Returns the reference to target cat

        Returns:
            constants.ColourSpace: The reference to target cat
        """
        return self._led_settings[constants.LedWallSettingsKeys.REFERENCE_TO_TARGET_CAT]

    @reference_to_target_cat.setter
    def reference_to_target_cat(self, value: constants.CAT):
        """Set the reference to target cat

        Args:
            value (constants.CAT): The reference to a target cat
        """
        self._set_property(constants.LedWallSettingsKeys.REFERENCE_TO_TARGET_CAT, value)

    @property
    def roi(self) -> List[int]:
        """Return the region of interest (ROI).

        Returns:
            Any: The region of interest (ROI).
        """

        return self._led_settings[constants.LedWallSettingsKeys.ROI]

    @roi.setter
    def roi(self, value: List[int]):
        """ Set the region of interest (ROI). We do not set this on the verification wall as this needs to be unique

        Args:
            value (Any): The region of interest (ROI).
        """
        self._led_settings[constants.LedWallSettingsKeys.ROI] = value

    @property
    def shadow_rolloff(self) -> float:
        """Returns the shadow rolloff

        Returns:
            float: The shadow rolloff
        """
        return self._led_settings[constants.LedWallSettingsKeys.SHADOW_ROLLOFF]

    @shadow_rolloff.setter
    def shadow_rolloff(self, value: float):
        """Set the shadow rolloff

        Args:
            value (float): the shadow rolloff
        """
        self._set_property(constants.LedWallSettingsKeys.SHADOW_ROLLOFF, value)

    @property
    def target_gamut(self) -> constants.ColourSpace:
        """Returns the target colorspace

        Returns:
            constants.ColourSpace: The target colorspace
        """
        return self._led_settings[constants.LedWallSettingsKeys.TARGET_GAMUT]

    @target_gamut.setter
    def target_gamut(self, value: constants.ColourSpace):
        """Set the target colorspace

        Args:
            value (constants.ColourSpace): the colour space we want to set the target as
        """
        self._set_property(constants.LedWallSettingsKeys.TARGET_GAMUT, value)

    @property
    def target_eotf(self) -> constants.EOTF:
        """Returns the target eotf

        Returns:
            constants.EOTF: The target eotf
        """
        return self._led_settings[constants.LedWallSettingsKeys.TARGET_EOTF]

    @target_eotf.setter
    def target_eotf(self, value: constants.EOTF):
        """Set the target eotf, which also forces the target max lum to be 100, if not using PQ.

        Args:
            value (constants.EOTF): the eotf for the target
        """
        self._set_property(constants.LedWallSettingsKeys.TARGET_EOTF, value)
        if value != constants.EOTF.EOTF_ST2084:
            self._set_property(constants.LedWallSettingsKeys.TARGET_MAX_LUM_NITS, constants.TARGET_MAX_LUM_NITS_NONE_PQ)

    @property
    def target_max_lum_nits(self) -> int:
        """Return the target max luminance in nits.

        Returns:
            int: target max luminance in nits.
        """
        return self._led_settings[constants.LedWallSettingsKeys.TARGET_MAX_LUM_NITS]

    @target_max_lum_nits.setter
    def target_max_lum_nits(self, value: int):
        """ Set the target max luminance in nits, unless you are using an eotf which is not PQ, in which case
           we force 100 nits, aka 1.0

        Args:
            value (int): target max luminance in nits.
        """
        if self.target_eotf != constants.EOTF.EOTF_ST2084:
            value = constants.TARGET_MAX_LUM_NITS_NONE_PQ
        self._set_property(constants.LedWallSettingsKeys.TARGET_MAX_LUM_NITS, value)

    @property
    def target_to_screen_cat(self) -> constants.CAT:
        """Returns the target screen cat

        Returns:
            constants.CAT: The target screen cat
        """
        return self._led_settings[constants.LedWallSettingsKeys.TARGET_TO_SCREEN_CAT]

    @target_to_screen_cat.setter
    def target_to_screen_cat(self, value: constants.CAT):
        """Set the target screen cat

        Args:
            value (constants.CAT): the target screen cat
        """
        self._set_property(constants.LedWallSettingsKeys.TARGET_TO_SCREEN_CAT, value)

    @classmethod
    def from_json_file(cls, project_settings: "ProjectSettings", json_file: str):
        """Create a LedWallSettings object from a JSON file.

        Args:
            project_settings (ProjectSettings): The project we want the LED wall to belong to
            json_file (str): The path to the JSON file.

        Returns:
            LedWallSettings: A LedWallSettings object.
        """
        json_data = cls._settings_from_json_file(json_file)
        return cls._from_json_data(project_settings, json_data)

    @classmethod
    def from_json_string(cls, project_settings: "ProjectSettings", json_string: str) -> "LedWallSettings":
        """ Creates a LedWallSettings object from a JSON string.

        Args:
            project_settings: The project we want the LED wall to belong to
            json_string: The JSON string representing the data of the LED wall

        Returns: A LedWallSettings object.

        """
        return cls._from_json_data(project_settings, json.loads(json_string))

    @classmethod
    def _from_json_data(cls, project_settings, json_data):
        instance = cls(project_settings)
        instance._led_settings = json_data
        return instance

    @classmethod
    def from_dict(cls, project_settings: "ProjectSettings", input_dict: dict) -> "LedWallSettings":
        """ Creates a LedWallSettings object from a dictionary.

        Args:
            project_settings:
            input_dict:

        Returns:

        """
        instance = cls(project_settings)
        for key in input_dict:
            setattr(instance, key, input_dict[key])
        return instance

    def to_dict(self) -> dict:
        """ Returns a dictionary representation of the LedWallSettings object.

        Returns: A dictionary representation of the LedWallSettings object.

        """
        return self._led_settings

    @classmethod
    def _settings_from_json_file(cls, json_file) -> dict:
        """ Returns the project settings from a JSON file.

        Args:
            json_file: The path to the JSON file.

        Returns: The project settings from a JSON file

        """
        with open(json_file, 'r', encoding='utf-8') as file:
            data = json.load(file)
        return data

    def to_json(self, json_file: str):
        """Save the LedWallSettings object to a JSON file.

        Args:
            json_file (str): The path to the JSON file.
        """
        with open(json_file, 'w', encoding='utf-8') as file:
            json.dump(self._led_settings, file, indent=4)

    @property
    def sequence_loader(self):
        """Returns the sequence loader for the LED wall"""
        if not self._sequence_loader:
            self._sequence_loader = self._sequence_loader_class(self)
        return self._sequence_loader

    @property
    def attrs(self) -> List[str]:
        """ Returns the attributes of the LedWallSettings object

        Returns: The attributes of the LedWallSettings object
        """
        return list(self._default_led_settings.keys())

    @property
    def match_reference_wall(self) -> bool:
        """ Whether we are using an external white point from a reference LED wall or not

        Returns:
            bool: Gets whether we want to use an external white point from a reference LED or not
        """
        return self._led_settings[constants.LedWallSettingsKeys.MATCH_REFERENCE_WALL]

    @match_reference_wall.setter
    def match_reference_wall(self, value: bool):
        """ Set whether we are using an external white point from a reference LED wall or not

        Args:
            value (bool): Whether to use the external white point from a reference LED or not
        """
        self._set_property(constants.LedWallSettingsKeys.MATCH_REFERENCE_WALL, value)

    @property
    def reference_wall(self) -> str:
        """ Get the reference wall we want to use as the external white point

        Returns:
            str: The name of the led wall we want to use as the reference wall
        """
        return self._led_settings[constants.LedWallSettingsKeys.REFERENCE_WALL]

    @property
    def reference_wall_as_wall(self) -> Union["LedWallSettings", None]:
        """ Get the reference wall we want to use as the external white point

        Returns:
            LedWallSettings: The LED wall we want to use as the reference wall
        """
        wall_name = self.reference_wall
        if wall_name:
            return self.project_settings.get_led_wall(wall_name)
        return None

    @reference_wall.setter
    def reference_wall(self, value: Union["LedWallSettings", str]):
        """ Set the reference wall we want to use as the external white point

        Args:
            value: The LED wall we want to set as the reference wall
        """
        if not value:
            self._led_settings[constants.LedWallSettingsKeys.REFERENCE_WALL] = value
            return

        if isinstance(value, LedWallSettings):
            value = value.name

        if value == self.name:
            raise ValueError("Cannot set the reference wall to be the same as the current wall")

        # We get the led wall to make sure it exists and is added to the project
        led_wall = self.project_settings.get_led_wall(value)

        self._set_property(constants.LedWallSettingsKeys.REFERENCE_WALL, led_wall.name)

    @property
    def use_white_point_offset(self) -> bool:
        """ Whether we are using a white point offset for the LED wall or not

        Returns:
            bool: Gets whether we want to use a white point offset or not
        """
        return self._led_settings[constants.LedWallSettingsKeys.USE_WHITE_POINT_OFFSET]

    @use_white_point_offset.setter
    def use_white_point_offset(self, value: bool):
        """ Set whether we are using a white point offset or not

        Args:
            value (bool): Whether to use the external white point or not
        """
        self._set_property(constants.LedWallSettingsKeys.USE_WHITE_POINT_OFFSET, value)

    @property
    def white_point_offset_source(self) -> str:
        """ The source which contains an image sample from which we want to calculate the white point offset from

        Returns:
            str: The filepath which contains the image we want to sample to calculate the white point offset from
        """
        return self._led_settings[constants.LedWallSettingsKeys.WHITE_POINT_OFFSET_SOURCE]

    @white_point_offset_source.setter
    def white_point_offset_source(self, value: str):
        """ Set the source which contains an image sample from which we want to calculate the white point offset from

        Args:
            value (str): The filepath which contains the image we want to sample to calculate the white point offset from
        """
        self._set_property(constants.LedWallSettingsKeys.WHITE_POINT_OFFSET_SOURCE, value)

    @property
    def verification_wall(self) -> str:
        """ Get the name of the led wall which this wall is linked to for verifying the calibration

        Returns:
            str: The name of the led wall which this wall linked for verification
        """
        return self._led_settings[constants.LedWallSettingsKeys.VERIFICATION_WALL]

    @property
    def verification_wall_as_wall(self) -> Union["LedWallSettings", None]:
        """ Get the led wall which this wall is linked to for verifying the calibration

        Returns:
            LedWallSettings: The LED wall this wall is linked to for verifying the calibration
        """
        wall_name = self.verification_wall
        if wall_name:
            return self.project_settings.get_led_wall(wall_name)
        return None

    @verification_wall.setter
    def verification_wall(self, value: Union["LedWallSettings", str]):
        """ Set the led wall which this wall is linked to verify the calibration.
            We do not directly set this on the verification wall as this needs to be a bidirectional link
            We leave the setting of this value to the api call within project settings to establish this link

        Args:
            value: The LED wall which this instance is intended to verify
        """
        if not value:
            self._led_settings[constants.LedWallSettingsKeys.VERIFICATION_WALL] = value
            return

        if isinstance(value, LedWallSettings):
            value = value.name

        if value == self.name:
            raise ValueError("Cannot set the verification wall to be the same as the current wall")

        # We get the led wall to make sure it exists and is added to the project
        led_wall = self.project_settings.get_led_wall(value)

        self._led_settings[constants.LedWallSettingsKeys.VERIFICATION_WALL] = led_wall.name

    @property
    def is_verification_wall(self) -> bool:
        """ Whether this wall is a verification wall which should take settings from the linked wall,
        or if this is the original wall which should be dictating the settings to the linked wall

        Returns:
            bool: Whether this wall is a verification wall or not
        """
        return self._led_settings[constants.LedWallSettingsKeys.IS_VERIFICATION_WALL]

    @is_verification_wall.setter
    def is_verification_wall(self, value: bool) -> None:
        """ Set whether this wall is a verification wall which should take settings from the linked wall,
            or if this is the original wall which should be dictating the settings to the linked wall

            We do not set this on the verification wall directly, as this needs to be unique we leave this
            to the project settings api to establish the correct values

        Args:
            value: Whether this wall is to be set as a Verification wall or not
        """
        self._led_settings[constants.LedWallSettingsKeys.IS_VERIFICATION_WALL] = value

    def has_valid_white_balance_options(self) -> bool:
        """ Checks whether the white balance options are valid or not, we can only have one of these options
            set at anyone time

        Returns: True or False depending on whether the white balance options are valid or not

        """
        values = [self.auto_wb_source, self.match_reference_wall, self.use_white_point_offset].count(True)
        if values > 1:
            return False
        return True
