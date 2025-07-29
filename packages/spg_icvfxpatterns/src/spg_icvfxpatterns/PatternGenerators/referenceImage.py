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

Module which holds the ReferenceImage pattern generator
"""
import spg.utils.constants as _constants
from spg.PatternGenerators.basePatternGenerator import BasePatternGenerator, BasePatternGeneratorMeta
from spg.utils.attributeUtils import CategorizedAttribute, UICategory
from spg.utils.imageUtils import oiio


def normalize(value, min_val, max_val):
    return (value - min_val) / (max_val - min_val)


class ReferenceImageMeta(BasePatternGeneratorMeta):
    """ The meta class which handles the class param access via properties

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        bit_depth_override - The bit depth for the images generated, as an override to the project settings
        input_transform - The color transform which describes our input color space we want to convert from
        enable_color_conversion - If we want to disable or enable color conversions via ocio, defaults to enabled
        reference_filepath - Then filepath to the reference image we want to use
        image_scale - The target percentage of the wall we want to cover whilst respecting the aspect ratio of the image

    """
    def __init__(cls, *args, **kwargs):
        super().__init__(cls)
        cls._pattern_type = CategorizedAttribute(
            "ReferenceImage", UICategory.UI_CAT_STRING, "The type of the pattern generator",
            readOnly=True
        )

        cls._reference_filepath = CategorizedAttribute(
            "", UICategory.UI_CAT_UPLOAD, "Then filepath to the reference image we want to use"
        )

        cls._image_scale = CategorizedAttribute(
            0.5, UICategory.UI_CAT_FLOAT, "Percentage of the wall covered"
        )

    @property
    def reference_filepath(cls):
        """ The getter for the class attribute reference_filepath

        :return: The value stored within the reference_filepath CategorizedAttribute
        """
        return cls._reference_filepath.value

    @reference_filepath.setter
    def reference_filepath(cls, value):
        """ Setter for the class attribute reference_filepath

        :param value: the value we want to store within the reference_filepath class attribute, inside the CategorizedAttribute
        """
        cls._reference_filepath.value = value

    @property
    def image_scale(cls):
        """ The getter for the class attribute image_scale

        :return: The value stored within the image_scale CategorizedAttribute
        """
        return cls._image_scale.value

    @image_scale.setter
    def image_scale(cls, value):
        """ Setter for the class attribute image_scale

        :param value: the value we want to store within the image_scale class attribute, inside the CategorizedAttribute
        """
        cls._image_scale.value = value


class ReferenceImage(BasePatternGenerator, metaclass=ReferenceImageMeta):
    """ Takes a given image as a reference and fits it to the centre of the LED wall maintaining its aspect ratio.

    .. image:: ../_static/images/reference_image.png
        :width: 400
        :alt: Example Reference Image Pattern

    Attributes:
        name - The user given name for the generator, used to name the image sequence created
        pattern_type - The unique name used to identify the generator class
        sequence_length - The length of the sequence we want to generate in seconds
        bit_depth_override - The bit depth for the images generated, as an override to the project settings
        input_transform - The color transform which describes our input color space we want to convert from
        enable_color_conversion - If we want to disable or enable color conversions via ocio, defaults to enabled
        reference_filepath - Then filepath to the reference image we want to use
        image_scale - The target percentage of the wall we want to cover whilst respecting the aspect ratio of the image
    """
    method = _constants.GM_FIXED

    def __init__(self):
        super(ReferenceImage, self).__init__()

    @property
    def reference_filepath(self):
        """ Gets the reference_filepath of the generator stored within the class property

        :return: Returns the name
        """
        return self.__class__.reference_filepath

    @property
    def image_scale(self):
        """ Gets the image_scale of the generator stored within the class property

        :return: Returns the name
        """
        return self.__class__.image_scale

    def __iter__(self):
        yield from super().__iter__()
        yield from {
            "image_scale": self.image_scale,
            "reference_filepath": self.reference_filepath
        }.items()

    def get_properties(self):
        """ Returns the names of the properties in the class with the property object containing all the data for that
            property

        :return: a dict of property name values with CategorizedAttribute values
        """
        results = super(ReferenceImage, self).get_properties()
        results.update({
            "image_scale": self.__class__._image_scale,
            "reference_filepath": self.__class__._reference_filepath
        })
        return results

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

        wall_width_scaled = led_wall.resolution_width * cls.image_scale
        wall_height_scaled = led_wall.resolution_height * cls.image_scale

        reference_image = oiio.ImageBuf(cls.reference_filepath)
        spec = reference_image.spec()

        scale_factor = 1.0
        if reference_image.xmax > wall_width_scaled:
            scale_factor = reference_image.xmax/wall_width_scaled

        new_width = int(reference_image.xmax/scale_factor)
        new_height = int(reference_image.ymax / scale_factor)

        if new_height > wall_height_scaled:
            scale_factor = reference_image.ymax/wall_height_scaled
            new_width = int(reference_image.xmax / scale_factor)
            new_height = int(reference_image.ymax / scale_factor)

        y_centre = int((led_wall.resolution_height - new_height) * 0.5)
        x_centre = int((led_wall.resolution_width - new_width) * 0.5)
        resized = oiio.ImageBuf(oiio.ImageSpec(new_width, new_height, spec.nchannels, spec.format))
        oiio.ImageBufAlgo.resize(resized, reference_image)

        oiio.ImageBufAlgo.paste(
            led_wall_image, x_centre, y_centre, 0, 0, resized, roi=oiio.ROI.All
        )

        # Write the image to disk and store the result
        cls.write_image_and_store_result(
            frame_num, full_file_path, led_wall.name, led_wall_image, results
        )
