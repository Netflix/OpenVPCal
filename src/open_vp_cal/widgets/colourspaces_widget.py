"""
This module provides the Model, View and Controller for our colour spaces widgets, which allow us to plot and visualise
data against the CIE spectrum
"""
from typing import List

import pyqtgraph as pg
import numpy as np
import colour
from PySide6.QtGui import QColor
from PySide6.QtWidgets import QCheckBox

from open_vp_cal.imaging import imaging_utils, macbeth
from open_vp_cal.core import constants
from open_vp_cal.core import utils
from open_vp_cal.core.constants import Results
from open_vp_cal.led_wall_settings import LedWallSettings
from open_vp_cal.widgets.graph_widget import LineGraphView, LineGraphModel, LineGraphController


class CustomAxis(pg.AxisItem):
    """
    Class: CustomAxis, allows us to adjust the visual representation of the axis scale vs its actual scale, as the
    image of the cie spectrum needs to be much larger than 0-1 for visual display purposes to be readable,
    but the actual scale needs to be correct for the actual values
    """

    def tickStrings(self, values, scale, spacing) -> List[str]:
        # Transform values to be in the range [0, 1]
        values = [value / constants.COLOR_WIDGET_GRAPH_SCALE for value in values]
        # Use the default implementation to convert the transformed values to strings
        return [f"{value:.2f}" for value in values]


class ColorSpacesController(LineGraphController):
    """
    Class to control the updating of the colour spaces model
    """

    def update_model_with_results(self, led_wall: LedWallSettings, pre_calibration=False) -> None:
        """ Updates the model with the calibration results for the given led wall.
            We display the screen primaries, and the screen white point for each wall.

        Args:
            led_wall: The LED wall we want to update the model with
            pre_calibration: Whether we want to update the pre-calibration results the calibration results

        """
        self.update_model_with_led_targets([led_wall])
        results_name, results = self.get_display_name_and_results(led_wall, pre_calibration)
        if not results_name or not results:
            return

        if pre_calibration:
            primaries_key = Results.PRE_CALIBRATION_SCREEN_PRIMARIES
            white_point_key = Results.PRE_CALIBRATION_SCREEN_WHITEPOINT
            macbeth_key = Results.PRE_MACBETH_SAMPLES_XY
        else:
            primaries_key = Results.POST_CALIBRATION_SCREEN_PRIMARIES
            white_point_key = Results.POST_CALIBRATION_SCREEN_WHITEPOINT
            macbeth_key = Results.POST_MACBETH_SAMPLES_XY

        self._plot_results(
            led_wall, primaries_key, results, results_name, white_point_key, macbeth_key)

    def _plot_results(
            self,
            led_wall: LedWallSettings,
            primaries_key: str,
            results: dict, results_name: str, white_point_key: str, macbeth_key: str) -> None:
        """ Handles The Plotting Of The Results

        Args:
            led_wall: The led wall we want to plot the results for
            primaries_key: The name of the primaries key
            results: The results we want to plot from
            results_name: The name of the results in the model we want to plot
            white_point_key: The name of the white point key we want to plot
        """

        plot_data_x = []
        plot_data_y = []
        for primary in results[primaries_key]:
            plot_data_x.append(primary[0])
            plot_data_y.append(primary[1])
        plot_data_x.append(plot_data_x[0])
        plot_data_y.append(plot_data_y[0])

        data = self._model.get_data()

        if led_wall.name not in data:
            data[led_wall.name] = {}

        data[led_wall.name][results_name] = {
            "line_colour": utils.generate_color(f"{led_wall.name}_{results_name}"),
            "plot_data": (plot_data_x, plot_data_y),
            "white_point": results[white_point_key]
        }

        data[led_wall.name][constants.DisplayFilters.MACBETH][results_name] = results[macbeth_key]
        self._model.set_data(data)

    def update_model_with_led_targets(self, led_walls: List[LedWallSettings]) -> None:
        """ When the LED wall selection changes, we want to update the model so that the targets for each wall
            are displayed correctly based on if their target gamuts have changed or not

        Args:
            led_walls: The LED walls we want to update the model with
        """
        data = self._model.get_data()
        did_gamuts_change = False
        for led_wall in led_walls:
            target_gamut = led_wall.target_gamut
            if led_wall.name not in data:
                data[led_wall.name] = {}

            if constants.DisplayFilters.TARGET in data[led_wall.name]:
                if data[led_wall.name][constants.DisplayFilters.TARGET]["gamut_name"] == target_gamut:
                    break

            did_gamuts_change = True
            color_space = self.get_target_colourspace_for_led_wall(led_wall)
            target_macbeth = macbeth.get_rgb_references_for_color_checker(color_space, illuminant=None)
            target_macbeth_XYZ = np.apply_along_axis(
                lambda rgb: color_space.matrix_RGB_to_XYZ.dot(rgb), 1, target_macbeth
            )
            target_macbeth_xy = colour.XYZ_to_xy(target_macbeth_XYZ)

            if constants.DisplayFilters.MACBETH not in data[led_wall.name]:
                data[led_wall.name][constants.DisplayFilters.MACBETH] = {}

            data[led_wall.name][constants.DisplayFilters.MACBETH][constants.DisplayFilters.TARGET] = target_macbeth_xy

            data_x, data_y = [], []
            for primary in color_space.primaries:
                data_x.append(primary[0])
                data_y.append(primary[1])

            data_x.append(data_x[0])
            data_y.append(data_y[0])

            color = utils.generate_color(f"{led_wall.name}_{constants.DisplayFilters.TARGET}")
            data[led_wall.name][constants.DisplayFilters.TARGET] = {
                "gamut_name": target_gamut,
                "line_colour": color,
                "plot_data": (data_x, data_y),
                "white_point": color_space.whitepoint
            }

        if did_gamuts_change:
            self._model.set_data(data)


