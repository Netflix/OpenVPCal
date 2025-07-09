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

This module contains the classes associated with loading image sequences into a cache, and allowing and east method
for iterating over the frames in the cache
"""
import re
import os
import threading
from typing import TYPE_CHECKING

from collections import OrderedDict

from open_vp_cal.core import constants
from open_vp_cal.framework.frame import Frame
from open_vp_cal.imaging import imaging_utils

if TYPE_CHECKING:
    from open_vp_cal.led_wall_settings import LedWallSettings


class FrameRangeException(IOError):
    """Base class for exceptions in this module."""


class SequenceLoader:
    """This class is designed to load image sequences."""

    def __init__(self, led_wall_settings: "LedWallSettings"):
        """Initializes a SequenceLoader instance."""
        self.led_wall_settings = led_wall_settings
        self.init()

    def init(self):
        self.cache = OrderedDict()
        self._current_frame = -1
        self._start_frame = -1
        self._end_frame = -1
        self.folder_path = None
        self.file_name = None
        self.padding = None
        self.file_type = constants.FileFormats.FF_EXR
        self.frames = []
        self.frame_class = Frame

    def reset(self):
        """Resets the SequenceLoader instance to its initial state. And clears anything cached
        in the led wall from previous runs"""
        self.init()
        self.led_wall_settings.clear()


    def set_start_frame(self, frame: int) -> bool:
        """
        Sets the start frame value only if it is different and indicates if it has updated or not

        Parameters:
        frame (int): The new frame number to set as the start frame.

        Returns:
        bool: True if the start frame was updated, False otherwise.
        """
        if self._start_frame != frame:
            self._start_frame = frame
            return True
        return False

    def set_end_frame(self, frame: int) -> bool:
        """
        Sets the end frame value only if it is different and indicates if it has updated or not

        Parameters:
        frame (int): The new frame number to set as the end frame.

        Returns:
        bool: True if the end frame was updated, False otherwise.
        """
        if self._end_frame != frame:
            self._end_frame = frame
            return True
        return False

    @property
    def start_frame(self) -> int:
        """
        Property for start_frame.
        """
        return self._start_frame

    @property
    def current_frame(self) -> int:
        """
        Property for current_frame.
        """
        return self._current_frame

    @property
    def end_frame(self) -> int:
        """
        Property for end_frame.
        """
        return self._end_frame

    def set_current_frame(self, frame: int) -> tuple[bool, Frame]:
        """
        Sets the current frame and loads it into the cache if it's not already there.
        It checks if the new frame value is different from the current one,
        if it is, it updates the current value and returns True.
        Otherwise, it returns False. Also, it returns the current frame.

        If the frame is out of the defined frame range, it raises a FrameRangeException.

        Parameters:
        frame (int): The frame number to set as the current frame.

        Returns:
        tuple[bool, Frame]: A tuple where the first element indicates whether the
        frame was changed (True if it was False otherwise), and the second element is the
        current Frame instance.
        """
        frame_changed = False
        if frame < self.start_frame or frame > self.end_frame:
            raise FrameRangeException(f"Frame:{frame} out of range {self.start_frame}-{self.end_frame}")

        if self.current_frame != frame:
            self._current_frame = frame
            frame_changed = True

        if frame not in self.cache:
            self.cache[frame] = self._load_frame(frame)

        return frame_changed, self.cache[frame]

    @staticmethod
    def detect_padding(filename: str) -> int:
        """Detect the amount of padding in a filename.

        Padding refers to adding zeros to the left of a number
        in the filename to maintain a consistent number of digits.

        Args:
            filename (str): The filename to check.

        Returns:
            int: The amount of padding in the filename.
        """
        # This regular expression pattern will find sequences of digits
        # directly after the '.' and before the file extension
        pattern = r'(?<=\.)\d+(?=\.\w+$)'

        # Find all sequences of digits in the filename
        matches = re.findall(pattern, filename)

        # If no sequence of digits is found, return 0
        if not matches:
            return 0

        # Return the length from the first sequence of digits found
        return len(matches[0])

    def load_sequence(self, folder_path: str) -> None:
        """
        Loads the image sequence from the provided folder path.

        Parameters:
        folder_path (str): The directory path containing the image sequence.

        """
        self.cache = OrderedDict()
        self.folder_path = folder_path
        files = [f for f in os.listdir(folder_path) if not f.startswith(".")]
        files.sort()
        file_extensions = list(set([os.path.splitext(f)[1] for f in files]))

        if len(file_extensions) > 1:
            raise IOError("More Than One File Extension Found In Sequence Folder")

        for ext in file_extensions:
            if ext not in constants.FileFormats.all_read():
                raise IOError(f"File Extension: .{ext}, not supported")

        if not files:
            raise IOError("Sequence Folder Does Not Contain Any Files")

        self.file_type = file_extensions[0]
        self.padding = self.detect_padding(files[0])
        self.file_name = files[0].split('.')[0]

        self.frames = [int(os.path.splitext(f)[0].split('.')[-1]) for f in files]

        if not self.frames:
            raise IOError("No frames found in the provided folder.")

        self.set_end_frame(max(self.frames))
        self.set_start_frame(min(self.frames))

        self._cache_frames()

        self.set_current_frame(self.start_frame)

    def get_frame(self, frame: int) -> Frame:
        """ Returns the frame from the cache.

        :param frame: The frame number to get
        :return: The frame we requested
        """
        if frame < self.start_frame or frame > self.end_frame:
            raise FrameRangeException(f"Frame:{frame} out of range {self.start_frame}-{self.end_frame}")

        if frame not in self.cache:
            self._load_and_cache(frame)
        return self.cache[frame]

    def _load_and_cache(self, frame: int) -> None:
        """ For the given frame, we load it and store it in the cache

        Args:
            frame: The frame number to load and cache
        """
        self.cache[frame] = self._load_frame(frame)

    def _cache_frames(self) -> None:
        """
        Loads frames into the cache.
        """

        threads = []
        cache_frames = 50
        if cache_frames > self.end_frame:
            cache_frames = self.end_frame

        for frame in range(self.start_frame, cache_frames + 1):
            if frame not in self.cache:
                self.cache[frame] = None
                thread = threading.Thread(target=self._load_and_cache, args=(frame,), daemon=True)
                thread.start()
                threads.append(thread)

        for thread in threads:
            thread.join()

    def _load_frame(self, frame_num: int) -> Frame:
        """
        Loads a specific frame from the disk.

        Parameters:
        frame_num (int): The number of the frame to load.

        Returns:
            Frame: The loaded frame.
        """
        full_file_name = f"{self.file_name}.{str(frame_num).zfill(self.padding)}{self.file_type}"
        full_file_path = os.path.join(self.folder_path, full_file_name)
        if not os.path.exists(full_file_path):
            raise IOError(f"File {full_file_path} does not exist.")

        frame = self.frame_class(self.led_wall_settings.project_settings)
        frame.frame_num = frame_num
        frame.file_name = full_file_name
        frame.image_buf = imaging_utils.load_image(full_file_path)
        return frame

    def __iter__(self):
        """Makes this class iterable.

        Returns:
        Iterator: The class instance itself.
        """
        return self

    def __next__(self) -> Frame:
        """
        Used to get the next frame in the sequence during iteration.

        Returns:
        Frame: The Frame object for the next in the sequence.
        Raises:
        StopIteration: If no more frames are available in the sequence.
        """
        try:
            _, result = self.set_current_frame(self.current_frame)
            self._current_frame += 1
            return result
        except FrameRangeException as exc:
            raise StopIteration from exc
