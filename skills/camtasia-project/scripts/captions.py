#!/usr/bin/env python3
"""Inspect and stage closed/source-backed dynamic captions without editing inputs.

inspect PROJECT inventories audio-owned captions, imported Caption/captionData,
recognized source transcription, logical audio uses and separate dynamic-caption
displays. audioUses supplies logical/physical IDs, source selection, clocks and
nearest-first containers even when a recognized clip has no closed parameter. map
PROJECT --clip-id ID maps closed-cue holds and eligible recognized word holds
through a source clip's trim, inverse speed, placement and Group ancestors.
Linked AV clocks are mirrors, never summed. A source trim omits earlier dynamic
word onsets; ancestor cropping carries a word already active in the Group.
The verified caption/word clock is 705600000 ticks/sec, independently of each
source stream's sample/edit rate. Group mapping requires Mac 2026.2.4 and returns
ancestors nearest first. map --closed-only omits source recognition and requires
existing closed cues. Stitched and multiscene mappings refuse.

set-text PROJECT --clip-id ID --spec SPEC corrects existing plain closed points.
set-rtf-text uses edits [{index, expected, replacements:[{start,end,text}]}] for
native text-only Cocoa RTF cues. expected is the complete decoded cue; half-open
substring ranges count original Unicode code points. Replacements inherit the
first removed character's style, insertions the following character's style,
and end insertions the last character's style. Unchanged text and all existing
format controls/groups are preserved byte for byte. Removed encoded spans leave
empty groups as lexical separators. Empty RTF insertion requires
the native editor to establish a style. Complex/unsupported RTF refuses. Inspect
RTF with rtf-text PROJECT --clip-id ID before choosing ranges. No timing changes.
correct-words PROJECT --source-id ID --source-track INDEX --spec SPEC corrects
actual saved Mac 2026.2.4 transcription. Both specs have schema_version 1 and
edits [{index, expected, text}]. Only value/text changes; point times, unknown
fields and display modifiers survive. Shared-source corrections affect every use.
Native %GAP markers cannot be replaced or invented. Recognition must run in the
editor or an explicitly chosen external workflow; this helper never generates it.

set-cues PROJECT --clip-id ID --spec SPEC replaces unstyled closed cue points.
Spec schema_version 1 has clock media|timeline and cues [{start,end,text}], in
rational seconds. Nonoverlapping cues compile to native hold/clear points,
including a final clear. Existing opaque per-point data or RTF/styled values
refuse replacement; use set-text for preserving point fields. Parameter, clip,
source and global style payload survive; the existing caption enabled flag turns on.
Group-contained cues support media or global timeline seconds. Timeline cues must
fit entirely inside the child's visible interval through every ancestor Group.

retime PROJECT --clip-id ID --spec SPEC changes a clean Caption/audio/linked
AV clock. Supply schema_version 1, start, duration, media_start (rational seconds)
and positive scalar (inverse speed). Complete mirrored clocks change together;
source words/cues and dynamic displays do not change. Consumed source bounds,
lane collisions and transitions are checked. Effects/animations need their own
retiming contract. Bound the independent display with set-display separately.
Linked-video cut inputs and edited display bounds must align with the document's
video frame grid. Recognized onsets and intentional subframe audio stay unchanged.
Group descendants require clock parent: placement is in the containing Group's
clock and all ancestor clocks and durations survive unchanged. Closed-only Group
operations accept signed child and nested-Group starts; root placement remains
nonnegative. They refuse known native Group save/reopen drift configurations.

set-display PROJECT --clip-id ID --spec SPEC edits an existing native dynamic
display. Spec schema_version 1 accepts start/duration seconds, definition (existing
supported numeric controls), and rich (existing fontName/fontSize/fgColor).
The native placeholder, partial rich ranges, style IDs and all other controls
remain unchanged. Bound edits require an untrimmed scalar-one clean display.
Group descendants require clock parent, accept signed local placement and retain
every ancestor. Edited bounds use the parent clock's document frame grid; source
onsets stay subframe. Display bounds are separate from source-word clock mapping.
The exercised display and audio share a Group; a root display over grouped audio
did not render words in the native assembled control. Check actual binding/output.
No vendor definitions, fonts, media or recognition models are copied.

set-style PROJECT --spec SPEC --output CANDIDATE edits existing global closed-
caption appearance, not the separate dynamic-caption display. Schema version 1
has a nonempty style object. CLOSED_STYLE_FIELDS and CLOSED_FONTS own the
supported fields and native font choices. Font size is a positive integer;
foreground/background colors are four integer RGBA bytes. Background opacity
is the backgroundColor alpha byte, not the legacy opacity scalar.
Foreground alpha changes glyph fill; the native black glyph outline remains
visible even at zero. Background alpha zero removes the panel.
No aliases, percent conversion, missing-field insertion or global default reconstruction
is inferred. Every omitted style field, other global attribute, cue/RTF payload,
source word, clip clock, display and unrelated value survives. The style applies
globally to closed captions across the project, including later cue edits.
Only the observed Mac 2026.2.4 format-10 style contract is supported. Native font
availability, text fitting and transparency still require rendered checks.

Edits require the observed Mac 2025.0.3/format 9 or 2026.2.4/format 10 and exact
caption clock; source-backed dynamic and RTF edits require the latter. JSON stdout schema_version
1 owner camtasia-captions reports hashes, inventory, changed/written and
nativeVerified false. Staging is exclusive or an identical no-op. Follow project
validate/diff/apply, matching native save/reopen and actual caption/highlight or
Smart Player CC checks. Exit 0 success, 1 input/I/O refusal, 2 CLI syntax (JSON
stderr). --help emits the versioned JSON owner envelope with a help string.
Python 3.11+, standard library only.
"""

from __future__ import annotations

import copy
from fractions import Fraction
import json
from pathlib import Path
import re
import sys
from typing import Any

import annotations
import effects
import hotspots
import project
import transitions

RATE = 705600000
CLOSED_STYLE_FIELDS = frozenset({"fontName", "fontSize", "foregroundColor", "backgroundColor"})
CLOSED_FONTS = frozenset({"Arial", "Trebuchet MS", "Verdana"})
DISPLAY_NUMBERS = frozenset(
    {
        "dynamic-caption-new-paragraph-for-each-sentence",
        "dynamic-caption-current-word-enabled",
        "dynamic-caption-current-word-extra-scale",
        "dynamic-caption-current-word-stroke-extra-width",
        "dynamic-caption-future-word-opacity",
        "dynamic-caption-past-word-opacity",
        "dynamic-caption-word-easing-duration",
        "dynamic-caption-block-transition-duration",
    }
    | {"dynamic-caption-current-word-color-" + ch for ch in ("red", "green", "blue", "alpha")}
)


