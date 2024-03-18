"""
The module contains a View which allows us to view the swatch analysis results, and control their exposure.
"""
from PySide6.QtWidgets import QWidget, QGraphicsView, QGraphicsScene, QVBoxLayout, QSlider, QLabel, \
    QHBoxLayout, QSpinBox, QComboBox, QCheckBox
from PySide6.QtGui import QPixmap, QPainter, QMouseEvent
from PySide6.QtCore import Qt

import PyOpenColorIO as Ocio
import numpy as np
import colour
import colour.algebra as ca

from open_vp_cal.core import constants
from open_vp_cal.core import utils as core_utils
from open_vp_cal.core.ocio_config import OcioConfigWriter
from open_vp_cal.core.resource_loader import ResourceLoader
from open_vp_cal.imaging import imaging_utils
from open_vp_cal.widgets import utils


class ImageViewerGraphicsView(QGraphicsView):
    """
    A QGraphicsView which allows us to zoom in and out of the image
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setRenderHint(QPainter.Antialiasing)
        self.setRenderHint(QPainter.SmoothPixmapTransform)
        self.setDragMode(QGraphicsView.ScrollHandDrag)
        self.setOptimizationFlags(QGraphicsView.DontAdjustForAntialiasing | QGraphicsView.DontSavePainterState)
        self.setViewportUpdateMode(QGraphicsView.FullViewportUpdate)
        self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)

    def wheelEvent(self, event: QMouseEvent) -> None:
        """Implement zooming functionality"""
        zoom_in_factor = 1.15
        zoom_out_factor = 1 / zoom_in_factor

        # Save the scene pos
        old_pos = self.mapToScene(event.position().toPoint())

        # Zoom
        if event.angleDelta().y() > 0:
            zoom_factor = zoom_in_factor
        else:
            zoom_factor = zoom_out_factor
        self.scale(zoom_factor, zoom_factor)

        # Get the new position
        new_pos = self.mapToScene(event.position().toPoint())

        # Move the scene to old position
        delta = new_pos - old_pos
        self.translate(delta.x(), delta.y())


class SwatchViewer(QWidget):
    """
    A widget which allows us to view the swatch analysis results, and control their exposure with a slider
    """

    def __init__(self, project_settings, parent=None):
        super().__init__(parent)
        self.led_walls = []
        self.view = ImageViewerGraphicsView()
        self.scene = QGraphicsScene()
        self.view.setScene(self.scene)
        self.project_settings = project_settings

        # slider for exposure control
        self.slider = QSlider(Qt.Horizontal)
        self.slider.setRange(-10, 10)
        self.slider.setValue(0)
        self.slider.valueChanged.connect(self.exposure_changed)

        # spin box for displaying slider value
        self.spin_box = QSpinBox()
        self.spin_box.setRange(-10, 10)
        self.spin_box.setValue(0)
        self.slider.valueChanged.connect(self.spin_box.setValue)
        self.spin_box.valueChanged.connect(self.slider.setValue)

        display_space_layout = QHBoxLayout()
        self.display_transform_combo_box = QComboBox()
        self.display_transform_label = QLabel("Display")
        display_space_layout.addWidget(self.display_transform_label)
        display_space_layout.addWidget(self.display_transform_combo_box)

        view_space_layout = QHBoxLayout()
        self.view_combo_box = QComboBox()
        self.view_label = QLabel("View")
        view_space_layout.addWidget(self.view_label)
        view_space_layout.addWidget(self.view_combo_box)

        preview_calibration_layout = QHBoxLayout()
        self.preview_calibration_checkbox = QCheckBox()
        self.preview_calibration_checkbox.setChecked(False)
        self.preview_calibration_checkbox.stateChanged.connect(self.preview_calibration_changed)
        self.preview_calibration_label = QLabel("Preview Calibration")
        preview_calibration_layout.addWidget(self.preview_calibration_label)
        preview_calibration_layout.addWidget(self.preview_calibration_checkbox)

        apply_white_balance_layout = QHBoxLayout()
        self.apply_white_balance_checkbox = QCheckBox()
        self.apply_white_balance_checkbox.setChecked(True)
        self.apply_white_balance_checkbox.stateChanged.connect(self.preview_calibration_changed)
        self.apply_white_balance_label = QLabel("Apply White Balance Preview")
        apply_white_balance_layout.addWidget(self.apply_white_balance_label)
        apply_white_balance_layout.addWidget(self.apply_white_balance_checkbox)

        # label for the slider
        self.label = QLabel("Exposure")

        layout = QVBoxLayout()
        layout.addWidget(self.view)

        # layout for slider and its label
        slider_layout = QHBoxLayout()
        slider_layout.addWidget(self.label)
        slider_layout.addWidget(self.slider)
        slider_layout.addWidget(self.spin_box)

        controls_layout = QHBoxLayout()
        controls_layout.addLayout(slider_layout)
        controls_layout.addLayout(display_space_layout)
        controls_layout.addLayout(view_space_layout)
        controls_layout.addLayout(apply_white_balance_layout)
        controls_layout.addLayout(preview_calibration_layout)
        layout.addLayout(controls_layout)

        self.setLayout(layout)
        self.ocio_config = None
        self._image_cache = {}
        self.init()

    def init(self) -> None:
        """ Initializes some of the display transform combo box with its options

        Returns:

        """
        self.display_transform_combo_box.currentTextChanged.connect(self.display_transform_changed)
        self.view_combo_box.currentTextChanged.connect(self.update_exposure)
        self.update_display_combo_box()

    def update_display_combo_box(self):
        """ Updates the display transform combo box with the available options
        """
        self.display_transform_combo_box.clear()
        self.ocio_config = Ocio.Config.CreateFromFile(ResourceLoader.ocio_config_path())
        for display in self.ocio_config.getDisplaysAll():
            self.display_transform_combo_box.addItem(display)

    def clear_image_cache(self) -> None:
        """ Clears the image cache """
        self._image_cache = {}

    def exposure_changed(self) -> None:
        """ Function, which runs when the exposure slider changes, forces the update_exposure to run
        """
        self.clear_image_cache()
        self.update_exposure()

    def preview_calibration_changed(self, _) -> None:
        """ Function, which runs when the preview calibration checkbox changes, forces the update_exposure to run
        """
        self.clear_image_cache()
        self.update_exposure()

    def display_transform_changed(self, display_transform: str) -> None:
        """ Function, which runs when the display transform changes, updates the views combo box for the valid options

        Args:
            display_transform: the name of the new display transform
        """
        self.clear_image_cache()
        self.update_view_combo_box(display_transform)

    def update_view_combo_box(self, display_transform: str) -> None:
        """ Updates the view combo box with the available options for the given display transform

        Args:
            display_transform: the name of the display transform
        """
        self.clear_image_cache()
        self.view_combo_box.clear()
        views = self.ocio_config.getViews(display_transform)
        for view in views:
            self.view_combo_box.addItem(view)

    def display_images(self) -> None:
        """Displays the images in the QGraphicsView."""
        self.update_exposure()
        self.view.fitInView(self.scene.sceneRect(), Qt.KeepAspectRatio)

    def update_exposure(self) -> None:
        """Update exposure based on slider value."""

        if not self.led_walls:
            return

        display_transform = self.display_transform_combo_box.currentText()
        view_transform = self.view_combo_box.currentText()
        if not display_transform or not view_transform:
            return

        self.clear()
        width = 0

        exposure_slider_value = self.slider.value()
        preview_calibration = self.preview_calibration_checkbox.isChecked()
        for led_wall in self.led_walls:
            if (not led_wall.auto_wb_source and not led_wall.match_reference_wall
                    and not led_wall.use_external_white_point):
                apply_white_balance_checked = False
            else:
                apply_white_balance_checked = self.apply_white_balance_checkbox.isChecked()
            cache_key = (f"{display_transform}_{view_transform}_{exposure_slider_value}_"
                         f"{apply_white_balance_checked}_{preview_calibration}_{led_wall.name}")
            if cache_key not in self._image_cache:
                sample_buffers_processed = []
                reference_buffers_processed = []

                # Take the image buffers in their input space (ACES2065-1) and apply the calibration if we have one
                for count, sample in enumerate(led_wall.processing_results.sample_buffers):
                    sample_buffers_stitched = sample
                    sample_reference_buffers_stitched = led_wall.processing_results.sample_reference_buffers[count]

                    sp_np = imaging_utils.image_buf_to_np_array(sample_buffers_stitched)
                    exposure_scaling_factor = None
                    if led_wall.processing_results.calibration_results:
                        exposure_scaling_factor = led_wall.processing_results.calibration_results[
                            constants.Results.EXPOSURE_SCALING_FACTOR]

                    if not exposure_scaling_factor:
                        if led_wall.processing_results.pre_calibration_results:
                            exposure_scaling_factor = led_wall.processing_results.pre_calibration_results[
                                constants.Results.EXPOSURE_SCALING_FACTOR]

                    sp_np = sp_np / exposure_scaling_factor

                    if apply_white_balance_checked and led_wall.processing_results:
                        white_balance_matrix = None
                        if led_wall.processing_results.calibration_results:
                            white_balance_matrix = led_wall.processing_results.calibration_results[
                                constants.Results.WHITE_BALANCE_MATRIX]

                        if not white_balance_matrix:
                            if led_wall.processing_results.pre_calibration_results:
                                white_balance_matrix = led_wall.processing_results.pre_calibration_results[
                                    constants.Results.WHITE_BALANCE_MATRIX]

                        if white_balance_matrix:
                            working_cs = colour.RGB_COLOURSPACES[constants.ColourSpace.CS_ACES]
                            native_camera_gamut_cs = core_utils.get_native_camera_colourspace_for_led_wall(led_wall)

                            camera_conversion_cat = constants.CAT.CAT_CAT02
                            if native_camera_gamut_cs.name == constants.CameraColourSpace.RED_WIDE_GAMUT:
                                camera_conversion_cat = constants.CAT.CAT_BRADFORD

                            # Convert the samples from working to camera native gamut
                            sp_np = colour.RGB_to_RGB(
                                sp_np, working_cs, native_camera_gamut_cs, camera_conversion_cat
                            )

                            # Apply the white balance matrix
                            sp_np = [ca.vector_dot(white_balance_matrix, m) for m in sp_np]

                            # Convert the samples from camera native gamut to working
                            sp_np = colour.RGB_to_RGB(
                                sp_np, native_camera_gamut_cs, working_cs, camera_conversion_cat
                            )

                    sp_np = sp_np.astype(np.float32)

                    # Calibration Is Applied
                    if led_wall.processing_results:
                        if led_wall.processing_results.ocio_config_output_file and preview_calibration:
                            calibration_cs_metadata = OcioConfigWriter.get_calibration_preview_space_metadata(led_wall)
                            imaging_utils.apply_color_converstion_to_np_array(
                                sp_np,
                                constants.ColourSpace.CS_ACES,
                                calibration_cs_metadata[0],
                                color_config=led_wall.processing_results.ocio_config_output_file
                            )

                    rf_np = imaging_utils.image_buf_to_np_array(sample_reference_buffers_stitched)

                    # For the Macbeth Samples We Need TO Scale Them Down To 100 Nits Range
                    if count >= len(led_wall.processing_results.sample_buffers) - 18:
                        sp_np /= (led_wall.target_max_lum_nits * 0.01)
                        rf_np /= (led_wall.target_max_lum_nits * 0.01)

                    # Expose up the array linearly
                    sp_np_exposed = sp_np * (2.0 ** exposure_slider_value)
                    rf_np_exposed = rf_np * (2.0 ** exposure_slider_value)

                    # Convert back to an image buffer and convert to srgb for display
                    exposed_sp_buffer = imaging_utils.img_buf_from_numpy_array(sp_np_exposed)
                    exposed_rf_buffer = imaging_utils.img_buf_from_numpy_array(rf_np_exposed)

                    sample_buffers_processed.append(exposed_sp_buffer)
                    reference_buffers_processed.append(exposed_rf_buffer)

                # Stitch The Processed Buffers Together
                exposed_sp_buffer, exposed_rf_buffer = imaging_utils.create_and_stitch_analysis_strips(
                    reference_buffers_processed, sample_buffers_processed)

                # Nest The Image Together
                sample_swatch_nested = imaging_utils.nest_analysis_swatches(
                    exposed_sp_buffer,
                    exposed_rf_buffer
                )

                # Convert To Display
                exposed_display_buffer = imaging_utils.apply_display_conversion(
                    sample_swatch_nested, display_transform, view_transform
                )

                # Add Text Label Above Each Strip
                header_height = int(exposed_display_buffer.spec().height * 0.1)
                text_size = int(exposed_display_buffer.spec().height * 0.05)
                text_buffer = imaging_utils.new_image(exposed_display_buffer.spec().width, header_height)

                name = led_wall.name
                text_color = [1, 1, 1]
                imaging_utils.add_text_to_image_buffer(name, text_buffer, text_color, text_size)

                stitched_value = imaging_utils.stitch_images_vertically([text_buffer, exposed_display_buffer])

                # Convert back to a numpy array and create a QImage from it
                image = utils.create_qimage_rgb8_from_numpy_array(
                    imaging_utils.image_buf_to_np_array(stitched_value)
                )
                self._image_cache[cache_key] = (
                    image, stitched_value.spec().width, stitched_value.spec().height)

            image, im_width, _ = self._image_cache[cache_key]
            item = self.scene.addPixmap(QPixmap.fromImage(image))
            item.setPos(width, 0)
            width += im_width

    def on_led_wall_selection_changed(self, led_walls: [str]) -> None:
        """Update the image viewer when the LED wall selection changes."""
        self.led_walls = []
        self.clear()
        self.preview_calibration_checkbox.setEnabled(True)
        for led_wall_name in led_walls:
            led_wall = self.project_settings.get_led_wall(led_wall_name)

            if not led_wall.processing_results:
                continue

            if not led_wall.processing_results.sample_buffers:
                continue

            if not led_wall.processing_results.sample_reference_buffers:
                continue

            if not led_wall.processing_results.ocio_config_output_file:
                self.preview_calibration_checkbox.setChecked(False)
                self.preview_calibration_checkbox.setEnabled(False)

            self.led_walls.append(led_wall)

        if self.led_walls:
            self.display_images()

    def clear(self) -> None:
        """ Clear the scene back to an empty state
        """
        self.scene.clear()
