"""
Module dedicated to the creation of colour chart images in given colour spaces, and under certain illuminents
"""
from typing import Tuple

import colour
from colour.models import RGB_COLOURSPACE_ACES2065_1

# pylint: disable=E0401
import OpenImageIO as Oiio


# pylint: enable=E0401


def calculate_gap(
        chart_width: int,
        chart_height: int,
        patch_size: int,
        patches_horizontally: int,
        patches_vertically: int) -> Tuple[float, float]:
    """ Calculates the gap between patches in the chart

    Args:
        chart_width: The width of the chart
        chart_height: The height of the chart
        patch_size: The size of the patches
        patches_horizontally: The number of patches horizontally
        patches_vertically: The number of patches vertically

    Returns: The width and height of the gaps between patches

    """
    # Calculate the total size of the patches in each dimension
    total_patch_width = patches_horizontally * patch_size
    total_patch_height = patches_vertically * patch_size

    # Calculate the total space available for gaps in each dimension
    gap_space_width = chart_width - total_patch_width
    gap_space_height = chart_height - total_patch_height

    # Calculate the number of gaps in each dimension (one more than the number of patches)
    gaps_horizontally = patches_horizontally + 1
    gaps_vertically = patches_vertically + 1

    # Calculate the size of the gaps
    gap_width = gap_space_width / gaps_horizontally
    gap_height = gap_space_height / gaps_vertically

    return gap_width, gap_height


def generate_color_chart(patch_colors, chart_width: int = 1920, chart_height: int = 1280):
    """ Generates a colour chart for the given patch colours

    Args:
        patch_colors: A list of RGB values for each patch
        chart_width: The width of the chart in pixels
        chart_height: The height of the chart in pixels

    Returns: An image buffer containing the colour chart

    """
    # Colour charts are 6 patches wide by 4 patches deep
    patches_horizontally, patches_vertically = 6, 4

    # Each patch is scaled by 20%, so they have a gap between them
    patch_scale = 0.8

    # Patches are square
    patch_size = int((chart_width / patches_horizontally) * patch_scale)

    # Calculate the gaps between patches
    gap_width, gap_height = calculate_gap(
        chart_width, chart_height, patch_size, patches_horizontally, patches_vertically
    )

    # Create an overall image buffer with 3 channels (for RGB colours)
    chart = Oiio.ImageBuf(Oiio.ImageSpec(chart_width, chart_height, 3, Oiio.FLOAT))

    # Iterate over the number of patches horizontally and vertically
    count = 0
    for j in range(patches_vertically):
        for i in range(patches_horizontally):
            # Calculate the position for the top left corner of the current patch
            # Add a gap to the position to allow for border space
            x_pos = int((i * (patch_size + gap_width)) + gap_width)
            y_pos = int((j * (patch_size + gap_height)) + gap_height)

            # Create an image buffer for the current patch
            patch = Oiio.ImageBuf(Oiio.ImageSpec(patch_size, patch_size, 3, Oiio.FLOAT))

            # Fill the patch with the corresponding colour
            Oiio.ImageBufAlgo.fill(patch, patch_colors[count].tolist())

            # Copy the patch into the overall chart at the correct position
            Oiio.ImageBufAlgo.paste(chart, x_pos, y_pos, 0, 0, patch)

            count += 1

    return chart


def get_colour_checker_for_colour_space_and_illuminant(
        colour_space: colour.RGB_Colourspace, illuminant=None, chart_width: int = 1920,
        chart_height: int = 1280) -> Oiio.ImageBuf:
    """ Generates a colour chart in the given colour space using the provided illuminant

    Args:
        colour_space: The colour space to use for the colour chart
        illuminant: The illuminant to use for the colour chart
        chart_width: The width of the chart in pixels
        chart_height: The height of the chart in pixels

    Returns: An image buffer containing the colour chart

    """
    rgb_references = get_rgb_references_for_color_checker(colour_space, illuminant)
    return generate_color_chart(rgb_references, chart_width=chart_width, chart_height=chart_height)


def get_rgb_references_for_color_checker(colour_space, illuminant=None):
    """ Gets the RGB references for the colour checker in the given colour space

    Args:
        colour_space: The colour space to use for the colour chart
        illuminant: The illuminant to use for the colour chart

    Returns: The RGB references for the colour checker in the given colour space

    """
    colour_checker_reference, xyY_references = get_color_checker_reference_in_xyY()
    illuminant = illuminant if illuminant else colour_checker_reference.illuminant
    xyz_references = colour.xyY_to_XYZ(xyY_references)
    rgb_references = colour.XYZ_to_RGB(
        xyz_references,
        illuminant,
        colour_space.whitepoint,
        colour_space.matrix_XYZ_to_RGB,
    )
    return rgb_references


def get_color_checker_reference_in_xyY() -> Tuple:
    """ Gets the colour checker reference in xyY, and the colour checker reference
    
    Returns: The colour checker reference in xyY, and the colour checker reference

    """
    colour_checker_reference = colour.CCS_COLOURCHECKERS[
        'ColorChecker24 - After November 2014']
    xyY_references = colour.utilities.as_float_array(
        colour_checker_reference.data.values())
    return colour_checker_reference, xyY_references


def get_color_checker_aces2065_1(illuminant=None, chart_width: int = 1920, chart_height: int = 1280) -> Oiio.ImageBuf:
    """ Generates a colour chart in ACES2065-1 colour space using the provided illuminant

    Keyword Args:
        illuminant: The illuminant to use for the colour chart
        chart_width: The width of the chart in pixels
        chart_height: The height of the chart in pixels

    Returns: An image buffer containing the colour chart

    """
    return get_colour_checker_for_colour_space_and_illuminant(
        RGB_COLOURSPACE_ACES2065_1, illuminant=illuminant, chart_width=chart_width, chart_height=chart_height
    )
