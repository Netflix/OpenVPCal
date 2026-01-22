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

Pytest configuration and fixtures for test cleanup.
"""
import glob
import os
import shutil
import tempfile
import time

import pytest


def cleanup_old_test_temp_folders(max_age_seconds=3600):
    """Remove test temp folders older than max_age_seconds.

    Only cleans up folders that are older than the specified age to avoid
    deleting folders that are still in use by running tests.

    Args:
        max_age_seconds: Only delete folders older than this (default: 1 hour)

    Returns:
        Number of folders cleaned up
    """
    temp_dir = tempfile.gettempdir()
    # Clean up both openvpcal_test_* and spg_test_* folders
    patterns = [
        os.path.join(temp_dir, "openvpcal_test_*"),
        os.path.join(temp_dir, "spg_test_*"),
    ]
    current_time = time.time()
    count = 0

    for pattern in patterns:
        folders = glob.glob(pattern)
        for folder in folders:
            try:
                # Check folder age
                folder_mtime = os.path.getmtime(folder)
                age_seconds = current_time - folder_mtime

                if age_seconds > max_age_seconds:
                    shutil.rmtree(folder, ignore_errors=True)
                    count += 1
            except Exception:
                pass

    return count


@pytest.hookimpl(tryfirst=True)
def pytest_sessionstart(session):
    """Clean up old temp folders from previous test runs (older than 1 hour)."""
    count = cleanup_old_test_temp_folders(max_age_seconds=3600)
    if count > 0:
        print(f"\nCleaned up {count} old test temp folders (>1 hour old)")