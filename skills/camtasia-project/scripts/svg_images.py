#!/usr/bin/env python3
"""Inspect SVG image references and stage explicitly selected PNG embedding.

CLI: inspect SOURCE [--require-embedded]; embed SOURCE --expected-sha256 HASH
(--image-id ID | --image-index N) --image PNG --output CANDIDATE.
Image indices are zero-based document-order SVG image elements, not project IDs.
Only selected existing href attribute value bytes change. UTF-8 SVG namespaces,
prefixes, whitespace, quoting, numeric precision, comments, geometry, unknown
elements, other references and font declarations remain byte-for-byte intact.
Equivalent href/xlink:href pairs change together; conflicting pairs, missing
references, duplicate IDs, dynamic hrefs, active content and incompatible MIME
hints refuse embedding. No stored URL/file reference is opened or executed.

SVG parsing requires namespace-qualified SVG and UTF-8/ASCII source bytes;
DTDs/custom entities and other encodings refuse. This is not a full SVG validator.
PNG checks reuse lottie_images' container-only contract without decoding pixels.
SVG viewport geometry is preserved independently of PNG physical dimensions.
Fonts, stylesheets, other references, scripts and general dependency closure
remain unresolved. The image-only gate covers static SVG image hrefs, not full
rendering, font resolution or arbitrary SVG resources. Native verification is
always separate. Existing native evidence targets Mac 2026.2.4/format 10.

Stdout schema 1, owner camtasia-svg-images: sourceSha256, images, duplicateIds,
otherReferences, font/style declarations, active/dynamic indices, imageAssetsEmbedded
and nativeVerified:false. Embed adds PNG/candidate hashes, changed/written and
the selected image identity. No continuity state is read. Readers recheck hashes.
Only a separate exclusive candidate is written; identical reruns are no-ops.
Source/image aliases, output symlinks and differing occupied candidates refuse.
Exit 0 success, 1 refusal/unmet image gate, 2 argument syntax; errors are JSON
with actionable guidance on stderr. Special files/changed input snapshots refuse.
"""

from __future__ import annotations

import base64
from dataclasses import dataclass
from functools import cached_property
import json
import os
from pathlib import Path
import sys
from typing import Any
from xml.parsers import expat

import lottie_images
import project

SVG = "http://www.w3.org/2000/svg}"
XLINK_HREF = "http://www.w3.org/1999/xlink}href"
XML_ID = "http://www.w3.org/XML/1998/namespace}id"
HREFS = {"href", XLINK_HREF}
SPACE = b" \t\r\n"


@dataclass(frozen=True)
class Attribute:
    name: str
    value: str
    start: int
    end: int


@dataclass
class Element:
    index: int
    name: str
    parent: int | None
    attributes: dict[str, Attribute]
    namespaces: dict[str, str | None]

    def value(self, name: str) -> str | None:
        attribute = self.attributes.get(name)
        return attribute.value if attribute else None


def attribute_spans(raw: bytes, offset: int) -> list[tuple[str, int, int]]:
    """Locate quoted values only within an Expat-identified UTF-8 start tag.

    XML well-formedness/namespaces belong to Expat; this bounded lexical scan
    preserves the original attribute spelling and all bytes outside its value.
    """
    cursor = offset + 1
    while cursor < len(raw) and raw[cursor] not in SPACE + b"/>":
        cursor += 1
    result = []
    while cursor < len(raw):
        while cursor < len(raw) and raw[cursor] in SPACE:
            cursor += 1
        if raw[cursor : cursor + 1] in {b"/", b">"}:
            return result
        begin = cursor
        while cursor < len(raw) and raw[cursor] not in SPACE + b"=":
            cursor += 1
        name = raw[begin:cursor].decode("utf-8")
        while cursor < len(raw) and raw[cursor] in SPACE:
            cursor += 1
        if raw[cursor : cursor + 1] != b"=":
            raise ValueError("repair the SVG start-tag attribute assignment")
        cursor += 1
        while cursor < len(raw) and raw[cursor] in SPACE:
            cursor += 1
        quote = raw[cursor : cursor + 1]
        if quote not in {b"'", b'"'}:
            raise ValueError("repair SVG attributes to use quoted values")
        begin = cursor + 1
        end = raw.find(quote, begin)
        if end < 0:
            raise ValueError("repair the unterminated SVG attribute value")
        if name != "xmlns" and not name.startswith("xmlns:"):
            result.append((name, begin, end))
        cursor = end + 1
    raise ValueError("repair the incomplete SVG start tag")


