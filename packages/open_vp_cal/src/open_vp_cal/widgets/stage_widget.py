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

The module contains the Mode, View and Controller for the Stage Widget which allows us to control which of the LED walls
we are working on
"""
import re

from PySide6.QtWidgets import QVBoxLayout, QPushButton, QWidget, QListView, QInputDialog, QMessageBox, \
    QAbstractItemView, QMenu
from PySide6.QtGui import QStandardItemModel, QStandardItem, QColor, QAction
from PySide6.QtCore import Signal, Slot, QObject, Qt, QItemSelectionModel

from open_vp_cal.core import constants
from open_vp_cal.led_wall_settings import LedWallSettings
from open_vp_cal.project_settings import ProjectSettings
from open_vp_cal.widgets.timeline_widget import TimelineLoader


class LedWallTimelineLoader(LedWallSettings):
    """
    Class: LedWallTimelineLoader

    A specialization of the LedWallSettings which allows us to override the sequence loader class
    """
    def __init__(self, project_settings: ProjectSettings, name="Wall1"):
        super().__init__(project_settings, name)
        self._sequence_loader_class = TimelineLoader


class StageModel(QStandardItemModel):
    """
    Model for Led Wall items
    """

    def __init__(self, project_settings: ProjectSettings):
        super().__init__()
        self.project_settings = project_settings

    def add_led_wall(self, wall_name: str):
        """
        Add a LED wall to the model

        Args:
            wall_name (str): name of the wall to add
        """
        wall = QStandardItem(wall_name)
        self.appendRow(wall)

    def remove_led_wall(self, index: int):
        """
        Remove a LED wall from the model

        Args:
            index (int): index of the wall to remove
        """
        self.removeRow(index)

    def data(self, index, role=Qt.DisplayRole):
        """
        Override QStandardItemModel data method for custom roles

        Args:
            index (QModelIndex): index of the item
            role (int): role of the data

        Returns:
            any: data based on the role
        """
        if not index.isValid():
            return None
        if role == Qt.DisplayRole:
            # Return a custom display name based on the item's data
            original_name = super().data(index, role)

            led_wall = self.project_settings.get_led_wall(original_name)
            if led_wall.sequence_loader.file_name:
                return f"{original_name} -> {led_wall.sequence_loader.file_name}"

            return f"{original_name}"

        if role == Qt.BackgroundRole:
            original_name = super().data(index, Qt.DisplayRole)
            led_wall = self.project_settings.get_led_wall(original_name)
            if led_wall.sequence_loader.file_name:
                return QColor(*constants.GREEN)
            return QColor(*constants.RED)

        return super().data(index, role)


class StageView(QWidget):
    """
    View for Led Wall items
    """
    led_wall_selected = Signal(list)
    led_wall_copied = Signal()
    led_wall_added = Signal()
    led_wall_removed = Signal()
    led_wall_reset = Signal()
    led_wall_load_sequence = Signal()
    led_wall_clear_sequence = Signal()
    verification_wall_added = Signal()

    def __init__(self, model: StageModel):
        super().__init__()

        self.model = model

        self.list_view = QListView()
        self.list_view.setModel(self.model)
        self.list_view.setSelectionMode(QAbstractItemView.ExtendedSelection)
        self.list_view.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.list_view.selectionModel().selectionChanged.connect(self.on_led_wall_selected)

        self.list_view.setContextMenuPolicy(Qt.CustomContextMenu)
        self.list_view.customContextMenuRequested.connect(self.show_context_menu)

        self.add_button = QPushButton("Add LED Wall")
        self.remove_button = QPushButton("Remove LED Wall")

        layout = QVBoxLayout()
        layout.addWidget(self.list_view)
        layout.addWidget(self.add_button)
        layout.addWidget(self.remove_button)

        self.setLayout(layout)

    def show_context_menu(self, position) -> None:
        """ Shows the right click content menu at the given position with the relevant actions added

        Args:
            position: The position of the menu
        """
        context_menu = QMenu(self)
        add_action = QAction("Add LED Wall", context_menu)
        copy_action = QAction("Copy LED Wall", context_menu)
        remove_action = QAction("Remove LED Wall", context_menu)
        load_sequence_action = QAction("Load Plate Sequence", context_menu)
        clear_sequence_action = QAction("Clear Plate Sequence", context_menu)
        verification_add_action = QAction("Add Verification Wall", context_menu)
        reset_settings_action = QAction("Reset Wall Settings", context_menu)

        index = self.list_view.indexAt(position)
        if index.isValid():
            display = index.data(Qt.DisplayRole)
            original_name = display.split(" -> ")[0]
            led_wall = self.model.project_settings.get_led_wall(original_name)
            has_sequence = bool(led_wall.sequence_loader.file_name)

            load_sequence_action.setEnabled(not has_sequence)
            clear_sequence_action.setEnabled(has_sequence)
        else:
            # No valid item: disable context actions
            for act in (copy_action, remove_action, load_sequence_action,
                        clear_sequence_action, verification_add_action,
                        reset_settings_action):
                act.setEnabled(False)

        context_menu.addAction(add_action)
        context_menu.addAction(copy_action)
        context_menu.addAction(remove_action)
        context_menu.addSeparator()
        context_menu.addAction(load_sequence_action)
        context_menu.addAction(clear_sequence_action)
        context_menu.addSeparator()
        context_menu.addAction(verification_add_action)
        context_menu.addSeparator()
        context_menu.addAction(reset_settings_action)

        add_action.triggered.connect(self.add_led_wall)
        copy_action.triggered.connect(self.copy_led_wall)
        remove_action.triggered.connect(self.remove_led_wall)
        load_sequence_action.triggered.connect(self.load_sequence)
        verification_add_action.triggered.connect(self.add_verification_wall)
        reset_settings_action.triggered.connect(self.reset_settings)
        clear_sequence_action.triggered.connect(self.clear_sequence)

        # Map the position to global coordinates for the menu
        global_position = self.list_view.viewport().mapToGlobal(position)
        context_menu.exec_(global_position)

    @Slot()
    def reset_settings(self) -> None:
        """ Emits a signal when the reset LED wall settings action is triggered
        """
        self.led_wall_reset.emit()

    @Slot()
    def clear_sequence(self) -> None:
        """ Emits a signal when the reset LED wall settings action is triggered
        """
        self.led_wall_clear_sequence.emit()

    @Slot()
    def copy_led_wall(self) -> None:
        """ Emits a signal when the copy LED wall action is triggered
        """
        self.led_wall_copied.emit()

    @Slot()
    def load_sequence(self) -> None:
        """ Emits a signal when the load sequence action is triggered
        """
        self.led_wall_load_sequence.emit()

    @Slot()
    def add_verification_wall(self) -> None:
        """ Emits a signal when the add verification wall action is triggered
        """
        self.verification_wall_added.emit()

    @Slot()
    def add_led_wall(self) -> None:
        """ Emits a signal when the add LED wall action is triggered
        """
        self.led_wall_added.emit()

    @Slot()
    def remove_led_wall(self) -> None:
        """ Emits a signal when the remove LED wall action is triggered
        """
        self.led_wall_removed.emit()

    @Slot()
    def on_led_wall_selected(self) -> None:
        """ Emit a signal when a LED wall is selected
        """
        self.led_wall_selected.emit(
            self.selected_led_walls()
        )

    def selected_led_walls(self) -> [str]:
        """ Get the names of the selected LED walls

        Returns: list of LED wall names
        """
        indexes = self.list_view.selectionModel().selectedIndexes()
        wall_names = []
        for index in indexes:
            wall_names.append(self.model.itemFromIndex(index).text())
        return wall_names


class StageController(QObject):
    """
    Controller for Led Wall items
    """

    led_wall_added = Signal(str)
    led_wall_removed = Signal(str)
    led_wall_copied = Signal(str, str)
    led_wall_reset = Signal(str)
    current_led_wall_changed = Signal(str)
    led_wall_selection_changed = Signal(list)
    led_wall_verification_added = Signal(str)

    def __init__(self, model: StageModel, view: StageView):
        super().__init__()
        self.model = model
        self.view = view

        self.view.add_button.clicked.connect(self.add_led_wall_dialog)
        self.view.remove_button.clicked.connect(self.remove_led_wall)
        self.view.led_wall_selected.connect(self.led_wall_selected)
        self.view.led_wall_copied.connect(self.copy_led_wall_dialog)
        self.view.led_wall_added.connect(self.add_led_wall_dialog)
        self.view.led_wall_removed.connect(self.remove_led_wall)
        self.view.led_wall_reset.connect(self.reset_led_wall)
        self.view.verification_wall_added.connect(self.add_verification_wall)

    @Slot()
    def add_led_wall(self, led_wall: LedWallSettings):
        """ Add a LED wall to the model

        Args:
            led_wall: The LED wall we want to add
        """
        self.model.add_led_wall(led_wall.name)
        last_index = self.model.index(self.model.rowCount() - 1, 0)
        self.view.list_view.setCurrentIndex(last_index)

    @Slot()
    def reset_led_wall(self):
        """ Resets the settings for the currently selected led wall """
        current_index = self.view.list_view.currentIndex().row()
        if current_index >= 0:
            wall_name = self.model.item(current_index).text()
            self.led_wall_reset.emit(wall_name)

    @Slot()
    def add_verification_wall(self):
        """ Add a verification wall to the model based on the current selection """
        current_index = self.view.list_view.currentIndex().row()
        if current_index >= 0:
            wall_name = self.model.item(current_index).text()
            self.led_wall_verification_added.emit(wall_name)


    @Slot()
    def add_led_wall_dialog(self) -> None:
        """ Add a LED wall to the model using a dialog box to provide the name which is validated
        """
        while True:
            text, status = QInputDialog.getText(self.view, 'Input Dialog', 'Enter LED Wall name:')
            if status:
                if re.match("^[A-Za-z0-9_]*$", text):
                    self.led_wall_added.emit(text)
                    break

                QMessageBox.critical(
                    self.view, 'Invalid Name',
                    'The name can only contain alphanumeric characters and underscores.'
                )
            else:
                break

    @Slot()
    def copy_led_wall_dialog(self) -> None:
        """ Copy an LED wall to the model using a dialog box to provide the name which is validated
        """
        current_led_wall_selection = self.selected_led_walls()
        if len(current_led_wall_selection) != 1:
            QMessageBox.critical(
                self.view, 'Invalid Selection',
                'Please select one LED wall to copy.'
            )
            return
        current_wall = current_led_wall_selection[0]
        while True:
            text, status = QInputDialog.getText(self.view, 'Input Dialog', 'Enter LED Wall name:')
            if status:
                if re.match("^[A-Za-z0-9_]*$", text):
                    self.led_wall_copied.emit(current_wall, text)
                    break

                QMessageBox.critical(
                    self.view, 'Invalid Name',
                    'The name can only contain alphanumeric characters and underscores.'
                )
            else:
                break

    @Slot()
    def remove_led_wall(self) -> None:
        """ Remove a LED wall from the model based on the current selection
        """
        current_index = self.view.list_view.currentIndex().row()
        if current_index >= 0:
            wall_name = self.model.item(current_index).text()
            message = f"Are You Sure You Want To Remove {wall_name} ?"
            reply = QMessageBox.question(
                None, "Confirm Removal" , message,
                QMessageBox.Yes | QMessageBox.No, QMessageBox.No)
            if reply == QMessageBox.Yes:
                self.model.remove_led_wall(current_index)
                self.led_wall_removed.emit(wall_name)

    def remove_all_walls(self) -> None:
        """ Remove all LED walls from the model
        """
        indexes = range(self.model.rowCount())
        for index in reversed(indexes):
            wall_name = self.model.item(index, 0).text()
            self.model.remove_led_wall(index)
            self.led_wall_removed.emit(wall_name)

    def selected_led_walls(self) -> [str]:
        """ Get the names of the selected LED walls

        Returns: list of LED wall names
        """
        return self.view.selected_led_walls()

    @Slot(str)
    def led_wall_selected(self, wall_names: [str]) -> None:
        """ Emit a signal when a LED wall is selected

        Args:
            wall_names: The names of the selected LED walls
        """
        if wall_names:
            self.current_led_wall_changed.emit(wall_names[0])
        self.led_wall_selection_changed.emit(wall_names)

    def select_led_walls(self, wall_names: [str]) -> None:
        """ Select the LED walls with the given names in the ui

        Args:
            wall_names: The names of the LED walls to select
        """
        selection_model = self.view.list_view.selectionModel()
        selection_model.clearSelection()
        indexes = range(self.model.rowCount())
        for index in reversed(indexes):
            name = self.model.data(self.model.index(index, 0), Qt.DisplayRole)
            for wall_name in wall_names:
                if wall_name in name:
                    selection_model.select(self.model.index(index, 0), QItemSelectionModel.Select)
