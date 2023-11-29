"""
ledPanel.py
====================================
Holds the class definition for an LED Panel
"""
import json

from stageassets.utils import CategorizedAttribute, UICategory


class LEDPanel(object):
    """ Object to represent an LED panel

        Attributes:
            name - The name of the panel
            manufacturer - The name of the manufacturer
            panel_width - The width of the panel in mm
            panel_height - The height of the panel in mm
            panel_depth - The depth of the panel in mm
            pixel_pitch - The pixel pitch of the panel
            brightness - The max brightness of the panel in nits
            refresh_rate - The max refresh rate of the leds
            scan_rate - The scan rate of the panels
    """
    def __init__(self):

        self._name = CategorizedAttribute("", UICategory.UI_CAT_STRING, "The name of the panel")
        self._manufacturer = CategorizedAttribute("", UICategory.UI_CAT_STRING, "The name of the manufacturer")
        self._panel_width = CategorizedAttribute(0.0, UICategory.UI_CAT_FLOAT, "The width of the panel in mm")
        self._panel_height = CategorizedAttribute(0.0, UICategory.UI_CAT_FLOAT, "The height of the panel in mm")
        self._panel_depth = CategorizedAttribute(0.0, UICategory.UI_CAT_FLOAT, "The depth of the panel in mm")
        self._pixel_pitch = CategorizedAttribute(0.0, UICategory.UI_CAT_FLOAT, "The pixel pitch of the panel")
        self._brightness = CategorizedAttribute(0, UICategory.UI_CAT_INTEGER, "The max brightness of the panel in nits")
        self._refresh_rate = CategorizedAttribute(0, UICategory.UI_CAT_INTEGER, "The max refresh rate of the leds")
        self._scan_rate = CategorizedAttribute("", UICategory.UI_CAT_STRING, "The scan rate of the panels eg 1/8")

    @property
    def name(self):
        """ Getter for the name

        :return: Returns the name of the panels
        """
        return self._name.value

    @name.setter
    def name(self, value):
        """ Setter for the name categorized param

        :param value: the value we want to store in the name categorized param
        """
        self._name.value = value

    @property
    def manufacturer(self):
        """ Getter for the manufacturer

        :return: Returns the manufacturer of the panels
        """
        return self._manufacturer.value

    @manufacturer.setter
    def manufacturer(self, value):
        """ Setter for the manufacturer categorized param

        :param value: the value we want to store in the manufacturer categorized param
        """
        self._manufacturer.value = value

    @property
    def panel_width(self):
        """ Getter for the panel_width

        :return: Returns the panel_width of the panels
        """
        return self._panel_width.value

    @panel_width.setter
    def panel_width(self, value):
        """ Setter for the panel_width categorized param

        :param value: the value we want to store in the panel_width categorized param
        """
        self._panel_width.value = value

    @property
    def panel_height(self):
        """ Getter for the panel_height

        :return: Returns the panel_height of the panels
        """
        return self._panel_height.value

    @panel_height.setter
    def panel_height(self, value):
        """ Setter for the panel_height categorized param

        :param value: the value we want to store in the panel_height categorized param
        """
        self._panel_height.value = value

    @property
    def panel_depth(self):
        """ Getter for the panel_depth

        :return: Returns the panel_depth of the panels
        """
        return self._panel_depth.value

    @panel_depth.setter
    def panel_depth(self, value):
        """ Setter for the panel_depth categorized param

        :param value: the value we want to store in the panel_depth categorized param
        """
        self._panel_depth.value = value

    @property
    def pixel_pitch(self):
        """ Getter for the pixel_pitch

        :return: Returns the pixel_pitch of the panels
        """
        return self._pixel_pitch.value

    @pixel_pitch.setter
    def pixel_pitch(self, value):
        """ Setter for the pixel_pitch categorized param

        :param value: the value we want to store in the pixel_pitch categorized param
        """
        self._pixel_pitch.value = value

    @property
    def brightness(self):
        """ Getter for the brightness

        :return: Returns the brightness of the panels
        """
        return self._brightness.value

    @brightness.setter
    def brightness(self, value):
        """ Setter for the brightness categorized param

        :param value: the value we want to store in the brightness categorized param
        """
        self._brightness.value = value

    @property
    def refresh_rate(self):
        """ Getter for the refresh_rate

        :return: Returns the refresh_rate of the panels
        """
        return self._refresh_rate.value

    @refresh_rate.setter
    def refresh_rate(self, value):
        """ Setter for the refresh rate categorized param

        :param value: the value we want to store in the refresh rate categorized param
        """
        self._refresh_rate.value = value

    @property
    def scan_rate(self):
        """ Getter for the scan rate

        :return: Returns the scan rate of the panels
        """
        return self._scan_rate.value

    @scan_rate.setter
    def scan_rate(self, value):
        """ Setter for the scan rate categorized param

        :param value: the value we want to store in the scan rate categorized param
        """
        self._scan_rate.value = value

    @property
    def panel_resolution_width(self):
        """
        :return: The panel's resolution in pixels based on its physical width and its pixel pitch
        """
        return int(self.panel_width / self.pixel_pitch)

    @property
    def panel_resolution_height(self):
        """
        :return: The panel's resolution in pixels based on its physical width and its pixel pitch
        """
        return int(self.panel_height / self.pixel_pitch)

    def __iter__(self):
        yield from {
            "name": self.name,
            "manufacturer": self.manufacturer,
            "panel_width": self.panel_width,
            "panel_height": self.panel_height,
            "panel_depth": self.panel_depth,
            "pixel_pitch": self.pixel_pitch,
            "brightness": self.brightness,
            "refresh_rate": self.refresh_rate,
            "scan_rate": self.scan_rate
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
            "name": self._name,
            "manufacturer": self._manufacturer,
            "panel_width": self._panel_width,
            "panel_height": self._panel_height,
            "panel_depth": self._panel_depth,
            "pixel_pitch": self._pixel_pitch,
            "brightness": self._brightness,
            "refresh_rate": self._refresh_rate,
            "scan_rate": self._scan_rate
        }

    @staticmethod
    def from_json(json_dict):
        """ Returns an LEDPanel object from the given json data

        :param json_dict: the json dictionary representing the data for the LEDPanel
        :return: Returns an LEDPanel object from the given json data
        """
        panel = LEDPanel()
        for key, value in json_dict.items():
            if not hasattr(panel, key):
                raise AttributeError("LED Panel does not have attribute {0}".format(key))

            setattr(panel, key, value)
        return panel
