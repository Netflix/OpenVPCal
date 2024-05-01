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

from spg_icvfxpatterns.PatternGenerators.frameCountSync import FrameCountSync as _FrameCountSync


class TestFrameSync(utils.TestGenerator):
    pattern_type = _FrameCountSync.pattern_type
    generator_class = None
    config = {
        "name": "FrameSync",
        "pattern_type": "Frame_Count_Sync",
        "bit_depth_override": 8,
        "sequence_length": 0.05,
        "border_width": 2,
        "border_color": [1, 1, 1]
    }

    def setUp(self):
        super(TestFrameSync, self).setUp()

    def test_fromJson(self):
        super(TestFrameSync, self).test_fromJson()

    def test_get_properties(self):
        super(TestFrameSync, self).test_get_properties()
