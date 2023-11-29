""" Module which holds the BitDepth Pattern Generator
"""
import math

import spg.utils.constants as _constants
from spg.PatternGenerators.basePatternGenerator import BasePatternGenerator, BasePatternGeneratorMeta
from spg.utils.attributeUtils import CategorizedAttribute, UICategory


def normalize(value, min_val, max_val):
    return (value - min_val) / (max_val - min_val)


class BitDepthMeta(BasePatternGeneratorMeta):
    """ The meta class which handles the class param access via properties

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        bit_depth_override - The bit depth for the images generated, as an override to the project settings
        input_transform - The color transform which describes our input color space we want to convert from
        enable_color_conversion - If we want to disable or enable color conversions via ocio, defaults to enabled
        bit_depth_value - The bit depth we want to represent all the code values for, this is not the bit depth of the
            image container.

    """
    def __init__(cls, *args, **kwargs):
        super().__init__(cls)
        cls._pattern_type = CategorizedAttribute(
            "BitDepth", UICategory.UI_CAT_STRING, "The type of the pattern generator",
            readOnly=True
        )

        cls._bit_depth_value = CategorizedAttribute(
            16, UICategory.UI_CAT_OPTION, "Bit depth to represent all code values",
            ui_function_name="get_img_bit_depths"
        )

    @property
    def bit_depth_value(cls):
        """ The getter for the class attribute bit_depth_value

        :return: The value stored within the bit_depth_value CategorizedAttribute
        """
        return cls._bit_depth_value.value

    @bit_depth_value.setter
    def bit_depth_value(cls, value):
        """ Setter for the class attribute bit_depth_value

        :param value: the value we want to store within the bit_depth_value class attribute, inside the CategorizedAttribute
        """
        cls._bit_depth_value.value = value


class BitDepth(BasePatternGenerator, metaclass=BitDepthMeta):
    """ Allows us to store all the code values for a given bit depth and display this on the led wall.
    i.e. Store all the code values for 8-bit in an image container of say 12-bit.

    .. image:: ../_static/images/bit_depth.png
        :width: 400
        :alt: Example Bit Depth Pattern

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        bit_depth_value - The bit depth we want to represent all the code values for, this is not the bit depth of the
            image container.
    """
    method = _constants.GM_FIXED

    def __init__(self):
        super(BitDepth, self).__init__()

    @property
    def bit_depth_value(self):
        """ Gets the bit_depth_value of the generator stored within the class property

        :return: Returns the bit_depth_value
        """
        return self.__class__.bit_depth_value

    def __iter__(self):
        yield from super().__iter__()
        yield from {
            "bit_depth_value": self.bit_depth_value
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

        # Calculate the code values for the given bit depth
        image_bit_depth = cls.bit_depth_value
        min_code_value = 0
        max_code_value = (2 ** image_bit_depth)

        # How many rows of pixels do we need to display all the code values
        number_of_rows = int(math.ceil(max_code_value/led_wall.resolution_width))

        # We assume the whole height of the led wall for the length of the strip per code value
        # and each code value is a single pixel wide
        per_value_height = led_wall.resolution_height
        per_value_width = 1

        # If we can't fit each code value on a single line we need to do multiple rows and the height of each strip
        # calculated so all rows can fit on the led wall but fill as much of it as possible
        if number_of_rows > 1:
            per_value_height = int(led_wall.resolution_height/number_of_rows)
        else:
            # If we can fit all values on a single row, we make each of the strips wider so we fill the led wall as
            # much as possible
            per_value_width = int(led_wall.resolution_width/max_code_value)

        x_value = 0
        y_value = 0
        for code_value in range(max_code_value+1):
            norm_code_value = normalize(code_value, min_code_value, max_code_value)
            for x in range(per_value_width):
                for y in range(per_value_height):
                    led_wall_image.setpixel(
                        x + x_value,
                        y + y_value, 0,
                        [norm_code_value, norm_code_value, norm_code_value])

            x_value += per_value_width
            if x_value == led_wall.resolution_width:
                x_value = 0
                y_value += per_value_height

        # Write the image to disk and store the result
        cls.write_image_and_store_result(
            frame_num, full_file_path, led_wall.name, led_wall_image, results
        )

    def get_properties(self):
        """ Returns the names of the properties in the class with the property object containing all the data for that
            property

        :return: a dict of property name values with CategorizedAttribute values
        """
        results = super(BitDepth, self).get_properties()
        results.update({
            "bit_depth_value": self.__class__._bit_depth_value
        })
        return results
