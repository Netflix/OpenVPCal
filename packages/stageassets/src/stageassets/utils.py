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
import json


class UICategory(object):
    UI_CAT_STRING = "string"
    UI_CAT_FLOAT = "float"
    UI_CAT_INTEGER = "int"
    UI_CAT_COLOR = "color"
    UI_CAT_OPTION = "option"
    UI_CAT_OPTION_FLOAT = "option_" + UI_CAT_FLOAT
    UI_CAT_OPTION_INTEGER = "option_" + UI_CAT_INTEGER
    UI_CAT_OBJECT = "object"
    UI_CAT_EXCLUDE = "exclude"
    UI_CAT_BOOLEAN = "boolean"
    UI_CAT_UPLOAD = "upload"


class CategorizedAttribute(object):
    """ We create a simple class to hold a value for a param, but can also contain additional data alongside it

        Attributes:
            value - The value for the attribute we want to store
            ui_category - The category in which the attribute should be grouped/exposed for UI purposes
            optional - Is the param optional or mandatory
            doc - A documentation or tool tip for the attribute
            multi - Whether the attribute is a multi attribute ie an array of ints, floats, color etc
    """
    def __init__(self, value, ui_category, doc, optional=False, readOnly=False, multi=False, ui_function_name=None):
        self.value = value
        self.ui_category = ui_category
        self.doc = doc
        self.optional = optional
        self.multi = multi
        self.readOnly = readOnly
        self.ui_function_name = ui_function_name

        option_categories = [
            UICategory.UI_CAT_OPTION_FLOAT, UICategory.UI_CAT_OPTION_INTEGER, UICategory.UI_CAT_OPTION
        ]
        if ui_category in option_categories:
            if not self.ui_function_name:
                raise ValueError(
                    "Need to provide a function name to populate the options field"
                )

    def to_json(self):
        return json.dumps(
            {
                "value": self.value,
                "ui_category": self.ui_category,
                "doc": self.doc,
                "optional": self.optional,
                "readOnly": self.readOnly,
                "multi": self.multi,
                "ui_function_name": self.ui_function_name
            }
        )
