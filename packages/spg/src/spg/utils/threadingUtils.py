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

Contains some helper functions and classes for threading

"""
import threading


class ThreadedFunction(threading.Thread):
    """ Simple Thread class which handles the threaded execution of the given function

    """
    def __init__(self, func, frame, kwargs, results):
        """ Constructor

        :param func: the function we want to execute
        :param frame: the frame number for the frame we are generating
        :param kwargs: a dictionary of kwargs to pass to the function
        :param results: a dictionary to store the results which is accessed cross thread
        """
        threading.Thread.__init__(self)
        self.func = func
        self.frame = frame
        self.kwargs = kwargs
        self.results = results

    def run(self):
        """ Handles the execution of the thread
        """
        self.func(self.frame, self.kwargs, self.results)
