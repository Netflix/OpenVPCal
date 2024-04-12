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
import tests_spgicvfxpatterns.utils as utils

from spg_icvfxpatterns.PatternGenerators.checkboard import Checkerboard as _Checkerboard


class TestCheckerboard(utils.TestGenerator):
    pattern_type = _Checkerboard.pattern_type
    generator_class = None
    config = {
        "name": "Checkerboard_quarters",
        "pattern_type": "Checkerboard",
        "bit_depth_override": 10,
        "sequence_length": 0.05,
        "panels_per_patch": 0.25,
        "odd_color": [0, 0, 0],
        "even_color": [1, 1, 1]
    }

    def test_fromJson(self):
        super(TestCheckerboard, self).test_fromJson()

    def test_get_properties(self):
        super(TestCheckerboard, self).test_get_properties()
