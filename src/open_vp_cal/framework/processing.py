"""
Module which contains the Processing class, which is responsible for taking in the project settings and a sequence
loader, and processing the analysis of the images and producing the resulting ocio configs
"""
import json
import os
import tempfile
import threading
from typing import Union, Tuple, List, Dict


from colour import RGB_Colourspace

import open_vp_cal.framework.utils as framework_utils
from open_vp_cal.core import calibrate, constants, utils, ocio_utils, ocio_config
from open_vp_cal.imaging import macbeth, imaging_utils
from open_vp_cal.core.constants import DEFAULT_PROJECT_SETTINGS_NAME, Results
from open_vp_cal.core.resource_loader import ResourceLoader
from open_vp_cal.core.structures import ProcessingResults
from open_vp_cal.framework.generation import PatchGeneration
from open_vp_cal.led_wall_settings import LedWallSettings
from open_vp_cal.framework.identify_separation import IdentifySeparation
from open_vp_cal.project_settings import ProjectSettings
from open_vp_cal.framework.sample_patch import SamplePatch, SampleRampPatches, MacBethSample
from open_vp_cal.framework.auto_roi import AutoROI, AutoROIResults


class Processing:
    """
    Class responsible for taking project settings and a sequence loader, processing the image analysis, and
    producing the resulting OCIO configurations.
    """
    def __init__(self, led_wall_settings: LedWallSettings):
        """ Initialize an instance of Processing.

        Args:
            led_wall_settings: The LED wall settings to use for the processing
        """
        self.led_wall = led_wall_settings
        self._samples = {}
        self._reference_samples = {}
        self._sample_frames = []
        self._reference_frames = []
        self._generation = PatchGeneration(self.led_wall, (200, 200))

    def get_max_white_samples(self, separation_results):
        """ Get the max white samples

        :param separation_results: Separation results
        :return: Sample results
        """
        results = self._get_samples(separation_results, constants.PATCHES.MAX_WHITE)
        self._samples[constants.Measurements.MAX_WHITE] = results[0].samples
        return results

    def get_macbeth_samples(self, separation_results):
        """
            Get macbeth chart samples for each of the swatches

        :param separation_results: Separation results
        :return: Sample results
        """
        sample_patch = MacBethSample(
            self.led_wall, separation_results
        )
        results = sample_patch.run()
        self._samples[constants.Measurements.MACBETH] = results[0].samples
        colour_space = utils.get_target_colourspace_for_led_wall(self.led_wall)
        rgb_references = macbeth.get_rgb_references_for_color_checker(colour_space, illuminant=None)
        peak_lum = self.led_wall.target_max_lum_nits * 0.01
        rgb_references = rgb_references * peak_lum
        self._reference_samples[constants.Measurements.MACBETH] = rgb_references.tolist()

        for sample_result in results[0].samples[:-6]:
            self._sample_frames.append(self._generation.generate_solid_patch(sample_result)[0])

        for reference_patch in rgb_references[:-6]:
            self._reference_frames.append(self._generation.generate_solid_patch(reference_patch)[0])
        return results

    def get_additional_samples_data(self) -> Tuple[Dict, Dict]:
        """ Gets the additional samples data from the processing, mainly the primary saturation for the LED wall

        Returns: The samples data from the processing

        """
        self._samples[constants.Measurements.PRIMARIES_SATURATION] = self.led_wall.primaries_saturation
        self._reference_samples[constants.Measurements.PRIMARIES_SATURATION] = self.led_wall.primaries_saturation
        return self._samples, self._reference_samples

    def run_sampling(self):
        """ Runs the sampling process to extract the samples form the image sequences,
        and generates the reference swatches from the results

        """

        self.identify_separation()
        self.auto_detect_roi(self.led_wall.separation_results)

        self.get_grey_samples(self.led_wall.separation_results)
        self.get_primaries_samples(self.led_wall.separation_results)
        self.get_eotf_ramp_samples(self.led_wall.separation_results)
        self.get_eotf_ramp_signals()
        self.get_macbeth_samples(self.led_wall.separation_results)
        self.get_max_white_samples(self.led_wall.separation_results)
        samples, reference_samples = self.get_additional_samples_data()

        results = ProcessingResults()
        results.samples = samples
        results.reference_samples = reference_samples
        results.sample_buffers = self._sample_frames
        results.sample_reference_buffers = self._reference_frames

        self.led_wall.processing_results = results
        self.generate_sample_swatches()

    def analyse(self):
        """
        Runs an analysis process on the samples to generate the status of the LED wall before calibration
        """
        target_cs, target_to_screen_cat = self._analysis_prep()

        reference_wall_external_white_balance_matrix = None
        if self.led_wall.match_reference_wall and self.led_wall.use_external_white_point:
            raise ValueError("Cannot use external white point and a reference wall")

        if self.led_wall.match_reference_wall:
            if self.led_wall.reference_wall_as_wall:
                reference_wall_processing_results = self.led_wall.reference_wall_as_wall.processing_results
                if not reference_wall_processing_results:
                    raise ValueError("Reference wall has not been analysed yet")
                reference_wall_external_white_balance_matrix = reference_wall_processing_results.pre_calibration_results[
                    Results.WHITE_BALANCE_MATRIX]

        decoupled_lens_white_samples = None
        if self.led_wall.use_external_white_point:
            decoupled_lens_white_samples = imaging_utils.get_decoupled_white_samples_from_file(
                self.led_wall.external_white_point_file)

        default_wall = LedWallSettings("default")

        calibration_results = calibrate.run(
            measured_samples=self.led_wall.processing_results.samples,
            reference_samples=self.led_wall.processing_results.reference_samples,
            input_plate_gamut=self.led_wall.input_plate_gamut,
            native_camera_gamut=self.led_wall.native_camera_gamut,
            target_gamut=target_cs, target_to_screen_cat=target_to_screen_cat,
            reference_to_target_cat=default_wall.reference_to_target_cat,
            target_max_lum_nits=self.led_wall.target_max_lum_nits,
            target_EOTF=self.led_wall.target_eotf,
            enable_plate_white_balance=self.led_wall.auto_wb_source,
            enable_gamut_compression=False, enable_EOTF_correction=False,
            calculation_order=constants.CalculationOrder.CO_CS_EOTF,
            gamut_compression_shadow_rolloff=default_wall.shadow_rolloff,
            reference_wall_external_white_balance_matrix=reference_wall_external_white_balance_matrix,
            decoupled_lens_white_samples=decoupled_lens_white_samples,
            avoid_clipping=self.led_wall.avoid_clipping
        )

        self.led_wall.processing_results.pre_calibration_results = calibration_results
        return self.led_wall.processing_results

    def _analysis_prep(self) -> tuple[RGB_Colourspace, constants.CAT]:
        """ Run the steps which are needed for both calibration and the pre-calibration analysis steps

        Returns: The target colour space and the target to screen CAT

        """
        if not self.led_wall.processing_results or not self.led_wall.processing_results.samples:
            self.run_sampling()

        target_to_screen_cat = self.led_wall.target_to_screen_cat
        if target_to_screen_cat == constants.CAT.CAT_NONE:
            target_to_screen_cat = None

        return utils.get_target_colourspace_for_led_wall(self.led_wall), target_to_screen_cat

    def calibrate(self) -> ProcessingResults:
        """
        Runs an analysis process on the samples to generate the calibration results
        """
        target_cs, target_to_screen_cat = self._analysis_prep()

        reference_wall_external_white_balance_matrix = None
        if self.led_wall.match_reference_wall and self.led_wall.use_external_white_point:
            raise ValueError("Cannot use external white point and a reference wall")

        if self.led_wall.match_reference_wall:
            if self.led_wall.reference_wall_as_wall:
                reference_wall_processing_results = self.led_wall.reference_wall_as_wall.processing_results
                if not reference_wall_processing_results:
                    raise ValueError("Reference wall has not been analysed yet")
                reference_wall_external_white_balance_matrix = reference_wall_processing_results.calibration_results[
                    Results.WHITE_BALANCE_MATRIX]

        decoupled_lens_white_samples = None
        if self.led_wall.use_external_white_point:
            decoupled_lens_white_samples = imaging_utils.get_decoupled_white_samples_from_file(
                self.led_wall.external_white_point_file)

        calibration_results = calibrate.run(
            measured_samples=self.led_wall.processing_results.samples,
            reference_samples=self.led_wall.processing_results.reference_samples,
            input_plate_gamut=self.led_wall.input_plate_gamut,
            native_camera_gamut=self.led_wall.native_camera_gamut,
            target_gamut=target_cs, target_to_screen_cat=target_to_screen_cat,
            reference_to_target_cat=self.led_wall.reference_to_target_cat,
            target_max_lum_nits=self.led_wall.target_max_lum_nits,
            target_EOTF=self.led_wall.target_eotf,
            enable_plate_white_balance=self.led_wall.auto_wb_source,
            enable_gamut_compression=self.led_wall.enable_gamut_compression,
            enable_EOTF_correction=self.led_wall.enable_eotf_correction,
            calculation_order=self.led_wall.calculation_order,
            gamut_compression_shadow_rolloff=self.led_wall.shadow_rolloff,
            reference_wall_external_white_balance_matrix=reference_wall_external_white_balance_matrix,
            decoupled_lens_white_samples=decoupled_lens_white_samples,
            avoid_clipping=self.led_wall.avoid_clipping
        )

        self.led_wall.processing_results.calibration_results = calibration_results

        # We export and store the results of this in a temporary location, so we can use it for previewing the results
        temp_dir = tempfile.mkdtemp()
        self._export_calibration(
            temp_dir, [self.led_wall], ResourceLoader.ocio_config_path()
        )
        return self.led_wall.processing_results

    @staticmethod
    def _export_calibration(
            output_folder: str, led_walls: List[LedWallSettings],
            base_ocio_config: str, export_filter: bool = True,
            export_lut_for_aces_cct: bool = False) -> List[LedWallSettings]:
        """ Runs the export process to generate the OCIO configuration files, CLF and luts

        Args:
            output_folder: The folder to export into
            led_walls: The LED walls to export
            base_ocio_config: The base OCIO config to use for the ocio config export

        Returns: The LED walls with the export results stored in the wall processing results
        """
        if not os.path.exists(output_folder):
            os.makedirs(output_folder)

        results_folder = os.path.join(output_folder, constants.ProjectFolders.RESULTS)
        if not os.path.exists(results_folder):
            os.makedirs(results_folder)

        calibration_folder = os.path.join(output_folder, constants.ProjectFolders.CALIBRATION)
        if not os.path.exists(calibration_folder):
            os.makedirs(calibration_folder)

        ocio_config_output_file = os.path.join(
            calibration_folder, ocio_config.OcioConfigWriter.post_calibration_config_name
        )

        ocio_config_writer = ocio_config.OcioConfigWriter(calibration_folder)
        for led_wall in led_walls:
            samples_output_folder = os.path.join(
                results_folder, f"{led_wall.name}_samples.json"
            )
            with open(samples_output_folder, "w", encoding="utf-8") as handle:
                json.dump(led_wall.processing_results.samples, handle, indent=4)

            reference_samples_output_folder = os.path.join(
                results_folder, f"{led_wall.name}_reference_samples.json"
            )

            with open(reference_samples_output_folder, "w", encoding="utf-8") as handle:
                json.dump(led_wall.processing_results.reference_samples, handle, indent=4)

            calibration_results_file = os.path.join(
                results_folder,
                led_wall.name + "_calibration_results.json"
            )
            with open(calibration_results_file, "w", encoding="utf-8") as handle:
                json.dump(led_wall.processing_results.calibration_results, handle, indent=4)

            led_wall.processing_results.calibration_results_file = calibration_results_file

        ocio_config_writer.generate_post_calibration_ocio_config(
            led_walls, output_file=ocio_config_output_file, base_ocio_config=base_ocio_config,
            preview_export_filter=export_filter, export_lut_for_aces_cct=export_lut_for_aces_cct
        )

        for led_wall in led_walls:
            if led_wall.is_verification_wall:
                continue

            led_wall.processing_results.ocio_config_output_file = ocio_config_output_file
            if led_wall.calculation_order == constants.CalculationOrder.CO_CS_EOTF:
                calc_order_string = constants.CalculationOrder.CO_CS_EOTF_STRING
            else:
                calc_order_string = constants.CalculationOrder.CO_EOTF_CS_STRING
            if not led_wall.enable_eotf_correction:
                calc_order_string = constants.CalculationOrder.CS_ONLY_STRING

            aces_cct_desc = ""
            if export_lut_for_aces_cct:
                aces_cct_desc = "_ACES_CCT"

            lut_name = (f"{led_wall.processing_results.led_wall_colour_spaces.calibration_cs.getName()}_"
                        f"{led_wall.processing_results.led_wall_colour_spaces.display_colour_space_cs.getName()}_"
                        f"{calc_order_string}{aces_cct_desc}.cube")

            lut_output_file = os.path.join(
                calibration_folder, lut_name
            )

            if not export_lut_for_aces_cct:
                ocio_utils.bake_3d_lut(
                    led_wall.processing_results.led_wall_colour_spaces.target_with_inv_eotf_cs.getName(),
                    led_wall.processing_results.led_wall_colour_spaces.display_colour_space_cs.getName(),
                    led_wall.processing_results.led_wall_colour_spaces.view_transform.getName(),
                    ocio_config_output_file, lut_output_file
                )

            else:
                ocio_utils.bake_3d_lut(
                    constants.CameraColourSpace.CS_ACES_CCT,
                    led_wall.processing_results.led_wall_colour_spaces.aces_cct_display_colour_space_cs.getName(),
                    led_wall.processing_results.led_wall_colour_spaces.aces_cct_calibration_view_transform.getName(),
                    ocio_config_output_file, lut_output_file
                )

            led_wall.processing_results.lut_output_file = lut_output_file
        return led_walls

    @staticmethod
    def run_export(project_settings: ProjectSettings, led_walls: List[LedWallSettings]) -> List[LedWallSettings]:
        """ Runs the export process to generate the OCIO configuration files, CLF, and luts.
            We also save the project settings

        Args:
            project_settings: The project settings to use to do the export
            led_walls: The LED walls to export

        Returns: The LED walls with the export results stored in the wall processing results

        """
        walls = Processing._export_calibration(
            project_settings.export_folder,
            led_walls, project_settings.ocio_config_path, export_filter=False,
            export_lut_for_aces_cct=project_settings.export_lut_for_aces_cct
        )

        project_settings.to_json(
            os.path.join(project_settings.output_folder, DEFAULT_PROJECT_SETTINGS_NAME)
        )

        data_dict = project_settings.to_dict()
        for led_wall in walls:
            processed_data = {
                "samples": led_wall.processing_results.samples,
                "reference_samples": led_wall.processing_results.reference_samples,
            }
            data_dict[f"{led_wall.name}_processed_data"] = processed_data

        thread = threading.Thread(target=framework_utils.log_results, args=(data_dict,), daemon=True)
        thread.start()
        thread.join(timeout=5)
        return walls

    def auto_detect_roi(self, separation_results) -> Union[AutoROIResults, None]:
        """ Auto-detects the region of interest and returns the results

        :param separation_results:
        :return:
        """
        if not self.led_wall.roi:
            results = AutoROI(self.led_wall, separation_results).run()
            if not results.is_valid:
                raise ValueError("Auto ROI detection failed, no ROI detected")
            self.led_wall.roi = results.roi
            return results
        return None

    def identify_separation(self):
        """
        Identify separation in the sequence.

        :return: Separation results
        """
        if not self.led_wall.separation_results:
            identify_sep = IdentifySeparation(self.led_wall)
            separation_results = identify_sep.run()
            return separation_results
        return self.led_wall.separation_results

    def get_eotf_ramp_signals(self) -> None:
        """
        Get EOTF ramp signals.
        """
        self._samples[constants.Measurements.EOTF_RAMP_SIGNAL] = utils.get_grey_signals(
            self.led_wall.target_max_lum_nits, self.led_wall.num_grey_patches
        )
        self._reference_samples[constants.Measurements.EOTF_RAMP_SIGNAL] = utils.get_grey_signals(
            self.led_wall.target_max_lum_nits, self.led_wall.num_grey_patches
        )

    def get_eotf_ramp_samples(self, separation_results):
        """
        Get EOTF ramp samples.

        :param separation_results: Separation results
        :return: Sample results
        """
        sample_patches = SampleRampPatches(
            self.led_wall, separation_results, constants.PATCHES.EOTF_RAMPS
        )
        sample_results = sample_patches.run()

        reference_patches, reference_patch_values = self._generation.find_and_generate_patch_from_map(
            constants.PATCHES.EOTF_RAMPS
        )
        self._reference_samples[constants.Measurements.EOTF_RAMP] = [
            [value, value, value] for value in reference_patch_values
        ]
        self._reference_frames.extend(
            reference_patches
        )

        self._samples[constants.Measurements.EOTF_RAMP] = []
        for sample_result in sample_results:
            self._samples[constants.Measurements.EOTF_RAMP].append(sample_result.samples)
            self._sample_frames.append(self._generation.generate_solid_patch(sample_result.samples)[0])
        return sample_results

    def get_primaries_samples(self, separation_results):
        """
        Get primary samples.

        :param separation_results: Separation results
        :return: Tuple of red, green, and blue results
        """
        red_results = self._get_samples(separation_results, constants.PATCHES.RED_PRIMARY_DESATURATED)
        self._sample_frames.append(self._generation.generate_solid_patch(red_results[0].samples)[0])
        self._reference_samples[constants.Measurements.DESATURATED_RGB] = []

        reference_patch, reference_patch_values = self._generation.find_and_generate_patch_from_map(
            constants.PATCHES.RED_PRIMARY_DESATURATED)
        self._reference_frames.extend(reference_patch)
        self._reference_samples[constants.Measurements.DESATURATED_RGB].append(reference_patch_values)

        green_results = self._get_samples(separation_results, constants.PATCHES.GREEN_PRIMARY_DESATURATED)
        self._sample_frames.append(self._generation.generate_solid_patch(green_results[0].samples)[0])
        reference_patch, reference_patch_values = self._generation.find_and_generate_patch_from_map(
            constants.PATCHES.GREEN_PRIMARY_DESATURATED)
        self._reference_frames.extend(reference_patch)
        self._reference_samples[constants.Measurements.DESATURATED_RGB].append(reference_patch_values)

        blue_results = self._get_samples(separation_results, constants.PATCHES.BLUE_PRIMARY_DESATURATED)
        self._sample_frames.append(self._generation.generate_solid_patch(blue_results[0].samples)[0])
        reference_patch, reference_patch_values = self._generation.find_and_generate_patch_from_map(
            constants.PATCHES.BLUE_PRIMARY_DESATURATED)
        self._reference_frames.extend(reference_patch)
        self._reference_samples[constants.Measurements.DESATURATED_RGB].append(reference_patch_values)

        self._samples[constants.Measurements.DESATURATED_RGB] = [
            red_results[0].samples,
            green_results[0].samples,
            blue_results[0].samples
        ]
        return red_results, green_results, blue_results

    def get_grey_samples(self, separation_results):
        """
        Get grey samples for the 18 percent grey patch.

        :param separation_results: Separation results
        :return: Sample results
        """
        results = self._get_samples(separation_results, constants.PATCHES.GREY_18_PERCENT)
        self._samples[constants.Measurements.GREY] = results[0].samples

        self._sample_frames.append(
            self._generation.generate_solid_patch(results[0].samples)[0]
        )
        reference_patch, reference_values = self._generation.find_and_generate_patch_from_map(
            constants.PATCHES.GREY_18_PERCENT)
        self._reference_frames.extend(reference_patch)
        self._reference_samples[constants.Measurements.GREY] = reference_values

        return results

    def _get_samples(self, separation_results, patch):
        """
        Get samples for the given patch.

        :param separation_results: Separation results
        :param patch: Patch to get samples from
        :return: Sample results
        """
        sample_patch = SamplePatch(
            self.led_wall, separation_results, patch
        )
        sample_results = sample_patch.run()
        return sample_results

    def generate_sample_swatches(self) -> tuple[list["ImageBuf"], list["ImageBuf"]]:
        """ Generate sample swatches to allow us to compare the samples, to the original references which where
            sent to the wall.

            The samples are exposed up linearly, so the samples match apart from the
            gamut changes we expect to see

        Returns: Tuple of sample swatch, and reference swatch

        """
        input_gamut = self.led_wall.input_plate_gamut
        working_gamut = constants.ColourSpace.CS_ACES

        if not os.path.exists(self.led_wall.project_settings.export_folder):
            os.makedirs(self.led_wall.project_settings.export_folder)

        ocio_config_writer = ocio_config.OcioConfigWriter(self.led_wall.project_settings.export_folder)
        led_wall_for_ocio_generation = self.led_wall
        if self.led_wall.is_verification_wall:
            led_wall_for_ocio_generation = self.led_wall.verification_wall_as_wall

        generation_ocio_config_path = ocio_config_writer.generate_pre_calibration_ocio_config(
            [led_wall_for_ocio_generation]
        )

        converted_sample_buffers = []
        for img_buf in self.led_wall.processing_results.sample_buffers:
            output_img_buf = imaging_utils.apply_color_conversion(
                img_buf, str(input_gamut), working_gamut,
                color_config=generation_ocio_config_path
            )
            converted_sample_buffers.append(output_img_buf)

        converted_reference_buffers = []

        target_gamut_only_cs_name, _ = ocio_config_writer.target_gamut_only_cs_metadata(self.led_wall)
        for img_buf in self.led_wall.processing_results.sample_reference_buffers:
            output_img_buf = imaging_utils.apply_color_conversion(
                img_buf, target_gamut_only_cs_name, working_gamut,
                color_config=generation_ocio_config_path)
            converted_reference_buffers.append(output_img_buf)

        self.led_wall.processing_results.sample_buffers = converted_sample_buffers
        self.led_wall.processing_results.sample_reference_buffers = converted_reference_buffers

        return converted_sample_buffers, converted_reference_buffers
