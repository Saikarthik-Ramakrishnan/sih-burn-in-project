"""Export the OpenAPI document so the frontend can generate types offline.

Usage (from the repository root):

    .venv/Scripts/python.exe scripts/export_openapi.py

Writes docs/backend/openapi.json. The document is produced from the live
FastAPI app, so it can never drift from the running service.
"""

from __future__ import annotations

import json
from pathlib import Path

from sih26170.api.config import PROJECT_ROOT
from sih26170.api.main import create_app


def main() -> None:
    app = create_app()
    document = app.openapi()

    target = PROJECT_ROOT / "docs" / "backend" / "openapi.json"
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(document, indent=2, sort_keys=False) + "\n", encoding="utf-8")

    print(f"wrote {target}")
    print(f"  paths:   {len(document['paths'])}")
    print(f"  schemas: {len(document.get('components', {}).get('schemas', {}))}")


if __name__ == "__main__":
    main()
