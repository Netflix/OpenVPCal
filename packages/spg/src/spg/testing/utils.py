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
import json
import os
import unittest

from spg import PatternGenerators as _PatternGenerators
from spg.spg import PatternGenerator as _PatternGenerator
from spg.utils import constants, imageUtils
from spg.utils.imageUtils import oiio


OIIO_INSTALLED = oiio is None
OIIO_MSG = "OpenImageIO Is Not Installed"


class TestBase(unittest.TestCase):
    image_fail_count = 0

    @classmethod
    def get_folder_for_this_file(cls):
        raise NotImplementedError("Needs Implementing In The Inheriting Class: return os.path.dirname(__file__)")

    @classmethod
    def get_test_resource_folder(cls):
        path = os.path.join(
            cls.get_folder_for_this_file(),
            'resources'
        )
        return path

    @classmethod
    def get_test_resource_config(cls, config_name):
        path = os.path.join(
            cls.get_test_resource_folder(),
            "configs",
            config_name
        )
        return path

    @classmethod
    def get_test_resource_ocio_config(cls):
        path = cls.get_test_resource_config("ocio")
        return os.path.join(path, "aces", "cg", "cg-config-v0.1.0_aces-v1.3_ocio-v2.1.1.ocio")

    @classmethod
    def get_test_resource(cls, resource_name, ext):
        ext = ext.replace(".", "")
        path = os.path.join(
            cls.get_test_resource_folder(),
            resource_name + "." + ext
        )
        return path

    @classmethod
    def get_test_image(cls, image_name, ext):
        path = cls.get_test_resource(image_name, ext)
        if os.path.exists(path):
            return oiio.ImageBuf(path)
        raise IOError("File Not Found: " + path)

    @classmethod
    def get_test_result_folder(cls):
        results_folder = os.path.join(
            cls.get_folder_for_this_file(),
            'results')
        if not os.path.exists(results_folder):
            os.makedirs(results_folder)
        return results_folder

    @classmethod
    def get_test_result(cls, resource_name, ext):
        return os.path.join(
            cls.get_test_result_folder(),
            resource_name + "." + ext
        )

    def _store_test_resource_image(self, image, ext="dpx", img_format=None):
        """ Used only during dev to store an example image for a unit test, which can be used as a validation
        to compare images generated during unit testing

        """
        if not img_format:
            img_format = oiio.UNKNOWN
        file_name = self.get_test_resource(self._testMethodName, ext)
        if not image.has_error:
            image.write(file_name, img_format)
        if image.has_error:
            raise IOError("Error writing: " + file_name + " : " + image.geterror())

    def compare_against_test_image(self, image_buffer, ext="dpx"):
        expected_image = self.get_test_image(self._testMethodName, ext)
        self.compare_image_buffers(expected_image, image_buffer, ext)

    def compare_images(self, expected_filepath, actual_filepath, ext="dpx"):
        if not os.path.exists(expected_filepath):
            self.fail("File Path Does Not Exist: " + expected_filepath)

        if not os.path.exists(actual_filepath):
            self.fail("File Path Does Not Exist: " + actual_filepath)

        buffer_a = oiio.ImageBuf(expected_filepath)
        buffer_b = oiio.ImageBuf(actual_filepath)
        self.compare_image_buffers(buffer_a, buffer_b, ext)

    def compare_image_buffers(self, expected_image, image_buffer, ext):
        # Compare The Format
        expected_spec = expected_image.spec()
        image_buffer_spec = image_buffer.spec()
        self.assertEqual(expected_spec.format, image_buffer_spec.format)

        # Compare The Bits Per Sample
        expected_bps = expected_spec.get_int_attribute(constants.OIIO_BITS_PER_SAMPLE, defaultval=0)
        actual_bps = image_buffer_spec.get_int_attribute(constants.OIIO_BITS_PER_SAMPLE, defaultval=0)
        self.assertEqual(expected_bps, actual_bps)

        comp_results = oiio.ImageBufAlgo.compare(expected_image, image_buffer, 1.0e-5, 1.0e-5)
        if comp_results.nfail > self.image_fail_count:

            file_name = "_".join([self.__class__.__name__, self._testMethodName])
            diff = oiio.ImageBufAlgo.absdiff(expected_image, image_buffer)

            self.write_test_image_result(diff, file_name.replace("test", "result_diff"), ext, expected_bps)
            self.write_test_image_result(image_buffer, file_name.replace("test", "result"), ext, expected_bps)
            self.fail(file_name + ": Images did not match")

    @classmethod
    def write_test_image_result(cls, image, image_name, ext, bit_depth):
        file_name = cls.get_test_result(image_name, ext)
        imageUtils.write_image(image, file_name, bit_depth)
        return file_name


