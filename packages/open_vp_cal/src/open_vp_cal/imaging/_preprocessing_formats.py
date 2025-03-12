from open_vp_cal.core.constants import FileFormats
from open_vp_cal.core.resource_loader import ResourceLoader



REDLINE_CMD = "Redline"
ARC_CMD = "art-cmd"
RAW_EXPORTER_CMD = "rawexporter"
FFMPEG_CMD = "ffmpeg"

RED_FORMATS = (FileFormats.FF_R3D,)
ARRI_FORMATS = (".arx", ".ari", FileFormats.FF_MXF)
SONY_FORMATS = (FileFormats.FF_MXF,)
RANDOM_FORMATS = (FileFormats.FF_MOV,)

FORMAT_MAP = {
    RED_FORMATS: {
        "commandName": REDLINE_CMD,
        "args": [("--i", "<FILEPATH_IN>"), ("--format", "2"), ("--useMeta", ""), ("--resizeX", "<RESOLUTION_X>"), ("--resizeY", "<RESOLUTION_Y>"), ("-gpuPlatform", "1"), ("-o", "<FILEPATH_OUT>")]
    },
    # ARRI_FORMATS: {
    #     "commandName": ARC_CMD,
    #     "args": [("process", ""), ("--input", "<FILEPATH_IN>"), ("--output", "<OUTPUT_FOLDER>/output.%07d.exr"), ("--video-codec", "exr_uncompressed/f16"), ("--target-colorspace", "AP0/D60/linear"), ("--letterbox-size", "<RESOLUTION_X>x<RESOLUTION_Y>")]
    # },
    SONY_FORMATS: {
        "commandName": RAW_EXPORTER_CMD,
        "args": [("--input", "<FILEPATH_IN>"), ("-D", "<OUTPUT_FOLDER>"), ("-O", "<OUTPUT_FILENAME>"), ("-V", "exr"), ("--bake", "ACES_LINEAR"), ("--width", "<RESOLUTION_X>"), ("--height", "<RESOLUTION_Y>")]
    },
    RANDOM_FORMATS: {
        "commandName": FFMPEG_CMD,
        "args": [("-i", "<FILEPATH_IN>"), ("-vf", "scale=<RESOLUTION_X>:<RESOLUTION_Y>"), ("", "<OUTPUT_FOLDER>/output.%07d.dpx")]
    }
}

# art-cmd process --input /Users/adamdavis/Downloads/F004C001_190925_MN99.mxf --output /tmp --video-codec  --target-colorspace AP0/D60/linear --letterbox-size
