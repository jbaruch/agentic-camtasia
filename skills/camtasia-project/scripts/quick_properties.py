#!/usr/bin/env python3
"""Stage native Group Quick Property bindings and value edits (Mac 2026.2.4).

inspect PROJECT inventories raw properties and their resolved descendant owners.
bindings PROJECT --group-id ID --spec SPEC stages an ordered property array:
{schema_version:1, expected:[old entries], properties:[desired entries]}.
This covers rename/reorder/remove/re-add and explicit child-ID rebinding. New
entries use native type/name/objects shapes, without invented mappings. Existing
opaque entry fields survive. Creating shared controls uses link, not bindings.

link/unlink PROJECT --group-id ID --index N --spec SPEC require
{schema_version:1, expected:[complete old entries]}. Link merges the selected row
with its predecessor: first label/text or media source, second mappings (absence
removes the first mapping). Dynamic color linking additionally requires an
explicit color:[R,G,B,A] to synchronize its values. Media linking uses
skills/camtasia-project/scripts/media_replacement.py's replacement contract.
Unlink emits one row per binding and keeps current content/mappings.

value PROJECT --group-id ID --index N --spec SPEC requires schema_version:1,
expected (the selected entry), and text/rich/definition for text/appearance or
color:[R,G,B,A] normalized channels for a dynamic source color. Uniform native
rich runs keep all fields and resize UTF-8 byte ranges. No theme is applied here.
Changing mappings or linking with an active AppliedThemeId requires the native
Theme Manager, because storing mappings alone does not apply resources. Labels,
order and visibility can change while that theme remains applied.

Only demonstrated type-0 text, type-1 Callout appearance or {media,property}
dynamic color, and type-2 media bindings are editable. All IDs must identify
unique descendants of the selected Group; AV media binds the wrapper. Mixed,
partial or animated content requires its feature contract and is refused.
No source/editor/media writes occur. Exclusive staged candidates or identical
existing output are supported. Stdout schema_version:1 owner camtasia-quick-
properties includes hashes, changed/written, properties and nativeVerified:false.
Exit 0 success, 1 actionable JSON stderr refusal, 2 JSON stderr CLI usage.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path
import sys
from typing import Any

import annotations
import effects
import hotspots
import project

COLOR_SLOTS = frozenset({"foreground-1", "background-1", "background-2", "accent-1", "accent-2"})
MAPPINGS = {
    0: {"font-family": {"font-1", "font-2"}, "font-color": COLOR_SLOTS},
    1: {"fill": COLOR_SLOTS, "outline": COLOR_SLOTS},
    2: {"logo-1": {"logo-1"}},
}
MEDIA_TYPES = frozenset({"UnifiedMedia", "IMFile", "Callout"})


def selected(doc: dict[str, Any], clip_id: int) -> dict[str, Any]:
    if type(clip_id) is not int:
        raise ValueError("select a numeric clip ID from inspection")
    matches = [
        node
        for _, node in hotspots.clips(doc)
        if type(node.get("id")) is int and node["id"] == clip_id
    ]
    if len(matches) != 1:
        raise ValueError("select a unique native clip ID from inspection")
    return matches[0]


def group(doc: dict[str, Any], clip_id: int) -> dict[str, Any]:
    annotations.require_native(doc)
    owner = selected(doc, clip_id)
    if owner.get("_type") != "Group" or not isinstance(owner.get("attributes"), dict):
        raise ValueError("select a saved native Group with attributes.assetProperties")
    properties(owner)
    return owner


def properties(owner: dict[str, Any]) -> list[dict[str, Any]]:
    attrs = owner.get("attributes")
    rows = attrs.get("assetProperties") if isinstance(attrs, dict) else None
    if not isinstance(rows, list) or any(not isinstance(row, dict) for row in rows):
        raise ValueError("capture a native Group assetProperties array before editing")
    return rows


def descendants(doc: dict[str, Any], owner: dict[str, Any]) -> dict[int, dict[str, Any]]:
    result = {}
    for _, child in hotspots.clips({"timeline": owner}):
        clip_id = child.get("id")
        if type(clip_id) is not int or clip_id in result or selected(doc, clip_id) is not child:
            raise ValueError("repair descendant numeric clip identities before binding properties")
        result[clip_id] = child
    return result


def bindings(
    doc: dict[str, Any], owner: dict[str, Any], row: dict[str, Any]
) -> list[dict[str, Any]]:
    kind, objects = row.get("type"), row.get("objects")
    if (
        type(kind) is not int
        or kind not in MAPPINGS
        or not isinstance(row.get("name"), str)
        or not row["name"].strip()
    ):
        raise ValueError("use a native property type and a nonempty display name")
    if not isinstance(objects, list) or not objects:
        raise ValueError("bind a nonempty native objects array")
    children, result, seen = descendants(doc, owner), [], set()
    shape = type(objects[0])
    for binding in objects:
        if type(binding) is not shape or shape not in (int, dict):
            raise ValueError("preserve uniform integer or dynamic-color binding shapes")
        clip_id = binding if shape is int else binding.get("media")
        prop = None if shape is int else binding.get("property")
        if shape is dict and (not isinstance(prop, str) or not prop):
            raise ValueError("use a captured native dynamic color property name")
        if type(clip_id) is not int or clip_id not in children or (clip_id, prop) in seen:
            raise ValueError(
                "bind unique descendant IDs; source IDs and external clips are not children"
            )
        child = children[clip_id]
        if shape is dict:
            if (
                kind != 1
                or set(binding) != {"media", "property"}
                or not isinstance(prop, str)
                or not prop
            ):
                raise ValueError("use the captured {media,property} dynamic-color binding")
            color_parameters(child, prop)
        elif kind == 0:
            definition = child.get("def")
            if (
                child.get("_type") != "Callout"
                or not isinstance(definition, dict)
                or not isinstance(definition.get("text"), str)
            ):
                raise ValueError("bind text properties to native text Callouts")
        elif kind == 1:
            if child.get("_type") != "Callout" or not isinstance(child.get("def"), dict):
                raise ValueError("bind appearance properties to native Callouts")
        elif child.get("_type") not in MEDIA_TYPES:
            raise ValueError("bind media to a native AV wrapper, image or cleared Callout")
        seen.add((clip_id, prop))
        result.append(child)
    mapping = row.get("themeMappings", {})
    if not isinstance(mapping, dict) or any(
        k not in MAPPINGS[kind] or not isinstance(v, str) or v not in MAPPINGS[kind][k]
        for k, v in mapping.items()
    ):
        raise ValueError("preserve observed native theme mapping keys and slots")
    if shape is dict and mapping.keys() - {"fill"}:
        raise ValueError("use only the captured fill mapping for dynamic colors")
    return result


def color_parameters(child: dict[str, Any], prop: str) -> dict[str, Any]:
    source = child.get("sourceEffect", {})
    params = source.get("parameters") if isinstance(source, dict) else None
    if not isinstance(params, dict) or any(
        prop + "-" + c not in params for c in ("red", "green", "blue", "alpha")
    ):
        raise ValueError("capture the child's native dynamic color components before binding")
    return params


def check_rows(doc: dict[str, Any], owner: dict[str, Any], rows: list[dict[str, Any]]) -> None:
    seen = set()
    for row in rows:
        bindings(doc, owner, row)
        for obj in row["objects"]:
            identity = (row["type"], json.dumps(obj, sort_keys=True))
            if identity in seen:
                raise ValueError(
                    "expose each binding once per property type; use a shared row for links"
                )
            seen.add(identity)


def spec_version(spec: dict[str, Any], keys: set[str], required: set[str]) -> None:
    if (
        type(spec.get("schema_version")) is not int
        or spec["schema_version"] != 1
        or set(spec) - (keys | {"schema_version"})
        or not required <= set(spec)
    ):
        raise ValueError("use schema_version 1 with the documented required spec fields")


def no_active_theme(owner: dict[str, Any]) -> None:
    metadata = owner.get("metadata", {})
    if not isinstance(metadata, dict) or metadata.get("AppliedThemeId"):
        raise ValueError(
            "edit mapped bindings through the native Theme Manager while a theme is applied"
        )


def descriptor(row: dict[str, Any], *, objects: bool = True) -> dict[str, Any]:
    omitted = {"name", "themeMappings"} if objects else {"name", "themeMappings", "objects"}
    return {k: v for k, v in row.items() if k not in omitted}


def set_bindings(doc: dict[str, Any], group_id: int, spec: dict[str, Any]) -> dict[str, Any]:
    spec_version(spec, {"expected", "properties"}, {"expected", "properties"})
    result = copy.deepcopy(doc)
    owner = group(result, group_id)
    old, new = properties(owner), spec["properties"]
    if (
        not isinstance(spec["expected"], list)
        or not isinstance(new, list)
        or any(not isinstance(r, dict) for r in new)
    ):
        raise ValueError("supply complete expected and desired property arrays")
    check_rows(result, owner, old)
    check_rows(result, owner, new)
    if old == new:
        return result
    if old != spec["expected"]:
        raise ValueError("reinspect properties and refresh the stale expected array")
    for row in new:
        same = [r for r in old if r["type"] == row["type"] and r["objects"] == row["objects"]]
        if len(row["objects"]) > 1 and not same:
            raise ValueError("create shared rows with link so bound content is synchronized")
        if same:
            if descriptor(same[0]) != descriptor(row):
                raise ValueError("preserve opaque property descriptors when renaming or mapping")
            if same[0].get("themeMappings") != row.get("themeMappings"):
                no_active_theme(owner)
        elif set(row) - {"type", "name", "objects"}:
            raise ValueError(
                "re-add native bindings without invented mappings or opaque descriptors"
            )
    owner["attributes"]["assetProperties"] = copy.deepcopy(new)
    return result


def row_at(doc: dict[str, Any], group_id: int, index: int) -> tuple[dict[str, Any], dict[str, Any]]:
    owner = group(doc, group_id)
    rows = properties(owner)
    if type(index) is not int or not 0 <= index < len(rows):
        raise ValueError("select a zero-based property index from inspection")
    bindings(doc, owner, rows[index])
    return owner, rows[index]


def set_value(
    doc: dict[str, Any], group_id: int, index: int, spec: dict[str, Any]
) -> dict[str, Any]:
    spec_version(spec, {"expected", "text", "rich", "definition", "color"}, {"expected"})
    result = copy.deepcopy(doc)
    owner, row = row_at(result, group_id, index)
    if row != spec["expected"]:
        raise ValueError("reinspect the selected property and refresh its expected descriptor")
    changes = {k: v for k, v in spec.items() if k not in {"schema_version", "expected"}}
    if not changes:
        raise ValueError("name a bound text, style or color value to change")
    children = bindings(result, owner, row)
    if isinstance(row["objects"][0], dict):
        color = changes.get("color")
        if (
            set(changes) != {"color"}
            or not isinstance(color, list)
            or len(color) != 4
            or any(not 0 <= project.number(c) <= 1 for c in color)
        ):
            raise ValueError("supply color:[R,G,B,A] with four normalized native channels")
        for child, binding in zip(children, row["objects"]):
            parameters = color_parameters(child, binding["property"])
            for channel, value in zip(("red", "green", "blue", "alpha"), color):
                effects.patch_parameter(parameters, binding["property"] + "-" + channel, value)
        return result
    allowed = {0: {"text", "rich"}, 1: {"definition"}, 2: set()}
    if set(changes) - allowed[row["type"]]:
        raise ValueError(
            "use text/rich for Text, definition for appearance, and media_replacement.py for media"
        )
    for child in children:
        result = annotations.edit_annotation(result, child["id"], dict(schema_version=1, **changes))
    return result


def link_rows(
    doc: dict[str, Any], group_id: int, index: int, spec: dict[str, Any], *, unlink: bool = False
) -> dict[str, Any]:
    spec_version(spec, {"expected", "color"}, {"expected"})
    result = copy.deepcopy(doc)
    owner, row = row_at(result, group_id, index)
    rows = properties(owner)
    if rows != spec["expected"]:
        raise ValueError("reinspect properties and refresh the expected array before linking")
    check_rows(result, owner, rows)
    no_active_theme(owner)
    if unlink:
        if "color" in spec:
            raise ValueError("unlink keeps current values; omit color from its spec")
        rows[index : index + 1] = [
            dict(copy.deepcopy(row), objects=[copy.deepcopy(obj)]) for obj in row["objects"]
        ]
        return result
    if index == 0:
        raise ValueError("select a property with an adjacent compatible item above")
    first = rows[index - 1]
    if first["type"] != row["type"] or type(first["objects"][0]) is not type(row["objects"][0]):
        raise ValueError("link adjacent properties of the same native binding kind")
    if descriptor(first, objects=False) != descriptor(row, objects=False):
        raise ValueError(
            "preserve conflicting opaque property descriptors; link through the editor"
        )
    if row["type"] == 1 and type(row["objects"][0]) is int:
        raise ValueError(
            "capture a native Callout appearance link separately; dynamic colors use explicit color"
        )
    if row["type"] != 1 and "color" in spec:
        raise ValueError("supply color only when linking dynamic color bindings")
    children = bindings(result, owner, first)
    donor = copy.deepcopy(children[0])
    first["objects"] += copy.deepcopy(row["objects"])
    if "themeMappings" in row:
        first["themeMappings"] = copy.deepcopy(row["themeMappings"])
    else:
        first.pop("themeMappings", None)
    rows.pop(index)
    check_rows(result, owner, rows)
    if first["type"] == 2:
        import media_replacement

        for child in bindings(result, owner, first):
            if project.number(child.get("mediaStart")) != 0:
                raise ValueError(
                    "use native untrimmed media when linking; replace trims explicitly"
                )
            media_replacement.replace_child(result, child, donor, linking=True)
        return result
    changes = {"text": donor["def"]["text"]} if first["type"] == 0 else {"color": spec.get("color")}
    return set_value(
        result,
        group_id,
        index - 1,
        dict(schema_version=1, expected=copy.deepcopy(first), **changes),
    )


def inventory(doc: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for path, owner in hotspots.clips(doc):
        if owner.get("_type") == "Group":
            properties(owner)
            result.append(
                dict(
                    groupId=owner.get("id"),
                    path=path,
                    properties=copy.deepcopy(properties(owner)),
                    descendants=[
                        dict(clipId=i, ownerType=child.get("_type"))
                        for i, child in descendants(doc, owner).items()
                    ],
                )
            )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = annotations.JsonArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("project", type=Path)
    for name in ("bindings", "value", "link", "unlink"):
        command = commands.add_parser(name)
        command.add_argument("project", type=Path)
        command.add_argument("--group-id", type=int, required=True)
        command.add_argument("--spec", type=Path, required=True)
        command.add_argument("--output", type=Path, required=True)
        if name != "bindings":
            command.add_argument("--index", type=int, required=True)
    args = parser.parse_args(argv)
    try:
        doc, raw = project.load(args.project)
        report: dict[str, Any] = dict(
            schema_version=1,
            owner="camtasia-quick-properties",
            ok=True,
            projectSha256=project.digest(raw),
        )
        if args.command == "inspect":
            report["groups"] = inventory(doc)
        else:
            spec = project.load(args.spec)[0]
            if args.command == "bindings":
                candidate = set_bindings(doc, args.group_id, spec)
            elif args.command == "value":
                candidate = set_value(doc, args.group_id, args.index, spec)
            else:
                candidate = link_rows(
                    doc, args.group_id, args.index, spec, unlink=args.command == "unlink"
                )
            report.update(
                groups=inventory(candidate),
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
