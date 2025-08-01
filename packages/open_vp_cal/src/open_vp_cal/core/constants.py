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

This file contains constants used throughout the openvpcal calibration process
"""
from enum import Enum, StrEnum, IntEnum

COLOR_WIDGET_GRAPH_SCALE = 1000

OIIO_COMPRESSION_ATTRIBUTE = "compression"
OIIO_COMPRESSION_NONE = "none"
OIIO_BITS_PER_SAMPLE = "oiio:BitsPerSample"

GAMUT_COMPRESSION_LIMIT_MIN = 1.001
GAMUT_COMPRESSION_LIMIT_MAX = 65504
GAMUT_COMPRESSION_SHADOW_ROLLOFF = 0.008

DEFAULT_PROJECT_SETTINGS_NAME = "project_settings.json"

FILE_FORMAT_CLF = "Academy/ASC Common LUT Format"

LUT_LEN = 4096
DEFAULT_LUZ_SIZE = 64
DEFAULT = "default"
OPTIONS = "options"

DELTA_E_THRESHOLD_IMP = 1.0
DELTA_E_THRESHOLD_JND = 2.0

RED = (162, 44, 41)
GREEN = (60, 179, 113)
YELLOW = (252, 186, 3)

KELVIN_TEMPERATURES = [5003, 6000, 6504]

OPEN_VP_CAL_UNIT_TESTING = "OPEN_VP_CAL_UNIT_TESTING"
PRE_PROCESSING_FORMAT_MAP = "PRE_PROCESSING_FORMAT_MAP"

TARGET_MAX_LUM_NITS_NONE_PQ = 100
TARGET_MAX_LUM_NITS_HLG = 1000

DEFAULT_RESOLUTION_WIDTH = 1920
DEFAULT_RESOLUTION_HEIGHT = 1080

DEFAULT_OCIO_CONFIG = "studio-config-v2.1.0_aces-v1.3_ocio-v2.3"
ARC_CONFIG = "arc_config.xml"


class UILayouts(StrEnum):
    """
    Constants for defining the different layouts we want to use for the UI
    """
    ANALYSIS_LAYOUT = "AnalysisLayout.layout"
    PROJECT_LAYOUT = "ProjectLayout.layout"
    ANALYSIS_LAYOUT_WINDOWS = "AnalysisLayout_Windows.layout"
    PROJECT_LAYOUT_WINDOWS = "ProjectLayout_Windows.layout"


class DisplayFilters(StrEnum):
    """
    Constants for defining the different filters we want to use to display the results
    """
    TARGET = "target"
    PRE_CAL = "pre_cal"
    POST_CAL = "post_cal"
    MACBETH = "macbeth"


class CopyFormats(StrEnum):
    """
    Constants for defining the different modes we want to copy data into the clip board
    """
    NUKE = "Nuke"
    PYTHON = "Python"
    CSV = "CSV"


class OpenVPCalSettingsKeys(StrEnum):
    VERSION = "openvp_cal_version"
    PROJECT_SETTINGS = "project_settings"


class ProjectSettingsKeys(StrEnum):
    """
    Constants for the project settings attribute names
    """
    CONTENT_MAX_LUM = "content_max_lum"
    FILE_FORMAT = "file_format"
    RESOLUTION_WIDTH = "resolution_width"
    RESOLUTION_HEIGHT = "resolution_height"
    OUTPUT_FOLDER = "output_folder"
    OCIO_CONFIG_PATH = "ocio_config_path"
    CUSTOM_LOGO_PATH = "custom_logo_path"
    FRAMES_PER_PATCH = "frames_per_patch"
    REFERENCE_GAMUT = 'reference_gamut'
    LED_WALLS = "led_walls"
    PROJECT_CUSTOM_PRIMARIES = "project_custom_primaries"
    FRAME_RATE = "frame_rate"
    EXPORT_LUT_FOR_ACES_CCT = "export_lut_for_aces_cct"
    EXPORT_LUT_FOR_ACES_CCT_IN_TARGET_OUT = "export_lut_for_aces_cct_in_target_out"
    PROJECT_ID = "project_id"
    LUT_SIZE = "lut_size"

    @staticmethod
    def all() -> list[str]:
        """ Returns the list of all Enum values"""
        return [member.value for member in ProjectSettingsKeys]


class FrameRates(IntEnum):
    """
    Constants for the different frame rates we can use
    """
    FPS_24 = 24
    FPS_25 = 25
    FPS_30 = 30
    FPS_48 = 48
    FPS_50 = 50
    FPS_60 = 60

    @staticmethod
    def all() -> list[int]:
        """ Returns the list of all Enum values"""
        return [member.value for member in FrameRates]

    @staticmethod
    def default() -> int:
        return FrameRates.FPS_24


class LedWallSettingsKeys(StrEnum):
    """
    Constants for the LED wall settings attribute names
    """
    NAME = "name"
    AVOID_CLIPPING = "avoid_clipping"
    ENABLE_EOTF_CORRECTION = "enable_eotf_correction"
    ENABLE_GAMUT_COMPRESSION = "enable_gamut_compression"
    AUTO_WB_SOURCE = "auto_wb_source"
    INPUT_SEQUENCE_FOLDER = 'input_sequence_folder'
    NUM_GREY_PATCHES = "num_grey_patches"
    PRIMARIES_SATURATION = 'primaries_saturation'
    CALCULATION_ORDER = 'calculation_order'
    INPUT_PLATE_GAMUT = 'input_plate_gamut'
    NATIVE_CAMERA_GAMUT = 'native_camera_gamut'
    REFERENCE_TO_TARGET_CAT = 'reference_to_target_cat'
    ROI = 'roi'
    SHADOW_ROLLOFF = 'shadow_rolloff'
    TARGET_MAX_LUM_NITS = "target_max_lum_nits"
    TARGET_GAMUT = "target_gamut"
    TARGET_EOTF = "target_eotf"
    TARGET_TO_SCREEN_CAT = "target_to_screen_cat"
    MATCH_REFERENCE_WALL = "match_reference_wall"
    REFERENCE_WALL = "reference_wall"
    WHITE_POINT_OFFSET_SOURCE = "white_point_offset_source"
    USE_WHITE_POINT_OFFSET = "use_white_point_offset"
    IS_VERIFICATION_WALL = "is_verification_wall"
    VERIFICATION_WALL = "verification_wall"

    @staticmethod
    def all() -> list[str]:
        """ Returns the list of all Enum values"""
        return [member.value for member in LedWallSettingsKeys]

class PATCHES(StrEnum):
    """ Constants to define the names of the patches we use for the calibration, and a small helper function to get the
    order of the patches
    """
    SLATE = "Slate"
    RED_PRIMARY_DESATURATED = "Red_Primary_Desaturated"
    GREEN_PRIMARY_DESATURATED = "Green_Primary_Desaturated"
    BLUE_PRIMARY_DESATURATED = "Blue_Primary_Desaturated"
    GREY_18_PERCENT = "Grey_18_Percent"
    RED_PRIMARY = "Red_Primary"
    GREEN_PRIMARY = "Green_Primary"
    BLUE_PRIMARY = "Blue_Primary"
    MAX_WHITE = "White"
    MACBETH = "Macbeth"
    SATURATION_RAMP = "Saturation_Ramp"
    DISTORT_AND_ROI = "Distort_and_Roi"
    FLAT_FIELD = "Flat_Field"
    EOTF_RAMPS = "EOTF_Ramps"
    END_SLATE = "End_Slate"

    @staticmethod
    def patch_order() -> list[str]:
        """ Returns the order of patches

        :return: The list of patch names in order
        """
        return [member.value for member in PATCHES]

    @staticmethod
    def patch_index(patch_name: str) -> int:
        """ Gets the index for the given patch name, so we know what order the patches are in

        :param patch_name: The name of the patch
        :return: The index of the patch
        """
        return PATCHES.patch_order().index(patch_name)


class Measurements(StrEnum):
    """
    Class to hold constants used to describe the measurements we take
    """
    GREY = "grey"
    DESATURATED_RGB = "desaturated_rgb"
    PRIMARIES_SATURATION = "primaries_saturation"
    EOTF_RAMP = "EOTF_ramp"
    EOTF_RAMP_SIGNAL = "EOTF_ramp_signal"
    MACBETH = "Macbeth"
    MAX_WHITE = "Max_White"


class Results(StrEnum):
    """
    Class to hold the constants to describe the results of the calibration
    """
    TARGET_GAMUT = "target_gamut"
    CALCULATION_ORDER = "calculation_order"
    ENABLE_PLATE_WHITE_BALANCE = "enable_plate_white_balance"
    ENABLE_GAMUT_COMPRESSION = "enable_gamut_compression"
    ENABLE_EOTF_CORRECTION = "enable_EOTF_correction"
    WHITE_BALANCE_MATRIX = "white_balance_matrix"
    TARGET_TO_SCREEN_MATRIX = "target_to_screen_matrix"
    REFERENCE_TO_SCREEN_MATRIX = "reference_to_screen_matrix"
    REFERENCE_TO_TARGET_MATRIX = "reference_to_target_matrix"
    MAX_DISTANCES = "max_distances"
    EOTF_LUT_R = "eotf_1d_lut_red"
    EOTF_LUT_G = "eotf_1d_lut_green"
    EOTF_LUT_B = "eotf_1d_lut_blue"
    TARGET_EOTF = "target_EOTF"
    PRE_CALIBRATION_SCREEN_PRIMARIES = "pre_calibration_screen_primaries"
    PRE_CALIBRATION_SCREEN_WHITEPOINT = "pre_calibration_screen_whitepoint"
    POST_CALIBRATION_SCREEN_PRIMARIES = "post_calibration_screen_primaries"
    POST_CALIBRATION_SCREEN_WHITEPOINT = "post_calibration_screen_whitepoint"
    PRE_EOTF_RAMPS = "pre_EOTF_ramps"
    POST_EOTF_RAMPS = "post_EOTF_ramps"
    PRE_MACBETH_SAMPLES_XY = "pre_macbeth_samples_xy"
    POST_MACBETH_SAMPLES_XY = "post_macbeth_samples_xy"
    NATIVE_CAMERA_GAMUT = "native_camera_gamut"
    OCIO_REFERENCE_GAMUT = "ocio_reference_gamut"
    DELTA_E_RGBW = "DELTA_E_RGBW"
    DELTA_E_EOTF_RAMP = "DELTA_E_EOTF_RAMP"
    DELTA_E_MACBETH = "DELTA_E_MACBETH"
    EXPOSURE_SCALING_FACTOR = "exposure_scaling_factor"
    MEASURED_18_PERCENT_SAMPLE = "measured_18_percent_sample"
    TARGET_MAX_LUM_NITS = "target_max_lum_nits"
    MEASURED_MAX_LUM_NITS = "measured_max_lum_nits"
    REFERENCE_EOTF_RAMP = "reference_eotf_ramp"
    TARGET_TO_XYZ_MATRIX = "target_to_XYZ_matrix"
    REFERENCE_TO_XYZ_MATRIX = "reference_to_XYZ_matrix"
    REFERENCE_TO_INPUT_MATRIX = "reference_to_input_matrix"
    MAX_WHITE_DELTA = "max_white_delta"
    EOTF_LINEARITY = "eotf_linearity"
    AVOID_CLIPPING = "avoid_clipping"
    CAMERA_WHITE_BALANCE_MATRIX = "camera_white_balance_matrix"
    SCALED_AND_CONVERTED_SAMPLES = "scaled_and_converted_samples"


class CAT(StrEnum):
    """
    Class to hold the constants to describe the chromatic adaptation transforms we can use
    """
    CAT_NONE = "None"
    CAT_BRADFORD = "Bradford"
    CAT_BIANCO2010 = "Bianco 2010"
    CAT_PC_BIANCO2010 = "Bianco PC 2010"
    CAT_CAT02_BRILL2008 = "CAT02 Brill 2008"
    CAT_CAT02 = "CAT02"
    CAT_CAT16 = "CAT16"
    CAT_CMCCAT2000 = "CMCCAT2000"
    CAT_CMCCAT97 = "CMCCAT97"
    CAT_FAIRCHILD = "Fairchild"
    CAT_SHARP = "Sharp"
    CAT_VON_KRIES = "Von Kries"
    CAT_XYZ_SCALING = "XYZ Scaling"

    @staticmethod
    def all() -> list[str]:
        """ Returns the list of all CATs without the none option

        :return: The list of all CATs without the none option
        """
        return CAT.all_with_none()[1:]

    @staticmethod
    def all_with_none() -> list[str]:
        """ Returns the list of all CATs with the none option

        :return: The list of all CATs with the none option
        """
        return [member.value for member in CAT]

    @staticmethod
    def default() -> str:
        return CAT.CAT_CAT02


class ColourSpace(StrEnum):
    """
    Class to hold the constants to describe the colour spaces we can use
    """
    CS_ACES = "ACES2065-1"
    CS_BT2020 = "ITU-R BT.2020"
    CS_SRGB = "sRGB"
    CS_P3 = "DCI-P3"

    @staticmethod
    def all() -> list[str]:
        return [member.value for member in ColourSpace]

    @staticmethod
    def default_target() -> str:
        return ColourSpace.CS_BT2020

    @staticmethod
    def default_ref() -> str:
        return ColourSpace.CS_ACES


class CameraColourSpace(StrEnum):
    """
    Class to hold the constants to describe the colour spaces we can use
    """
    CS_ACES = "ACES2065-1"
    CS_ACES_CG = "ACEScg"
    CS_ACES_CCT = "ACEScct"
    ARRI_WIDE_GAMUT_3 = "ARRI Wide Gamut 3"
    ARRI_WIDE_GAMUT_4 = "ARRI Wide Gamut 4"
    BLACKMAGIC_WIDE_GAMUT = "Blackmagic Wide Gamut"
    CANON_CINEMA_GAMUT = "Cinema Gamut"
    DJI_D_GAMUT = "DJI D-Gamut"
    CS_BT2020 = "ITU-R BT.2020"
    CS_BT709 = "ITU-R BT.709"
    P3_D65 = "P3-D65"
    PROTUNE_NATIVE = "Protune Native"
    RED_WIDE_GAMUT = "REDWideGamutRGB"
    SGAMUT = "S-Gamut"
    SGAMUT3 = "S-Gamut3"
    SGAMUT3_CINE = "S-Gamut3.Cine"
    VGAMUT = "V-Gamut"
    VENICE_SGAMUT3 = "Venice S-Gamut3"
    VENICE_SGAMUT3_CINE = "Venice S-Gamut3.Cine"

    @staticmethod
    def all() -> list[str]:
        """ Returns the list of all Enum values"""
        return [member.value for member in CameraColourSpace]

    @staticmethod
    def default() -> str:
        return CameraColourSpace.CS_ACES


class LedColourSpace(StrEnum):
    """
    Class to hold the constants to describe the LED colour spaces we can use
    """
    CS_BT2020 = "ITU-R BT.2020"
    CS_SRGB = "sRGB"
    CS_P3 = "DCI-P3"

    @staticmethod
    def default_target() ->str:
        return LedColourSpace.CS_BT2020


class EOTF(StrEnum):
    """
    Class to hold the constants to describe the EOTFs we can use
    """
    EOTF_GAMMA_1_8 = "gamma 1.80"
    EOTF_GAMMA_2_2 = "gamma 2.20"
    EOTF_GAMMA_2_4 = "gamma 2.40"
    EOTF_GAMMA_2_6 = "gamma 2.60"
    EOTF_BT1886 = "ITU-R BT.1886"
    EOTF_SRGB = "sRGB"
    EOTF_ST2084 = "ST 2084"
    EOTF_HLG = "HLG"

    @staticmethod
    def all() -> list[str]:
        """ Returns all EOTFs except HLG """
        # TODO : Remove HLG exclusion when we get a response from Brompton on how their gamma is handing things
        return [
            member.value
            for member in EOTF
            if member is not EOTF.EOTF_HLG
        ]

    @staticmethod
    def default() -> str:
        return EOTF.EOTF_ST2084


class CalculationOrder(StrEnum):
    """
    Class to hold the constants to describe the operation order we can use
    """
    CO_CS_EOTF = "CS > EOTF"
    CO_EOTF_CS = "EOTF > CS"

    @staticmethod
    def all() -> list[str]:
        """ Returns the list of all Enum values"""
        return [member.value for member in CalculationOrder]

    @staticmethod
    def default() -> str:
        return CalculationOrder.CO_EOTF_CS

    @staticmethod
    def cs_only_string() -> str:
        return  "CS_Only"

    @staticmethod
    def cs_eotf_string() -> str:
        return "CS_EOTF"

    @staticmethod
    def eotf_cs_string() -> str:
        return "EOTF_CS"


class PQ(float, Enum):
    """
    Class to hold the constants to calculate values going to and from PQ
    """
    PQ_MAX_NITS = 10000.0
    PQ_MAX_NITS_100_1 = 100.0
    PQ_M1 = 0.1593017578125
    PQ_M2 = 78.84375
    PQ_C1 = 0.8359375
    PQ_C2 = 18.8515625
    PQ_C3 = 18.6875

class SourceSelect(StrEnum):
    SINGLE = "Single"
    SEQUENCE = "Sequence"
    CANCEL = "Cancel"

class FileFormats(StrEnum):
    """
    Class to hold the constants to describe the file formats we can use
    """
    FF_EXR = ".exr"
    FF_DPX = ".dpx"
    FF_TIF = ".tif"
    FF_PNG = ".png"
    FF_R3D = ".R3D"
    FF_MXF = ".mxf"
    FF_MOV = ".mov"
    FF_MP4 = ".mp4"
    FF_ARI = ".ari"
    FF_ARX = ".arx"

    @staticmethod
    def all_read() -> list[str]:
        """
        Returns the list of all readable file formats
        """
        return [FileFormats.FF_EXR, FileFormats.FF_DPX, FileFormats.FF_TIF, FileFormats.FF_PNG]

    @staticmethod
    def all_write() -> list[str]:
        """
        Returns the list of all writable file formats
        """
        return [FileFormats.FF_EXR, FileFormats.FF_DPX, FileFormats.FF_TIF]

    @staticmethod
    def all_convert() -> list[str]:
        """
        Returns the list of all convertible file formats
        """
        return [FileFormats.FF_R3D, FileFormats.FF_MXF, FileFormats.FF_MOV, FileFormats.FF_ARI, FileFormats.FF_ARX, FileFormats.FF_MP4]

    @staticmethod
    def default() -> str:
        return FileFormats.FF_EXR


class ValidationStatus(StrEnum):
    """
    Class to hold the constants to describe the validation status of a calibration
    """
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"
    INFO = "INFO"


class ProjectFolders(StrEnum):
    """
    Constants used to describe the folder names within the project
    """
    PATCHES = "patches"
    PLATES = "plates"
    EXPORT = "export"
    PLOTS = "plots"
    RESULTS = "results"
    SWATCHES = "swatches"
    CALIBRATION = "calibration"
    SPG = "spg"


class InputSelectSources(StrEnum):
    """
    Represents the different input sources.
    """
    RED = "RED"
    SONY = "SONY"
    ARRI = "ARRI"
    RBG_SEQUENCE = "RGB_Sequence"
    MOV = "MOV"


class InputFormats:
    """
    Contains tuples of file formats for each input source.
    """
    RED_FORMATS = (FileFormats.FF_R3D,)
    ARRI_FORMATS = (FileFormats.FF_ARX, FileFormats.FF_ARI, FileFormats.FF_MXF)
    SONY_FORMATS = (FileFormats.FF_MXF,)
    MOV_FORMATS = (FileFormats.FF_MOV, FileFormats.FF_MP4)

    @classmethod
    def get_formats_for_source(cls, source: InputSelectSources) -> tuple:
        """
        Returns the tuple of file formats corresponding to the given input source.

        Parameters:
            source (str): The input source, e.g. InputSelectSources.RED, InputSelectSources.ARRI, etc.

        Returns:
            tuple: The tuple of file formats corresponding to the source.
                   If the source is not found, returns an empty tuple.
        """
        mapping = {
            InputSelectSources.RED: cls.RED_FORMATS,
            InputSelectSources.ARRI: cls.ARRI_FORMATS,
            InputSelectSources.SONY: cls.SONY_FORMATS,
            InputSelectSources.MOV: cls.MOV_FORMATS,
        }
        return mapping.get(source, ())
