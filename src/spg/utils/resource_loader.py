"""
The module is dedicated to the handling of accessing non python file resources from within the package.
"""
import importlib.resources


class ResourceLoader:
    """ Class which provides access to the resources which are stored in the resources
     folder within the installed package.

    """
    @staticmethod
    def _get_resource(filename: str) -> str:
        """ For the given filename, we return the absolute file path from within the installed package.

        Args:
            filename: the file name to get the absolute path for

        Returns: The absolute path to the file within the resources folder

        """
        with importlib.resources.path(
                "spg.resources", filename
        ) as config_path:
            return str(config_path)

    @classmethod
    def regular_font(cls) -> str:
        """

        Returns: The absolute path to the regular font

        """
        return cls._get_resource("Roboto-Regular.ttf")

    @classmethod
    def bold_font(cls) -> str:
        """

        Returns: The absolute path to the bold font

        """
        return cls._get_resource("Roboto-Bold.ttf")

