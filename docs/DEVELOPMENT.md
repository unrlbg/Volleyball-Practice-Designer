# Development guide

## Environment

Python 3.11 or newer is required. The frontend has no build step and no online runtime dependency.

```powershell
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python -m uvicorn app.main:app --reload
```

Development URL: `http://127.0.0.1:8000`.

## Tests

```powershell
pytest -q
```

`pytest.ini` sends temporary test data to `.test-temp/` inside the repository and disables the persistent pytest cache. Every API test replaces `app.main.DATA` with a unique temporary directory before constructing the application. Tests never touch `data/drills` or `data/practices`.

## Validation

```powershell
python -m compileall -q app tests
node --check app\static\js\app.js
```

The Node command is optional for users; it is a development syntax check only.

## Application factory

`app.main.create_app()` creates fresh `JsonStore` instances for drills and practices and mounts `/static`. The module-level `app` is the Uvicorn entry point.

## Adding an object type

1. Add its label to the appropriate palette list in `app/static/js/app.js`.
2. Extend `renderObject` or the SVG graphic helper.
3. Store semantic object fields rather than serialized SVG.
4. Add persistence-contract and browser-interaction tests.
5. Update `docs/DATA_MODEL.md` and `docs/USER_GUIDE.md`.

## Schema evolution

Increment `schema_version` only with a documented migration strategy. Readers should remain tolerant of unknown metadata and object fields so new clients can extend the model safely.

## Independence rule

Never import, symlink, read, or write Volleyball Scout internals. Future integration must use an explicit public file format or optional API boundary.
