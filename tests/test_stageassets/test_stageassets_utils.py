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


class TestBase(unittest.TestCase):
    @staticmethod
    def get_test_resource_folder():
        path = os.path.join(
            os.path.dirname(__file__),
            'resources'
        )
        return path

    @staticmethod
    def get_test_resource_config(config_name):
        path = os.path.join(
            TestBase.get_test_resource_folder(),
            "configs",
            config_name
        )
        return path

    @staticmethod
    def get_test_resource(resource_name, ext):
        ext = ext.replace(".", "")
        path = os.path.join(
            TestBase.get_test_resource_folder(),
            resource_name + "." + ext
        )
        return path

    @staticmethod
    def get_panels_config():
        path = TestBase.get_test_resource_config("test_panels.json")
        return TestBase.load_json_from_file(path)

    @staticmethod
    def get_walls_config():
        path = TestBase.get_test_resource_config("test_walls.json")
        return TestBase.load_json_from_file(path)

    @staticmethod
    def get_raster_config():
        path = TestBase.get_test_resource_config("test_raster.json")
        return TestBase.load_json_from_file(path)

    @staticmethod
    def load_json_from_file(path):
        if not os.path.exists(path):
            raise IOError("File does not exist: " + path)

        with open(path) as handle:
            return json.load(handle)
