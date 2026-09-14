"""Atomic cache writes. Shared map updates serialize so parallel fetches compose."""
from __future__ import annotations

import fcntl
import json
import os
import tempfile
from pathlib import Path
from typing import Any


def atomic_write_json(path: Path, value: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, name = tempfile.mkstemp(prefix=f'.{path.name}.', dir=path.parent)
    try:
        with os.fdopen(fd, 'w') as stream:
            json.dump(value, stream, ensure_ascii=False, indent=1)
            stream.write('\n')
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(name, path)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def merge_json_map(path: Path, entries: dict) -> int:
    if not entries:
        return 0
    path.parent.mkdir(parents=True, exist_ok=True)
    # Keep the lock inode stable across atomic replacement of the JSON itself.
    with path.with_suffix(path.suffix + '.lock').open('a') as lock:
        fcntl.flock(lock, fcntl.LOCK_EX)
        cache = json.loads(path.read_text()) if path.exists() else {}
        if not isinstance(cache, dict):
            raise ValueError(f'{path}: expected a JSON object')
        before = len(cache)
        cache.update(entries)
        atomic_write_json(path, cache)
        return len(cache) - before
