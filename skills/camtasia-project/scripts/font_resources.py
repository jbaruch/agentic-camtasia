#!/usr/bin/env python3
"""Inspect declared fonts and stage explicitly licensed physical font handoffs.

inspect PROJECT [--font FILE ...] inventories stored rich/global/default font
names and explicitly supplied OpenType font files. Declarations are not proof
of effective face selection, fallback, glyph coverage or complete font closure.
FontTools reads SFNT names, style/weight, embedding flags, collection faces and
variable axes/instances; no font is activated, installed, modified or subsetted.
The optional parser dependency is declared in the repository fonts extra. Its
installed-consumer pin and quarterly renewal point are FONTTOOLS_REQUIREMENT.

stage PROJECT --expected-sha256 HASH --spec SPEC --output NEW_DIRECTORY copies
whole unmodified fonts and copyright/license notices into a separate handoff.
Spec schema_version 1 requires redistribution_confirmed:true, fonts and licenses.
Each font has path, sha256, postscript_names (nonempty distinct explicit face
names) and license_id. Each license has id, path and sha256. Paths resolve beside
the spec. Select the actual font versions and confirm that the supplied licenses
cover distribution of each complete file, including every face in a collection.
Metadata embedding flags are reported, never treated as a redistribution grant;
restricted/bitmap-only faces and application-bundle font sources refuse staging.
Selected face names must occur in the file and relate to a project declaration.
Unknown/RTF declarations remain unresolved, not guessed or silently converted.

The saved project must be closed and match HASH; its bytes are never changed.
Source reads are regular/stable snapshots. The handoff retains independent file
copies, original font basenames and exact bytes. Different occupied outputs,
symlinks, hard links and input/output aliases refuse; identical reruns are no-ops.
A temporary sibling and reserved empty output precede atomic directory publication.
verify DIRECTORY re-reads its manifest, every file/hash and physical face metadata.
Extra files, unrecognized schema, unsafe paths and changed content refuse.

font-handoff.json schema_version 1, owner camtasia-font-resources, is written and
read only by this module. It records projectSha256, redistributionConfirmed,
font records (relativePath, sha256, sizeBytes, faces, postscriptNames, licenseId)
and license records (id, relativePath, sha256, sizeBytes). It carries no authority
for activation or new distribution. No legacy schema is migrated; unknown schemas
refuse verification. Recheck live bytes before delivery. Stdout schema 1 reports
nativeVerified:false. Native absence/install/relocation/render checks remain
separate; a .cmproj does not automatically install this adjacent font handoff.
Exit 0 success; 1 input/I/O/dependency refusal; 2 CLI syntax (JSON stderr).
"""

from __future__ import annotations

import argparse
import io
import json
import os
from pathlib import Path, PurePosixPath
import re
import shutil
import struct
import subprocess
import sys
import tempfile
from typing import Any

import bundles
import lottie_images
import project

# Renew quarterly and with upstream security releases; keep pyproject.toml aligned.
FONTTOOLS_REQUIREMENT = "fonttools==4.68.0"
OWNER = "camtasia-font-resources"
MANIFEST = "font-handoff.json"


class ArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.exit(2, json.dumps(dict(ok=False, error=message, action="run --help")) + "\n")


