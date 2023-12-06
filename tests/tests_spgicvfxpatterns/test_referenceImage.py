import os

import tests_spgicvfxpatterns.utils as utils

from spg_icvfxpatterns.PatternGenerators.referenceImage import ReferenceImage as _ReferenceImage


class TestReferenceImage(utils.TestGenerator):
    pattern_type = _ReferenceImage.pattern_type
    generator_class = None
    config = {
        "name": "ReferenceImage2",
        "pattern_type": "ReferenceImage",
        "bit_depth_override": 0,
        "sequence_length": 0.05,
        "image_scale": 0.8,
        "reference_filepath": "",
        "input_transform":  "ACES - ACES2065-1"
    }

    @classmethod
    def setUpClass(cls):
        super(TestReferenceImage, cls).setUpClass()
        file_name = "syntheticChart.01.exr"
        file_path = os.path.join(cls.get_test_resource_folder(), file_name)
        if not os.path.exists(file_path):
            raise IOError("File Not Found: " + file_path)
        cls.config["reference_filepath"] = file_path

    def test_fromJson(self):
        super(TestReferenceImage, self).test_fromJson()

    def test_get_properties(self):
        super(TestReferenceImage, self).test_get_properties()