class ColorSpacesView(LineGraphView):
    """
    Class: ColorSpacesView
    This class represents the view for a line graph, with an added background image of the CIE spectrum
    """

    def __init__(self, model: LineGraphModel,
                 max_scale: int = constants.COLOR_WIDGET_GRAPH_SCALE,
                 default_scale: int = constants.COLOR_WIDGET_GRAPH_SCALE,
                 plot_reference: bool = False, display_plot_labels: bool = True) -> None:
        """
        Initialize the view

        Args:
            model: The line graph model we want to use
            max_scale: The maximum scale of the graph
            default_scale: The default scale of the graph we want to zoom in to
            plot_reference: Whether we want to plot the reference line or not
            display_plot_labels: Whether we want to display the plot labels or not
        """
        self.image_buf = imaging_utils.get_scaled_cie_spectrum_bg_image(max_scale)

        # Convert the image to a numpy array and rotate 90 degrees to match the graph widget
        self.image_np = imaging_utils.image_buf_to_np_array(self.image_buf)
        self.image_np = np.rot90(self.image_np, -1)
        self.image = pg.ImageItem()
        self.image.setPos(0, 0)

        super().__init__(model, max_scale, default_scale, plot_reference, display_plot_labels)

        self.macbeth_checkbox = QCheckBox("Macbeth")
        self.macbeth_checkbox.setChecked(False)
        self.macbeth_checkbox.stateChanged.connect(self.plot)

        self.display_filter_layout.addWidget(self.macbeth_checkbox)

        bg_color = QColor(255, 255, 255)  # Replace with your desired background colour
        self.graph_widget.setBackground(bg_color)

        # Add the image item to the plot
        self.plot_item.addItem(self.image)

        # Set the image to the correct position and scale it to the plot size
        # self.image.setImage(image_data)
        self.image.setImage(self.image_np)

        # Ensure the image is drawn below the plot curves
        self.image.setZValue(-1)

        self.plot_item.setAxisItems(
            {'bottom': CustomAxis(orientation='bottom'), 'left': CustomAxis(orientation='left')})

        spectral_locus_x, spectral_locus_y = utils.get_spectral_locus_positions(self.max_scale)
        self.spectral_locus_x = spectral_locus_x.tolist()
        self.spectral_locus_y = spectral_locus_y.tolist()
        self.planckian_x = None
        self.planckian_y = None

    def plot(self) -> None:
        selected_data = LineGraphView.plot(self)
        self.plot_item.addItem(self.image)
        self.plot_spectral_locus()
        display_filters = self.get_display_filters()
        self.plot_macbeth(selected_data, display_filters)
        for item in selected_data:
            for display_filter in display_filters:
                if display_filter in item:
                    white_point = item[display_filter]["white_point"]
                    self.plot_white_point(
                        item[display_filter]["line_colour"], "", white_point
                    )

    def plot_macbeth(self, selected_data, display_filters):
        """ Plots the macbeth data for the selected data

        Args:
            selected_data: The selected data we want to plot the macbeth data for
            display_filters: The display filters we want to plot the macbeth data for
        """
        if not self.macbeth_checkbox.isChecked():
            return

        plot_colour = [0, 0, 0]
        for item in selected_data:
            if constants.DisplayFilters.MACBETH in item:
                macbeth_data = item[constants.DisplayFilters.MACBETH]
                for display_filter in display_filters:
                    if display_filter in macbeth_data:
                        xy_data = macbeth_data[display_filter]
                        for xy_position in xy_data:
                            self.plot_white_point(
                                plot_colour, "", xy_position
                            )

    def plot_spectral_locus(self) -> None:
        """
        Plots a line which depicts the spectral locus
        """
        black_color = [0, 0, 0]
        self.plot_item.plot(
            self.spectral_locus_x, self.spectral_locus_y,
            pen=pg.mkPen(color=black_color, width=3)
        )

    def plot_planckian_locus(self) -> None:
        """ Plots the planckian locus and selected temperatures
        """
        black_color = [0, 0, 0]
        if not self.planckian_x or self.planckian_y:
            self.planckian_x, self.planckian_y = utils.get_planckian_locus_positions(
                self.max_scale
            )

        for i in constants.KELVIN_TEMPERATURES:
            cie_xy = colour.temperature.CCT_to_xy_CIE_D(i)
            scaled_x = float(cie_xy[0]) * self.max_scale
            scaled_y = float(cie_xy[1]) * self.max_scale
            text_label = f"{int(i)}K"
            text_item = pg.TextItem(text_label, color=black_color)
            text_item.setPos(scaled_x, scaled_y)
            self.plot_item.addItem(text_item)

        self.plot_item.plot(
            self.planckian_x, self.planckian_y,
            pen=pg.mkPen(color=black_color, width=3)
        )

    def plot_white_point(
            self,
            plot_colour: tuple[float, float, float],
            label: str,
            position: tuple[float, float, float],
            symbol: str = 'x') -> None:
        """ For the given colour, label and position, we plot a point on the graph that represents the white point

        Args:
            plot_colour: The colour of the point we want to draw
            label: A prefix label for the point
            position: the position in the graph we want to draw
            symbol: The symbol we want to use to draw the point

        """
        scaled_position = [pos * self.max_scale for pos in position]
        self.plot_item.plot(
            [scaled_position[0]], [scaled_position[1]],
            pen=pg.mkPen(color=plot_colour, width=3),
            symbolBrush=pg.mkBrush(plot_colour), symbol=symbol, symbolSize=10
        )

        text = f"({label} {position[0]:{self.decimal_points}}, {position[1]:{self.decimal_points}})"
        text_item = pg.TextItem(text, color=[0, 0, 0])
        text_item.setPos(*scaled_position)
        self.plot_item.addItem(text_item)


