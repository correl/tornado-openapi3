import unittest

import tornado.web
from tornado_openapi3.testing import AsyncOpenAPITestCase


class RootHandler(tornado.web.RequestHandler):
    async def get(self):
        self.finish("Hello, World!")


class BaseTestCase(AsyncOpenAPITestCase):
    spec_dict = {
        "openapi": "3.0.0",
        "info": {
            "title": "Simple Example",
            "version": "1.0.0",
        },
        "paths": {
            "/": {
                "get": {
                    "responses": {
                        "200": {
                            "description": "Index",
                            "content": {
                                "text/html": {
                                    "schema": {"type": "string"},
                                }
                            },
                        }
                    }
                }
            }
        },
    }

    def get_app(self):
        return tornado.web.Application([(r"/", RootHandler)])

    def test_root_endpoint(self):
        response = self.fetch("/")
        self.assertEqual(200, response.code)
        self.assertEqual(b"Hello, World!", response.body)


if __name__ == "__main__":
    unittest.main()
