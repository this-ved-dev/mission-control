import json
import sys
import tempfile
from pathlib import Path

from app.main import create_app

if __name__ == "__main__":
    with tempfile.TemporaryDirectory() as tmp:
        spec = create_app(db_path=Path(tmp) / "spec.db", run_pipeline=False).openapi()
    with open(sys.argv[1], "w") as f:
        json.dump(spec, f, indent=2)
        f.write("\n")
