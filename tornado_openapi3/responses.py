from tornado.httpclient import HTTPResponse
from werkzeug.datastructures import Headers


class TornadoOpenAPIResponse:
    def __init__(self, response: HTTPResponse) -> None:
        self.status_code = response.code
        self.headers = Headers(response.headers.get_all())
        self.content_type = response.headers.get("Content-Type", "text/html")
        self.data = response.body


__all__ = ["TornadoOpenAPIResponse"]
