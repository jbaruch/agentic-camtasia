#!/usr/bin/env python3
"""Stage native Quick Property AV/image replacement and clearing.

replace PROJECT --group-id ID --index N --source-clip-id ID --spec SPEC --output
OUT uses an ordinary saved IMFile or linked VMFile/AMFile donor in the same
project. No file import/source constructor is inferred. The complete source bin
stays unchanged, and both AV streams resolve their own track clocks/ranges.
clear takes --template-project PROJECT --template-clip-id ID for an actual native
transparent cleared Quick Property Callout. Both take {schema_version:1,
expected:ENTRY}; the expected row protects selection against stale edits.

Replacement resets source starts to zero, fits inside the remembered original
box, clamps finite AV use to both stream bounds, and restores remembered use
when a longer source follows a short one. Images use their native still hold.
Clear restores the remembered used duration. Group bounds never change.
Existing AV gain survives AV replacement; removing its audio through image/clear
and restoring AV creates unity gain. Static geometry/opacity and Colorize are
preserved; unknown/animated processing needs its feature contract. Native
replacement metadata intentionally becomes the five REPLACEMENT_FIELDS; native
linking extends metadata instead. No theme application or source import occurs.

Bound root IDs survive; existing AV child IDs survive same-kind replacement.
Type changes allocate fresh children above the complete document ID namespace,
never renumber unrelated clips. Bindings remain on their root owner. References
to removed child IDs cause refusal. Unknown type-specific fields are retained
on same-kind edits and refused before a type change could discard them.

Stdout schema_version:1 owner camtasia-media-replacement includes hashes,
changed/written, properties and nativeVerified:false. Only an exclusive staged
candidate is written; identical existing output is a no-op. Inputs, editor,
sources and media files are untouched. Exit 0 success, 1 actionable JSON stderr
refusal, 2 JSON stderr CLI usage. Native save/reopen/render remains required.
"""

from __future__ import annotations

import copy
from fractions import Fraction
import json
from pathlib import Path
import sys
from typing import Any

import annotations
import captions
import effects
import hotspots
import project
import quick_properties as quick

REPLACEMENT_FIELDS = (
    "originalMediaWidth",
    "originalMediaHeight",
    "originalMediaQuickPropertyDuration",
    "previousReplacementWidth",
    "previousReplacementHeight",
)
GEOMETRY = frozenset(
    {
        "scale0",
        "scale1",
        "translation0",
        "translation1",
        "translation2",
        "opacity",
        "rotation0",
        "rotation1",
        "rotation2",
        "geometryCrop0",
        "geometryCrop1",
        "geometryCrop2",
        "geometryCrop3",
    }
)
COMMON_FIELDS = frozenset(
    {
        "id",
        "_type",
        "attributes",
        "parameters",
        "effects",
        "start",
        "duration",
        "mediaStart",
        "mediaDuration",
        "scalar",
        "metadata",
        "animationTracks",
    }
)


def static(value: Any) -> Fraction:
    if isinstance(value, dict):
        if (
            value.get("type") != "double"
            or value.get("keyframes", [])
            or "defaultValue" not in value
        ):
            raise ValueError(
                "use native static double controls; preserve animated media separately"
            )
        return project.number(value["defaultValue"])
    return project.number(value)


def visual(owner: dict[str, Any]) -> dict[str, Any]:
    if owner.get("_type") == "UnifiedMedia":
        video, audio = owner.get("video"), owner.get("audio")
        if (
            not isinstance(video, dict)
            or video.get("_type") != "VMFile"
            or not isinstance(audio, dict)
            or audio.get("_type") != "AMFile"
        ):
            raise ValueError("use an ordinary native linked VMFile/AMFile replacement owner")
        for child in (video, audio):
            if any(
                project.number(child.get(k)) != project.number(owner.get(k))
                for k in ("start", "duration", "mediaStart", "mediaDuration", "scalar")
            ):
                raise ValueError("repair complete linked AV clocks before media replacement")
        return video
    if owner.get("_type") not in {"IMFile", "Callout"}:
        raise ValueError("select a bound ordinary image, linked AV or native cleared Callout")
    return owner


def source_stream(
    doc: dict[str, Any], node: dict[str, Any], kind: int
) -> tuple[dict[str, Any], dict[str, Any]]:
    if type(node.get("src")) is not int:
        raise ValueError("select a numeric native source ID")
    sources = doc.get("sourceBin")
    if not isinstance(sources, list) or any(not isinstance(s, dict) for s in sources):
        raise ValueError("capture the native source bin before replacing media")
    matches = [s for s in sources if type(s.get("id")) is int and s["id"] == node.get("src")]
    track = node.get("trackNumber")
    if len(matches) != 1 or type(track) is not int or track < 0:
        raise ValueError("resolve the selected clip's unique source ID and trackNumber")
    tracks = matches[0].get("sourceTracks")
    if (
        not isinstance(tracks, list)
        or track >= len(tracks)
        or not isinstance(tracks[track], dict)
        or type(tracks[track].get("type")) is not int
        or tracks[track]["type"] != kind
    ):
        raise ValueError("select the matching native image/video/audio source track")
    return matches[0], tracks[track]


