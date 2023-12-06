import tests_spgicvfxpatterns.utils as utils

from spg_icvfxpatterns.PatternGenerators.movingBars import MovingBars as _MovingBars


class TestMovingBars(utils.TestGenerator):
    pattern_type = _MovingBars.pattern_type
    generator_class = None
    config = {
        "name": "MovingBars",
        "pattern_type": "MovingBars",
        "sequence_length": 5,
        "bar_width": 5,
        "bg_color": [0.25, 0.25, 0.25],
        "bar_color": [1.0, 1.0, 1.0]
    }

    def test_fromJson(self):
        super(TestMovingBars, self).test_fromJson()

    def test_get_properties(self):
        super(TestMovingBars, self).test_get_properties()
