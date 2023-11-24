"""
This module contains the classes to write the OCIO configuration file.
"""
import os
import typing
from typing import List

import PyOpenColorIO as ocio
import colour
from PyOpenColorIO import ColorSpace
from colour import RGB_COLOURSPACES, matrix_RGB_to_RGB
from open_vp_cal.core import constants, ocio_utils, utils
from open_vp_cal.core.constants import EOTF, Results, CalculationOrder
from open_vp_cal.core.ocio_utils import numpy_matrix_to_ocio_matrix
from open_vp_cal.core.resource_loader import ResourceLoader
from open_vp_cal.core.structures import LedWallColourSpaces
from open_vp_cal.led_wall_settings import LedWallSettings


class OcioConfigWriter:
    """
    Class to write the OCIO configuration files for OpenVPCal
    """
    pre_calibration_config_name = "Pre_Calibration_OpenVPCal.ocio"
    post_calibration_config_name = "Post_Calibration_OpenVPCal.ocio"
    family_open_vp_cal = "OpenVPCal"
    family_display = "Display"

    encoding_scene_linear = "scene-linear"
    encoding_hdr_video = "hdr-video"

    def __init__(self, output_folder: str):
        self._output_folder = output_folder

    def _get_view_transform(self, name: str, description: str) -> ocio.ViewTransform:
        """ Get a view transform with the given name and description

        Args:
            name: The name of the view transform
            description: The description of the view transform

        Returns: The view transform

        """
        pre_calibration_view_transform = ocio.ViewTransform(ocio.REFERENCE_SPACE_SCENE)
        pre_calibration_view_transform.setName(name)
        pre_calibration_view_transform.setFamily(self.family_display)
        pre_calibration_view_transform.setDescription(description)
        return pre_calibration_view_transform

    def _get_display_colour_space(
            self, name: str, description: str,
            encoding: str = encoding_scene_linear) -> ocio.ColorSpace:
        """ Gets a colour space with the given name and description

        Args:
            name: The name of the colour space
            description: The description of the colour space

        Returns: The colour space
        """
        display_colour_space = ocio.ColorSpace(ocio.REFERENCE_SPACE_DISPLAY)
        display_colour_space.setName(name)
        display_colour_space.setFamily(self.family_display)
        display_colour_space.setEncoding(encoding)
        display_colour_space.setBitDepth(ocio.BIT_DEPTH_F32)
        display_colour_space.setDescription(description)
        display_colour_space.setAllocation(ocio.Allocation.ALLOCATION_UNIFORM)
        return display_colour_space

    def _get_colour_space(
            self, name: str, description: str,
            encoding: str = encoding_scene_linear) -> ocio.ColorSpace:
        """ Gets a colour space with the given name and description

        Args:
            name: The name of the colour space
            description: The description of the colour space

        Returns: The colour space
        """
        colour_space = ocio.ColorSpace(ocio.REFERENCE_SPACE_SCENE)
        colour_space.setName(name)
        colour_space.setFamily(self.family_open_vp_cal)
        colour_space.setEncoding(encoding)
        colour_space.setBitDepth(ocio.BIT_DEPTH_F32)
        colour_space.setDescription(description)
        return colour_space

    def _get_ocio_config_colour_spaces_for_patch_generation(self, led_wall_settings, preview_export_filter=True) -> LedWallColourSpaces:
        """ Gets the OCIO colour spaces for patch generation

        Args:
            led_wall_settings: the LED wall settings we want the colour spaces for

        Returns: The target_gamut_only, target_gamut_and_transfer_function and transfer_function_only colour spaces

        """
        led_wall_colour_spaces = LedWallColourSpaces()

        # Add Target Gamut Only Colour Space
        led_wall_colour_spaces.target_gamut_cs = self.get_target_gamut_only_cs(led_wall_settings)

        # Add Transfer Function Only Colour Space (Needs to be in a colour space so oiio can apply it)
        led_wall_colour_spaces.transfer_function_only_cs = self.get_transfer_function_only_cs(led_wall_settings)

        # Add Target Gamut Colour Space And Transfer Function
        led_wall_colour_spaces.target_with_inv_eotf_cs = self.get_target_gamut_and_transfer_function_cs(
            led_wall_settings)

        # View Transform
        led_wall_colour_spaces.pre_calibration_view_transform = self.get_pre_calibration_view_transform_vt()

        # Display Colour Space
        led_wall_colour_spaces.display_colour_space_cs = self.get_display_colour_space(led_wall_settings)
        return led_wall_colour_spaces

    def get_display_colour_space(self, led_wall_settings: LedWallSettings) -> ColorSpace:
        """ Get the display colour space for the given led wall

        Args:
            led_wall_settings: The LED wall settings we want the colour space for

        Returns: The display colour space

        """
        target_color_space = utils.get_target_colourspace_for_led_wall(led_wall_settings)

        display_colour_space_name, display_description = self.get_display_colour_space_metadata(led_wall_settings)
        display_colour_space_cs = self._get_display_colour_space(
            display_colour_space_name,
            display_description,
            encoding=self.encoding_hdr_video,
        )

        target_to_XYZ_matrix = target_color_space.matrix_RGB_to_XYZ
        group = self.create_inverse_eotf_group(str(led_wall_settings.target_eotf))
        group.prependTransform(
            ocio.MatrixTransform(
                ocio_utils.numpy_matrix_to_ocio_matrix(target_to_XYZ_matrix.tolist()),
                direction=ocio.TransformDirection.TRANSFORM_DIR_INVERSE
            )
        )
        display_colour_space_cs.setTransform(group, ocio.COLORSPACE_DIR_FROM_REFERENCE)
        return display_colour_space_cs

    @staticmethod
    def get_calibration_preview_space_metadata(led_wall_settings: LedWallSettings) -> tuple[str, str]:
        """ Get the calibration colour space name

        Args:
            led_wall_settings: The LED wall settings we want the colour space names for

        Returns: The calibration colour space name

        """
        calibration_cs_name = f"Calibration Preview {led_wall_settings.name} - {led_wall_settings.native_camera_gamut}"
        calibration_cs_description = ("Calibration colourspace used in the UI only to preview the calibration. "
                                      "Note that the order of operations is inverted to the actual calibration "
                                      "colour space which is exported")
        return calibration_cs_name, calibration_cs_description

    @staticmethod
    def get_calibration_space_metadata(led_wall_settings: LedWallSettings) -> str:
        """ Get the calibration colour space name

        Args:
            led_wall_settings: The LED wall settings we want the colour space names for

        Returns: The calibration colour space name

        """
        calibration_cs_name = f"Calibration {led_wall_settings.name} - {led_wall_settings.native_camera_gamut}"
        return calibration_cs_name

    @staticmethod
    def get_display_colour_space_metadata(led_wall_settings) -> tuple[str, str]:
        """ Get the display colour space name and description

        Args:
            led_wall_settings: The LED wall settings we want the colour space names for

        Returns: The display colour space name and description

        """
        display_colour_space_name = (f"{led_wall_settings.target_gamut} - "
                                     f"{led_wall_settings.target_eotf} - OpenVPCal LED")
        display_description = f"OpenVPCal LED Output {led_wall_settings.target_gamut} - {led_wall_settings.target_eotf}"
        return display_colour_space_name, display_description

    def get_pre_calibration_view_transform_vt(self) -> ocio.ViewTransform:
        """ Get the OCIO view transform for pre-calibration

        Returns: The OCIO view transform for pre-calibration

        """
        pre_calibration_view_transform_name = "OpenVPCal PreCalibration"
        pre_calibration_view_transform_description = "The OpenVPCal Pre Calibrated native Output"
        pre_calibration_view_transform = self._get_view_transform(
            pre_calibration_view_transform_name,
            pre_calibration_view_transform_description
        )

        builtin_acesd_to_XYZ_D65_bradford = ocio.BuiltinTransform(
            "UTILITY - ACES-AP0_to_CIE-XYZ-D65_BFD",
            direction=ocio.TransformDirection.TRANSFORM_DIR_FORWARD,
        )

        pre_calibration_view_transform.setTransform(
            builtin_acesd_to_XYZ_D65_bradford, ocio.ViewTransformDirection.VIEWTRANSFORM_DIR_FROM_REFERENCE
        )
        return pre_calibration_view_transform

    def get_target_gamut_and_transfer_function_cs(self, led_wall_settings: LedWallSettings) -> ColorSpace:
        """ Get the target gamut and transfer function colour space for the given led wall

        Args:
            led_wall_settings: The LED wall settings we want the colour space for

        Returns: The target gamut and transfer function colour space

        """
        name, description = self.target_gamut_and_transfer_function_cs_metadata(led_wall_settings)
        target_gamut_and_tf_cs = self._get_colour_space(
            name, description, encoding=self.encoding_hdr_video)

        inverse_eotf_group_transform = self.create_inverse_eotf_group(str(led_wall_settings.target_eotf))
        target_gamut_and_tf_cs.setTransform(inverse_eotf_group_transform, ocio.COLORSPACE_DIR_FROM_REFERENCE)

        ref_to_target_matrix_transform = self.get_reference_to_target_matrix(
            led_wall_settings
        )

        inverse_eotf_group_transform.prependTransform(ref_to_target_matrix_transform)
        target_gamut_and_tf_cs.setTransform(inverse_eotf_group_transform, ocio.COLORSPACE_DIR_FROM_REFERENCE)
        return target_gamut_and_tf_cs

    @staticmethod
    def create_inverse_eotf_group(tgt_eotf: str) -> ocio.GroupTransform:
        """ Create an OCIO group transform for the inverse EOTF

        Args:
            tgt_eotf: The target EOTF

        Returns: The OCIO group transform for the inverse EOTF

        """
        inverse_eotf_group_transform = ocio.GroupTransform()
        if tgt_eotf:
            if tgt_eotf.startswith("gamma "):
                gamma = float(tgt_eotf[5:])
                inverse_eotf_group_transform.appendTransform(
                    ocio.ExponentTransform(
                        value=[gamma, gamma, gamma, 1],
                        negativeStyle=ocio.NegativeStyle.NEGATIVE_PASS_THRU,
                        direction=ocio.TransformDirection.TRANSFORM_DIR_INVERSE)
                )
            elif tgt_eotf == EOTF.EOTF_ST2084:
                # OCIO PQ builtin expects 1 to be 100nits
                inverse_eotf_group_transform.appendTransform(
                    ocio.BuiltinTransform(
                        "CURVE - ST-2084_to_LINEAR",
                        direction=ocio.TransformDirection.TRANSFORM_DIR_INVERSE,
                    )
                )
            elif tgt_eotf == EOTF.EOTF_BT1886:
                inverse_eotf_group_transform.appendTransform(
                    ocio.ExponentTransform(
                        value=2.4, negativeStyle=ocio.NegativeStyle.NEGATIVE_PASS_THRU,
                        direction=ocio.TransformDirection.TRANSFORM_DIR_INVERSE,
                    )
                )
            elif tgt_eotf == EOTF.EOTF_SRGB:
                inverse_eotf_group_transform.appendTransform(
                    ocio.ExponentWithLinearTransform(
                        gamma=2.4, offset=0.055,
                        direction=ocio.TransformDirection.TRANSFORM_DIR_INVERSE,
                    )
                )
            else:
                raise RuntimeError("Unknown EOTF: " + tgt_eotf)
        return inverse_eotf_group_transform

    def get_transfer_function_only_cs(self, led_wall_settings: LedWallSettings) -> ColorSpace:
        """ Get the transfer function only colour space for the given led wall

        Args:
            led_wall_settings: The LED wall settings we want the colour space for

        Returns: The transfer function only colour space

        """
        name, description = self.transfer_function_only_cs_metadata(led_wall_settings)
        transfer_function_only_cs = self._get_colour_space(
            name, description, encoding=self.encoding_hdr_video)

        inverse_eotf_group_transform = self.create_inverse_eotf_group(str(led_wall_settings.target_eotf))
        transfer_function_only_cs.setTransform(inverse_eotf_group_transform, ocio.COLORSPACE_DIR_FROM_REFERENCE)
        return transfer_function_only_cs

    @staticmethod
    def target_gamut_and_transfer_function_cs_metadata(led_wall_settings: LedWallSettings) -> tuple[str, str]:
        """ Get the target gamut and transfer function only colour space name and description

        Args:
            led_wall_settings: The LED wall settings we want the colour space names for

        Returns: The transfer function only colour space name and description

        """
        target_color_space = utils.get_target_colourspace_for_led_wall(led_wall_settings)
        target_gamut_and_tf_cs_name = f"{target_color_space.name} - {led_wall_settings.target_eotf}"
        transfer_function_only_cs_description = "OpenVPCal Target Gamut and EOTF"
        return target_gamut_and_tf_cs_name, transfer_function_only_cs_description

    @staticmethod
    def transfer_function_only_cs_metadata(led_wall_settings: LedWallSettings) -> tuple[str, str]:
        """ Get the transfer function only colour space name and description

        Args:
            led_wall_settings: The LED wall settings we want the colour space names for

        Returns: The transfer function only colour space name and description

        """
        transfer_function_only_cs_name = f"{led_wall_settings.target_eotf} - Curve"
        transfer_function_only_cs_description = "OpenVPCal EOTF Only"
        return transfer_function_only_cs_name, transfer_function_only_cs_description

    @staticmethod
    def target_gamut_only_cs_metadata(led_wall_settings: LedWallSettings) -> tuple[str, str]:
        """ Get the target gamut only colour space name and description

        Args:
            led_wall_settings: The LED wall settings we want the colour space names for

        Returns: The target gamut only colour space name and description

        """
        target_color_space = utils.get_target_colourspace_for_led_wall(led_wall_settings)

        target_gamut_only_cs_name = f"Linear {target_color_space.name}"
        target_gamut_only_cs_description = "OpenVPCal Target Gamut In Linear Space"
        return target_gamut_only_cs_name, target_gamut_only_cs_description

    def get_target_gamut_only_cs(
            self, led_wall_settings: LedWallSettings) -> ColorSpace:
        """ Get the target gamut only ocio colour space object and the reference to target matrix ocio transform

        Args:
            led_wall_settings: The LED wall settings we want the colour space for

        Returns: The target gamut only colour space

        """
        name, description = self.target_gamut_only_cs_metadata(led_wall_settings)
        target_gamut_only_cs = self._get_colour_space(
            name, description)

        ref_to_target_matrix_transform = self.get_reference_to_target_matrix(
            led_wall_settings
        )

        target_gamut_only_cs.setTransform(
            ref_to_target_matrix_transform, direction=ocio.ColorSpaceDirection.COLORSPACE_DIR_FROM_REFERENCE)

        return target_gamut_only_cs

    @staticmethod
    def get_reference_to_target_matrix(
            led_wall_settings: LedWallSettings) -> ocio.MatrixTransform:
        """ Get the reference to target matrix transform which goes from the reference colour space to the target

        Args:
            led_wall_settings: The LED wall settings we want the matrix transform for

        Returns: The matrix transform which goes from the reference colour space to the target colour space

        """
        reference_colour_space = RGB_COLOURSPACES[led_wall_settings.input_plate_gamut]
        target_color_space = utils.get_target_colourspace_for_led_wall(led_wall_settings)
        reference_to_target_matrix = matrix_RGB_to_RGB(
            input_colourspace=reference_colour_space,
            output_colourspace=target_color_space,
            chromatic_adaptation_transform=str(led_wall_settings.reference_to_target_cat),
        )
        ref_to_target_matrix_transform = ocio.MatrixTransform(
            ocio_utils.numpy_matrix_to_ocio_matrix(reference_to_target_matrix)
        )
        return ref_to_target_matrix_transform

    def _get_openvpcal_colour_spaces(self,
                                     led_wall_settings: LedWallSettings,
                                     preview_export_filter: bool = True) -> LedWallColourSpaces:
        """ Gets The OpenVPCal Colour Spaces we need to write to disk as an ocio config

        Args:
            led_wall_settings: The LED wall settings we want the colour spaces for
            preview_export_filter: Whether we want to write out the preview clf or not

        Returns: The colour spaces for the given LED wall settings

        """
        led_wall_colour_spaces = LedWallColourSpaces()
        results = led_wall_settings.processing_results.calibration_results

        led_wall_colour_spaces.target_gamut_cs = self.get_target_gamut_only_cs(led_wall_settings)
        led_wall_colour_spaces.target_with_inv_eotf_cs = self.get_target_gamut_and_transfer_function_cs(
            led_wall_settings)

        # Get Calibration Colour Space and Calibration Preview Colour Space Adding A Reference To Target Matrix
        calibration_cs, calibration_preview_cs = self.get_calibration_and_calibration_preview_cs(
            led_wall_settings,
            results,
            preview_export_filter=preview_export_filter
        )
        led_wall_colour_spaces.calibration_cs = calibration_cs
        led_wall_colour_spaces.calibration_preview_cs = calibration_preview_cs

        # Pre-Calibration View Transform
        led_wall_colour_spaces.pre_calibration_view_transform = self.get_pre_calibration_view_transform_vt()

        # View Transform
        led_wall_colour_spaces.view_transform = self.get_post_calibration_view_transform(led_wall_settings)

        # Display Colour Space
        led_wall_colour_spaces.display_colour_space_cs = self.get_display_colour_space(led_wall_settings)

        # Add Transfer Function Only Colour Space (Needs to be in a colour space so oiio can apply it)
        led_wall_colour_spaces.transfer_function_only_cs = self.get_transfer_function_only_cs(led_wall_settings)
        return led_wall_colour_spaces

    def get_calibration_and_calibration_preview_cs(
            self, led_wall_settings: LedWallSettings, results: dict,
            preview_export_filter: bool = True) -> typing.Tuple[ColorSpace, ColorSpace]:
        """ Get the calibration colour space for the given led wall, we also get the preview colour space for use in
            UI applications

        Args:
            led_wall_settings: The LED wall settings we want the colour space for
            results: The results of the calibration we want to add into the description
            preview_export_filter: Whether we want to write out the preview clf or not

        Returns: The calibration colour space and the calibration preview colour space

        """
        calibration_cs = self.get_calibration_cs(led_wall_settings, results)
        group = ocio.GroupTransform()
        group.appendTransform(self.get_reference_to_target_matrix(led_wall_settings))
        calibration_preview_cs = self.get_calibration_preview_cs(led_wall_settings)
        group_preview = ocio.GroupTransform()
        group_preview.appendTransform(self.get_reference_to_target_matrix(led_wall_settings))
        EOTF_CS_string = CalculationOrder.CO_EOTF_CS_STRING
        CS_EOTF_string = CalculationOrder.CO_CS_EOTF_STRING
        if results[Results.CALCULATION_ORDER] == CalculationOrder.CO_EOTF_CS:

            # matrix transform to screen colour space
            ocio_utils.populate_ocio_group_transform_for_CO_EOTF_CS(
                "_".join([calibration_cs.getName(), EOTF_CS_string]), group, self._output_folder, results)

            if preview_export_filter:
                ocio_utils.populate_ocio_group_transform_for_CO_CS_EOTF(
                    "_".join([calibration_preview_cs.getName(), CS_EOTF_string]),
                    group_preview,
                    self._output_folder, results
                )

        elif results[Results.CALCULATION_ORDER] == CalculationOrder.CO_CS_EOTF:

            ocio_utils.populate_ocio_group_transform_for_CO_CS_EOTF(
                "_".join([calibration_cs.getName(), CS_EOTF_string]), group,
                self._output_folder,
                results
            )
            if preview_export_filter:
                ocio_utils.populate_ocio_group_transform_for_CO_EOTF_CS(
                    "_".join([calibration_preview_cs.getName(), EOTF_CS_string]), group_preview,
                    self._output_folder,
                    results
                )

        else:
            raise RuntimeError("Unknown calculation order: " + results[Results.CALCULATION_ORDER])
        # gamut compression fixed function
        if results[Results.ENABLE_GAMUT_COMPRESSION]:
            gamut_comp_group = ocio_utils.create_gamut_compression(results)
            group.appendTransform(gamut_comp_group)
            group_preview.appendTransform(gamut_comp_group)
        # Apply The Inverse Reference To Target Matrix "reverse"
        inv_ref_to_target = ocio.MatrixTransform(
            numpy_matrix_to_ocio_matrix(results[Results.REFERENCE_TO_TARGET_MATRIX]),
            direction=ocio.TransformDirection.TRANSFORM_DIR_INVERSE
        )
        group.appendTransform(inv_ref_to_target)
        group_preview.appendTransform(inv_ref_to_target)
        calibration_cs.setTransform(group, ocio.COLORSPACE_DIR_FROM_REFERENCE)
        calibration_preview_cs.setTransform(group_preview, ocio.COLORSPACE_DIR_FROM_REFERENCE)
        return calibration_cs, calibration_preview_cs

    def get_post_calibration_view_transform(self, led_wall_settings: LedWallSettings) -> ocio.ViewTransform:
        """ Get the OCIO view transform for post-calibration

        Args:
            led_wall_settings: The LED wall settings we want the view transform for

        Returns: The OCIO view transform for post-calibration

        """
        view_transform_description, view_transform_name = self.get_post_calibration_view_transform_metadata(
            led_wall_settings)

        view_transform = self._get_view_transform(view_transform_name, view_transform_description)
        group = ocio.GroupTransform()
        group.appendTransform(
            ocio.ColorSpaceTransform(
                src=constants.ColourSpace.CS_ACES, dst=self.get_calibration_space_metadata(led_wall_settings)
            )
        )

        builtin_aces_to_XYZ_D65_bradford = ocio.BuiltinTransform(
            "UTILITY - ACES-AP0_to_CIE-XYZ-D65_BFD",
            direction=ocio.TransformDirection.TRANSFORM_DIR_FORWARD,
        )

        group.appendTransform(
            builtin_aces_to_XYZ_D65_bradford
        )
        view_transform.setTransform(group, ocio.ViewTransformDirection.VIEWTRANSFORM_DIR_FROM_REFERENCE)
        return view_transform

    @staticmethod
    def get_post_calibration_view_transform_metadata(led_wall_settings: LedWallSettings) -> tuple[str, str]:
        """ Get the post-calibration view transform name and description

        Args:
            led_wall_settings: The LED wall settings we want the view transform names and description for

        Returns: The post-calibration view transform name and description

        """
        target_colour_space = utils.get_target_colourspace_for_led_wall(led_wall_settings)
        view_transform_name = f"OpenVPCal {led_wall_settings.name} - {led_wall_settings.native_camera_gamut}"
        view_transform_description = f"OpenVPCal {target_colour_space.name} {led_wall_settings.native_camera_gamut}"
        return view_transform_description, view_transform_name

    def get_calibration_cs(self, led_wall_settings: LedWallSettings, results: typing.Dict) -> ColorSpace:
        """ Get the calibration colour space for the given led wall

        Args:
            led_wall_settings: The LED wall settings we want the colour space for
            results: The results of the calibration we want to add into the description

        Returns: The calibration colour space

        """
        calibration_cs_name = self.get_calibration_space_metadata(led_wall_settings)
        desc_dict = {
            k: results[k]
            for k in (
                Results.TARGET_EOTF,
                Results.TARGET_GAMUT,
                Results.CALCULATION_ORDER,
                Results.ENABLE_PLATE_WHITE_BALANCE,
                Results.ENABLE_GAMUT_COMPRESSION,
                Results.ENABLE_EOTF_CORRECTION
            )
        }
        config_str = "\n".join([f"{k}--{v}" for (k, v) in desc_dict.items()])
        description = ("Colourspace for OpenVPCal.\n"
                       "EOTF correction assumes signal 1.0 represents 100 nits\n"
                       "Configuration---\n") + config_str
        return self._get_colour_space(calibration_cs_name, description)

    def get_calibration_preview_cs(self, led_wall_settings: LedWallSettings) -> ColorSpace:
        """ Get the calibration preview colour space for the given led wall

        Args:
            led_wall_settings: The LED wall settings we want the colour space for

        Returns: The calibration preview colour space

        """
        name, description = self.get_calibration_preview_space_metadata(led_wall_settings)
        calibration_preview_cs = self._get_colour_space(name, description)
        return calibration_preview_cs

    def _generate_ocio_config(
            self, led_walls: List[LedWallSettings], colour_space_function: typing.Callable,
            output_file=None, base_ocio_config=None,
            preview_export_filter=True) -> str:
        """ Generate an OCIO config for the necessary colour spaces and transforms retrieved by the given function

        Args:
            led_walls: The LED walls we want the colour spaces for
            colour_space_function: The function to get the colour spaces

        Returns: The file path to the ocio config we write out

        """
        reference_spaces = []
        led_walls = [led_wall for led_wall in led_walls if not led_wall.is_verification_wall]
        for led_wall in led_walls:
            if led_wall.processing_results:
                if led_wall.processing_results.calibration_results:
                    reference_spaces.append(
                        led_wall.processing_results.calibration_results[constants.Results.OCIO_REFERENCE_GAMUT]
                    )
                else:
                    if led_wall.processing_results.pre_calibration_results:
                        reference_spaces.append(
                            led_wall.processing_results.pre_calibration_results[constants.Results.OCIO_REFERENCE_GAMUT]
                        )

        ocio_config_reference_space_names = list(set(reference_spaces))
        if not ocio_config_reference_space_names:
            ocio_config_reference_space_names.append(constants.ColourSpace.CS_ACES)

        if len(ocio_config_reference_space_names) != 1:
            raise ValueError("Multiple reference colour spaces found for the ocio config")

        colour_spaces = {}
        for led_wall in led_walls:
            led_wall_colour_spaces = colour_space_function(led_wall, preview_export_filter=preview_export_filter)
            led_wall.processing_results.led_wall_colour_spaces = led_wall_colour_spaces
            colour_spaces[led_wall.name] = led_wall_colour_spaces

        return self.write_config(
            colour_spaces,
            output_file,
            ocio_config_reference_space_names[0],
            base_ocio_config,
            preview_export_filter=preview_export_filter
        )

    def generate_pre_calibration_ocio_config(
            self, led_walls: List[LedWallSettings],
            output_file: str = None, base_ocio_config: str = None, preview_export_filter: bool = True) -> str:
        """ Generate an OCIO config for pre-calibration with all the necessary colour spaces and transforms.

        Args:
            led_walls: The LED walls we want the colour spaces for
            output_file: The file path to the ocio config we write to disk
            base_ocio_config: The base ocio config path to use
            preview_export_filter: Whether to export the preview colour space or not

        Returns: The file path to the ocio config we write out

        """
        if not output_file:
            output_file = os.path.join(
                self._output_folder,
                constants.ProjectFolders.CALIBRATION,
                self.pre_calibration_config_name
            )

        return self._generate_ocio_config(
            led_walls, self._get_ocio_config_colour_spaces_for_patch_generation,
            output_file=output_file, base_ocio_config=base_ocio_config,
            preview_export_filter=preview_export_filter)

    def generate_post_calibration_ocio_config(
            self, led_walls: List[LedWallSettings], output_file: str = None, base_ocio_config: str = None,
            preview_export_filter: bool = False) -> str:
        """ Generate an OCIO config for post-calibration with all the necessary colour spaces and transforms.

        Args:
            led_walls: The LED walls we want the colour spaces for
            output_file: The file path to the ocio config we write to disk
            base_ocio_config: The base ocio config path to use
            preview_export_filter: Whether to export the preview colour space or not

        Returns: The file path to the ocio config we write out

        """
        if not output_file:
            output_file = os.path.join(
                self._output_folder,
                self.post_calibration_config_name
            )

        return self._generate_ocio_config(
            led_walls, self._get_openvpcal_colour_spaces, output_file=output_file, base_ocio_config=base_ocio_config,
            preview_export_filter=preview_export_filter)

    @staticmethod
    def write_config(
            colour_spaces: typing.Dict[str, LedWallColourSpaces],
            filename: str,
            ocio_reference_space_name: str,
            base_config_path: str = None,
            preview_export_filter: bool = True) -> str:
        """ Writes the OpenVPCal ocio config to disk using the given map of led wall names and colour spaces

        Args:
            colour_spaces: The colour spaces we want to write out per led wall
            filename: The filename to write the ocio config to
            ocio_reference_space_name: The name of the ocio reference space
            base_config_path: The base ocio config path to use
            preview_export_filter: Whether to export the preview colour space or not

        Returns: The file path to the ocio config we write out

        """

        if not base_config_path:
            base_config_path = ResourceLoader.ocio_config_path()

        config = ocio.Config.CreateFromFile(base_config_path)

        # Ensure that the config contains the aces_interchange role and colour space
        interchange_colorspace = config.getColorSpace("aces_interchange")
        if not interchange_colorspace:
            raise ValueError("aces_interchange not found in OCIO config")

        # Check that the ocio reference space name we are using is the same as the aces_interchange colour space
        if ocio_reference_space_name != interchange_colorspace.getName():
            raise ValueError(
                f"OCIO Reference Space: {ocio_reference_space_name} "
                f"Does Not Match The 'aces_interchange': {interchange_colorspace.getName()}"
            )

        added_colour_spaces = []
        added_view_transforms = []
        added_display_colour_spaces = []
        added_target_colour_spaces = []
        pre_calibration_view_transform_added = []
        for _, lw_cs in colour_spaces.items():
            if lw_cs.transfer_function_only_cs:
                if lw_cs.transfer_function_only_cs.getName() not in added_colour_spaces:
                    config.addColorSpace(lw_cs.transfer_function_only_cs)
                    added_colour_spaces.append(lw_cs.transfer_function_only_cs.getName())

            if lw_cs.pre_calibration_view_transform:
                if lw_cs.pre_calibration_view_transform.getName() not in pre_calibration_view_transform_added:
                    config.addViewTransform(lw_cs.pre_calibration_view_transform)
                    pre_calibration_view_transform_added.append(lw_cs.pre_calibration_view_transform.getName())

            if lw_cs.calibration_preview_cs and preview_export_filter:
                if lw_cs.calibration_preview_cs.getName() not in added_colour_spaces:
                    config.addColorSpace(lw_cs.calibration_preview_cs)
                    added_colour_spaces.append(lw_cs.calibration_preview_cs.getName())

            # if lw_cs.aces_to_cie_d65_cat02_cs:
            #     if lw_cs.aces_to_cie_d65_cat02_cs.getName() not in added_colour_spaces:
            #         config.addColorSpace(lw_cs.aces_to_cie_d65_cat02_cs)
            #         added_colour_spaces.append(lw_cs.aces_to_cie_d65_cat02_cs.getName())

            if lw_cs.target_with_inv_eotf_cs:
                if lw_cs.target_with_inv_eotf_cs.getName() not in added_target_colour_spaces:
                    config.addColorSpace(lw_cs.target_with_inv_eotf_cs)
                    added_target_colour_spaces.append(lw_cs.target_with_inv_eotf_cs.getName())

            if lw_cs.target_gamut_cs:
                if lw_cs.target_gamut_cs.getName() not in added_target_colour_spaces:
                    config.addColorSpace(lw_cs.target_gamut_cs)
                    added_target_colour_spaces.append(lw_cs.target_gamut_cs.getName())

            if lw_cs.view_transform:
                if lw_cs.view_transform.getName() not in added_view_transforms:
                    config.addViewTransform(lw_cs.view_transform)
                    added_view_transforms.append(lw_cs.view_transform.getName())

            if lw_cs.calibration_cs:
                if lw_cs.calibration_cs.getName() not in added_colour_spaces:
                    config.addColorSpace(lw_cs.calibration_cs)
                    added_colour_spaces.append(lw_cs.calibration_cs.getName())

            if lw_cs.display_colour_space_cs:
                if lw_cs.display_colour_space_cs.getName() not in added_display_colour_spaces:
                    config.addColorSpace(lw_cs.display_colour_space_cs)
                    added_display_colour_spaces.append(lw_cs.display_colour_space_cs.getName())
                    config.addDisplayView(lw_cs.display_colour_space_cs.getName(), "Raw", "Raw")

            if lw_cs.display_colour_space_cs and lw_cs.view_transform:
                config.addDisplaySharedView(lw_cs.display_colour_space_cs.getName(), lw_cs.view_transform.getName())

            if lw_cs.view_transform:
                config.addSharedView(
                    lw_cs.view_transform.getName(), lw_cs.view_transform.getName(), ocio.OCIO_VIEW_USE_DISPLAY_NAME)

                active_views = config.getActiveViews()
                active_views += f", {lw_cs.view_transform.getName()}"
                config.setActiveViews(active_views)

        for added_display_colour_space in added_display_colour_spaces:
            config.addDisplaySharedView(added_display_colour_space, pre_calibration_view_transform_added[0])

            active_displays = config.getActiveDisplays()
            active_displays += f", {added_display_colour_space}"
            config.setActiveDisplays(active_displays)

        if pre_calibration_view_transform_added:
            config.addSharedView(
                pre_calibration_view_transform_added[0], pre_calibration_view_transform_added[0],
                ocio.OCIO_VIEW_USE_DISPLAY_NAME
            )

            active_views = config.getActiveViews()
            active_views += f", {pre_calibration_view_transform_added[0]}"
            config.setActiveViews(active_views)

        # Set the search path so its relative to the ocio config folder
        config.setSearchPath("./")

        filename = os.path.abspath(filename)
        parent_dir = os.path.dirname(filename)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        with open(filename, "w", encoding="utf-8") as file:
            file.write(config.serialize())

        return filename
