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

Module which is responsible for the models, view and controllers which make up the project settings ui components
"""
import json
import os
from typing import Union, List, Tuple

import colour
import numpy as np
from PySide6.QtCore import QObject, Signal, Qt
from PySide6.QtGui import QIcon, QPixmap
from PySide6.QtWidgets import (QWidget, QVBoxLayout, QGroupBox, QFormLayout, QComboBox, QSpinBox, QLineEdit, QLabel,
                               QCheckBox, QDoubleSpinBox, QPushButton, QDialog, QHBoxLayout, QDialogButtonBox,
                               QGridLayout, QMessageBox,
                               QFileDialog, QScrollArea, QApplication
                               )

from open_vp_cal.core import constants
from open_vp_cal.core import utils as core_utils
from open_vp_cal.core.resource_loader import ResourceLoader
from open_vp_cal.led_wall_settings import LedWallSettings
from open_vp_cal.project_settings import ProjectSettings
from open_vp_cal.widgets import utils
from open_vp_cal.widgets.utils import LockableWidget


class ProjectSettingsModel(ProjectSettings, QObject):
    """
    A class used to represent the Model in MVC structure.
    ...

    Attributes
    ----------
    data_changed : Signal
        a signal emitted when data is changed

    Methods
    -------
    set_data(key: str, value: object)
        Updates the stored data with the new value and emits the data_changed signal.

    Get_data(key: str)
        Retrieves the value of a given key from the stored data.
    """

    data_changed = Signal(str, object)
    led_wall_added = Signal(object)
    led_wall_removed = Signal(object)
    error_occurred = Signal(str)
    register_custom_gamut_from_load = Signal(str)

    def __init__(self, parent=None, led_wall_class=None):
        """
        Constructs all the necessary attributes for the Model object.

        Parameters
        ----------
        parent : QWidget, optional
            parent widget (default is None)
        """
        QObject.__init__(self)
        ProjectSettings.__init__(self)
        self.parent = parent
        self._led_wall_class = led_wall_class
        self.default_data = {}
        self.current_wall = None
        self.refresh_default_data()

    def refresh_default_data(self):
        """
        Refreshes the default data dictionary with the current default values from the LedWallSettings class
        """
        target_gamut_options = constants.ColourSpace.CS_ALL
        target_gamut_options.pop(target_gamut_options.index(constants.ColourSpace.CS_ACES))
        target_gamut_options.extend(self.project_custom_primaries.keys())
        default_led_wall = LedWallSettings(self, constants.DEFAULT)

        self.default_data = {
            constants.ProjectSettingsKeys.OUTPUT_FOLDER: {constants.DEFAULT: self.output_folder},
            constants.LedWallSettingsKeys.TARGET_GAMUT: {
                constants.OPTIONS: target_gamut_options,
                constants.DEFAULT: default_led_wall.target_gamut},
            constants.LedWallSettingsKeys.TARGET_EOTF: {
                constants.OPTIONS: constants.EOTF.EOTF_ALL, constants.DEFAULT: default_led_wall.target_eotf
            },
            constants.LedWallSettingsKeys.INPUT_PLATE_GAMUT: {
                constants.OPTIONS: constants.ColourSpace.CS_ALL, constants.DEFAULT: default_led_wall.input_plate_gamut
            },
            constants.LedWallSettingsKeys.NATIVE_CAMERA_GAMUT: {
                constants.OPTIONS: constants.CameraColourSpace.CS_ALL,
                constants.DEFAULT: default_led_wall.native_camera_gamut
            },
            constants.LedWallSettingsKeys.TARGET_TO_SCREEN_CAT: {
                constants.OPTIONS: constants.CAT.CAT_ALL_WITH_NONE,
                constants.DEFAULT: default_led_wall.target_to_screen_cat
            },
            constants.LedWallSettingsKeys.REFERENCE_TO_TARGET_CAT: {
                constants.OPTIONS: constants.CAT.CAT_ALL,
                constants.DEFAULT: default_led_wall.reference_to_target_cat
            },
            constants.LedWallSettingsKeys.MATCH_REFERENCE_WALL: {
                constants.DEFAULT: default_led_wall.match_reference_wall
            },
            constants.LedWallSettingsKeys.REFERENCE_WALL: {
                constants.OPTIONS: [""], constants.DEFAULT: default_led_wall.reference_wall
            },
            constants.LedWallSettingsKeys.AUTO_WB_SOURCE: {
                constants.DEFAULT: default_led_wall.auto_wb_source
            },
            constants.LedWallSettingsKeys.ENABLE_EOTF_CORRECTION: {
                constants.DEFAULT: default_led_wall.enable_eotf_correction
            },
            constants.LedWallSettingsKeys.ENABLE_GAMUT_COMPRESSION: {
                constants.DEFAULT: default_led_wall.enable_gamut_compression
            },
            constants.LedWallSettingsKeys.PRIMARIES_SATURATION: {
                constants.DEFAULT: default_led_wall.primaries_saturation,
                "min": 0.0, "max": 1.0, "step": 0.01, "decimals": 2
            },
            constants.LedWallSettingsKeys.TARGET_MAX_LUM_NITS: {
                constants.DEFAULT: default_led_wall.target_max_lum_nits,
                "min": 0, "max": constants.PQ.PQ_MAX_NITS, "step": 100
            },
            constants.LedWallSettingsKeys.NUM_GREY_PATCHES: {
                constants.DEFAULT: default_led_wall.num_grey_patches, "min": 0, "max": 100, "step": 1},
            constants.ProjectSettingsKeys.FRAMES_PER_PATCH: {
                constants.DEFAULT: self.frames_per_patch, "min": 0, "max": 100, "step": 1},
            constants.ProjectSettingsKeys.RESOLUTION_WIDTH: {constants.DEFAULT: 3840, "min": 0, "max": 7680, "step": 1},
            constants.ProjectSettingsKeys.RESOLUTION_HEIGHT: {constants.DEFAULT: 2160, "min": 0, "max": 2160, "step": 1},
            constants.ProjectSettingsKeys.FILE_FORMAT: {
                constants.OPTIONS: constants.FileFormats.FF_ALL, constants.DEFAULT: constants.FileFormats.FF_DEFAULT},
            constants.LedWallSettingsKeys.CALCULATION_ORDER: {
                constants.OPTIONS: constants.CalculationOrder.CO_ALL,
                constants.DEFAULT: default_led_wall.calculation_order
            },
            constants.LedWallSettingsKeys.AVOID_CLIPPING: {
                constants.DEFAULT: default_led_wall.avoid_clipping
            },
            constants.ProjectSettingsKeys.FRAME_RATE: {
                constants.DEFAULT: self.frame_rate, constants.OPTIONS: constants.FrameRates.FPS_ALL
            },
            constants.ProjectSettingsKeys.EXPORT_LUT_FOR_ACES_CCT: {
                constants.DEFAULT: self.export_lut_for_aces_cct
            },
            constants.ProjectSettingsKeys.EXPORT_LUT_FOR_ACES_CCT_IN_TARGET_OUT: {
                constants.DEFAULT: self.export_lut_for_aces_cct_in_target_out
            },
            constants.ProjectSettingsKeys.CUSTOM_LOGO_PATH: {constants.DEFAULT: self.custom_logo_path},
        }

    def set_data(self, key: str, value: object):
        """
        Updates the stored data with the new value and emits the data_changed signal.

        Parameters
        ----------
        key : str
            key of the data
        value : object
            new value of the data
        """
        if not hasattr(self, key):
            if not self.current_wall:
                return

            if not hasattr(self.current_wall, key):
                raise AttributeError(f"ProjectSettingsModel has no attribute {key}")
            setattr(self.current_wall, key, value)
        else:
            setattr(self, key, value)
        self.data_changed.emit(key, value)

        # Because we do not allow the user to set the target nits if working outside of PQ, we add special handling to
        # reflect these changes in the UI
        if self.current_wall:
            if key == constants.LedWallSettingsKeys.TARGET_EOTF or constants.LedWallSettingsKeys.TARGET_MAX_LUM_NITS:
                self.data_changed.emit(
                    constants.LedWallSettingsKeys.TARGET_MAX_LUM_NITS, self.current_wall.target_max_lum_nits)

    def get_data(self, key: str):
        """
        Retrieves the value of a given key from the stored data.

        Parameters
        ----------
        key : str
            key of the data

        Returns
        ----------
        object
            value of the data
        """
        if not hasattr(self, key):
            if not hasattr(self.current_wall, key):
                raise AttributeError(f"ProjectSettingsModel has no attribute {key}")
            return getattr(self.current_wall, key)

        return getattr(self, key)

    def load_from_json(self, json_file: str):
        """Loads the settings from a JSON file into this instance

        Args:
            json_file (str): The path to the JSON file.

        """
        project_settings = self._settings_from_json_file(json_file)
        for key, value in project_settings.items():
            self.set_data(key, value)

        for led_wall in self.led_walls:
            self.led_wall_added.emit(led_wall)

        self.refresh_default_data()
        for gamut_name in self.project_custom_primaries:
            self.register_custom_gamut_from_load.emit(gamut_name)

    def clear_project_settings(self):
        """ Clears the project settings back to the default settings and emits a signal to inform the views
        """
        super().clear_project_settings()
        for key, value in self._project_settings.items():
            self.data_changed.emit(key, value)

    def add_led_wall(self, name: str) -> Union[LedWallSettings, None]:
        """
        Adds a new wall to the project and emits a signal to inform the views

        Args:
            name: The name of the wall to add

        Returns: The newly created led wall

        """
        try:
            led_wall = super().add_led_wall(name)
        except ValueError as handled_exception:
            self.error_occurred.emit(str(handled_exception))
            return None

        return self._add_led_wall(led_wall)

    def _add_led_wall(self, led_wall: LedWallSettings) -> LedWallSettings:
        """ Adds a given led wall and emits a signal to inform the views

        Args:
            led_wall: The LED wall to add

        Returns: The newly created LED wall

        """
        self.current_wall = led_wall
        self.led_wall_added.emit(led_wall)
        for key in self._project_settings:
            self.data_changed.emit(key, self.get_data(key))
        for key in self.current_wall.attrs:
            self.data_changed.emit(key, self.get_data(key))
        return led_wall

    def copy_led_wall(self, existing_wall_name: str, new_name: str) -> LedWallSettings:
        """ Copies a given led wall and emits a signal to inform the views

        Args:
            existing_wall_name: The name of the LED wall to copy
            new_name: The name of the LED wall to be created

        Returns: The newly created LED wall

        """
        try:
            led_wall = super().copy_led_wall(existing_wall_name, new_name)
        except ValueError as handled_exception:
            self.error_occurred.emit(str(handled_exception))
            return None

        return self._add_led_wall(led_wall)

    def add_verification_wall(self, existing_wall_name: str) -> LedWallSettings:
        """ Adds the verification wall for the given wall and emits a signal to inform the views.

        Args:
            existing_wall_name: The name of the wall to add the verification wall for

        Returns:

        """
        try:
            led_wall = super().add_verification_wall(existing_wall_name)
        except ValueError as handled_exception:
            self.error_occurred.emit(str(handled_exception))
            return None

        return self._add_led_wall(led_wall)

    def remove_led_wall(self, name: str) -> None:
        """ Removes a wall from the project and emits a signal to inform the views

        Args:
            name: The name of the wall to remove
        """
        super().remove_led_wall(name)
        if not self.led_walls:
            self.current_wall = None
        self.led_wall_removed.emit(name)

    def set_current_wall(self, led_wall: Union[str, LedWallSettings]) -> None:
        """ Sets the current wall and emits a signal to inform the views

        Args:
            led_wall: The wall to set as the current wall
        """
        if isinstance(led_wall, str):
            for wall in self.led_walls:
                if wall.name == led_wall:
                    self.current_wall = wall
        else:
            self.current_wall = led_wall

        for key in self._project_settings:
            self.data_changed.emit(key, self.get_data(key))

        for key in self.current_wall.attrs:
            self.data_changed.emit(key, self.get_data(key))

    def reset_led_wall(self, name: str) -> None:
        super().reset_led_wall(name)
        self.set_current_wall(name)


class CustomGamutMatrixDialog(QDialog):
    """ A class which allows the user to enter a RGB_To_XYZ matrix for a custom gamut"""

    def __init__(self, title: str = "Custom Gamut from NPM Matrix", parent=None):
        """
        Args:
            title (str, optional): Window title. Defaults to "Matrix".
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.setWindowTitle(title)
        self.main_layout = QVBoxLayout()

        self.paste_icon = QPixmap(ResourceLoader.copy_icon())
        self.copy_button = QPushButton()
        self.copy_button.setIcon(QIcon(self.paste_icon))
        self.copy_button.clicked.connect(self.paste_matrix_from_clipboard)

        self.copy_format_combo = QComboBox()
        self.copy_format_combo.addItem(constants.CopyFormats.PYTHON)
        self.copy_format_combo.addItem(constants.CopyFormats.CSV)

        self.main_layout.addWidget(QLabel("Specify a NMP Matrix from RGB to CIE XYZ. eg. Camera RGB to XYZ."))
        self.custom_name_edit = QLineEdit()
        self.custom_name_edit.setText("")
        self.main_layout.addWidget(QLabel("Custom Name:"))
        self.main_layout.addWidget(self.custom_name_edit)

        self.grid_layout = QGridLayout()
        self.main_layout.addLayout(self.grid_layout)

        self.setLayout(self.main_layout)

        self.matrix_widgets = [[QDoubleSpinBox() for _ in range(3)] for _ in range(3)]

        for i in range(3):
            for j in range(3):
                spin_box = self.matrix_widgets[i][j]
                spin_box.setMinimum(-100)
                spin_box.setDecimals(6)
                spin_box.setMaximum(100)
                spin_box.setSingleStep(0.01)
                self.grid_layout.addWidget(spin_box, i, j)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)

        self.main_layout.addWidget(self.copy_format_combo)
        self.main_layout.addWidget(self.copy_button)
        self.main_layout.addWidget(button_box)

    def paste_matrix_from_clipboard(self):
        """ Pastes the matrix from the clipboard into the spin boxes

        """
        value = QApplication.clipboard().text()
        if not value:
            QMessageBox.warning(self, "Empty Clipboard", "The clipboard is empty")
            return
        mode = self.copy_format_combo.currentText()
        if mode == constants.CopyFormats.PYTHON:
            try:
                python_values = json.loads(value)
                if len(python_values) != 3 and len(python_values) != 9:
                    QMessageBox.warning(self,
                                        "Invalid Format",
                                        "Copied Text should be a nested 3x3 list or a single list of 9 values")
                    return
                if len(python_values) == 3:
                    for i in range(3):
                        for j in range(3):
                            self.matrix_widgets[i][j].setValue(python_values[i][j])
                else:
                    for i in range(3):
                        for j in range(3):
                            self.matrix_widgets[i][j].setValue(python_values[i * 3 + j])
            except json.JSONDecodeError:
                QMessageBox.warning(self, "Invalid Format", "The copied text is not in a valid format")
                return

        elif mode == constants.CopyFormats.CSV:
            csv_values = value.split(",")
            if len(csv_values) != 9:
                QMessageBox.warning(self, "Invalid Format", "The copied text is not in a valid format")
                return
            for i in range(3):
                for j in range(3):
                    self.matrix_widgets[i][j].setValue(float(csv_values[i * 3 + j]))

    def get_values(self) -> Tuple[List[List[float]], str]:
        """
        Returns the values of the spin boxes in a nested list.
        """
        matrix = [[spin_box.value() for spin_box in value] for value in self.matrix_widgets]
        return matrix, self.custom_name_edit.text()

    def validate(self) -> str:
        """ Validates the input values for the custom primaries

        Returns: error message if validation fails, empty string otherwise

        """
        values, name = self.get_values()
        grand_total = sum(sum(sublist) for sublist in values)
        if grand_total == 0:
            return "All values cannot be zero"
        if not name:
            return "Name cannot be empty"
        return ""

    def accept(self) -> None:
        """ Accepts the dialogue if the validation passes, otherwise shows a warning message
        """
        invalid = self.validate()
        if not invalid:
            super().accept()
        else:
            QMessageBox.warning(self, "Validation Error", invalid)


