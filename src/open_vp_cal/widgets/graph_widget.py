"""
Module: line_graph
This module uses the pyqtgraph library along with PySide6 to create an interactive line graph widget.
"""
from typing import Dict, Tuple, List

from PySide6.QtWidgets import QVBoxLayout, QWidget, QListView, QHBoxLayout, QAbstractItemView, QCheckBox
from PySide6.QtCore import Qt, QStringListModel, Signal, QObject, QSize, Slot, QItemSelectionModel
import pyqtgraph as pg
from pyqtgraph import exporters

from open_vp_cal.core import constants, utils
from open_vp_cal.core.constants import Results
from open_vp_cal.led_wall_settings import LedWallSettings


class LineGraphModel(QObject):
    """
    Class: LineGraphModel
    This class represents the data model for a line graph. It contains the data points for the graph.
    """
    data_changed = Signal()

    def __init__(self, data_lines: Dict[str, Dict[str, Tuple]] = None) -> None:
        """
        Initialize the LineGraphModel instance.

        :param data_lines: A dictionary containing the name of the line, the colour, and the data points.
        :type data_lines: Dict[str, Dict[str, Tuple]]
        """
        super().__init__()
        if not data_lines:
            data_lines = {}
        self._data_lines = data_lines

    def get_data(self):
        """
        Retrieve the data of the line graph.

        :return: The data lines of the line graph.
        """
        return self._data_lines

    def set_data(self, data_lines):
        """
        Set the data lines of the line graph and emit a signal that the data has changed.

        :param data_lines: A dictionary containing the name of the line, the colour, and the data points.
        :return: None
        """
        self._data_lines = data_lines
        self.data_changed.emit()

    def clear_data(self) -> None:
        """ Clears all the data from the model
        """
        self._data_lines = {}


class DisplayFiltersWidget(QWidget):
    """
    Class Which contains the display filters for the line graph
    """

    def __init__(self):
        super().__init__()
        self.target_display_checkbox = QCheckBox("Target")
        self.target_display_checkbox.setChecked(True)
        self.pre_cal_display_checkbox = QCheckBox("PreCal")
        self.pre_cal_display_checkbox.setChecked(True)
        self.post_cal_display_checkbox = QCheckBox("PostCal")
        self.post_cal_display_checkbox.setChecked(True)
        self.target_display_checkbox.stateChanged.connect(self.plot)
        self.pre_cal_display_checkbox.stateChanged.connect(self.plot)
        self.post_cal_display_checkbox.stateChanged.connect(self.plot)

        self.display_filter_layout = QHBoxLayout()
        self.display_filter_layout.addWidget(self.target_display_checkbox)
        self.display_filter_layout.addWidget(self.pre_cal_display_checkbox)
        self.display_filter_layout.addWidget(self.post_cal_display_checkbox)

    def plot(self) -> None:
        """
        Needs to be implemented in the subclass and is called each time the display filters are changed
        """
        raise NotImplementedError("This method must be implemented by a subclass.")

    def get_display_filters(self) -> List:
        """ Based on the state of the checkboxes, we return a list of the display filters we want to plot

        Returns: A list of the display filters we want to plot

        """
        display_filters = []
        if self.target_display_checkbox.isChecked():
            display_filters.append(constants.DisplayFilters.TARGET)
        if self.pre_cal_display_checkbox.isChecked():
            display_filters.append(constants.DisplayFilters.PRE_CAL)
        if self.post_cal_display_checkbox.isChecked():
            display_filters.append(constants.DisplayFilters.POST_CAL)
        return display_filters