class WhitePointsController(LineGraphController):
    """
    Class to control the updating of the white points model
    """

    def update_model_with_results(self, led_wall: LedWallSettings, pre_calibration=False) -> None:
        """ Updates the model with the calibration results for the given led wall.
            Updating the model with the screen white point.

        Args:
            led_wall: The LED wall we want to update the model with
            pre_calibration: Whether we want to update the pre-calibration results the calibration results

        """
        results_name, results = self.get_display_name_and_results(led_wall, pre_calibration)
        if not results_name or not results:
            return

        if pre_calibration:
            white_point_key = Results.PRE_CALIBRATION_SCREEN_WHITEPOINT
        else:
            white_point_key = Results.POST_CALIBRATION_SCREEN_WHITEPOINT
        self._set_results(led_wall, results, results_name, white_point_key)

    def _set_results(self, led_wall: LedWallSettings, results: dict, results_name: str, white_point_key: str) -> None:
        """ Handles The Setting Of The Results

        Args:
            led_wall: The led wall we want to plot the results for
            results: The results we want to plot from
            results_name: The name of the results in the model we want to plot
            white_point_key: The name of the white point key we want to plot
        """
        white_points = self._model.get_data()
        if led_wall.name not in white_points:
            white_points[led_wall.name] = {}

        white_points[led_wall.name][results_name] = {
            "name": results_name,
            "position": results[white_point_key],
            "color": utils.generate_color(f"{led_wall.name}_{results_name}"),
            "symbol": "x"
        }
        color_space = self.get_target_colourspace_for_led_wall(led_wall)
        white_points[led_wall.name][constants.DisplayFilters.TARGET] = {
            "name": constants.DisplayFilters.TARGET,
            "position": color_space.whitepoint,
            "color": utils.generate_color(f"{led_wall.name}_{constants.DisplayFilters.TARGET}"),
            "symbol": "o"
        }
        self._model.set_data(white_points)


class WhitePointsView(ColorSpacesView):
    """
    Class: WhitePointsView
    This class view is a specialised version of the colour spaces view.

    It is designed to only draw the white points plotted
    """

    def __init__(self, model: LineGraphModel,
                 max_scale: int = constants.COLOR_WIDGET_GRAPH_SCALE,
                 default_scale: int = constants.COLOR_WIDGET_GRAPH_SCALE,
                 plot_reference: bool = False, display_plot_labels: bool = True) -> None:
        """
        Initialize the view

        Args:
            model: The line graph model we want to use
            max_scale: The maximum scale of the graph
            default_scale: The default scale of the graph we want to zoom in to
            plot_reference: Whether we want to plot the reference line or not
            display_plot_labels: Whether we want to display the plot labels or not
        """
        super().__init__(model, max_scale, default_scale, plot_reference, display_plot_labels)
        default_zoom_x = self.default_scale * 0.31
        default_zoom_y = self.default_scale * 0.34
        threshold = 20
        self.plot_item.setRange(
            xRange=(default_zoom_x - threshold, default_zoom_x + threshold),
            yRange=(default_zoom_y - threshold, default_zoom_y + threshold), padding=0
        )

    def plot(self):
        self.plot_item.clear()
        self.plot_planckian_locus()
        selected_indexes = self.list_view.selectedIndexes()
        data = [self._model.get_data()[index.data()] for index in selected_indexes]
        display_filters = self.get_display_filters()
        for item in data:
            for display_filter in display_filters:
                if display_filter not in item:
                    continue

                led_wall = item[display_filter]["name"]
                position = item[display_filter]["position"]
                color = item[display_filter]["color"]
                symbol = item[display_filter]["symbol"]
                self.plot_white_point(color, led_wall, position, symbol=symbol)

        self.plot_item.addItem(self.image)
