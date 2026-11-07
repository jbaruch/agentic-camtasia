#!/usr/bin/env python3
"""Inspect and stage closed/source-backed dynamic captions without editing inputs.

inspect PROJECT inventories audio-owned captions, imported Caption/captionData,
recognized source transcription and separate dynamic-caption displays. map
PROJECT --clip-id ID maps closed-cue holds and in-range word onsets through a single root clip's
trim, inverse speed and placement. Linked AV clocks are mirrors, never summed.
The verified caption/word clock is 705600000 ticks/sec, independently of each
source stream's sample/edit rate. Nested/stitched/multiscene mappings refuse.

set-text PROJECT --clip-id ID --spec SPEC corrects existing plain closed points.
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

retime PROJECT --clip-id ID --spec SPEC changes a clean root Caption/audio/linked
AV clock. Supply schema_version 1, start, duration, media_start (rational seconds)
and positive scalar (inverse speed). Complete mirrored clocks change together;
source words/cues and dynamic displays do not change. Consumed source bounds,
lane collisions and transitions are checked. Effects/animations need their own
retiming contract. Bound the independent display with set-display separately.
Linked-video cut inputs and edited display bounds must align with the document's
video frame grid. Recognized onsets and intentional subframe audio stay unchanged.

set-display PROJECT --clip-id ID --spec SPEC edits an existing native dynamic
display. Spec schema_version 1 accepts start/duration seconds, definition (existing
supported numeric controls), and rich (existing fontName/fontSize/fgColor).
The native placeholder, partial rich ranges, style IDs and all other controls
remain unchanged. Bound edits require an untrimmed scalar-one clean root display.
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
caption clock; source-backed dynamic edits require the latter. RTF captions are
inspectable but need a native/RTF-aware editing route. JSON stdout schema_version
1 owner camtasia-captions reports hashes, inventory, changed/written and
nativeVerified false. Staging is exclusive or an identical no-op. Follow project
validate/diff/apply, matching native save/reopen and actual caption/highlight or
Smart Player CC checks. Exit 0 success, 1 input/I/O refusal, 2 CLI syntax (JSON
stderr). --help prints plaintext stdout. Python 3.11+, standard library only.
"""

from __future__ import annotations

import copy
from fractions import Fraction
import json
from pathlib import Path
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
    if type(owner.get("id")) is not int:
        raise ValueError(
            "repair the root owner's numeric clip ID before caption mapping or retiming"
        )
    selected(doc, owner["id"])
    if not isinstance(audio, dict) or audio.get("_type") not in ("AMFile", "Caption"):
        raise ValueError("select a root Caption or speech-bearing audio/linked AV clip")
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
            values["start"] < 0
            or values["mediaStart"] < 0
            or any(values[key] <= 0 for key in ("duration", "mediaDuration", "scalar"))
        ):
            raise ValueError("retain complete positive native caption owner clocks")
        if any(project.number(owner[key]) != values[key] for key in effects.CLOCK_FIELDS):
            raise ValueError("repair conflicting complete linked AV caption clocks")
    return track, owner, audio


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
    _, owner, audio = root_clock(result, clip_id)
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
            begin, end = (
                project.number(owner["mediaStart"])
                + (p - project.number(owner["start"])) / project.number(owner["scalar"])
                for p in (begin, end)
            )
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


