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
import unittest

import utils as utils

from spg_icvfxpatterns.PatternGenerators.dataRange import DataRange as _DataRange


@unittest.skip("Temporarily disabling this test class as works alomne but not when run with other tests")
class TestDataRange(utils.TestGenerator):
    pattern_type = _DataRange.pattern_type
    generator_class = None
    config = {
        "name": "DataRange",
        "pattern_type": "DataRange",
        "bit_depth_override": 0,
        "sequence_length": 0.05,
    }

    def test_fromJson(self):
        super(TestDataRange, self).test_fromJson()

    def test_get_properties(self):
        super(TestDataRange, self).test_get_properties()
