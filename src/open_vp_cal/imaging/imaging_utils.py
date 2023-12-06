"""
The module contains functions for manipulating images using the OpemImageIO library
"""
from typing import Union, List, Tuple

import os
import os.path
import tempfile

from PySide6 import QtGui
from PySide6.QtGui import QImage, QPixmap
import PyOpenColorIO as ocio

try:
    import OpenImageIO as Oiio
except ImportError:
    print("OpenImageIO not found, please make sure it is available on the python path")


    class MissingModuleError(Exception):
        """
        An exception raised when a module is missing
        """


    class MockModule:
        """
        A mock module that raises an exception when any attribute is accessed
        """

        def __getattr__(self, name):
            raise MissingModuleError(f"'OpenImageIO' module is missing. Can't access '{name}'.")


    Oiio = MockModule()

import colour
from colour.models import RGB_COLOURSPACE_ACES2065_1
import numpy as np

from open_vp_cal.core.constants import OIIO_COMPRESSION_ATTRIBUTE, OIIO_COMPRESSION_NONE, OIIO_BITS_PER_SAMPLE
from open_vp_cal.core.resource_loader import ResourceLoader
from open_vp_cal.core import utils


def image_buf_to_np_array(image_buf: Oiio.ImageBuf) -> np.array:
    """ Convert an OIIO ImageBuf to a NumPy array

    Args:
        image_buf: The OIIO ImageBuf to convert

    Returns: The NumPy array representing the image

    """
    # Load the image using oiio.ImageBuf
    # Get the image metadata
    spec = image_buf.spec()

    # Get the dimensions and number of channels of the image
    width = spec.width
    height = spec.height
    channels = spec.nchannels

    # Create a NumPy array of the appropriate shape and data type
    image_np = np.zeros((height, width, channels), dtype=np.float32)

    # Copy pixel data from ImgBuf to NumPy array
    pixels = image_buf.get_pixels(Oiio.FLOAT)  # Assuming the image is in half precision
    image_np[:] = np.array(pixels).reshape((height, width, channels))
    return image_np


def img_buf_from_numpy_array(np_array: np.array) -> Oiio.ImageBuf:
    """ Create an Oiio.ImgBuf from a numpy array

    Args:
        np_array: The numpy array to create the Oiio.ImgBuf from

    Returns: The Oiio.ImgBuf

    """
    image_buf = Oiio.ImageBuf(Oiio.ImageSpec(np_array.shape[1], np_array.shape[0], np_array.shape[2], Oiio.FLOAT))

    # Set the pixels of the ImageBuf using the numpy array
    image_buf.set_pixels(Oiio.ROI(0, np_array.shape[1], 0, np_array.shape[0]), np_array)
    return image_buf


def load_image(file_path) -> Oiio.ImageBuf:
    """ Loads an image from the given file path

    Args:
        file_path: The file path to load the image from

    Returns: The image buffer

    """
    if not os.path.exists(file_path):
        raise IOError("File does not exist: " + file_path)

    image_buf = Oiio.ImageBuf(file_path)
    if image_buf.has_error:
        raise ValueError("Failed to load image buffer: " + image_buf.geterror())
    return image_buf


def write_image(image, filename, bit_depth, channel_mapping=None):
    """ Writes the given image buffer to the file name provided

    :param image: The ImageBuf we want to write to disk
    :param filename: the full file path with extension we want to write the file
    :param bit_depth: The bit depth we want to write the image out as
    :param channel_mapping: the order of the channels we want to write out, "RGB", "BGR", "RBG" etc we work in rgb by
        default and swap if specified.
        i.e. pattern generators force the swap, the raster stitching keeps what its given

    :return: The filepath to the image we just wrote out
    """

    if channel_mapping:
        mapping_order = list(channel_mapping)
        image = Oiio.ImageBufAlgo.channels(
            image, tuple(mapping_order)
        )

    if not image.has_error:
        # We ensure we are writing out none compressed images
        image.specmod().attribute(
            OIIO_COMPRESSION_ATTRIBUTE, OIIO_COMPRESSION_NONE
        )

        # We explicitly set the bits per sample for 10 and 12 bit images
        oiio_bit_depth = get_oiio_bit_depth(bit_depth)
        if bit_depth in (10, 12):
            image.specmod().attribute(OIIO_BITS_PER_SAMPLE, bit_depth)

        image.write(filename, oiio_bit_depth)
        return filename

    if image.has_error:
        raise IOError("Error writing", filename, ":", image.geterror())

    return ""


