from open_vp_cal.core.constants import FileFormats, InputSelectSources

REDLINE_CMD = "Redline"
ARC_CMD = "art-cmd"
RAW_EXPORTER_CMD = "rawexporter"
FFMPEG_CMD = "ffmpeg"

RED_FORMATS = (FileFormats.FF_R3D,)
ARRI_FORMATS = (FileFormats.FF_ARX, FileFormats.FF_ARI, FileFormats.FF_MXF)
SONY_FORMATS = (FileFormats.FF_MXF,)
MOV_FORMATS = (FileFormats.FF_MOV,)

FORMAT_MAP = {
    InputSelectSources.RED:
    {
        RED_FORMATS: {
            "commandName": REDLINE_CMD,
            "args": [("--i", "<FILEPATH_IN>"), ("--format", "2"), ("--useMeta", ""), ("--resizeX", "<RESOLUTION_X>"), ("--resizeY", "<RESOLUTION_Y>"), ("-gpuPlatform", "1"), ("-o", "<FILEPATH_OUT>")]
        },
    },
    InputSelectSources.ARRI:
    {
        ARRI_FORMATS: {
                "commandName": ARC_CMD,
                "args": [("process", ""), ("--input", "<FILEPATH_IN>"), ("--output", "<OUTPUT_FOLDER>/output.%07d.exr"), ("--video-codec", "exr_uncompressed/f16"), ("--target-colorspace", "AP0/D60/linear"), ("--letterbox-size", "<RESOLUTION_X>x<RESOLUTION_Y>")]
        },
    },
    InputSelectSources.SONY:
    {
        SONY_FORMATS: {
            "commandName": RAW_EXPORTER_CMD,
            "args": [("--input", "<FILEPATH_IN>"), ("-D", "<OUTPUT_FOLDER>"), ("-O", "<OUTPUT_FILENAME>"), ("-V", "exr"), ("--bake", "ACES_LINEAR"), ("--width", "<RESOLUTION_X>"), ("--height", "<RESOLUTION_Y>")]
        },
    },
    InputSelectSources.MOV:
    {
        MOV_FORMATS: {
            "commandName": FFMPEG_CMD,
            "args": [("-i", "<FILEPATH_IN>"), ("-vf", "scale=<RESOLUTION_X>:<RESOLUTION_Y>"), ("", "<OUTPUT_FOLDER>/output.%07d.dpx")]
        }
    }
}
