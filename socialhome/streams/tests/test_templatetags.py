from collections import OrderedDict

from socialhome.streams.templatetags.json_context import json_context
from socialhome.tests.utils import SocialhomeTestCase


class TestJsonContext(SocialhomeTestCase):
    def test_empty_json_context_returns_falsy_values(self):
        self.assertEqual(json_context({}), "")
        self.assertEqual(json_context({"json_context": {}}), "")

    def test_serialisable_json_context_returns_script(self):
        target = json_context({
            "json_context": OrderedDict(sorted({
                "variable1": True,
                "variable2": "value2"
            }.items()))
        })
        result = '<script>window.context = {"variable1": true, "variable2": "value2"};</script>'
        self.assertEqual(target, result)

    def test_json_context_with_non_json_serializable_value(self):
        lambda_val = (lambda: "")
        target = json_context({
            "json_context": OrderedDict(sorted({
                "variable1": True,
                "variable2": lambda_val
            }.items()))
        })
        result = '<script>window.context = {"variable1": true, "variable2": "%s"};</script>' % lambda_val
        self.assertEqual(target, result)

    def test_json_context_unsafe_raises_with_non_json_serializable_value(self):
        self.assertRaises(TypeError, json_context, {"json_context": {"variable1": lambda: ""}}, True)
