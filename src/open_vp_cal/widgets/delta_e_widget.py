"""
Module which contains the models and views which are used to display the Delta E results
"""
from PySide6.QtGui import QColor, QKeySequence
from PySide6.QtWidgets import QLabel, QWidget, QTableView, QListView, QGridLayout, QApplication
from PySide6.QtCore import Qt, QAbstractListModel, QAbstractTableModel, QModelIndex, QItemSelectionModel, Slot, QEvent

from open_vp_cal.core import constants
from open_vp_cal.core.constants import Results
from open_vp_cal.led_wall_settings import LedWallSettings
from open_vp_cal.widgets.graph_widget import BaseController


class DeltaELEDWallListModel(QAbstractListModel):
    """Model for representing the list of LED walls."""

    def __init__(self):
        """
        Initializes the model
        """
        super().__init__()
        self.data_dict = {}

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Returns the number of rows in the model."""
        return len(self.data_dict)

    def set_data(self, data: dict):
        """Sets the data dictionary."""
        self.beginResetModel()
        self.data_dict = data
        self.endResetModel()

    def get_data(self) -> dict:
        """Returns the data dictionary."""
        return self.data_dict

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        """Returns the data at the specified model index."""
        if role == Qt.DisplayRole:
            return list(self.data_dict.keys())[index.row()]

    def clear(self):
        """Clears the model data."""
        self.beginResetModel()
        self.data_dict = {}
        self.endResetModel()


class DeltaEDataTableModel(QAbstractTableModel):
    """Model for representing the data tables of a selected LED wall."""

    def __init__(self, key: str, led_walls: list = None):
        """
        Initializes the model with the provided key and LED walls.

        Args:
            key (str): The key identifying the data to be displayed.
            led_walls (list, optional): The list of LED walls. Defaults to None.
        """
        super().__init__()
        self.key = key
        self.led_walls = led_walls or []

    def update_data(self, led_walls: list):
        """Updates the model data with the provided LED walls."""
        self.beginResetModel()
        self.led_walls = led_walls
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Returns the number of rows in the model."""
        return max(len(led_wall["data"].get(self.key, [])) for led_wall in self.led_walls) if self.led_walls else 0

    def columnCount(self, parent: QModelIndex = QModelIndex()) -> int:
        """Returns the number of columns in the model."""
        return len(self.led_walls)

    def data(self, index: QModelIndex, role: int = Qt.DisplayRole):
        """Returns the data at the specified model index."""
        if role == Qt.DisplayRole:
            led_wall = self.led_walls[index.column()]
            return led_wall["data"][self.key][index.row()]

        if role == Qt.BackgroundRole:
            led_wall = self.led_walls[index.column()]
            value = led_wall["data"][self.key][index.row()]
            if value < constants.DELTA_E_THRESHOLD_IMP:
                return QColor(*constants.GREEN)
            if constants.DELTA_E_THRESHOLD_IMP < value < constants.DELTA_E_THRESHOLD_JND:
                return QColor(*constants.YELLOW)
            return QColor(*constants.RED)

    def headerData(self, section: int, orientation: Qt.Orientation, role: int = Qt.DisplayRole):
        """Returns the header data for the specified section and orientation."""
        if role == Qt.DisplayRole and orientation == Qt.Horizontal:
            return self.led_walls[section]["name"]

    def clear(self):
        """Clears the model data."""
        self.beginResetModel()
        self.led_walls = []
        self.endResetModel()


class DeltaETableView(QTableView):
    """ A special table view which allows us to copy the data to the clipboard in a tab separated format

    """
    def keyPressEvent(self, event: QEvent) -> None:
        """ Override the key press event to allow us to copy the data to the clipboard

        Args:
            event: The key press event
        """
        if event.matches(QKeySequence.Copy):
            self.copy_selection()
        else:
            super().keyPressEvent(event)

    def copy_selection(self) -> None:
        """ Copy the selected data to the clipboard in a tab separated format
        """
        selection = self.selectionModel()
        indexes = selection.selectedIndexes()

        if len(indexes) < 1:
            return

        # Sort the indexes based on row and column number
        indexes.sort(key=lambda index: (index.row(), index.column()))

        # Use set to keep track of the rows that have been added
        rows_seen = set()
        clipboard_string = ""

        for index in indexes:
            data = index.data()
            if index.row() in rows_seen:
                clipboard_string += '\t' + str(data)
            else:
                clipboard_string += '\n' + str(data)
                rows_seen.add(index.row())

        # Remove the first newline character
        clipboard_string = clipboard_string[1:]

        QApplication.clipboard().setText(clipboard_string)


class DeltaEWidget(QWidget):
    """View for displaying the LED wall list and data tables."""

    def __init__(self):
        """Initializes the view and creates the UI elements."""
        super().__init__()
        self.layout = QGridLayout(self)
        self.list_view = QListView()
        self.list_view.setSelectionMode(QListView.ExtendedSelection)
        self.layout.addWidget(self.list_view, 0, 0, 3, 1)  # Span three rows

        self.column_labels = [QLabel(text) for text in [
            Results.DELTA_E_RGBW, Results.DELTA_E_EOTF_RAMP, Results.DELTA_E_MACBETH]]
        self.green_labels = [QLabel() for _ in range(3)]
        self.tables = [DeltaETableView() for _ in range(3)]
        for i, (col_label, table, green_label) in enumerate(zip(self.column_labels, self.tables, self.green_labels)):
            self.layout.addWidget(col_label, 0, i + 1)
            self.layout.addWidget(table, 1, i + 1)
            self.layout.addWidget(green_label, 2, i + 1)


