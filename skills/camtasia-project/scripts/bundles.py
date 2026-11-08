#!/usr/bin/env python3
"""Inspect source links and stage an independent Mac Camtasia source bundle.

inspect PROJECT reads a .cmproj tree and source-manifest; source rows add
referenceKind, symlink and hardLinkCount. stage PROJECT --expected-sha256 HASH
--copy-source ID (repeat for every source-bin ID) --output NEW.cmproj copies the
complete closed bundle and selected local regular source files. All source IDs
must be explicitly selected; URLs, missing/foreign sources, application-bundle
resources and physical font files refuse. No vendor resource is discovered or
copied from logical installation selectors. Obtain media redistribution rights
before selecting it. Existing source-bin IDs, streams, clocks, unknown payload,
companion bytes and authoring identity survive; only external src values change.
External files receive relative ID-specific slots under an unused media-packed
folder. Ordinary internal paths survive. Bundle symlinks/special files refuse;
external source symlinks are snapshotted as regular independent copies. All hard
links are broken. Empty directories and file modes survive; no xattr, resource
fork or archive transport guarantee is made.

Stages require macOS project.ensure_closed ownership checks, an unchanged
project hash and stable source/companion content. Work happens in
a disposable sibling directory before publication. An identical complete output
is a no-op; aliases, nested outputs and different occupied outputs refuse.
There is no continuity-state file. Stdout schema_version 1 owner camtasia-bundles
contains projectSha256, the live source manifest, companion hashes and limits;
stage adds output, candidateSha256, written and a destination source manifest.
Readers recheck the live files; retained reports authorize no future mutation.
allSourcesBundled is source-bin containment, not full dependency closure. Fonts,
SVG/Lottie internals, installation assets and licenses require their own checks.
No input is changed. nativeVerified is always false; save/reopen, relocate with
prior paths absent, inspect actual media handles and compare native exports.
Exit 0 inspection/staging success; 1 refusal, unresolved sources or I/O error;
2 syntax error. --help is human-readable; errors are JSON on stderr.
"""

from __future__ import annotations

import argparse
import copy
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any

import project

FONT_SUFFIXES = frozenset({".ttf", ".otf", ".ttc", ".dfont", ".woff", ".woff2"})


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.exit(2, json.dumps(dict(ok=False, error=message, action="run --help")) + "\n")


def tree(root: Path) -> tuple[set[str], dict[str, dict[str, Any]]]:
    """Snapshot regular companion files and directories without following links."""

    def fail(error: OSError) -> None:
        raise error

    directories: set[str] = set()
    files: dict[str, dict[str, Any]] = {}
    for folder, dirs, names in os.walk(root, followlinks=False, onerror=fail):
        for name in dirs + names:
            path = Path(folder) / name
            mode = path.lstat().st_mode
            if stat.S_ISLNK(mode) or not (stat.S_ISREG(mode) or stat.S_ISDIR(mode)):
                raise ValueError(
                    f"replace the linked/special bundle companion in a working copy: {path}"
                )
            relative = path.relative_to(root).as_posix()
            if stat.S_ISDIR(mode):
                directories.add(relative)
            else:
                files[relative] = dict(**project.source_file_digest(path), mode=stat.S_IMODE(mode))
    return directories, files


def inspect_bundle(source: Path) -> tuple[dict[str, Any], bytes, dict[str, Any]]:
    if source.is_symlink() or source.suffix.lower() != ".cmproj" or not source.is_dir():
        raise ValueError("select a saved nonsymlink .cmproj bundle directory")
    source = source.resolve()
    directories, companions = tree(source)
    doc, raw = project.load(source)
    manifest = project.source_manifest(doc, raw, source)
    for row in manifest["sources"]:
        stored = Path(row["storedPath"])
        row["referenceKind"] = "absolute" if stored.is_absolute() else "relative"
        row["symlink"] = False
        row["hardLinkCount"] = None
        if row["status"] == "available":
            referenced = stored if stored.is_absolute() else source / stored
            row["symlink"] = referenced.absolute() != referenced.resolve()
            row["hardLinkCount"] = referenced.stat().st_nlink
        else:
            row["referenceKind"] = "unresolved"
    return (
        doc,
        raw,
        dict(
            schema_version=1,
            owner="camtasia-bundles",
            ok=manifest["ok"],
            projectSha256=project.digest(raw),
            sources=manifest,
            directories=sorted(directories),
            companions=companions,
            nativeVerified=False,
            limits=manifest["limits"]
            + [
                "Physical file copies do not establish redistribution rights or internal resource closure."
            ],
        ),
    )


def copy_snapshot(source: Path, output: Path, expected: dict[str, Any]) -> None:
    checksum = hashlib.sha256()
    with os.fdopen(os.open(source, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)), "rb") as inp:
        before = os.fstat(inp.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"select a regular file before copying: {source}")
        with output.open("xb") as out:
            while chunk := inp.read(project.HASH_CHUNK_BYTES):
                checksum.update(chunk)
                out.write(chunk)
        after = os.fstat(inp.fileno())
    current = source.stat()
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    if any(
        getattr(before, key) != getattr(after, key) or getattr(after, key) != getattr(current, key)
        for key in fields
    ):
        raise ValueError(f"source changed while copying; finish writes and retry: {source}")
    if after.st_size != expected["sizeBytes"] or checksum.hexdigest() != expected["sha256"]:
        raise ValueError(f"source content changed; inspect and stage again: {source}")
    output.chmod(expected.get("mode", stat.S_IMODE(before.st_mode)))


