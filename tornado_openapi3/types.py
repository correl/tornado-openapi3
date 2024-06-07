import typing

#: A type representing an OpenAPI deserializer.
Deserializer = typing.Callable[[typing.Union[bytes]], typing.Any]
FormatValidator = typing.Callable[[str], bool]
