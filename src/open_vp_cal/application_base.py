"""
This file contains the base class for the application, this class contains all the methods which are used by the
application to perform the analysis, calibration and export of the LED walls. This class is inherited by the UI and
CLI classes which implement the methods to display the results to the user.
"""
import json
import os
import tempfile
from typing import List, Dict, Tuple, Any

from open_vp_cal.core import constants, utils
from open_vp_cal.core.resource_loader import ResourceLoader
from open_vp_cal.framework.configuraton import Configuration
from open_vp_cal.framework.processing import Processing, SeparationException
from open_vp_cal.framework.utils import export_pre_calibration_ocio_config
from open_vp_cal.framework.validation import Validation
from open_vp_cal.led_wall_settings import LedWallSettings
from open_vp_cal.project_settings import ProjectSettings

from spg.projectSettings import ProjectSettings as SPGProjectSettings
from spg.main import run_spg_pattern_generator
from stageassets.ledWall import LEDWall as SPGLedWall
from stageassets.ledPanel import LEDPanel as SPGLedPanel
from stageassets.rasterMap import RasterMap as SPGRasterMap
from stageassets.rasterMap import Mapping as SPGMapping


class OpenVPCalBase:
    """
    This class contains all the methods which are used by the application to perform the analysis, calibration and
    export of the LED walls. This class is inherited by the UI and used by the CLI or directly via custom python
    scripts
    """

    def __init__(self):
        self._errors = []
        self._warnings = []
        self._infos = []

    def error_messages(self) -> list[Any]:
        """ Returns the list of error messages which have been logged
        """
        return self._errors

    def error_message(self, message) -> None:
        """ Logs an error message and stores it within the class

        Args:
            message: The message to log
        """
        self._errors.append(message)

    def warning_messages(self) -> list[Any]:
        """ Returns the list of warning messages which have been logged
        """
        return self._warnings

    def warning_message(self, message: str, yes_text: str = "Yes", no_text: str = "No") -> bool:
        """ Logs a warning message and stores it within the class

        Args:
            message: The message to log
            yes_text: The text to display on any ui which inherits this class for the yes button
            no_text: The text to display on the no button for any ui which inherits this class

        Returns:
            Whether the user has selected yes or no if implemented in an ui, otherwise returns True
        """
        self._warnings.append(message)
        return True

    def info_messages(self) -> list[Any]:
        """ Returns the list of warning messages which have been logged
        """
        return self._infos

    def info_message(self, message) -> None:
        """ Logs an info message and stores it within the class

        Args:
            message: The message to log
        """
        self._infos.append(message)

    def single_camera_across_all_wall(self, led_walls: List[LedWallSettings]) -> bool:
        """ Checks to see if all the LED walls have the same camera gamut, if they do, we return True, otherwise we
            return False

        Args:
            led_walls: The LED walls we want to check

        Returns:

        """
        camera_gamuts = {led_wall.native_camera_gamut for led_wall in led_walls}
        if len(camera_gamuts) > 1:
            message = "Multiple Camera Gamuts Detected, Would You Like To Continue?"
            if not self.warning_message(message):
                return False
        return True

    def run_pre_checks(self, led_walls: List[LedWallSettings]) -> bool:
        """ Runs the pre-checks for the analysis and calibration, we report any warnings or failures to the user.

        Args:
            led_walls: The LED walls we want to run the pre-checks on

        Returns:
            Whether we should continue with the analysis/calibration or not
        """
        led_wall_names = [led_wall.name for led_wall in led_walls]
        for led_wall in led_walls:
            if led_wall.native_camera_gamut == led_wall.target_gamut:
                message = f"Target Gamut & Native Camera Gamut Can Not Be The Same For {led_wall.name}"
                self.error_message(message)
                return False

            if not led_wall.has_valid_white_balance_options():
                message = f"Only Select 1 option from AutoWB, or Reference Wall or External White {led_wall.name}"
                self.error_message(message)
                return False

            if led_wall.native_camera_gamut == constants.CameraColourSpace.CS_ACES:
                message = f"Native Camera Gamut Should Not Be {constants.CameraColourSpace.CS_ACES} For {led_wall.name}"
                self.error_message(message)
                return False

            if led_wall.use_external_white_point:
                if not led_wall.external_white_point_file:
                    self.error_message(f"External White Point Enabled But File Not Set {led_wall.name}")
                    return False

                if not os.path.exists(led_wall.external_white_point_file):
                    self.error_message(f"External White Point File Set Does Not Exist {led_wall.name}")
                    return False

            if led_wall.match_reference_wall:
                if not led_wall.reference_wall:
                    self.error_message(f"Match Reference Wall Enabled But Not Set {led_wall.name} Not In Selection")
                    return False

                if led_wall.reference_wall not in led_wall_names:
                    self.error_message(f"Reference Wall {led_wall.reference_wall} Not In Selection")
                    return False

        if not self.single_camera_across_all_wall(led_walls):
            return False

        return True

    def analyse(self, led_walls: List[LedWallSettings]) -> bool:
        """ Runs the analysis for each of the LED walls in the selection, and performs some pre validation checks
        to ensure that the LED walls are correctly setup

        Args:
            led_walls: The LED walls we want to analyse

        Returns:
            Whether the analysis was successful or not
        """
        if not led_walls:
            message = "No Led Walls Provided"
            self.error_message(message)
            return False

        for led_wall in led_walls:
            if led_wall.processing_results:
                if led_wall.processing_results.samples:
                    message = f"Sampling Results Already Exist For {led_wall.name}, Would You Like To Overwrite?"
                    if not self.warning_message(message):
                        return False
                    break

        if not self.run_pre_checks(led_walls):
            return False

        led_walls = utils.led_wall_reference_wall_sort(led_walls)

        # We have to do these sequentially encase we are using a reference wall
        # if the separation fails inform the user to try again or that they have an issue
        for led_wall in led_walls:
            try:
                processing = Processing(led_wall)
                processing.run_sampling()
                processing.analyse()
            except SeparationException as e:
                self.error_message(f"{led_wall.name}\n{e}")
                return False
        return True

    def calibrate(self, led_walls: List[LedWallSettings]) -> bool:
        """
        Runs the calibration for each of the LED walls in the selection, and performs some pre validation checks

        Args:
            led_walls: The LED walls we want to calibrate

        Returns:
            Whether the calibration was successful or not
        """
        if not led_walls:
            message = "No Led Walls To Calibrate"
            self.error_message(message)
            return False

        for led_wall in led_walls:
            if not led_wall.processing_results:
                self.error_message(f"No Sampling Results For {led_wall.name}")
                return False

            if not led_wall.has_valid_white_balance_options():
                message = f"Only Select 1 option from AutoWB, or Reference Wall or External White {led_wall.name}"
                self.error_message(message)
                return False

        if not self.run_pre_checks(led_walls):
            return False

        led_walls = utils.led_wall_reference_wall_sort(led_walls)

        # We have to do these sequentially encase we are using a reference wall
        for led_wall in led_walls:
            processing = Processing(led_wall)
            processing.calibrate()
        return True

    def post_analysis_validations(self, led_walls: List[LedWallSettings]) -> bool:
        """ Run the validation checks on the results of the analysis, we report any warnings or failures to the user.

        Args:
            led_walls: A list of led walls we want to validate the calibration results for

        Returns:
            Whether we should continue with the analysis or not

        """
        validation = Validation()
        validation_results = []
        validation_status = constants.ValidationStatus.PASS
        for led_wall in led_walls:
            results = validation.run_validations(led_wall.processing_results.pre_calibration_results)
            for result in results:
                if result.status != constants.ValidationStatus.PASS:
                    validation_status = utils.calculate_validation_status(validation_status, result.status)
                    validation_results.append(f"{led_wall.name} - {result.name}\n{result.message}\n")

        if validation_status == constants.ValidationStatus.FAIL:
            validation_results_message = "\n".join(validation_results)
            self.error_message(f"Validation Failed:\n{validation_results_message}\n"
                               f"We Strongly Suggest To Address These Issues Before Continuing")
            return False

        if validation_status == constants.ValidationStatus.WARNING:
            validation_results_message = "\n".join(validation_results)
            if not self.warning_message(f"Validation Warning:\n{validation_results_message}",
                                        yes_text="Continue", no_text="Abort"):
                return False
        return True

    def apply_post_analysis_configuration(self, led_walls: List[LedWallSettings]) -> Dict:
        """ Runs the configuration checks on the results of the analysis, we can inform the user and from the ui or
        inheriting class apply these settings to the LED walls


        Args:
            led_walls: A list of led walls we want to run the configuration checks on

        Returns:
            A dictionary containing the configuration results for each led wall, the key is the LED wall name and the
            value is a list of tuples containing the configuration parameter and the value we have recommended
        """
        configuration = Configuration()
        configuration_messages = ["Based On The Analysis We Have Recommended The Following Settings:"]
        configuration_results = {}
        for led_wall in led_walls:
            configuration_results[led_wall.name] = []
            results = configuration.run_configuration_checks(led_wall.processing_results.pre_calibration_results)
            configuration_messages.append(f"\n{led_wall.name}")
            for result in results:
                configuration_messages.append(f"{result.param}: {result.value}")
                configuration_results[led_wall.name].append((result.param, result.value))
        self.info_message("\n".join(configuration_messages))
        return configuration_results

    def export(self, project_settings_model: ProjectSettings, led_walls: List[LedWallSettings]) -> Tuple[bool, List]:
        """ Runs the export for the given led walls, we report any warnings or failures to the user.

        Args:
            project_settings_model: The project settings model we want to export
            led_walls: A list of led walls we want to export the calibration for

        Returns:
            Whether the export was successful or not
        """
        # We need to ensure that all the walls have been analysed before we can ex
        for led_wall in led_walls:
            if not led_wall.processing_results:
                self.error_message(f"No Sampling Results For {led_wall.name}")
                return False, []

            if not led_wall.processing_results.calibration_results:
                self.error_message(f"No Analysis Results For {led_wall.name}")
                return False, []

        walls = Processing.run_export(project_settings_model, led_walls)
        return True, walls

    @staticmethod
    def generate_spg_patterns_for_led_walls(
            project_settings: ProjectSettings, led_walls: List) -> None:
        """ For the given project settings and list of led walls, generate the patterns for SPG which is used to
            evaluate and diagnose issues with the imaging chain

        Args:
            project_settings: The project settings used for the project
            led_walls: the led walls we want to generate patterns from
        """

        config_writer, ocio_config_path = export_pre_calibration_ocio_config(project_settings, led_walls)
        spg_project_settings = SPGProjectSettings()
        spg_project_settings.frame_rate = project_settings.frame_rate
        spg_project_settings.image_file_format = project_settings.file_format
        spg_project_settings.image_file_bit_depth = 10
        spg_project_settings.output_folder = os.path.join(
            project_settings.export_folder,
            constants.ProjectFolders.SPG
        )
        spg_project_settings.channel_mapping = "RGB"
        spg_project_settings.ocio_config_path = ocio_config_path
        apply_eotf_colour_transform = False
        if spg_project_settings.image_file_format != constants.FileFormats.FF_EXR:
            apply_eotf_colour_transform = True

        spg_led_walls = []
        spg_led_panels = []
        spg_raster_maps = []

        for count, led_wall in enumerate(led_walls):
            idx = count + 1

            # As this is a basic setup we default to a typical panel as we are not doing a deep dive and pixel perfect
            # match
            spg_panel = SPGLedPanel()
            spg_panel.name = f"Panel_{idx}_{led_wall.name}"
            spg_panel.manufacturer = "Unknown"
            spg_panel.panel_width = 500
            spg_panel.panel_height = 500
            spg_panel.panel_depth = 80
            spg_panel.pixel_pitch = 2.85
            spg_panel.brightness = led_wall.target_max_lum_nits
            spg_panel.refresh_rate = "3840"
            spg_panel.scan_rate = "1/8"
            spg_led_panels.append(spg_panel)

            # We create a faux led wall which is the largest which we can fit into a given resolution image
            # as we are not doing a pixel perfect diagnosis
            target_gamut_only_cs = config_writer.get_target_gamut_only_cs(led_wall)
            target_gamut_and_tf_cs = config_writer.get_target_gamut_and_transfer_function_cs(led_wall)

            # If we are not using an EXR file format, we apply the EOTF colour transform
            if not apply_eotf_colour_transform:
                target_gamut_and_tf_cs = target_gamut_only_cs

            spg_led_wall = SPGLedWall()
            spg_led_wall.gamut_only_cs_name = target_gamut_only_cs.getName()
            spg_led_wall.gamut_and_transfer_function_cs_name = target_gamut_and_tf_cs.getName()
            spg_led_wall.id = idx
            spg_led_wall.name = led_wall.name
            spg_led_wall.panel_name = spg_panel.name
            spg_led_wall.panel = spg_panel
            spg_led_wall.panel_count_width = int(project_settings.resolution_width / spg_panel.panel_resolution_width)
            spg_led_wall.panel_count_height = int(
                project_settings.resolution_height / spg_panel.panel_resolution_height
            )
            spg_led_wall.wall_default_color = utils.generate_color(led_wall.name)

            spg_led_walls.append(spg_led_wall)

            spg_mapping = SPGMapping()
            spg_mapping.wall_name = spg_led_wall.name
            spg_mapping.raster_u = 0
            spg_mapping.raster_v = 0
            spg_mapping.wall_segment_u_start = 0
            spg_mapping.wall_segment_u_end = spg_led_wall.resolution_width
            spg_mapping.wall_segment_v_start = 0
            spg_mapping.wall_segment_v_end = spg_led_wall.resolution_height
            spg_mapping.wall_segment_orientation = 0

            spg_raster_map = SPGRasterMap()
            spg_raster_map.name = f"Raster_{led_wall.name}"
            spg_raster_map.resolution_width = project_settings.resolution_width
            spg_raster_map.resolution_height = project_settings.resolution_height
            spg_raster_map.mappings = [spg_mapping]

            spg_raster_maps.append(spg_raster_map)

        spg_led_panel_json = [json.loads(spg_led_panel.to_json()) for spg_led_panel in spg_led_panels]
        spg_led_wall_json = [json.loads(spg_led_wall.to_json()) for spg_led_wall in spg_led_walls]
        spg_raster_map_json = [json.loads(spg_raster_map.to_json()) for spg_raster_map in spg_raster_maps]

        tmp_dir = tempfile.TemporaryDirectory()
        spg_led_panel_json_file = os.path.join(tmp_dir.name, "led_panel_settings.json")
        spg_led_wall_json_file = os.path.join(tmp_dir.name, "led_wall_settings.json")
        spg_raster_map_json_file = os.path.join(tmp_dir.name, "raster_map_settings.json")
        spg_project_settings_json_file = os.path.join(tmp_dir.name, "spg_project_settings.json")

        with open(spg_led_panel_json_file, 'w') as f:
            json.dump(spg_led_panel_json, f, indent=4)
        with open(spg_led_wall_json_file, 'w') as f:
            json.dump(spg_led_wall_json, f, indent=4)
        with open(spg_raster_map_json_file, 'w') as f:
            json.dump(spg_raster_map_json, f, indent=4)
        with open(spg_project_settings_json_file, 'w') as f:
            json.dump(json.loads(spg_project_settings.to_json()), f, indent=4)

        run_spg_pattern_generator(
            spg_led_panel_json_file,
            spg_led_wall_json_file,
            spg_raster_map_json_file,
            spg_project_settings_json_file,
            ResourceLoader.spg_pattern_basic_config())
