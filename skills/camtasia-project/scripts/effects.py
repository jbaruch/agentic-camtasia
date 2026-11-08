#!/usr/bin/env python3
"""Construct from native templates, inspect, edit or remove visual effects.

CLIENT_FORMATS owns the verified Mac builds. inspect PROJECT lists physical
instances, array positions and optional stable effectIndex tokens. set PROJECT
--clip-id ID --effect NAME [--effect-token TOKEN] --spec SPEC --output CANDIDATE
patches an existing effect; remove uses the same selector without a spec.
add PROJECT --clip-id ID --effect NAME --template-project TEMPLATE
--template-clip-id ID [--template-effect-token TOKEN] --output CANDIDATE
appends the complete saved effect. Linked pairs receive a fresh effectIndex
token; direct owners preserve native metadata without allocating an identity. Construction
requires verified Mac format 10, matching visual owner types/link layout and edit
rate. Timed payloads additionally require matching owner clocks; no animation,
edge, freeze or source clock is inferred or retimed. Resource references remain
unchanged and must resolve separately at the destination. Existing effects,
their order/tokens, audio and unrelated owner data survive. Effect-level reset
and opaque data are copied, including distinct wrapper/video payloads. Selected
owner default-NAME-* reset companions are copied without overwriting conflicting
defaults; last-applied ease defaults need the selected effect as effectApplied.
MediaPath construction uses motion_paths.py to preserve its clip-rotation coupling.
Its editing/removal also use that dedicated helper.
Direct moving recordings, frozen recordings and stitched parents support native
template construction and lifecycle edits. FROZEN_STITCHED_TYPES is restricted to
verified Mac format 10 for all mutations. Root and Group-contained linked moving
recordings support
matching wrapper/video mirrors with complete equal clocks, positive project
rate/inverse speed and a same-source AMFile audio child. Their visual effects
require unique canonical tokens; recorded audio is preserved. Group ancestors
and their clocks/geometry remain unchanged. Complete effect payloads keep the
child's source clock independently of parent placement; no Group retiming is
performed. Linked held, stitched and other containing owner kinds retain
separate contracts. Other feature callers
must explicitly opt into their own verified linked-recording scope.
Stitched parent edits preserve descendants and virtual holds;
no recording/freeze/stitch constructor is inferred. Timed templates retain the
complete matching-clock requirement, including held source-frame selection.

Spec schema_version 1 accepts parameters (existing-name-to-scalar object) and/or
bypassed (boolean). Raw native units/codes are required. Numeric rational input
is converted to the existing scalar kind; static typed double/int/bool parameters
retain their representation, interpolation, bounds and hints. Present numeric
minValue/maxValue bounds are enforced. Enum meaning and cross-parameter/geometry
companions require the feature reference. Prefer a dedicated feature helper
when its contract covers the request. No string/resource changes,
animated/default-less parameter flattening or new parameter names are inferred.

Linked selections resolve to video and require the matching wrapper mirror.
Unique effect names work without tokens in older saves; duplicate names require
an existing canonical decimal token. Tokens are stable identities, not array
positions. Mirror controls/tokens must agree. Metadata may retain role-specific
opaque fields. Audio, sources, IDs, other effects and reset data stay unchanged.
Removal deletes only the selected physical instances, never renumbers other
tokens and is an identical no-op when the selected effect is already absent.

No native project/media is written and no editor is launched. Candidate output
is exclusive or an identical no-op; use project diff/validate/apply and native
verification afterward. Stdout schema_version 1 owner camtasia-effects includes
hashes, inventory, changed/written and nativeVerified false. Exit 0 success,
1 input/I/O refusal, 2 CLI syntax. Errors are JSON on stderr. Structural/type
checks do not prove a new scalar combination renders as intended. Help emits
the same owner/version with ok true and a formatted help string.
"""

from __future__ import annotations

import argparse
import copy
import json
import math
from pathlib import Path
import sys
from typing import Any

import hotspots
import project

CLIENT_FORMATS = {"2025.0.3": "9.0", "2026.2.4": "10.0", "2026.2.5": "10.0"}
CATEGORY = "categoryVisualEffects"
MIRRORED_CONTROLS = (
    "effectName",
    "category",
    "bypassed",
    "parameters",
    "leftEdgeMods",
    "rightEdgeMods",
    "start",
    "duration",
)
FROZEN_STITCHED_TYPES = frozenset({"ScreenIMFile", "StitchedMedia"})
RECORDING_TYPES = FROZEN_STITCHED_TYPES | {"ScreenVMFile"}
LINKED_RECORDING_TYPES = frozenset({"ScreenVMFile"})
CONSTRUCTOR_TYPES = frozenset({"VMFile", "IMFile", "Callout", "Group"})
EFFECT_TYPES = CONSTRUCTOR_TYPES | RECORDING_TYPES
CLOCK_FIELDS = ("start", "duration", "mediaStart", "mediaDuration", "scalar")


