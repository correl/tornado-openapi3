from dataclasses import dataclass
from typing import Dict, List, Optional
import unittest
from urllib.parse import urlencode

import attr
from hypothesis import given
import hypothesis.strategies as s
from openapi_core import create_spec  # type: ignore
from openapi_core.schema.parameters.exceptions import (  # type: ignore
    MissingRequiredParameter,
)
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


@dataclass
class Parameters:
    headers: Dict[str, str]
    query_parameters: Dict[str, str]

    def as_openapi(self) -> List[dict]:
        headers = [
            {
                "name": name.lower(),
                "in": "header",
                "required": True,
                "schema": {"type": "string", "enum": [value]},
            }
            for name, value in self.headers.items()
        ]
        qargs = [
            {
                "name": name.lower(),
                "in": "query",
                "required": True,
                "schema": {"type": "string", "enum": [value]},
            }
            for name, value in self.query_parameters.items()
        ]
        return headers + qargs


@s.composite
def parameters(draw, min_headers=0, min_query_parameters=0) -> Parameters:
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
    return Parameters(
        headers=draw(s.dictionaries(field_name, field_value, min_size=min_headers)),
        query_parameters=draw(
            s.dictionaries(field_name, field_value, min_size=min_query_parameters)
        ),
    )


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
    def test_simple_request(self, parameters: Parameters) -> None:
        spec = create_spec(
            {
                "openapi": "3.0.0",
                "info": {"title": "Test specification", "version": "0.1"},
                "paths": {
                    "/": {
                        "get": {
                            "parameters": parameters.as_openapi(),
                            "responses": {"default": {"description": "Root response"}},
                        }
                    }
                },
            }
        )
        validator = RequestValidator(spec)
        self.fetch(
            "/?" + urlencode(parameters.query_parameters),
            headers=HTTPHeaders(parameters.headers),
        )
        result = validator.validate(self.request)
        result.raise_for_errors()

    @given(parameters(min_headers=1) | parameters(min_query_parameters=1))
    def test_simple_request_fails_without_parameters(
        self, parameters: Parameters
    ) -> None:
        spec = create_spec(
            {
                "openapi": "3.0.0",
                "info": {"title": "Test specification", "version": "0.1"},
                "paths": {
                    "/": {
                        "get": {
                            "parameters": parameters.as_openapi(),
                            "responses": {"default": {"description": "Root response"}},
                        }
                    }
                },
            }
        )
        validator = RequestValidator(spec)
        self.fetch("/")
        result = validator.validate(self.request)
        with self.assertRaises(MissingRequiredParameter):
            result.raise_for_errors()