def get_oiio_bit_depth(value: Union[int, str]) -> Oiio.BASETYPE:
    """ Gets the correct oiio constant for the given bit depth described as an int

    Args:
        value: The bit depth we want the constant for

    Returns:

    """
    bit_depth_map = {
        8: Oiio.UINT8,
        10: Oiio.UINT16,
        12: Oiio.UINT16,
        16: Oiio.UINT16,
        32: Oiio.UINT32,
        64: Oiio.UINT64,
        "half": Oiio.HALF,
        "float": Oiio.FLOAT
    }
    if value not in bit_depth_map:
        raise KeyError("Unsupported Bit Depth - Must Be " + ",".join([str(k) for k in bit_depth_map]))

    return bit_depth_map[value]


def stitch_images_vertically(image_buffers: List[Oiio.ImageBuf]) -> Oiio.ImageBuf:
    """ Stacks the given images vertically on top of each other, first image in the list is at the top, last is at
        the bottom

    Args:
        image_buffers: The images to stack

    Returns: A new ImgBuf containing the stacked images

    """
    # Determine the width and height of the final image
    width = 0
    height = 0
    for img_buf in image_buffers:
        spec = img_buf.spec()
        width = max(width, spec.width)
        height += spec.height

    # Create the output ImageBuf
    out_buf = Oiio.ImageBuf(Oiio.ImageSpec(width, height, 3, Oiio.FLOAT))

    # Y coordinate for the current image in the output
    y_offset = 0

    for img_buf in image_buffers:
        # Copy the source image and paste it into the correct place in the output
        spec = img_buf.spec()
        temp_buf = Oiio.ImageBufAlgo.copy(img_buf)
        Oiio.ImageBufAlgo.paste(out_buf, 0, y_offset, 0, 0, temp_buf)

        # Update y coordinate for the next image
        y_offset += spec.height

    return out_buf


def stitch_images_horizontally(img_buffers):
    """
    Takes a list of ImageBuf and stitches them together horizontally.

    Args:
        img_buffers (List[oiio.ImageBuf]): List of ImageBuf objects

    Returns:
        oiio.ImageBuf: Stitched ImageBuf
    """
    # Initialize variables to store total width and maximum height
    total_width = 0
    max_height = 0

    # Calculate the total width and maximum height
    for img_buf in img_buffers:
        total_width += img_buf.spec().width
        max_height = max(max_height, img_buf.spec().height)

    # Create an output image buffer with the total width and maximum height
    output = Oiio.ImageBuf(
        Oiio.ImageSpec(total_width, max_height, img_buffers[0].nchannels, img_buffers[0].spec().format)
    )

    # Initialize x_offset to 0
    x_offset = 0

    # Iterate over each image buffer and append it to the output image buffer
    for img_buf in img_buffers:
        Oiio.ImageBufAlgo.paste(output, x_offset, 0, 0, 0, img_buf)
        x_offset += img_buf.spec().width

    return output


def apply_color_conversion(
        image_buffer: Oiio.ImageBuf,
        from_transform: str,
        to_transform: str,
        color_config: Union[str, None] = None) -> Oiio.ImageBuf:
    """ Applies a colour conversion to the given image buffer from and to the given transforms.
    If no colour config is supplied, it uses the pre-installed studio config

    Args:
        image_buffer: The image buffer to convert
        from_transform: The transform to convert from
        to_transform: The transform to convert to
        color_config: The colour config to use for the conversion

    Returns: The converted image buffer

    """
    if not color_config:
        color_config = ResourceLoader.ocio_config_path()

    image = image_buf_to_np_array(image_buffer)
    apply_color_converstion_to_np_array(image, from_transform, to_transform, color_config)
    converted_buffer = img_buf_from_numpy_array(image)
    return converted_buffer


