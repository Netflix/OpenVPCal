import tests_spgicvfxpatterns.utils as utils

from spg_icvfxpatterns.PatternGenerators.dataRange import DataRange as _DataRange


class TestDataRange(utils.TestGenerator):
    pattern_type = _DataRange.pattern_type
    generator_class = None
    config = {
        "name": "DataRange",
        "pattern_type": "DataRange",
        "bit_depth_override": 0,
        "sequence_length": 0.05,
    }

    def test_fromJson(self):
        super(TestDataRange, self).test_fromJson()

    def test_get_properties(self):
        super(TestDataRange, self).test_get_properties()
