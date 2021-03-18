import typing
import typing_extensions

Deserializer = typing.Callable[[typing.Union[bytes, str]], typing.Any]


class Formatter(typing_extensions.Protocol):
    """A type representing an OpenAPI formatter."""

    def validate(self, value: str) -> bool:  # pragma: no cover
        ...

    def unmarshal(self, value: str) -> typing.Any:  # pragma: no cover
        ...
