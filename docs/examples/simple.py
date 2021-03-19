import tornado.ioloop
import tornado.web
from tornado_openapi3.handler import OpenAPIRequestHandler


class MyRequestHandler(OpenAPIRequestHandler):
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


class RootHandler(MyRequestHandler):
    async def get(self):
        self.finish("Hello, World!")


if __name__ == "__main__":
    app = tornado.web.Application([(r"/", RootHandler)])
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
