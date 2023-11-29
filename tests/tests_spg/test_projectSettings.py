import json
import os

import spg.testing.utils as utils

from spg.projectSettings import ProjectSettings


class TestProjectSettings(utils.SpgTestBase):
    project_settings_data = None
    project_settings = None

    @classmethod
    def get_folder_for_this_file(cls):
        return os.path.dirname(__file__)

    def setUp(self):
        super(TestProjectSettings, self).setUp()
        self.project_settings_data = self.get_project_settings()
        self.project_settings = ProjectSettings.from_json(self.project_settings_data)

    def test_project_settings_serialize(self):
        result = json.loads(
            self.project_settings.to_json()
        )

        for key, value in self.project_settings_data.items():
            self.assertIn(key, result)
            self.assertEqual(self.project_settings_data[key], result[key])
