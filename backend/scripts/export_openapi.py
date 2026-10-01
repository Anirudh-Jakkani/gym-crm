"""Writes the OpenAPI spec so the frontend can generate its typed client."""

import json
import os
import sys
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.main import app  # noqa: E402

out = Path(sys.argv[1] if len(sys.argv) > 1 else "../frontend/openapi.json")
out.write_text(json.dumps(app.openapi(), indent=2))
print(f"Wrote {out}")
