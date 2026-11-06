from __future__ import annotations

import base64
import copy
import io
import json
import os
from pathlib import Path
import struct
import sys
import tempfile
from types import SimpleNamespace
from typing import Any
import unittest
from unittest.mock import patch
import zlib

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/camtasia-project/scripts"))
import lottie_images  # noqa: E402
import project  # noqa: E402


def chunk(tag: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + tag + data + struct.pack(">I", zlib.crc32(tag + data))


def png(width: int = 2, height: int = 3) -> bytes:
    pixels = (b"\0" + bytes([255, 0, 0, 255]) * width) * height
    return (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
        + chunk(b"tEXt", b"Creator\0Independent fixed fixture")
        + chunk(b"IDAT", zlib.compress(pixels))
        + chunk(b"IEND", b"")
    )


def fixture() -> dict:
    return {
        "v": "5.7.4",
        "w": 640,
        "h": 360,
        "fr": 30,
        "ip": 0,
        "op": 120,
        "assets": [
            {
                "id": "photo",
                "w": 2,
                "h": 3,
                "p": "photo.png",
                "u": "/original/",
                "e": 0,
                "nm": "Café — image",
                "future": {"retain": [False, None]},
            },
            {
                "id": "composition",
                "layers": [
                    {
                        "ty": 2,
                        "refId": "photo",
                        "ip": 0,
                        "op": 120,
                        "ks": {"p": {"k": [100, 50, 0]}},
                    }
                ],
            },
        ],
        "layers": [{"ty": 0, "refId": "composition", "ip": 0, "op": 120}],
        "fonts": {
            "list": [
                {
                    "fName": "Private",
                    "fFamily": "Uninstalled face",
                    "fStyle": "Regular",
                    "fPath": "https://example.test/font.ttf",
                    "origin": 3,
                }
            ]
        },
        "chars": [{"ch": "A", "data": {"shapes": [{"ty": "gr", "opaque": True}]}}],
        "future": {"expression": "never execute this", "colors": [0.5, 1, 0, 1]},
    }


class LottieImageTests(unittest.TestCase):
    def test_embedding_changes_only_selected_native_fields_and_keeps_exact_png_bytes(self) -> None:
        source = fixture()
        before = copy.deepcopy(source)
        raw = png()
        result = lottie_images.embed_png(source, "photo", raw)
        asset = result["assets"][0]
        self.assertEqual(asset["u"], "")
        self.assertEqual(asset["e"], 1)
        self.assertEqual(type(asset["e"]), int)
        self.assertTrue(asset["p"].startswith("data:image/png;base64,"))
        self.assertEqual(base64.b64decode(asset["p"].split(",", 1)[1]), raw)
        for key in ("p", "u", "e"):
            asset[key] = before["assets"][0][key]
        self.assertEqual(result, before)
        self.assertEqual(source, before)

    def test_embedding_is_idempotent_without_changing_animation_clocks(self) -> None:
        source = fixture()
        source.update(fr=29.97, ip=1.5, op=120.5)
        first = lottie_images.embed_png(source, "photo", png())
        self.assertEqual(lottie_images.embed_png(first, "photo", png()), first)
        self.assertEqual((first["fr"], first["ip"], first["op"]), (29.97, 1.5, 120.5))

    def test_inventory_distinguishes_external_reference_forms_without_following_them(self) -> None:
        for directory, filename, kind in [
            ("images/", "photo.png", "relative-path"),
            ("/absolute/", "photo.png", "absolute-path"),
            ("file:///native/", "photo.png", "file-uri"),
            ("https://example.test/", "photo.png", "remote"),
            ("C:\\Media\\", "photo.png", "windows-path"),
        ]:
            source = fixture()
            source["assets"][0].update(u=directory, p=filename)
            with patch.object(
                Path, "read_bytes", side_effect=AssertionError("Unexpected resource read")
            ):
                report = lottie_images.inventory(source)
            self.assertEqual(report["images"][0]["referenceKind"], kind)
            self.assertFalse(report["imageAssetsEmbedded"])
            self.assertEqual(report["images"][0]["filename"], filename)
            self.assertEqual(report["images"][0]["directory"], directory)

    def test_embedded_inventory_reports_hashes_without_echoing_the_data_url(self) -> None:
        source = lottie_images.embed_png(fixture(), "photo", png())
        report = lottie_images.inventory(source)
        self.assertTrue(report["imageAssetsEmbedded"])
        row = report["images"][0]
        self.assertEqual(row["pngSha256"], project.digest(png()))
        self.assertEqual(row["sizeBytes"], len(png()))
        self.assertEqual(row["dimensions"], [2, 3])
        self.assertIsNone(row["filename"])
        self.assertNotIn("base64", json.dumps(report))

    def test_missing_and_malformed_nested_image_references_remain_unresolved(self) -> None:
        source = lottie_images.embed_png(fixture(), "photo", png())
        source["assets"][1]["layers"].append({"ty": 2, "refId": "absent"})
        report = lottie_images.inventory(source)
        self.assertEqual(report["missingImageAssetIds"], ["absent"])
        self.assertFalse(report["imageAssetsEmbedded"])
        source["assets"][1]["layers"][-1]["refId"] = None
        report = lottie_images.inventory(source)
        self.assertEqual(report["invalidImageReferencePaths"], ["/assets/1/layers/1"])
        self.assertFalse(report["imageAssetsEmbedded"])

    def test_font_declarations_and_glyph_count_never_become_font_resolution(self) -> None:
        source = lottie_images.embed_png(fixture(), "photo", png())
        report = lottie_images.inventory(source)
        self.assertEqual(report["fontDeclarations"], source["fonts"])
        self.assertEqual(report["embeddedGlyphCount"], 1)
        self.assertIn("unresolved", report["limits"][1])
        self.assertIn("no complete", report["limits"][0])

    def test_no_images_is_only_a_vacuous_image_inventory_not_project_closure(self) -> None:
        source = fixture()
        source["assets"], source["layers"] = [], []
        report = lottie_images.inventory(source)
        self.assertTrue(report["imageAssetsEmbedded"])
        self.assertEqual(report["images"], [])
        self.assertIsNotNone(report["fontDeclarations"])

    def test_bad_embedded_payload_dimensions_or_companions_do_not_pass_the_gate(self) -> None:
        valid = lottie_images.embed_png(fixture(), "photo", png())
        for changes in [
            {"p": "data:image/png;base64,%%%"},
            {"p": "data:image/jpeg;base64,AAAA"},
            {"p": "data:image/png;base64," + base64.b64encode(b"not a PNG").decode()},
            {"w": 3},
            {"e": 0},
            {"e": True},
            {"u": "images/"},
        ]:
            source = copy.deepcopy(valid)
            source["assets"][0].update(changes)
            report = lottie_images.inventory(source)
            self.assertFalse(report["imageAssetsEmbedded"], changes)
            self.assertIn("reason", report["images"][0])

    def test_other_image_and_unfamiliar_asset_payload_survive_a_selected_edit(self) -> None:
        source = fixture()
        source["assets"].extend(
            [
                {"id": "second", "w": 1, "h": 1, "p": "other.png", "u": "elsewhere/"},
                {"id": "future-audio", "p": "audio.bin", "future": [1, 2]},
            ]
        )
        result = lottie_images.embed_png(source, "photo", png())
        self.assertEqual(result["assets"][1:], source["assets"][1:])
        report = lottie_images.inventory(result)
        self.assertFalse(report["imageAssetsEmbedded"])
        self.assertEqual(report["unhandledAssetIds"], ["future-audio"])

    def test_ambiguous_missing_or_nonimage_asset_selection_refuses_unchanged_input(self) -> None:
        source = fixture()
        before = copy.deepcopy(source)
        selections: tuple[Any, ...] = ("missing", "composition", "", True)
        for selected in selections:
            with self.assertRaises(ValueError):
                lottie_images.embed_png(source, selected, png())
        self.assertEqual(source, before)
        source["assets"].append(copy.deepcopy(source["assets"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            lottie_images.embed_png(source, "photo", png())

    def test_mismatched_or_unfamiliar_geometry_refuses_without_mutation(self) -> None:
        source = fixture()
        with self.assertRaisesRegex(ValueError, "dimensions"):
            lottie_images.embed_png(source, "photo", png(3, 3))
        for width in (True, 0, -1, 1.5, "2", None):
            source["assets"][0]["w"] = width
            before = copy.deepcopy(source)
            with self.assertRaisesRegex(ValueError, "dimensions"):
                lottie_images.embed_png(source, "photo", png())
            self.assertEqual(source, before)

    def test_invalid_composition_and_asset_shapes_require_repair(self) -> None:
        for changes in [
            {"v": None},
            {"fr": 0},
            {"fr": True},
            {"op": 0},
            {"layers": {}},
            {"assets": {}},
            {"assets": [None]},
            {"assets": [{"id": 1}]},
        ]:
            source = fixture()
            source.update(changes)
            with self.assertRaises(ValueError):
                lottie_images.inventory(source)

    def test_png_container_rejects_truncation_bad_crc_empty_size_and_bad_chunk_order(self) -> None:
        header = chunk(b"IHDR", struct.pack(">IIBBBBB", 2, 3, 8, 6, 0, 0, 0))
        for bad in [
            b"",
            b"JPEG",
            png()[:-1],
            png()[:20],
            png() + b"trailing",
            png()[:30] + b"changed" + png()[37:],
            b"\x89PNG\r\n\x1a\n" + chunk(b"IEND", b""),
            b"\x89PNG\r\n\x1a\n" + header + header + chunk(b"IEND", b""),
            png(0, 3),
        ]:
            with self.subTest(length=len(bad)), self.assertRaises(ValueError):
                lottie_images.png_size(bad)
        self.assertEqual(lottie_images.png_size(png()), (2, 3))

    def test_cli_stage_gate_noop_and_collision_preserve_both_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, image, output = [
                root / n for n in ("animation.json", "chosen.png", "staged.json")
            ]
            source.write_bytes(project.encode_document(fixture()))
            image.write_bytes(png())
            original = source.read_bytes()
            stream = io.StringIO()
            with patch("sys.stdout", stream):
                self.assertEqual(
                    lottie_images.main(["inspect", str(source), "--require-embedded"]), 1
                )
            self.assertFalse(json.loads(stream.getvalue())["imageAssetsEmbedded"])
            command = [
                "embed",
                str(source),
                "--asset-id",
                "photo",
                "--image",
                str(image),
                "--output",
                str(output),
            ]
            for written in (True, False):
                stream = io.StringIO()
                with patch("sys.stdout", stream):
                    self.assertEqual(lottie_images.main(command), 0)
                report = json.loads(stream.getvalue())
                self.assertEqual(report["written"], written)
                self.assertEqual(report["sourceSha256"], project.digest(original))
                self.assertEqual(report["owner"], "camtasia-lottie-images")
                self.assertEqual(report["schema_version"], 1)
                self.assertFalse(report["nativeVerified"])
            saved = output.read_bytes()
            stream = io.StringIO()
            with patch("sys.stdout", stream):
                self.assertEqual(
                    lottie_images.main(["inspect", str(output), "--require-embedded"]), 0
                )
            changed = fixture()
            changed["future"]["colors"] = [0, 0, 1, 1]
            source.write_bytes(project.encode_document(changed))
            with patch("sys.stderr", io.StringIO()):
                self.assertEqual(lottie_images.main(command), 1)
            self.assertEqual(output.read_bytes(), saved)
            self.assertEqual(image.read_bytes(), png())

    def test_cli_refuses_source_alias_output_symlinks_and_input_races(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, image, output = [root / n for n in ("source.json", "image.png", "out.json")]
            source.write_bytes(project.encode_document(fixture()))
            image.write_bytes(png())
            original = source.read_bytes()
            base = ["embed", str(source), "--asset-id", "photo", "--image", str(image), "--output"]
            with patch("sys.stderr", io.StringIO()):
                self.assertEqual(lottie_images.main([*base, str(source)]), 1)
            output.symlink_to(image)
            with patch("sys.stderr", io.StringIO()):
                self.assertEqual(lottie_images.main([*base, str(output)]), 1)
            self.assertEqual(image.read_bytes(), png())
            output.unlink()
            before = image.stat()
            changed = SimpleNamespace(
                st_dev=before.st_dev,
                st_ino=before.st_ino,
                st_size=before.st_size + 1,
                st_mtime_ns=before.st_mtime_ns,
                st_ctime_ns=before.st_ctime_ns,
            )
            with (
                patch.object(os, "fstat", side_effect=[before, changed]),
                patch("sys.stderr", io.StringIO()),
            ):
                self.assertEqual(lottie_images.main([*base, str(output)]), 1)
            self.assertFalse(output.exists())
            self.assertEqual(source.read_bytes(), original)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX pipe fixture")
    def test_explicit_pipe_is_refused_without_blocking(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pipe = Path(directory) / "image.png"
            os.mkfifo(pipe)
            with self.assertRaisesRegex(ValueError, "regular PNG file"):
                lottie_images.read_image(pipe)

    def test_cli_never_follows_stored_image_or_font_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, image, output = [root / n for n in ("source.json", "image.png", "out.json")]
            source.write_bytes(project.encode_document(fixture()))
            image.write_bytes(png())
            read = Path.read_bytes
            allowed = {source.resolve(), image.resolve()}

            def selected_only(path: Path) -> bytes:
                self.assertIn(path.resolve(), allowed)
                return read(path)

            with (
                patch.object(Path, "read_bytes", selected_only),
                patch("sys.stdout", io.StringIO()),
            ):
                self.assertEqual(
                    lottie_images.main(
                        [
                            "embed",
                            str(source),
                            "--asset-id",
                            "photo",
                            "--image",
                            str(image),
                            "--output",
                            str(output),
                        ]
                    ),
                    0,
                )
