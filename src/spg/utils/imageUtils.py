""" A selection of utils to aid in the production of images used in our test patterns

"""
import os
import subprocess
import sys
from spg.utils.resource_loader import ResourceLoader

import PyOpenColorIO as ocio

try:
    # Due to OpenImageIO being unavailable via pip, we handle the import error so we can still use SPG without the
    # image generation. Place holder until we can get OpenImageIO easily installed as a dependency
    import OpenImageIO as oiio
    from OpenImageIO import ImageBuf, ImageSpec, ImageBufAlgo
except ModuleNotFoundError as e:
    oiio = None
    print("Unable To Import OpenImageIO")
    print(e.msg)

from spg.utils import constants
from open_vp_cal.imaging import imaging_utils


def create_solid_color_image(width, height, num_channels=3, color=(0, 0, 0)):
    """ Creates an OIIO ImageBuffer of a given solid color

    :param width: The width of the image we want to create
    :param height: The height of the image we want to create
    :param num_channels: The number of channels within the image
    :param color: The color that we want to fill the image with
    :return: ImageBuf
    """

    # We always work in floats until we write to disk as not to limit the buffer
    spec = ImageSpec(width, height, num_channels, oiio.FLOAT)
    buffer = ImageBuf(spec)
    oiio.ImageBufAlgo.fill(buffer, color)
    return buffer


def add_border_to_image(buffer, border_width, border_color=(0, 0, 0)):
    """ Adds a border of given color and width to the image

    :param buffer: ImageBuf we want to add the border too
    :param border_width: the width of the border in number of pixels
    :param border_color: the color we want the border to be
    :return: ImageBuf
    """
    for x in range(0, border_width):
        ImageBufAlgo.render_box(
            buffer,
            buffer.xmin + x,
            buffer.ymin + x,
            buffer.xmax - x,
            buffer.ymax - x,
            color=border_color, fill=False
        )

    return buffer


def add_text_to_image_centre(buffer, text, font_size=None, font_path=None, text_color=(0, 0, 0),
                             x_pos_override=None, y_pos_override=None):
    """ Adds the given text to the centre of the image, if not font size provided we estimate 80 % of the average height
        and width to try and fill as much of the image as possible.

    :param buffer: ImageBuf we want to add the text too
    :param text: The text we want to display on the image
    :param font_size: The size of the font
    :param font_path: The filepath to the font we want to use
    :param text_color: The color of the text we want to apply
    :param x_pos_override: Overrides the position of the text in the x
    :param y_pos_override: Overrides the position of the text in the y
    :return: ImageBuf
    """
    if not font_path:
        font_path = ResourceLoader.regular_font()

    if not font_size:
        if buffer.roi.width == buffer.roi.height:
            average = (buffer.roi.width + buffer.roi.height) / 2

        elif buffer.roi.width > buffer.roi.height:
            average = buffer.roi.height / 2

        else:
            average = buffer.roi.width / 2

        font_size = int(average * 0.8)

    if not os.path.exists(font_path):
        raise IOError("Font Path Not Found: " + font_path)

    size = ImageBufAlgo.text_size(text, fontsize=font_size, fontname=font_path)
    if size.defined:
        if not x_pos_override:
            x_pos_override = buffer.roi.xbegin + buffer.roi.width / 2 - (size.xbegin + size.width / 2)

        if not y_pos_override:
            y_pos_override = buffer.roi.ybegin + buffer.roi.height / 2 - (size.ybegin + size.height / 2)

        if not ImageBufAlgo.render_text(
                buffer, int(x_pos_override), int(y_pos_override), text, fontname=font_path, fontsize=font_size,
                textcolor=text_color):

            raise ValueError("error: " + buffer.geterror())

    return buffer


def write_image(image, filename, bit_depth, channel_mapping=None):
    """ Writes the given image buffer to the file name provided

    :param image: The ImageBuf we want to write to disk
    :param filename: the full file path with extension we want to write the file
    :param bit_depth: The bit depth we want to write the image out as
    :param channel_mapping: the order of the channels we want to write out, "RGB", "BGR", "RBG" etc we work in rgb by
        default and swap if specified. Ie pattern generators force the swap, the raster stitching keeps what its given
    :return: The filepath to the image we just wrote out
    """
    # The images have been created within a floating point buffer, but some of the patterns have been designed to
    # calculate values using a lower bit depth for a given imaging chain. However if we are writing out exr we
    # always want to keep the float point values
    if filename.endswith(".exr"):
        bit_depth = "float"

    if channel_mapping:
        mapping_order = [char for char in channel_mapping]
        image = ImageBufAlgo.channels(
            image, tuple(mapping_order)
        )

    if not image.has_error:
        # We ensure we are writing out none compressed images
        image.specmod().attribute(
            constants.OCIO_COMPRESSION_ATTRIBUTE, constants.OCIO_COMPRESSION_NONE
        )

        # We explicitly set the bits per sample for 10 and 12 bit images
        oiio_bit_depth = get_oiio_bit_depth(bit_depth)
        if bit_depth == 10 or bit_depth == 12:
            image.specmod().attribute(constants.OIIO_BITS_PER_SAMPLE, bit_depth)

        image.write(filename, oiio_bit_depth)
        return filename

    if image.has_error:
        raise IOError("Error writing", filename, ":", image.geterror())


