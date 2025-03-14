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
from pathlib import Path

import numpy as np
from PySide6.QtGui import QImage, Qt, QPixmap
from PySide6.QtWidgets import QFileDialog, QWidget, QMessageBox

from open_vp_cal.core.constants import FileFormats, SourceSelect, InputSelectSources
from open_vp_cal.core.resource_loader import ResourceLoader
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


def select_file() -> Path | None:
    """
    Opens a QFileDialog to select a single file with specified extensions.

    Returns:
        str: The path to the selected file. Empty string if no file was selected.
    """
    dialog = QFileDialog()
    dialog.setFileMode(QFileDialog.ExistingFile)  # Allow selection of only existing files
    # Combine all extensions into a single filter
    all_extensions = " ".join(f"*{ext}" for ext in FileFormats.FF_ALL_CONVERT)
    dialog.setNameFilter(f"Supported Files ({all_extensions})")

    if dialog.exec_() == QFileDialog.Accepted:
        selected_files = dialog.selectedFiles()
        if selected_files:
            return Path(selected_files[0])  # Return the first selected file

    return None


def ask_file_type() -> SourceSelect:
    """
    Asks the user whether they are loading from a file sequence or a single file.

    Returns:
        str: "file_sequence", "single_file", or "cancel" based on user choice.
    """
    msg_box = QMessageBox()
    msg_box.setWindowTitle("File Selection")
    msg_box.setText("Are you loading from a file sequence or a single file?")
    msg_box.addButton("File Sequence", QMessageBox.YesRole)
    msg_box.addButton("Single File", QMessageBox.NoRole)
    cancel_button = msg_box.addButton("Cancel", QMessageBox.RejectRole)

    choice = msg_box.exec_()
    if msg_box.clickedButton() == cancel_button:
        return SourceSelect.CANCEL
    return SourceSelect.SEQUENCE if choice == 0 else SourceSelect.SINGLE

def ask_input_source() -> SourceSelect | InputSelectSources:
    """
    Asks the user to select an input source.

    Returns:
        str: One of the InputSelectSources options ("Red", "Sony", "Arri", "RGB_Sequence", "Mov")
             or "cancel" if the user cancels the dialog.
    """
    msg_box = QMessageBox()
    msg_box.setWindowTitle("Input Source Selection")
    msg_box.setText("Please select the input source:")
    logo = QPixmap(ResourceLoader.open_vp_cal_logo())
    msg_box.setIconPixmap(
        logo.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))

    rgb_seq_button = msg_box.addButton("RGB Sequence", QMessageBox.AcceptRole)
    red_button = msg_box.addButton("Red", QMessageBox.AcceptRole)
    sony_button = msg_box.addButton("Sony", QMessageBox.AcceptRole)
    arri_button = msg_box.addButton("Arri", QMessageBox.AcceptRole)
    mov_button = msg_box.addButton("Mov", QMessageBox.AcceptRole)
    cancel_button = msg_box.addButton("Cancel", QMessageBox.RejectRole)

    msg_box.exec_()
    clicked = msg_box.clickedButton()

    if clicked == cancel_button:
        return SourceSelect.CANCEL
    elif clicked == red_button:
        return InputSelectSources.RED
    elif clicked == sony_button:
        return InputSelectSources.SONY
    elif clicked == arri_button:
        return InputSelectSources.ARRI
    elif clicked == rgb_seq_button:
        return InputSelectSources.RBG_SEQUENCE
    elif clicked == mov_button:
        return InputSelectSources.MOV
    return SourceSelect.CANCEL


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
