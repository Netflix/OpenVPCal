"""
The module contains the View for the image selection widget, this allows the user to display an image and select a
region of it for analysis at a later date
"""
from typing import Tuple, List

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtGui import QPixmap
from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt, QEvent

from open_vp_cal.core.resource_loader import ResourceLoader
from open_vp_cal.widgets.project_settings_widget import ProjectSettingsModel
from open_vp_cal.widgets.timeline_widget import PixMapFrame


class ImageSelectionGraphicsView(QtWidgets.QGraphicsView):
    """
    Class: ImageSelectionGraphicsView
    A simple graphics view to display an image and allow the user to select a region of it
    """
    def __init__(self, parent=None):
        super().__init__()
        self.parent = parent

    # pylint: disable=C0103
    def mapToSceneInverted(self, pos) -> QtCore.QPointF:
        """ Map a position in view coordinates to scene coordinates and return the inverted transform

        Args:
            pos: position in view coordinates

        Returns: position in scene coordinates

        """
        transform = self.transform().inverted()[0]  # Inverted transform
        return transform.map(pos)

    def wheelEvent(self, event):
        if event.modifiers() == Qt.ControlModifier:
            # Zoom only when Ctrl key is pressed
            zoom_factor = 1.02  # Adjust the zoom factor as desired

            # Get the position of the wheel event in view coordinates
            view_pos = event.position()

            # Map the view position to the scene coordinates
            scene_pos = self.mapToScene(view_pos.toPoint())

            # Zoom in or out based on the wheel delta
            if event.angleDelta().y() > 0:
                self.scale(zoom_factor, zoom_factor)
            else:
                self.scale(1 / zoom_factor, 1 / zoom_factor)

            # Calculate the new position in the view after the zoom
            new_view_pos = self.mapFromScene(scene_pos)

            # Adjust the scrollbars to keep the scene position fixed
            self.horizontalScrollBar().setValue(self.horizontalScrollBar().value() + view_pos.x() - new_view_pos.x())
            self.verticalScrollBar().setValue(self.verticalScrollBar().value() + view_pos.y() - new_view_pos.y())
        else:
            # Let the base class handle the event
            super().wheelEvent(event)


class ResizableRectItem(QtWidgets.QGraphicsRectItem):
    """
    A QGraphicsItem that represents a rectangle which can be resized by dragging its corners.
    """
    handle_size = +8.0

    def __init__(self, rect=QtCore.QRectF()):
        """
        Initialize the rectangle item.
        Args:
            rect: The rectangle to be displayed.
        """
        super().__init__(rect)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable, True)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable, True)
        self.setAcceptHoverEvents(True)

        self.pen = QtGui.QPen(Qt.red)
        self.pen.setWidth(1)
        self.setPen(self.pen)

        self.drag_start = QtCore.QPointF()
        self.dragging = -1
        self._drag_drop_callback = None

    def set_drag_drop_callback(self, func) -> None:
        """ Set the callback function to be called when the rectangle is dropped

        Args:
            func: callback function
        """
        self._drag_drop_callback = func

    def mousePressEvent(self, event: QEvent) -> None:
        """ Handles mouse press events

        Args:
            event: an instance of QGraphicsSceneMouseEvent
        """
        handle = self.handle_at(event.pos())
        if event.button() == Qt.LeftButton and handle >= 0:
            self.dragging = handle
            self.drag_start = event.pos()
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event: QEvent) -> None:
        """ Handles mouse move events

        Args:
            event: an instance of QGraphicsSceneMouseEvent
        """
        if self.dragging >= 0:
            delta = event.pos() - self.drag_start
            rect = self.rect()
            if self.dragging == 0:   # top-left
                rect.setTopLeft(rect.topLeft() + delta)
            elif self.dragging == 1:  # top-right
                rect.setTopRight(rect.topRight() + delta)
            elif self.dragging == 2:  # bottom-right
                rect.setBottomRight(rect.bottomRight() + delta)
            elif self.dragging == 3:  # bottom-left
                rect.setBottomLeft(rect.bottomLeft() + delta)
            self.setRect(rect.normalized())
            self.drag_start = event.pos()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event: QEvent) -> None:
        """ Handles mouse release events

        Args:
            event: An instance of QGraphicsSceneMouseEvent
        """
        self.dragging = -1
        super().mouseReleaseEvent(event)
        if self._drag_drop_callback:
            self._drag_drop_callback()

    def hoverMoveEvent(self, event: QEvent) -> None:
        """ Handles hover move events

        Args:
            event: An instance of QGraphicsSceneHoverEvent
        """
        handle = self.handle_at(event.pos())
        if handle >= 0 or self.dragging >= 0:
            self.setCursor(Qt.SizeAllCursor)
        else:
            self.setCursor(Qt.ArrowCursor)

    # pylint: disable=W0613
    def hoverLeaveEvent(self, event: QEvent) -> None:
        """ Handles hover leave events

        Args:
            event: An instance of QGraphicsSceneHoverEvent
        """
        self.setCursor(Qt.ArrowCursor)

    def handle_at(self, point: QtCore.QPointF) -> int:
        """ Returns the index of the handle at the given point.

        Args:
            point: A point in the item's coordinate system

        Returns: The index of the handle at the given point, or -1 if no handle is at the point
        """
        for i, rect in enumerate(self.handles()):
            if rect.contains(point):
                return i
        return -1

    def handles(self) -> List[QtCore.QRectF]:
        """
        Returns a list of rectangles representing the handles for resizing.

        :return: A list of rectangles representing the handles for resizing
        """
        rect = self.rect()
        size = self.handle_size
        return [
            QtCore.QRectF(rect.left(), rect.top(), size, size),        # top-left
            QtCore.QRectF(rect.right() - size, rect.top(), size, size),   # top-right
            QtCore.QRectF(rect.right() - size, rect.bottom() - size, size, size),  # bottom-right
            QtCore.QRectF(rect.left(), rect.bottom() - size, size, size)  # bottom-left
        ]


