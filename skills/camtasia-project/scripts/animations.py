#!/usr/bin/env python3
"""Inspect and stage native Mac 2026.2.4 format-10 visual animation intervals.

inspect PROJECT is read-only. set-interval PROJECT --clip-id ID --spec SPEC
--output CANDIDATE stages one coupled interval. ease-interval PROJECT --clip-id
ID --start SECONDS --end SECONDS --easing CHOICE --output CANDIDATE changes an
existing interval's easing and its matching geometry keyframes together.
remove-interval PROJECT --clip-id ID --start SECONDS --end SECONDS --output
CANDIDATE removes a coupled visual interval and its known geometry frames.

Spec schema_version 1 requires start/end rational clip-relative timeline seconds
and values (property-to-target object); optional initial supplies missing
parameter defaults, easing selects interval/frame interpolation, and
parameterEasing explicitly selects parameter-level interpolation. EASINGS owns
the saved codes; auto omits that field without resetting other interpolation
owners. set-interval accepts empty values for a native Custom interval marker;
ease-interval still requires an existing interval. The Python API uses the
explicit allow_empty keyword for marker creation.
PROPERTIES and OWNERS define the verified geometric parameters/visual owners.
Linked IDs resolve to the video child; wrapper, audio, effects and sources stay
unchanged. New missing parameters require explicit initial values; existing
defaults cannot be changed implicitly. Source-position bounds use project ticks
through mediaStart/scalar; ScreenIMFile uses a local zero origin with the same
inverse-speed conversion while mediaStart selects its held source frame.
Negative starts and exact subframe bounds are legal.

New intervals cannot overlap existing intervals. Matching intervals/frames are
updated in place, retaining opaque fields. Existing parameter-level easing and
all unrelated curves survive. An explicit global easing change updates every
matching known geometry frame; unknown/effect-owned coupled curves are refused.
This is curve authoring/editing, not SmartFocus subject detection or a preset
framing formula. Removal retains other intervals, their frames and initial
geometry. Last-frame removal collapses plain parameters to their initial values;
REMOVAL_DEFAULTS identifies omitted native defaults, while crop zeroes stay
explicit. Extra parameter fields remain typed and survive without their removed
frames. Absent intervals are no-ops only without orphaned coupled frames.
Unknown/effect-owned coupling, overlaps and geometry point frames are refused.
Images, Callouts and Groups retain their own source clocks and child data;
Group descendant transforms are not rewritten when editing the parent.
Frozen ScreenIMFile and StitchedMedia retain source selection, virtual hold
duration, child clocks and recorded cursor data. interval_properties recognizes
their native constant cursorScale companion for coupled easing/removal; dynamic
cursor curves remain outside this geometry authoring contract.

Never writes the input project/media or launches an editor. Candidate staging
uses the project workflow; stdout schema_version 1 owner camtasia-animations
includes hashes, inventory, changed/written and nativeVerified false. Exit 0
success, 1 input/I/O refusal, 2 CLI syntax. Diagnostics are JSON on stderr.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any

import hotspots
import project

OWNERS = frozenset(
    {"VMFile", "ScreenVMFile", "IMFile", "ScreenIMFile", "Callout", "Group", "StitchedMedia"}
)
PROPERTIES = frozenset(
    {
        "scale0",
        "scale1",
        "opacity",
        "translation0",
        "translation1",
        "translation2",
        "rotation0",
        "rotation1",
        "rotation2",
        "geometryCrop0",
        "geometryCrop1",
        "geometryCrop2",
        "geometryCrop3",
    }
)
EASINGS = {
    "auto": None,
    "linear": "linr",
    "exponential": "eioe",
    "bounce": "bnce",
    "spring": "sprg",
}
REMOVAL_DEFAULTS = {
    "scale0": 1.0,
    "scale1": 1.0,
    "opacity": 1.0,
    "translation0": 0.0,
    "translation1": 0.0,
    "translation2": 0.0,
    "rotation0": 0.0,
    "rotation1": 0.0,
    "rotation2": 0.0,
}


def value_number(name: str, value: Any) -> float:
    try:
        result = float(project.number(value))
    except OverflowError as exc:
        raise ValueError("supply geometry values representable as native finite doubles") from exc
    if name == "opacity" and not 0 <= result <= 1:
        raise ValueError("supply opacity between 0 and 1")
    # Fraction accepts arbitrarily large integers; native geometry is binary64.
    if not (-sys.float_info.max <= result <= sys.float_info.max):
        raise ValueError("supply finite native geometry values")
    return result


def interpolation(value: Any) -> str | None:
    if not isinstance(value, str) or value not in EASINGS:
        raise ValueError("choose an easing from EASINGS")
    return EASINGS[value]


def set_interp(owner: dict[str, Any], code: str | None) -> None:
    if code is None:
        owner.pop("interp", None)
    else:
        owner["interp"] = code


def source_bounds(
    doc: dict[str, Any], owner: dict[str, Any], start: Any, end: Any
) -> tuple[int, int]:
    rate = project.number(doc.get("editRate"))
    scalar = project.number(owner.get("scalar"))
    if rate <= 0 or scalar <= 0:
        raise ValueError("repair positive project rate and visual inverse speed")
    frozen_recording = owner.get("_type") == "ScreenIMFile"
    start_value, end_value = project.number(start), project.number(end)
    if start_value >= end_value:
        raise ValueError("supply an animation end after its start")
    bounds = [
        (0 if frozen_recording else project.number(owner.get("mediaStart"))) + point * rate / scalar
        for point in (start_value, end_value)
    ]
    if any(point.denominator != 1 for point in bounds):
        raise ValueError("choose animation bounds that map to exact native project ticks")
    return int(bounds[0]), int(bounds[1])


def interval_bounds(interval: Any) -> tuple[int, int]:
    if (
        not isinstance(interval, dict)
        or type(interval.get("endTime")) is not int
        or type(interval.get("duration")) is not int
        or interval["duration"] <= 0
    ):
        raise ValueError("preserve unfamiliar visual intervals; inspect their native timing")
    return interval["endTime"] - interval["duration"], interval["endTime"]


def frame_bounds(frame: Any) -> tuple[int, int]:
    bounds = interval_bounds(frame)
    if type(frame.get("time")) is not int or frame["time"] != bounds[0]:
        raise ValueError("preserve unfamiliar keyframe clocks; capture a native example")
    return bounds


def overlaps(first: tuple[int, int], second: tuple[int, int]) -> bool:
    return max(first[0], second[0]) < min(first[1], second[1])


def parameter_frames(parameter: dict[str, Any]) -> list[dict[str, Any]]:
    frames = parameter.get("keyframes", [])
    if not isinstance(frames, list):
        raise ValueError("inspect the native geometry keyframe array")
    return frames


def has_coupled_frame(parameter: dict[str, Any], bounds: tuple[int, int]) -> bool:
    for frame in parameter_frames(parameter):
        if (
            isinstance(frame, dict)
            and type(frame.get("duration")) is int
            and frame["duration"] == 0
            and type(frame.get("time")) is int
            and frame["time"] == frame.get("endTime")
        ):
            continue
        if frame_bounds(frame) == bounds:
            return True
    return False


def interval_properties(owner: dict[str, Any], bounds: tuple[int, int]) -> frozenset[str]:
    """Include the native constant cursor-size companion on frozen/stitched intervals.

    Fresh native loading creates cursorScale frames alongside parent geometry.
    Only constant double interval frames qualify; dynamic/point cursor scaling
    retains the existing unknown-coupling refusal. Input authoring still accepts
    PROPERTIES only, so this does not construct cursor animation controls.
    """
    if owner.get("_type") not in {"StitchedMedia", "ScreenIMFile"}:
        return PROPERTIES
    parameter = owner.get("parameters", {}).get("cursorScale")
    if not isinstance(parameter, dict) or parameter.get("type") != "double":
        return PROPERTIES
    frames = parameter_frames(parameter)
    if not frames or type(parameter.get("defaultValue")) not in (int, float):
        return PROPERTIES
    default = value_number("cursorScale", parameter["defaultValue"])
    if any(
        not isinstance(frame, dict)
        or type(frame.get("duration")) is not int
        or frame["duration"] <= 0
        or type(frame.get("value")) not in (int, float)
        or value_number("cursorScale", frame["value"]) != default
        for frame in frames
    ):
        return PROPERTIES
    if any(frame_bounds(frame) == bounds for frame in frames):
        return PROPERTIES | {"cursorScale"}
    return PROPERTIES


def edit_interval(
    doc: dict[str, Any], clip_id: int, spec: dict[str, Any], *, allow_empty: bool = False
) -> dict[str, Any]:
    if doc.get("version") != "10.0" or doc.get("authoringClientName") != hotspots.NATIVE_CLIENT:
        raise ValueError("use the verified Mac 2026.2.4 format-10 animation contract")
    required = {"schema_version", "start", "end", "values"}
    if (
        not isinstance(spec, dict)
        or not required <= set(spec)
        or set(spec) - required - {"initial", "easing", "parameterEasing"}
        or type(spec["schema_version"]) is not int
        or spec["schema_version"] != 1
    ):
        raise ValueError("supply animation schema_version 1, start, end and values")
    values, initial, parameter_easing = (
        spec["values"],
        spec.get("initial", {}),
        spec.get("parameterEasing", {}),
    )
    if (
        not all(isinstance(item, dict) for item in (values, initial, parameter_easing))
        or set(values) - PROPERTIES
        or set(initial) - set(values)
        or set(parameter_easing) - set(values)
    ):
        raise ValueError(
            "use known geometry properties; initial/parameterEasing must name requested values"
        )
    if not values and "easing" not in spec and not allow_empty:
        raise ValueError(
            "supply target geometry values or an explicit existing-interval easing change"
        )
    code = interpolation(spec["easing"]) if "easing" in spec else None
    result = copy.deepcopy(doc)
    _, owner = hotspots.visual_target(result, clip_id, visual_types=OWNERS)
    if owner.get("_type") not in OWNERS:
        raise ValueError("select a verified visual animation owner from OWNERS")
    bounds = source_bounds(result, owner, spec["start"], spec["end"])
    tracks = owner.setdefault("animationTracks", {})
    if not isinstance(tracks, dict) or not isinstance(tracks.get("visual", []), list):
        raise ValueError("inspect the native visual animation track")
    intervals = tracks.setdefault("visual", [])
    matched = [entry for entry in intervals if interval_bounds(entry) == bounds]
    if len(matched) > 1 or any(
        interval_bounds(entry) != bounds and overlaps(interval_bounds(entry), bounds)
        for entry in intervals
    ):
        raise ValueError("select a unique nonoverlapping native animation interval")
    if not matched and not values and not allow_empty:
        raise ValueError("select an existing interval before changing only its easing")
    parameters = owner.get("parameters")
    if not isinstance(parameters, dict):
        raise ValueError("inspect the visual owner's native parameters")
    coupled_properties = interval_properties(owner, bounds)
    if not matched and not values:
        for _, parameter in project.objects([parameters, owner.get("effects", [])]):
            if parameter.get("keyframes") and has_coupled_frame(parameter, bounds):
                raise ValueError("repair orphaned coupled frames before adding an empty interval")
    if "easing" in spec:
        for name, parameter in parameters.items():
            if (
                isinstance(parameter, dict)
                and parameter.get("keyframes")
                and name not in coupled_properties
            ):
                if has_coupled_frame(parameter, bounds):
                    raise ValueError("preserve unknown curves coupled to this animation interval")
        for _, parameter in project.objects(owner.get("effects", [])):
            if parameter.get("keyframes") and has_coupled_frame(parameter, bounds):
                raise ValueError(
                    "preserve effect-owned easing; capture its coupled native contract"
                )
    for name, target in values.items():
        if name not in parameters:
            if name not in initial:
                raise ValueError(
                    "supply an explicit initial value for missing geometry parameter: " + name
                )
            parameters[name] = {"type": "double", "defaultValue": value_number(name, initial[name])}
        elif type(parameters[name]) in (int, float):
            parameters[name] = {
                "type": "double",
                "defaultValue": value_number(name, parameters[name]),
            }
        parameter = parameters[name]
        if not isinstance(parameter, dict) or parameter.get("type") != "double":
            raise ValueError("preserve unfamiliar geometry parameter types: " + name)
        default = value_number(name, parameter.get("defaultValue"))
        if name in initial and default != value_number(name, initial[name]):
            raise ValueError(
                "preserve the existing initial value before editing an interval: " + name
            )
        frames = parameter_frames(parameter)
        hits = [frame for frame in frames if frame_bounds(frame) == bounds]
        if len(hits) > 1 or any(
            frame_bounds(frame) != bounds and overlaps(frame_bounds(frame), bounds)
            for frame in frames
        ):
            raise ValueError("preserve ambiguous or overlapping geometry curves: " + name)
        frame: dict[str, Any]
        if hits:
            frame = hits[0]
        else:
            frame = {"time": bounds[0], "endTime": bounds[1], "duration": bounds[1] - bounds[0]}
            if matched and "easing" not in spec and "interp" in matched[0]:
                if matched[0]["interp"] not in EASINGS.values():
                    raise ValueError(
                        "capture the unfamiliar interval interpolation before adding a curve"
                    )
                frame["interp"] = matched[0]["interp"]
            frames.append(frame)
            frames.sort(key=lambda entry: frame_bounds(entry))
            parameter["keyframes"] = frames
        frame["value"] = value_number(name, target)
        if name in parameter_easing:
            set_interp(parameter, interpolation(parameter_easing[name]))
    if matched:
        interval = matched[0]
    else:
        interval = {"endTime": bounds[1], "duration": bounds[1] - bounds[0]}
        intervals.append(interval)
        intervals.sort(key=interval_bounds)
    if "easing" in spec:
        set_interp(interval, code)
        for name, parameter in parameters.items():
            if (
                name in coupled_properties
                and isinstance(parameter, dict)
                and parameter.get("keyframes")
            ):
                if parameter.get("type") != "double":
                    raise ValueError("inspect a coupled geometry parameter's native type")
                for frame in parameter_frames(parameter):
                    if frame_bounds(frame) == bounds:
                        set_interp(frame, code)
    return result


def remove_interval(doc: dict[str, Any], clip_id: int, start: Any, end: Any) -> dict[str, Any]:
    """Remove one native interval without changing the retained initial/target geometry."""
    if doc.get("version") != "10.0" or doc.get("authoringClientName") != hotspots.NATIVE_CLIENT:
        raise ValueError("use the verified Mac 2026.2.4 format-10 animation contract")
    result = copy.deepcopy(doc)
    _, owner = hotspots.visual_target(result, clip_id, visual_types=OWNERS)
    if owner.get("_type") not in OWNERS:
        raise ValueError("select a verified visual animation owner from OWNERS")
    bounds = source_bounds(result, owner, start, end)
    tracks, parameters = owner.get("animationTracks", {}), owner.get("parameters", {})
    if not isinstance(tracks, dict) or not isinstance(tracks.get("visual", []), list):
        raise ValueError("inspect the native visual animation track")
    if not isinstance(parameters, dict):
        raise ValueError("inspect the visual owner's native parameters")
    coupled_properties = interval_properties(owner, bounds)
    intervals = tracks.get("visual", [])
    matched = [entry for entry in intervals if interval_bounds(entry) == bounds]
    if len(matched) > 1 or any(
        interval_bounds(entry) != bounds and overlaps(interval_bounds(entry), bounds)
        for entry in intervals
    ):
        raise ValueError("select a unique nonoverlapping native animation interval")
    changed_parameters: list[str] = []
    for name, parameter in list(parameters.items()):
        if not isinstance(parameter, dict):
            continue
        if name not in coupled_properties:
            if has_coupled_frame(parameter, bounds):
                raise ValueError("preserve unknown curves coupled to this animation interval")
            continue
        frames = parameter_frames(parameter)
        hits = [frame for frame in frames if frame_bounds(frame) == bounds]
        if len(hits) > 1 or any(
            frame_bounds(frame) != bounds and overlaps(frame_bounds(frame), bounds)
            for frame in frames
        ):
            raise ValueError("preserve ambiguous or overlapping geometry curves: " + name)
        if not hits:
            continue
        if not matched:
            raise ValueError("repair orphaned geometry frames before removing an absent interval")
        if parameter.get("type") != "double":
            raise ValueError("preserve unfamiliar geometry parameter types: " + name)
        default = value_number(name, parameter.get("defaultValue"))
        kept = [frame for frame in frames if frame_bounds(frame) != bounds]
        if kept:
            parameter["keyframes"] = kept
        elif set(parameter) - {"type", "defaultValue", "keyframes"}:
            # Do not discard parameter-level interpolation, UI hints or opaque data.
            parameter.pop("keyframes", None)
        elif name in REMOVAL_DEFAULTS and default == REMOVAL_DEFAULTS[name]:
            del parameters[name]
        else:
            parameters[name] = default
        changed_parameters.append(name)
    for _, parameter in project.objects(owner.get("effects", [])):
        if parameter.get("keyframes") and has_coupled_frame(parameter, bounds):
            raise ValueError("preserve effect-owned curves coupled to this animation interval")
    if not matched:
        return result
    if changed_parameters:
        owner["parameters"] = parameters
    kept_intervals = [entry for entry in intervals if interval_bounds(entry) != bounds]
    if kept_intervals:
        tracks["visual"] = kept_intervals
    else:
        tracks.pop("visual", None)
    return result


def inventory(doc: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for path, owner in hotspots.clips(doc):
        if not isinstance(owner.get("parameters", {}), dict) or not isinstance(
            owner.get("animationTracks", {}), dict
        ):
            raise ValueError("inspect malformed native parameters or animation tracks")
        curves = {
            name: parameter
            for name, parameter in owner.get("parameters", {}).items()
            if isinstance(parameter, dict) and parameter.get("keyframes")
        }
        tracks = owner.get("animationTracks", {})
        if curves or tracks.get("visual"):
            result.append(
                {
                    "clipId": owner.get("id"),
                    "type": owner.get("_type"),
                    "path": path,
                    "visualIntervals": tracks.get("visual", []),
                    "parameterCurves": curves,
                }
            )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("project", type=Path)
    edit = commands.add_parser("set-interval")
    edit.add_argument("project", type=Path)
    edit.add_argument("--clip-id", type=int, required=True)
    edit.add_argument("--spec", type=Path, required=True)
    edit.add_argument("--output", type=Path, required=True)
    ease = commands.add_parser("ease-interval")
    ease.add_argument("project", type=Path)
    ease.add_argument("--clip-id", type=int, required=True)
    ease.add_argument("--start", required=True)
    ease.add_argument("--end", required=True)
    ease.add_argument("--easing", choices=EASINGS, required=True)
    ease.add_argument("--output", type=Path, required=True)
    remove = commands.add_parser("remove-interval")
    remove.add_argument("project", type=Path)
    remove.add_argument("--clip-id", type=int, required=True)
    remove.add_argument("--start", required=True)
    remove.add_argument("--end", required=True)
    remove.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        doc, raw = project.load(args.project)
        report = {
            "schema_version": 1,
            "owner": "camtasia-animations",
            "ok": True,
            "projectSha256": project.digest(raw),
        }
        if args.command == "inspect":
            report["animations"] = inventory(doc)
        else:
            if args.command == "remove-interval":
                candidate = remove_interval(doc, args.clip_id, args.start, args.end)
            else:
                spec = (
                    project.load(args.spec)[0]
                    if args.command == "set-interval"
                    else {
                        "schema_version": 1,
                        "start": args.start,
                        "end": args.end,
                        "values": {},
                        "easing": args.easing,
                    }
                )
                candidate = edit_interval(
                    doc, args.clip_id, spec, allow_empty=args.command == "set-interval"
                )
            report.update(
                animations=inventory(candidate),
                output=str(args.output),
                written=hotspots.stage(args.project, args.output, candidate),
                candidateSha256=project.digest(project.encode_document(candidate)),
                changed=candidate != doc,
                nativeVerified=False,
            )
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except (OSError, ValueError, OverflowError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