class Document:
    def __init__(self, raw: bytes):
        try:
            raw.decode("utf-8-sig")
        except UnicodeError as exc:
            raise ValueError("select or explicitly convert a separate SVG copy to UTF-8") from exc
        if b"\0" in raw:
            raise ValueError("select a UTF-8 SVG without NUL bytes or UTF-16 encoding")
        self.raw = raw
        self.elements: list[Element] = []
        self.images: list[Element] = []
        self.stylesheets: list[str] = []
        self.style_text: list[dict[str, Any]] = []
        stack: list[int] = []
        pending_namespaces: dict[str, str | None] = {}
        parser = expat.ParserCreate(namespace_separator="}")
        parser.ordered_attributes = True
        parser.specified_attributes = True

        def start(name: str, attributes: list[str]) -> None:
            if not self.elements and name != SVG + "svg":
                raise ValueError("select a document rooted in the SVG namespace")
            spans = attribute_spans(raw, parser.CurrentByteIndex)
            if len(spans) * 2 != len(attributes):
                raise ValueError("inspect unfamiliar XML attribute expansion before editing")
            values = {
                attributes[index * 2]: Attribute(
                    attributes[index * 2], attributes[index * 2 + 1], begin, end
                )
                for index, (_, begin, end) in enumerate(spans)
            }
            node = Element(
                len(self.elements),
                name,
                stack[-1] if stack else None,
                values,
                dict(pending_namespaces),
            )
            pending_namespaces.clear()
            self.elements.append(node)
            stack.append(node.index)
            if name == SVG + "image":
                self.images.append(node)

        def finish(_name: str) -> None:
            stack.pop()

        def declaration(_version: str, encoding: str | None, _standalone: int) -> None:
            if encoding and encoding.lower().replace("-", "") not in {"utf8", "ascii", "usascii"}:
                raise ValueError("convert a separate SVG copy to an explicit UTF-8 encoding")

        def doctype(*_args: Any) -> None:
            raise ValueError("remove DTD/entity declarations in a separate reviewed SVG copy")

        def external(*_args: Any) -> int:
            raise ValueError("inline or remove external XML entities in a separate SVG copy")

        def instruction(target: str, data: str) -> None:
            if target == "xml-stylesheet":
                self.stylesheets.append(data)

        def text(data: str) -> None:
            if stack and self.elements[stack[-1]].name == SVG + "style":
                self.style_text.append({"elementIndex": stack[-1], "text": data})

        parser.StartElementHandler = start
        parser.EndElementHandler = finish
        parser.XmlDeclHandler = declaration
        parser.StartDoctypeDeclHandler = doctype
        parser.ExternalEntityRefHandler = external
        parser.ProcessingInstructionHandler = instruction
        parser.CharacterDataHandler = text
        parser.StartNamespaceDeclHandler = lambda prefix, uri: pending_namespaces.update(
            {prefix or "": uri}
        )
        parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
        try:
            parser.Parse(raw, True)
        except expat.ExpatError as exc:
            raise ValueError(f"repair SVG XML before inspecting or embedding: {exc}") from exc

    @cached_property
    def identities(self) -> dict[str, list[int]]:
        result: dict[str, list[int]] = {}
        for node in self.elements:
            for key in ("id", XML_ID):
                value = node.value(key)
                if value is not None:
                    result.setdefault(value, []).append(node.index)
        return result

    @cached_property
    def duplicates(self) -> list[str]:
        return sorted(key for key, indices in self.identities.items() if len(set(indices)) > 1)

    @cached_property
    def active(self) -> list[int]:
        return [
            node.index
            for node in self.elements
            if node.name == SVG + "script"
            or any(name.startswith("on") and "}" not in name for name in node.attributes)
        ]

    def namespace(self, node: Element, prefix: str) -> str | None:
        while True:
            if prefix in node.namespaces:
                return node.namespaces[prefix]
            if node.parent is None:
                return None
            node = self.elements[node.parent]

    @cached_property
    def dynamic(self) -> dict[int, list[int]]:
        result: dict[int, list[int]] = {}
        identities = self.identities
        for node in self.elements:
            if node.name not in {SVG + "animate", SVG + "set"}:
                continue
            attribute = node.value("attributeName") or ""
            if attribute != "href" and not (
                ":" in attribute
                and attribute.split(":", 1)[1] == "href"
                and self.namespace(node, attribute.split(":", 1)[0])
                == "http://www.w3.org/1999/xlink"
            ):
                continue
            targets = [a.value for key, a in node.attributes.items() if key in HREFS]
            owners = [
                index
                for target in targets
                if target.startswith("#")
                for index in identities.get(target[1:], [])
            ]
            if not targets and node.parent is not None:
                owners = [node.parent]
            for owner in owners:
                result.setdefault(owner, []).append(node.index)
        return result


