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
