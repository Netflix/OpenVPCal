"""
The module defines a splash screen widget which opens when the application launches
"""
from PySide6.QtGui import QPainter
from PySide6.QtWidgets import QSplashScreen
from PySide6.QtCore import Qt


class SplashScreen(QSplashScreen):
    """
    Class: SplashScreen
    Creates a splash screen widget to display when the application launches
    """

    def __init__(self, pixmap, version_info, *args, **kwargs):
        """ Initialize the splash screen

        Args:
            pixmap: The pixmap to display on the splash screen
            version_info: The version info of the product
            *args: Variable length argument list
            **kwargs: Arbitrary keyword arguments
        """
        super().__init__(pixmap, *args, **kwargs)
        self.version_info = version_info

    def drawContents(self, painter: QPainter) -> None:
        """ Draw the contents of the splash screen

        Args:
            painter: The painter object to draw with

        """
        painter.drawText(self.rect().adjusted(0, 20, 0, 0), Qt.AlignBottom, self.version_info)
