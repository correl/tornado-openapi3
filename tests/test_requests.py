from typing import Optional
import unittest
from urllib.parse import urlencode

import attr
from hypothesis import given
import hypothesis.strategies as s
from openapi_core import create_spec  # type: ignore
from openapi_core.validation.request.datatypes import (  # type: ignore
    RequestParameters,
    OpenAPIRequest,
)
from openapi_core.validation.request.validators import RequestValidator  # type: ignore
from tornado.httputil import HTTPHeaders, HTTPServerRequest
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, RequestHandler
from werkzeug.datastructures import ImmutableMultiDict

from openapi3 import TornadoRequestFactory


@s.composite
def parameters(draw):
    field_name = s.text(
        s.characters(
            min_codepoint=33,
            max_codepoint=126,
            blacklist_categories=("Lu",),
            blacklist_characters=":",
        ),
        min_size=1,
    )
    field_value = s.text(
        s.characters(
            min_codepoint=0x20, max_codepoint=0x7E, blacklist_characters=" \r\n"
        ),
        min_size=1,
    )
    return {
        "headers": draw(s.dictionaries(field_name, field_value)),
        "query_parameters": draw(s.dictionaries(field_name, field_value)),
    }


class TestRequestFactory(unittest.TestCase):
    def test_request(self) -> None:
        tornado_request = HTTPServerRequest(
            method="GET", uri="http://example.com/foo?bar=baz"
        )
        expected = OpenAPIRequest(
            full_url_pattern="http://example.com/foo",
            method="get",
            parameters=RequestParameters(query=ImmutableMultiDict([("bar", "baz")])),
            body="",
            mimetype="text/html",
        )
        openapi_request = TornadoRequestFactory.create(tornado_request)
        self.assertEqual(attr.asdict(expected), attr.asdict(openapi_request))


class TestRequest(AsyncHTTPTestCase):
    def setUp(self) -> None:
        super(TestRequest, self).setUp()
        self.request: Optional[OpenAPIRequest] = None

    def get_app(self) -> Application:
        testcase = self

        class TestHandler(RequestHandler):
            def get(self) -> None:
                nonlocal testcase
                testcase.request = TornadoRequestFactory.create(self.request)

        return Application([(r"/", TestHandler)])

    @given(parameters())
    def test_simple_request(self, parameters) -> None:
        headers = [
            {
                "name": name.lower(),
                "in": "header",
                "required": True,
                "schema": {"type": "string", "enum": [value]},
            }
            for name, value in parameters["headers"].items()
        ]
        qargs = [
            {
                "name": name.lower(),
                "in": "query",
                "required": True,
                "schema": {"type": "string", "enum": [value]},
            }
            for name, value in parameters["query_parameters"].items()
        ]
        spec = create_spec(
            {
                "openapi": "3.0.0",
                "info": {"title": "Test specification", "version": "0.1"},
                "paths": {
                    "/": {
                        "get": {
                            "parameters": headers + qargs,
                            "responses": {"default": {"description": "Root response"}},
                        }
                    }
                },
            }
        )
        validator = RequestValidator(spec)
        self.fetch(
            "/?" + urlencode(parameters["query_parameters"]),
            headers=HTTPHeaders(parameters["headers"]),
        )
        result = validator.validate(self.request)
        result.raise_for_errors()