def font_faces(raw: bytes) -> list[dict[str, Any]]:
    try:
        from fontTools.ttLib import TTCollection, TTFont, TTLibError
    except ImportError as exc:
        raise ValueError(
            "run this command in an isolated environment with " + FONTTOOLS_REQUIREMENT
        ) from exc
    magic = raw[:4]
    if magic not in {b"\x00\x01\x00\x00", b"OTTO", b"true", b"ttcf"}:
        raise ValueError("select an uncompressed OpenType/TrueType font or collection")
    container = None
    fonts = []
    try:
        if magic == b"ttcf":
            container = TTCollection(io.BytesIO(raw), lazy=True, recalcTimestamp=False)
            fonts = container.fonts
        else:
            fonts = [TTFont(io.BytesIO(raw), lazy=True, recalcTimestamp=False)]
        result = []
        for index, font in enumerate(fonts):
            if "name" not in font:
                raise ValueError("select a font with identifiable physical face names")
            names = font["name"]
            by_id = {
                str(nid): sorted({n.toUnicode() for n in names.names if n.nameID == nid})
                for nid in (0, 1, 2, 4, 5, 6, 13, 14, 16, 17)
            }
            if len(by_id["6"]) != 1 or not by_id["6"][0]:
                raise ValueError("select a font with one unambiguous PostScript face name")
            axes, instances = [], []
            if "fvar" in font:
                fvar = font["fvar"]
                axes = [
                    dict(
                        tag=a.axisTag,
                        minimum=a.minValue,
                        default=a.defaultValue,
                        maximum=a.maxValue,
                    )
                    for a in fvar.axes
                ]
                instances = [
                    dict(
                        subfamily=names.getDebugName(i.subfamilyNameID),
                        postscriptName=names.getDebugName(i.postscriptNameID)
                        if i.postscriptNameID != 65535
                        else None,
                        coordinates=dict(i.coordinates),
                    )
                    for i in fvar.instances
                ]
            os2: Any = font.get("OS/2")
            result.append(
                dict(
                    index=index,
                    names=by_id,
                    postscriptName=by_id["6"][0],
                    family=names.getBestFamilyName(),
                    subfamily=names.getBestSubFamilyName(),
                    weightClass=int(os2.usWeightClass) if os2 is not None else None,
                    selectionFlags=int(os2.fsSelection) if os2 is not None else None,
                    embeddingFlags=int(os2.fsType) if os2 is not None else None,
                    variableAxes=axes,
                    namedInstances=instances,
                )
            )
        if not result:
            raise ValueError("select a nonempty physical font collection")
        return result
    except (TTLibError, KeyError, UnicodeError, struct.error, IndexError, EOFError) as exc:
        raise ValueError(
            "repair or replace the malformed font metadata before handoff: " + str(exc)
        ) from exc
    finally:
        if container is not None:
            container.close()
        else:
            for font in fonts:
                font.close()


def declarations(doc: dict[str, Any]) -> dict[str, Any]:
    names, rtf = [], []
    for path, node in project.objects(doc):
        if node.get("name") == "fontName" and isinstance(node.get("value"), str):
            names.append(
                dict(
                    path=path + "/value",
                    fontName=node["value"],
                    role="rich",
                    rangeStart=node.get("rangeStart"),
                    rangeEnd=node.get("rangeEnd"),
                )
            )
        if isinstance(node.get("fontName"), str):
            names.append(dict(path=path + "/fontName", fontName=node["fontName"], role="stored"))
        for key in ("font", "defaultFont"):
            if isinstance(node.get(key), dict) and isinstance(node[key].get("name"), str):
                names.append(
                    dict(
                        path=path + "/" + key + "/name", fontName=node[key]["name"], role="default"
                    )
                )
        if isinstance(node.get("text"), str) and node["text"].lstrip().startswith(r"{\rtf"):
            rtf.append(path + "/text")
    return dict(fontDeclarations=names, unresolvedRTF=rtf, completeFontClosure=False)


def read_font(path: Path) -> tuple[bytes, dict[str, Any]]:
    raw = lottie_images.read_file(path, "physical font")
    return raw, dict(sha256=project.digest(raw), sizeBytes=len(raw), faces=font_faces(raw))


def inspect_fonts(source: Path, fonts: list[Path]) -> dict[str, Any]:
    doc, raw = project.load(source)
    return dict(
        schema_version=1,
        owner=OWNER,
        ok=True,
        projectSha256=project.digest(raw),
        **declarations(doc),
        fontFiles=[dict(path=str(p), **read_font(p)[1]) for p in fonts],
        nativeVerified=False,
    )


