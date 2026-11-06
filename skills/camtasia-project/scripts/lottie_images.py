#!/usr/bin/env python3
"""Inspect Lottie raster references and stage explicitly selected PNG embedding.

Mac 2026.2.4 native evidence supports p=data:image/png;base64,..., e=1, u="".
This edits a Lottie source JSON, not a Camtasia project. A source is recognized
by composition identity/clocks/layers, never just its filename extension.
Select one existing image asset by its animation-local ID and supply the PNG
explicitly; no stored path is followed, remote content fetched, or installation
resource/font copied. The PNG's physical size must match the asset's w/h.
Only p/u/e change; animation clocks, geometry, layers, colors, glyphs, fonts,
unknown fields and other assets remain intact. Repeated identical staging is
a no-op; originals, different occupied outputs and output symlinks are protected.

PNG checks cover signature, complete chunk framing/CRCs, IHDR dimensions and
IDAT/IEND presence. They do not decode pixels or certify every PNG feature.
Fonts are reported as unresolved declarations, not selected physical faces;
glyph counts do not establish text coverage. imageAssetsEmbedded covers the
recognized image assets and root/asset-precomposition image layer references.
Other file assets remain unresolved in unhandledAssetIds without gating images.
It never establishes complete Lottie/project dependency closure or rendering.

CLI: inspect SOURCE [--require-embedded]; embed SOURCE --asset-id ID --image PNG
--output CANDIDATE. Stdout schema 1, owner camtasia-lottie-images, source hash,
image inventory, font declarations and nativeVerified:false. Embed also emits
selected PNG/candidate hashes and changed/written. No continuity state is read.
Exit 0 successful inspection/staging, 1 refusal or unmet --require-embedded,
2 argument syntax. Recheck source hashes before using a staged source in a new
project bundle; preserve originals and verify a relocated native export.
"""

from __future__ import annotations

import argparse
import base64
import copy
from decimal import Decimal, InvalidOperation
import json
import math
import os
from pathlib import Path, PureWindowsPath
import stat
import struct
import sys
from typing import Any
import zlib

import project

PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"
PNG_DATA_PREFIX = "data:image/png;base64,"
PNG_DEPTHS = {0: {1, 2, 4, 8, 16}, 2: {8, 16}, 3: {1, 2, 4, 8}, 4: {8, 16}, 6: {8, 16}}
PNG_MAX_DIMENSION = (1 << 31) - 1


class JSONArgumentParser(argparse.ArgumentParser):
    def error(self, message: str) -> None:
        self.exit(2, json.dumps({"ok": False, "error": message, "action": "run --help"}) + "\n")


def load_source(path: Path) -> tuple[dict[str, Any], bytes]:
    """Keep finite decimal values exact, including unfamiliar animation payload."""
    raw = path.read_bytes()
    try:
        doc = json.loads(
            raw,
            parse_float=Decimal,
            parse_constant=project.invalid_constant,
            object_pairs_hook=project.unique_object,
        )
    except InvalidOperation as exc:
        raise ValueError(
            "use finite animation numbers within the exact decimal parser's range"
        ) from exc
    if not isinstance(doc, dict):
        raise ValueError("select a Lottie JSON object rather than a scalar or array")
    return doc, raw


def encode_document(doc: dict[str, Any]) -> bytes:
    """Serialize exact finite decimals as JSON numbers without a float conversion."""

    def value(node: Any) -> str:
        if isinstance(node, Decimal):
            if not node.is_finite():
                raise ValueError("replace nonfinite animation numbers with finite values")
            return str(node)
        if isinstance(node, dict):
            if not all(isinstance(key, str) for key in node):
                raise ValueError("retain string JSON object keys before staging")
            return (
                "{"
                + ",".join(
                    json.dumps(k, ensure_ascii=False) + ":" + value(v) for k, v in node.items()
                )
                + "}"
            )
        if isinstance(node, list):
            return "[" + ",".join(value(child) for child in node) + "]"
        return json.dumps(node, ensure_ascii=False, allow_nan=False)

    return (value(doc) + "\n").encode("utf-8")


