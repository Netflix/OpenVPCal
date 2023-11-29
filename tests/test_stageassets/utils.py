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