class ImageSelectionWidget(QtWidgets.QWidget):
    """
    A widget for selecting a rectangular region in an image.
    """

    def __init__(self, project_settings: ProjectSettingsModel, parent=None):
        """
        Initialize the widget.

        Args:
            project_settings
            parent: The parent widget
        """
        super().__init__(parent)
        self.place_holder_pixmap = None
        self.current_frame = None
        self.layout = None
        self.pixmap = None
        self.graphics_view = None
        self.graphics_scene = None
        self.selection_rect = None
        self.project_settings = project_settings
        self.init_ui()

    def init_ui(self):
        """
        Set up the user interface of the widget.
        """
        self.layout = QtWidgets.QVBoxLayout(self)
        self.graphics_view = ImageSelectionGraphicsView(self)
        self.layout.addWidget(self.graphics_view)

        self.graphics_scene = QtWidgets.QGraphicsScene(self.graphics_view)
        self.graphics_view.setScene(self.graphics_scene)

        self.selection_rect = ResizableRectItem()
        self.place_holder_pixmap = QPixmap(ResourceLoader.open_vp_cal_logo()).scaled(500, 500, Qt.KeepAspectRatio)

        if not self.project_settings.current_wall \
                or not self.project_settings.current_wall.roi:
            roi = [0, 100, 0, 100]
        else:
            roi = self.project_settings.current_wall.roi

        self.selection_rect.setRect(
            roi[0],
            roi[2],
            roi[1] - roi[0],
            roi[3] - roi[2],
        )
        self.selection_rect.set_drag_drop_callback(self.store_roi)
        self.pixmap = self.graphics_scene.addPixmap(self.place_holder_pixmap)
        self.graphics_scene.addItem(self.selection_rect)
        self.clear()
        QApplication.processEvents()

    def current_frame_changed(self, frame: PixMapFrame) -> None:
        """ Update the displayed image when the frame changes

        Args:
            frame: The new frame we want to display
        """
        self.display_image(frame)

    def display_image(self, frame: PixMapFrame) -> None:
        """
        Load and display an image from the given path.

        :param frame: The frame we want to display
        """
        QApplication.processEvents()
        self.current_frame = frame
        if not self.selection_rect:
            self.selection_rect = ResizableRectItem()

        self.selection_rect.setPos(0, 0)

        if self.project_settings.current_wall.roi:
            self.selection_rect.setRect(

                self.project_settings.current_wall.roi[0],
                self.project_settings.current_wall.roi[2],

                self.project_settings.current_wall.roi[1] -
                self.project_settings.current_wall.roi[0],

                self.project_settings.current_wall.roi[3] -
                self.project_settings.current_wall.roi[2],
            )

        # Set The Current Frame & Ensure Its Position Is Top Left Corner
        self.pixmap.setPixmap(self.current_frame.pixmap)
        self.pixmap.setPos(0, 0)
        QApplication.processEvents()

    def clear(self) -> None:
        """ Clear the image from the view and set the placeholder image.
        """
        if self.pixmap:
            self.pixmap.setPixmap(self.place_holder_pixmap)
            scene_rect = self.graphics_scene.sceneRect()
            center_x = scene_rect.width() / 2
            center_y = scene_rect.height() / 2

            # Calculate pixmap top left position to be centered
            pixmap_width = self.pixmap.pixmap().width()
            pixmap_height = self.pixmap.pixmap().height()
            pixmap_x = center_x - pixmap_width / 2
            pixmap_y = center_y - pixmap_height / 2

            # We set the pixmap in the center of the scene
            self.pixmap.setPos(pixmap_x, pixmap_y)

    def get_selection_coordinates(self) -> Tuple[float, float, float, float]:
        """ Return the coordinates of the current selection, and stores the current selection position in the widget

        Returns: A tuple (top_left_x, top_left_y, bottom_right_x, bottom_right_y)

        """
        rect = self.selection_rect.rect()
        top_left = self.graphics_view.mapToSceneInverted((self.selection_rect.pos() + rect.topLeft()).toPoint())
        bottom_right = self.graphics_view.mapToSceneInverted((self.selection_rect.pos() + rect.bottomRight()).toPoint())
        return top_left.x(), top_left.y(), bottom_right.x(), bottom_right.y()

    def store_roi(self) -> None:
        """
        Store the ROI in the project model
        """
        self.graphics_view.resetTransform()
        coords = self.get_selection_coordinates()
        if self.project_settings.current_wall:
            self.project_settings.current_wall.roi = [
                int(coords[0]), int(coords[2]), int(coords[1]), int(coords[3])
            ]

    def contextMenuEvent(self, event: QtGui.QContextMenuEvent) -> None:
        """ Display the context menu when we right click on the widget and setup the menu

        Args:
            event: The context menu event
        """
        context_menu = QtWidgets.QMenu(self)  # Create a QMenu object

        # Create an action
        reset_roi = context_menu.addAction("Reset ROI")

        # Connect the action's triggered signal to your desired function
        reset_roi.triggered.connect(self.on_reset_roi)

        # Display the context menu
        context_menu.exec_(event.globalPos())

    def on_reset_roi(self) -> None:
        """ Reset the ROI to its default position and size when the right click menu is triggered.
            Only does anything if there is a current frame loaded and a current wall selected
        """
        if self.current_frame and self.project_settings.current_wall:
            self.project_settings.current_wall.roi = [
                0, 100, 0, 100
            ]
            self.display_image(self.current_frame)
