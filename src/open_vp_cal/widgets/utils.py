"""
A module to hold ui-specific utility functions
"""
from PySide6.QtWidgets import QFileDialog, QWidget


def select_folder() -> str:
    """
    Opens a QFileDialog to select a folder.

    Returns:
        str: The path to the selected folder. Empty string if no folder was selected.
    """
    dialog = QFileDialog()
    dialog.setFileMode(QFileDialog.Directory)  # Set mode to select directories
    dialog.setOption(QFileDialog.ShowDirsOnly, True)  # Show only directories, no files

    if dialog.exec_() == QFileDialog.Accepted:
        # User clicked 'OK', so get the selected directories
        selected_directories = dialog.selectedFiles()

        if selected_directories:
            # Return the first selected directory
            return selected_directories[0]

    # If we get here, no folder was selected
    return ""


class LockableWidget(QWidget):
    """
    A widget that can be locked to prevent user interaction.
    """

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.active_state = True
        self.master_layout = None

    def _set_active_state(self, value: bool):
        """ Sets the active state of all the UI components

        Args:
            value: The value to set the active state to
        """
        for i in range(self.master_layout.count()):
            widget = self.master_layout.itemAt(i).widget()
            if widget is not None:
                widget.setDisabled(value)

    def disable(self):
        """
        Disables all the UI components
        """
        if self.active_state:
            self.active_state = False
            self._set_active_state(True)

    def enable(self):
        """
        Enables all the UI components
        """
        if not self.active_state:
            self.active_state = True
            self._set_active_state(False)
