"""
The main module of the core which deals with the calculation of the calibration for the LED walls
"""
from typing import Union, List, Dict, Tuple

import json
import colour
import colour.algebra as ca
import numpy as np
from colour import RGB_Colourspace
from colour.models import eotf_inverse_BT2100_PQ

from open_vp_cal.core import constants
from open_vp_cal.core.constants import ColourSpace, Measurements, Results, CAT, EOTF, CalculationOrder
from open_vp_cal.core import utils


def saturate_RGB(samples, factor):
    """ Saturate the given RGB samples by the provided factor.

        Behaviour is based on the Nuke Saturation node, with luminance math in
        Average mode.  This is a lerp between greyscale (equal R,G,B) computed
        as the input luminance (via mean of R,G,B) and the original values.
        'factor' is not clamped to [0,1].

    Args:
        samples (array-like): colour samples in RGB colour space
        factor (float): Saturation for the output samples. A value of 1 equals no change. A value of 0
        produces grayscale values.

    Returns:
        output samples (array-like)

    """
    sample_array = np.array(samples)
    lum = np.mean(sample_array, axis=1, keepdims=True)
    delta = sample_array - lum
    return delta * factor + lum


def saturation(rgb):
    """Return the saturation computed from given RGB sample using the HSV model.

    Args:
        rgb (array-like): colour sample in RGB.  Values must be in range [0,1]

    Returns:
        saturation (float)
    """
    c_max, c_min = (max(rgb[:2]), min(rgb[:2]))
    chroma = c_max - c_min
    value = c_max
    return chroma / value if value > 0 else 0


def achromatic(rgb, shadow_rolloff):
    """Compute the value on the achromatic axis corresponding to the given RGB value.

    Args:
        rgb (array-like): RGB colour value
        shadow_rolloff (float): the rolloff to apply towards the dark end of the gamut

    Returns:
        achromatic RGB value (3x float)
    """
    value = max(rgb[0], rgb[1], rgb[2])
    if value <= shadow_rolloff:
        value = shadow_rolloff * (1 - np.tanh((shadow_rolloff - value) / shadow_rolloff))
    return np.asarray([value, value, value])


def eotf_correction_calculation(
        grey_ramp_screen, grey_signal_value_rgb, deltaE_grey_ramp, avoid_clipping=True,
        peak_lum=None, deltaE_threshold=20):
    """ Compute a LUT to correct the EOTF as measured from grey patches. Any grey patches with a delta E greater than
        the deltaE_threshold are ignored.

        Args:
            deltaE_threshold: The threshold for delta E values to be considered
            grey_ramp_screen (array-like): Grey ramp in Screen Colour Space
            grey_signal_value_rgb: Reference Signal Values For The EOTF as RGB values
            deltaE_grey_ramp: Delta E Values For The Grey Ramp
            avoid_clipping: If we want to avoid clipping of values on the led wall we scale any values
            using the peak lum if values go above this
            peak_lum: The peak luminance of the led wall

        Returns:
            lut_r (array-like): 1D LUT with elements as (y,x)
            lut_g (array-like): 1D LUT with elements as (y,x)
            lut_b (array-like): 1D LUT with elements as (y,x)

    """
    num_steps = len(grey_ramp_screen)
    assert num_steps > 1
    assert len(grey_signal_value_rgb) == num_steps
    assert len(deltaE_grey_ramp) == num_steps

    grey_ramp_screen = np.maximum(0, grey_ramp_screen)

    lut_r, lut_g, lut_b = [[0.0, 0.0]], [[0.0, 0.0]], [[0.0, 0.0]]

    for idx, grey_ramp_screen_value in enumerate(grey_ramp_screen):
        if deltaE_grey_ramp[idx] > deltaE_threshold:
            continue

        lut_r.append([grey_ramp_screen_value[0], grey_signal_value_rgb[idx][0]])
        lut_g.append([grey_ramp_screen_value[1], grey_signal_value_rgb[idx][1]])
        lut_b.append([grey_ramp_screen_value[2], grey_signal_value_rgb[idx][2]])

    lut_r = np.array(lut_r)
    lut_g = np.array(lut_g)
    lut_b = np.array(lut_b)

    if avoid_clipping:
        if not peak_lum:
            raise ValueError("Peak luminance must be provided if avoid_clipping is True")

        max_r = np.max(np.max(lut_r[:, 0]))
        max_g = np.max(np.max(lut_g[:, 0]))
        max_b = np.max(np.max(lut_b[:, 0]))
        max_value = max(max_r, max_g, max_b)
        if max_value > peak_lum:
            scale_factor = peak_lum / max_value

            lut_r[:, 0] *= scale_factor
            lut_g[:, 0] *= scale_factor
            lut_b[:, 0] *= scale_factor

    return lut_r, lut_g, lut_b


def resample_lut(lut, values):
    """Resample the provided LUT at the given values.

    Uses piecewise linear interpolation

    Args:
        lut (array-like): list of (y,x) pairs in ascending order
        values (array-like): list of new sample values

    Returns:
        1D LUT: list of (y,x) pairs
    """
    lut = np.array(lut)
    x_values = lut[:, 1]
    y_values = lut[:, 0]
    y_interp = np.interp(values, x_values, y_values)
    return np.stack((y_interp, values), axis=1)


def colourspace_max_distances(
        source_cs: RGB_Colourspace, destination_cs: RGB_Colourspace, cat: str, shadow_rolloff: float):
    """Compute the maximum distances between two colour spaces, with a shadow rolloff.

    Args:
        source_cs (RGB_Colourspace): the source colour space
        destination_cs (RGB_Colourspace): the colourspace we are mapping to
        cat (basestring): the chromatic adaptation transformation to apply
        shadow_rolloff (float): a rolloff to apply to dark colours

    Returns:
        distances per component (3x float)
    """
    primaries = colour.RGB_to_RGB(
        RGB=np.asarray([[1.0, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, 1.0]]),
        input_colourspace=source_cs,
        output_colourspace=destination_cs,
        chromatic_adaptation_transform=cat,
    )
    achromatic_values = np.apply_along_axis(
        lambda rgb: achromatic(rgb, shadow_rolloff), 1, primaries
    )
    distances = (achromatic_values - primaries) / achromatic_values
    return np.amax(distances, axis=0)