class CustomGamutDialog(QDialog):
    """
    A class used to represent the CustomGamutDialog.

    Methods
    -------
    init_ui()
        Initializes the UI components.
    Get_values()
        Returns the values of the spin boxes.
    """

    def __init__(self, model, parent=None):
        """
        Constructs all the necessary attributes for the CustomGamutDialog object.

        Parameters
        ----------
        parent : QWidget, optional
            parent widget (default is None)
        """
        super().__init__(parent)
        self.custom_name_edit = None
        self.grid_layout = None
        self.setWindowTitle('Custom Gamut for xy Primaries')
        self.model = model
        self.spin_boxes = {}
        self.init_ui()

    def init_ui(self):
        """
        Initializes the UI components of the dialogue.
        """
        default_values, default_name = self.get_defaults()

        layout = QFormLayout()
        self.grid_layout = QGridLayout()
        self.grid_layout.addWidget(QLabel("X"), 0, 1)
        self.grid_layout.addWidget(QLabel("Y"), 0, 2)

        # Add the line edit for the custom name at the top
        self.custom_name_edit = QLineEdit()
        self.custom_name_edit.setText(default_name)
        layout.addRow(QLabel("Custom Name:"), self.custom_name_edit)

        for count, color in enumerate(["R", "G", "B", "W"]):
            x_spinbox = QDoubleSpinBox()
            x_spinbox.setRange(0, 1)
            x_spinbox.setDecimals(5)
            x_spinbox.setValue(default_values[count][0])
            self.spin_boxes[f"{color}_x"] = x_spinbox
            self.grid_layout.addWidget(QLabel(color), count + 1, 0)
            self.grid_layout.addWidget(x_spinbox, count + 1, 1)

            y_spinbox = QDoubleSpinBox()
            y_spinbox.setRange(0, 1)
            y_spinbox.setDecimals(5)
            y_spinbox.setValue(default_values[count][1])
            self.spin_boxes[f"{color}_y"] = y_spinbox
            self.grid_layout.addWidget(y_spinbox, count + 1, 2)

        layout.addRow(self.grid_layout)

        # Add OK and Cancel buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addRow(button_box)

        self.setLayout(layout)

    def get_defaults(self) -> tuple[np.ndarray, str]:
        """ Returns the default values for the custom gamut if its already set, or it picks the existing colour space

        Returns: The default values for the custom gamut and the default name

        """
        primaries = colour.RGB_COLOURSPACES[constants.ColourSpace.CS_BT2020].primaries
        white_point = colour.RGB_COLOURSPACES[constants.ColourSpace.CS_BT2020].whitepoint
        white_point = white_point.reshape(1, -1)
        return np.concatenate((primaries, white_point), axis=0), ""

    def get_values(self) -> tuple[list[list[float, float]], str]:
        """
        Returns the values of the spin boxes in a nested list.
        """
        values = []
        for color in ["R", "G", "B", "W"]:
            values.append([self.spin_boxes[f"{color}_x"].value(), self.spin_boxes[f"{color}_y"].value()])

        return values, self.custom_name_edit.text()

    def validate(self) -> str:
        """ Validates the input values for the custom primaries

        Returns: error message if validation fails, empty string otherwise

        """
        values, name = self.get_values()
        grand_total = sum(sum(sublist) for sublist in values)
        if grand_total == 0:
            return "All values cannot be zero"
        if not name:
            return "Name cannot be empty"
        return ""

    def accept(self) -> None:
        """ Accepts the dialogue if the validation passes, otherwise shows a warning message
        """
        invalid = self.validate()
        if not invalid:
            super().accept()
        else:
            QMessageBox.warning(self, "Validation Error", invalid)


