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

from stageassets.rasterMap import Mapping, RasterMap


class TestRasterMap(utils.TestBase):
    raster_map = None

    def setUp(self):
        self.raster_config = self.get_raster_config()
        self.raster_map = RasterMap.from_json(self.raster_config["raster1"])

    def test_ledPanel_serialize(self):
        for raster_name, data in self.raster_config.items():
            raster_map = RasterMap.from_json(data)

            for item in raster_map.mappings:
                self.assertIsInstance(item, Mapping)

            result = json.loads(
                raster_map.to_json()
            )

            for key, value in data.items():
                if key != "mappings":
                    self.assertEqual(value, result[key])
                else:
                    for idx, val in enumerate(value):
                        indexed_result = json.loads(result[key][idx])
                        for index_key, index_value in indexed_result.items():
                            self.assertEqual(index_value, indexed_result[index_key])

    def test_mapping_props(self):
        for mapping_data in self.raster_config["raster1"]["mappings"]:
            mapping = Mapping.from_json(mapping_data)
            for name, value in mapping.get_properties().items():
                self.assertEqual(mapping_data[name], value.value)

    def test_raster_props(self):
        raster_data = self.raster_config["raster1"]
        mapping = RasterMap.from_json(raster_data)
        for name, value in mapping.get_properties().items():

            if name != "mappings":
                self.assertEqual(raster_data[name], value.value)
