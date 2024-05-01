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
"""
import importlib
import pkgutil

from spg.PatternGenerators.basePatternGenerator import BasePatternGenerator as _BasePatternGenerator

# Registration for each of the generators written
_patterns = {
    _BasePatternGenerator.pattern_type: _BasePatternGenerator,
}


def load_plugins():
    """ Looks for any pattern generator plugins which exist on the PYTHONPATH and registers each pattern generator
    into the SPG
    """
    discovered_plugins = {
        name: importlib.import_module(name)
        for finder, name, ispkg
        in pkgutil.iter_modules()
        if name.startswith('spg')
    }

    for plugin, module in discovered_plugins.items():
        try:
            importlib.import_module(plugin + ".PatternGenerators")
        except ModuleNotFoundError:
            print("Plugin: {0} Does Not Contain A Module Called PatternGenerators".format(plugin))
            continue

        for pattern_type, class_dec in module.PatternGenerators.get_patterns().items():
            register_pattern(class_dec)


def get_pattern(pattern_type):
    """ Returns the generator class for the given pattern_type

    :param pattern_type: the name of the pattern_type we want
    :return: Generator class
    """
    if pattern_type not in _patterns:
        raise KeyError("Invalid Pattern Name: " + pattern_type)
    return _patterns[pattern_type]


def register_pattern(class_object):
    """ Hook for third party libraries to develop and register their own generator without having to change the source
    of SPD

    :param class_object: the class object we want to register which inherits from BasePatternGenerator
    """
    if not issubclass(class_object, _BasePatternGenerator):
        raise ValueError("Class does not inherit from BasePatternGenerator")

    _patterns[class_object.pattern_type] = class_object


def get_patterns():
    """ Returns all of the patterns which are registered within the plugin
    """
    return _patterns
