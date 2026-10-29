#!/usr/bin/env python3
"""Stage interactive-hotspot JSON without opening or changing a Camtasia project.

Native contract: Mac 2026.2.4, format 10.0; visual types in VISUAL_TYPES,
including UnifiedMedia.video. Native application stores Group hotspots on the
Group itself, independently of its children.
The four actions and defaults come from independent native property/save captures.
Marker targets use the logical media owner: a linked video's markers live on its
video child, but markerParametricId identifies the UnifiedMedia wrapper. Verified
single-scene media/Group clocks resolve marker global time automatically, using
exact rational arithmetic and treating linked child timing as a mirror. Other
clock structures require an explicit global time. Smart Player behavior
requires a separate native web export/runtime check; MP4 is not interactive.

CLI: inspect PROJECT; set/remove PROJECT --clip-id ID --output CANDIDATE.
set requires --action continue|time|url|marker and the corresponding target.
All time arguments are nonnegative rational seconds, exactly representable in
the project's edit rate. An existing candidate is accepted only if byte-identical.
Exit 0: inspection/staging succeeded; 1: input/I/O refusal; 2: argument syntax.
Stdout reports schema_version 1, owner camtasia-hotspots, input hash and outcome.
No media is read, no original is written, and no editor/export is launched.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any

import project

NATIVE_CLIENT = {"name": "Camtasia", "platform": "Mac", "version": "2026.2.4"}
ACTIONS = {"continue": 0, "time": 1, "url": 2, "marker": 3}
VISUAL_TYPES = frozenset({"VMFile", "IMFile", "ScreenVMFile", "Callout", "Group"})
DEFAULT_HOTSPOT = {
    "action": 0,
    "gotoTime": 0,
    "pauseAtEnd": True,
    "url": "",
    "openURLInNewWindow": True,
    "markerParametricId": 0,
    "markerTime": -1,
    "lastMarkerGlobalTime": 0,
}


def ticks(doc: dict[str, Any], seconds: Any) -> int:
    rate, value = project.number(doc.get("editRate")), project.number(seconds)
    if rate <= 0 or value < 0:
        raise ValueError("use a positive project editRate and nonnegative target seconds")
    result = rate * value
    if result.denominator != 1:
        raise ValueError("target falls between project ticks; supply an exactly representable time")
    return result.numerator


def clips(doc: dict[str, Any]) -> list[tuple[str, dict[str, Any]]]:
    paths = project.clip_paths(doc)
    return [(path, node) for path, node in project.objects(doc) if path in paths]


def visual_target(
    doc: dict[str, Any], clip_id: int, *, visual_types: frozenset[str] = VISUAL_TYPES
) -> tuple[str, dict[str, Any]]:
    if type(clip_id) is not int:
        raise ValueError("select a numeric clip ID from project inspection")
    matches = [(p, n) for p, n in clips(doc) if n.get("id") == clip_id]
    if len(matches) != 1:
        raise ValueError(f"clip ID {clip_id} is missing or ambiguous; inspect and repair IDs")
    path, node = matches[0]
    if node.get("_type") == "UnifiedMedia":
        node = node.get("video")
        path = project.pointer(path, "video")
    if not isinstance(node, dict) or node.get("_type") not in visual_types:
        raise ValueError("select a visual clip type verified for the requested operation")
    return path, node


def markers(doc: dict[str, Any]) -> list[dict[str, Any]]:
    """List existing native points, retaining physical and logical owner identity."""
    candidates = [("/timeline", doc.get("timeline", {}))]
    linked_children = set()
    for path, node in clips(doc):
        if node.get("_type") == "UnifiedMedia":
            linked_children.update(project.pointer(path, key) for key in ("video", "audio"))
    for path, node in clips(doc):
        if path in linked_children:
            continue
        candidates.append((path, node))
    result = []
    for path, owner in candidates:
        if not isinstance(owner, dict):
            continue
        parameter_owner, parameter_path = owner, path
        if owner.get("_type") == "UnifiedMedia":
            parameter_owner = owner.get("video", {})
            parameter_path = project.pointer(path, "video")
        if not isinstance(parameter_owner, dict):
            raise ValueError(
                f"{parameter_path}: repair the linked visual child before inspecting markers"
            )
        parameters = parameter_owner.get("parameters", {})
        if not isinstance(parameters, dict) or "toc" not in parameters:
            continue
        toc = parameters["toc"]
        if not isinstance(toc, dict) or toc.get("type") != "string":
            raise ValueError(f"{parameter_path}/parameters/toc: inspect unfamiliar marker encoding")
        frames = toc.get("keyframes", [])
        if not isinstance(frames, list):
            raise ValueError(f"{parameter_path}/parameters/toc: repair marker keyframes array")
        for index, frame in enumerate(frames):
            if not isinstance(frame, dict):
                raise ValueError(f"{parameter_path}: repair marker point {index}")
            time = project.number(frame.get("time"))
            if (
                type(owner.get("id")) is not int
                or time < 0
                or time.denominator != 1
                or project.number(frame.get("duration")) != 0
                or project.number(frame.get("endTime")) != time
                or not isinstance(frame.get("value"), str)
            ):
                raise ValueError(f"{parameter_path}: inspect unsupported marker point {index}")
            result.append(
                {
                    "ownerId": owner["id"],
                    "parameterOwnerId": parameter_owner.get("id"),
                    "path": f"{parameter_path}/parameters/toc/keyframes/{index}",
                    "time": time.numerator,
                    "label": frame["value"],
                    "timelineMarker": path == "/timeline",
                }
            )
    return result


def marker_global_ticks(doc: dict[str, Any], owner_id: int, point: int) -> int:
    """Map an existing point through its observed media/Group ancestry.

    Native image holds have mediaDuration 1 even when holding for seconds; use
    their visible duration, not mediaDuration, when checking point visibility.
    UnifiedMedia owns one transform; its video's mirrored start is not added.
    Exact native captures cover trims, inverse speed, nested Groups and Group
    markers. Stitched containers, multiple scenes, missing timing, trimmed-out
    points and fractional final ticks require the explicit caller-supplied path.
    """
    if type(owner_id) is not int or type(point) is not int:
        raise ValueError("use the numeric marker owner and integer point from inspection")
    timeline = doc.get("timeline", {})
    if isinstance(timeline, dict) and timeline.get("id") == owner_id:
        return point
    if len(project.scene_tracks(doc)) != 1:
        raise ValueError("multiple scene clocks require an explicit global marker time")
    nodes = clips(doc)
    owners = [(path, node) for path, node in nodes if node.get("id") == owner_id]
    if len(owners) != 1:
        raise ValueError("marker owner is missing or ambiguous; repair clip IDs")
    path, owner = owners[0]
    if owner.get("_type") not in VISUAL_TYPES | {"UnifiedMedia"}:
        raise ValueError("this marker owner's clock needs a native global-time example")
    ancestors = sorted(
        [(p, n) for p, n in nodes if path.startswith(p + "/")],
        key=lambda entry: len(entry[0]),
        reverse=True,
    )
    if any(node.get("_type") != "Group" for _, node in ancestors):
        raise ValueError("this container's clock requires an explicit global marker time")
    result = project.number(point)
    for _, node in [(path, owner), *ancestors]:
        start = project.number(node.get("start"))
        media_start = project.number(node.get("mediaStart"))
        scalar = project.number(node.get("scalar"))
        duration = project.number(node.get("duration"))
        if scalar <= 0 or duration <= 0:
            raise ValueError("use positive scalar/duration or supply a verified global marker time")
        result = start + (result - media_start) * scalar
        if not start <= result <= start + duration:
            raise ValueError("marker is outside its visible trimmed interval")
    if result.denominator != 1:
        raise ValueError("mapped marker falls between project ticks; supply a verified global time")
    return result.numerator


def edit_hotspot(
    doc: dict[str, Any],
    clip_id: int,
    action: str,
    *,
    time: Any = None,
    url: str | None = None,
    pause: bool | None = None,
    new_window: bool | None = None,
    marker_owner: int | None = None,
    marker_time: Any = None,
    marker_global_time: Any = None,
) -> dict[str, Any]:
    """Return a separate candidate, preserving inactive and unfamiliar fields."""
    if doc.get("version") != "10.0" or doc.get("authoringClientName") != NATIVE_CLIENT:
        raise ValueError(
            "use the observed Mac 2026.2.4 format-10 project; capture other builds first"
        )
    if action not in {*ACTIONS, "remove"}:
        raise ValueError("choose continue, time, url, marker or remove")
    for name, value in (("pause", pause), ("new_window", new_window)):
        if value is not None and type(value) is not bool:
            raise ValueError(f"{name} must be a boolean or omitted")
    targets = {"time": time, "url": url, "marker": marker_owner}
    if any(value is not None and name != action for name, value in targets.items()):
        raise ValueError("supply target arguments only for the selected action")
    if (marker_time is not None or marker_global_time is not None) and action != "marker":
        raise ValueError("supply marker times only for the marker action")
    if new_window is not None and action != "url":
        raise ValueError("supply a new-window choice only for a URL action")
    if action == "remove" and pause is not None:
        raise ValueError("remove takes no hotspot settings")
    candidate = copy.deepcopy(doc)
    _, node = visual_target(candidate, clip_id)
    attributes = node.get("attributes", {})
    if not isinstance(attributes, dict):
        raise ValueError("inspect malformed clip attributes before editing its hotspot")
    if action == "remove":
        attributes.pop("hotspot", None)
        return candidate
    hotspot = attributes.get("hotspot", {})
    if not isinstance(hotspot, dict):
        raise ValueError("inspect unfamiliar hotspot encoding before replacing it")
    hotspot = {**DEFAULT_HOTSPOT, **hotspot}
    hotspot["action"] = ACTIONS[action]
    if pause is not None:
        hotspot["pauseAtEnd"] = pause
    if action == "continue":
        if pause is False:
            raise ValueError("Click to continue requires Pause at end; omit --no-pause")
        hotspot["pauseAtEnd"] = True
    elif action == "time":
        if time is None:
            raise ValueError("supply --time in project seconds for the seek destination")
        hotspot["gotoTime"] = ticks(doc, time)
    elif action == "url":
        if not isinstance(url, str) or not url or url != url.strip():
            raise ValueError("supply a nonempty URL without surrounding whitespace")
        if any(ord(char) < 32 or ord(char) == 127 for char in url):
            raise ValueError("remove control characters from the hotspot URL")
        hotspot["url"] = url
        if new_window is not None:
            hotspot["openURLInNewWindow"] = new_window
    else:
        if type(marker_owner) is not int or marker_time is None:
            raise ValueError("supply --marker-owner and --marker-time from marker inspection")
        target_time = ticks(doc, marker_time)
        matches = [
            marker
            for marker in markers(doc)
            if marker["ownerId"] == marker_owner and marker["time"] == target_time
        ]
        if len(matches) != 1:
            raise ValueError("marker owner/time is missing or ambiguous; inspect existing points")
        if matches[0]["timelineMarker"]:
            global_time = target_time
            if marker_global_time is not None and ticks(doc, marker_global_time) != global_time:
                raise ValueError("timeline marker global time must equal its existing point time")
        else:
            if marker_global_time is None:
                try:
                    global_time = marker_global_ticks(doc, marker_owner, target_time)
                except ValueError as exc:
                    raise ValueError(
                        f"supply --marker-global-time from native evidence: {exc}"
                    ) from exc
            else:
                global_time = ticks(doc, marker_global_time)
                try:
                    mapped_time = marker_global_ticks(doc, marker_owner, target_time)
                except ValueError:
                    # Explicit caller timing covers structures outside this mapper's
                    # observed contract; the staged candidate still needs native proof.
                    mapped_time = None
                if mapped_time is not None and mapped_time != global_time:
                    raise ValueError(
                        "explicit global marker time conflicts with the clip-clock mapping"
                    )
        hotspot.update(
            markerParametricId=marker_owner,
            markerTime=target_time,
            lastMarkerGlobalTime=global_time,
        )
    attributes["hotspot"] = hotspot
    node["attributes"] = attributes
    return candidate


def stage(source: Path, output: Path, candidate: dict[str, Any]) -> bool:
    """Write a new full candidate; accept an identical rerun without overwriting."""
    if output.is_symlink() or output.resolve() == project.project_file(source).resolve():
        raise ValueError("choose a separate nonsymlink candidate file outside the source document")
    raw = project.encode_document(candidate)
    try:
        with output.open("xb") as stream:
            stream.write(raw)
    except FileExistsError:
        if not output.is_file() or output.read_bytes() != raw:
            raise ValueError(
                "candidate path contains different data; choose a new output path"
            ) from None
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("project", type=Path)
    for command in ("set", "remove"):
        edit = commands.add_parser(command)
        edit.add_argument("project", type=Path)
        edit.add_argument("--clip-id", type=int, required=True)
        edit.add_argument("--output", type=Path, required=True)
        if command == "set":
            edit.add_argument("--action", choices=sorted(ACTIONS), required=True)
            edit.add_argument("--time")
            edit.add_argument("--url")
            edit.add_argument("--pause", action=argparse.BooleanOptionalAction, default=None)
            edit.add_argument("--new-window", action=argparse.BooleanOptionalAction, default=None)
            edit.add_argument("--marker-owner", type=int)
            edit.add_argument("--marker-time")
            edit.add_argument("--marker-global-time")
    args = parser.parse_args(argv)
    try:
        doc, raw = project.load(args.project)
        report: dict[str, Any] = {
            "schema_version": 1,
            "owner": "camtasia-hotspots",
            "ok": True,
            "projectSha256": project.digest(raw),
        }
        if args.command == "inspect":
            report.update(
                markers=markers(doc),
                hotspots=[
                    {"path": path, "clipId": node.get("id"), "hotspot": attributes["hotspot"]}
                    for path, node in clips(doc)
                    if isinstance(attributes := node.get("attributes"), dict)
                    and "hotspot" in attributes
                ],
            )
        else:
            options = (
                {
                    key: getattr(args, key)
                    for key in (
                        "time",
                        "url",
                        "pause",
                        "new_window",
                        "marker_owner",
                        "marker_time",
                        "marker_global_time",
                    )
                }
                if args.command == "set"
                else {}
            )
            candidate = edit_hotspot(
                doc, args.clip_id, args.action if args.command == "set" else "remove", **options
            )
            path, node = visual_target(candidate, args.clip_id)
            report.update(
                output=str(args.output),
                written=stage(args.project, args.output, candidate),
                candidateSha256=project.digest(project.encode_document(candidate)),
                changed=candidate != doc,
                clipPath=path,
                hotspot=node.get("attributes", {}).get("hotspot"),
                nativeVerified=False,
            )
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