def retime(doc: dict[str, Any], clip_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    require_native(doc)
    keys = {"start", "duration", "media_start", "scalar"}
    spec_keys(spec, keys, keys)
    map_captions(doc, clip_id)
    result = copy.deepcopy(doc)
    track, owner, audio = root_clock(result, clip_id)
    start, duration, media_start = (
        hotspots.ticks(result, spec[k]) for k in ("start", "duration", "media_start")
    )
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
    collisions = project.native_lane_collisions(result)
    if collisions:
        raise ValueError(
            "resolve destination lane collisions before caption retiming: " + collisions[0]
        )
    for transition in transitions.transition_list(track):
        transitions.check_fit(track, transition, transition)
    return result


def set_display(doc: dict[str, Any], clip_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    require_native(doc, dynamic=True)
    keys = {"start", "duration", "definition", "rich"}
    spec_keys(spec, keys, set())
    if len(spec) == 1:
        raise ValueError(
            "name a display bound, existing definition control or existing rich font/color"
        )
    result = copy.deepcopy(doc)
    _, owner = selected(result, clip_id)
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
        lanes = [t for t in root_tracks(result) if any(n is owner for n in t.get("medias", []))]
        if (
            len(lanes) != 1
            or project.number(owner.get("mediaStart")) != 0
            or project.number(owner.get("scalar")) != 1
            or owner.get("effects", [])
            or owner.get("animationTracks", {})
            or owner.get("leftEdgeMods")
            or owner.get("rightEdgeMods")
        ):
            raise ValueError(
                "bound a clean scalar-one untrimmed root display; capture other clocks first"
            )
        if "start" in spec:
            owner["start"] = hotspots.ticks(result, spec["start"])
        if "duration" in spec:
            duration = hotspots.ticks(result, spec["duration"])
            if duration <= 0:
                raise ValueError("use a positive native display duration")
            owner.update(duration=duration, mediaDuration=duration)
        require_frame_grid(result, dict(start=owner.get("start"), duration=owner.get("duration")))
        collisions = project.native_lane_collisions(result)
        if collisions:
            raise ValueError("resolve overlapping display clips: " + collisions[0])
        for transition in transitions.transition_list(lanes[0]):
            transitions.check_fit(lanes[0], transition, transition)
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
    frames: list[dict[str, Any]], owner: dict[str, Any], bound: Fraction, *, words: bool
) -> list[dict[str, Any]]:
    start, duration, media_start, scalar = (
        project.number(owner[k]) for k in ("start", "duration", "mediaStart", "scalar")
    )
    limit = media_start + duration / scalar
    if limit > bound:
        raise ValueError("repair the caption owner's consumed interval beyond source bounds")
    result = []
    for index, frame in enumerate(frames):
        # Native closed cues carry into a trim; dynamic words with earlier
        # onsets are omitted, including the partly trimmed opening word.
        if words and frame["time"] < media_start:
            continue
        begin = max(Fraction(frame["time"]), media_start)
        end = min(Fraction(frames[index + 1]["time"]) if index + 1 < len(frames) else bound, limit)
        if begin >= end:
            continue
        left, right = (start + (p - media_start) * scalar for p in (begin, end))
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


def map_captions(doc: dict[str, Any], clip_id: int) -> dict[str, Any]:
    require_native(doc)
    _, owner, audio = root_clock(doc, clip_id)
    bound, result = capacity(doc, audio), dict(clipId=owner["id"], clock=RATE)
    key = "captionData" if audio["_type"] == "Caption" else "captions"
    parameters = audio.get("parameters", {})
    if not isinstance(parameters, dict):
        raise ValueError("inspect native audio/caption parameter objects")
    result["closed"] = (
        mapped_holds(point_frames(parameters[key], "caption"), owner, bound, words=False)
        if key in parameters
        else []
    )
    recognized = False
    if audio["_type"] == "AMFile":
        source, stream = audio_stream(doc, audio)
        if stream.get("transcriptionSet") is True:
            require_native(doc, dynamic=True)
            result["words"] = mapped_holds(
                point_frames(transcription(doc, source["id"], audio["trackNumber"]), "string"),
                owner,
                bound,
                words=True,
            )
            recognized = True
        else:
            result["words"] = []
    if key not in parameters and not recognized:
        raise ValueError("select saved closed captions or actual recognized source transcription")
    return result


def inventory(doc: dict[str, Any]) -> dict[str, Any]:
    closed, words, displays = [], [], []
    for path, owner in hotspots.clips(doc):
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
        displays=displays,
        captionAttributes=copy.deepcopy(
            timeline.get("captionAttributes") if isinstance(timeline, dict) else None
        ),
    )


def main(argv: list[str] | None = None) -> int:
    parser = annotations.JsonArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in (
        "inspect",
        "map",
        "set-text",
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
        if name not in ("inspect", "map"):
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
            report["mapping"] = map_captions(doc, args.clip_id)
        else:
            spec = project.load(args.spec)[0]
            if args.command == "correct-words":
                candidate = correct_words(doc, args.source_id, args.source_track, spec)
            elif args.command == "set-style":
                candidate = set_style(doc, spec)
            else:
                operation = {
                    "set-text": correct_text,
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