class ProjectSettingsView(LockableWidget):
    """
    A class used to represent the View in MVC structure.

    Methods
    -------
    init_ui()
        Initializes the UI components.
    """

    def __init__(self, parent=None):
        """
        Constructs all the necessary attributes for the View object.

        Parameters
        ----------
        parent : QWidget, optional
            parent widget (default is None)
        """
        super().__init__(parent)
        self.master_layout = None
        self.custom_logo_button = None
        self.custom_logo_path = None
        self.output_folder_button = None

        self.resolution_height = None
        self.resolution_width = None
        self.file_format = None
        self.frames_per_patch = None
        self.output_folder = None

        self.frame_rate = None
        self.export_lut_for_aces_cct_in_target_out = None
        self.export_lut_for_aces_cct = None
        self.init_ui()

    def init_ui(self):
        """
        Initializes the UI components.
        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        self._setup_patch_generation_widgets(main_layout)

        # Add the main widget to the scroll area
        scroll.setWidget(main_widget)

        # Set the scroll area as the main layout of the widget
        self.master_layout = QVBoxLayout(self)
        self.master_layout.addWidget(scroll)

    def _setup_patch_generation_widgets(self, main_layout: QVBoxLayout) -> None:
        """ Sets up the widgets for the patch generation section

        Args:
            main_layout: The main layout of the widget
        """
        self.output_folder = QLineEdit()
        self.output_folder_button = QPushButton("Browse")
        output_folder_layout = QHBoxLayout()
        output_folder_layout.addWidget(QLabel("Output Folder:"))
        output_folder_layout.addWidget(self.output_folder)
        output_folder_layout.addWidget(self.output_folder_button)
        main_layout.addLayout(output_folder_layout)

        self.export_lut_for_aces_cct = QCheckBox()
        self.export_lut_for_aces_cct_in_target_out = QCheckBox()
        aces_cct_layout = QFormLayout()
        aces_cct_layout.addRow(QLabel("Export LUT For ACEScct:"), self.export_lut_for_aces_cct)
        aces_cct_layout.addRow(QLabel("Export LUT For ACEScct In/Target Out:"),
                               self.export_lut_for_aces_cct_in_target_out)
        main_layout.addLayout(aces_cct_layout)

        self.file_format = QComboBox()
        self.resolution_width = QSpinBox()
        self.resolution_height = QSpinBox()
        self.frames_per_patch = QSpinBox()
        self.frame_rate = QComboBox()

        custom_logo_layout = QHBoxLayout()
        self.custom_logo_path = QLineEdit()
        self.custom_logo_button = QPushButton("Browse")
        custom_logo_layout.addWidget(self.custom_logo_path)
        custom_logo_layout.addWidget(self.custom_logo_button)

        patch_generation_group = QGroupBox("Patch Generation")
        patch_generation_layout = QFormLayout()
        patch_generation_layout.addRow(QLabel("File Format:"), self.file_format)
        patch_generation_layout.addRow(QLabel("Resolution: Width:"), self.resolution_width)
        patch_generation_layout.addRow(QLabel("Resolution: Height:"), self.resolution_height)
        patch_generation_layout.addRow(QLabel("Frames Per Patch:"), self.frames_per_patch)
        patch_generation_layout.addRow(QLabel("Frame Rate:"), self.frame_rate)
        patch_generation_layout.addRow(QLabel("Custom Logo:"), custom_logo_layout)
        patch_generation_group.setLayout(patch_generation_layout)

        main_layout.addWidget(patch_generation_group)


class PlateSettingsView(LockableWidget):
    """Widget for Plate Settings."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.master_layout = None
        self.input_plate_gamut = QComboBox()
        self.native_camera_gamut = QComboBox()
        self.match_reference_wall = QCheckBox()
        self.reference_wall = QComboBox()
        self.auto_wb_source = QCheckBox()
        self.external_white_point_file_button = None
        self.use_external_white_point = QCheckBox()
        self.external_white_point_file = QLineEdit()
        self.init_ui()

    def init_ui(self):
        """
        Initializes the UI components.
        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        plate_settings_group = QGroupBox("Plate Settings")
        plate_settings_layout = QFormLayout()
        plate_settings_layout.addRow(QLabel("Input Plate Gamut:"), self.input_plate_gamut)
        plate_settings_layout.addRow(QLabel("Native Camera Gamut:"), self.native_camera_gamut)
        plate_settings_layout.addRow(QLabel("Auto WB Source:"), self.auto_wb_source)
        plate_settings_group.setLayout(plate_settings_layout)
        main_layout.addWidget(plate_settings_group)

        reference_settings_group = QGroupBox("Reference Settings")
        reference_settings_layout = QFormLayout()
        reference_settings_layout.addRow(QLabel("Match Reference Wall:"), self.match_reference_wall)
        reference_settings_layout.addRow(QLabel("Reference Wall:"), self.reference_wall)
        reference_settings_group.setLayout(reference_settings_layout)
        main_layout.addWidget(reference_settings_group)

        self.external_white_point_file_button = QPushButton("Browse")
        external_white_point_file_layout = QHBoxLayout()
        external_white_point_file_layout.addWidget(self.external_white_point_file)
        external_white_point_file_layout.addWidget(self.external_white_point_file_button)

        external_white_point_group = QGroupBox("External White Point")
        external_white_point_layout = QFormLayout()
        external_white_point_layout.addRow(QLabel("Use External White Point:"), self.use_external_white_point)
        external_white_point_layout.addRow("External White Point File:", external_white_point_file_layout)
        external_white_point_group.setLayout(external_white_point_layout)
        main_layout.addWidget(external_white_point_group)

        # Add the main widget to the scroll area
        scroll.setWidget(main_widget)

        # Set the scroll area as the main layout of the widget
        self.master_layout = QVBoxLayout(self)
        self.master_layout.addWidget(scroll)



class LEDSettingsView(LockableWidget):
    """
    A class used to represent the View in MVC structure.

    Methods
    -------
    init_ui()
        Initializes the UI components.
    """

    def __init__(self, parent=None):
        """
        Constructs all the necessary attributes for the View object.

        Parameters
        ----------
        parent : QWidget, optional
            parent widget (default is None)
        """
        super().__init__(parent)
        self.master_layout = None
        self.gamut_dialog_button = None
        self.num_grey_patches = None
        self.primaries_saturation = None
        self.target_max_lum_nits = None
        self.target_eotf = None
        self.target_gamut = None
        self.init_ui()

    def init_ui(self):
        """
        Initializes the UI components.
        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        self._setup_target_specs_widgets(main_layout)

        self._setup_tool_settings_widgets(main_layout)

        # Add the main widget to the scroll area
        scroll.setWidget(main_widget)

        # Set the scroll area as the main layout of the widget
        self.master_layout = QVBoxLayout(self)
        self.master_layout.addWidget(scroll)

    def _setup_tool_settings_widgets(self, main_layout: QVBoxLayout) -> None:
        """ Sets up the widgets for the tool settings section

        Args:
            main_layout: The main layout of the widget
        """
        self.primaries_saturation = QDoubleSpinBox()
        self.num_grey_patches = QSpinBox()
        tool_settings_group = QGroupBox("Tool Settings")
        tool_settings_layout = QFormLayout()
        tool_settings_layout.addRow(QLabel("Primaries Saturation:"), self.primaries_saturation)
        tool_settings_layout.addRow(QLabel("Number of Grey Patches:"), self.num_grey_patches)
        tool_settings_group.setLayout(tool_settings_layout)
        main_layout.addWidget(tool_settings_group)

    def _setup_target_specs_widgets(self, main_layout: QVBoxLayout) -> None:
        """ Sets up the widgets for the target specs section

        Args:
            main_layout: The main layout of the widget
        """
        self.target_gamut = QComboBox()
        self.gamut_dialog_button = QPushButton('Add Custom Gamut')
        target_gamut_layout = QHBoxLayout()
        target_gamut_layout.addWidget(self.target_gamut)
        target_gamut_layout.addWidget(self.gamut_dialog_button)
        self.target_eotf = QComboBox()
        self.target_max_lum_nits = QSpinBox()
        target_specs_group = QGroupBox("Target Specs")
        target_specs_layout = QFormLayout()
        target_specs_layout.addRow(QLabel("Target Gamut:"), target_gamut_layout)
        target_specs_layout.addRow(QLabel("Target EOTF:"), self.target_eotf)
        target_specs_layout.addRow(QLabel("Target Max Lum (nits):"), self.target_max_lum_nits)
        target_specs_group.setLayout(target_specs_layout)
        main_layout.addWidget(target_specs_group)


