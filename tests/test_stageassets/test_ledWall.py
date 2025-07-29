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

import test_stageassets_utils as utils

from stageassets.ledPanel import LEDPanel
from stageassets.ledWall import LEDWall


class TestLedWall(utils.TestBase):
    wall = None

    def setUp(self):
        super(TestLedWall, self).setUp()
        walls_config = self.get_walls_config()
        self.wall_config = walls_config["mainWall"]
        self.wall = LEDWall.from_json(self.wall_config)

        panels_config = self.get_panels_config()
        panel_data = panels_config[self.wall.panel_name]
        self.wall.panel = LEDPanel.from_json(panel_data)

    def test_ledWall_serialize(self):
        walls_config = self.get_walls_config()
        for wall_name, data in walls_config.items():
            wall = LEDWall.from_json(data)

            result = json.loads(
                wall.to_json()
            )

            for key, value in data.items():
                self.assertIn(key, result)
                self.assertEqual(value, result[key])

    def test_wall_num_panels(self):
        self.assertEqual(210, self.wall.num_panels)

    def test_wall_resolution_width(self):
        self.assertEqual(3696, self.wall.resolution_width)

    def test_wall_resolution_height(self):
        self.assertEqual(1760, self.wall.resolution_height)

    def test_wall_height(self):
        self.assertEqual(5000, self.wall.wall_height)

    def test_wall_width(self):
        self.assertEqual(10500, self.wall.wall_width)

    def test_gamut_only_cs_name(self):
        self.assertEqual("", self.wall.gamut_only_cs_name)
        self.wall.gamut_only_cs_name = "Test1"
        self.assertEqual("Test1", self.wall.gamut_only_cs_name)

    def test_gamut_and_transfer_function_cs_name(self):
        self.assertEqual("", self.wall.gamut_and_transfer_function_cs_name)
        self.wall.gamut_and_transfer_function_cs_name = "Test2"
        self.assertEqual("Test2", self.wall.gamut_and_transfer_function_cs_name)

    def test_panel(self):
        panels_config = self.get_panels_config()
        data = panels_config[self.wall.panel_name]

        result = json.loads(
            self.wall.panel.to_json()
        )
        for key, value in data.items():
            self.assertEqual(value, result[key])

    def test_panel_get_properties(self):
        properties = self.wall.get_properties()

        for name, value in self.wall_config.items():
            for prop_name, prop_value in properties.items():
                if prop_name == name:
                    result = json.loads(prop_value.to_json())
                    self.assertEqual(value, result["value"])
