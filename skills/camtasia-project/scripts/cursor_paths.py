#!/usr/bin/env python3
"""Stage explicit created and recorded cursor paths on Mac 2026.2.4 format 10.

inspect PROJECT lists physical CursorPath effects. set-path PROJECT --clip-id ID
--spec SPEC --output CANDIDATE replaces only cursorLocation keyframes in an
existing native CursorPath. Select a root VMFile or its root UnifiedMedia
wrapper/video ID. Linked controls, clocks and canonical effectIndex tokens must
agree; both visual mirrors update while audio remains unchanged. Duplicate
paths, missing native effects, nested/recording/image/Group owners and recorded
cursor overrides refuse. Capture other owner contracts before using them.

set-recorded-path PROJECT --clip-id ID --spec SPEC --output CANDIDATE creates
or replaces a complete cursorLocation override on a standalone root ScreenVMFile.
The native recording representation is ignoreSource true plus edits containing
source-clock time/value and optional interp; it is not a CursorPath effect or
typed keyframe array. restore-recorded-path removes only a known complete
override, returning to the original TREC path; an absent override is a no-op.
Partial source edits/deletions, linked/nested/frozen/stitched recordings and
unfamiliar override shapes refuse. Source files and recorded clicks stay intact.

Spec schema_version 1 requires points: a nonempty ordered list with time
(rational clip-relative timeline seconds), position ([x,y,0]) and optional
interpolation. TIMINGS and the shared Motion Path point compiler own native
timing tokens and explicit {"bezier":[control1,control2,optional timing]} shapes.
Coordinates and handles use the unscaled source image plane, not canvas/media
translation. No automatic handle adjustment, spline or UI easing mapping is
inferred. Supply the complete desired point list for insertion/deletion/retiming.

Source ticks equal mediaStart + time * editRate / scalar. Times must land on
exact nonnegative native ticks and increase strictly. Points outside the visible
trim may survive; the helper does not clip them to the media interval. Same-time
frame metadata survives; removed/re-timed frames do not donate opaque metadata
to another point. Existing native point shape and interpolation must be known.
Missing interpolation stays missing. All other parameter/effect/owner fields,
cursor image paths, click events, smoothing, scale, opacity, geometry, sources
and audio survive. Built-in/custom cursor resources still need host verification.
Use effects.py for its existing bypass/removal or matching-template contract;
this helper constructs no effect, click or cursor resource. Recorded commands
construct only the complete native override above, never a recording or TREC.

No editor is launched and no original project/media is written. Exclusive or
identical staging follows project diff/validate/apply and native save/reopen/
render checks. Stdout schema_version 2 owner camtasia-cursor-paths retains the
version-1 fields and adds recordings inventory. Input specs remain version 1.
Reports include hashes, inventory, changed/written and nativeVerified false.
JSON diagnostics on stderr:
exit 1 input/I/O refusal, 2 CLI syntax; exit 0 success. --help is plaintext stdout.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any, NoReturn

import effects
import hotspots
import motion_paths
import project

OWNERS = frozenset({"VMFile"})
RECORDING_OWNERS = frozenset({"ScreenVMFile"})
TIMINGS = motion_paths.TIMINGS


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.exit(2, json.dumps(dict(ok=False, error=message), ensure_ascii=False) + "\n")


def planar_vector(value: Any) -> None:
    if motion_paths.vector(value)[2] != 0:
        raise ValueError("supply cursor positions and handles in the [x,y,0] source image plane")


def selected(doc: dict[str, Any], clip_id: int) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    if doc.get("version") != "10.0" or doc.get("authoringClientName") != hotspots.NATIVE_CLIENT:
        raise ValueError("use the verified Mac 2026.2.4 format-10 created-cursor path contract")
    path, visual = hotspots.visual_target(doc, clip_id, visual_types=OWNERS)
    ancestors = [(p, n) for p, n in hotspots.clips(doc) if path.startswith(p + "/")]
    if any(n.get("_type") != "UnifiedMedia" or path != p + "/video" for p, n in ancestors):
        raise ValueError("select a root video or root linked video; capture nested cursor clocks")
    targets = effects.targets(doc, clip_id, "CursorPath", None, visual_types=OWNERS)
    for owner, effect in targets:
        if type(effect.get("bypassed")) is not bool:
            raise ValueError("capture the native boolean CursorPath bypass before editing")
        if any(
            project.number(owner.get(key)) != project.number(visual.get(key))
            for key in effects.CLOCK_FIELDS
        ):
            raise ValueError("repair conflicting linked owner clocks before cursor path editing")
        if effects.token_of(effect) is None:
            raise ValueError("capture a native CursorPath effectIndex token before editing")
    if project.number(doc.get("editRate")) <= 0 or project.number(visual.get("scalar")) <= 0:
        raise ValueError("repair the positive project edit rate and visual inverse speed")
    return targets


def curve_of(effect: dict[str, Any]) -> dict[str, Any]:
    curve = effect["parameters"].get("cursorLocation")
    if (
        not isinstance(curve, dict)
        or curve.get("type") != "point"
        or {"defaultValue", "edits", "deletions", "ignoreSource", "interp"} & curve.keys()
        or not isinstance(curve.get("keyframes"), list)
        or not curve["keyframes"]
    ):
        raise ValueError("capture an existing native cursorLocation point keyframe descriptor")
    previous = -1
    for frame in curve["keyframes"]:
        if (
            not isinstance(frame, dict)
            or type(frame.get("time")) is not int
            or frame["time"] <= previous
            or type(frame.get("endTime")) is not int
            or frame["endTime"] != frame["time"]
            or type(frame.get("duration")) is not int
            or frame["duration"] != 0
        ):
            raise ValueError("capture ordered nonnegative native cursor point frames")
        planar_vector(frame.get("value"))
        if "interp" in frame:
            interp = motion_paths.interpolation(frame["interp"])
            if isinstance(interp, dict):
                for control in interp["bezier"][:2]:
                    planar_vector(control)
        previous = frame["time"]
    return curve


def check_spec(spec: dict[str, Any]) -> None:
    if (
        not isinstance(spec, dict)
        or set(spec) != {"schema_version", "points"}
        or type(spec["schema_version"]) is not int
        or spec["schema_version"] != 1
    ):
        raise ValueError("supply cursor-path schema_version 1 with the complete points list")


def set_path(doc: dict[str, Any], clip_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    check_spec(spec)
    result = copy.deepcopy(doc)
    targets = selected(result, clip_id)
    visual = targets[-1][0]
    for _, effect in targets:
        curve = curve_of(effect)
        frames = motion_paths.point_frames(
            result, visual, spec["points"], curve["keyframes"], label="Cursor Path"
        )
        checked = copy.deepcopy(curve)
        checked["keyframes"] = frames
        curve_of({"parameters": {"cursorLocation": checked}})
        curve["keyframes"] = frames
    return result


def recording_target(doc: dict[str, Any], clip_id: int) -> dict[str, Any]:
    if doc.get("version") != "10.0" or doc.get("authoringClientName") != hotspots.NATIVE_CLIENT:
        raise ValueError("use the verified Mac 2026.2.4 format-10 recorded cursor contract")
    path, owner = hotspots.visual_target(doc, clip_id, visual_types=RECORDING_OWNERS)
    if any(path.startswith(parent + "/") for parent, _ in hotspots.clips(doc)):
        raise ValueError("select a standalone root moving recording; capture other cursor clocks")
    if not isinstance(owner.get("parameters"), dict):
        raise ValueError("capture the native recording parameters before editing its cursor")
    if any(effect.get("effectName") == "CursorPath" for effect in effects.effects_of(owner)):
        raise ValueError("capture native recording cursor ownership without a CursorPath effect")
    if project.number(doc.get("editRate")) <= 0 or project.number(owner.get("scalar")) <= 0:
        raise ValueError("repair the positive project edit rate and recording inverse speed")
    return owner


def recorded_frames(override: Any) -> list[dict[str, Any]]:
    """Adapt complete recording edits to the shared point compiler's frame form."""
    if (
        not isinstance(override, dict)
        or override.get("ignoreSource") is not True
        or {"type", "keyframes", "defaultValue", "deletions", "interp"} & override.keys()
        or not isinstance(override.get("edits"), list)
        or not override["edits"]
    ):
        raise ValueError("capture a complete ignoreSource true recording path with nonempty edits")
    frames = []
    for edit in override["edits"]:
        if (
            not isinstance(edit, dict)
            or {
                "endTime",
                "duration",
                "type",
                "keyframes",
                "defaultValue",
                "edits",
                "deletions",
                "ignoreSource",
            }
            & edit.keys()
        ):
            raise ValueError("capture recorded time/value edits, not typed point keyframes")
        frame = copy.deepcopy(edit)
        frame.update(endTime=edit.get("time"), duration=0)
        frames.append(frame)
    curve_of({"parameters": {"cursorLocation": {"type": "point", "keyframes": frames}}})
    return frames


