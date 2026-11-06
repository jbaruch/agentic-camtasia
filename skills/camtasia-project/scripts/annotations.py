#!/usr/bin/env python3
"""Stage native-template annotations and bounded shape/text edits as JSON.

inspect PROJECT lists Callouts, complete definitions and declared font names.
add PROJECT --track SCENE:TRACK --new-clip-id ID --template-project TEMPLATE
--template-clip-id ID --output CANDIDATE copies a complete standalone Callout
from its own root lane into an existing empty root lane. Both projects must be
single-scene Mac 2026.2.4 format 10 with equal edit rate and canvas dimensions.
All clocks, opaque fields, native style IDs, animation tracks and drawing edge
modifiers survive. One-sided Fade companions are copied with remapped media IDs.
No retiming, group extraction, source/resource copying or effect rebinding is
inferred. Capture a clean annotation without effects, hotspots, markers or quizzes first.
An identical existing result is a no-op; occupied lanes and reused IDs refuse.

set PROJECT --clip-id ID --spec SPEC --output CANDIDATE accepts schema_version 1
with text, rich (existing property names), and/or definition (existing supported
static fields). resize-behavior accepts the native resizeText (automatic text
sizing) or resizeCallout choice; enable-ligatures accepts native numeric 0/1.
Both require the existing field. REGION_PARAMETERS admits intensity on native
Blur/Pixelate/Spotlight annotation kinds, blur-invert on Blur and fill-invert plus
legacy fillColorRed/Green/Blue on Highlighter. New region values use native 0..1
units; inversion uses numeric 0/1. Existing spellings and scalar/static typed
representations survive. No color aliases, missing fields, animated/default-less
flattening or generic intensity controls on other kinds are inferred. UI edits
can save different floating precision; these inputs are raw saved units, not UI
percentages or a promise of sufficient obscuration. Layout controls preserve rich
values/ranges, default fonts, geometry and reset metadata. Automatic fitting can display a smaller size while
the saved rich fontSize remains unchanged. Shape/style replacement is not a constructor. Uniform static
rich runs use UTF-8 byte offsets; text replacement updates every range end.
KEYSTROKE_PARAMETERS admits existing MacKey keys, keyStyle, showKeyBackg and
showKeyHint. keys is a nonempty printable native key string, copied literally;
no chord parsing, modifier ordering, event synthesis or text-to-key conversion
is inferred. keyStyle uses native numeric 0..4 (Clear, Gray, Traditional, Outline,
Black); the two flags use numeric 0/1, not JSON booleans. Definition name and
clip ident remain unchanged. Native key/style edits can recompute width; use
same-build native geometry when staging a matching layout, then verify output.
The helper preserves omitted width; native reopening does not repair a stale
width, and output can omit the final key. No automatic fitting is promised.
In version 1, mixed, partial, duplicate, animated and unfamiliar runs refuse rather than
guessing a new styling map. Rich values retain native valueType and signed codes;
fgColor is a native '(R,G,B,A)' byte tuple string. Default fonts are preserved.
Spec schema_version 2 additionally accepts rich_ranges: nonempty objects with
start/end Unicode code-point offsets (end exclusive) and rich property changes.
Offsets index the resulting text, not UTF-8 bytes, UTF-16 units or graphemes.
The helper compiles them to native UTF-8 boundaries, splits only selected
property runs and merges adjacent equal payloads without losing opaque fields.
Static mixed inputs need complete, nonoverlapping coverage per present property;
overlapping requests for the same property refuse. Whole-text rich edits in v2
retain other properties' partitions. Changed text still requires uniform runs;
an identical text value preserves mixed styles. Animated/partial/unfamiliar
maps remain refused. Native font resolution and text fitting need output checks.
Spec schema_version 3 additionally accepts text_edits. Each edit has original
Unicode code-point start/end offsets, exact expected text, replacement text,
and style_from for nonempty replacements. style_from selects an original
character's complete per-property payload, not a byte offset or a caret guess.
Nonoverlapping edits run in original-coordinate order; insertions at a shared
boundary precede the replacement there. Repeated insertions at one point refuse.
Whole text and text_edits are mutually exclusive. rich/rich_ranges run afterward
against the resulting text. A fully deleted annotation retains its static frame
with native null value. Inserting into a saved empty null frame requires explicit
text_style, with EMPTY_STYLE_REQUIRED and optional kerning; no font defaults or
cached typing styles are inferred. Text edits require static native rich data.
Declared font names do not establish physical font availability or glyph coverage.
set-rich-steps PROJECT --clip-id ID --spec SPEC --output CANDIDATE replaces
rich states on a root remix text annotation. Schema 1 has optional initial
rich/rich_ranges edits and nonempty steps, each with at (positive rational local
seconds) and rich/rich_ranges. Changes accumulate from the initial complete
zero-time state. Times increase strictly, remain inside the visible duration
and map to exact source ticks through mediaStart/inverse speed. The initial
zero-time fallback remains; later frames are discrete points, not interpolated
font/color ramps. Native Auto Animate font-size edits remain static. Existing
point states are explicitly replaced; interval/unknown frames refuse. Existing
text, geometry/visual intervals, styles, fonts, resets and other payload survive.
clear-rich-steps PROJECT --clip-id ID --at SECONDS --output CANDIDATE keeps the
complete state effective at that visible local time as a static zero-time frame.
Both commands validate complete per-property UTF-8 partitions. General set still
refuses timed rich text; clear explicitly before changing its text. No text
content, RTF, nested-owner clock or font-file closure is inferred.
No proprietary presets, SVGs or fonts are distributed by this helper.

No original, media or editor is written. Exclusive/identical candidate staging
is followed by project validate/diff/apply and native save/reopen/export checks.
JSON stdout schema_version 1 owner camtasia-annotations reports hashes/inventory,
changed/written and nativeVerified false. Exit 0 success, 1 input/I/O refusal,
2 CLI syntax (JSON stderr); --help prints plaintext stdout.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import re
import sys
from typing import Any, NoReturn
import xml.etree.ElementTree as ET

import effects
import hotspots
import project
import transitions

KINDS = frozenset(
    {
        "remix",
        "TypeWinSVG",
        "TypeWinBlur",
        "TypeWinPixelate",
        "TypeWinHighlighter",
        "TypeWinSpotlight",
        "MacKey",
    }
)
RICH_TYPES = {
    "fontName": "string",
    "fontSize": "double",
    "fontWeight": "int",
    "fontItalic": "int",
    "underline": "int",
    "strikethrough": "int",
    "fgColor": "color",
    "kerning": "double",
}
EMPTY_STYLE_REQUIRED = frozenset(RICH_TYPES) - {"kerning"}
REGION_PARAMETERS = {
    "TypeWinBlur": frozenset({"intensity", "blur-invert"}),
    "TypeWinPixelate": frozenset({"intensity"}),
    "TypeWinSpotlight": frozenset({"intensity"}),
    "TypeWinHighlighter": frozenset(
        {"fill-invert", "fillColorRed", "fillColorGreen", "fillColorBlue"}
    ),
}
KEYSTROKE_PARAMETERS = frozenset({"keys", "keyStyle", "showKeyBackg", "showKeyHint"})
ENUMS = {
    "horizontal-alignment": {"left", "center", "right"},
    "vertical-alignment": {"top", "center", "bottom"},
    "stroke-style": {"solid", "dot", "dash"},
    "resize-behavior": {"resizeText", "resizeCallout"},
    "shape-anchor": {"none", "arrow", "circle", "diamond"},
    "shape-tail": {"none", "arrow", "circle", "diamond"},
}
NUMBERS = frozenset(
    {
        "width",
        "height",
        "corner-radius",
        "stroke-width",
        "text-stroke-width",
        "line-spacing",
        "tail-x",
        "tail-y",
        "numCtrlPts",
        "enable-ligatures",
        "ctrlPt0-x",
        "ctrlPt0-y",
        "ctrlPt1-x",
        "ctrlPt1-y",
    }
    | {
        prefix + channel
        for prefix in ("fill-color-", "stroke-color-", "text-stroke-color-")
        for channel in ("red", "green", "blue", "opacity", "alpha")
    }
)


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.exit(2, json.dumps(dict(ok=False, error=message), ensure_ascii=False) + "\n")


def require_native(doc: dict[str, Any]) -> None:
    if doc.get("version") != "10.0" or doc.get("authoringClientName") != hotspots.NATIVE_CLIENT:
        raise ValueError("use the verified Mac 2026.2.4 format-10 annotation contract")
    if project.number(doc.get("editRate")) <= 0:
        raise ValueError("repair the positive project edit rate")


def target(doc: dict[str, Any], clip_id: int) -> dict[str, Any]:
    require_native(doc)
    _, clip = hotspots.visual_target(doc, clip_id, visual_types=frozenset({"Callout"}))
    definition = clip.get("def")
    if (
        not isinstance(definition, dict)
        or not isinstance(definition.get("kind"), str)
        or definition["kind"] not in KINDS
    ):
        raise ValueError("select an observed native annotation definition kind")
    return clip


def static_runs(definition: dict[str, Any], *, empty_null: bool = False) -> list[dict[str, Any]]:
    attributes = definition.get("textAttributes")
    if attributes is None:
        return []
    if not isinstance(attributes, dict) or attributes.get("type") != "textAttributeList":
        raise ValueError("inspect the native textAttributeList representation")
    frames = attributes.get("keyframes")
    if not isinstance(frames, list) or len(frames) != 1 or not isinstance(frames[0], dict):
        raise ValueError(
            "preserve animated/multiple rich-text frames; use a uniform native template"
        )
    frame = frames[0]
    if any(type(frame.get(k)) is not int or frame[k] != 0 for k in ("time", "duration", "endTime")):
        raise ValueError("use a static zero-time rich-text frame")
    text = definition.get("text")
    if not isinstance(text, str):
        raise ValueError("inspect the native annotation text string")
    size = len(text.encode("utf-8"))
    runs = frame.get("value")
    if empty_null and text == "" and "value" in frame and runs is None:
        return []
    if not isinstance(runs, list) or not runs:
        raise ValueError("capture nonempty uniform native rich properties")
    boundaries = {0}
    offset = 0
    for character in text:
        offset += len(character.encode("utf-8"))
        boundaries.add(offset)
    properties: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        if not isinstance(run, dict):
            raise ValueError("inspect native rich property objects")
        name = run.get("name")
        if (
            not isinstance(name, str)
            or name not in RICH_TYPES
            or run.get("valueType") != RICH_TYPES[name]
            or type(run.get("rangeStart")) is not int
            or type(run.get("rangeEnd")) is not int
            or run["rangeStart"] not in boundaries
            or run["rangeEnd"] not in boundaries
            or not 0 <= run["rangeStart"] <= run["rangeEnd"] <= size
            or (size > 0 and run["rangeStart"] == run["rangeEnd"])
            or "value" not in run
        ):
            raise ValueError(
                "capture supported rich properties with complete native UTF-8 boundary ranges"
            )
        properties.setdefault(name, []).append(run)
    for values in properties.values():
        end = 0
        for run in sorted(values, key=lambda r: r["rangeStart"]):
            if run["rangeStart"] != end:
                raise ValueError("repair partial or overlapping native rich property coverage")
            end = run["rangeEnd"]
        if end != size or (size == 0 and len(values) != 1):
            raise ValueError(
                "repair partial or duplicate native rich property coverage; capture complete ranges"
            )
    return runs


def uniform_runs(definition: dict[str, Any]) -> list[dict[str, Any]]:
    runs = static_runs(definition)
    if any(
        run["rangeStart"] != 0 or run["rangeEnd"] != len(definition["text"].encode("utf-8"))
        for run in runs
    ):
        raise ValueError(
            "preserve mixed rich styles; capture a uniform template before replacing text"
        )
    return runs


def coalesce_rich_runs(runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Merge adjacent equal property payloads without discarding opaque fields."""
    merged: list[dict[str, Any]] = []
    for run in sorted(runs, key=lambda r: r["rangeStart"]):
        payload = {k: v for k, v in run.items() if k not in {"rangeStart", "rangeEnd"}}
        prior = (
            {k: v for k, v in merged[-1].items() if k not in {"rangeStart", "rangeEnd"}}
            if merged
            else None
        )
        if merged and merged[-1]["rangeEnd"] == run["rangeStart"] and payload == prior:
            merged[-1]["rangeEnd"] = run["rangeEnd"]
        else:
            merged.append(copy.deepcopy(run))
    return merged


