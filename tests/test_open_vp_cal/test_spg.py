from test_open_vp_cal.test_utils import TestProject
from open_vp_cal.widgets.main_window import MainWindow


class TestSPG(TestProject):
    project_name = "Sample_Project6_Reference_Wall_With_Decoupled_Lens"

    def test_generate_spg_patterns_for_led_walls(self):
        led_walls = [self.project_settings.led_walls[0]]
        result = MainWindow.generate_spg_patterns_for_led_walls(
            self.project_settings, led_walls)
