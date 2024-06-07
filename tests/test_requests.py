import unittest
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple
from urllib.parse import urlencode, urlparse

import attr
import hypothesis.strategies as s
from hypothesis import given
from jsonschema_path import SchemaPath
from openapi_core.exceptions import OpenAPIError
from openapi_core.validation.request.datatypes import RequestParameters
from openapi_core.validation.request.exceptions import MissingRequiredParameter
from tornado.httpclient import HTTPRequest
from tornado.httputil import HTTPHeaders, HTTPServerRequest
from tornado.testing import AsyncHTTPTestCase
from tornado.web import Application, RequestHandler
from werkzeug.datastructures import ImmutableMultiDict

from tornado_openapi3 import RequestValidator, TornadoRequestFactory
from tornado_openapi3.requests import Request


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


field_name = s.text(
    s.characters(
        min_codepoint=33,
        max_codepoint=126,
        blacklist_categories=["Lu"],
        blacklist_characters=":",
    ),
    min_size=1,
)
field_value = s.text(
    s.characters(min_codepoint=0x20, max_codepoint=0x7E, blacklist_characters=" \r\n"),
    min_size=1,
)


def headers(min_size: int = 0) -> s.SearchStrategy[Dict[str, str]]:
    return s.dictionaries(field_name, field_value, min_size=min_size)


def query_parameters(min_size: int = 0) -> s.SearchStrategy[Dict[str, str]]:
    return s.dictionaries(field_name, field_value, min_size=min_size)


@s.composite
def parameters(
    draw: Callable[[Any], Any], min_headers: int = 0, min_query_parameters: int = 0
) -> Parameters:
    return Parameters(
        headers=draw(headers(min_size=min_headers)),
        query_parameters=draw(query_parameters(min_size=min_query_parameters)),
    )


class TestRequestFactory(unittest.TestCase):
    @given(
        s.one_of(
            s.tuples(s.just(""), s.just(dict())),
            s.tuples(s.just("http://example.com/foo"), query_parameters()),
        )
    )
    def test_http_request(self, opts: Tuple[str, Dict[str, str]]) -> None:
        url, parameters = opts
        request_url = f"{url}?{urlencode(parameters)}" if url else ""
        tornado_request = HTTPRequest(method="GET", url=request_url)
        expected = Request(
            full_url_pattern=url,
            method="get",
            parameters=RequestParameters(query=ImmutableMultiDict(parameters)),
            body=b"",
            content_type="application/x-www-form-urlencoded",
        )
        openapi_request = TornadoRequestFactory.create(tornado_request)
        self.assertEqual(attr.asdict(expected), attr.asdict(openapi_request))

    @given(
        s.one_of(
            s.tuples(s.just(""), s.just(dict())),
            s.tuples(s.just("http://example.com/foo"), query_parameters()),
        )
    )
    def test_http_server_request(self, opts: Tuple[str, Dict[str, str]]) -> None:
        url, parameters = opts
        request_url = f"{url}?{urlencode(parameters)}" if url else ""
        parsed = urlparse(request_url)
        tornado_request = HTTPServerRequest(
            method="GET",
            uri=f"{parsed.path}?{parsed.query}",
        )
        tornado_request.protocol = parsed.scheme
        tornado_request.host = parsed.netloc.split(":")[0]
        expected = Request(
            full_url_pattern=url,
            method="get",
            parameters=RequestParameters(
                query=ImmutableMultiDict(parameters), path={}, cookie={}
            ),
            body=b"",
            content_type="application/x-www-form-urlencoded",
        )
        openapi_request = TornadoRequestFactory.create(tornado_request)
        self.assertEqual(attr.asdict(expected), attr.asdict(openapi_request))


class TestRequest(AsyncHTTPTestCase):
    def setUp(self) -> None:
        super(TestRequest, self).setUp()
        self.request: Optional[HTTPServerRequest] = None

    def get_app(self) -> Application:
        testcase = self

        class TestHandler(RequestHandler):
            def get(self) -> None:
                nonlocal testcase
                testcase.request = self.request

        return Application([(r"/.*", TestHandler)])

    @given(parameters())
    def test_simple_request(self, parameters: Parameters) -> None:
        spec = SchemaPath.from_dict(
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
        assert self.request is not None
        validator.validate(self.request)

    @given(parameters(min_headers=1) | parameters(min_query_parameters=1))
    def test_simple_request_fails_without_parameters(
        self, parameters: Parameters
    ) -> None:
        spec = SchemaPath.from_dict(
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
        assert self.request is not None
        with self.assertRaises(MissingRequiredParameter):
            validator.validate(self.request)

    def test_url_parameters(self) -> None:
        spec = SchemaPath.from_dict(
            {
                "openapi": "3.0.0",
                "info": {"title": "Test specification", "version": "0.1"},
                "paths": {
                    "/{id}": {
                        "get": {
                            "parameters": [
                                {
                                    "name": "id",
                                    "in": "path",
                                    "required": True,
                                    "schema": {"type": "integer"},
                                }
                            ],
                            "responses": {"default": {"description": "Root response"}},
                        }
                    }
                },
            }
        )
        validator = RequestValidator(spec)
        self.fetch("/1234")
        assert self.request is not None
        validator.validate(self.request)

    def test_bad_url_parameters(self) -> None:
        spec = SchemaPath.from_dict(
            {
                "openapi": "3.0.0",
                "info": {"title": "Test specification", "version": "0.1"},
                "paths": {
                    "/{id}": {
                        "get": {
                            "parameters": [
                                {
                                    "name": "id",
                                    "in": "path",
                                    "required": True,
                                    "schema": {"type": "integer"},
                                }
                            ],
                            "responses": {"default": {"description": "Root response"}},
                        }
                    }
                },
            }
        )
        validator = RequestValidator(spec)
        self.fetch("/abcd")
        assert self.request is not None
        with self.assertRaises(OpenAPIError):
            validator.validate(self.request)