def postscript_names(face: dict[str, Any]) -> set[str]:
    return {face["postscriptName"]} | {
        i["postscriptName"] for i in face["namedInstances"] if i["postscriptName"]
    }


def selected_faces(faces: list[dict[str, Any]], selected: Any) -> list[dict[str, Any]]:
    if (
        not isinstance(selected, list)
        or not selected
        or not all(isinstance(n, str) and n for n in selected)
        or len(selected) != len(set(selected))
    ):
        raise ValueError("select distinct explicit PostScript face names from inspection")
    for face in faces:
        if face["embeddingFlags"] is not None and face["embeddingFlags"] & (2 | 512):
            raise ValueError(
                "select a font without restricted/bitmap-only embedding flags for this handoff"
            )
    result = []
    for name in selected:
        matching = [face for face in faces if name in postscript_names(face)]
        if len(matching) != 1:
            raise ValueError(
                "select an unambiguous PostScript face actually present in the font file"
            )
        result.append(matching[0])
    return result


def spec_records(
    spec: dict[str, Any], root: Path, declared: set[str]
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[Path]]:
    if (
        set(spec) != {"schema_version", "redistribution_confirmed", "fonts", "licenses"}
        or type(spec.get("schema_version")) is not int
        or spec["schema_version"] != 1
        or spec.get("redistribution_confirmed") is not True
    ):
        raise ValueError(
            "supply schema_version 1 and explicitly confirm redistribution rights for complete font files"
        )
    fonts, licenses, inputs = [], [], []
    for kind, fields in (
        ("licenses", {"id", "path", "sha256"}),
        ("fonts", {"path", "sha256", "postscript_names", "license_id"}),
    ):
        rows = spec[kind]
        if not isinstance(rows, list) or not rows:
            raise ValueError("supply nonempty font and copyright/license selections")
        for index, row in enumerate(rows):
            if (
                not isinstance(row, dict)
                or set(row) != fields
                or not isinstance(row["path"], str)
                or not row["path"]
                or not isinstance(row["sha256"], str)
                or not re.fullmatch(r"[0-9a-f]{64}", row["sha256"])
            ):
                raise ValueError("inspect each selected file and provide its path and SHA-256")
            path = root / row["path"]
            if any(part.lower().endswith(".app") for part in path.resolve().parts):
                raise ValueError(
                    "provide independently licensed font sources outside application bundles"
                )
            raw = lottie_images.read_file(path, "font handoff input")
            if project.digest(raw) != row["sha256"]:
                raise ValueError(
                    "selected font/license changed; inspect its bytes and refresh the spec"
                )
            inputs.append(path)
            record = dict(
                relativePath=f"{kind}/{index}/{path.name}", sha256=row["sha256"], sizeBytes=len(raw)
            )
            if kind == "licenses":
                if (
                    not isinstance(row["id"], str)
                    or not row["id"]
                    or row["id"] in {r["id"] for r in licenses}
                    or not raw.decode("utf-8").strip()
                    or b"\0" in raw
                ):
                    raise ValueError(
                        "provide distinct license IDs and nonempty UTF-8 copyright/license notices"
                    )
                licenses.append(dict(id=row["id"], **record))
            else:
                selected = row["postscript_names"]
                faces = font_faces(raw)
                for face in selected_faces(faces, selected):
                    aliases = {
                        v for k in ("1", "6", "16") for v in face["names"][k]
                    } | postscript_names(face)
                    if not aliases & declared:
                        raise ValueError(
                            "select physical faces related to inspected project declarations"
                        )
                prior = {
                    ps
                    for record in fonts
                    for face in record["faces"]
                    for ps in postscript_names(face)
                }
                if any(postscript_names(face) & prior for face in faces):
                    raise ValueError(
                        "select one physical version of each PostScript face for the handoff"
                    )
                if not isinstance(row["license_id"], str) or row["license_id"] not in {
                    r["id"] for r in licenses
                }:
                    raise ValueError(
                        "link every complete font file to a selected copyright/license notice"
                    )
                if row["sha256"] in {r["sha256"] for r in fonts}:
                    raise ValueError(
                        "select each complete font file once, listing every needed face together"
                    )
                fonts.append(
                    dict(
                        **record, faces=faces, postscriptNames=selected, licenseId=row["license_id"]
                    )
                )
    # Inputs follow license records first, then font records.
    return fonts, licenses, inputs