class JsonHelpParser(argparse.ArgumentParser):
    def format_help(self) -> str:
        return (
            json.dumps(
                dict(
                    schema_version=1, owner="camtasia-effects", ok=True, help=super().format_help()
                ),
                ensure_ascii=False,
            )
            + "\n"
        )


def require_native(doc: dict[str, Any]) -> None:
    client = doc.get("authoringClientName", {})
    if (
        not isinstance(client, dict)
        or client.get("name") != "Camtasia"
        or client.get("platform") != "Mac"
        or not isinstance(client.get("version"), str)
        or client.get("version") not in CLIENT_FORMATS
        or doc.get("version") != CLIENT_FORMATS[client["version"]]
    ):
        raise ValueError("use a verified Mac authoring build/format from CLIENT_FORMATS")


def effects_of(node: dict[str, Any]) -> list[dict[str, Any]]:
    values = node.get("effects", [])
    if not isinstance(values, list) or any(not isinstance(value, dict) for value in values):
        raise ValueError("inspect the native clip effects array before editing")
    return values


def canonical_token(value: Any) -> str:
    if not isinstance(value, str) or not value.isdecimal() or str(int(value)) != value:
        raise ValueError("select a canonical native effectIndex token from inspection")
    return value


def token_of(effect: dict[str, Any]) -> str | None:
    metadata = effect.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("inspect native effect metadata before editing")
    token = metadata.get("effectIndex")
    return None if token is None else canonical_token(token)


def matching(node: dict[str, Any], name: str, token: str | None) -> list[dict[str, Any]]:
    found = [
        effect
        for effect in effects_of(node)
        if effect.get("effectName") == name and effect.get("category") == CATEGORY
    ]
    if not found and any(effect.get("effectName") == name for effect in effects_of(node)):
        raise ValueError(
            "use this helper only for categoryVisualEffects; read the feature contract"
        )
    if token is not None:
        found = [effect for effect in found if token_of(effect) == token]
    if len(found) > 1:
        raise ValueError("select a unique effectIndex token for repeated visual effect names")
    return found


