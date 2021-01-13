import ietfparse.headers


def parse_mimetype(content_type: str) -> str:
    parsed = ietfparse.headers.parse_content_type(content_type)
    return "{}/{}{}".format(
        parsed.content_type,
        parsed.content_subtype,
        "+{}".format(parsed.content_suffix) if parsed.content_suffix else "",
    )
