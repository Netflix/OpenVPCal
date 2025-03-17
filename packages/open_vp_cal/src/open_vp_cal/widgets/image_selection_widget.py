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

This module contains the updated view for the image selection widget.
It now implements a polygon-based selection using Qt so that the user can click four
points over the image. When four points are selected, they are ordered and the resulting
ROI is saved to the current wall in the project settings. The underlying image remains unchanged,
and the polygon is drawn as an overlay. Additionally, control point vertices are drawn in green,
and they are movable to adjust the polygon.
"""

import math
from typing import Tuple, List

import numpy as np

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt, QEvent
from PySide6.QtWidgets import QApplication

from open_vp_cal.core.resource_loader import ResourceLoader
from open_vp_cal.widgets.project_settings_widget import ProjectSettingsModel
from open_vp_cal.widgets.timeline_widget import PixMapFrame


def order_points(pts: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Orders four points in the order: top-left, top-right, bottom-right, bottom-left.
    This is computed using the sum and difference of coordinates.
    """
    pts_array = np.array(pts, dtype="float32")
    s = pts_array.sum(axis=1)
    rect = [None] * 4
    rect[0] = pts_array[np.argmin(s)]  # top-left has smallest sum
    rect[2] = pts_array[np.argmax(s)]  # bottom-right has largest sum

    diff = np.diff(pts_array, axis=1)
    rect[1] = pts_array[np.argmin(diff)]  # top-right has smallest difference
    rect[3] = pts_array[np.argmax(diff)]  # bottom-left has largest difference

    return [tuple(pt) for pt in rect]


class ControlPoint(QtWidgets.QGraphicsEllipseItem):
    def __init__(self, index: int, pos: QtCore.QPointF, update_func):
        radius = 4
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.index = index
        self.setBrush(QtGui.QBrush(Qt.green))
        # Enable selection and movement.
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsScenePositionChanges, True)
        self.update_func = update_func
        self.setPos(pos)
        # Ensure control points appear above the polygon.
        self.setZValue(150)

    def itemChange(self, change, value):
        if change == QtWidgets.QGraphicsItem.ItemPositionChange:
            newPos = value
            if self.update_func:
                self.update_func(self.index, newPos)
        return super().itemChange(change, value)


class PolygonSelectionScene(QtWidgets.QGraphicsScene):
    def __init__(self, parent=None, selection_callback=None):
        super().__init__(parent)
        self.selection_callback = selection_callback
        self.polygon_points: List[QtCore.QPointF] = []
        self.selection_complete = False

        # Draw the polygon with a red outline.
        self.polygon_item = QtWidgets.QGraphicsPolygonItem()
        pen = QtGui.QPen(Qt.red)
        pen.setWidth(2)
        self.polygon_item.setPen(pen)
        self.polygon_item.setZValue(100)
        # Disable mouse events on the polygon so control points get them.
        self.polygon_item.setAcceptedMouseButtons(Qt.NoButton)
        self.addItem(self.polygon_item)

        # Control points list; created after 4 points are selected.
        self.control_points: List[ControlPoint] = []

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        if not self.selection_complete:
            if event.button() == Qt.LeftButton:
                point = event.scenePos()
                self.polygon_points.append(point)
                poly = QtGui.QPolygonF(self.polygon_points)
                self.polygon_item.setPolygon(poly)
                if len(self.polygon_points) == 4:
                    self.finalizePolygon()
        # Always call the base implementation so that control points receive events.
        super().mousePressEvent(event)

    def finalizePolygon(self):
        # Order the points for consistency.
        pts = [(p.x(), p.y()) for p in self.polygon_points]
        ordered = order_points(pts)
        self.polygon_points = [QtCore.QPointF(x, y) for (x, y) in ordered]
        self.polygon_item.setPolygon(QtGui.QPolygonF(self.polygon_points))
        # Create control points for each vertex.
        for i, pt in enumerate(self.polygon_points):
            cp = ControlPoint(i, pt, self.controlPointMoved)
            self.control_points.append(cp)
            self.addItem(cp)
        self.selection_complete = True
        self._emitSelection()

    def controlPointMoved(self, index: int, newPos: QtCore.QPointF):
        """
        Called by a control point when it is moved.
        Updates the corresponding vertex in the polygon and recalculates the ROI.
        """
        self.polygon_points[index] = newPos
        self.polygon_item.setPolygon(QtGui.QPolygonF(self.polygon_points))
        self._emitSelection()

    def _emitSelection(self):
        """
        Recalculates the ROI from the current polygon and calls the selection callback.
        """
        pts = [(pt.x(), pt.y()) for pt in self.polygon_points]
        xs = [pt[0] for pt in pts]
        ys = [pt[1] for pt in pts]
        left = int(min(xs))
        right = int(max(xs))
        top = int(min(ys))
        bottom = int(max(ys))
        if self.selection_callback:
            self.selection_callback(left, right, top, bottom, pts)

    def resetSelection(self):
        """
        Clears the polygon overlay, removes control points, and resets the selection.
        """
        self.selection_complete = False
        self.polygon_points = []
        self.polygon_item.setPolygon(QtGui.QPolygonF())
        for cp in self.control_points:
            self.removeItem(cp)
        self.control_points = []

    def setPolygon(self, points: List[Tuple[float, float]]):
        """
        Sets the polygon (e.g. from a saved ROI). The expected order is:
        top-left, top-right, bottom-right, bottom-left.
        """
        poly = QtGui.QPolygonF([QtCore.QPointF(x, y) for (x, y) in points])
        self.polygon_item.setPolygon(poly)
        self.polygon_points = [QtCore.QPointF(x, y) for (x, y) in points]
        self.selection_complete = True
        # Create control points for the loaded polygon.
        for i, pt in enumerate(self.polygon_points):
            cp = ControlPoint(i, pt, self.controlPointMoved)
            self.control_points.append(cp)
            self.addItem(cp)
        self._emitSelection()


