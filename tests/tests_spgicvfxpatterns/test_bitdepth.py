import tests_spgicvfxpatterns.utils as utils

from spg_icvfxpatterns.PatternGenerators.bitdepth import BitDepth as _BitDepth


class TestBitDepth(utils.TestGenerator):
    pattern_type = _BitDepth.pattern_type
    generator_class = None
    config = {
        "name": "BitDepth12",
        "pattern_type": "BitDepth",
        "bit_depth_override": 0,
        "bit_depth_value": 12,
        "sequence_length": 0.05
    }

    def test_fromJson(self):
        super(TestBitDepth, self).test_fromJson()

    def test_get_properties(self):
        super(TestBitDepth, self).test_get_properties()
