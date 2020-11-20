import itertools

from openapi_core.validation.request.datatypes import (  # type: ignore
    RequestParameters,
    OpenAPIRequest,
)
from tornado.httputil import HTTPServerRequest
from werkzeug.datastructures import ImmutableMultiDict, Headers


class TornadoRequestFactory:
    @classmethod
    def create(cls, request: HTTPServerRequest) -> OpenAPIRequest:
        if request.uri:
            path, _, _ = request.uri.partition("?")
        else:
            path = ""
        query_arguments: ImmutableMultiDict[str, str] = ImmutableMultiDict(
            itertools.chain(
                *[
                    [(k, v.decode("utf-8")) for v in vs]
                    for k, vs in request.query_arguments.items()
                ]
            )
        )
        return OpenAPIRequest(
            full_url_pattern=path,
            method=request.method.lower() if request.method else "get",
            parameters=RequestParameters(
                query=query_arguments, header=Headers(request.headers.get_all())
            ),
            body=request.body.decode("utf-8"),
            mimetype=request.headers.get(
                "Content-Type", "application/x-www-form-urlencoded"
            ),
        )
