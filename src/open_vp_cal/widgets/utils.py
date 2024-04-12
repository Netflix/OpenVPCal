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

A module to hold ui-specific utility functions
"""
import numpy as np
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QFileDialog, QWidget

from open_vp_cal.core.utils import stack_numpy_array


def select_folder() -> str:
    """
    Opens a QFileDialog to select a folder.

    Returns:
        str: The path to the selected folder. Empty string if no folder was selected.
    """
    dialog = QFileDialog()
    dialog.setFileMode(QFileDialog.Directory)  # Set mode to select directories
    dialog.setOption(QFileDialog.ShowDirsOnly, True)  # Show only directories, no files

    if dialog.exec_() == QFileDialog.Accepted:
        # User clicked 'OK', so get the selected directories
        selected_directories = dialog.selectedFiles()

        if selected_directories:
            # Return the first selected directory
            return selected_directories[0]

    # If we get here, no folder was selected
    return ""


class LockableWidget(QWidget):
    """
    A widget that can be locked to prevent user interaction.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.active_state = True
        self.master_layout = None

    def _set_active_state(self, value: bool):
        """ Sets the active state of all the UI components

        Args:
            value: The value to set the active state to
        """
        for i in range(self.master_layout.count()):
            widget = self.master_layout.itemAt(i).widget()
            if widget is not None:
                widget.setDisabled(value)

    def disable(self):
        """
        Disables all the UI components
        """
        if self.active_state:
            self.active_state = False
            self._set_active_state(True)

    def enable(self):
        """
        Enables all the UI components
        """
        if not self.active_state:
            self.active_state = True
            self._set_active_state(False)


def create_qimage_rgb8_from_numpy_array(img_np):
    """ Create a QImage from a numpy array

    Args:
        img_np: The numpy array to create the QImage from

    Returns: The QImage in 8 bit

    """
    img_np, height, width, channels = stack_numpy_array(img_np)
    img_np = np.clip(img_np * 255, 0, 255).astype(np.uint8)
    bytes_per_line = channels * width
    image_format = QImage.Format_RGB888 if channels == 3 else QImage.Format_RGBA8888
    qimage = QImage(img_np.data, width, height, bytes_per_line, image_format)
    return qimage
