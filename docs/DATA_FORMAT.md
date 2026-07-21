# Drill JSON format, schema version 1

Top-level fields:

- `id`: UUID
- `schema_version`: currently `1`
- `metadata`: flexible drill-information object; `name` is the only required UI field
- `created_at`, `modified_at`: UTC ISO-8601 timestamps
- `court`: active court options for compatibility
- `frames`: ordered frame documents
- `thumbnail`: reserved preview reference

Each frame contains `id`, `name`, independent `court` settings, and an ordered `objects` list.

Supported object types are `player`, `equipment`, `arrow`, `shape`, and `text`. Common transform properties are `x`, `y`, `width`, `height`, `rotation`, `scale`, `opacity`, `mirror`, and `locked`.

This format is deliberately independent of the rendering implementation.

