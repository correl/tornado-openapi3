import unittest

from tornado_openapi3 import util


class TestMimetypeParsing(unittest.TestCase):
    def test_parameters_are_stripped(self) -> None:
        self.assertEqual("text/html", util.parse_mimetype("text/html; charset=utf-8"))

    def test_mimetype_is_lowercase(self) -> None:
        self.assertEqual("text/html", util.parse_mimetype("TEXT/HTML"))

    def test_type_suffix_is_preserved(self) -> None:
        self.assertEqual(
            "application/custom+json", util.parse_mimetype("application/custom+json")
        )
