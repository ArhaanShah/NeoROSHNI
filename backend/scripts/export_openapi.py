from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

BACKEND_DIR = Path(__file__).resolve().parents[1]
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.main import app  # noqa: E402


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Export FastAPI OpenAPI schema to JSON.")
    parser.add_argument(
        "--out",
        type=Path,
        default=BACKEND_DIR / "openapi.json",
        help="Path where the OpenAPI JSON file should be saved.",
    )
    return parser.parse_args()


def export_openapi(out_path: Path) -> None:
    schema = app.openapi()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(schema, f, indent=2)
    print(f"Exported OpenAPI schema to {out_path}")


def main() -> int:
    args = parse_args()
    export_openapi(args.out)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
