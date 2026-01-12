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
import json
from typing import List, Union, Any, Optional
from typing import TYPE_CHECKING
from pydantic import BaseModel, Field, field_validator, PrivateAttr, ConfigDict
from pydantic.json_schema import SkipJsonSchema

from open_vp_cal.core import constants
from open_vp_cal.core.structures import ProcessingResults
from open_vp_cal.framework.sequence_loader import SequenceLoader
from open_vp_cal.framework.identify_separation import SeparationResults

if TYPE_CHECKING:
    from open_vp_cal.project_settings import ProjectSettings


class LedWallSettings(BaseModel):
    """A pydantic model class to handle led wall settings with serialization and business logic."""

    model_config = ConfigDict(
        arbitrary_types_allowed=True,
        validate_assignment=True,
    )

    # ===== Serialized Fields (from former LedWallSettingsBaseModel) =====
    name: str = Field(default="Wall1")
    avoid_clipping: bool = Field(default=False)
    enable_eotf_correction: bool = Field(default=True)
    enable_gamut_compression: bool = Field(default=True)
    auto_wb_source: bool = Field(default=False)
    input_sequence_folder: str = Field(default="")
    num_grey_patches: int = Field(default=30, ge=0, le=100)
    primaries_saturation: float = Field(default=0.7, ge=0, le=1)
    calculation_order: constants.CalculationOrder = Field(
        default=constants.CalculationOrder(constants.CalculationOrder.default())
    )
    input_plate_gamut: constants.ColourSpace | str = Field(
        default=constants.ColourSpace(constants.ColourSpace.default_ref())
    )
    native_camera_gamut: constants.CameraColourSpace | str = Field(
        default=constants.CameraColourSpace(constants.CameraColourSpace.default())
    )
    reference_to_target_cat: constants.CAT = Field(
        default=constants.CAT(constants.CAT.CAT_BRADFORD)
    )
    roi: List[List[int]] = Field(
        default=[],
        description="roi is consist of 4 points [[tl.x,tl.y],[tr.x,tr.y],[br.x,br.y],[bl.x,bl.y]]"
    )
    shadow_rolloff: float = Field(default=0.008)
    target_max_lum_nits: int = Field(default=1000, ge=0, le=constants.PQ.PQ_MAX_NITS)
    target_gamut: constants.LedColourSpace | str = Field(
        default=constants.LedColourSpace(constants.LedColourSpace.default_target())
    )
    target_eotf: constants.EOTF = Field(
        default=constants.EOTF(constants.EOTF.default())
    )
    target_to_screen_cat: constants.CAT = Field(default=constants.CAT.CAT_NONE)
    match_reference_wall: bool = Field(default=False)
    reference_wall: str = Field(default="")
    white_point_offset_source: str = Field(default="")
    use_white_point_offset: bool = Field(default=False)
    is_verification_wall: bool = Field(default=False)
    verification_wall: str = Field(default="")

    # ===== Runtime Fields (excluded from serialization) =====
    processing_results: SkipJsonSchema[ProcessingResults] = Field(
        default_factory=ProcessingResults,
        exclude=True
    )
    separation_results: SkipJsonSchema[Optional[SeparationResults]] = Field(
        default=None,
        exclude=True
    )

    # ===== Private Attributes (not in schema at all) =====
    _sequence_loader: Optional[SequenceLoader] = PrivateAttr(default=None)
    _sequence_loader_class: type = PrivateAttr(default=SequenceLoader)
    _project_settings: Optional["ProjectSettings"] = PrivateAttr(default=None)

    @field_validator(
        "roi",
        mode="before",
        json_schema_input_type=Union[List[int], List[List[int]]]
    )
    @classmethod
    def upgrade_roi(cls, value: Any) -> List[List[int]]:
        """
        Upgrade roi data structure
        - version 1.x: [x, y, width, height]
        - version 2.x: [[tl.x, tl.y], [tr.x, tr.y], [br.x, br.y], [bl.x, bl.y]]
        Parameters:
            value: roi in type of either List[int] or List[List[int]]
        Returns:
            list: A list of four lists representing the corners in the following order:
                  top left, top right, bottom right, bottom left.
        """
        if isinstance(value, list) and len(value) == 4 and all(isinstance(e, int) for e in value):
            left, right, top, bottom = value
            top_left: List[int] = [left, top]
            top_right: List[int] = [right, top]
            bottom_right: List[int] = [right, bottom]
            bottom_left: List[int] = [left, bottom]
            return [top_left, top_right, bottom_right, bottom_left]
        return value

    def __init__(self, project_settings: Optional["ProjectSettings"] = None, **data):
        """Initialize a LedWallSettings object.

        Args:
            project_settings: The project this LED wall belongs to
            **data: Field values to initialize
        """
        super().__init__(**data)
        self._project_settings = project_settings
        self._sequence_loader = None
        self._sequence_loader_class = SequenceLoader

    def __setattr__(self, name: str, value: Any) -> None:
        """Custom setattr to handle verification wall linking and validation.

        For linked properties:
        - Verification walls cannot modify these (changes are ignored)
        - Parent walls propagate changes to their verification wall

        For reference_wall and verification_wall:
        - Validates the wall exists and isn't itself

        For target_eotf:
        - Sets target_max_lum_nits appropriately for non-PQ EOTFs
        """
        # Handle reference_wall validation
        if name == 'reference_wall':
            value = self._validate_reference_wall(value)

        # Handle verification_wall validation
        if name == 'verification_wall':
            value = self._validate_verification_wall(value)

        # Handle target_eotf - set target_max_lum_nits for non-PQ EOTFs
        if name == 'target_eotf' and value != constants.EOTF.EOTF_ST2084:
            # For non-PQ EOTFs, set the appropriate max lum
            if value == constants.EOTF.EOTF_HLG:
                max_lum = constants.TARGET_MAX_LUM_NITS_HLG
            else:
                max_lum = constants.TARGET_MAX_LUM_NITS_NONE_PQ
            # Set target_max_lum_nits after setting target_eotf
            super().__setattr__(name, value)
            self.target_max_lum_nits = max_lum
            return

        # Handle target_max_lum_nits - enforce limits based on current EOTF
        if name == 'target_max_lum_nits':
            current_eotf = getattr(self, 'target_eotf', constants.EOTF.EOTF_ST2084)
            if current_eotf != constants.EOTF.EOTF_ST2084:
                # For non-PQ EOTFs, override the value
                if current_eotf == constants.EOTF.EOTF_HLG:
                    value = constants.TARGET_MAX_LUM_NITS_HLG
                else:
                    value = constants.TARGET_MAX_LUM_NITS_NONE_PQ

        # Check if this is a linked property and we're a verification wall
        if name in constants.LINKED_LED_WALL_PROPERTIES:
            # Verification walls can't modify linked properties directly
            if getattr(self, 'is_verification_wall', False):
                return
            # Set the value on self
            super().__setattr__(name, value)
            # Propagate to verification wall if it exists
            verification_wall = self.verification_wall_as_wall
            if verification_wall is not None:
                # Use object.__setattr__ to bypass the verification wall's blocking logic
                object.__setattr__(verification_wall, name, value)
        else:
            super().__setattr__(name, value)

    def _validate_reference_wall(self, value: Any) -> str:
        """Validate and normalize reference_wall value."""
        if not value:
            return ""

        ref_wall_name = value.name if isinstance(value, LedWallSettings) else str(value)

        # Can't set reference wall to itself
        if ref_wall_name == getattr(self, 'name', ''):
            raise ValueError("Cannot set the reference wall to be the same as the current wall")

        # Verify the wall exists in the project (if we have a project_settings reference)
        project = getattr(self, '_project_settings', None)
        if project is not None:
            # This will raise ValueError if the wall doesn't exist
            led_wall = project.get_led_wall(ref_wall_name)
            return led_wall.name

        return ref_wall_name

    def _validate_verification_wall(self, value: Any) -> str:
        """Validate and normalize verification_wall value."""
        if not value:
            return ""

        wall_name = value.name if isinstance(value, LedWallSettings) else str(value)

        # Can't set verification wall to itself
        if wall_name == getattr(self, 'name', ''):
            raise ValueError("Cannot set the verification wall to be the same as the current wall")

        return wall_name

    def __getattribute__(self, name: str) -> Any:
        """Custom getattribute to handle verification wall linking.

        For linked properties, verification walls read from their parent wall.
        If the parent wall was removed (verification_wall=""), fall back to local values.
        """
        # For non-linked properties, just use normal attribute access
        if name not in constants.LINKED_LED_WALL_PROPERTIES:
            return super().__getattribute__(name)

        # For linked properties, check if this is a verification wall
        try:
            is_verification = object.__getattribute__(self, '__dict__').get('is_verification_wall', False)
        except (AttributeError, KeyError):
            # Model might not be fully initialized yet
            return super().__getattribute__(name)

        if not is_verification:
            return super().__getattribute__(name)

        # This is a verification wall - get value from parent
        try:
            project_settings = object.__getattribute__(self, '__pydantic_private__').get('_project_settings')
            verification_wall_name = object.__getattribute__(self, '__dict__').get('verification_wall', '')
        except (AttributeError, KeyError, TypeError):
            return super().__getattribute__(name)

        # If parent wall was removed (verification_wall=""), fall back to local value
        if not verification_wall_name:
            return super().__getattribute__(name)

        if project_settings is not None:
            try:
                parent_wall = project_settings.get_led_wall(verification_wall_name)
                if parent_wall is not None:
                    return getattr(parent_wall, name)
            except ValueError:
                # Parent wall was removed, fall back to local value
                return super().__getattribute__(name)

        raise ValueError("The Wall is a verification wall, but the parent wall was removed")

    @property
    def project_settings(self) -> Optional["ProjectSettings"]:
        """The project settings this wall belongs to."""
        return self._project_settings

    @project_settings.setter
    def project_settings(self, value: "ProjectSettings") -> None:
        """Set the project settings reference."""
        self._project_settings = value

    @property
    def verification_wall_as_wall(self) -> Union["LedWallSettings", None]:
        """Get the led wall which this wall is linked to for verifying the calibration.

        Returns:
            LedWallSettings: The LED wall this wall is linked to for verifying the calibration
        """
        wall_name = object.__getattribute__(self, 'verification_wall')
        if wall_name and self._project_settings is not None:
            try:
                return self._project_settings.get_led_wall(wall_name)
            except ValueError:
                return None
        return None

    @property
    def reference_wall_as_wall(self) -> Union["LedWallSettings", None]:
        """Get the reference wall we want to use as the external white point.

        Returns:
            LedWallSettings: The LED wall we want to use as the reference wall
        """
        wall_name = self.reference_wall
        if wall_name and self._project_settings is not None:
            try:
                return self._project_settings.get_led_wall(wall_name)
            except ValueError:
                return None
        return None

    def reset_defaults(self):
        """Reset the LedWallSettings object to its default values."""
        name = self.name
        defaults = LedWallSettings(project_settings=self._project_settings, name=name)

        # Set target_eotf first to ensure correct target_max_lum_nits behavior
        if 'target_eotf' in LedWallSettings.model_fields:
            setattr(self, 'target_eotf', getattr(defaults, 'target_eotf'))

        # Copy all field values except name and target_eotf (already set)
        for field_name in LedWallSettings.model_fields:
            if field_name not in ('name', 'target_eotf'):
                setattr(self, field_name, getattr(defaults, field_name))

    def clear(self):
        """Clears the roi, processing and separation results. So that we can start fresh with
        a new sequence being loaded"""
        self.processing_results = ProcessingResults()
        self.separation_results = None
        self.roi = []

    def clear_led_settings(self):
        """Clear the LED settings and restore them to the defaults."""
        self.reset_defaults()

    def has_valid_white_balance_options(self) -> bool:
        """Checks whether the white balance options are valid or not, we can only have one of these options
            set at anyone time

        Returns: True or False depending on whether the white balance options are valid or not
        """
        values = [self.auto_wb_source, self.match_reference_wall, self.use_white_point_offset].count(True)
        if values > 1:
            return False
        return True

    @classmethod
    def from_json_file(cls, project_settings: "ProjectSettings", json_file: str) -> "LedWallSettings":
        """Create a LedWallSettings object from a JSON file.

        Args:
            project_settings: The project we want the LED wall to belong to
            json_file: The path to the JSON file.

        Returns:
            LedWallSettings: A LedWallSettings object.
        """
        json_data = cls._settings_from_json_file(json_file)
        return cls._from_json_data(project_settings, json_data)

    @classmethod
    def from_json_string(cls, project_settings: "ProjectSettings", json_string: str) -> "LedWallSettings":
        """Creates a LedWallSettings object from a JSON string.

        Args:
            project_settings: The project we want the LED wall to belong to
            json_string: The JSON string representing the data of the LED wall

        Returns: A LedWallSettings object.
        """
        instance = cls.model_validate_json(json_string)
        instance._project_settings = project_settings
        return instance

    @classmethod
    def _from_json_data(cls, project_settings: "ProjectSettings", json_data: dict) -> "LedWallSettings":
        """Create a LedWallSettings from a dictionary."""
        instance = cls.model_validate(json_data)
        instance._project_settings = project_settings
        return instance

    @classmethod
    def from_dict(cls, project_settings: "ProjectSettings", input_dict: dict) -> "LedWallSettings":
        """Creates a LedWallSettings object from a dictionary.

        Args:
            project_settings: The project we want the LED wall to belong to
            input_dict: The dictionary with settings

        Returns:
            LedWallSettings
        """
        instance = cls.model_validate(input_dict)
        instance._project_settings = project_settings
        return instance

    def to_dict(self) -> dict:
        """Returns a dictionary representation of the LedWallSettings object.

        Returns: A dictionary representation of the LedWallSettings object.
        """
        return self.model_dump()

    @classmethod
    def _settings_from_json_file(cls, json_file: str) -> dict:
        """Returns the project settings from a JSON file.

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
            json_file: The path to the JSON file.
        """
        with open(json_file, 'w', encoding='utf-8') as file:
            file.write(self.model_dump_json(indent=4))

    @property
    def sequence_loader(self) -> SequenceLoader:
        """Returns the sequence loader for the LED wall."""
        if not self._sequence_loader:
            self._sequence_loader = self._sequence_loader_class(self)
        return self._sequence_loader
