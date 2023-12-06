import unittest

import spg.PatternGenerators as _PatternGenerators
from spg.PatternGenerators.basePatternGenerator import BasePatternGenerator, BasePatternGeneratorMeta
from spg.utils.attributeUtils import CategorizedAttribute, UICategory


class ExampleGenValidMeta(BasePatternGeneratorMeta):
    def __init__(cls, *args, **kwargs):
        super().__init__(cls)
        cls._pattern_type = CategorizedAttribute(
            "ExampleGenValid", UICategory.UI_CAT_STRING, "The type of the pattern generator",
            readOnly=True
        )


class ExampleGenValid(BasePatternGenerator, metaclass=ExampleGenValidMeta):
    @classmethod
    def generator(cls, frame, kwargs, results):
        return


class ExampleGenInValidMeta(BasePatternGeneratorMeta):
    def __init__(cls, *args, **kwargs):
        super().__init__(cls)
        cls._pattern_type = CategorizedAttribute(
            "ExampleGenInValid", UICategory.UI_CAT_STRING, "The type of the pattern generator",
            readOnly=True
        )


class ExampleGenInValid(object, metaclass=ExampleGenInValidMeta):
    @classmethod
    def generator(cls, frame, kwargs, results):
        return


class TestRegister(unittest.TestCase):
    def test_register_valid_class(self):
        _PatternGenerators.register_pattern(ExampleGenValid)
        result = _PatternGenerators.get_pattern("ExampleGenValid")
        self.assertEqual(result, ExampleGenValid)

    def test_register_invalid_class(self):
        self.assertRaises(ValueError, _PatternGenerators.register_pattern, ExampleGenInValid)
