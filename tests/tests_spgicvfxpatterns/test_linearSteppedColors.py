import utils as utils

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
