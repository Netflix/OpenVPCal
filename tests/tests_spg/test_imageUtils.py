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

from spg.utils import constants as _constants
from spg.utils import imageUtils as _imageUtils
from spg.utils.imageUtils import oiio


class TestImageUtils(utils.TestBase):
    expected_width = 30
    expected_height = 15
    expected_bit_depth = 10
    red_color = [1.0, 0.0, 0.0]
    file_format = "dpx"

    @classmethod
    def get_folder_for_this_file(cls):
        return os.path.dirname(__file__)

    def setUp(self):
        self.image_buffer = _imageUtils.create_solid_color_image(
            self.expected_width, self.expected_height, num_channels=3,
            color=self.red_color
        )

    @unittest.skipIf(utils.OIIO_INSTALLED, utils.OIIO_MSG)
    def test_create_solid_color_10bit(self):
        self.assertEqual(self.expected_width, self.image_buffer.oriented_full_width)
        self.assertEqual(self.expected_height, self.image_buffer.oriented_full_height)

        spec = self.image_buffer.spec()
        self.assertEqual(oiio.TypeFloat, spec.format)

        tmp_output_file = self.write_test_image_result(
            self.image_buffer, "test_create_solid_color_10bit",
            self.file_format,
            self.expected_bit_depth
        )

        loaded_buf = oiio.ImageBuf(tmp_output_file)
        self.compare_against_test_image(loaded_buf)
        os.remove(tmp_output_file)

    @unittest.skipIf(utils.OIIO_INSTALLED, utils.OIIO_MSG)
    def test_get_oiio_bit_depth(self):
        result = _imageUtils.get_oiio_bit_depth(self.expected_bit_depth)
        self.assertEqual(oiio.UINT16, result)

    @unittest.skipIf(utils.OIIO_INSTALLED, utils.OIIO_MSG)
    def test_get_oiio_bit_depth_invalid(self):
        self.assertRaises(KeyError, _imageUtils.get_oiio_bit_depth, 24)

    @unittest.skipIf(utils.OIIO_INSTALLED, utils.OIIO_MSG)
    def test_add_border_to_image(self):
        _imageUtils.add_border_to_image(self.image_buffer, 2, border_color=(0, 1, 0))

        tmp_output_file = self.write_test_image_result(
            self.image_buffer, "test_add_border_to_image",
            self.file_format,
            self.expected_bit_depth
        )

        loaded_buf = oiio.ImageBuf(tmp_output_file)
        self.compare_against_test_image(loaded_buf)
        os.remove(tmp_output_file)

    @unittest.skipIf(utils.OIIO_INSTALLED, utils.OIIO_MSG)
    def test_add_text_to_image(self):
        _imageUtils.add_text_to_image_centre(
            self.image_buffer, "T", text_color=(0, 0, 0)
        )

    @unittest.skipIf(utils.OIIO_INSTALLED, utils.OIIO_MSG)
    def test_write_image_rgb(self):
        manual_rgb = os.path.join(self.get_test_result_folder(), "test_write_image_rgb.dpx")
        _imageUtils.write_image(
            self.image_buffer,
            manual_rgb,
            self.expected_bit_depth,
            channel_mapping=["R", "G", "B"]
        )

        image_buffer = oiio.ImageBuf(manual_rgb)
        os.remove(manual_rgb)
        self.compare_against_test_image(image_buffer)

    @unittest.skipIf(utils.OIIO_INSTALLED, utils.OIIO_MSG)
    def test_write_image_bgr(self):
        manual_bgr = os.path.join(self.get_test_result_folder(), "test_write_image_bgr.dpx")
        _imageUtils.write_image(
            self.image_buffer,
            manual_bgr,
            self.expected_bit_depth,
            channel_mapping=["B", "G", "R"]
        )
        image_buffer = oiio.ImageBuf(manual_bgr)
        os.remove(manual_bgr)
        self.compare_against_test_image(image_buffer)

    @unittest.skipIf(utils.OIIO_INSTALLED, utils.OIIO_MSG)
    def test_color_conversion(self):
        test_color_conversion_file = os.path.join(self.get_test_result_folder(), "test_color_conversion.dpx")
        image_buffer = _imageUtils.create_solid_color_image(
            self.expected_width, self.expected_height, num_channels=3,
            color=[0.2, 0.4, 0.1]
        )

        ocio_config_path = os.path.join(
            self.get_test_resource_folder(),
            "configs",
            "ocio",
            "aces",
            "reference",
            "reference-config-v0.1.0_aces-v1.3_ocio-v2.1.1.ocio"
        )

        image_buffer = _imageUtils.apply_color_conversion(
            image_buffer, "Display - sRGB", "ACES - ACEScg",
            ocio_config_path
        )

        _imageUtils.write_image(
            image_buffer,
            test_color_conversion_file,
            self.expected_bit_depth
        )

        image_buffer = oiio.ImageBuf(test_color_conversion_file)
        os.remove(test_color_conversion_file)
        self.compare_against_test_image(image_buffer)

    @unittest.skipIf(utils.OIIO_INSTALLED, utils.OIIO_MSG)
    def test_color_conversion_reference(self):
        test_color_conversion_file = os.path.join(self.get_test_result_folder(), "test_color_conversion_reference.dpx")
        image_buffer = _imageUtils.create_solid_color_image(
            self.expected_width, self.expected_height, num_channels=3,
            color=[0.2, 0.4, 0.1]
        )

        ocio_config_path = os.path.join(
            self.get_test_resource_folder(),
            "configs",
            "ocio",
            "aces",
            "reference",
            "reference-config-v0.1.0_aces-v1.3_ocio-v2.1.1.ocio"
        )

        image_buffer = _imageUtils.apply_color_conversion(
            image_buffer, None, "ACES - ACES2065-1",
            ocio_config_path
        )

        _imageUtils.write_image(
            image_buffer,
            test_color_conversion_file,
            self.expected_bit_depth
        )

        image_buffer = oiio.ImageBuf(test_color_conversion_file)
        self.compare_against_test_image(image_buffer)
        os.remove(test_color_conversion_file)

    @unittest.skipIf(utils.OIIO_INSTALLED, utils.OIIO_MSG)
    def test_color_conversion_metadata(self):
        test_color_conversion_file = os.path.join(self.get_test_result_folder(), "test_color_conversion_metadata.exr")
        image_buffer = _imageUtils.create_solid_color_image(
            self.expected_width, self.expected_height, num_channels=3,
            color=[0.2, 0.4, 0.1]
        )

        ocio_config_path = os.path.join(
            self.get_test_resource_folder(),
            "configs",
            "ocio",
            "aces",
            "reference",
            "reference-config-v0.1.0_aces-v1.3_ocio-v2.1.1.ocio"
        )

        image_buffer = _imageUtils.apply_color_conversion(
            image_buffer, None, "ACES - ACES2065-1",
            ocio_config_path
        )

        _imageUtils.write_image(
            image_buffer,
            test_color_conversion_file,
            self.expected_bit_depth
        )

        image_buffer = oiio.ImageBuf(test_color_conversion_file)
        spec = image_buffer.spec()
        input_transform = spec.get_string_attribute(_constants.OCIO_INPUT_TRANSFORM)
        self.assertEqual("ACES - ACEScg", input_transform)

        output_transform = spec.get_string_attribute(_constants.OCIO_OUTPUT_TRANSFORM)
        self.assertEqual("ACES - ACES2065-1", output_transform)

        os.remove(test_color_conversion_file)
