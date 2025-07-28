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

This module contains the classes to write the OCIO configuration file.
"""
import os
import shutil
import typing
from typing import List

import PyOpenColorIO as ocio
import numpy as np
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
    pre_calibration_config_name = "Pre_Calibration_OpenVPCal_{project_id}.ocio"
    post_calibration_config_name = "Post_Calibration_OpenVPCal_{project_id}.ocio"
    family_open_vp_cal = "OpenVPCal"
    family_display = "Display"
    family_open_vp_cal_input = "OpenVPCal/Input"
    family_open_vp_cal_utility = "OpenVPCal/Utility"

    encoding_scene_linear = "scene-linear"
    encoding_hdr_video = "hdr-video"
    encoding_log = "log"

    pre_calibration_output = "Pre-Calibration Output"
    calibrated_output = "Calibrated Output"

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
        pre_calibration_view_transform.setDescription(description)
        return pre_calibration_view_transform

    def _get_display_colour_space(
            self, name: str, description: str,
            encoding: str = encoding_scene_linear, family: str = "") -> ocio.ColorSpace:
        """ Gets a colour space with the given name and description

        Args:
            name: The name of the colour space
            description: The description of the colour space

        Returns: The colour space
        """
        family = family if family else self.family_display
        display_colour_space = ocio.ColorSpace(ocio.REFERENCE_SPACE_DISPLAY)
        display_colour_space.setName(name)
        display_colour_space.setFamily(family)
        display_colour_space.setEncoding(encoding)
        display_colour_space.setBitDepth(ocio.BIT_DEPTH_F32)
        display_colour_space.setDescription(description)
        display_colour_space.setAllocation(ocio.Allocation.ALLOCATION_UNIFORM)
        return display_colour_space

    def _get_colour_space(
            self, name: str, description: str,
            encoding: str = encoding_scene_linear, family: str = "") -> ocio.ColorSpace:
        """ Gets a colour space with the given name and description

        Args:
            name: The name of the colour space
            description: The description of the colour space

        Returns: The colour space
        """
        family = family if family else self.family_open_vp_cal
        colour_space = ocio.ColorSpace(ocio.REFERENCE_SPACE_SCENE)
        colour_space.setName(name)
        colour_space.setFamily(family)
        colour_space.setEncoding(encoding)
        colour_space.setBitDepth(ocio.BIT_DEPTH_F32)
        colour_space.setDescription(description)
        return colour_space

    def _get_ocio_config_colour_spaces_for_patch_generation(self, led_wall_settings,
                                                            preview_export_filter=True,
                                                            export_lut_for_aces_cct=False) -> LedWallColourSpaces:
        """ Gets the OCIO colour spaces for patch generation

        Args:
            led_wall_settings: the LED wall settings we want the colour spaces for

        Returns: The target_gamut_only, target_gamut_and_transfer_function and transfer_function_only colour spaces

        """
        led_wall_colour_spaces = LedWallColourSpaces()
        led_wall_colour_spaces.led_wall_settings = led_wall_settings

        # Add Target Gamut Only Colour Space
        led_wall_colour_spaces.target_gamut_cs = self.get_target_gamut_only_cs(led_wall_settings)

        # Add Transfer Function Only Colour Space (Needs to be in a colour space so oiio can apply it)
        led_wall_colour_spaces.transfer_function_only_cs = self.get_transfer_function_only_cs(led_wall_settings)

        # Add Target Gamut Colour Space And Transfer Function
        led_wall_colour_spaces.target_with_inv_eotf_cs = self.get_target_gamut_and_transfer_function_cs(
            led_wall_settings)

        # View Transform
        led_wall_colour_spaces.pre_calibration_view_transform = self.get_pre_calibration_view_transform_vt(led_wall_settings)

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
            family=self.family_display
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
    def get_calibration_space_metadata(led_wall_settings: LedWallSettings) -> [str, str]:
        """ Get the calibration colour space name

        Args:
            led_wall_settings: The LED wall settings we want the colour space names for

        Returns: The calibration colour space name

        """
        calc_order = CalculationOrder.CO_EOTF_CS_STRING
        if led_wall_settings.calculation_order == CalculationOrder.CO_CS_EOTF:
            calc_order = CalculationOrder.CO_CS_EOTF_STRING
        calibration_cs_name = (f"Calibration CSC - {led_wall_settings.name} - "
                               f"{led_wall_settings.native_camera_gamut} - "
                               f"{calc_order}")

        clf_name = (f"EOTF Correction 1D - {led_wall_settings.name} - "
                               f"{led_wall_settings.native_camera_gamut} - "
                               f"{calc_order}")

        return calibration_cs_name, clf_name

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

    def get_pre_calibration_view_transform_vt(self, led_wall_settings: LedWallSettings) -> ocio.ViewTransform:
        """ Get the OCIO view transform for pre-calibration

        Args:
            led_wall_settings: The LED wall settings we want the view transform for

        Returns: The OCIO view transform for pre-calibration

        """
        pre_calibration_view_transform_name = "Pre-Calibration - Default Target"
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
            name, description, encoding=self.encoding_hdr_video, family=self.family_open_vp_cal_input)

        inverse_eotf_group_transform = self.create_inverse_eotf_group(str(led_wall_settings.target_eotf))
        target_gamut_and_tf_cs.setTransform(inverse_eotf_group_transform, ocio.COLORSPACE_DIR_FROM_REFERENCE)

        ref_to_target_matrix_transform = self.get_reference_to_target_matrix(
            led_wall_settings
        )

        inverse_eotf_group_transform.prependTransform(ref_to_target_matrix_transform)
        target_gamut_and_tf_cs.setTransform(inverse_eotf_group_transform, ocio.COLORSPACE_DIR_FROM_REFERENCE)
        return target_gamut_and_tf_cs

    def create_inverse_eotf_group(self, tgt_eotf: str) -> ocio.GroupTransform:
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
                        gamma=[2.4, 2.4, 2.4, 2.4], offset=[0.055, 0.055, 0.055, 0.055],
                        direction=ocio.TransformDirection.TRANSFORM_DIR_INVERSE,
                    )
                )
            elif tgt_eotf == EOTF.EOTF_HLG:
                cst = ocio.ColorSpaceTransform(
                    src="ACES2065-1",
                    dst="HLG to Linear - 0 - 100"
                )
                inverse_eotf_group_transform.appendTransform(cst)

                # TODO when we migrate to OCIO 2.4 when its widly supported
                # inverse_eotf_group_transform.appendTransform(
                #     ocio.BuiltinTransform(
                #         "CURVE - HLG-OETF-INVERSE",
                #         direction=ocio.TransformDirection.TRANSFORM_DIR_INVERSE,
                #     )
                # )
            else:
                raise RuntimeError("Unknown EOTF: " + tgt_eotf)
        return inverse_eotf_group_transform

    @staticmethod
    def create_hlg_to_linear_colorspace(cube_path: str) -> ocio.ColorSpace:
        """
        Return an OCIO ColorSpace that converts BT.2100 HLG (OETF) to a
        scene-referred linear reference space by means of an external *.cube* LUT.

        Parameters
        ----------
        cube_path : str
            Absolute or config-relative path to the 1D/3D LUT file
            (e.g. "luts/HLG_to_Linear.cube").

        Returns
        -------
        ocio.ColorSpace
            A fully populated ColorSpace object ready to be added to an OCIO
            Config via `config.addColorSpace()`.
        """
        # 1. Create the colour space container
        cs = ocio.ColorSpace(name="HLG to Linear - 0 - 100")
        cs.setFamily("HLG")
        cs.setDescription(
            "Converts ITU-R BT.2100 HLG OETF to scene-linear using external LUT"
        )
        cs.setBitDepth(ocio.BIT_DEPTH_F32)  # or BIT_DEPTH_F16 for half-float
        cs.setAllocation(ocio.Allocation.ALLOCATION_UNIFORM)

        group = ocio.GroupTransform()
        lut = ocio.FileTransform()
        lut.setSrc(cube_path)
        lut.setInterpolation(ocio.INTERP_LINEAR)
        lut.setDirection(ocio.TransformDirection.TRANSFORM_DIR_FORWARD)
        group.appendTransform(lut)

        # Calculated to take the peak output in linear space to 10
        scale = 0.83334
        rgb_scale_matrix = np.eye(3) * scale

        scaling_matrix = ocio.MatrixTransform(
            ocio_utils.numpy_matrix_to_ocio_matrix(rgb_scale_matrix.tolist()),
            direction=ocio.TransformDirection.TRANSFORM_DIR_FORWARD
        )
        group.appendTransform(scaling_matrix)


        cs.setTransform(group, ocio.COLORSPACE_DIR_TO_REFERENCE)

        return cs

    def get_transfer_function_only_cs(self, led_wall_settings: LedWallSettings) -> ColorSpace:
        """ Get the transfer function only colour space for the given led wall

        Args:
            led_wall_settings: The LED wall settings we want the colour space for

        Returns: The transfer function only colour space

        """
        name, description = self.transfer_function_only_cs_metadata(led_wall_settings)
        transfer_function_only_cs = self._get_colour_space(
            name, description, encoding=self.encoding_hdr_video, family=self.family_open_vp_cal_utility)

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
        eotf_name = "OpenVPCal_sRGB" \
            if led_wall_settings.target_eotf == EOTF.EOTF_SRGB else led_wall_settings.target_eotf
        transfer_function_only_cs_name = f"{eotf_name} - Curve"
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

        target_gamut_only_cs_name = f"{target_color_space.name} - Linear"
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
            name, description, family=self.family_open_vp_cal_input)

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
        reference_colour_space = RGB_COLOURSPACES[led_wall_settings.project_settings.reference_gamut]
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
                                     preview_export_filter: bool = True,
                                     export_lut_for_aces_cct: bool = False) -> LedWallColourSpaces:
        """ Gets The OpenVPCal Colour Spaces we need to write to disk as an ocio config

        Args:
            led_wall_settings: The LED wall settings we want the colour spaces for
            preview_export_filter: Whether we want to write out the preview clf or not

        Returns: The colour spaces for the given LED wall settings

        """
        if not led_wall_settings:
            raise ValueError("No LED Wall Settings Provided")

        led_wall_colour_spaces = LedWallColourSpaces()
        led_wall_colour_spaces.led_wall_settings = led_wall_settings
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
        led_wall_colour_spaces.pre_calibration_view_transform = self.get_pre_calibration_view_transform_vt(led_wall_settings)

        # View Transform
        led_wall_colour_spaces.view_transform = self.get_post_calibration_view_transform(led_wall_settings)

        # Display Colour Space
        led_wall_colour_spaces.display_colour_space_cs = self.get_display_colour_space(led_wall_settings)

        # Add Transfer Function Only Colour Space (Needs to be in a colour space so oiio can apply it)
        led_wall_colour_spaces.transfer_function_only_cs = self.get_transfer_function_only_cs(led_wall_settings)

        if export_lut_for_aces_cct:
            reference_gamut = led_wall_settings.project_settings.reference_gamut
            led_wall_colour_spaces.aces_cct_view_transform = self.get_aces_cct_view_transform(reference_gamut)
            led_wall_colour_spaces.aces_cct_calibration_view_transform = self.get_aces_cct_calibration_view_transform(
                led_wall_settings)
            led_wall_colour_spaces.aces_cct_display_colour_space_cs = self.get_aces_cct_display_colour_space()

        if led_wall_settings.target_eotf == EOTF.EOTF_ST2084:
            soft, med, hard = self.get_rolloff_look(led_wall_settings)
            led_wall_colour_spaces.rolloff_look_soft = soft
            led_wall_colour_spaces.rolloff_view_soft = self.get_post_calibration_view_transform_rolloff(led_wall_settings, soft.getName())

            led_wall_colour_spaces.rolloff_look_medium = med
            led_wall_colour_spaces.rolloff_view_medium = self.get_post_calibration_view_transform_rolloff(led_wall_settings, med.getName())

            led_wall_colour_spaces.rolloff_look_hard = hard
            led_wall_colour_spaces.rolloff_view_hard = self.get_post_calibration_view_transform_rolloff(led_wall_settings, hard.getName())


        return led_wall_colour_spaces

    def get_aces_cct_display_colour_space(self) -> ocio.ColorSpace:
        """ Gets a display colour space for ACEScct, whilst not used for display it is used to bake
            luts which go via a ACEScct

        Returns: The ACEScct display colour space

        """
        aces_cct_display_colour_space = self._get_display_colour_space(
            "ACES_output",
            "An ACEScct output",
            encoding=self.encoding_log,

        )
        return aces_cct_display_colour_space

    def get_aces_cct_calibration_view_transform_metadata(self, led_wall_settings: LedWallSettings) -> tuple[str, str]:
        """ The metadata for the ACEScct calibrated view transform

        Args:
            led_wall_settings: The LED wall settings we want the metadata for

        Returns: The name and the description

        """
        view_transform_description = "An ACEScct view output, with the OpenVPCal calibration applied"
        _, view_transform_name = self.get_post_calibration_view_transform_metadata(led_wall_settings)
        return view_transform_name + "_ACEScct", view_transform_description

    def get_aces_cct_calibration_view_transform(self, led_wall_settings: LedWallSettings) -> ocio.ViewTransform:
        """ Returns the ACEScct calibrated view transform, which we use for baking luts whcih need to go via aces cct

        Args:
            led_wall_settings: The LED wall settings we want the view transform for

        Returns: The ACEScct calibrated view transform

        """
        view_transform_name, view_transform_description = self.get_aces_cct_calibration_view_transform_metadata(
            led_wall_settings)

        calibration_name, clf_name = self.get_calibration_space_metadata(led_wall_settings)

        view_transform = self._get_view_transform(view_transform_name, view_transform_description)
        group = ocio.GroupTransform()
        group.appendTransform(
            ocio.ColorSpaceTransform(
                src=led_wall_settings.project_settings.reference_gamut,
                dst=calibration_name
            )
        )
        group.appendTransform(
            ocio.ColorSpaceTransform(
                src=led_wall_settings.project_settings.reference_gamut,
                dst=constants.CameraColourSpace.CS_ACES_CCT
            )
        )

        view_transform.setTransform(group, ocio.ViewTransformDirection.VIEWTRANSFORM_DIR_FROM_REFERENCE)
        return view_transform

    def get_aces_cct_view_transform(self, reference_gamut) -> ocio.ViewTransform:
        """ Get the ACEScct view transform which we use for baking luts that need to go via ACEScct

        Args:
            reference_gamut: The reference gamut we want to use for the view transform

        Returns: The ACEScct view transform

        """
        view_transform_name = "ACEScct_view"
        view_transform_description = "An ACEScct view output"
        view_transform = self._get_view_transform(view_transform_name, view_transform_description)
        cs_transform = ocio.ColorSpaceTransform(
                src=reference_gamut, dst=constants.CameraColourSpace.CS_ACES_CCT
            )

        view_transform.setTransform(cs_transform, ocio.ViewTransformDirection.VIEWTRANSFORM_DIR_FROM_REFERENCE)
        return view_transform

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
        calibration_cs, clf_name = self.get_calibration_cs(led_wall_settings, results)
        group = ocio.GroupTransform()
        group.appendTransform(self.get_reference_to_target_matrix(led_wall_settings))
        group.appendTransform(
            ocio.MatrixTransform(
                numpy_matrix_to_ocio_matrix(
                    results[constants.Results.CAMERA_WHITE_BALANCE_MATRIX]
                )
            )
        )

        calibration_preview_cs = self.get_calibration_preview_cs(led_wall_settings)

        group_preview = ocio.GroupTransform()
        group_preview.appendTransform(
            self.get_reference_to_target_matrix(led_wall_settings)
        )

        group_preview.appendTransform(
            ocio.MatrixTransform(
                numpy_matrix_to_ocio_matrix(
                    results[constants.Results.CAMERA_WHITE_BALANCE_MATRIX])
            ),
        )

        EOTF_CS_string = CalculationOrder.CO_EOTF_CS_STRING
        CS_EOTF_string = CalculationOrder.CO_CS_EOTF_STRING
        if results[Results.CALCULATION_ORDER] == CalculationOrder.CO_EOTF_CS:

            # matrix transform to screen colour space
            ocio_utils.populate_ocio_group_transform_for_CO_EOTF_CS(
                clf_name, group, self._output_folder, results)

            if preview_export_filter:
                ocio_utils.populate_ocio_group_transform_for_CO_CS_EOTF(
                    "_".join([calibration_preview_cs.getName(), CS_EOTF_string]),
                    group_preview,
                    self._output_folder, results
                )

        elif results[Results.CALCULATION_ORDER] == CalculationOrder.CO_CS_EOTF:

            ocio_utils.populate_ocio_group_transform_for_CO_CS_EOTF(
                clf_name, group,
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

    def get_post_calibration_view_transform_rolloff(self, led_wall_settings: LedWallSettings, look_name) -> ocio.ViewTransform:
        """ Get the OCIO view transform for post-calibration

        Args:
            led_wall_settings: The LED wall settings we want the view transform for

        Returns: The OCIO view transform for post-calibration

        """
        view_transform_description, view_transform_name = self.get_post_calibration_view_transform_metadata(
            led_wall_settings)

        view_transform_name = f"{view_transform_name} - {look_name}"
        view_transform_description = view_transform_description + f" With Rolloff {look_name}"

        view_transform = self._get_view_transform(view_transform_name, view_transform_description)
        group = ocio.GroupTransform()
        look_trans = ocio.LookTransform(
            src=led_wall_settings.project_settings.reference_gamut,
            dst=led_wall_settings.project_settings.reference_gamut,
            looks=look_name,
        )
        group.appendTransform(look_trans)

        name, clf_name = self.get_calibration_space_metadata(led_wall_settings)
        group.appendTransform(
            ocio.ColorSpaceTransform(
                src=led_wall_settings.project_settings.reference_gamut, dst=name
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
        name, clf_name = self.get_calibration_space_metadata(led_wall_settings)
        group.appendTransform(
            ocio.ColorSpaceTransform(
                src=led_wall_settings.project_settings.reference_gamut, dst=name
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
        calc_order = CalculationOrder.CO_EOTF_CS_STRING
        if led_wall_settings.calculation_order == CalculationOrder.CO_CS_EOTF:
            calc_order = CalculationOrder.CO_CS_EOTF_STRING

        target_colour_space = utils.get_target_colourspace_for_led_wall(led_wall_settings)
        view_transform_name = f"Calibrated {led_wall_settings.name} - {led_wall_settings.target_gamut} - {led_wall_settings.native_camera_gamut} - {calc_order}"
        view_transform_description = f"Calibrated Output - OpenVPCal {target_colour_space.name} {led_wall_settings.native_camera_gamut} - {calc_order}"
        return view_transform_description, view_transform_name

    def get_calibration_cs(self, led_wall_settings: LedWallSettings, results: typing.Dict) -> [ColorSpace, str]:
        """ Get the calibration colour space for the given led wall

        Args:
            led_wall_settings: The LED wall settings we want the colour space for
            results: The results of the calibration we want to add into the description

        Returns: The calibration colour space and the clf name

        """
        calibration_cs_name, clf_name = self.get_calibration_space_metadata(led_wall_settings)
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
        return self._get_colour_space(calibration_cs_name, description, family=self.family_open_vp_cal_utility), clf_name

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
            preview_export_filter=True, export_lut_for_aces_cct=False) -> str:
        """ Generate an OCIO config for the necessary colour spaces and transforms retrieved by the given function

        Args:
            led_walls: The LED walls we want the colour spaces for
            colour_space_function: The function to get the colour spaces

        Returns: The file path to the ocio config we write out

        """
        reference_spaces = []
        led_walls = [led_wall for led_wall in led_walls if not led_wall.is_verification_wall]
        if not led_walls:
            raise ValueError("No LED walls found to generate OCIO config")

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
            ocio_config_reference_space_names.append(
                led_walls[0].project_settings.reference_gamut
            )

        if len(ocio_config_reference_space_names) != 1:
            raise ValueError("Multiple reference colour spaces found for the ocio config")

        colour_spaces = {}
        for led_wall in led_walls:
            led_wall_colour_spaces = colour_space_function(
                led_wall, preview_export_filter=preview_export_filter, export_lut_for_aces_cct=export_lut_for_aces_cct)
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
        if not led_walls:
            raise ValueError("No LED walls found to generate OCIO config")

        project_id = led_walls[0].project_settings.project_id

        if not output_file:
            output_file = os.path.join(
                self._output_folder,
                constants.ProjectFolders.CALIBRATION,
                self.pre_calibration_config_name
            )

        return self._generate_ocio_config(
            led_walls, self._get_ocio_config_colour_spaces_for_patch_generation,
            output_file=output_file.format(project_id=project_id), base_ocio_config=base_ocio_config,
            preview_export_filter=preview_export_filter)

    def generate_post_calibration_ocio_config(
            self, led_walls: List[LedWallSettings], output_file: str = None, base_ocio_config: str = None,
            preview_export_filter: bool = False, export_lut_for_aces_cct: bool = False) -> str:
        """ Generate an OCIO config for post-calibration with all the necessary colour spaces and transforms.

        Args:
            led_walls: The LED walls we want the colour spaces for
            output_file: The file path to the ocio config we write to disk
            base_ocio_config: The base ocio config path to use
            preview_export_filter: Whether to export the preview colour space or not
            export_lut_for_aces_cct: Whether to add the colour spaces displays and views needed to export a lut for
                ACEScct

        Returns: The file path to the ocio config we write out

        """

        if not led_walls:
            raise ValueError("No LED walls found to generate OCIO config")

        project_id = led_walls[0].project_settings.project_id

        if not output_file:
            output_file = os.path.join(
                self._output_folder,
                self.post_calibration_config_name
            )


        return self._generate_ocio_config(
            led_walls, self._get_openvpcal_colour_spaces, output_file=output_file.format(project_id=project_id), base_ocio_config=base_ocio_config,
            preview_export_filter=preview_export_filter, export_lut_for_aces_cct=export_lut_for_aces_cct
        )

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
        added_acess_cct_view_transforms = []
        added_display_colour_spaces = []
        added_acess_cct_display_colour_spaces = []
        added_target_colour_spaces = []
        pre_calibration_view_transform_added = []
        for _, lw_cs in colour_spaces.items():
            calibrated_output_name = OcioConfigWriter.get_calibrated_output_name(lw_cs)

            if lw_cs.rolloff_look_soft:
                config.addLook(lw_cs.rolloff_look_soft)
                config.addViewTransform(lw_cs.rolloff_view_soft)
                config.addSharedView(
                    lw_cs.rolloff_view_soft.getName(), lw_cs.rolloff_view_soft.getName(),
                    ocio.OCIO_VIEW_USE_DISPLAY_NAME)

            if lw_cs.rolloff_look_medium:
                config.addLook(lw_cs.rolloff_look_medium)
                config.addViewTransform(lw_cs.rolloff_view_medium)
                config.addSharedView(
                    lw_cs.rolloff_view_medium.getName(), lw_cs.rolloff_view_medium.getName(),
                    ocio.OCIO_VIEW_USE_DISPLAY_NAME)

            if lw_cs.rolloff_look_hard:
                config.addLook(lw_cs.rolloff_look_hard)
                config.addViewTransform(lw_cs.rolloff_view_hard)
                config.addSharedView(
                    lw_cs.rolloff_view_hard.getName(), lw_cs.rolloff_view_hard.getName(),
                    ocio.OCIO_VIEW_USE_DISPLAY_NAME)

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

            if lw_cs.aces_cct_view_transform:
                if lw_cs.aces_cct_view_transform.getName() not in added_view_transforms:
                    config.addViewTransform(lw_cs.aces_cct_view_transform)

            if lw_cs.aces_cct_calibration_view_transform:
                if lw_cs.aces_cct_calibration_view_transform.getName() not in added_acess_cct_view_transforms:
                    config.addViewTransform(lw_cs.aces_cct_calibration_view_transform)
                    added_acess_cct_view_transforms.append(lw_cs.aces_cct_calibration_view_transform.getName())

            if lw_cs.calibration_cs:
                if lw_cs.calibration_cs.getName() not in added_colour_spaces:
                    config.addColorSpace(lw_cs.calibration_cs)
                    added_colour_spaces.append(lw_cs.calibration_cs.getName())

            if lw_cs.display_colour_space_cs:
                if lw_cs.display_colour_space_cs.getName() not in added_display_colour_spaces:
                    config.addColorSpace(lw_cs.display_colour_space_cs)
                    added_display_colour_spaces.append(lw_cs.display_colour_space_cs.getName())
                    config.addDisplayView(lw_cs.display_colour_space_cs.getName(), "Raw", "Raw")

            if lw_cs.aces_cct_display_colour_space_cs:
                if lw_cs.aces_cct_display_colour_space_cs.getName() not in added_acess_cct_display_colour_spaces:
                    config.addColorSpace(lw_cs.aces_cct_display_colour_space_cs)
                    added_acess_cct_display_colour_spaces.append(lw_cs.aces_cct_display_colour_space_cs.getName())
                    config.addDisplayView(lw_cs.aces_cct_display_colour_space_cs.getName(), "Raw", "Raw")

            # Adds to the displays: section of the config
            if lw_cs.display_colour_space_cs and lw_cs.view_transform:
                config.addDisplaySharedView(lw_cs.display_colour_space_cs.getName(),
                                            calibrated_output_name)
                if lw_cs.rolloff_view_soft:
                    config.addDisplaySharedView(lw_cs.display_colour_space_cs.getName(), lw_cs.rolloff_view_soft.getName())

                if lw_cs.rolloff_view_medium:
                    config.addDisplaySharedView(lw_cs.display_colour_space_cs.getName(), lw_cs.rolloff_view_medium.getName())

                if lw_cs.rolloff_view_hard:
                    config.addDisplaySharedView(lw_cs.display_colour_space_cs.getName(), lw_cs.rolloff_view_hard.getName())


            if lw_cs.aces_cct_display_colour_space_cs and lw_cs.aces_cct_view_transform:
                config.addDisplaySharedView(
                    lw_cs.aces_cct_display_colour_space_cs.getName(), lw_cs.aces_cct_view_transform.getName()
                )

            if lw_cs.view_transform:
                config.addSharedView(
                    calibrated_output_name, lw_cs.view_transform.getName(), ocio.OCIO_VIEW_USE_DISPLAY_NAME)

                # Update the active_views part of the config
                active_views = config.getActiveViews()
                comps = active_views.split(",")
                if calibrated_output_name not in comps:
                    comps.insert(0, calibrated_output_name)
                    if lw_cs.rolloff_view_soft:
                        if lw_cs.rolloff_view_soft.getName() not in comps:
                            comps.insert(1, lw_cs.rolloff_view_soft.getName())
                    if lw_cs.rolloff_view_medium:
                        if lw_cs.rolloff_view_medium.getName() not in comps:
                            comps.insert(2, lw_cs.rolloff_view_medium.getName())
                    if lw_cs.rolloff_view_hard:
                        if lw_cs.rolloff_view_hard.getName() not in comps:
                            comps.insert(3, lw_cs.rolloff_view_hard.getName())

                    active_views = ",".join(comps)
                    config.setActiveViews(active_views)

            if lw_cs.aces_cct_view_transform:
                config.addSharedView(
                    lw_cs.aces_cct_view_transform.getName(), lw_cs.aces_cct_view_transform.getName(), ocio.OCIO_VIEW_USE_DISPLAY_NAME)

                active_views = config.getActiveViews()
                active_views += f", {lw_cs.aces_cct_view_transform.getName()}"
                config.setActiveViews(active_views)

            if lw_cs.aces_cct_calibration_view_transform:
                config.addSharedView(
                    lw_cs.aces_cct_calibration_view_transform.getName(),
                    lw_cs.aces_cct_calibration_view_transform.getName(), ocio.OCIO_VIEW_USE_DISPLAY_NAME)

                active_views = config.getActiveViews()
                active_views += f", {lw_cs.aces_cct_calibration_view_transform.getName()}"
                config.setActiveViews(active_views)

        for added_display_colour_space in added_display_colour_spaces:
            config.addDisplaySharedView(added_display_colour_space, OcioConfigWriter.pre_calibration_output)

            active_displays = config.getActiveDisplays()
            comps = active_displays.split(",")
            if added_display_colour_space not in comps:
                comps.insert(0, added_display_colour_space)
                active_displays = ",".join(comps)
                config.setActiveDisplays(active_displays)

        for added_acess_cct_display_colour_space in added_acess_cct_display_colour_spaces:
            config.addDisplaySharedView(added_acess_cct_display_colour_space, added_acess_cct_view_transforms[0])

        if pre_calibration_view_transform_added:
            config.addSharedView(
                OcioConfigWriter.pre_calibration_output, pre_calibration_view_transform_added[0],
                ocio.OCIO_VIEW_USE_DISPLAY_NAME
            )

            active_views = config.getActiveViews()
            comps = active_views.split(",")
            if OcioConfigWriter.pre_calibration_output not in comps:
                comps.insert(1, OcioConfigWriter.pre_calibration_output)
                active_views = ",".join(comps)
                config.setActiveViews(active_views)

        # Set the search path so its relative to the ocio config folder
        config.setSearchPath("./")

        filename = os.path.abspath(filename)
        parent_dir = os.path.dirname(filename)
        if parent_dir:
            os.makedirs(parent_dir, exist_ok=True)

        # TODO Ensure we copy the HLG LUT if we are using HLG, this can all go away once we can migrate
        # TODO to OCIO 2.4 configs widley
        for name, cs in colour_spaces.items():
            if cs.led_wall_settings.target_eotf == constants.EOTF.EOTF_HLG:
                hlg_cube = ResourceLoader.hlg_to_linear_cube()
                hlg_cube_name = os.path.basename(hlg_cube)
                output_lut_file_name = os.path.join(parent_dir, hlg_cube_name)
                shutil.copy(hlg_cube, output_lut_file_name)

                cs = OcioConfigWriter.create_hlg_to_linear_colorspace(hlg_cube_name)
                config.addColorSpace(cs)
                break


        with open(filename, "w", encoding="utf-8") as file:
            file.write(config.serialize())

        return filename

    @staticmethod
    def get_calibrated_output_name(lw_cs: LedWallColourSpaces) -> str:
        """
        Get the name of the calibrated output for the view transform
        """
        calc_order = CalculationOrder.CO_EOTF_CS_STRING
        if lw_cs.led_wall_settings.calculation_order == CalculationOrder.CO_CS_EOTF:
            calc_order = CalculationOrder.CO_CS_EOTF_STRING
        calibrated_output_name = (f"{OcioConfigWriter.calibrated_output} - "
                                  f"{lw_cs.led_wall_settings.name} - "
                                  f"{lw_cs.led_wall_settings.target_gamut} - "
                                  f"{lw_cs.led_wall_settings.native_camera_gamut} - "
                                  f"{calc_order}")
        return calibrated_output_name

    def get_rolloff_look(self, led_wall_settings: LedWallSettings):
        soft = ocio_utils.create_rolloff_look(
            led_wall_settings.target_max_lum_nits,
            led_wall_settings.project_settings.content_max_lum,
            prefix="Soft",
            rolloff_start=0.7
        )

        medium = ocio_utils.create_rolloff_look(
            led_wall_settings.target_max_lum_nits,
            led_wall_settings.project_settings.content_max_lum,
            prefix="Medium",
            rolloff_start=0.8
        )

        hard = ocio_utils.create_rolloff_look(
            led_wall_settings.target_max_lum_nits,
            led_wall_settings.project_settings.content_max_lum,
            prefix="Hard",
            rolloff_start=0.9
        )
        return soft, medium, hard