def extract_screen_cs(
        primaries_measurements,
        primaries_saturation,
        white_point_measurements,
        camera_native_cs,
        target_cs,
        cs_cat,
        reference_to_target_matrix,
        native_camera_gamut_cs, input_plate_cs, camera_conversion_cat, avoid_clipping,
        macbeth_measurements_camera_native_gamut,
        reference_samples,
) -> Union[RGB_Colourspace, List, RGB_Colourspace]:
    """Extract the screen colourspace from measured primaries.

    Args:
        primaries_measurements (array-like): RGB samples for desaturated primaries in target CS
        primaries_saturation (float): saturation level for primaries
        white_point_measurements (array-like) RGB sample for white point in target CS
        camera_native_cs (RGB_Colourspace): The Colour RGB colourspace for the camera
        target_cs (RGB_Colourspace): Target colourspace
        cs_cat (str): CAT for CS conversions
        reference_to_target_matrix: The matrix which goes from the reference space to the target space
        native_camera_gamut_cs: The native camera colourspace
        input_plate_cs: The input plate colourspace
        camera_conversion_cat: The CAT method to use for the camera colour space conversion
        avoid_clipping: Whether to avoid clipping from the led by scaling results to peak

    Returns:
        screen_cs (RGB_Colourspace): screen colourspace
        target_to_screen_matrix (array_like): 3x3 RGB transformation matrix
        calibrated_screen_cs (RGB_Colourspace): screen colourspace calibrated to target
    """
    # format inputs
    primaries_measurements = np.reshape(primaries_measurements, (-1, 3))
    white_point_measurements = np.reshape(white_point_measurements, -1)

    primaries_measurements_target = colour.RGB_to_RGB(
        primaries_measurements, native_camera_gamut_cs, target_cs, None
    )

    # We re-saturate the primaries in the same target space they where desaturated in
    saturated_primaries_target = saturate_RGB(primaries_measurements_target, 1.0 / primaries_saturation)

    saturated_primaries = colour.RGB_to_RGB(
        saturated_primaries_target, target_cs, native_camera_gamut_cs, None
    )

    primaries_XYZ = np.apply_along_axis(
        lambda rgb: camera_native_cs.matrix_RGB_to_XYZ.dot(rgb), 1, saturated_primaries
    )

    primaries_xy = colour.XYZ_to_xy(primaries_XYZ)

    white_point_XYZ = camera_native_cs.matrix_RGB_to_XYZ @ white_point_measurements
    white_point_xy = colour.XYZ_to_xy(white_point_XYZ)

    screen_cs = colour.RGB_Colourspace(
        name="screen",
        primaries=primaries_xy,
        whitepoint=white_point_xy,
        use_derived_matrix_XYZ_to_RGB=True,
        use_derived_matrix_RGB_to_XYZ=True,
    )

    target_to_screen_matrix = colour.matrix_RGB_to_RGB(
        input_colourspace=target_cs,
        output_colourspace=screen_cs,
        chromatic_adaptation_transform=cs_cat,
    )

    macbeth_reference_samples = reference_samples[Measurements.MACBETH]
    macbeth_reference_samples_camera_native = colour.RGB_to_RGB(
        macbeth_reference_samples, target_cs, camera_native_cs, None
    )

    colour_matrix1 = colour.matrix_colour_correction(
        macbeth_measurements_camera_native_gamut,
        macbeth_reference_samples_camera_native,
        method='Cheung 2004'
    )

    # If we want to avoid clipping, we need to scale the matrix so that the sum of each row is 1
    if avoid_clipping:
        row_sums = target_to_screen_matrix.sum(axis=1, keepdims=True)
        max_value = max(row_sums)
        if max_value > 1:
            target_to_screen_matrix = target_to_screen_matrix / max_value

    saturated_primaries_input_plate_gamut = colour.RGB_to_RGB(
        saturated_primaries, native_camera_gamut_cs, input_plate_cs, camera_conversion_cat
    )

    saturated_primaries_target_gamut = [
        ca.vector_dot(reference_to_target_matrix, m) for m in saturated_primaries_input_plate_gamut
    ]

    calibrated_saturated_primaries_target = [
        ca.vector_dot(target_to_screen_matrix, m) for m in saturated_primaries_target_gamut
    ]

    primaries_XYZ_calibrated = colour.RGB_to_XYZ(
        calibrated_saturated_primaries_target,
        target_cs.whitepoint,
        target_cs.whitepoint,
        target_cs.matrix_RGB_to_XYZ
    )

    # White Point
    white_measurements_input_plate_gamut = colour.RGB_to_RGB(
        white_point_measurements, native_camera_gamut_cs, input_plate_cs, camera_conversion_cat
    )

    white_point_measurements_target_gamut = ca.vector_dot(
        reference_to_target_matrix, white_measurements_input_plate_gamut)

    calibrated_white_point_target = ca.vector_dot(
        target_to_screen_matrix, white_point_measurements_target_gamut
    )

    white_point_XYZ_calibrated = colour.RGB_to_XYZ(
        calibrated_white_point_target,
        target_cs.whitepoint,
        target_cs.whitepoint,
        target_cs.matrix_RGB_to_XYZ
    )
    white_point_xy_calibrated = colour.XYZ_to_xy(white_point_XYZ_calibrated)

    primaries_xy_calibrated = colour.XYZ_to_xy(primaries_XYZ_calibrated)
    calibrated_screen_cs = colour.RGB_Colourspace(
        name="screen_calibrated",
        primaries=primaries_xy_calibrated,
        whitepoint=white_point_xy_calibrated,
        use_derived_matrix_XYZ_to_RGB=True,
        use_derived_matrix_RGB_to_XYZ=True,
    )

    return screen_cs, target_to_screen_matrix, calibrated_screen_cs


def apply_luts(
        inputs_rgb,
        lut_r,
        lut_g,
        lut_b,
        inverse=False
):
    """Apply luts to the given RGB values.

    Args:
        inputs_rgb (array-like): RGB values
        lut_r: LUT for R channel
        lut_g: LUT for G channel
        lut_b: LUT for B channel
        inverse: Whether we want to apply the lut as the inverse or not

    Returns:
        outputs_RGB (array-like): RGB values
    """
    inputs_r = np.asarray(inputs_rgb)[:, 0]
    inputs_g = np.asarray(inputs_rgb)[:, 1]
    inputs_b = np.asarray(inputs_rgb)[:, 2]

    x_idx, y_idx = (0, 1) if not inverse else (1, 0)
    output_r = np.interp(inputs_r, lut_r[:, x_idx], lut_r[:, y_idx])
    output_g = np.interp(inputs_g, lut_g[:, x_idx], lut_g[:, y_idx])
    output_b = np.interp(inputs_b, lut_b[:, x_idx], lut_b[:, y_idx])

    return np.stack((output_r, output_g, output_b), axis=1)


