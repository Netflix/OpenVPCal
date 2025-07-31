from typing import Tuple, List
from open_vp_cal.application_base import OpenVPCalBase
from test_utils import TestBase

class TestApplicationBase(TestBase):
    def setUp(self) -> None:
        super(TestBase, self).setUp()
        self.application = OpenVPCalBase()

    def test_validate_roi(self):
        tl: Tuple[float,float] = (0, 0)
        tr: Tuple[float,float] = (1, 0)
        br: Tuple[float,float] = (1, 1)
        bl: Tuple[float,float] = (0, 1)
        valid_roi:List[Tuple[float, float]] = [tl, tr, br, bl]
        self.assertTrue(self.application.validate_roi(valid_roi))
        self.assertFalse(self.application.validate_roi(valid_roi[:-1]))

        for i in range(len(valid_roi) - 1):
            for j in range (i + 1, len(valid_roi)):
                invalid_roi = valid_roi.copy()
                invalid_roi[i], invalid_roi[j] = invalid_roi[j], invalid_roi[i]
                self.assertFalse(self.application.validate_roi(invalid_roi),
                    f"Invalid roi should return False: swap[{i},{j}], roi={invalid_roi}")
