"""
Module defines a simple view to allow us to control execution flow; this consists of a simple widget with 3 buttons,
however, could become much more advanced in the future
"""
from PySide6.QtWidgets import QWidget, QPushButton, QHBoxLayout


class ExecutionView(QWidget):
    """
    Class: ExecutionView
    Creates a simple widget with 3 buttons to allow us to control execution flow
    """
    def __init__(self):
        super().__init__()
        self.export_button = None
        self.calibrate_button = None
        self.analyse_button = None
        self.init_ui()

    def init_ui(self) -> None:
        """ Initialize the UI and widgets
        """
        self.setLayout(QHBoxLayout())

        self.analyse_button = QPushButton("Analyse")
        self.calibrate_button = QPushButton("Calibrate")
        self.export_button = QPushButton("Export")

        self.layout().addWidget(self.analyse_button)
        self.layout().addWidget(self.calibrate_button)
        self.layout().addWidget(self.export_button)
