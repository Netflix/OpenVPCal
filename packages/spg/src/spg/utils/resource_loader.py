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

