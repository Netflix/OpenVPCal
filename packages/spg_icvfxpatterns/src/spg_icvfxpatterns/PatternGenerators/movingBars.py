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

Module which holds the MovingBars pattern generator
"""
import math

import spg.utils.constants as _constants
from spg.PatternGenerators.basePatternGenerator import BasePatternGenerator, BasePatternGeneratorMeta
from spg.utils.attributeUtils import CategorizedAttribute, UICategory
from spg.utils.imageUtils import oiio


def normalize(value, min_val, max_val):
    return (value - min_val) / (max_val - min_val)


class MovingBarsMeta(BasePatternGeneratorMeta):
    """ The meta class which handles the class param access via properties

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        bit_depth_override - The bit depth for the images generated, as an override to the project settings
        input_transform - The color transform which describes our input color space we want to convert from
        enable_color_conversion - If we want to disable or enable color conversions via ocio, defaults to enabled
        bar_width - The width of the bar that moves
        bg_color - The color of the wall
        bar_color - The color of the bar

    """
    def __init__(cls, *args, **kwargs):
        super().__init__(cls)
        cls._pattern_type = CategorizedAttribute(
            "MovingBars", UICategory.UI_CAT_STRING, "The type of the pattern generator",
            readOnly=True
        )

        cls._bar_width = CategorizedAttribute(
            5, UICategory.UI_CAT_INTEGER, "The width of the bar (pixels)"
        )

        cls._bg_color = CategorizedAttribute(
            [0, 0, 0], UICategory.UI_CAT_COLOR, "The color of the wall"
        )

        cls._bar_color = CategorizedAttribute(
            [1, 1, 1], UICategory.UI_CAT_COLOR, "The color of the bar"
        )

    @property
    def bar_width(cls):
        """ The getter for the class attribute bar_width

        :return: The value stored within the bar_width CategorizedAttribute
        """
        return cls._bar_width.value

    @bar_width.setter
    def bar_width(cls, value):
        """ Setter for the class attribute limit

        :param value: the value we want to store within the bar_width class attribute, inside the CategorizedAttribute
        """
        cls._bar_width.value = value

    @property
    def bg_color(cls):
        """ The getter for the class attribute bg_color

        :return: The value stored within the bg_color CategorizedAttribute
        """
        return cls._bg_color.value

    @bg_color.setter
    def bg_color(cls, value):
        """ Setter for the class attribute bg_color

        :param value: the value we want to store within the bg_color class attribute, inside the CategorizedAttribute
        """
        cls._bg_color.value = value

    @property
    def bar_color(cls):
        """ The getter for the class attribute bar_color

        :return: The value stored within the bar_color CategorizedAttribute
        """
        return cls._bar_color.value

    @bar_color.setter
    def bar_color(cls, value):
        """ Setter for the class attribute bar_color

        :param value: the value we want to store within the bar_color class attribute, inside the CategorizedAttribute
        """
        cls._bar_color.value = value


class MovingBars(BasePatternGenerator, metaclass=MovingBarsMeta):
    """ Generates a sequence of images which cause a solid bar to move around across the led walls, in the order that
    they are organized on the stage. This allows us to test to ensure that as content moves at across panels, walls and
    processors we have no issues with sync, alignment, mappings etc

    .. image:: ../_static/images/moving_bars.gif
        :width: 400
        :alt: Example Color Patch Pattern

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        bit_depth_override - The bit depth for the images generated, as an override to the project settings
        input_transform - The color transform which describes our input color space we want to convert from
        enable_color_conversion - If we want to disable or enable color conversions via ocio, defaults to enabled
        bar_width - The width of the bar that moves
        bg_color - The color of the wall
        bar_color - The color of the bar
    """
    method = _constants.GM_PER_FRAME_STAGE

    def __init__(self):
        super(MovingBars, self).__init__()

    @property
    def bar_width(self):
        """ Gets the bar_width of the generator stored within the class property

        :return: Returns the limit
        """
        return self.__class__.bar_width

    @property
    def bg_color(self):
        """ Gets the bg_color of the generator stored within the class property

        :return: Returns the limit
        """
        return self.__class__.bg_color

    @property
    def bar_color(self):
        """ Gets the bar_color of the generator stored within the class property

        :return: Returns the limit
        """
        return self.__class__.bar_color

    def __iter__(self):
        yield from super().__iter__()
        yield from {
            "bar_width": self.bar_width,
            "bg_color": self.bg_color,
            "bar_color": self.bar_color,
        }.items()

    @classmethod
    def generator(cls, frame, kwargs, results):
        """ The method which creates the moving bars across the whole wall

        :param frame: the frame number we are generating
        :param kwargs: a dictionary of the arguments for the generator
        :param results: a dictionary to store the results
        """
        led_walls = kwargs.get("led_walls", None)
        if led_walls is None:
            raise ValueError("led_walls not found in kwargs")

        led_walls_order = cls.order_led_walls(led_walls)

        stage_resolution_width = 0
        stage_resolution_max_height = 0
        for led_wall in led_walls_order:
            stage_resolution_width += led_wall.resolution_width
            if led_wall.resolution_height > stage_resolution_max_height:
                stage_resolution_max_height = led_wall.resolution_height

        stage_image = cls.create_solid_color_image(
            stage_resolution_width, stage_resolution_max_height, color=cls.bg_color
        )

        per_pixel_steps = int(math.ceil(stage_resolution_width/cls.number_of_frames()))
        x_start = int(math.ceil(frame * per_pixel_steps))

        for pixel_width in range(cls.bar_width):
            line_x_pos = x_start + pixel_width
            if line_x_pos > stage_resolution_width:
                continue

            oiio.ImageBufAlgo.render_line(
                stage_image, line_x_pos, 0, line_x_pos, stage_resolution_max_height, color=cls.bar_color,
                skip_first_point=False
            )

        cls.split_stage_image_to_per_wall_images(frame, led_walls_order, results, stage_image)

    @classmethod
    def order_led_walls(cls, led_walls):
        """ Returns the led walls in the order they appear on the stage base on the led wall id

        :param led_walls: A list of led walls we are operating on

        :return: List of led walls in the order they appear on the stage
        """
        led_walls_order = []
        for led_wall in led_walls:
            led_walls_order.insert(led_wall.id, led_wall)
        return led_walls_order

    @classmethod
    def split_stage_image_to_per_wall_images(cls, frame, led_walls_ordered, results, stage_image):
        """ Takes in an image representing the whole stage, splits the image into images per wall
            and writes it to disk and stores the result

        :param frame: the frame number we are generating
        :param led_walls_ordered: the led_walls in the order they appear in the stage
        :param results: a dictionary to store the results cross thread
        :param stage_image: the stage image we want to split into per wall image sequences
        """
        previous_width = 0
        for led_wall in led_walls_ordered:
            roi = oiio.ROI(
                previous_width, previous_width + led_wall.resolution_width, 0, led_wall.resolution_height
            )

            led_wall_image = oiio.ImageBufAlgo.cut(stage_image, roi)

            frame_num, full_file_path = cls.get_frame_num_and_file_path(frame, led_wall.name)

            # Write the image to disk and store the result
            cls.write_image_and_store_result(
                frame_num, full_file_path, led_wall.name, led_wall_image, results
            )

            previous_width += led_wall.resolution_width

    def get_properties(self):
        """ Returns the names of the properties in the class with the property object containing all the data for that
            property

        :return: a dict of property name values with CategorizedAttribute values
        """
        results = super(MovingBars, self).get_properties()
        results.update({
            "bar_width": self.__class__._bar_width,
            "bg_color": self.__class__._bg_color,
            "bar_color": self.__class__._bar_color,
        })
        return results
