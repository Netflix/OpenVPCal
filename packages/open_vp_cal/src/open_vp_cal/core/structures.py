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

This module contains the structures for containing data which run through the framework
"""
from typing import TypedDict, Any

from open_vp_cal.core.constants import ValidationStatus


class CalibrationResult(TypedDict):
    """TypedDict representing the results of the calibration process in a JSON serializable format.

    All fields are optional (total=False) as different calibration modes may include different fields.
    """

    # Target and configuration
    target_gamut: str  # The name of the target gamut used for the calibration,
    calculation_order: str  # The order each step of the calibration is calculated and applied
    enable_plate_white_balance: bool  # Whether the plate white balance was enabled or not
    enable_gamut_compression: bool  # Whether the gamut compression was enabled or not
    enable_EOTF_correction: bool  # Whether the EOTF correction was enabled or not
    target_EOTF: str | None  # The name of the EOTF we want to target for the calibration
    native_camera_gamut: str  # The native colour space of the camera, used to capture the input plate
    ocio_reference_gamut: str  # The reference colour space of the ocio config we will be writing too
    avoid_clipping: bool  # Whether to avoid clipping in the calibration process

    # Matrices
    white_balance_matrix: list[list[float]]  # The white balance matrix applied to the plate samples
    target_to_screen_matrix: list[list[float]]  # The calculated target to screen calibration matrix
    reference_to_screen_matrix: list[list[float]]  # The calculated reference to screen calibration matrix
    reference_to_target_matrix: list[list[float]]  # The calculated reference to target matrix
    target_to_XYZ_matrix: list[list[float]]  # The computed target colour space to XYZ matrix
    reference_to_XYZ_matrix: list[list[float]]  # The computed reference colour space to XYZ matrix
    reference_to_input_matrix: list[list[float]]  # The computed reference to input plate colour space matrix
    camera_white_balance_matrix: list[list[float]]  # White balance matrix for camera color correction

    # EOTF correction LUTs
    eotf_1d_lut_red: list[float]  # The values for the red channel of the EOTF correction LUT
    eotf_1d_lut_green: list[float]  # The values for the green channel of the EOTF correction LUT
    eotf_1d_lut_blue: list[float]  # The values for the blue channel of the EOTF correction LUT

    # Gamut compression
    max_distances: list[float]  # The calculated maximum distances for the out of gamut colours, from the target gamut

    # Pre-calibration measurements
    pre_calibration_screen_primaries: list[list[float]]  # The calculated screen colour space primaries CIE1931-xy, pre calibration
    pre_calibration_screen_whitepoint: list[float]  # The calculated screen colour space white point CIE1931-xy, pre calibration
    pre_EOTF_ramps: list[list[float]]  # The measured EOTF of the led wall based on the grey ramp tracking (list of [r,g,b])
    pre_macbeth_samples_xy: list[list[float]]  # Macbeth color checker samples in xy coordinates before calibration

    # Post-calibration measurements
    post_calibration_screen_primaries: list[list[float]]  # The calculated screen colour space primaries CIE1931-xy, post calibration
    post_calibration_screen_whitepoint: list[float]  # The calculated screen colour space white point CIE1931-xy, post calibration
    post_EOTF_ramps: list[list[float]]  # The measured EOTF of the led wall, with the EOTF correction applied (list of [r,g,b])
    post_macbeth_samples_xy: list[list[float]]  # Macbeth color checker samples in xy coordinates after calibration

    # Delta E measurements
    DELTA_E_RGBW: list[float]  # The IPT DeltaE of the R, G, B, W between the measured and reference samples
    DELTA_E_EOTF_RAMP: list[float]  # The IPT DeltaE of the EOTF Ramp between the measured and reference samples
    DELTA_E_MACBETH: list[float]  # The IPT DeltaE of the Macbeth chart between the measured and reference samples

    # Exposure and luminance
    exposure_scaling_factor: float  # Normalization scaling factor for the measured samples
    target_max_lum_nits: float  # The maximum luminance of the target led wall expressed in nits
    measured_max_lum_nits: list[float]  # The measured maximum luminance of the led wall expressed in nits as xyY values [x, y, Y]
    measured_18_percent_sample: float  # The measured 18 percent sample as seen through the camera, using the green channel

    # Reference values
    reference_eotf_ramp: list[float]  # Reference EOTF ramp values

    # Additional metrics
    max_white_delta: float  # Maximum delta for white point
    eotf_linearity: list[list[float]]  # List of [r, g, b] linearity values for EOTF

    # Scaled samples
    scaled_and_converted_samples: dict[str, Any]  # Dictionary containing scaled and converted sample data


class ProcessingResults:
    """ Class to store the results of the processing

    """
    def __init__(self):
        self.samples = None
        self.reference_samples = None
        self.sample_buffers = []
        self.sample_buffers_stitched = None
        self.sample_reference_buffers = []
        self.sample_reference_buffers_stitched = None
        self.sample_swatch_nested = None
        self.pre_calibration_results: CalibrationResult|None = None # Result from Processing.analyse
        self.calibration_results: CalibrationResult|None = None # Result from Processing.calibrate
        self.ocio_config_output_file: str|None = None
        self.calibration_results_file: str|None  = None
        self.lut_output_file: str|None = None
        self.led_wall_colour_spaces: LedWallColourSpaces|None = None


class ValidationResult:
    """ Small class to hold the results of the validation check

    """
    name = ""
    status = ValidationStatus.PASS
    message = ""


class SamplePatchResults:
    """
    Class to store the results of patch sampling.
    """

    def __init__(self):
        """
        Initialize an instance of SamplePatchResults.
        """
        self.samples = []
        self.frames = []


class ConfigurationResult:
    """ Simple class to hold the results of the configuration check
    """
    param = ""
    value = ""


class LedWallColourSpaces:
    """
    Simple class to store all the colour spaces for a led wall
    """
    led_wall_settings = None
    calibration_cs = None
    calibration_preview_cs = None
    target_with_inv_eotf_cs = None
    target_gamut_cs = None
    view_transform = None
    rolloff_look_soft = None
    rolloff_view_soft = None
    rolloff_look_medium = None
    rolloff_view_medium = None
    rolloff_look_hard = None
    rolloff_view_hard = None
    pre_calibration_view_transform = None
    display_colour_space_cs = None
    transfer_function_only_cs = None
    aces_cct_view_transform = None
    aces_cct_calibration_view_transform = None
    aces_cct_display_colour_space_cs = None


class OpenVPCalException(Exception):
    """
    A Simple exception to raise handled exceptions specific to OpenVPCal
    """
    def __init__(self, message):
        super().__init__(message)

class OpenVPCalWarning(Exception):
    """
    A Simple exception to raise handled exceptions specific to OpenVPCal that should
    be treated as warnings
    """
    def __init__(self, message):
        super().__init__(message)
