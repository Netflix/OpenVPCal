""" Module contains the Mapping and RasterMap class definitions

"""
import json

from stageassets.utils import CategorizedAttribute, UICategory


class Mapping(object):
    """ Object to represent a Mapping of an LED wall and its position in the raster map, we describe the top left corner
    of the led walls position within the raster, with the top left corner of the raster as 0,0 in UV space.

    Attributes:
        wall_name - The name of the led wall
        raster_u - The start position on the wall segment within the raster in U, in pixels
        raster_v - The end position on the wall segment within the raster in V, in pixels
        wall_segment_u_start - The position in U of the wall we want to start our segment from, pixels
        wall_segment_u_end - The position in U of the wall we want to end our segment at, pixels
        wall_segment_v_start - The position in V of the wall we want to start our segment from, pixels
        wall_segment_v_end - The position in V of the wall we want to end our segment at, pixels
        wall_segment_orientation - The orientation of the segment, degrees 0, 90, 180 etc. clockwise

    """
    def __init__(self):
        self._wall_name = CategorizedAttribute(
            "", UICategory.UI_CAT_OPTION, "The name of the led wall",
            ui_function_name="get_led_walls"
        )
        self._raster_u = CategorizedAttribute(
            0, UICategory.UI_CAT_INTEGER, "The start position on the wall segment within the raster in U, in pixels"
        )
        self._raster_v = CategorizedAttribute(
            0, UICategory.UI_CAT_INTEGER, "The end position on the wall segment within the raster in V, in pixels"
        )
        self._wall_segment_u_start = CategorizedAttribute(
            0, UICategory.UI_CAT_INTEGER, "The position in U of the wall we want to start our segment from, pixels"
        )
        self._wall_segment_u_end = CategorizedAttribute(
            0, UICategory.UI_CAT_INTEGER, "The position in U of the wall we want to end our segment at, pixels"
        )
        self._wall_segment_v_start = CategorizedAttribute(
            0, UICategory.UI_CAT_INTEGER, "The position in V of the wall we want to start our segment from, pixels"
        )
        self._wall_segment_v_end = CategorizedAttribute(
            0, UICategory.UI_CAT_INTEGER, "The position in V of the wall we want to end our segment at, pixels"
        )
        self._wall_segment_orientation = CategorizedAttribute(
            0, UICategory.UI_CAT_INTEGER, "The orientation of the segment, degrees 0, 90, 180 etc. clockwise"
        )

    def __iter__(self):
        yield from {
            "wall_name": self.wall_name,
            "raster_u": self.raster_u,
            "raster_v": self.raster_v,
            "wall_segment_u_start": self.wall_segment_u_start,
            "wall_segment_u_end": self.wall_segment_u_end,
            "wall_segment_v_start": self.wall_segment_v_start,
            "wall_segment_v_end": self.wall_segment_v_end,
            "wall_segment_orientation": self.wall_segment_orientation
        }.items()

    @property
    def wall_name(self):
        """ Getter for the wall_name

        :return: Returns the wall_name of the panels
        """
        return self._wall_name.value

    @wall_name.setter
    def wall_name(self, value):
        """ Setter for the wall_name categorized param

        :param value: the value we want to store in the wall_name categorized param
        """
        self._wall_name.value = value

    @property
    def raster_u(self):
        """ Getter for the raster_u

        :return: Returns the raster_u of the panels
        """
        return self._raster_u.value

    @raster_u.setter
    def raster_u(self, value):
        """ Setter for the raster_u categorized param

        :param value: the value we want to store in the raster_u categorized param
        """
        self._raster_u.value = value

    @property
    def raster_v(self):
        """ Getter for the raster_v

        :return: Returns the raster_v of the panels
        """
        return self._raster_v.value

    @raster_v.setter
    def raster_v(self, value):
        """ Setter for the raster_v categorized param

        :param value: the value we want to store in the raster_v categorized param
        """
        self._raster_v.value = value

    @property
    def wall_segment_u_start(self):
        """ Getter for the wall_segment_u_start

        :return: Returns the wall_segment_u_start of the panels
        """
        return self._wall_segment_u_start.value

    @wall_segment_u_start.setter
    def wall_segment_u_start(self, value):
        """ Setter for the wall_segment_u_start categorized param

        :param value: the value we want to store in the wall_segment_u_start categorized param
        """
        self._wall_segment_u_start.value = value

    @property
    def wall_segment_u_end(self):
        """ Getter for the wall_segment_u_end

        :return: Returns the wall_segment_u_end of the panels
        """
        return self._wall_segment_u_end.value

    @wall_segment_u_end.setter
    def wall_segment_u_end(self, value):
        """ Setter for the wall_segment_u_end categorized param

        :param value: the value we want to store in the wall_segment_u_end categorized param
        """
        self._wall_segment_u_end.value = value

    @property
    def wall_segment_v_start(self):
        """ Getter for the wall_segment_v_start

        :return: Returns the wall_segment_v_start of the panels
        """
        return self._wall_segment_v_start.value

    @wall_segment_v_start.setter
    def wall_segment_v_start(self, value):
        """ Setter for the wall_segment_v_start categorized param

        :param value: the value we want to store in the wall_segment_v_start categorized param
        """
        self._wall_segment_v_start.value = value

    @property
    def wall_segment_v_end(self):
        """ Getter for the wall_segment_v_end

        :return: Returns the wall_segment_v_end of the panels
        """
        return self._wall_segment_v_end.value

    @wall_segment_v_end.setter
    def wall_segment_v_end(self, value):
        """ Setter for the wall_segment_v_end categorized param

        :param value: the value we want to store in the wall_segment_v_end categorized param
        """
        self._wall_segment_v_end.value = value

    @property
    def wall_segment_orientation(self):
        """ Getter for the wall_segment_orientation

        :return: Returns the wall_segment_orientation of the panels
        """
        return self._wall_segment_orientation.value

    @wall_segment_orientation.setter
    def wall_segment_orientation(self, value):
        """ Setter for the wall_segment_orientation categorized param

        :param value: the value we want to store in the wall_segment_orientation categorized param
        """
        self._wall_segment_orientation.value = value

    def __str__(self):
        return json.dumps(dict(self), ensure_ascii=False)

    def __repr__(self):
        return self.__str__()

    def get_properties(self):
        return {
            "wall_name": self._wall_name,
            "raster_u": self._raster_u,
            "raster_v": self._raster_v,
            "wall_segment_u_start": self._wall_segment_u_start,
            "wall_segment_u_end": self._wall_segment_u_end,
            "wall_segment_v_start": self._wall_segment_v_start,
            "wall_segment_v_end": self._wall_segment_v_end,
            "wall_segment_orientation": self._wall_segment_orientation
        }

    def to_json(self):
        """
        :return: Returns the json data in a string format
        """
        return self.__str__()

    @staticmethod
    def from_json(json_dict):
        """ Returns a Mapping object from the given json data

        :param json_dict: the json dictionary representing the data for the RasterMap
        :return: Returns an Mapping object from the given json data
        """
        mapping = Mapping()
        if isinstance(json_dict, str):
            json_dict = json.loads(json_dict)

        for key, value in json_dict.items():
            if not hasattr(mapping, key):
                raise AttributeError("Mapping does not have attribute {0}".format(key))

            setattr(mapping, key, value)
        return mapping


