""" Module which holds the LinearSteppedRamp Generator
"""
import spg.utils.imageUtils as _imageUtils
from spg.PatternGenerators.basePatternGenerator import BasePatternGenerator, BasePatternGeneratorMeta
from spg.utils import constants as _constants
from spg.utils.attributeUtils import CategorizedAttribute, UICategory
from spg.utils.imageUtils import oiio


class ExposureStopsMeta(BasePatternGeneratorMeta):
    """ The metaclass which handles the class param access via properties

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        number_of_stops - The number of exposure stops we want to generate
        font_size - The size of the display text displaying the nit values
        text_color - The color of the text displaying the nit values
        fit_to_wall - Fits the number of stops within the limits of the walls max brightness, defaults to true.
            Else when set to false, we only limit the values to the limits of PQ encoding at 10,000 nits

    """
    def __init__(cls, *args, **kwargs):
        super().__init__(cls)
        cls._pattern_type = CategorizedAttribute(
            "ExposureStops", UICategory.UI_CAT_STRING, "The type of the pattern generator",
            readOnly=True
        )

        cls._number_of_stops = CategorizedAttribute(
            7, UICategory.UI_CAT_INTEGER, "Number of exposure stops we want to generate patches for"
        )

        cls._font_size = CategorizedAttribute(
            50, UICategory.UI_CAT_INTEGER, "Size of display text"
        )

        cls._text_color = CategorizedAttribute(
            [1, 0, 0], UICategory.UI_CAT_COLOR, "Color of display text"
        )

        cls._fit_to_wall = CategorizedAttribute(
            True, UICategory.UI_CAT_BOOLEAN, "Fit the values below the max brightness of the led wall"
        )

    @property
    def number_of_stops(cls):
        """ The getter for the class attribute number_of_stops

        :return: The value stored within the number_of_stops CategorizedAttribute
        """
        return cls._number_of_stops.value

    @number_of_stops.setter
    def number_of_stops(cls, value):
        """ Setter for the class attribute number_of_stops

        :param value: the value we want to store within the number_of_stops class attribute, inside the CategorizedAttribute
        """
        cls._number_of_stops.value = value

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
    def fit_to_wall(cls):
        """ The getter for the class attribute fit_to_wall

        :return: The value stored within the fit_to_wall CategorizedAttribute
        """
        return cls._fit_to_wall.value

    @fit_to_wall.setter
    def fit_to_wall(cls, value):
        """ Setter for the class attribute fit_to_wall

        :param value: the value we want to store within the fit_to_wall class attribute, inside the CategorizedAttribute
        """
        cls._fit_to_wall.value = value


