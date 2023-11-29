"""
The module defines the main window for the application
"""
import json
import os
import sys
import tempfile
from typing import Tuple, Optional, List

from PySide6.QtGui import QIcon, QAction, QPixmap
from PySide6.QtWidgets import QMainWindow, QDockWidget, QMenu, QFileDialog, QMessageBox, QPushButton
from PySide6.QtCore import Qt, QObject, QEvent, Signal, QSettings, QDataStream, QFile, QIODevice, QByteArray, QTimer

from open_vp_cal.framework.auto_roi import AutoROIResults
from open_vp_cal.framework.configuraton import Configuration
from open_vp_cal.core import constants, utils, ocio_config
from open_vp_cal.core.constants import DEFAULT_PROJECT_SETTINGS_NAME
from open_vp_cal.core.resource_loader import ResourceLoader
from open_vp_cal.framework.generation import PatchGeneration
from open_vp_cal.framework.identify_separation import SeparationResults
from open_vp_cal.imaging import imaging_utils
from open_vp_cal.led_wall_settings import LedWallSettings
from open_vp_cal.framework.processing import Processing
from open_vp_cal.framework.validation import Validation
from open_vp_cal.project_settings import ProjectSettings
from open_vp_cal.widgets.bar_chart_widget import ChartModel, ChartController, ChartView
from open_vp_cal.widgets.calibration_matrix_widget import MatrixModel, MatrixView, MatrixController
from open_vp_cal.widgets.colourspaces_widget import ColorSpacesView, WhitePointsView, ColorSpacesController, \
    WhitePointsController
from open_vp_cal.widgets.delta_e_widget import DeltaELEDWallListModel, DeltaEDataTableModel, DeltaEWidget, \
    DeltaEController
from open_vp_cal.widgets.execution_widget import ExecutionView
from open_vp_cal.widgets.image_selection_widget import ImageSelectionWidget
from open_vp_cal.widgets.graph_widget import LineGraphModel, EotfAnalysisView, EOFTAnalysisController
from open_vp_cal.widgets.project_settings_widget import ProjectSettingsView, ProjectSettingsModel, \
    ProjectSettingsController, LEDSettingsView, CalibrationSettingsView, PlateSettingsView
from open_vp_cal.widgets.stage_widget import StageView, StageModel, StageController, \
    LedWallTimelineLoader
from open_vp_cal.widgets.swatch_analysis_widget import SwatchViewer
from open_vp_cal.widgets.timeline_widget import TimelineWidget, TimelineModel
from open_vp_cal.widgets.utils import select_folder

from spg.projectSettings import ProjectSettings as SPGProjectSettings
from spg.main import run_spg_pattern_generator
from stageassets.ledWall import LEDWall as SPGLedWall
from stageassets.ledPanel import LEDPanel as SPGLedPanel
from stageassets.rasterMap import RasterMap as SPGRasterMap
from stageassets.rasterMap import Mapping as SPGMapping


class EventFilter(QObject):
    """ A QObject which allows us to filter events which detect when the left and right arrow keys are pressed
    """
    left_arrow_pressed = Signal()
    right_arrow_pressed = Signal()

    def eventFilter(self, obj, event):
        if event.type() == QEvent.KeyPress:
            if event.key() == Qt.Key_Left:
                self.left_arrow_pressed.emit()
                return True
            if event.key() == Qt.Key_Right:
                self.right_arrow_pressed.emit()
                return True
        return super().eventFilter(obj, event)


