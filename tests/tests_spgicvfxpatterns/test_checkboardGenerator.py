import utils as utils

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