def safe_relative(value: Any) -> str:
    if not isinstance(value, str) or not value or "\\" in value or ":" in value:
        raise ValueError("retain portable relative handoff paths")
    path = PurePosixPath(value)
    if path.is_absolute() or any(p in {".", ".."} for p in value.split("/")):
        raise ValueError("retain portable relative handoff paths")
    return value


def verify_handoff(root: Path) -> dict[str, Any]:
    if root.is_symlink() or not root.is_dir():
        raise ValueError("select a nonsymlink font handoff directory")
    directories, files = bundles.tree(root)
    if MANIFEST not in files:
        raise ValueError("retain the regular font-handoff.json manifest")
    manifest, _ = project.load(root / MANIFEST)
    if (
        set(manifest)
        != {
            "schema_version",
            "owner",
            "projectSha256",
            "redistributionConfirmed",
            "fonts",
            "licenses",
        }
        or type(manifest.get("schema_version")) is not int
        or manifest["schema_version"] != 1
        or manifest.get("owner") != OWNER
        or manifest.get("redistributionConfirmed") is not True
        or not isinstance(manifest.get("projectSha256"), str)
        or not re.fullmatch(r"[0-9a-f]{64}", manifest["projectSha256"])
    ):
        raise ValueError(
            "use the supported schema-1 font handoff manifest; regenerate unknown or damaged records"
        )
    if any(not isinstance(manifest.get(k), list) or not manifest[k] for k in ("fonts", "licenses")):
        raise ValueError("retain the font and copyright/license inventories")
    expected = {MANIFEST}
    licenses, physical_names = set(), set()
    for kind in ("licenses", "fonts"):
        for row in manifest[kind]:
            required = {"relativePath", "sha256", "sizeBytes"} | (
                {"id"} if kind == "licenses" else {"faces", "postscriptNames", "licenseId"}
            )
            if not isinstance(row, dict) or set(row) != required:
                raise ValueError("regenerate malformed font handoff records")
            name = safe_relative(row["relativePath"])
            if name in expected:
                raise ValueError("retain distinct font handoff paths")
            expected.add(name)
            raw = lottie_images.read_file(root / name, "handoff content")
            if (
                type(row["sizeBytes"]) is not int
                or len(raw) != row["sizeBytes"]
                or project.digest(raw) != row["sha256"]
            ):
                raise ValueError(
                    "handoff content changed; restore the inspected bytes or restage it"
                )
            if kind == "licenses":
                if (
                    not isinstance(row["id"], str)
                    or not row["id"]
                    or row["id"] in licenses
                    or not raw.decode("utf-8").strip()
                    or b"\0" in raw
                ):
                    raise ValueError("retain distinct copyright/license notices")
                licenses.add(row["id"])
            else:
                faces = font_faces(raw)
                selected_faces(faces, row["postscriptNames"])
                names = {name for face in faces for name in postscript_names(face)}
                if names & physical_names:
                    raise ValueError(
                        "retain one physical version of each PostScript face in the handoff"
                    )
                physical_names.update(names)
                if (
                    faces != row["faces"]
                    or not isinstance(row["licenseId"], str)
                    or row["licenseId"] not in licenses
                ):
                    raise ValueError(
                        "restore selected physical face identities and their license associations"
                    )
    expected_dirs = {
        str(p) for name in expected for p in PurePosixPath(name).parents if str(p) != "."
    }
    if (
        set(files) != expected
        or directories != expected_dirs
        or any((root / name).stat().st_nlink != 1 for name in files)
    ):
        raise ValueError("retain only independent regular handoff files and their directories")
    return dict(schema_version=1, owner=OWNER, ok=True, manifest=manifest, nativeVerified=False)


