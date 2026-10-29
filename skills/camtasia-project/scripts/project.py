#!/usr/bin/env python3
"""Partial Camtasia structural checks and conservative project replacement.

Unknown JSON survives. This is not a complete format schema or renderer.
Nested timing is intentionally not flattened. Still holds, rational source
durations, and negative internal offsets are legal. Source-range/keyframe
semantics require a matching editor or a version-specific feature probe.
"""

from __future__ import annotations

import argparse
from collections import Counter
from decimal import Decimal
from fractions import Fraction
import hashlib
import json
import math
import os
from pathlib import Path, PureWindowsPath
import shutil
import stat
import subprocess
import sys
import tempfile
from typing import Any, Iterator

KNOWN_CLIPS = frozenset(
    {
        "AMFile",
        "VMFile",
        "IMFile",
        "ScreenVMFile",
        "ScreenIMFile",
        "Callout",
        "Caption",
        "Group",
        "StitchedMedia",
        "UnifiedMedia",
        "PlaceholderMedia",
    }
)
FILE_CLIPS = frozenset({"AMFile", "VMFile", "IMFile", "ScreenVMFile", "ScreenIMFile"})
# Logical installation references observed in native saves; not bundle-relative files.
ASSET_PARAMETERS = {
    "DeviceFrameEffect": ("deviceFrameSource",),
    "CursorPath": ("cursorImagePath",),
}
LIMITS = [
    "Partial structural checks; no complete official schema is asserted.",
    "No source-stream bounds, nested clock mapping, or keyframe-domain proof.",
    "No codec, font, asset license, rendering, audio, or Smart Player validation.",
]
PREVIEW_CHARS = 180
DEFAULT_DIFF_LIMIT = 200
HASH_CHUNK_BYTES = 1024 * 1024
NATIVE_LUFS_LITERAL = "-1.79769313486232e+308"
NATIVE_LUFS_BUILD_FORMATS = {"2025.0.3": "9.0", "2026.2.4": "10.0"}


class NativeLoudnessSentinel(Decimal):
    """Preserve the native finite decimal that exceeds binary64's range."""


def native_float(value: str) -> float | NativeLoudnessSentinel:
    if value == NATIVE_LUFS_LITERAL:
        return NativeLoudnessSentinel(value)
    return float(value)


def number(value: Any) -> Fraction:
    """Parse JSON numeric/rational time without silently accepting booleans."""
    if isinstance(value, bool) or not isinstance(value, (int, float, str)):
        raise ValueError(f"expected a number or rational string, got {value!r}")
    if isinstance(value, float) and not math.isfinite(value):
        raise ValueError("non-finite numbers are invalid JSON")
    try:
        return Fraction(str(value))
    except (ValueError, ZeroDivisionError) as exc:
        raise ValueError(f"invalid rational value {value!r}") from exc


def project_file(path: Path) -> Path:
    if path.is_dir():
        return path / "project.tscproj"
    return path


