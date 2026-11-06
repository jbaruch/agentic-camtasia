#!/usr/bin/env python3
"""Stage explicit created-cursor point paths on Mac 2026.2.4 format-10 video.

inspect PROJECT lists physical CursorPath effects. set-path PROJECT --clip-id ID
--spec SPEC --output CANDIDATE replaces only cursorLocation keyframes in an
existing native CursorPath. Select a root VMFile or its root UnifiedMedia
wrapper/video ID. Linked controls, clocks and canonical effectIndex tokens must
agree; both visual mirrors update while audio remains unchanged. Duplicate
paths, missing native effects, nested/recording/image/Group owners and recorded
cursor overrides refuse. Capture other owner contracts before using them.

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
this helper constructs no effect, recording override, click or cursor resource.

No editor is launched and no original project/media is written. Exclusive or
identical staging follows project diff/validate/apply and native save/reopen/
render checks. Stdout schema_version 1 owner camtasia-cursor-paths reports hashes,
inventory, changed/written and nativeVerified false. JSON diagnostics on stderr:
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


def set_path(doc: dict[str, Any], clip_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    if (
        not isinstance(spec, dict)
        or set(spec) != {"schema_version", "points"}
        or type(spec["schema_version"]) is not int
        or spec["schema_version"] != 1
    ):
        raise ValueError("supply cursor-path schema_version 1 with the complete points list")
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


def inventory(doc: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(clipId=node.get("id"), type=node.get("_type"), path=path, effect=effect)
        for path, node in hotspots.clips(doc)
        for effect in effects.effects_of(node)
        if effect.get("effectName") == "CursorPath"
    ]


def main(argv: list[str] | None = None) -> int:
    parser = JsonArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("project", type=Path)
    edit = commands.add_parser("set-path")
    edit.add_argument("project", type=Path)
    edit.add_argument("--clip-id", type=int, required=True)
    edit.add_argument("--spec", type=Path, required=True)
    edit.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        doc, raw = project.load(args.project)
        report: dict[str, Any] = dict(
            schema_version=1,
            owner="camtasia-cursor-paths",
            ok=True,
            projectSha256=project.digest(raw),
        )
        if args.command == "inspect":
            report["paths"] = inventory(doc)
        else:
            candidate = set_path(doc, args.clip_id, project.load(args.spec)[0])
            report.update(
                paths=inventory(candidate),
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