class JsonHelpParser(annotations.JsonArgumentParser):
    def format_help(self) -> str:
        return (
            json.dumps(
                dict(
                    schema_version=1, owner="camtasia-captions", ok=True, help=super().format_help()
                ),
                ensure_ascii=False,
            )
            + "\n"
        )


def require_native(doc: dict[str, Any], *, dynamic: bool = False) -> None:
    effects.require_native(doc)
    if project.number(doc.get("editRate")) != RATE:
        raise ValueError(
            "capture the caption clock for this edit rate; verified clock is 705600000"
        )
    if dynamic and doc.get("authoringClientName") != hotspots.NATIVE_CLIENT:
        raise ValueError("use the verified Mac 2026.2.4 source-backed dynamic caption contract")


def spec_keys(spec: dict[str, Any], allowed: set[str], required: set[str]) -> None:
    if (
        type(spec.get("schema_version")) is not int
        or spec["schema_version"] != 1
        or spec.keys() - (allowed | {"schema_version"})
        or not required <= spec.keys()
    ):
        raise ValueError("use spec schema_version 1 and the documented required fields")


def exact(value: Fraction) -> int | str:
    return value.numerator if value.denominator == 1 else str(value)


def point_frames(parameter: Any, kind: str) -> list[dict[str, Any]]:
    if (
        not isinstance(parameter, dict)
        or parameter.get("type") != kind
        or not isinstance(parameter.get("keyframes"), list)
    ):
        raise ValueError("inspect the native " + kind + " point parameter and keyframes")
    frames, prior = parameter["keyframes"], -1
    for frame in frames:
        if (
            not isinstance(frame, dict)
            or type(frame.get("time")) is not int
            or frame["time"] < 0
            or frame["time"] <= prior
            or type(frame.get("endTime")) is not int
            or frame["endTime"] != frame["time"]
            or type(frame.get("duration")) is not int
            or frame["duration"] != 0
        ):
            raise ValueError(
                "retain strictly ordered native zero-duration points with equal time/endTime"
            )
        prior = frame["time"]
        if kind == "caption":
            value = frame.get("value")
            if not isinstance(value, dict) or not isinstance(value.get("text"), str):
                raise ValueError("inspect native caption value.text objects")
        elif not isinstance(frame.get("value"), str):
            raise ValueError("inspect native recognized word strings")
    return frames


def plain(value: dict[str, Any]) -> None:
    if value.get("textAttributes", "missing") is not None or value["text"].lstrip(
        "\ufeff \t\r\n"
    ).startswith("{\\rtf"):
        raise ValueError("use the native caption editor or an RTF/style-aware route for this value")


def selected(doc: dict[str, Any], clip_id: int) -> tuple[str, dict[str, Any]]:
    if type(clip_id) is not int:
        raise ValueError("select a numeric clip ID from inspection")
    matches = [(p, n) for p, n in hotspots.clips(doc) if n.get("id") == clip_id]
    if len(matches) != 1:
        raise ValueError("select a unique saved clip ID before caption editing")
    return matches[0]


def closed_target(doc: dict[str, Any], clip_id: int) -> tuple[dict[str, Any], str, dict[str, Any]]:
    _, owner = selected(doc, clip_id)
    if owner.get("_type") == "UnifiedMedia":
        owner = owner.get("audio")
    if not isinstance(owner, dict) or owner.get("_type") not in ("AMFile", "Caption"):
        raise ValueError("select an audio-owned closed caption or imported Caption clip")
    key = "captionData" if owner["_type"] == "Caption" else "captions"
    parameters = owner.get("parameters")
    if not isinstance(parameters, dict) or key not in parameters:
        raise ValueError("add/import native closed captions first, then select their saved owner")
    point_frames(parameters[key], "caption")
    return owner, key, parameters[key]


def root_tracks(doc: dict[str, Any]) -> list[dict[str, Any]]:
    scenes = project.scene_tracks(doc)
    if len(scenes) != 1:
        raise ValueError("capture multiscene caption mapping separately; use a single scene")
    for track in scenes[0]:
        medias = track.get("medias", [])
        if not isinstance(medias, list) or any(not isinstance(n, dict) for n in medias):
            raise ValueError(
                "repair native root lane medias arrays and clip objects before caption timing edits"
            )
    return scenes[0]


def require_frame_grid(doc: dict[str, Any], cuts: dict[str, Any]) -> None:
    try:
        fps, rate = (project.number(doc.get(k)) for k in ("videoFormatFrameRate", "editRate"))
    except ValueError as exc:
        raise ValueError(
            "read/repair native videoFormatFrameRate and editRate before video timing edits"
        ) from exc
    if fps <= 0 or rate <= 0:
        raise ValueError("use positive native videoFormatFrameRate and editRate for video cuts")
    for name, ticks in cuts.items():
        if (project.number(ticks) * fps / rate).denominator != 1:
            raise ValueError("supply target frame-grid-aligned video timing for " + name)


def root_clock(
    doc: dict[str, Any], clip_id: int
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any]]:
    selected(doc, clip_id)
    matches = []
    for track in root_tracks(doc):
        for owner in track.get("medias", []):
            if not isinstance(owner, dict):
                raise ValueError("repair native root clip objects")
            audio = owner.get("audio") if owner.get("_type") == "UnifiedMedia" else owner
            if owner.get("id") == clip_id or isinstance(audio, dict) and audio.get("id") == clip_id:
                matches.append((track, owner, audio))
    if len(matches) != 1:
        raise ValueError(
            "select a root Caption/audio/linked AV owner; nested/stitched clocks need native evidence"
        )
    track, owner, audio = matches[0]
    validate_caption_clock(doc, owner, audio)
    return track, owner, audio


def validate_caption_clock(
    doc: dict[str, Any], owner: dict[str, Any], audio: Any, *, nested: bool = False
) -> None:
    if type(owner.get("id")) is not int:
        raise ValueError("repair the owner's numeric clip ID before caption mapping or retiming")
    selected(doc, owner["id"])
    if not isinstance(audio, dict) or audio.get("_type") not in ("AMFile", "Caption"):
        raise ValueError("select a Caption or speech-bearing audio/linked AV clip")
    attributes = audio.get("attributes", {})
    if (
        not isinstance(attributes, dict)
        or project.number(attributes.get("sourceFileOffset", 0)) != 0
    ):
        raise ValueError(
            "capture caption mapping for nonzero/unknown audio sourceFileOffset separately"
        )
    clocks = [owner]
    if owner.get("_type") == "UnifiedMedia":
        video = owner.get("video")
        if not isinstance(video, dict) or video.get("_type") != "VMFile":
            raise ValueError(
                "capture ordinary linked AV caption clocks without recording/freeze variants"
            )
        clocks += [video, audio]
    for node in clocks:
        values = {key: project.number(node.get(key)) for key in effects.CLOCK_FIELDS}
        if (
            (values["start"] < 0 and not nested)
            or values["mediaStart"] < 0
            or any(values[key] <= 0 for key in ("duration", "mediaDuration", "scalar"))
        ):
            raise ValueError("retain complete positive native caption owner clocks")
        if any(project.number(owner[key]) != values[key] for key in effects.CLOCK_FIELDS):
            raise ValueError("repair conflicting complete linked AV caption clocks")


