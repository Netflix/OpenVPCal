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