class ExposureStops(BasePatternGenerator, metaclass=ExposureStopsMeta):
    """ A generator which creates a number of sections which can be used to ensure that from our media server and camera,
    we are able to move up and down expsure stops in unison, and in a linear fashion. It also displays the stop value
    and actual nit values for the batch, basing these from the maximum nit value the led panel can support.

    Generator creates a patch
    TODO
    .. image:: ../_static/images/exposureStops.png
        :width: 400
        :alt: Example Exposure Stops

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        number_of_stops - The number of exposure stops we want to generate
        font_size - The size of the display text displaying the nit values
        text_color - The color of the text displaying the nit values
        fit_to_wall - Fits the number of stops within the limits of the walls max brightness, defaults to true.
            Else when set to false, we only limit the values to the limits of PQ encoding at 10,000 nits

    """
    method = _constants.GM_FIXED
    MAX_PQ = 100.0

    def __init__(self):
        super(ExposureStops, self).__init__()

    @property
    def number_of_stops(self):
        """ Gets the number_of_stops of the generator stored within the class property

        :return: Returns the number_of_stops
        """
        return self.__class__.number_of_stops

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
    def fit_to_wall(self):
        """ Gets the fit_to_wall of the generator stored within the class property

        :return: Returns the fit_to_wall
        """
        return self.__class__.fit_to_wall

    def __iter__(self):
        yield from super().__iter__()
        yield from {
            "number_of_stops": self.number_of_stops,
            "font_size": self.font_size,
            "text_color": self.text_color,
            "fit_to_wall": self.fit_to_wall
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

        exposures = [section for section in range(-cls.number_of_stops, cls.number_of_stops + 1)]
        number_of_grids = len(exposures)
        section_width = int(led_wall.resolution_width / number_of_grids)

        # If we fit to wall we find what the start point for the nit values must be in order to fit the number
        # of exposure stops onto the ledwall based on its max brightness
        if cls.fit_to_wall:
            start_brightness_max = led_wall.panel.brightness / (2 ** ((len(exposures) - 1) * 0.5))
        else:
            # If fit to wall is false, we find the 18% grey as the start point for the exposure
            start_brightness_max = (led_wall.panel.brightness * 0.01) * 18.0

        start_brightness_max_code_values = start_brightness_max * 0.01
        for section_count, exposure in enumerate(exposures):
            # For now we do nits per section but this needs to become stops
            # step_value = (10000 / number_of_grids) * section_count
            power_of = exposure
            step_value = start_brightness_max_code_values * (2 ** power_of)

            # We can not go above 10,000 nits, so we clamp to the max that PQ can encode
            if step_value > cls.MAX_PQ:
                step_value = cls.MAX_PQ

            step_image = cls.create_solid_color_image(
                section_width, led_wall.resolution_height,
                color=[step_value, step_value, step_value]
            )

            string_step_value = str(exposure)
            if exposure > 0:
                string_step_value = "+{0}".format(string_step_value)

            _imageUtils.add_text_to_image_centre(
                step_image, str(string_step_value), font_size=cls.font_size, text_color=cls.text_color,
                y_pos_override=led_wall.resolution_height - (led_wall.resolution_height/100) * 10)

            string_step_value = "{:.2f} NITS".format(step_value * 100)
            _imageUtils.add_text_to_image_centre(
                step_image, str(string_step_value), font_size=int(cls.font_size * 0.25), text_color=cls.text_color,
                y_pos_override=led_wall.resolution_height - (led_wall.resolution_height / 100) * 20
            )

            oiio.ImageBufAlgo.paste(
                led_wall_image, section_count * section_width, 0, 0, 0, step_image, roi=oiio.ROI.All)

            # start_section +=1
            section_count += 1

        top_left = led_wall_image.copy()
        top_left = oiio.ImageBufAlgo.resize(
            top_left, roi=oiio.ROI(
                0, int(led_wall.resolution_width * 0.5), 0,
                int(led_wall.resolution_height * 0.5), 0, 1, 0, 3
            )
        )

        bottom_left = top_left.copy()
        top_right = top_left.copy()
        bottom_right = top_left.copy()

        top_left = oiio.ImageBufAlgo.flop(top_left)
        top_right = oiio.ImageBufAlgo.flop(top_right)

        top_left = oiio.ImageBufAlgo.flip(top_left)
        top_right = oiio.ImageBufAlgo.flip(top_right)

        oiio.ImageBufAlgo.paste(
            led_wall_image, 0, 0, 0, 0, top_left, roi=oiio.ROI.All)

        oiio.ImageBufAlgo.paste(
            led_wall_image, 0, int(led_wall.resolution_height * 0.5), 0, 0, bottom_left, roi=oiio.ROI.All)

        oiio.ImageBufAlgo.paste(
            led_wall_image, int(led_wall.resolution_width * 0.5), 0, 0, 0, top_right, roi=oiio.ROI.All)

        oiio.ImageBufAlgo.paste(
            led_wall_image, int(led_wall.resolution_width * 0.5), int(led_wall.resolution_height * 0.5), 0, 0,
            bottom_right, roi=oiio.ROI.All)

        # Write the image to disk and store the result
        cls.write_image_and_store_result(
            frame_num, full_file_path, led_wall.name, led_wall_image, results
        )

    def get_properties(self):
        """ Returns the names of the properties in the class with the property object containing all the data for that
            property

        :return: a dict of property name values with CategorizedAttribute values
        """
        results = super(ExposureStops, self).get_properties()
        results.update({
            "number_of_stops": self.__class__._number_of_stops,
            "font_size": self.__class__._font_size,
            "text_color": self.__class__._text_color,
            "fit_to_wall": self.__class__._fit_to_wall
        })
        return results
