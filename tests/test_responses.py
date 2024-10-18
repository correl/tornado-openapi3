import dataclasses
import io
import typing
import unittest


from hypothesis import given
import hypothesis.strategies as s

import openapi_core.protocols
import tornado.httpclient
import tornado.httputil
from werkzeug.datastructures import Headers

import tornado_openapi3.responses

from tests import common
import tornado_openapi3


@dataclasses.dataclass
class TestOpenAPIResponse:
    status_code: int
    headers: Headers
    content_type: str
    data: typing.Optional[bytes]


@s.composite
def openapi_responses(
    draw: typing.Callable[[typing.Any], typing.Any]
) -> openapi_core.protocols.Response:
    status_code = draw(s.integers(min_value=100, max_value=599))
    headers = draw(common.headers)
    content_type = draw(common.field_values)
    headers["Content-Type"] = content_type
    data = draw(s.binary())
    return TestOpenAPIResponse(
        status_code=status_code,
        headers=headers,
        content_type=content_type,
        data=data,
    )


class ResponseTests(unittest.TestCase):
    def assertOpenAPIResponsesEqual(
        self,
        value: openapi_core.protocols.Response,
        expected: openapi_core.protocols.Response,
    ) -> None:
        self.assertEqual(
            value.status_code, expected.status_code, "Status codes are equal"
        )
        self.assertEqual(value.headers, expected.headers, "Headers are equal")
        self.assertEqual(
            value.content_type, expected.content_type, "Content types are equal"
        )
        self.assertEqual(value.data, expected.data, "Bodies are equal")

    def openapi_to_tornado_response(
        self, response: TestOpenAPIResponse
    ) -> tornado.httpclient.HTTPResponse:
        headers = tornado.httputil.HTTPHeaders()
        for key, value in response.headers.items():
            headers.add(key, value)
        return tornado.httpclient.HTTPResponse(
            request=tornado.httpclient.HTTPRequest(""),
            code=response.status_code,
            headers=headers,
            buffer=io.BytesIO(response.data or b""),
        )

    @given(openapi_responses())
    def test_http_response_round_trip_conversion(
        self, response: TestOpenAPIResponse
    ) -> None:
        converted = tornado_openapi3.responses.TornadoOpenAPIResponse(
            self.openapi_to_tornado_response(response)
        )
        self.assertOpenAPIResponsesEqual(converted, response)
