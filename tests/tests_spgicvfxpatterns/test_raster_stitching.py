import os
import shutil
import unittest

import spg.testing.utils as utils
from spg import PatternGenerators as PatternGenerators
from spg.spg import PatternGenerator as _PatternGenerator

PatternGenerators.load_plugins()


class TestStitching_WithSegment_Rotation(utils.SpgTestBase):
    @classmethod
    def get_folder_for_this_file(cls):
        return os.path.dirname(__file__)

    def setUp(self):
        super(TestStitching_WithSegment_Rotation, self).setUp()

        self.project_settings_config["image_file_format"] = "dpx"
        self.pattern_settings_config = [
            {
                "name": "FrameSync",
                "pattern_type": "Frame_Count_Sync",
                "bit_depth_override": 8,
                "sequence_length": 0.05,
                "border_width": 2,
                "border_color": [1, 1, 1]
            },
        ]
        self.walls_config = [{
            "id": 1,
            "name": "wall_larger_than_proc_with_rotated_section",
            "panel_name": "BP2 v2",
            "panel_count_width": 24,
            "panel_count_height": 8,
            "wall_default_color": [1, 0, 1]
        }]
        self.raster_config = [
            {
                "name": "raster_with_rotated_section",
                "resolution_width": 3840,
                "resolution_height": 2160,
                "mappings": [
                  {
                    "wall_name": "wall_larger_than_proc_with_rotated_section",
                    "raster_u": 0,
                    "raster_v": 0,
                    "wall_segment_u_start": 0,
                    "wall_segment_u_end": 3520,
                    "wall_segment_v_start": 0,
                    "wall_segment_v_end": 1408,
                    "wall_segment_orientation": 0
                  },
                  {
                    "wall_name": "wall_larger_than_proc_with_rotated_section",
                    "raster_u": 0,
                    "raster_v": 1450,
                    "wall_segment_u_start": 3521,
                    "wall_segment_u_end": 4224,
                    "wall_segment_v_start": 0,
                    "wall_segment_v_end": 1408,
                    "wall_segment_orientation": 90
                  },
                ]
            }
        ]
        self.spg = _PatternGenerator(
            self.panels_config, self.walls_config, self.raster_config, self.project_settings_config,
            self.pattern_settings_config)

    @unittest.skipIf(utils.OIIO_INSTALLED, utils.OIIO_MSG)
    def test_stitching(self):
        for _ in self.spg.generate_patterns_and_stitch_rasters():
            pass

        expected_filepath = self.get_test_resource("raster_with_rotated_section.000000", "dpx")
        expected_file_name = os.path.basename(expected_filepath)

        output_folder = self.project_settings_config["output_folder"]
        generated_file_path = os.path.join(output_folder, "RasterMaps", "raster_with_rotated_section.seq", expected_file_name)
        self.compare_images(expected_filepath, generated_file_path)


class TestStitching_Multiple_Walls_Single_Raster_All_Fit(utils.SpgTestBase):
    @classmethod
    def get_folder_for_this_file(cls):
        return os.path.dirname(__file__)

    def setUp(self):
        super(TestStitching_Multiple_Walls_Single_Raster_All_Fit, self).setUp()

        self.project_settings_config["image_file_format"] = "dpx"
        self.pattern_settings_config = [
            {
                "name": "FrameSync",
                "pattern_type": "Frame_Count_Sync",
                "bit_depth_override": 8,
                "sequence_length": 0.05,
                "border_width": 2,
                "border_color": [1, 1, 1]
            },
        ]

        self.spg = _PatternGenerator(
            self.panels_config, self.walls_config, self.raster_config, self.project_settings_config,
            self.pattern_settings_config)

    @unittest.skipIf(utils.OIIO_INSTALLED, utils.OIIO_MSG)
    def test_stitching(self):
        for _ in self.spg.generate_patterns_and_stitch_rasters():
            pass

        expected_filepath = self.get_test_resource("raster1.000000", "dpx")
        expected_file_name = os.path.basename(expected_filepath)

        output_folder = self.project_settings_config["output_folder"]
        generated_file_path = os.path.join(output_folder, "RasterMaps", "raster1.seq", expected_file_name)
        self.compare_images(expected_filepath, generated_file_path)
