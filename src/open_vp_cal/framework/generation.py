"""
The module handles the synthetic generation of patches for the calibration process which are played back on the LED
wall and recorded in camera. It also generates the same data which is used for comparison during the analysis phase of
the processing
"""
import os.path
import math
from typing import List, Tuple

import numpy as np

# pylint: disable=E0401
import OpenImageIO as Oiio
# pylint: enable=E0401


import open_vp_cal
from open_vp_cal.imaging import imaging_utils
from open_vp_cal.imaging.macbeth import get_colour_checker_for_colour_space_and_illuminant
from open_vp_cal.led_wall_settings import LedWallSettings
from open_vp_cal.core import constants, utils, ocio_config
from open_vp_cal.core.resource_loader import ResourceLoader
from open_vp_cal.core.calibrate import saturate_RGB


class PatchGeneration:
    """
    The PatchGeneration class is responsible for generating colour squares using OpenImageIO (Oiio).
    """

    def __init__(self, led_wall: LedWallSettings, patch_size=(1000, 1000)):
        """
        Initializes the PatchGeneration with the LED wall settings

        Parameters:
            led_wall (LedWallSettings): The LED wall we want to generate patches for
        """
        self.led_wall = led_wall
        self.patch_size = patch_size
        self.base_name = None
        self.generation_ocio_config_path = None

        self.peak_lum = None
        self.percent_18_lum = None
        self.grey_18_percent = np.array([])
        self.max_black = 0

        self.red_primary = np.array([])
        self.green_primary = np.array([])
        self.blue_primary = np.array([])

        self.desaturated_red = np.array([])
        self.desaturated_green = np.array([])
        self.desaturated_blue = np.array([])
        self.flat_field = [0.5, 0.5, 0.5]

        self.calc_constants()

        self.patches_map = {
            constants.PATCHES.SLATE: (self.generate_slate_patch, (1, 1, 1)),
            constants.PATCHES.MAX_WHITE: (self.generate_solid_patch, (
                constants.PQ.PQ_MAX_NITS_100_1, constants.PQ.PQ_MAX_NITS_100_1, constants.PQ.PQ_MAX_NITS_100_1)),
            constants.PATCHES.RED_PRIMARY: (self.generate_solid_patch, self.red_primary.tolist()),
            constants.PATCHES.GREEN_PRIMARY: (self.generate_solid_patch, self.green_primary.tolist()),
            constants.PATCHES.BLUE_PRIMARY: (self.generate_solid_patch, self.blue_primary.tolist()),
            constants.PATCHES.RED_PRIMARY_DESATURATED: (
                self.generate_solid_patch, self.desaturated_red.tolist()),
            constants.PATCHES.GREEN_PRIMARY_DESATURATED: (
                self.generate_solid_patch, self.desaturated_green.tolist()),
            constants.PATCHES.BLUE_PRIMARY_DESATURATED: (
                self.generate_solid_patch, self.desaturated_blue.tolist()),
            constants.PATCHES.GREY_18_PERCENT: (self.generate_solid_patch, self.grey_18_percent.tolist()),
            constants.PATCHES.MACBETH: (self.generate_macbeth, 1.5),
            constants.PATCHES.DISTORT_AND_ROI: (self.distort_and_roi, [20, 100, 0, 0.1]),
            constants.PATCHES.FLAT_FIELD: (self.generate_solid_patch_full, self.flat_field),
            constants.PATCHES.EOTF_RAMPS: (
                self.generate_eotf_ramps,
                utils.get_grey_signals(
                    self.led_wall.target_max_lum_nits, self.led_wall.num_grey_patches)
            ),
            constants.PATCHES.SATURATION_RAMP: (self.generate_saturation_ramp, 10),
            constants.PATCHES.END_SLATE: (self.generate_reference_image, ResourceLoader.open_vp_cal_logo()),
        }

    def calc_constants(self) -> None:
        """ Calculates the constants needed for the patch generation based on the specifics of the LED wall
        """
        self.peak_lum = self.led_wall.target_max_lum_nits * 0.01
        self.percent_18_lum = self.peak_lum * 0.18
        self.grey_18_percent = np.array([self.percent_18_lum, self.percent_18_lum, self.percent_18_lum])
        self.max_black = 0

        self.red_primary = np.array([self.percent_18_lum, 0, 0])
        self.green_primary = np.array([0, self.percent_18_lum, 0])
        self.blue_primary = np.array([0, 0, self.percent_18_lum])

        self.desaturated_red = saturate_RGB([self.red_primary], self.led_wall.primaries_saturation)[0]
        self.desaturated_green = saturate_RGB([self.green_primary], self.led_wall.primaries_saturation)[0]
        self.desaturated_blue = saturate_RGB([self.blue_primary], self.led_wall.primaries_saturation)[0]

        self.flat_field = [self.peak_lum * 0.5, self.peak_lum * 0.5, self.peak_lum * 0.5]

    def generate_eotf_ramps(self, patch_values: list[float]) -> list[Oiio.ImageBuf]:
        """ Generates a list of grey ramp patches, which ramp up over a number of steps from 0 nits to peak luminance
        of the LED wall

        Args:
            patch_values: the values to use for the grey ramp patches

        Returns: A list of grey ramp patches

        """
        patch_width, patch_height = self.patch_size
        patches = []
        for patch_value in patch_values:
            patch = Oiio.ImageBuf(Oiio.ImageSpec(patch_width, patch_height, 3, Oiio.FLOAT))
            Oiio.ImageBufAlgo.fill(patch, [
                patch_value, patch_value, patch_value])
            patches.append(patch)
        return patches

    @staticmethod
    def _generate_saturation_ramp_patch(
            per_section_width: int,
            per_section_height: int, fill_value: List[float]) -> Oiio.ImageBuf:
        """ Generates a saturation ramp patch filled with the given colour

        Args:
            per_section_width: The width of the section
            per_section_height: The height of the section
            fill_value: The colour to fill the patch with

        Returns: A saturation ramp patch

        """
        patch_image = Oiio.ImageBuf(Oiio.ImageSpec(per_section_width, per_section_height, 3, Oiio.FLOAT))
        Oiio.ImageBufAlgo.fill(patch_image, fill_value)
        return patch_image

    def generate_saturation_ramp(self, patch_values: int) -> list[Oiio.ImageBuf]:
        """ Generates a list of saturation ramp patches. This shows full saturation of the primaries at peak luminance
        18% of peak luminance, 10 steps from 18% peak luminance down to ramp up over a number of steps from 0 to 100%
        saturation of the primaries

        Args:
            patch_values: The number of saturation steps we want to take in the ramp

        Returns: A list of saturation ramp patches

        """
        patch_width, patch_height = self.patch_size

        # We have two additional patches for the peak luminance and 18% luminance
        number_of_patches = patch_values + 2
        per_section_width = int(patch_width/number_of_patches)

        # We have two strips of the full ramp, and we want to leave a full strip between clearance, each strip has 3
        # sections r, g, b so we have 9 sections in height, 3 in the middle, which will be blank
        per_section_height = int(patch_height / 9)

        # Peak Lum & 18-Percent Saturation
        peak_luminance_patch, saturated_18_patch = self._get_initial_saturation_strips_for_ramp(
            per_section_height,
            per_section_width
        )
        patches = [peak_luminance_patch, saturated_18_patch]

        # primaries are already 18% luminance
        for patch_value in reversed(range(patch_values)):
            saturation_value = patch_value * 0.1
            saturated_patch = self._generate_saturation_ramp_strip(per_section_height, per_section_width,
                                                                   saturation_value)
            patches.append(saturated_patch)

        patch = self._embed_saturation_ramps_and_flop(patch_height, patch_width, patches)
        return [patch]

    def _generate_saturation_ramp_strip(self,
                                        per_section_height: int, per_section_width: int,
                                        saturation_value: float) -> Oiio.ImageBuf:
        """ Generates a saturation ramp strip of the given height and width and saturation value

        Args:
            per_section_height: The height of the strip
            per_section_width: The width of the strip
            saturation_value: The saturation value to use

        Returns: The saturation ramp strip

        """
        red_value = saturate_RGB([self.red_primary], saturation_value)[0]
        green_value = saturate_RGB([self.green_primary], saturation_value)[0]
        blue_value = saturate_RGB([self.blue_primary], saturation_value)[0]
        red_saturated = self._generate_saturation_ramp_patch(
            per_section_width, per_section_height, red_value.tolist()
        )
        green_saturated = self._generate_saturation_ramp_patch(
            per_section_width, per_section_height, green_value.tolist()
        )
        blue_saturated = self._generate_saturation_ramp_patch(
            per_section_width, per_section_height, blue_value.tolist()
        )
        saturated_patch = imaging_utils.stitch_images_vertically([red_saturated, green_saturated, blue_saturated])
        return saturated_patch

    @staticmethod
    def _embed_saturation_ramps_and_flop(
            patch_height: int,
            patch_width: int, patches: List[Oiio.ImageBuf]) -> Oiio.ImageBuf:
        """ Embeds the saturation ramps into a single patch and flops it, also adds an empty space between the two
            ramps.

            Finally rescales the embedded ramps to the correct patch size

        Args:
            patch_height: The height of the patch
            patch_width: The width of the patch
            patches: The patches to embed

        Returns: The embedded and flopped saturation ramp embedded into a single image

        """
        patch = imaging_utils.stitch_images_horizontally(patches)
        patch_flopped = Oiio.ImageBufAlgo.flop(patch)
        empty_ramp = Oiio.ImageBuf(Oiio.ImageSpec(patch.spec().width, patch.spec().height, 3, Oiio.FLOAT))
        Oiio.ImageBufAlgo.fill(empty_ramp, [0, 0, 0])
        stacked_ramps = imaging_utils.stitch_images_vertically([patch, empty_ramp, patch_flopped])
        patch = Oiio.ImageBuf(Oiio.ImageSpec(patch_width, patch_height, 3, Oiio.FLOAT))
        Oiio.ImageBufAlgo.resample(patch, stacked_ramps)
        return patch

    def _get_initial_saturation_strips_for_ramp(
            self,
            per_section_height: int,
            per_section_width: int) -> Tuple[Oiio.ImageBuf, Oiio.ImageBuf]:
        """ Generates the initial saturation strips for the saturation ramp

        Args:
            per_section_height: The height of each section in the saturation ramp
            per_section_width: The width of each section in the saturation ramp

        Returns: A tuple containing the peak luminance patch and the 18% saturation patch

        """

        red_patch = self._generate_saturation_ramp_patch(
            per_section_width, per_section_height, [self.peak_lum, 0, 0]
        )
        green_patch = self._generate_saturation_ramp_patch(
            per_section_width, per_section_height, [0, self.peak_lum, 0]
        )
        blue_patch = self._generate_saturation_ramp_patch(
            per_section_width, per_section_height, [0, 0, self.peak_lum]
        )
        peak_luminance_patch = imaging_utils.stitch_images_vertically([red_patch, green_patch, blue_patch])

        red_18_saturated = self._generate_saturation_ramp_patch(
            per_section_width, per_section_height, [self.percent_18_lum, 0, 0]
        )
        green_18_saturated = self._generate_saturation_ramp_patch(
            per_section_width, per_section_height, [0, self.percent_18_lum, 0]
        )
        blue_18_saturated = self._generate_saturation_ramp_patch(
            per_section_width, per_section_height, [0, 0, self.percent_18_lum]
        )
        saturated_18_patch = imaging_utils.stitch_images_vertically(
            [red_18_saturated, green_18_saturated, blue_18_saturated])
        return peak_luminance_patch, saturated_18_patch

    def generate_reference_image(self, file_path: str) -> list[Oiio.ImageBuf]:
        """ Generates a patch which centres the given reference image in the middle of the patch

        Args:
            file_path: The path to the reference image

        Returns: A list containing the reference image patch

        """
        patch_width, patch_height = self.patch_size
        ref = Oiio.ImageBuf(file_path)
        target_gamut_only_cs_name, _ = ocio_config.OcioConfigWriter.target_gamut_only_cs_metadata(self.led_wall)
        ref = imaging_utils.apply_color_conversion(
            ref, "sRGB - Texture",  target_gamut_only_cs_name, self.generation_ocio_config_path
        )

        patch = Oiio.ImageBuf(Oiio.ImageSpec(patch_width, patch_height, 3, Oiio.FLOAT))
        Oiio.ImageBufAlgo.resize(patch, ref)
        return [patch]

    def generate_macbeth(self, ratio: float) -> list[Oiio.ImageBuf]:
        """ Generates a Macbeth chart at the given aspect ratio, converts it to the target gamut and scales it so that
            the values are correct based on the peak luminance of the LED wall

        Args:
            ratio: the aspect ratio we want to generate the Macbeth chart at

        Returns: A list containing the Macbeth chart patch

        """
        # Macbeth charts are built best at a 1.5 aspect ratio.
        patch_width, _ = self.patch_size
        patch_height = int(patch_width / ratio)

        colour_space = utils.get_target_colourspace_for_led_wall(self.led_wall)
        output_img_buf = get_colour_checker_for_colour_space_and_illuminant(
            colour_space, chart_width=patch_width, chart_height=patch_height
        )

        # Our image is in 0-1 with 1 being max white. We need to scale it to our target peak luminance.
        np_array = imaging_utils.image_buf_to_np_array(output_img_buf)
        np_array_scaled = np_array * self.peak_lum
        scaled_img = imaging_utils.img_buf_from_numpy_array(np_array_scaled)

        outer_image_buf = Oiio.ImageBuf(Oiio.ImageSpec(
            patch_width, patch_height, 3,
            Oiio.FLOAT)
        )

        outer_image_buf = imaging_utils.insert_resized_image(scaled_img, outer_image_buf, 20)

        return [outer_image_buf]

    def get_patch_start_positions(self) -> tuple[int, int]:
        """ Gets the start positions for the patch based on the resolution of the content needed for the LED wall

        Returns: A tuple containing the start positions for the patch of the form (start_x, start_y)

        """
        patch_width, patch_height = self.patch_size
        start_x = (self.led_wall.project_settings.resolution_width - patch_width) // 2
        start_y = (self.led_wall.project_settings.resolution_height - patch_height) // 2
        return start_x, start_y

    def distort_and_roi(self, patch_values: list[int]) -> list[Oiio.ImageBuf]:
        """ Generates a list of patches which are used to auto-detect the ROI from the captured image sequence; it also
            surrounds this with a checkerboard pattern.

            This allows for lens distortion correction at a later date

        Args:
            patch_values:

        Returns:

        """
        patch_width, patch_height = self.patch_size
        start_x, start_y = self.get_patch_start_positions()

        roi_size, checker_size, checker_odd, checker_even = patch_values

        full_image = Oiio.ImageBuf(Oiio.ImageSpec(
            self.led_wall.project_settings.resolution_width, self.led_wall.project_settings.resolution_height, 3,
            Oiio.FLOAT)
        )

        Oiio.ImageBufAlgo.checker(
            full_image, checker_size, checker_size, 1,
            [checker_odd, checker_odd, checker_odd], [checker_even, checker_even, checker_even],
            xoffset=0, yoffset=0, zoffset=0
        )

        red_roi = Oiio.ROI(start_x, start_x + roi_size, start_y, start_y + roi_size)
        green_roi = Oiio.ROI(start_x + patch_width - roi_size, start_x + patch_width, start_y, start_y + roi_size)
        blue_roi = Oiio.ROI(start_x, start_x + roi_size, start_y + patch_height - roi_size, start_y + patch_height)
        white_roi = Oiio.ROI(start_x + patch_width - roi_size, start_x + patch_width,
                             start_y + patch_height - roi_size, start_y + patch_height)

        Oiio.ImageBufAlgo.fill(full_image, (self.peak_lum, 0.0, 0.0), roi=red_roi)
        Oiio.ImageBufAlgo.fill(full_image, (0.0, self.peak_lum, 0.0), roi=green_roi)
        Oiio.ImageBufAlgo.fill(full_image, (0.0, 0.0, self.peak_lum), roi=blue_roi)
        Oiio.ImageBufAlgo.fill(full_image, (self.peak_lum, self.peak_lum, self.peak_lum), roi=white_roi)
        return [full_image]

    @staticmethod
    def reduce_roi(roi: Oiio.ROI, reduction_percentage: float) -> Oiio.ROI:
        """ For a given ROI, we reduce it by the given percentage

        Args:
            roi: The ROI to reduce
            reduction_percentage: The percentage to reduce the ROI by

        Returns: The reduced ROI

        """
        # Make a copy of the input roi to avoid modifying the original
        reduced_roi = Oiio.ROI(roi.xbegin, roi.xend, roi.ybegin, roi.yend, roi.zbegin, roi.zend, roi.chbegin, roi.chend)

        # Calculate the amount to reduce on each side
        x_reduction = int((roi.width * reduction_percentage) / 100)
        y_reduction = int((roi.height * reduction_percentage) / 100)

        # Reduce the ROI
        reduced_roi.xbegin += x_reduction // 2
        reduced_roi.xend -= x_reduction // 2
        reduced_roi.ybegin += y_reduction // 2
        reduced_roi.yend -= y_reduction // 2

        return reduced_roi

    @staticmethod
    def draw_circle(img_buf, horizontal_centre, vertical_centre, radius, thickness, colour) -> None:
        """ For a given image, we draw a circle at the given position, radius, and colour.
            We also specify the thickness of the line to draw.

        Args:
            img_buf: The image to draw the circle on
            horizontal_centre: The horizontal centre of the circle
            vertical_centre: The vertical centre of the circle
            radius: The radius of the circle
            thickness: The thickness of the line to draw
            colour: The colour of the circle
        """
        # Get the image specs
        spec = img_buf.spec()

        y_range = range(
            max(0, vertical_centre - radius - thickness // 2),
            min(spec.height, vertical_centre + radius + thickness // 2 + 1)
        )

        x_range = range(
            max(0, horizontal_centre - radius - thickness // 2),
            min(spec.width, horizontal_centre + radius + thickness // 2 + 1)
        )

        # Create the circle
        for y_point in y_range:
            for x_point in x_range:
                # Calculate the distance from the centre of the circle
                distance = math.sqrt((x_point - horizontal_centre) ** 2 + (y_point - vertical_centre) ** 2)
                # If the distance is within the line thickness, set the pixel colour
                if radius - thickness // 2 <= distance <= radius + thickness // 2:
                    img_buf.setpixel(x_point, y_point, colour)

    @staticmethod
    def draw_crosshair(img_buf, x_pos, y_pos, length, thickness, colour):
        """ Draws a crosshair at the given position, length, and colour.
            We also specify the thickness of the line

        Args:
            img_buf: The image to draw the crosshair on
            x_pos: The horizontal position of the crosshair centre
            y_pos: The vertical position of the crosshair centre
            length: The length of the crosshair
            thickness: The thickness of the crosshair
            colour: The colour of the crosshair

        Returns:

        """
        # Get the image specs
        spec = img_buf.spec()

        # Create the crosshair
        for j in range(max(0, y_pos - thickness // 2), min(spec.height, y_pos + thickness // 2 + 1)):
            for i in range(max(0, x_pos - length), min(spec.width, x_pos + length)):
                # Draw horizontal line
                img_buf.setpixel(i, j, colour)

        for j in range(max(0, x_pos - thickness // 2), min(spec.width, x_pos + thickness // 2 + 1)):
            for i in range(max(0, y_pos - length), min(spec.height, y_pos + length)):
                # Draw vertical line
                img_buf.setpixel(j, i, colour)

    @staticmethod
    def split_roi(original_roi: Oiio.ROI, sections: int) -> List[Oiio.ROI]:
        """ Splits the given ROI into the given number smaller ROI

        Args:
            original_roi: The ROI to split
            sections: The number of sections to split the ROI into

        Returns: A list of ROIs

        """
        # We want one more division because we want to include a zero section
        width = original_roi.xend - original_roi.xbegin
        section_width = width // sections
        rois = []

        for i in range(sections):
            start = i * section_width
            end = start + section_width if i != sections - 1 else width  # Ensure last section includes any extra pixels
            roi = Oiio.ROI(start + original_roi.xbegin, end + original_roi.xbegin, original_roi.ybegin,
                           original_roi.yend)
            rois.append(roi)

        return rois

    @staticmethod
    def create_image_buffers_from_rois(rois: List[Oiio.ROI]) -> List[Oiio.ImageBuf]:
        """ Creates a list of blank image buffers from the given list of ROIs

        Args:
            rois: The ROIs to create image buffers for

        Returns: A list of image buffers

        """
        image_buffers = []

        for roi in rois:
            width = roi.xend - roi.xbegin
            height = roi.yend - roi.ybegin
            spec = Oiio.ImageSpec(width, height, 3, Oiio.FLOAT)
            section_buf = Oiio.ImageBuf(spec)
            image_buffers.append(section_buf)

        return image_buffers

    @staticmethod
    def insert_image_buffers(
            target_buffer: Oiio.ImageBuf,
            source_buffers: List[Oiio.ImageBuf],
            x_pos: int, y_pos: int) -> Oiio.ImageBuf:
        """ Inserts the given image buffers into the target image buffer starting at the given position, and
        incrementing horizontally

        Args:
            target_buffer: The target image buffer we want to add the source buffers to
            source_buffers: The source image buffers we want to add to the target buffer
            x_pos: The horizontal position to insert the source buffers
            y_pos: The vertical position to insert the source buffers

        Returns:

        """
        width = sum(buf.spec().width for buf in source_buffers)
        height = max(buf.spec().height for buf in source_buffers)

        result_buf = Oiio.ImageBuf(Oiio.ImageSpec(width, height, 3, Oiio.FLOAT))

        current_x = 0
        for buf in source_buffers:
            Oiio.ImageBufAlgo.paste(result_buf, current_x, 0, 0, 0, buf)
            current_x += buf.spec().width

        # Paste the stitched image into the target image at the specified position
        Oiio.ImageBufAlgo.paste(target_buffer, x_pos - width // 2, y_pos - height // 2, 0, 0, result_buf)

        return target_buffer

    # pylint: disable=W0613(unused-argument)
    def generate_slate_patch(self, patch_values: None) -> list[Oiio.ImageBuf]:
        """ Generates a slate patch which takes no inputs but has the same signature as the other patch generators

        Args:
            patch_values: Unused

        Returns: A list of image buffers

        """
        patch_width, patch_height = self.patch_size
        start_x, start_y = self.get_patch_start_positions()

        src_patch = Oiio.ImageBuf(ResourceLoader.slate())
        patch = Oiio.ImageBufAlgo.resize(
            src_patch, roi=Oiio.ROI(
                0, self.led_wall.project_settings.resolution_width, 0,
                self.led_wall.project_settings.resolution_height
            )
        )

        # Step 1. Add Central Square With 18% Peal Lum and Inner Square Boarder
        self._add_slate_inner_squares(patch, patch_height, patch_width, start_x, start_y)

        # Step 2. Add Central Circle And Cross-Hairs For Focus & Alignment Assistance
        self._add_slate_cross_hairs_and_inner_circle(patch, patch_height, patch_width, start_x, start_y)

        # Step 3: Add Nit Bar From 0 to Peak Lum Over 10 steps
        patch = self._add_slate_nit_bar(patch, patch_height, patch_width, start_x, start_y)

        # Step 4: Peak lum, Max pq lum
        patch = self._add_slate_peak_and_max_lum_patches(patch)

        # Step 4a: Add 17% and 19% patches
        patch = self._add_17_and_19_percent_patches(patch)

        # Step 5: Legal and Extended Range
        patch = self._add_slate_legal_and_extended_patches(patch)

        # Step 6: 90% peak lum
        patch = self._add_slate_90_percent_peak_lum_patch(patch)

        # Step 7: Add Slate Version and Settings Info Text
        patch = self._add_slate_version_setting_info_text(patch)

        # Step 8: Inlay the logos as needed
        patch = self._add_slate_logos(patch)

        return [patch]

    def _add_17_and_19_percent_patches(self, patch: Oiio.ImageBuf) -> Oiio.ImageBuf:
        """ Add a small 17 % and 19% of peak luminance patches to the slate as a guide for the exposure using the false
            colour. There is some error in most cameras, so this helps guide us to being as close to 18% as possible.

        Args:
            patch: The patch we want to add too

        Returns: the patch with the 17% and 19% patches added

        """
        nit_bar_height = 100
        nit_bar_steps = 2
        nit_bar_width = nit_bar_height * nit_bar_steps
        nit_bar_roi = Oiio.ROI(0, nit_bar_width, 0, nit_bar_height)
        rois = self.split_roi(nit_bar_roi, nit_bar_steps)
        img_buffers = self.create_image_buffers_from_rois(rois)
        Oiio.ImageBufAlgo.fill(
            img_buffers[0],
            [self.peak_lum * 0.17, self.peak_lum * 0.17, self.peak_lum * 0.17]
        )
        Oiio.ImageBufAlgo.fill(
            img_buffers[1],

            [self.peak_lum * 0.19, self.peak_lum * 0.19, self.peak_lum * 0.19]
        )
        patch = self.insert_image_buffers(patch, img_buffers, x_pos=1920, y_pos=1800)
        self._add_slate_text(
            patch, "17 %",
            (1850, 1900), 30, bold=False
        )
        self._add_slate_text(
            patch, "19 %",
            (1950, 1900), 30, bold=False
        )
        return patch

    def _add_slate_logos(self, patch) -> Oiio.ImageBuf:
        """ Adds the logos to the slate patch

        Args:
            patch: The slate patch to add the logos to

        Returns: The slate patch with the logos added

        """
        scale_factor = 0.25
        orca_buf = Oiio.ImageBuf(ResourceLoader.orca_logo())
        netflix_buf = Oiio.ImageBuf(ResourceLoader.netflix_logo())
        custom_buf = Oiio.ImageBuf()
        if self.led_wall.project_settings.custom_logo_path:
            custom_logo_buf = Oiio.ImageBuf(self.led_wall.project_settings.custom_logo_path)

            Oiio.ImageBufAlgo.resize(custom_buf, custom_logo_buf,
                                     roi=Oiio.ROI(0, 500, 0, 250))
            custom_buf = imaging_utils.convert_to_grayscale(custom_buf)

        new_nf_width = int(netflix_buf.spec().width * scale_factor)
        new_nf_height = int(netflix_buf.spec().height * scale_factor)

        new_orca_width = int(orca_buf.spec().width * scale_factor)
        new_orca_height = int(orca_buf.spec().height * scale_factor)

        # Resize source image
        resized_orca_buf = Oiio.ImageBuf()
        resized_netflix_buf = Oiio.ImageBuf()

        Oiio.ImageBufAlgo.resize(resized_netflix_buf, netflix_buf, roi=Oiio.ROI(0, new_nf_width, 0, new_nf_height))
        Oiio.ImageBufAlgo.resize(resized_orca_buf, orca_buf, roi=Oiio.ROI(0, new_orca_width, 0, new_orca_height))

        cropped_netflix_buf = Oiio.ImageBuf()
        Oiio.ImageBufAlgo.crop(cropped_netflix_buf, resized_netflix_buf, roi=Oiio.ROI(
            50, resized_netflix_buf.spec().width - 50, 50, resized_netflix_buf.spec().height - 50)
                               )

        # Paste the resized netflix and orca into the target buffer at specified position
        Oiio.ImageBufAlgo.paste(patch, 90, 1900, 0, 0, cropped_netflix_buf)
        Oiio.ImageBufAlgo.paste(patch, 600, 1900, 0, 0, resized_orca_buf)

        if not self.led_wall.project_settings.custom_logo_path:
            Oiio.ImageBufAlgo.paste(patch, 1360, 150, 0, 0, cropped_netflix_buf)
            Oiio.ImageBufAlgo.paste(patch, 1960, 150, 0, 0, resized_orca_buf)
        else:
            Oiio.ImageBufAlgo.paste(patch, 1660, 150, 0, 0, custom_buf)

        return patch

    def _add_slate_text(
            self,
            buffer: Oiio.ImageBuf,
            text: str, position: Tuple[int, int],
            font_size: int, bold: bool = False) -> None:
        """ Adds text to the slate buffer at the specified position, size

        Args:
            buffer: The buffer to add the text to
            text: The text to add
            position: The position to add the text at
            font_size: The font size to use
            bold: Whether to use the bold font
        """
        Oiio.ImageBufAlgo.render_text(
            buffer, int(position[0]), int(position[1]), text,
            fontname=ResourceLoader.bold_font() if bold else ResourceLoader.regular_font(),
            fontsize=font_size,
            textcolor=[1, 1, 1]
        )

    def _add_slate_90_percent_peak_lum_patch(self, patch: Oiio.ImageBuf) -> Oiio.ImageBuf:
        """ Adds the 90% peak lum patch to the slate

        Args:
            patch: The slate patch to add the 90% peak lum patch to

        Returns: The slate patch with the 90% peak lum patch added

        """
        nit_bar_height = 100
        nit_bar_steps = 1
        nit_bar_width = 200
        nit_bar_roi = Oiio.ROI(0, nit_bar_width, 0, nit_bar_height)
        rois = self.split_roi(nit_bar_roi, nit_bar_steps)
        img_buffers = self.create_image_buffers_from_rois(rois)
        Oiio.ImageBufAlgo.fill(
            img_buffers[0],
            [self.peak_lum * 0.9, self.peak_lum * 0.9, self.peak_lum * 0.9]
        )
        patch = self.insert_image_buffers(patch, img_buffers, x_pos=2700, y_pos=1880)
        return patch

    def _add_slate_legal_and_extended_patches(self, patch) -> Oiio.ImageBuf:
        """ Adds the legal and extended patches to the slate

        Args:
            patch: The patch to add the patches to

        Returns: The patch with the legal and extended patches added

        """
        nit_bar_height = 100
        nit_bar_steps = 4
        nit_bar_width = nit_bar_height * nit_bar_steps
        nit_bar_roi = Oiio.ROI(0, nit_bar_width, 0, nit_bar_height)
        rois = self.split_roi(nit_bar_roi, nit_bar_steps)
        img_buffers = self.create_image_buffers_from_rois(rois)

        minimum_legal, maximum_legal, minimum_extended, maximum_extended = utils.get_legal_and_extended_values(
            self.led_wall.target_max_lum_nits
        )
        Oiio.ImageBufAlgo.fill(
            img_buffers[0],
            [minimum_extended, minimum_extended, minimum_extended]
        )
        Oiio.ImageBufAlgo.fill(
            img_buffers[1],

            [minimum_legal, minimum_legal, minimum_legal]
        )
        Oiio.ImageBufAlgo.fill(
            img_buffers[2],

            [maximum_legal, maximum_legal, maximum_legal]
        )
        Oiio.ImageBufAlgo.fill(
            img_buffers[3],

            [maximum_extended, maximum_extended, maximum_extended]
        )

        transfer_function_only_cs_name, _ = ocio_config.OcioConfigWriter.transfer_function_only_cs_metadata(
            self.led_wall
        )
        color_converted_img_buffers = []
        for img_buf in img_buffers:
            output_img_buf = imaging_utils.apply_color_conversion(
                img_buf, transfer_function_only_cs_name,
                constants.ColourSpace.CS_ACES,
                color_config=self.generation_ocio_config_path
            )
            color_converted_img_buffers.append(output_img_buf)

        patch = self.insert_image_buffers(patch, color_converted_img_buffers[:2], x_pos=2900, y_pos=850)
        patch = self.insert_image_buffers(patch, color_converted_img_buffers[2:], x_pos=3200, y_pos=850)
        return patch

    def _add_slate_peak_and_max_lum_patches(self, patch: Oiio.ImageBuf) -> Oiio.ImageBuf:
        """ Adds the peak and max lum patches to the slate

        Args:
            patch: The patch to add the patches to

        Returns: The patch with the peak and max lum patches added

        """
        nit_bar_height = 100
        nit_bar_steps = 2
        nit_bar_width = nit_bar_height * nit_bar_steps
        nit_bar_roi = Oiio.ROI(0, nit_bar_width, 0, nit_bar_height)
        rois = self.split_roi(nit_bar_roi, nit_bar_steps)
        img_buffers = self.create_image_buffers_from_rois(rois)
        Oiio.ImageBufAlgo.fill(
            img_buffers[0],
            [self.peak_lum, self.peak_lum, self.peak_lum]
        )
        Oiio.ImageBufAlgo.fill(
            img_buffers[1],

            [constants.PQ.PQ_MAX_NITS * 0.01, constants.PQ.PQ_MAX_NITS * 0.01, constants.PQ.PQ_MAX_NITS * 0.01]
        )
        patch = self.insert_image_buffers(patch, img_buffers, x_pos=2700, y_pos=470)
        return patch

    def _add_slate_nit_bar(
            self,
            patch: Oiio.ImageBuf,
            patch_height: int,
            patch_width: int,
            start_x: int,
            start_y: int):
        """ Adds the nit bar to the slate which runs from 0 to peak luminance over 10 steps (11 patches)

        Args:
            patch: The patch to add the nit bar to
            patch_height: The height of the patch
            patch_width: The width of the patch
            start_x: The x position to start the nit bar at
            start_y: The y position to start the nit bar at

        Returns: The patch with the nit bar added

        """
        nit_bar_height = 100
        nit_bar_steps = 10
        nit_bar_roi = Oiio.ROI(start_x, start_x + patch_width, start_y, start_y + nit_bar_height)
        rois = self.split_roi(nit_bar_roi, nit_bar_steps + 1)
        img_buffers = self.create_image_buffers_from_rois(rois)
        for count, img_buf in enumerate(img_buffers):
            val = self.peak_lum * count * 0.1
            Oiio.ImageBufAlgo.fill(img_buf, [val, val, val])
        patch = self.insert_image_buffers(patch, img_buffers, x_pos=start_x + (int(patch_width * 0.5)),
                                          y_pos=start_y + patch_height + nit_bar_height)

        self._add_slate_text(patch, "0 Nits", (start_x, start_y + patch_height + 200), 30, bold=False)
        self._add_slate_text(
            patch, f"{self.led_wall.target_max_lum_nits} Nits",
            (start_x + patch_width - 100, start_y + patch_height + 200), 30, bold=False
        )
        return patch

    def _add_slate_cross_hairs_and_inner_circle(
            self,
            patch: Oiio.ImageBuf,
            patch_height: int,
            patch_width: int,
            start_x: int,
            start_y: int) -> None:
        """ Adds cross-hairs and inner focus circle to the patch

        Args:
            patch: The patch to add the cross-hairs and inner circle to
            patch_height: The height of the patch
            patch_width: The width of the patch
            start_x: The x position of the patch
            start_y: The y position of the patch
        """
        self.draw_crosshair(patch, x_pos=start_x + 50, y_pos=start_y + 50, length=20, thickness=5, colour=[0, 0, 0])
        self.draw_crosshair(patch, x_pos=start_x + patch_width - 50, y_pos=start_y + 50, length=20, thickness=5,
                            colour=[0, 0, 0])
        self.draw_crosshair(patch, x_pos=start_x + 50, y_pos=start_y + patch_width - 50, length=20, thickness=5,
                            colour=[0, 0, 0])
        self.draw_crosshair(patch, x_pos=start_x + patch_width - 50, y_pos=start_y + patch_width - 50, length=20,
                            thickness=5, colour=[0, 0, 0])
        self.draw_crosshair(patch, x_pos=start_x + (int(patch_width * 0.5)), y_pos=start_y + (int(patch_height * 0.5)),
                            length=20, thickness=5, colour=[0, 0, 0])
        self.draw_circle(patch, horizontal_centre=start_x + (int(patch_width * 0.5)),
                         vertical_centre=start_y + (int(patch_height * 0.5)),
                         radius=(int(patch_width * 0.48)), thickness=5, colour=[0, 0, 0])

    def _add_slate_version_setting_info_text(self, patch: Oiio.ImageBuf) -> Oiio.ImageBuf:
        """ Adds the version and key parameters to the slate

        Args:
            patch: the slate image we want to apply the text too

        Returns: The slate image with the text applied

        """
        self._add_slate_text(
            patch, f"Target Content Gamut: {self.led_wall.target_gamut}", (130, 1700), 40,
            bold=False
        )

        self._add_slate_text(
            patch, f"Screen: EOTF {self.led_wall.target_eotf}, "
                   f"Max Lum {self.led_wall.target_max_lum_nits} Nits", (130, 1750), 40,
            bold=False
        )

        self._add_slate_text(
            patch, f"Model: RGBW Sequence, Ref Images, {self.led_wall.num_grey_patches} "
                   f"Greyscale Patches", (130, 1800), 40,
            bold=False
        )

        self._add_slate_text(
            patch, f"Version: {open_vp_cal.__version__}", (130, 1850), 40,
            bold=False
        )

        self._add_slate_text(
            patch, f"Authors: {' / '.join(open_vp_cal.__authors__)}", (130, 1885), 25,
            bold=False
        )
        return patch

    def _add_slate_inner_squares(
            self,
            patch: Oiio.ImageBuf,
            patch_height: int,
            patch_width: int,
            start_x: int,
            start_y: int):
        """ Adds the inner squares to the slate

        Args:
            patch: The patch to add the inner squares to
            patch_height: The height of the patch
            patch_width: The width of the patch
            start_x: The x position of the patch
            start_y: The y position of the patch

        Returns: The patch with the inner squares added

        """
        patch_roi = Oiio.ROI(start_x, start_x + patch_width, start_y, start_y + patch_height)
        inner_edge_roi = self.reduce_roi(patch_roi, 1)
        inner_patch_roi = self.reduce_roi(inner_edge_roi, 1)
        Oiio.ImageBufAlgo.fill(patch, (self.percent_18_lum, self.percent_18_lum, self.percent_18_lum), roi=patch_roi)
        Oiio.ImageBufAlgo.fill(patch, (0.0, 0.0, 0.0), roi=inner_edge_roi)
        Oiio.ImageBufAlgo.fill(patch, (self.percent_18_lum, self.percent_18_lum, self.percent_18_lum),
                               roi=inner_patch_roi)

        title = "Open VP Cal - LED Calibration Tool"
        self._add_slate_text(patch, title, (start_x + 40, start_y - 90), 60, bold=True)
        major_settings = f"v{open_vp_cal.__version__} {self.led_wall.target_gamut} " \
                         f"{self.led_wall.target_eotf} " \
                         f"{self.led_wall.target_max_lum_nits} Nits " \
                         f"GS {self.led_wall.num_grey_patches} " \
                         f"SAT {self.led_wall.primaries_saturation} "

        self._add_slate_text(patch, major_settings, (start_x + 20, start_y - 30), 40, bold=False)

    def generate_solid_patch(self, patch_values: tuple[float, float, float]) -> list[Oiio.ImageBuf]:
        """ Generates a full saturation patch with the given values.

        Args:
            patch_values: The RGB values of the patch

        Returns: A list of ImageBufs containing the patch

        """
        # Create the colour patch
        patch_width, patch_height = self.patch_size

        patch = Oiio.ImageBuf(Oiio.ImageSpec(patch_width, patch_height, 3, Oiio.FLOAT))
        Oiio.ImageBufAlgo.fill(patch, (patch_values[0], patch_values[1], patch_values[2]))
        return [patch]

    def generate_solid_patch_full(self, patch_values: tuple[float, float, float]) -> list[Oiio.ImageBuf]:
        """ Creates the same solid patch but for the full resolution of the image

        :return:
        """
        # Create the colour patch for the full image size
        full_image = Oiio.ImageBuf(Oiio.ImageSpec(
            self.led_wall.project_settings.resolution_width, self.led_wall.project_settings.resolution_height, 3,
            Oiio.FLOAT)
        )
        Oiio.ImageBufAlgo.fill(full_image, (patch_values[0], patch_values[1], patch_values[2]))
        return [full_image]

    def generate_patch(self, patch_name: constants.PATCHES) -> list[Oiio.ImageBuf]:
        """
        Generates a colour square using OpenImageIO (Oiio) for the given pattern name.

        Parameters:
            patch_name (str): The name of the pattern

        Returns:
            Oiio.ImageBuf: The image buffer of the generated colour square.
        """
        image_width, image_height = self.led_wall.project_settings.resolution_width, \
            self.led_wall.project_settings.resolution_height

        patches, _ = self.find_and_generate_patch_from_map(patch_name)

        # Calculate the start position of the patch so that it is centered in the image
        start_x, start_y = self.get_patch_start_positions()

        result = []
        for patch in patches:
            # If we generated a full image rather than just a patch, we return it as it
            if patch.spec().width == image_width and patch.spec().height == image_height:
                result.append(patch)
                continue

            # Create a new ImageBuf with the given resolution and fill it with black
            img = Oiio.ImageBuf(Oiio.ImageSpec(image_width, image_height, 3, Oiio.FLOAT))
            Oiio.ImageBufAlgo.fill(img, (0, 0, 0))

            # Paste the patch onto the image
            Oiio.ImageBufAlgo.paste(img, int(start_x), int(start_y), 0, 0, patch)
            result.append(img)

        return result

    def find_and_generate_patch_from_map(self, patch_name: str) -> Tuple[List[Oiio.ImageBuf], List[float]]:
        """ Finds the patch function and values from the patches map and generates the patch

        Args:
            patch_name: The name of the patch to generate

        Returns: The generated patches, and the values which went into generating them

        """
        # get the patch function and values
        if patch_name in self.patches_map:
            patch_func, patch_values = self.patches_map[patch_name]
        else:
            raise ValueError(f"Patch name {patch_name} not found in patches map")
        patches = patch_func(patch_values)
        return patches, patch_values

    def apply_color_convert(self, img_buf):
        """
        Applies the Oiio.ImageBufAlgo colour convert method to the given image buffer.

        Parameters:
            img_buf (Oiio.ImageBuf): The image buffer to apply the colour convert to.

        Returns:
            Oiio.ImageBuf: The image buffer after applying the colour convert.
        """
        target_gamut_only_cs_name, _ = ocio_config.OcioConfigWriter.target_gamut_only_cs_metadata(self.led_wall)
        target_gamut_and_tf_cs_name, _ = ocio_config.OcioConfigWriter.target_gamut_and_transfer_function_cs_metadata(
            self.led_wall
        )

        output_img_buf = imaging_utils.apply_color_conversion(
            img_buf,
            target_gamut_only_cs_name,
            target_gamut_and_tf_cs_name,
            color_config=self.generation_ocio_config_path
        )
        return output_img_buf

    def write_to_disk(self, img_buf, patch_name) -> str:
        """ Writes the given image buffer to disk using the output folder parameter name from the project settings.

        Parameters:
            img_buf (Oiio.ImageBuf): The image buffer to write to disk.
            patch_name (str): The name of the patch.
        """
        folder_path = os.path.join(
            self.led_wall.project_settings.export_folder, constants.ProjectFolders.PATCHES)

        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        folder_path = os.path.join(folder_path, self.base_name, self.led_wall.project_settings.file_format)
        if not os.path.exists(folder_path):
            os.makedirs(folder_path)

        file_path = os.path.join(folder_path, f"{patch_name}.{self.led_wall.project_settings.file_format}")

        bit_depth = 10
        if self.led_wall.project_settings.file_format == constants.FileFormats.FF_EXR:
            bit_depth = "float"

        if self.led_wall.project_settings.file_format == constants.FileFormats.FF_TIF:
            bit_depth = 16

        imaging_utils.write_image(img_buf, file_path, bit_depth, channel_mapping=None)
        return file_path

    def generate_patches(self, patch_names: list[constants.PATCHES]):
        """
        Generates colour squares for the given patch names, applies colour convert, and writes them to disk.

        # 1. Load The OCIO Config
        # 2. Now have a virtual colour config
        # 3. Add a new colourspace which is just the target gamut (linear gamut rec2020)

        # 4. Apply this to the macbeth chart
        # 5. Add another colour space which has the target gamut and the transfer function (2020 pq)
        # 6. Apply the transfer function (ST-2084_to_LINEAR) to the legal patches only
        # 7. Apply for all things that are not EXR add, the forward colour space from 5 to everything with 3 as an input

        Parameters:
            patch_names (list[str]): The list of patch names.

        """
        self.calc_constants()
        ocio_config_writer = ocio_config.OcioConfigWriter(self.led_wall.project_settings.output_folder)
        self.generation_ocio_config_path = ocio_config_writer.generate_pre_calibration_ocio_config([self.led_wall])
        led_wall_name_cleaned = utils.replace_non_alphanumeric(self.led_wall.name, "_")
        target_gamut_cleaned = utils.replace_non_alphanumeric(str(self.led_wall.target_gamut), "_")
        target_eotf_cleaned = utils.replace_non_alphanumeric(str(self.led_wall.target_eotf), "_")
        self.base_name = f"OpenVPCal_{led_wall_name_cleaned}_{target_gamut_cleaned}_{target_eotf_cleaned}"

        count = 0
        file_paths = []
        for patch_name in patch_names:
            img_buffers = self.generate_patch(patch_name)
            for img_buf in img_buffers:
                if self.led_wall.project_settings.file_format != constants.FileFormats.FF_EXR:
                    img_buf = self.apply_color_convert(img_buf)
                for _ in range(self.led_wall.project_settings.frames_per_patch):
                    file_name = f"{self.base_name}.{str(count).zfill(6)}"
                    file_paths.append(
                        self.write_to_disk(img_buf, str(file_name))
                    )
                    count += 1
        return file_paths