class LineGraphView(DisplayFiltersWidget):
    """
    Class: LineGraphView
    This class represents the view for a line graph. It is responsible for the visual representation of the line graph.
    """

    def __init__(self, model: LineGraphModel,
                 max_scale: int = 1, default_scale: int = 0.125, plot_reference: bool = True,
                 display_plot_labels: bool = False) -> None:
        """
        Initialize the LineGraphView instance.

        :param model: The data model for the line graph.
        :type model: LineGraphModel
        """
        super().__init__()

        self.display_plot_labels = display_plot_labels
        self.plot_reference = plot_reference
        self._model = model

        # Create a PlotWidget instance
        self.graph_widget = pg.PlotWidget()

        # Create a QListView instance
        self.list_view = QListView()
        self.list_view.setSelectionMode(QAbstractItemView.ExtendedSelection)

        # Set up the layout
        self.main_layout = QVBoxLayout()
        self.horizontal_layout = QHBoxLayout()
        self.horizontal_layout.addWidget(self.list_view)
        self.horizontal_layout.addWidget(self.graph_widget)
        self.main_layout.addLayout(self.horizontal_layout)

        # Add The Display Filter Layout
        self.main_layout.addLayout(self.display_filter_layout)

        self.setLayout(self.main_layout)

        # Create a QStringListModel instance for the list view
        self.list_model = QStringListModel()
        self.list_view.setModel(self.list_model)

        # Update the list view with the line labels
        self.update_list_model()

        # Set the default PlotItem
        self.plot_item = self.graph_widget.getPlotItem()

        # Set the maximum range and view range limits
        self.max_scale = max_scale
        self.decimal_points = ".4f"
        self.default_scale = default_scale
        self.plot_item.setRange(xRange=(0, self.default_scale), yRange=(0, self.default_scale), padding=0)
        self.plot_item.getViewBox().setLimits(xMin=0, xMax=self.max_scale, yMin=0, yMax=self.max_scale)

        # Set the labels
        self.plot_item.setLabels(left='Y', bottom='X')

        # Plot all lines initially
        self.plot_initialize()

    def clear(self) -> None:
        """ Clears the ui and re-initialises the plot with the reference line
        """
        self.update_list_model()
        self.plot()

    def sizeHint(self):
        return QSize(300, 480)

    def plot(self) -> list[dict[str, tuple]]:
        """
        Plot the line graph based on the data lines in the model.

        :return: None
        """
        selected_lines = self.plot_initialize()

        display_filters = self.get_display_filters()

        for line in selected_lines:
            for display_filter in display_filters:
                if display_filter in line:
                    color, x_scaled, y_scaled = self.extract_scaled_data(line[display_filter])
                    self.plot_item.plot(
                        x_scaled, y_scaled, pen=pg.mkPen(color=color, width=3), symbol='o', symbolSize=5)
                    self.plot_labels(x_scaled, y_scaled)

        return selected_lines

    def extract_scaled_data(self, line) -> Tuple[List[float], List[float], List[float]]:
        """ Extracts the colour and scaled positional data from the line

        Args:
            line: the line we want to extract the data from

        Returns: a tuple of the colour, x scaled, and y scaled data
        """
        color, x_pos, y_pos = self.get_positions_and_color_from_data(line)
        x_scaled, y_scaled = self.get_scaled_positions(x_pos, y_pos)
        return color, x_scaled, y_scaled

    @staticmethod
    def get_positions_and_color_from_data(line) -> Tuple[List[float], List[float], List[float]]:
        """ Gets the positions and colour from the data

        Args:
            line: the data representing the line we want to draw

        Returns:
            A tuple of the colour, x positions, and y positions

        """
        x_pos, y_pos = line["plot_data"]
        color = line["line_colour"]
        return color, x_pos, y_pos

    def get_scaled_positions(self, x_pos: List[float], y_pos: List[float]) -> Tuple[List[float], List[float]]:
        """ Scales the positions to the max scale

        Args:
            x_pos: the x positions to scale
            y_pos: the y positions to scale

        Returns: A tuple of the scaled x positions and scaled y positions
        """
        x_scaled = [x * self.max_scale for x in x_pos]
        y_scaled = [y * self.max_scale for y in y_pos]
        return x_scaled, y_scaled

    def plot_labels(self, x_positions, y_positions) -> None:
        """ For each data point, we create a new TextItem, position it at the data point's location, and add it to the
        PlotItem.

        The TextItem displays the data point's coordinates as a tooltip.

        Args:
            x_positions: the list of positions in x we want to place labels
            y_positions: the list of positions in y we want to place labels
        """
        if self.display_plot_labels:
            for position in zip(x_positions, y_positions):
                text = (f"({position[0] / self.max_scale:{self.decimal_points}},"
                        f" {position[1] / self.max_scale:{self.decimal_points}})")
                text_item = pg.TextItem(text, color=[0, 0, 0])
                text_item.setPos(*position)
                self.plot_item.addItem(text_item)

    def plot_initialize(self) -> List[Dict[str, Tuple]]:
        """ Clears the plot and plots the reference line, and prepares the selected lines for plotting

        Returns:
            A list of the data ready for plotting based on the selected items in the list_view

        """
        self.plot_item.clear()
        # Plot the reference line
        if self.plot_reference:
            self.plot_reference_line()
        # Get selected lines
        selected_indexes = self.list_view.selectedIndexes()
        selected_lines = [self._model.get_data()[index.data()] for index in selected_indexes]
        return selected_lines

    def plot_reference_line(self):
        """
        Plot a white line that runs from 0 to 1 and is always present.

        :return: None
        """
        self.plot_item.plot([0, self.max_scale], [0, self.max_scale], pen=pg.mkPen(color=[255, 255, 255]))

    def update_list_model(self) -> None:
        """ Updates the list widget model with the names of the curves stored in the data model
        """
        self.list_model.setStringList(list(self._model.get_data().keys()))

    def keyPressEvent(self, event):
        """
        Handle key press events.

        :param event: The key event.
        :type event: QKeyEvent
        :return: None
        """
        if event.key() == Qt.Key_F:
            # On 'F' key press, fit the view to display all curves
            self.plot_item.getViewBox().autoRange()

    def export_plot(self, filename: str) -> None:
        """ Export the plot to an image file.

        :param filename: The name of the file to export the plot to.
        :type filename: str
        :return: None
        """
        exporters.ImageExporter(self.graph_widget.plotItem).export(filename)