class CalibrationSettingsView(LockableWidget):
    """
    A class used to represent the View in MVC structure.

    Methods
    -------
    init_ui()
        Initializes the UI components.
    """

    def __init__(self, parent=None):
        """
        Constructs all the necessary attributes for the View object.

        Parameters
        ----------
        parent : QWidget, optional
            parent widget (default is None)
        """
        super().__init__(parent)
        self.master_layout = None
        self.calculation_order = None
        self.enable_gamut_compression = None
        self.enable_eotf_correction = None
        self.reference_to_target_cat = None
        self.target_to_screen_cat = None
        self.avoid_clipping = None

        self.init_ui()

    def init_ui(self):
        """
        Initializes the UI components.
        """
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)

        self._setup_analysis_widgets(main_layout)

        # Add the main widget to the scroll area
        scroll.setWidget(main_widget)

        # Set the scroll area as the main layout of the widget
        self.master_layout = QVBoxLayout(self)
        self.master_layout.addWidget(scroll)

    def _setup_analysis_widgets(self, main_layout: QVBoxLayout) -> None:
        """ Sets up the widgets for the analysis section

        Args:
            main_layout: The main layout of the widget
        """
        self.reference_to_target_cat = QComboBox()
        self.enable_eotf_correction = QCheckBox()
        self.calculation_order = QComboBox()
        self.target_to_screen_cat = QComboBox()
        self.enable_gamut_compression = QCheckBox()
        self.avoid_clipping = QCheckBox()
        patch_analysis_group = QGroupBox("Calibration Setup")
        patch_analysis_layout = QFormLayout()
        patch_analysis_layout.addRow(QLabel("Reference To Target CAT:"), self.reference_to_target_cat)
        patch_analysis_layout.addRow(QLabel("Calculation Order:"), self.calculation_order)
        patch_analysis_layout.addRow(QLabel("Enable EOTF Correction:"), self.enable_eotf_correction)
        patch_analysis_layout.addRow(QLabel("Target To Screen CAT:"), self.target_to_screen_cat)
        patch_analysis_layout.addRow(QLabel("Enable Gamut Compression:"), self.enable_gamut_compression)
        patch_analysis_layout.addRow(QLabel("Avoid Clipping:"), self.avoid_clipping)
        patch_analysis_group.setLayout(patch_analysis_layout)
        main_layout.addWidget(patch_analysis_group)


