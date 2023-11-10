"""
This file contains constants used throughout the openvpcal calibration process
"""
import numpy as np

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
DEFAULT = "default"
OPTIONS = "options"

DELTA_E_THRESHOLD = 2.0

E_toD65_matrix = np.array(
    [
        [1.052157, 0.000000, 0.000000],
        [0.000000, 1.000000, 0.000000],
        [0.000000, 0.000000, 0.918358]
    ]
)

RED = (162, 44, 41)
GREEN = (60, 179, 113)

KELVIN_TEMPERATURES = [5003, 6000, 6504]

OPEN_VP_CAL_UNIT_TESTING = "OPEN_VP_CAL_UNIT_TESTING"
LOG_URL = 'https://yl6ov5gen9.execute-api.eu-west-1.amazonaws.com/default/update_openvpcal_database'
VERSION = "openvp_cal_version"


class UILayouts:
    """
    Constants for defining the different layouts we want to use for the UI
    """
    ANALYSIS_LAYOUT = "AnalysisLayout.layout"
    DEFAULT_LAYOUT = "DefaultLayout.layout"
    ANALYSIS_LAYOUT_WINDOWS = "AnalysisLayout_Windows.layout"
    DEFAULT_LAYOUT_WINDOWS = "DefaultLayout_Windows.layout"



class DisplayFilters:
    """
    Constants for defining the different filters we want to use to display the results
    """
    TARGET = "target"
    PRE_CAL = "pre_cal"
    POST_CAL = "post_cal"
    MACBETH = "macbeth"


class CopyFormats:
    """
    Constants for defining the different modes we want to copy data into the clip board
    """
    NUKE = "Nuke"
    PYTHON = "Python"
    CSV = "CSV"


class ProjectSettings:
    """
    Constants for the project settings attribute names
    """
    FILE_FORMAT = "file_format"
    RESOLUTION_WIDTH = "resolution_width"
    RESOLUTION_HEIGHT = "resolution_height"
    OUTPUT_FOLDER = "output_folder"
    OCIO_CONFIG_PATH = "ocio_config_path"
    CUSTOM_LOGO_PATH = "custom_logo_path"
    FRAMES_PER_PATCH = "frames_per_patch"
    LED_WALLS = "led_walls"
    PROJECT_CUSTOM_PRIMARIES = "project_custom_primaries"
    PROJECT_SETTINGS = "project_settings"
    ALL = [FILE_FORMAT, RESOLUTION_WIDTH, RESOLUTION_HEIGHT, OUTPUT_FOLDER, OCIO_CONFIG_PATH, CUSTOM_LOGO_PATH,
           FRAMES_PER_PATCH, LED_WALLS, PROJECT_CUSTOM_PRIMARIES]


class LedWallSettings:
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
    EXTERNAL_WHITE_POINT_FILE = "external_white_point_file"
    USE_EXTERNAL_WHITE_POINT = "use_external_white_point"
    IS_VERIFICATION_WALL = "is_verification_wall"
    VERIFICATION_WALL = "verification_wall"
    ALL = [NAME, ENABLE_EOTF_CORRECTION, ENABLE_GAMUT_COMPRESSION, AUTO_WB_SOURCE, INPUT_SEQUENCE_FOLDER,
           NUM_GREY_PATCHES, PRIMARIES_SATURATION, CALCULATION_ORDER, INPUT_PLATE_GAMUT, NATIVE_CAMERA_GAMUT,
           REFERENCE_TO_TARGET_CAT, ROI, SHADOW_ROLLOFF, TARGET_MAX_LUM_NITS, TARGET_GAMUT, TARGET_EOTF,
           TARGET_TO_SCREEN_CAT, MATCH_REFERENCE_WALL, REFERENCE_WALL, USE_EXTERNAL_WHITE_POINT,
           EXTERNAL_WHITE_POINT_FILE, VERIFICATION_WALL, IS_VERIFICATION_WALL, AVOID_CLIPPING]


class PATCHES:
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

    PATCH_ORDER = [
        SLATE, RED_PRIMARY_DESATURATED, GREEN_PRIMARY_DESATURATED, BLUE_PRIMARY_DESATURATED, GREY_18_PERCENT,
        RED_PRIMARY, GREEN_PRIMARY, BLUE_PRIMARY, MAX_WHITE, MACBETH, SATURATION_RAMP,
        DISTORT_AND_ROI, FLAT_FIELD, EOTF_RAMPS, END_SLATE
    ]

    @classmethod
    def get_patch_index(cls, patch_name: str) -> int:
        """ Gets the index for the given patch name, so we know what order the patches are in

        :param patch_name: The name of the patch
        :return: The index of the patch
        """
        return cls.PATCH_ORDER.index(patch_name)


