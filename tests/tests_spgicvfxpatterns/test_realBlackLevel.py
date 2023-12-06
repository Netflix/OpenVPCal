import tests_spgicvfxpatterns.utils as utils

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