def caption_context(doc: dict[str, Any], path: str) -> tuple[dict[str, Any], list[dict[str, Any]]]:
    """Resolve the selected caption clip's lane and nearest-first Group clocks."""
    root_tracks(doc)
    nodes = hotspots.clips(doc)
    if path not in {p for p, _ in nodes}:
        raise ValueError("select a saved caption media clip from project inspection")
    ancestors = sorted(
        [(p, n) for p, n in nodes if path.startswith(p + "/")],
        key=lambda item: len(item[0]),
        reverse=True,
    )
    if ancestors and doc.get("authoringClientName") != hotspots.NATIVE_CLIENT:
        raise ValueError("use the verified Mac 2026.2.4 Group closed-caption clock contract")
    if any(n.get("_type") != "Group" for _, n in ancestors):
        raise ValueError("select Group-only caption ancestry; capture other container clocks first")
    for _, group in ancestors:
        if type(group.get("id")) is not int:
            raise ValueError("repair numeric Group IDs before caption clock editing")
        selected(doc, group["id"])
        values = {k: project.number(group.get(k)) for k in effects.CLOCK_FIELDS}
        if (
            (values["start"] < 0 and group is ancestors[-1][1])
            or values["mediaStart"] < 0
            or any(values[k] <= 0 for k in ("duration", "mediaDuration", "scalar"))
        ):
            raise ValueError("retain complete positive native ancestor Group clocks")
    for problem in project.native_group_reopen_hazards(doc):
        if any(problem.startswith(p + ":") for p, _ in ancestors):
            raise ValueError(problem)
    lane_path = path.rsplit("/medias/", 1)[0]
    tracks = [n for p, n in project.objects(doc) if p == lane_path]
    if (
        len(tracks) != 1
        or not isinstance(tracks[0].get("medias"), list)
        or any(not isinstance(n, dict) for n in tracks[0]["medias"])
    ):
        raise ValueError("repair the selected Group child's native lane before editing clocks")
    return tracks[0], [n for _, n in ancestors]


def closed_clock(
    doc: dict[str, Any], clip_id: int
) -> tuple[dict[str, Any], dict[str, Any], dict[str, Any], list[dict[str, Any]]]:
    """Select one logical caption source clock, with nearest Group first."""
    path, owner = selected(doc, clip_id)
    linked = [
        (p, n)
        for p, n in hotspots.clips(doc)
        if n.get("_type") == "UnifiedMedia" and path == p + "/audio"
    ]
    if linked:
        if len(linked) != 1:
            raise ValueError("repair ambiguous linked caption ownership")
        path, owner = linked[0]
    track, ancestors = caption_context(doc, path)
    if not ancestors:
        track, owner, audio = root_clock(doc, clip_id)
        return track, owner, audio, []
    audio = owner.get("audio") if owner.get("_type") == "UnifiedMedia" else owner
    if owner.get("_type") not in ("AMFile", "Caption", "UnifiedMedia") or not isinstance(
        audio, dict
    ):
        raise ValueError("select a Group-contained Caption/audio/ordinary linked AV owner")
    validate_caption_clock(doc, owner, audio, nested=True)
    return track, owner, audio, ancestors


def closed_interval(
    begin: Fraction, end: Fraction, owner: dict[str, Any], ancestors: list[dict[str, Any]]
) -> tuple[Fraction, Fraction] | None:
    """Crop each interval in its immediate source clock, then apply placement."""
    for node in [owner, *ancestors]:
        start, duration, inpoint, scalar = (
            project.number(node[k]) for k in ("start", "duration", "mediaStart", "scalar")
        )
        begin, end = max(begin, inpoint), min(end, inpoint + duration / scalar)
        if begin >= end:
            return None
        begin, end = (start + (value - inpoint) * scalar for value in (begin, end))
    return begin, end


def closed_source_tick(
    point: Fraction, owner: dict[str, Any], ancestors: list[dict[str, Any]]
) -> Fraction:
    for node in reversed([owner, *ancestors]):
        point = project.number(node["mediaStart"]) + (
            point - project.number(node["start"])
        ) / project.number(node["scalar"])
    return point


def source_stream(
    doc: dict[str, Any], owner: dict[str, Any], kind: int
) -> tuple[dict[str, Any], dict[str, Any]]:
    sources = doc.get("sourceBin", [])
    if not isinstance(sources, list) or type(owner.get("src")) is not int:
        raise ValueError("inspect the selected source reference before caption clock mapping")
    matches = [s for s in sources if isinstance(s, dict) and s.get("id") == owner["src"]]
    if len(matches) != 1:
        raise ValueError("repair missing/ambiguous selected source IDs")
    source, index = matches[0], owner.get("trackNumber")
    tracks = source.get("sourceTracks")
    if (
        type(index) is not int
        or not isinstance(tracks, list)
        or not 0 <= index < len(tracks)
        or not isinstance(tracks[index], dict)
        or tracks[index].get("type") != kind
    ):
        raise ValueError("select the matching source stream kind by its saved native trackNumber")
    return source, tracks[index]


def audio_stream(
    doc: dict[str, Any], owner: dict[str, Any]
) -> tuple[dict[str, Any], dict[str, Any]]:
    return source_stream(doc, owner, 2)


def capacity(doc: dict[str, Any], owner: dict[str, Any]) -> Fraction:
    if owner.get("_type") == "Caption":
        bound = project.number(owner.get("maxMediaDuration"))
    else:
        if owner.get("_type") not in ("AMFile", "VMFile"):
            raise ValueError("select a Caption or ordinary audio/video source owner for bounds")
        _, stream = source_stream(doc, owner, 0 if owner["_type"] == "VMFile" else 2)
        span, rate = stream.get("range"), project.number(stream.get("editRate"))
        if (
            not isinstance(span, list)
            or len(span) != 2
            or project.number(span[0]) != 0
            or rate <= 0
        ):
            raise ValueError("capture the caption mapping for nonzero/unknown source ranges")
        bound = project.number(span[1]) * RATE / rate
    if bound <= 0:
        raise ValueError("retain a positive source/caption media bound")
    return bound


