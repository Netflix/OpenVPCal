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

import os

import utils as utils

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

    def setUp(self):
        super(TestReferenceImage, self).setUp()

    def test_fromJson(self):
        super(TestReferenceImage, self).test_fromJson()

    def test_get_properties(self):
        super(TestReferenceImage, self).test_get_properties()