def unique_object(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
    result: dict[str, Any] = {}
    for key, value in pairs:
        if key in result:
            raise ValueError(f"duplicate JSON key {key!r}; repair it before editing")
        result[key] = value
    return result


def invalid_constant(value: str) -> Any:
    raise ValueError(f"non-finite JSON token {value}; replace it with a finite value")


def load(path: Path) -> tuple[dict[str, Any], bytes]:
    raw = project_file(path).read_bytes()
    doc = json.loads(
        raw,
        object_pairs_hook=unique_object,
        parse_constant=invalid_constant,
        parse_float=native_float,
    )
    if not isinstance(doc, dict):
        raise ValueError(f"{path}: project root must be an object")
    errors = nonfinite_errors(doc)
    if errors:
        raise ValueError(f"{path}: {errors[0]}")
    return doc, raw


def digest(raw: bytes) -> str:
    return hashlib.sha256(raw).hexdigest()


def pointer(path: str, key: Any) -> str:
    return path + "/" + str(key).replace("~", "~0").replace("/", "~1")


def nonfinite_errors(doc: dict[str, Any]) -> list[str]:
    """Reject nonfinite numbers; scope the observed large native LUFS literal.

    Native Opus and legacy stitched saves contain NATIVE_LUFS_LITERAL in the
    exact builds/formats listed in NATIVE_LUFS_BUILD_FORMATS. This finite decimal
    metadata overflows an ordinary float parser.
    All literal infinities and other numeric overflow remain invalid.
    """
    allowed: set[str] = set()
    sources = doc.get("sourceBin")
    if any(
        doc.get("version") == format_version
        and doc.get("authoringClientName")
        == {"name": "Camtasia", "platform": "Mac", "version": build}
        for build, format_version in NATIVE_LUFS_BUILD_FORMATS.items()
    ) and isinstance(sources, list):
        for index, source in enumerate(sources):
            tracks = source.get("sourceTracks") if isinstance(source, dict) else None
            if not isinstance(tracks, list):
                continue
            for track_index, track in enumerate(tracks):
                if (
                    isinstance(track, dict)
                    and type(track.get("type")) is int
                    and track["type"] == 2
                ):
                    allowed.add(f"/sourceBin/{index}/sourceTracks/{track_index}/integratedLUFS")

    def visit(value: Any, path: str) -> Iterator[str]:
        if isinstance(value, dict):
            for key, child in value.items():
                yield from visit(child, pointer(path, key))
        elif isinstance(value, list):
            for index, child in enumerate(value):
                yield from visit(child, pointer(path, index))
        elif isinstance(value, NativeLoudnessSentinel):
            if value == Decimal(NATIVE_LUFS_LITERAL) and path in allowed:
                return
            yield f"{path}: native loudness sentinel outside its observed audio metadata field/build"
        elif isinstance(value, float) and not math.isfinite(value):
            yield (f"{path}: non-finite number; inspect the value and use finite numbers")

    return list(visit(doc, ""))


def _encode_json_value(value: Any) -> str:
    if isinstance(value, NativeLoudnessSentinel):
        return NATIVE_LUFS_LITERAL
    if isinstance(value, dict):
        if not all(isinstance(key, str) for key in value):
            raise ValueError(
                "JSON object keys must be strings; repair the candidate before encoding"
            )
        return (
            "{"
            + ",".join(
                json.dumps(key, ensure_ascii=False) + ":" + _encode_json_value(child)
                for key, child in value.items()
            )
            + "}"
        )
    if isinstance(value, list):
        return "[" + ",".join(_encode_json_value(child) for child in value) + "]"
    return json.dumps(value, ensure_ascii=False, allow_nan=False)


def encode_document(doc: dict[str, Any]) -> bytes:
    """Encode a loaded candidate without rounding the observed LUFS decimal.

    Returns UTF-8 JSON bytes with a final newline, preserves JSON value types,
    and refuses unsupported nonfinite values or misplaced native sentinels.
    This does not apply, save, or validate source media in a project.
    """
    errors = nonfinite_errors(doc)
    if errors:
        raise ValueError(errors[0])
    return (_encode_json_value(doc) + "\n").encode("utf-8")


def objects(value: Any, path: str = "") -> Iterator[tuple[str, dict[str, Any]]]:
    """Read-only generic traversal; never assumes one scene or a flat timeline."""
    if isinstance(value, dict):
        yield path, value
        for key, child in value.items():
            yield from objects(child, pointer(path, key))
    elif isinstance(value, list):
        for index, child in enumerate(value):
            yield from objects(child, pointer(path, index))


def scene_tracks(doc: dict[str, Any]) -> list[list[dict[str, Any]]]:
    try:
        scenes = doc["timeline"]["sceneTrack"]["scenes"]
        if not isinstance(scenes, list):
            raise ValueError("scenes must be an array")
        result = []
        for scene in scenes:
            tracks = scene["csml"]["tracks"]
            if not isinstance(tracks, list) or not all(isinstance(t, dict) for t in tracks):
                raise ValueError("scene tracks must be an array of objects")
            result.append(tracks)
        return result
    except (KeyError, TypeError) as exc:
        raise ValueError("expected timeline.sceneTrack.scenes[].csml.tracks") from exc


def selected_track(doc: dict[str, Any], selector: str) -> dict[str, Any]:
    try:
        scene, track = (int(part) for part in selector.split(":"))
        if scene < 0 or track < 0:
            raise ValueError("negative index")
        return scene_tracks(doc)[scene][track]
    except (ValueError, IndexError) as exc:
        raise ValueError(
            f"track {selector!r} not found; use zero-based SCENE:TRACK positions"
        ) from exc


def clip_paths(doc: dict[str, Any]) -> set[str]:
    result: set[str] = set()
    for path, node in objects(doc.get("timeline", {}), "/timeline"):
        if isinstance(node.get("medias"), list):
            for index, clip in enumerate(node["medias"]):
                if isinstance(clip, dict):
                    result.add(pointer(pointer(path, "medias"), index))
        if node.get("_type") == "UnifiedMedia":
            result.update(
                pointer(path, key) for key in ("video", "audio") if isinstance(node.get(key), dict)
            )
    return result


def native_lane_collisions(doc: dict[str, Any]) -> list[str]:
    """Reject overlapping known clips on format-10 Mac 2026.2.4 scene lanes.

    Simultaneous callout panels/titles raised the native parser's Collision
    exception. Separating them onto lanes opened and rendered successfully.
    Check scene-lane placement only: linked AV children share intervals, and
    nested/stitched clocks have separate contracts. Gaps and touching endpoints
    are legal. Unknown clip types remain opaque, not certified by this check.
    """
    client = {"name": "Camtasia", "platform": "Mac", "version": "2026.2.4"}
    if doc.get("version") != "10.0" or doc.get("authoringClientName") != client:
        return []
    try:
        scenes = scene_tracks(doc)
    except ValueError:
        # validate() reports malformed scene structure independently.
        return []
    errors = []
    for scene_index, tracks in enumerate(scenes):
        for track_index, track in enumerate(tracks):
            medias = track.get("medias")
            if not isinstance(medias, list):
                continue
            intervals = []
            for index, media in enumerate(medias):
                if (
                    not isinstance(media, dict)
                    or not isinstance(media.get("_type"), str)
                    or media["_type"] not in KNOWN_CLIPS
                ):
                    continue
                try:
                    start, duration = number(media.get("start")), number(media.get("duration"))
                except ValueError:
                    # validate() reports invalid clip time fields independently.
                    continue
                if duration > 0:
                    intervals.append((start, start + duration, index))
            previous_end: Fraction | None = None
            previous_index = None
            for start, end, index in sorted(intervals):
                if previous_end is not None and start < previous_end:
                    path = f"/timeline/sceneTrack/scenes/{scene_index}/csml/tracks/{track_index}"
                    errors.append(
                        f"{path}/medias/{index}: overlaps media {previous_index}; "
                        "Camtasia Mac 2026.2.4 rejects scene-lane collisions. "
                        "Place simultaneous layers on separate tracks and verify native output"
                    )
                if previous_end is None or end > previous_end:
                    previous_end, previous_index = end, index
    return errors


def native_group_reopen_hazards(doc: dict[str, Any]) -> list[str]:
    """Reject the reproduced format-10 trimmed 2x Group duration drift.

    Two fresh native loads grow the exercised Group from 2 to 2.5 to 3 seconds
    while retaining its positive in-point. Its unanimated one-video counterpart
    retains source intervals and marker positions after rebasing the internal
    timeline to an in-point of zero; fresh saves and renders then repeat.
    This guard does not infer behavior at other unexercised Group speeds.
    """
    client = {"name": "Camtasia", "platform": "Mac", "version": "2026.2.4"}
    if doc.get("version") != "10.0" or doc.get("authoringClientName") != client:
        return []
    errors = []
    for path, node in objects(doc.get("timeline", {}), "/timeline"):
        if node.get("_type") != "Group":
            continue
        try:
            affected = (
                number(node.get("scalar")) == Fraction(1, 2) and number(node.get("mediaStart")) > 0
            )
        except ValueError:
            # validate() reports malformed clip clocks independently.
            continue
        if affected:
            errors.append(
                f"{path}: a 2x Group with a positive in-point grows on native reopen "
                "in Mac 2026.2.4. Rebase a plain unanimated Group to in-point zero "
                "while preserving child source intervals; derive and verify a stable "
                "constructor for animated Groups before applying"
            )
    return errors


def native_duplicate_track_indices(doc: dict[str, Any]) -> list[str]:
    """Reject the observed format-10 sibling-track index collision.

    A five-lane probe reused index 2 for its last two tracks and reached native
    logCorruptProjectOpened. Changing only those indices to 3/4 opened normally.
    Indices are scoped to each scene/Group; no contiguous-index rule is inferred.
    """
    client = {"name": "Camtasia", "platform": "Mac", "version": "2026.2.4"}
    if doc.get("version") != "10.0" or doc.get("authoringClientName") != client:
        return []
    errors = []
    for path, node in objects(doc.get("timeline", {}), "/timeline"):
        if not path.endswith("/csml") and node.get("_type") != "Group":
            continue
        tracks = node.get("tracks", [])
        if not isinstance(tracks, list):
            continue
        seen: set[int] = set()
        for index, track in enumerate(tracks):
            if not isinstance(track, dict) or type(track.get("trackIndex")) is not int:
                continue
            value = track["trackIndex"]
            if value in seen:
                errors.append(
                    f"{path}/tracks/{index}/trackIndex: duplicate sibling track index {value}; "
                    "assign distinct native track indices before opening the project"
                )
            seen.add(value)
    return errors


def native_hazards(doc: dict[str, Any]) -> list[str]:
    """Reject reproduced native parser hazards in their observed builds.

    A static double phase parameter with a redundant point keyframe at zero
    reaches AnimationTrack::mutex() during native loading. The same ten-preset
    corpus saves successfully with only that redundant keyframe removed.
    This guard claims no safety result for other animated behavior shapes.
    """
    errors = (
        native_lane_collisions(doc)
        + native_group_reopen_hazards(doc)
        + native_duplicate_track_indices(doc)
    )
    client = {"name": "Camtasia", "platform": "Mac", "version": "2025.0.3"}
    if doc.get("version") != "9.0" or doc.get("authoringClientName") != client:
        return errors
    for path, node in objects(doc.get("timeline", {}), "/timeline"):
        if node.get("_type") != "GenericBehaviorEffect":
            continue
        for phase in ("in", "center", "out"):
            phase_data = node.get(phase, {})
            if not isinstance(phase_data, dict):
                errors.append(f"{path}/{phase}: behavior phase must be an object")
                continue
            parameters = phase_data.get("parameters", {})
            if not isinstance(parameters, dict):
                errors.append(f"{path}/{phase}/parameters: expected an object")
                continue
            for name, parameter in parameters.items():
                if not isinstance(parameter, dict) or parameter.get("type") != "double":
                    continue
                frames = parameter.get("keyframes")
                if (
                    not isinstance(frames, list)
                    or len(frames) != 1
                    or not isinstance(frames[0], dict)
                ):
                    continue
                frame = frames[0]
                if (
                    frame.get("time") == 0
                    and frame.get("duration", 0) == 0
                    and frame.get("endTime", 0) == 0
                    and frame.get("value") == parameter.get("defaultValue")
                ):
                    errors.append(
                        f"{path}/{phase}/parameters/{name}: redundant static double behavior "
                        "keyframe reproduces a Camtasia 2025.0.3 crash; retain the default "
                        "without that redundant keyframe and verify the native behavior"
                    )
    return errors


def native_text_warnings(doc: dict[str, Any]) -> list[str]:
    """Flag incomplete byte-range coverage from the exercised Mac text renderer."""
    client = {"name": "Camtasia", "platform": "Mac", "version": "2025.0.3"}
    if doc.get("version") != "9.0" or doc.get("authoringClientName") != client:
        return []
    warnings = []
    for path, node in objects(doc.get("timeline", {}), "/timeline"):
        if node.get("_type") != "Callout" or not isinstance(node.get("def"), dict):
            continue
        definition = node["def"]
        text = definition.get("text")
        attributes = definition.get("textAttributes")
        if not isinstance(text, str) or not isinstance(attributes, dict):
            continue
        frames = attributes.get("keyframes", [])
        if not isinstance(frames, list):
            continue
        for index, frame in enumerate(frames):
            if not isinstance(frame, dict) or not isinstance(frame.get("value"), list):
                continue
            ends = [
                value["rangeEnd"]
                for value in frame["value"]
                if isinstance(value, dict) and type(value.get("rangeEnd")) is int
            ]
            size = len(text.encode("utf-8"))
            if ends and max(ends) < size:
                warnings.append(
                    f"{path}/def/textAttributes/keyframes/{index}: rich-text ranges end at "
                    f"{max(ends)} before the UTF-8 byte length {size}; this native build can "
                    "omit the suffix. Verify byte offsets, styling coverage, and rendered text"
                )
    return warnings


def native_geometry_warnings(doc: dict[str, Any]) -> list[str]:
    """Flag ordinary translation points folded by the exercised Mac renderer.

    Mac 2026.2.4 format-10 VMFile saves collapse point-only translation0/1 to
    their final static value, even with a visual interval marker. A leading
    point before a positive-duration frame becomes the initial value. This is
    not the MediaPath point parameter or a recorded cursor's point contract.
    Other properties, owners and builds require their own native evidence.
    """
    client = {"name": "Camtasia", "platform": "Mac", "version": "2026.2.4"}
    if doc.get("version") != "10.0" or doc.get("authoringClientName") != client:
        return []
    warnings = []
    for path, node in objects(doc.get("timeline", {}), "/timeline"):
        if node.get("_type") != "VMFile" or not isinstance(node.get("parameters"), dict):
            continue
        for name in ("translation0", "translation1"):
            parameter = node["parameters"].get(name)
            if not isinstance(parameter, dict) or parameter.get("type") != "double":
                continue
            frames = parameter.get("keyframes")
            if not isinstance(frames, list):
                continue
            if any(
                isinstance(frame, dict)
                and type(frame.get("duration")) is int
                and frame["duration"] == 0
                and type(frame.get("time")) is int
                and type(frame.get("endTime")) is int
                and frame["time"] == frame["endTime"]
                and type(frame.get("value")) in (int, float)
                and (type(frame["value"]) is int or math.isfinite(frame["value"]))
                for frame in frames
            ):
                warnings.append(
                    f"{path}/parameters/{name}: zero-duration ordinary geometry points "
                    "are folded into static/initial values by Mac 2026.2.4; use "
                    "positive-duration animation intervals for timed movement and "
                    "verify native save and rendered output"
                )
    return warnings


def validate(
    doc: dict[str, Any], media_root: Path, contiguous: list[str] | None = None
) -> dict[str, Any]:
    errors: list[str] = native_hazards(doc) + nonfinite_errors(doc)
    warnings: list[str] = native_text_warnings(doc) + native_geometry_warnings(doc)
    for key in ("editRate", "width", "height"):
        try:
            if number(doc.get(key)) <= 0:
                raise ValueError("must be positive")
        except ValueError as exc:
            errors.append(f"/{key}: {exc}")
    if not isinstance(doc.get("version"), str):
        errors.append("/version: expected a saved project's format version string")
    try:
        scene_tracks(doc)
    except ValueError as exc:
        errors.append(str(exc))
    # Camtasia 2025.0.3 omits sourceBin when saving a new empty project.
    sources = doc.get("sourceBin", [])
    source_ids: set[int] = set()
    if not isinstance(sources, list):
        errors.append("/sourceBin: expected an array")
        sources = []
    for index, source in enumerate(sources):
        where = f"/sourceBin/{index}"
        if not isinstance(source, dict):
            errors.append(f"{where}: expected an object")
            continue
        sid = source.get("id")
        if type(sid) is not int or sid in source_ids:
            errors.append(f"{where}/id: missing, noninteger, or duplicate source ID")
        else:
            source_ids.add(sid)
        src = source.get("src")
        if not isinstance(src, str) or not src:
            errors.append(f"{where}/src: expected a nonempty source path")
        elif "://" in src or (PureWindowsPath(src).is_absolute() and os.name != "nt"):
            warnings.append(f"{where}/src: nonlocal path not checked on this host: {src}")
        else:
            file = Path(src)
            resolved = file if file.is_absolute() else media_root / file
            if not resolved.is_file():
                errors.append(
                    f"{where}/src: missing media {src!r}; relink or copy it into the bundle"
                )
            if file.is_absolute() or not resolved.resolve().is_relative_to(media_root.resolve()):
                warnings.append(f"{where}/src: media is external to the project directory")
    clip_ids: set[int] = set()
    locations = clip_paths(doc)
    for path, node in objects(doc.get("timeline", {}), "/timeline"):
        if "medias" in node:
            medias = node["medias"]
            if not isinstance(medias, list) or not all(
                isinstance(m, dict) and "_type" in m for m in medias
            ):
                errors.append(f"{path}/medias: expected clip objects with _type")
        if path in locations:
            cid = node.get("id")
            if type(cid) is not int or cid in clip_ids:
                errors.append(f"{path}/id: missing, noninteger, or duplicate clip ID")
            else:
                clip_ids.add(cid)
            kind = node.get("_type")
            if not isinstance(kind, str):
                errors.append(f"{path}/_type: expected a clip type string")
            elif kind not in KNOWN_CLIPS:
                warnings.append(
                    f"{path}: unrecognized clip type {kind!r}; preserved, semantics unchecked"
                )
            if isinstance(kind, str) and kind in FILE_CLIPS and "src" not in node:
                errors.append(f"{path}/src: {kind} needs a source-bin reference")
            for key in ("start", "duration", "mediaStart", "mediaDuration", "scalar"):
                try:
                    value = number(node.get(key))
                    if key in ("duration", "mediaDuration", "scalar") and value <= 0:
                        raise ValueError("must be positive")
                except ValueError as exc:
                    errors.append(f"{path}/{key}: {exc}")
            if "src" in node and (type(node["src"]) is not int or node["src"] not in source_ids):
                errors.append(f"{path}/src: dangling source ID {node['src']!r}")
            if kind == "Group" and not isinstance(node.get("tracks"), list):
                errors.append(f"{path}/tracks: Group needs child tracks")
            if kind == "UnifiedMedia" and not all(
                isinstance(node.get(k), dict) for k in ("video", "audio")
            ):
                errors.append(f"{path}: UnifiedMedia needs video and audio children")
        if "medias" in node and isinstance(node["medias"], list):
            local_ids = {
                m.get("id")
                for m in node["medias"]
                if isinstance(m, dict) and type(m.get("id")) is int
            }
            transitions = node.get("transitions", [])
            if not isinstance(transitions, list):
                errors.append(f"{path}/transitions: expected an array")
                continue
            for i, transition in enumerate(transitions):
                where = f"{path}/transitions/{i}"
                if not isinstance(transition, dict):
                    errors.append(f"{where}: expected an object")
                    continue
                endpoints = [
                    transition.get(k)
                    for k in ("leftMedia", "rightMedia")
                    if transition.get(k) is not None
                ]
                if not endpoints or any(
                    type(e) is not int or e not in local_ids for e in endpoints
                ):
                    errors.append(
                        f"{where}: transition endpoints must reference clips on this track"
                    )
                try:
                    if number(transition.get("duration")) <= 0:
                        raise ValueError("must be positive")
                except ValueError as exc:
                    errors.append(f"{where}/duration: {exc}")
    for selector in contiguous or []:
        try:
            clips = selected_track(doc, selector).get("medias", [])
            intervals = sorted((number(m["start"]), number(m["duration"])) for m in clips)
            end = Fraction(0)
            for start, duration in intervals:
                if start != end:
                    errors.append(
                        f"track {selector}: gap or overlap at tick {start}; previous end {end}"
                    )
                end = start + duration
        except (ValueError, KeyError, TypeError) as exc:
            errors.append(f"track {selector}: cannot check continuity: {exc}")
    return {"ok": not errors, "errors": errors, "warnings": warnings, "limits": LIMITS}


def inventory(doc: dict[str, Any], raw: bytes, root: Path) -> dict[str, Any]:
    types: Counter[str] = Counter()
    effects: Counter[str] = Counter()
    tracks = []
    locations = clip_paths(doc)
    for path, node in objects(doc.get("timeline", {}), "/timeline"):
        if path in locations:
            types[str(node.get("_type"))] += 1
        if "effectName" in node:
            effects[str(node["effectName"])] += 1
        if "medias" in node:
            tracks.append(
                {
                    "path": path,
                    "trackIndex": node.get("trackIndex"),
                    "name": node.get("ident"),
                    "clipCount": len(node["medias"]) if isinstance(node["medias"], list) else None,
                }
            )
    return {
        "sha256": digest(raw),
        "formatVersion": doc.get("version"),
        "authoringClient": doc.get("authoringClientName", doc.get("clientName")),
        "editRate": doc.get("editRate"),
        "frameRate": doc.get("videoFormatFrameRate"),
        "canvas": [doc.get("width"), doc.get("height")],
        "tracks": tracks,
        "clipTypes": dict(types),
        "effects": dict(effects),
        "assetReferences": asset_references(doc),
        "validation": validate(doc, root),
    }


def asset_references(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """Expose demonstrated logical asset selectors without guessing file paths.

    The finite parameter registry is ASSET_PARAMETERS. Preserve each location,
    including wrapper/child mirrors, so a consumer can edit the actual owner.
    This is not an inventory of all fonts, models, assets, or transitive files.
    """
    result = []
    for path, node in objects(doc):
        effect_name = node.get("effectName")
        parameters = node.get("parameters")
        if not isinstance(effect_name, str) or not isinstance(parameters, dict):
            continue
        for name in ASSET_PARAMETERS.get(effect_name, ()):
            if name in parameters:
                result.append(
                    {
                        "path": pointer(pointer(path, "parameters"), name),
                        "effectName": node["effectName"],
                        "parameter": name,
                        "reference": parameters[name],
                        "resolution": "Requires target-editor asset resolution; not checked as source-bin media.",
                    }
                )
    return result


def source_file_digest(path: Path) -> dict[str, Any]:
    """Hash one regular source and refuse changes/replacement during the read."""

    def identity(info: os.stat_result) -> tuple[int, int, int, int, int]:
        return (info.st_dev, info.st_ino, info.st_size, info.st_mtime_ns, info.st_ctime_ns)

    checksum = hashlib.sha256()
    flags = os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)
    with os.fdopen(os.open(path, flags), "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError(f"Source is not a regular file: {path}; inspect its media reference")
        while chunk := stream.read(HASH_CHUNK_BYTES):
            checksum.update(chunk)
        after = os.fstat(stream.fileno())
    if identity(before) != identity(after) or identity(after) != identity(path.stat()):
        raise ValueError(f"Source changed while hashing: {path}; finish media writes and rerun")
    return {"sizeBytes": after.st_size, "sha256": checksum.hexdigest()}


def source_manifest(doc: dict[str, Any], raw: bytes, media_root: Path) -> dict[str, Any]:
    """Read-only source-bin closure, separate from native dependency portability.

    Schema 1 is owned by camtasia-source-manifest. Sources retain array order,
    identity and stored paths. Only local regular files are hashed. URLs and
    foreign-platform paths are never fetched or opened. The bundled result
    requires a relative reference resolving inside media_root, including after
    symlink resolution. Logical installation selectors remain unresolved.
    No report authorizes writes or claims complete native asset closure.
    """
    sources = doc.get("sourceBin", [])
    if not isinstance(sources, list):
        raise ValueError("/sourceBin must be an array; repair the project before manifesting media")
    root = media_root.resolve(strict=True)
    if not root.is_dir():
        raise ValueError(f"Media root is not a directory: {root}; select the destination bundle")
    rows: list[dict[str, Any]] = []
    seen: set[int] = set()
    for index, source in enumerate(sources):
        where = f"/sourceBin/{index}"
        if not isinstance(source, dict):
            raise ValueError(f"{where} must be an object; repair the source-bin entry")
        sid, stored = source.get("id"), source.get("src")
        if type(sid) is not int or sid in seen:
            raise ValueError(f"{where}/id must be a distinct integer; repair source identities")
        seen.add(sid)
        if not isinstance(stored, str) or not stored or "\0" in stored:
            raise ValueError(f"{where}/src must be a nonempty file reference without NUL bytes")
        row: dict[str, Any] = {
            "path": where + "/src",
            "sourceId": sid,
            "storedPath": stored,
            "resolvedPath": None,
            "status": "unchecked",
            "bundled": False,
            "sizeBytes": None,
            "sha256": None,
        }
        if "://" in stored or (PureWindowsPath(stored).is_absolute() and os.name != "nt"):
            row["reason"] = "Nonlocal or foreign-platform reference; resolve on the target host."
        else:
            file = Path(stored)
            source_path = file if file.is_absolute() else root / file
            resolved = source_path.resolve()
            row["resolvedPath"] = str(resolved)
            if resolved.is_file():
                row.update(source_file_digest(resolved))
                if source_path.resolve() != resolved:
                    raise ValueError(
                        f"Source link changed while hashing: {stored}; rerun the manifest"
                    )
                row["status"] = "available"
                row["bundled"] = not file.is_absolute() and resolved.is_relative_to(root)
            else:
                row["status"] = "missing"
                row["reason"] = "Source is absent or not a regular file; relink before delivery."
        rows.append(row)
    return {
        "schema_version": 1,
        "owner": "camtasia-source-manifest",
        "ok": all(row["status"] == "available" for row in rows),
        "projectSha256": digest(raw),
        "mediaRoot": str(root),
        "sources": rows,
        "allSourcesBundled": all(row["status"] == "available" and row["bundled"] for row in rows),
        "assetReferences": asset_references(doc),
        "limits": [
            "Source-bin file closure only; not complete native dependency or portability proof.",
            "Fonts, models, installation assets, bookmarks, and bundle companions are not resolved.",
            "Read-only snapshot; recheck hashes and native playback on the destination host.",
        ],
    }


def differences(before: Any, after: Any, path: str = "") -> Iterator[dict[str, Any]]:
    def preview(value: Any) -> str:
        text = _encode_json_value(value)
        return text if len(text) <= PREVIEW_CHARS else text[:PREVIEW_CHARS] + "…"

    if type(before) is type(after) and isinstance(before, dict):
        for key in sorted(before.keys() | after.keys()):
            child = pointer(path, key)
            if key not in before:
                yield {"path": child, "change": "added", "after": preview(after[key])}
            elif key not in after:
                yield {"path": child, "change": "removed", "before": preview(before[key])}
            else:
                yield from differences(before[key], after[key], child)
    elif isinstance(before, list) and isinstance(after, list):
        for i in range(max(len(before), len(after))):
            child = pointer(path, i)
            if i >= len(before):
                yield {"path": child, "change": "added", "after": preview(after[i])}
            elif i >= len(after):
                yield {"path": child, "change": "removed", "before": preview(before[i])}
            else:
                yield from differences(before[i], after[i], child)
    elif before != after or type(before) is not type(after):
        yield {
            "path": path,
            "change": "changed",
            "before": preview(before),
            "after": preview(after),
        }


def ensure_closed(target: Path) -> None:
    """Check marker plus macOS process handles; uncertainty refuses writes."""
    marker = target.with_name("~" + target.name)
    if marker.is_file() and marker.stat().st_size:
        raise ValueError(f"{marker} has recovery/live data; save and close the project in Camtasia")
    if sys.platform != "darwin":
        raise ValueError(
            "live project ownership checks support macOS only; stage the candidate and save through Camtasia on this platform"
        )
    for name in ("pgrep", "lsof"):
        if shutil.which(name) is None:
            raise ValueError(f"{name} is missing; restore the system tool before applying")
    running = subprocess.run(
        ["pgrep", "-ix", "Camtasia"], capture_output=True, text=True, check=False
    )
    if running.returncode == 1:
        return
    if running.returncode != 0:
        raise ValueError(f"cannot check Camtasia processes: {running.stderr.strip()}")
    held = subprocess.run(
        ["lsof", "-Fn", "-p", ",".join(running.stdout.split())],
        capture_output=True,
        text=True,
        check=False,
    )
    if held.returncode != 0 or not held.stdout:
        raise ValueError("cannot inspect Camtasia file handles; quit Camtasia before applying")
    bundle = target.parent if target.parent.suffix.lower() == ".cmproj" else None
    for line in held.stdout.splitlines():
        if line.startswith("n/"):
            opened = Path(line[1:]).resolve()
            if opened == target.resolve() or (
                bundle is not None and opened.is_relative_to(bundle.resolve())
            ):
                raise ValueError(
                    f"Camtasia holds {opened}; save and close the target before applying. "
                    "If it is already closed, quit Camtasia normally to release cached handles"
                )


def protected(doc: dict[str, Any], selector: str) -> dict[str, Any]:
    track = selected_track(doc, selector)
    refs = {n["src"] for _, n in objects(track) if type(n.get("src")) is int}
    _, index = (int(part) for part in selector.split(":"))
    attrs = doc.get("timeline", {}).get("trackAttributes", [])
    return {
        "track": track,
        "attributes": attrs[index] if index < len(attrs) else None,
        "sources": [s for s in doc.get("sourceBin", []) if s.get("id") in refs],
        "audioSettings": {
            k: doc.get(k)
            for k in ("targetLoudness", "shouldApplyLoudnessNormalization", "audioFormatSampleRate")
        },
        "timelineAudioSettings": {
            k: doc.get("timeline", {}).get(k) for k in ("gain", "legacyAttenuateAudioMix")
        },
    }


def apply_candidate(
    target: Path, candidate: Path, expected: str, preserve: list[str], contiguous: list[str]
) -> dict[str, Any]:
    target = project_file(target)
    if target.is_symlink():
        raise ValueError("refusing a symlink target; use the real project path")
    before, raw = load(target)
    after, candidate_raw = load(candidate)
    report = validate(after, target.parent, contiguous)
    if not report["ok"]:
        return {"changed": False, "validation": report}
    if before == after:
        return {"changed": False, "sha256": digest(raw), "backup": None, "validation": report}
    if digest(raw) != expected:
        raise ValueError(
            "project changed since inspection; inspect it again and rebuild the candidate"
        )
    for key in ("version", "authoringClientName", "clientName"):
        if before.get(key) != after.get(key):
            raise ValueError(
                f"/{key} changed; generate the candidate with the target editor's format identity"
            )
    for selector in preserve:
        if protected(before, selector) != protected(after, selector):
            raise ValueError(
                f"preserved track {selector}, its source entries, or audio settings changed"
            )
    ensure_closed(target)
    if target.read_bytes() != raw:
        raise ValueError("project changed during validation; inspect again before applying")
    backup = target.with_name(f"{target.stem}.before-{digest(raw)}.tscproj")
    try:
        with backup.open("xb") as stream:
            stream.write(raw)
            stream.flush()
            os.fsync(stream.fileno())
    except FileExistsError:
        if backup.read_bytes() != raw:
            raise ValueError(
                f"backup collision at {backup}; preserve that file and choose a clean target"
            )
    fd, name = tempfile.mkstemp(prefix=".camtasia-", suffix=".writing", dir=target.parent)
    staging = Path(name)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(candidate_raw)
            stream.flush()
            os.fsync(stream.fileno())
        staging.chmod(stat.S_IMODE(target.stat().st_mode))
        ensure_closed(target)
        if target.read_bytes() != raw:
            raise ValueError(
                "project changed before replacement; rebuild the candidate from a fresh inspection"
            )
        os.replace(staging, target)
    finally:
        staging.unlink(missing_ok=True)
    return {
        "changed": True,
        "sha256": digest(candidate_raw),
        "backup": str(backup),
        "validation": report,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "validate", "source-manifest", "diff", "apply"):
        command = commands.add_parser(name)
        command.add_argument("project", type=Path)
        if name in ("diff", "apply"):
            command.add_argument("candidate", type=Path)
        if name in ("validate", "source-manifest"):
            command.add_argument("--media-root", type=Path)
        if name in ("validate", "apply"):
            command.add_argument("--contiguous-track", action="append", default=[])
        if name == "diff":
            command.add_argument("--limit", type=int, default=DEFAULT_DIFF_LIMIT)
        if name == "apply":
            command.add_argument("--expected-sha256", required=True)
            command.add_argument("--preserve-track", action="append", default=[])
    args = parser.parse_args(argv)
    try:
        doc, raw = load(args.project)
        root = project_file(args.project).parent
        if args.command == "inspect":
            result = inventory(doc, raw, root)
        elif args.command == "validate":
            result = validate(doc, args.media_root or root, args.contiguous_track)
        elif args.command == "source-manifest":
            result = source_manifest(doc, raw, args.media_root or root)
        elif args.command == "diff":
            if args.limit < 1:
                parser.error("--limit must be positive")
            after, _ = load(args.candidate)
            changes = list(differences(doc, after))
            result = {
                "count": len(changes),
                "changes": changes[: args.limit],
                "truncated": len(changes) > args.limit,
            }
        else:
            result = apply_candidate(
                args.project,
                args.candidate,
                args.expected_sha256,
                args.preserve_track,
                args.contiguous_track,
            )
        print(json.dumps(result, ensure_ascii=False))
        report = result.get("validation", result)
        return 1 if report.get("ok") is False else 0
    except (OSError, ValueError, UnicodeError, subprocess.SubprocessError) as exc:
        print(f"Camtasia project: {exc}", file=sys.stderr)
        print(json.dumps({"ok": False, "error": str(exc)}))
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