class DeltaEController(BaseController):
    """Controller for managing user interactions with the view."""

    def __init__(self,
                 model: DeltaELEDWallListModel,
                 view: DeltaEWidget,
                 table_model_rgbw: DeltaEDataTableModel,
                 table_model_eotf: DeltaEDataTableModel,
                 table_model_macbeth: DeltaEDataTableModel):
        """
        Initializes the controller with the provided model, view, and table models.

        Args:
            model (LedWallListModel): The model representing the LED wall list.
            view (DeltaEView): The view displaying the LED wall list and data tables.
            table_model_rgbw (DataTableModel): The table model for the DELTA_E_RGBW data.
            table_model_eotf (DataTableModel): The table model for the DELTA_E_EOTF_RAMP data.
            table_model_macbeth (DataTableModel): The table model for the DELTA_E_MACBETH data.
        """
        self.model = model
        self.table_model_rgbw = table_model_rgbw
        self.table_model_eotf = table_model_eotf
        self.table_model_macbeth = table_model_macbeth

        self.view = view
        # Store the table models in a list for easy iteration
        self.table_models = [table_model_rgbw, table_model_eotf, table_model_macbeth]
        for table, table_model in zip(self.view.tables, self.table_models):
            table.setModel(table_model)

        self.view.list_view.setModel(model)
        self.view.list_view.selectionModel().selectionChanged.connect(self.update_data)
        self.view.list_view.selectionModel().selectionChanged.connect(self.update_best_delta_labels)

    def update_data(self, selected, deselected):
        """Updates the data tables based on the selected LED walls."""
        selected_walls = [self.model.data(index, Qt.DisplayRole) for index in self.view.list_view.selectedIndexes()]
        data_entries = [{'name': wall, 'data': self.model.data_dict[wall]['pre_cal']} for wall in selected_walls]
        for table_model in self.table_models:
            table_model.update_data(data_entries)

    def update_best_delta_labels(self, selected, deselected):
        """Updates the labels indicating the LED wall with the most green values."""
        selected_walls = [self.model.data(index, Qt.DisplayRole) for index in self.view.list_view.selectedIndexes()]
        data_entries = [{'name': wall, 'data': self.model.data_dict[wall]['pre_cal']} for wall in selected_walls]

        for i, table_model in enumerate(self.table_models):
            lowest_avg_value = float('inf')
            best_candidate = None
            for candidate, _ in enumerate(data_entries):
                avg_value = sum(data_entries[candidate]["data"][table_model.key]) / len(
                    data_entries[candidate]["data"][table_model.key])
                if avg_value < lowest_avg_value:
                    lowest_avg_value = avg_value
                    best_candidate = candidate
            if best_candidate is not None:
                self.view.green_labels[i].setText(f'Best: {data_entries[best_candidate]["name"]}')
            else:
                self.view.green_labels[i].setText('No Data')



    def clear(self):
        """Clear all data in the models."""
        self.model.clear()
        self.table_model_rgbw.clear()
        self.table_model_eotf.clear()
        self.table_model_macbeth.clear()

    @Slot()
    def led_wall_selection_changed(self, wall_names):
        """ Allows us to connect a signal to the controller which in forms us that the LED wall selection has changed.
        This is provided as a list of led wall names which we then mirror the selection in the  list view.

        Args:
            wall_names: names of the LED walls, which have been selected

        """
        if not wall_names:
            return

        selection_model = self.view.list_view.selectionModel()
        selection_model.clearSelection()
        indexes = range(self.model.rowCount())
        for index in reversed(indexes):
            name = self.model.data(self.model.index(index), Qt.DisplayRole)
            if name in wall_names:
                selection_model.select(self.model.index(index), QItemSelectionModel.Select)

    def update_model_with_results(self, led_wall: LedWallSettings, pre_calibration=False) -> None:
        """  Updates the model with the results from the calibration

        Args:
            led_wall: The LED wall which has been calibrated
            pre_calibration: Whether the calibration was pre or post calibration

        """
        results_name, results = self.get_display_name_and_results(led_wall, pre_calibration)
        if not results_name or not results:
            return

        data = self.model.get_data()
        if led_wall.name not in data:
            data[led_wall.name] = {}

        if results_name not in data[led_wall.name]:
            data[led_wall.name][results_name] = {}

        # Trim the last 6 patches from the macbeth as we don't display those in the swatches as we already have far move
        # grey ramps from our eotf
        macbeth_deltae_values = results[Results.DELTA_E_MACBETH][:-6]
        data[led_wall.name][results_name] = {
            Results.DELTA_E_RGBW: results[Results.DELTA_E_RGBW],
            Results.DELTA_E_EOTF_RAMP: results[Results.DELTA_E_EOTF_RAMP],
            Results.DELTA_E_MACBETH: macbeth_deltae_values,
        }

        self.model.set_data(data)
