from dataclasses import dataclass
from typing import Any, Dict, Optional
import unittest

import attr

from hypothesis import given, settings  # type: ignore
import hypothesis.strategies as s  # type: ignore

from openapi_core import create_spec  # type: ignore
from openapi_core.validation.response.datatypes import OpenAPIResponse  # type: ignore
from tornado.httpclient import HTTPRequest, HTTPResponse  # type: ignore
from tornado.testing import AsyncHTTPTestCase  # type: ignore
from tornado.web import Application, RequestHandler  # type: ignore

from tornado_openapi3 import (
    ResponseValidator,
    TornadoResponseFactory,
)

settings(deadline=None)


@dataclass
class Responses:
    code: int
    headers: Dict[str, str]

    def as_openapi(self) -> Dict[str, Any]:
        return {
            str(self.code): {
                "description": "Response",
                "headers": {
                    name: {"schema": {"type": "string", "enum": [value]}}
                    for name, value in self.headers.items()
                },
            }
        }


@s.composite
def responses(draw, min_headers=0) -> Responses:
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
    return Responses(
        code=draw(s.sampled_from([200, 304, 400, 500])),
        headers=draw(s.dictionaries(field_name, field_value, min_size=min_headers)),
    )


class TestResponseFactory(unittest.TestCase):
    def test_response(self) -> None:
        tornado_request = HTTPRequest(url="http://example.com")
        tornado_response = HTTPResponse(request=tornado_request, code=200)
        expected = OpenAPIResponse(
            data="",
            status_code=200,
            mimetype="text/html",
        )
        openapi_response = TornadoResponseFactory.create(tornado_response)
        self.assertEqual(attr.asdict(expected), attr.asdict(openapi_response))


class ResponsesHandler(RequestHandler):
    responses: Optional[Responses] = None

    def get(self) -> None:
        if ResponsesHandler.responses:
            self.set_status(ResponsesHandler.responses.code)
            for name, value in ResponsesHandler.responses.headers.items():
                self.add_header(name, value)


class TestResponse(AsyncHTTPTestCase):
    def get_app(self) -> Application:
        return Application([(r"/.*", ResponsesHandler)])

    @given(responses())
    def test_simple_request(self, responses: Responses) -> None:
        spec = create_spec(
            {
                "openapi": "3.0.0",
                "info": {"title": "Test specification", "version": "0.1"},
                "paths": {
                    "/": {
                        "get": {
                            "responses": responses.as_openapi(),
                        }
                    }
                },
            }
        )
        ResponsesHandler.responses = responses
        validator = ResponseValidator(spec)
        response = self.fetch("/")
        result = validator.validate(response)
        result.raise_for_errors()
