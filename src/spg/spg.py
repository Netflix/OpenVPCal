""" The main interface for the SPG that a third-party client would interface with.
Handles the dispatching of the pattern generation and raster map stitching from the various configs

"""
import math
import os
import shutil

from stageassets.ledPanel import LEDPanel as _LEDPanel
from stageassets.ledWall import LEDWall as _LEDWall
from stageassets.rasterMap import RasterMap as _RasterMap

from spg import PatternGenerators as _PatternGenerators
from spg.projectSettings import ProjectSettings as _ProjectSettings
from spg.utils import constants as _constants
from spg.utils import imageUtils as _imageUtils
from spg.utils.imageUtils import oiio
from spg.utils.threadingUtils import ThreadedFunction as _ThreadedFunction


class PatternGenerator(object):
    """ The main interface for executing and dispatching of the pattern generation

    """
    def __init__(self, panels_config, walls_config, raster_config, project_settings_config, pattern_settings_config):
        """
        :param panels_config: dict of data representing all the panels from the database
        :param walls_config: dict of data representing the led walls on the stage
        :param raster_config: dict of data representing the raster maps and how the walls are arranged out on the
            processors
        :param project_settings_config: dict of data representing global settings for the project such as frame rate
        :param pattern_settings_config: dict of data representing the patterns we want to generate and their settings
        """
        self._panels_config = panels_config
        self._walls_config = walls_config
        self._raster_config = raster_config
        self._project_settings_config = project_settings_config
        self._pattern_settings_config = pattern_settings_config

        self.panels = {}
        self.walls = {}
        self.rasters = {}
        self.project_settings = None

        self.load_plugins()
        self.initialize()

        self.status = "Initializing"
        self.num_tasks = self.calculate_num_tasks()
        self.completed_tasks = 0
        self.per_wall_results = {}

    def calculate_num_tasks(self):
        """ Calculate the number of tasks we have to process

        :return: the number of tasks which need to be performed
        """
        return len(self._pattern_settings_config) + len(self.rasters.keys())

    def progress(self):
        """ Reports the current status and the percentage of the tasks completed

        :return: returns a tuple with the status and percentage of progress
        """
        return self.status, (self.completed_tasks/self.num_tasks) * 100.0

    @staticmethod
    def load_plugins():
        """ Looks for any pattern generator plugins which exist on the PYTHONPATH and registers each pattern generator
        into the SPG
        """
        _PatternGenerators.load_plugins()

    def initialize(self):
        """ Loads and converts raw data dicts which have been loaded or provided as json data into
            python objects so they can be operated on
        """
        self.project_settings = _ProjectSettings.from_json(self._project_settings_config)

        for panel_data in self._panels_config:
            self.panels[panel_data["name"]] = _LEDPanel.from_json(panel_data)

        for wall_data in self._walls_config:
            led_wall_name = wall_data["name"]
            self.walls[led_wall_name] = _LEDWall.from_json(wall_data)
            self.walls[led_wall_name].panel = self.panels[self.walls[led_wall_name].panel_name]

        for raster_data in self._raster_config:
            self.rasters[raster_data["name"]] = _RasterMap.from_json(raster_data)

    def generate_output_dir(self):
        """ Creates the root output directory as defined in the project settings. If the folder exists it is
        removed along with its contents to ensure a clean slate
        """
        if os.path.exists(self.project_settings.output_folder):
            shutil.rmtree(self.project_settings.output_folder)

        os.makedirs(self.project_settings.output_folder)

    def generate_patterns_and_stitch_rasters(self):
        for progress in self.generate_patterns():
            yield progress

        # Pass all the results for all the patterns to be processed into the correct raster maps
        if not self.per_wall_results:
            return

        for progress in self.add_pattens_to_raster(self.per_wall_results):
            yield progress

    def generate_patterns(self):
        """ The method which loads the required pattern generators and executes them.
        In future this could be extended to allow us to dispatch this onto multiple machines or cloud instances

        """
        # Create & clean the output directory
        self.generate_output_dir()

        # For each of the patterns specified in the pattern config
        for pattern_settings in self._pattern_settings_config:
            # Get the generator class
            try:
                generator_class = _PatternGenerators.get_pattern(pattern_settings["pattern_type"])
            except KeyError:
                print("Pattern Not Registered: " + pattern_settings["pattern_type"])
                continue

            self.status = "Generating Pattern: " + pattern_settings["name"]
            yield self.progress()
            # Create an instance of the generator from the serialized settings
            generator = generator_class.from_json(self, pattern_settings)

            # Execute the pattern generator and store the results
            # Example: results[led_wall_name][frame_num] = full_file_path
            self.per_wall_results[generator] = generator.execute()

            self.completed_tasks += 1

        return self.per_wall_results

    def add_pattens_to_raster(self, per_wall_results):
        """ Takes all the results from the pattern generators, and processes them into the valid raster
        maps for each of the processors

        :param per_wall_results: dict of results data from generate patterns method
        """
        generator_changes_per_frame_threads = []
        generator_threads = []
        replicator_threads = []
        results = {}
        count = 0
        for raster_name, raster_map in self.rasters.items():
            self.status = "Generating Raster: " + raster_name
            yield self.progress()
            results[raster_name] = {}
            base_path = self.get_raster_base_path(raster_name)

            if not os.path.exists(base_path):
                os.makedirs(base_path)

            start_frame_offset = self.project_settings.sequence_start_frame
            for pattern_generator, pattern_results in per_wall_results.items():
                first_pattern_frame = True
                first_pattern_sequence_frame = 0
                for frame in range(int(pattern_generator.sequence_length * self.project_settings.frame_rate)):
                    full_sequence_frame_num = start_frame_offset

                    kwargs = {
                        "full_sequence_frame_num": full_sequence_frame_num,
                        "raster_map": raster_map,
                        "pattern_results": pattern_results
                    }

                    # If we are the first frame of a pattern we stitch it
                    # If we are also a none fixed pattern we stitch it (ie every frame)
                    generator_changes_per_frame = pattern_generator.method != _constants.GM_FIXED
                    if first_pattern_frame or generator_changes_per_frame:
                        # We create a new thread which executes our generator, which we start and keep track of
                        first_pattern_sequence_frame = full_sequence_frame_num
                        thread = _ThreadedFunction(self.stitch_raster_frame, frame, kwargs, results)
                        thread.start()
                        if generator_changes_per_frame:
                            generator_changes_per_frame_threads.append(thread)
                        else:
                            generator_threads.append(thread)
                    else:
                        # If we are not the first frame and not a fixed pattern we replicate the first frame
                        kwargs["first_pattern_sequence_frame"] = first_pattern_sequence_frame
                        thread = _ThreadedFunction(self.replicate_stitch_raster_frame, frame, kwargs, results)
                        replicator_threads.append(thread)

                    first_pattern_frame = False
                    start_frame_offset += 1

            count += 1

        # We wait for all the generator threads to complete first
        [thread.join() for thread in generator_threads]

        # We start the replicator threads and wait for them to all finish
        [thread.start() for thread in replicator_threads]
        [thread.join() for thread in replicator_threads]

        # Finally we wait for all the per frame generators to finish stitching
        [thread.join() for thread in generator_changes_per_frame_threads]

        self.completed_tasks += count

        yield self.progress()
        return results

    def get_raster_base_path(self, raster_name):
        """ For the given raster_name, we get the output folder for the raster maps

        :param raster_name: the name of the raster map we are want the folder for
        :return: the file path to the folder
        """
        folder_name = "".join(
            [self.project_settings.folder_prefix, raster_name, self.project_settings.folder_suffix]
        )
        base_path = os.path.join(
            self.project_settings.output_folder,
            "RasterMaps",
            folder_name
        )
        return base_path

    def stitch_raster_frame(self, frame, kwargs, results):
        """ The method to produce a single raster frame stitched from the output of each of the generators

        :param frame: the frame we are going to stitch
        :param kwargs: a dictionary of arguments for the function
        :param results: a dictionary to store the output results in cross thread
        """
        raster_map = kwargs.get("raster_map", None)
        if raster_map is None:
            raise ValueError("raster_data not found in kwargs")

        full_sequence_frame_num = kwargs.get("full_sequence_frame_num", None)
        if full_sequence_frame_num is None:
            raise ValueError("full_sequence_frame_num not found in kwargs")

        pattern_results = kwargs.get("pattern_results", None)
        if pattern_results is None:
            raise ValueError("pattern_results not found in kwargs")

        raster_name = raster_map.name
        base_path = self.get_raster_base_path(raster_name)
        resolution_width = raster_map.resolution_width
        resolution_height = raster_map.resolution_height

        raster_image = _imageUtils.create_solid_color_image(
            resolution_width, resolution_height,
            num_channels=3, color=(0, 0, 0)
        )
        frame_num = self.project_settings.sequence_start_frame + frame
        for mapping in raster_map.mappings:
            led_wall = self.walls[mapping.wall_name]
            file_path = pattern_results[led_wall.name][frame_num]
            buf = oiio.ImageBuf(file_path)
            buf.read()
            if buf.has_error:
                print("Error reading the file:", buf.geterror())

            wall_segment_region = oiio.ROI(
                mapping.wall_segment_u_start, mapping.wall_segment_u_end,
                mapping.wall_segment_v_start, mapping.wall_segment_v_end
            )

            # We always make the top left hand corner the origin before we apply any positioning
            # into the mapping
            wall_segment = oiio.ImageBufAlgo.cut(buf, roi=wall_segment_region, nthreads=0)
            wall_segment_rotated = oiio.ImageBufAlgo.rotate(wall_segment,
                                                            math.radians(mapping.wall_segment_orientation),
                                                            recompute_roi=True)
            wall_segment_rotated.set_origin(0, 0)

            oiio.ImageBufAlgo.paste(
                raster_image, mapping.raster_u, mapping.raster_v, 0, 0, wall_segment_rotated, roi=oiio.ROI.All
            )

        file_name = "{0}.{1}.{2}".format(
            raster_name,
            str(full_sequence_frame_num).zfill(self.project_settings.frame_padding), self.project_settings.image_file_format
        )
        full_file_path = os.path.join(
            base_path,
            file_name
        )

        # We do not provide a channel mapping here as our images will already have had their channels swapped
        # We do not apply a color space conversion here either as these will have already been done
        _imageUtils.write_image(raster_image, full_file_path, self.project_settings.image_file_bit_depth)
        results[raster_name][full_sequence_frame_num] = full_file_path

    def replicate_stitch_raster_frame(self, frame, kwargs, results):
        """ The method to replicate an existing stitched frame and renumber it in the sequence

        :param frame: the frame we are going to stitch
        :param kwargs: a dictionary of arguments for the function
        :param results: a dictionary to store the output results in cross thread
        """
        raster_map = kwargs.get("raster_map", None)
        if raster_map is None:
            raise ValueError("raster_data not found in kwargs")

        full_sequence_frame_num = kwargs.get("full_sequence_frame_num", None)
        if full_sequence_frame_num is None:
            raise ValueError("full_sequence_frame_num not found in kwargs")

        first_pattern_sequence_frame = kwargs.get("first_pattern_sequence_frame", None)
        if first_pattern_sequence_frame is None:
            raise ValueError("first_pattern_sequence_frame not found in kwargs")

        raster_name = raster_map.name
        base_path = self.get_raster_base_path(raster_name)

        file_name = "{0}.{1}.{2}".format(
            raster_name,
            str(full_sequence_frame_num).zfill(self.project_settings.frame_padding), self.project_settings.image_file_format
        )

        first_frame_file_name = "{0}.{1}.{2}".format(
            raster_name,
            str(first_pattern_sequence_frame).zfill(self.project_settings.frame_padding),
            self.project_settings.image_file_format
        )

        full_file_path = os.path.join(
            base_path,
            file_name
        )

        first_frame_file_full_path = os.path.join(
            base_path,
            first_frame_file_name
        )

        # We do not provide a channel mapping here as our images will already have had their channels swapped
        # We do not apply a color space conversion here either as these will have already been done
        shutil.copy(first_frame_file_full_path, full_file_path)
        results[raster_name][full_sequence_frame_num] = full_file_path