def stage(source: Path, output: Path, candidate: dict[str, Any]) -> bool:
    """Stage exact source values to an exclusive file, refusing inode aliases."""
    if output.is_symlink() or output.resolve() == source.resolve():
        raise ValueError("choose a separate nonsymlink candidate outside the source document")
    raw = encode_document(candidate)
    try:
        with output.open("xb") as stream:
            stream.write(raw)
    except FileExistsError:
        if output.is_symlink() or os.path.samefile(source, output):
            raise ValueError(
                "choose a candidate that is not linked to the original source"
            ) from None
        if not output.is_file() or output.read_bytes() != raw:
            raise ValueError(
                "candidate contains different data; choose a new output path"
            ) from None
        return False
    return True


def read_image(path: Path) -> bytes:
    """Read an explicit regular-file snapshot, refusing a changed identity."""
    with os.fdopen(os.open(path, os.O_RDONLY | getattr(os, "O_NONBLOCK", 0)), "rb") as stream:
        before = os.fstat(stream.fileno())
        if not stat.S_ISREG(before.st_mode):
            raise ValueError("select a regular PNG file instead of a device, directory or pipe")
        raw = stream.read()
        after = os.fstat(stream.fileno())
    fields = ("st_dev", "st_ino", "st_size", "st_mtime_ns", "st_ctime_ns")
    current = path.stat()
    if any(
        getattr(before, name) != getattr(after, name)
        or getattr(after, name) != getattr(current, name)
        for name in fields
    ):
        raise ValueError("PNG changed while reading; finish image writes and retry")
    return raw


def png_size(raw: bytes) -> tuple[int, int]:
    """Check a PNG container without interpreting compressed pixels."""
    if not raw.startswith(PNG_SIGNATURE):
        raise ValueError("select a PNG file with its original PNG signature")
    offset, size, image_data = 8, None, False
    while offset < len(raw):
        if len(raw) - offset < 12:
            raise ValueError("replace the truncated PNG chunk with an intact PNG")
        length = int.from_bytes(raw[offset : offset + 4], "big")
        end = offset + 12 + length
        if end > len(raw):
            raise ValueError("replace the truncated PNG chunk payload with an intact PNG")
        tag = raw[offset + 4 : offset + 8]
        data = raw[offset + 8 : end - 4]
        if zlib.crc32(tag + data) != int.from_bytes(raw[end - 4 : end], "big"):
            raise ValueError("replace the PNG with intact chunk CRCs")
        if offset == 8:
            if tag != b"IHDR" or length != 13:
                raise ValueError("select a PNG with its complete initial IHDR")
            width, height, depth, color, compression, filtering, interlace = struct.unpack(
                ">IIBBBBB", data
            )
            if (
                not 0 < width <= PNG_MAX_DIMENSION
                or not 0 < height <= PNG_MAX_DIMENSION
                or depth not in PNG_DEPTHS.get(color, set())
                or compression != 0
                or filtering != 0
                or interlace not in {0, 1}
            ):
                raise ValueError("select a PNG with a supported nonempty IHDR")
            size = width, height
        elif tag == b"IHDR":
            raise ValueError("select a PNG containing only one IHDR")
        if tag == b"IDAT" and length:
            image_data = True
        if tag == b"IEND":
            if length or end != len(raw) or not image_data or size is None:
                raise ValueError("select an intact PNG ending in IEND after image data")
            return size
        offset = end
    raise ValueError("select a complete PNG with image data and a final IEND")


def finite_number(value: Any) -> bool:
    return (
        type(value) is int
        or (type(value) is float and math.isfinite(value))
        or (isinstance(value, Decimal) and value.is_finite())
    )


