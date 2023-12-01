import json

import test_stageassets.utils as utils

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
