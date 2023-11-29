import utils as utils

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
