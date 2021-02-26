import asyncio
import logging

from openapi_core import create_spec  # type: ignore
from openapi_core.exceptions import OpenAPIError  # type: ignore
from openapi_core.deserializing.exceptions import DeserializeError  # type: ignore
from openapi_core.schema.media_types.exceptions import (  # type: ignore
    InvalidContentType,
)
from openapi_core.templating.paths.exceptions import (  # type: ignore
    OperationNotFound,
    PathNotFound,
)
from openapi_core.unmarshalling.schemas.exceptions import ValidateError  # type: ignore
from openapi_core.validation.exceptions import InvalidSecurity  # type: ignore
import tornado.web

from tornado_openapi3.requests import RequestValidator

logger = logging.getLogger(__name__)


class OpenAPIRequestHandler(tornado.web.RequestHandler):
    spec: dict = {}
    custom_media_type_deserializers: dict = {}

    async def prepare(self) -> None:
        maybe_coro = super().prepare()
        if maybe_coro and asyncio.iscoroutine(maybe_coro):  # pragma: no cover
            await maybe_coro

        validator = RequestValidator(
            create_spec(self.spec),
            custom_media_type_deserializers=self.custom_media_type_deserializers,
        )
        result = validator.validate(self.request)
        try:
            result.raise_for_errors()
        except PathNotFound as e:
            self.on_openapi_error(404, e)
        except OperationNotFound as e:
            self.on_openapi_error(405, e)
        except (DeserializeError, ValidateError) as e:
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
        self.set_status(status_code)
        self.finish()
