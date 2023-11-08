import unittest
import colour
import numpy as np

import open_vp_cal.core.calibrate as calibrate

from open_vp_cal.core import constants, utils
from open_vp_cal.core.constants import (
    CalculationOrder,
)
from test_utils import TestProject


class TestCalibrate(TestProject):
    tolerance = 0.0001

    # TODO Need to re implement these unit tests with new intermediate data
    # def test_chromatic_adaptation(self):
    #     samples = self.get_samples(self.led_wall)
    #     ref_cs = colour.RGB_COLOURSPACES[self.led_wall.input_plate_gamut]
    #     matrix = calibrate.white_point_adaptation(
    #         grey_meas=samples[Measurements.GREY],
    #         working_cs=ref_cs,
    #         cat=test_set.cat,
    #     )
    #     adapted_wp = matrix @ samples[Measurements.GREY]
    #     # TODO: We are comparing a matrix from XYZ to XYZ to a matrix from RGB to RGB. Fix it and lower tolerance
    #     self.assertTrue(
    #         np.allclose(
    #             a=matrix, b=results[Results.WHITE_BALANCE_MATRIX], atol=0.01
    #         )
    #     )
    #     self.assertTrue(
    #         np.allclose(
    #             a=adapted_wp,
    #             b=intermediates[Intermediates.ADAPTED_WP],
    #             atol=self.tolerance,
    #         )
    #     )
    #
    # def test_eotf_correction(self):
    #     lut_r, lut_g, lut_b, _, _ = calibrate.eotf_correction_calculation(
    #         test_set.intermediates[Intermediates.GREY_RAMP_SCREEN],
    #         test_set.samples[Measurements.GREY_RAMP_SIGNAL],
    #     )
    #     self.assertTrue(
    #         np.allclose(
    #             a=lut_r, b=test_set.results[Results.LUT_R], atol=test_set.tolerance
    #         )
    #     )
    #     self.assertTrue(
    #         np.allclose(
    #             a=lut_g, b=test_set.results[Results.LUT_G], atol=test_set.tolerance
    #         )
    #     )
    #     self.assertTrue(
    #         np.allclose(
    #             a=lut_b, b=test_set.results[Results.LUT_B], atol=test_set.tolerance
    #         )
    #     )
    #
    # def test_extract_cs(self):
    #     ref_cs = colour.RGB_COLOURSPACES[test_set.reference_cs]
    #     camera_cs = colour.RGB_COLOURSPACES[constants.CameraColourSpace.ARRI_WIDE_GAMUT_3]
    #
    #     primaries_camera_gamut = [
    #         [0.102772, 0.024514, 0.017269],
    #         [0.049771, 0.130678, 0.011766],
    #         [0.028142, 0.021454, 0.111558],
    #     ]
    #     grey_ref = [0.193445, 0.186562, 0.155536]
    #
    #     cat = CAT.CAT_CAT02
    #
    #     # Test that grey (in reference space) is mapped to neutral in screen space
    #
    #     screen_cs, target_to_screen_matrix = calibrate.extract_screen_cs(
    #         primaries_measurements=primaries_camera_gamut,
    #         primaries_saturation=0.7,
    #         white_point_measurements=grey_ref,
    #         target_cs=ref_cs,
    #         camera_native_cs=camera_cs,
    #         cs_cat=cat,
    #     )
    #     # TODO: replace with a quantitative test
    #
    # def test_gamut_compression(self):
    #     ref_cs = colour.RGB_COLOURSPACES[self.led_wall.input_plate_gamut]
    #     tgt_cs = colour.RGB_COLOURSPACES[self.led_wall.target_gamut]
    #     primaries = np.asarray(test_set.intermediates[Intermediates.SCREEN_PRIMARIES])
    #     primaries_XYZ = np.apply_along_axis(
    #         lambda rgb: ref_cs.matrix_RGB_to_XYZ.dot(rgb), 1, primaries
    #     )
    #     primaries_xy = colour.XYZ_to_xy(primaries_XYZ)
    #     screen_cs = colour.RGB_Colourspace(
    #         name="screen",
    #         primaries=primaries_xy,
    #         whitepoint=ref_cs.whitepoint,
    #         use_derived_matrix_RGB_to_XYZ=True,
    #         use_derived_matrix_XYZ_to_RGB=True,
    #     )
    #     max_distances = calibrate.colourspace_max_distances(
    #         source_cs=tgt_cs,
    #         destination_cs=screen_cs,
    #         cat=test_set.cat,
    #         shadow_rolloff=test_set.shadow_rolloff,
    #     )
    #     self.assertTrue(
    #         np.allclose(
    #             a=max_distances,
    #             b=test_set.results[Results.MAX_DISTANCES],
    #             atol=test_set.tolerance,
    #         )
    #     )

    def test_run(self):
        samples = self.get_samples(self.led_wall)
        reference_samples = self.get_reference_samples(self.led_wall)

        target_colour_space = utils.get_target_colourspace_for_led_wall(self.led_wall)
        result = calibrate.run(measured_samples=samples, reference_samples=reference_samples,
                               input_plate_gamut=self.led_wall.input_plate_gamut,
                               native_camera_gamut=constants.CameraColourSpace.CS_ACES,
                               target_gamut=target_colour_space,
                               target_to_screen_cat=self.led_wall.target_to_screen_cat,
                               reference_to_target_cat=self.led_wall.reference_to_target_cat,
                               target_max_lum_nits=self.led_wall.target_max_lum_nits, target_EOTF=None,
                               enable_plate_white_balance=True, enable_gamut_compression=True,
                               enable_EOTF_correction=True, calculation_order=CalculationOrder.CO_CS_EOTF,
                               gamut_compression_shadow_rolloff=constants.GAMUT_COMPRESSION_SHADOW_ROLLOFF,
                               reference_wall_external_white_balance_matrix=None)

        # disable comparisons as ref data is obsolete
        # self.compare_results(result)

    # def test_apply_lut(self):
    #     lut_r, lut_g, lut_b, norm_factor, rgb_ratio = calibrate.eotf_correction_calculation(
    #         test_set.intermediates[Intermediates.GREY_RAMP_SCREEN],
    #         test_set.samples[Measurements.GREY_RAMP_SIGNAL],
    #         False,
    #     )
    #
    #     # test zero maps to zero
    #     zero = np.array(
    #         [
    #             [0, 0, 0],
    #         ]
    #     )
    #     out0 = calibrate.apply_luts(zero, lut_r, lut_g, lut_b, norm_factor, rgb_ratio)
    #
    #     self.assertTrue(
    #         np.allclose(
    #             a=zero,
    #             b=out0,
    #             atol=test_set.tolerance,
    #         )
    #     )
    #
    #     # test ramp is mapped back to linear
    #     greys_meas = test_set.intermediates[Intermediates.GREY_RAMP_SCREEN]
    #     grey_signal = np.array(test_set.samples[Measurements.GREY_RAMP_SIGNAL]).reshape(
    #         -1, 1
    #     ) @ np.array([[1, 1, 1]])
    #
    #     out_greys = calibrate.apply_luts(
    #         greys_meas,
    #         lut_r,
    #         lut_g,
    #         lut_b,
    #         norm_factor,  # rgb_ratio
    #     )
    #
    #     diff = out_greys - grey_signal
    #
    #     # TODO: handle fact that match is only expected for the higher part of the range
    #     self.assertTrue(
    #         np.allclose(
    #             a=grey_signal,
    #             b=out_greys,
    #             atol=0.001,
    #         )
    #     )

    def test_run_with_custom_colourspaces(self):
        ref_cs = colour.RGB_COLOURSPACES[constants.ColourSpace.CS_SRGB]
        tgt_cs = colour.RGB_COLOURSPACES[constants.ColourSpace.CS_SRGB]

        samples = self.get_samples(self.led_wall)
        reference_samples = self.get_reference_samples(self.led_wall)

        result = calibrate.run(measured_samples=samples, reference_samples=reference_samples, input_plate_gamut=ref_cs,
                               native_camera_gamut=constants.CameraColourSpace.RED_WIDE_GAMUT, target_gamut=tgt_cs,
                               target_to_screen_cat=self.led_wall.target_to_screen_cat,
                               reference_to_target_cat=self.led_wall.reference_to_target_cat,
                               target_max_lum_nits=self.led_wall.target_max_lum_nits, target_EOTF=None,
                               enable_plate_white_balance=True, enable_gamut_compression=True,
                               enable_EOTF_correction=True, calculation_order=CalculationOrder.CO_CS_EOTF,
                               gamut_compression_shadow_rolloff=constants.GAMUT_COMPRESSION_SHADOW_ROLLOFF,
                               reference_wall_external_white_balance_matrix=None)


    def test_run_alt_order(self):
        samples = self.get_samples(self.led_wall)
        reference_samples = self.get_reference_samples(self.led_wall)

        target_colour_space = utils.get_target_colourspace_for_led_wall(self.led_wall)
        result = calibrate.run(measured_samples=samples, reference_samples=reference_samples,
                               input_plate_gamut=self.led_wall.input_plate_gamut,
                               native_camera_gamut=constants.CameraColourSpace.RED_WIDE_GAMUT,
                               target_gamut=target_colour_space,
                               target_to_screen_cat=self.led_wall.target_to_screen_cat,
                               reference_to_target_cat=self.led_wall.reference_to_target_cat,
                               target_max_lum_nits=self.led_wall.target_max_lum_nits, target_EOTF=None,
                               enable_plate_white_balance=True, enable_gamut_compression=True,
                               enable_EOTF_correction=True, calculation_order=CalculationOrder.CO_EOTF_CS,
                               gamut_compression_shadow_rolloff=constants.GAMUT_COMPRESSION_SHADOW_ROLLOFF,
                               reference_wall_external_white_balance_matrix=None)

    def test_run_with_red_camera_gamut(self):
        samples = self.get_samples(self.led_wall)
        reference_samples = self.get_reference_samples(self.led_wall)

        target_colour_space = utils.get_target_colourspace_for_led_wall(self.led_wall)
        result = calibrate.run(measured_samples=samples, reference_samples=reference_samples,
                               input_plate_gamut=self.led_wall.input_plate_gamut,
                               native_camera_gamut=constants.CameraColourSpace.RED_WIDE_GAMUT,
                               target_gamut=target_colour_space,
                               target_to_screen_cat=self.led_wall.target_to_screen_cat,
                               reference_to_target_cat=self.led_wall.reference_to_target_cat,
                               target_max_lum_nits=self.led_wall.target_max_lum_nits, target_EOTF=None,
                               enable_plate_white_balance=True, enable_gamut_compression=True,
                               enable_EOTF_correction=True, calculation_order=CalculationOrder.CO_CS_EOTF,
                               gamut_compression_shadow_rolloff=constants.GAMUT_COMPRESSION_SHADOW_ROLLOFF,
                               reference_wall_external_white_balance_matrix=None)