def transcription(doc: dict[str, Any], source_id: int, index: int) -> dict[str, Any]:
    if type(source_id) is not int or type(index) is not int:
        raise ValueError("select numeric source ID and zero-based source-track index")
    _, stream = audio_stream(doc, dict(src=source_id, trackNumber=index))
    parameters = stream.get("parameters")
    if (
        stream.get("transcriptionSet") is not True
        or not isinstance(parameters, dict)
        or "transcription" not in parameters
    ):
        raise ValueError("generate actual recognition/transcription and save it in Camtasia first")
    value = parameters["transcription"]
    if not point_frames(value, "string"):
        raise ValueError("generate and save nonempty native recognition points before corrections")
    return value


def correction_edits(spec: dict[str, Any], frames: list[dict[str, Any]], *, words: bool) -> None:
    spec_keys(spec, {"edits"}, {"edits"})
    edits, seen = spec["edits"], set()
    if not isinstance(edits, list) or not edits:
        raise ValueError("supply nonempty occurrence-specific edits with index, expected and text")
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != {"index", "expected", "text"}:
            raise ValueError("supply each edit as index, expected and text")
        index, expected, text = edit["index"], edit["expected"], edit["text"]
        if (
            type(index) is not int
            or not 0 <= index < len(frames)
            or index in seen
            or not isinstance(expected, str)
            or not isinstance(text, str)
            or "\x00" in text
        ):
            raise ValueError(
                "select distinct existing point indices and Unicode strings without NUL"
            )
        seen.add(index)
        frame = frames[index]
        if words:
            current = frame["value"]
            if (
                current.startswith("%GAP")
                or text.startswith("%GAP")
                or not text
                or any(c.isspace() for c in text)
            ):
                raise ValueError(
                    "preserve pause markers and correct one recognized word without inventing onsets"
                )
        else:
            plain(frame["value"])
            plain(dict(text=text, textAttributes=None))
            current = frame["value"]["text"]
        if current not in (expected, text):
            raise ValueError(
                "point text differs from expected; inspect the selected occurrence again"
            )
        if words:
            frame["value"] = text
        else:
            frame["value"]["text"] = text


