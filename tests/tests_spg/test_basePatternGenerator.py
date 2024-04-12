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
"""
import os
import unittest

import spg.testing.utils as utils

from spg.PatternGenerators.basePatternGenerator import BasePatternGenerator as _BasePatternGenerator
from spg.utils import imageUtils as _imageUtils
from spg.utils.imageUtils import oiio


class TestBaseGenerator(utils.TestGenerator):
    pattern_type = _BasePatternGenerator.pattern_type
    generator_class = None
    config = {
        "name": "",
        "pattern_type": "",
        "bit_depth_override": 0,
        "sequence_length": 2
    }

    @classmethod
    def get_folder_for_this_file(cls):
        return os.path.dirname(__file__)

    def test_fromJson(self):
        super(TestBaseGenerator, self).test_fromJson()

    def test_get_frame_num_and_file_path(self):
        name = "Test_num"
        expected_frame = 10
        expected_path = os.path.join(self.output_folder, "Patterns/{0}_.seq/{1}_.000010.dpx".format(name, name))
        result_frame, result_path = self.generator_class.get_frame_num_and_file_path(expected_frame, name)

        self.assertEqual(expected_frame, result_frame)
        self.assertEqual(expected_path, result_path)

    def test_store_result(self):
        frame_num = 1
        full_file_path = "test"
        led_wall_name = "test_wall"
        expected = {
            led_wall_name: {frame_num: full_file_path}
        }
        results = {led_wall_name: {}}

        self.generator_class.store_result(frame_num, full_file_path, led_wall_name, results)
        self.assertEqual(expected, results)

    @unittest.skipIf(utils.OIIO_INSTALLED, utils.OIIO_MSG)
    def test_write_image_and_store_result(self):
        image_buffer = _imageUtils.create_solid_color_image(
            10, 10, num_channels=3,
            color=[1.0, 0.0, 0.0]
        )
        frame_num = 1
        full_file_path = os.path.join(self.get_test_result_folder(), "manual_{0}.dpx".format(self._testMethodName))
        led_wall_name = "test_wall"
        expected = {
            led_wall_name: {frame_num: full_file_path}
        }
        results = {led_wall_name: {}}

        self.generator_class.write_image_and_store_result(frame_num, full_file_path, led_wall_name, image_buffer, results)

        self.assertTrue(os.path.exists(full_file_path))
        self.assertEqual(expected, results)

        loaded_buffer = oiio.ImageBuf(full_file_path)
        self.compare_against_test_image(loaded_buffer)
        os.remove(full_file_path)

    @unittest.skipIf(utils.OIIO_INSTALLED, utils.OIIO_MSG)
    def test_create_solid_color_image(self):
        expected_width = 10
        expected_height = 10
        expected_color = [0.0, 0.0, 0.0]
        image_buffer = self.generator_class.create_solid_color_image(
            expected_width, expected_height, color=expected_color
        )

        spec = image_buffer.spec()
        self.assertEqual(oiio.TypeFloat, spec.format)

        tmp_output_file = self.write_test_image_result(
            image_buffer, "test_create_solid_color_image", self.spg.project_settings.image_file_format,
            self.spg.project_settings.image_file_bit_depth
        )

        loaded_buf = oiio.ImageBuf(tmp_output_file)
        self.compare_against_test_image(loaded_buf)
        os.remove(tmp_output_file)

    @unittest.skipIf(utils.OIIO_INSTALLED, utils.OIIO_MSG)
    def test_create_solid_color_image_override_bit_depth(self):
        expected_width = 10
        expected_height = 10
        expected_color = [0.0, 0.0, 0.0]
        current_bit_depth = self.generator_class.bit_depth_override
        self.generator_class.bit_depth_override = 8

        image_buffer = self.generator_class.create_solid_color_image(
            expected_width, expected_height, color=expected_color
        )

        spec = image_buffer.spec()
        self.assertEqual(oiio.TypeFloat, spec.format)

        tmp_output_file = self.write_test_image_result(
            image_buffer, "test_create_solid_color_image_override_bit_depth",
            self.spg.project_settings.image_file_format,
            self.generator_class.bit_depth_for_pattern()
        )

        loaded_buf = oiio.ImageBuf(tmp_output_file)
        self.compare_against_test_image(loaded_buf)
        os.remove(tmp_output_file)

        self.generator_class.bit_depth_override = current_bit_depth

    def test_get_image_file_name(self):
        pattern_output_folder = "folder"
        frame_num = 10
        name = "adam"
        self.generator_class.name = "GenericGen"
        expected = "folder/adam_GenericGen.000010.dpx"
        result = self.generator_class.get_image_file_name(
            pattern_output_folder, frame_num, name
        )
        self.generator_class.name = ""
        self.assertEqual(expected, result)

    def test_getKwargs(self):
        expected = ["led_wall", "led_walls"]
        result = self.generator.get_kwargs()
        self.assertEqual(expected, list(result.keys()))

    def test_get_and_create_pattern_output_folder(self):
        sub_folder_name = "UnitTest"
        expected = os.path.join(
            self.output_folder, "Patterns", "{0}{1}".format
            (
                sub_folder_name, self.generator.spg.project_settings.folder_suffix
            )
        )
        result = self.generator_class.get_and_create_pattern_output_folder(sub_folder=sub_folder_name)
        self.assertEqual(expected, result)

    def test_number_of_frames(self):
        expected = 48
        result = self.generator_class.number_of_frames()
        self.assertEqual(expected, result)

    def test_generator(self):
        return
