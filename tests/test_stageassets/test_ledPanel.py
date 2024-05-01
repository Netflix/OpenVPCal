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

import test_stageassets.utils as utils

from stageassets.ledPanel import LEDPanel


class TestLedPanel(utils.TestBase):
    panel = None

    def setUp(self):
        panels_config = self.get_panels_config()
        self.panel_config = panels_config["BP2 v2"]
        self.panel = LEDPanel.from_json(self.panel_config)

    def test_ledPanel_serialize(self):
        panels_config = self.get_panels_config()
        for panel_name, data in panels_config.items():
            panel = LEDPanel.from_json(data)

            result = json.loads(
                panel.to_json()
            )

            for key, value in data.items():
                self.assertEqual(value, result[key])

    def test_panel_resolution_height(self):
        self.assertEqual(176, self.panel.panel_resolution_height)

    def test_panel_resolution_width(self):
        self.assertEqual(176, self.panel.panel_resolution_width)

    def test_panel_get_properties(self):
        properties = self.panel.get_properties()

        for name, value in self.panel_config.items():
            for prop_name, prop_value in properties.items():
                if prop_name == name:
                    result = json.loads(prop_value.to_json())
                    self.assertEqual(value, result["value"])
