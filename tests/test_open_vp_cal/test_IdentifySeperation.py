"""
Copyright 2024 Netflix Inc.

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

    http://www.apache.org/licenses/LICENSE-2.0

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.
"""

from test_utils import TestProcessorBase

from open_vp_cal.framework.identify_separation import IdentifySeparation


class TestIdentifySeparation(TestProcessorBase):
    def test_identify_separation(self):
        self.led_wall.roi = self.recalc_old_roi(self.led_wall.roi)
        identify_sep = IdentifySeparation(self.led_wall)
        results = identify_sep.run()
        self.assertEqual(results.first_red_frame.frame_num, 72)
        self.assertEqual(results.first_green_frame.frame_num, 77)
        self.assertEqual(results.first_blue_frame.frame_num, 82)
        self.assertEqual(results.first_grey_frame.frame_num, 87)
        self.assertEqual(results.second_red_frame.frame_num, 92)
        self.assertEqual(results.separation, 5)

