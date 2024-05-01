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

Module that contains the Frame class which is used to represent a frame within the sequence loader
"""
from typing import List

from open_vp_cal.imaging import imaging_utils


class Frame:
    """
    A class to represent a single frame of an image sequence.
    """

    def __init__(self, project_settings: "ProjectSettings"):
        """
        Initializes a Frame instance with frame number, file name, and image buffer set to None.
        """
        self._frame_num = None
        self._file_name = None
        self._image_buf = None
        self._project_settings = project_settings

    @property
    def frame_num(self) -> int:
        """
        Property for _frame_num.

        Returns:
        int: The frame number of this frame.
        """
        return self._frame_num

    @frame_num.setter
    def frame_num(self, value: int):
        """
        Setter for _frame_num.

        Parameters:
        value (int): The new frame number to set.
        """
        self._frame_num = value

    @property
    def file_name(self) -> str:
        """
        Property for _file_name.

        Returns:
        str: The file name of this frame.
        """
        return self._file_name

    @file_name.setter
    def file_name(self, value: str):
        """
        Setter for _file_name.

        Parameters:
        value (str): The new file name to set.
        """
        self._file_name = value

    @property
    def image_buf(self) -> "Oiio.ImageBuf":
        """
        Property for _image_buf.

        Returns:
        any: The image buffer of this frame.
        """
        return self._image_buf

    @image_buf.setter
    def image_buf(self, value):
        """
        Setter for _image_buf.

        Parameters:
            value (Oiio.ImageBuf): The new image buffer to set.
        """
        self._image_buf = value

    def __str__(self) -> str:
        """
        Generates a string representation of this Frame instance.

        Returns:
        str: A string representation of this Frame instance.
        """
        result = {
            "frame_num": self._frame_num,
            "file_name": self._file_name,
            "image_buf": str(self._image_buf)
        }
        return str(result)

    def extract_roi(self, roi: List) -> "Oiio.ImageBuf":
        """
        Extracts a region of interest from the image buffer of this frame.

        Parameters:
            roi (Oiio.ROI): The region of interest to extract from the image buffer.

        Returns:
            Oiio.ImageBuf: The extracted region of interest.
        """
        return imaging_utils.extract_roi(self._image_buf, roi)
