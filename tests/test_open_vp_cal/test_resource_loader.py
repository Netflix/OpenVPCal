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

import os
import platform
import unittest
from open_vp_cal.core.resource_loader import ResourceLoader


class TestResourceLoader(unittest.TestCase):
    def test_ocio_config_path(self):
        actual = ResourceLoader.ocio_config_path()
        expected = "studio-config-v1.0.0_aces-v1.3_ocio-v2.1.ocio"
        self.assertTrue(os.path.exists(actual))
        self.assertEqual(os.path.basename(actual), expected)

    def test_slate(self):
        actual = ResourceLoader.slate()
        expected = "Slate.exr"
        self.assertTrue(os.path.exists(actual))
        self.assertEqual(os.path.basename(actual), expected)

    def test_regular_font(self):
        actual = ResourceLoader.regular_font()
        expected = "Roboto-Regular.ttf"
        self.assertTrue(os.path.exists(actual))
        self.assertEqual(os.path.basename(actual), expected)

    def test_bold_font(self):
        actual = ResourceLoader.bold_font()
        expected = "Roboto-Bold.ttf"
        self.assertTrue(os.path.exists(actual))
        self.assertEqual(os.path.basename(actual), expected)

    def test_netflix_logo(self):
        actual = ResourceLoader.netflix_logo()
        expected = "Netflix_Logo_RGB.png"
        self.assertTrue(os.path.exists(actual))
        self.assertEqual(os.path.basename(actual), expected)

    def test_orca_logo(self):
        actual = ResourceLoader.orca_logo()
        expected = "Orca.png"
        self.assertTrue(os.path.exists(actual))
        self.assertEqual(os.path.basename(actual), expected)

    def test_icon(self):
        actual = ResourceLoader.icon()
        expected = "icon.ico"
        self.assertTrue(os.path.exists(actual))
        self.assertEqual(os.path.basename(actual), expected)

    def test_copy_icon(self):
        actual = ResourceLoader.copy_icon()
        expected = "content-copy-custom.png"
        self.assertTrue(os.path.exists(actual))
        self.assertEqual(os.path.basename(actual), expected)

    def test_project_layout(self):
        actual = ResourceLoader.project_layout()
        if platform.system() == "Windows":
            expected = "ProjectLayout_Windows.layout"
        else:
            expected = "ProjectLayout.layout"
        self.assertTrue(os.path.exists(actual))
        self.assertEqual(os.path.basename(actual), expected)

    def test_analysis_layout(self):
        actual = ResourceLoader.analysis_layout()
        if platform.system() == "Windows":
            expected = "AnalysisLayout_Windows.layout"
        else:
            expected = "AnalysisLayout.layout"
        self.assertTrue(os.path.exists(actual))
        self.assertEqual(os.path.basename(actual), expected)