class EotfAnalysisView(LineGraphView):
    """
    A view for plotting the EOTF of the LED walls, which we are calibrating, we want to see as linear a line as possible
    """

    def __init__(self, model: LineGraphModel,
                 max_scale: int = constants.PQ.PQ_MAX_NITS, default_scale: int = 1200, plot_reference: bool = True,
                 display_plot_labels: bool = False) -> None:

        super().__init__(model, max_scale, default_scale, plot_reference, display_plot_labels)

        self.red_check = QCheckBox('Red')
        self.green_check = QCheckBox('Green')
        self.blue_check = QCheckBox('Blue')

        # Set default state to checked
        self.red_check.setChecked(True)
        self.green_check.setChecked(True)
        self.blue_check.setChecked(True)

        # Connect checkboxes to the plot method
        self.red_check.stateChanged.connect(self.plot)
        self.green_check.stateChanged.connect(self.plot)
        self.blue_check.stateChanged.connect(self.plot)

        # Add checkboxes to horizontal layout
        layout = QHBoxLayout()
        layout.addWidget(self.red_check)
        layout.addWidget(self.green_check)
        layout.addWidget(self.blue_check)

        self.target_display_checkbox.setVisible(False)
        self.main_layout.addLayout(layout)

    def plot(self) -> List[Dict[str, Tuple]]:
        """
        Plot the line graph based on the data lines in the model.

        :return: None
        """
        selected_lines = self.plot_initialize()

        display_filters = self.get_display_filters()
        for item in selected_lines:
            for display_filter in display_filters:
                if display_filter not in item:
                    continue

                if self.red_check.isChecked():
                    self._plot_channel(item[display_filter]["red"])

                if self.green_check.isChecked():
                    self._plot_channel(item[display_filter]["green"])

                if self.blue_check.isChecked():
                    self._plot_channel(item[display_filter]["blue"])

        return selected_lines

    def _plot_channel(self, line):
        color, x_pos, y_pos = self.get_positions_and_color_from_data(line)

        x_scaled = [x * 100 for x in x_pos]
        y_scaled = [y * 100 for y in y_pos]

        self.plot_item.plot(x_scaled, y_scaled, pen=pg.mkPen(color=color, width=3), symbol='o',
                            symbolSize=5)
        self.plot_labels(x_scaled, y_scaled)


class BaseController:
    """
    A Base Controller To Hold Common Functions Across All The Controllers
    """
    @staticmethod
    def get_display_name_and_results(led_wall, pre_calibration) -> (str, dict):
        """ Helper function to get the display name and results for the LED wall based on if we are doing
            pre-calibration or post-calibration

        Args:
            led_wall: The LED wall we want to get the results for
            pre_calibration: Whether we want to get the pre-calibration results or the calibration results

        Returns: The display name and results for the given led wall based on if we are doing pre-calibration or
            calibration

        """
        if not led_wall.processing_results:
            return None, None

        if not pre_calibration:
            if not led_wall.processing_results.calibration_results:
                return None, None
            name = constants.DisplayFilters.POST_CAL
            results = led_wall.processing_results.calibration_results
        else:
            if not led_wall.processing_results.pre_calibration_results:
                return None, None
            name = constants.DisplayFilters.PRE_CAL
            results = led_wall.processing_results.pre_calibration_results
        return name, results


