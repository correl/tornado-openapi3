import asyncio
import logging
from typing import Mapping

from openapi_core import create_spec  # type: ignore
from openapi_core.casting.schemas.exceptions import CastError  # type: ignore
from openapi_core.exceptions import OpenAPIError  # type: ignore
from openapi_core.deserializing.exceptions import DeserializeError  # type: ignore
from openapi_core.schema.specs.models import Spec  # type: ignore
from openapi_core.schema.media_types.exceptions import (  # type: ignore
    InvalidContentType,
)
from openapi_core.schema.parameters.exceptions import (  # type: ignore
    MissingRequiredParameter,
)
from openapi_core.schema.request_bodies.exceptions import (  # type: ignore
    MissingRequestBody,
)
from openapi_core.templating.paths.exceptions import (  # type: ignore
    OperationNotFound,
    PathNotFound,
)
from openapi_core.unmarshalling.schemas.exceptions import ValidateError  # type: ignore
from openapi_core.validation.exceptions import InvalidSecurity  # type: ignore
import tornado.web  # type: ignore

from tornado_openapi3.requests import RequestValidator
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
    def spec(self) -> Spec:
        """The OpenAPI 3 specification.

        Override this in your request handlers to customize how your OpenAPI 3
        spec is loaded and validated.

        :rtype: :class:`openapi_core.schema.specs.model.Spec`

        """
        return create_spec(self.spec_dict, validate_spec=False)

    @property
    def custom_formatters(self) -> Mapping[str, Formatter]:
        """A dictionary mapping value formats to formatter objects.

        If your schemas make use of format modifiers, you may specify them in
        this dictionary paired with a Formatter object that provides methods to
        validate values and unmarshal them into Python objects.

        :rtype: Mapping[str, :class:`~tornado_openapi3.types.Formatter`]

        """

        return dict()

    @property
    def custom_media_type_deserializers(self) -> Mapping[str, Deserializer]:
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
        |``InvalidContentType``       |``415``   |The content type of the request did  |
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

        validator = RequestValidator(
            self.spec,
            custom_formatters=self.custom_formatters,
            custom_media_type_deserializers=self.custom_media_type_deserializers,
        )
        result = validator.validate(self.request)
        try:
            result.raise_for_errors()
        except PathNotFound as e:
            self.on_openapi_error(404, e)
        except OperationNotFound as e:
            self.on_openapi_error(405, e)
        except (
            CastError,
            DeserializeError,
            MissingRequiredParameter,
            MissingRequestBody,
            ValidateError,
        ) as e:
            self.on_openapi_error(400, e)
        except InvalidSecurity as e:
            self.on_openapi_error(401, e)
        except InvalidContentType as e:
            self.on_openapi_error(415, e)
        except OpenAPIError as e:
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
