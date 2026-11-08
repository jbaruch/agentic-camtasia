#!/usr/bin/env python3
"""Inspect and stage verified Mac format-10 Color LUT controls.

resources --app APP lists CUBE names, paths and SHA-256 hashes from the verified
installation and native user Color LUTs directory. It reads files, never imports
or copies resources. Case aliases with different bytes are ambiguous.
set PROJECT --clip-id ID [--effect-token TOKEN] --spec SPEC [--app APP]
--output CANDIDATE edits an existing LutEffect through the shared visual selector.
inspect PROJECT lists its physical instances. Linked mirrors change together;
audio, other effects, tokens, reset metadata and original presetName survive.

Spec schema_version 1 accepts source (existing lookup filename; requires --app),
intensity in [0,1], range from RANGE_CHOICES, nonnegative rational easeIn/easeOut
seconds, and/or boolean bypassed. Range controls keep their raw native channel
and ramp units. Static native doubles may be bare numbers or typed descriptors;
descriptors retain hints/bounds and curves are never flattened. Easing patches
only lut_intensity FadeInFunc/FadeOutFunc edges, with exact project-tick durations
that fit the displayed clip. Existing zero-duration edge records are retained.
Shared edge timing is never changed on unrelated controls. Other curve shapes,
resource installation and new keyframe authoring need their native contracts.

Selected resources must be complete finite 3D CUBE tables. Header checks and
file hashes do not prove native lookup, rendering or complete dependency closure.
The resource audit describes only the selected file; null means not checked.
No project/media/resource is overwritten and no editor is launched. Staging is
exclusive or an identical no-op. Use ordinary diff/validate/apply and matching
native save/reopen/export afterward. JSON stdout schema_version 1, owner
camtasia-luts, contains hashes, inventory, resource audit and nativeVerified false.
Exit 0 success, 1 input/I/O refusal, 2 CLI syntax; diagnostics are JSON on stderr.
--help retains standard plaintext help on stdout.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
import plistlib
import shlex
import sys
from typing import Any, NoReturn
from xml.parsers.expat import ExpatError

import effects
import hotspots
import project

CHANNELS = {"grey": 0, "red": 1, "green": 2, "blue": 3}
RAMPS = {
    "all": (0.0, 0.0, 1.0, 1.0),
    "shadows": (0.0, 0.0, 0.25, 0.5),
    "midtones": (0.25, 0.4, 0.6, 0.75),
    "highlights": (0.5, 0.75, 1.0, 1.0),
}
RAMP_NAMES = ("shadowRampStart", "shadowRampEnd", "highlightRampStart", "highlightRampEnd")
RANGE_CHOICES = {
    channel + "-" + region: (code, values)
    for channel, code in CHANNELS.items()
    for region, values in RAMPS.items()
    if region != "all" or channel == "grey"
}


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.exit(2, json.dumps(dict(ok=False, error=message), ensure_ascii=False) + "\n")


def require_native(doc: dict[str, Any]) -> None:
    if not project.is_native_format10(doc):
        raise ValueError("use a verified Camtasia Mac format-10 LUT contract")


def lookup_roots(app: Path, user_root: Path | None = None) -> list[Path]:
    app = app.expanduser().resolve(strict=True)
    try:
        info = plistlib.loads((app / "Contents/Info.plist").read_bytes())
    except (plistlib.InvalidFileException, ExpatError) as exc:
        raise ValueError(f"{app}: repair Info.plist or select a complete native app") from exc
    if (
        not isinstance(info, dict)
        or info.get("CFBundleIdentifier") != "com.techsmith.camtasia"
        or not isinstance(info.get("CFBundleShortVersionString"), str)
        or (info.get("CFBundleShortVersionString"), info.get("CFBundleVersion"))
        not in project.NATIVE_FORMAT10_BUILDS.items()
    ):
        raise ValueError("select a verified Camtasia Mac build for LUT resource lookup")
    installed = app / "Contents/Resources/Color LUTs"
    if not installed.is_dir():
        raise ValueError("select a complete app with Contents/Resources/Color LUTs")
    user = (
        user_root
        if user_root is not None
        else Path.home() / "Library/Application Support/TechSmith/Camtasia/Color LUTs"
    )
    if user.exists() and not user.is_dir():
        raise ValueError(f"{user}: restore the native user Color LUTs directory")
    return [installed, *([user] if user.is_dir() else [])]


def resources(app: Path, user_root: Path | None = None) -> list[dict[str, Any]]:
    found: dict[str, list[dict[str, Any]]] = {}
    for root in lookup_roots(app, user_root):
        for path in sorted(root.iterdir()):
            if path.suffix.lower() == ".cube":
                raw = path.read_bytes()
                found.setdefault(path.name, []).append(
                    dict(path=str(path), sha256=project.digest(raw), bytes=len(raw))
                )
    records = []
    for name, locations in sorted(found.items()):
        aliases = sorted(other for other in found if other.casefold() == name.casefold())
        digests = {v["sha256"] for alias in aliases for v in found[alias]}
        records.append(
            dict(name=name, locations=locations, aliases=aliases, ambiguous=len(digests) != 1)
        )
    return records


def cube_metadata(raw: bytes) -> dict[str, Any]:
    headers: dict[str, Any] = {}
    rows = 0
    for number, line in enumerate(raw.decode("utf-8-sig").splitlines(), 1):
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if line[0].isalpha():
            tokens = shlex.split(line, comments=True)
            key, values = tokens[0], tokens[1:]
            if rows or key in headers:
                raise ValueError(f"CUBE line {number}: put unique headers before the RGB table")
            if key == "TITLE" and len(values) == 1:
                headers[key] = values[0]
            elif (
                key == "LUT_3D_SIZE"
                and len(values) == 1
                and values[0].isdigit()
                and int(values[0]) >= 2
            ):
                headers[key] = int(values[0])
            elif key in {"DOMAIN_MIN", "DOMAIN_MAX"} and len(values) == 3:
                headers[key] = [float(value) for value in values]
                if not all(math.isfinite(v) for v in headers[key]):
                    raise ValueError(f"CUBE line {number}: supply finite domain values")
            else:
                raise ValueError(f"CUBE line {number}: use the observed finite 3D CUBE format")
        else:
            values = line.partition("#")[0].split()
            if (
                "LUT_3D_SIZE" not in headers
                or len(values) != 3
                or not all(math.isfinite(float(v)) for v in values)
            ):
                raise ValueError(
                    f"CUBE line {number}: supply three finite RGB values after LUT_3D_SIZE"
                )
            rows += 1
    size = headers.get("LUT_3D_SIZE")
    if not isinstance(size, int) or rows != size**3:
        raise ValueError("supply a complete 3D CUBE table with size cubed RGB rows")
    minimum, maximum = headers.get("DOMAIN_MIN", [0.0] * 3), headers.get("DOMAIN_MAX", [1.0] * 3)
    if any(a >= b for a, b in zip(minimum, maximum)):
        raise ValueError("supply increasing CUBE domain bounds for each channel")
    return dict(
        gridSize=size, rows=rows, title=headers.get("TITLE"), domainMin=minimum, domainMax=maximum
    )


def resolve_resource(app: Path, name: Any, user_root: Path | None = None) -> dict[str, Any]:
    if not isinstance(name, str) or not name or Path(name).name != name or "\\" in name:
        raise ValueError("select a LUT filename from resources; paths are not native selectors")
    matches = [record for record in resources(app, user_root) if record["name"] == name]
    if len(matches) != 1:
        raise ValueError(
            "select an existing filename from resources; import new CUBE files in Camtasia first"
        )
    record = matches[0]
    if record["ambiguous"]:
        raise ValueError(
            "resolve conflicting installed/user LUT bytes for this filename before editing"
        )
    location = record["locations"][0]
    raw = Path(location["path"]).read_bytes()
    if project.digest(raw) != location["sha256"]:
        raise ValueError("the LUT changed during inspection; inspect its resource again")
    try:
        metadata = cube_metadata(raw)
    except ValueError as exc:
        raise ValueError(
            f"{location['path']}: {exc}; select a complete finite 3D CUBE resource"
        ) from exc
    return dict(**record, **metadata, sha256=location["sha256"], closure="selected-file-only")


def patch_double(parameters: dict[str, Any], name: str, value: float) -> None:
    old = parameters.get(name)
    if type(old) in (int, float):
        parameters[name] = value
    elif isinstance(old, dict) and old.get("type") == "double":
        effects.patch_parameter(parameters, name, value)
    else:
        raise ValueError(
            f"inspect the native double control {name}; preserve unfamiliar representations"
        )


def patch_edge(effect: dict[str, Any], key: str, function: str, duration: int) -> None:
    modifiers = effect.get(key, [])
    if not isinstance(modifiers, list):
        raise ValueError("inspect the native LUT edge array before editing")
    matches = []
    for modifier in modifiers:
        if not isinstance(modifier, dict) or not isinstance(modifier.get("parameters"), list):
            raise ValueError("inspect unfamiliar LUT edge modifier parameters")
        for parameter in modifier["parameters"]:
            if not isinstance(parameter, dict):
                raise ValueError("inspect the native edge parameter entry")
            if parameter.get("name") == "lut_intensity":
                if modifier.get("group") != "Video" or parameter.get("func") != function:
                    raise ValueError("preserve unfamiliar LUT intensity edge functions")
                matches.append(modifier)
    if len(matches) > 1:
        raise ValueError("inspect multiple LUT intensity fades before editing")
    if matches:
        modifier = matches[0]
        if (
            len(modifier["parameters"]) != 1
            and project.number(modifier.get("duration")) != duration
        ):
            raise ValueError("preserve shared edge timing; separate native controls before editing")
        modifier["duration"] = duration
    elif duration:
        effect.setdefault(key, []).append(
            dict(
                group="Video",
                duration=duration,
                parameters=[dict(name="lut_intensity", func=function)],
            )
        )


def edit_lut(
    doc: dict[str, Any],
    clip_id: int,
    spec: dict[str, Any],
    *,
    token: str | None = None,
    app: Path | None = None,
    user_root: Path | None = None,
) -> tuple[dict[str, Any], dict[str, Any] | None]:
    require_native(doc)
    fields = {"source", "intensity", "range", "easeIn", "easeOut", "bypassed"}
    if (
        not isinstance(spec, dict)
        or type(spec.get("schema_version")) is not int
        or spec.get("schema_version") != 1
        or set(spec) - (fields | {"schema_version"})
        or not (set(spec) & fields)
    ):
        raise ValueError("supply LUT schema_version 1 with supported LUT controls")
    resource = None
    if "source" in spec:
        if app is None:
            raise ValueError("supply --app to resolve an existing native LUT resource filename")
        resource = resolve_resource(app, spec["source"], user_root)
    if "range" in spec and (
        not isinstance(spec["range"], str) or spec["range"] not in RANGE_CHOICES
    ):
        raise ValueError("choose a native range from RANGE_CHOICES")
    if "bypassed" in spec and type(spec["bypassed"]) is not bool:
        raise ValueError("supply a boolean LUT bypass")
    intensity = project.number(spec["intensity"]) if "intensity" in spec else None
    if intensity is not None and not 0 <= intensity <= 1:
        raise ValueError("supply LUT intensity between 0 and 1")
    result = copy.deepcopy(doc)
    selected = effects.targets(result, clip_id, "LutEffect", token)
    edges = {key: hotspots.ticks(doc, spec[key]) for key in ("easeIn", "easeOut") if key in spec}
    if edges:
        duration = project.number(selected[0][0].get("duration"))
        if duration <= 0 or any(value > duration for value in edges.values()):
            raise ValueError("fit each LUT ease duration inside the displayed clip")
    for _, effect in selected:
        parameters = effect["parameters"]
        if resource is not None:
            if not isinstance(parameters.get("lutSource"), str):
                raise ValueError("inspect the existing native LUT filename selector before editing")
            parameters["lutSource"] = resource["name"]
        if intensity is not None:
            patch_double(parameters, "lut_intensity", float(intensity))
        if "range" in spec:
            channel, ramps = RANGE_CHOICES[spec["range"]]
            if type(parameters.get("channel")) is not int:
                raise ValueError("inspect the native integer LUT channel selector")
            parameters["channel"] = channel
            for name, value in zip(RAMP_NAMES, ramps):
                patch_double(parameters, name, value)
        if "bypassed" in spec:
            if type(effect.get("bypassed")) is not bool:
                raise ValueError("inspect the native boolean LUT bypass")
            effect["bypassed"] = spec["bypassed"]
        for key, field, function in [
            ("easeIn", "leftEdgeMods", "FadeInFunc"),
            ("easeOut", "rightEdgeMods", "FadeOutFunc"),
        ]:
            if key in edges:
                patch_edge(effect, field, function, edges[key])
    return result, resource


def inventory(doc: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for row in effects.inventory(doc):
        name = row["effect"].get("effectName")
        if not isinstance(name, str) or not name:
            raise ValueError(
                f"{row['path']}/effectName: restore a nonempty native visual-effect name"
            )
        if name == "LutEffect":
            result.append(row)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = JsonArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    command = commands.add_parser("resources")
    command.add_argument("--app", type=Path, required=True)
    for name in ("inspect", "set"):
        command = commands.add_parser(name)
        command.add_argument("project", type=Path)
        if name == "set":
            command.add_argument("--clip-id", type=int, required=True)
            command.add_argument("--effect-token")
            command.add_argument("--spec", type=Path, required=True)
            command.add_argument("--app", type=Path)
            command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        report: dict[str, Any] = dict(
            schema_version=1, owner="camtasia-luts", ok=True, nativeVerified=False
        )
        if args.command == "resources":
            report["resources"] = resources(args.app)
        else:
            doc, raw = project.load(args.project)
            require_native(doc)
            report["projectSha256"] = project.digest(raw)
            if args.command == "set":
                candidate, resource = edit_lut(
                    doc,
                    args.clip_id,
                    project.load(args.spec)[0],
                    token=args.effect_token,
                    app=args.app,
                )
                report.update(
                    effects=inventory(candidate),
                    resource=resource,
                    output=str(args.output),
                    written=hotspots.stage(args.project, args.output, candidate),
                    candidateSha256=project.digest(project.encode_document(candidate)),
                    changed=candidate != doc,
                )
            else:
                report["effects"] = inventory(doc)
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except (OSError, ValueError, OverflowError) as exc:
        print(json.dumps(dict(ok=False, error=str(exc)), ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
