import unittest

import attr
from openapi_core.validation.request.datatypes import (  # type: ignore
    RequestParameters,
    OpenAPIRequest,
)
from tornado.httputil import HTTPServerRequest
from werkzeug.datastructures import ImmutableMultiDict

from openapi3 import TornadoRequestFactory


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
