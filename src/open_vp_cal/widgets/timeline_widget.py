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

Module describes the class which is responsible for the timeline widget.
"""
import os

from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QVBoxLayout, QHBoxLayout, QSlider, QLabel, QPushButton, QSpinBox
from PySide6.QtCore import QObject, Signal, Slot, Qt, QEvent

from open_vp_cal.framework.sequence_loader import SequenceLoader, FrameRangeException
from open_vp_cal.framework.frame import Frame
from open_vp_cal.imaging.imaging_utils import load_image_buffer_to_qpixmap
from open_vp_cal.widgets import utils
from open_vp_cal.core import constants
from open_vp_cal.led_wall_settings import LedWallSettings
from open_vp_cal.widgets.project_settings_widget import ProjectSettingsModel
from open_vp_cal.widgets.utils import LockableWidget


class PixMapFrame(Frame):
    """
    A Frame which holds a QPixmap instead of an ImageBuf
    """
    def __init__(self, project_settings: ProjectSettingsModel):
        super().__init__(project_settings)
        self._pixmap = None

    @property
    def pixmap(self) -> QPixmap:
        """
        Property for _frame_num.

        Returns:
        int: The frame number of this frame.
        """
        if not self._pixmap:
            self.load_pixmap()
        return self._pixmap

    def load_pixmap(self) -> None:
        """ Load the pixmap from the image buffer if it does not exist
        """
        if not self._pixmap:
            self._pixmap = load_image_buffer_to_qpixmap(self._image_buf, self._project_settings)


class TimelineModel(QObject):
    """
        Timeline model, which holds data for start, end, and current frames.
    """
    start_frame_changed = Signal(int)
    end_frame_changed = Signal(int)
    current_frame_changed = Signal(int)
    current_frame_changed_frame = Signal(Frame)
    sequence_loaded = Signal(object)
    no_sequence_loaded = Signal()
    has_sequence_loaded = Signal()

    def __init__(self, project_settings: ProjectSettingsModel):
        super().__init__()
        self.project_settings = project_settings
        self.sequence_changed = False

    def set_start_frame(self, frame: int) -> None:
        """ Set start frame value and emit a signal

        Args:
            frame: The frame to set
        """
        if self.project_settings.current_wall.sequence_loader.set_start_frame(frame) or self.sequence_changed:
            self.start_frame_changed.emit(frame)

    def set_end_frame(self, frame: int) -> None:
        """ Set end frame value and emit a signal.

        Args:
            frame: The frame to set
        """
        if self.project_settings.current_wall.sequence_loader.set_end_frame(frame) or self.sequence_changed:
            self.end_frame_changed.emit(frame)

    def set_current_frame(self, frame: int) -> tuple[bool, Frame]:
        """ Sets the current frame and emits a signal if the frame or sequence has changed

        Args:
            frame: The frame to set

        Returns: A tuple of if the frame has changed and the frame object

        """
        frame_changed, result = self.project_settings.current_wall.sequence_loader.set_current_frame(frame)
        if frame_changed or self.sequence_changed:
            self.current_frame_changed.emit(frame)
            self.current_frame_changed_frame.emit(result)
        return frame_changed, result

    def led_wall_selection_changed(self) -> None:
        """ Called when the LED wall selection has changed. We need to update the model to reflect the new wall
        """
        if self.current_frame == -1:
            self.no_sequence_loaded.emit()
            return

        if not self.project_settings.current_wall:
            self.no_sequence_loaded.emit()
            return

        self.sequence_changed = True
        self.has_sequence_loaded.emit()
        self.set_start_frame(self.project_settings.current_wall.sequence_loader.start_frame)
        self.set_end_frame(self.project_settings.current_wall.sequence_loader.end_frame)

        # We cant keep the current frame as sequences could be different frame numbers
        self.set_current_frame(self.project_settings.current_wall.sequence_loader.start_frame)
        self.sequence_changed = False

    def load_sequence(self, folder_path: str, file_type: str = constants.FileFormats.FF_EXR) -> None:
        """ Loads a sequence into the sequence loader and stores the folder path in the LED wall we have set as the
        current wall

        Args:
            folder_path: The folder path to load
            file_type: The file type to load
        """
        # Load the sequence into the sequence loader and store the folder path
        self.project_settings.current_wall.sequence_loader.load_sequence(folder_path, file_type)
        self.project_settings.current_wall.input_sequence_folder = folder_path

        # We now force the system to note that the LED wall selection has changed because the sequence has changed
        # which causes the signals to fire ensuring the model and ui are now in sync
        self.led_wall_selection_changed()
        self.sequence_loaded.emit(self.project_settings.current_wall)

    def load_all_sequences_for_led_walls(self, file_type: str = constants.FileFormats.FF_EXR) -> None:
        """ Loads all sequences for all led walls

        Args:
            file_type: The file type to load
        """
        for wall in self.project_settings.led_walls:
            if wall.input_sequence_folder:
                wall.sequence_loader.load_sequence(wall.input_sequence_folder, file_type)

    @property
    def start_frame(self) -> int:
        """ Returns the start frame of the current sequence if one is loaded, otherwise -1

        Returns: The start frame of the current sequence if one is loaded, otherwise -1
        """
        if not self.project_settings.current_wall:
            return -1
        return self.project_settings.current_wall.sequence_loader.start_frame

    @property
    def current_frame(self) -> int:
        """ Returns the current frame of the current sequence if one is loaded, otherwise -1

        Returns: The current frame of the current sequence if one is loaded, otherwise -1
        """
        if not self.project_settings.current_wall:
            return -1

        return self.project_settings.current_wall.sequence_loader.current_frame

    @property
    def end_frame(self) -> int:
        """ Returns the end frame of the current sequence if one is loaded, otherwise -1

        Returns: The end frame of the current sequence if one is loaded, otherwise -1
        """
        if not self.project_settings.current_wall:
            return -1
        return self.project_settings.current_wall.sequence_loader.end_frame


class TimelineLoader(SequenceLoader):
    """
    Which inherits from SequenceLoader and specializes in loading PixMapFrames.
    """

    def __init__(self, led_wall_settings: LedWallSettings):
        """
        Initialize the model with start, end, and current frames.
        """
        SequenceLoader.__init__(self, led_wall_settings)
        self.frame_class = PixMapFrame

    def _load_and_cache(self, frame):
        super()._load_and_cache(frame)
        self.cache[frame].load_pixmap()


class TimelineWidget(LockableWidget):
    """
    Widget to control the timeline.
    """

    def __init__(self, model, event_filter, parent=None):
        """
        Initialize the widget and set up UI.
        """
        super().__init__()
        self.setFocusPolicy(Qt.StrongFocus)

        self.transport_layout = None
        self.to_start_button = None
        self.step_back_button = None
        self.step_back_pattern_button = None
        self.step_forward_button = None
        self.step_forward_pattern_button = None
        self.current_frame_spinbox = None
        self.current_frame_label = None
        self.end_frame_spinbox = None
        self.end_frame_label = None
        self.slider = None
        self.start_frame_spinbox = None
        self.start_frame_label = None
        self.h_layout = None
        self.layout = None
        self.to_end_button = None
        self.model = model
        self.parent = parent
        self.event_filter = event_filter

        self.init_ui()

        self.installEventFilter(self.event_filter)
        self.event_filter.left_arrow_pressed.connect(self.step_back_pattern)
        self.event_filter.right_arrow_pressed.connect(self.step_forward_pattern)

        self.model.start_frame_changed.connect(self.slider.setMinimum)
        self.model.start_frame_changed.connect(self.start_frame_spinbox.setMinimum)
        self.model.start_frame_changed.connect(self.end_frame_spinbox.setMinimum)
        self.model.start_frame_changed.connect(self.start_frame_spinbox.setValue)
        self.model.start_frame_changed.connect(self.current_frame_spinbox.setMinimum)

        self.model.end_frame_changed.connect(self.current_frame_spinbox.setMaximum)
        self.model.end_frame_changed.connect(self.end_frame_spinbox.setMaximum)
        self.model.end_frame_changed.connect(self.end_frame_spinbox.setValue)
        self.model.end_frame_changed.connect(self.start_frame_spinbox.setMaximum)
        self.model.end_frame_changed.connect(self.slider.setMaximum)
        self.model.current_frame_changed.connect(self.update_slider_value)
        self.model.current_frame_changed.connect(self.current_frame_spinbox.setValue)

        self.slider.valueChanged.connect(self.model.set_current_frame)
        self.start_frame_spinbox.editingFinished.connect(self.update_start_frame)
        self.end_frame_spinbox.editingFinished.connect(self.update_end_frame)
        self.current_frame_spinbox.editingFinished.connect(self.update_current_frame)
        self.disable()

    def init_ui(self):
        """
        Set up UI elements.
        """
        self.layout = QVBoxLayout()
        self.h_layout = QHBoxLayout()

        self.start_frame_label = QLabel("Start Frame:")
        self.start_frame_spinbox = QSpinBox()
        self.start_frame_spinbox.setMinimum(0)
        self.start_frame_spinbox.setMaximum(1000)
        self.start_frame_spinbox.setValue(self.model.start_frame)

        self.slider = QSlider(Qt.Horizontal)
        self.slider.setMinimum(0)
        self.slider.setMaximum(1000)
        self.slider.setValue(self.model.current_frame)

        self.end_frame_label = QLabel("End Frame:")
        self.end_frame_spinbox = QSpinBox()
        self.end_frame_spinbox.setMinimum(0)
        self.end_frame_spinbox.setMaximum(1000)
        self.end_frame_spinbox.setValue(self.model.end_frame)

        self.current_frame_label = QLabel("Current Frame:")
        self.current_frame_spinbox = QSpinBox()
        self.current_frame_spinbox.setMinimum(0)
        self.current_frame_spinbox.setMaximum(1000)
        self.current_frame_spinbox.setValue(self.model.current_frame)

        self.h_layout.addWidget(self.start_frame_label)
        self.h_layout.addWidget(self.start_frame_spinbox)
        self.h_layout.addWidget(self.slider)
        self.h_layout.addWidget(self.end_frame_label)
        self.h_layout.addWidget(self.end_frame_spinbox)
        self.h_layout.addWidget(self.current_frame_label)
        self.h_layout.addWidget(self.current_frame_spinbox)

        self.layout.addLayout(self.h_layout)
        self.transport_controls()

        self.setLayout(self.layout)

    def transport_controls(self):
        """
        Create transport controls.
        """
        self.transport_layout = QHBoxLayout()
        self.transport_layout.setAlignment(Qt.AlignCenter)

        self.step_back_pattern_button = QPushButton("#<<")
        self.step_back_pattern_button.clicked.connect(self.step_back_pattern)

        self.to_start_button = QPushButton("|<<")
        self.to_start_button.clicked.connect(self.set_to_start)

        self.step_back_button = QPushButton("|<")
        self.step_back_button.clicked.connect(self.step_back)

        self.step_forward_button = QPushButton(">|")
        self.step_forward_button.clicked.connect(self.step_forward)

        self.to_end_button = QPushButton(">>|")
        self.to_end_button.clicked.connect(self.set_to_end)

        self.step_forward_pattern_button = QPushButton(">>#")
        self.step_forward_pattern_button.clicked.connect(self.step_forward_pattern)

        self.transport_layout.addWidget(self.to_start_button)
        self.transport_layout.addWidget(self.step_back_pattern_button)
        self.transport_layout.addWidget(self.step_back_button)
        self.transport_layout.addWidget(self.step_forward_button)
        self.transport_layout.addWidget(self.step_forward_pattern_button)
        self.transport_layout.addWidget(self.to_end_button)

        self.layout.addLayout(self.transport_layout)

    # pylint: disable=W0613(unused-argument)
    def enterEvent(self, event: QEvent) -> None:
        self.setFocus()

    @staticmethod
    def select_folder() -> str:
        """ returns the file path to the selected folder if one was selected

        :return: returns the file path to the selected folder if one was selected
        """
        return utils.select_folder()

    def _set_active_state(self, value: bool):
        """
        Either enables or disables all the UI components
        """
        for i in range(self.layout.count()):
            layout = self.layout.itemAt(i)
            for j in range(self.layout.itemAt(i).count()):
                widget = layout.itemAt(j).widget()
                if widget is not None:
                    widget.setDisabled(value)

    def load_sequence(self):
        """ Loads an image sequence into the model
        """

        folder_path = self.select_folder()
        if not folder_path:
            return

        if not os.path.exists(folder_path):
            return

        file_ext = constants.FileFormats.FF_EXR
        self.model.load_sequence(folder_path, file_ext)
        frame = self.model.current_frame

        self.model.set_current_frame(frame + 1)
        self.model.set_current_frame(frame)

    @Slot()
    def update_slider_value(self, value):
        """
           Update slider value.
        """
        self.slider.repaint()
        self.slider.setValue(value)
        self.slider.repaint()

    @Slot()
    def update_start_frame(self):
        """
        Update start frame in the model.
        """
        self.model.set_start_frame(self.start_frame_spinbox.value())
        self.slider.setMinimum(self.start_frame_spinbox.value())
        self.slider.repaint()

    @Slot()
    def update_end_frame(self):
        """
        Update end frame in the model.
        """
        self.model.set_end_frame(self.end_frame_spinbox.value())
        self.slider.setMaximum(self.end_frame_spinbox.value())
        self.slider.repaint()

    @Slot()
    def update_current_frame(self):
        """
        Update current frame in model.
        """
        self.model.set_current_frame(self.current_frame_spinbox.value())

    @Slot()
    def set_to_start(self):
        """
        Set current frame to start frame.
        """
        self.model.set_current_frame(self.start_frame_spinbox.value())
        self.slider.repaint()

    @Slot()
    def step_back(self):
        """
        Step back one frame.
        """
        try:
            self.model.set_current_frame(max(self.model.current_frame - 1, self.start_frame_spinbox.value()))
            self.slider.repaint()
        except FrameRangeException:
            return

    @Slot()
    def step_forward(self):
        """
        Step forward one frame.
        """
        try:
            self.model.set_current_frame(min(self.model.current_frame + 1, self.end_frame_spinbox.value()))
            self.slider.repaint()
        except FrameRangeException:
            return

    @Slot()
    def step_forward_pattern(self):
        """
        Step forward to next pattern frame.
        """
        try:
            first_red_frame = self.model.project_settings.current_wall.separation_results.first_red_frame
            target_frame = self.model.current_frame
            if target_frame < first_red_frame.frame_num:
                target_frame = first_red_frame.frame_num
            elif target_frame >= first_red_frame.frame_num:
                target_frame += self.model.project_settings.current_wall.separation_results.separation
            self.model.set_current_frame(target_frame)
            self.slider.repaint()
        except FrameRangeException:
            return

    @Slot()
    def step_back_pattern(self):
        """
        Step back to next pattern frame.
        """
        try:
            first_red_frame = self.model.project_settings.current_wall.separation_results.first_red_frame
            target_frame = self.model.current_frame
            if target_frame < first_red_frame.frame_num:
                target_frame = first_red_frame.frame_num
            elif target_frame >= first_red_frame.frame_num:
                target_frame -= self.model.project_settings.current_wall.separation_results.separation
            self.model.set_current_frame(target_frame)
            self.slider.repaint()
        except FrameRangeException:
            return

    @Slot()
    def set_to_end(self):
        """
        Set current frame to end frame.
        """
        self.model.set_current_frame(self.end_frame_spinbox.value())
        self.slider.repaint()