def dimensions(doc: dict[str, Any], owner: dict[str, Any]) -> tuple[Fraction, Fraction]:
    node = visual(owner)
    if node.get("_type") == "Callout":
        cleared(node)
        return static(node["def"].get("width")), static(node["def"].get("height"))
    _, track = source_stream(doc, node, 1 if node.get("_type") == "IMFile" else 0)
    rect = track.get("trackRect")
    if not isinstance(rect, list) or len(rect) != 4:
        raise ValueError("capture the selected source trackRect dimensions")
    width, height = project.number(rect[2]), project.number(rect[3])
    if width <= 0 or height <= 0 or project.number(rect[0]) != 0 or project.number(rect[1]) != 0:
        raise ValueError("use a native positive origin-zero source rectangle")
    return width, height


def cleared(node: dict[str, Any]) -> None:
    definition = node.get("def")
    if node.keys() - (COMMON_FIELDS | {"def"}):
        raise ValueError("use a source-free native cleared-media template without extra companions")
    if (
        node.get("_type") != "Callout"
        or not isinstance(definition, dict)
        or any(
            definition.get(k) != v
            for k, v in {
                "kind": "remix",
                "shape": "shape-rectangle",
                "style": "bold",
                "fill-style": "solid",
                "stroke-style": "solid",
            }.items()
        )
    ):
        raise ValueError("capture a native transparent cleared media Quick Property Callout")
    for key in (
        "fill-color-red",
        "fill-color-green",
        "fill-color-blue",
        "fill-color-opacity",
        "stroke-width",
    ):
        if static(definition.get(key)) != 0:
            raise ValueError("use the unmodified transparent zero-stroke native clear template")
    if definition.keys() - {
        "kind",
        "shape",
        "style",
        "fill-style",
        "stroke-style",
        "width",
        "height",
        "corner-radius",
        "fill-color-red",
        "fill-color-green",
        "fill-color-blue",
        "fill-color-opacity",
        "stroke-width",
    }:
        raise ValueError("preserve unfamiliar clear definitions through the editor")


def clean(owner: dict[str, Any], *, donor: bool = False) -> None:
    node = visual(owner)
    if (
        any(project.number(owner.get(k)) <= 0 for k in ("duration", "mediaDuration"))
        or project.number(owner.get("mediaStart")) < 0
    ):
        raise ValueError("use positive native media intervals and a nonnegative source offset")
    if project.number(owner.get("scalar")) != 1:
        raise ValueError("use unretimed media for the native replacement contract")
    if owner.get("_type") == "Callout":
        cleared(owner)
    if owner.get("_type") == "IMFile" and (
        project.number(owner.get("mediaDuration")) != 1
        or project.number(owner.get("trimStartSum", 0)) != 0
    ):
        raise ValueError("use the native single-tick untrimmed image hold")
    parts = [owner, node, owner["audio"]] if owner is not node else [owner]
    if any(type(part.get("id")) is not int for part in parts) or len(
        {part["id"] for part in parts}
    ) != len(parts):
        raise ValueError("capture unique numeric native replacement owner/child IDs")
    for part in [owner, node, owner["audio"]] if owner is not node else [owner]:
        if part.get("animationTracks", {}) or part.get("leftEdgeMods") or part.get("rightEdgeMods"):
            raise ValueError(
                "preserve animated/transitioned media through its separate replacement contract"
            )
        for effect in effects.effects_of(part):
            if (
                donor
                or effect.get("effectName") != "Colorize"
                or effect.get("category") != effects.CATEGORY
                or effects.timed_payload(effect)
            ):
                raise ValueError(
                    "use an unprocessed donor and static native Colorize-only destination"
                )
    if owner is not node and owner.get("effects", []) != node.get("effects", []):
        raise ValueError("repair matching linked visual processing before replacement")
    params = node.get("parameters", {})
    if "sourceEffect" in node:
        raise ValueError("preserve source-specific dynamic controls through their feature contract")
    if not isinstance(params, dict) or params.keys() - GEOMETRY:
        raise ValueError("preserve unfamiliar media parameter companions through the native editor")
    for key, value in params.items():
        number = static(value)
        if (key.startswith("geometryCrop") or key.startswith("rotation")) and number != 0:
            raise ValueError("use uncropped unrotated native replacement boxes")
    x, y = (static(params.get(k, 1)) for k in ("scale0", "scale1"))
    if x <= 0 or y != x:
        raise ValueError("use a positive uniform native media fit")
    if owner is not node:
        audio = owner["audio"]
        attributes = audio.get("attributes", {})
        if (
            not isinstance(attributes, dict)
            or project.number(attributes.get("sourceFileOffset", 0)) != 0
            or audio.get("parameters", {})
            or audio.get("effects", [])
        ):
            raise ValueError(
                "preserve source-offset/caption/processed audio through its separate contract"
            )
    if not isinstance(node.get("attributes", {}), dict):
        raise ValueError("repair native visual attributes before media replacement")