def get_ocio_reference_to_target_matrix(
        input_plate_cs: RGB_Colourspace,
        target_cs: RGB_Colourspace, cs_cat: str = None, ocio_reference_cs: RGB_Colourspace = None):
    """ Get a matrix which goes from the reference space of ocio config, to the target space provided.
        If not ocio reference cs is provided, it defaults to ACES2065-1
        If no cat is provided, it defaults to Bradford

    Args:
        input_plate_cs: the input plate colourspace
        target_cs: the target colourspace we want to convert to
        cs_cat: the chromatic adaptation transform we want to use
        ocio_reference_cs: the reference colourspace of the ocio config

    Returns:
        ocio_reference_to_target_matrix: the matrix which goes from the ocio reference space to the target space
        ocio_reference_cs: the reference colourspace of the ocio config

    """
    if ocio_reference_cs is None:
        ocio_reference_cs = colour.RGB_COLOURSPACES[ColourSpace.CS_ACES]

    if cs_cat is None:
        cs_cat = CAT.CAT_BRADFORD

    reference_to_target_matrix = colour.matrix_RGB_to_RGB(
        input_colourspace=ocio_reference_cs,
        output_colourspace=target_cs,
        chromatic_adaptation_transform=cs_cat,
    )

    target_to_XYZ_matrix = target_cs.matrix_RGB_to_XYZ
    reference_to_XYZ_matrix = ocio_reference_cs.matrix_RGB_to_XYZ
    reference_to_input_matrix = colour.matrix_RGB_to_RGB(
        input_colourspace=ocio_reference_cs,
        output_colourspace=input_plate_cs,
        chromatic_adaptation_transform=cs_cat,
    )

    return (reference_to_target_matrix, ocio_reference_cs,
            target_to_XYZ_matrix, reference_to_XYZ_matrix, reference_to_input_matrix)


def scale_to_absolute_nits(input_array: Union[List, np.ndarray]) -> List:
    """ For an array of RGB values, scale them to nits

    Args:
        input_array: (array-like) RGB values

    Returns: (array-like) RGB values scaled to absolute nits

    """
    return [
        [item[0] * 100, item[1] * 100, item[2] * 100] for item in input_array
    ]


