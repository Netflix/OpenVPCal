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

Module which holds the Frame Count Sync pattern generator
"""
import spg.utils.imageUtils as _imageUtils
from spg.PatternGenerators.basePatternGenerator import BasePatternGenerator, BasePatternGeneratorMeta
from spg.utils import constants as _constants
from spg.utils.attributeUtils import CategorizedAttribute, UICategory
from spg.utils.imageUtils import oiio


class FrameCountSyncMeta(BasePatternGeneratorMeta):
    """ The meta class which handles the class param access via properties

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        bit_depth_override - The bit depth for the images generated, as an override to the project settings
        input_transform - The color transform which describes our input color space we want to convert from
        enable_color_conversion - If we want to disable or enable color conversions via ocio, defaults to enabled
        border_width - The width of the border of the panel in pixels
        border_color - The color of the border
    """
    def __init__(cls, *args, **kwargs):
        super().__init__(cls)
        cls._pattern_type = CategorizedAttribute(
            "Frame_Count_Sync", UICategory.UI_CAT_STRING, "The type of the pattern generator",
            readOnly=True
        )

        cls._border_width = CategorizedAttribute(
            1, UICategory.UI_CAT_INTEGER, "The width of the border",
        )

        cls._border_color = CategorizedAttribute(
            [1, 1, 1], UICategory.UI_CAT_COLOR, "The border color",
        )

    @property
    def border_width(cls):
        """ The getter for the class attribute border_width

        :return: The value stored within the border_width CategorizedAttribute
        """
        return cls._border_width.value

    @border_width.setter
    def border_width(cls, value):
        """ Setter for the class attribute border_width

        :param value: the value we want to store within the border_width class attribute, inside the CategorizedAttribute
        """
        cls._border_width.value = value

    @property
    def border_color(cls):
        """ The getter for the class attribute border_color

        :return: The value stored within the border_color CategorizedAttribute
        """
        return cls._border_color.value

    @border_color.setter
    def border_color(cls, value):
        """ Setter for the class attribute border_color

        :param value: the value we want to store within the border_color class attribute, inside the CategorizedAttribute
        """
        cls._border_color.value = value


class FrameCountSync(BasePatternGenerator, metaclass=FrameCountSyncMeta):
    """ A generator which creates frame count pattern. This generates a per panel square with a frame number in the
    centre. The frame number increments and loops through the shooting rate, ie 0-24, 0-30. etc

    If when this pattern is recorded in the camera we do not see all the numbers,
    we have a sync problem

    .. image:: ../_static/images/frame_count_sync.gif
        :width: 400
        :alt: Example Frame Count Sync Pattern

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        bit_depth_override - The bit depth for the images generated, as an override to the project settings
        input_transform - The color transform which describes our input color space we want to convert from
        enable_color_conversion - If we want to disable or enable color conversions via ocio, defaults to enabled
        border_width - The width of the border of the panel in pixels
        border_color - The color of the border
    """
    method = _constants.GM_PER_FRAME

    def __init__(self,):
        super(FrameCountSync, self).__init__()
        self.timecode_frame = 0

    @property
    def border_width(self):
        """ Gets the border_width of the generator stored within the class property

        :return: Returns the border_width
        """
        return self.__class__.border_width

    @property
    def border_color(self):
        """ Gets the border_color of the generator stored within the class property

        :return: Returns the border_color
        """
        return self.__class__.border_color

    def __iter__(self):
        yield from super().__iter__()
        yield from {
            "border_width": self.border_width,
            "border_color": self.border_color
        }.items()

    def sequence_start(self):
        """ When we start generating a new sequence we set the timecode frame to 0
        """
        self.timecode_frame = 0

    def frame_end(self):
        """ As we end each frame we increment the timecode_frame by 1 unless we need to reset this, if we reach
        our shooting rate
        """
        self.timecode_frame += 1
        if self.timecode_frame == self.spg.project_settings.frame_rate:
            self.timecode_frame = 0
        return

    @classmethod
    def generator(cls, frame, kwargs, results):
        """ The function which generates the actual image for the current frame

        :param frame: the frame number we are generating
        :param kwargs: a dictionary of arguments needed for this generator
        :param results: a dictionary to store the results cross thread
        """
        led_wall = kwargs.get("led_wall", None)
        if led_wall is None:
            raise ValueError("led_wall not found in kwargs")

        timecode_frame = kwargs.get("timecode_frame", None)
        if timecode_frame is None:
            raise ValueError("timecode_frame not found in kwargs")

        frame_num, full_file_path = cls.get_frame_num_and_file_path(frame, led_wall.name)

        led_wall_image = cls.create_solid_color_image(
            led_wall.resolution_width, led_wall.resolution_height
        )

        # We create an image for the resolution of our panel
        panel_image = cls.create_solid_color_image(
            led_wall.panel.panel_resolution_width,
            led_wall.panel.panel_resolution_height,
            color=led_wall.wall_default_color
        )

        # We add a border of given border width and color
        _imageUtils.add_border_to_image(
            panel_image, cls.border_width, border_color=cls.border_color)

        for panel_count_width in range(led_wall.panel_count_width):
            x_offset = led_wall.panel.panel_resolution_width * panel_count_width
            for panel_count_height in range(led_wall.panel_count_height):
                y_offset = led_wall.panel.panel_resolution_height * panel_count_height

                per_panel_image = panel_image.copy()
                # We add text to the centre of the image for the given timecode frame
                _imageUtils.add_text_to_image_centre(per_panel_image, str(timecode_frame))

                # We insert the panel image into the whole led wall image
                oiio.ImageBufAlgo.paste(
                    led_wall_image, x_offset, y_offset, 0, 0, per_panel_image, roi=oiio.ROI.All
                )

        # Write the image to disk and store the result
        cls.write_image_and_store_result(
            frame_num, full_file_path, led_wall.name, led_wall_image, results
        )

    def get_kwargs(self):
        """ We return the base arguments along with the custom data introduced and updated
            on a per frame bases

        :return: a dictionary of kwargs needed by the generator function
        """
        kwargs = super(FrameCountSync, self).get_kwargs()
        kwargs_local = {
            "timecode_frame": self.timecode_frame,
        }
        kwargs.update(kwargs_local)
        return kwargs

    def get_properties(self):
        """ Returns the names of the properties in the class with the property object containing all the data for that
            property

        :return: a dict of property name values with CategorizedAttribute values
        """
        results = super(FrameCountSync, self).get_properties()
        results.update({
            "border_width": self.__class__._border_width,
            "border_color": self.__class__._border_color
        })
        return results