def edit_text(definition: dict[str, Any], edits: Any, text_style: Any = None) -> None:
    old = definition["text"]
    runs: list[dict[str, Any]] = static_runs(definition, empty_null=True)
    attributes = definition.get("textAttributes")
    if not isinstance(attributes, dict) or (not runs and old):
        raise ValueError(
            "capture static native rich data or a saved empty null text frame before text_edits"
        )
    frame = attributes["keyframes"][0]
    if text_style is not None:
        if (
            runs
            or old
            or not isinstance(text_style, dict)
            or not EMPTY_STYLE_REQUIRED <= text_style.keys()
            or text_style.keys() - RICH_TYPES.keys()
        ):
            raise ValueError(
                "use text_style only for a saved empty null frame; supply its complete required native properties"
            )
        runs = [
            dict(
                name=name,
                valueType=RICH_TYPES[name],
                value=rich_value(name, value),
                rangeStart=0,
                rangeEnd=0,
            )
            for name, value in text_style.items()
        ]
    if not isinstance(edits, list) or not edits:
        raise ValueError(
            "supply a nonempty text_edits list with original start/end, expected and text"
        )
    ordered = []
    for edit in edits:
        if (
            not isinstance(edit, dict)
            or not {"start", "end", "expected", "text"} <= edit.keys()
            or edit.keys() - {"start", "end", "expected", "text", "style_from"}
            or type(edit["start"]) is not int
            or type(edit["end"]) is not int
            or not 0 <= edit["start"] <= edit["end"] <= len(old)
            or not isinstance(edit["expected"], str)
            or edit["expected"] != old[edit["start"] : edit["end"]]
            or not isinstance(edit["text"], str)
            or "\x00" in edit["text"]
        ):
            raise ValueError(
                "use original code-point bounds and matching expected text; replacement text must omit NUL"
            )
        if edit["text"] or "style_from" in edit:
            anchor = edit.get("style_from")
            if type(anchor) is not int or not (0 <= anchor < len(old) or anchor == 0 == len(old)):
                raise ValueError(
                    "select an original style_from character, or zero for explicitly styled empty text"
                )
        if edit["text"] and not runs:
            raise ValueError(
                "supply explicit text_style before inserting into a saved empty null frame"
            )
        ordered.append(edit)
    ordered.sort(key=lambda e: (e["start"], e["end"]))
    for before, after in zip(ordered, ordered[1:]):
        if (
            before["end"] > after["start"]
            or before["start"] == before["end"] == after["start"] == after["end"]
        ):
            raise ValueError(
                "use nonoverlapping text_edits and one insertion per original boundary"
            )
    offsets = [0]
    for char in old:
        offsets.append(offsets[-1] + len(char.encode("utf-8")))
    # Each piece maps an unchanged source slice or an explicitly anchored insertion.
    pieces: list[tuple[int, int, int, int | None, int]] = []
    chunks = []
    cursor = output = 0
    for edit in [*ordered, dict(start=len(old), end=len(old), text="")]:
        start, end, text = edit["start"], edit["end"], edit["text"]
        if cursor < start:
            chunks.append(old[cursor:start])
            pieces.append((offsets[cursor], offsets[start], output, None, 0))
            output += offsets[start] - offsets[cursor]
        if text:
            size = len(text.encode("utf-8"))
            chunks.append(text)
            pieces.append((0, size, output, edit["style_from"], size))
            output += size
        cursor = end
    new_text = "".join(chunks)
    if not new_text:
        definition["text"] = ""
        frame["value"] = None
        return
    by_name: dict[str, list[dict[str, Any]]] = {}
    for run in runs:
        by_name.setdefault(run["name"], []).append(run)
    result = []
    for candidates in by_name.values():
        fragments = []
        for a, b, destination, anchor, inserted_size in pieces:
            for run in candidates:
                if anchor is None:
                    left, right = max(a, run["rangeStart"]), min(b, run["rangeEnd"])
                    if left >= right:
                        continue
                    left, right = destination + left - a, destination + right - a
                else:
                    point = offsets[anchor]
                    if not (
                        run["rangeStart"] <= point < run["rangeEnd"]
                        or point == run["rangeStart"] == run["rangeEnd"] == 0
                        and not old
                    ):
                        continue
                    left, right = destination, destination + inserted_size
                fragment = copy.deepcopy(run)
                fragment.update(rangeStart=left, rangeEnd=right)
                fragments.append(fragment)
        result.extend(coalesce_rich_runs(fragments))

    def key(run: dict[str, Any]) -> tuple[str, int, int]:
        return run["name"], run["rangeStart"], run["rangeEnd"]

    frame["value"] = (
        runs if new_text == old and sorted(result, key=key) == sorted(runs, key=key) else result
    )
    definition["text"] = new_text