class Measurements:
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


class Results:
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
    E_TO_D65_MATRIX = "E_to_D65_matrix"
    MAX_WHITE_DELTA = "max_white_delta"
    EOTF_LINEARITY = "eotf_linearity"
    AVOID_CLIPPING = "avoid_clipping"


class CAT:
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
    CAT_ALL = [CAT_BRADFORD, CAT_BIANCO2010, CAT_PC_BIANCO2010, CAT_CAT02_BRILL2008, CAT_CAT02, CAT_CAT16,
               CAT_CMCCAT2000, CAT_CMCCAT97, CAT_FAIRCHILD, CAT_SHARP, CAT_VON_KRIES, CAT_XYZ_SCALING]
    CAT_ALL_WITH_NONE = [CAT_NONE] + CAT_ALL
    CAT_DEFAULT = CAT_CAT02


class ColourSpace:
    """
    Class to hold the constants to describe the colour spaces we can use
    """
    CS_ACES = "ACES2065-1"
    CS_BT2020 = "ITU-R BT.2020"
    CS_SRGB = "sRGB"
    CS_DEFAULT_TARGET = CS_BT2020
    CS_DEFAULT_REF = CS_ACES
    CS_ALL = [CS_ACES, CS_BT2020, CS_SRGB]


class CameraColourSpace:
    """
    Class to hold the constants to describe the colour spaces we can use
    """
    CS_ACES = "ACES2065-1"
    CS_ACES_CG = "ACEScg"
    ARRI_WIDE_GAMUT_3 = "ARRI Wide Gamut 3"
    ARRI_WIDE_GAMUT_4 = "ARRI Wide Gamut 4"
    BLACKMAGIC_WIDE_GAMUT = "Blackmagic Design Wide Gamut"
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
    CS_ALL = [CS_ACES, CS_ACES_CG, ARRI_WIDE_GAMUT_3, ARRI_WIDE_GAMUT_4, BLACKMAGIC_WIDE_GAMUT, CANON_CINEMA_GAMUT,
              DJI_D_GAMUT, CS_BT2020, CS_BT709, P3_D65, PROTUNE_NATIVE, RED_WIDE_GAMUT, SGAMUT, SGAMUT3, SGAMUT3_CINE,
              VGAMUT, VENICE_SGAMUT3, VENICE_SGAMUT3_CINE]
    CS_DEFAULT = CS_ACES


class EOTF:
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
    EOTF_ALL = [EOTF_GAMMA_1_8, EOTF_GAMMA_2_2, EOTF_GAMMA_2_4, EOTF_GAMMA_2_6, EOTF_BT1886, EOTF_SRGB, EOTF_ST2084]
    EOTF_DEFAULT = EOTF_ST2084


class CalculationOrder:
    """
    Class to hold the constants to describe the operation order we can use
    """
    CO_CS_EOTF = "CS > EOTF"
    CO_EOTF_CS = "EOTF > CS"
    CO_ALL = [CO_CS_EOTF, CO_EOTF_CS]
    CO_DEFAULT = CO_EOTF_CS
    CS_ONLY_STRING = "CS_Only"
    CO_CS_EOTF_STRING = "CS_EOTF"
    CO_EOTF_CS_STRING = "EOTF_CS"


class PQ:
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


class FileFormats:
    """
    Class to hold the constants to describe the file formats we can use
    """
    FF_EXR = "exr"
    FF_DPX = "dpx"
    FF_TIF = "tif"
    FF_ALL = [FF_EXR, FF_DPX, FF_TIF]
    FF_DEFAULT = FF_EXR


class ValidationStatus:
    """
    Class to hold the constants to describe the validation status of a calibration
    """
    PASS = "PASS"
    WARNING = "WARNING"
    FAIL = "FAIL"


class ProjectFolders:
    """
    Constants used to describe the folder names within the project
    """
    PATCHES = "patches"
    EXPORT = "export"
    PLOTS = "plots"
    RESULTS = "results"
    SWATCHES = "swatches"
    CALIBRATION = "calibration"