def remembered(doc: dict[str, Any], owner: dict[str, Any]) -> tuple[Fraction, Fraction, Fraction]:
    metadata = owner.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("repair the native replacement metadata object")
    present = [k in metadata for k in REPLACEMENT_FIELDS]
    if any(present):
        if not all(present) or any(
            not isinstance(metadata[k], dict) or metadata[k].get("type") != "double"
            for k in REPLACEMENT_FIELDS
        ):
            raise ValueError("capture all five native typed replacement metadata fields")
        values = [project.number(metadata[k].get("value")) for k in REPLACEMENT_FIELDS]
        if any(v <= 0 for v in values):
            raise ValueError("repair positive native replacement dimensions and duration")
        return values[0], values[1], values[2]
    width, height = dimensions(doc, owner)
    params = visual(owner).get("parameters", {})
    return (
        width * static(params.get("scale0", 1)),
        height * static(params.get("scale1", 1)),
        project.number(owner.get("duration")),
    )


def finite_duration(doc: dict[str, Any], owner: dict[str, Any]) -> Fraction:
    limits = []
    for node, kind in ((owner["video"], 0), (owner["audio"], 2)):
        _, stream = source_stream(doc, node, kind)
        extent = stream.get("range")
        rate = project.number(stream.get("editRate"))
        if (
            not isinstance(extent, list)
            or len(extent) != 2
            or project.number(extent[0]) != 0
            or rate <= 0
            or project.number(extent[1]) <= 0
        ):
            raise ValueError("use finite origin-zero native stream ranges and positive clocks")
        limits.append(project.number(extent[1]) / rate * project.number(doc.get("editRate")))
    return min(limits)


