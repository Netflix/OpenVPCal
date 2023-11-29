"""
Module which holds the Alignment pattern generator
"""
import spg.utils.imageUtils as _imageUtils
from spg.PatternGenerators.basePatternGenerator import BasePatternGenerator, BasePatternGeneratorMeta
from spg.utils import constants as _constants
from spg.utils.attributeUtils import CategorizedAttribute, UICategory
from spg.utils.imageUtils import oiio


class AlignmentMeta(BasePatternGeneratorMeta):
    """ The meta class which handles the class param access via properties

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        bit_depth_override - The bit depth for the images generated, as an override to the project settings
        input_transform - The color transform which describes our input color space we want to convert from
        enable_color_conversion - If we want to disable or enable color conversions via ocio, defaults to enabled
        width - The width of the lines which make up the crosshair, defaults to 10 pixels
        line_border_width - The width of the border which edges the crosshair lines, defaults to 3 pixels
        line_color - The color of the lines which make up the crosshair, defaults to [1,0,0]
        line_border_color - The color of the border which edges the crosshair lines, defaults to [1,0,0]
        enable_border - Enables the panel border, defaults to True
        border_width - The width of the panel border in pixels, defaults to 1
        border_color - The color of the panel border, defaults to [0,0,1]

    """
    def __init__(cls, *args, **kwargs):
        super().__init__(cls)
        cls._pattern_type = CategorizedAttribute(
            "Alignment", UICategory.UI_CAT_STRING, "The type of the pattern generator",
            readOnly=True
        )

        cls._width = CategorizedAttribute(
            10, UICategory.UI_CAT_INTEGER, "Crosshair width (pixels)"
        )

        cls._line_border_width = CategorizedAttribute(
            3, UICategory.UI_CAT_INTEGER, "Crosshair border width (pixels)"
        )

        cls._line_color = CategorizedAttribute(
            [1, 1, 1], UICategory.UI_CAT_COLOR, "Crosshair color"
        )

        cls._line_border_color = CategorizedAttribute(
            [1, 0, 0], UICategory.UI_CAT_COLOR, "Crosshair border color"
        )

        cls._enable_border = CategorizedAttribute(
            False, UICategory.UI_CAT_BOOLEAN, "Enable panel border"
        )

        cls._border_width = CategorizedAttribute(
            1, UICategory.UI_CAT_INTEGER, "Panel border width (pixels))"
        )

        cls._border_color = CategorizedAttribute(
            [0, 0, 1], UICategory.UI_CAT_COLOR, "Panel border color"
        )

    @property
    def width(cls):
        """ The getter for the class attribute width

        :return: The value stored within the width CategorizedAttribute
        """
        return cls._width.value

    @width.setter
    def width(cls, value):
        """ Setter for the class attribute width

        :param value: the value we want to store within the width class attribute, inside the CategorizedAttribute
        """
        cls._width.value = value

    @property
    def line_border_width(cls):
        """ The getter for the class attribute line_border_width

        :return: The value stored within the line_border_width CategorizedAttribute
        """
        return cls._line_border_width.value

    @line_border_width.setter
    def line_border_width(cls, value):
        """ Setter for the class attribute line_border_width

        :param value: the value we want to store within the line_border_width class attribute, inside the CategorizedAttribute
        """
        cls._line_border_width.value = value

    @property
    def line_color(cls):
        """ The getter for the class attribute line_color

        :return: The value stored within the line_color CategorizedAttribute
        """
        return cls._line_color.value

    @line_color.setter
    def line_color(cls, value):
        """ Setter for the class attribute line_color

        :param value: the value we want to store within the line_color class attribute, inside the CategorizedAttribute
        """
        cls._line_color.value = value

    @property
    def line_border_color(cls):
        """ The getter for the class attribute line_border_color

        :return: The value stored within the line_border_color CategorizedAttribute
        """
        return cls._line_border_color.value

    @line_border_color.setter
    def line_border_color(cls, value):
        """ Setter for the class attribute line_border_color

        :param value: the value we want to store within the line_border_color class attribute, inside the CategorizedAttribute
        """
        cls._line_border_color.value = value

    @property
    def enable_border(cls):
        """ The getter for the class attribute enable_border

        :return: The value stored within the enable_border CategorizedAttribute
        """
        return cls._enable_border.value

    @enable_border.setter
    def enable_border(cls, value):
        """ Setter for the class attribute enable_border

        :param value: the value we want to store within the enable_border class attribute, inside the CategorizedAttribute
        """
        cls._enable_border.value = value

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