class ProjectSettingsController(QObject):
    """
    A class used to represent the Controller in MVC structure.

    ...

    Methods
    -------
    on_model_data_changed(key: str, value: object)
        Updates the UI component corresponding to the data key when the data value changes.
    """

    def __init__(self,
                 project_settings_view,
                 led_settings_view,
                 led_analysis_settings_view,
                 plate_settings_view, model, parent=None):
        """
        Constructs all the necessary attributes for the Controller object.

        Parameters
        ----------
        project_settings_view: View
            instance of the View class
        model: Model
            instance of the Model class
        parent: QWidget, optional
            parent widget (default is None)
        """
        super().__init__(parent)
        self.project_settings_view = project_settings_view
        self.led_settings_view = led_settings_view
        self.led_analysis_settings_view = led_analysis_settings_view
        self.plate_settings_view = plate_settings_view
        self.model = model
        self.reference_wall_widget = self.plate_settings_view.reference_wall
        self.match_reference_wall_widget = self.plate_settings_view.match_reference_wall
        self.use_external_white_point_widget = self.plate_settings_view.use_external_white_point
        self.external_white_point_file_widget = self.plate_settings_view.external_white_point_file
        self.external_white_point_file_button_widget = self.plate_settings_view.external_white_point_file_button

        self.reference_wall_widget.setEnabled(
            self.match_reference_wall_widget.checkState() == Qt.Checked
        )

        # Connect view signals to model slots
        self.led_settings_view.target_gamut.currentIndexChanged.connect(
            lambda: self.model.set_data(
                constants.LedWallSettingsKeys.TARGET_GAMUT, self.led_settings_view.target_gamut.currentText())
        )
        self.led_settings_view.target_eotf.currentIndexChanged.connect(
            lambda: self.model.set_data(
                constants.LedWallSettingsKeys.TARGET_EOTF, self.led_settings_view.target_eotf.currentText())
        )
        self.led_settings_view.target_max_lum_nits.valueChanged.connect(
            lambda: self.model.set_data(
                constants.LedWallSettingsKeys.TARGET_MAX_LUM_NITS, self.led_settings_view.target_max_lum_nits.value())
        )
        self.led_settings_view.primaries_saturation.valueChanged.connect(
            lambda: self.model.set_data(
                constants.LedWallSettingsKeys.PRIMARIES_SATURATION, self.led_settings_view.primaries_saturation.value())
        )
        self.led_settings_view.num_grey_patches.valueChanged.connect(
            lambda: self.model.set_data(
                constants.LedWallSettingsKeys.NUM_GREY_PATCHES, self.led_settings_view.num_grey_patches.value()))

        self.project_settings_view.frames_per_patch.valueChanged.connect(
            lambda: self.model.set_data(
                constants.ProjectSettingsKeys.FRAMES_PER_PATCH, self.project_settings_view.frames_per_patch.value())
        )
        self.project_settings_view.frame_rate.currentIndexChanged.connect(
            lambda: self.model.set_data(
                constants.ProjectSettingsKeys.FRAME_RATE, float(self.project_settings_view.frame_rate.currentText()))
        )
        self.project_settings_view.export_lut_for_aces_cct.stateChanged.connect(
            lambda: self.model.set_data(
                constants.ProjectSettingsKeys.EXPORT_LUT_FOR_ACES_CCT,
                self.project_settings_view.export_lut_for_aces_cct.isChecked())
        )
        self.project_settings_view.export_lut_for_aces_cct_in_target_out.stateChanged.connect(
            lambda: self.model.set_data(
                constants.ProjectSettingsKeys.EXPORT_LUT_FOR_ACES_CCT_IN_TARGET_OUT,
                self.project_settings_view.export_lut_for_aces_cct_in_target_out.isChecked())
        )
        self.project_settings_view.output_folder.textChanged.connect(
            lambda: self.model.set_data(
                constants.ProjectSettingsKeys.OUTPUT_FOLDER, self.project_settings_view.output_folder.text()))
        self.project_settings_view.file_format.currentIndexChanged.connect(
            lambda: self.model.set_data(
                constants.ProjectSettingsKeys.FILE_FORMAT, self.project_settings_view.file_format.currentText()))
        self.project_settings_view.resolution_width.valueChanged.connect(
            lambda: self.model.set_data(
                constants.ProjectSettingsKeys.RESOLUTION_WIDTH, self.project_settings_view.resolution_width.value()))
        self.project_settings_view.resolution_height.valueChanged.connect(
            lambda: self.model.set_data(
                constants.ProjectSettingsKeys.RESOLUTION_HEIGHT, self.project_settings_view.resolution_height.value()))
        self.plate_settings_view.input_plate_gamut.currentIndexChanged.connect(
            lambda: self.model.set_data(
                constants.LedWallSettingsKeys.INPUT_PLATE_GAMUT, self.plate_settings_view.input_plate_gamut.currentText()))
        self.plate_settings_view.native_camera_gamut.currentIndexChanged.connect(
            lambda: self.model.set_data(constants.LedWallSettingsKeys.NATIVE_CAMERA_GAMUT,
                                        self.plate_settings_view.native_camera_gamut.currentText()))
        self.plate_settings_view.match_reference_wall.stateChanged.connect(
            lambda: self.model.set_data(
                constants.LedWallSettingsKeys.MATCH_REFERENCE_WALL,
                self.plate_settings_view.match_reference_wall.isChecked()))
        self.plate_settings_view.reference_wall.currentIndexChanged.connect(
            lambda: self.model.set_data(
                constants.LedWallSettingsKeys.REFERENCE_WALL, self.plate_settings_view.reference_wall.currentText()))
        self.plate_settings_view.use_external_white_point.stateChanged.connect(
            lambda: self.model.set_data(
                constants.LedWallSettingsKeys.USE_EXTERNAL_WHITE_POINT,
                self.plate_settings_view.use_external_white_point.isChecked()))
        self.plate_settings_view.external_white_point_file.textChanged.connect(
            lambda: self.model.set_data(
                constants.LedWallSettingsKeys.EXTERNAL_WHITE_POINT_FILE,
                self.plate_settings_view.external_white_point_file.text()))
        self.led_analysis_settings_view.target_to_screen_cat.currentIndexChanged.connect(
            lambda: self.model.set_data(constants.LedWallSettingsKeys.TARGET_TO_SCREEN_CAT,
                                        self.led_analysis_settings_view.target_to_screen_cat.currentText()))
        self.led_analysis_settings_view.reference_to_target_cat.currentIndexChanged.connect(
            lambda: self.model.set_data(constants.LedWallSettingsKeys.REFERENCE_TO_TARGET_CAT,
                                        self.led_analysis_settings_view.reference_to_target_cat.currentText()))
        self.plate_settings_view.auto_wb_source.stateChanged.connect(
            lambda: self.model.set_data(constants.LedWallSettingsKeys.AUTO_WB_SOURCE,
                                        self.plate_settings_view.auto_wb_source.isChecked()))
        self.led_analysis_settings_view.enable_gamut_compression.stateChanged.connect(
            lambda: self.model.set_data(constants.LedWallSettingsKeys.ENABLE_GAMUT_COMPRESSION,
                                        self.led_analysis_settings_view.enable_gamut_compression.isChecked()))
        self.led_analysis_settings_view.avoid_clipping.stateChanged.connect(
            lambda: self.model.set_data(constants.LedWallSettingsKeys.AVOID_CLIPPING,
                                        self.led_analysis_settings_view.avoid_clipping.isChecked()))
        self.led_analysis_settings_view.enable_eotf_correction.stateChanged.connect(
            lambda: self.model.set_data(constants.LedWallSettingsKeys.ENABLE_EOTF_CORRECTION,
                                        self.led_analysis_settings_view.enable_eotf_correction.isChecked()))
        self.led_analysis_settings_view.calculation_order.currentIndexChanged.connect(
            lambda: self.model.set_data(constants.LedWallSettingsKeys.CALCULATION_ORDER,
                                        self.led_analysis_settings_view.calculation_order.currentText()))
        self.project_settings_view.custom_logo_path.textChanged.connect(
            lambda: self.model.set_data(constants.ProjectSettingsKeys.CUSTOM_LOGO_PATH,
                                        self.project_settings_view.custom_logo_path.text()))

        self.led_settings_view.gamut_dialog_button.clicked.connect(self.open_custom_gamut_dialog)
        self.project_settings_view.output_folder_button.clicked.connect(self.open_folder_select_dialog)
        self.project_settings_view.custom_logo_button.clicked.connect(self.open_logo_select_dialog)
        self.plate_settings_view.external_white_point_file_button.clicked.connect(
            self.open_external_white_point_file_dialog)

        self.match_reference_wall_widget.stateChanged.connect(self.on_match_reference_wall_changed)
        self.model.led_wall_removed.connect(self.on_led_wall_removed)
        self.model.led_wall_added.connect(self.on_led_wall_added)
        self.model.register_custom_gamut_from_load.connect(self.add_custom_gamut_to_ui)

        # Connect model signals to view slots
        self.model.data_changed.connect(self.on_model_data_changed)

        for view in self.get_views():
            for key, widget in view.__dict__.items():
                self.update_widgets(key, widget)

        if not self.model.current_wall:
            for view in self.get_views():
                view.disable()

    def get_views(self) -> List[QWidget]:
        """ Returns a list of all the views in the controller

        Returns: List of views in the controller

        """
        return [
            self.project_settings_view,
            self.led_settings_view,
            self.led_analysis_settings_view,
            self.plate_settings_view]

    def update_widgets(self, key, widget) -> None:
        """ Updates the widgets with the default values from the model

        Args:
            key: Key of the widget name
            widget: Widget to update
        """
        if isinstance(widget, (QDoubleSpinBox, QSpinBox)):
            if isinstance(widget, QDoubleSpinBox):
                widget.setDecimals(self.model.default_data[key]["decimals"])
            widget.setMinimum(self.model.default_data[key]["min"])
            widget.setMaximum(self.model.default_data[key]["max"])
            widget.setSingleStep(self.model.default_data[key]["step"])
            widget.setValue(self.model.default_data[key][constants.DEFAULT])
        if isinstance(widget, QComboBox) and key in self.model.default_data:
            options = self.model.default_data[key][constants.OPTIONS]
            if callable(options):
                options = options()
            options = [str(option) for option in options]
            widget.addItems(options)
            widget.setCurrentText(str(self.model.default_data[key][constants.DEFAULT]))
        if isinstance(widget, QCheckBox) and key in self.model.default_data:
            widget.setChecked(self.model.default_data[key][constants.DEFAULT])
        if isinstance(widget, QLineEdit) and key in self.model.default_data:
            widget.setText(self.model.default_data[key][constants.DEFAULT])

    def lock_target_max_nits(self, led_wall_name: str) -> None:
        """ Locks the target max nits if we are not using PQ

        Args:
            led_wall_name: The name of the wall
        """
        led_wall = self.model.get_led_wall(led_wall_name)
        enabled = True
        if led_wall.target_eotf != constants.EOTF.EOTF_ST2084:
            enabled = False
        self.led_settings_view.target_max_lum_nits.setEnabled(enabled)

    def highlight_invalid_settings(self, led_wall_name: str) -> None:
        """ Highlights the invalid settings in the UI

        Args:
            led_wall_name: State of the checkbox
        """
        led_wall = self.model.get_led_wall(led_wall_name)
        valid = led_wall.has_valid_white_balance_options()
        error_style_sheet = f"border: 2px solid rgb({constants.RED[0]}, {constants.RED[1]}, {constants.RED[2]});"
        style_sheet = error_style_sheet if not valid else ""

        self.plate_settings_view.auto_wb_source.setStyleSheet(style_sheet if led_wall.auto_wb_source else "")
        self.match_reference_wall_widget.setStyleSheet(style_sheet if led_wall.match_reference_wall else "")
        self.use_external_white_point_widget.setStyleSheet(style_sheet if led_wall.use_external_white_point else "")
        self.external_white_point_file_widget.setStyleSheet(style_sheet if led_wall.use_external_white_point else "")
        self.external_white_point_file_button_widget.setStyleSheet(
            style_sheet if led_wall.use_external_white_point else "")

        if led_wall.match_reference_wall and not led_wall.reference_wall:
            self.reference_wall_widget.setStyleSheet(error_style_sheet)
        else:
            self.reference_wall_widget.setStyleSheet(style_sheet if led_wall.match_reference_wall else "")

    def open_logo_select_dialog(self) -> None:
        """ Opens a file dialogue to select a logo image, and sets the path in the model
        """
        filename, _ = QFileDialog.getOpenFileName(
            None, "Load Image", os.getenv('HOME'),
            "PNG (*.png);;TIF (*.tif);;JPG (*.jpg);;"
        )
        if not filename:
            return
        self.model.set_data(constants.ProjectSettingsKeys.CUSTOM_LOGO_PATH, filename)

    def open_external_white_point_file_dialog(self)-> None:
        """ Opens a file dialogue to select an image to use as a reference to an external white point analysis,
        and sets the path in the model
        """
        filename, _ = QFileDialog.getOpenFileName(
            None, "Load Image", os.getenv('HOME'),
            "EXR (*.exr);;"
        )
        if not filename:
            return
        self.model.set_data(constants.LedWallSettingsKeys.USE_EXTERNAL_WHITE_POINT, True)
        self.model.set_data(constants.LedWallSettingsKeys.EXTERNAL_WHITE_POINT_FILE, filename)

    def open_folder_select_dialog(self) -> None:
        """
        Opens a folder dialogue to select an output folder, and sets the path in the model
        """
        folder = utils.select_folder()
        if folder:
            self.model.set_data(constants.ProjectSettingsKeys.OUTPUT_FOLDER, folder)

    def open_custom_gamut_dialog(self) -> None:
        """
        Opens a dialogue to select custom gamut values, and sets the values in the model
        """
        dialog = CustomGamutDialog(self.model, self.project_settings_view)
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.get_values()

            primaries, gamut_name = values
            self.model.add_custom_primary(gamut_name, primaries)
            self.add_custom_gamut_to_ui(gamut_name)

    def open_custom_gamut_from_matrix_dialog(self) -> None:
        """
        Opens a dialogue to select custom gamut values, and sets the values in the model
        """
        dialog = CustomGamutMatrixDialog()
        if dialog.exec_() == QDialog.Accepted:
            values = dialog.get_values()

            matrix, gamut_name = values
            primaries, wp = core_utils.get_primaries_and_wp_for_XYZ_matrix(matrix)
            primaries = primaries.tolist()
            primaries.append(wp.tolist())
            self.model.add_custom_primary(gamut_name, primaries)
            self.add_custom_gamut_to_ui(gamut_name)

    def add_custom_gamut_to_ui(self, gamut_name: str) -> None:
        """ Adds the custom gamut to the list of available gamuts in the ui

        Args:
            gamut_name: The name of the gamut to add
        """
        self.led_settings_view.target_gamut.addItem(gamut_name)
        self.plate_settings_view.native_camera_gamut.addItem(gamut_name)

    # pylint: disable=W0613
    def on_led_wall_removed(self, removed_wall: str) -> None:
        """ When a wall is removed, this disables the UI if there are no walls left.
            We also update the reference wall options in the analysis settings view.
            We also remove any reference walls which where referencing the removed wall.

        Args:
            removed_wall: The wall that was removed
        """
        if not self.model.led_walls:
            for view in self.get_views():
                view.disable()

        index = self.reference_wall_widget.findText(removed_wall)

        if index >= 0:
            self.reference_wall_widget.removeItem(index)

        for led_wall in self.model.led_walls:
            if led_wall.reference_wall == removed_wall:
                led_wall.reference_wall = ""

    def on_led_wall_added(self, added_wall: LedWallSettings) -> None:
        """ When a wall is added, this disables the UI if there are no walls left.
        We also update the reference wall options in the analysis settings view.

        Args:
            added_wall: The wall that was added
        """
        self.reference_wall_widget.addItem(added_wall.name)
        self.handle_plate_settings_if_no_sequence_loaded_or_verification_wall(added_wall.name)
        self._disable_reference_wall_illegal_selection(added_wall.name)

    def on_sequence_loaded(self, led_wall: LedWallSettings) -> None:
        """ When a sequence is loaded, we enable the plate settings view if the sequence is loaded or not

        Args:
            led_wall: the led wall we want to check is the current wall
        """
        if self.model.current_wall.name == led_wall.name:
            self.handle_plate_settings_if_no_sequence_loaded_or_verification_wall(led_wall.name)

    def on_led_wall_selection_changed(self, selected_walls: List) -> None:
        """ When the selection of walls changes, this enables the UI if there is one wall selected.

        Args:
            selected_walls: The currently selected walls
        """
        if not selected_walls or len(selected_walls) != 1:
            for view in self.get_views():
                view.disable()
            return

        for view in self.get_views():
            view.enable()

        led_wall_name = selected_walls[0]
        self.handle_plate_settings_if_no_sequence_loaded_or_verification_wall(led_wall_name)

        self._disable_reference_wall_illegal_selection(led_wall_name)

    def handle_plate_settings_if_no_sequence_loaded_or_verification_wall(self, led_wall_name: str) -> None:
        """ For the given led wall name if there is no sequence loaded, we disable the plate settings view

        Args:
            led_wall_name: The name of the led wall to check
        """
        led_wall = self.model.get_led_wall(led_wall_name)
        if not led_wall.sequence_loader.file_name or led_wall.is_verification_wall:
            self.plate_settings_view.disable()
            if led_wall.is_verification_wall:
                self.project_settings_view.disable()
                self.led_settings_view.disable()
                self.led_analysis_settings_view.disable()
        else:
            self.plate_settings_view.enable()
            self.project_settings_view.enable()
            self.led_settings_view.enable()
            self.led_analysis_settings_view.enable()

    def _disable_reference_wall_illegal_selection(self, led_wall_name: str) -> None:
        """ We make the selected wall unselectable in the reference wall options, so that you cant select yourself.
            We also make sure that if wall 1 has set wall 2 as reference, wall 2 can't set wall 1

        Args:
            led_wall_name: The name of the LED wall we want to make not selectable
        """
        walls_to_disable = [led_wall_name]
        for led_wall in self.model.led_walls:
            if led_wall.name == led_wall_name:
                continue

            if led_wall.reference_wall == led_wall_name:
                walls_to_disable.append(led_wall.name)

        for idx in range(self.reference_wall_widget.count()):
            item_text = self.reference_wall_widget.itemText(idx)
            disabled = True
            if item_text in walls_to_disable:
                disabled = False
            self.reference_wall_widget.model().item(idx).setEnabled(disabled)

    def on_match_reference_wall_changed(self, state: int) -> None:
        """ Triggered when the state of the match_reference_wall checkbox is changed.
            We enable the reference wall options if the checkbox is checked, and disable them if it is not.

            When we disable it we also set the reference wall to none.

        Args:
            state: State of the checkbox
        """
        if state == Qt.Checked.value:
            self.reference_wall_widget.setEnabled(True)
        else:
            self.reference_wall_widget.setCurrentIndex(0)
            self.reference_wall_widget.setEnabled(False)

    def on_model_data_changed(self, key: str, value: object):
        """
        Updates the UI component corresponding to the data key when the data value changes.

        Parameters
        ----------
        key : str
            key of the data
        value : object
            new value of the data
        """
        if not self.model.current_wall:
            for view in self.get_views():
                view.disable()
            return

        for view in self.get_views():
            view.enable()

        for view in self.get_views():
            if hasattr(view, key):
                if isinstance(getattr(view, key), QComboBox):
                    if isinstance(value, LedWallSettings):
                        value = value.name
                    getattr(view, key).setCurrentText(str(value))
                elif isinstance(getattr(view, key), QLineEdit):
                    getattr(view, key).setText(value)
                elif isinstance(getattr(view, key), (QSpinBox, QDoubleSpinBox)):
                    getattr(view, key).setValue(value)
                elif isinstance(getattr(view, key), QCheckBox):
                    getattr(view, key).setChecked(value)

        # If we select a sequence which has no sequence loaded we handle the disabling of params
        self.handle_plate_settings_if_no_sequence_loaded_or_verification_wall(self.model.current_wall.name)
        self.highlight_invalid_settings(self.model.current_wall.name)
        self.lock_target_max_nits(self.model.current_wall.name)
