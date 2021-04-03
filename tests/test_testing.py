import json

from openapi_core.schema.responses.exceptions import InvalidResponse  # type: ignore
import tornado.web  # type: ignore

from tornado_openapi3.handler import OpenAPIRequestHandler
from tornado_openapi3.testing import AsyncOpenAPITestCase


def spec(responses: dict = dict()) -> dict:
    if not responses:
        responses = {"200": {"description": "Success"}}
    return {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
        },
        "components": {
            "schemas": {
                "resource": {
                    "type": "object",
                    "properties": {"name": {"type": "string"}},
                    "required": ["name"],
                },
            },
        },
        "paths": {
            "/resource": {
                "get": {
                    "responses": responses,
                }
            }
        },
    }


class TestTestCase(AsyncOpenAPITestCase):
    def setUp(self) -> None:
        ...

    def tearDown(self) -> None:
        ...

    def test_schema_must_be_implemented(self) -> None:
        with self.assertRaises(NotImplementedError):
            self.spec

    def test_no_custom_media_type_deserializers(self) -> None:
        self.assertEqual(dict(), self.custom_media_type_deserializers)


class BaseTestCase(AsyncOpenAPITestCase):
    spec_dict = spec()
    custom_media_type_deserializers = {
        "application/vnd.example.resource+json": json.loads,
    }

    def get_app(self) -> tornado.web.Application:
        testcase = self

        class ResourceHandler(OpenAPIRequestHandler):
            spec = self.spec
            custom_media_type_deserializers = self.custom_media_type_deserializers

            async def get(self) -> None:
                await testcase.get(self)

        return tornado.web.Application([(r"/resource", ResourceHandler)])

    async def get(self, handler: tornado.web.RequestHandler) -> None:
        ...


class SuccessTests(BaseTestCase):
    spec_dict = spec(
        responses={
            "200": {
                "description": "Success",
                "content": {
                    "application/vnd.example.resource+json": {
                        "schema": {"$ref": "#/components/schemas/resource"}
                    }
                },
            }
        }
    )

    async def get(self, handler: tornado.web.RequestHandler) -> None:
        handler.set_header("Content-Type", "application/vnd.example.resource+json")
        handler.finish(json.dumps({"name": "Name"}))

    def test_success(self) -> None:
        response = self.fetch("/resource")
        self.assertEqual(200, response.code)


class IncorrectResponseTests(BaseTestCase):
    spec_dict = spec(responses={"200": {"description": "Success"}})

    async def get(self, handler: tornado.web.RequestHandler) -> None:
        handler.set_status(400)

    def test_unexpected_response_code(self) -> None:
        with self.assertRaises(InvalidResponse) as context:
            self.fetch("/resource")
        self.assertEqual("400", context.exception.http_status)

    def test_errors_not_raised_when_using_absolute_url(self) -> None:
        self.fetch(self.get_url("/resource"))


class RaiseErrorTests(BaseTestCase):
    spec_dict = spec(
        responses={
            "500": {
                "description": "An error has occurred.",
            }
        }
    )

    async def get(self, handler: tornado.web.RequestHandler) -> None:
        handler.set_status(500)

    def test_fetch_throws_error_on_expected_failure(self) -> None:
        with self.assertRaises(tornado.httpclient.HTTPError) as context:
            self.fetch("/resource", raise_error=True)
        self.assertEqual(500, context.exception.code)
