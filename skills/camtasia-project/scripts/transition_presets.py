"""Read Mac 2026.2.4 transition defaults from a caller-selected installation.

Only the observed metadata extension (trailing decimal points outside strings)
is normalized. Project parsing stays strict. Shader strings are never executed,
returned or copied. Unsupported metadata fails discovery rather than dropping
attributes. No resources are written. See transitions.py for staging and CLI.
"""

from __future__ import annotations

import json
import math
from pathlib import Path
import plistlib
import re
from typing import Any
from xml.parsers.expat import ExpatError

import project

COMMON_ATTRIBUTES = dict(
    bypass=False, reverse=False, trivial=False, useAudioPreRoll=True, useVisualPreRoll=True
)
# The first alternative consumes whole strings, including escaped quotes. Only
# number tokens outside those strings can reach the normalization alternative.
METADATA_TOKEN = re.compile(r'"(?:[^"\\]|\\.)*"|(?<![\w.])-?(?:0|[1-9][0-9]*)\.(?=\s*[,}\]])')


def metadata(text: str) -> dict[str, Any]:
    text = METADATA_TOKEN.sub(
        lambda match: match[0] if match[0].startswith('"') else match[0] + "0", text
    )
    value = json.loads(
        text,
        object_pairs_hook=project.unique_object,
        parse_constant=project.invalid_constant,
        parse_float=project.native_float,
    )
    if not isinstance(value, dict) or project.nonfinite_errors(value):
        raise ValueError("use a finite metadata object from the matching installation")
    return value


def defaults(definition: dict[str, Any]) -> dict[str, Any]:
    declarations = definition.get("attributes", [])
    if definition.get("type") != "transition" or not isinstance(declarations, list):
        raise ValueError("select a native transition definition with optional attributes array")
    result: dict[str, Any] = dict(COMMON_ATTRIBUTES)
    declared: set[str] = set()
    for item in declarations:
        if not isinstance(item, dict) or not isinstance(item.get("name"), str) or not item["name"]:
            raise ValueError("inspect the native attribute declaration and its name")
        name = item["name"]
        if name in declared:
            raise ValueError(f"duplicate attribute {name}; use an unmodified native definition")
        declared.add(name)
        kind, value = item.get("type"), item.get("defaultValue")
        if (
            kind == "double"
            and isinstance(value, (int, float))
            and not isinstance(value, bool)
            and math.isfinite(value)
        ):
            additions = {name: float(value)}
        elif kind == "bool" and type(value) is bool:
            additions = {name: value}
        elif kind == "Color" and isinstance(item.get("value"), str):
            color = item["value"]
            if not re.fullmatch(r"[0-9a-fA-F]{6}", color):
                raise ValueError(f"inspect the six-digit RGB metadata for {name}")
            additions = {
                name + "-" + channel: int(color[offset : offset + 2], 16) / 255
                for channel, offset in [("red", 0), ("green", 2), ("blue", 4)]
            }
        else:
            raise ValueError(f"unsupported {kind!r} default for {name}; use a native template")
        if result.keys() & additions.keys():
            raise ValueError(f"attribute collision at {name}; use an unmodified native definition")
        result.update(additions)
    return result


def installed(app: Path) -> list[dict[str, Any]]:
    app = app.expanduser().resolve(strict=True)
    try:
        info = plistlib.loads((app / "Contents/Info.plist").read_bytes())
    except (plistlib.InvalidFileException, ExpatError) as exc:
        raise ValueError(
            f"{app}: repair the app's invalid Info.plist or select another copy"
        ) from exc
    if (
        not isinstance(info, dict)
        or info.get("CFBundleIdentifier") != "com.techsmith.camtasia"
        or info.get("CFBundleShortVersionString") != "2026.2.4"
        or info.get("CFBundleVersion") != "2026.132"
    ):
        raise ValueError("select the verified Camtasia Mac 2026.2.4 (2026.132) installation")
    presets = []
    names: set[str] = set()
    for path in sorted((app / "Contents/Resources/Transitions").glob("*.tsceffect")):
        try:
            definition = metadata(path.read_text(encoding="utf-8"))
            name = definition.get("name")
            if not isinstance(name, str) or not name or name in names:
                raise ValueError("require a unique nonempty internal transition name")
            names.add(name)
            labels = definition.get("localizedName", {})
            presets.append(
                dict(
                    name=name,
                    label=labels.get("en", name) if isinstance(labels, dict) else name,
                    definition=str(path),
                    attributes=defaults(definition),
                )
            )
        except ValueError as exc:
            raise ValueError(f"{path}: {exc}") from exc
    if not presets:
        raise ValueError("no transition definitions found; select the matching native app bundle")
    return presets