def stage_bundle(source: Path, output: Path, expected: str, selected: list[int]) -> dict[str, Any]:
    if not re.fullmatch(r"[0-9a-f]{64}", expected):
        raise ValueError("supply the inspected project SHA-256")
    doc, raw, report = inspect_bundle(source)
    source = source.resolve()
    output = output.absolute()
    if output.is_symlink() or output.suffix.lower() != ".cmproj":
        raise ValueError("choose a separate nonsymlink .cmproj output")
    output = output.parent.resolve(strict=True) / output.name
    if (
        output.is_relative_to(source)
        or source.is_relative_to(output)
        or any(os.path.samefile(source, p) for p in output.parents)
        or (output.exists() and any(os.path.samefile(output, p) for p in [source, *source.parents]))
    ):
        raise ValueError("choose an output outside the input bundle and its ancestors")
    if project.digest(raw) != expected:
        raise ValueError("project changed; inspect the saved bundle and supply its current SHA-256")
    if not project.is_native_format10(doc):
        raise ValueError(
            "use a verified Mac format-10 project; convert a separate copy in Camtasia first"
        )
    project.ensure_closed(source / "project.tscproj")
    rows = report["sources"]["sources"]
    if (
        any(type(sid) is not int for sid in selected)
        or len(selected) != len(set(selected))
        or set(selected) != {r["sourceId"] for r in rows}
    ):
        raise ValueError(
            "select every source-bin ID once with --copy-source after reviewing the manifest"
        )
    if not report["ok"]:
        raise ValueError("relink every missing, remote or foreign source before staging the bundle")
    for row in rows:
        path = Path(row["resolvedPath"])
        if path.suffix.lower() in FONT_SUFFIXES or any(
            part.lower().endswith(".app") for part in path.parts
        ):
            raise ValueError(
                "retain physical fonts and application resources outside this source-copy workflow"
            )
    directories, files = set(report["directories"]), report["companions"]
    for name in files:
        path = Path(name)
        if path.suffix.lower() in FONT_SUFFIXES or any(
            part.lower().endswith(".app") for part in path.parts
        ):
            raise ValueError(
                "remove physical fonts/application resources from a separate working bundle before source-only staging"
            )
    slot = "media-packed"
    index = 0
    while slot in directories or slot in files:
        index += 1
        slot = f"media-packed-{index}"
    candidate = copy.deepcopy(doc)
    additions = []
    for row, entry in zip(rows, candidate.get("sourceBin", []), strict=True):
        if not row["bundled"]:
            name = f"{slot}/source-{row['sourceId']}/{Path(row['storedPath']).name}"
            entry["src"] = "./" + name
            additions.append((row, name))
    encoded = project.encode_document(candidate)
    temporary = Path(tempfile.mkdtemp(prefix=".camtasia-bundle-", dir=output.parent))
    reserved = None
    try:
        for name in sorted(directories, key=lambda p: (p.count("/"), p)):
            (temporary / name).mkdir()
        for name, record in files.items():
            copy_snapshot(source / name, temporary / name, record)
        (temporary / "project.tscproj").chmod(0o600)
        (temporary / "project.tscproj").write_bytes(encoded)
        (temporary / "project.tscproj").chmod(files["project.tscproj"]["mode"])
        for row, name in additions:
            target = temporary / name
            target.parent.mkdir(parents=True, exist_ok=True)
            copy_snapshot(Path(row["resolvedPath"]), target, row)
        # Recheck the complete input tree, all source links/content, and ownership
        # after the copy; a retained inspection report never grants mutation.
        _, latest_raw, latest = inspect_bundle(source)
        if raw != latest_raw or latest != report:
            raise ValueError("input bundle or source files changed; inspect and stage again")
        project.ensure_closed(source / "project.tscproj")
        destination = project.source_manifest(candidate, encoded, temporary)
        validation = project.validate(candidate, temporary)
        if not destination["allSourcesBundled"] or not validation["ok"]:
            raise ValueError(
                "repair the staged source references or project structure before native use"
            )
        planned = tree(temporary)
        written = True
        if output.exists():
            if not output.is_dir() or tree(output) != planned:
                raise ValueError("output contains different data; choose a new .cmproj path")
            if any((output / name).stat().st_nlink != 1 for name in planned[1]):
                raise ValueError(
                    "output contains hard-linked files; choose a new independent .cmproj path"
                )
            written = False
        else:
            output.mkdir()
            reserved = output.stat()
            os.replace(temporary, output)
            reserved = None
        report.update(
            output=str(output),
            candidateSha256=project.digest(encoded),
            written=written,
            destination=project.source_manifest(candidate, encoded, output),
            validation=validation,
        )
        return report
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
        if reserved is not None and output.is_dir() and output.stat().st_ino == reserved.st_ino:
            output.rmdir()


def main(argv: list[str] | None = None) -> int:
    parser = ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("project", type=Path)
    stage = commands.add_parser("stage")
    stage.add_argument("project", type=Path)
    stage.add_argument("--expected-sha256", required=True)
    stage.add_argument("--copy-source", type=int, action="append", default=[])
    stage.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        result = (
            inspect_bundle(args.project)[2]
            if args.command == "inspect"
            else stage_bundle(args.project, args.output, args.expected_sha256, args.copy_source)
        )
        print(json.dumps(result, ensure_ascii=False))
        return 0 if result["ok"] else 1
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError) as exc:
        print(
            json.dumps(
                dict(
                    ok=False,
                    error=str(exc),
                    action="inspect the source bundle and choose a separate output",
                )
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