class ImageSelectionGraphicsView(QtWidgets.QGraphicsView):
    """
    A graphics view that displays an image and supports Ctrl+wheel zooming.
    """
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent

    def mapToSceneInverted(self, pos) -> QtCore.QPointF:
        transform = self.transform().inverted()[0]
        return transform.map(pos)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            zoom_factor = 1.02
            view_pos = event.position()
            scene_pos = self.mapToScene(view_pos.toPoint())
            if event.angleDelta().y() > 0:
                self.scale(zoom_factor, zoom_factor)
            else:
                self.scale(1 / zoom_factor, 1 / zoom_factor)
            new_view_pos = self.mapFromScene(scene_pos)
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + view_pos.x() - new_view_pos.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + view_pos.y() - new_view_pos.y())
        else:
            super().wheelEvent(event)


class ImageSelectionWidget(QtWidgets.QWidget):
    """
    A widget for selecting a polygonal region in an image.
    The user selects four points on the image; these points are ordered and used
    to compute a bounding box ROI (in the format [left, right, top, bottom]) which is saved to the
    current wall in the project settings. The underlying image remains unchanged and the polygon
    overlay (red) with movable control points (green) is drawn on top.
    """
    def __init__(self, project_settings: ProjectSettingsModel, parent=None):
        super().__init__(parent)
        self.place_holder_pixmap = None
        self.current_frame = None
        self.layout = None
        self.pixmap = None
        self.graphics_view = None
        self.graphics_scene = None
        self.project_settings = project_settings
        self.init_ui()

    def init_ui(self):
        self.layout = QtWidgets.QVBoxLayout(self)
        self.graphics_view = ImageSelectionGraphicsView(self)
        self.layout.addWidget(self.graphics_view)

        # Create the polygon selection scene with the callback.
        self.graphics_scene = PolygonSelectionScene(selection_callback=self.polygonSelected)
        self.graphics_view.setScene(self.graphics_scene)

        self.place_holder_pixmap = QPixmap(ResourceLoader.open_vp_cal_logo()).scaled(
            500, 500, Qt.KeepAspectRatio
        )
        # Add the image pixmap with a low z-value so it appears behind the polygon.
        self.pixmap = self.graphics_scene.addPixmap(self.place_holder_pixmap)
        self.pixmap.setZValue(0)

        # If a saved ROI exists, load it and set up the polygon overlay.
        if self.project_settings.current_wall and self.project_settings.current_wall.roi:
            roi = self.project_settings.current_wall.roi  # [left, right, top, bottom]
            points = [(roi[0], roi[2]), (roi[1], roi[2]), (roi[1], roi[3]), (roi[0], roi[3])]
            self.graphics_scene.setPolygon(points)
        self.clear()
        QApplication.processEvents()

    def current_frame_changed(self, frame: PixMapFrame) -> None:
        """Update the displayed image when the frame changes."""
        self.display_image(frame)

    def display_image(self, frame: PixMapFrame) -> None:
        """
        Load and display an image from the given frame.
        Resets the polygon overlay for a new image.
        """
        QApplication.processEvents()
        self.current_frame = frame
        self.graphics_scene.resetSelection()
        self.pixmap.setPixmap(self.current_frame.pixmap)
        self.pixmap.setPos(0, 0)
        QApplication.processEvents()

    def clear(self) -> None:
        """Clear the image and display the placeholder."""
        if self.pixmap:
            self.pixmap.setPixmap(self.place_holder_pixmap)
            scene_rect = self.graphics_scene.sceneRect()
            center_x = scene_rect.width() / 2
            center_y = scene_rect.height() / 2

            pixmap_width = self.pixmap.pixmap().width()
            pixmap_height = self.pixmap.pixmap().height()
            pixmap_x = center_x - pixmap_width / 2
            pixmap_y = center_y - pixmap_height / 2

            self.pixmap.setPos(pixmap_x, pixmap_y)

    def polygonSelected(self, left: int, right: int, top: int, bottom: int,
                        ordered_points: List[Tuple[float, float]]) -> None:
        """
        Callback when the polygon selection is complete or updated.
        Stores the ROI (as the bounding box) in the project settings.
        The underlying image is left intact.
        """
        if self.project_settings.current_wall:
            self.project_settings.current_wall.roi = [left, right, top, bottom]

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        """
        Display a context menu on right-click with an option to reset the ROI.
        """
        context_menu = QtWidgets.QMenu(self)
        reset_roi = context_menu.addAction("Reset ROI")
        reset_roi.triggered.connect(self.on_reset_roi)
        context_menu.exec_(event.globalPos())

    def on_reset_roi(self) -> None:
        """
        Reset the ROI to its default value ([0, 100, 0, 100]),
        reset the polygon overlay, and re-display the current frame.
        """
        if self.current_frame and self.project_settings.current_wall:
            self.project_settings.current_wall.roi = [0, 100, 0, 100]
            self.graphics_scene.resetSelection()
            self.display_image(self.current_frame)