def open_image(file_path):
    """ Opens the given file in the systems default image viewer

    :param file_path: The filepath of the image we want to open
    """
    image_viewer_cmds = {
        'linux': 'xdg-open',
        'win32': 'explorer',
        'darwin': 'open'
    }

    platform_cmd = image_viewer_cmds[sys.platform]
    subprocess.Popen([platform_cmd, file_path])


def get_oiio_bit_depth(value):
    """ Gets the correct oiio constant for the given bit depth described as an int

    :param value: the int value of the bit depth we want
    :return: the correct oiio.TypeDesc
    """
    bit_depth_map = {
        8: oiio.UINT8,
        10: oiio.UINT16,
        12: oiio.UINT16,
        16: oiio.UINT16,
        32: oiio.UINT32,
        64: oiio.UINT64,
        "half": oiio.HALF,
        "float": oiio.FLOAT
    }
    if value not in bit_depth_map:
        KeyError("Unsupported Bit Depth - Must Be" + ",".join([str(k) for k in bit_depth_map.keys()]))

    return bit_depth_map[value]


def apply_color_conversion(image, input_transform, output_transform, ocio_config_path):
    """ Applies a color space conversion to the image from the input color space to the output color space using the
        ocio color config provided. If the input_transform is None, then we get the scene_linear transform.
        This is most commonly AcesCG, and is the scene_linear role in the ocio studio, reference and cg configs by
        default

    :param image: the image buf we want to apply the color conversion too
    :param input_transform: the name of the input color transform we want to convert from
    :param output_transform: the name of the input color transform we want to convert to
    :param ocio_config_path: the filepath to the ocio color config we want to use
    :return: returns the image with the new color correction
    """

    if not os.path.exists(ocio_config_path):
        raise IOError("File Path Does Not Exist: " + ocio_config_path)

    ocio_config = ocio.Config.CreateFromFile(ocio_config_path)

    if input_transform is None:
        input_transform = get_role_from_config(ocio_config_path, ocio_config, "scene_linear")

    ics = get_transform_or_colorspace(ocio_config, input_transform)
    if ics is None:
        raise ValueError("Input Transform Not Found In Config: " + input_transform)

    ocs = get_transform_or_colorspace(ocio_config, output_transform)
    if ocs is None:
        raise ValueError("Output Transform Not Found In Config: " + output_transform)

    image = imaging_utils.apply_color_conversion(image, input_transform, output_transform, ocio_config_path)
    if image.has_error:
        raise ValueError("Error Converting Color: " + image.geterror())

    # This only works in exr which is a real pain
    image.specmod().attribute(constants.OCIO_INPUT_TRANSFORM, input_transform)
    image.specmod().attribute(constants.OCIO_OUTPUT_TRANSFORM, output_transform)

    return image


def get_role_from_config(ocio_color_path, ocio_config, required_role):
    for role, name in ocio_config.getRoles():
        if role == required_role:
            return name

    raise ValueError("No '{0}' Role found in ocio config: {1}".format(required_role, ocio_color_path))


def get_transform_or_colorspace(ocio_config, transform):
    """ Gets either the ColorSpace or NamedTransform from the ocio config for the given transform name

    :param ocio_config: the ocio config we want to get the transform from
    :param transform: the name of the transform we want
    :return: ColorSpace or NamedTransform for the given transform
    """
    ocs = ocio_config.getColorSpace(transform)
    if ocs is None:
        ocs = ocio_config.getNamedTransform(transform)
    return ocs


def get_image_buffer(file_path):
    """ Gets an oiio image buffer for the givern image file path

    :param file_path: the file path to the image we want to get the buffer for
    :return: ImgBuffer
    """
    if not os.path.exists(file_path):
        raise IOError("File not found: " + file_path)
    return oiio.ImageBuf(file_path)


def nits_to_pq(nits: int) -> float:
    """
    Convert nits (luminance in cd/m^2) to Perceptual Quantizer (PQ) non-linear signal value.

    Parameters:
    nits (float): Luminance in nits (cd/m^2).

    Returns:
    float: Corresponding PQ non-linear signal value.
    """
    FD = nits
    Y = FD / constants.PQ_MAX_NITS
    E = ((constants.PQ_C1 + constants.PQ_C2 * Y ** constants.PQ_M1) /
         (1 + constants.PQ_C3 * Y ** constants.PQ_M1)) ** constants.PQ_M2
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
    FD = constants.PQ_MAX_NITS * ((max((E ** (1 / constants.PQ_M2) - constants.PQ_C1), 0)) /
                           (constants.PQ_C2 - constants.PQ_C3 * E ** (1 / constants.PQ_M2))) ** (1 / constants.PQ_M1)
    return FD


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
