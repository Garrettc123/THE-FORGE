#!/usr/bin/env python3
"""Expand forge_cognitive_core.py from compressed chunked blob if missing."""
from pathlib import Path
import base64, zlib, sys

ROOT = Path(__file__).resolve().parent
TARGET = ROOT / "forge_cognitive_core.py"

if TARGET.exists() and TARGET.stat().st_size > 1000:
    print(f"[expand] {TARGET.name} already present ({TARGET.stat().st_size} bytes)")
    sys.exit(0)

# Prefer single blob, else concatenate chunks
blob = ROOT / "forge_cognitive_core.py.zlib.b64"
parts = sorted(ROOT.glob("forge_cognitive_core.py.zlib.b64.part*"))

if blob.exists() and blob.stat().st_size > 1000:
    b64 = blob.read_text().strip()
elif parts:
    b64 = "".join(p.read_text().strip() for p in parts)
else:
    print("[expand] ERROR: no compressed core blob found", file=sys.stderr)
    sys.exit(1)

data = zlib.decompress(base64.b64decode(b64))
TARGET.write_bytes(data)
print(f"[expand] Wrote {TARGET} ({len(data)} bytes)")
