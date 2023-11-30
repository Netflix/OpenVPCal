"""
ledWall.py
====================================
Holds the class definition for an LED Wall
"""
import json

from stageassets.ledPanel import LEDPanel as _LEDPanel
from stageassets.utils import CategorizedAttribute, UICategory


class LEDWall(object):
    """ Defines an led wall of given name, panel, panel width and height

    Attributes:
        id - the ID number & the order of the wall on the stage from left to right
        name - the name of the led wall
        panel_name - the name of the panel which makes up the wall
        panel_count_width - the number of panels wide the wall is
        panel_count_height - the number of panels high the wall is
        wall_default_color - the default color for the wall to help id it
    """
    def __init__(self):
        self._id = CategorizedAttribute(
            0, UICategory.UI_CAT_INTEGER, "The ID number & the order of the wall on the stage from left to right"
        )

        self._name = CategorizedAttribute(
            "", UICategory.UI_CAT_STRING, "The name of the led wall"
        )

        self._panel_name = CategorizedAttribute(
            "", UICategory.UI_CAT_OPTION, "The name of the panels which makes up the wall",
            ui_function_name="get_led_panels"
        )

        self._panel_count_width = CategorizedAttribute(
            "", UICategory.UI_CAT_INTEGER, "The number of panels wide the wall is"
        )
        self._panel_count_height = CategorizedAttribute(
            "", UICategory.UI_CAT_INTEGER, "The number of panels high the wall is"
        )
        self._wall_default_color = CategorizedAttribute(
            [1, 0, 0], UICategory.UI_CAT_COLOR, "The default color for the wall to help id it"
        )

        self._panel = None

    @property
    def id(self):
        """ Getter for the id

        :return: Returns the id of the led wall
        """
        return self._id.value

    @id.setter
    def id(self, value):
        """ Setter for the name categorized param

        :param value: the value we want to store in the id categorized param
        """
        self._id.value = value

    @property
    def name(self):
        """ Getter for the name

        :return: Returns the name of the led wall
        """
        return self._name.value

    @name.setter
    def name(self, value):
        """ Setter for the name categorized param

        :param value: the value we want to store in the name categorized param
        """
        self._name.value = value

    @property
    def panel_name(self):
        """ Getter for the panel_name

        :return: Returns the panel_name of the led wall
        """
        return self._panel_name.value

    @panel_name.setter
    def panel_name(self, value):
        """ Setter for the panel_name categorized param

        :param value: the value we want to store in the panel_name categorized param
        """
        self._panel_name.value = value

    @property
    def panel_count_width(self):
        """ Getter for the panel_count_width

        :return: Returns the panel_count_width of the led wall
        """
        return self._panel_count_width.value

    @panel_count_width.setter
    def panel_count_width(self, value):
        """ Setter for the panel_count_width categorized param

        :param value: the value we want to store in the panel_count_width categorized param
        """
        self._panel_count_width.value = value

    @property
    def panel_count_height(self):
        """ Getter for the panel_count_height

        :return: Returns the panel_count_height of the led wall
        """
        return self._panel_count_height.value

    @panel_count_height.setter
    def panel_count_height(self, value):
        """ Setter for the panel_count_height categorized param

        :param value: the value we want to store in the panel_count_height categorized param
        """
        self._panel_count_height.value = value

    @property
    def wall_default_color(self):
        """ Getter for the wall_default_color

        :return: Returns the wall_default_color of the led wall
        """
        return self._wall_default_color.value

    @wall_default_color.setter
    def wall_default_color(self, value):
        """ Setter for the wall_default_color categorized param

        :param value: the value we want to store in the wall_default_color categorized param
        """
        self._wall_default_color.value = value

    @property
    def num_panels(self):
        """
        :return: The total number of panels
        """
        return self.panel_count_width * self.panel_count_height

    @property
    def resolution_width(self):
        """
        :return: The resolution width
        """
        return self.panel_count_width * self.panel.panel_resolution_width

    @property
    def resolution_height(self):
        """
        :return: The resolution height
        """
        return self.panel_count_height * self.panel.panel_resolution_height

    @property
    def wall_height(self):
        """

        :return: The flat height of the led wall panels in mm
        """
        return self.panel_count_height * self.panel.panel_height

    @property
    def wall_width(self):
        """

        :return: The flat width of the led wall panels in mm
        """
        return self.panel_count_width * self.panel.panel_width

    @property
    def panel(self):
        if not self._panel:
            raise ValueError("Panel Object Net Set Please Set Panel")
        return self._panel

    @panel.setter
    def panel(self, panel):
        if not isinstance(panel, _LEDPanel):
            raise TypeError("Attempting to set object which is not of type LedPanel")

        if panel.name != self.panel_name:
            raise ValueError("Attempting To Set Panel Of Incorrect Panel Type")

        self._panel = panel

    def __iter__(self):
        yield from {
            "id": self.id,
            "name": self.name,
            "panel_name": self.panel_name,
            "panel_count_width": self.panel_count_width,
            "panel_count_height": self.panel_count_height,
            "wall_default_color": self.wall_default_color
        }.items()

    def __str__(self):
        return json.dumps(dict(self), ensure_ascii=False)

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
            "id": self._id,
            "name": self._name,
            "panel_name": self._panel_name,
            "panel_count_width": self._panel_count_width,
            "panel_count_height": self._panel_count_height,
            "wall_default_color": self._wall_default_color
        }

    @staticmethod
    def from_json(json_dict):
        """ Returns an LEDWall object from the given json data

        :param json_dict: the json dictionary representing the data for the LEDWall
        :return: Returns an LEDWall object from the given json data
        """
        wall = LEDWall()
        for key, value in json_dict.items():
            if not hasattr(wall, key):
                raise AttributeError("LED Wall does not have attribute {0}".format(key))

            setattr(wall, key, value)
        return wall