class LineGraphController(BaseController):
    """
    Class: LineGraphController
    This class represents the controller for a line graph. It coordinates the model and the view.
    """

    def __init__(self, model: LineGraphModel, view: LineGraphView) -> None:
        """
        Initialize the LineGraphController instance.

        :param model: The data model for the line graph.
        :type model: LineGraphModel
        :param view: The view for the line graph.
        :type view: LineGraphView
        """
        super().__init__()
        self._model = model
        self._view = view

        # Connect the list view's selection changed signal to the view's plot method
        self._view.list_view.selectionModel().selectionChanged.connect(self._view.plot)

        # Connect the model's data_changed signal to the view's plot method
        self._model.data_changed.connect(self._view.plot)
        self._model.data_changed.connect(self._view.update_list_model)

    @Slot()
    def led_wall_selection_changed(self, wall_names):
        """ Allows us to connect a signal to the controller which in forms us that the LED wall selection has changed.
        This is provided as a list of led wall names which we then mirror the selection in the bar chart list view.

        Args:
            wall_names: names of the LED walls, which have been selected

        """
        selection_model = self._view.list_view.selectionModel()
        selection_model.clearSelection()
        indexes = range(self._view.list_model.rowCount())
        for index in reversed(indexes):
            name = self._view.list_model.data(self._view.list_model.index(index), Qt.DisplayRole)
            for wall_name in wall_names:
                if wall_name in name:
                    selection_model.select(self._view.list_model.index(index), QItemSelectionModel.Select)

    def clear_project_settings(self) -> None:
        """ Clears all the data from the model, and resets the view
        """
        self._model.clear_data()
        self._view.clear()

    @staticmethod
    def get_target_colourspace_for_led_wall(led_wall):
        """ For the given led wall we get the colour space for the walls target gamut

        Args:
            led_wall:

        Returns:

        """
        return utils.get_target_colourspace_for_led_wall(led_wall)


class EOFTAnalysisController(LineGraphController):
    """ Controller for the EOTF analysis view, which contains specialised functionality for the EOTF analysis model

    """

    def update_model_with_results(self, led_wall: LedWallSettings, pre_calibration=False) -> None:
        """ Updates the model with the results from the LED wall, to display the EOTF analysis for the wall.
            We plot the inverse of x & y because the lut values are doing the opposite of what the screen is doing

        Args:
            led_wall: the LED wall, which we are updating the model with the results from
            pre_calibration: Whether we want to get the pre-calibration results or the calibration results
        """
        results_name, results = self.get_display_name_and_results(led_wall, pre_calibration)
        if not results_name or not results:
            return

        plot_data_red_y = results[Results.REFERENCE_EOTF_RAMP]
        plot_data_green_y = results[Results.REFERENCE_EOTF_RAMP]
        plot_data_blue_y = results[Results.REFERENCE_EOTF_RAMP]

        data_source = Results.POST_EOTF_RAMPS
        if pre_calibration:
            data_source = Results.PRE_EOTF_RAMPS

        plot_data_red_x = [max(0, primary[0]) for primary in results[data_source]]
        plot_data_green_x = [max(0, primary[1]) for primary in results[data_source]]
        plot_data_blue_x = [max(0, primary[2]) for primary in results[data_source]]

        data_lines = self._model.get_data()
        if led_wall.name not in data_lines:
            data_lines[led_wall.name] = {}

        if results_name not in data_lines[led_wall.name]:
            data_lines[led_wall.name][results_name] = {}

        # We plot the inverse of the data
        data_lines[led_wall.name][f"{results_name}"]["red"] = {
            "line_colour": [255, 0, 0], "plot_data": (plot_data_red_y, plot_data_red_x)
        }
        data_lines[led_wall.name][f"{results_name}"]["green"] = {
            "line_colour": [0, 255, 0], "plot_data": (plot_data_green_y, plot_data_green_x)
        }
        data_lines[led_wall.name][f"{results_name}"]["blue"] = {
            "line_colour": [0, 0, 255], "plot_data": (plot_data_blue_y, plot_data_blue_x)
        }
        self._model.set_data(data_lines)
