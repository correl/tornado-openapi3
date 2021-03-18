import datetime
import json
import re
import unittest.mock

from openapi_core.exceptions import OpenAPIError  # type: ignore
import tornado.httpclient  # type: ignore
import tornado.web  # type: ignore
import tornado.testing  # type: ignore

from tornado_openapi3.handler import OpenAPIRequestHandler


class USDateFormatter:
    def validate(self, value: str) -> bool:
        return bool(re.match(r"^\d{1,2}/\d{1,2}/\d{4}$", value))

    def unmarshal(self, value: str) -> datetime.date:
        return datetime.datetime.strptime(value, "%m/%d/%Y").date()


class ResourceHandler(OpenAPIRequestHandler):
    spec_dict = {
        "openapi": "3.0.0",
        "info": {
            "title": "Test API",
            "version": "1.0.0",
        },
        "components": {
            "schemas": {
                "resource": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "date": {"type": "string", "format": "usdate"},
                    },
                    "required": ["name"],
                },
            },
            "securitySchemes": {
                "basicAuth": {
                    "type": "http",
                    "scheme": "bearer",
                }
            },
        },
        "security": [{"basicAuth": []}],
        "paths": {
            "/resource": {
                "post": {
                    "requestBody": {
                        "required": True,
                        "content": {
                            "application/vnd.example.resource+json": {
                                "schema": {"$ref": "#/components/schemas/resource"},
                            }
                        },
                    },
                    "responses": {
                        "200": {
                            "description": "Success",
                            "content": {
                                "application/vnd.example.resource+json": {
                                    "schema": {"$ref": "#/components/schemas/resource"},
                                }
                            },
                        },
                        "401": {
                            "description": "Missing or invalid credentials",
                        },
                    },
                }
            }
        },
    }

    custom_formatters = {
        "usdate": USDateFormatter(),
    }

    custom_media_type_deserializers = {
        "application/vnd.example.resource+json": json.loads,
    }

    async def post(self) -> None:
        self.set_header("Content-Type", "application/vnd.example.resource+json")
        self.finish(
            json.dumps(
                {
                    "name": self.validated.body["name"],
                }
            )
        )


class DefaultSchemaTest(tornado.testing.AsyncHTTPTestCase):
    def get_app(self) -> tornado.web.Application:
        test = self

        class RequestHandler(OpenAPIRequestHandler):
            async def prepare(self) -> None:
                with test.assertRaises(NotImplementedError):
                    self.spec

            async def get(self) -> None:
                ...

        return tornado.web.Application(
            [
                (r"/", RequestHandler),
            ]
        )

    def test_schema_must_be_implemented(self) -> None:
        response = self.fetch("/")
        self.assertEqual(200, response.code)


class DefaultFormatters(tornado.testing.AsyncHTTPTestCase):
    def get_app(self) -> tornado.web.Application:
        test = self

        class RequestHandler(OpenAPIRequestHandler):
            async def prepare(self) -> None:
                test.assertEqual(dict(), self.custom_formatters)

            async def get(self) -> None:
                ...

        return tornado.web.Application(
            [
                (r"/", RequestHandler),
            ]
        )

    def test_schema_must_be_implemented(self) -> None:
        response = self.fetch("/")
        self.assertEqual(200, response.code)


class DefaultDeserializers(tornado.testing.AsyncHTTPTestCase):
    def get_app(self) -> tornado.web.Application:
        test = self

        class RequestHandler(OpenAPIRequestHandler):
            async def prepare(self) -> None:
                test.assertEqual(dict(), self.custom_media_type_deserializers)

            async def get(self) -> None:
                ...

        return tornado.web.Application(
            [
                (r"/", RequestHandler),
            ]
        )

    def test_schema_must_be_implemented(self) -> None:
        response = self.fetch("/")
        self.assertEqual(200, response.code)


class RequestHandlerTests(tornado.testing.AsyncHTTPTestCase):
    def get_app(self) -> tornado.web.Application:
        return tornado.web.Application(
            [
                (r"/resource", ResourceHandler),
                (r"/undocumented", ResourceHandler),
            ]
        )

    def test_invalid_operation(self) -> None:
        response = self.fetch("/resource")
        self.assertEqual(405, response.code)

    def test_bad_data(self) -> None:
        response = self.fetch(
            "/resource",
            method="POST",
            headers={
                "Authorization": "Bearer secret",
                "Content-Type": "application/vnd.example.resource+json",
            },
            body="asdf",
        )
        self.assertEqual(400, response.code)

    def test_missing_field(self) -> None:
        response = self.fetch(
            "/resource",
            method="POST",
            headers={
                "Authorization": "Bearer secret",
                "Content-Type": "application/vnd.example.resource+json",
            },
            body=json.dumps({}),
        )
        self.assertEqual(400, response.code)

    def test_missing_security(self) -> None:
        response = self.fetch(
            "/resource",
            method="POST",
            headers={
                "Content-Type": "application/vnd.example.resource+json",
            },
            body=json.dumps({"name": "Name"}),
        )
        self.assertEqual(401, response.code)

    def test_invalid_content_type(self) -> None:
        response = self.fetch(
            "/resource",
            method="POST",
            headers={
                "Authorization": "Bearer secret",
                "Content-Type": "application/json",
            },
            body=json.dumps({"name": "Name"}),
        )
        self.assertEqual(415, response.code)

    def test_undocumented_endpoint(self) -> None:
        response = self.fetch(
            "/undocumented",
            method="POST",
            headers={
                "Authorization": "Bearer secret",
                "Content-Type": "application/vnd.example.resource+json",
            },
            body=json.dumps({"name": "Name"}),
        )
        self.assertEqual(404, response.code)

    def test_format_error(self) -> None:
        response = self.fetch(
            "/resource",
            method="POST",
            headers={
                "Authorization": "Bearer secret",
                "Content-Type": "application/vnd.example.resource+json",
            },
            body=json.dumps({"name": "Name", "date": "2020.01.01"}),
        )
        self.assertEqual(400, response.code)

    def test_unexpected_openapi_error(self) -> None:
        with unittest.mock.patch(
            "openapi_core.validation.datatypes.BaseValidationResult.raise_for_errors",
            side_effect=OpenAPIError,
        ):
            response = self.fetch(
                "/resource",
                method="POST",
                headers={
                    "Authorization": "Bearer secret",
                    "Content-Type": "application/vnd.example.resource+json",
                },
                body=json.dumps({"name": "Name"}),
            )
        self.assertEqual(500, response.code)

    def test_success(self) -> None:
        response = self.fetch(
            "/resource",
            method="POST",
            headers={
                "Authorization": "Bearer secret",
                "Content-Type": "application/vnd.example.resource+json",
            },
            body=json.dumps({"name": "Name", "date": "01/01/2020"}),
        )
        self.assertEqual(200, response.code)
