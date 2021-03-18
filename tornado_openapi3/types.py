import typing
import typing_extensions

#: A type representing an OpenAPI deserializer.
Deserializer = typing.Callable[[typing.Union[bytes, str]], typing.Any]


class Formatter(typing_extensions.Protocol):
    """A type representing an OpenAPI formatter."""

    def validate(self, value: str) -> bool:  # pragma: no cover
        """Validate that the value matches the expected format."""
        ...

    def unmarshal(self, value: str) -> typing.Any:  # pragma: no cover
        """Translate the value into a Python object."""
        ...
