import hypothesis.strategies as s
from werkzeug.datastructures import Headers

field_names = s.text(
    s.characters(
        min_codepoint=33,
        max_codepoint=126,
        blacklist_categories=["Lu"],
        blacklist_characters=":\r\n",
    ),
    min_size=1,
)

field_values = s.text(
    s.characters(min_codepoint=0x20, max_codepoint=0x7E, blacklist_characters="; \r\n"),
    min_size=1,
)

headers: s.SearchStrategy[Headers] = s.builds(
    Headers, s.lists(s.tuples(field_names, field_values))
)