def references(node: Element) -> list[Attribute]:
    return [attribute for name, attribute in node.attributes.items() if name in HREFS]


def reference_kind(value: str) -> str:
    return "fragment" if value.startswith("#") else lottie_images.reference_kind(value, "")


def eligible(document: Document, node: Element) -> list[Attribute]:
    if document.active:
        raise ValueError(
            "remove or separately verify active SVG content before static image embedding"
        )
    if node.index in document.dynamic:
        raise ValueError("resolve animated image references before replacing their static fallback")
    if document.duplicates:
        raise ValueError("repair duplicate SVG IDs before selecting image ownership")
    refs = references(node)
    if not refs or len({attribute.value for attribute in refs}) != 1:
        raise ValueError("select an image with an existing unambiguous href reference")
    if node.value("type") not in {None, "image/png"}:
        raise ValueError("review the non-PNG image MIME hint before staging a PNG replacement")
    return refs


def inventory(document: Document) -> dict[str, Any]:
    rows = []
    for index, node in enumerate(document.images):
        refs = references(node)
        row: dict[str, Any] = {
            "imageIndex": index,
            "elementIndex": node.index,
            "id": node.value("id"),
            "xmlId": node.value(XML_ID),
            "embeddedPNG": False,
            "references": [
                {
                    "attribute": a.name,
                    "referenceKind": reference_kind(a.value),
                    "value": None if a.value.startswith("data:") else a.value,
                }
                for a in refs
            ],
            "pngSha256": None,
            "sizeBytes": None,
            "dimensions": None,
        }
        try:
            selected = eligible(document, node)
            value = selected[0].value
            if not value.startswith(lottie_images.PNG_DATA_PREFIX):
                raise ValueError("select a PNG explicitly to embed the intended image bytes")
            raw = base64.b64decode(value[len(lottie_images.PNG_DATA_PREFIX) :], validate=True)
            row.update(
                dimensions=list(lottie_images.png_size(raw)),
                pngSha256=project.digest(raw),
                sizeBytes=len(raw),
                embeddedPNG=True,
            )
        except ValueError as exc:
            row["reason"] = str(exc)
        rows.append(row)
    return {
        "images": rows,
        "duplicateIds": document.duplicates,
        "activeElementIndices": document.active,
        "dynamicImageReferences": [
            {"elementIndex": key, "animationElementIndices": value}
            for key, value in document.dynamic.items()
        ],
        "otherReferences": [
            {
                "elementIndex": node.index,
                "element": node.name,
                "attribute": a.name,
                "referenceKind": reference_kind(a.value),
                "value": None if a.value.startswith("data:") else a.value,
            }
            for node in document.elements
            if node.name != SVG + "image"
            for a in references(node)
        ],
        "fontStyleDeclarations": [
            {
                "elementIndex": node.index,
                "element": node.name,
                "attributes": {
                    name: a.value
                    for name, a in node.attributes.items()
                    if name in {"font-family", "font-style", "font-weight", "style"}
                },
            }
            for node in document.elements
            if any(
                name in node.attributes
                for name in {"font-family", "font-style", "font-weight", "style"}
            )
        ],
        "stylesheetInstructions": document.stylesheets,
        "styleText": document.style_text,
        "imageAssetsEmbedded": all(row["embeddedPNG"] for row in rows)
        and not document.active
        and not document.duplicates,
        "limits": [
            "Static SVG image hrefs only; no full SVG/project resource closure or rendering proof.",
            "Fonts, stylesheets, other references, CSS and nonimage resources remain unresolved.",
            "PNG containers are checked without pixel decoding; verify the relocated native render.",
        ],
    }


