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
import ctypes
import os
import sys
import threading

# Frame work is partly file I/O (reading and writing images), so running more frames than there are CPUs hides
# that latency. Measured on a 16 core machine, 2x cores recovered most of the unbounded speed at ~2/3 the memory.
WORKERS_PER_CPU = 2
# Float RGB image copies a single frame typically holds at once (source, converted, cropped, rotated, written)
FRAME_IMAGE_COPIES = 6
# The share of the memory available at start-up that concurrent frames may use
MEMORY_BUDGET_FRACTION = 0.6


def estimate_frame_bytes(width, height, channels=3):
    """ Rough peak memory a single in-flight frame needs for the given resolution

    :param width: image width in pixels
    :param height: image height in pixels
    :param channels: number of channels
    :return: estimated bytes
    """
    return int(width) * int(height) * channels * 4 * FRAME_IMAGE_COPIES


def available_memory_bytes():
    """ The memory currently available to this process using only the standard library, honouring container
    limits on Linux. Returns None when it cannot be determined, in which case only the CPU limit applies.
    """
    try:
        if sys.platform.startswith("linux"):
            available = None
            with open("/proc/meminfo", encoding="utf8") as meminfo:
                for line in meminfo:
                    if line.startswith("MemAvailable:"):
                        available = int(line.split()[1]) * 1024
                        break
            for limit_file in ("/sys/fs/cgroup/memory.max", "/sys/fs/cgroup/memory/memory.limit_in_bytes"):
                if os.path.exists(limit_file):
                    with open(limit_file, encoding="utf8") as limit:
                        value = limit.read().strip()
                    if value.isdigit() and int(value) < (1 << 60) and (available is None or int(value) < available):
                        available = int(value)
                    break
            return available
        if sys.platform == "win32":
            class _MemoryStatus(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("sullAvailExtendedVirtual", ctypes.c_ulonglong)]
            status = _MemoryStatus()
            status.dwLength = ctypes.sizeof(_MemoryStatus)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(status)):
                return int(status.ullAvailPhys)
            return None
        # macOS and other POSIX: total physical memory is the best stdlib figure
        return os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES")
    except (OSError, ValueError, AttributeError):
        return None


class ResourceGate:
    """ Limits concurrently running frames by CPU count and by an estimated memory budget, so that large machines
    run wide whilst small machines are not driven out of memory. A frame larger than the whole budget still runs,
    alone, so progress is always guaranteed.
    """

    def __init__(self, max_workers=None, memory_budget=None):
        self._condition = threading.Condition()
        self._active = 0
        self._used = 0
        self.max_workers = max_workers or self._env_int("SPG_MAX_WORKERS") or (os.cpu_count() or 1) * WORKERS_PER_CPU
        if memory_budget is None:
            budget_mb = self._env_int("SPG_MEMORY_BUDGET_MB")
            if budget_mb:
                memory_budget = budget_mb * 1024 * 1024
            else:
                available = available_memory_bytes()
                memory_budget = int(available * MEMORY_BUDGET_FRACTION) if available else None
        self.memory_budget = memory_budget

    @staticmethod
    def _env_int(name):
        try:
            return max(1, int(os.environ.get(name, "")))
        except ValueError:
            return None

    def _cost(self, memory_estimate):
        if not self.memory_budget:
            return 0
        return min(int(memory_estimate or 0), self.memory_budget)

    def acquire(self, memory_estimate=0):
        cost = self._cost(memory_estimate)
        with self._condition:
            while self._active >= self.max_workers or (
                    self._active > 0 and self._used + cost > (self.memory_budget or float("inf"))):
                self._condition.wait()
            self._active += 1
            self._used += cost
        return cost

    def release(self, cost):
        with self._condition:
            self._active -= 1
            self._used -= cost
            self._condition.notify_all()


# Shared by all ThreadedFunction instances so the limits apply across the whole process
_GATE = ResourceGate()


class ThreadedFunction(threading.Thread):
    """ Simple Thread class which handles the threaded execution of the given function

    """
    def __init__(self, func, frame, kwargs, results, memory_estimate=0):
        """ Constructor

        :param func: the function we want to execute
        :param frame: the frame number for the frame we are generating
        :param kwargs: a dictionary of kwargs to pass to the function
        :param results: a dictionary to store the results which is accessed cross thread
        :param memory_estimate: estimated peak bytes this frame needs, used to throttle concurrency
        """
        threading.Thread.__init__(self)
        self.memory_estimate = memory_estimate
        self.func = func
        self.frame = frame
        self.kwargs = kwargs
        self.results = results

    def run(self):
        """ Handles the execution of the thread
        """
        cost = _GATE.acquire(self.memory_estimate)
        try:
            self.func(self.frame, self.kwargs, self.results)
        finally:
            _GATE.release(cost)
