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

Module contains the base pattern generator from which all pattern generators inherit.
"""
import json
import os
import shutil

from spg.utils import constants as _constants
from spg.utils import imageUtils as _imageUtils
from spg.utils.attributeUtils import CategorizedAttribute, UICategory
from spg.utils.threadingUtils import ThreadedFunction as _ThreadedFunction


class BasePatternGeneratorMeta(type):
    """ The base class meta class which handles the class param access via properties

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        bit_depth_override - The bit depth for the images generated, as an override to the project settings
        input_transform - The color transform which describes our input color space we want to convert from
        enable_color_conversion - If we want to disable or enable color conversions via ocio, defaults to enabled

    """
    def __init__(cls, *args, **kwargs):
        super().__init__(cls)
        cls._name = CategorizedAttribute(
            "", UICategory.UI_CAT_STRING, "The name of the pattern generator"
        )

        cls._pattern_type = CategorizedAttribute(
            "", UICategory.UI_CAT_STRING, "The type of the pattern generator",
            readOnly=True
        )

        cls._sequence_length = CategorizedAttribute(
            2, UICategory.UI_CAT_INTEGER, "Lenght of sequence in seconds"
        )

        cls._bit_depth_override = CategorizedAttribute(
            None, UICategory.UI_CAT_OPTION, "The bit depth used, overrides project",
            ui_function_name="get_img_bit_depth_override"
        )

        cls._input_transform = CategorizedAttribute(
            None, UICategory.UI_CAT_OPTION, "The input color transform",
            ui_function_name="get_input_color_transforms"
        )

        cls._enable_color_conversion = CategorizedAttribute(
            True, UICategory.UI_CAT_BOOLEAN, "Perform ocio color conversion",
        )

    @property
    def name(cls):
        """ The getter for the class attribute name

        :return: The value stored within the name CategorizedAttribute
        """
        return cls._name.value

    @name.setter
    def name(cls, value):
        """ Setter for the class attrbiute name

        :param value: the value we want to store within the name class attribute, inside the CategorizedAttribute
        """
        cls._name.value = value

    @property
    def pattern_type(cls):
        """ The getter for the class attribute pattern_type

        :return: The value stored within the pattern_type CategorizedAttribute
        """
        return cls._pattern_type.value

    @pattern_type.setter
    def pattern_type(cls, value):
        """ Setter for the class attrbiute pattern_type

        :param value: the value we want to store within the pattern_type class attribute, inside the CategorizedAttribute
        """
        cls._pattern_type.value = value

    @property
    def sequence_length(cls):
        """ The getter for the class attribute sequence_length

        :return: The value stored within the sequence_length CategorizedAttribute
        """
        return cls._sequence_length.value

    @sequence_length.setter
    def sequence_length(cls, value):
        """ Setter for the class attrbiute sequence_length

        :param value: value to store within the sequence_length class attribute, inside the CategorizedAttribute
        """
        cls._sequence_length.value = value

    @property
    def bit_depth_override(cls):
        """ The getter for the class attribute bit_depth_override

        :return: The value stored within the bit_depth_override CategorizedAttribute
        """
        return cls._bit_depth_override.value

    @bit_depth_override.setter
    def bit_depth_override(cls, value):
        """ Setter for the class attrbiute bit_depth_override

        :param value: value to store within the bit_depth_override class attribute, inside the CategorizedAttribute
        """
        cls._bit_depth_override.value = value

    @property
    def input_transform(cls):
        """ The getter for the class attribute input_transform

        :return: The value stored within the input_transform CategorizedAttribute
        """
        return cls._input_transform.value

    @input_transform.setter
    def input_transform(cls, value):
        """ Setter for the class attrbiute input_transform

        :param value: value to store within the input_transform class attribute, inside the CategorizedAttribute
        """
        cls._input_transform.value = value

    @property
    def enable_color_conversion(cls):
        """ The getter for the class attribute enable_color_conversion

        :return: The value stored within the enable_color_conversion CategorizedAttribute
        """
        return cls._enable_color_conversion.value

    @enable_color_conversion.setter
    def enable_color_conversion(cls, value):
        """ Setter for the class attrbiute enable_color_conversion

        :param value: value to store within the enable_color_conversion class attribute, inside the CategorizedAttribute
        """
        cls._enable_color_conversion.value = value


class BasePatternGenerator(object, metaclass=BasePatternGeneratorMeta):
    """ The base class for all the pattern generators which provides the base functionality

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        bit_depth_override - The bit depth for the images generated, as an override to the project settings
        input_transform - The color transform which describes our input color space we want to convert from
        enable_color_conversion - If we want to disable or enable color conversions via ocio, defaults to enabled

    """
    spg = None
    method = None

    def __init__(self):
        """ The base pattern generator which is inherited by all the pattern generators.
        """
        self.frame = None
        self.led_wall = None

    @property
    def name(self):
        """ Gets the name of the generator stored within the class property

        :return: Returns the name
        """
        return self.__class__.name

    @property
    def pattern_type(self):
        """ Gets the pattern_type of the generator stored within the class property

        :return: Returns the pattern_type
        """
        return self.__class__.pattern_type

    @property
    def sequence_length(self):
        """ Gets the sequence_length of the generator stored within the class property

        :return: Returns the sequence_length
        """
        return self.__class__.sequence_length

    @property
    def bit_depth_override(self):
        """ Gets the bit_depth_override of the generator stored within the class property

        :return: Returns the bit_depth_override
        """
        return self.__class__.bit_depth_override

    @property
    def input_transform(self):
        """ Gets the input_transform of the generator stored within the class property

        :return: Returns the input_transform
        """
        return self.__class__.input_transform

    @property
    def enable_color_conversion(self):
        """ Gets the enable_color_conversion of the generator stored within the class property

        :return: Returns the enable_color_conversion
        """
        return self.__class__.enable_color_conversion

    @classmethod
    def number_of_frames(cls):
        """
        :return: Returns the given number of frames needed to be generated from the project frame rate and the
            length of the sequence requested
        """
        return int(cls.spg.project_settings.frame_rate * cls.sequence_length)

    def __iter__(self):
        """
        :yield: Yields the attributes which are important to be serialized to disk
        """
        yield from {
            "name": self.__class__.name,
            "pattern_type": self.__class__.pattern_type,
            "sequence_length": self.__class__.sequence_length,
            "bit_depth_override": self.__class__.bit_depth_override,
            "input_transform": self.__class__.input_transform,
            "enable_color_conversion": self.__class__.enable_color_conversion
        }.items()

    def __str__(self):
        """
        :return: Returns the string representation of the class, which is a json string
        """
        return json.dumps(dict(self), ensure_ascii=False)

    def __repr__(self):
        return self.__str__()

    def to_json(self):
        """
        :return: Returns the json data in a string format
        """
        return self.__str__()

    @classmethod
    def from_json(cls, spg, json_dct):
        """ Returns the generator for the given spg and json_data

        :param spg: The pattern generator instance to be use by the generator
        :param json_dct: the json dictionary representing the data for the generator settings
        :return: BasePatternGenerator
        """
        for key, value in json_dct.items():
            if not hasattr(cls, key):
                raise AttributeError("Class: {0} does not have attribute {1}".format(cls.name, key))
            setattr(cls, key, value)

        cls.spg = spg
        return cls()

    def execute(self):
        """ The main function which triggers either _execute_fixed or _execute_per_frame depending
        on the type of generator

        :return: A dict of led wall name to frame and filepath values
        """
        if self.method == _constants.GM_FIXED:
            return self._execute_fixed()

        if self.method == _constants.GM_PER_FRAME:
            return self._execute_per_frame()

        if self.method == _constants.GM_PER_FRAME_STAGE:
            return self._execute_per_frame_stage()

        raise ValueError("Unknown Pattern Generator Method ", self.method)

    def _execute_fixed(self):
        """ Triggers the control loop for the pattern generators which need patterns to have the same contents per frame,
            and are independent of all the other led walls on the stage.

            The user needs to implement generator method which is executed in a separate thread for the first frame
            whilst subsequent frames are duplicated with the replicator method. This can also be overridden however the
            base class implementation is often enough

        :return: A dict of led wall name to frame and filepath values
        """
        generator_threads = []
        replicator_threads = []
        results = {}

        # We loop over all the walls in the spd config
        for self.led_wall in self.spg.walls.values():

            results[self.led_wall.name] = {}
            self.get_and_create_pattern_output_folder(
                sub_folder="_".join([self.led_wall.name, self.name]))

            # We add a hook to perform custom logic before we start a new sequence
            self.sequence_start()
            first_frame = True

            for self.frame in range(self.number_of_frames()):
                # We add a hook to perform custom logic before we start a frame
                self.frame_start()

                # We get a dictionary of arguments to pass to our custom generator function
                kwargs = self.get_kwargs()

                if first_frame:
                    # We create a new thread which executes our generator, which we start and keep track of
                    thread = _ThreadedFunction(self.generator, self.frame, kwargs, results)
                    thread.start()
                    generator_threads.append(thread)
                else:
                    # We create a new thread which executes our replicator, which we do not start and keep track of
                    thread = _ThreadedFunction(self.replicator, self.frame, kwargs, results)
                    replicator_threads.append(thread)

                # We add a hook to perform custom logic as we end a frame
                self.frame_end()
                first_frame = False

            # We add a hook to perform custom logic as we end a sequence
            self.sequence_end()

        # We wait for the first frame to be finished
        [thread.join() for thread in generator_threads]

        # We start the replicator threads and wait for them to all finish
        [thread.start() for thread in replicator_threads]

        [thread.join() for thread in replicator_threads]

        return results

    def _execute_per_frame(self):
        """ Triggers the control loop for the pattern generators which need patterns to change contents per frame,
            but are independent of all the other led walls on the stage

            The user needs to implement generator method which is executed in separate thread per frame

        :return: A dict of led wall name to frame and filepath values
        """
        # Storage for a list of threads we are going to create, and the results we are going to return
        threads = []
        results = {}

        # We loop over all the walls in the spd config
        for self.led_wall in self.spg.walls.values():

            results[self.led_wall.name] = {}
            self.get_and_create_pattern_output_folder(
                sub_folder="_".join([self.led_wall.name, self.name]))

            # We add a hook to perform custom logic before we start a new sequence
            self.sequence_start()
            for self.frame in range(self.number_of_frames()):

                # We add a hook to perform custom logic before we start a frame
                self.frame_start()

                # We get a dictionary of arguments to pass to our custom generator function
                kwargs = self.get_kwargs()

                # We create a new thread which executes our generator, which we start and keep track of
                thread = _ThreadedFunction(self.generator, self.frame, kwargs, results)
                thread.start()
                threads.append(thread)

                # We add a hook to perform custom logic as we end a frame
                self.frame_end()

            # We add a hook to perform custom logic as we end a sequence
            self.sequence_end()

        # We wait for all the frames to finish before we return the results
        [thread.join() for thread in threads]

        return results

    def _execute_per_frame_stage(self):
        """ Triggers the control loop for the pattern generators which need patterns to change contents per frame,
            but are required to move across the whole stage and are dependent on the order of the led walls

            The user needs to implement generator method which is executed in separate thread per frame

        :return: A dict of led wall name to frame and filepath values
        """
        # Storage for a list of threads we are going to create, and the results we are going to return
        threads = []
        results = {}

        # We loop over all the walls in the spd config
        for self.led_wall in self.spg.walls.values():

            results[self.led_wall.name] = {}
            self.get_and_create_pattern_output_folder(
                sub_folder="_".join([self.led_wall.name, self.name]))

        # We add a hook to perform custom logic before we start a new sequence
        self.sequence_start()
        for self.frame in range(self.number_of_frames()):

            # We add a hook to perform custom logic before we start a frame
            self.frame_start()

            # We get a dictionary of arguments to pass to our custom generator function
            kwargs = self.get_kwargs()

            # We create a new thread which executes our generator, which we start and keep track of
            thread = _ThreadedFunction(self.generator, self.frame, kwargs, results)
            thread.start()
            threads.append(thread)

            # We add a hook to perform custom logic as we end a frame
            self.frame_end()

        # We add a hook to perform custom logic as we end a sequence
        self.sequence_end()

        # We wait for all the frames to finish before we return the results
        [thread.join() for thread in threads]

        return results

    @classmethod
    def get_and_create_pattern_output_folder(cls, sub_folder=None):
        """ Creates the folder to store the generated patterns, and returns the folder path.
        The folder path comes from the name of the generator and the output folder defined in the project settings.
        If the folder already exists it is deleted to ensure we start from a clean slate.

        :return: The folder path to the folder we want to write out images into, if the folder does not exist it makes
            the folder
        """
        pattern_folder_name = cls.name
        if not sub_folder:
            pattern_folder_name = "".join(
                [cls.spg.project_settings.folder_prefix, cls.name, cls.spg.project_settings.folder_suffix]
            )

        if sub_folder:
            sub_folder = "".join(
                [cls.spg.project_settings.folder_prefix, sub_folder, cls.spg.project_settings.folder_suffix]
            )

        base_path = os.path.join(
            cls.spg.project_settings.output_folder,
            "Patterns",
            pattern_folder_name,
            sub_folder
        )

        if not os.path.exists(base_path):
            os.makedirs(base_path)

        return base_path

    def sequence_start(self):
        """ Method which can be overridden in inherited classes to add custom logic to the execute loop,
        before a new image sequence is prepared

        :return: None
        """
        return

    def sequence_end(self):
        """ Method which can be overridden in inherited classes to add custom logic to execute loop,
        when an image sequence preparation has finished

        :return: None
        """
        return

    def frame_start(self):
        """ Method which can be overridden in inherited classes to add custom logic to execute loop,
        before we prepare a new frame in the sequence

        :return: None
        """
        return

    def frame_end(self):
        """ Method which can be overridden in inherited classes to add custom logic to execute loop,
        when a new frame has been prepared in the sequence

        :return: None
        """
        return

    @classmethod
    def generator(cls, frame, kwargs, results):
        """ The method to be overridden which implements the specific pattern generation

        :param frame: the frame number we are generating
        :param kwargs: a dictionary of args required for this generator, returned from get_kwargs
        :param results: a dictionary to store results cross thread
        :return:
        """
        raise NotImplementedError("generator function is not implemented")

    @classmethod
    def replicator(cls, frame, kwargs, results):
        """ The method to replicate an image with a new frame num

        :param frame: the frame number we are generating
        :param kwargs: a dictionary of args required for this generator, returned from get_kwargs
        :param results: a dictionary to store results cross thread
        :return:
        """
        led_wall = kwargs.get("led_wall", None)
        if led_wall is None:
            raise ValueError("led_wall not found in kwargs")

        first_frame_file_path = results[led_wall.name][0]

        frame_num, full_file_path = cls.get_frame_num_and_file_path(frame, led_wall.name)

        shutil.copy(first_frame_file_path, full_file_path)

        # Write the image to disk and store the result
        cls.store_result(frame_num, full_file_path, led_wall.name, results)

    def get_kwargs(self):
        """ Method returns a dictionary of kwargs which are passed to the generator function

        :return: dict of kwargs
        """

        kwargs = {
            "led_wall": self.led_wall,
            "led_walls": self.spg.walls.values()
        }
        return kwargs

    @classmethod
    def get_image_file_name(cls, pattern_output_folder, frame_num, name):
        """ Returns the correct file name for the image we are going to write to disk

        :param pattern_output_folder: the root output folder for the pattern
        :param frame_num: the frame number we want to write
        :param name: the name of the image
        :return: the full file path to the image we want to write to disk
        """
        file_name = "{0}_{1}.{2}.{3}".format(
            name,
            cls.name, str(frame_num).zfill(cls.spg.project_settings.frame_padding),
            cls.spg.project_settings.image_file_format
        )

        return os.path.join(
            pattern_output_folder,
            file_name
        )

    @classmethod
    def create_solid_color_image(cls, resolution_width, resolution_height, color=(0, 0, 0)):
        """ Creates a solid color with the given resolution and color, with the correct settings for this generator

        :param resolution_width: the width of the image
        :param resolution_height: the height of the image
        :param color: the color of the image
        :return: oiio.ImageBuf
        """
        led_wall_image = _imageUtils.create_solid_color_image(
            resolution_width, resolution_height,
            num_channels=3, color=color
        )
        return led_wall_image

    @classmethod
    def bit_depth_for_pattern(cls):
        """ Returns the bit depth for the given generator either from the project settings or from the generator
            override

        :return: The bit depth of the images generated
        """
        bit_depth = cls.bit_depth_override if cls.bit_depth_override else cls.spg.project_settings.image_file_bit_depth
        return bit_depth

    @classmethod
    def write_image_and_store_result(cls, frame_num, full_file_path, led_wall_name, image, results):
        """ Applies the needed color transforms to the image, and writes it
         to disk. The result is stored in results dict

        :param frame_num: the frame number we are writing out
        :param full_file_path: the full file path we want to write the image too
        :param led_wall_name: the name of the led_wall the image relates too
        :param image: the image we want to save
        :param results: a dict to store the results cross thread
        """
        if cls.enable_color_conversion:
            gamut_only_cs_name = None
            gamut_and_transfer_function_cs_name = None
            if led_wall_name in cls.spg.walls:
                gamut_only_cs_name = cls.spg.walls[led_wall_name].gamut_only_cs_name
                gamut_and_transfer_function_cs_name = cls.spg.walls[led_wall_name].gamut_and_transfer_function_cs_name

            if gamut_only_cs_name and gamut_and_transfer_function_cs_name:
                # If we have a pattern generator that has an input transform we use it else we use the gamut only
                # Reference images for instance may come in a different color space etc
                input_transform = cls.input_transform if cls.input_transform else gamut_only_cs_name
                image = _imageUtils.apply_color_conversion(
                    image, input_transform, gamut_and_transfer_function_cs_name,
                    cls.spg.project_settings.ocio_config_path
                )
            else:
                image = _imageUtils.apply_color_conversion(
                    image, cls.input_transform, cls.spg.project_settings.output_transform,
                    cls.spg.project_settings.ocio_config_path
                )

        _imageUtils.write_image(
            image, full_file_path, cls.bit_depth_for_pattern(), channel_mapping=cls.spg.project_settings.channel_mapping)
        cls.store_result(frame_num, full_file_path, led_wall_name, results)

    @classmethod
    def store_result(cls, frame_num, full_file_path, led_wall_name, results):
        """ Store the resulting image in the results dict

        :param frame_num: the frame number we are writing out
        :param full_file_path: the full file path we want to write the image too
        :param led_wall_name: the name of the led_wall the image relates too
        :param results: a dict to store the results cross thread
        """
        results[led_wall_name][frame_num] = full_file_path

    @classmethod
    def get_frame_num_and_file_path(cls, frame, item_name):
        """ Gets the output frame number for the given frame count, along with the file_path for the image we want to
        write out

        :param frame: the frame num of the sequence
        :param item_name: the name of the item this image relates too, this could be the led wall name for example
        :return: The frame number offset based on the sequence start num and the filepath we want to write the image too
        """
        pattern_output_folder = cls.get_and_create_pattern_output_folder(
            sub_folder="_".join([item_name, cls.name]))
        frame_num = cls.spg.project_settings.sequence_start_frame + frame

        full_file_path = cls.get_image_file_name(
            pattern_output_folder, frame_num, item_name
        )

        return frame_num, full_file_path

    def get_properties(self):
        """ Returns the names of the properties in the class with the property object containing all the data for that
            property

        :return: a dict of property name values with CategorizedAttribute values
        """
        return {
            "name": self.__class__._name,
            "pattern_type": self.__class__._pattern_type,
            "sequence_length": self.__class__._sequence_length,
            "bit_depth_override": self.__class__._bit_depth_override,
            "input_transform": self.__class__._input_transform,
            "enable_color_conversion": self.__class__._enable_color_conversion
        }