def patch_rich_range(
    runs: list[dict[str, Any]], name: str, start: int, end: int, value: Any
) -> None:
    if not any(run["name"] == name for run in runs):
        raise ValueError("capture the existing rich property before editing: " + name)
    value = rich_value(name, value)
    selected = []
    changed = False
    for run in runs:
        if run["name"] != name:
            continue
        left, right = run["rangeStart"], run["rangeEnd"]
        overlap = max(left, start) < min(right, end) or left == right == start == end
        if not overlap or run["value"] == value:
            selected.append(run)
            continue
        changed = True
        for a, b, v in (
            (left, min(right, start), run["value"]),
            (max(left, start), min(right, end), value),
            (max(left, end), right, run["value"]),
        ):
            if a < b or (left == right == start == end and v == value):
                piece = copy.deepcopy(run)
                piece.update(rangeStart=a, rangeEnd=b, value=v)
                selected.append(piece)
    if not changed:
        return
    merged = coalesce_rich_runs(selected)
    result = []
    inserted = False
    for run in runs:
        if run["name"] != name:
            result.append(run)
        elif not inserted:
            result.extend(merged)
            inserted = True
    runs[:] = result


def edit_rich_ranges(definition: dict[str, Any], runs: list[dict[str, Any]], changes: Any) -> None:
    if not isinstance(changes, list) or not changes:
        raise ValueError("supply a nonempty rich_ranges list with start, end and rich")
    text = definition["text"]
    requested: dict[str, list[tuple[int, int]]] = {}
    for change in changes:
        if (
            not isinstance(change, dict)
            or change.keys() != {"start", "end", "rich"}
            or type(change["start"]) is not int
            or type(change["end"]) is not int
            or not 0 <= change["start"] < change["end"] <= len(text)
            or not isinstance(change["rich"], dict)
            or not change["rich"]
            or change["rich"].keys() - RICH_TYPES.keys()
        ):
            raise ValueError(
                "use nonempty rich changes and code-point start/end within the resulting text"
            )
        start, end = change["start"], change["end"]
        for name, value in change["rich"].items():
            if any(start < b and a < end for a, b in requested.get(name, [])):
                raise ValueError("use non-overlapping rich_ranges requests for each property")
            requested.setdefault(name, []).append((start, end))
            patch_rich_range(
                runs,
                name,
                len(text[:start].encode("utf-8")),
                len(text[:end].encode("utf-8")),
                value,
            )