def targets(
    doc: dict[str, Any],
    clip_id: int,
    name: str,
    token: str | None,
    absent_ok: bool = False,
    *,
    visual_types: frozenset[str] = hotspots.VISUAL_TYPES,
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    """Resolve effect ownership within the calling feature's verified visual types."""
    if not isinstance(name, str) or not name:
        raise ValueError("select an existing visual effect name from inspection")
    if token is not None:
        canonical_token(token)
    path, visual = hotspots.visual_target(doc, clip_id, visual_types=visual_types)
    found = matching(visual, name, token)
    wrappers = [
        node
        for parent, node in hotspots.clips(doc)
        if node.get("_type") == "UnifiedMedia" and path == parent + "/video"
    ]
    if len(wrappers) > 1:
        raise ValueError("repair ambiguous linked visual ownership")
    mirrored = matching(wrappers[0], name, token) if wrappers else []
    if wrappers and bool(found) != bool(mirrored):
        raise ValueError("repair missing linked visual effect mirrors before editing")
    if not found:
        if absent_ok:
            return []
        raise ValueError(
            "select an existing visual effect from inspection; no constructor is inferred"
        )
    effect = found[0]
    if not isinstance(effect.get("parameters"), dict):
        raise ValueError("inspect the selected native effect parameters")
    token_of(effect)
    if not wrappers:
        return [(visual, effect)]
    mirror = mirrored[0]
    if token_of(effect) != token_of(mirror) or any(
        effect.get(key) != mirror.get(key) for key in MIRRORED_CONTROLS
    ):
        raise ValueError("repair conflicting linked visual effect controls or tokens")
    return [(wrappers[0], mirror), (visual, effect)]


def scalar_like(kind: type, value: Any) -> bool | int | float:
    if kind is bool:
        if type(value) is not bool:
            raise ValueError("supply a boolean for the native boolean parameter")
        return value
    number = project.number(value)
    if kind is int:
        if number.denominator != 1:
            raise ValueError("supply an integral value for the native integer parameter")
        return int(number)
    if kind is float:
        try:
            result = float(number)
        except OverflowError as exc:
            raise ValueError("supply a value representable as a finite native double") from exc
        if not math.isfinite(result):
            raise ValueError("supply a finite native double")
        return result
    raise ValueError("use the feature contract for string, resource or structured parameters")


def patch_parameter(parameters: dict[str, Any], name: str, value: Any) -> None:
    if name not in parameters:
        raise ValueError("select an existing native parameter; no field is inferred: " + str(name))
    old = parameters[name]
    if not isinstance(old, dict):
        parameters[name] = scalar_like(type(old), value)
        return
    if "keyframes" in old and not isinstance(old["keyframes"], list):
        raise ValueError(
            "preserve unfamiliar effect keyframe arrays; inspect their native contract"
        )
    if old.get("keyframes"):
        raise ValueError("preserve animated effect parameters; use the feature's curve contract")
    kinds = {"double": float, "int": int, "bool": bool}
    if (
        not isinstance(old.get("type"), str)
        or old["type"] not in kinds
        or "defaultValue" not in old
    ):
        raise ValueError(
            "preserve structured/default-less parameters; inspect their native contract"
        )
    kind = kinds[old["type"]]
    if (kind is bool and type(old["defaultValue"]) is not bool) or (
        kind is not bool and type(old["defaultValue"]) not in (int, float)
    ):
        raise ValueError("inspect the native typed parameter default")
    converted = scalar_like(kind, value)
    if "valueBounds" in old:
        bounds = old["valueBounds"]
        if not isinstance(bounds, dict):
            raise ValueError("inspect unfamiliar native parameter bounds before editing")
        numeric = project.number(int(converted) if type(converted) is bool else converted)
        for limit, minimum in (("minValue", True), ("maxValue", False)):
            if limit in bounds:
                boundary = project.number(
                    int(bounds[limit]) if type(bounds[limit]) is bool else bounds[limit]
                )
                outside = numeric < boundary if minimum else numeric > boundary
                if outside:
                    raise ValueError("choose a value inside the native parameter bounds")
    old["defaultValue"] = converted


def edit_effect(
    doc: dict[str, Any], clip_id: int, name: str, spec: dict[str, Any], *, token: str | None = None
) -> dict[str, Any]:
    require_native(doc)
    if name == "MediaPath":
        raise ValueError("edit Motion Path with motion_paths.py to preserve rotation coupling")
    if (
        not isinstance(spec, dict)
        or not {"schema_version"} <= set(spec)
        or set(spec) - {"schema_version", "parameters", "bypassed"}
        or type(spec["schema_version"]) is not int
        or spec["schema_version"] != 1
    ):
        raise ValueError("supply effect schema_version 1 with parameters and/or bypassed")
    parameters = spec.get("parameters", {})
    if not isinstance(parameters, dict) or (not parameters and "bypassed" not in spec):
        raise ValueError("supply existing native parameters or a boolean bypass change")
    if "bypassed" in spec and type(spec["bypassed"]) is not bool:
        raise ValueError("supply a boolean effect bypass")
    result = copy.deepcopy(doc)
    constructor_owners(
        result, clip_id, visual_types=EFFECT_TYPES, linked_recordings=True, grouped_recordings=True
    )
    for _, effect in targets(result, clip_id, name, token, visual_types=EFFECT_TYPES):
        for key, value in parameters.items():
            patch_parameter(effect["parameters"], key, value)
        if "bypassed" in spec:
            if type(effect.get("bypassed")) is not bool:
                raise ValueError("inspect the native bypass representation before editing")
            effect["bypassed"] = spec["bypassed"]
    return result


def remove_effect(
    doc: dict[str, Any], clip_id: int, name: str, *, token: str | None = None
) -> dict[str, Any]:
    require_native(doc)
    if name == "MediaPath":
        raise ValueError("remove Motion Path with motion_paths.py to preserve rotation coupling")
    result = copy.deepcopy(doc)
    constructor_owners(
        result, clip_id, visual_types=EFFECT_TYPES, linked_recordings=True, grouped_recordings=True
    )
    for owner, effect in targets(
        result, clip_id, name, token, absent_ok=True, visual_types=EFFECT_TYPES
    ):
        effects_of(owner).remove(effect)
    return result


def constructor_owners(
    doc: dict[str, Any],
    clip_id: int,
    *,
    visual_types: frozenset[str] = CONSTRUCTOR_TYPES,
    linked_recordings: bool = False,
    grouped_recordings: bool = False,
) -> list[dict[str, Any]]:
    """Select general-operation owners; other feature callers retain their own scope."""
    path, visual = hotspots.visual_target(doc, clip_id, visual_types=visual_types)
    if visual.get("_type") in FROZEN_STITCHED_TYPES and not project.is_native_format10(doc):
        raise ValueError("edit frozen/stitched effects with verified Mac format-10 native evidence")
    wrappers = [
        (parent, node)
        for parent, node in hotspots.clips(doc)
        if node.get("_type") == "UnifiedMedia" and path == parent + "/video"
    ]
    if len(wrappers) > 1:
        raise ValueError("repair ambiguous linked visual ownership before construction")
    if wrappers and visual.get("_type") in RECORDING_TYPES:
        if not linked_recordings or visual.get("_type") not in LINKED_RECORDING_TYPES:
            raise ValueError("capture native linked recording effect mirrors before editing")
        wrapper_path, wrapper = wrappers[0]
        if not project.is_native_format10(doc):
            raise ValueError("use verified Mac format-10 linked recording effect evidence")
        ancestors = [
            node for parent, node in hotspots.clips(doc) if wrapper_path.startswith(parent + "/")
        ]
        if len(project.scene_tracks(doc)) != 1 or (
            ancestors
            and (not grouped_recordings or any(node.get("_type") != "Group" for node in ancestors))
        ):
            raise ValueError(
                "select a root linked moving recording or a verified Group-contained effect owner"
            )
        audio = wrapper.get("audio")
        if (
            not isinstance(audio, dict)
            or audio.get("_type") != "AMFile"
            or type(visual.get("src")) is not int
            or type(audio.get("src")) is not int
            or audio["src"] != visual["src"]
        ):
            raise ValueError("capture native linked recording AMFile audio with a shared source")
        if any(field not in owner for field in CLOCK_FIELDS for owner in (wrapper, visual)):
            raise ValueError("capture complete linked recording wrapper/video clocks")
        if any(
            project.number(wrapper[field]) != project.number(visual[field])
            for field in CLOCK_FIELDS
        ):
            raise ValueError("repair conflicting linked recording wrapper/video clocks")
        if project.number(doc.get("editRate")) <= 0 or project.number(visual["scalar"]) <= 0:
            raise ValueError("repair positive project rate and linked recording inverse speed")
        for owner in (wrapper, visual):
            tokens = [token_of(effect) for effect in effects_of(owner)]
            if None in tokens or len(tokens) != len(set(tokens)):
                raise ValueError("capture unique native linked recording visual effectIndex tokens")
    return [*(node for _, node in wrappers), visual]


def timed_payload(value: Any) -> bool:
    """Detect stored timing without interpreting parameter-specific clock units."""
    if isinstance(value, dict):
        if any(key in value for key in ("start", "duration")) or any(
            key in value and value[key] != []
            for key in ("keyframes", "leftEdgeMods", "rightEdgeMods")
        ):
            return True
        return any(timed_payload(child) for child in value.values())
    if isinstance(value, list):
        return any(timed_payload(child) for child in value)
    return False


def next_constructor_token(owners: list[dict[str, Any]]) -> str:
    nodes = list(owners)
    if len(owners) == 2:
        audio = owners[0].get("audio")
        if not isinstance(audio, dict):
            raise ValueError("repair the linked audio child before constructing visual effects")
        nodes.append(audio)
    observed = []
    for owner in nodes:
        seen: set[str] = set()
        for effect in effects_of(owner):
            token = token_of(effect)
            if token is None or token in seen:
                raise ValueError("capture unique native effectIndex bindings before adding effects")
            seen.add(token)
            observed.append(int(token))
    return str(max(observed, default=-1) + 1)


def owner_defaults(owner: dict[str, Any], name: str) -> dict[str, Any]:
    metadata = owner.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("inspect native owner metadata before copying reset companions")
    selected = {k: v for k, v in metadata.items() if k.startswith("default-" + name + "-")}
    for key in ("default-easeIn", "default-easeOut"):
        if key in metadata:
            if metadata.get("effectApplied") != name:
                raise ValueError(
                    "capture this effect as the last native applied effect to identify ease defaults"
                )
            selected[key] = metadata[key]
    if metadata.get("effectApplied") == name:
        selected["effectApplied"] = name
    return selected


def add_effect(
    doc: dict[str, Any],
    clip_id: int,
    template: dict[str, Any],
    template_clip_id: int,
    name: str,
    *,
    template_token: str | None = None,
) -> dict[str, Any]:
    require_native(doc)
    require_native(template)
    if not project.is_native_format10(doc):
        raise ValueError("construct effects using a verified Mac format-10 contract")
    if template.get("authoringClientName") != doc.get("authoringClientName"):
        raise ValueError("select a native effect template from the same authoring build")
    if name == "MediaPath":
        raise ValueError(
            "construct Motion Path with motion_paths.py to preserve its clip rotation companion"
        )
    if project.number(doc.get("editRate")) <= 0 or project.number(
        doc.get("editRate")
    ) != project.number(template.get("editRate")):
        raise ValueError("select a same-build template with the destination project edit rate")
    source_owners = constructor_owners(
        template,
        template_clip_id,
        visual_types=EFFECT_TYPES,
        linked_recordings=True,
        grouped_recordings=True,
    )
    source = targets(template, template_clip_id, name, template_token, visual_types=EFFECT_TYPES)
    result = copy.deepcopy(doc)
    destination = constructor_owners(
        result, clip_id, visual_types=EFFECT_TYPES, linked_recordings=True, grouped_recordings=True
    )
    if len(source_owners) != len(destination) or any(
        a.get("_type") != b.get("_type") for a, b in zip(source_owners, destination)
    ):
        raise ValueError("select matching native visual owner types and linked mirror layout")
    if any(timed_payload(effect) for _, effect in source):
        for a, b in zip(source_owners, destination):
            for key in CLOCK_FIELDS:
                if key not in a or key not in b or project.number(a[key]) != project.number(b[key]):
                    raise ValueError(
                        "preserve timed effect payloads with matching complete owner clocks; use the feature helper for retiming"
                    )
    token = next_constructor_token(destination) if len(destination) == 2 else None
    for (source_owner, native), owner in zip(source, destination):
        companions = owner_defaults(source_owner, name)
        metadata = owner.get("metadata", {})
        if not isinstance(metadata, dict):
            raise ValueError("inspect the destination owner's metadata before construction")
        if any(
            k != "effectApplied" and k in metadata and metadata[k] != v
            for k, v in companions.items()
        ):
            raise ValueError(
                "preserve conflicting existing reset defaults; apply this preset through the native editor"
            )
        effect = copy.deepcopy(native)
        if token is not None:
            effect.setdefault("metadata", {})["effectIndex"] = token
        owner.setdefault("effects", [])
        effects_of(owner).append(effect)
        if companions:
            metadata = owner.setdefault("metadata", {})
            for key, value in companions.items():
                if key == "effectApplied":
                    metadata[key] = value
                else:
                    metadata.setdefault(key, copy.deepcopy(value))
    return result


def inventory(doc: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for path, owner in hotspots.clips(doc):
        for index, effect in enumerate(effects_of(owner)):
            if effect.get("category") == CATEGORY:
                result.append(
                    {
                        "clipId": owner.get("id"),
                        "ownerType": owner.get("_type"),
                        "path": path + f"/effects/{index}",
                        "arrayPosition": index,
                        "effectToken": token_of(effect),
                        "effect": effect,
                    }
                )
    return result


def main(argv: list[str] | None = None) -> int:
    parser = JsonHelpParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("project", type=Path)
    for name in ("add", "set", "remove"):
        command = commands.add_parser(name)
        command.add_argument("project", type=Path)
        command.add_argument("--clip-id", type=int, required=True)
        command.add_argument("--effect", required=True)
        if name != "add":
            command.add_argument("--effect-token")
        command.add_argument("--output", type=Path, required=True)
        if name == "set":
            command.add_argument("--spec", type=Path, required=True)
        if name == "add":
            command.add_argument("--template-project", type=Path, required=True)
            command.add_argument("--template-clip-id", type=int, required=True)
            command.add_argument("--template-effect-token")
    args = parser.parse_args(argv)
    try:
        doc, raw = project.load(args.project)
        report = {
            "schema_version": 1,
            "owner": "camtasia-effects",
            "ok": True,
            "projectSha256": project.digest(raw),
        }
        if args.command == "inspect":
            report["effects"] = inventory(doc)
        else:
            if args.command == "add":
                candidate = add_effect(
                    doc,
                    args.clip_id,
                    project.load(args.template_project)[0],
                    args.template_clip_id,
                    args.effect,
                    template_token=args.template_effect_token,
                )
            elif args.command == "set":
                candidate = edit_effect(
                    doc,
                    args.clip_id,
                    args.effect,
                    project.load(args.spec)[0],
                    token=args.effect_token,
                )
            else:
                candidate = remove_effect(doc, args.clip_id, args.effect, token=args.effect_token)
            report.update(
                effects=inventory(candidate),
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
