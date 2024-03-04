import colour

from open_vp_cal.core import constants
from test_open_vp_cal.test_utils import TestBase


class TestConstants(TestBase):
    def test_camera_colour_space_enum(self):
        for item in constants.CameraColourSpace.CS_ALL:
            cs = colour.RGB_COLOURSPACES[item]
            self.assertNotEquals(cs, None)

    def test_colour_space_enum(self):
        for item in constants.ColourSpace.CS_ALL:
            cs = colour.RGB_COLOURSPACES[item]
            self.assertNotEquals(cs, None)