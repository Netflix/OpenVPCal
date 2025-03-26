import json
import shutil
import subprocess
import sys

from open_vp_cal.core.structures import OpenVPCalException
from packaging import version

from pathlib import Path

import open_vp_cal
from open_vp_cal.core.constants import ProjectFolders, PRE_PROCESSING_FORMAT_MAP, \
    VERSION, LedWallSettingsKeys
from open_vp_cal.core.resource_loader import ResourceLoader
from open_vp_cal.imaging._preprocessing_formats import PREPROCESSING_CONFIG
from open_vp_cal.project_settings import ProjectSettings


def run_command(command_name, command_dict):
    """
    Constructs the command from the given dictionary and executes it using subprocess.

    Blocks until the process is complete and returns the exit status.

    Parameters:
    - command_dict (dict): A dictionary containing "commandName" and "args".

    Returns:
    - int: The exit code of the command (0 for success, non-zero for failure).
    """
    args = command_dict["args"]

    # Flatten the args list into a single list
    command_list = [command_name] + [item for pair in args for item in pair if item]

    try:
        print(f"Running command: {' '.join(command_list)}")

        # Run the command, block until completion, and capture output
        result = subprocess.run(command_list, stdout=subprocess.PIPE,
                                stderr=subprocess.PIPE, text=True)

        # Print standard output and error
        if result.stdout:
            print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")

        # Check exit code
        if result.returncode == 0:
            print(f"Command '{command_name}' executed successfully.")
        else:
            print(
                f"Command '{command_name}' failed with exit code {result.returncode}.")

        return result.returncode
    except Exception as e:
        print(f"Unexpected error while running command '{command_name}': {e}")
        return -1

def replace_command_args(command_dict, replacement_dict):
    """
    Replaces placeholders in the command args with actual values from the replacement_dict,
    ensuring all occurrences are replaced while preserving the original data type.

    Parameters:
    - command_dict (dict): A dictionary containing "commandName" and "args".
    - replacement_dict (dict): A dictionary of placeholders and their corresponding values.

    Returns:
    - dict: A new command dictionary with updated arguments, maintaining the correct data types.
    """
    def replace_placeholders(value):
        """Replaces all placeholders in a string or preserves non-string values."""
        if isinstance(value, str):
            for placeholder, replacement in replacement_dict.items():
                value = value.replace(placeholder, replacement)  # Replace all occurrences
        return value  # Preserve original data type if not a string

    updated_args = [(key, replace_placeholders(value)) for key, value in command_dict["args"]]

    return {
        "commandName": command_dict["commandName"],
        "args": updated_args
    }

def check_command_on_path(command_name: str):
    if shutil.which(command_name):
        return True
    return False

def get_format(pre_process_config, input_source, extension):
    format_map = pre_process_config.get(PRE_PROCESSING_FORMAT_MAP, None)
    if not format_map:
        return None

    input_format_maps = format_map.get(input_source, None)
    if not input_format_maps:
        return None

    for format_data in input_format_maps:
        formats = format_data.get("formats", [])
        if extension in formats:
            return format_data
    return None

def convert_raw_to_plate(pre_process_config, input_source, input_file, output_file, resolution_x=1920, resolution_y=1080):
    input_file = Path(input_file)
    if not input_file.exists():
        raise FileNotFoundError(f"Input file/folder {input_file} does not exist.")

    output_file = Path(output_file)
    output_folder = output_file.parent / output_file.stem
    output_folder.mkdir(parents=True, exist_ok=True)

    format_details = get_format(pre_process_config, input_source, input_file.suffix)
    if not format_details:
        raise OpenVPCalException(f"No format details found for extensions '{input_file.suffix}'")

    command_name = format_details.get("commandName", None)
    if not command_name:
        raise OpenVPCalException(f"No commandName found for format '{input_file.suffix}'")

    result = check_command_on_path(command_name)
    if not result:
        command_name = format_details.get("command_path_overrides", {}).get(sys.platform, "")
        if not command_name:
            raise OpenVPCalException(f"Command {command_name} not installed on system or on $PATH")

        if not Path(command_name).exists():
            raise OpenVPCalException(f"Command {command_name} not installed on system or on $PATH")

    filename = f"{input_file.stem}_"
    output_file_name = output_folder / filename
    replacement_dict = {
        "<FILEPATH_IN>": input_file.as_posix(),
        "<FILEPATH_OUT>": output_file_name.as_posix(),
        "<RESOLUTION_X>": str(resolution_x),
        "<RESOLUTION_Y>": str(resolution_y),
        "<OUTPUT_FILENAME>": filename.replace(".", "_"),
        "<OUTPUT_FOLDER>": output_folder.as_posix()
    }
    format_details_populated = replace_command_args(format_details, replacement_dict)
    run_command(command_name, format_details_populated)
    return output_folder, format_details[LedWallSettingsKeys.INPUT_PLATE_GAMUT]


class PreProcessConvert:
    def __init__(self, project_settings : ProjectSettings):
        self.project_settings = project_settings
        self.pre_process_config = {}
        self.pre_process_config_name = "pre_process_config.json"
        prefs = ResourceLoader.prefs_dir()
        self.pre_process_config_file = Path(prefs) / self.pre_process_config_name
        self._load_and_refresh_config()

    def _load_and_refresh_config(self):
        generate_new = False

        # No config file then generate
        if not self.pre_process_config_file.exists():
            generate_new = True
        else:
            # Tru and load the config if this fails generate a new one
            with self.pre_process_config_file.open("r") as f:
                try:
                    self.pre_process_config = json.load(f)
                except json.decoder.JSONDecodeError:
                    generate_new = True


        if self.pre_process_config:
            current_version = version.parse(open_vp_cal.__version__)
            config_version = version.parse(self.pre_process_config.get(VERSION))
            if current_version > config_version:
                generate_new = True

        # Check Versions
        if generate_new:
            self.pre_process_config = PREPROCESSING_CONFIG
            self.save_pre_process_config()

    def convert_raw_to_aces(self, input_source, input_file):
        output = Path(self.project_settings.output_folder) / ProjectFolders.PLATES
        output = output /Path(input_file).name
        output_folder, plate_gamut = convert_raw_to_plate(self.pre_process_config, input_source, input_file, output)
        return output_folder, plate_gamut

    def save_pre_process_config(self):
        with self.pre_process_config_file.open("w") as f:
            json.dump(self.pre_process_config, f, indent=4)

