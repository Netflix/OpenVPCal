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

The Module contains the models, views and controllers which allow us to draw a bar chart;
as an example, this can be useful for displaying how much each chanel is being compressed via the gamut compression
"""
from typing import Dict, List, Tuple

from PySide6.QtGui import QColor, Qt
from PySide6.QtWidgets import QAbstractItemView, QListView, QHBoxLayout, QVBoxLayout
from PySide6.QtCore import Signal, QObject, QStringListModel, QItemSelectionModel
import pyqtgraph as pg
from pyqtgraph import exporters

from open_vp_cal.led_wall_settings import LedWallSettings
from open_vp_cal.widgets.graph_widget import DisplayFiltersWidget, BaseController


# Model
class ChartModel(QObject):
    """A model to manage chart data."""

    data_changed = Signal()

    def __init__(self):
        super().__init__()
        self._data: Dict[str, Dict[str, int]] = {}

    def set_data(self, data: Dict[str, Dict[str, int]]) -> None:
        """Set data to the model.

        Args:
            data: The data we want to store in the model

        Returns:
            None
        """
        self._data = data
        self.data_changed.emit()

    def get_data(self) -> Dict[str, Dict[str, int]]:
        """Get data from the model

        Returns:
            The data stored in the model
        """
        return self._data

    def clear(self) -> None:
        """ Clears The Model
        """
        self._data = {}


class ChartView(DisplayFiltersWidget):
    """A view to display chart data and a list view."""

    def __init__(self, model: ChartModel):
        super().__init__()
        self._model = model
        self.list_view = None
        self.graph_widget = None
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize the UI.

        Returns:
            None
        """
        self.graph_widget = pg.PlotWidget()
        self.list_view = QListView()
        self.list_view.setSelectionMode(QAbstractItemView.ExtendedSelection)

        layout = QHBoxLayout()
        layout.addWidget(self.list_view)
        layout.addWidget(self.graph_widget)

        layout_vertical = QVBoxLayout()
        layout_vertical.addLayout(layout)
        layout_vertical.addLayout(self.display_filter_layout)
        self.target_display_checkbox.setVisible(False)
        self.setLayout(layout_vertical)

    def draw_chart(self, data_lists: List[Tuple[str, Dict[str, Dict[str, int]]]]) -> None:
        """Draw a bar chart with the given data."""
        self.graph_widget.clear()

        for index, item in enumerate(data_lists):
            name, data_list = item
            for i, (color, value) in enumerate(data_list.items()):
                q_color = QColor(color)
                q_color.setAlpha(255 // len(data_lists))
                width = 0.6 * (1 - index / len(data_list))
                bg1 = pg.BarGraphItem(x=[i], height=[value-1.0], width=width, brush=q_color)
                self.graph_widget.addItem(bg1)
                text = pg.TextItem(text=name, color=(1, 1, 1), anchor=(0.5, -1))
                text.setPos(i, value)
                self.graph_widget.addItem(text)

    def plot(self):
        data_list = []
        for index in self.list_view.selectionModel().selectedIndexes():
            name = index.data()
            data = self._model.get_data()
            display_filters = self.get_display_filters()
            for display_filter in display_filters:
                if display_filter in data[name]:
                    data_list.append((name, data[name][display_filter]))
        self.draw_chart(data_list)

    def export_plot(self, filename: str) -> None:
        """ Export the plot to an image file.

        :param filename: The name of the file to export the plot to.
        :type filename: str
        :return: None
        """
        exporters.ImageExporter(self.graph_widget.plotItem).export(filename)


class ChartController(BaseController):
    """A controller to manage the interaction between the model and the view."""

    def __init__(self, model: ChartModel, view: ChartView):
        super().__init__()
        self._model = model
        self._view = view
        self._list_model = QStringListModel()

        self._view.list_view.setModel(self._list_model)
        self._view.list_view.selectionModel().selectionChanged.connect(self.data_selected)
        self._model.data_changed.connect(self.update_list)

    def update_list(self) -> None:
        """Update the list view with the names of the data in the model.

        Returns:
            None
        """
        names = list(self._model.get_data().keys())
        self._list_model.setStringList(names)

    # pylint: disable=W0613
    def data_selected(self, selected, deselected) -> None:
        """Draw the selected data when the current selection changes."""
        self._view.plot()

    def on_led_wall_selection_changed(self, wall_names: List[str]) -> None:
        """ Allows us to connect a signal to the controller which in forms us that the LED wall selection has changed.
            This is provided as a list of led wall names which we then mirror the selection in the bar chart list view.

        Args:
            wall_names: names of the LED walls, which have been selected

        """
        selection_model = self._view.list_view.selectionModel()
        selection_model.clearSelection()
        indexes = range(self._list_model.rowCount())
        for index in reversed(indexes):
            name = self._list_model.data(self._list_model.index(index), Qt.DisplayRole)
            for wall_name in wall_names:
                if wall_name in name:
                    selection_model.select(self._list_model.index(index), QItemSelectionModel.Select)

    def update_model_with_results(self, led_wall: LedWallSettings, pre_calibration=False) -> None:
        """ Given a LedWallSettings object, we update the model with the results of the gamut compression.

        Args:
            led_wall: LedWallSettings object which contains the results of the gamut compression
            pre_calibration: Boolean which indicates if the results are from the pre calibration or post calibration

        """
        results_name, results = self.get_display_name_and_results(led_wall, pre_calibration)
        if not results:
            return

        data = self._model.get_data()
        if led_wall.name not in data:
            data[led_wall.name] = {}

        data[led_wall.name][results_name] = {
            "red": results["max_distances"][0],
            "green": results["max_distances"][1],
            "blue": results["max_distances"][2],
        }
        self._model.set_data(data)

    def clear(self) -> None:
        """Clear the model, list view, and graph view.

        Returns:
            None
        """
        self._model.clear()
        self._list_model.setStringList([])
        self._view.graph_widget.clear()
