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

The module containing the main entry point for the application.
This could be the opening of the UI or the utilisation of the CLI. This module also contains the exception handler for
the application which logs all errors to a file in the user's home directory.
"""
import argparse
from datetime import datetime
import json
import os
import sys
import time
import traceback

import open_vp_cal
from open_vp_cal.application_base import OpenVPCalBase
from open_vp_cal.core import constants
from open_vp_cal.core.resource_loader import ResourceLoader
from open_vp_cal.framework.utils import generate_patterns_for_led_walls, \
    generate_spg_patterns_for_led_walls
from open_vp_cal.led_wall_settings import LedWallSettings
from open_vp_cal.project_settings import ProjectSettings


def open_ui() -> None:
    """ Opens the MainWindow as QApplication after the splash screen loads
    """
    from PySide6.QtWidgets import QMessageBox
    from PySide6 import QtWidgets
    from PySide6.QtGui import QPixmap

    from open_vp_cal.widgets.splash_screen import SplashScreen
    from open_vp_cal.widgets.main_window import MainWindow

    def handle_exception(exc_type: type, exc_value: Exception, exc_traceback: traceback) -> None:
        """ Handles any unhandled exceptions by logging them to a file in the user's home directory and displaying a
            QMessageBox to the user.

        Args:
            exc_type: The type of exception
            exc_value: The value of the exception
            exc_traceback: The traceback of the exception
        """
        # Format current date and time as a string
        current_time = datetime.now().strftime("%Y%m%d_%H%M%S")

        # Get the home directory and form the full filename
        log_dir = ResourceLoader.log_dir()
        filename = log_dir / f"OpenVPCal_{current_time}.log"

        # Open the file in appended mode and write the stack trace
        with filename.open("a") as handle:
            traceback.print_exception(exc_type, exc_value, exc_traceback, file=handle)

        # Display the error message in a QMessageBox
        QMessageBox.critical(None, "An unhandled Exception Occurred",
                             "An unhandled Exception Occurred\n" + str(exc_value),
                             QMessageBox.Ok)

        # Then call the default handler if you want
        sys.__excepthook__(exc_type, exc_value, exc_traceback)

    sys.excepthook = handle_exception
    app = QtWidgets.QApplication(sys.argv)
    app.setStyle("Fusion")

    pixmap = QPixmap(ResourceLoader.open_vp_cal_logo_full())

    # Define product name, version info, and credits
    product_name = 'OpenVPCal'
    version_info = open_vp_cal.__version__

    # Create and show the splash screen
    splash = SplashScreen(pixmap, version_info)
    splash.show()

    # Simulate a delay for loading the main application
    time.sleep(4)

    # After loading is done, close the splash screen
    splash.close()

    window = MainWindow(f"{product_name} v{version_info}")
    window.show()
    window.load_project_layout()
    sys.exit(app.exec())


def validate_file_path(file_path: str) -> str:
    """ Validates that the file path exists.

    Args:
        file_path: The file path to validate

    Returns: The file path if it exists

    """
    if not os.path.exists(file_path):
        raise argparse.ArgumentTypeError(f"{file_path} does not exist.")
    return file_path


def validate_folder_path(folder_path: str) -> str:
    """ Validates that the folder path exists and is a directory.

    Args:
        folder_path: The folder path to validate

    Returns: The folder path if it exists and is a directory

    """
    if not os.path.isdir(folder_path):
        raise argparse.ArgumentTypeError(f"{folder_path} is not a valid directory.")
    return folder_path


def validate_is_file(file_path: str) -> str:
    """ Validates that the file path exists and is a file.

    Args:
        file_path: The file path to validate
    """
    if not os.path.exists(file_path):
        raise argparse.ArgumentTypeError(f"{file_path} does not exist.")

    if not os.path.isfile(file_path):
        raise argparse.ArgumentTypeError(f"{file_path} is not a valid file.")
    return file_path


def validate_project_settings(file_path: str) -> str:
    """ Validates that the project settings file path exists and is a valid JSON file.

    Args:
        file_path: The file path to validate

    Returns: The file path if it exists and is a valid JSON file

    """
    try:
        with open(file_path, 'r', encoding="utf-8") as handle:
            json.load(handle)
    except json.JSONDecodeError as exc:
        raise exc
    return file_path

def generate_spg_patterns(project_settings_file_path: str, output_folder: str) -> None:
    """ Generates then spg round trip test patterns for the given project settings file and output folder.

        Args:
            project_settings_file_path: the file path to the project settings file we want to generate patterns for
            output_folder: the output folder to save the patterns to

        """
    project_settings = ProjectSettings.from_json(project_settings_file_path)
    project_settings.output_folder = output_folder
    generate_spg_patterns_for_led_walls(project_settings, project_settings.led_walls)

def generate_patterns(project_settings_file_path: str, output_folder: str) -> str:
    """ Generates then calibration patterns for the given project settings file and output folder.

    Args:
        project_settings_file_path: the file path to the project settings file we want to generate patterns for
        output_folder: the output folder to save the patterns to

    Returns: The file path to the ocio config which is generated as part of the process

    """
    project_settings = ProjectSettings.from_json(project_settings_file_path)
    project_settings.output_folder = output_folder
    return generate_patterns_for_led_walls(project_settings, project_settings.led_walls)

def add_error_to_log(error_log: str, error: str) -> None:
    """ Adds an error to the error log file.

    Args:
        error_log: The error log file path
        error: The error to add to the log file
    """
    if not error_log:
        return

    data = {"errors": []}

    # Ensure the file exists before attempting to read
    if os.path.exists(error_log):
        with open(error_log, 'r') as handle:
            try:
                data = json.load(handle)
            except json.JSONDecodeError:
                pass  # Ignore decoding errors and use default empty structure

    data["errors"].append(error)

    # Open the file in write mode to properly save the updated data
    with open(error_log, 'w') as handle:
        json.dump(data, handle, indent=4)

def run_cli(
        project_settings_file_path: str,
        output_folder: str,
        ocio_config_path: str = None, force=False, error_log: str = None ) -> dict[str, LedWallSettings]:
    """ Runs the application in CLI mode to process the given project settings file.

    Args:
        project_settings_file_path: The project settings file path
        output_folder: The output folder path
        ocio_config_path: The OCIO config path
        force: Whether to force the processing to continue even if there are warnings and errors, highly discouraged and
            primarily for testing purposes
        error_log: The error log file path to store errors in as a json file

    Returns: The list of ProcessingResults

    """
    project_settings = ProjectSettings.from_json(project_settings_file_path)
    project_settings.output_folder = output_folder
    open_vp_cal_base = OpenVPCalBase()

    if ocio_config_path:
        project_settings.ocio_config_path = ocio_config_path

    # Load all the led walls and load the sequences
    for led_wall in project_settings.led_walls:
        if not led_wall.input_sequence_folder:
            output = f"Input sequence folder not set for '{led_wall.name}'"
            add_error_to_log(error_log, output)
            raise IOError(output)
        if not os.path.exists(led_wall.input_sequence_folder):
            output = f"Input sequence folder '{led_wall.input_sequence_folder}' does not exist"
            add_error_to_log(error_log, output)
            raise IOError(output)
        led_wall.sequence_loader.load_sequence(led_wall.input_sequence_folder)

        if not led_wall.roi:
            _, auto_roi_results = open_vp_cal_base.run_auto_detect(led_wall)
            if not auto_roi_results or not auto_roi_results.is_valid:
                output = "Auto ROI detection failed."
                add_error_to_log(error_log, output)
                raise ValueError(output)

        led_wall.sequence_loader.set_current_frame(led_wall.sequence_loader.start_frame)

    # Now we have everything lets sort the led walls so they are in the correct order
    status = open_vp_cal_base.analyse(project_settings.led_walls)
    if not status:
        error_messages = "\n".join(open_vp_cal_base.error_messages())
        warning_messages = "\n".join(open_vp_cal_base.warning_messages())
        output = f"Analysis Failed\nWarning Messages:\n{warning_messages}\nError Messages:\n{error_messages}\n"
        add_error_to_log(error_log, output)
        if not force:
            raise ValueError(output)

    status = open_vp_cal_base.post_analysis_validations(project_settings.led_walls)
    if not status:
        error_messages = "\n".join(open_vp_cal_base.error_messages())
        warning_messages = "\n".join(open_vp_cal_base.warning_messages())
        output = f"Analysis Validation Failed\nWarning Messages:\n{warning_messages}\nError Messages:\n{error_messages}\n"
        add_error_to_log(error_log, output)
        if not force:
            raise ValueError(output)

    status = open_vp_cal_base.calibrate(project_settings.led_walls)
    if not status:
        error_messages = "\n".join(open_vp_cal_base.error_messages())
        warning_messages = "\n".join(open_vp_cal_base.warning_messages())
        output = f"Calibrate Failed\nWarning Messages:\n{warning_messages}\nError Messages:\n{error_messages}\n"
        add_error_to_log(error_log, output)
        if not force:
            raise ValueError(output)

    status, led_walls = open_vp_cal_base.export(project_settings, project_settings.led_walls)
    if not status:
        error_messages = "\n".join(open_vp_cal_base.error_messages())
        warning_messages = "\n".join(open_vp_cal_base.warning_messages())
        output = f"Export Failed\nWarning Messages:\n{warning_messages}\nError Messages:\n{error_messages}\n"
        add_error_to_log(error_log, output)
        if not force:
            raise ValueError(output)

    return {led_wall.name: led_wall for led_wall in led_walls}


def main() -> None:
    """ Main function to run the application which parses the command line arguments and runs the application.

    Returns:

    """
    args = parse_args()
    run_args(args)


def run_args(args: argparse.Namespace) -> None:
    """ Runs the application with the given command line arguments.

    Args:
        args: The command line arguments
    """
    if args.ui:
        open_ui()
    else:

        if args.generate_patterns:
            generate_patterns(args.project_settings, args.output_folder)
        if args.generate_spg_patterns:
            generate_spg_patterns(args.project_settings, args.output_folder)

        if not args.generate_patterns and not args.generate_spg_patterns:
            run_cli(
                args.project_settings,
                args.output_folder,
                args.ocio_config_path,
                force=args.ignore_errors,
                error_log=args.error_log
            )


def str2bool(v: str) -> bool:
    """ Converts a string to a bool value

    Args:
        v: The value to convert

    Returns: True if the value can be converted to a bool, False otherwise

    """
    if isinstance(v, bool):
        return v
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    if v.lower() in ('no', 'false', 'f', '0'):
        return False

    raise argparse.ArgumentTypeError('Boolean value expected.')


def parse_args() -> argparse.Namespace:
    """ Parses the command line arguments and returns the parsed arguments.

    Returns: The parsed arguments

    """
    parser = argparse.ArgumentParser(description='Command line arguments')
    parser.add_argument('--ui', type=str2bool, default=True, help='UI flag')
    parser.add_argument('--generate_patterns', type=str2bool, default=False,
                        help='CLI flag to generate the calibration patterns for the given project settings')
    parser.add_argument('--generate_spg_patterns', type=str2bool, default=False,
                        help='CLI flag to generate the spg roundtrip patterns for the given project settings')
    parser.add_argument('--project_settings', type=validate_project_settings,
                        required=False, help='Path to project settings JSON file')
    parser.add_argument('--output_folder', type=validate_folder_path,
                        required=False, help='Path to output folder')
    parser.add_argument('--ocio_config_path', type=validate_file_path,
                        required=False, help='Path to OCIO config file')
    parser.add_argument('--ignore_errors', type=str2bool, default=False,
                        help='CLI flag to ignore any errors produced during the calibration process and logging them in the provided error log file')
    parser.add_argument('--error_log', required=False, help='A file path to store any errors in a json file, the file is created if it does not already exist')
    args = parser.parse_args(sys.argv[1:])

    if not args.ui:
        if args.project_settings is None:
            parser.error("--project_settings must be set when --ui is False.")
    return args


if __name__ == "__main__":
    main()
