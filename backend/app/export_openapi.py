import json
import sys

from app.main import create_app

if __name__ == "__main__":
    spec = create_app(db_path=":memory:", run_pipeline=False).openapi()
    with open(sys.argv[1], "w") as f:
        json.dump(spec, f, indent=2)
        f.write("\n")
