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

Module which holds the RealBlackLevel pattern generator
"""
import spg.utils.imageUtils as _imageUtils
from spg.PatternGenerators.basePatternGenerator import BasePatternGenerator, BasePatternGeneratorMeta
from spg.utils import constants as _constants
from spg.utils.attributeUtils import CategorizedAttribute, UICategory
from spg.utils.imageUtils import oiio


def normalize(value, min_val, max_val):
    return (value - min_val) / (max_val - min_val)


class RealBlackLevelMeta(BasePatternGeneratorMeta):
    """ The meta class which handles the class param access via properties

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        bit_depth_override - The bit depth for the images generated, as an override to the project settings
        input_transform - The color transform which describes our input color space we want to convert from
        enable_color_conversion - If we want to disable or enable color conversions via ocio, defaults to enabled
        limit - The limit we apply to the range of all the code values available at the given bit depth, defaults to
            0.18 so we create a step in the ramp for the first 18% of all the valid values
        font_size - The size of the display text displaying the values at each step
        text_color - The color of the text displaying the values at each step

    """
    def __init__(cls, *args, **kwargs):
        super().__init__(cls)
        cls._pattern_type = CategorizedAttribute(
            "RealBlackLevel", UICategory.UI_CAT_STRING, "The type of the pattern generator",
            readOnly=True
        )

        cls._limit = CategorizedAttribute(
            0.18, UICategory.UI_CAT_FLOAT, "The % of the values to show"
        )

        cls._font_size = CategorizedAttribute(
            10, UICategory.UI_CAT_INTEGER, "The size of the display text"
        )

        cls._text_color = CategorizedAttribute(
            [1, 0, 0], UICategory.UI_CAT_COLOR, "The color of the text display"
        )

    @property
    def limit(cls):
        """ The getter for the class attribute limit

        :return: The value stored within the limit CategorizedAttribute
        """
        return cls._limit.value

    @limit.setter
    def limit(cls, value):
        """ Setter for the class attribute limit

        :param value: the value we want to store within the limit class attribute, inside the CategorizedAttribute
        """
        cls._limit.value = value

    @property
    def font_size(cls):
        """ The getter for the class attribute font_size

        :return: The value stored within the font_size CategorizedAttribute
        """
        return cls._font_size.value

    @font_size.setter
    def font_size(cls, value):
        """ Setter for the class attribute font_size

        :param value: the value we want to store within the font_size class attribute, inside the CategorizedAttribute
        """
        cls._font_size.value = value

    @property
    def text_color(cls):
        """ The getter for the class attribute text_color

        :return: The value stored within the text_color CategorizedAttribute
        """
        return cls._text_color.value

    @text_color.setter
    def text_color(cls, value):
        """ Setter for the class attribute text_color

        :param value: the value we want to store within the text_color class attribute, inside the CategorizedAttribute
        """
        cls._text_color.value = value


class RealBlackLevel(BasePatternGenerator, metaclass=RealBlackLevelMeta):
    """ We create a stepped ramp displaying the bottom % range of valid values for the current bit depth.
    This allows us to identify where our actual black levels become clipped and the difference becomes undetermined.


    Default we display the bottom 18% of values.

    .. image:: ../_static/images/real_black_level.png
        :width: 400
        :alt: Example Real Black Level Pattern

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        limit - The limit we apply to the range of all the code values available at the given bit depth, defaults to
            0.18 so we create a step in the ramp for the first 18% of all the valid values
        font_size - The size of the display text displaying the values at each step
        text_color - The color of the text displaying the values at each step

    """
    method = _constants.GM_FIXED

    def __init__(self):
        super(RealBlackLevel, self).__init__()

    @property
    def limit(self):
        """ Gets the limit of the generator stored within the class property

        :return: Returns the limit
        """
        return self.__class__.limit

    @property
    def font_size(self):
        """ Gets the font_size of the generator stored within the class property

        :return: Returns the font_size
        """
        return self.__class__.font_size

    @property
    def text_color(self):
        """ Gets the text_color of the generator stored within the class property

        :return: Returns the text_color
        """
        return self.__class__.text_color

    def __iter__(self):
        yield from super().__iter__()
        yield from {
            "limit": self.limit,
            "font_size": self.font_size,
            "text_color": self.text_color,
        }.items()

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

        frame_num, full_file_path = cls.get_frame_num_and_file_path(frame, led_wall.name)

        led_wall_image = cls.create_solid_color_image(
            led_wall.resolution_width, led_wall.resolution_height
        )

        bit_depth = cls.bit_depth_for_pattern()

        max_code_value = (2 ** bit_depth) - 1
        limited_max_code_value = int(max_code_value * cls.limit)

        height_per_step = int(led_wall.resolution_height/(limited_max_code_value + 1))
        for x in range(limited_max_code_value + 1):
            value = normalize(x, 0, max_code_value)
            step_image = cls.create_solid_color_image(
                led_wall.resolution_width, height_per_step,
                color=[value, value, value]
            )

            string_step_value = "{:.{}f}".format(value, 3)
            _imageUtils.add_text_to_image_centre(
                step_image, str(string_step_value), font_size=cls.font_size, text_color=cls.text_color)

            oiio.ImageBufAlgo.paste(
                led_wall_image, 0, x * height_per_step, 0, 0, step_image, roi=oiio.ROI.All)

        # Write the image to disk and store the result
        cls.write_image_and_store_result(
            frame_num, full_file_path, led_wall.name, led_wall_image, results
        )

    def get_properties(self):
        """ Returns the names of the properties in the class with the property object containing all the data for that
            property

        :return: a dict of property name values with CategorizedAttribute values
        """
        results = super(RealBlackLevel, self).get_properties()
        results.update({
            "limit": self.__class__._limit,
            "font_size": self.__class__._font_size,
            "text_color": self.__class__._text_color,
        })
        return results