def source_assets(doc: dict[str, Any]) -> list[dict[str, Any]]:
    if (
        not isinstance(doc.get("v"), str)
        or not doc["v"]
        or not all(finite_number(doc.get(k)) for k in ("w", "h", "fr", "ip", "op"))
        or any(doc[k] <= 0 for k in ("w", "h", "fr"))
        or doc["op"] <= doc["ip"]
        or not isinstance(doc.get("layers"), list)
    ):
        raise ValueError(
            "select a Lottie source with composition dimensions, frame clocks and layers"
        )
    assets = doc.get("assets", [])
    if not isinstance(assets, list):
        raise ValueError("repair the Lottie assets array before editing images")
    seen = set()
    for asset in assets:
        if (
            not isinstance(asset, dict)
            or not isinstance(asset.get("id"), str)
            or not asset["id"]
            or asset["id"] in seen
        ):
            raise ValueError("repair missing or duplicate animation-local asset IDs")
        seen.add(asset["id"])
    return assets


def image_size(asset: dict[str, Any]) -> tuple[int, int]:
    if "layers" in asset or asset.get("t") == 3 or not isinstance(asset.get("p"), str):
        raise ValueError(
            "select an image asset, keeping precompositions and unfamiliar assets intact"
        )
    values: tuple[Any, Any] = (asset.get("w"), asset.get("h"))
    if not all(finite_number(value) and 0 < value <= PNG_MAX_DIMENSION for value in values):
        raise ValueError("retain positive whole-pixel image asset dimensions before embedding")
    width, height = (int(value) for value in values)
    if (width, height) != values:
        raise ValueError("retain positive whole-pixel image asset dimensions before embedding")
    return width, height


def reference_kind(filename: str, directory: str) -> str:
    reference = directory + filename
    if filename.startswith("data:"):
        return "data-uri"
    if reference.startswith("file:"):
        return "file-uri"
    if "://" in reference:
        return "remote"
    if PureWindowsPath(reference).drive:
        return "windows-path"
    return "absolute-path" if Path(reference).is_absolute() else "relative-path"


def inventory(doc: dict[str, Any]) -> dict[str, Any]:
    rows = []
    unhandled = []
    assets = source_assets(doc)
    for index, asset in enumerate(assets):
        # File paths alone also describe sound and data assets. Image dimensions
        # or a slotted image identity distinguish this image-only inventory.
        if (
            "layers" in asset
            or asset.get("t") == 3
            or not any(field in asset for field in ("w", "h", "sid"))
        ):
            if "p" in asset:
                unhandled.append(asset["id"])
            continue
        row: dict[str, Any] = {
            "assetId": asset["id"],
            "path": f"/assets/{index}",
            "embeddedPNG": False,
            "pngSha256": None,
            "sizeBytes": None,
        }
        try:
            dimensions = image_size(asset)
            filename, directory = asset["p"], asset.get("u", "")
            if not isinstance(directory, str):
                raise ValueError("inspect the image asset's unfamiliar directory value")
            row.update(
                dimensions=list(dimensions),
                referenceKind=reference_kind(filename, directory),
                filename=None if filename.startswith("data:") else filename,
                directory=directory,
                declaredEmbedded=asset.get("e", 0),
            )
            if not filename.startswith(PNG_DATA_PREFIX):
                row["reason"] = "Select a PNG explicitly to stage the native embedded image form."
            else:
                raw = base64.b64decode(filename[len(PNG_DATA_PREFIX) :], validate=True)
                if png_size(raw) != dimensions:
                    raise ValueError("match the embedded PNG's physical size to the image asset")
                row.update(pngSha256=project.digest(raw), sizeBytes=len(raw))
                if type(asset.get("e")) is int and asset["e"] == 1 and directory == "":
                    row["embeddedPNG"] = True
                else:
                    row["reason"] = "Stage the native e=1 and empty u companions for this PNG."
        except ValueError as exc:
            row["reason"] = str(exc)
        rows.append(row)
        if "dimensions" not in row:
            unhandled.append(asset["id"])
    ids = {row["assetId"] for row in rows if row["assetId"] not in unhandled}
    layer_arrays = [("/layers", doc["layers"])] + [
        (f"/assets/{index}/layers", asset["layers"])
        for index, asset in enumerate(assets)
        if isinstance(asset.get("layers"), list)
    ]
    references = [
        (f"{path}/{index}", layer)
        for path, layers in layer_arrays
        for index, layer in enumerate(layers)
        if isinstance(layer, dict) and layer.get("ty") == 2
    ]
    missing = sorted(
        {
            node["refId"]
            for _, node in references
            if isinstance(node.get("refId"), str) and node["refId"] not in ids
        }
    )
    invalid_references = [
        path
        for path, node in references
        if not isinstance(node.get("refId"), str) or not node["refId"]
    ]
    return {
        "images": rows,
        "missingImageAssetIds": missing,
        "unhandledAssetIds": unhandled,
        "invalidImageReferencePaths": invalid_references,
        "imageAssetsEmbedded": all(row["embeddedPNG"] for row in rows)
        and not missing
        and not invalid_references,
        "fontDeclarations": copy.deepcopy(doc.get("fonts")),
        "embeddedGlyphCount": len(doc["chars"]) if isinstance(doc.get("chars"), list) else None,
        "limits": [
            "Image-asset embedding only; no complete Lottie or project dependency closure.",
            "Font faces, glyph coverage, expressions, plugins and other render resources are unresolved.",
            "PNG containers are checked without pixel decoding; verify a relocated native render.",
        ],
    }


