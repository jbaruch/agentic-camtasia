#!/usr/bin/env python3
"""Construct from native templates and edit existing Mac behavior phase controls.

inspect PROJECT lists GenericBehaviorEffect instances and stable optional tokens.
add PROJECT --clip-id ID --behavior NAME --template-project TEMPLATE
--template-clip-id ID [--template-effect-token TOKEN] --output CANDIDATE copies
one complete same-build saved behavior. It requires matching visual owner kinds,
linked layout, project rate and all complete owner clocks. No outer interval or
phase retiming is inferred. Linked copies receive a fresh stable effectIndex;
direct copies retain native metadata and refuse ambiguous repeated identities.
Selected reset companions are copied without overwriting conflicting defaults.
The added behavior becomes the wrapper/direct owner's last-applied name.

set PROJECT --clip-id ID --behavior NAME [--effect-token TOKEN] --spec SPEC
--output CANDIDATE edits existing phase timing/static parameters and/or bypass.
remove uses that selector without a spec and leaves all other tokens unchanged.
Spec schema_version 1 accepts bypassed (boolean) and phases (in/center/out maps).
Each phase map accepts attributes and/or parameters, naming existing fields.
TICK_ATTRIBUTES are entered as rational seconds and compiled to exact project
ticks. secondsPerLoop is positive rational seconds; numberOfLoops is an integer
at least -1 (the observed indefinite-loop sentinel). No UI speed percentage or
per-character total duration is inferred. Other selectors, dimensionless overlap,
phase identifiers, structured/animated parameters and unrelated data survive.
Only named supported timing attributes and static scalar parameters are patched.
Inactive none phases are preserved and cannot be edited into active phases.

NAMES and PHASE_NAMES own the exact observed outer/phase identifiers, separately.
Edits require Mac 2026.2.4/format 10 and visual owners in OWNERS.
Mirrored controls/tokens and complete owner clocks must agree; audio is untouched.
Direct moving/frozen recordings and stitched parents retain cursor data, child
clocks, virtual holds and source selection. Their complete native behavior
intervals are copied, not retimed: moving/stitched outer origins can follow
source in-points, while held recordings use local zero. No recording/freeze/
stitch constructor or linked recording behavior mirror is inferred. Hidden
stitched descendants are refused; select their independently verified parent.
A redundant static-double zero-point frame reproduces a 2025 parser hazard;
this helper also refuses that unsupported shape in a 2026 template, without
claiming a 2026 crash. No vendor preset, shader, media or resource is copied.

Existing native owner reset fields survive. A first entry/exit duration edit
seeds its observed default-Speed-NAME companion from the prior duration; edits
with differing unrecorded phase defaults refuse instead of choosing one reset.
Other attribute controls do not manufacture reset descriptors; retain native
reset companions when the requested reset behavior matters.

No editor/input/media is written. Staging is exclusive or an identical no-op;
follow project diff/validate/apply and matching native save/reopen/export.
JSON stdout schema_version 1 owner camtasia-behaviors reports hashes, inventory,
changed/written and nativeVerified false. Exit 0 success, 1 input/I/O refusal,
2 CLI syntax (JSON stderr). --help retains plaintext stdout. Native acceptance
and correct per-glyph layout remain separate from these structural checks.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any, NoReturn

import effects
import hotspots
import project

OWNERS = frozenset(
    {"VMFile", "IMFile", "Callout", "Group", "ScreenVMFile", "ScreenIMFile", "StitchedMedia"}
)

NAMES = frozenset(
    {
        "drifting",
        "explode",
        "fade",
        "flyIn",
        "jumpAndFall",
        "popUp",
        "pulsating",
        "reveal",
        "scale",
        "shifting",
        "sliding",
        "tremble",
        "wiggle",
    }
)
PHASE_NAMES = {
    "in": frozenset(
        {
            "drifting",
            "implode",
            "fadeIn",
            "flyIn",
            "bounceIn",
            "hinge",
            "grow",
            "reveal",
            "shifting",
            "sliding",
            "none",
        }
    ),
    "center": frozenset(
        {
            "drifting",
            "none",
            "jump",
            "popUp",
            "pulsate",
            "reveal",
            "shifting",
            "fading",
            "tremble",
            "wiggle",
        }
    ),
    "out": frozenset(
        {
            "drifting",
            "explode",
            "fadeOut",
            "flyOut",
            "drop",
            "hinge",
            "shrink",
            "reveal",
            "shifting",
            "sliding",
            "none",
        }
    ),
}
TICK_ATTRIBUTES = frozenset(
    {"suggestedDurationPerCharacter", "offsetBetweenCharacters", "delayBetweenLoops"}
)
PHASE_ATTRIBUTES = {
    "in": frozenset({"suggestedDurationPerCharacter", "offsetBetweenCharacters"}),
    "center": frozenset(
        {"offsetBetweenCharacters", "secondsPerLoop", "numberOfLoops", "delayBetweenLoops"}
    ),
    "out": frozenset({"suggestedDurationPerCharacter", "offsetBetweenCharacters"}),
}
CONTROLS = ("_type", "effectName", "bypassed", "start", "duration", "in", "center", "out")


class JsonArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> NoReturn:
        self.exit(2, json.dumps(dict(ok=False, error=message), ensure_ascii=False) + "\n")


def require_native(doc: dict[str, Any]) -> None:
    if doc.get("version") != "10.0" or doc.get("authoringClientName") != hotspots.NATIVE_CLIENT:
        raise ValueError("use the verified Camtasia Mac 2026.2.4 format-10 behavior contract")
    if project.number(doc.get("editRate")) <= 0:
        raise ValueError("repair the positive project edit rate before behavior edits")


def validate_behavior(behavior: dict[str, Any]) -> None:
    name = behavior.get("effectName")
    if (
        not isinstance(name, str)
        or name not in NAMES
        or behavior.get("_type") != "GenericBehaviorEffect"
    ):
        raise ValueError(
            "select an observed outer behavior from NAMES; phase names are not outer names"
        )
    if type(behavior.get("bypassed")) is not bool:
        raise ValueError("inspect the native behavior bypass representation")
    if project.number(behavior.get("start")) < 0 or project.number(behavior.get("duration")) <= 0:
        raise ValueError("capture a positive native behavior interval before editing")
    effects.token_of(behavior)
    for phase, names in PHASE_NAMES.items():
        data = behavior.get(phase)
        if not isinstance(data, dict) or not isinstance(data.get("attributes"), dict):
            raise ValueError(
                "preserve complete native behavior phases and their attributes: " + phase
            )
        if (
            not isinstance(data["attributes"].get("name"), str)
            or data["attributes"]["name"] not in names
        ):
            raise ValueError(
                "select an observed native phase identifier from PHASE_NAMES: " + phase
            )
        parameters = data.get("parameters", {})
        if not isinstance(parameters, dict):
            raise ValueError("inspect the native behavior phase parameters: " + phase)
        for parameter in parameters.values():
            if not isinstance(parameter, dict) or parameter.get("type") != "double":
                continue
            frames = parameter.get("keyframes")
            if isinstance(frames, list) and len(frames) == 1 and isinstance(frames[0], dict):
                frame = frames[0]
                if (
                    frame.get("time") == 0
                    and frame.get("duration", 0) == 0
                    and frame.get("endTime", 0) == 0
                    and frame.get("value") == parameter.get("defaultValue")
                ):
                    raise ValueError(
                        "capture native phase controls without the redundant static zero-point frame; this shape reproduces the 2025 parser hazard"
                    )


def matching(owner: dict[str, Any], name: str, token: str | None) -> list[dict[str, Any]]:
    found = [
        value
        for value in effects.effects_of(owner)
        if value.get("_type") == "GenericBehaviorEffect" and value.get("effectName") == name
    ]
    if token is not None:
        found = [value for value in found if effects.token_of(value) == token]
    if len(found) > 1:
        raise ValueError("select a unique effectIndex token for repeated behavior names")
    return found


def behavior_owners(doc: dict[str, Any], clip_id: int) -> list[dict[str, Any]]:
    """Resolve verified owners for both template selection and lifecycle operations."""
    path, _ = hotspots.visual_target(doc, clip_id, visual_types=OWNERS)
    if any(
        ancestor.get("_type") == "StitchedMedia" and path.startswith(parent_path + "/")
        for parent_path, ancestor in hotspots.clips(doc)
    ):
        raise ValueError("select the stitched parent; capture independent child behavior ownership")
    return effects.constructor_owners(doc, clip_id, visual_types=OWNERS)


def targets(
    doc: dict[str, Any], clip_id: int, name: str, token: str | None, *, absent_ok: bool = False
) -> list[tuple[dict[str, Any], dict[str, Any]]]:
    require_native(doc)
    if not isinstance(name, str) or name not in NAMES:
        raise ValueError(
            "select a native outer behavior from NAMES; no phase-name constructor is inferred"
        )
    if token is not None:
        effects.canonical_token(token)
    owners = behavior_owners(doc, clip_id)
    found = [matching(owner, name, token) for owner in owners]
    if len({bool(values) for values in found}) != 1:
        raise ValueError("repair missing linked behavior mirrors before editing")
    if not found[-1]:
        if absent_ok:
            return []
        raise ValueError(
            "select an existing native behavior from inspection or add from a native template"
        )
    pairs = [(owner, values[0]) for owner, values in zip(owners, found)]
    for _, behavior in pairs:
        validate_behavior(behavior)
    if len(pairs) == 2:
        first, second = pairs[0][1], pairs[1][1]
        if effects.token_of(first) != effects.token_of(second) or any(
            first.get(key) != second.get(key) for key in CONTROLS
        ):
            raise ValueError("repair conflicting linked behavior controls or effectIndex tokens")
        for field in effects.CLOCK_FIELDS:
            if project.number(owners[0].get(field)) != project.number(owners[1].get(field)):
                raise ValueError("repair conflicting complete linked visual owner clocks")
    return pairs


def reset_companions(owner: dict[str, Any], name: str) -> dict[str, Any]:
    metadata = owner.get("metadata", {})
    if not isinstance(metadata, dict):
        raise ValueError("inspect native owner metadata before copying behavior reset values")
    values = {
        key: value
        for key, value in metadata.items()
        if key.startswith("default-") and key.endswith("-" + name)
    }
    return values


def add_behavior(
    doc: dict[str, Any],
    clip_id: int,
    template: dict[str, Any],
    template_clip_id: int,
    name: str,
    *,
    template_token: str | None = None,
) -> dict[str, Any]:
    require_native(doc)
    source = targets(template, template_clip_id, name, template_token)
    if project.number(doc["editRate"]) != project.number(template["editRate"]):
        raise ValueError("select a native template with the destination project edit rate")
    result = copy.deepcopy(doc)
    destination = behavior_owners(result, clip_id)
    if len(source) != len(destination) or any(
        a.get("_type") != b.get("_type") for (a, _), b in zip(source, destination)
    ):
        raise ValueError("select matching native visual owner kinds and linked layouts")
    for (original, _), owner in zip(source, destination):
        if any(
            project.number(original.get(field)) != project.number(owner.get(field))
            for field in effects.CLOCK_FIELDS
        ):
            raise ValueError(
                "select matching complete owner clocks; behavior/phase retiming is not inferred"
            )
    token = effects.next_constructor_token(destination) if len(destination) == 2 else None
    if len(destination) == 1:
        source_token = effects.token_of(source[0][1])
        repeated = [
            value
            for value in effects.effects_of(destination[0])
            if value.get("_type") == "GenericBehaviorEffect" and value.get("effectName") == name
        ]
        if repeated and (
            source_token is None
            or any(effects.token_of(value) in (None, source_token) for value in repeated)
        ):
            raise ValueError(
                "capture unique native effectIndex tokens before repeating a direct behavior; add it through the editor"
            )
    for owner_index, ((original, native), owner) in enumerate(zip(source, destination)):
        companions = reset_companions(original, name)
        metadata = owner.get("metadata", {})
        if not isinstance(metadata, dict) or any(
            key in metadata and metadata[key] != value for key, value in companions.items()
        ):
            raise ValueError(
                "preserve conflicting destination reset metadata; apply this behavior natively"
            )
        behavior = copy.deepcopy(native)
        if token is not None:
            behavior.setdefault("metadata", {})["effectIndex"] = token
        effects.effects_of(owner)
        owner.setdefault("effects", []).append(behavior)
        if companions or owner_index == 0:
            metadata = owner.setdefault("metadata", {})
            if owner_index == 0:
                metadata["effectApplied"] = name
            for key, value in companions.items():
                metadata.setdefault(key, copy.deepcopy(value))
    return result


def attribute_value(name: str, value: Any, rate: Any) -> int | str:
    number = project.number(value)
    if name == "numberOfLoops":
        if number.denominator != 1 or number < -1:
            raise ValueError("supply an integral loop count at least -1")
        return int(number)
    if number < 0 or (name == "secondsPerLoop" and number == 0):
        raise ValueError("supply nonnegative phase seconds and a positive secondsPerLoop")
    if name in TICK_ATTRIBUTES:
        ticks = number * project.number(rate)
        if ticks.denominator != 1:
            raise ValueError("choose phase seconds that map to exact native project ticks")
        return int(ticks)
    return int(number) if number.denominator == 1 else str(number)


def edit_behavior(
    doc: dict[str, Any], clip_id: int, name: str, spec: dict[str, Any], *, token: str | None = None
) -> dict[str, Any]:
    if (
        not isinstance(spec, dict)
        or not {"schema_version"} <= set(spec)
        or set(spec) - {"schema_version", "phases", "bypassed"}
        or type(spec["schema_version"]) is not int
        or spec["schema_version"] != 1
    ):
        raise ValueError("supply behavior schema_version 1 with phases and/or bypassed")
    phases = spec.get("phases", {})
    if (
        not isinstance(phases, dict)
        or set(phases) - set(PHASE_NAMES)
        or (not phases and "bypassed" not in spec)
    ):
        raise ValueError("supply existing in/center/out phase controls or a bypass change")
    if "bypassed" in spec and type(spec["bypassed"]) is not bool:
        raise ValueError("supply a boolean behavior bypass")
    result = copy.deepcopy(doc)
    for owner_index, (owner, behavior) in enumerate(targets(result, clip_id, name, token)):
        speed_defaults = []
        for phase, change in phases.items():
            if (
                not isinstance(change, dict)
                or not change
                or set(change) - {"attributes", "parameters"}
            ):
                raise ValueError("supply each phase with attributes and/or static parameters")
            data = behavior[phase]
            if data["attributes"]["name"] == "none":
                raise ValueError(
                    "preserve inactive none phases; capture the requested active phase natively"
                )
            attributes, parameters = change.get("attributes", {}), change.get("parameters", {})
            if (
                not isinstance(attributes, dict)
                or not isinstance(parameters, dict)
                or not (attributes or parameters)
                or set(attributes) - PHASE_ATTRIBUTES[phase]
            ):
                raise ValueError(
                    "supply supported phase timing attributes and/or static parameters"
                )
            for key, value in attributes.items():
                if key not in data["attributes"]:
                    raise ValueError(
                        "capture the existing native phase timing field before editing: " + key
                    )
                converted = attribute_value(key, value, result["editRate"])
                if key == "suggestedDurationPerCharacter" and converted != data["attributes"][key]:
                    previous = project.number(data["attributes"][key])
                    if previous.denominator != 1 or previous < 0:
                        raise ValueError(
                            "inspect the existing native duration before recording reset ticks"
                        )
                    speed_defaults.append(str(previous.numerator))
                data["attributes"][key] = converted
            if parameters:
                if not isinstance(data.get("parameters"), dict):
                    raise ValueError("capture existing native phase parameters before editing")
                for key, value in parameters.items():
                    effects.patch_parameter(data["parameters"], key, value)
        if speed_defaults and owner_index == 0:
            metadata = owner.setdefault("metadata", {})
            if not isinstance(metadata, dict):
                raise ValueError("inspect native reset metadata before editing phase duration")
            key = "default-Speed-" + name
            if key not in metadata:
                if len(set(speed_defaults)) != 1:
                    raise ValueError(
                        "capture native reset defaults for differing entry/exit durations before editing both"
                    )
                metadata[key] = speed_defaults[0]
        if "bypassed" in spec:
            behavior["bypassed"] = spec["bypassed"]
    return result


def remove_behavior(
    doc: dict[str, Any], clip_id: int, name: str, *, token: str | None = None
) -> dict[str, Any]:
    result = copy.deepcopy(doc)
    for owner, behavior in targets(result, clip_id, name, token, absent_ok=True):
        effects.effects_of(owner).remove(behavior)
    return result


def inventory(doc: dict[str, Any]) -> list[dict[str, Any]]:
    rows = []
    for path, owner in hotspots.clips(doc):
        for index, behavior in enumerate(effects.effects_of(owner)):
            if behavior.get("_type") == "GenericBehaviorEffect":
                rows.append(
                    dict(
                        clipId=owner.get("id"),
                        ownerType=owner.get("_type"),
                        effectIndex=index,
                        effectToken=effects.token_of(behavior),
                        path=project.pointer(project.pointer(path, "effects"), index),
                        behavior=behavior,
                    )
                )
    return rows


def main(argv: list[str] | None = None) -> int:
    parser = JsonArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("project", type=Path)
    for name in ["add", "set", "remove"]:
        command = commands.add_parser(name)
        command.add_argument("project", type=Path)
        command.add_argument("--clip-id", type=int, required=True)
        command.add_argument("--behavior", required=True)
        command.add_argument("--output", type=Path, required=True)
        if name == "add":
            command.add_argument("--template-project", type=Path, required=True)
            command.add_argument("--template-clip-id", type=int, required=True)
            command.add_argument("--template-effect-token")
        else:
            command.add_argument("--effect-token")
        if name == "set":
            command.add_argument("--spec", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        doc, raw = project.load(args.project)
        report: dict[str, Any] = dict(
            schema_version=1, owner="camtasia-behaviors", ok=True, projectSha256=project.digest(raw)
        )
        if args.command == "inspect":
            report["behaviors"] = inventory(doc)
        else:
            if args.command == "add":
                candidate = add_behavior(
                    doc,
                    args.clip_id,
                    project.load(args.template_project)[0],
                    args.template_clip_id,
                    args.behavior,
                    template_token=args.template_effect_token,
                )
            elif args.command == "set":
                candidate = edit_behavior(
                    doc,
                    args.clip_id,
                    args.behavior,
                    project.load(args.spec)[0],
                    token=args.effect_token,
                )
            else:
                candidate = remove_behavior(
                    doc, args.clip_id, args.behavior, token=args.effect_token
                )
            report.update(
                behaviors=inventory(candidate),
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
