import utils as utils

from spg_icvfxpatterns.PatternGenerators.colorPatch import ColorPatch as _ColorPatch


class TestColorPatch(utils.TestGenerator):
    pattern_type = _ColorPatch.pattern_type
    generator_class = None
    config = {
        "name": "ColorPatch",
        "pattern_type": "ColorPatch",
        "percentage_width": 0.5,
        "percentage_height": 0.5,
        "absolute_pixel_width": 0,
        "absolute_pixel_height": 0,
        "color_range_min": 0,
        "color_range_max": 255,
        "duration_per_patch": 0.1,
        "color_patch_values": [[255, 0, 0]]
    }

    def test_fromJson(self):
        super(TestColorPatch, self).test_fromJson()

    def test_get_properties(self):
        super(TestColorPatch, self).test_get_properties()