def embed_png(doc: dict[str, Any], asset_id: str, raw: bytes) -> dict[str, Any]:
    matches = [asset for asset in source_assets(doc) if asset["id"] == asset_id]
    if len(matches) != 1:
        raise ValueError("select an existing unique image asset ID from inspection")
    if image_size(matches[0]) != png_size(raw):
        raise ValueError(
            "choose a PNG matching the image asset's dimensions; keep geometry unchanged"
        )
    candidate = copy.deepcopy(doc)
    target = next(asset for asset in candidate["assets"] if asset["id"] == asset_id)
    target.update(p=PNG_DATA_PREFIX + base64.b64encode(raw).decode("ascii"), u="", e=1)
    return candidate


def main(argv: list[str] | None = None) -> int:
    parser = JSONArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("source", type=Path)
    inspect.add_argument("--require-embedded", action="store_true")
    embed = commands.add_parser("embed")
    embed.add_argument("source", type=Path)
    embed.add_argument("--asset-id", required=True)
    embed.add_argument("--image", type=Path, required=True)
    embed.add_argument("--output", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        doc, source = load_source(args.source)
        report: dict[str, Any] = {
            "schema_version": 1,
            "owner": "camtasia-lottie-images",
            "ok": True,
            "sourceSha256": project.digest(source),
            "nativeVerified": False,
        }
        if args.command == "embed":
            image = args.image.resolve(strict=True)
            raw = read_image(image)
            candidate = embed_png(doc, args.asset_id, raw)
            report.update(inventory(candidate))
            report.update(
                assetId=args.asset_id,
                pngSha256=project.digest(raw),
                output=str(args.output),
                candidateSha256=project.digest(encode_document(candidate)),
                changed=encode_document(candidate) != encode_document(doc),
                written=stage(args.source, args.output, candidate),
            )
        else:
            report.update(inventory(doc))
            report["ok"] = not args.require_embedded or report["imageAssetsEmbedded"]
        print(encode_document(report).decode("utf-8"), end="")
        return 0 if report["ok"] else 1
    except RecursionError:
        print(
            json.dumps(
                {"ok": False, "error": "reduce excessive Lottie JSON nesting before staging"}
            ),
            file=sys.stderr,
        )
        return 1
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
