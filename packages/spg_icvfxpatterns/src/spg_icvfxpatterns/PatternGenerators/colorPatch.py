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

Module holds the color patch pattern generator
"""
import math

import spg.utils.constants as _constants
from spg.PatternGenerators.basePatternGenerator import BasePatternGenerator, BasePatternGeneratorMeta
from spg.utils.attributeUtils import CategorizedAttribute, UICategory
from spg.utils.imageUtils import oiio


def normalize(value, min_val, max_val):
    return (value - min_val) / (max_val - min_val)


class ColorPatchMeta(BasePatternGeneratorMeta):
    """ The meta class which handles the class param access via properties

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        bit_depth_override - The bit depth for the images generated, as an override to the project settings
        input_transform - The color transform which describes our input color space we want to convert from
        enable_color_conversion - If we want to disable or enable color conversions via ocio, defaults to enabled
        percentage_width - The width of the patch as a percentage of the wall width
        percentage_height - The height of the patch as a percentage of the wall height
        absolute_pixel_width - The exact width of the patch in pixels, overrides the percentage_width
        absolute_pixel_height - The exact height of the patch in pixels, overrides the percentage_height
        color_range_min - The min range of the colors, be it [0-1], [0-255]
        color_range_max - The max range of the colors, be it [0-1], [0-255]
        duration_per_patch - How long we want each patch to appear for (seconds)
        color_patch_values - A list of color values we want to generate a patch for

    """
    def __init__(cls, *args, **kwargs):
        super().__init__(cls)
        cls._pattern_type = CategorizedAttribute(
            "ColorPatch", UICategory.UI_CAT_STRING, "The type of the pattern generator",
            readOnly=True
        )

        cls._percentage_width = CategorizedAttribute(
            0.5, UICategory.UI_CAT_FLOAT, "Patch width as % of wall width"
        )

        cls._percentage_height = CategorizedAttribute(
            0.5, UICategory.UI_CAT_FLOAT, "Patch height as % of wall width"
        )

        cls._absolute_pixel_width = CategorizedAttribute(
            0, UICategory.UI_CAT_INTEGER, "Patch width in pixels"
        )

        cls._absolute_pixel_height = CategorizedAttribute(
            0, UICategory.UI_CAT_INTEGER, "Patch height in pixels"
        )

        cls._color_range_min = CategorizedAttribute(
            0, UICategory.UI_CAT_INTEGER, "The min range of the colors"
        )

        cls._color_range_max = CategorizedAttribute(
            1, UICategory.UI_CAT_INTEGER, "The max range of the colors"
        )

        cls._duration_per_patch = CategorizedAttribute(
            2, UICategory.UI_CAT_INTEGER, "Duration of each patch (secs)"
        )

        cls._color_patch_values = CategorizedAttribute(
            [[1, 0, 0]], UICategory.UI_CAT_COLOR, "Color of patch", multi=True
        )

    @property
    def percentage_width(cls):
        """ The getter for the class attribute percentage_width

        :return: The value stored within the percentage_width CategorizedAttribute
        """
        return cls._percentage_width.value

    @percentage_width.setter
    def percentage_width(cls, value):
        """ Setter for the class attribute percentage_width

        :param value: the value we want to store within the percentage_width class attribute, inside the
        CategorizedAttribute
        """
        cls._percentage_width.value = value

    @property
    def percentage_height(cls):
        """ The getter for the class attribute percentage_height

        :return: The value stored within the percentage_height CategorizedAttribute
        """
        return cls._percentage_height.value

    @percentage_height.setter
    def percentage_height(cls, value):
        """ Setter for the class attribute percentage_height

        :param value: the value we want to store within the percentage_height class attribute, inside the
        CategorizedAttribute
        """
        cls._percentage_height.value = value

    @property
    def absolute_pixel_width(cls):
        """ The getter for the class attribute absolute_pixel_width

        :return: The value stored within the absolute_pixel_width CategorizedAttribute
        """
        return cls._absolute_pixel_width.value

    @absolute_pixel_width.setter
    def absolute_pixel_width(cls, value):
        """ Setter for the class attribute absolute_pixel_width

        :param value: the value we want to store within the absolute_pixel_width class attribute, inside the
        CategorizedAttribute
        """
        cls._absolute_pixel_width.value = value

    @property
    def absolute_pixel_height(cls):
        """ The getter for the class attribute absolute_pixel_height

        :return: The value stored within the absolute_pixel_height CategorizedAttribute
        """
        return cls._absolute_pixel_height.value

    @absolute_pixel_height.setter
    def absolute_pixel_height(cls, value):
        """ Setter for the class attribute absolute_pixel_height

        :param value: the value we want to store within the absolute_pixel_height class attribute, inside the
        CategorizedAttribute
        """
        cls._absolute_pixel_height.value = value

    @property
    def color_range_min(cls):
        """ The getter for the class attribute color_range_min

        :return: The value stored within the color_range_min CategorizedAttribute
        """
        return cls._color_range_min.value

    @color_range_min.setter
    def color_range_min(cls, value):
        """ Setter for the class attribute color_range_min

        :param value: the value we want to store within the color_range_min class attribute, inside the
        CategorizedAttribute
        """
        cls._color_range_min.value = value

    @property
    def color_range_max(cls):
        """ The getter for the class attribute color_range_max

        :return: The value stored within the color_range_max CategorizedAttribute
        """
        return cls._color_range_max.value

    @color_range_max.setter
    def color_range_max(cls, value):
        """ Setter for the class attribute color_range_max

        :param value: the value we want to store within the color_range_max class attribute, inside the
        CategorizedAttribute
        """
        cls._color_range_max.value = value

    @property
    def duration_per_patch(cls):
        """ The getter for the class attribute duration_per_patch

        :return: The value stored within the duration_per_patch CategorizedAttribute
        """
        return cls._duration_per_patch.value

    @duration_per_patch.setter
    def duration_per_patch(cls, value):
        """ Setter for the class attribute duration_per_patch

        :param value: the value we want to store within the duration_per_patch class attribute, inside the
        CategorizedAttribute
        """
        cls._duration_per_patch.value = value

    @property
    def color_patch_values(cls):
        """ The getter for the class attribute color_patch_values

        :return: The value stored within the color_patch_values CategorizedAttribute
        """
        return cls._color_patch_values.value

    @color_patch_values.setter
    def color_patch_values(cls, value):
        """ Setter for the class attribute color_patch_values

        :param value: the value we want to store within the color_patch_values class attribute, inside the
        CategorizedAttribute
        """
        cls._color_patch_values.value = value


class ColorPatch(BasePatternGenerator, metaclass=ColorPatchMeta):
    """ Generates a number of color patches of given or calculated dimensions, from a list of colors want to
    display. Either filling a given percentage of the led wall, or exact pixel height and widths

    .. image:: ../_static/images/color_patch.png
        :width: 400
        :alt: Example Color Patch Pattern

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        bit_depth_override - The bit depth for the images generated, as an override to the project settings
        input_transform - The color transform which describes our input color space we want to convert from
        enable_color_conversion - If we want to disable or enable color conversions via ocio, defaults to enabled
        percentage_width - The width of the patch as a percentage of the wall width
        percentage_height - The height of the patch as a percentage of the wall height
        absolute_pixel_width - The exact width of the patch in pixels, overrides the percentage_width
        absolute_pixel_height - The exact height of the patch in pixels, overrides the percentage_height
        color_range_min - The min range of the colors, be it [0-1], [0-255]
        color_range_max - The max range of the colors, be it [0-1], [0-255]
        duration_per_patch - How long we want each patch to appear for (seconds)
        color_patch_values - A list of color values we want to generate a patch for

    """
    method = _constants.GM_PER_FRAME

    def __init__(self):
        super(ColorPatch, self).__init__()
        self.patch_counter = 0
        self.num_patch_frames = 0

    @classmethod
    def number_of_frames(cls):
        """ Overrides the number of frames needed to be generated, as this needs to be calculated from the number of
            color patches we want to generate and how long each patch needs to stay visible for

        :return: Returns the given number of frames needed to be generated from the project frame rate and the
            length of the sequence requested
        """
        number_of_frames_per_patch = int(cls.duration_per_patch * cls.spg.project_settings.frame_rate)
        number_of_frames = int(math.ceil(len(cls.color_patch_values) * number_of_frames_per_patch))

        # We update the sequence length based on the number of frames and frame rate
        cls.sequence_length = number_of_frames / cls.spg.project_settings.frame_rate
        return number_of_frames

    @property
    def percentage_width(self):
        """ Gets the percentage_width of the generator stored within the class property

        :return: Returns the percentage_width
        """
        return self.__class__.percentage_width

    @property
    def percentage_height(self):
        """ Gets the percentage_height of the generator stored within the class property

        :return: Returns the percentage_height
        """
        return self.__class__.percentage_height

    @property
    def absolute_pixel_width(self):
        """ Gets the absolute_pixel_width of the generator stored within the class property

        :return: Returns the absolute_pixel_width
        """
        return self.__class__.absolute_pixel_width

    @property
    def absolute_pixel_height(self):
        """ Gets the absolute_pixel_height of the generator stored within the class property

        :return: Returns the absolute_pixel_height
        """
        return self.__class__.absolute_pixel_height

    @property
    def color_range_min(self):
        """ Gets the color_range_min of the generator stored within the class property

        :return: Returns the color_range_min
        """
        return self.__class__.color_range_min

    @property
    def color_range_max(self):
        """ Gets the color_range_max of the generator stored within the class property

        :return: Returns the color_range_max
        """
        return self.__class__.color_range_max

    @property
    def duration_per_patch(self):
        """ Gets the duration_per_patch of the generator stored within the class property

        :return: Returns the duration_per_patch
        """
        return self.__class__.duration_per_patch

    @property
    def color_patch_values(self):
        """ Gets the color_patch_values of the generator stored within the class property

        :return: Returns the color_patch_values
        """
        return self.__class__.color_patch_values

    def __iter__(self):
        yield from super().__iter__()
        yield from {
            "percentage_width": self.percentage_width,
            "percentage_height": self.percentage_height,
            "absolute_pixel_width": self.absolute_pixel_width,
            "absolute_pixel_height": self.absolute_pixel_height,
            "color_range_min": self.color_range_min,
            "color_range_max": self.color_range_max,
            "duration_per_patch": self.duration_per_patch,
            "color_patch_values": self.color_patch_values
        }.items()

    def sequence_start(self):
        """ At the start of each new sequence we reset the counters, we use these to count how many frames
        each patch has been generated for
        """
        self.patch_counter = 0
        self.num_patch_frames = 0

    def frame_end(self):
        """ At the end of each frame we increment the count for the number of frames the current patch has been
        generated for. Once we have generated a specific patch for the required number of frames, we reset the counter
        and increase the index of the patch

        Returns:

        """
        self.num_patch_frames += 1
        if self.num_patch_frames == int(self.duration_per_patch * self.spg.project_settings.frame_rate):
            self.patch_counter += 1
            self.num_patch_frames = 0

    @classmethod
    def generator(cls, frame, kwargs, results):
        """ The method which creates the checkerboard images based on the kwargs provided

        :param frame: the frame number we are generating
        :param kwargs: a dictionary of the arguments for the generator
        :param results: a dictionary to store the results
        """
        led_wall = kwargs.get("led_wall", None)
        if led_wall is None:
            raise ValueError("led_wall not found in kwargs")

        patch_counter = kwargs.get("patch_counter", None)
        if patch_counter is None:
            raise ValueError("patch_counter not found in kwargs")

        frame_num, full_file_path = cls.get_frame_num_and_file_path(frame, led_wall.name)

        led_wall_image = cls.create_solid_color_image(
            led_wall.resolution_width, led_wall.resolution_height
        )

        pixel_width = cls.absolute_pixel_width
        pixel_height = cls.absolute_pixel_width

        if not pixel_width or not pixel_height:
            if not cls.percentage_width or not cls.percentage_height:
                raise ValueError("Please specify either absolute pixel widths or heights")

            pixel_width = int(cls.percentage_width * led_wall.resolution_width)
            pixel_height = int(cls.percentage_height * led_wall.resolution_height)

        patch_color = cls.color_patch_values[patch_counter]
        normalized_color = [
            normalize(patch_color_channel, cls.color_range_min, cls.color_range_max)
            for patch_color_channel in patch_color
        ]

        patch_image = cls.create_solid_color_image(
            pixel_width, pixel_height, color=normalized_color
        )

        centre_x = int((led_wall.resolution_width * 0.5) - (pixel_width * 0.5))
        centre_y = int((led_wall.resolution_height * 0.5) - (pixel_height * 0.5))

        oiio.ImageBufAlgo.paste(
            led_wall_image, centre_x, centre_y, 0, 0, patch_image, roi=oiio.ROI.All)

        # Write the image to disk and store the result
        cls.write_image_and_store_result(
            frame_num, full_file_path, led_wall.name, led_wall_image, results
        )

    def get_kwargs(self):
        """ We return the base arguments along with the custom data introduced and updated
            on a per frame bases

        :return: a dictionary of kwargs needed by the generator function
        """
        kwargs = super(ColorPatch, self).get_kwargs()
        kwargs_local = {
            "patch_counter": self.patch_counter,
        }
        kwargs.update(kwargs_local)
        return kwargs

    def get_properties(self):
        """ Returns the names of the properties in the class with the property object containing all the data for that
            property

        :return: a dict of property name values with CategorizedAttribute values
        """
        results = super(ColorPatch, self).get_properties()
        results.update({
            "percentage_width": self.__class__._percentage_width,
            "percentage_height": self.__class__._percentage_height,
            "absolute_pixel_width": self.__class__._absolute_pixel_width,
            "absolute_pixel_height": self.__class__._absolute_pixel_height,
            "color_range_min": self.__class__._color_range_min,
            "color_range_max": self.__class__._color_range_max,
            "duration_per_patch": self.__class__._duration_per_patch,
            "color_patch_values": self.__class__._color_patch_values
        })
        return results
