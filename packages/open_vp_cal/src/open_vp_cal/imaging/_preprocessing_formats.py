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

import open_vp_cal
from open_vp_cal.core.constants import InputSelectSources, VERSION, \
    PRE_PROCESSING_FORMAT_MAP, InputFormats, CameraColourSpace, LedWallSettingsKeys

REDLINE_CMD = "Redline"
ART_CMD = "art-cmd"
RAW_EXPORTER_CMD = "rawexporter"
FFMPEG_CMD = "ffmpeg"

_FORMAT_MAP = {
    InputSelectSources.RED:
    [
        {
            "commandName": REDLINE_CMD,
            "command_path_overrides": {
                "darwin": "/usr/local/bin/Redline",
                "win32": "C:\\Program Files\\REDCINE-X PRO 64-bit\\Redline.exe",
                "linux": "/usr/local/bin/Redline"
            },
            "formats": InputFormats.RED_FORMATS,
            "args": [("--i", "<FILEPATH_IN>"), ("--format", "2") ,("--exrACES", "1"), ("--useMeta", ""), ("--resizeX", "<RESOLUTION_X>"), ("--resizeY", "<RESOLUTION_Y>"), ("-gpuPlatform", "1"), ("-o", "<FILEPATH_OUT>")],
            LedWallSettingsKeys.INPUT_PLATE_GAMUT: CameraColourSpace.CS_ACES
        }
    ],

    InputSelectSources.ARRI:
    [
        {
            "commandName": ART_CMD,
            "command_path_overrides": {
                "darwin": "~/Downloads/art-cmd_0.3.0_macos_universal/bin/art-cmd",
                "win32": "C:\\ARRI\\bin\\art-cmd.exe",
                "linux": "~/Downloads/art-cmd_0.3.0_macos_universal/bin/art-cmd"
            },
            "formats": InputFormats.ARRI_FORMATS,
            "args": [("--mode", "process"), ("--input", "<FILEPATH_IN>"), ("--output", "<OUTPUT_FOLDER>/<OUTPUT_FILENAME>.%07d.exr"), ("--video-codec", "exr_uncompressed/f16"), ("--target-colorspace", "AP0/D60/linear"), ("--letterbox-size", "<RESOLUTION_X>x<RESOLUTION_Y>")],
            LedWallSettingsKeys.INPUT_PLATE_GAMUT: CameraColourSpace.CS_ACES

        }
    ],
    InputSelectSources.SONY:
    [
        {
            "commandName": RAW_EXPORTER_CMD,
            "command_path_overrides": {
                "darwin": "/Applications/RAW Viewer.app/Contents/MacOS/rawexporter",
                "win32": "C:\\Program Files\\Sony\\RAW Viewer\\rawexporter.exe",
                "linux": "/usr/local/bin/rawexporter"
            },
            "formats": InputFormats.SONY_FORMATS,
            "args": [("--input", "<FILEPATH_IN>"), ("-D", "<OUTPUT_FOLDER>"), ("-O", "<OUTPUT_FILENAME>"), ("-V", "dpx"), ("--bake", "INPUT"), ("--color", "SGAMUT3"), ("--tone", "SLOG3"), ("--width", "<RESOLUTION_X>"), ("--height", "<RESOLUTION_Y>")],
            LedWallSettingsKeys.INPUT_PLATE_GAMUT: "S-Log3 S-Gamut3"
        },
    ],
    InputSelectSources.MOV:
    [
        {
            "commandName": FFMPEG_CMD,
            "command_path_overrides": {
                "darwin": "/opt/homebrew/bin/ffmpeg",
                "win32": "C:\\FFMpeg\\ffmpeg.exe",
                "linux": "/usr/local/bin/ffmpeg"
            },
            "formats": InputFormats.MOV_FORMATS,
            "args": [("-i", "<FILEPATH_IN>"), ("-vf", "scale=<RESOLUTION_X>:<RESOLUTION_Y>"), ("", "<OUTPUT_FOLDER>/<OUTPUT_FILENAME>.%07d.dpx")],
            LedWallSettingsKeys.INPUT_PLATE_GAMUT: CameraColourSpace.CS_ACES
        }
    ]
}

PREPROCESSING_CONFIG = {
    VERSION: open_vp_cal.__version__,
    PRE_PROCESSING_FORMAT_MAP: _FORMAT_MAP
}
