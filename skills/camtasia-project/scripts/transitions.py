#!/usr/bin/env python3
"""Stage Mac 2026.2.4 format-10 root-track transition edits without changing clips.

inspect PROJECT lists physical transitions. add-fade PROJECT --left-id ID and/or
--right-id ID --duration SECONDS constructs the native Fade. set uses the same
endpoint selector plus --spec SPEC; remove uses the selector alone. Every edit
requires --output CANDIDATE. IDs select root visual clips or linked AV wrappers,
never source IDs or linked children. Null endpoints and nested tracks need their
own native contract. Omitted endpoints remain omitted.

Spec schema_version 1 accepts duration (displayed total timeline seconds) and/or
attributes (existing-name scalar patches). Durations convert to half extents at
shared joins and full extents at single edges, on exact project ticks. Requested
extents must fit their clips; overlapping transition windows and nonadjacent
shared endpoints are refused. No source-handle availability is inferred.
Static numeric/bool attributes retain scalar kinds; strings, new fields and
structured controls need native investigation. Existing names/opaque payloads,
unpatched flags, IDs, source clocks, media, audio and other transitions survive.
FADE_ATTRIBUTES owns constructor defaults. Other presets require an existing
same-build transition; no installed vendor definition is distributed.

No original project/media is written or editor launched. Candidate staging is
exclusive or an identical no-op. Stdout schema_version 1 owner camtasia-transitions
reports hashes, inventory, changed/written and nativeVerified false. Exit 0
success, 1 input/I/O refusal, 2 CLI syntax; errors are JSON on stderr. Use the
ordinary project diff/validate/apply and native save/reopen/render workflow.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any

import effects
import hotspots
import project

FADE_ATTRIBUTES = dict(
    bypass=False, reverse=False, trivial=False, useAudioPreRoll=True, useVisualPreRoll=True
)
VISUAL_TYPES = frozenset(
    {
        "UnifiedMedia",
        "VMFile",
        "IMFile",
        "Callout",
        "Group",
        "ScreenVMFile",
        "ScreenIMFile",
        "StitchedMedia",
    }
)


def require_native(doc: dict[str, Any]) -> None:
    if doc.get("version") != "10.0" or doc.get("authoringClientName") != hotspots.NATIVE_CLIENT:
        raise ValueError("use the verified Mac 2026.2.4 format-10 transition contract")


def root_tracks(doc: dict[str, Any]):
    for scene, tracks in enumerate(project.scene_tracks(doc)):
        for index, track in enumerate(tracks):
            yield f"/timeline/sceneTrack/scenes/{scene}/csml/tracks/{index}", track


def transition_list(track: dict[str, Any]) -> list[dict[str, Any]]:
    values = track.get("transitions", [])
    if not isinstance(values, list) or any(not isinstance(v, dict) for v in values):
        raise ValueError("inspect the native track transition array before editing")
    return values


def selector(left: int | None, right: int | None) -> dict[str, int]:
    values = {k: v for k, v in [("leftMedia", left), ("rightMedia", right)] if v is not None}
    if not values or any(type(v) is not int or v < 0 for v in values.values()):
        raise ValueError("select at least one nonnegative root visual clip ID")
    if left is not None and left == right:
        raise ValueError("select distinct clips for a shared transition")
    return values


def endpoints(value: dict[str, Any]) -> dict[str, int]:
    selected = {k: value[k] for k in ["leftMedia", "rightMedia"] if k in value}
    if not selected or any(type(v) is not int or v < 0 for v in selected.values()):
        raise ValueError("inspect missing, null or unfamiliar transition endpoints")
    return selected


def selected_track(doc: dict[str, Any], chosen: dict[str, int]) -> dict[str, Any]:
    matches = []
    for clip_id in chosen.values():
        found = [
            track
            for _, track in root_tracks(doc)
            for clip in track.get("medias", [])
            if clip.get("id") == clip_id and clip.get("_type") in VISUAL_TYPES
        ]
        if len(found) != 1:
            raise ValueError("select a unique root visual clip or linked AV wrapper ID")
        matches.append(found[0])
    if any(track is not matches[0] for track in matches):
        raise ValueError("select endpoints from the same root track")
    return matches[0]


def window(track: dict[str, Any], transition: dict[str, Any]):
    chosen = endpoints(transition)
    extent = transition.get("duration")
    if type(extent) is not int or extent <= 0:
        raise ValueError("supply a positive transition extent on exact native ticks")
    clips = {}
    for side, clip_id in chosen.items():
        found = [c for c in track.get("medias", []) if c.get("id") == clip_id]
        if len(found) != 1:
            raise ValueError("repair missing or ambiguous transition endpoints")
        clip = found[0]
        start, duration = project.number(clip.get("start")), project.number(clip.get("duration"))
        if duration <= 0 or extent > duration:
            raise ValueError("fit the transition extent inside each endpoint clip")
        clips[side] = (start, start + duration)
    if len(clips) == 2 and clips["leftMedia"][1] != clips["rightMedia"][0]:
        raise ValueError("use separate edge fades for a gap; shared endpoints must be adjacent")
    boundary = clips["leftMedia"][1] if "leftMedia" in clips else clips["rightMedia"][0]
    return (
        boundary - extent if "leftMedia" in clips else boundary,
        boundary + extent if "rightMedia" in clips else boundary,
    )


def check_fit(track: dict[str, Any], candidate: dict[str, Any], old: dict[str, Any] | None) -> None:
    begin, end = window(track, candidate)
    ids = set(endpoints(candidate).values())
    for clip in track.get("medias", []):
        start = project.number(clip.get("start"))
        finish = start + project.number(clip.get("duration"))
        if clip.get("id") not in ids and max(begin, start) < min(end, finish):
            raise ValueError("resolve overlapping clips in the transition window before editing")
    for other in transition_list(track):
        if other is old:
            continue
        a, b = window(track, other)
        if max(begin, a) < min(end, b):
            raise ValueError("shorten or remove overlapping transitions before editing")


def extent_ticks(doc: dict[str, Any], chosen: dict[str, int], seconds: Any) -> int:
    rate = project.number(doc.get("editRate"))
    ticks = project.number(seconds) * rate / len(chosen)
    if rate <= 0 or ticks <= 0 or ticks.denominator != 1:
        raise ValueError("supply a positive displayed duration on exact native extent ticks")
    return int(ticks)


def selected_transition(track: dict[str, Any], chosen: dict[str, int]) -> dict[str, Any] | None:
    matches = [t for t in transition_list(track) if endpoints(t) == chosen]
    if len(matches) > 1:
        raise ValueError("repair duplicate transitions at the selected boundary")
    return matches[0] if matches else None


def add_fade(
    doc: dict[str, Any], left: int | None, right: int | None, seconds: Any
) -> dict[str, Any]:
    require_native(doc)
    result = copy.deepcopy(doc)
    chosen = selector(left, right)
    track = selected_track(result, chosen)
    if selected_transition(track, chosen) is not None:
        raise ValueError("edit or remove the existing transition at this boundary first")
    value = dict(
        name="Fade",
        duration=extent_ticks(result, chosen, seconds),
        **chosen,
        attributes=copy.deepcopy(FADE_ATTRIBUTES),
    )
    check_fit(track, value, None)
    track.setdefault("transitions", []).append(value)
    return result


def set_transition(
    doc: dict[str, Any], left: int | None, right: int | None, spec: dict[str, Any]
) -> dict[str, Any]:
    require_native(doc)
    if (
        not isinstance(spec, dict)
        or type(spec.get("schema_version")) is not int
        or spec.get("schema_version") != 1
        or set(spec) - {"schema_version", "duration", "attributes"}
        or not (set(spec) & {"duration", "attributes"})
    ):
        raise ValueError("supply schema_version 1 and duration and/or existing attributes")
    result = copy.deepcopy(doc)
    chosen = selector(left, right)
    track = selected_track(result, chosen)
    old = selected_transition(track, chosen)
    if old is None:
        raise ValueError("select an existing transition or construct a native Fade first")
    value = copy.deepcopy(old)
    if "duration" in spec:
        value["duration"] = extent_ticks(result, chosen, spec["duration"])
    if "attributes" in spec:
        changes, attributes = spec["attributes"], value.get("attributes")
        if not isinstance(changes, dict) or not changes or not isinstance(attributes, dict):
            raise ValueError("supply a nonempty patch for existing native scalar attributes")
        for key, new in changes.items():
            if key not in attributes or type(attributes[key]) not in (bool, int, float):
                raise ValueError("select existing numeric/bool transition attributes: " + str(key))
            attributes[key] = effects.scalar_like(type(attributes[key]), new)
    check_fit(track, value, old)
    track["transitions"][track["transitions"].index(old)] = value
    return result


def remove_transition(doc: dict[str, Any], left: int | None, right: int | None) -> dict[str, Any]:
    require_native(doc)
    result = copy.deepcopy(doc)
    chosen = selector(left, right)
    track = selected_track(result, chosen)
    old = selected_transition(track, chosen)
    if old is not None:
        track["transitions"].remove(old)
        if not track["transitions"]:
            track.pop("transitions")
    return result


def inventory(doc: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(path=path + "/transitions/" + str(i), transition=copy.deepcopy(t))
        for path, track in root_tracks(doc)
        for i, t in enumerate(transition_list(track))
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ["inspect", "add-fade", "set", "remove"]:
        command = commands.add_parser(name)
        command.add_argument("project", type=Path)
        if name != "inspect":
            command.add_argument("--left-id", type=int)
            command.add_argument("--right-id", type=int)
            command.add_argument("--output", type=Path, required=True)
        if name == "add-fade":
            command.add_argument("--duration", required=True)
        if name == "set":
            command.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        doc, raw = project.load(args.project)
        report: dict[str, Any] = dict(
            schema_version=1,
            owner="camtasia-transitions",
            ok=True,
            projectSha256=project.digest(raw),
        )
        candidate = doc
        if args.command == "add-fade":
            candidate = add_fade(doc, args.left_id, args.right_id, args.duration)
        elif args.command == "set":
            candidate = set_transition(doc, args.left_id, args.right_id, project.load(args.spec)[0])
        elif args.command == "remove":
            candidate = remove_transition(doc, args.left_id, args.right_id)
        if args.command != "inspect":
            report.update(
                output=str(args.output),
                written=hotspots.stage(args.project, args.output, candidate),
                candidateSha256=project.digest(project.encode_document(candidate)),
                changed=candidate != doc,
                nativeVerified=False,
            )
        report["transitions"] = inventory(candidate)
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except (OSError, ValueError, OverflowError) as exc:
        print(json.dumps(dict(ok=False, error=str(exc)), ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