def correct_text(doc: dict[str, Any], clip_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    require_native(doc)
    result = copy.deepcopy(doc)
    correction_edits(spec, point_frames(closed_target(result, clip_id)[2], "caption"), words=False)
    return result


# The text-only Cocoa form captured from the native caption editor. Unknown
# controls refuse: a general RTF reader can have additional text destinations.
RTF_FORMAT = frozenset(
    "rtf ansi ansicpg cocoartf cocoatextscaling cocoaplatform pard tx pardirnatural "
    "partightenfactor f fs cf b i ul ulnone strike plain ql qc qr qj li ri fi "
    "sa sb sl slmult kerning expnd expndtw charrsid lang langfe langnp "
    "ltrch rtlch ltrpar rtlpar af adeflang deff deflang viewkind vieww viewh "
    "paperw paperh margl margr margt margb widowctrl hyphauto fet adeflangfe "
    "CocoaLigature fsmilli expansion obliqueness outl strokewidth strokec "
    "ulc ulstyle strikec strikestyle nosupersub super sub highlight cb cbpat "
    "pardeftab qnatural slleading slmaximum slminimum".split()
)
RTF_CHARACTERS = {
    "par": "\n",
    "line": "\n",
    "tab": "\t",
    "emdash": "—",
    "endash": "–",
    "bullet": "•",
    "lquote": "‘",
    "rquote": "’",
    "ldblquote": "“",
    "rdblquote": "”",
}
RTF_CONTROL = re.compile(r"\\(?:([A-Za-z]+)(-?\d+)? ?|'([0-9a-fA-F]{2})|([^A-Za-z]))", re.DOTALL)


def rtf_characters(text: str) -> list[tuple[str, list[tuple[int, int]]]]:
    """Map native text-only RTF Unicode scalars to their exact encoded spans."""
    if not text.startswith(r"{\rtf1\ansi\ansicpg1252") or not text.endswith("}"):
        raise ValueError("capture the native text-only ANSI/1252 Cocoa RTF caption first")
    # Each group scopes destination and Unicode fallback count. Header groups
    # are copied, not interpreted as cue text. Binary/attachment/field forms and
    # other destinations are intentionally outside this editing contract.
    stack: list[tuple[bool, int]] = []
    skip, uc, fallback, pos = False, 1, 0, 0
    units: list[tuple[str, list[tuple[int, int]]]] = []
    while pos < len(text):
        start, char = pos, text[pos]
        if char in "{}":
            fallback = 0
            if char == "{":
                stack.append((skip, uc))
            elif not stack:
                raise ValueError("repair unmatched RTF braces in the native caption editor")
            else:
                skip, uc = stack.pop()
                if not stack and pos != len(text) - 1:
                    raise ValueError("retain exactly one complete native RTF root group")
            pos += 1
            continue
        if not stack:
            raise ValueError("retain all caption RTF data inside its root group")
        if char in "\r\n":
            pos += 1
            continue
        word, number, visible = None, None, None
        if char == "\\":
            match = RTF_CONTROL.match(text, pos)
            if match is None:
                raise ValueError("repair malformed RTF escapes in the native caption editor")
            word, numeric, hexadecimal, symbol = match.groups()
            number = int(numeric) if numeric is not None else None
            pos = match.end()
            if hexadecimal is not None:
                try:
                    visible = bytes([int(hexadecimal, 16)]).decode("cp1252")
                except UnicodeDecodeError as exc:
                    raise ValueError(
                        "replace undefined RTF codepage bytes in the native editor"
                    ) from exc
            elif symbol is not None:
                symbols = {
                    "\\": "\\",
                    "{": "{",
                    "}": "}",
                    "~": "\u00a0",
                    "_": "‑",
                    "-": "\u00ad",
                    "\n": "\n",
                    "\r": "\n",
                }
                if symbol == "*" and text[start + 2 :].startswith("\\expandedcolortbl"):
                    skip = True
                elif symbol in symbols:
                    visible = symbols[symbol]
                else:
                    raise ValueError("use the native editor for unsupported RTF control symbols")
        else:
            if not " " <= char <= "~":
                raise ValueError(
                    "retain native escaped ANSI/Unicode RTF text; re-save in the editor"
                )
            visible, pos = char, pos + 1
        if word in {"bin", "pict", "object", "field", "NeXTGraphic", "upr", "ud"}:
            raise ValueError("use the native editor for embedded/binary/alternate-destination RTF")
        if fallback:
            units[-1][1].append((start, pos))
            fallback -= 1
            continue
        if word in {"fonttbl", "colortbl"}:
            if len(stack) != 2:
                raise ValueError("retain native RTF header destinations at root depth")
            skip = True
        if skip:
            if word == "fcharset" and number != 0:
                raise ValueError("use the native editor for font-specific RTF character sets")
            if word == "cpg" and number != 1252:
                raise ValueError("use the native editor for font-specific RTF codepages")
            continue
        if word == "uc":
            if number is None or not 0 <= number <= 16:
                raise ValueError("retain a bounded native RTF Unicode fallback count")
            uc = number
        elif word == "u":
            if number is None or not -32768 <= number <= 65535:
                raise ValueError("retain native signed/unsigned UTF-16 RTF Unicode controls")
            visible, fallback = chr(number % 65536), uc
        elif word in RTF_CHARACTERS:
            visible = RTF_CHARACTERS[word]
        elif word == "ansicpg" and number != 1252:
            raise ValueError("use the native editor for other RTF codepages")
        elif word is not None and word not in RTF_FORMAT:
            raise ValueError("use the native editor for unsupported RTF control: " + word)
        if visible is not None:
            units.append((visible, [(start, pos)]))
    if stack:
        raise ValueError("repair unclosed RTF groups in the native caption editor")
    result: list[tuple[str, list[tuple[int, int]]]] = []
    index = 0
    while index < len(units):
        char, spans = units[index]
        code = ord(char)
        if 0xD800 <= code <= 0xDBFF and index + 1 < len(units):
            low, more = units[index + 1]
            if 0xDC00 <= ord(low) <= 0xDFFF:
                result.append(
                    (chr(0x10000 + (code - 0xD800) * 1024 + ord(low) - 0xDC00), spans + more)
                )
                index += 2
                continue
        if 0xD800 <= code <= 0xDFFF:
            raise ValueError("repair unpaired RTF Unicode surrogates in the native editor")
        result.append((char, spans))
        index += 1
    return result


def rtf_encode(text: str) -> str:
    chunks = [r"{\uc0 "]
    for char in text:
        code = ord(char)
        if char in "\\{}":
            chunks.append("\\" + char)
        elif char == "\n":
            chunks.append("\\\n")
        elif char == "\t":
            chunks.append(r"\tab ")
        elif " " <= char <= "~":
            chunks.append(char)
        elif code < 32 or 0xD800 <= code <= 0xDFFF or code == 127:
            raise ValueError(
                "supply Unicode caption text without control characters or lone surrogates"
            )
        else:
            encoded = char.encode("utf-16-le")
            for offset in range(0, len(encoded), 2):
                unit = int.from_bytes(encoded[offset : offset + 2], "little")
                chunks.append("\\u" + str(unit if unit < 32768 else unit - 65536) + " ")
    return "".join(chunks) + "}"


def replace_rtf(text: str, expected: str, replacements: Any) -> str:
    chars = rtf_characters(text)
    current = "".join(c for c, _ in chars)
    if current != expected:
        raise ValueError("RTF visible text differs from expected; inspect the native cue again")
    if not isinstance(replacements, list) or not replacements:
        raise ValueError("supply nonempty ordered RTF substring replacements")
    changes: list[tuple[int, int, str]] = []
    previous_end, previous_start = -1, -1
    for edit in replacements:
        if not isinstance(edit, dict) or set(edit) != {"start", "end", "text"}:
            raise ValueError("supply each RTF replacement as start, end and text")
        start, end, replacement = edit["start"], edit["end"], edit["text"]
        if (
            type(start) is not int
            or type(end) is not int
            or not 0 <= start <= end <= len(chars)
            or start < previous_end
            or start == previous_start
            or not isinstance(replacement, str)
        ):
            raise ValueError("use ordered nonoverlapping original Unicode code-point ranges")
        previous_start, previous_end = start, end
        encoded = rtf_encode(replacement)
        if current[start:end] == replacement:
            continue
        if not chars:
            raise ValueError(
                "add text to an empty RTF cue in the native editor to establish its style"
            )
        anchor = chars[start][1][0][0] if start < len(chars) else chars[-1][1][-1][1]
        if replacement:
            changes.append((anchor, anchor, encoded))
        removed: list[tuple[int, int]] = []
        for _, spans in chars[start:end]:
            for a, b in spans:
                if removed and removed[-1][1] == a:
                    removed[-1] = (removed[-1][0], b)
                else:
                    removed.append((a, b))
        # Empty groups separate every removed chunk, including chunks after
        # retained style controls. Removing a control's delimiter must never
        # turn e.g. \b\par text into the different control \btext.
        changes.extend((a, b, "{}") for a, b in removed)
    for start, end, replacement in sorted(changes, reverse=True):
        text = text[:start] + replacement + text[end:]
    return text


def correct_rtf(doc: dict[str, Any], clip_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    require_native(doc, dynamic=True)
    spec_keys(spec, {"edits"}, {"edits"})
    edits, seen = spec["edits"], set()
    if not isinstance(edits, list) or not edits:
        raise ValueError("supply nonempty occurrence-specific RTF cue edits")
    result = copy.deepcopy(doc)
    frames = point_frames(closed_target(result, clip_id)[2], "caption")
    for edit in edits:
        if not isinstance(edit, dict) or set(edit) != {"index", "expected", "replacements"}:
            raise ValueError("supply RTF edits as index, expected visible text and replacements")
        index = edit["index"]
        if type(index) is not int or not 0 <= index < len(frames) or index in seen:
            raise ValueError("select distinct existing RTF caption point indices")
        seen.add(index)
        value = frames[index]["value"]
        if value.get("textAttributes", "missing") is not None or not isinstance(
            edit["expected"], str
        ):
            raise ValueError("select native RTF-only caption text with null textAttributes")
        value["text"] = replace_rtf(value["text"], edit["expected"], edit["replacements"])
    return result


def inspect_rtf(doc: dict[str, Any], clip_id: int) -> list[dict[str, Any]]:
    require_native(doc, dynamic=True)
    frames = point_frames(closed_target(doc, clip_id)[2], "caption")
    return [
        dict(index=i, text="".join(c for c, _ in rtf_characters(frame["value"]["text"])))
        for i, frame in enumerate(frames)
        if frame["value"]["text"].startswith(r"{\rtf")
    ]


def correct_words(
    doc: dict[str, Any], source_id: int, index: int, spec: dict[str, Any]
) -> dict[str, Any]:
    require_native(doc, dynamic=True)
    result = copy.deepcopy(doc)
    correction_edits(
        spec, point_frames(transcription(result, source_id, index), "string"), words=True
    )
    return result


def closed_style_value(name: str, value: Any, *, requested: bool) -> None:
    if name == "fontName":
        if (
            not isinstance(value, str)
            or not value.strip()
            or (requested and value not in CLOSED_FONTS)
        ):
            raise ValueError("use an observed native closed-caption font choice")
    elif name == "fontSize":
        if type(value) is not int or value <= 0:
            raise ValueError("use a positive integer closed-caption font size")
    elif (
        not isinstance(value, list)
        or len(value) != 4
        or any(type(channel) is not int or not 0 <= channel <= 255 for channel in value)
    ):
        raise ValueError("use four integer RGBA bytes for closed-caption colors")


def set_style(doc: dict[str, Any], spec: dict[str, Any]) -> dict[str, Any]:
    require_native(doc)
    if doc.get("authoringClientName") != hotspots.NATIVE_CLIENT:
        raise ValueError("use the verified Mac 2026.2.4 global closed-caption style contract")
    spec_keys(spec, {"style"}, {"style"})
    requested = spec["style"]
    if not isinstance(requested, dict) or not requested or requested.keys() - CLOSED_STYLE_FIELDS:
        raise ValueError("supply nonempty supported global closed-caption style fields")
    timeline = doc.get("timeline")
    current = timeline.get("captionAttributes") if isinstance(timeline, dict) else None
    if not isinstance(current, dict):
        raise ValueError("capture native global captionAttributes before editing style")
    for name in requested:
        if name not in current:
            raise ValueError(
                "retain existing captionAttributes fields; no missing defaults are inserted"
            )
        closed_style_value(name, current[name], requested=False)
        closed_style_value(name, requested[name], requested=True)
    result = copy.deepcopy(doc)
    result["timeline"]["captionAttributes"].update(copy.deepcopy(requested))
    return result


def set_cues(doc: dict[str, Any], clip_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    require_native(doc)
    spec_keys(spec, {"clock", "cues"}, {"clock", "cues"})
    if spec["clock"] not in ("media", "timeline") or not isinstance(spec["cues"], list):
        raise ValueError("supply cue arrays and an explicit media or timeline clock")
    result = copy.deepcopy(doc)
    physical, _, parameter = closed_target(result, clip_id)
    for frame in point_frames(parameter, "caption"):
        plain(frame["value"])
        if set(frame) != {"time", "duration", "endTime", "value"} or set(frame["value"]) != {
            "text",
            "textAttributes",
        }:
            raise ValueError(
                "preserve opaque per-point data with set-text; capture a plain replacement template"
            )
    _, owner, audio, ancestors = closed_clock(result, clip_id)
    bound, points, previous = capacity(result, audio), {0: ""}, Fraction(-1)
    for cue in spec["cues"]:
        if (
            not isinstance(cue, dict)
            or set(cue) != {"start", "end", "text"}
            or not isinstance(cue["text"], str)
            or not cue["text"]
            or "\x00" in cue["text"]
        ):
            raise ValueError("supply nonempty plain cue text with explicit start and end")
        plain(dict(text=cue["text"], textAttributes=None))
        begin, end = (project.number(cue[k]) * RATE for k in ("start", "end"))
        if spec["clock"] == "timeline":
            if ancestors:
                visible = closed_interval(Fraction(0), bound, owner, ancestors)
                if visible is None or begin < visible[0] or end > visible[1]:
                    raise ValueError(
                        "place timeline cues inside the child's visible Group window; "
                        "use the media clock to author cropped source cues"
                    )
            begin, end = (closed_source_tick(p, owner, ancestors) for p in (begin, end))
        if (
            begin < 0
            or begin < previous
            or begin >= end
            or end > bound
            or begin.denominator != 1
            or end.denominator != 1
        ):
            raise ValueError(
                "supply ordered nonoverlapping cues within source bounds on exact media ticks"
            )
        points[begin.numerator], points[end.numerator] = cue["text"], ""
        previous = end
    parameter["keyframes"] = [
        dict(time=t, endTime=t, duration=0, value=dict(text=text, textAttributes=None))
        for t, text in sorted(points.items())
    ]
    attributes = result.get("timeline", {}).get("captionAttributes")
    if not isinstance(attributes, dict) or type(attributes.get("enabled")) is not bool:
        raise ValueError("capture native global captionAttributes before authoring cues")
    attributes["enabled"] = True
    # Identity is retained even when a caller selected the linked wrapper.
    if physical is not audio:
        raise ValueError("repair the caption's physical audio owner before replacing cues")
    return result


def placement_ticks(doc: dict[str, Any], seconds: Any, *, nested: bool) -> int:
    value = project.number(seconds)
    if value < 0 and not nested:
        raise ValueError("use nonnegative root placement; signed starts require a parent Group")
    return hotspots.ticks(doc, exact(abs(value))) * (-1 if value < 0 else 1)


def caption_lane_fit(
    doc: dict[str, Any],
    track: dict[str, Any],
    owner: dict[str, Any],
    ancestors: list[dict[str, Any]],
) -> None:
    collisions = project.native_lane_collisions(doc)
    if collisions:
        raise ValueError("resolve overlapping caption clips: " + collisions[0])
    if ancestors:
        start, duration = (project.number(owner[k]) for k in ("start", "duration"))
        for other in track["medias"]:
            if other is owner:
                continue
            left = project.number(other.get("start"))
            right = left + project.number(other.get("duration"))
            if max(start, left) < min(start + duration, right):
                raise ValueError(
                    "keep the edited Group caption clip and its lane siblings nonoverlapping"
                )
    for transition in transitions.transition_list(track):
        transitions.check_fit(track, transition, transition)


def retime(doc: dict[str, Any], clip_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    require_native(doc)
    keys = {"start", "duration", "media_start", "scalar"}
    spec_keys(spec, keys | {"clock"}, keys)
    if "clock" in spec and spec["clock"] != "parent":
        raise ValueError("use explicit clock parent for Group-child retiming")
    _, _, audio, ancestors = closed_clock(doc, clip_id)
    if ancestors and spec.get("clock") != "parent":
        raise ValueError("set clock parent to retime a Group child in its immediate parent clock")
    key = "captionData" if audio["_type"] == "Caption" else "captions"
    parameters = audio.get("parameters", {})
    if not isinstance(parameters, dict):
        raise ValueError("inspect native audio/caption parameter objects before retiming")
    map_captions(doc, clip_id, closed_only=bool(ancestors) and key in parameters)
    result = copy.deepcopy(doc)
    track, owner, audio, ancestors = closed_clock(result, clip_id)
    start = placement_ticks(result, spec["start"], nested=bool(ancestors))
    duration, media_start = (hotspots.ticks(result, spec[k]) for k in ("duration", "media_start"))
    scalar = project.number(spec["scalar"])
    if owner is not audio:
        require_frame_grid(result, dict(start=start, duration=duration, mediaStart=media_start))
    streams = [audio] if owner is audio else [audio, owner["video"]]
    if (
        duration <= 0
        or scalar <= 0
        or any(
            media_start + Fraction(duration) / scalar > capacity(result, child) for child in streams
        )
    ):
        raise ValueError(
            "use positive duration/inverse speed and a consumed interval within every selected stream's source bounds"
        )
    media_duration = exact(Fraction(duration) / scalar)
    if owner is not audio:
        require_frame_grid(result, dict(mediaDuration=media_duration))
    nodes = [owner] if owner is audio else [owner, owner["video"], audio]
    for node in nodes:
        if (
            node.get("effects", [])
            or node.get("animationTracks", {})
            or node.get("leftEdgeMods")
            or node.get("rightEdgeMods")
        ):
            raise ValueError(
                "capture a separate retiming contract for effected/animated caption owners"
            )
        node.update(
            start=start,
            duration=duration,
            mediaStart=media_start,
            mediaDuration=media_duration,
            scalar=exact(scalar),
        )
    caption_lane_fit(result, track, owner, ancestors)
    return result


def set_display(doc: dict[str, Any], clip_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    require_native(doc, dynamic=True)
    keys = {"start", "duration", "definition", "rich", "clock"}
    spec_keys(spec, keys, set())
    if not spec.keys() - {"schema_version", "clock"}:
        raise ValueError(
            "name a display bound, existing definition control or existing rich font/color"
        )
    result = copy.deepcopy(doc)
    if "clock" in spec and spec["clock"] != "parent":
        raise ValueError("use explicit clock parent for Group display bounds")
    path, owner = selected(result, clip_id)
    definition = owner.get("def")
    if (
        owner.get("_type") != "Callout"
        or not isinstance(definition, dict)
        or definition.get("modifier") != "dynamicCaption"
    ):
        raise ValueError(
            "select a saved native dynamic-caption display, separately from its source words"
        )
    if "start" in spec or "duration" in spec:
        track, ancestors = caption_context(result, path)
        if ancestors and spec.get("clock") != "parent":
            raise ValueError("set clock parent to bound a display in its immediate Group clock")
        if (
            project.number(owner.get("mediaStart")) != 0
            or project.number(owner.get("scalar")) != 1
            or owner.get("effects", [])
            or owner.get("animationTracks", {})
            or owner.get("leftEdgeMods")
            or owner.get("rightEdgeMods")
        ):
            raise ValueError(
                "bound a clean scalar-one untrimmed display; capture other clocks first"
            )
        if "start" in spec:
            owner["start"] = placement_ticks(result, spec["start"], nested=bool(ancestors))
        if "duration" in spec:
            duration = hotspots.ticks(result, spec["duration"])
            if duration <= 0:
                raise ValueError("use a positive native display duration")
            owner.update(duration=duration, mediaDuration=duration)
        require_frame_grid(result, dict(start=owner.get("start"), duration=owner.get("duration")))
        caption_lane_fit(result, track, owner, ancestors)
    if "definition" in spec:
        changes = spec["definition"]
        if not isinstance(changes, dict) or not changes or changes.keys() - DISPLAY_NUMBERS:
            raise ValueError("name supported existing native dynamic display numeric controls")
        for name, value in changes.items():
            number = project.number(value)
            if (
                (name.endswith(("-enabled", "-sentence")) and number not in (0, 1))
                or (("-color-" in name or name.endswith("-opacity")) and not 0 <= number <= 1)
                or (name.endswith("-duration") and number < 0)
            ):
                raise ValueError("use the observed native range for " + name)
            effects.patch_parameter(definition, name, value)
    if "rich" in spec:
        changes = spec["rich"]
        if (
            not isinstance(changes, dict)
            or not changes
            or changes.keys() - {"fontName", "fontSize", "fgColor"}
        ):
            raise ValueError("name existing rich fontName/fontSize/fgColor controls")
        attributes, text = definition.get("textAttributes"), definition.get("text")
        if (
            not isinstance(attributes, dict)
            or attributes.get("type") != "textAttributeList"
            or not isinstance(text, str)
        ):
            raise ValueError("capture the native placeholder and rich display font representation")
        frames = attributes.get("keyframes")
        if (
            not isinstance(frames, list)
            or len(frames) != 1
            or not isinstance(frames[0], dict)
            or any(
                type(frames[0].get(k)) is not int or frames[0][k] != 0
                for k in ("time", "duration", "endTime")
            )
            or not isinstance(frames[0].get("value"), list)
        ):
            raise ValueError("capture a static native display rich frame before styling")
        for name, value in changes.items():
            runs = [r for r in frames[0]["value"] if isinstance(r, dict) and r.get("name") == name]
            if (
                len(runs) != 1
                or runs[0].get("valueType") != annotations.RICH_TYPES[name]
                or type(runs[0].get("rangeStart")) is not int
                or runs[0]["rangeStart"] != 0
                or type(runs[0].get("rangeEnd")) is not int
                or runs[0]["rangeEnd"] != len(text.encode("utf-8"))
            ):
                raise ValueError("select one full-placeholder native rich property: " + name)
            runs[0]["value"] = annotations.rich_value(name, value)
    return result


def mapped_holds(
    frames: list[dict[str, Any]],
    owner: dict[str, Any],
    bound: Fraction,
    *,
    words: bool,
    ancestors: list[dict[str, Any]] | None = None,
) -> list[dict[str, Any]]:
    duration, media_start, scalar = (
        project.number(owner[k]) for k in ("duration", "mediaStart", "scalar")
    )
    limit = media_start + duration / scalar
    if limit > bound:
        raise ValueError("repair the caption owner's consumed interval beyond source bounds")
    result = []
    for index, frame in enumerate(frames):
        # A selected source trim omits earlier dynamic word onsets. Ancestor
        # cropping instead carries a hold already active inside that Group.
        if words and frame["time"] < media_start:
            continue
        begin = max(Fraction(frame["time"]), media_start)
        end = min(Fraction(frames[index + 1]["time"]) if index + 1 < len(frames) else bound, limit)
        if begin >= end:
            continue
        mapped = closed_interval(begin, end, owner, ancestors or [])
        if mapped is None:
            continue
        left, right = mapped
        result.append(
            dict(
                index=index,
                value=frame["value"] if words else frame["value"]["text"],
                sourceTime=frame["time"],
                timelineStartTicks=exact(left),
                timelineEndTicks=exact(right),
                timelineStartSeconds=str(left / RATE),
                timelineEndSeconds=str(right / RATE),
            )
        )
    return result


def map_captions(doc: dict[str, Any], clip_id: int, *, closed_only: bool = False) -> dict[str, Any]:
    require_native(doc)
    _, owner, audio, ancestors = closed_clock(doc, clip_id)
    bound, result = capacity(doc, audio), dict(clipId=owner["id"], clock=RATE)
    key = "captionData" if audio["_type"] == "Caption" else "captions"
    parameters = audio.get("parameters", {})
    if not isinstance(parameters, dict):
        raise ValueError("inspect native audio/caption parameter objects")
    result["closed"] = (
        mapped_holds(
            point_frames(parameters[key], "caption"),
            owner,
            bound,
            words=False,
            ancestors=ancestors,
        )
        if key in parameters
        else []
    )
    if closed_only:
        if key not in parameters:
            raise ValueError("select saved closed captions before requesting closed-only mapping")
        result.update(scope="closed", ancestors=[group["id"] for group in ancestors])
        return result
    recognized = False
    if ancestors:
        result["ancestors"] = [group["id"] for group in ancestors]
    if audio["_type"] == "AMFile":
        source, stream = audio_stream(doc, audio)
        if stream.get("transcriptionSet") is True:
            require_native(doc, dynamic=True)
            result["words"] = mapped_holds(
                point_frames(transcription(doc, source["id"], audio["trackNumber"]), "string"),
                owner,
                bound,
                words=True,
                ancestors=ancestors,
            )
            recognized = True
        else:
            result["words"] = []
    if key not in parameters and not recognized:
        raise ValueError("select saved closed captions or actual recognized source transcription")
    return result


def inventory(doc: dict[str, Any]) -> dict[str, Any]:
    closed, words, displays, audio_uses = [], [], [], []
    clips = hotspots.clips(doc)
    linked_audio = {path + "/audio" for path, node in clips if node.get("_type") == "UnifiedMedia"}
    for path, owner in clips:
        audio = owner.get("audio") if owner.get("_type") == "UnifiedMedia" else owner
        if isinstance(audio, dict) and audio.get("_type") == "AMFile" and path not in linked_audio:
            parents = sorted(
                [(p, n) for p, n in clips if path.startswith(p + "/")],
                key=lambda item: len(item[0]),
                reverse=True,
            )
            audio_uses.append(
                dict(
                    clipId=owner.get("id"),
                    audioClipId=audio.get("id"),
                    ownerType=owner.get("_type"),
                    path=path,
                    sourceId=audio.get("src"),
                    sourceTrack=audio.get("trackNumber"),
                    clocks={k: owner.get(k) for k in effects.CLOCK_FIELDS},
                    containers=[
                        dict(clipId=n.get("id"), ownerType=n.get("_type")) for _, n in parents
                    ],
                )
            )
        parameters = owner.get("parameters", {})
        if isinstance(parameters, dict):
            for key in ("captions", "captionData"):
                if key in parameters:
                    closed.append(
                        dict(
                            clipId=owner.get("id"),
                            ownerType=owner.get("_type"),
                            path=project.pointer(project.pointer(path, "parameters"), key),
                            parameter=parameters[key],
                        )
                    )
        definition = owner.get("def")
        if isinstance(definition, dict) and definition.get("modifier") == "dynamicCaption":
            displays.append(
                dict(
                    clipId=owner.get("id"),
                    path=path,
                    definition=definition,
                    clocks={k: owner.get(k) for k in effects.CLOCK_FIELDS},
                )
            )
    sources = doc.get("sourceBin", [])
    if not isinstance(sources, list) or any(not isinstance(s, dict) for s in sources):
        raise ValueError("inspect the native sourceBin array before caption inventory")
    for source in sources:
        streams = source.get("sourceTracks", [])
        if not isinstance(streams, list) or any(not isinstance(s, dict) for s in streams):
            raise ValueError("inspect native sourceTracks arrays before caption inventory")
        for index, stream in enumerate(streams):
            parameters = stream.get("parameters", {})
            if isinstance(parameters, dict) and "transcription" in parameters:
                words.append(
                    dict(
                        sourceId=source.get("id"),
                        sourceTrack=index,
                        streamEditRate=stream.get("editRate"),
                        transcriptionSet=stream.get("transcriptionSet"),
                        parameter=parameters["transcription"],
                    )
                )
    timeline = doc.get("timeline")
    return dict(
        closed=closed,
        transcriptions=words,
        audioUses=audio_uses,
        displays=displays,
        captionAttributes=copy.deepcopy(
            timeline.get("captionAttributes") if isinstance(timeline, dict) else None
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = JsonHelpParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in (
        "inspect",
        "map",
        "set-text",
        "rtf-text",
        "set-rtf-text",
        "set-cues",
        "correct-words",
        "retime",
        "set-display",
        "set-style",
    ):
        command = commands.add_parser(name)
        command.add_argument("project", type=Path)
        if name not in ("inspect", "correct-words", "set-style"):
            command.add_argument("--clip-id", type=int, required=True)
        if name == "correct-words":
            command.add_argument("--source-id", type=int, required=True)
            command.add_argument("--source-track", type=int, required=True)
        if name == "map":
            command.add_argument("--closed-only", action="store_true")
        if name not in ("inspect", "map", "rtf-text"):
            command.add_argument("--spec", type=Path, required=True)
            command.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        doc, raw = project.load(args.project)
        report: dict[str, Any] = dict(
            schema_version=1, owner="camtasia-captions", ok=True, projectSha256=project.digest(raw)
        )
        if args.command == "inspect":
            report.update(inventory(doc))
        elif args.command == "map":
            report["mapping"] = map_captions(doc, args.clip_id, closed_only=args.closed_only)
        elif args.command == "rtf-text":
            report["cues"] = inspect_rtf(doc, args.clip_id)
        else:
            spec = project.load(args.spec)[0]
            if args.command == "correct-words":
                candidate = correct_words(doc, args.source_id, args.source_track, spec)
            elif args.command == "set-style":
                candidate = set_style(doc, spec)
            else:
                operation = {
                    "set-text": correct_text,
                    "set-rtf-text": correct_rtf,
                    "set-cues": set_cues,
                    "retime": retime,
                    "set-display": set_display,
                }[args.command]
                candidate = operation(doc, args.clip_id, spec)
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
        print(json.dumps(dict(ok=False, error=str(exc)), ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
