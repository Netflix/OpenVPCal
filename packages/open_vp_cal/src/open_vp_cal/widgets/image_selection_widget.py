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
ROI is saved to the current wall in the project settings as a list of four (x, y) tuples.
The underlying image remains unchanged, and the polygon is drawn as an overlay.
Control point vertices are drawn using a color map:
    0: red (top-left)
    1: green (top-right)
    2: blue (bottom-right)
    3: white (bottom-left)
If the ROI is inside out or if the control points do not satisfy the following criteria:
    - Red is higher than blue and white and more left than green.
    - Green is higher than blue and white and more right than red.
    - White is lower than red and green and more left than blue.
    - Blue is lower than red and green and more right than white.
then the polygon outline is drawn in red; otherwise, it is green.
After the initial ROI is set, subsequent left-clicks update the next corner sequentially—but only if the
user holds Alt (or Command on macOS). Without the modifier key the click only does selection.
The ROI is stored purely as four coordinate pairs with no UI transformation information.
"""

from typing import List, Tuple
import numpy as np

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtGui import QPixmap
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication

from open_vp_cal.core.resource_loader import ResourceLoader
from open_vp_cal.widgets.project_settings_widget import ProjectSettingsModel
from open_vp_cal.widgets.timeline_widget import PixMapFrame


def order_points(pts: List[Tuple[float, float]]) -> List[Tuple[float, float]]:
    """
    Orders four points in the order: top-left, top-right, bottom-right, bottom-left.
    Computed using the sum and difference of coordinates.

    Parameters:
        pts (List[Tuple[float, float]]): List of four (x, y) tuples.

    Returns:
        List[Tuple[float, float]]: Ordered list of points.
    """
    pts_array = np.array(pts, dtype="float32")
    s = pts_array.sum(axis=1)
    rect = [None] * 4
    rect[0] = pts_array[np.argmin(s)]  # top-left
    rect[2] = pts_array[np.argmax(s)]  # bottom-right
    diff = np.diff(pts_array, axis=1)
    rect[1] = pts_array[np.argmin(diff)]  # top-right
    rect[3] = pts_array[np.argmax(diff)]  # bottom-left
    return [tuple(pt) for pt in rect]


class ControlPoint(QtWidgets.QGraphicsEllipseItem):
    """
    A movable control point displayed as a small colored ellipse.

    Attributes:
        index (int): The index of the control point (0 to 3).
        update_func (callable): Callback function called with the control point index
                                and its new scene coordinate.

    Colors are assigned as follows:
        0: red, 1: green, 2: blue, 3: white.
    """
    def __init__(self, index: int, pos: QtCore.QPointF, update_func) -> None:
        radius: int = 4
        super().__init__(-radius, -radius, 2 * radius, 2 * radius)
        self.index: int = index
        color_map = {0: Qt.red, 1: Qt.green, 2: Qt.blue, 3: Qt.white}
        self.setBrush(QtGui.QBrush(color_map.get(index, Qt.green)))
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemSendsScenePositionChanges, True)
        self.update_func = update_func
        self.setPos(pos)
        self.setZValue(150)

    def itemChange(self, change: QtWidgets.QGraphicsItem.GraphicsItemChange, value) -> object:
        """
        Called when the item's state changes.

        Parameters:
            change: The type of change.
            value: The new value.

        Returns:
            The updated value.
        """
        if change == QtWidgets.QGraphicsItem.ItemPositionHasChanged:
            if self.update_func:
                self.update_func(self.index, self.mapToScene(0, 0))
        return super().itemChange(change, value)

    def mouseReleaseEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """
        Called on mouse release to ensure the final position is reported.

        Parameters:
            event: The mouse release event.
        """
        super().mouseReleaseEvent(event)
        if self.update_func:
            self.update_func(self.index, self.mapToScene(0, 0))


class PolygonSelectionScene(QtWidgets.QGraphicsScene):
    """
    A QGraphicsScene for polygon-based ROI selection.

    Before ROI finalization, left-clicks add points.
    Once 4 points are set, the ROI is finalized and subsequent left-clicks update corners sequentially,
    but only if the Alt key (or Command on macOS) is held.
    The ROI is emitted via a callback as a list of four (x, y) tuples in scene coordinates.
    Additionally, the polygon outline color is updated:
      - If the polygon is inside out or the control points do not meet the expected criteria,
        the outline is red.
      - Otherwise, the outline is green.

    Attributes:
        selection_callback (callable): A callback function that accepts a list of four (x, y) tuples.
    """
    def __init__(self, parent=None, selection_callback=None) -> None:
        super().__init__(parent)
        self.selection_callback = selection_callback
        self.polygon_points: List[QtCore.QPointF] = []
        self.selection_complete: bool = False
        self.current_update_index: int = 0
        self.polygon_item = QtWidgets.QGraphicsPolygonItem()
        pen = QtGui.QPen(Qt.red)
        pen.setWidth(2)
        self.polygon_item.setPen(pen)
        self.polygon_item.setZValue(100)
        self.polygon_item.setAcceptedMouseButtons(Qt.NoButton)
        self.addItem(self.polygon_item)
        self.control_points: List[ControlPoint] = []

    def mousePressEvent(self, event: QtWidgets.QGraphicsSceneMouseEvent) -> None:
        """
        Handles mouse press events.
        Before ROI finalization, left-clicks add points.
        After finalization, left-clicks update the next corner sequentially only if the Alt or Command modifier is held.

        Parameters:
            event (QtWidgets.QGraphicsSceneMouseEvent): The mouse press event.
        """
        if not self.selection_complete:
            if event.button() == Qt.LeftButton:
                point: QtCore.QPointF = event.scenePos()
                self.polygon_points.append(point)
                self.polygon_item.setPolygon(QtGui.QPolygonF(self.polygon_points))
                if len(self.polygon_points) == 4:
                    self.finalizePolygon()
        else:
            # After ROI is finalized, only update next corner if Alt or Command is held.
            if event.button() == Qt.LeftButton and (event.modifiers() & (Qt.AltModifier | Qt.MetaModifier)):
                point: QtCore.QPointF = event.scenePos()
                self.polygon_points[self.current_update_index] = point
                self.polygon_item.setPolygon(QtGui.QPolygonF(self.polygon_points))
                if self.control_points and self.current_update_index < len(self.control_points):
                    self.control_points[self.current_update_index].setPos(point)
                self._emitSelection()
                self.current_update_index = (self.current_update_index + 1) % 4
        super().mousePressEvent(event)

    def finalizePolygon(self) -> None:
        """
        Finalizes the ROI by ordering the 4 points, updating the polygon,
        and creating control points with distinct colors.
        """
        pts: List[Tuple[float, float]] = [(p.x(), p.y()) for p in self.polygon_points]
        ordered: List[Tuple[float, float]] = order_points(pts)
        self.polygon_points = [QtCore.QPointF(x, y) for (x, y) in ordered]
        self.polygon_item.setPolygon(QtGui.QPolygonF(self.polygon_points))
        for i, pt in enumerate(self.polygon_points):
            cp = ControlPoint(i, pt, self.controlPointMoved)
            self.control_points.append(cp)
            self.addItem(cp)
        self.selection_complete = True
        self.current_update_index = 0
        self._emitSelection()

    def controlPointMoved(self, index: int, newPos: QtCore.QPointF) -> None:
        """
        Called when a control point is moved; updates the corresponding vertex and emits the ROI.

        Parameters:
            index (int): The index of the control point.
            newPos (QtCore.QPointF): The new scene coordinate.
        """
        self.polygon_points[index] = newPos
        self.polygon_item.setPolygon(QtGui.QPolygonF(self.polygon_points))
        self._emitSelection()

    def compute_signed_area(self) -> float:
        """
        Computes the signed area of the polygon using the shoelace formula.

        Returns:
            float: The signed area (negative if the points are ordered clockwise).
        """
        area: float = 0.0
        n: int = len(self.polygon_points)
        for i in range(n):
            x1, y1 = self.polygon_points[i].x(), self.polygon_points[i].y()
            x2, y2 = self.polygon_points[(i + 1) % n].x(), self.polygon_points[(i + 1) % n].y()
            area += (x1 * y2 - y1 * x2)
        return area / 2.0

    def validate_control_points(self) -> bool:
        """
        Validates the control point arrangement.

        Conditions:
          - Red (index 0) must be higher than blue (index 2) and white (index 3) and more left than green (index 1).
          - Green (index 1) must be higher than blue (index 2) and white (index 3) and more right than red (index 0).
          - White (index 3) must be lower than red (index 0) and green (index 1) and more left than blue (index 2).
          - Blue (index 2) must be lower than red (index 0) and green (index 1) and more right than white (index 3).

        Returns:
            bool: True if all conditions are satisfied; False otherwise.
        """
        if len(self.polygon_points) < 4:
            return True
        r = self.polygon_points[0]
        g = self.polygon_points[1]
        b = self.polygon_points[2]
        w = self.polygon_points[3]
        cond1 = (r.y() < b.y() and r.y() < w.y() and r.x() < g.x())
        cond2 = (g.y() < b.y() and g.y() < w.y() and g.x() > r.x())
        cond3 = (w.y() > r.y() and w.y() > g.y() and w.x() < b.x())
        cond4 = (b.y() > r.y() and b.y() > g.y() and b.x() > w.x())
        return cond1 and cond2 and cond3 and cond4

    def _emitSelection(self) -> None:
        """
        Emits the current ROI as a list of four (x, y) tuples in scene coordinates.
        Also updates the polygon outline:
          - If the polygon is inverted (negative area) or the control point validation fails, outline is red.
          - Otherwise, outline is green.
        """
        area: float = self.compute_signed_area()
        pen: QtGui.QPen = self.polygon_item.pen()
        if area < 0 or not self.validate_control_points():
            pen.setColor(Qt.red)
        else:
            pen.setColor(Qt.green)
        self.polygon_item.setPen(pen)
        pts: List[Tuple[int, int]] = [(int(pt.x()), int(pt.y())) for pt in self.polygon_points]
        if self.selection_callback:
            self.selection_callback(pts)

    def resetSelection(self) -> None:
        """
        Clears the polygon overlay, removes control points, and resets the selection.
        """
        self.selection_complete = False
        self.polygon_points = []
        self.polygon_item.setPolygon(QtGui.QPolygonF())
        for cp in self.control_points:
            self.removeItem(cp)
        self.control_points = []

    def setPolygon(self, points: List[Tuple[float, float]]) -> None:
        """
        Loads a saved ROI (a list of four (x, y) tuples) and updates the polygon and control points.

        Parameters:
            points (List[Tuple[float, float]]): The ROI points in scene coordinates.
        """
        for cp in self.control_points:
            self.removeItem(cp)
        self.control_points = []
        poly = QtGui.QPolygonF([QtCore.QPointF(x, y) for (x, y) in points])
        self.polygon_item.setPolygon(poly)
        self.polygon_points = [QtCore.QPointF(x, y) for (x, y) in points]
        self.selection_complete = True
        for i, pt in enumerate(self.polygon_points):
            cp = ControlPoint(i, pt, self.controlPointMoved)
            self.control_points.append(cp)
            self.addItem(cp)
        self._emitSelection()


class ImageSelectionGraphicsView(QtWidgets.QGraphicsView):
    """
    A graphics view that displays an image and supports Ctrl+wheel zooming.
    """
    def __init__(self, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.parent = parent

    def mapToSceneInverted(self, pos: QtCore.QPointF) -> QtCore.QPointF:
        """
        Maps a point in view coordinates to scene coordinates.

        Parameters:
            pos (QtCore.QPointF): The point in view coordinates.

        Returns:
            QtCore.QPointF: The corresponding scene coordinate.
        """
        transform = self.transform().inverted()[0]
        return transform.map(pos)

    def wheelEvent(self, event: QtGui.QWheelEvent) -> None:
        """
        Handles mouse wheel events for zooming when Ctrl is held.

        Parameters:
            event (QtGui.QWheelEvent): The wheel event.
        """
        if event.modifiers() == Qt.ControlModifier:
            zoom_factor: float = 1.02
            view_pos: QtCore.QPointF = event.position()
            scene_pos: QtCore.QPointF = self.mapToScene(view_pos.toPoint())
            if event.angleDelta().y() > 0:
                self.scale(zoom_factor, zoom_factor)
            else:
                self.scale(1/zoom_factor, 1/zoom_factor)
            new_view_pos: QtCore.QPointF = self.mapFromScene(scene_pos)
            self.horizontalScrollBar().setValue(
                self.horizontalScrollBar().value() + view_pos.x() - new_view_pos.x())
            self.verticalScrollBar().setValue(
                self.verticalScrollBar().value() + view_pos.y() - new_view_pos.y())
        else:
            super().wheelEvent(event)


class ImageSelectionWidget(QtWidgets.QWidget):
    """
    A widget for selecting a polygonal region in an image.

    The user selects four points on the image to define an ROI as a list of four (x, y) tuples.
    The ROI is saved to the current wall in the project settings. The underlying image remains unchanged,
    and the polygon overlay is drawn with a red or green outline (red if inverted or invalid) along with
    control points in distinct colors (red, green, blue, white).
    After the initial ROI is set, subsequent left-clicks update corners sequentially only when the
    Alt (or Command on macOS) modifier is held.

    The ROI is stored in scene coordinates as a list of four (x, y) tuples.
    """
    def __init__(self, project_settings: ProjectSettingsModel, parent: QtWidgets.QWidget = None) -> None:
        super().__init__(parent)
        self.place_holder_pixmap: QPixmap = None
        self.current_frame: PixMapFrame = None
        self.layout: QtWidgets.QVBoxLayout = None
        self.pixmap: QtWidgets.QGraphicsPixmapItem = None
        self.graphics_view: ImageSelectionGraphicsView = None
        self.graphics_scene: PolygonSelectionScene = None
        self.project_settings: ProjectSettingsModel = project_settings
        self.init_ui()

    def init_ui(self) -> None:
        """
        Sets up the UI by creating the graphics view, scene, and image placeholder.
        """
        self.layout = QtWidgets.QVBoxLayout(self)
        self.graphics_view = ImageSelectionGraphicsView(self)
        self.layout.addWidget(self.graphics_view)
        self.graphics_scene = PolygonSelectionScene(selection_callback=self.polygonSelected)
        self.graphics_view.setScene(self.graphics_scene)
        self.place_holder_pixmap = QPixmap(ResourceLoader.open_vp_cal_logo()).scaled(
            500, 500, Qt.KeepAspectRatio)
        self.pixmap = self.graphics_scene.addPixmap(self.place_holder_pixmap)
        self.pixmap.setZValue(0)
        if self.project_settings.current_wall and self.project_settings.current_wall.roi:
            roi: List[Tuple[float, float]] = self.project_settings.current_wall.roi
            self.graphics_scene.setPolygon(roi)
        self.clear()
        QApplication.processEvents()

    def current_frame_changed(self, frame: PixMapFrame) -> None:
        """
        Called when the current frame changes.

        Parameters:
            frame (PixMapFrame): The new frame.
        """
        self.display_image(frame)

    def display_image(self, frame: PixMapFrame) -> None:
        """
        Loads and displays an image from the given frame.
        If a saved ROI exists, updates the polygon overlay accordingly.

        Parameters:
            frame (PixMapFrame): The frame to display.
        """
        QApplication.processEvents()
        self.current_frame = frame
        if self.project_settings.current_wall and self.project_settings.current_wall.roi:
            roi: List[List[float]] = self.project_settings.current_wall.roi
            roi_tuples = [(x, y) for x, y in roi]
            self.graphics_scene.setPolygon(roi_tuples)
        else:
            self.graphics_scene.resetSelection()
        self.pixmap.setPixmap(self.current_frame.pixmap)
        self.pixmap.setPos(0, 0)
        QApplication.processEvents()

    def clear(self) -> None:
        """
        Clears the image view and displays the placeholder.
        """
        if self.pixmap:
            self.pixmap.setPixmap(self.place_holder_pixmap)
            scene_rect = self.graphics_scene.sceneRect()
            center_x: float = scene_rect.width() / 2
            center_y: float = scene_rect.height() / 2
            pixmap_width: float = self.pixmap.pixmap().width()
            pixmap_height: float = self.pixmap.pixmap().height()
            pixmap_x: float = center_x - pixmap_width / 2
            pixmap_y: float = center_y - pixmap_height / 2
            self.pixmap.setPos(pixmap_x, pixmap_y)

    def polygonSelected(self, points: List[Tuple[float, float]]) -> None:
        """
        Callback when the polygon selection is updated.
        Stores the ROI (list of four (x, y) tuples) in the project settings.

        Parameters:
            points (List[Tuple[float, float]]): The ROI points.
        """
        if self.project_settings.current_wall:
            self.project_settings.current_wall.roi = [[x, y] for x, y in points]

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        """
        Displays a context menu with an option to reset the ROI.

        Parameters:
            event (QtGui.QContextMenuEvent): The context menu event.
        """
        context_menu = QtWidgets.QMenu(self)
        reset_roi = context_menu.addAction("Reset ROI")
        reset_roi.triggered.connect(self.on_reset_roi)
        context_menu.exec_(event.globalPos())

    def on_reset_roi(self) -> None:
        """
        Resets the ROI to a default value, clears the polygon overlay, and re-displays the current frame.
        """
        if self.current_frame and self.project_settings.current_wall:
            self.project_settings.current_wall.roi = [[0, 0], [100, 0], [100, 100], [0, 100]]
            self.graphics_scene.resetSelection()
            self.display_image(self.current_frame)
