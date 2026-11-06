#!/usr/bin/env python3
"""Stage interval curves on existing typed native visual-effect double parameters.

inspect PROJECT inventories effects. set PROJECT --clip-id ID --effect NAME
[--effect-token TOKEN] --parameter NAME --spec SPEC --output CANDIDATE replaces
only the selected parameter's default and complete interval curve. clear uses
--value SCALAR instead of --spec and removes only that parameter's keyframes.

Spec schema_version 1 requires defaultValue and nonempty segments, each with
start/end rational clip-relative timeline seconds and target value. Gaps hold
the preceding value. Raw native units are required; existing valueBounds apply.
Version 1 stays linear. Version 2 adds optional per-segment easing: linear
(default), exponential, bounce or spring, using animations.EASINGS codes.
Default/target bounds remain enforced; native spring interpolation can overshoot.
Exact project ticks use the visual source clock (mediaStart/inverse speed).
OWNERS names visual owners verified for these clocks; linked wrapper
and video clocks must agree. Only Mac 2026.2.4/format 10 is admitted. Existing
native typed double descriptors are required; no scalar, resource, point,
integer, boolean, missing parameter or effect constructor is inferred. MediaPath
retains its dedicated motion_paths.py coupling and is refused here.

Existing interval-shaped selected frames are explicitly replaced; unknown or
point frames are refused. Version 1 sets parameter/frame interpolation linear
and refuses conflicting interval easing. Version 2 removes parameter-level
interpolation and selects each frame's easing explicitly; existing matching
visual intervals retain their known easing and unrelated geometry. New
nonoverlapping intervals use the requested easing on the visual owner only.
Unknown interval easing and overlapping bounds refuse.
Clear preserves descriptors, parameter interpolation, all visual intervals and
other curves. Native save can regenerate constant frames from retained visual
intervals. Reset metadata, stable effect tokens, edges, audio and sources survive.
Structural success is not native rendering verification for a new combination.

Direct moving/frozen recordings and stitched parents use their existing effects.
ScreenIMFile intervals have a local-zero origin, independent of the held source
frame in mediaStart; other owners retain source-position clocks. Stitched edits
retain descendants, virtual hold durations, cursor data and source processing.
Root linked moving ScreenVMFile recordings use matching wrapper/video mirrors,
complete shared clocks and the source/audio/token guard in effects.constructor_owners.
Recorded audio is preserved. Linked held, stitched and nested variants retain
separate contracts. Ordinary linked AV keeps its existing mirror contract.
No recording/freeze/stitch constructor is inferred.

No editor is launched and no input project/media is written. Output is exclusive
or an identical no-op; use the project diff/validate/apply and native workflow.
JSON stdout schema_version 1 owner camtasia-effect-curves reports hashes,
inventory, changed/written and nativeVerified false. JSON diagnostics on stderr:
exit 1 input/I/O refusal, 2 CLI syntax; exit 0 success. Help emits the same
owner/version with ok true and a formatted help string.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any, NoReturn

import animations
import effects
import hotspots
import project

RECORDING_OWNERS = frozenset({"ScreenVMFile", "ScreenIMFile", "StitchedMedia"})
OWNERS = frozenset({"VMFile", "IMFile", "Callout", "Group"}) | RECORDING_OWNERS


class JsonArgumentParser(argparse.ArgumentParser):
    def format_help(self) -> str:
        return (
            json.dumps(
                dict(
                    schema_version=1,
                    owner="camtasia-effect-curves",
                    ok=True,
                    help=super().format_help(),
                ),
                ensure_ascii=False,
            )
            + "\n"
        )

    def error(self, message: str) -> NoReturn:
        self.exit(2, json.dumps(dict(ok=False, error=message), ensure_ascii=False) + "\n")


def selected(
    doc: dict[str, Any], clip_id: int, name: str, token: str | None
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    if doc.get("version") != "10.0" or doc.get("authoringClientName") != hotspots.NATIVE_CLIENT:
        raise ValueError("use the verified Camtasia Mac 2026.2.4 format-10 curve contract")
    if name == "MediaPath":
        raise ValueError("use motion_paths.py for Motion Path and its rotation coupling")
    targets = effects.targets(doc, clip_id, name, token, visual_types=OWNERS)
    visual = targets[-1][0]
    if visual.get("_type") not in OWNERS:
        raise ValueError("select a visual owner from OWNERS; capture other native clocks")
    if len(targets) > 1 and visual.get("_type") in RECORDING_OWNERS:
        effects.constructor_owners(doc, clip_id, visual_types=OWNERS, linked_recordings=True)
    for field in effects.CLOCK_FIELDS:
        value = project.number(visual.get(field))
        if any(project.number(owner.get(field)) != value for owner, _ in targets):
            raise ValueError("repair conflicting linked owner clocks before effect animation")
    if project.number(doc.get("editRate")) <= 0 or project.number(visual.get("scalar")) <= 0:
        raise ValueError("repair the positive project edit rate and visual inverse speed")
    return targets


def parameter_of(effect: dict[str, Any], name: str) -> dict[str, Any]:
    value = effect["parameters"].get(name)
    if not isinstance(value, dict) or value.get("type") != "double":
        raise ValueError("select an existing typed double parameter; capture its native descriptor")
    # Reuse static validation without flattening the actual parameter's curve.
    scalar_value(value, value.get("defaultValue"))
    frames = value.get("keyframes", [])
    if not isinstance(frames, list):
        raise ValueError("inspect the selected native keyframes array before replacing its curve")
    previous_end = None
    for frame in frames:
        start, end = animations.frame_bounds(frame)
        scalar_value(value, frame.get("value"))
        if previous_end is not None and start < previous_end:
            raise ValueError("repair overlapping or unordered native parameter frames")
        previous_end = end
    return value


def scalar_value(parameter: dict[str, Any], value: Any) -> float:
    scratch = copy.deepcopy(parameter)
    scratch.pop("keyframes", None)
    effects.patch_parameter({"value": scratch}, "value", value)
    return scratch["defaultValue"]


def visual_intervals(owner: dict[str, Any]) -> list[dict[str, Any]]:
    tracks = owner.setdefault("animationTracks", {})
    if not isinstance(tracks, dict) or not isinstance(tracks.get("visual", []), list):
        raise ValueError("inspect the native visual animation track before adding curve intervals")
    intervals = tracks.setdefault("visual", [])
    bounds = [animations.interval_bounds(interval) for interval in intervals]
    if any(
        animations.overlaps(first, second)
        for i, first in enumerate(bounds)
        for second in bounds[i + 1 :]
    ):
        raise ValueError("repair overlapping native visual intervals before effect animation")
    return intervals


def edit_curve(
    doc: dict[str, Any],
    clip_id: int,
    name: str,
    parameter: str,
    spec: dict[str, Any],
    *,
    token: str | None = None,
) -> dict[str, Any]:
    if (
        not isinstance(spec, dict)
        or set(spec) != {"schema_version", "defaultValue", "segments"}
        or type(spec["schema_version"]) is not int
        or spec["schema_version"] not in (1, 2)
        or not isinstance(spec["segments"], list)
        or not spec["segments"]
    ):
        raise ValueError(
            "supply curve schema_version 1 or 2 with defaultValue and nonempty segments"
        )
    result = copy.deepcopy(doc)
    targets = selected(result, clip_id, name, token)
    visual = targets[-1][0]
    old = parameter_of(targets[-1][1], parameter)
    default = scalar_value(old, spec["defaultValue"])
    frames = []
    previous_end = None
    intervals = visual_intervals(visual)
    duration = project.number(visual["duration"]) / project.number(result["editRate"])
    for segment in spec["segments"]:
        required = {"start", "end", "value"}
        optional = {"easing"} if spec["schema_version"] == 2 else set()
        if (
            not isinstance(segment, dict)
            or not required <= set(segment)
            or set(segment) - required - optional
        ):
            raise ValueError(
                "supply each curve segment with start, end, value and optional v2 easing"
            )
        easing = segment.get("easing", "linear")
        if not isinstance(easing, str) or easing == "auto" or easing not in animations.EASINGS:
            raise ValueError("choose effect easing linear, exponential, bounce or spring")
        code = animations.EASINGS[easing]
        if any(isinstance(segment[key], bool) for key in ("start", "end")):
            raise ValueError("supply rational timeline seconds, not booleans")
        start, end = (project.number(segment[key]) for key in ("start", "end"))
        if (
            start < 0
            or end > duration
            or end <= start
            or (previous_end is not None and start < previous_end)
        ):
            raise ValueError(
                "supply ordered nonoverlapping positive segments within the displayed clip"
            )
        bounds = animations.source_bounds(result, visual, segment["start"], segment["end"])
        matched = [
            interval for interval in intervals if animations.interval_bounds(interval) == bounds
        ]
        if any(
            animations.interval_bounds(interval) != bounds
            and animations.overlaps(animations.interval_bounds(interval), bounds)
            for interval in intervals
        ):
            raise ValueError("preserve overlapping visual intervals; select their existing bounds")
        accepted = (None, "linr") if spec["schema_version"] == 1 else animations.EASINGS.values()
        if matched and matched[0].get("interp") not in accepted:
            raise ValueError("preserve shared interval easing; select a compatible native interval")
        if not matched:
            intervals.append(dict(endTime=bounds[1], duration=bounds[1] - bounds[0], interp=code))
        frames.append(
            dict(
                time=bounds[0],
                endTime=bounds[1],
                duration=bounds[1] - bounds[0],
                value=scalar_value(old, segment["value"]),
                interp=code,
            )
        )
        previous_end = end
    for _, effect in targets:
        descriptor = parameter_of(effect, parameter)
        descriptor.update(defaultValue=default, keyframes=copy.deepcopy(frames))
        if spec["schema_version"] == 1:
            descriptor["interp"] = "linr"
        else:
            descriptor.pop("interp", None)
    return result


def clear_curve(
    doc: dict[str, Any],
    clip_id: int,
    name: str,
    parameter: str,
    value: Any,
    *,
    token: str | None = None,
) -> dict[str, Any]:
    result = copy.deepcopy(doc)
    for _, effect in selected(result, clip_id, name, token):
        descriptor = parameter_of(effect, parameter)
        descriptor["defaultValue"] = scalar_value(descriptor, value)
        descriptor.pop("keyframes", None)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = JsonArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("project", type=Path)
    for name in ("set", "clear"):
        command = commands.add_parser(name)
        command.add_argument("project", type=Path)
        command.add_argument("--clip-id", type=int, required=True)
        command.add_argument("--effect", required=True)
        command.add_argument("--effect-token")
        command.add_argument("--parameter", required=True)
        command.add_argument("--output", type=Path, required=True)
        if name == "set":
            command.add_argument("--spec", type=Path, required=True)
        else:
            command.add_argument("--value", required=True)
    args = parser.parse_args(argv)
    try:
        doc, raw = project.load(args.project)
        report: dict[str, Any] = dict(
            schema_version=1,
            owner="camtasia-effect-curves",
            ok=True,
            projectSha256=project.digest(raw),
        )
        if args.command == "inspect":
            report["effects"] = effects.inventory(doc)
        else:
            if args.command == "set":
                candidate = edit_curve(
                    doc,
                    args.clip_id,
                    args.effect,
                    args.parameter,
                    project.load(args.spec)[0],
                    token=args.effect_token,
                )
            else:
                candidate = clear_curve(
                    doc,
                    args.clip_id,
                    args.effect,
                    args.parameter,
                    args.value,
                    token=args.effect_token,
                )
            report.update(
                effects=effects.inventory(candidate),
                output=str(args.output),
                written=hotspots.stage(args.project, args.output, candidate),
                candidateSha256=project.digest(project.encode_document(candidate)),
                changed=candidate != doc,
                nativeVerified=False,
            )
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps(dict(ok=False, error=str(exc)), ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
