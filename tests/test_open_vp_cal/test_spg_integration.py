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

from test_utils import TestProject
from open_vp_cal.widgets.main_window import MainWindow


class TestSPG(TestProject):
    project_name = "Sample_Project6_Reference_Wall_With_Decoupled_Lens"

    def test_generate_spg_patterns_for_led_walls(self):
        led_walls = [self.project_settings.led_walls[0]]
        MainWindow.generate_spg_patterns_for_led_walls(
            self.project_settings, led_walls)