class SpgTestBase(TestBase):
    spg = None

    def setUp(self):
        self.output_folder = os.path.join(self.get_test_result_folder(), "pattern_outputs")

        self.panels_config = self.get_panels_config()
        self.walls_config = self.get_walls_config()
        self.raster_config = self.get_raster_config()
        self.project_settings_config = self.get_project_settings()
        self.pattern_settings_config = self.get_pattern_settings()

        self.project_settings_config['ocio_config_path'] = self.get_test_resource_ocio_config()
        self.spg = _PatternGenerator(
            self.panels_config, self.walls_config, self.raster_config, self.project_settings_config,
            self.pattern_settings_config)

    def get_panels_config(self):
        path = self.get_test_resource_config("test_panels.json")
        return self.load_json_from_file(path)

    def get_walls_config(self):
        path = self.get_test_resource_config("test_walls.json")
        return self.load_json_from_file(path)

    def get_raster_config(self):
        path = self.get_test_resource_config("test_raster.json")
        return self.load_json_from_file(path)

    def get_project_settings(self):
        path = self.get_test_resource_config("test_project.json")
        data = self.load_json_from_file(path)
        data["output_folder"] = self.output_folder
        return data

    def get_pattern_settings(self):
        path = self.get_test_resource_config("test_patterns.json")
        return self.load_json_from_file(path)

    @staticmethod
    def load_json_from_file(path):
        if not os.path.exists(path):
            raise IOError("File does not exist: " + path)

        with open(path) as handle:
            return json.load(handle)


class TestGenerator(SpgTestBase):
    pattern_type = None
    generator_class = None
    config = {
    }

    def setUp(self):
        super(TestGenerator, self).setUp()
        self.generator_class = _PatternGenerators.get_pattern(self.pattern_type)
        self.generator = self.generator_class.from_json(self.spg, self.config)

    def test_fromJson(self):
        for key, value in self.config.items():
            self.assertTrue(hasattr(self.generator, key))
            attr = getattr(self.generator, key)
            self.assertEqual(attr, value, msg="Value For attribute {0} does not match".format(key))

    def test_iter(self):
        generator_iter_results = {}
        for key, value in self.generator:
            generator_iter_results[key] = value

        for key, value in self.config.items():
            self.assertEqual(value, generator_iter_results[key])

    def test_get_properties(self):
        result = self.generator.get_properties()
        for key, prop in result.items():
            if key in self.config:
                expected_value = self.config[key]
                self.assertEqual(expected_value, prop.value)

    @unittest.skipIf(OIIO_INSTALLED, OIIO_MSG)
    def test_generator(self):
        frame_num = 0
        results = self.generator.execute()
        for led_wall, result in results.items():
            file_path = result[frame_num]
            file_name, ext = os.path.splitext(os.path.basename(file_path))
            file_resource_path = self.get_test_resource("test_" + file_name, ext)

            # Enable To Replace/ Update The Reference Images For Comparison When We Need To Re Generate
            # TODO: Think of a nicer way to turn this on and off it should be off 90% of the time
            # if os.path.exists(file_resource_path):
            #     shutil.copy(file_path, file_resource_path)

            if not os.path.exists(file_path):
                raise IOError("Generated Image Not Found: " + file_path)

            if not os.path.exists(file_resource_path):
                raise IOError("Comparison Image Not Found: " + file_resource_path)

            generated_image = oiio.ImageBuf(file_path)
            test_resource_image = oiio.ImageBuf(file_resource_path)
            self.compare_image_buffers(test_resource_image, generated_image, ext)
