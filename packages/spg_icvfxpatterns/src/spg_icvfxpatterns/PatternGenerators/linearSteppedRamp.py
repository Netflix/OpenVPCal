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

Module which holds the LinearSteppedRamp Generator
"""
import spg.utils.imageUtils as _imageUtils
from spg.PatternGenerators.basePatternGenerator import BasePatternGenerator, BasePatternGeneratorMeta
from spg.utils import constants as _constants
from spg.utils.attributeUtils import CategorizedAttribute, UICategory
from spg.utils.imageUtils import oiio


class LinearSteppedRampMeta(BasePatternGeneratorMeta):
    """ The meta class which handles the class param access via properties

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        number_of_steps - The number of steps between the range we want to create bands in the ramp
        min_value - The minimum value in the range
        max_value - The maximum value in the range
        font_size - The size of the display text displaying the nit values
        text_color - The color of the text displaying the nit values

    """
    def __init__(cls, *args, **kwargs):
        super().__init__(cls)
        cls._pattern_type = CategorizedAttribute(
            "LinearSteppedRamp", UICategory.UI_CAT_STRING, "The type of the pattern generator",
            readOnly=True
        )

        cls._number_of_steps = CategorizedAttribute(
            10, UICategory.UI_CAT_INTEGER, "No. steps through the range"
        )

        cls._min_value = CategorizedAttribute(
            0, UICategory.UI_CAT_INTEGER, "Min value of range"
        )

        cls._max_value = CategorizedAttribute(
            100, UICategory.UI_CAT_INTEGER, "Max value of range"
        )

        cls._font_size = CategorizedAttribute(
            50, UICategory.UI_CAT_INTEGER, "Size of display text"
        )

        cls._text_color = CategorizedAttribute(
            [1, 0, 0], UICategory.UI_CAT_COLOR, "Color of display text"
        )

    @property
    def number_of_steps(cls):
        """ The getter for the class attribute number_of_steps

        :return: The value stored within the number_of_steps CategorizedAttribute
        """
        return cls._number_of_steps.value

    @number_of_steps.setter
    def number_of_steps(cls, value):
        """ Setter for the class attribute number_of_steps

        :param value: the value we want to store within the number_of_steps class attribute, inside the CategorizedAttribute
        """
        cls._number_of_steps.value = value

    @property
    def min_value(cls):
        """ The getter for the class attribute min_value

        :return: The value stored within the min_value CategorizedAttribute
        """
        return cls._min_value.value

    @min_value.setter
    def min_value(cls, value):
        """ Setter for the class attribute min_value

        :param value: the value we want to store within the min_value class attribute, inside the CategorizedAttribute
        """
        cls._min_value.value = value

    @property
    def max_value(cls):
        """ The getter for the class attribute max_value

        :return: The value stored within the max_value CategorizedAttribute
        """
        return cls._max_value.value

    @max_value.setter
    def max_value(cls, value):
        """ Setter for the class attribute max_value

        :param value: the value we want to store within the max_value class attribute, inside the CategorizedAttribute
        """
        cls._max_value.value = value

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


class LinearSteppedRamp(BasePatternGenerator, metaclass=LinearSteppedRampMeta):
    """ A generator which creates a stepped ramp patterns, between a given range and number of steps.
    By default, this generates 10 steps, between 0-100 which represents 0-10,000 nits based on PQ encoding
    so is used to detect which values are being clipped on the led wall. Changing the range to 0-10 would allow
    us to check a range of nits between 0-1000 nits, similarly a range of 0-1 would allow us to check a range of
    nits between 0-100 nits.

    .. image:: ../_static/images/linear_stepped_ramp.png
        :width: 400
        :alt: Example Linear Stepped Ramp Pattern

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        number_of_steps - The number of steps between the range we want to create bands in the ramp
        min_value - The minimum value in the range
        max_value - The maximum value in the range
        font_size - The size of the display text displaying the nit values
        text_color - The color of the text displaying the nit values

    """
    method = _constants.GM_FIXED

    def __init__(self):
        super(LinearSteppedRamp, self).__init__()

    @property
    def number_of_steps(self):
        """ Gets the number_of_steps of the generator stored within the class property

        :return: Returns the number_of_steps
        """
        return self.__class__.number_of_steps

    @property
    def min_value(self):
        """ Gets the min_value of the generator stored within the class property

        :return: Returns the min_value
        """
        return self.__class__.min_value

    @property
    def max_value(self):
        """ Gets the max_value of the generator stored within the class property

        :return: Returns the max_value
        """
        return self.__class__.max_value

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
            "number_of_steps": self.number_of_steps,
            "min_value": self.min_value,
            "max_value": self.max_value,
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

        value_range = cls.max_value - cls.min_value
        value_per_step = value_range/cls.number_of_steps
        height_per_step = int(led_wall.resolution_height/(cls.number_of_steps + 1))
        for x in range(cls.number_of_steps + 1):
            step_value = (value_per_step * x) + cls.min_value
            step_image = cls.create_solid_color_image(
                led_wall.resolution_width, height_per_step,
                color=[step_value, step_value, step_value]
            )

            string_step_value = str(int(step_value * 100)) + " NITS"
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
        results = super(LinearSteppedRamp, self).get_properties()
        results.update({
            "number_of_steps": self.__class__._number_of_steps,
            "min_value": self.__class__._min_value,
            "max_value": self.__class__._max_value,
            "font_size": self.__class__._font_size,
            "text_color": self.__class__._text_color,
        })
        return results
