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

Utility functions for open_vp_cal
"""
import hashlib
import re
import uuid
from typing import Tuple, Union, List, TYPE_CHECKING
import numpy as np

import colour
from colour import SpectralShape

from open_vp_cal.core import constants
from open_vp_cal.core.constants import PQ, CAT, CameraColourSpace

if TYPE_CHECKING:
    from open_vp_cal.led_wall_settings import LedWallSettings


def nits_to_pq(nits: int) -> float:
    """
    Convert nits (luminance in cd/m^2) to Perceptual Quantizer (PQ) non-linear signal value.

    Parameters:
    nits (float): Luminance in nits (cd/m^2).

    Returns:
    float: Corresponding PQ non-linear signal value.
    """
    FD = nits
    Y = FD / PQ.PQ_MAX_NITS
    E = ((PQ.PQ_C1 + PQ.PQ_C2 * Y ** PQ.PQ_M1) / (1 + PQ.PQ_C3 * Y ** PQ.PQ_M1)) ** PQ.PQ_M2
    return E


def pq_to_nits(pq_value: float) -> float:
    """
    Convert PQ non-linear signal value to nits (luminance in cd/m^2).

    Parameters:
    pq_value (float): PQ non-linear signal value.

    Returns:
    float: Corresponding luminance in nits (cd/m^2).
    """
    E = pq_value
    FD = PQ.PQ_MAX_NITS * ((max((E ** (1 / PQ.PQ_M2) - PQ.PQ_C1), 0)) /
                           (PQ.PQ_C2 - PQ.PQ_C3 * E ** (1 / PQ.PQ_M2))) ** (1 / PQ.PQ_M1)
    return FD


def scale_value(input_value, input_min, input_max, output_min, output_max):
    """
    Scales a given input value from one range to another.

    Args:
        input_value (float): The value to be scaled.
        input_min (float): The minimum value of the original range.
        input_max (float): The maximum value of the original range.
        output_min (float): The minimum value of the target range.
        output_max (float): The maximum value of the target range.

    Returns:
        float: The scaled value.
    """
    span = input_max - input_min
    scaled_value = output_min + ((input_value - input_min) / span) * (output_max - output_min)
    return scaled_value


def normalize(value, min_val, max_val):
    """
    Normalizes a value to a given range

    Args:
        value: The value to be normalized
        min_val: The minimum value of the range
        max_val: The maximum value of the range

    Returns: The normalised value

    """
    return (value - min_val) / (max_val - min_val)


def get_grey_signals(target_max_lum_nits, num_grey_patches) -> list[float]:
    """
    Generates a list of grey signal values based on the target maximum luminance and the number of grey patches.

    Args:
        target_max_lum_nits (int): The target maximum luminance in nits (cd/m^2).
        num_grey_patches (int): The number of grey patches.

    Returns:
        list[float]: A list of grey signal values from 0 to target_max_lum_nits, scaled so that 1 is 100 nits.
    """
    grey_signals = []
    max_nits_pq = nits_to_pq(target_max_lum_nits)
    pq_value_per_patch = max_nits_pq / num_grey_patches
    for idx in range(0, num_grey_patches + 1):
        patch_pq_value = idx * pq_value_per_patch
        patch_nits = pq_to_nits(patch_pq_value)
        grey_signals.append(patch_nits * 0.01)
    return grey_signals


def stack_numpy_array(img_np: "np.Array") -> ("np.Array", int, int, int):
    """ Stack the numpy array to be 3 channels

    Args:
        img_np: The numpy array to stack

    Returns: The stacked numpy array, the height & width of the image along with the number of channels

    """
    height, width, channels = None, None, None
    if len(img_np.shape) == 3:
        height, width, channels = img_np.shape
    elif len(img_np.shape) == 2:
        height, width = img_np.shape
        channels = 1
        img_np = np.stack((img_np,) * 3, axis=-1)  # make it a 3-channel image
    return img_np, height, width, channels


def get_legal_and_extended_values(peak_lum: int,
                                  image_bit_depth: int = 10,
                                  use_pq_peak_luminance: bool = True) -> tuple[int, int, int, int]:
    """ Get the legal and extended values for a given peak luminance and the bit depth

    Args:
        peak_lum: The peak luminance of the LED wall or display
        image_bit_depth: The bit depth of the image
        use_pq_peak_luminance: Whether to use the PQ peak luminance or not

    Returns: A tuple containing the minimum legal code value,
        the maximum legal code value, the minimum extended code

    """
    min_code_value = 0
    max_code_value = (2 ** image_bit_depth) - 1

    minimum_legal_code_value = int((2 ** image_bit_depth) / 16.0)
    maximum_legal_code_value = int((2 ** (image_bit_depth - 8)) * (16 + 219))

    # If we are in a PQ HDR workflow, our maximum nits are limited by our LED panels
    if use_pq_peak_luminance:
        pq_v = nits_to_pq(peak_lum)

        full_peak_white_at_given_bit_depth = pq_v * max_code_value
        legal_white_at_given_bit_depth = (full_peak_white_at_given_bit_depth / max_code_value *
                                          (maximum_legal_code_value - minimum_legal_code_value) +
                                          minimum_legal_code_value)
        legal_white_for_peak_luminance = legal_white_at_given_bit_depth
        maximum_legal_code_value = legal_white_for_peak_luminance

    minimum_legal = normalize(minimum_legal_code_value, min_code_value, max_code_value)
    maximum_legal = normalize(maximum_legal_code_value, min_code_value, max_code_value)

    minimum_extended = normalize(min_code_value, min_code_value, max_code_value)
    maximum_extended = normalize(max_code_value, min_code_value, max_code_value)

    return minimum_legal, maximum_legal, minimum_extended, maximum_extended


def get_target_colourspace_for_led_wall(led_wall: "LedWallSettings") -> colour.RGB_Colourspace:
    """ Gets the target colour space for the given led wall based on the target gamut
        If its standard gamut we return this directly from colour
        If its custom gamut we create a custom colour space from the primaries and white point

    Args:
        led_wall: The led wall to get the target colour space for

    Returns: The target colour space

    """
    try:
        color_space = colour.RGB_COLOURSPACES[led_wall.target_gamut]
    except KeyError:
        custom_primaries = led_wall.project_settings.project_custom_primaries[led_wall.target_gamut]
        color_space = get_custom_colour_space_from_primaries_and_wp(led_wall.target_gamut, custom_primaries)
    return color_space


def get_native_camera_colourspace_for_led_wall(led_wall: "LedWallSettings") -> colour.RGB_Colourspace:
    """ Gets the native camera colour space for the given led wall based on the native camera gamut
        If its standard gamut we return this directly from colour
        If its custom gamut we create a custom colour space from the primaries and white point

    Args:
        led_wall: The led wall to get the target colour space for

    Returns: The target colour space

    """
    try:
        color_space = colour.RGB_COLOURSPACES[led_wall.native_camera_gamut]
    except KeyError:
        custom_primaries = led_wall.project_settings.project_custom_primaries[led_wall.native_camera_gamut]
        color_space = get_custom_colour_space_from_primaries_and_wp(led_wall.native_camera_gamut, custom_primaries)
    return color_space


def get_custom_colour_space_from_primaries_and_wp(custom_name: str, values: List[List]) -> colour.RGB_Colourspace:
    """ Creates a custom colour space from the given primaries and white point

    Args:
        custom_name: The name of the custom colour space
        values: The values of the primaries and white point

    Returns: The custom colour space

    """
    if len(values) != 4:
        raise ValueError("Must provide 4 tuples for 3 primaries and 1 white point")

    white_point = values[-1]
    primaries = values[:3]
    return colour.RGB_Colourspace(custom_name, primaries, white_point)


def get_primaries_and_wp_for_XYZ_matrix(XYZ_matrix) -> Tuple[np.array, np.array]:
    """ Get the primaries and white point for the given XYZ matrix """
    primaries, wp = colour.primaries_whitepoint(XYZ_matrix)
    return primaries, wp


def replace_non_alphanumeric(input_string, replace_char):
    """
    Replace any non-alphanumeric characters in a string with a given character.

    Args:
        input_string (str): The input string.
        replace_char (str): The character to replace non-alphanumeric characters with.

    Returns:
        The modified string.
    """
    return re.sub(r'\W+', replace_char, input_string)


def generate_color(name) -> Tuple[int, int, int]:
    """ Generates a colour based on the given name.

    Args:
        name: The name to generate a colour for.

    Returns: A list of 3 ints representing the RGB colour.

    """
    name_hash = hash(name)

    red = abs((name_hash * 23) % 256)
    green = abs((name_hash * 37) % 256)
    blue = abs((name_hash * 51) % 256)

    return red, green, blue


def led_wall_reference_wall_sort(led_walls: list["LedWallSettings"]) -> list["LedWallSettings"]:
    """ Sorts the given list of led_walls so that they are processed in the correct order based on their references

    Args:
        led_walls: A list of led walls to sort

    Returns: The same list of led walls in the correct order for processing based on their external references to other
        walls

    """
    visited = {led_wall.name: False for led_wall in led_walls}
    stack = []

    def visit(instance):
        if not visited[instance.name]:
            visited[instance.name] = True
            if instance.reference_wall:
                ref_wall = instance.project_settings.get_led_wall(instance.reference_wall)
                visit(ref_wall)
            stack.append(instance)

    for led_wall in led_walls:
        if not visited[led_wall.name]:
            visit(led_wall)

    return stack


def calculate_validation_status(current_status, result):
    """ Calculates the validation status based on the current status and the result

    Args:
        current_status: The current status
        result: The result status

    Returns: The new status

    """
    values = {
        constants.ValidationStatus.PASS: 2,
        constants.ValidationStatus.WARNING: 1,
        constants.ValidationStatus.FAIL: 0
    }
    current_status_val = values[current_status]
    result_val = values[result]
    if result_val < current_status_val:
        return result
    return current_status


def get_spectral_locus_positions(scale: int) -> Tuple[np.array, np.array]:
    """ Get the positions of the spectral locus in xy space, scaled by the given factor

    Args:
        scale: The scale to apply to the spectral locus

    Returns: The x and y positions of the spectral locus

    """
    spectral_locus_values = SpectralShape(390, 780, 0.1).range()
    XYZ = colour.wavelength_to_XYZ(spectral_locus_values)
    values = colour.XYZ_to_xy(XYZ)
    values = values * scale
    spectral_locus_x = values[:, 0]
    spectral_locus_y = values[:, 1]
    return np.append(spectral_locus_x, spectral_locus_x[0]), np.append(spectral_locus_y, spectral_locus_y[0])


def get_planckian_locus_positions(scale: int) -> tuple[list[float], list[float]]:
    """ Get the positions of the planckian locus in xy space, scaled by the given factor

    Args:
        scale: The scale to apply to the planckian locus

    Returns: The x and y positions of the planckian locus

    """
    x_pos = []
    y_pos = []
    for i in range(2500, 10001, 100):
        cie_xy = colour.temperature.CCT_to_xy_CIE_D(i)
        scaled_x = float(cie_xy[0]) * scale
        scaled_y = float(cie_xy[1]) * scale
        x_pos.append(scaled_x)
        y_pos.append(scaled_y)
    return x_pos, y_pos


def is_point_inside_polygon(point: Tuple[float, float], polygon: np.array) -> bool:
    """
    Checks if a given point of x & y coordinates is inside a given polygon, an array of points which form a closed shape
    of connecting edges

    Args:
        point: The point to check
        polygon: The polygon to check against

    Returns: True if the point is inside the polygon, False otherwise

    """
    x_pos, y_pos = point
    odd_nodes = False
    j = len(polygon) - 1  # Last vertex in the polygon
    for idx in range(0, len(polygon)):
        xi, yi = polygon[idx]
        xj, yj = polygon[j]
        if yi < y_pos <= yj or yj < y_pos <= yi:
            if xi + (y_pos - yi) / (yj - yi) * (xj - xi) < x_pos:
                odd_nodes = not odd_nodes
        j = idx
    return odd_nodes


def find_factors_pairs(input_num: int) -> List[Tuple[int, int]]:
    """ Find the factor pairs for the given number

    Args:
        input_num: The number to find the factor pairs for

    Returns: A list of factor pairs

    """
    factor_pairs = []

    for i in range(4, int(input_num ** 0.5) + 1):  # start loop from 4
        if input_num % i == 0:
            factor_pairs.append((i, input_num // i))

    return factor_pairs


def find_nearest_factors_for_ratio(n, ratio_width=16, ratio_height=9) -> Tuple[int, int]:
    """ Find the nearest factors for the given ratio

    Args:
        n: The number to find the factors for
        ratio_width: The width of the ratio
        ratio_height: The height of the ratio

    Returns: The nearest factors for the given ratio

    """
    if n % 2 != 0:
        n += 1

    best_a = 4
    best_b = n // 4
    min_difference = float("inf")

    for pair in find_factors_pairs(n):
        a_item, b_item = pair
        difference = abs(ratio_width / ratio_height - a_item / b_item)
        if difference < min_difference:
            best_a = a_item
            best_b = b_item
            min_difference = difference

    return best_a, best_b


def split_list(input_list: List, split_factor: int) -> List[List]:
    """ For the given input list, we split it into split_factor number of approximately equal parts

    Args:
        input_list: the list we want to split
        split_factor: the amount we want to split the lists by

    Returns: A list of lists each the size of split_factor, unless the input list is not divisible by split_factor,
        in which case the last list will be smaller

    """
    avg = len(input_list) // split_factor
    leftovers = len(input_list) % split_factor
    parts = []
    start = 0
    for i in range(split_factor):
        end = start + avg + (1 if i < leftovers else 0)
        parts.append(input_list[start:end])
        start = end
    return parts


def clamp(value: Union[int, float], min_value: Union[int, float], max_value: Union[int, float]) -> Union[int, float]:
    """ Clamp a value between a min and max value

    Args:
        value: value to clamp
        min_value: The minimum value
        max_value: The maximum value

    Returns: The clamped value

    """
    return max(min_value, min(value, max_value))


def create_white_balance_matrix(input_rgb_sample: np.ndarray):
    """ Creates a white balance matrix from the input RGB sample, by using the red and blue multiplies, based on the
        green channel.

    Args:
        input_rgb_sample: An array of RGB values in the form [R,G,B]

    Returns: A 3x3 matrix which can be used to white balance the input RGB values

    """
    green_value = input_rgb_sample[1]

    # Green Value / Red Value
    red_mult_val = green_value / input_rgb_sample[0]

    green_mult_val = green_value / input_rgb_sample[1]

    # Green Value / Blue Value
    blue_mult_val = green_value / input_rgb_sample[2]

    white_balance_matrix = np.asarray([[red_mult_val, 0.0, 0.0], [0.0, green_mult_val, 0.0], [0.0, 0.0, blue_mult_val]])
    return white_balance_matrix


def get_cat_for_camera_conversion(camera_colour_space_name: str) -> CAT:
    """ For the given camera colour space, return the appropriate chromatic adaptation transform method

    Args:
        camera_colour_space_name: The name of the camera colour space

    Returns: The chromatic adaptation transform method

    """
    camera_conversion_cat = CAT.CAT_CAT02
    if camera_colour_space_name == CameraColourSpace.RED_WIDE_GAMUT:
        camera_conversion_cat = CAT.CAT_BRADFORD
    return camera_conversion_cat


def generate_truncated_hash(length: int = 6) -> str:
    """
    Generate a truncated SHA-256 hash from a UUID.

    Args:
        length: The length of the truncated hash, by default 4.

    Returns:
        str: The truncated hexadecimal hash.
    """
    # Generate a UUID
    unique_id = uuid.uuid4()

    # Hash the UUID using SHA-256
    hash_object = hashlib.sha256(str(unique_id).encode())

    # Convert the hash to a hexadecimal string
    hash_hex = hash_object.hexdigest()

    # Truncate the hash to the desired length
    return hash_hex[:length]
