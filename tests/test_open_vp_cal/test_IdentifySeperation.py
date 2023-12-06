from test_open_vp_cal.test_utils import TestProcessorBase

from open_vp_cal.framework.identify_separation import IdentifySeparation


class TestIdentifySeparation(TestProcessorBase):
    def test_identify_separation(self):
        identify_sep = IdentifySeparation(self.led_wall)
        results = identify_sep.run()
        self.assertEqual(results.first_red_frame.frame_num, 73)
        self.assertEqual(results.first_green_frame.frame_num, 78)
        self.assertEqual(results.separation, 5)

