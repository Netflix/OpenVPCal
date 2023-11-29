import utils as utils

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
