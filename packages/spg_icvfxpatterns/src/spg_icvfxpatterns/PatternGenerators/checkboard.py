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

Module which contains the checkerboard pattern generator
"""
import spg.utils.constants as _constants
from spg.PatternGenerators.basePatternGenerator import BasePatternGenerator, BasePatternGeneratorMeta
from spg.utils.attributeUtils import CategorizedAttribute, UICategory
from spg.utils.imageUtils import oiio


class CheckerboardMeta(BasePatternGeneratorMeta):
    """ The meta class which handles the class param access via properties

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        bit_depth_override - The bit depth for the images generated, as an override to the project settings
        input_transform - The color transform which describes our input color space we want to convert from
        enable_color_conversion - If we want to disable or enable color conversions via ocio, defaults to enabled
        panels_per_patch - The number of panels of the led wall per square of the checkerboard
        odd_color - The color of the odd numbered squares
        even_color - The color of the even numbered squares

    """
    def __init__(cls, *args, **kwargs):
        super().__init__(cls)
        cls._pattern_type = CategorizedAttribute(
            "Checkerboard", UICategory.UI_CAT_STRING, "The type of the pattern generator",
            readOnly=True
        )

        cls._panels_per_patch = CategorizedAttribute(
            1.0, UICategory.UI_CAT_FLOAT, "The type of the pattern generator"
        )

        cls._odd_color = CategorizedAttribute(
            [0, 0, 0], UICategory.UI_CAT_COLOR, "Color for odd numbered squares"
        )

        cls._even_color = CategorizedAttribute(
            [1, 1, 1], UICategory.UI_CAT_COLOR, "Color for even numbered squares"
        )

    @property
    def panels_per_patch(cls):
        """ The getter for the class attribute panels_per_patch

        :return: The value stored within the panels_per_patch CategorizedAttribute
        """
        return cls._panels_per_patch.value

    @panels_per_patch.setter
    def panels_per_patch(cls, value):
        """ Setter for the class attribute panels_per_patch

        :param value: the value we want to store within the panels_per_patch class attribute, inside the
        CategorizedAttribute
        """
        cls._panels_per_patch.value = value

    @property
    def odd_color(cls):
        """ The getter for the class attribute odd_color

        :return: The value stored within the odd_color CategorizedAttribute
        """
        return cls._odd_color.value

    @odd_color.setter
    def odd_color(cls, value):
        """ Setter for the class attribute odd_color

        :param value: the value we want to store within the odd_color class attribute, inside the CategorizedAttribute
        """
        cls._odd_color.value = value

    @property
    def even_color(cls):
        """ The getter for the class attribute even_color

        :return: The value stored within the even_color CategorizedAttribute
        """
        return cls._even_color.value

    @even_color.setter
    def even_color(cls, value):
        """ Setter for the class attribute even_color

        :param value: the value we want to store within the even_color class attribute, inside the CategorizedAttribute
        """
        cls._even_color.value = value


class Checkerboard(BasePatternGenerator, metaclass=CheckerboardMeta):
    """ A generator which creates checkerboard pattern which creates x number of patches per panel.
    Default one square covers, one entire panel.

    .. image:: ../_static/images/checkerboard.png
        :width: 400
        :alt: Example Checkerboard Pattern

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        bit_depth_override - The bit depth for the images generated, as an override to the project settings
        input_transform - The color transform which describes our input color space we want to convert from
        enable_color_conversion - If we want to disable or enable color conversions via ocio, defaults to enabled
        panels_per_patch - The number of panels of the led wall per square of the checkerboard
        odd_color - The color of the odd numbered squares
        even_color - The color of the even numbered squares

    """
    method = _constants.GM_FIXED

    def __init__(self):
        super(Checkerboard, self).__init__()

    @property
    def panels_per_patch(self):
        """ Gets the panels_per_patch of the generator stored within the class property

        :return: Returns the panels_per_patch
        """
        return self.__class__.panels_per_patch

    @property
    def odd_color(self):
        """ Gets the odd_color of the generator stored within the class property

        :return: Returns the odd_color
        """
        return self.__class__.odd_color

    @property
    def even_color(self):
        """ Gets the even_color of the generator stored within the class property

        :return: Returns the even_color
        """
        return self.__class__.even_color

    def __iter__(self):
        yield from super().__iter__()
        yield from {
            "panels_per_patch": self.panels_per_patch,
            "odd_color": self.odd_color,
            "even_color": self.even_color
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

        checker_width = int(led_wall.panel.panel_resolution_width * cls.panels_per_patch)
        checker_height = int(led_wall.panel.panel_resolution_height * cls.panels_per_patch)
        x_offset = led_wall.panel.panel_resolution_width if led_wall.id % 2 == 0 else 0

        oiio.ImageBufAlgo.checker(
            led_wall_image, checker_width, checker_height, 1, cls.odd_color, cls.even_color,
            xoffset=x_offset
        )

        # Write the image to disk and store the result
        cls.write_image_and_store_result(
            frame_num, full_file_path, led_wall.name, led_wall_image, results
        )

    def get_properties(self):
        """ Returns the names of the properties in the class with the property object containing all the data for that
            property

        :return: a dict of property name values with CategorizedAttribute values
        """
        results = super(Checkerboard, self).get_properties()
        results.update({
            "panels_per_patch": self.__class__._panels_per_patch,
            "odd_color": self.__class__._odd_color,
            "even_color": self.__class__._even_color
        })
        return results