def replace_child(
    doc: dict[str, Any], old: dict[str, Any], donor: dict[str, Any], *, linking: bool = False
) -> None:
    clean(old)
    clean(donor, donor=True)
    width, height, duration = remembered(doc, old)
    old_visual, donor_visual = visual(old), visual(donor)
    intrinsic_width, intrinsic_height = dimensions(doc, donor)
    is_clear = donor.get("_type") == "Callout"
    if is_clear:
        intrinsic_width, intrinsic_height = dimensions(doc, old)
        scale = static(old_visual.get("parameters", {}).get("scale0", 1))
        new_width, new_height = intrinsic_width * scale, intrinsic_height * scale
    else:
        scale = min(width / intrinsic_width, height / intrinsic_height)
        new_width, new_height = intrinsic_width * scale, intrinsic_height * scale
    if donor.get("_type") == "UnifiedMedia":
        duration = min(duration, finite_duration(doc, donor))
    captions.require_frame_grid(
        doc, dict(start=old.get("start"), duration=captions.exact(duration))
    )
    same = old.get("_type") == donor.get("_type")
    if not same:
        for node in [old, old_visual, old["audio"]] if old is not old_visual else [old]:
            allowed = COMMON_FIELDS | (
                {"video", "audio"}
                if node is old and old is not old_visual
                else {"src", "trackNumber", "channelNumber", "def", "trimStartSum"}
            )
            if node.keys() - allowed:
                raise ValueError(
                    "preserve unknown type-specific clip fields before changing media kind"
                )
        if old_visual.get("attributes", {}).keys() - {"ident", "autoRotateText"} or (
            old_visual is not old and old_visual.get("metadata", {})
        ):
            raise ValueError(
                "preserve opaque visual attributes/metadata before changing media kind"
            )
        removed = {n["id"] for n in ([old_visual, old["audio"]] if old is not old_visual else [])}
        for _, group in hotspots.clips(doc):
            if group.get("_type") == "Group":
                for row in quick.properties(group):
                    if any(
                        (b if type(b) is int else b.get("media") if isinstance(b, dict) else None)
                        in removed
                        for b in row.get("objects", [])
                    ):
                        raise ValueError(
                            "remove/rebind properties on AV children before removing those children"
                        )
        for _, value in project.objects(doc.get("timeline", {})):
            if any(
                type(value.get(k)) is int and value[k] in removed
                for k in ("leftMedia", "rightMedia")
            ):
                raise ValueError(
                    "preserve transitions referencing children before changing media kind"
                )
    target = copy.deepcopy(old if same else donor)
    target["id"] = old["id"]
    if target.get("_type") == "UnifiedMedia" and not same:
        next_id = (
            max((n["id"] for _, n in project.objects(doc) if type(n.get("id")) is int), default=0)
            + 1
        )
        target["video"]["id"], target["audio"]["id"] = next_id, next_id + 1
        target["audio"].setdefault("attributes", {})["gain"] = 1.0
    target_visual = visual(target)
    params = copy.deepcopy(old_visual.get("parameters", {}))
    for key, value in (("scale0", scale), ("scale1", scale)):
        if key in params:
            effects.patch_parameter(params, key, captions.exact(value))
        else:
            params[key] = effects.scalar_like(float, captions.exact(value))
    for key in ("geometryCrop0", "geometryCrop1", "geometryCrop2", "geometryCrop3"):
        params.setdefault(key, 0.0)
    target_visual["parameters"] = params
    target_visual["effects"] = copy.deepcopy(old_visual.get("effects", []))
    target_visual["animationTracks"] = {}
    if target is not target_visual:
        target["effects"] = copy.deepcopy(old_visual.get("effects", []))
        for key in ("video", "audio"):
            target[key]["src"] = donor[key]["src"]
            target[key]["trackNumber"] = donor[key]["trackNumber"]
        target_visual.setdefault("attributes", {})["ident"] = donor_visual.get(
            "attributes", {}
        ).get("ident", "")
    elif not is_clear:
        target["src"], target["trackNumber"] = donor["src"], donor["trackNumber"]
        target.setdefault("attributes", {})["ident"] = donor.get("attributes", {}).get("ident", "")
    else:
        target["def"] = copy.deepcopy(donor["def"])
        for key, value in (("width", intrinsic_width), ("height", intrinsic_height)):
            effects.patch_parameter(target["def"], key, captions.exact(value))
    parts = [target] if target is target_visual else [target, target_visual, target["audio"]]
    for part in parts:
        part.update(
            start=old["start"],
            duration=captions.exact(duration),
            mediaStart=0,
            mediaDuration=(1 if target.get("_type") == "IMFile" else captions.exact(duration)),
            scalar=1,
        )
    original_width, original_height, original_duration = remembered(doc, old)
    values = (original_width, original_height, original_duration, new_width, new_height)
    metadata = copy.deepcopy(old.get("metadata", {})) if linking else {}
    for key, value in zip(REPLACEMENT_FIELDS, values):
        metadata[key] = dict(type="double", value=effects.scalar_like(float, captions.exact(value)))
    target["metadata"] = metadata
    old.clear()
    old.update(target)


def edit_media(
    doc: dict[str, Any], group_id: int, index: int, spec: dict[str, Any], donor: dict[str, Any]
) -> dict[str, Any]:
    quick.spec_version(spec, {"expected"}, {"expected"})
    result = copy.deepcopy(doc)
    owner, row = quick.row_at(result, group_id, index)
    if row != spec["expected"] or row["type"] != 2:
        raise ValueError("reinspect and select the expected native type-2 media property")
    children = quick.bindings(result, owner, row)
    donor = copy.deepcopy(donor)
    for child in children:
        replace_child(result, child, donor)
    return result


def main(argv: list[str] | None = None) -> int:
    parser = annotations.JsonArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    for name in ("replace", "clear"):
        command = commands.add_parser(name)
        command.add_argument("project", type=Path)
        command.add_argument("--group-id", type=int, required=True)
        command.add_argument("--index", type=int, required=True)
        command.add_argument("--spec", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        if name == "replace":
            command.add_argument("--source-clip-id", type=int, required=True)
        else:
            command.add_argument("--template-project", type=Path, required=True)
            command.add_argument("--template-clip-id", type=int, required=True)
    args = parser.parse_args(argv)
    try:
        doc, raw = project.load(args.project)
        if args.command == "replace":
            donor = quick.selected(doc, args.source_clip_id)
            if donor.get("_type") not in {"UnifiedMedia", "IMFile"}:
                raise ValueError(
                    "select a saved ordinary image or AV donor, or use clear with a native template"
                )
        else:
            template = project.load(args.template_project)[0]
            annotations.require_native(template)
            donor = quick.selected(template, args.template_clip_id)
            cleared(donor)
        candidate = edit_media(doc, args.group_id, args.index, project.load(args.spec)[0], donor)
        report = dict(
            schema_version=1,
            owner="camtasia-media-replacement",
            ok=True,
            projectSha256=project.digest(raw),
            candidateSha256=project.digest(project.encode_document(candidate)),
            changed=candidate != doc,
            written=hotspots.stage(args.project, args.output, candidate),
            output=str(args.output),
            groups=quick.inventory(candidate),
            nativeVerified=False,
        )
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps(dict(ok=False, error=str(exc)), ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