class TestAvoidClipping(TestProject):

    def test_avoid_clipping(self):
        samples = self.get_samples(self.led_wall)
        reference_samples = self.get_reference_samples(self.led_wall)

        target_colour_space = utils.get_target_colourspace_for_led_wall(self.led_wall)
        result = calibrate.run(
            measured_samples=samples, reference_samples=reference_samples,
            input_plate_gamut=self.led_wall.input_plate_gamut,
            native_camera_gamut=constants.CameraColourSpace.RED_WIDE_GAMUT,
            target_gamut=target_colour_space,
            target_to_screen_cat=self.led_wall.target_to_screen_cat,
            reference_to_target_cat=self.led_wall.reference_to_target_cat,
            target_max_lum_nits=self.led_wall.target_max_lum_nits, target_EOTF=None,
            enable_plate_white_balance=True, enable_gamut_compression=True,
            enable_EOTF_correction=True, calculation_order=CalculationOrder.CO_CS_EOTF,
            gamut_compression_shadow_rolloff=constants.GAMUT_COMPRESSION_SHADOW_ROLLOFF,
            reference_wall_external_white_balance_matrix=None,
            avoid_clipping=False
        )

        result2 = calibrate.run(
            measured_samples=samples, reference_samples=reference_samples,
            input_plate_gamut=self.led_wall.input_plate_gamut,
            native_camera_gamut=constants.CameraColourSpace.RED_WIDE_GAMUT,
            target_gamut=target_colour_space,
            target_to_screen_cat=self.led_wall.target_to_screen_cat,
            reference_to_target_cat=self.led_wall.reference_to_target_cat,
            target_max_lum_nits=self.led_wall.target_max_lum_nits, target_EOTF=None,
            enable_plate_white_balance=True, enable_gamut_compression=True,
            enable_EOTF_correction=True, calculation_order=CalculationOrder.CO_CS_EOTF,
            gamut_compression_shadow_rolloff=constants.GAMUT_COMPRESSION_SHADOW_ROLLOFF,
            reference_wall_external_white_balance_matrix=None,
            avoid_clipping=True
        )

        no_clipping_primaries = result[constants.Results.POST_CALIBRATION_SCREEN_PRIMARIES]
        no_clipping_whitepoint = result[constants.Results.POST_CALIBRATION_SCREEN_WHITEPOINT]

        clipping_primaries = result2[constants.Results.POST_CALIBRATION_SCREEN_PRIMARIES]
        clipping_whitepoint = result2[constants.Results.POST_CALIBRATION_SCREEN_WHITEPOINT]

        self.assertTrue(np.allclose(no_clipping_primaries, clipping_primaries, atol=0.00001))
        self.assertTrue(np.allclose(no_clipping_whitepoint, clipping_whitepoint, atol=0.00001))




