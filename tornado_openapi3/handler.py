import asyncio
import logging
import typing

import openapi_core
import openapi_core.validation.request.exceptions
from openapi_core.exceptions import OpenAPIError
from openapi_core.validation.request.exceptions import (
    RequestBodyValidationError,
    SecurityValidationError,
)
from openapi_core.templating.media_types.exceptions import (
    MediaTypeNotFound,
)
from openapi_core.templating.paths.exceptions import (
    OperationNotFound,
    PathNotFound,
)
import tornado.web

import tornado_openapi3.requests
import tornado_openapi3.types
from tornado_openapi3.types import Deserializer, Formatter

logger = logging.getLogger(__name__)


class OpenAPIRequestHandler(tornado.web.RequestHandler):
    """Base class for HTTP request handlers.

    A request handler extending :class:`tornado.web.RequestHandler` providing
    OpenAPI spec validation on incoming requests and translating errors into
    appropriate HTTP responses.

    """

    @property
    def spec_dict(self) -> dict:
        """The OpenAPI 3 specification

        Override this in your request handlers to load or define your OpenAPI 3
        spec.

        :rtype: dict

        """
        raise NotImplementedError()

    @property
    def spec(self) -> openapi_core.OpenAPI:
        """The OpenAPI 3 specification.

        Override this in your request handlers to customize how your OpenAPI 3
        spec is loaded and validated.

        :rtype: :class:`openapi_core.schema.specs.model.Spec`

        """
        config = openapi_core.Config(
            extra_format_unmarshallers={
                format: formatter.unmarshal
                for format, formatter in self.custom_formatters.items()
            },
            extra_format_validators={
                format: formatter.validate
                for format, formatter in self.custom_formatters.items()
            },
            extra_media_type_deserializers=self.custom_media_type_deserializers,
        )
        return openapi_core.OpenAPI.from_dict(self.spec_dict, config=config)

    @property
    def custom_formatters(self) -> typing.Dict[str, Formatter]:
        """A dictionary mapping value formats to formatter objects.

        If your schemas make use of format modifiers, you may specify them in
        this dictionary paired with a Formatter object that provides methods to
        validate values and unmarshal them into Python objects.

        :rtype: Mapping[str, :class:`~tornado_openapi3.types.Formatter`]

        """

        return dict()

    @property
    def custom_media_type_deserializers(self) -> typing.Dict[str, Deserializer]:
        """A dictionary mapping media types to deserializing functions.

        If your endpoints make use of content types beyond ``application/json``,
        you must add them to this dictionary with a deserializing method that
        converts the raw body (as ``bytes`` or ``str``) to Python objects.

        :rtype: Mapping[str, :attr:`~tornado_openapi3.types.Deserializer`]
        """
        return dict()

    async def prepare(self) -> None:
        """Called at the beginning of a request before *get/post/etc*.

        Performs OpenAPI validation of the incoming request. Problems
        encountered while validating the request are translated to HTTP error
        codes:

        +-----------------------------+----------+-------------------------------------+
        |OpenAPI Errors               |Error Code|Description                          |
        +-----------------------------+----------+-------------------------------------+
        |``PathNotFound``             |``404``   |Could not find the path for this     |
        |                             |          |request in the OpenAPI specification.|
        +-----------------------------+----------+-------------------------------------+
        |``OperationNotFound``        |``405``   |Could not find the operation         |
        |                             |          |specified for this request in the    |
        |                             |          |OpenAPI specification.               |
        +-----------------------------+----------+-------------------------------------+
        |``CastError``,               |``400``   |The message body could not be decoded|
        |``DeserializeError``,        |          |or did not validate against the      |
        |``MissingRequiredParameter``,|          |specified schema.                    |
        |``MissingRequestBody``,      |          |                                     |
        |``ValidateError``            |          |                                     |
        +-----------------------------+----------+-------------------------------------+
        |``InvalidSecurity``          |``401``   |Required authorization was missing   |
        |                             |          |from the request.                    |
        +-----------------------------+----------+-------------------------------------+
        |``MediaTypeNotFound``        |``415``   |The content type of the request did  |
        |                             |          |not match any of the types in the    |
        |                             |          |OpenAPI specification.               |
        +-----------------------------+----------+-------------------------------------+
        |Any other ``OpenAPIError``   |``500``   |An unexpected error occurred.        |
        +-----------------------------+----------+-------------------------------------+

        To provide content in these error requests, you may override
        :meth:`on_openapi_error`.

        """
        maybe_coro = super().prepare()
        if maybe_coro and asyncio.iscoroutine(maybe_coro):  # pragma: no cover
            await maybe_coro

        request = tornado_openapi3.requests.TornadoOpenAPIRequest(self.request)
        result = self.spec.unmarshal_request(request)
        try:
            result.raise_for_errors()
        except PathNotFound as e:
            self.on_openapi_error(404, e)
        except OperationNotFound as e:
            self.on_openapi_error(405, e)
        except RequestBodyValidationError as e:
            if isinstance(e.__cause__, MediaTypeNotFound):
                self.on_openapi_error(415, e)
            else:
                self.on_openapi_error(400, e)
        except SecurityValidationError as e:
            self.on_openapi_error(401, e)
        except OpenAPIError as e:  # pragma: no cover
            logger.exception("Unexpected validation failure")
            self.on_openapi_error(500, e)
        self.validated = result

    def on_openapi_error(self, status_code: int, error: OpenAPIError) -> None:
        """Sets an HTTP status code and finishes the request.

        By default, no content is returned. To provide more informative
        responses, you may override this method.

        """
        self.set_status(status_code)
        self.finish()