class MainWindow(QMainWindow):
    """
    The main window for the application
    """

    def __init__(self, title):
        super().__init__()
        self.action_color_space_analysis = None
        self.action_eotf_analysis = None
        self.action_execution_window = None
        self.action_generate_patterns = None
        self.action_generate_spg_patterns = None
        self.action_image_selection = None
        self.action_led_settings_window = None
        self.action_calibration_settings_window = None
        self.action_load_layout = None
        self.action_load_project_layout = None
        self.action_load_analysis_layout = None
        self.action_load_project_settings = None
        self.action_calibration_matrix_view_window = None
        self.action_delta_e_analysis_window = None
        self.action_max_distance_analysis = None
        self.action_new_project_settings = None
        self.action_export_swatches = None
        self.action_plate_settings_window = None
        self.action_project_settings_window = None
        self.action_save_layout = None
        self.action_save_project_settings = None
        self.action_save_project_settings_as = None
        self.action_export_selection_as = None
        self.action_stage_view_window = None
        self.action_swatch_viewer = None
        self.action_timeline_window = None
        self.action_white_point_analysis = None
        self.colour_space_controller = None
        self.colour_spaces_model = None
        self.colour_spaces_view = None
        self.delta_e_led_wall_list_model = None
        self.delta_e_rgbw_model = None
        self.delta_e_eotf_ramp_model = None
        self.delta_e_macbeth_model = None
        self.delta_e_widget = None
        self.delta_e_controller = None
        self.dock_widget_color_space_analysis = None
        self.dock_widget_eotf_analysis = None
        self.dock_widget_execution = None
        self.dock_widget_image_selection = None
        self.dock_widget_led_settings = None
        self.dock_widget_calibration_settings = None
        self.dock_widget_plate_settings = None
        self.dock_widget_calibration_matrix = None
        self.dock_widget_delta_e_analysis = None
        self.dock_widget_max_distance_analysis = None
        self.dock_widget_project_settings = None
        self.dock_widget_stage_view = None
        self.dock_widget_swatch_analysis = None
        self.dock_widget_timeline = None
        self.dock_widget_white_point_analysis = None
        self.event_filter = None
        self.execution_view = None
        self.file_menu = None
        self.eotf_analysis_controller = None
        self.graph_view_model = None
        self.eotf_analysis_view = None
        self.image_selection_widget = None
        self.led_settings_view = None
        self.calibration_settings_view = None
        self.load_sequence_action = None
        self.matrix_controller = None
        self.matrix_model = None
        self.matrix_view = None
        self.max_distances_controller = None
        self.max_distances_model = None
        self.max_distances_view = None
        self.menu_bar = None
        self.plate_settings_view = None
        self.project_settings_controller = None
        self.project_settings_model = None
        self.project_settings_view = None
        self.stage_controller = None
        self.stage_model = None
        self.stage_view = None
        self.swatch_analysis_view = None
        self.timeline_model = None
        self.timeline_view = None
        self.white_point_controller = None
        self.white_point_model = None
        self.white_point_view = None
        self.windows_menu = None

        self._load_resources()
        self.setWindowTitle(title)

        # We Create A Sub Main Window To Allow Us To Set The Central Widgets and Dock Widgets Into It
        self.sub_main_window = QMainWindow()
        self.setCentralWidget(self.sub_main_window)

        # Create settings we can save out to disk
        self.settings = QSettings('Netflix', 'OpenVPCal')

        self.setDockNestingEnabled(True)

        # Initialize The UI
        self.init_ui()

        # Menu Bar
        self._setup_menus()

        # Finalize & Start Welcome Wizard
        self.project_settings_changed()
        self.display_welcome_wizard()

    def init_ui(self) -> None:
        """ Initializes the ui with all the Modes, Views and Controllers we need to operate the user experience
        of the application
        """
        self._create_dock_widgets()
        self._add_dock_widgets_to_main_window()
        self._setup_stage_and_project_settings_widgets()
        self._setup_color_space_analysis_widgets()
        self._setup_white_point_analysis_widgets()
        self._setup_eotf_analysis_widgets()
        self._setup_max_distances_widgets()
        self._setup_delta_e_widgets()
        self.image_selection_widget = ImageSelectionWidget(self.project_settings_model)
        self._setup_timeline_widgets()
        self._setup_execution_widget()
        self._setup_swatch_analysis_widgets()
        self._setup_matrix_calibration_widgets()
        self._set_widgets_into_dock_widgets()

    def _setup_stage_and_project_settings_widgets(self) -> None:
        """ Sets up the stage MVC and project settings MVC and connects them together, given they have a slightly
        intertwined relationship, the order in which objects are created and connected is important as to avoid signals
        firing before initialisation has finished or completed
        """
        # ProjectSettings
        self.project_settings_view = ProjectSettingsView()
        self.project_settings_model = ProjectSettingsModel(self, led_wall_class=LedWallTimelineLoader)
        self.project_settings_model.data_changed.connect(self.project_settings_changed)
        self.project_settings_model.error_occurred.connect(self.error_message)

        self.led_settings_view = LEDSettingsView()
        self.calibration_settings_view = CalibrationSettingsView()
        self.plate_settings_view = PlateSettingsView()

        # Stage
        self.stage_model = StageModel(self.project_settings_model)
        self.stage_view = StageView(self.stage_model)
        self.stage_controller = StageController(self.stage_model, self.stage_view)
        self.stage_controller.current_led_wall_changed.connect(self.project_settings_model.set_current_wall)
        self.stage_controller.led_wall_added.connect(self.project_settings_model.add_led_wall)
        self.stage_controller.led_wall_removed.connect(self.project_settings_model.remove_led_wall)
        self.stage_controller.led_wall_copied.connect(self.project_settings_model.copy_led_wall)
        self.stage_controller.led_wall_verification_added.connect(self.project_settings_model.add_verification_wall)
        self.stage_controller.led_wall_reset.connect(self.project_settings_model.reset_led_wall)
        self.stage_view.led_wall_load_sequence.connect(self.load_sequence)

        self.project_settings_model.led_wall_added.connect(self.stage_controller.add_led_wall)
        self.project_settings_controller = ProjectSettingsController(
            self.project_settings_view,
            self.led_settings_view,
            self.calibration_settings_view,
            self.plate_settings_view,
            self.project_settings_model
        )
        self.stage_controller.led_wall_selection_changed.connect(
            self.project_settings_controller.on_led_wall_selection_changed
        )

    def _setup_color_space_analysis_widgets(self) -> None:
        """ Sets up the MVC for the colour space analysis widgets and connects it to the stage controller
        """
        self.colour_spaces_model = LineGraphModel()
        self.colour_spaces_view = ColorSpacesView(
            self.colour_spaces_model)
        self.colour_space_controller = ColorSpacesController(self.colour_spaces_model, self.colour_spaces_view)
        self.stage_controller.led_wall_selection_changed.connect(
            self.colour_space_controller.led_wall_selection_changed)

    def _setup_white_point_analysis_widgets(self) -> None:
        """ Sets up the MVC for the white point analysis widgets and connects it to the stage controller
        """
        self.white_point_model = LineGraphModel()
        self.white_point_view = WhitePointsView(
            self.white_point_model)
        self.white_point_controller = WhitePointsController(self.white_point_model, self.white_point_view)
        self.stage_controller.led_wall_selection_changed.connect(
            self.white_point_controller.led_wall_selection_changed)

    def _setup_eotf_analysis_widgets(self) -> None:
        """ Sets up the MVC for the EOTF analysis widgets and connects it to the stage controller
        """
        # EOTF Analysis
        self.graph_view_model = LineGraphModel()
        self.eotf_analysis_view = EotfAnalysisView(self.graph_view_model)
        self.eotf_analysis_controller = EOFTAnalysisController(self.graph_view_model, self.eotf_analysis_view)
        self.stage_controller.led_wall_selection_changed.connect(
            self.eotf_analysis_controller.led_wall_selection_changed)

    def _setup_max_distances_widgets(self) -> None:
        """ Sets up the MVC for the max distances widgets and connects it to the stage controller
        """
        # Max Distances
        self.max_distances_model = ChartModel()
        self.max_distances_view = ChartView(self.max_distances_model)
        self.max_distances_controller = ChartController(self.max_distances_model, self.max_distances_view)
        self.stage_controller.led_wall_selection_changed.connect(
            self.max_distances_controller.on_led_wall_selection_changed
        )

    def _setup_delta_e_widgets(self) -> None:
        self.delta_e_led_wall_list_model = DeltaELEDWallListModel()
        self.delta_e_rgbw_model = DeltaEDataTableModel(constants.Results.DELTA_E_RGBW)
        self.delta_e_eotf_ramp_model = DeltaEDataTableModel(constants.Results.DELTA_E_EOTF_RAMP)
        self.delta_e_macbeth_model = DeltaEDataTableModel(constants.Results.DELTA_E_MACBETH)
        self.delta_e_widget = DeltaEWidget()
        self.delta_e_controller = DeltaEController(
            self.delta_e_led_wall_list_model,
            self.delta_e_widget,
            self.delta_e_rgbw_model,
            self.delta_e_eotf_ramp_model,
            self.delta_e_macbeth_model)

        self.stage_controller.led_wall_selection_changed.connect(
            self.delta_e_controller.led_wall_selection_changed)

    def _setup_timeline_widgets(self) -> None:
        """ Sets up the MVC for the timeline widgets and connects it to all the other widgets it needs to interact
        with.

        Returns:

        """
        self.event_filter = EventFilter()

        self.timeline_model = TimelineModel(self.project_settings_model)
        self.timeline_view = TimelineWidget(self.timeline_model, self.event_filter, self)

        self.event_filter.left_arrow_pressed.connect(self.timeline_view.step_back)
        self.event_filter.right_arrow_pressed.connect(self.timeline_view.step_forward)

        self.stage_controller.current_led_wall_changed.connect(self.timeline_model.led_wall_selection_changed)

        self.timeline_model.current_frame_changed_frame.connect(
            self.image_selection_widget.current_frame_changed
        )
        self.timeline_model.no_sequence_loaded.connect(self.image_selection_widget.clear)
        self.timeline_model.no_sequence_loaded.connect(self.timeline_view.disable)
        self.timeline_model.has_sequence_loaded.connect(self.timeline_view.enable)
        self.timeline_model.sequence_loaded.connect(self.sequence_loaded)
        self.timeline_model.sequence_loaded.connect(self.project_settings_controller.on_sequence_loaded)

    def _setup_execution_widget(self) -> None:
        """ Sets up the execution widget and connects it to all the other widgets it needs to interact
        """
        self.execution_view = ExecutionView()
        self.execution_view.analyse_button.pressed.connect(self.analyse)
        self.execution_view.calibrate_button.pressed.connect(self.calibrate)
        self.execution_view.export_button.pressed.connect(self.export)

    def _setup_swatch_analysis_widgets(self) -> None:
        """ Sets up the view and the controller for the swatch analysis widgets and connects it to the stage controller
        """
        self.swatch_analysis_view = SwatchViewer(self.project_settings_model)
        self.stage_controller.led_wall_selection_changed.connect(
            self.swatch_analysis_view.on_led_wall_selection_changed
        )

    def _setup_matrix_calibration_widgets(self) -> None:
        """ Sets up the view, model and controller for the matrix calibration widgets and connects it to the stage
        """
        self.matrix_view = MatrixView(title="Target To Wall Matrix")
        self.matrix_model = MatrixModel()
        self.matrix_controller = MatrixController(self.matrix_view, self.matrix_model, self.project_settings_model)
        self.matrix_controller.matrix_updated.connect(self.matrix_view.update_matrix)
        self.matrix_view.matrix_option_combo.currentTextChanged.connect(self.matrix_controller.on_matrix_combo_changed)

        self.matrix_view.matrixCopied.connect(
            self.matrix_controller.copy_matrix_to_clipboard
        )

        self.stage_controller.led_wall_selection_changed.connect(
            self.matrix_controller.on_led_wall_selection_changed
        )

    def _setup_menus(self) -> None:
        """ Sets up all the menus and actions for the main window
        """
        self._create_menus()
        self._create_actions_for_window_menu()
        self._create_actions_for_file_menu()
        self._add_actions_to_windows_menu()
        self._add_actions_to_file_menu()
        self._connect_window_menu_actions_to_dock_widget_vis()
        self._connect_file_menu_actions_to_functionality()

    def _load_resources(self) -> None:
        """ Loads the resources for the application, so they are available on a load, such as the icon and logo
        """

        self.icon = QIcon(ResourceLoader.icon())
        self.logo = QPixmap(ResourceLoader.open_vp_cal_logo())
        self.setWindowIcon(self.icon)

    def _connect_file_menu_actions_to_functionality(self) -> None:
        """ Connects the actions in the file menu to the functionality they should perform
        """
        self.load_sequence_action.triggered.connect(self.load_sequence)
        self.action_save_project_settings.triggered.connect(self.on_save_project)
        self.action_save_project_settings_as.triggered.connect(self.save_project_settings_as)
        self.action_export_selection_as.triggered.connect(self.export_selection_as)
        self.action_load_project_settings.triggered.connect(self.load_project_settings)
        self.action_new_project_settings.triggered.connect(self.new_project)
        self.action_generate_patterns.triggered.connect(self.generate_patterns)
        self.action_generate_spg_patterns.triggered.connect(self.generate_spg_patterns)
        self.action_save_layout.triggered.connect(self.on_save_layout)
        self.action_load_layout.triggered.connect(self.on_load_layout)
        self.action_load_project_layout.triggered.connect(self.load_project_layout)
        self.action_load_analysis_layout.triggered.connect(self.load_analysis_layout)
        self.action_export_swatches.triggered.connect(self.export_analysis_swatches)

    def _connect_window_menu_actions_to_dock_widget_vis(self) -> None:
        """ Connects the actions in the window menu to the dock widgets, so they can be shown and hidden
        """
        self.action_execution_window.triggered.connect(self.dock_widget_execution.show)
        self.action_swatch_viewer.triggered.connect(self.dock_widget_swatch_analysis.show)
        self.action_image_selection.triggered.connect(self.dock_widget_image_selection.show)
        self.action_color_space_analysis.triggered.connect(self.dock_widget_color_space_analysis.show)
        self.action_white_point_analysis.triggered.connect(self.dock_widget_white_point_analysis.show)
        self.action_max_distance_analysis.triggered.connect(self.dock_widget_max_distance_analysis.show)
        self.action_eotf_analysis.triggered.connect(self.dock_widget_eotf_analysis.show)
        self.action_timeline_window.triggered.connect(self.dock_widget_timeline.show)
        self.action_project_settings_window.triggered.connect(self.dock_widget_project_settings.show)
        self.action_led_settings_window.triggered.connect(self.dock_widget_led_settings.show)
        self.action_calibration_settings_window.triggered.connect(self.dock_widget_calibration_settings.show)
        self.action_plate_settings_window.triggered.connect(self.dock_widget_plate_settings.show)
        self.action_stage_view_window.triggered.connect(self.dock_widget_stage_view.show)
        self.action_calibration_matrix_view_window.triggered.connect(self.dock_widget_calibration_matrix.show)
        self.action_delta_e_analysis_window.triggered.connect(self.dock_widget_delta_e_analysis.show)

    def _add_actions_to_file_menu(self) -> None:
        """ Adds the actions to the file menu
        """
        self.file_menu.addAction(self.action_new_project_settings)
        self.file_menu.addAction(self.action_save_project_settings)
        self.file_menu.addAction(self.action_load_project_settings)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.action_save_project_settings_as)
        self.file_menu.addAction(self.action_export_selection_as)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.action_generate_patterns)
        self.file_menu.addAction(self.action_generate_spg_patterns)
        self.file_menu.addAction(self.action_export_swatches)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.load_sequence_action)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.action_save_layout)
        self.file_menu.addAction(self.action_load_layout)
        self.file_menu.addSeparator()
        self.file_menu.addAction(self.action_load_project_layout)
        self.file_menu.addAction(self.action_load_analysis_layout)

    def _add_actions_to_windows_menu(self) -> None:
        """ Adds the actions to the window menu
        """
        self.windows_menu.addAction(self.action_execution_window)
        self.windows_menu.addAction(self.action_image_selection)
        self.windows_menu.addAction(self.action_color_space_analysis)
        self.windows_menu.addAction(self.action_white_point_analysis)
        self.windows_menu.addAction(self.action_eotf_analysis)
        self.windows_menu.addAction(self.action_max_distance_analysis)
        self.windows_menu.addAction(self.action_timeline_window)
        self.windows_menu.addAction(self.action_project_settings_window)
        self.windows_menu.addAction(self.action_led_settings_window)
        self.windows_menu.addAction(self.action_calibration_settings_window)
        self.windows_menu.addAction(self.action_plate_settings_window)
        self.windows_menu.addAction(self.action_stage_view_window)
        self.windows_menu.addAction(self.action_swatch_viewer)
        self.windows_menu.addAction(self.action_calibration_matrix_view_window)
        self.windows_menu.addAction(self.action_delta_e_analysis_window)

    def _create_actions_for_file_menu(self) -> None:
        """ Creates the actions for the file menu
        """
        self.action_new_project_settings = QAction("New Project", self)
        self.action_save_project_settings = QAction("Save Project", self)
        self.action_save_project_settings_as = QAction("Save Project As...", self)
        self.action_export_selection_as = QAction("Export Selection As...", self)
        self.action_load_project_settings = QAction("Load Project", self)
        self.action_generate_patterns = QAction("Generate OpenVPCal Patterns", self)
        self.action_generate_spg_patterns = QAction("Generate SPG Patterns", self)
        self.action_save_layout = QAction("Save Layout As...", self)
        self.action_load_layout = QAction("Load Layout...", self)
        self.action_load_project_layout = QAction("Load Project Layout", self)
        self.action_load_analysis_layout = QAction("Load Analysis Layout", self)
        self.load_sequence_action = QAction("Load Plate Sequence", self)
        self.action_export_swatches = QAction("Export Debug Swatches", self)

    def _create_actions_for_window_menu(self) -> None:
        """ Creates the actions for the window menu
        """
        self.action_execution_window = QAction("Execution", self)
        self.action_swatch_viewer = QAction("Swatch Viewer", self)
        self.action_image_selection = QAction("Image Selection", self)
        self.action_color_space_analysis = QAction("Colour Space Analysis", self)
        self.action_white_point_analysis = QAction("White Point Analysis", self)
        self.action_max_distance_analysis = QAction("Max Distances Analysis", self)
        self.action_eotf_analysis = QAction("EOTF Analysis", self)
        self.action_timeline_window = QAction("Timeline", self)
        self.action_project_settings_window = QAction("Project Settings", self)
        self.action_led_settings_window = QAction("LED Settings", self)
        self.action_calibration_settings_window = QAction("Calibration Settings", self)
        self.action_plate_settings_window = QAction("Plate Settings", self)
        self.action_stage_view_window = QAction("Stage View", self)
        self.action_calibration_matrix_view_window = QAction("Calibration Matrix View", self)
        self.action_delta_e_analysis_window = QAction("Delta E Analysis", self)

    def _create_menus(self) -> None:
        """ Creates the menus for the main window
        """
        self.menu_bar = self.menuBar()
        self.windows_menu = QMenu('Windows', self.menu_bar)
        self.file_menu = QMenu('File', self.menu_bar)
        self.menu_bar.addMenu(self.file_menu)
        self.menu_bar.addMenu(self.windows_menu)

    def _set_widgets_into_dock_widgets(self) -> None:
        """ Sets the widgets into the dock widgets, so they can be docked and undocked as required
        """
        self.dock_widget_color_space_analysis.setWidget(self.colour_spaces_view)
        self.dock_widget_white_point_analysis.setWidget(self.white_point_view)
        self.dock_widget_max_distance_analysis.setWidget(self.max_distances_view)
        self.dock_widget_eotf_analysis.setWidget(self.eotf_analysis_view)
        self.dock_widget_timeline.setWidget(self.timeline_view)
        self.dock_widget_project_settings.setWidget(self.project_settings_view)
        self.dock_widget_led_settings.setWidget(self.led_settings_view)
        self.dock_widget_calibration_settings.setWidget(self.calibration_settings_view)
        self.dock_widget_plate_settings.setWidget(self.plate_settings_view)
        self.dock_widget_stage_view.setWidget(self.stage_view)
        self.dock_widget_swatch_analysis.setWidget(self.swatch_analysis_view)
        self.dock_widget_execution.setWidget(self.execution_view)
        self.dock_widget_image_selection.setWidget(self.image_selection_widget)
        self.dock_widget_calibration_matrix.setWidget(self.matrix_view)
        self.dock_widget_delta_e_analysis.setWidget(self.delta_e_widget)

    def _add_dock_widgets_to_main_window(self) -> None:
        """ Adds the dock widgets to the main window or sub main window, our main widgets such as
        execution, swatch analysis, and image selection is added to the sub main window, as they take priority of screen
        space over the other widgets which can be moved around the edges.
        """
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget_color_space_analysis)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget_white_point_analysis)
        self.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget_max_distance_analysis)
        self.splitDockWidget(self.dock_widget_color_space_analysis, self.dock_widget_eotf_analysis, Qt.Vertical)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget_stage_view)
        self.splitDockWidget(self.dock_widget_stage_view, self.dock_widget_project_settings, Qt.Vertical)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget_led_settings)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget_calibration_settings)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget_plate_settings)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget_calibration_matrix)
        self.addDockWidget(Qt.RightDockWidgetArea, self.dock_widget_delta_e_analysis)
        self.addDockWidget(Qt.BottomDockWidgetArea, self.dock_widget_timeline)

        self.sub_main_window.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget_image_selection)
        self.sub_main_window.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget_swatch_analysis)
        self.sub_main_window.addDockWidget(Qt.LeftDockWidgetArea, self.dock_widget_execution)

    def _create_dock_widgets(self) -> None:
        """ Creates the dock widgets for the main window
        """
        # Create dock widgets
        self.dock_widget_execution = QDockWidget("Execution", self)
        self.dock_widget_execution.setObjectName('dock_execution')
        self.dock_widget_swatch_analysis = QDockWidget("Swatch Analysis", self)
        self.dock_widget_swatch_analysis.setObjectName('dock_widget_swatch_analysis')
        self.dock_widget_color_space_analysis = QDockWidget("Colour Space Analysis", self)
        self.dock_widget_color_space_analysis.setObjectName('dock_widget_color_space_analysis')
        self.dock_widget_white_point_analysis = QDockWidget("White Point Analysis", self)
        self.dock_widget_white_point_analysis.setObjectName('white_point_analysis')
        self.dock_widget_max_distance_analysis = QDockWidget("Max Distance Analysis", self)
        self.dock_widget_max_distance_analysis.setObjectName('max_distance_analysis')
        self.dock_widget_delta_e_analysis = QDockWidget("IPT-DeltaE Analysis", self)
        self.dock_widget_delta_e_analysis.setObjectName('dock_widget_delta_e_analysis')
        self.dock_widget_eotf_analysis = QDockWidget("EOTF Analysis", self)
        self.dock_widget_eotf_analysis.setObjectName('dock_widget_eotf_analysis')
        self.dock_widget_timeline = QDockWidget("Timeline", self)
        self.dock_widget_timeline.setObjectName('timeline_dock_widget')
        self.dock_widget_project_settings = QDockWidget("Project Settings", self)
        self.dock_widget_project_settings.setObjectName('dock_widget_project_settings')
        self.dock_widget_led_settings = QDockWidget("LED Settings", self)
        self.dock_widget_led_settings.setObjectName('dock_widget_led_settings')
        self.dock_widget_calibration_settings = QDockWidget("Calibration Settings", self)
        self.dock_widget_calibration_settings.setObjectName('dock_widget_led_analysis_settings')
        self.dock_widget_plate_settings = QDockWidget("Plate Settings", self)
        self.dock_widget_plate_settings.setObjectName('dock_widget_plate_settings')
        self.dock_widget_calibration_matrix = QDockWidget("Calibration Matrix", self)
        self.dock_widget_calibration_matrix.setObjectName('dock_widget_calibration_matrix')
        self.dock_widget_stage_view = QDockWidget("Stage View", self)
        self.dock_widget_stage_view.setObjectName('dock_widget_stage_view')
        self.dock_widget_image_selection = QDockWidget("Image Selection", self)
        self.dock_widget_image_selection.setObjectName('dock_widget_image_selection')

    def new_project(self) -> None:
        """
        Create a new project, allows the user to select a folder, clears the current project, sets the new output_folder
            and loads the default layout of the UI.
        """
        folder = select_folder()
        if folder:
            self.clear_project_settings()
            self.project_settings_model.output_folder = folder
            self.project_settings_model.set_data(constants.ProjectSettingsKeys.OUTPUT_FOLDER, folder)
            self.save_project_settings(inform_completion=False)
        self.load_project_layout()

    def clear_project_settings(self) -> None:
        """ Clears the current project settings from all the widgets, models and controllers
        """
        self.stage_controller.remove_all_walls()
        self.project_settings_model.clear_project_settings()
        self.eotf_analysis_controller.clear_project_settings()
        self.colour_space_controller.clear_project_settings()
        self.white_point_controller.clear_project_settings()
        self.image_selection_widget.clear()
        self.max_distances_controller.clear()
        self.delta_e_controller.clear()

    def export_analysis_swatches(self) -> None:
        """ Export the Analysis Swatches in their raw format that was sampled from the camera
        """
        swatches_folder = os.path.join(
            self.project_settings_model.export_folder, constants.ProjectFolders.SWATCHES)
        if not os.path.exists(swatches_folder):
            os.mkdir(swatches_folder)

        for led_wall in self.project_settings_model.led_walls:
            if led_wall.processing_results.sample_buffers:
                led_swatches_output_folder = os.path.join(swatches_folder, led_wall.name)
                if not os.path.exists(led_swatches_output_folder):
                    os.mkdir(led_swatches_output_folder)
                file_name = f"{led_wall.name}_swatches_ACES2065-1.exr"
                output_file_name = os.path.join(led_swatches_output_folder, file_name)
                sample_buffers_stitched, _ = imaging_utils.create_and_stitch_analysis_strips(
                    [], led_wall.processing_results.sample_buffers)
                result = imaging_utils.stitch_images_vertically([sample_buffers_stitched])
                imaging_utils.write_image(result, output_file_name, "float")

    def generate_patterns(self) -> None:
        """ Generates the patterns for the selected led walls, if no led walls are selected, it asks the user
            if they would like to generate them for all the walls in the project.

            We also save the project settings after the patterns have been generated.
        """
        selected_led_walls = self.stage_controller.selected_led_walls()
        if self.warning_message("Would you like to generate patterns for all walls?"):
            led_walls = self.project_settings_model.led_walls
        else:
            led_walls = []
            for selected_led_wall in selected_led_walls:
                for wall in self.project_settings_model.led_walls:
                    if wall.name == selected_led_wall:
                        led_walls.append(wall)
                        break

        self.generate_patterns_for_led_walls(self.project_settings_model, led_walls)

        self.save_project_settings(inform_completion=False)
        self.task_completed()

    def generate_spg_patterns(self):
        selected_led_walls = self.stage_controller.selected_led_walls()
        if self.warning_message("Would you like to generate patterns for all walls?"):
            led_walls = self.project_settings_model.led_walls
        else:
            led_walls = []
            for selected_led_wall in selected_led_walls:
                for wall in self.project_settings_model.led_walls:
                    if wall.name == selected_led_wall:
                        led_walls.append(wall)
                        break

        self.generate_spg_patterns_for_led_walls(self.project_settings_model, led_walls)

        self.save_project_settings(inform_completion=False)
        self.task_completed()

    @staticmethod
    def generate_spg_patterns_for_led_walls(project_settings: ProjectSettingsModel, led_walls: List) -> str:

        spg_project_settings = SPGProjectSettings()
        spg_project_settings.frame_rate = 24.0
        spg_project_settings.image_file_format = project_settings.file_format
        spg_project_settings.image_file_bit_depth = 10
        spg_project_settings.output_folder = os.path.join(
            project_settings.output_folder,
            constants.ProjectFolders.SPG
        )
        spg_project_settings.channel_mapping = "RGB"
        spg_project_settings.ocio_config_path = ResourceLoader.ocio_config_path()
        spg_project_settings.output_transform = constants.CameraColourSpace.CS_ACES_CG
        if spg_project_settings.image_file_format == constants.FileFormats.FF_DPX:
            spg_project_settings.output_transform = constants.CameraColourSpace.CS_ACES_CCT

        spg_led_walls = []
        spg_led_panels = []
        spg_raster_maps = []

        for count, led_wall in enumerate(led_walls):
            idx = count + 1
            spg_panel = SPGLedPanel()
            spg_panel.name = f"Panel_{idx}_{led_wall.name}"
            spg_panel.manufacturer = "Unknown"
            spg_panel.panel_width = 500
            spg_panel.panel_height = 500
            spg_panel.panel_depth = 80
            spg_panel.pixel_pitch = 2.85
            spg_panel.brightness = led_wall.target_max_lum_nits
            spg_panel.refresh_rate = "3840"
            spg_panel.scan_rate = "1/8"
            spg_led_panels.append(spg_panel)

            spg_led_wall = SPGLedWall()
            spg_led_wall.id = idx
            spg_led_wall.name = led_wall.name
            spg_led_wall.panel_name = spg_panel.name
            spg_led_wall.panel = spg_panel
            spg_led_wall.panel_count_width = int(project_settings.resolution_width / spg_panel.panel_resolution_width)
            spg_led_wall.panel_count_height = int(
                project_settings.resolution_height / spg_panel.panel_resolution_height
            )
            spg_led_wall.wall_default_color = utils.generate_color(led_wall.name)

            spg_led_walls.append(spg_led_wall)

            spg_mapping = SPGMapping()
            spg_mapping.wall_name = spg_led_wall.name
            spg_mapping.raster_u = 0
            spg_mapping.raster_v = 0
            spg_mapping.wall_segment_u_start = 0
            spg_mapping.wall_segment_u_end = spg_led_wall.resolution_width
            spg_mapping.wall_segment_v_start = 0
            spg_mapping.wall_segment_v_end = spg_led_wall.resolution_height
            spg_mapping.wall_segment_orientation = 0

            spg_raster_map = SPGRasterMap()
            spg_raster_map.name = f"Raster_{led_wall.name}"
            spg_raster_map.resolution_width = project_settings.resolution_width
            spg_raster_map.resolution_height = project_settings.resolution_height
            spg_raster_map.mappings = [spg_mapping]

            spg_raster_maps.append(spg_raster_map)

        spg_led_panel_json = [json.loads(spg_led_panel.to_json()) for spg_led_panel in spg_led_panels]
        spg_led_wall_json = [json.loads(spg_led_wall.to_json()) for spg_led_wall in spg_led_walls]
        spg_raster_map_json = [json.loads(spg_raster_map.to_json()) for spg_raster_map in spg_raster_maps]

        spg_led_panel_json_file = tempfile.NamedTemporaryFile(suffix=".json", mode='w', delete=False).name
        spg_led_wall_json_file = tempfile.NamedTemporaryFile(suffix=".json", mode='w', delete=False).name
        spg_raster_map_json_file = tempfile.NamedTemporaryFile(suffix=".json", mode='w', delete=False).name
        spg_project_settings_json_file = tempfile.NamedTemporaryFile(suffix=".json", mode='w', delete=False).name

        with open(spg_led_panel_json_file, 'w') as f:
            json.dump(spg_led_panel_json, f, indent=4)
        with open(spg_led_wall_json_file, 'w') as f:
            json.dump(spg_led_wall_json, f, indent=4)
        with open(spg_raster_map_json_file, 'w') as f:
            json.dump(spg_raster_map_json, f, indent=4)
        with open(spg_project_settings_json_file, 'w') as f:
            json.dump(json.loads(spg_project_settings.to_json()), f, indent=4)

        run_spg_pattern_generator(
            spg_led_panel_json_file,
            spg_led_wall_json_file,
            spg_raster_map_json_file,
            spg_project_settings_json_file,
            ResourceLoader.spg_pattern_basic_config())


    @staticmethod
    def generate_patterns_for_led_walls(project_settings: ProjectSettingsModel, led_walls: List) -> str:
        """ For the given list of led walls filter out any walls which are verification walls, then generate the
            calibration patterns for the remaining walls.

        Args:
            project_settings: The project settings with the settings for the pattern generation
            led_walls: A list of led walls we want to generate patters for

        Returns: The ocio config file path which was generated

        """
        led_walls = [led_wall for led_wall in led_walls if not led_wall.is_verification_wall]
        if not led_walls:
            return ""

        for led_wall in led_walls:
            patch_generator = PatchGeneration(led_wall)
            patch_generator.generate_patches(constants.PATCHES.PATCH_ORDER)

        config_writer = ocio_config.OcioConfigWriter(project_settings.export_folder)
        return config_writer.generate_pre_calibration_ocio_config(led_walls)

    def load_sequence(self) -> None:
        """ Loads the sequence from the selected folder, if no LED wall is selected, it asks the user to select one.
        """
        if not self.project_settings_model.current_wall:
            self.error_message("No Led Wall Selected To Associate Sequence With")
            return

        self.timeline_view.load_sequence()

    def sequence_loaded(self, led_wall):
        """ Called when a sequence has been loaded, we force the timeline widget to the start frame, we then run the
        auto roi detection

        Args:
            led_wall: the LED wall which we just loaded the sequence for
        """
        self.timeline_view.set_to_start()

        sep_results, auto_roi_results = self.run_auto_detect(
            led_wall
        )
        if not sep_results or not sep_results.is_valid:
            self.error_message("Unable To Identify Separation")

        if not auto_roi_results or not auto_roi_results.is_valid:
            self.error_message("Unable To Auto Identify ROI")

        self.timeline_view.set_to_end()
        self.timeline_view.set_to_start()

    def project_settings_changed(self):
        """ Called when the project settings have changed, we get the current LED wall, and update the colour spaces
        view
        """
        selected_wall_names = self.stage_controller.selected_led_walls()
        if not selected_wall_names:
            return

        selected_walls = [self.project_settings_model.get_led_wall(name) for name in selected_wall_names]
        self.colour_space_controller.update_model_with_led_targets(selected_walls)

    @staticmethod
    def task_completed() -> None:
        """ Opens a QDialog box which informs the user a task has completed successfully
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)

        msg.setText("Completed Successfully")
        msg.setWindowTitle("Task Status")
        msg.setStandardButtons(QMessageBox.Ok)

        msg.exec_()

    @staticmethod
    def info_message(message) -> None:
        """ Opens a QDialog box which informs the user of useful info

        Args:
            message: The message we want to provide to the user regarding the error
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Information)

        msg.setText(message)
        msg.setWindowTitle("Info")
        msg.setStandardButtons(QMessageBox.Ok)

        msg.exec_()
    @staticmethod
    def error_message(message) -> None:
        """ Opens a QDialog box which informs the user an error has occurred

        Args:
            message: The message we want to provide to the user regarding the error
        """
        msg = QMessageBox()
        msg.setIcon(QMessageBox.Critical)

        msg.setText(message)
        msg.setWindowTitle("Error")
        msg.setStandardButtons(QMessageBox.Ok)

        msg.exec_()

    @staticmethod
    def warning_message(message: str, yes_text: str = "Yes", no_text: str = "No") -> bool:
        """ Displays a QMessageBox which displays a warning message to the user and asks them to make a yes or no choice

        Args:
            message: The message we want to display to the user
            yes_text: The text we want to display on the yes button
            no_text: The text we want to display on the no button

        Returns: True if the user selects yes, False if the user selects no

        """
        msg_box = QMessageBox()
        msg_box.setIcon(QMessageBox.Warning)
        msg_box.setText(message)
        msg_box.setWindowTitle("Warning")

        yes_button = QPushButton(yes_text)
        no_button = QPushButton(no_text)

        msg_box.addButton(yes_button, QMessageBox.YesRole)
        msg_box.addButton(no_button, QMessageBox.NoRole)

        # Setting default focus on No button
        msg_box.setDefaultButton(QMessageBox.No)

        msg_box.exec_()
        if msg_box.clickedButton() == yes_button:
            return True
        return False

    def display_welcome_wizard(self) -> None:
        """ Displays a welcome wizard to the user, asking them if they want to create a new project or load an existing
            one.
        """
        # Create a QMessageBox
        msg_box = QMessageBox()
        msg_box.setText("Welcome to OpenVPCal!\nWhat would you like to do?")
        msg_box.setIconPixmap(self.logo.scaled(100, 100, Qt.KeepAspectRatio, Qt.SmoothTransformation))

        # Create the custom buttons
        new_project_button = msg_box.addButton("New Project", QMessageBox.ActionRole)
        load_existing_project_button = msg_box.addButton("Load Existing Project", QMessageBox.ActionRole)
        msg_box.addButton("Exit", QMessageBox.RejectRole)

        # Show the message box
        msg_box.exec_()

        # Check which button was clicked and return result
        if msg_box.clickedButton() == new_project_button:
            self.new_project()
        elif msg_box.clickedButton() == load_existing_project_button:
            self.load_project_settings()
        else:
            self.exit()

    @staticmethod
    def exit() -> None:
        """ Causes the application to exit
        """
        sys.exit(0)

    def _get_led_walls_for_processing(self, mode):
        if not self.project_settings_model.led_walls:
            self.error_message("No Led Walls In Project")
            return []

        led_walls = [
            self.project_settings_model.get_led_wall(led_wall)
            for led_wall in self.stage_controller.selected_led_walls()
        ]

        if not led_walls:
            message = f"No Led Walls Selected, Would you like to {mode} all of them?"
            if not self.warning_message(message):
                return []
            led_walls = self.project_settings_model.led_walls
        else:
            led_wall_names = [led_wall.name for led_wall in led_walls]
            message = f"{mode.title()} The Following Walls\n" + "\n".join(led_wall_names) + "\nContinue?"
            if not self.warning_message(message):
                return []
        return led_walls

    def export(self):
        """ Runs the export of the LED walls that we have in our selection, providing validation to ensure all the walls
        have been sampled, and analysed

        Returns:

        """
        mode = "export"
        led_walls = self._get_led_walls_for_processing(mode)
        if not led_walls:
            return

        for led_wall in led_walls:
            if not led_wall.processing_results:
                self.error_message(f"No Sampling Results For {led_wall.name}")
                return

            if not led_wall.processing_results.calibration_results:
                self.error_message(f"No Analysis Results For {led_wall.name}")
                return

        new_config = self.warning_message(
            f"Would you like to export a new config based on \n{os.path.basename(ResourceLoader.ocio_config_path())}\n"
            f", or provide your own config to update?",
            yes_text="New Config",
            no_text="Update Existing Config"
        )

        # If the user wants to update their existing config then we need to get the path to the config file
        if not new_config:
            dialog = QFileDialog()
            dialog.setDefaultSuffix('.ocio')
            dialog.setAcceptMode(QFileDialog.AcceptOpen)
            dialog.setNameFilter('OCIO files (*.ocio)')

            # We store the filepath in the project_settings
            if dialog.exec_() == QFileDialog.Accepted:
                file_name = dialog.selectedFiles()[0]
                self.project_settings_model.ocio_config_path = file_name
            else:
                self.error_message("No Config Selected")
                return

        Processing.run_export(self.project_settings_model, led_walls)
        # Reset the ocio config path to None so we don't use it next time
        self.project_settings_model.ocio_config_path = None
        self.export_plots()
        self.export_analysis_swatches()
        self.task_completed()

    def export_plots(self) -> None:
        """ Exports the images of the plotted graphs
        """
        plots_folder = os.path.join(self.project_settings_model.export_folder, constants.ProjectFolders.PLOTS)
        if not os.path.exists(plots_folder):
            os.mkdir(plots_folder)

        self.eotf_analysis_view.export_plot(
            os.path.join(plots_folder, "eotf_analysis.png")
        )
        self.colour_spaces_view.export_plot(
            os.path.join(plots_folder, "colour_space_analysis.png")
        )
        self.white_point_view.export_plot(
            os.path.join(plots_folder, "white_point_analysis.png")
        )
        self.max_distances_view.export_plot(
            os.path.join(plots_folder, "max_distances_view.png")
        )

    def single_camera_across_all_wall(self, led_walls: List[LedWallSettings]) -> bool:
        """ Checks to see if all the LED walls have the same camera gamut, if they do, we return True, otherwise we
            return False

        Args:
            led_walls: The LED walls we want to check

        Returns:

        """
        camera_gamuts = {led_wall.native_camera_gamut for led_wall in led_walls}
        if len(camera_gamuts) > 1:
            message = "Multiple Camera Gamuts Detected, Would You Like To Continue?"
            if not self.warning_message(message):
                return False
        return True

    def post_analysis_validations(self, led_walls: List[LedWallSettings]) -> bool:
        """ Run the validation checks on the results of the analysis, we report any warnings or failures to the user.

        Args:
            led_walls: A list of led walls we want to validate the calibration results for

        Returns:
            Whether we should continue with the analysis or not

        """
        validation = Validation()
        validation_results = []
        validation_status = constants.ValidationStatus.PASS
        for led_wall in led_walls:
            results = validation.run_validations(led_wall.processing_results.pre_calibration_results)
            for result in results:
                if result.status != constants.ValidationStatus.PASS:
                    validation_status = utils.calculate_validation_status(validation_status, result.status)
                    validation_results.append(f"{led_wall.name} - {result.name}\n{result.message}\n")

        if validation_status == constants.ValidationStatus.FAIL:
            validation_results_message = "\n".join(validation_results)
            self.error_message(f"Validation Failed:\n{validation_results_message}\n"
                                 f"We Strongly Suggest To Address These Issues Before Continuing")
            return False

        if validation_status == constants.ValidationStatus.WARNING:
            validation_results_message = "\n".join(validation_results)
            if not self.warning_message(f"Validation Warning:\n{validation_results_message}",
                                        yes_text="Continue", no_text="Abort"):
                return False
        return True

    def analyse(self) -> None:
        """ Runs the sampling of the LED walls that we have in our selection, providing validation to ensure all that
        we do not override existing sampling unless the user desires.

        We also analyse the sampled data showing the current state of the LED wall
        """
        mode = "analyse"
        led_walls = self._get_led_walls_for_processing(mode)
        if not led_walls:
            return

        for led_wall in led_walls:
            if led_wall.native_camera_gamut == constants.CameraColourSpace.CS_ACES:
                message = f"Native Camera Gamut Should Not Be {constants.CameraColourSpace.CS_ACES} For {led_wall.name}"
                self.error_message(message)
                return

            if led_wall.processing_results:
                if led_wall.processing_results.samples:
                    message = f"Sampling Results Already Exist For {led_wall.name}, Would You Like To Overwrite?"
                    if not self.warning_message(message):
                        return
                    break

            if not led_wall.has_valid_white_balance_options():
                message = f"Only Select 1 option from AutoWB, or Reference Wall or External White {led_wall.name}"
                self.error_message(message)
                return

        led_wall_names = [led_wall.name for led_wall in led_walls]
        for led_wall in led_walls:
            if led_wall.use_external_white_point:
                if not led_wall.external_white_point_file:
                    self.error_message(f"External White Point Enabled But File Not Set {led_wall.name}")
                    return

                if not os.path.exists(led_wall.external_white_point_file):
                    self.error_message(f"External White Point File Set Does Not Exist {led_wall.name}")
                    return

            if led_wall.match_reference_wall:
                if not led_wall.reference_wall:
                    self.error_message(f"Match Reference Wall Enabled But Not Set {led_wall.name} Not In Selection")
                    return

                if led_wall.reference_wall not in led_wall_names:
                    self.error_message(f"Reference Wall {led_wall.reference_wall} Not In Selection")
                    return

        if not self.single_camera_across_all_wall(led_walls):
            return

        led_walls = utils.led_wall_reference_wall_sort(led_walls)

        self.timeline_view.set_to_start()

        # We have to do these sequentially encase we are using a reference wall
        for led_wall in led_walls:
            processing = Processing(led_wall)
            processing.run_sampling()
            processing.analyse()

        self.timeline_view.set_to_end()
        self.timeline_view.set_to_start()

        self.load_analysis_layout()
        for led_wall in led_walls:
            self.colour_space_controller.update_model_with_results(led_wall, pre_calibration=True)
            self.eotf_analysis_controller.update_model_with_results(led_wall, pre_calibration=True)
            self.white_point_controller.update_model_with_results(led_wall, pre_calibration=True)
            self.max_distances_controller.update_model_with_results(led_wall, pre_calibration=True)
            self.delta_e_controller.update_model_with_results(led_wall, pre_calibration=True)

        self.stage_controller.select_led_walls(
            [led_wall.name for led_wall in led_walls]
        )

        if not self.post_analysis_validations(led_walls):
            return

        self.apply_post_analysis_configuration(led_walls)

        # Select All LED Walls
        self.stage_controller.select_led_walls(
            [led_wall.name for led_wall in led_walls]
        )

        self.task_completed()

    def apply_post_analysis_configuration(self, led_walls: List[LedWallSettings]) -> None:
        """ Runs the configuration checks on the results of the analysis, we apply any recommended settings and inform
            the user

        Args:
            led_walls: A list of led walls we want to run the configuration checks on
        """
        configuration = Configuration()
        configuration_messages = ["Based On The Analysis We Have Recommended The Following Settings:"]
        for led_wall in led_walls:
            self.stage_controller.select_led_walls(
                [led_wall.name]
            )
            results = configuration.run_configuration_checks(led_wall.processing_results.pre_calibration_results)
            configuration_messages.append(f"\n{led_wall.name}")
            for result in results:
                configuration_messages.append(f"{result.param}: {result.value}")
                self.project_settings_model.set_data(result.param, result.value)
        self.info_message("\n".join(configuration_messages))

    def calibrate(self):
        """ Runs the analysis for each of the LED walls in the selection, adding validation to ensure that the LED walls
        have previously been sampled
        """
        mode = "calibrate"
        led_walls = self._get_led_walls_for_processing(mode)
        if not led_walls:
            return

        for led_wall in led_walls:
            if not led_wall.processing_results:
                self.error_message(f"No Sampling Results For {led_wall.name}")
                return

            if not led_wall.has_valid_white_balance_options():
                message = f"Only Select 1 option from AutoWB, or Reference Wall or External White {led_wall.name}"
                self.error_message(message)
                return

        led_wall_names = [led_wall.name for led_wall in led_walls]
        for led_wall in led_walls:
            if led_wall.use_external_white_point:
                if not led_wall.external_white_point_file:
                    self.error_message(f"External White Point Enabled But File Not Set {led_wall.name}")
                    return
                if not os.path.exists(led_wall.external_white_point_file):
                    self.error_message(f"External White Point File Set Does Not Exist {led_wall.name}")
                    return
            if led_wall.match_reference_wall:
                if not led_wall.reference_wall:
                    self.error_message(f"Match Reference Wall Enabled But Not Set {led_wall.name} Not In Selection")
                    return

                if led_wall.reference_wall not in led_wall_names:
                    self.error_message(f"Reference Wall {led_wall.reference_wall} Not In Selection")
                    return

        if not self.single_camera_across_all_wall(led_walls):
            return

        led_walls = utils.led_wall_reference_wall_sort(led_walls)

        # We have to do these sequentially encase we are using a reference wall
        self.timeline_view.set_to_start()
        for led_wall in led_walls:
            processing = Processing(led_wall)
            processing.calibrate()

            self.colour_space_controller.update_model_with_results(led_wall)
            self.eotf_analysis_controller.update_model_with_results(led_wall)
            self.white_point_controller.update_model_with_results(led_wall)
            self.max_distances_controller.update_model_with_results(led_wall)

        # We force a refresh and reload of all the data
        self.timeline_view.set_to_end()
        self.timeline_view.set_to_start()
        self.stage_controller.select_led_walls(
            [led_wall.name for led_wall in led_walls]
        )
        self.task_completed()

    def save_project_settings_as(self):
        """ Saves the current project settings to disk
        """
        folder = select_folder()
        if folder:
            self.project_settings_model.output_folder = folder
            self.project_settings_model.set_data(constants.ProjectSettingsKeys.OUTPUT_FOLDER, folder)
            self.save_project_settings(inform_completion=False)
            self.task_completed()

    def export_selection_as(self) -> None:
        """ Exports the selected led walls, and any of their references

        Returns:

        """
        folder = select_folder()
        if folder:
            # Get All The Walls Selected And Any They Reference
            all_walls_to_export = []
            selected_led_walls = self.stage_controller.selected_led_walls()
            for led_wall_name in selected_led_walls:
                led_wall = self.project_settings_model.get_led_wall(led_wall_name)
                all_walls_to_export.append(led_wall_name)

                reference_wall = led_wall.reference_wall
                if reference_wall:
                    all_walls_to_export.append(led_wall_name)

                verification_wall = led_wall.verification_wall
                if verification_wall:
                    all_walls_to_export.append(verification_wall)

            # Make Sure We Have A Unique List Of Walls To Export
            all_walls_to_export = list(set(all_walls_to_export))

            # Make A New Project Settings Model With Only The Walls We Want To Export
            current_folder = self.project_settings_model.output_folder
            self.project_settings_model.output_folder = folder
            new_project_settings = self.save_project_settings(inform_completion=False)
            self.project_settings_model.output_folder = current_folder

            export_project = ProjectSettings.from_json(new_project_settings)
            for led_wall in export_project.led_walls:
                if led_wall.name not in all_walls_to_export:
                    export_project.remove_led_wall(led_wall.name)

            filename = os.path.join(
                export_project.output_folder,
                DEFAULT_PROJECT_SETTINGS_NAME
            )
            export_project.to_json(filename)
            self.task_completed()

    def on_save_project(self) -> None:
        """ Callback for when the save action is called
        """
        self.save_project_settings(inform_completion=True)

    def save_project_settings(self, inform_completion: bool = True) -> str:
        """ Saves the current project settings to disk using the output_folder as the project name

        Args:
            inform_completion: Whether we want to inform the user of completion or not

        Returns The file path of the saved project settings
        """
        filename = os.path.join(
            self.project_settings_model.output_folder,
            DEFAULT_PROJECT_SETTINGS_NAME
        )
        # TODO inform_completion is always True
        self.project_settings_model.to_json(filename)
        if inform_completion:
            self.task_completed()
        return filename

    def load_project_settings(self):
        """ Loads project settings from disk
        """
        dialog = QFileDialog()
        dialog.setDefaultSuffix('.json')
        dialog.setAcceptMode(QFileDialog.AcceptOpen)
        dialog.setNameFilter('JSON files (*.json)')

        if dialog.exec_() == QFileDialog.Accepted:
            file_name = dialog.selectedFiles()[0]
            self.clear_project_settings()
            self.project_settings_model.load_from_json(file_name)
            self.timeline_model.load_all_sequences_for_led_walls()
            if self.project_settings_model.current_wall:
                self.stage_controller.select_led_walls([self.project_settings_model.current_wall.name])

            self.stage_controller.select_led_walls([])
            for led_wall in self.project_settings_model.led_walls:
                if led_wall.input_sequence_folder:
                    if not led_wall.roi:
                        self.run_auto_detect(led_wall)
                    else:
                        self.get_separation_results(led_wall)
        self.load_project_layout()

    def on_save_layout(self):
        """Save the current layout to a file based on a File Dialog selected file name"""
        filename, _ = QFileDialog.getSaveFileName(
            self, "Save Layout", str(ResourceLoader.prefs_dir()), "Layout Files (*.layout)")
        if not filename:
            return
        self._save_layout(filename)

    def _save_layout(self, filename: str):
        """Save the current layout to a file"""
        file = QFile(filename)
        if not file.open(QIODevice.WriteOnly):
            return
        stream = QDataStream(file)
        # pylint: disable=W0106
        stream << self.saveGeometry() << self.saveState() \
        << self.sub_main_window.saveGeometry() << self.sub_main_window.saveState()
        # pylint: enable=W0106

    def on_load_layout(self):
        """Load the layout from a file selected from a File Dialog"""
        filename, _ = QFileDialog.getOpenFileName(
            self, "Load Layout", str(ResourceLoader.prefs_dir()), "Layout Files (*.layout)")
        if not filename:
            return

        self.load_layout(filename)

    def load_project_layout(self) -> None:
        """ Loads the project layout from the resources folder
        """
        project_layout = ResourceLoader.project_layout()
        user_project_layout = str(ResourceLoader.prefs_dir() / constants.UILayouts.PROJECT_LAYOUT)
        if os.path.exists(user_project_layout):
            project_layout = user_project_layout
        self.load_layout(project_layout)

    def load_analysis_layout(self) -> None:
        """ Loads the analysis layout from the resources folder
        """
        analysis_layout = ResourceLoader.analysis_layout()
        user_analysis_layout = str(ResourceLoader.prefs_dir() / constants.UILayouts.ANALYSIS_LAYOUT)
        if os.path.exists(user_analysis_layout):
            analysis_layout = user_analysis_layout
        self.load_layout(analysis_layout)

    def load_layout(self, filename: str) -> None:
        """ Loads a layout the given file path using a QTimer to ensure the UI is in a loadable state

        Args:
            filename: the file we want to load the layout from
        """
        QTimer.singleShot(100, lambda: self._load_layout(filename))

    def _load_layout(self, filename):
        """ Loads a layout the given file path

        Args:
            filename: the file we want to load the layout from
        """
        file = QFile(filename)
        if not file.open(QIODevice.ReadOnly):
            return

        geometry = QByteArray()
        state = QByteArray()
        sub_geometry = QByteArray()
        sub_state = QByteArray()
        stream = QDataStream(file)
        # pylint: disable=pointless-statement
        stream >> geometry >> state >> sub_geometry >> sub_state
        # pylint: enable=pointless-statement
        self.restoreGeometry(geometry)
        self.restoreState(state)
        self.sub_main_window.restoreGeometry(sub_geometry)
        self.sub_main_window.restoreState(sub_state)

    @staticmethod
    def run_auto_detect(
            led_wall_settings: LedWallSettings) -> Tuple[Optional[SeparationResults], Optional[AutoROIResults]]:
        """ For the given led wall, we run the auto-detection algorithm which aims to detect and store the roi from
            within the image sequence which is loaded

        Args:
            led_wall_settings: the LED wall, which contains the sequence we want to detect the roi for

        Returns:

        """
        # We get the current frame and calculate an ROI which would select the whole image
        current_frame = led_wall_settings.sequence_loader.current_frame
        frame = led_wall_settings.sequence_loader.get_frame(current_frame)
        roi = [0, frame.image_buf.spec().width, 0, frame.image_buf.spec().height]

        # We store the ROI into the project settings
        led_wall_settings.roi = roi

        # Now we have the whole image selected we run the image separation algorithm
        processing, sep_results = MainWindow.get_separation_results(led_wall_settings)
        if not sep_results or not sep_results.is_valid:
            led_wall_settings.roi = roi
            return sep_results, None

        # We now remove the ROI so that we can run the autodetect ROI algorithm
        led_wall_settings.roi = None
        try:
            auto_roi_results = processing.auto_detect_roi(sep_results)
            # If we can not detect the roi automatically, we resort back to the whole image ROI
            if not auto_roi_results or not auto_roi_results.is_valid:
                led_wall_settings.roi = roi
        except ValueError:
            led_wall_settings.roi = roi
            auto_roi_results = None
        return sep_results, auto_roi_results

    @staticmethod
    def get_separation_results(led_wall_settings: LedWallSettings) -> Tuple[Processing, SeparationResults]:
        """ Gets the processing object and the separation results for the given LED wall

        Args:
            led_wall_settings: The LED wall we want to get the separation results for

        Returns: The processing object and the separation results

        """
        processing = Processing(led_wall_settings)
        sep_results = processing.identify_separation()
        return processing, sep_results