class RasterMap(object):
    """ Object to represent a RasterMap

    Attributes:
        name - The name of the raster map, often the name of the processor
        resolution_width - The width of the image
        resolution_height - The height of the image
        mappings - A list of mappings between walls and their panel positions
    """
    def __init__(self):
        self._name = CategorizedAttribute(
            "", UICategory.UI_CAT_STRING, "The name of the raster map, often the name of the processor"
        )
        self._resolution_width = CategorizedAttribute(
            0, UICategory.UI_CAT_INTEGER, "The width of the image"
        )
        self._resolution_height = CategorizedAttribute(
            0, UICategory.UI_CAT_INTEGER, "The height of the image"
        )
        self._mappings = CategorizedAttribute(
            [], UICategory.UI_CAT_EXCLUDE, "A list of mappings between walls and their panel positions", multi=True
        )

    def __iter__(self):
        yield from {
            "name": self.name,
            "resolution_width": self.resolution_width,
            "resolution_height": self.resolution_height,
            "mappings": self.mappings
        }.items()

    @property
    def name(self):
        """ Getter for the name

        :return: Returns the name of the raster map
        """
        return self._name.value

    @name.setter
    def name(self, value):
        """ Setter for the name categorized param

        :param value: the value we want to store in the name categorized param
        """
        self._name.value = value

    @property
    def resolution_width(self):
        """ Getter for the resolution_width

        :return: Returns the resolution_width of the raster map
        """
        return self._resolution_width.value

    @resolution_width.setter
    def resolution_width(self, value):
        """ Setter for the resolution_width categorized param

        :param value: the value we want to store in the resolution_width categorized param
        """
        self._resolution_width.value = value

    @property
    def resolution_height(self):
        """ Getter for the resolution_height

        :return: Returns the resolution_height of the raster map
        """
        return self._resolution_height.value

    @resolution_height.setter
    def resolution_height(self, value):
        """ Setter for the resolution_height categorized param

        :param value: the value we want to store in the resolution_height categorized param
        """
        self._resolution_height.value = value

    @property
    def mappings(self):
        """ Getter for the mappings

        :return: Returns the mappings of the raster map
        """
        return self._mappings.value

    @mappings.setter
    def mappings(self, value):
        """ Setter for the mappings categorized param

        :param value: the value we want to store in the mappings categorized param
        """
        self._mappings.value = value

    def __str__(self):
        a = dict(self)
        a["mappings"] = [item.to_json() for item in a["mappings"]]
        return json.dumps(a, ensure_ascii=False)

    def __repr__(self):
        return self.__str__()

    def to_json(self):
        """
        :return: Returns the json data in a string format
        """
        return self.__str__()

    def get_properties(self):
        """ Returns the names of the properties in the class with the property object containing all the data for that
            property

        :return: a dict of property name values with CategorizedAttribute values
        """
        return {
            "name": self._name,
            "resolution_width": self._resolution_width,
            "resolution_height": self._resolution_height,
            "mappings": self._mappings
        }

    @staticmethod
    def from_json(json_dict):
        """ Returns an RasterMap object from the given json data

        :param json_dict: the json dictionary representing the data for the RasterMap
        :return: Returns an RasterMap object from the given json data
        """
        raster_map = RasterMap()
        for key, value in json_dict.items():
            if not hasattr(raster_map, key):
                raise AttributeError("Raster Map does not have attribute {0}".format(key))

            if key == "mappings":
                value = [Mapping.from_json(data) for data in value]
            setattr(raster_map, key, value)
        return raster_map