def deltaE_ICtCp(
        rgbw_reference_samples, macbeth_reference_samples, eotf_ramp_reference_samples,
        rgbw_measurements_camera_native_gamut: np.ndarray,
        eotf_ramp_camera_native_gamut: List[np.ndarray],
        macbeth_measurements_camera_native_gamut: List[np.ndarray],
        target_cs: RGB_Colourspace, native_camera_gamut_cs: RGB_Colourspace
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    """ Calculates the deltaE between the reference samples and the measured samples for RGBW, eotf ramp, and macbeth
        chart

        The DeltaE is based on the normalized values, rather than the absolute nit values

    Args:
        reference_samples: The reference samples
        rgbw_measurements_camera_native_gamut: The RGBW measurements in the camera native gamut
        eotf_ramp_camera_native_gamut: The eotf ramp measurements in the camera native gamut
        macbeth_measurements_camera_native_gamut: The macbeth measurements in the camera native gamut
        target_cs: The target colour space
        native_camera_gamut_cs: The native camera gamut colour space

    Returns: The deltaE values for RGBW, eotf ramp, and macbeth chart

    """
    eotf_ramp_camera_native_gamut = scale_to_absolute_nits(eotf_ramp_camera_native_gamut)
    rgbw_measurements_camera_native_gamut = scale_to_absolute_nits(rgbw_measurements_camera_native_gamut)
    macbeth_measurements_camera_native_gamut = scale_to_absolute_nits(macbeth_measurements_camera_native_gamut)

    rgbw_reference_samples = scale_to_absolute_nits(rgbw_reference_samples)
    rgbw_reference_samples_native_camera_gamut = colour.RGB_to_RGB(
        rgbw_reference_samples, target_cs, native_camera_gamut_cs, None)

    macbeth_reference_samples = scale_to_absolute_nits(macbeth_reference_samples)
    macbeth_reference_samples_native_camera_gamut = colour.RGB_to_RGB(
        macbeth_reference_samples, target_cs, native_camera_gamut_cs, None)

    # Convert The Grey Ramp Reference Samples From The Target Colour Space To Rec 2020
    eotf_ramp_reference_samples = scale_to_absolute_nits(eotf_ramp_reference_samples)
    eotf_ramp_reference_samples_native_camera_gamut = colour.RGB_to_RGB(
        eotf_ramp_reference_samples, target_cs, native_camera_gamut_cs, None)

    rgbw_samples_ICtCp = colour.RGB_to_ICtCp(rgbw_measurements_camera_native_gamut, 'Dolby 2016')
    eotf_ramp_samples_ICtCp = colour.RGB_to_ICtCp(eotf_ramp_camera_native_gamut, 'Dolby 2016')
    macbeth_samples_ICtCp = colour.RGB_to_ICtCp(macbeth_measurements_camera_native_gamut, 'Dolby 2016')

    rgbw_reference_samples_ICtCp = colour.RGB_to_ICtCp(
        rgbw_reference_samples_native_camera_gamut, 'Dolby 2016',
    )
    eotf_ramp_reference_samples_ICtCp = colour.RGB_to_ICtCp(
        eotf_ramp_reference_samples_native_camera_gamut, 'Dolby 2016',
    )
    macbeth_reference_samples_ICtCp = colour.RGB_to_ICtCp(
        macbeth_reference_samples_native_camera_gamut, 'Dolby 2016',
    )

    delta_e_rgbw = colour.difference.delta_E_ITP(rgbw_samples_ICtCp, rgbw_reference_samples_ICtCp)
    delta_e_eotf_ramp = colour.difference.delta_E_ITP(eotf_ramp_samples_ICtCp, eotf_ramp_reference_samples_ICtCp)
    delta_e_macbeth = colour.difference.delta_E_ITP(macbeth_samples_ICtCp, macbeth_reference_samples_ICtCp)
    delta_e_wrgb = np.roll(delta_e_rgbw, shift=1)

    # We divide the results by 3 to move the scalar down from 720 to 240 as per
    # https://www.portrait.com/resource-center/ictcp-color-difference-metric/
    return delta_e_wrgb / 3, delta_e_eotf_ramp / 3, delta_e_macbeth / 3


def calculate_eotf_linearity(eotf_signal_values: List, eotf_ramp_camera_native_gamut: List) -> List:
    """ Calculate the difference between the eotf signal values and the eotf ramp values, for each channel

    Args:
        eotf_signal_values: The eotf signal values
        eotf_ramp_camera_native_gamut:  The eotf ramp values

    Returns: The difference between the eotf signal values and the eotf ramp values, for each channel

    """
    eotf_linearity = []
    for idx, eotf_value in enumerate(eotf_ramp_camera_native_gamut):
        eotf_signal_value = eotf_signal_values[idx]
        red, green, blue = eotf_value

        red_result = red / eotf_signal_value if eotf_signal_value != 0 else red
        green_result = green / eotf_signal_value if eotf_signal_value != 0 else green
        blue_result = blue / eotf_signal_value if eotf_signal_value != 0 else blue

        eotf_linearity.append([red_result, green_result, blue_result])

    return eotf_linearity


def create_decoupling_white_balance_matrix(
        grey_measurements_native_camera_gamut, decoupled_lens_white_samples_camera_native_gamut):
    green_scaling_factor = grey_measurements_native_camera_gamut[1] / decoupled_lens_white_samples_camera_native_gamut[
        1]
    scaled_decoupled_samples = np.array(decoupled_lens_white_samples_camera_native_gamut) * green_scaling_factor
    red_mult_val = scaled_decoupled_samples[0] / grey_measurements_native_camera_gamut[0]
    blue_mult_val = scaled_decoupled_samples[2] / grey_measurements_native_camera_gamut[2]
    decoupling_white_balance_matrix = np.asarray(
        [[red_mult_val, 0.0, 0.0], [0.0, 1.0, 0.0], [0.0, 0.0, blue_mult_val]])

    return decoupling_white_balance_matrix


def run(
        measured_samples: Dict,
        reference_samples: Dict,
        input_plate_gamut: Union[str, RGB_Colourspace, constants.ColourSpace],
        native_camera_gamut: Union[str, RGB_Colourspace, constants.CameraColourSpace],
        target_gamut: Union[str, RGB_Colourspace, constants.ColourSpace],
        target_to_screen_cat: Union[str, CAT],
        reference_to_target_cat: Union[str, CAT],
        target_max_lum_nits: int,
        target_EOTF: Union[None, str, EOTF] = None,
        enable_plate_white_balance: bool = True,
        enable_gamut_compression: bool = True,
        enable_EOTF_correction: bool = True,
        calculation_order: Union[str, CalculationOrder] = CalculationOrder.CO_DEFAULT,
        gamut_compression_shadow_rolloff: float = constants.GAMUT_COMPRESSION_SHADOW_ROLLOFF,
        reference_wall_external_white_balance_matrix: Union[None, List] = None,
        decoupled_lens_white_samples: Union[None, List] = None,
        avoid_clipping: bool = True):
    """ Run the entire calibration process.

    Args:
        measured_samples: a dictionary containing the measured values sampled from the input plate
        reference_samples: a dictionary containing the reference values for the calibration process displayed on
        the led wall
        input_plate_gamut: The colour space of the input plate we measured the samples from
        native_camera_gamut: The native colour space of the camera, used to capture the input plate
        target_gamut: The colour space we want to target for the calibration
        target_to_screen_cat: The chromatic adaptation transform method for target to screen calibration matrix
        target_max_lum_nits: The maximum luminance of the target led wall expressed in nits
        target_EOTF: The name of the EOTF we want to target for the calibration
        enable_plate_white_balance: Applies the white balance matrix calculated for the input plate
        enable_gamut_compression: Whether to enable the gamut compression or not, as part of the calibration
        enable_EOTF_correction: Whether to enable the EOTF correction or now, as part of the calibration
        calculation_order: The order each step of the calibration is calculated and applied
        gamut_compression_shadow_rolloff: A rolloff to apply to dark colours
        reference_to_target_cat: The chromatic adaptation transform method, for reference to target matrix
        reference_wall_external_white_balance_matrix: A precomputed white balance matrix to apply to the input plate
        samples, used when matching other led walls. By default, the white balance matrix is independently
        calculated for each wall

    Returns: A dictionary containing the results of the calibration process in a json serializable format
        PRE_CALIBRATION_SCREEN_PRIMARIES: (List) The calculated screen colour space primaries CIE1931-xy,
        pre calibration
        PRE_CALIBRATION_SCREEN_WHITEPOINT: (List) The calculated screen colour space white point CIE1931-xy,
        pre calibration
        TARGET_GAMUT: The name of the target gamut used for the calibration,
        ENABLE_PLATE_WHITE_BALANCE: (bool) Whether the plate white balance was enabled or not
        ENABLE_GAMUT_COMPRESSION: (bool) Whether the gamut compression was enabled or not
        ENABLE_EOTF_CORRECTION: (bool) Whether the EOTF correction was enabled or not
        CALCULATION_ORDER: (str) The order each step of the calibration is calculated and applied
        WHITE_BALANCE_MATRIX: (List) The white balance matrix applied to the plate samples
        TARGET_TO_SCREEN_MATRIX: (List) The calculated target to screen calibration matrix
        REFERENCE_TO_SCREEN_MATRIX: (List) The calculated reference to screen calibration matrix
        REFERENCE_TO_TARGET_MATRIX: (List) The calculated reference to target matrix
        EOTF_LUT_R: (List) The values for the red channel of the EOTF correction LUT
        EOTF_LUT_G: (List) The values for the green channel of the EOTF correction LUT
        EOTF_LUT_B: (List) The values for the blue channel of the EOTF correction LUT
        MAX_DISTANCES: (List) The calculated maximum distances for the out of gamut colours, from the target gamut
        TARGET_EOTF: The name of the EOTF we want to target for the calibration
        NATIVE_CAMERA_GAMUT: The native colour space of the camera, used to capture the input plate
        OCIO_REFERENCE_GAMUT: The reference colour space of the ocio config we will be writing too
        POST_CALIBRATION_SCREEN_PRIMARIES: (List) The calculated screen colour space primaries CIE1931-xy, post calibration
        POST_CALIBRATION_SCREEN_WHITEPOINT: (List) The calculated screen colour space white point CIE1931-xy, post calibration
        PRE_EOTF_RAMPS: The measured EOTF of the led wall based on the grey ramp tracking
        POST_EOTF_RAMPS: The measured EOTF of the led wall, with the EOTF correction applied
        DELTA_E_RGBW: The IPT DeltaE of the R, G, B, W between the measured and reference samples
        DELTA_E_EOTF_RAMP: The IPT DeltaE of the EOTF Ramp between the measured and reference samples
        DELTA_E_MACBETH: The IPT DeltaE of the Macbeth chart between the measured and reference samples
        EXPOSURE_SCALING_FACTOR: Normalization scaling factor for the measured samples
        TARGET_MAX_LUM_NITS: The maximum luminance of the target led wall expressed in nits
        MEASURED_18_PERCENT_SAMPLE: The measured 18 percent sample as seen through the camera, using the green channel
        MEASURED_MAX_LUM_NITS: The measured maximum luminance of the led wall expressed in nits
        REFERENCE_EOTF_RAMP: The reference EOTF ramp values
        TARGET_TO_XYZ_MATRIX: The computed target colour space to XYZ matrix
        REFERENCE_TO_XYZ_MATRIX: The computed reference colour space to XYZ matrix
        REFERENCE_TO_INPUT_MATRIX: The computed reference to input plate colour space matrix

    """
    # If we are not working in PQ we force target nits to 100 aka 1.0
    if target_EOTF != constants.EOTF.EOTF_ST2084:
        target_max_lum_nits = 100
    peak_lum = target_max_lum_nits * 0.01

    if target_to_screen_cat == constants.CAT.CAT_NONE:
        target_to_screen_cat = None

    # 0) Ensure we can do only one of auto white balance, external white balance, or decoupled lens white balance
    configuration_check = [
        enable_plate_white_balance,
        reference_wall_external_white_balance_matrix is not None,
        decoupled_lens_white_samples is not None].count(True)

    if configuration_check > 1:
        raise ValueError("Only one of auto white balance, external white balance, "
                         "or decoupled lens white balance is allowed")

    # 1) First We Get Our Colour Spaces
    input_plate_cs, native_camera_gamut_cs, target_cs = get_calibration_colour_spaces(
        input_plate_gamut, native_camera_gamut, target_gamut)

    # 2) Once we have our camera native colour space we decide on the cat we want to use to convert to camera space
    camera_conversion_cat = utils.get_cat_for_camera_conversion(native_camera_gamut_cs.name)

    # 3) We take our measured samples and convert them to camera space
    (
        eotf_ramp_camera_native_gamut, grey_measurements_native_camera_gamut,
        macbeth_measurements_camera_native_gamut, max_white_camera_native_gamut,
        rgbw_measurements_camera_native_gamut,
        eotf_signal_values, decoupled_lens_white_samples_camera_native_gamut,
        rgbw_reference_samples, macbeth_reference_samples, eotf_ramp_reference_samples
    ) = convert_samples_to_required_cs(
        camera_conversion_cat, input_plate_cs, measured_samples, reference_samples, native_camera_gamut_cs,
        decoupled_lens_white_samples, peak_lum
    )

    # 4) We Calculate a decoupled white balance matrix if we have a decoupled lens white samples
    decoupling_white_balance_matrix = None
    if decoupled_lens_white_samples_camera_native_gamut is not None:
        decoupling_white_balance_matrix = create_decoupling_white_balance_matrix(
            grey_measurements_native_camera_gamut, decoupled_lens_white_samples_camera_native_gamut)

    # 5) We Apply The Decoupling White Balance Matrix To All The Samples If We Have One
    if decoupling_white_balance_matrix is not None:
        (
            eotf_ramp_camera_native_gamut, grey_measurements_native_camera_gamut,
            macbeth_measurements_camera_native_gamut, max_white_camera_native_gamut,
            rgbw_measurements_camera_native_gamut
        ) = apply_matrix_to_samples(
            decoupling_white_balance_matrix, eotf_ramp_camera_native_gamut,
            grey_measurements_native_camera_gamut,
            macbeth_measurements_camera_native_gamut, max_white_camera_native_gamut,
            rgbw_measurements_camera_native_gamut
        )

    # 4) We Calculate The White Balance Matrix By Balancing The Grey Samples Against The Green Channel Or Use The One
    # Provided By The External Reference Wall
    # Green Value / Red Value
    if reference_wall_external_white_balance_matrix is None:
        grey_measurements_camera_target = colour.RGB_to_RGB(
            grey_measurements_native_camera_gamut, native_camera_gamut_cs, target_cs, None
        )
        white_balance_matrix = utils.create_white_balance_matrix(grey_measurements_camera_target)
    else:
        white_balance_matrix = np.array(reference_wall_external_white_balance_matrix)

    # 5) Apply the white balance matrix to the RGBW measurements and Grey Ramps In Camera Space If Enabled
    if enable_plate_white_balance:
        (
            eotf_ramp_camera_native_gamut, _,
            macbeth_measurements_camera_native_gamut, max_white_camera_native_gamut,
            rgbw_measurements_camera_native_gamut
        ) = apply_matrix_to_samples(
            white_balance_matrix, eotf_ramp_camera_native_gamut,
            grey_measurements_native_camera_gamut,
            macbeth_measurements_camera_native_gamut, max_white_camera_native_gamut,
            rgbw_measurements_camera_native_gamut
        )

    # 6) We Get The Matrix To Convert From OCIO Reference Space To Target Space
    (
        reference_to_target_matrix, ocio_reference_cs,
        target_to_XYZ_matrix, reference_to_XYZ_matrix,
        reference_to_input_matrix
    ) = get_ocio_reference_to_target_matrix(
        input_plate_cs, target_cs, cs_cat=reference_to_target_cat
    )

    # 7) We Get The Green Value From The 18% Grey Patch, Scale This So It Equals 18% Of Peak Luminance
    # Apply This Scaling To RGBW & Grey Ramp Samples
    grey_measurements_white_balanced_native_gamut = rgbw_measurements_camera_native_gamut[3]
    grey_measurements_white_balanced_native_gamut_green = grey_measurements_white_balanced_native_gamut[1]

    target_over_white = 1 / max_white_camera_native_gamut[1]
    exposure_scaling_factor = 1.0 / (peak_lum * target_over_white)
    max_white_delta = max_white_camera_native_gamut[1] / eotf_ramp_camera_native_gamut[-1][1]

    rgbw_measurements_camera_native_gamut = rgbw_measurements_camera_native_gamut / exposure_scaling_factor
    eotf_ramp_camera_native_gamut = [
        item / exposure_scaling_factor for item in eotf_ramp_camera_native_gamut
    ]
    macbeth_measurements_camera_native_gamut = [
        item / exposure_scaling_factor for item in macbeth_measurements_camera_native_gamut
    ]

    # 8) We do the deltaE analysis
    delta_e_wrgb, delta_e_eotf_ramp, delta_e_macbeth = deltaE_ICtCp(
        rgbw_reference_samples, macbeth_reference_samples, eotf_ramp_reference_samples,
        rgbw_measurements_camera_native_gamut, eotf_ramp_camera_native_gamut,
        macbeth_measurements_camera_native_gamut, target_cs, native_camera_gamut_cs
    )

    # 9 If we have disabled eotf correction, we have to force the operation order
    if not enable_EOTF_correction:
        calculation_order = CalculationOrder.CO_CS_EOTF

    eotf_signal_value_rgb = np.array([
        [signal, signal, signal] for signal in eotf_signal_values
    ])

    # 10 We calculate the difference in the linearity of the wall based on the signals and eotf ramps
    eotf_linearity = calculate_eotf_linearity(eotf_signal_values, eotf_ramp_camera_native_gamut)

    eotf_ramp_camera_native_gamut_calibrated = eotf_ramp_camera_native_gamut.copy()
    macbeth_measurements_camera_native_gamut_calibrated = macbeth_measurements_camera_native_gamut.copy()
    if calculation_order == CalculationOrder.CO_CS_EOTF:  # Calc 3x3 -> 1Ds, and 3x3 only

        # 2: Create target to screen matrix
        screen_cs, target_to_screen_matrix, calibrated_screen_cs = extract_screen_cs(
            primaries_measurements=rgbw_measurements_camera_native_gamut[:3],
            primaries_saturation=measured_samples[Measurements.PRIMARIES_SATURATION],
            white_point_measurements=rgbw_measurements_camera_native_gamut[3],
            camera_native_cs=native_camera_gamut_cs,
            target_cs=target_cs,
            cs_cat=target_to_screen_cat,
            reference_to_target_matrix=reference_to_target_matrix,
            native_camera_gamut_cs=native_camera_gamut_cs, input_plate_cs=input_plate_cs,
            camera_conversion_cat=camera_conversion_cat,
            avoid_clipping=avoid_clipping,
            macbeth_measurements_camera_native_gamut=macbeth_measurements_camera_native_gamut,
            reference_samples=reference_samples

        )

        lut_r, lut_g, lut_b = np.array([]), np.array([]), np.array([])
        if enable_EOTF_correction:
            # 3: Compute LUTs for EOTF correction
            eotf_ramp_target = colour.RGB_to_RGB(
                eotf_ramp_camera_native_gamut, native_camera_gamut_cs, target_cs, None
            )

            rgbw_measurements_target = colour.RGB_to_RGB(
                rgbw_measurements_camera_native_gamut, native_camera_gamut_cs, target_cs, None
            )

            eotf_ramp_screen_target = [ca.vector_dot(target_to_screen_matrix, m) for m in eotf_ramp_target]
            rgbw_measurements_target = ca.vector_dot(target_to_screen_matrix, rgbw_measurements_target)
            white_balance_offset_matrix = utils.create_white_balance_matrix(rgbw_measurements_target[3])

            eotf_ramp_screen_target = [ca.vector_dot(white_balance_offset_matrix, m) for m in eotf_ramp_screen_target]

            lut_r, lut_g, lut_b = eotf_correction_calculation(
                eotf_ramp_screen_target,
                eotf_signal_value_rgb,
                delta_e_eotf_ramp,
                avoid_clipping=avoid_clipping,
                peak_lum=peak_lum
            )

            eotf_ramp_target_calibrated = colour.RGB_to_RGB(
                eotf_ramp_camera_native_gamut_calibrated, native_camera_gamut_cs, target_cs, None
            )

            eotf_ramp_target_calibrated = ca.vector_dot(
                target_to_screen_matrix, eotf_ramp_target_calibrated
            )

            eotf_ramp_camera_native_gamut_calibrated = colour.RGB_to_RGB(
                eotf_ramp_target_calibrated, target_cs, native_camera_gamut_cs, None
            )

            macbeth_measurements_target_calibrated = colour.RGB_to_RGB(
                macbeth_measurements_camera_native_gamut_calibrated, native_camera_gamut_cs, target_cs, None
            )

            macbeth_measurements_target_calibrated = ca.vector_dot(
                target_to_screen_matrix, macbeth_measurements_target_calibrated
            )

            macbeth_measurements_camera_native_gamut_calibrated = colour.RGB_to_RGB(
                macbeth_measurements_target_calibrated, target_cs, native_camera_gamut_cs, None
            )

            rgbw_measurements_target = apply_luts(
                rgbw_measurements_target,
                lut_r,
                lut_g,
                lut_b,
                inverse=False
            )

            rgbw_measurements_camera_native_gamut = colour.RGB_to_RGB(
                rgbw_measurements_target, target_cs, native_camera_gamut_cs, None
            )

            screen_cs, _, calibrated_screen_cs = extract_screen_cs(
                primaries_measurements=rgbw_measurements_camera_native_gamut[:3],
                primaries_saturation=measured_samples[Measurements.PRIMARIES_SATURATION],
                white_point_measurements=rgbw_measurements_camera_native_gamut[3],
                camera_native_cs=native_camera_gamut_cs,
                target_cs=target_cs,
                cs_cat=target_to_screen_cat,
                reference_to_target_matrix=reference_to_target_matrix,
                native_camera_gamut_cs=native_camera_gamut_cs, input_plate_cs=input_plate_cs,
                camera_conversion_cat=camera_conversion_cat,
                avoid_clipping=avoid_clipping,
                macbeth_measurements_camera_native_gamut=macbeth_measurements_camera_native_gamut,
                reference_samples=reference_samples
            )

    elif calculation_order == CalculationOrder.CO_EOTF_CS:  # Calc 1Ds->3x3
        eotf_ramp_target = colour.RGB_to_RGB(
            eotf_ramp_camera_native_gamut, native_camera_gamut_cs, target_cs, None
        )
        if not enable_plate_white_balance:
            eotf_ramp_target = [ca.vector_dot(white_balance_matrix, m) for m in eotf_ramp_target]

        # 1: Compute LUTs for EOTF correction
        lut_r, lut_g, lut_b, = eotf_correction_calculation(
            eotf_ramp_target,
            eotf_signal_value_rgb,
            delta_e_eotf_ramp,
            avoid_clipping=avoid_clipping,
            peak_lum=peak_lum
        )

        # rgb_ratio is not passed as the LUTs already include this factor
        rgbw_measurements_target = colour.RGB_to_RGB(
            rgbw_measurements_camera_native_gamut, native_camera_gamut_cs, target_cs, None
        )

        rgbw_measurements_target = apply_luts(
            rgbw_measurements_target,
            lut_r,
            lut_g,
            lut_b,
            inverse=False
        )

        rgbw_measurements_camera_native_gamut = colour.RGB_to_RGB(
            rgbw_measurements_target, target_cs, native_camera_gamut_cs, None
        )

        # 3: Create target to screen matrix
        screen_cs, target_to_screen_matrix, calibrated_screen_cs = extract_screen_cs(
            primaries_measurements=rgbw_measurements_camera_native_gamut[:3],
            primaries_saturation=measured_samples[Measurements.PRIMARIES_SATURATION],
            white_point_measurements=rgbw_measurements_camera_native_gamut[3],
            camera_native_cs=native_camera_gamut_cs,
            target_cs=target_cs,
            cs_cat=target_to_screen_cat,
            reference_to_target_matrix=reference_to_target_matrix,
            native_camera_gamut_cs=native_camera_gamut_cs, input_plate_cs=input_plate_cs,
            camera_conversion_cat=camera_conversion_cat,
            avoid_clipping=avoid_clipping,
            macbeth_measurements_camera_native_gamut=macbeth_measurements_camera_native_gamut,
            reference_samples=reference_samples
        )

    else:
        raise RuntimeError("Unknown calculation order: " + calculation_order)

    # 4: Compute max distances for gamut compression
    max_distances = colourspace_max_distances(
        source_cs=target_cs,
        destination_cs=screen_cs,
        cat=target_to_screen_cat,
        shadow_rolloff=gamut_compression_shadow_rolloff,
    )

    # Just For Plotting Needs
    if enable_EOTF_correction:
        eotf_ramp_camera_target_calibrated = colour.RGB_to_RGB(
            eotf_ramp_camera_native_gamut_calibrated, native_camera_gamut_cs, target_cs, None
        )
        if calculation_order == CalculationOrder.CO_EOTF_CS:
            eotf_ramp_camera_target_calibrated = [
                ca.vector_dot(target_to_screen_matrix, m) for m in eotf_ramp_camera_target_calibrated]

        eotf_ramp_camera_target_calibrated = apply_luts(
            eotf_ramp_camera_target_calibrated,
            lut_r,
            lut_g,
            lut_b,
            inverse=False
        )
        eotf_ramp_camera_native_gamut_calibrated = colour.RGB_to_RGB(
            eotf_ramp_camera_target_calibrated, target_cs, native_camera_gamut_cs, None
        )

        macbeth_measurements_target_calibrated = colour.RGB_to_RGB(
            macbeth_measurements_camera_native_gamut_calibrated, native_camera_gamut_cs, target_cs, None
        )

        macbeth_measurements_target_calibrated = apply_luts(
            macbeth_measurements_target_calibrated,
            lut_r, lut_g, lut_b, inverse=False
        )
        macbeth_measurements_camera_native_gamut_calibrated = colour.RGB_to_RGB(
            macbeth_measurements_target_calibrated, target_cs, native_camera_gamut_cs, None
        )

    measured_peak_lum_nits = [item * 100 for item in eotf_ramp_camera_native_gamut[-1]]

    macbeth_measurements_camera_native_gamut_XYZ = np.apply_along_axis(
        lambda rgb: native_camera_gamut_cs.matrix_RGB_to_XYZ.dot(rgb), 1, macbeth_measurements_camera_native_gamut
    )
    macbeth_measurements_camera_native_gamut_xy = colour.XYZ_to_xy(macbeth_measurements_camera_native_gamut_XYZ)

    macbeth_measurements_camera_native_gamut_calibrated_XYZ = np.apply_along_axis(
        lambda rgb: native_camera_gamut_cs.matrix_RGB_to_XYZ.dot(rgb), 1,
        macbeth_measurements_camera_native_gamut_calibrated
    )
    macbeth_measurements_camera_native_gamut_calibrated_xy = colour.XYZ_to_xy(
        macbeth_measurements_camera_native_gamut_calibrated_XYZ
    )
    # Return the results using simple, serializable types
    return {
        Results.PRE_CALIBRATION_SCREEN_PRIMARIES: screen_cs.primaries.tolist(),
        Results.PRE_CALIBRATION_SCREEN_WHITEPOINT: screen_cs.whitepoint.tolist(),
        Results.TARGET_GAMUT: target_cs.name,
        Results.ENABLE_PLATE_WHITE_BALANCE: enable_plate_white_balance,
        Results.ENABLE_GAMUT_COMPRESSION: enable_gamut_compression,
        Results.ENABLE_EOTF_CORRECTION: enable_EOTF_correction,
        Results.CALCULATION_ORDER: calculation_order,
        Results.WHITE_BALANCE_MATRIX: white_balance_matrix.tolist(),
        Results.TARGET_TO_SCREEN_MATRIX: target_to_screen_matrix.tolist(),
        Results.REFERENCE_TO_SCREEN_MATRIX: reference_to_target_matrix.tolist(),
        Results.REFERENCE_TO_TARGET_MATRIX: reference_to_target_matrix.tolist(),
        Results.EOTF_LUT_R: lut_r.tolist(),
        Results.EOTF_LUT_G: lut_g.tolist(),
        Results.EOTF_LUT_B: lut_b.tolist(),
        Results.MAX_DISTANCES: max_distances.tolist(),
        Results.TARGET_EOTF: target_EOTF,
        Results.NATIVE_CAMERA_GAMUT: native_camera_gamut,
        Results.OCIO_REFERENCE_GAMUT: ocio_reference_cs.name,
        Results.POST_CALIBRATION_SCREEN_PRIMARIES: calibrated_screen_cs.primaries.tolist(),
        Results.POST_CALIBRATION_SCREEN_WHITEPOINT: calibrated_screen_cs.whitepoint.tolist(),
        Results.PRE_EOTF_RAMPS: np.array(eotf_ramp_camera_native_gamut).tolist(),
        Results.POST_EOTF_RAMPS: np.array(eotf_ramp_camera_native_gamut_calibrated).tolist(),
        Results.PRE_MACBETH_SAMPLES_XY: np.array(macbeth_measurements_camera_native_gamut_xy).tolist(),
        Results.POST_MACBETH_SAMPLES_XY: np.array(macbeth_measurements_camera_native_gamut_calibrated_xy).tolist(),
        Results.DELTA_E_RGBW: delta_e_wrgb.tolist(),
        Results.DELTA_E_EOTF_RAMP: delta_e_eotf_ramp.tolist(),
        Results.DELTA_E_MACBETH: delta_e_macbeth.tolist(),
        Results.EXPOSURE_SCALING_FACTOR: exposure_scaling_factor,
        Results.TARGET_MAX_LUM_NITS: target_max_lum_nits,
        Results.MEASURED_18_PERCENT_SAMPLE: grey_measurements_white_balanced_native_gamut_green,
        Results.MEASURED_MAX_LUM_NITS: measured_peak_lum_nits,
        Results.REFERENCE_EOTF_RAMP: eotf_signal_values,
        Results.TARGET_TO_XYZ_MATRIX: target_to_XYZ_matrix.tolist(),
        Results.REFERENCE_TO_XYZ_MATRIX: reference_to_XYZ_matrix.tolist(),
        Results.REFERENCE_TO_INPUT_MATRIX: reference_to_input_matrix.tolist(),
        Results.MAX_WHITE_DELTA: max_white_delta,
        Results.EOTF_LINEARITY: eotf_linearity,
        Results.AVOID_CLIPPING: avoid_clipping
    }


def apply_matrix_to_samples(
        input_matrix: np.ndarray,
        eotf_ramp_camera_native_gamut: np.ndarray,
        grey_measurements_native_camera_gamut: np.ndarray,
        macbeth_measurements_camera_native_gamut: np.ndarray,
        max_white_camera_native_gamut: np.ndarray,
        rgbw_measurements_camera_native_gamut: np.ndarray) -> Tuple:
    """ Applies the given matrix to all the provided arrays and returns their modified form

    Args:
        input_matrix: The matrix we want to apply
        eotf_ramp_camera_native_gamut: The eotf ramp samples in camera colour space
        grey_measurements_native_camera_gamut: The grey samples in camera colour space
        macbeth_measurements_camera_native_gamut: The macbeth samples in camera colour space
        max_white_camera_native_gamut: The max-white samples in camera colour space
        rgbw_measurements_camera_native_gamut: The rgbw samples in camera colour space

    Returns: Tuple containing the modified samples

    """

    eotf_ramp_camera_native_gamut = [ca.vector_dot(input_matrix, m) for m in
                                     eotf_ramp_camera_native_gamut]
    rgbw_measurements_camera_native_gamut = ca.vector_dot(input_matrix,
                                                          rgbw_measurements_camera_native_gamut)
    macbeth_measurements_camera_native_gamut = ca.vector_dot(input_matrix,
                                                             macbeth_measurements_camera_native_gamut)

    grey_measurements_native_camera_gamut = ca.vector_dot(input_matrix,
                                                          grey_measurements_native_camera_gamut)
    max_white_camera_native_gamut = ca.vector_dot(
        input_matrix,
        max_white_camera_native_gamut)

    return (
        eotf_ramp_camera_native_gamut, grey_measurements_native_camera_gamut,
        macbeth_measurements_camera_native_gamut, max_white_camera_native_gamut,
        rgbw_measurements_camera_native_gamut
    )


def find_closest_below(sorted_numbers, target):
    closest_index = None

    for index, value in enumerate(sorted_numbers):
        if value > target:
            # Stop the search if the current value exceeds the target
            break
        closest_index = index

    return closest_index + 1


def convert_samples_to_required_cs(
        camera_conversion_cat: Union[str, constants.CAT],
        input_plate_cs: RGB_Colourspace,
        measured_samples: Dict, reference_samples: Dict, native_camera_gamut_cs: RGB_Colourspace,
        decoupled_lens_white_samples: np.array, peak_lum: float) -> Tuple:
    """ Convert the measured and reference samples to the required colour spaces.
        We also inject synthetic values for the 18% grey which helps us with the calibration

    Args:
        camera_conversion_cat: The colour conversion cat we want to use
        input_plate_cs: The colour space of the input plate we measured the samples from
        measured_samples: The measured samples from the input plate
        native_camera_gamut_cs: The native colour space of the camera, used to capture the input plate
        decoupled_lens_white_samples: An additional sample of the decoupled white
        reference_samples: The reference samples for the calibration process displayed on the led wall
        peak_lum: The peak luminance of the led wall

    Returns: Tuple containing the converted samples

    """
    eotf_signal_values = list(measured_samples[Measurements.EOTF_RAMP_SIGNAL])
    closest_18_percent_index = find_closest_below(eotf_signal_values, peak_lum * 0.18)
    eotf_signal_values.insert(closest_18_percent_index, peak_lum * 0.18)

    grey_measurements_native_camera_gamut = colour.RGB_to_RGB(
        measured_samples[Measurements.GREY], input_plate_cs, native_camera_gamut_cs, camera_conversion_cat
    )

    max_white_camera_native_gamut = colour.RGB_to_RGB(
        measured_samples[Measurements.MAX_WHITE], input_plate_cs, native_camera_gamut_cs, camera_conversion_cat
    )
    # Get The Macbeth Samples And Convert To Camera Native
    macbeth_measurements_camera_native_gamut = colour.RGB_to_RGB(
        measured_samples[Measurements.MACBETH], input_plate_cs, native_camera_gamut_cs, camera_conversion_cat
    )

    # Combine the primaries and white samples to give us RGBW in the input plate gamut space
    rgbw_measurements_input_plate_gamut = np.concatenate(
        (measured_samples[Measurements.DESATURATED_RGB], [measured_samples[Measurements.GREY]])
    )

    rgbw_measurements_camera_native_gamut = colour.RGB_to_RGB(
        rgbw_measurements_input_plate_gamut, input_plate_cs, native_camera_gamut_cs, camera_conversion_cat
    )

    eotf_ramp_camera_native_gamut = colour.RGB_to_RGB(
        measured_samples[Measurements.EOTF_RAMP], input_plate_cs, native_camera_gamut_cs, camera_conversion_cat
    )

    eotf_ramp_camera_native_gamut = np.insert(
        eotf_ramp_camera_native_gamut, closest_18_percent_index, grey_measurements_native_camera_gamut,
        axis=0
    )

    rgbw_reference_samples = np.concatenate(
        (reference_samples[Measurements.DESATURATED_RGB], [reference_samples[Measurements.GREY]])
    )

    macbeth_reference_samples = reference_samples[Measurements.MACBETH]
    eotf_ramp_reference_samples = list(reference_samples[Measurements.EOTF_RAMP])
    eotf_ramp_reference_samples.insert(closest_18_percent_index, [peak_lum * 0.18, peak_lum * 0.18, peak_lum * 0.18])

    decoupled_lens_white_samples_camera_native_gamut = None
    if decoupled_lens_white_samples:
        decoupled_lens_white_samples_camera_native_gamut = colour.RGB_to_RGB(
            decoupled_lens_white_samples, input_plate_cs, native_camera_gamut_cs, camera_conversion_cat
        )

    return (
        eotf_ramp_camera_native_gamut,
        grey_measurements_native_camera_gamut,
        macbeth_measurements_camera_native_gamut,
        max_white_camera_native_gamut,
        rgbw_measurements_camera_native_gamut,
        eotf_signal_values,
        decoupled_lens_white_samples_camera_native_gamut,
        rgbw_reference_samples,
        macbeth_reference_samples,
        eotf_ramp_reference_samples
    )


def get_calibration_colour_spaces(
        input_plate_gamut: Union[str, RGB_Colourspace, constants.ColourSpace],
        native_camera_gamut: Union[str, RGB_Colourspace, constants.ColourSpace],
        target_gamut: Union[str, RGB_Colourspace, constants.ColourSpace]
) -> Tuple[colour.RGB_Colourspace, colour.RGB_Colourspace, colour.RGB_Colourspace]:
    """ Get the colour spaces needed for the calibration process

    Args:
        input_plate_gamut: The colour space of the input plate we measured the samples from
        native_camera_gamut: The native colour space of the camera, used to capture the input plate
        target_gamut: The colour space we want to target for the calibration

    Returns: The python colour colour spaces needed for the calibration process

    """
    input_plate_cs = (
        colour.RGB_COLOURSPACES[input_plate_gamut] if isinstance(input_plate_gamut, str) else input_plate_gamut
    )
    native_camera_gamut_cs = (
        colour.RGB_COLOURSPACES[native_camera_gamut] if isinstance(native_camera_gamut, str) else native_camera_gamut
    )
    target_cs = (
        colour.RGB_COLOURSPACES[target_gamut] if isinstance(target_gamut, str) else target_gamut
    )
    return input_plate_cs, native_camera_gamut_cs, target_cs


def read_results_from_json(filename):
    """Read results from a JSON formatted file.

    Args:
        filename: (str)

    Returns:
        (dict) results

    """
    with open(filename, "r", encoding="utf-8") as json_file:
        results = json.load(json_file)

    return results