class Alignment(BasePatternGenerator, metaclass=AlignmentMeta):
    """ Generates a test pattern to check the alignment of the led panels and content mapping.
    Each panel is surrounded by a border which should map to the exact edge of each led panel.
    A crosshair runs from the middle of each panel and should line up with the adjacent panels.
    The crosshair is edged with it's a separate color to help identify miss-alignment & miss mapped pixels

    .. image:: ../_static/images/alignment.png
        :width: 400
        :alt: Example Alignment Pattern

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        bit_depth_override - The bit depth for the images generated, as an override to the project settings
        input_transform - The color transform which describes our input color space we want to convert from
        enable_color_conversion - If we want to disable or enable color conversions via ocio, defaults to enabled
        width - The width of the lines which make up the crosshair, defaults to 10 pixels
        line_border_width - The width of the border which edges the crosshair lines, defaults to 3 pixels
        line_color - The color of the lines which make up the crosshair, defaults to [1,0,0]
        line_border_color - The color of the border which edges the crosshair lines, defaults to [1,0,0]
        enable_border - Enables the panel border, defaults to True
        border_width - The width of the panel border in pixels, defaults to 1
        border_color - The color of the panel border, defaults to [0,0,1]
    """
    method = _constants.GM_FIXED

    def __init__(self):
        super(Alignment, self).__init__()

    @property
    def width(self):
        """ Gets the width of the generator stored within the class property

        :return: Returns the width
        """
        return self.__class__.width

    @property
    def line_border_width(self):
        """ Gets the line_border_width of the generator stored within the class property

        :return: Returns the line_border_width
        """
        return self.__class__.line_border_width

    @property
    def line_color(self):
        """ Gets the line_color of the generator stored within the class property

        :return: Returns the line_color
        """
        return self.__class__.line_color

    @property
    def line_border_color(self):
        """ Gets the line_border_color of the generator stored within the class property

        :return: Returns the line_border_color
        """
        return self.__class__.line_border_color

    @property
    def enable_border(self):
        """ Gets the enable_border of the generator stored within the class property

        :return: Returns the enable_border
        """
        return self.__class__.enable_border

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
            "width": self.width,
            "line_border_width": self.line_border_width,
            "line_color": self.line_color,
            "line_border_color": self.line_border_color,
            "enable_border": self.enable_border,
            "border_width": self.border_width,
            "border_color": self.border_color
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

        # We create an image for the resolution of our panel
        panel_image = cls.create_solid_color_image(
            led_wall.panel.panel_resolution_width,
            led_wall.panel.panel_resolution_height,
            color=[0, 0, 0]
        )

        # We add a border of given border width and color
        if cls.enable_border:
            _imageUtils.add_border_to_image(
                panel_image, cls.border_width, border_color=cls.border_color)

        centre_x_pos = int(led_wall.panel.panel_resolution_width * 0.5)
        centre_y_pos = int(led_wall.panel.panel_resolution_height * 0.5)

        half_width_border = int(cls.width + (cls.line_border_width * 2) * 0.5)
        half_width = int(cls.width * 0.5)

        start_border_range = 0 - half_width
        end_border_range = 0 + half_width

        start_range = 0 - half_width_border
        end_range = 0 + half_width_border

        for x in range(start_range, end_range, 1):
            color = cls.line_color
            if x < start_border_range or x > end_border_range:
                color = cls.line_border_color

            oiio.ImageBufAlgo.render_line(
                panel_image, centre_x_pos + x, 0, centre_x_pos + x, led_wall.panel.panel_resolution_height, color=color,
                skip_first_point=False
            )

        for y in range(start_range, end_range, 1):
            color = cls.line_color
            if y < start_border_range or y > end_border_range:
                color = cls.line_border_color

            oiio.ImageBufAlgo.render_line(
                panel_image, 0, centre_y_pos + y, int(led_wall.panel.panel_resolution_width * 0.5) - (cls.line_border_width * 2),
                centre_y_pos + y, color=color, skip_first_point=False
            )

            oiio.ImageBufAlgo.render_line(
                panel_image, int(led_wall.panel.panel_resolution_width * 0.5) + (cls.line_border_width * 2), centre_y_pos + y,
                led_wall.panel.panel_resolution_width,
                centre_y_pos + y, color=color, skip_first_point=False
            )

        for panel_count_width in range(led_wall.panel_count_width):
            x_offset = led_wall.panel.panel_resolution_width * panel_count_width
            for panel_count_height in range(led_wall.panel_count_height):
                y_offset = led_wall.panel.panel_resolution_height * panel_count_height

                per_panel_image = panel_image.copy()

                # We insert the panel image into the whole led wall image
                oiio.ImageBufAlgo.paste(
                    led_wall_image, x_offset, y_offset, 0, 0, per_panel_image, roi=oiio.ROI.All
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
        results = super(Alignment, self).get_properties()
        results.update({
            "width": self.__class__._width,
            "line_border_width": self.__class__._line_border_width,
            "line_color": self.__class__._line_color,
            "line_border_color": self.__class__._line_border_color,
            "enable_border": self.__class__._enable_border,
            "border_width": self.__class__._border_width,
            "border_color": self.__class__._border_color
        })
        return results
