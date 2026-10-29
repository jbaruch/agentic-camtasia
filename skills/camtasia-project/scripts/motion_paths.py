#!/usr/bin/env python3
"""Inspect and stage Mac 2026.2.4 format-10 Motion Path point curves.

inspect PROJECT reports physical MediaPath owners. set-path PROJECT --clip-id ID
--spec SPEC --output CANDIDATE creates or replaces the selected visual owner's
path. Wrapper/video IDs resolve to the same visual owner; audio is never edited.
OWNERS defines verified direct constructors; linked UnifiedMedia/VMFile edits
update both visual mirrors. Group/stitched children and recorded cursor data survive.
set-bypass PROJECT --clip-id ID --bypass|--no-bypass --output CANDIDATE changes
the selected path's bypass and observed orientation companion. remove-path removes that effect and its known
Auto Orient zero-rotation companion, retaining reset metadata and other effects.

Spec schema_version 1 requires points, a nonempty ordered array. Each point has
time (rational clip-relative timeline seconds), position ([x,y,z] finite canvas
coordinates), optional interpolation: a TIMINGS code or {"bezier":[control1,
control2, optional TIMINGS code]}. Interpolation belongs to the destination point.
No spline, insert-handle, framing or easing formula is inferred. Full explicit
point replacement supports insertion, removal, extension and line/handle editing.
Missing interpolation stays missing; subframe times are exact project ticks.
Existing same-time frame metadata and unrelated parameter/effect state survive.
Optional autoOrient is boolean; omission preserves the existing control. A new
path defaults to false. Turning it on adds the observed reset metadata/zero
rotation companion and refuses an existing nonzero/animated rotation. Turning
it off removes that zero-rotation companion and retains the reset metadata.

Linked mirrors must agree on path controls, clocks and stable effectIndex token.
New tokens are allocated beyond all linked effect tokens, preserving order and
unknown effects. Source-position clocks use the selected visual's mediaStart and
inverse speed. ScreenIMFile instead starts its path clock at local zero, still
using inverse speed; mediaStart independently selects the held source frame.
Auto Orient uses bare zero rotation except ScreenVMFile's RECORDING_ROTATION.
All verified owners omit that companion while bypassed, including orientation
edits made while the path remains disabled; enabling restores its native form.
No original document/media is written; exclusive/identical staging
uses the ordinary guarded project apply workflow. Stdout schema_version 1 owner
camtasia-motion-paths includes hashes/inventory, changed/written and nativeVerified
false. Exit 0 success, 1 input/I/O refusal, 2 invalid CLI. JSON errors use stderr.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any

import animations
import hotspots
import mattes
import project

TIMINGS = frozenset({"eioe", "esIn", "esOt", "linr"})
OWNERS = frozenset(
    {"VMFile", "IMFile", "Callout", "Group", "ScreenVMFile", "ScreenIMFile", "StitchedMedia"}
)
RECORDING_ROTATION = {"type": "double", "defaultValue": 0.0, "interp": "eioe"}


def vector(value: Any) -> list[int | float]:
    if not isinstance(value, list) or len(value) != 3:
        raise ValueError("supply three finite canvas coordinates per position/control point")
    result = []
    for number in value:
        checked = animations.value_number("coordinate", number)
        result.append(number if type(number) in (int, float) else checked)
    return result


def interpolation(value: Any) -> Any:
    if isinstance(value, str) and value in TIMINGS:
        return value
    if not isinstance(value, dict) or set(value) != {"bezier"}:
        raise ValueError("supply a TIMINGS code or the observed bezier interpolation object")
    controls = value["bezier"]
    if not isinstance(controls, list) or len(controls) not in (2, 3):
        raise ValueError("supply two Bézier control points and an optional timing code")
    result: list[Any] = [vector(controls[0]), vector(controls[1])]
    if len(controls) == 3:
        if not isinstance(controls[2], str) or controls[2] not in TIMINGS:
            raise ValueError("choose a Bézier timing code from TIMINGS")
        result.append(controls[2])
    return {"bezier": result}


def path_effect(node: dict[str, Any]) -> dict[str, Any] | None:
    found = [
        effect for effect in mattes.effects_of(node) if effect.get("effectName") == "MediaPath"
    ]
    if len(found) > 1:
        raise ValueError("inspect multiple Motion Path effects before selecting one")
    if not found:
        return None
    effect = found[0]
    if effect.get("category") != "categoryVisualEffects" or not isinstance(
        effect.get("parameters"), dict
    ):
        raise ValueError("inspect the unfamiliar native Motion Path effect")
    return effect


def visual_targets(doc: dict[str, Any], clip_id: int) -> list[dict[str, Any]]:
    path, visual = hotspots.visual_target(doc, clip_id, visual_types=OWNERS)
    wrappers = [
        n
        for p, n in hotspots.clips(doc)
        if n.get("_type") == "UnifiedMedia" and path == p + "/video"
    ]
    if visual.get("_type") not in OWNERS:
        raise ValueError("select a verified Motion Path visual owner from OWNERS")
    if not wrappers:
        path_effect(visual)
        return [visual]
    if visual.get("_type") != "VMFile" or len(wrappers) != 1:
        raise ValueError("select a verified linked UnifiedMedia/VMFile Motion Path owner")
    wrapper = wrappers[0]
    for key in ("start", "duration", "mediaStart", "mediaDuration", "scalar"):
        if project.number(wrapper.get(key)) != project.number(visual.get(key)):
            raise ValueError("repair conflicting linked visual clocks before path editing")
    first, second = path_effect(wrapper), path_effect(visual)
    if (first is None) != (second is None):
        raise ValueError("repair the missing linked Motion Path mirror")
    if first is not None and second is not None:
        token = mattes.effect_token(first)
        if token is None or token != mattes.effect_token(second):
            raise ValueError("repair conflicting linked Motion Path effectIndex tokens")
        for key in ("parameters", "bypassed", "leftEdgeMods", "rightEdgeMods"):
            if first.get(key) != second.get(key):
                raise ValueError("repair conflicting linked Motion Path controls")
    return [wrapper, visual]


def require_native(doc: dict[str, Any]) -> None:
    if doc.get("version") != "10.0" or doc.get("authoringClientName") != hotspots.NATIVE_CLIENT:
        raise ValueError("use the verified Mac 2026.2.4 format-10 Motion Path contract")


def zero_rotation_parameters(visual: dict[str, Any]) -> dict[str, Any]:
    parameters = visual.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("inspect the native visual geometry parameters")
    if "rotation2" in parameters:
        value = parameters["rotation2"]
        plain_zero = type(value) in (int, float) and value == 0
        recording_zero = (
            visual.get("_type") == "ScreenVMFile"
            and isinstance(value, dict)
            and type(value.get("defaultValue")) in (int, float)
            and value == RECORDING_ROTATION
        )
        if not plain_zero and not recording_zero:
            raise ValueError(
                "capture native Auto Orient behavior for the existing nonzero/animated rotation"
            )
    return parameters


def point_frames(
    doc: dict[str, Any], visual: dict[str, Any], points: Any, old: Any
) -> list[dict[str, Any]]:
    if not isinstance(points, list) or not points:
        raise ValueError("supply at least one ordered Motion Path point")
    if not isinstance(old, list):
        raise ValueError("inspect the native Motion Path keyframe array")
    old_by_time = {}
    for frame in old:
        if (
            not isinstance(frame, dict)
            or type(frame.get("time")) is not int
            or type(frame.get("duration")) is not int
            or frame["duration"] != 0
            or type(frame.get("endTime")) is not int
            or frame.get("endTime") != frame["time"]
            or frame["time"] in old_by_time
        ):
            raise ValueError("inspect ambiguous or non-point native Motion Path frames")
        old_by_time[frame["time"]] = frame
    result = []
    previous = None
    for point in points:
        if (
            not isinstance(point, dict)
            or not {"time", "position"} <= set(point)
            or set(point) - {"time", "position", "interpolation"}
        ):
            raise ValueError("supply point time, position and optional interpolation only")
        rate = project.number(doc.get("editRate"))
        scalar = project.number(visual.get("scalar"))
        if rate <= 0 or scalar <= 0:
            raise ValueError("repair positive project rate and visual inverse speed")
        origin = (
            0 if visual.get("_type") == "ScreenIMFile" else project.number(visual.get("mediaStart"))
        )
        time = origin + project.number(point["time"]) * rate / scalar
        if time.denominator != 1 or (previous is not None and time <= previous):
            raise ValueError("supply strictly increasing points on exact native project ticks")
        previous = time
        frame = copy.deepcopy(old_by_time.get(int(time), {}))
        frame.update(time=int(time), endTime=int(time), duration=0, value=vector(point["position"]))
        if "interpolation" in point:
            frame["interp"] = interpolation(point["interpolation"])
        else:
            frame.pop("interp", None)
        result.append(frame)
    return result


def set_path(doc: dict[str, Any], clip_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    require_native(doc)
    if (
        not isinstance(spec, dict)
        or type(spec.get("schema_version")) is not int
        or spec["schema_version"] != 1
        or "points" not in spec
        or set(spec) - {"schema_version", "points", "autoOrient"}
    ):
        raise ValueError("supply Motion Path schema_version 1, points and optional autoOrient")
    if "autoOrient" in spec and type(spec["autoOrient"]) is not bool:
        raise ValueError("supply a boolean autoOrient control")
    result = copy.deepcopy(doc)
    targets = visual_targets(result, clip_id)
    wrapper, visual = targets[0], targets[-1]
    metadata = wrapper.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("repair the native linked-media metadata object")
    existing = path_effect(visual)
    prior_orientation = existing["parameters"].get("mediaPathAutoOrient") if existing else 0
    if existing is None:
        token = mattes.next_effect_token(wrapper) if len(targets) == 2 else None
        for target in targets:
            created_effect: dict[str, Any] = {
                "effectName": "MediaPath",
                "bypassed": False,
                "category": "categoryVisualEffects",
                "parameters": {
                    "mediaLocation": {"type": "point", "keyframes": []},
                    "mediaPathAutoOrient": 0,
                },
            }
            if token is not None:
                created_effect["metadata"] = {"effectIndex": token}
            target.setdefault("effects", []).append(created_effect)
        wrapper.setdefault("metadata", {})["effectApplied"] = "MediaPath"
    for target in targets:
        effect = path_effect(target)
        if effect is None:
            raise ValueError("restore the selected native Motion Path effect")
        params = effect["parameters"]
        curve = params.get("mediaLocation")
        if not isinstance(curve, dict) or curve.get("type") != "point":
            raise ValueError("inspect the native mediaLocation point parameter")
        curve["keyframes"] = point_frames(
            result, visual, spec["points"], curve.get("keyframes", [])
        )
        if "autoOrient" in spec:
            if type(params.get("mediaPathAutoOrient")) is not int or params[
                "mediaPathAutoOrient"
            ] not in (0, 1):
                raise ValueError("inspect the native Motion Path orientation control")
            params["mediaPathAutoOrient"] = int(spec["autoOrient"])
    if spec.get("autoOrient"):
        parameters = zero_rotation_parameters(visual)
        wrapper.setdefault("metadata", {}).setdefault("default-MediaPath-mediaPathAutoOrient", "0")
        parameters["rotation2"] = (
            copy.deepcopy(RECORDING_ROTATION) if visual["_type"] == "ScreenVMFile" else 0.0
        )
        selected = path_effect(visual)
        if selected is None or type(selected.get("bypassed")) is not bool:
            raise ValueError("inspect native Motion Path bypass before changing orientation")
        if selected["bypassed"]:
            parameters.pop("rotation2", None)
    elif spec.get("autoOrient") is False and prior_orientation == 1:
        parameters = zero_rotation_parameters(visual)
        parameters.pop("rotation2", None)
    return result


def set_bypass(doc: dict[str, Any], clip_id: int, bypass: bool) -> dict[str, Any]:
    require_native(doc)
    if type(bypass) is not bool:
        raise ValueError("supply a boolean Motion Path bypass")
    result = copy.deepcopy(doc)
    targets = visual_targets(result, clip_id)
    for target in targets:
        effect = path_effect(target)
        if effect is None:
            raise ValueError("add a Motion Path before changing its bypass")
        effect["bypassed"] = bypass
    visual = targets[-1]
    selected = path_effect(visual)
    if selected is None:
        raise ValueError("restore the selected Motion Path before changing orientation")
    orientation = selected["parameters"].get("mediaPathAutoOrient")
    if type(orientation) is not int or orientation not in (0, 1):
        raise ValueError("inspect native Motion Path orientation before changing bypass")
    if orientation == 1:
        parameters = zero_rotation_parameters(visual)
        if bypass:
            parameters.pop("rotation2", None)
        else:
            parameters["rotation2"] = (
                copy.deepcopy(RECORDING_ROTATION) if visual["_type"] == "ScreenVMFile" else 0.0
            )
    return result


def remove_path(doc: dict[str, Any], clip_id: int) -> dict[str, Any]:
    require_native(doc)
    result = copy.deepcopy(doc)
    targets = visual_targets(result, clip_id)
    visual = targets[-1]
    effect = path_effect(visual)
    if effect is None:
        return result
    orientation = effect["parameters"].get("mediaPathAutoOrient")
    if type(orientation) is not int or orientation not in (0, 1):
        raise ValueError("inspect the native Motion Path orientation before removal")
    if orientation == 1:
        zero_rotation_parameters(visual).pop("rotation2", None)
    for target in targets:
        selected = path_effect(target)
        if selected is None:
            raise ValueError("restore matching Motion Path effect mirrors before removal")
        target["effects"].remove(selected)
    return result


def inventory(doc: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for path, node in hotspots.clips(doc):
        effect = path_effect(node)
        if effect is not None:
            rows.append(
                dict(clipId=node.get("id"), type=node.get("_type"), path=path, effect=effect)
            )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("project", type=Path)
    edit = commands.add_parser("set-path")
    edit.add_argument("project", type=Path)
    edit.add_argument("--clip-id", type=int, required=True)
    edit.add_argument("--spec", type=Path, required=True)
    edit.add_argument("--output", type=Path, required=True)
    bypass = commands.add_parser("set-bypass")
    bypass.add_argument("project", type=Path)
    bypass.add_argument("--clip-id", type=int, required=True)
    choice = bypass.add_mutually_exclusive_group(required=True)
    choice.add_argument("--bypass", dest="bypass", action="store_true")
    choice.add_argument("--no-bypass", dest="bypass", action="store_false")
    bypass.add_argument("--output", type=Path, required=True)
    remove = commands.add_parser("remove-path")
    remove.add_argument("project", type=Path)
    remove.add_argument("--clip-id", type=int, required=True)
    remove.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        doc, raw = project.load(args.project)
        report: dict[str, Any] = dict(
            schema_version=1,
            owner="camtasia-motion-paths",
            ok=True,
            projectSha256=project.digest(raw),
        )
        if args.command == "inspect":
            report["paths"] = inventory(doc)
        else:
            if args.command == "set-path":
                candidate = set_path(doc, args.clip_id, project.load(args.spec)[0])
            elif args.command == "set-bypass":
                candidate = set_bypass(doc, args.clip_id, args.bypass)
            else:
                candidate = remove_path(doc, args.clip_id)
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
