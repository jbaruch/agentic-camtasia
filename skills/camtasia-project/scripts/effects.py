#!/usr/bin/env python3
"""Inspect, set static parameters, bypass or remove existing native visual effects.

CLIENT_FORMATS owns the verified Mac builds. inspect PROJECT lists physical
instances, array positions and optional stable effectIndex tokens. set PROJECT
--clip-id ID --effect NAME [--effect-token TOKEN] --spec SPEC --output CANDIDATE
patches an existing effect; remove uses the same selector without a spec.

Spec schema_version 1 accepts parameters (existing-name-to-scalar object) and/or
bypassed (boolean). Raw native units/codes are required. Numeric rational input
is converted to the existing scalar kind; static typed double/int/bool parameters
retain their representation, interpolation, bounds and hints. Present numeric
minValue/maxValue bounds are enforced. Enum meaning and cross-parameter/geometry
companions require the feature reference. Prefer a dedicated feature helper
when its contract covers the request. No constructors, string/resource changes,
animated/default-less parameter flattening or new parameter names are inferred.

Linked selections resolve to video and require the matching wrapper mirror.
Unique effect names work without tokens in older saves; duplicate names require
an existing canonical decimal token. Tokens are stable identities, not array
positions. Mirror controls/tokens must agree. Metadata may retain role-specific
opaque fields. Audio, sources, IDs, other effects and reset data stay unchanged.
Removal deletes only both selected instances, never renumbers other tokens and
is an identical no-op if both instances are already absent.

No native project/media is written and no editor is launched. Candidate output
is exclusive or an identical no-op; use project diff/validate/apply and native
verification afterward. Stdout schema_version 1 owner camtasia-effects includes
hashes, inventory, changed/written and nativeVerified false. Exit 0 success,
1 input/I/O refusal, 2 CLI syntax. Errors are JSON on stderr. Structural/type
checks do not prove a new scalar combination renders as intended.
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

CLIENT_FORMATS = {"2025.0.3": "9.0", "2026.2.4": "10.0"}
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
    doc: dict[str, Any], clip_id: int, name: str, token: str | None, absent_ok: bool = False
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    if not isinstance(name, str) or not name:
        raise ValueError("select an existing visual effect name from inspection")
    if token is not None:
        canonical_token(token)
    path, visual = hotspots.visual_target(doc, clip_id)
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
    for _, effect in targets(result, clip_id, name, token):
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
    result = copy.deepcopy(doc)
    for owner, effect in targets(result, clip_id, name, token, absent_ok=True):
        effects_of(owner).remove(effect)
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
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("project", type=Path)
    for name in ("set", "remove"):
        command = commands.add_parser(name)
        command.add_argument("project", type=Path)
        command.add_argument("--clip-id", type=int, required=True)
        command.add_argument("--effect", required=True)
        command.add_argument("--effect-token")
        command.add_argument("--output", type=Path, required=True)
        if name == "set":
            command.add_argument("--spec", type=Path, required=True)
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
            candidate = (
                edit_effect(
                    doc,
                    args.clip_id,
                    args.effect,
                    project.load(args.spec)[0],
                    token=args.effect_token,
                )
                if args.command == "set"
                else remove_effect(doc, args.clip_id, args.effect, token=args.effect_token)
            )
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