def apply_color_converstion_to_np_array(
        image: np.array,
        from_transform: str,
        to_transform: str,
        color_config: Union[str, None] = None) -> None:
    """ Applies a colour conversion to the given image array from and to the given transforms.
        The conversions are done in place

    Args:
        image: The image array to convert
        from_transform: The transform to convert from
        to_transform: The transform to convert to
        color_config: The colour config to use for the conversion
    """
    if color_config is None:
        color_config = ResourceLoader.ocio_config_path()

    if not os.path.exists(color_config):
        raise ValueError("Color config does not exist: " + color_config)

    config = ocio.Config().CreateFromFile(color_config)
    processor = config.getProcessor(from_transform,
                                    to_transform)
    cpu = processor.getDefaultCPUProcessor()

    # Ensure we only have float32 data to work with OCIO
    if image.dtype.name != "float32":
        raise ValueError("Image must be float32 not " + image.dtype.name)

    # Apply the color transform to the existing RGBA pixel data
    _, _, channels = image.shape
    if channels == 3:
        cpu.applyRGB(image)
    if channels == 4:
        cpu.applyRGBA(image)


def apply_display_conversion(
        image_buffer: Oiio.ImageBuf,
        display: str,
        view: str,
        color_config: Union[str, None] = None) -> Oiio.ImageBuf:
    """ Applies a given display and view to the image_buffer using the inbuilt ocio config or the one provided

    Args:
        image_buffer: The image buffer to convert
        display: The display we want to apply
        view: The view for the display we want to apply
        color_config: The colour config to use for the conversion

    Returns: The converted image buffer

    """
    if not color_config:
        color_config = ResourceLoader.ocio_config_path()

    image = image_buf_to_np_array(image_buffer)
    apply_display_conversion_to_np_array(image, display, view, color_config)
    converted_buffer = img_buf_from_numpy_array(image)

    return converted_buffer


def apply_display_conversion_to_np_array(
        image: np.array,
        display: str,
        view: str,
        color_config: Union[str, None] = None) -> None:
    """ Applies a given display and view to the image using the inbuilt ocio config or the one provided.
        The conversions are done in place

    Args:
        image: The image array to convert
        display: The display we want to apply
        view: The view for the display we want to apply
        color_config: The colour config to use for the conversion

    """
    if not color_config:
        color_config = ResourceLoader.ocio_config_path()

    config = ocio.Config().CreateFromFile(color_config)
    processor = config.getProcessor(ocio.ROLE_SCENE_LINEAR, display, view, ocio.TRANSFORM_DIR_FORWARD)
    cpu = processor.getDefaultCPUProcessor()
    cpu.applyRGB(image)