def rich_value(name: str, value: Any) -> Any:
    if name == "fontName":
        if not isinstance(value, str) or not value.strip() or any(ord(c) < 32 for c in value):
            raise ValueError(
                "supply a nonempty native font family name; verify installed font/glyph coverage"
            )
        return value
    if name == "fgColor":
        if (
            not isinstance(value, str)
            or not re.fullmatch(r"\(\d{1,3},\d{1,3},\d{1,3},\d{1,3}\)", value)
            or any(int(c) > 255 for c in value[1:-1].split(","))
        ):
            raise ValueError("use the native fgColor '(R,G,B,A)' string with bytes 0..255")
        return value
    if name in {"fontWeight", "fontItalic", "underline", "strikethrough"}:
        allowed = {
            "fontWeight": {400, 700},
            "fontItalic": {0, 2},
            "underline": {0, 1},
            "strikethrough": {0, -1},
        }
        if type(value) is not int or value not in allowed[name]:
            raise ValueError("use the observed signed native code for " + name)
        return value
    number = project.number(value)
    if name == "fontSize" and number <= 0:
        raise ValueError("use a positive fontSize and verify native text fitting")
    return effects.scalar_like(float, value)


def edit_annotation(doc: dict[str, Any], clip_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    if (
        not isinstance(spec, dict)
        or type(spec.get("schema_version")) is not int
        or spec["schema_version"] not in {1, 2, 3}
        or spec.keys()
        - (
            {"schema_version", "text", "rich", "definition"}
            | ({"rich_ranges"} if spec["schema_version"] >= 2 else set())
            | ({"text_edits", "text_style"} if spec["schema_version"] == 3 else set())
        )
        or len(spec) == 1
    ):
        raise ValueError("use spec schema_version 1, 2 or 3 with supported annotation edits")
    if "text_style" in spec and "text_edits" not in spec or "text_edits" in spec and "text" in spec:
        raise ValueError(
            "use text_style with text_edits only; choose whole text or text_edits, not both"
        )
    if "text_style" in spec and not isinstance(spec["text_style"], dict):
        raise ValueError("supply explicit native text_style properties as an object")
    result = copy.deepcopy(doc)
    definition = target(result, clip_id)["def"]
    if any(key in spec for key in ("text", "rich", "rich_ranges", "text_edits")):
        if definition.get("kind") != "remix" or not isinstance(definition.get("text"), str):
            raise ValueError(
                "select a remix text annotation; keystrokes and SVG text need separate contracts"
            )
        if "text_edits" in spec:
            edit_text(definition, spec["text_edits"], spec.get("text_style"))
    if any(key in spec for key in ("text", "rich", "rich_ranges")):
        version = spec["schema_version"]
        if "text" in spec and (not isinstance(spec["text"], str) or "\x00" in spec["text"]):
            raise ValueError("use a Unicode text string without NUL")
        replacing = "text" in spec and spec["text"] != definition["text"]
        runs = uniform_runs(definition) if version == 1 or replacing else static_runs(definition)
        if "text" in spec:
            text = spec["text"]
            definition["text"] = text
            if replacing:
                for run in runs:
                    run["rangeEnd"] = len(text.encode("utf-8"))
        prior_runs = copy.deepcopy(runs)
        if "rich" in spec:
            changes = spec["rich"]
            if not isinstance(changes, dict) or not changes or changes.keys() - RICH_TYPES.keys():
                raise ValueError("name existing supported native rich properties")
            by_name = {run["name"]: run for run in runs}
            for name, value in changes.items():
                if name not in by_name:
                    raise ValueError("capture the existing rich property before editing: " + name)
                if version == 1:
                    by_name[name]["value"] = rich_value(name, value)
                else:
                    patch_rich_range(runs, name, 0, len(definition["text"].encode("utf-8")), value)
        if "rich_ranges" in spec:
            edit_rich_ranges(definition, runs, spec["rich_ranges"])

        def key(run: dict[str, Any]) -> tuple[str, int, int]:
            return run["name"], run["rangeStart"], run["rangeEnd"]

        if sorted(prior_runs, key=key) == sorted(runs, key=key):
            runs[:] = prior_runs
    if "definition" in spec:
        changes = spec["definition"]
        if (
            not isinstance(changes, dict)
            or not changes
            or changes.keys()
            - (
                NUMBERS
                | ENUMS.keys()
                | REGION_PARAMETERS.get(definition["kind"], frozenset())
                | (KEYSTROKE_PARAMETERS if definition["kind"] == "MacKey" else frozenset())
            )
        ):
            raise ValueError("name supported existing static annotation definition fields")
        for name, value in changes.items():
            if name not in definition:
                raise ValueError("capture the native field before editing: " + name)
            if name == "keys":
                if (
                    not isinstance(definition[name], str)
                    or not isinstance(value, str)
                    or not value
                    or not value.isprintable()
                ):
                    raise ValueError("supply a nonempty printable native key string")
                definition[name] = value
                continue
            if name in ENUMS:
                if (
                    not isinstance(definition[name], str)
                    or not isinstance(value, str)
                    or value not in ENUMS[name]
                ):
                    raise ValueError("use an observed native choice for " + name)
                definition[name] = value
                continue
            number = project.number(value)
            if (
                (name in {"width", "height"} and number <= 0)
                or (name in {"corner-radius", "stroke-width", "text-stroke-width"} and number < 0)
                or ("color-" in name and not 0 <= number <= 1)
                or (name == "line-spacing" and not 0 <= number <= 3)
                or (name == "numCtrlPts" and number != 2)
                or (name == "enable-ligatures" and number not in {0, 1})
                or (name in REGION_PARAMETERS.get(definition["kind"], ()) and not 0 <= number <= 1)
                or (name in {"blur-invert", "fill-invert"} and number not in {0, 1})
                or (name == "keyStyle" and number not in {0, 1, 2, 3, 4})
                or (name in {"showKeyBackg", "showKeyHint"} and number not in {0, 1})
            ):
                raise ValueError("use the observed numeric range for " + name)
            effects.patch_parameter(definition, name, value)
    return result


def rich_step_frames(clip: dict[str, Any]) -> list[dict[str, Any]]:
    """Validate saved discrete rich states without flattening their partitions."""
    definition = clip["def"]
    if definition.get("kind") != "remix" or not isinstance(definition.get("text"), str):
        raise ValueError("select a remix text annotation for timed rich styles")
    attributes = definition.get("textAttributes")
    if not isinstance(attributes, dict) or attributes.get("type") != "textAttributeList":
        raise ValueError("capture native textAttributeList states before timed editing")
    frames = attributes.get("keyframes")
    if not isinstance(frames, list) or not frames:
        raise ValueError("capture a native zero-time initial rich state")
    previous = -1
    for frame in frames:
        if (
            not isinstance(frame, dict)
            or type(frame.get("time")) is not int
            or frame["time"] <= previous
            or frame.get("endTime") != frame["time"]
            or type(frame.get("endTime")) is not int
            or type(frame.get("duration")) is not int
            or frame["duration"] != 0
        ):
            raise ValueError(
                "use ordered discrete rich point frames; inspect interval/unknown frames"
            )
        view = copy.deepcopy(definition)
        point = copy.deepcopy(frame)
        point.update(time=0, endTime=0, duration=0)
        view["textAttributes"]["keyframes"] = [point]
        static_runs(view)
        previous = frame["time"]
    if frames[0]["time"] != 0:
        raise ValueError("retain the native zero-time initial rich state")
    return frames


def rich_source_time(doc: dict[str, Any], clip_id: int, at: Any) -> int:
    clip = target(doc, clip_id)
    path, _ = hotspots.visual_target(doc, clip_id, visual_types=frozenset({"Callout"}))
    if len(project.scene_tracks(doc)) != 1 or any(
        path.startswith(parent + "/") for parent, _ in hotspots.clips(doc) if parent != path
    ):
        raise ValueError("select a root annotation for the verified timed-rich source clock")
    rate, scalar = project.number(doc.get("editRate")), project.number(clip.get("scalar"))
    duration, start = project.number(clip.get("duration")), project.number(clip.get("mediaStart"))
    point = project.number(at)
    if rate <= 0 or scalar <= 0 or start < 0 or duration <= 0 or not 0 <= point * rate < duration:
        raise ValueError(
            "choose a visible clip-relative time with positive rate, speed and duration"
        )
    value = start + point * rate / scalar
    if value.denominator != 1:
        raise ValueError("choose a rich style time that maps to exact native project ticks")
    return int(value)


def set_rich_steps(doc: dict[str, Any], clip_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    """Replace discrete style states; each step patches the preceding complete state."""
    if (
        not isinstance(spec, dict)
        or type(spec.get("schema_version")) is not int
        or spec["schema_version"] != 1
        or spec.keys() - {"schema_version", "initial", "steps"}
        or not isinstance(spec.get("steps"), list)
        or not spec["steps"]
    ):
        raise ValueError(
            "supply rich-step schema_version 1 with nonempty steps and optional initial"
        )
    rich_source_time(doc, clip_id, 0)
    frames = rich_step_frames(target(doc, clip_id))
    state = copy.deepcopy(doc)
    target(state, clip_id)["def"]["textAttributes"]["keyframes"] = [copy.deepcopy(frames[0])]

    def apply(changes: Any) -> None:
        nonlocal state
        if not isinstance(changes, dict) or not changes or changes.keys() - {"rich", "rich_ranges"}:
            raise ValueError("supply rich and/or rich_ranges only for each timed style state")
        state = edit_annotation(state, clip_id, dict(schema_version=2, **changes))

    if "initial" in spec:
        apply(spec["initial"])
    compiled = [copy.deepcopy(target(state, clip_id)["def"]["textAttributes"]["keyframes"][0])]
    previous = project.number(0)
    for step in spec["steps"]:
        if not isinstance(step, dict) or "at" not in step:
            raise ValueError("supply at and rich and/or rich_ranges for each style step")
        point = project.number(step["at"])
        if point <= previous:
            raise ValueError("supply strictly increasing positive clip-relative style-step times")
        time = rich_source_time(doc, clip_id, step["at"])
        apply({k: v for k, v in step.items() if k != "at"})
        value = target(state, clip_id)["def"]["textAttributes"]["keyframes"][0]["value"]
        compiled.append(dict(time=time, endTime=time, duration=0, value=copy.deepcopy(value)))
        previous = point
    result = copy.deepcopy(doc)
    target(result, clip_id)["def"]["textAttributes"]["keyframes"] = compiled
    return result


def clear_rich_steps(doc: dict[str, Any], clip_id: int, at: Any) -> dict[str, Any]:
    """Keep the complete effective rich state at a visible local time as static text."""
    time = rich_source_time(doc, clip_id, at)
    frames = rich_step_frames(target(doc, clip_id))
    selected = next(frame for frame in reversed(frames) if frame["time"] <= time)
    result = copy.deepcopy(doc)
    initial = copy.deepcopy(frames[0])
    initial["value"] = copy.deepcopy(selected["value"])
    target(result, clip_id)["def"]["textAttributes"]["keyframes"] = [initial]
    return result


def add_annotation(
    doc: dict[str, Any], track: str, new_id: int, template: dict[str, Any], template_id: int
) -> dict[str, Any]:
    require_native(doc)
    source = target(template, template_id)
    if len(project.scene_tracks(doc)) != 1 or len(project.scene_tracks(template)) != 1:
        raise ValueError("capture a single-scene native annotation template and destination")
    if (
        project.number(doc["editRate"]) != project.number(template["editRate"])
        or any(project.number(d.get(k)) <= 0 for d in (doc, template) for k in ("width", "height"))
        or doc.get("width") != template.get("width")
        or doc.get("height") != template.get("height")
    ):
        raise ValueError("match native project edit rate and canvas dimensions before copying")
    lanes = [t for t in project.scene_tracks(template)[0] if t.get("medias") == [source]]
    if len(lanes) != 1:
        raise ValueError("isolate the annotation on its own root template lane")
    if lanes[0].get("parameters", {}) != {}:
        raise ValueError("capture an annotation template without lane-level parameters")
    if (
        source.get("effects") != []
        or any(
            "src" in node or node.get("_type") in ("Group", "UnifiedMedia")
            for _, node in project.objects(source)
        )
        or not isinstance(source.get("parameters"), dict)
        or any(k in source["parameters"] for k in ("toc", "quiz", "interactiveHotspot"))
        or not isinstance(source.get("attributes"), dict)
        or "hotspot" in source["attributes"]
    ):
        raise ValueError(
            "use a clean source-free annotation without effects, hotspots, markers or quizzes"
        )
    for field in ("start", "duration", "mediaStart", "mediaDuration", "scalar"):
        value = project.number(source.get(field))
        if value < 0 or (field in {"duration", "mediaDuration", "scalar"} and value <= 0):
            raise ValueError("retain complete positive native annotation clocks")
        if field in {"start", "duration"} and type(source.get(field)) is not int:
            raise ValueError("retain integer native start/duration ticks")
    if type(new_id) is not int or new_id <= 0:
        raise ValueError("supply a fresh positive integer clip ID")
    if source["def"].get("kind") == "TypeWinSVG":
        xml = source["def"].get("xmlContent")
        if not isinstance(xml, str):
            raise ValueError("capture the native drawing SVG string")
        try:
            svg = ET.fromstring(xml)
        except ET.ParseError as exc:
            raise ValueError("capture a well-formed native Sketch Motion SVG") from exc
        if any(
            e.tag.split("}")[-1] in {"text", "image", "script", "style", "foreignObject"}
            or any(k.split("}")[-1] == "href" or "url(" in v.lower() for k, v in e.attrib.items())
            for e in svg.iter()
        ):
            raise ValueError(
                "capture a self-contained native drawing SVG without external/text dependencies"
            )
    clip = copy.deepcopy(source)
    clip["id"] = new_id
    companions = copy.deepcopy(lanes[0].get("transitions", []))
    if not isinstance(companions, list):
        raise ValueError("inspect native track transition companions")
    for original in transitions.transition_list(lanes[0]):
        transitions.check_fit(lanes[0], original, original)
    for transition in companions:
        if (
            not isinstance(transition, dict)
            or transition.get("name") != "Fade"
            or sum(k in transition for k in ("leftMedia", "rightMedia")) != 1
        ):
            raise ValueError("capture standalone one-sided Fade companions")
        key = "leftMedia" if "leftMedia" in transition else "rightMedia"
        if type(transition[key]) is not int or transition[key] != template_id:
            raise ValueError("repair annotation Fade references before copying")
        transition[key] = new_id
    result = copy.deepcopy(doc)
    destination = project.selected_track(result, track)
    if destination.get("medias") == [clip] and destination.get("transitions", []) == companions:
        if sum(n.get("id") == new_id for _, n in project.objects(doc)) != 1:
            raise ValueError("repair duplicate clip IDs before repeating construction")
        return result
    if destination.get("medias") != [] or destination.get("transitions", []):
        raise ValueError("select an existing empty root destination lane")
    if any(n.get("id") == new_id for _, n in project.objects(doc)):
        raise ValueError("clip ID is already used; inspect and choose a fresh ID")
    destination["medias"] = [clip]
    if companions:
        destination["transitions"] = companions
    return result


def inventory(doc: dict[str, Any]) -> list[dict[str, Any]]:
    return [
        dict(
            clipId=n.get("id"),
            path=p,
            definition=n.get("def"),
            declaredFonts=sorted(
                {
                    str(v["name"])
                    for _, v in project.objects(n.get("def", {}))
                    if "name" in v and "size" in v
                }
                | {
                    v["value"]
                    for _, v in project.objects(n.get("def", {}))
                    if v.get("name") == "fontName" and isinstance(v.get("value"), str)
                }
            ),
            fontFilesVerified=False,
        )
        for p, n in hotspots.clips(doc)
        if n.get("_type") == "Callout"
    ]


def main(argv: list[str] | None = None) -> int:
    parser = JsonArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("inspect", "add", "set", "set-rich-steps", "clear-rich-steps"):
        command = commands.add_parser(name)
        command.add_argument("project", type=Path)
        if name != "inspect":
            command.add_argument("--output", type=Path, required=True)
        if name in {"set", "set-rich-steps", "clear-rich-steps"}:
            command.add_argument("--clip-id", type=int, required=True)
            if name == "clear-rich-steps":
                command.add_argument("--at", required=True)
            else:
                command.add_argument("--spec", type=Path, required=True)
        if name == "add":
            command.add_argument("--track", required=True)
            command.add_argument("--new-clip-id", type=int, required=True)
            command.add_argument("--template-project", type=Path, required=True)
            command.add_argument("--template-clip-id", type=int, required=True)
    args = parser.parse_args(argv)
    try:
        doc, raw = project.load(args.project)
        report: dict[str, Any] = dict(
            schema_version=1,
            owner="camtasia-annotations",
            ok=True,
            projectSha256=project.digest(raw),
        )
        if args.command == "inspect":
            report["annotations"] = inventory(doc)
        else:
            if args.command == "set":
                candidate = edit_annotation(doc, args.clip_id, project.load(args.spec)[0])
            elif args.command == "set-rich-steps":
                candidate = set_rich_steps(doc, args.clip_id, project.load(args.spec)[0])
            elif args.command == "clear-rich-steps":
                candidate = clear_rich_steps(doc, args.clip_id, args.at)
            else:
                candidate = add_annotation(
                    doc,
                    args.track,
                    args.new_clip_id,
                    project.load(args.template_project)[0],
                    args.template_clip_id,
                )
            report.update(
                annotations=inventory(candidate),
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
