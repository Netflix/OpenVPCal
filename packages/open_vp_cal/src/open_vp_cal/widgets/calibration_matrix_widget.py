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

The module contains a simple view, model and controller to display the calibration matrix in a 3x3 grid.
Which can be copied to the clipboard.
"""
from typing import List
from PySide6.QtWidgets import QWidget, QGridLayout, QDoubleSpinBox, QVBoxLayout, QPushButton, QComboBox, \
    QApplication
from PySide6.QtCore import Signal, Slot, QObject
from PySide6.QtGui import QIcon, QPixmap

from open_vp_cal.core import constants
from open_vp_cal.core.resource_loader import ResourceLoader
from open_vp_cal.project_settings import ProjectSettings


class MatrixModel:
    """Model class for handling matrix data."""

    def __init__(self):
        """Initialize the model with an empty 3x3 matrix."""
        self.matrix = [[0.0 for _ in range(3)] for _ in range(3)]


class MatrixView(QWidget):
    """View class for displaying matrix data."""

    matrixCopied = Signal(List[List[float]])

    def __init__(self, title: str = "Matrix View", parent=None):
        """
        Args:
            title (str, optional): Window title. Defaults to "Matrix".
            parent (QWidget, optional): Parent widget. Defaults to None.
        """
        super().__init__(parent)
        self.copy_icon = QPixmap(ResourceLoader.copy_icon())
        self.setWindowTitle(title)
        self.main_layout = QVBoxLayout()
        self.matrix_option_combo = QComboBox()
        self.matrix_option_combo.addItem(constants.Results.TARGET_TO_SCREEN_MATRIX)
        self.matrix_option_combo.addItem(constants.Results.WHITE_BALANCE_MATRIX)
        self.matrix_option_combo.addItem(constants.Results.REFERENCE_TO_TARGET_MATRIX)
        self.matrix_option_combo.addItem(constants.Results.REFERENCE_TO_SCREEN_MATRIX)
        self.matrix_option_combo.addItem(constants.Results.REFERENCE_TO_INPUT_MATRIX)
        self.matrix_option_combo.addItem(constants.Results.REFERENCE_TO_XYZ_MATRIX)
        self.matrix_option_combo.addItem(constants.Results.CAMERA_WHITE_BALANCE_MATRIX)

        self.main_layout.addWidget(self.matrix_option_combo)
        self.grid_layout = QGridLayout()
        self.main_layout.addLayout(self.grid_layout)

        self.copy_button = QPushButton()
        self.copy_button.setIcon(QIcon(self.copy_icon))
        self.copy_button.clicked.connect(self.matrixCopied.emit)

        self.copy_format_combo = QComboBox()
        self.copy_format_combo.addItem(constants.CopyFormats.PYTHON)
        self.copy_format_combo.addItem(constants.CopyFormats.NUKE)
        self.copy_format_combo.addItem(constants.CopyFormats.CSV)
        self.main_layout.addWidget(self.copy_format_combo)
        self.main_layout.addWidget(self.copy_button)

        self.setLayout(self.main_layout)

        self.matrix_widgets = [[QDoubleSpinBox() for _ in range(3)] for _ in range(3)]

        for i in range(3):
            for j in range(3):
                spin_box = self.matrix_widgets[i][j]
                spin_box.setReadOnly(True)
                spin_box.setButtonSymbols(QDoubleSpinBox.NoButtons)
                spin_box.setMinimum(-100)
                spin_box.setDecimals(6)
                spin_box.setMaximum(100)
                self.grid_layout.addWidget(spin_box, i, j)


    @Slot()
    def update_matrix(self, matrix: List[List[float]]):
        """
        Update the entire displayed matrix.

        Args:
            matrix (List[List[float]]): New matrix data to display.
        """
        for i in range(3):
            for j in range(3):
                self.matrix_widgets[i][j].setValue(matrix[i][j])


class MatrixController(QObject):
    """Controller class for interfacing with MatrixModel."""

    matrix_updated = Signal(object)

    def __init__(self, view: MatrixView, model: MatrixModel, project_settings: ProjectSettings):
        """
        Args:
            model (MatrixModel): Matrix model to control.
        """
        super().__init__()
        self._model = model
        self._view = view
        self._project_settings = project_settings
        self._calibration_results = None

    def update_matrix(self, new_matrix: List[List[float]]):
        """
        Update the matrix in the model and emit a signal with the new matrix.

        Args:
            new_matrix (List[List[float]]): The new matrix data.
        """
        self._model.matrix = new_matrix
        self.matrix_updated.emit(self._model.matrix)

    def get_matrix(self) -> List[List[float]]:
        """
        Get the matrix from the model.

        Returns: The matrix data.
        """
        return self._model.matrix

    def copy_matrix_to_clipboard(self) -> None:
        """ Function which takes the matrix from the model, and based on the options selected in the UI
            we copy the data into the clip board into the relevant format

        """
        current_matrix = self.get_matrix()
        matrix_to_copy = str(current_matrix)
        current_format = self._view.copy_format_combo.currentText()
        if current_format == constants.CopyFormats.CSV:
            components = []
            for row in current_matrix:
                for idx in row:
                    components.append(str(idx))
            matrix_to_copy = ",".join(components)
        elif current_format == constants.CopyFormats.NUKE:
            matrix_to_copy = f"""
            ColorMatrix {{
             inputs 0
             matrix {{
                 {{ {current_matrix[0][0]:.10f}  {current_matrix[0][1]:.10f}  {current_matrix[0][2]:.10f}}}
                 {{ {current_matrix[1][0]:.10f}  {current_matrix[1][1]:.10f}  {current_matrix[1][2]:.10f}}}
                 {{ {current_matrix[2][0]:.10f}  {current_matrix[2][1]:.10f}  {current_matrix[2][2]:.10f}}}
               }}
             name "{self._view.matrix_option_combo.currentText()}"
             selected true
             xpos 0
             ypos 0
            }}
            """
        QApplication.clipboard().setText(matrix_to_copy)

    def on_led_wall_selection_changed(self, wall_names: List[str]) -> None:
        """ Allows us to connect a signal to the controller which in forms us that the LED wall selection has changed.
            This allows us to update the view based on the data from the first wall in the selection.

        Args:
            wall_names: names of the LED walls, which have been selected

        """
        if not wall_names:
            return

        led_wall = self._project_settings.get_led_wall(wall_names[0])
        if not led_wall.processing_results:
            return

        if not led_wall.processing_results.calibration_results:
            return

        self._calibration_results = led_wall.processing_results.calibration_results
        self.on_matrix_combo_changed(self._view.matrix_option_combo.currentText())

    def on_matrix_combo_changed(self, matrix_key: str) -> None:
        """ If the selected matrix we want to view changes and we have calibration results, we update the view
            with the relevant matrix
        Args:
            matrix_key: The name of the matrix we want to view

        Returns:

        """
        if self._calibration_results:
            matrix = self._calibration_results[matrix_key]
            self.update_matrix(matrix)
