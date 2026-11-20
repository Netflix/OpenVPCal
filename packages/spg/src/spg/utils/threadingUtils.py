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
import os
import threading


def _default_max_workers() -> int:
    """ The number of frames we allow to be processed at the same time. Every in-flight frame holds full resolution
    image buffers, so this is bounded by the CPU count (capped at 8) to keep peak memory proportional to the
    machine rather than to the number of frames in the sequence. Override with the SPG_MAX_WORKERS env var.
    """
    env_value = os.environ.get("SPG_MAX_WORKERS")
    if env_value:
        try:
            return max(1, int(env_value))
        except ValueError:
            pass
    return max(1, min(os.cpu_count() or 1, 8))


# Shared by all ThreadedFunction instances so the limit applies across the whole process
_CONCURRENCY_LIMIT = threading.BoundedSemaphore(_default_max_workers())


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
        with _CONCURRENCY_LIMIT:
            self.func(self.frame, self.kwargs, self.results)