def set_recorded_path(doc: dict[str, Any], clip_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    check_spec(spec)
    result = copy.deepcopy(doc)
    owner = recording_target(result, clip_id)
    parameters = owner["parameters"]
    override = parameters.get("cursorLocation")
    old = recorded_frames(override) if "cursorLocation" in parameters else []
    frames = motion_paths.point_frames(
        result, owner, spec["points"], old, label="Recorded Cursor Path"
    )
    candidate: dict[str, Any] = (
        copy.deepcopy(override) if override is not None else {"ignoreSource": True}
    )
    candidate["edits"] = [
        {key: value for key, value in frame.items() if key not in {"endTime", "duration"}}
        for frame in frames
    ]
    recorded_frames(candidate)
    parameters["cursorLocation"] = candidate
    return result


def restore_recorded_path(doc: dict[str, Any], clip_id: int) -> dict[str, Any]:
    result = copy.deepcopy(doc)
    parameters = recording_target(result, clip_id)["parameters"]
    if "cursorLocation" in parameters:
        recorded_frames(parameters["cursorLocation"])
        parameters.pop("cursorLocation")
    return result


def inventory(doc: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(clipId=node.get("id"), type=node.get("_type"), path=path, effect=effect)
        for path, node in hotspots.clips(doc)
        for effect in effects.effects_of(node)
        if effect.get("effectName") == "CursorPath"
    ]


def recording_inventory(doc: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for path, node in hotspots.clips(doc):
        if node.get("_type") not in RECORDING_OWNERS:
            continue
        parameters = node.get("parameters")
        if not isinstance(parameters, dict):
            raise ValueError("inspect the native recording parameters before cursor inventory")
        rows.append(
            dict(
                clipId=node.get("id"),
                type=node["_type"],
                path=path,
                override=copy.deepcopy(parameters.get("cursorLocation")),
            )
        )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = JsonArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("project", type=Path)
    for command in ("set-path", "set-recorded-path", "restore-recorded-path"):
        edit = commands.add_parser(command)
        edit.add_argument("project", type=Path)
        edit.add_argument("--clip-id", type=int, required=True)
        if command != "restore-recorded-path":
            edit.add_argument("--spec", type=Path, required=True)
        edit.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        doc, raw = project.load(args.project)
        report: dict[str, Any] = dict(
            schema_version=2,
            owner="camtasia-cursor-paths",
            ok=True,
            projectSha256=project.digest(raw),
        )
        if args.command == "inspect":
            report["paths"] = inventory(doc)
            report["recordings"] = recording_inventory(doc)
        else:
            if args.command == "set-path":
                candidate = set_path(doc, args.clip_id, project.load(args.spec)[0])
            elif args.command == "set-recorded-path":
                candidate = set_recorded_path(doc, args.clip_id, project.load(args.spec)[0])
            else:
                candidate = restore_recorded_path(doc, args.clip_id)
            report.update(
                paths=inventory(candidate),
                recordings=recording_inventory(candidate),
                output=str(args.output),
                written=hotspots.stage(args.project, args.output, candidate),
                candidateSha256=project.digest(project.encode_document(candidate)),
                changed=candidate != doc,
                nativeVerified=False,
            )
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except (OSError, ValueError, OverflowError) as exc:
        print(json.dumps(dict(ok=False, error=str(exc)), ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
