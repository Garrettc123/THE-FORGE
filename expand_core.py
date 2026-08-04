#!/usr/bin/env python3
"""Expand forge_cognitive_core.py from compressed blob if missing."""
from pathlib import Path
import base64, zlib, sys

TARGET = Path(__file__).resolve().parent / "forge_cognitive_core.py"
BLOB = Path(__file__).resolve().parent / "forge_cognitive_core.py.zlib.b64"

if TARGET.exists() and TARGET.stat().st_size > 1000:
    print(f"[expand] {TARGET.name} already present ({TARGET.stat().st_size} bytes)")
    sys.exit(0)

if not BLOB.exists():
    print(f"[expand] ERROR: {BLOB.name} not found", file=sys.stderr)
    sys.exit(1)

data = zlib.decompress(base64.b64decode(BLOB.read_text().strip()))
TARGET.write_bytes(data)
print(f"[expand] Wrote {TARGET} ({len(data)} bytes)")