def nest_analysis_swatches(
        source_img: Oiio.ImageBuf, target_img: Oiio.ImageBuf, patch_size: tuple[int, int] = (200, 200),
        central_roi_size: tuple[int, int] = (100, 100)) -> Oiio.ImageBuf:
    """
    The function takes a source image and a target image. For each patch of size patch_size in the source image,
    it extracts a central region of size central_roi_size and pastes it into the corresponding location in the target
    image.

    Args:
        source_img (str): The path of the source image.
        target_img (str): The path of the target image.
        patch_size (tuple[int, int]): The size of the image patch to be processed, default is (200, 200).
        central_roi_size (tuple[int, int]): The size of the central region to be extracted and pasted, default
        is (100, 100).

    Returns:
        target_img_path (str): The path of the processed target image.

    """
    # Calculate the central offsets for the region of interest
    central_roi_offset = ((patch_size[0] - central_roi_size[0]) // 2, (patch_size[1] - central_roi_size[1]) // 2)

    # Iterate over the patches in the source image
    for i in range(0, source_img.spec().width, patch_size[0]):
        for j in range(0, source_img.spec().height, patch_size[1]):
            # Define the region of interest in the source image
            src_roi = Oiio.ROI(i + central_roi_offset[0], i + central_roi_offset[0] + central_roi_size[0],
                               j + central_roi_offset[1], j + central_roi_offset[1] + central_roi_size[1])

            # Read the central region from the source image
            src_patch = source_img.get_pixels(roi=src_roi)

            # Write the central region into the target image
            target_img.set_pixels(src_roi, src_patch)

    return target_img


def generate_image_cie(scale: int, file_path: str) -> bool:
    """ Generates and image of the CIE 1931 chromaticity diagram in the correct 0-1 range and position
    within the image. Scaled to the given factor

    Args:
        scale: The scale to apply to the image
        file_path: The file path to write the image to

    Returns: True if the image was written successfully

    """
    spectral_locus_x, spectral_locus_y = utils.get_spectral_locus_positions(scale)
    polygon = list(zip(spectral_locus_x, spectral_locus_y))
    buf = Oiio.ImageBuf(Oiio.ImageSpec(scale, scale, 3, Oiio.FLOAT))
    Oiio.ImageBufAlgo.fill(
        buf,
        [1, 1, 1]
    )

    for y_pos in range(scale):
        for x_pos in range(scale):
            adjusted_y = scale - y_pos - 1
            if utils.is_point_inside_polygon((x_pos, adjusted_y), polygon):
                x_normalized = x_pos / scale
                y_normalized = adjusted_y / scale
                xyY = colour.xy_to_xyY((x_normalized, y_normalized), 1)
                XYZ = colour.xyY_to_XYZ(xyY)

                illuminant = colour.CCS_ILLUMINANTS[
                    "CIE 1931 2 Degree Standard Observer"
                ]["D65"]

                rgb = colour.XYZ_to_RGB(
                    XYZ,
                    illuminant,
                    RGB_COLOURSPACE_ACES2065_1.whitepoint,
                    RGB_COLOURSPACE_ACES2065_1.matrix_XYZ_to_RGB,
                    "Cat02",
                    None,
                )
                # rgb = [max(0, min(1, channel)) for channel in colour.XYZ_to_sRGB(XYZ)]
                buf.setpixel(x_pos, y_pos, (rgb[0], rgb[1], rgb[2]))

    res = write_image(buf, file_path, "float")
    if not res:
        raise ValueError("Failed to write image buffer to display")
    return True


def insert_resized_image(image_a: Oiio.ImageBuf, image_b: Oiio.ImageBuf, resize_percent) -> Oiio.ImageBuf:
    """
    Resize imageA by the given percentage and insert it into the center of imageB.

    Args:
        image_a (oiio.ImageBuf): The image to be resized and inserted.
        image_b (oiio.ImageBuf): The target image where imageA will be inserted.
        resize_percent (float): The percentage by which imageA should be resized.

    Returns:
        oiio.ImageBuf: The resulting image.
    """

    # Resize imageA
    width_reduction = int(image_a.spec().width * resize_percent / 100)
    height_reduction = int(image_a.spec().height * resize_percent / 100)
    new_width = int(image_a.spec().width - width_reduction)
    new_height = int(image_a.spec().height - height_reduction)
    resized_image_a = Oiio.ImageBuf()
    res = Oiio.ImageBufAlgo.resize(resized_image_a, image_a, "", 0, Oiio.ROI(0, new_width, 0, new_height))
    if not res:
        raise ValueError("Failed to resize image buffer")

    # Calculate the position in imageB to place the resized imageA
    x_offset = (image_b.spec().width - new_width) // 2
    y_offset = (image_b.spec().height - new_height) // 2

    res = Oiio.ImageBufAlgo.paste(image_b, x_offset, y_offset, 0, 0, resized_image_a)
    if not res:
        raise ValueError("Failed to paste image buffer")
    return image_b


def list_to_roi(roi: list) -> Oiio.ROI:
    """ Converts a list to an Oiio.ROI

    Args:
        roi: The list to convert

    Returns: The Oiio.ROI

    """
    return Oiio.ROI(roi[0], roi[1], roi[2], roi[3])


def extract_roi(input_image: Oiio.ImageBuf, roi_input: list) -> Oiio.ImageBuf:
    """ Extracts a region of interest from the image buffer of this frame.


    Parameters:
        input_image:
        roi_input: The region of interest to extract from the image buffer.

    Returns: Oiio.ImageBuf: The extracted region of interest.

    """
    roi = list_to_roi(roi_input)
    # Create an empty ImageBuf for the cropped image
    cropped_image = Oiio.ImageBuf()

    # Crop the image
    Oiio.ImageBufAlgo.cut(cropped_image, input_image, roi)
    if cropped_image.has_error:
        raise ValueError("Failed To Extract ROI: " + cropped_image.geterror())

    # Write the cropped image to disk
    return cropped_image


def get_scaled_cie_spectrum_bg_image(max_scale: int) -> Oiio.ImageBuf:
    """ Gets the scaled cie spectrum background image

    Args:
        max_scale: The max scale to apply to the image

    Returns: The scaled image

    """
    # Load the image using oiio.ImageBuf
    image_buf_orig = load_image(ResourceLoader.cie_spectrum_bg())

    # Resize the image for the scale of the graph widget
    image_buf = Oiio.ImageBuf()
    Oiio.ImageBufAlgo.resize(
        image_buf, image_buf_orig, "", 0, Oiio.ROI(0, max_scale, 0, max_scale)
    )
    return image_buf


def load_image_buffer_to_qimage(buffer: Oiio.ImageBuf, project_settings: "ProjectSettings") -> QImage:
    """ Load an image buffer into a QImage

    Args:
        buffer: The image buffer to load
        project_settings: The project settings we want to use to access the correct ocio config

    Returns: The QImage loaded from the buffer

    """
    buf = apply_color_conversion(
        buffer, project_settings.current_wall.input_plate_gamut, "sRGB - Display")
    with tempfile.NamedTemporaryFile(suffix='.jpg', delete=False) as temp:
        res = buf.write(temp.name, Oiio.UINT8)
        if not res:
            raise IOError(f"Failed to write image to temp file {temp.name}")

        # Create QImage with correct dimensions and format
        image = QtGui.QImage(temp.name)

    os.remove(temp.name)
    return image


def load_image_buffer_to_qpixmap(buffer: Oiio.ImageBuf, project_settings: "ProjectSettings") -> QPixmap:
    """ Load an Oiio.ImageBuf into a QPixmap so we can display it

    Args:
        buffer: The image buffer to load
        project_settings: The project settings we want to use to access the correct ocio config

    Returns: The QPixmap loaded from the buffer

    """
    image = load_image_buffer_to_qimage(buffer, project_settings)
    pixmap = QPixmap.fromImage(
        image
    )
    return pixmap


def new_image(width: int, height: int, fill_colour: List = None) -> Oiio.ImageBuf:
    """ Creates a new image buffer of the given width and height

    Args:
        width: The width of the image
        height: The height of the image
        fill_colour: The colour to fill the image with

    Returns: The new image buffer filled with the given colour or black if no colour is given
    """
    if fill_colour is None:
        fill_colour = [0, 0, 0]

    text_buffer = Oiio.ImageBuf(
        Oiio.ImageSpec(width, height, 3, Oiio.FLOAT)
    )
    Oiio.ImageBufAlgo.fill(text_buffer, fill_colour)
    return text_buffer


def create_and_stitch_analysis_strips(
        reference_buffers: List[Oiio.ImageBuf],
        sample_buffers: List[Oiio.ImageBuf]) -> Tuple[Oiio.ImageBuf, Oiio.ImageBuf]:
    """ Creates and stitches the analysis strips for the given reference and sample buffers, this function creates
        strips for each of the samples which respect the aspect ratio of 16:9, then stitches them together vertically.

    Args:
        reference_buffers: The reference buffers to create the strips for
        sample_buffers: The sample buffers to create the strips for

    Returns: The stitched sample and reference strips

    """
    x_count, _ = utils.find_nearest_factors_for_ratio(
        len(sample_buffers), ratio_width=16, ratio_height=9
    )
    sample_buffers_split = utils.split_list(sample_buffers, x_count)
    sample_buffers_strips = []
    for strip in sample_buffers_split:
        strip_stitched = stitch_images_horizontally(
            strip
        )
        sample_buffers_strips.append(strip_stitched)

    sample_buffers_stitched = []
    if sample_buffers_strips:
        sample_buffers_stitched = stitch_images_vertically(sample_buffers_strips)

    reference_buffers_strips = []
    if reference_buffers:
        reference_buffers_split = utils.split_list(reference_buffers, x_count)
        for strip in reference_buffers_split:
            strip_stitched = stitch_images_horizontally(
                strip
            )
            reference_buffers_strips.append(strip_stitched)

    reference_buffers_stitched = []
    if reference_buffers_strips:
        reference_buffers_stitched = stitch_images_vertically(
            reference_buffers_strips
        )
    return sample_buffers_stitched, reference_buffers_stitched


def add_text_to_image_buffer(text: str, img_buffer: Oiio.ImageBuf, text_color: List, text_size: int) -> None:
    """ Adds text to the given image buffer

    Args:
        text: The text to add to the image buffer
        img_buffer: The image buffer to add the text to
        text_color: The colour of the text
        text_size: The size of the text

    Returns:

    """
    Oiio.ImageBufAlgo.render_text(
        img_buffer, 0, text_size, text,
        fontname=ResourceLoader.bold_font(),
        fontsize=text_size,
        textcolor=text_color
    )


def convert_to_grayscale(input_image_buf, input_colour_space="sRGB") -> Oiio.ImageBuf:
    """ Convert an image to grayscale

    Args:
        input_image_buf: The input image buffer we want to convert to grey scale
        input_colour_space: The colour space of the input image buffer

    Returns: The converted image buffer

    """
    numpy_array = image_buf_to_np_array(input_image_buf)
    height, width, _ = numpy_array.shape
    numpy_array = numpy_array[:, :, :3]
    flattened_arr = numpy_array.reshape(-1, 3)

    input_colour_space_cs = colour.RGB_COLOURSPACES[input_colour_space]

    numpy_array_XYZ = colour.RGB_to_XYZ(
        flattened_arr,
        input_colour_space_cs.whitepoint,
        input_colour_space_cs.whitepoint,
        input_colour_space_cs.matrix_RGB_to_XYZ
    )
    numpy_array_xyY = colour.XYZ_to_xyY(numpy_array_XYZ)

    Y_values = numpy_array_xyY[:, 2]

    # Create a new array with Y values replacing the x and y values
    new_array = np.stack([Y_values, Y_values, Y_values], axis=-1)

    img_array_reformed = new_array.reshape(height, width, 3)
    return img_buf_from_numpy_array(img_array_reformed)


def sample_image(img_buf: Oiio.ImageBuf) -> List:
    """ Samples the given image and returns the average RGB values based on the clipped mean value

    Args:
        img_buf: The image buffer to sample

    Returns: The average RGB values of the image

    """
    img_array = image_buf_to_np_array(img_buf)
    result = [
        compute_clipped_mean(img_array, 0, sigma=3),
        compute_clipped_mean(img_array, 1, sigma=3),
        compute_clipped_mean(img_array, 2, sigma=3),
    ]

    return result


def get_average_value_above_average(img_buf: Oiio.ImageBuf) -> Tuple[List[float], Oiio.ImageBuf]:
    """ Eliminates any pixels which are below the average pixel value of the whole image, ie often black or very dark
        pixels, this leaves us the pixels from the whole image which are often not black, in this case the patch
        sections.

        We then return the average pixel values for the remaining pixels which gives us a more accurate indicator as
        to the true average

        Used primarily to detect the red and green frames when no ROI has been specificed as this helps isolate the main
        patch area without actually selecting it

    Args:
        img_buf: The image buffer to get the average RGB values from

    Returns: The average RGB values of the image, and the image buffer with the below average pixels highlighted which
        are removed/masked

    """
    img_array = image_buf_to_np_array(img_buf)

    # Compute the average RGB values of the original image
    original_average_rgb = np.mean(img_array, axis=(0, 1))

    # Create a mask for pixels below the average
    below_average_mask = np.mean(img_array, axis=2) < np.mean(original_average_rgb)

    # Create a copy of the original image for mask output
    img_to_write_out_with_mask = np.copy(img_array)
    img_to_write_out_with_mask[below_average_mask] = [1, 0, 0]  # Set below average pixels to red

    # Create another copy for average calculation
    img_avg_copy = np.copy(img_array)
    img_avg_copy[below_average_mask] = [0, 0, 0]  # Set below average pixels to black

    # Remove the black pixels for average calculation
    non_black_pixels = img_avg_copy[(img_avg_copy != [0, 0, 0]).all(axis=2)]

    # Sum the RGB values of the remaining pixels
    sum_rgb = np.sum(non_black_pixels, axis=0)

    # Count the number of non-black pixels
    count_non_black_pixels = len(non_black_pixels)

    # Compute the average RGB values of the remaining pixels
    above_average_rgb = sum_rgb / count_non_black_pixels

    return above_average_rgb.tolist(), img_to_write_out_with_mask


def _get_xyY_values(values: np.array, colour_space: str = "ACES2065-1") -> np.array:
    """ For the given values we return the xyY values based on the given colour space

    Args:
        values: The values to convert
        colour_space: The colour space to convert from

    Returns: The xyY values

    """
    input_colour_space_cs = colour.RGB_COLOURSPACES[colour_space]
    numpy_array_XYZ = colour.RGB_to_XYZ(
        values,
        input_colour_space_cs.whitepoint,
        input_colour_space_cs.whitepoint,
        input_colour_space_cs.matrix_RGB_to_XYZ
    )

    return colour.XYZ_to_xyY(numpy_array_XYZ)


def detect_red(values: np.array, colour_space: str = "ACES2065-1") -> bool:
    """ For the given values and colour space we convert to xyY and try to determine if the image is red or not

    Args:
        values: The values to convert
        colour_space: The colour space to convert from

    Returns: True if the image is red

    """
    numpy_array_xyY = _get_xyY_values(values, colour_space=colour_space)
    red_threshold = 0.4
    if numpy_array_xyY[0] > red_threshold:
        return True
    return False


def detect_green(values: np.array, colour_space: str = "ACES2065-1") -> bool:
    """ For the given values and colour space we convert to xyY and try to determine if the image is green or not

    Args:
        values: The values to convert
        colour_space: The colour space to convert from

    Returns: True if the image is green

    """
    numpy_array_xyY = _get_xyY_values(values, colour_space=colour_space)
    green_threshold = 0.5

    if numpy_array_xyY[1] > green_threshold:
        return True
    return False


def compute_clipped_mean(image: np.array, channel_idx: int, sigma: int = 3):
    """ Computes the mean of the given channel after clipping the outliers using standard deviation

    Args:
        image: The image we want to get clipped mean from
        channel_idx: the channel we want to get the mean from
        sigma: the multiplier for the standard deviation for the clipping

    Returns: The average value of the channel after clipping the outliers

    """
    channel_data = image[:, :, channel_idx]
    mean_val = np.mean(channel_data)
    std_dev = np.std(channel_data)

    # Define the lower and upper bounds for clipping
    lower_bound = mean_val - sigma * std_dev
    upper_bound = mean_val + sigma * std_dev

    # Clip the outliers
    clipped_data = channel_data[(channel_data >= lower_bound) & (channel_data <= upper_bound)]

    # Recompute the mean
    refined_mean = np.mean(clipped_data)

    return float(refined_mean)


def get_decoupled_white_samples_from_file(external_white_point_file: str) -> List:
    """ For the given file we load the image and get the average value from all the pixels which are above the
        initial average.

    Args:
        external_white_point_file: The file to load the image from

    Returns: The average values of rgb from the image

    """
    if not external_white_point_file:
        raise ValueError("No external white point file specified")

    if not os.path.exists(external_white_point_file):
        raise ValueError("External white point file does not exist")

    image_buffer = Oiio.ImageBuf(external_white_point_file)
    return sample_image(image_buffer)
