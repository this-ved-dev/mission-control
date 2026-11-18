"""Write openapi.json from the code, or with --check fail if the committed file has drifted."""

import json
import sys
import tempfile
from pathlib import Path

from app.config import Settings
from app.main import create_app

SPEC = Path(__file__).parent.parent / "openapi.json"


def current_spec() -> dict:
    with tempfile.TemporaryDirectory() as tmp:
        return create_app(Settings(llm="fake", db_path=f"{tmp}/spec.db")).openapi()


def main(argv: list[str]) -> int:
    text = json.dumps(current_spec(), indent=2) + "\n"
    if "--check" in argv:
        if not SPEC.exists() or SPEC.read_text() != text:
            print("openapi.json is out of date: run `uv run python -m app.export_openapi`")
            return 1
        print("openapi.json is up to date")
        return 0
    SPEC.write_text(text)
    print(f"wrote {SPEC.name}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
