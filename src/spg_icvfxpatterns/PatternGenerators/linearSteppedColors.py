""" Module for the LinearSteppedColor Generator
"""
import spg.utils.imageUtils as _imageUtils
from spg.PatternGenerators.basePatternGenerator import BasePatternGenerator, BasePatternGeneratorMeta
from spg.utils import constants as _constants
from spg.utils.attributeUtils import CategorizedAttribute, UICategory
from spg.utils.imageUtils import oiio


class LinearSteppedColorsMeta(BasePatternGeneratorMeta):
    """ The meta class which handles the class param access via properties

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        bit_depth_override - The bit depth for the images generated, as an override to the project settings
        input_transform - The color transform which describes our input color space we want to convert from
        enable_color_conversion - If we want to disable or enable color conversions via ocio, defaults to enabled
        number_of_steps - The number of steps between the range we want to step
        font_size - The size of the display text displaying the nit values
        text_color - The color of the text displaying the nit values
        color_range_min - The minimum value for the color ranges defaults 0-1
        color_range_max - The maximum value for the color ranges defaults 0-1

    """
    def __init__(cls, *args, **kwargs):
        super().__init__(cls)
        cls._pattern_type = CategorizedAttribute(
            "LinearSteppedColors", UICategory.UI_CAT_STRING, "The type of the pattern generator",
            readOnly=True
        )

        cls._number_of_steps = CategorizedAttribute(
            50, UICategory.UI_CAT_INTEGER, "No. steps through range"
        )

        cls._font_size = CategorizedAttribute(
            10, UICategory.UI_CAT_INTEGER, "Size of the display text"
        )

        cls._text_color = CategorizedAttribute(
            [1, 1, 1], UICategory.UI_CAT_COLOR, "Color of the display text"
        )

        cls._color_range_min = CategorizedAttribute(
            0, UICategory.UI_CAT_INTEGER, "Min value for the color range"
        )

        cls._color_range_max = CategorizedAttribute(
            1, UICategory.UI_CAT_INTEGER, "Max value for the color range"
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

    @property
    def color_range_min(cls):
        """ The getter for the class attribute color_range_min

        :return: The value stored within the color_range_min CategorizedAttribute
        """
        return cls._color_range_min.value

    @color_range_min.setter
    def color_range_min(cls, value):
        """ Setter for the class attribute color_range_min

        :param value: the value we want to store within the color_range_min class attribute, inside the CategorizedAttribute
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

        :param value: the value we want to store within the color_range_max class attribute, inside the CategorizedAttribute
        """
        cls._color_range_max.value = value


class LinearSteppedColors(BasePatternGenerator, metaclass=LinearSteppedColorsMeta):
    """ Generates 3 color ramps divided into the number of given steps from Red To Cyan, Green To Magenta & Blue To
    Yellow. This allows us to verify if anything in the chain is clipping any specific range of colors.

    Defaults to 50 steps

    .. image:: ../_static/images/linear_stepped_color.png
        :width: 400
        :alt: Example Linear Stepped Color Pattern

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        number_of_steps - The number of steps between the range we want to step
        font_size - The size of the display text displaying the nit values
        text_color - The color of the text displaying the nit values
        color_range_min - The minimum value for the color ranges defaults 0-1
        color_range_max - The maximum value for the color ranges defaults 0-1

    """
    method = _constants.GM_FIXED

    def __init__(self):
        super(LinearSteppedColors, self).__init__()

    @property
    def number_of_steps(self):
        """ Gets the number_of_steps of the generator stored within the class property

        :return: Returns the number_of_steps
        """
        return self.__class__.number_of_steps

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

    def __iter__(self):
        yield from super().__iter__()
        yield from {
            "number_of_steps": self.number_of_steps,
            "font_size": self.font_size,
            "text_color": self.text_color,
            "color_range_min": self.color_range_min,
            "color_range_max": self.color_range_max
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

        min_value = cls.color_range_min
        max_value = cls.color_range_max

        value_range = max_value - min_value
        value_per_step = value_range/cls.number_of_steps
        height_per_step = int(led_wall.resolution_height/(cls.number_of_steps + 1))

        red_cyan = [1.0 * max_value, 0.0 * min_value, 0.0 * min_value]
        green_magenta = [0.0 * min_value, 1.0 * max_value, 0.0 * min_value]
        blue_yellow = [0.0 * min_value, 0.0 * min_value, 1.0 * max_value]

        for x in range(cls.number_of_steps + 1):
            step_value = (value_per_step * x) + min_value

            # Add In The Red/Cyan Ramp
            red_cyan_value = [
                red_cyan[0] - step_value, red_cyan[1] + step_value, red_cyan[2] + step_value
            ]
            cls.add_ramp_section(height_per_step, led_wall, led_wall_image, red_cyan_value, x, 0)

            # Add In The Green/Magenta Ramp
            green_magenta_value = [
                green_magenta[0] + step_value, green_magenta[1] - step_value, green_magenta[2] + step_value
            ]
            cls.add_ramp_section(height_per_step, led_wall, led_wall_image, green_magenta_value, x, 1)

            blue_yellow_value = [
                blue_yellow[0] + step_value, blue_yellow[1] + step_value, blue_yellow[2] - step_value
            ]

            # Add In The Blue/Yellow Ramp
            cls.add_ramp_section(height_per_step, led_wall, led_wall_image, blue_yellow_value, x, 2)

        # Write the image to disk and store the result
        cls.write_image_and_store_result(
            frame_num, full_file_path, led_wall.name, led_wall_image, results
        )

    @classmethod
    def add_ramp_section(cls, height_per_step, led_wall, led_wall_image, section_value, x, y):
        image_width = int(led_wall.resolution_width / 3.0)
        section_image = cls.create_solid_color_image(
            image_width, height_per_step,
            color=section_value
        )
        section_value_string = ",".join(["{:.{}f}".format(value, 3) for value in section_value])
        _imageUtils.add_text_to_image_centre(
            section_image, str(section_value_string), font_size=cls.font_size, text_color=cls.text_color)

        oiio.ImageBufAlgo.paste(
            led_wall_image, y * image_width, x * height_per_step, 0, 0, section_image, roi=oiio.ROI.All)

    def get_properties(self):
        """ Returns the names of the properties in the class with the property object containing all the data for that
            property

        :return: a dict of property name values with CategorizedAttribute values
        """
        results = super(LinearSteppedColors, self).get_properties()
        results.update({
            "number_of_steps": self.__class__._number_of_steps,
            "font_size": self.__class__._font_size,
            "text_color": self.__class__._text_color,
            "color_range_min": self.__class__._color_range_min,
            "color_range_max": self.__class__._color_range_max
        })
        return results
