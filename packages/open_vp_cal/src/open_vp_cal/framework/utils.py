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

This module contains utility functions for the framework
"""
import json
import os
import tempfile

from typing import TYPE_CHECKING, List

from open_vp_cal.core import constants, ocio_config
from open_vp_cal.core import utils as core_utils
from open_vp_cal.core.ocio_config import OcioConfigWriter
from open_vp_cal.core.resource_loader import ResourceLoader
from open_vp_cal.framework.generation import PatchGeneration

if TYPE_CHECKING:
    from open_vp_cal.led_wall_settings import LedWallSettings
    from open_vp_cal.project_settings import ProjectSettings

from spg.projectSettings import ProjectSettings as SPGProjectSettings
from spg.main import run_spg_pattern_generator
from stageassets.ledWall import LEDWall as SPGLedWall
from stageassets.ledPanel import LEDPanel as SPGLedPanel
from stageassets.rasterMap import RasterMap as SPGRasterMap
from stageassets.rasterMap import Mapping as SPGMapping


def generate_spg_patterns_for_led_walls(
        project_settings: 'ProjectSettings',
        led_walls: List['LedWallSettings']) -> None:
    """ For the given project settings and list of led walls, generate the patterns for SPG which is used to
                evaluate and diagnose issues with the imaging chain

        Args:
            project_settings: The project settings used for the project
            led_walls: the led walls we want to generate patterns from
    """
    config_writer, ocio_config_path = export_pre_calibration_ocio_config(
        project_settings, led_walls)
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
        target_gamut_and_tf_cs = config_writer.get_target_gamut_and_transfer_function_cs(
            led_wall)
        transfer_function_only_cs = config_writer.get_transfer_function_only_cs(
            led_wall)

        # If we are not using an EXR file format, we apply the EOTF colour transform
        if not apply_eotf_colour_transform:
            target_gamut_and_tf_cs = target_gamut_only_cs

        spg_led_wall = SPGLedWall()
        spg_led_wall.gamut_only_cs_name = target_gamut_only_cs.getName()
        spg_led_wall.gamut_and_transfer_function_cs_name = target_gamut_and_tf_cs.getName()
        spg_led_wall.transfer_function_only_cs_name = transfer_function_only_cs.getName()
        spg_led_wall.id = idx
        spg_led_wall.name = led_wall.name
        spg_led_wall.panel_name = spg_panel.name
        spg_led_wall.panel = spg_panel
        spg_led_wall.panel_count_width = int(
            project_settings.resolution_width / spg_panel.panel_resolution_width)
        spg_led_wall.panel_count_height = int(
            project_settings.resolution_height / spg_panel.panel_resolution_height
        )
        spg_led_wall.wall_default_color = core_utils.generate_color(led_wall.name)

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

    spg_led_panel_json = [json.loads(spg_led_panel.to_json()) for spg_led_panel in
                          spg_led_panels]
    spg_led_wall_json = [json.loads(spg_led_wall.to_json()) for spg_led_wall in
                         spg_led_walls]
    spg_raster_map_json = [json.loads(spg_raster_map.to_json()) for spg_raster_map
                           in spg_raster_maps]
    tmp_dir = tempfile.TemporaryDirectory()
    spg_led_panel_json_file = os.path.join(tmp_dir.name, "led_panel_settings.json")
    spg_led_wall_json_file = os.path.join(tmp_dir.name, "led_wall_settings.json")
    spg_raster_map_json_file = os.path.join(tmp_dir.name,
                                            "raster_map_settings.json")
    spg_project_settings_json_file = os.path.join(tmp_dir.name,
                                                  "spg_project_settings.json")
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
        ResourceLoader.spg_pattern_basic_config()
    )

def generate_patterns_for_led_walls(project_settings: 'ProjectSettings', led_walls: List['LedWallSettings']) -> str:
    """ For the given list of led walls filter out any walls which are verification walls, then generate the
        calibration patterns for the remaining walls.

    Args:
        project_settings: The project settings with the settings for the pattern generation
        led_walls: A list of led walls we want to generate patters for

    Returns: The ocio config file path which was generated

    """
    led_walls = [led_wall for led_wall in led_walls if not led_wall.is_verification_wall]
    if not led_walls:
        return ""

    for led_wall in led_walls:
        patch_generator = PatchGeneration(led_wall)
        patch_generator.generate_patches(constants.PATCHES.patch_order())

    _, ocio_config_path = export_pre_calibration_ocio_config(project_settings, led_walls)
    return ocio_config_path


def export_pre_calibration_ocio_config(
        project_settings: 'ProjectSettings',
        led_walls: List['LedWallSettings']) -> tuple[OcioConfigWriter, str]:
    """ Export the pre calibration ocio config file for the given walls and project settings

    """
    config_writer = ocio_config.OcioConfigWriter(project_settings.export_folder)
    return config_writer, config_writer.generate_pre_calibration_ocio_config(led_walls)
