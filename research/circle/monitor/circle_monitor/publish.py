"""Explicit, data-only publishing. Never rewrites website code or old research."""
from __future__ import annotations

import re
import hashlib
import subprocess
from pathlib import Path

from .domain import DataError
from .store import atomic_write


def publish(export_directory, checkout, *, execute=False, git="git", remote="origin", branch="main"):
    source, root = Path(export_directory).resolve(), Path(checkout).resolve()
    managed = "circle/data/monitor/"

    def command(*args):
        return subprocess.run([git, "-C", str(root), *args], capture_output=True, text=True, check=True).stdout.strip()

    if not (source / "monitor.json").is_file():
        raise DataError("No tested monitor export to publish")
    paths = []
    for file in source.rglob("*"):
        if file.is_symlink():
            raise DataError("Export must not contain symlinks")
        if not file.is_file():
            continue
        relative = file.relative_to(source).as_posix()
        if relative in ("monitor.json", "health.json") or re.fullmatch(r"(?:forecasts|validations)/[a-f0-9]{64}\.json", relative):
            paths.append((file, managed + relative))
        else:
            raise DataError("Unexpected file in generated export: " + relative)
    if not execute:
        return {"published": False, "dry_run": True, "files": [p for _, p in paths]}
    if command("branch", "--show-current") != branch:
        raise DataError("Publishing checkout is not on the configured branch")
    status = command("status", "--porcelain", "--untracked-files=all")
    if any(line[3:].strip('"').startswith(managed) is False for line in status.splitlines()):
        raise DataError("Unrelated checkout changes prevent automated publication")
    command("fetch", remote, branch)
    remote_ref = remote + "/" + branch
    local_sha, remote_sha = command("rev-parse", "HEAD"), command("rev-parse", remote_ref)
    if local_sha != remote_sha:
        behind = subprocess.run([git, "-C", str(root), "merge-base", "--is-ancestor", "HEAD", remote_ref], capture_output=True).returncode == 0
        if behind:
            if status:
                raise DataError("Remote advanced while managed data was dirty; reconcile before publishing")
            command("merge", "--ff-only", remote_ref)
        else:
            ancestor = subprocess.run([git, "-C", str(root), "merge-base", "--is-ancestor", remote_ref, "HEAD"], capture_output=True).returncode == 0
            if not ancestor:
                raise DataError("Local and remote website histories diverged")
            unpublished = command("diff", "--name-only", remote_ref, "HEAD")
            if any(not p.startswith(managed) for p in unpublished.splitlines()):
                raise DataError("Unpublished website-code changes must not be pushed by the data publisher")
    if any((root / path).is_symlink() or any(parent.is_symlink() for parent in (root / path).parents if parent != root.parent) for _, path in paths):
        raise DataError("Publishing destination must not contain symlinks")
    for file, relative in paths:
        destination = root / relative
        body = file.read_bytes()
        if relative.endswith(".json") and ("/forecasts/" in relative or "/validations/" in relative):
            if file.stem != hashlib.sha256(body).hexdigest():
                raise DataError("Immutable export filename does not match its content hash")
            if destination.exists() and destination.read_bytes() != body:
                raise DataError("Refusing to replace published immutable evidence")
        if not destination.exists() or destination.read_bytes() != body:
            atomic_write(destination, body)
    command("add", "--", managed)
    changed = command("diff", "--cached", "--name-only")
    if changed and any(not path.startswith(managed) for path in changed.splitlines()):
        raise DataError("Staged changes contain non-monitor paths")
    if changed:
        command("-c", "user.name=Circle monitor", "-c", "user.email=circle-monitor@users.noreply.github.com", "commit", "-m", "Update Circle forecast evidence")
    # Also retry a previously committed but unpushed data update after an outage.
    command("push", remote, "HEAD:" + branch)
    return {"published": True, "commit": command("rev-parse", "HEAD"), "changed": bool(changed)}
