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

Module contains utility functions specific to OpenColorIO
"""
import math
import os
from typing import Any

import PyOpenColorIO as ocio
from importlib.metadata import version
from packaging.version import Version
import numpy as np

from colour.models import eotf_ST2084, eotf_inverse_ST2084

from open_vp_cal.core import constants, utils
from open_vp_cal.core.calibrate import resample_lut

# Currently we have a hard requirement on OCIO 2.1+ to support gamut compression
ocio_version = Version(version("opencolorio"))
required_version = Version("2.4")
if not ocio_version >= required_version:
    raise ImportError("Requires OCIO v2.4 or greater.")


def compute_power_curve_points(x_start: float, y_start: float, x_end: float, y_end: float, n: int):
    """
    Compute points for a power function curve.

    Args:
        x_start (float): The starting x value.
        y_start (float): The starting y value.
        x_end (float): The ending x value.
        y_end (float): The ending y value.
        n (int): The number of points to generate.

    """
    # Calculate the exponent B and coefficient A for the power function y = A * x^B.
    B = math.log2(y_end / y_start) / math.log2(x_end / x_start)
    A = y_start / (x_start ** B)

    # Generate n linearly spaced x values between x_start and x_end.
    x_vals = np.linspace(x_start, x_end, n)

    # Compute the corresponding y values using the power function.
    y_vals = A * (x_vals ** B)

    return x_vals, y_vals, A, B


def create_rolloff_grading_curve_pq(peak_lum: int, peak_content: int, rolloff_start: float = 0.9):
    """
    Create a rolloff grading curve for PQ values.

    Args:
        peak_lum (int): Peak luminance of the led wall in nits.
        peak_content (int): Peak content of the content in nits.
        rolloff_start (float): Percentage of the peak luminance to start the rolloff.
    """
    peak_lum_pq = eotf_inverse_ST2084(peak_lum)
    peak_content_pq = eotf_inverse_ST2084(peak_content)

    minimum_peak_lum_pq = eotf_inverse_ST2084(peak_lum * rolloff_start)

    minimum_peak_lum_anchor = minimum_peak_lum_pq * 0.9

    curve_points = [0.0, 0.0]
    curve_points.extend([minimum_peak_lum_anchor, minimum_peak_lum_anchor])

    n = 10
    x_vals, y_vals, _, _ = compute_power_curve_points(float(minimum_peak_lum_pq), float(minimum_peak_lum_pq), float(peak_content_pq), float(peak_lum_pq), n)
    for x, y in zip(x_vals, y_vals):
        curve_points.extend([x, y])

    curve = ocio.GradingBSplineCurve([point for point in curve_points])

    rolloff_transform_master = ocio.GradingRGBCurveTransform()
    rolloff_transform_master.setStyle(ocio.GRADING_LOG)

    # Create a GradingRGBCurve and assign the individual channel curves.
    grading_rgb_curve = ocio.GradingRGBCurve()
    grading_rgb_curve.master = curve
    rolloff_transform_master.setValue(grading_rgb_curve)


    return rolloff_transform_master

def create_rolloff_look(peak_lum: int, peak_content: int, prefix: str = "", rolloff_start: float = 0.9):
    """ Creates an ocio look containing a rolloff grading curve for a given wall.

    Args:
        peak_lum (int): Peak luminance of the led wall in nits.
        peak_content (int): Peak content of the content in nits.
        wall_name (str): Name of the wall.
        config (ocio.Config): OCIO configuration object.
        rolloff_start (float): Percentage of the peak luminance to start the rolloff.

    """
    look_name = f"{prefix}_Rolloff_{int(peak_lum * rolloff_start)}_nits_to_{peak_lum}_nits"
    look = ocio.Look()
    look.setProcessSpace("ACES2065-1")

    group = ocio.GroupTransform()
    curve = ocio.BuiltinTransform(
        "CURVE - ST-2084_to_LINEAR",
        direction=ocio.TransformDirection.TRANSFORM_DIR_INVERSE,
    )
    group.appendTransform(curve)
    rolloff_transform_master = create_rolloff_grading_curve_pq(peak_lum, peak_content, rolloff_start=rolloff_start)
    group.appendTransform(rolloff_transform_master)
    curve2 = ocio.BuiltinTransform(
        "CURVE - ST-2084_to_LINEAR"
    )
    group.appendTransform(curve2)

    look.setTransform(group)
    look.setName(look_name)
    return look


def write_eotf_lut_pq(lut_r, lut_g, lut_b, filename) -> None:
    """ Write a LUT to a file in CLF format using PQ

    Args:
        lut_r: The values for the red channel of the LUT
        lut_g: The values for the green channel of the LUT
        lut_b: The values for the blue channel of the LUT
        filename: The filename to write the LUT to
        peak_lum: The peak luminance of the display in nits
        avoid_clipping: Whether to avoid clipping the LUT values ensuring we do not go beyond the peak luminance
    """
    lut_transform = ocio.Lut1DTransform(length=constants.LUT_LEN, inputHalfDomain=False)

    # resample the lut data to be linearly indexed in PQ where 1 is 100 nits
    value_pq = np.linspace(0, 1, constants.LUT_LEN)
    pq_max_scaled_1_100 = constants.PQ.PQ_MAX_NITS * 0.01

    value = eotf_ST2084(value_pq) / pq_max_scaled_1_100

    lut_r_i = resample_lut(lut_r, value)
    lut_g_i = resample_lut(lut_g, value)
    lut_b_i = resample_lut(lut_b, value)

    lut_r_i_pq = eotf_inverse_ST2084(lut_r_i * pq_max_scaled_1_100)
    lut_g_i_pq = eotf_inverse_ST2084(lut_g_i * pq_max_scaled_1_100)
    lut_b_i_pq = eotf_inverse_ST2084(lut_b_i * pq_max_scaled_1_100)

    for i in range(constants.LUT_LEN):
        lut_transform.setValue(i, lut_r_i_pq[i][0], lut_g_i_pq[i][0], lut_b_i_pq[i][0])

    # write the LUT to CLF format
    write_lut_to_clf(filename, lut_transform)


def write_lut_to_clf(filename: str, lut_transform: ocio.Lut1DTransform) -> None:
    """ Writes the given lut transform to a CLF file for the given filepath

    Args:
        filename: The filename to write the LUT to
        lut_transform: The LUT transform to write
    """
    config = ocio.Config.CreateRaw()
    group = ocio.GroupTransform()
    group.appendTransform(lut_transform)
    with open(filename, "w", encoding="utf-8") as file:
        file.write(group.write(constants.FILE_FORMAT_CLF, config))


def numpy_matrix_to_ocio_matrix(np_mat: np.ndarray) -> Any:
    """ Convert a numpy matrix to an OCIO matrix

    Args:
        np_mat: The numpy matrix to convert

    Returns: The OCIO matrix as a flattened list

    """
    ocio_matrix = np.identity(4)
    ocio_matrix[0:3, 0:3] = np_mat
    return ocio_matrix.flatten().tolist()


def create_EOTF_LUT(lut_filename: str, results: dict) -> ocio.GroupTransform:
    """ Create an EOTF LUT

    Args:
        lut_filename: The filename to write the LUT too
        results: The results from the calibration

    Returns: The OCIO group transform for the EOTF LUT

    """
    # EOTF LUT
    # must be written to a sidecar file, which is named from the config
    write_eotf_lut_pq(
        results[constants.Results.EOTF_LUT_R],
        results[constants.Results.EOTF_LUT_G],
        results[constants.Results.EOTF_LUT_B],
        lut_filename
    )
    eotf_lut = ocio.FileTransform(
        os.path.basename(lut_filename),
        direction=ocio.TransformDirection.TRANSFORM_DIR_INVERSE,
    )
    eotf_lut_group = ocio.GroupTransform()
    # OCIO PQ builtin expects 1 to be 100nits
    eotf_lut_group.appendTransform(ocio.BuiltinTransform("CURVE - LINEAR_to_ST-2084"))
    eotf_lut_group.appendTransform(eotf_lut)
    eotf_lut_group.appendTransform(ocio.BuiltinTransform("CURVE - ST-2084_to_LINEAR"))

    return eotf_lut_group


def create_gamut_compression(results: dict) -> ocio.GroupTransform:
    """ Create a gamut compression transform

    Args:
        results: The results from the calibration

    Returns: The OCIO group transform for the gamut compression

    """
    gamut_comp_group = ocio.GroupTransform()

    # the three distances (called limits in the ctl) that we'll modify.
    max_dists = results[constants.Results.MAX_DISTANCES]

    lim_cyan = utils.clamp(
        max_dists[0], constants.GAMUT_COMPRESSION_LIMIT_MIN, constants.GAMUT_COMPRESSION_LIMIT_MAX)
    lim_magenta = utils.clamp(
        max_dists[1], constants.GAMUT_COMPRESSION_LIMIT_MIN, constants.GAMUT_COMPRESSION_LIMIT_MAX)
    lim_yellow = utils.clamp(
        max_dists[2], constants.GAMUT_COMPRESSION_LIMIT_MIN, constants.GAMUT_COMPRESSION_LIMIT_MAX)

    # other values shouldn't need to change, so hard coding.
    gc_params = [lim_cyan, lim_magenta, lim_yellow, 0.9, 0.9, 0.9, 4.0]

    # ACES gamut comp incorporates AP0 to AP1 input transform, which we need
    # to counteract by applying an AP1 to AP0 pre-transform and AP0 to AP1
    # post-transform
    gamut_comp_group.appendTransform(ocio.BuiltinTransform("ACEScg_to_ACES2065-1"))

    gamut_comp_group.appendTransform(
        ocio.FixedFunctionTransform(
            ocio.FixedFunctionStyle.FIXED_FUNCTION_ACES_GAMUT_COMP_13, gc_params
        )
    )

    gamut_comp_group.appendTransform(
        ocio.BuiltinTransform(
            "ACEScg_to_ACES2065-1", ocio.TransformDirection.TRANSFORM_DIR_INVERSE
        )
    )

    return gamut_comp_group


def create_grading_bspline_curve(lut: list) -> ocio.GradingBSplineCurve:
    """
    Creates a GradingCurve from a list of control points.

    Parameters:
        lut (list): A list of [x, y] pairs representing control poxwints.

    Returns:
        ocio.GradingCurve: A GradingCurve with the control points inserted.
    """
    curve = ocio.GradingBSplineCurve([v for point in lut for v in point])
    return curve



def create_LUT_GradingCurveTransform(lut_r, lut_g, lut_b):
    grading_transform_red = ocio.GradingRGBCurveTransform()
    grading_transform_red.setStyle(ocio.GRADING_LOG)

    # Create a GradingRGBCurve and assign the individual channel curves.
    grading_rgb_curve = ocio.GradingRGBCurve()
    grading_rgb_curve.red = create_grading_bspline_curve(lut_r)

    # Set the RGB curve into the transform.
    grading_transform_red.setValue(grading_rgb_curve)

    grading_transform_green = ocio.GradingRGBCurveTransform()
    grading_transform_green.setStyle(ocio.GRADING_LOG)

    # Create a GradingRGBCurve and assign the individual channel curves.
    grading_rgb_curve = ocio.GradingRGBCurve()
    grading_rgb_curve.green = create_grading_bspline_curve(lut_g)

    # Set the RGB curve into the transform.
    grading_transform_green.setValue(grading_rgb_curve)

    grading_transform_blue = ocio.GradingRGBCurveTransform()
    grading_transform_blue.setStyle(ocio.GRADING_LOG)

    # Create a GradingRGBCurve and assign the individual channel curves.
    grading_rgb_curve = ocio.GradingRGBCurve()
    grading_rgb_curve.blue = create_grading_bspline_curve(lut_b)

    # Set the RGB curve into the transform.
    grading_transform_blue.setValue(grading_rgb_curve)


    return grading_transform_red, grading_transform_green, grading_transform_blue



def populate_ocio_group_transform_for_CO_CS_EOTF(
        clf_name: str, group: ocio.GroupTransform, output_folder: str, results: dict) -> None:
    """ Populate the OCIO group transform for the CO_CS_EOTF calculation order

    Args:
        clf_name: The name of the clf file we want to write out
        group: The OCIO group transform to add the transforms to
        output_folder: The folder to write the CLF files to
        results: The results from the calibration

    """
    # EOTF LUT
    if results[constants.Results.ENABLE_EOTF_CORRECTION]:
        try:
            grading_group = ocio.GroupTransform()
            grading_curve_r, grading_curve_g, grading_curve_b = create_LUT_GradingCurveTransform(
                results[constants.Results.EOTF_LUT_R],
                results[constants.Results.EOTF_LUT_G],
                results[constants.Results.EOTF_LUT_B]
            )
            grading_group.appendTransform(grading_curve_r)
            grading_group.appendTransform(grading_curve_g)
            grading_group.appendTransform(grading_curve_b)
            group.appendTransform(grading_group)
        except:
            clf_name = os.path.join(output_folder, clf_name + ".clf")
            eotf_lut_group = create_EOTF_LUT(clf_name, results)
            group.appendTransform(eotf_lut_group)

    # matrix transform to screen colour space
    group.appendTransform(
        ocio.MatrixTransform(
            numpy_matrix_to_ocio_matrix(results[constants.Results.TARGET_TO_SCREEN_MATRIX])
        )
    )


def populate_ocio_group_transform_for_CO_EOTF_CS(
        clf_name: str, group: ocio.GroupTransform, output_folder: str, results: dict) -> None:
    """ Populate the OCIO group transform for the CO_EOTF_CS calculation order

    Args:
        clf_name: The name of the clf file we want to write out
        group: The OCIO group transform to add the transforms to
        output_folder: The folder to write the CLF files to
        results: The results from the calibration
    """
    group.appendTransform(
        ocio.MatrixTransform(
            numpy_matrix_to_ocio_matrix(results[constants.Results.TARGET_TO_SCREEN_MATRIX])
        )
    )

    # EOTF LUT
    # must be written to a sidecar file, which is named from the config
    if results[constants.Results.ENABLE_EOTF_CORRECTION]:
        try:
            grading_group = ocio.GroupTransform()
            grading_curve_r, grading_curve_g, grading_curve_b = create_LUT_GradingCurveTransform(
                results[constants.Results.EOTF_LUT_R],
                results[constants.Results.EOTF_LUT_G],
                results[constants.Results.EOTF_LUT_B]
            )
            grading_group.appendTransform(grading_curve_r)
            grading_group.appendTransform(grading_curve_g)
            grading_group.appendTransform(grading_curve_b)
            group.appendTransform(grading_group)
        except:
            lut_filename = os.path.join(output_folder, clf_name + ".clf")
            eotf_lut_group = create_EOTF_LUT(lut_filename, results)
            group.appendTransform(eotf_lut_group)


def bake_3d_lut(
        input_color_space: str, ocio_display_colour_space: str, ocio_view_transform: str, config_path: str,
        output_lut_path: str, cube_size: int = 64, lut_format: str = "resolve_cube") -> str:
    """
    Bake a 3D LUT from an OpenColorIO configuration.

    Args:
        input_color_space (str): The input colour space.
        ocio_display_colour_space (str): The OCIO display colour space.
        ocio_view_transform (str): The OCIO view transform.
        config_path (str): Path to the OCIO configuration file.
        output_lut_path (str): Path to save the baked 3D LUT.
        cube_size (int): Cube size for the 3D LUT. Default is 33.
        lut_format (str): Format for the 3D LUT. Default is "cub".
    """
    # Load the OCIO configuration
    config = ocio.Config.CreateFromFile(config_path)

    # Validate the colour spaces
    if not any(cs.getName() == input_color_space for cs in config.getColorSpaces()):
        raise ValueError(f"Input color space '{input_color_space}' does not exist in the provided OCIO config.")

    if not any(cs == ocio_display_colour_space for cs in config.getDisplaysAll()):
        raise ValueError(
            f"Display Colour Space '{ocio_display_colour_space}' does not exist in the provided OCIO config.")

    if not any(cs == ocio_view_transform for cs in config.getViews(ocio_display_colour_space)):
        raise ValueError(
            f"View Transform '{ocio_view_transform}' does not exist in the provided OCIO config.")

    # Create the Baker and set its properties
    baker = ocio.Baker()
    baker.setConfig(config)
    baker.setFormat(lut_format)
    baker.setInputSpace(input_color_space)
    baker.setDisplayView(ocio_display_colour_space, ocio_view_transform)
    baker.setCubeSize(cube_size)

    # Bake the LUT
    baker.bake(output_lut_path)
    return output_lut_path

def get_colorspace_names(color_config: str)-> list[str]:
    """ Gets the colour space names from the given color config

    Args:
        color_config: The file path to the colour config

    Returns:
        Returns a list of strings for the names of the available colour configs
    """
    if not os.path.exists(color_config):
        raise ValueError("Color config does not exist: " + color_config)

    config = ocio.Config().CreateFromFile(color_config)
    return [name for name in config.getColorSpaceNames()]
