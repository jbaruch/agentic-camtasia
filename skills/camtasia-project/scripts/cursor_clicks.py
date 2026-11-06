#!/usr/bin/env python3
"""Stage explicit cursor click lists on Mac 2026.2.4 format 10.

inspect PROJECT reports physical generated CursorPath and ScreenVMFile click
payloads; inventory does not promise editability. set-path-clicks PROJECT
--clip-id ID --spec SPEC --output CANDIDATE replaces clicks on an existing
root ordinary/linked video CursorPath. set-recorded-clicks replaces only authored
cursorAction.edits on a standalone root moving recording. The selectors in
cursor_paths.selected/recording_target own the verified build, owner, mirror,
clock and token boundaries. Neither command constructs an effect or recording.

Spec schema_version 1 requires exactly clicks: an ordered list of objects with
clip-relative timeline time (rational seconds) and button (left or right).
BUTTONS owns native values. Source ticks are mediaStart + time * editRate/scalar;
require exact, nonnegative, strictly increasing ticks. Clip placement is not
added; out-of-trim events survive. Empty clicks clears the selected authored
list. Same-time native event metadata survives; deleted/retimed events donate
no opaque fields to other events. Explicit replacement chooses one button per
timestamp; no interpolation or press/release/button-mask inference is made.

Generated clicks are typed int zero-duration keyframes. Their required source-
zero anchor stays present: it has value zero unless the spec explicitly places
a click there. Empty clicks restores that native zero value, unlike the known
native time-zero Remove UI quirk. All other descriptor fields survive.
Recordings use time/value edits, not typed frames. Existing deletions (opaque
nonnegative integer entries) and extra metadata survive untouched. An
empty edits-only override is removed, matching native removal of its last
authored click. Existing deletions/other fields retain an empty edits array.
This does not erase or restore captured TREC clicks, decode samples, change
deletion entries, or rewrite the recording. Unknown source override,
interpolation, event values and typed/partial descriptor forms refuse.

Cursor paths/images, scale/opacity/smoothing, geometry, effects, tokens, sources
and audio remain unchanged. Rendering still requires a native matching click
effect and cursor resources; event authoring alone does not create a visible
ripple/target or sound. Follow project diff/validate/apply and native save/reopen/
render checks. No editor launches or original project/media writes occur.
Stdout schema_version 1 owner camtasia-cursor-clicks has projectSha256 and paths/
recordings inventory; edit reports add hashes, output, changed/written and
nativeVerified false. Exclusive or identical staging uses hotspots.stage.
JSON diagnostics use stderr: exit 1 input/I/O refusal, 2 CLI syntax; exit 0
success. --help emits the same owner/schema version with ok true and a help
string containing argparse's usage, description and available options.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
from typing import Any

import cursor_paths
import hotspots
import project

BUTTONS = {"left": 1, "right": 4}
VALUES = frozenset(BUTTONS.values())


class JsonHelpParser(cursor_paths.JsonArgumentParser):
    def format_help(self) -> str:
        return (
            json.dumps(
                dict(
                    schema_version=1,
                    owner="camtasia-cursor-clicks",
                    ok=True,
                    help=super().format_help(),
                ),
                ensure_ascii=False,
            )
            + "\n"
        )


def spec_clicks(spec: Any) -> list[Any]:
    if (
        not isinstance(spec, dict)
        or set(spec) != {"schema_version", "clicks"}
        or type(spec["schema_version"]) is not int
        or spec["schema_version"] != 1
        or not isinstance(spec["clicks"], list)
    ):
        raise ValueError("supply cursor-click schema_version 1 with the complete clicks list")
    return spec["clicks"]


def events(
    doc: dict[str, Any], visual: dict[str, Any], clicks: list[Any], old: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    rate, scalar = project.number(doc.get("editRate")), project.number(visual.get("scalar"))
    if rate <= 0 or scalar <= 0:
        raise ValueError("repair positive project edit rate and visual inverse speed")
    origin = project.number(visual.get("mediaStart"))
    previous = -1
    old_by_time = {event["time"]: event for event in old}
    result = []
    for click in clicks:
        if (
            not isinstance(click, dict)
            or set(click) != {"time", "button"}
            or not isinstance(click["button"], str)
            or click["button"] not in BUTTONS
        ):
            raise ValueError("supply each click's time and left or right button only")
        time = origin + project.number(click["time"]) * rate / scalar
        if time.denominator != 1 or time <= previous:
            raise ValueError("supply ordered clicks on exact nonnegative source ticks")
        previous = time
        event = copy.deepcopy(old_by_time.get(int(time), {}))
        event.update(time=int(time), value=BUTTONS[click["button"]])
        result.append(event)
    return result


def path_curve(effect: dict[str, Any]) -> dict[str, Any]:
    curve = effect["parameters"].get("cursorAction")
    if (
        not isinstance(curve, dict)
        or curve.get("type") != "int"
        or {"defaultValue", "edits", "deletions", "ignoreSource", "interp"} & curve.keys()
        or not isinstance(curve.get("keyframes"), list)
        or not curve["keyframes"]
    ):
        raise ValueError("capture the native cursorAction int keyframes and source-zero anchor")
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
            or type(frame.get("value")) is not int
            or frame["value"] not in (VALUES | {0} if frame["time"] == 0 else VALUES)
            or "interp" in frame
        ):
            raise ValueError(
                "capture ordered known native click point frames without interpolation"
            )
        previous = frame["time"]
    if curve["keyframes"][0]["time"] != 0:
        raise ValueError("capture the native source-zero cursorAction anchor before editing")
    return curve


def set_path_clicks(doc: dict[str, Any], clip_id: int, spec: Any) -> dict[str, Any]:
    clicks = spec_clicks(spec)
    result = copy.deepcopy(doc)
    targets = cursor_paths.selected(result, clip_id)
    for _, effect in targets:
        curve = path_curve(effect)
        frames = events(result, targets[-1][0], clicks, curve["keyframes"])
        if not frames or frames[0]["time"] != 0:
            anchor = copy.deepcopy(curve["keyframes"][0])
            anchor["value"] = 0
            frames.insert(0, anchor)
        for frame in frames:
            frame.update(endTime=frame["time"], duration=0)
        curve["keyframes"] = frames
        path_curve(effect)
    return result


def recorded_override(override: Any) -> dict[str, Any]:
    if (
        not isinstance(override, dict)
        or {"type", "keyframes", "defaultValue", "ignoreSource", "interp"} & override.keys()
        or not isinstance(override.get("edits"), list)
    ):
        raise ValueError(
            "capture recording cursorAction edits and preserve native deletion entries"
        )
    if "deletions" in override:
        deleted = override["deletions"]
        if (
            not isinstance(deleted, list)
            or any(type(index) is not int or index < 0 for index in deleted)
            or len(set(deleted)) != len(deleted)
        ):
            raise ValueError("capture distinct nonnegative native click deletion entries")
    previous = -1
    for edit in override["edits"]:
        if (
            not isinstance(edit, dict)
            or {"type", "keyframes", "endTime", "duration", "interp", "ignoreSource"} & edit.keys()
            or type(edit.get("time")) is not int
            or edit["time"] <= previous
            or type(edit.get("value")) is not int
            or edit["value"] not in VALUES
        ):
            raise ValueError(
                "capture ordered recording click time/value edits without interpolation"
            )
        previous = edit["time"]
    return override


def set_recorded_clicks(doc: dict[str, Any], clip_id: int, spec: Any) -> dict[str, Any]:
    clicks = spec_clicks(spec)
    result = copy.deepcopy(doc)
    visual = cursor_paths.recording_target(result, clip_id)
    parameters = visual["parameters"]
    override = (
        recorded_override(parameters["cursorAction"])
        if "cursorAction" in parameters
        else {"edits": []}
    )
    candidate = copy.deepcopy(override)
    candidate["edits"] = events(result, visual, clicks, override["edits"])
    recorded_override(candidate)
    if not candidate["edits"] and set(candidate) == {"edits"}:
        parameters.pop("cursorAction", None)
    else:
        parameters["cursorAction"] = candidate
    return result


def inventories(doc: dict[str, Any]) -> dict[str, Any]:
    def action(parameters: Any) -> Any:
        if not isinstance(parameters, dict):
            raise ValueError("capture native owner/effect parameters before click inventory")
        return copy.deepcopy(parameters.get("cursorAction"))

    return dict(
        paths=[
            {
                **{key: value for key, value in row.items() if key != "effect"},
                "cursorAction": action(row["effect"].get("parameters", {})),
            }
            for row in cursor_paths.inventory(doc)
        ],
        recordings=[
            dict(
                clipId=node.get("id"),
                type=node["_type"],
                path=path,
                cursorAction=action(node.get("parameters", {})),
            )
            for path, node in hotspots.clips(doc)
            if node.get("_type") in cursor_paths.RECORDING_OWNERS
        ],
    )


def main(argv: list[str] | None = None) -> int:
    parser = JsonHelpParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("project", type=Path)
    for name in ("set-path-clicks", "set-recorded-clicks"):
        edit = commands.add_parser(name)
        edit.add_argument("project", type=Path)
        edit.add_argument("--clip-id", type=int, required=True)
        edit.add_argument("--spec", type=Path, required=True)
        edit.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        doc, raw = project.load(args.project)
        report: dict[str, Any] = dict(
            schema_version=1,
            owner="camtasia-cursor-clicks",
            ok=True,
            projectSha256=project.digest(raw),
        )
        if args.command == "inspect":
            report.update(inventories(doc))
        else:
            command = set_path_clicks if args.command == "set-path-clicks" else set_recorded_clicks
            candidate = command(doc, args.clip_id, project.load(args.spec)[0])
            report.update(
                inventories(candidate),
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