def embed_png(
    document: Document, raw: bytes, *, image_id: str | None = None, image_index: int | None = None
) -> tuple[bytes, int]:
    lottie_images.png_size(raw)
    if (image_id is None) == (image_index is None):
        raise ValueError("select exactly one image ID or zero-based image index from inspection")
    if image_id is not None:
        matches = [
            node for node in document.images if image_id in {node.value("id"), node.value(XML_ID)}
        ]
        if len(matches) != 1:
            raise ValueError("select a unique existing SVG image ID from inspection")
        node = matches[0]
        index = document.images.index(node)
    else:
        if type(image_index) is not int or not 0 <= image_index < len(document.images):
            raise ValueError("select an existing zero-based SVG image index from inspection")
        index, node = image_index, document.images[image_index]
    refs = eligible(document, node)
    replacement = (lottie_images.PNG_DATA_PREFIX + base64.b64encode(raw).decode("ascii")).encode(
        "ascii"
    )
    candidate = document.raw
    for attribute in sorted(refs, key=lambda item: item.start, reverse=True):
        candidate = candidate[: attribute.start] + replacement + candidate[attribute.end :]
    Document(candidate)
    return candidate, index


def stage(source: Path, output: Path, raw: bytes) -> bool:
    if output.is_symlink():
        raise ValueError("choose a separate nonsymlink SVG candidate outside the source")
    try:
        with output.open("xb") as stream:
            stream.write(raw)
    except FileExistsError:
        if output.is_symlink() or os.path.samefile(source, output):
            raise ValueError("choose a candidate that is not linked to the source SVG") from None
        if not output.is_file() or lottie_images.read_file(output, "SVG candidate") != raw:
            raise ValueError("choose a new output path; the existing candidate differs") from None
        return False
    return True


def main(argv: list[str] | None = None) -> int:
    parser = lottie_images.JSONArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("source", type=Path)
    inspect.add_argument("--require-embedded", action="store_true")
    embed = commands.add_parser("embed")
    embed.add_argument("source", type=Path)
    embed.add_argument("--expected-sha256", required=True)
    selection = embed.add_mutually_exclusive_group(required=True)
    selection.add_argument("--image-id")
    selection.add_argument("--image-index", type=int)
    embed.add_argument("--image", type=Path, required=True)
    embed.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    action = "select an existing readable UTF-8 SVG source and repair its XML if needed"
    try:
        raw = lottie_images.read_file(args.source, "SVG source")
        document = Document(raw)
        report = {
            "schema_version": 1,
            "owner": "camtasia-svg-images",
            "ok": True,
            "sourceSha256": project.digest(raw),
            "nativeVerified": False,
        }
        if args.command == "embed":
            if args.expected_sha256 != project.digest(raw):
                raise ValueError("inspect the changed SVG again and use its current source hash")
            action = "select an existing readable PNG image file"
            png = lottie_images.read_file(args.image, "PNG")
            action = "select an unambiguous static SVG image from inspection and a valid PNG"
            candidate, index = embed_png(
                document, png, image_id=args.image_id, image_index=args.image_index
            )
            report.update(inventory(Document(candidate)))
            action = "create the output parent and choose a writable separate SVG candidate path"
            report.update(
                imageIndex=index,
                pngSha256=project.digest(png),
                candidateSha256=project.digest(candidate),
                changed=candidate != raw,
                output=str(args.output),
                written=stage(args.source, args.output, candidate),
            )
        else:
            report.update(inventory(document))
            report["ok"] = not args.require_embedded or report["imageAssetsEmbedded"]
        print(json.dumps(report, ensure_ascii=False))
        if not report["ok"]:
            print(
                json.dumps(
                    {
                        "ok": False,
                        "error": "the static SVG image embedding requirement is unmet",
                        "action": "inspect image reasons and resolve unsupported or external image references",
                    }
                ),
                file=sys.stderr,
            )
            return 1
        return 0
    except (OSError, ValueError, RecursionError) as exc:
        print(json.dumps({"ok": False, "error": str(exc), "action": action}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
