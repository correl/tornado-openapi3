import logging
import pathlib

import tornado.ioloop
import tornado.web
from tornado_openapi3.handler import OpenAPIRequestHandler
import yaml

VERSION = "1.0.0"


class MyRequestHandler(OpenAPIRequestHandler):
    @property
    def spec_dict(self):
        return yaml.safe_load(self.render_string("openapi.yaml", version=VERSION))

    @property
    def spec(self):
        spec = getattr(self.application, "openapi_spec", None)
        if not spec:
            logging.info("Compiling OpenAPI spec")
            spec = super().spec
            setattr(self.application, "openapi_spec", spec)
        return spec


class RootHandler(MyRequestHandler):
    async def get(self):
        self.finish("Hello, World!")


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    example_root = pathlib.Path(__file__).parent
    app = tornado.web.Application(
        [(r"/", RootHandler)], template_path=str(example_root / "templates")
    )
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()
