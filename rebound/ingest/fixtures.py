import json
from pathlib import Path
from typing import Iterator


def load_fixture(path: Path) -> dict:
    return json.loads(Path(path).read_text(encoding="utf-8"))


def iter_fixtures(directory: Path) -> Iterator[dict]:
    for f in sorted(Path(directory).glob("*.json")):
        yield load_fixture(f)