def stage_handoff(source: Path, spec_path: Path, output: Path, expected: str) -> dict[str, Any]:
    doc, raw = project.load(source)
    if project.digest(raw) != expected:
        raise ValueError(
            "project changed; inspect its saved SHA-256 and rebuild the font handoff spec"
        )
    project.ensure_closed(project.project_file(source))
    spec, _ = project.load(spec_path)
    decl = declarations(doc)
    fonts, licenses, inputs = spec_records(
        spec, spec_path.parent, {d["fontName"] for d in decl["fontDeclarations"]}
    )
    output = output.absolute()
    if output.is_symlink():
        raise ValueError("choose a separate nonsymlink handoff output directory")
    output = output.parent.resolve(strict=True) / output.name
    protected = [project.project_file(source), spec_path, *inputs]
    if output.exists() and any(
        os.path.samefile(output, parent) for path in protected for parent in path.resolve().parents
    ):
        raise ValueError("choose an output separate from the input directories")
    if source.is_dir() and any(os.path.samefile(source, p) for p in output.parents):
        raise ValueError("choose an output outside the original project bundle")
    manifest = dict(
        schema_version=1,
        owner=OWNER,
        projectSha256=expected,
        redistributionConfirmed=True,
        fonts=fonts,
        licenses=licenses,
    )
    temporary = Path(tempfile.mkdtemp(prefix=".camtasia-fonts-", dir=output.parent))
    reservation = None
    try:
        for path, record in zip(inputs, [*licenses, *fonts], strict=True):
            target = temporary / record["relativePath"]
            target.parent.mkdir(parents=True, exist_ok=True)
            bundles.copy_snapshot(path, target, record)
        (temporary / MANIFEST).write_bytes(project.encode_document(manifest))
        verify_handoff(temporary)
        if project.load(source)[1] != raw:
            raise ValueError(
                "project changed during staging; rebuild the handoff from a saved baseline"
            )
        project.ensure_closed(project.project_file(source))
        planned = bundles.tree(temporary)
        written = True
        if output.exists():
            verify_handoff(output)
            if bundles.tree(output) != planned:
                raise ValueError("output contains different data; choose another handoff directory")
            written = False
        else:
            output.mkdir()
            reservation = output.stat()
            os.replace(temporary, output)
            reservation = None
        return dict(
            schema_version=1,
            owner=OWNER,
            ok=True,
            output=str(output),
            written=written,
            manifest=manifest,
            **decl,
            nativeVerified=False,
        )
    finally:
        if temporary.exists():
            shutil.rmtree(temporary)
        if (
            reservation is not None
            and output.is_dir()
            and output.stat().st_ino == reservation.st_ino
        ):
            output.rmdir()


def main(argv: list[str] | None = None) -> int:
    parser = ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("project", type=Path)
    inspect.add_argument("--font", type=Path, action="append", default=[])
    stage = commands.add_parser("stage")
    stage.add_argument("project", type=Path)
    stage.add_argument("--expected-sha256", required=True)
    stage.add_argument("--spec", type=Path, required=True)
    stage.add_argument("--output", type=Path, required=True)
    verify = commands.add_parser("verify")
    verify.add_argument("directory", type=Path)
    args = parser.parse_args(argv)
    try:
        if args.command == "inspect":
            result = inspect_fonts(args.project, args.font)
        elif args.command == "verify":
            result = verify_handoff(args.directory)
        else:
            result = stage_handoff(args.project, args.spec, args.output, args.expected_sha256)
        print(json.dumps(result, ensure_ascii=False))
        return 0
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError) as exc:
        print(
            json.dumps(
                dict(
                    ok=False,
                    error=str(exc),
                    action="inspect explicit font versions and copyright/license rights before staging",
                )
            ),
            file=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
