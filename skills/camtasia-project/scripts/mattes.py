#!/usr/bin/env python3
"""Inspect and stage Mac 2026.2.4 format-10 media/track mattes as JSON.

MODES owns native mode codes. Media constructors cover Callout, VMFile,
IMFile, Group and linked UnifiedMedia/video. Preserve native fill/alpha content
and use a separate lower track. Linked edits preserve the audio child and patch
both visual mirrors through their stable effectIndex token, not array position.
Media intensity is a scalar in [0,1]; omitted controls retain native values.
Ease arguments are nonnegative rational seconds on exact project ticks.
Known intensity FadeInFunc/FadeOutFunc edge controls are patched individually;
other edge modifiers/parameters and opaque effect/reset data survive.
Zero easing removes only that fade. Existing trackDepth is preserved; new
effects use the native 10002 default. Native tests of 0/1/2/3/10002 retain
different values but give the same immediate-layer result in the tested stack;
do not infer a lower-track count or flatten typed intensity/animated parameters.

Track mode lives in timeline.trackAttributes for the observed single scene,
or in a selected Group.tracks entry. Track indices are zero-based storage
positions, not displayed track numbers. Group IDs may select nested Groups.
Track modes and per-media effects are separate controls and may compound.

CLI: inspect PROJECT; set-media PROJECT --clip-id ID --output CANDIDATE
[--mode MODE] [--intensity SCALAR] [--ease-in SECONDS] [--ease-out SECONDS]
[--bypass|--no-bypass]. --mode none removes only the selected MediaMatte.
set-track PROJECT --track INDEX [--group-id ID] --mode MODE --output CANDIDATE.
set-intensity-curve PROJECT --clip-id ID --curve SPEC --output CANDIDATE;
clear-intensity-curve PROJECT --clip-id ID --intensity SCALAR --output CANDIDATE.
Curve input schema_version 1 has defaultValue and nonempty segments, each with
start/end rational clip-relative timeline seconds and value in [0,1]. Segments
have positive duration, retain input order and must not overlap. Negative starts
remain legal source-position bounds. Linear keyframes convert through mediaStart
and scalar to source positions in project ticks. Linked mirrors share the visual
clock; mismatched clocks are refused. Curves replace only intensity's timing and
default, preserving unrelated parameters/animations. Clear removes only intensity
keyframes; existing visual intervals and other parameter curves remain unchanged.
Native reopening can regenerate flat intensity companions from those intervals;
the cleared intensity remains constant.
Ambiguous multiple media mattes require inspection rather than an inferred
target. Original JSON/media are never written. Staging is exclusive or an
identical no-op; apply through project.py after closing the native document.
Stdout schema_version 1, owner camtasia-mattes, hashes/inventory and outcome;
nativeVerified false distinguishes staging from native acceptance. Exit 0
success, 1 input/I/O refusal, 2 CLI syntax. No editor or export is launched.
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

MODES = {"none": 0, "alpha": 1, "alpha-invert": 2, "luminosity": 3, "luminosity-invert": 4}
DEFAULT_EFFECT = {
    "effectName": "MediaMatte",
    "bypassed": False,
    "category": "categoryVisualEffects",
    "parameters": {
        "matteMode": 1,
        "intensity": {
            "type": "double",
            "defaultValue": 1.0,
            "interp": "linr",
            "uiHints": {"userInterfaceType": 0, "unitType": 0},
        },
        "trackDepth": 10002,
    },
}
MEDIA_TYPES = frozenset({"Callout", "VMFile", "IMFile", "Group"})


def require_native(doc: dict[str, Any]) -> None:
    if doc.get("version") != "10.0" or doc.get("authoringClientName") != hotspots.NATIVE_CLIENT:
        raise ValueError("use the observed Mac 2026.2.4 format-10 matte contract")


def mode_code(mode: str) -> int:
    if mode not in MODES:
        raise ValueError("choose a matte mode from MODES")
    return MODES[mode]


def scalar(value: Any) -> float:
    if isinstance(value, bool):
        raise ValueError("supply a numeric matte intensity between 0 and 1")
    result = project.number(value)
    if not 0 <= result <= 1:
        raise ValueError("supply matte intensity between 0 and 1")
    return float(result)


def set_parameter(effect: dict[str, Any], name: str, value: int | float) -> None:
    parameters = effect["parameters"]
    old = parameters.get(name)
    if name == "intensity" and isinstance(old, dict):
        if (
            old.get("type") != "double"
            or type(old.get("defaultValue")) not in (int, float)
            or old.get("keyframes")
        ):
            raise ValueError(
                "preserve animated or unfamiliar matte intensity; capture its native controls"
            )
        old["defaultValue"] = value
        return
    if name in parameters and type(parameters[name]) not in (int, float):
        raise ValueError(
            "preserve animated or unfamiliar matte parameters; capture their native controls"
        )
    parameters[name] = value


def effects_of(node: dict[str, Any]) -> list[dict[str, Any]]:
    effects = node.get("effects", [])
    if not isinstance(effects, list) or any(not isinstance(effect, dict) for effect in effects):
        raise ValueError("inspect the clip's effects array before editing")
    return effects


def one_matte(node: dict[str, Any]) -> dict[str, Any] | None:
    found = [e for e in effects_of(node) if e.get("effectName") == "MediaMatte"]
    if len(found) > 1:
        raise ValueError("inspect multiple media mattes before selecting an effect")
    return found[0] if found else None


def effect_token(effect: dict[str, Any]) -> str | None:
    metadata = effect.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("inspect native effect metadata before editing linked media")
    value = metadata.get("effectIndex")
    if value is not None and (
        not isinstance(value, str) or not value.isdecimal() or str(int(value)) != value
    ):
        raise ValueError("repair the native linked effectIndex token")
    return value


def media_targets(doc: dict[str, Any], clip_id: int) -> list[dict[str, Any]]:
    path, node = hotspots.visual_target(doc, clip_id)
    if node.get("_type") not in MEDIA_TYPES:
        raise ValueError("select a verified media-matte visual owner")
    wrappers = [
        n
        for p, n in hotspots.clips(doc)
        if n.get("_type") == "UnifiedMedia" and path == p + "/video"
    ]
    if not wrappers:
        return [node]
    if len(wrappers) != 1:
        raise ValueError("repair the ambiguous linked visual owner")
    wrapper = wrappers[0]
    video_matte, wrapper_matte = one_matte(node), one_matte(wrapper)
    if (video_matte is None) != (wrapper_matte is None):
        raise ValueError("repair missing linked media-matte mirrors before editing")
    if video_matte is not None and wrapper_matte is not None:
        token = effect_token(video_matte)
        if token is None or token != effect_token(wrapper_matte):
            raise ValueError("repair mismatched linked media-matte effectIndex tokens")
        for key in (
            "effectName",
            "category",
            "bypassed",
            "parameters",
            "leftEdgeMods",
            "rightEdgeMods",
        ):
            if video_matte.get(key) != wrapper_matte.get(key):
                raise ValueError("repair conflicting linked media-matte controls")
    return [wrapper, node]


def next_effect_token(wrapper: dict[str, Any]) -> str:
    observed = []
    for node in (wrapper, wrapper.get("video", {}), wrapper.get("audio", {})):
        if not isinstance(node, dict):
            raise ValueError("repair the linked media children")
        for effect in effects_of(node):
            token = effect_token(effect)
            if token is None:
                raise ValueError(
                    "capture linked effect bindings before adding to an unindexed effect list"
                )
            observed.append(int(token))
    return str(max(observed, default=-1) + 1)


def patch_ease(effect: dict[str, Any], edge: str, duration: int) -> None:
    key, function = (
        ("leftEdgeMods", "FadeInFunc") if edge == "in" else ("rightEdgeMods", "FadeOutFunc")
    )
    modifiers = effect.get(key, [])
    if not isinstance(modifiers, list):
        raise ValueError("inspect the existing matte edge modifier array")
    matches = []
    for modifier in modifiers:
        if not isinstance(modifier, dict) or not isinstance(modifier.get("parameters"), list):
            raise ValueError("inspect unfamiliar matte edge modifier parameters")
        for parameter in modifier["parameters"]:
            if not isinstance(parameter, dict):
                raise ValueError("inspect an unfamiliar matte edge parameter")
            if parameter.get("name") == "intensity":
                if modifier.get("group") != "Video" or parameter.get("func") != function:
                    raise ValueError(
                        "preserve unfamiliar intensity edge functions; capture a native case"
                    )
                matches.append((modifier, parameter))
    if len(matches) > 1:
        raise ValueError("inspect multiple matte intensity fades before editing")
    if matches:
        modifier, parameter = matches[0]
        if duration:
            if (
                len(modifier["parameters"]) != 1
                and project.number(modifier.get("duration")) != duration
            ):
                raise ValueError(
                    "split shared edge timing through a native example before changing it"
                )
            modifier["duration"] = duration
        else:
            modifier["parameters"].remove(parameter)
            if not modifier["parameters"] and not set(modifier) - {
                "group",
                "duration",
                "parameters",
            }:
                modifiers.remove(modifier)
    elif duration:
        modifiers.append(
            {
                "group": "Video",
                "duration": duration,
                "parameters": [{"name": "intensity", "func": function}],
            }
        )
    if modifiers:
        effect[key] = modifiers
    else:
        effect.pop(key, None)


def edit_media(
    doc: dict[str, Any],
    clip_id: int,
    *,
    mode: str | None = None,
    intensity: Any = None,
    ease_in: Any = None,
    ease_out: Any = None,
    bypass: bool | None = None,
) -> dict[str, Any]:
    require_native(doc)
    if mode is not None:
        mode_code(mode)
    if bypass is not None and type(bypass) is not bool:
        raise ValueError("use a boolean effect bypass")
    if all(value is None for value in (mode, intensity, ease_in, ease_out, bypass)):
        raise ValueError("supply at least one matte control to change")
    if mode == "none" and any(
        value is not None for value in (intensity, ease_in, ease_out, bypass)
    ):
        raise ValueError("remove a media matte separately from changing its controls")
    result = copy.deepcopy(doc)
    targets = media_targets(result, clip_id)
    new_token = (
        next_effect_token(targets[0])
        if len(targets) == 2 and one_matte(targets[0]) is None and mode != "none"
        else None
    )
    for node in targets:
        effects = effects_of(node)
        effect = one_matte(node)
        if mode == "none":
            if effect is not None:
                effects.remove(effect)
            continue
        if effect is not None:
            if effect.get("category") != "categoryVisualEffects" or not isinstance(
                effect.get("parameters"), dict
            ):
                raise ValueError("inspect an unfamiliar native media-matte effect")
        else:
            effect = copy.deepcopy(DEFAULT_EFFECT)
            if new_token is not None:
                effect["metadata"] = {"effectIndex": new_token}
            effects.append(effect)
            node["effects"] = effects
        if mode is not None:
            set_parameter(effect, "matteMode", mode_code(mode))
        if intensity is not None:
            set_parameter(effect, "intensity", scalar(intensity))
        if bypass is not None:
            effect["bypassed"] = bypass
        for edge, value in (("in", ease_in), ("out", ease_out)):
            if value is not None:
                if isinstance(value, bool):
                    raise ValueError("supply nonnegative easing seconds, not a boolean")
                patch_ease(effect, edge, hotspots.ticks(doc, value))
    return result


def curve_parameter(
    doc: dict[str, Any], visual: dict[str, Any], spec: dict[str, Any]
) -> dict[str, Any]:
    """Compile the observed linear interval curve from clip-local seconds."""
    if (
        not isinstance(spec, dict)
        or set(spec) != {"schema_version", "defaultValue", "segments"}
        or type(spec["schema_version"]) is not int
        or spec["schema_version"] != 1
    ):
        raise ValueError("supply curve schema_version 1 with defaultValue and segments")
    segments = spec["segments"]
    if not isinstance(segments, list) or not segments:
        raise ValueError("supply nonempty curve segments; use clear-intensity-curve to clear")
    rate = project.number(doc.get("editRate"))
    scalar_value = project.number(visual.get("scalar"))
    media_start = project.number(visual.get("mediaStart"))
    if rate <= 0 or scalar_value <= 0:
        raise ValueError("repair the positive project rate and visual source clock")
    result = copy.deepcopy(DEFAULT_EFFECT["parameters"]["intensity"])
    result.pop("interp")
    result["defaultValue"] = scalar(spec["defaultValue"])
    frames = []
    previous_end = None
    for segment in segments:
        if not isinstance(segment, dict) or set(segment) != {"start", "end", "value"}:
            raise ValueError("supply each curve segment with start, end and value")
        if any(isinstance(segment[key], bool) for key in ("start", "end")):
            raise ValueError("supply rational curve seconds, not booleans")
        start, end = (project.number(segment[key]) for key in ("start", "end"))
        if end <= start or (previous_end is not None and start < previous_end):
            raise ValueError("supply ordered, nonoverlapping curve segments of positive duration")
        bounds = [media_start + seconds * rate / scalar_value for seconds in (start, end)]
        if any(value.denominator != 1 for value in bounds):
            raise ValueError("choose curve bounds that map to exact native project ticks")
        time, end_time = (int(value) for value in bounds)
        frames.append(
            {
                "time": time,
                "endTime": end_time,
                "duration": end_time - time,
                "value": scalar(segment["value"]),
                "interp": "linr",
            }
        )
        previous_end = end
    result["keyframes"] = frames
    return result


def edit_intensity_curve(doc: dict[str, Any], clip_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    require_native(doc)
    result = copy.deepcopy(doc)
    targets = media_targets(result, clip_id)
    if len(targets) == 2:
        for field in ("mediaStart", "scalar"):
            if project.number(targets[0].get(field)) != project.number(targets[1].get(field)):
                raise ValueError("repair conflicting linked visual source clocks before animation")
    parameter = curve_parameter(result, targets[-1], spec)
    if one_matte(targets[0]) is None:
        result = edit_media(result, clip_id, mode="alpha")
        targets = media_targets(result, clip_id)
    for target in targets:
        effect = one_matte(target)
        if (
            effect is None
            or effect.get("category") != "categoryVisualEffects"
            or not isinstance(effect.get("parameters"), dict)
        ):
            raise ValueError("inspect native matte parameters before replacing the intensity curve")
        old = effect["parameters"].get("intensity")
        if isinstance(old, dict):
            if old.get("type") != "double":
                raise ValueError(
                    "preserve unfamiliar intensity parameter types; capture native controls"
                )
            replacement = copy.deepcopy(old)
            replacement.pop("interp", None)
            replacement.update(
                defaultValue=parameter["defaultValue"],
                keyframes=copy.deepcopy(parameter["keyframes"]),
            )
        elif type(old) in (int, float):
            replacement = copy.deepcopy(parameter)
        else:
            raise ValueError("inspect the native intensity before replacing its curve")
        effect["parameters"]["intensity"] = replacement
    return result


def clear_intensity_curve(doc: dict[str, Any], clip_id: int, intensity: Any) -> dict[str, Any]:
    require_native(doc)
    value = scalar(intensity)
    result = copy.deepcopy(doc)
    for target in media_targets(result, clip_id):
        effect = one_matte(target)
        if (
            effect is None
            or effect.get("category") != "categoryVisualEffects"
            or not isinstance(effect.get("parameters"), dict)
        ):
            raise ValueError("select an existing media matte before clearing its intensity curve")
        parameter = effect["parameters"].get("intensity")
        if isinstance(parameter, dict):
            if parameter.get("type") != "double":
                raise ValueError(
                    "preserve unfamiliar intensity parameter types; capture native controls"
                )
            parameter.pop("keyframes", None)
            parameter["defaultValue"] = value
        elif type(parameter) in (int, float):
            effect["parameters"]["intensity"] = value
        else:
            raise ValueError("inspect the native intensity before clearing its curve")
    return result


def track_target(doc: dict[str, Any], index: int, group_id: int | None = None) -> dict[str, Any]:
    if type(index) is not int or index < 0:
        raise ValueError("choose a nonnegative zero-based track index")
    if group_id is None:
        scenes = project.scene_tracks(doc)
        if len(scenes) != 1:
            raise ValueError("capture multi-scene track-matte ownership before editing")
        tracks = doc.get("timeline", {}).get("trackAttributes")
        if not isinstance(tracks, list) or len(tracks) != len(scenes[0]):
            raise ValueError("repair native track-attribute ownership before editing")
    else:
        if type(group_id) is not int:
            raise ValueError("select an integer Group ID from inspection")
        matches = [node for _, node in hotspots.clips(doc) if node.get("id") == group_id]
        if len(matches) != 1 or matches[0].get("_type") != "Group":
            raise ValueError("select a unique native Group ID")
        tracks = matches[0].get("tracks")
    if not isinstance(tracks, list) or index >= len(tracks) or not isinstance(tracks[index], dict):
        raise ValueError("choose an existing track from inspection")
    track = tracks[index]
    if type(track.get("matte")) is not int or track["matte"] not in MODES.values():
        raise ValueError("preserve the unfamiliar track matte code; capture a native example")
    return track


def edit_track(
    doc: dict[str, Any], index: int, mode: str, *, group_id: int | None = None
) -> dict[str, Any]:
    require_native(doc)
    code = mode_code(mode)
    result = copy.deepcopy(doc)
    track_target(result, index, group_id)["matte"] = code
    return result


def inventory(doc: dict[str, Any]) -> dict[str, Any]:
    media = []
    for path, node in hotspots.clips(doc):
        effects = node.get("effects", [])
        if not isinstance(effects, list):
            raise ValueError("inspect the native effects array before listing mattes")
        for index, effect in enumerate(effects):
            if isinstance(effect, dict) and effect.get("effectName") == "MediaMatte":
                media.append(
                    {
                        "clipId": node.get("id"),
                        "path": project.pointer(path, "effects") + f"/{index}",
                        "effect": effect,
                    }
                )
    tracks = [
        {"path": project.pointer(path, "matte"), "code": node["matte"]}
        for path, node in project.objects(doc.get("timeline", {}), "/timeline")
        if "matte" in node
    ]
    return {"mediaMattes": media, "trackMattes": tracks}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("project", type=Path)
    media = commands.add_parser("set-media")
    media.add_argument("project", type=Path)
    media.add_argument("--clip-id", type=int, required=True)
    media.add_argument("--mode", choices=MODES)
    media.add_argument("--intensity")
    media.add_argument("--ease-in")
    media.add_argument("--ease-out")
    media.add_argument("--bypass", action=argparse.BooleanOptionalAction, default=None)
    media.add_argument("--output", type=Path, required=True)
    curve = commands.add_parser("set-intensity-curve")
    curve.add_argument("project", type=Path)
    curve.add_argument("--clip-id", type=int, required=True)
    curve.add_argument("--curve", type=Path, required=True)
    curve.add_argument("--output", type=Path, required=True)
    clear = commands.add_parser("clear-intensity-curve")
    clear.add_argument("project", type=Path)
    clear.add_argument("--clip-id", type=int, required=True)
    clear.add_argument("--intensity", required=True)
    clear.add_argument("--output", type=Path, required=True)
    track = commands.add_parser("set-track")
    track.add_argument("project", type=Path)
    track.add_argument("--track", type=int, required=True)
    track.add_argument("--group-id", type=int)
    track.add_argument("--mode", choices=MODES, required=True)
    track.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        doc, raw = project.load(args.project)
        report = {
            "schema_version": 1,
            "owner": "camtasia-mattes",
            "ok": True,
            "projectSha256": project.digest(raw),
        }
        if args.command == "inspect":
            report.update(inventory(doc))
        else:
            if args.command == "set-intensity-curve":
                spec, _ = project.load(args.curve)
                candidate = edit_intensity_curve(doc, args.clip_id, spec)
            elif args.command == "clear-intensity-curve":
                candidate = clear_intensity_curve(doc, args.clip_id, args.intensity)
            elif args.command == "set-track":
                candidate = edit_track(doc, args.track, args.mode, group_id=args.group_id)
            else:
                candidate = edit_media(
                    doc,
                    args.clip_id,
                    mode=args.mode,
                    intensity=args.intensity,
                    ease_in=args.ease_in,
                    ease_out=args.ease_out,
                    bypass=args.bypass,
                )
            report.update(inventory(candidate))
            report.update(
                output=str(args.output),
                written=hotspots.stage(args.project, args.output, candidate),
                candidateSha256=project.digest(project.encode_document(candidate)),
                changed=candidate != doc,
                nativeVerified=False,
            )
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
