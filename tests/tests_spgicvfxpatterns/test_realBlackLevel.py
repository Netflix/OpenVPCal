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

import utils as utils

from spg_icvfxpatterns.PatternGenerators.realBlackLevel import RealBlackLevel as _RealBlackLevel


class TestRealBlackLevel(utils.TestGenerator):
    pattern_type = _RealBlackLevel.pattern_type
    generator_class = None
    config = {
        "name": "RealBlackLevel",
        "pattern_type": "RealBlackLevel",
        "sequence_length": 0.05
    }

    def test_fromJson(self):
        super(TestRealBlackLevel, self).test_fromJson()

    def test_get_properties(self):
        super(TestRealBlackLevel, self).test_get_properties()
