import tests_spgicvfxpatterns.utils as utils

from spg_icvfxpatterns.PatternGenerators.exposureStops import ExposureStops as _ExposureStops


class TestExposureStops(utils.TestGenerator):
    pattern_type = _ExposureStops.pattern_type
    generator_class = None
    config = {
        "name": "Exposure",
        "pattern_type": _ExposureStops.pattern_type,
        "bit_depth_override": 0,
        "sequence_length": 0.05,
        "number_of_stops": 7,
        "font_size": 100,
        "text_color": [1, 0, 0],
        "fit_to_wall": True
    }

    def test_fromJson(self):
        super(TestExposureStops, self).test_fromJson()

    def test_get_properties(self):
        super(TestExposureStops, self).test_get_properties()


class TestExposureStopsNotFit(utils.TestGenerator):
    pattern_type = _ExposureStops.pattern_type
    generator_class = None
    config = {
        "name": "ExposureNotFit",
        "pattern_type": _ExposureStops.pattern_type,
        "bit_depth_override": 0,
        "sequence_length": 0.05,
        "number_of_stops": 7,
        "font_size": 100,
        "text_color": [1, 0, 0],
        "fit_to_wall": False
    }

    def test_fromJson(self):
        super(TestExposureStopsNotFit, self).test_fromJson()

    def test_get_properties(self):
        super(TestExposureStopsNotFit, self).test_get_properties()
