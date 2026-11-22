"""Append-only evidence and forecasts; replace only the small published view."""
from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path
import tempfile

from .domain import DataError, canonical, digest


def atomic_write(path: Path, data: bytes):
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(prefix="." + path.name, dir=path.parent)
    try:
        with os.fdopen(fd, "wb") as file:
            file.write(data)
            file.flush()
            os.fsync(file.fileno())
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)


class Store:
    def __init__(self, root):
        self.root = Path(root)

    def put(self, collection, value):
        if collection not in {"financials", "funds", "releases", "forecasts", "validations", "issues", "runs"}:
            raise DataError("Unknown evidence collection")
        body = canonical(value)
        path = self.root / collection / (digest(value) + ".json")
        path.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(prefix=".record-", dir=path.parent)
        try:
            with os.fdopen(fd, "wb") as file:
                file.write(body)
                file.flush()
                os.fsync(file.fileno())
            try:
                # Linking a complete file is atomic and refuses an existing name.
                os.link(temporary, path)
            except FileExistsError:
                if path.read_bytes() != body:
                    raise DataError("Immutable record collision")
        finally:
            os.unlink(temporary)
        return path

    def rows(self, collection):
        return [json.loads(p.read_bytes()) for p in sorted((self.root / collection).glob("*.json"))]

    @contextlib.contextmanager
    def lock(self):
        self.root.mkdir(parents=True, exist_ok=True)
        file = (self.root / ".lock").open("a+b")
        try:
            if os.name == "nt":
                import msvcrt
                file.seek(0, 2)
                if file.tell() == 0:
                    file.write(b"0")
                    file.flush()
                file.seek(0)
                msvcrt.locking(file.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(file.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            file.close()
            raise DataError("Another monitor run holds the state lock") from exc
        try:
            yield self
        finally:
            if os.name == "nt":
                file.seek(0)
                msvcrt.locking(file.fileno(), msvcrt.LK_UNLCK, 1)
            file.close()
