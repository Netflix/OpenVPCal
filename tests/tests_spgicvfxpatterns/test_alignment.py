import utils as utils

from spg_icvfxpatterns.PatternGenerators.alignment import Alignment as _Alignment


class TestAlignment(utils.TestGenerator):
    pattern_type = _Alignment.pattern_type
    generator_class = None
    config = {
        "name": "Alignment",
        "pattern_type": "Alignment",
        "sequence_length": 0.05,
        "enable_border": True,
        "border_color": [0, 0, 1],
        "line_border_color": [1, 0, 0]
    }

    def test_fromJson(self):
        super(TestAlignment, self).test_fromJson()

    def test_get_properties(self):
        super(TestAlignment, self).test_get_properties()
