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

from spg_icvfxpatterns.PatternGenerators.linearSteppedColors import LinearSteppedColors as _LinearSteppedColors


class TestLinearSteppedColors(utils.TestGenerator):
    pattern_type = _LinearSteppedColors.pattern_type
    generator_class = None
    config = {
        "name": "LinearSteppedColors",
        "pattern_type": "LinearSteppedColors",
        "sequence_length": 0.05,
        "number_of_steps": 50,
        "font_size": 10,
        "text_color": [1, 1, 1],
        "color_range_min": 0,
        "color_range_max": 1,
    }

    def test_fromJson(self):
        super(TestLinearSteppedColors, self).test_fromJson()

    def test_get_properties(self):
        super(TestLinearSteppedColors, self).test_get_properties()
