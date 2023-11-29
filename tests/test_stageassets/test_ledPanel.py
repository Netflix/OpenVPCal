import json

import utils as utils

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
