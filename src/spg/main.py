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

Command line for creating the spg and generating the patterns
"""
import argparse
import json
import os

from spg import query as _query
from spg.spg import PatternGenerator


def validate_file(f):
    if not os.path.exists(f):
        raise argparse.ArgumentTypeError("File does not exist {0} ".format(f))
    return f


def run():
    parser = argparse.ArgumentParser(description="Synthetic Pattern Generator")
    parser.add_argument("-p", "--panels", dest="panels_config", type=validate_file,
                        help="the config file for all the panel data", metavar="FILE")

    parser.add_argument("-w", "--walls", dest="walls_config", type=validate_file,
                        help="the config file for all led wall data", metavar="FILE")

    parser.add_argument("-r", "--raster", dest="raster_config", type=validate_file,
                        help="the config file for all processor raster map data", metavar="FILE")

    parser.add_argument("-pr", "--project", dest="project_config", type=validate_file,
                        help="the config file for the project settings", metavar="FILE")

    parser.add_argument("-pt", "--pattern", dest="pattern_config", type=validate_file,
                        help="the config file for the pattern settings", metavar="FILE")
    args = parser.parse_args()

    if not args.panels_config:
        args.panels_config = _query.get_panels_config()

    if not args.walls_config:
        args.walls_config = _query.get_walls_config()

    if not args.raster_config:
        args.raster_config = _query.get_raster_config()

    if not args.project_config:
        args.project_config = _query.get_project_settings()

    if not args.pattern_config:
        args.pattern_config = _query.get_pattern_settings()

    run_spg_pattern_generator(
        args.panels_config, args.walls_config,
        args.raster_config, args.project_config, args.pattern_config
    )


def run_spg_pattern_generator(
        panels_config_file, walls_config_file, raster_config_file,
        project_config_file, pattern_config_file):

    if not os.path.exists(panels_config_file):
        raise ValueError("Panel config file does not exist {0}".format(panels_config_file))

    if not os.path.exists(walls_config_file):
        raise ValueError("Wall config file does not exist {0}".format(walls_config_file))

    if not os.path.exists(raster_config_file):
        raise ValueError("Raster config file does not exist {0}".format(raster_config_file))

    if not os.path.exists(project_config_file):
        raise ValueError("Project config file does not exist {0}".format(project_config_file))

    if not os.path.exists(pattern_config_file):
        raise ValueError("Pattern config file does not exist {0}".format(pattern_config_file))

    with open(panels_config_file, "r", encoding="utf-8") as handle:
        panels_config = json.load(handle)

    with open(walls_config_file, "r", encoding="utf-8") as handle:
        walls_config = json.load(handle)

    with open(raster_config_file, "r", encoding="utf-8") as handle:
        raster_config = json.load(handle)

    with open(project_config_file, "r", encoding="utf-8") as handle:
        project_config = json.load(handle)

    with open(pattern_config_file, "r", encoding="utf-8") as handle:
        pattern_config = json.load(handle)

    spg = PatternGenerator(
        panels_config, walls_config,
        raster_config, project_config, pattern_config)

    for progress in spg.generate_patterns_and_stitch_rasters():
        print(progress)


if __name__ == "__main__":
    run()
