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

Holds the ProjectSettings declaration

"""
import json

from spg.utils.attributeUtils import CategorizedAttribute, UICategory


class ProjectSettings(object):
    """ Object to represent the project settings we want to use to generate the image sequences

        Attributes
            frame_rate - The frame rate we are playing back and shooting
            sequence_start_frame: The frame number we want each sequence to start at
            image_file_format:  The format of the images we want to generate
            image_file_bit_depth:  The imaging bit-depth of our pipeline
            output_folder:  The root folder we want to output our generated images into
            frame_padding: The amount of padding required for frame numbers
            folder_suffix: A suffix to apply to any sequence folders created
            folder_prefix: A prefix to apply to any sequence folders created
            channel_mapping: The order of the channels be it RGB, BGR etc
            output_transform: The output transform for the image sequences
            ocio_config_path: The filepath to the ocio config we want to use
    """
    def __init__(self):
        self._frame_rate = CategorizedAttribute(
            None, UICategory.UI_CAT_OPTION_FLOAT, "The frame rate we are playing back and shooting",
            ui_function_name="get_frame_rates"
        )

        self._sequence_start_frame = CategorizedAttribute(
            0, UICategory.UI_CAT_INTEGER, "The frame number we want each sequence to start at"
        )

        self._image_file_format = CategorizedAttribute(
            None, UICategory.UI_CAT_OPTION, "The format of the images we want to generate",
            ui_function_name="get_img_file_formats"
        )

        self._image_file_bit_depth = CategorizedAttribute(
            None, UICategory.UI_CAT_OPTION, "The imaging bit-depth of our pipeline",
            ui_function_name="get_img_bit_depths"
        )

        self._output_folder = CategorizedAttribute(
            "", UICategory.UI_CAT_EXCLUDE, "The root folder we want to output our generated images into",
        )

        self._frame_padding = CategorizedAttribute(
            6, UICategory.UI_CAT_INTEGER, "The amount of padding required for frame numbers"
        )

        self._folder_suffix = CategorizedAttribute(
            "", UICategory.UI_CAT_STRING, "A suffix to apply to any sequence folders created",
            optional=True
        )
        self._folder_prefix = CategorizedAttribute(
            "", UICategory.UI_CAT_STRING, "A prefix to apply to any sequence folders created",
            optional=True
        )

        self._channel_mapping = CategorizedAttribute(
            None, UICategory.UI_CAT_OPTION, "The order of the channels be it RGB, BGR etc",
            ui_function_name="get_channel_mapping_options"
        )

        self._output_transform = CategorizedAttribute(
            "", UICategory.UI_CAT_EXCLUDE, "The output transform for the image sequences",
        )

        self._ocio_config_path = CategorizedAttribute(
            "", UICategory.UI_CAT_EXCLUDE, "The filepath to the ocio config we want to use",
        )

    def __iter__(self):
        yield from {
            "frame_rate": self.frame_rate,
            "sequence_start_frame": self.sequence_start_frame,
            "image_file_format": self.image_file_format,
            "image_file_bit_depth": self.image_file_bit_depth,
            "output_folder": self.output_folder,
            "frame_padding": self.frame_padding,
            "folder_suffix": self.folder_suffix,
            "folder_prefix": self.folder_prefix,
            "channel_mapping": self.channel_mapping,
            "output_transform": self.output_transform,
            "ocio_config_path": self.ocio_config_path
        }.items()

    def __str__(self):
        return json.dumps(dict(self), ensure_ascii=False)

    def __repr__(self):
        return self.__str__()

    @property
    def frame_rate(self):
        """ Getter for the frame_rate

        :return: Returns the frame_rate of the project
        """
        return self._frame_rate.value

    @frame_rate.setter
    def frame_rate(self, value):
        """ Setter for the frame_rate categorized param

        :param value: the value we want to store in the name categorized param
        """
        self._frame_rate.value = value

    @property
    def sequence_start_frame(self):
        """ Getter for the sequence_start_frame

        :return: Returns the sequence_start_frame of the project
        """
        return self._sequence_start_frame.value

    @sequence_start_frame.setter
    def sequence_start_frame(self, value):
        """ Setter for the sequence_start_frame categorized param

        :param value: the value we want to store in the sequence_start_frame categorized param
        """
        self._sequence_start_frame.value = value

    @property
    def image_file_format(self):
        """ Getter for the image_file_format

        :return: Returns the image_file_format of the project
        """
        return self._image_file_format.value

    @image_file_format.setter
    def image_file_format(self, value):
        """ Setter for the image_file_format categorized param

        :param value: the value we want to store in the image_file_format categorized param
        """
        self._image_file_format.value = value

    @property
    def image_file_bit_depth(self):
        """ Getter for the image_file_bit_depth

        :return: Returns the image_file_bit_depth of the project
        """
        return self._image_file_bit_depth.value

    @image_file_bit_depth.setter
    def image_file_bit_depth(self, value):
        """ Setter for the image_file_format categorized param

        :param value: the value we want to store in the image_file_bit_depth categorized param
        """
        self._image_file_bit_depth.value = value

    @property
    def output_folder(self):
        """ Getter for the output_folder

        :return: Returns the output_folder of the project
        """
        return self._output_folder.value

    @output_folder.setter
    def output_folder(self, value):
        """ Setter for the output_folder categorized param

        :param value: the value we want to store in the output_folder categorized param
        """
        self._output_folder.value = value

    @property
    def frame_padding(self):
        """ Getter for the frame_padding

        :return: Returns the frame_padding of the project
        """
        return self._frame_padding.value

    @frame_padding.setter
    def frame_padding(self, value):
        """ Setter for the frame_padding categorized param

        :param value: the value we want to store in the frame_padding categorized param
        """
        self._frame_padding.value = value

    @property
    def folder_suffix(self):
        """ Getter for the folder_suffix

        :return: Returns the folder_suffix of the project
        """
        return self._folder_suffix.value

    @folder_suffix.setter
    def folder_suffix(self, value):
        """ Setter for the folder_suffix categorized param

        :param value: the value we want to store in the folder_suffix categorized param
        """
        self._folder_suffix.value = value

    @property
    def folder_prefix(self):
        """ Getter for the folder_prefix

        :return: Returns the folder_prefix of the project
        """
        return self._folder_prefix.value

    @folder_prefix.setter
    def folder_prefix(self, value):
        """ Setter for the folder_prefix categorized param

        :param value: the value we want to store in the folder_prefix categorized param
        """
        self._folder_prefix.value = value

    @property
    def channel_mapping(self):
        """ Getter for the channel_mapping

        :return: Returns the channel_mapping of the project
        """
        return self._channel_mapping.value

    @channel_mapping.setter
    def channel_mapping(self, value):
        """ Setter for the channel_mapping categorized param

        :param value: the value we want to store in the channel_mapping categorized param
        """
        self._channel_mapping.value = value

    @property
    def output_transform(self):
        """ Getter for the output_transform

        :return: Returns the output_transform of the project
        """
        return self._output_transform.value

    @output_transform.setter
    def output_transform(self, value):
        """ Setter for the output_transform categorized param

        :param value: the value we want to store in the output_transform categorized param
        """
        self._output_transform.value = value

    @property
    def ocio_config_path(self):
        """ Getter for the ocio_config_path

        :return: Returns the ocio_config_path of the project
        """
        return self._ocio_config_path.value

    @ocio_config_path.setter
    def ocio_config_path(self, value):
        """ Setter for the ocio_config_path categorized param

        :param value: the value we want to store in the ocio_config_path categorized param
        """
        self._ocio_config_path.value = value

    def to_json(self):
        """
        :return: Returns the json data in a string format
        """
        return self.__str__()

    def get_properties(self):
        """ Returns the names of the properties in the class with the property object containing all the data for that
            property

        :return: a dict of property name values with CategorizedAttribute values
        """
        return {
            "frame_rate": self._frame_rate,
            "image_file_format": self._image_file_format,
            "image_file_bit_depth": self._image_file_bit_depth,
            "channel_mapping": self._channel_mapping,
            "sequence_start_frame": self._sequence_start_frame,
            "frame_padding": self._frame_padding,
            "folder_suffix": self._folder_suffix,
            "folder_prefix": self._folder_prefix,
            "output_folder": self._output_folder,
            "output_transform": self._output_transform,
            "ocio_config_path": self._ocio_config_path
        }

    @staticmethod
    def from_json(json_dict):
        """ Returns a ProjectSettings object from the given json data

        :param json_dict: the json dictionary representing the data for the ProjectSettings
        :return: Returns a ProjectSettings object from the given json data
        """
        project_settings = ProjectSettings(
        )
        for key, value in json_dict.items():
            if not hasattr(project_settings, key):
                raise AttributeError("ProjectSettings does not have attribute {0}".format(key))

            setattr(project_settings, key, value)
        return project_settings
