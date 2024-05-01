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

from spg_icvfxpatterns.PatternGenerators.linearSteppedRamp import LinearSteppedRamp as _LinearSteppedRamp


class TestLinearSteppedRamp(utils.TestGenerator):
    pattern_type = _LinearSteppedRamp.pattern_type
    generator_class = None
    config = {
        "name": "LinearSteppedRamp_10_20",
        "pattern_type": _LinearSteppedRamp.pattern_type,
        "bit_depth_override": 0,
        "sequence_length": 0.05,
        "number_of_steps": 10,
        "min_value": 10,
        "max_value": 20,
        "font_size": 40,
        "text_color": [0, 1, 0]
    }

    def test_fromJson(self):
        super(TestLinearSteppedRamp, self).test_fromJson()

    def test_get_properties(self):
        super(TestLinearSteppedRamp, self).test_get_properties()
