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

Module which holds the Data Range pattern generator
"""
import spg.utils.constants as _constants
from spg.PatternGenerators.basePatternGenerator import BasePatternGenerator, BasePatternGeneratorMeta
from spg.utils import imageUtils
from spg.utils.attributeUtils import CategorizedAttribute, UICategory
from spg.utils.imageUtils import oiio


def normalize(value, min_val, max_val):
    return (value - min_val) / (max_val - min_val)


class DataRangeMeta(BasePatternGeneratorMeta):
    """ The meta class which handles the class param access via properties

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        bit_depth_override - The bit depth for the images generated, as an override to the project settings
        input_transform - The color transform which describes our input color space we want to convert from
        enable_color_conversion - If we want to disable or enable color conversions via ocio, defaults to enabled
        use_pq_peak_luminance - Whether we want to display the legal and extended ranges based on SDR 0-1 range, or on
            a PQ 0-10000 nits range. By default we use the PQ values
    """
    def __init__(cls, *args, **kwargs):
        super().__init__(cls)
        cls._pattern_type = CategorizedAttribute(
            "DataRange", UICategory.UI_CAT_STRING, "The type of the pattern generator",
            readOnly=True
        )

        cls._enable_color_conversion = CategorizedAttribute(
            False, UICategory.UI_CAT_BOOLEAN, "Perform ocio color conversion",
        )

        cls._use_pq_peak_luminance = CategorizedAttribute(
            True, UICategory.UI_CAT_BOOLEAN, "Whether we want to evaluate in HDR using PQ or not",
        )

    @property
    def use_pq_peak_luminance(cls):
        """ The getter for the class attribute use_pq_peak_luminance

        :return: The value stored within the use_pq_peak_luminance CategorizedAttribute
        """
        return cls._use_pq_peak_luminance.value

    @use_pq_peak_luminance.setter
    def use_pq_peak_luminance(cls, value):
        """ Setter for the class attribute use_pq_peak_luminance

        :param value: the value we want to store within the use_pq_peak_luminance class attribute, inside the CategorizedAttribute
        """
        cls._use_pq_peak_luminance.value = value


class DataRange(BasePatternGenerator, metaclass=DataRangeMeta):
    """ A generator which creates a pattern to show the legal and extended ranges. We create and 2 squares which
    are the extended minumum (black) and the extended maximum (white), we then draw two inner squares which
        define the legal minimum and the legal maximum


    .. image:: ../_static/images/data_range.png
        :width: 400
        :alt: Example Data Range Pattern

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        bit_depth_override - The bit depth for the images generated, as an override to the project settings
        input_transform - The color transform which describes our input color space we want to convert from
        enable_color_conversion - If we want to disable or enable color conversions via ocio, defaults to enabled
        use_pq_peak_luminance - Whether we want to display the legal and extended ranges based on SDR 0-1 range, or on
            a PQ 0-10000 nits range. By default we use the PQ values
    """
    method = _constants.GM_FIXED

    def __init__(self):
        super(DataRange, self).__init__()

    def __iter__(self):
        yield from super().__iter__()
        yield from {
            "use_pq_peak_luminance": self.use_pq_peak_luminance,
        }.items()

    @property
    def use_pq_peak_luminance(self):
        """ Gets the use_pq_peak_luminance of the generator stored within the class property

        :return: Returns the use_pq_peak_luminance
        """
        return self.__class__.use_pq_peak_luminance

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

        image_bit_depth = cls.spg.project_settings.image_file_bit_depth

        minimum_legal, maximum_legal, minimum_extended, maximum_extended = imageUtils.get_legal_and_extended_values(
            led_wall.panel.brightness, image_bit_depth,
            use_pq_peak_luminance=bool(cls.use_pq_peak_luminance)
        )

        white_square_outer = cls.create_solid_color_image(
            int(led_wall.resolution_width * 0.5), led_wall.resolution_height,
            color=[maximum_extended, maximum_extended, maximum_extended]
        )

        white_square_inner = cls.create_solid_color_image(
            int(led_wall.resolution_width * 0.25), int(led_wall.resolution_height * 0.5),
            color=[maximum_legal, maximum_legal, maximum_legal]
        )

        black_square_outer = cls.create_solid_color_image(
            int(led_wall.resolution_width * 0.5), int(led_wall.resolution_height * 0.5),
            color=[minimum_extended, minimum_extended, minimum_extended]
        )

        black_square_inner = cls.create_solid_color_image(
            int(led_wall.resolution_width * 0.25), int(led_wall.resolution_height * 0.5),
            color=[minimum_legal, minimum_legal, minimum_legal]
        )

        oiio.ImageBufAlgo.paste(
            led_wall_image, 0, 0, 0, 0, white_square_outer, roi=oiio.ROI.All
        )

        oiio.ImageBufAlgo.paste(
            led_wall_image, int(led_wall.resolution_width * 0.125), int(led_wall.resolution_height * 0.25), 0, 0,
            white_square_inner, roi=oiio.ROI.All
        )

        oiio.ImageBufAlgo.paste(
            led_wall_image, int(led_wall.resolution_width * 0.5), 0, 0, 0, black_square_outer, roi=oiio.ROI.All
        )

        oiio.ImageBufAlgo.paste(
            led_wall_image, int(led_wall.resolution_width * 0.625), int(led_wall.resolution_height * 0.25), 0, 0,
            black_square_inner, roi=oiio.ROI.All
        )

        # We apply the transfer function only so that this gets reversed when the images are created with the colour
        # space conversion these values return to their original raw values in the file
        led_wall_image = imageUtils.apply_color_conversion(
            led_wall_image, led_wall.transfer_function_only_cs_name, led_wall.gamut_only_cs_name,
            cls.spg.project_settings.ocio_config_path
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
        results = super(DataRange, self).get_properties()
        results.update({
            "use_pq_peak_luminance": self.__class__._use_pq_peak_luminance,
        })
        return results
