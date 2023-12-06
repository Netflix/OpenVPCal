import os

from spg.testing import utils


class TestGenerator(utils.TestGenerator):
    @classmethod
    def get_folder_for_this_file(cls):
        return os.path.dirname(__file__)

    def setUp(self):
        super(TestGenerator, self).setUp()
        self.output_folder = os.path.join(self.get_test_result_folder(), "pattern_outputs")
