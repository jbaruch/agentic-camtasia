from __future__ import annotations

import base64
import copy
from decimal import Decimal
import io
import json
import os
from pathlib import Path
import struct
import subprocess
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
    def test_slotted_images_remain_unhandled_even_with_an_embedded_fallback(self) -> None:
        source = lottie_images.embed_png(fixture(), "photo", png())
        source["assets"][0]["sid"] = "picture-slot"
        source["slots"] = {"picture-slot": {"p": {"p": "external.png", "u": "/remote/"}}}
        before = copy.deepcopy(source)
        report = lottie_images.inventory(source)
        self.assertFalse(report["imageAssetsEmbedded"])
        self.assertEqual(report["unhandledAssetIds"], ["photo"])
        with self.assertRaisesRegex(ValueError, "slots"):
            lottie_images.embed_png(source, "photo", png())
        self.assertEqual(source, before)

    def test_sequences_cannot_be_replaced_or_pass_as_an_embedded_single_image(self) -> None:
        for embedded in (False, True):
            for with_dimensions in (False, True):
                source = (
                    lottie_images.embed_png(fixture(), "photo", png()) if embedded else fixture()
                )
                source["assets"][0]["t"] = "seq"
                if not with_dimensions:
                    del source["assets"][0]["w"], source["assets"][0]["h"]
                before = copy.deepcopy(source)
                report = lottie_images.inventory(source)
                self.assertFalse(report["imageAssetsEmbedded"])
                self.assertFalse(report["images"][0]["embeddedPNG"])
                self.assertEqual(report["unhandledAssetIds"], ["photo"])
                self.assertEqual(report["missingImageAssetIds"], [])
                self.assertEqual(
                    report["images"][0]["dimensions"], [2, 3] if with_dimensions else None
                )
                self.assertEqual(
                    report["images"][0]["referenceKind"],
                    "data-uri" if embedded else "absolute-path",
                )
                with self.assertRaisesRegex(ValueError, "sequences"):
                    lottie_images.embed_png(source, "photo", png())
                self.assertEqual(source, before)
                with tempfile.TemporaryDirectory() as directory:
                    path = Path(directory) / "source.json"
                    path.write_bytes(lottie_images.encode_document(source))
                    with (
                        patch("sys.stdout", io.StringIO()),
                        patch("sys.stderr", diagnostic := io.StringIO()),
                    ):
                        self.assertEqual(
                            lottie_images.main(
                                [
                                    "inspect",
                                    str(path),
                                    "--require-embedded",
                                ]
                            ),
                            1,
                        )
                    self.assertIn("inspect unresolved", json.loads(diagnostic.getvalue())["action"])

    def test_sound_and_data_file_assets_remain_unresolved_outside_the_image_gate(self) -> None:
        source = lottie_images.embed_png(fixture(), "photo", png())
        source["assets"].extend(
            [
                {"id": "sound", "p": "sound.wav", "u": "/audio/", "e": 0},
                {"id": "data", "p": "values.json", "u": "/data/", "t": 3},
            ]
        )
        source["layers"].append({"ty": 6, "refId": "sound", "ip": 0, "op": 120})
        report = lottie_images.inventory(source)
        self.assertEqual([row["assetId"] for row in report["images"]], ["photo"])
        self.assertEqual(report["unhandledAssetIds"], ["sound", "data"])
        self.assertTrue(report["imageAssetsEmbedded"])
        for asset_id in ("sound", "data"):
            with self.assertRaises(ValueError):
                lottie_images.embed_png(source, asset_id, png())
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.json"
            path.write_bytes(lottie_images.encode_document(source))
            with patch("sys.stdout", io.StringIO()):
                self.assertEqual(
                    lottie_images.main(["inspect", str(path), "--require-embedded"]), 0
                )
        source["layers"].append({"ty": 2, "refId": "sound"})
        report = lottie_images.inventory(source)
        self.assertFalse(report["imageAssetsEmbedded"])
        self.assertEqual(report["missingImageAssetIds"], [])
        self.assertIn("sound", report["unhandledAssetIds"])

    def test_effect_values_and_opaque_nested_objects_are_not_image_layers(self) -> None:
        source = lottie_images.embed_png(fixture(), "photo", png())
        color = {"ty": 2, "nm": "Color", "v": {"a": 0, "k": [1, 0, 0, 1]}}
        source["layers"][0]["ef"] = [copy.deepcopy(color)]
        source["assets"][1]["layers"][0]["ef"] = [copy.deepcopy(color)]
        source["future"]["layers"] = [{"ty": 2, "refId": "not-an-image-reference"}]
        report = lottie_images.inventory(source)
        self.assertTrue(report["imageAssetsEmbedded"])
        self.assertEqual(report["invalidImageReferencePaths"], [])
        self.assertEqual(report["missingImageAssetIds"], [])
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "source.json"
            path.write_bytes(lottie_images.encode_document(source))
            with patch("sys.stdout", stream := io.StringIO()):
                self.assertEqual(
                    lottie_images.main(["inspect", str(path), "--require-embedded"]), 0
                )
            self.assertTrue(json.loads(stream.getvalue())["imageAssetsEmbedded"])

    def test_compact_huge_decimal_image_dimensions_refuse_before_integer_conversion(self) -> None:
        for value in (Decimal("1e1000000"), Decimal("1e-1000000"), Decimal("2147483648")):
            source = fixture()
            source["assets"][0]["w"] = value
            report = lottie_images.inventory(source)
            self.assertFalse(report["imageAssetsEmbedded"])
            with self.assertRaisesRegex(ValueError, "dimensions"):
                lottie_images.embed_png(source, "photo", png())

    def test_boolean_embedded_flag_correction_reports_changed_with_json_types(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, image, output = [root / n for n in ("source.json", "image.png", "out.json")]
            candidate = lottie_images.embed_png(fixture(), "photo", png())
            candidate["assets"][0]["e"] = True
            source.write_bytes(lottie_images.encode_document(candidate))
            image.write_bytes(png())
            with patch("sys.stdout", stream := io.StringIO()):
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
            report = json.loads(stream.getvalue())
            self.assertTrue(report["changed"])
            self.assertTrue(report["written"])
            self.assertTrue(report["imageAssetsEmbedded"])
            self.assertIs(type(json.loads(output.read_bytes())["assets"][0]["e"]), int)
            self.assertIs(json.loads(source.read_bytes())["assets"][0]["e"], True)

    def test_deep_opaque_json_payload_refuses_at_cli_boundary_without_traceback(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.json"
            raw = project.encode_document(fixture()).rstrip()[:-1]
            # Inventory must copy/report font declarations even on interpreters
            # whose JSON parser accepts deeper nesting without recursion.
            raw = raw.replace(b'"fonts":', b'"originalFonts":')
            source.write_bytes(raw + b',"fonts":' + b"[" * 20000 + b"0" + b"]" * 20000 + b"}")
            result = subprocess.run(
                [
                    sys.executable,
                    "-B",
                    str(Path(lottie_images.__file__)),
                    "inspect",
                    str(source),
                ],
                capture_output=True,
                text=True,
            )
            self.assertEqual(result.returncode, 1)
            self.assertEqual(result.stdout, "")
            report = json.loads(result.stderr)
            self.assertFalse(report["ok"])
            self.assertIn("reduce", report["error"])
            self.assertIn("reduce source JSON nesting", report["action"])

    def test_cli_argument_failures_emit_json_with_exit_two(self) -> None:
        for command in ([], ["embed"], ["inspect"], ["unknown"]):
            with (
                patch("sys.stderr", stream := io.StringIO()),
                self.assertRaises(SystemExit) as error,
            ):
                lottie_images.main(command)
            self.assertEqual(error.exception.code, 2)
            report = json.loads(stream.getvalue())
            self.assertFalse(report["ok"])
            self.assertEqual(report["action"], "run --help")

    def test_unrepresentable_or_nonfinite_json_numbers_refuse_with_json_diagnostics(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.json"
            for value in ("1e99999999999999999999", "NaN", "Infinity", "-Infinity"):
                source.write_text('{"value":' + value + "}")
                with patch("sys.stderr", stream := io.StringIO()):
                    self.assertEqual(lottie_images.main(["inspect", str(source)]), 1)
                self.assertFalse(json.loads(stream.getvalue())["ok"])

    def test_cli_preserves_raw_json_decimal_clocks_and_opaque_precision(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, image, output = [root / n for n in ("source.json", "image.png", "out.json")]
            raw = project.encode_document(fixture()).replace(
                b'"fr":30', b'"fr":29.970000000000000001'
            )
            raw = raw.replace(b'"ip":0', b'"ip":0.000000000000000001')
            raw = raw.replace(b'"colors":[0.5,', b'"colors":[0.123456789012345678901,')
            source.write_bytes(raw)
            image.write_bytes(png())
            with patch("sys.stdout", io.StringIO()):
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
            before = json.loads(raw, parse_float=Decimal)
            after = json.loads(output.read_bytes(), parse_float=Decimal)
            self.assertEqual(after["fr"], Decimal("29.970000000000000001"))
            self.assertEqual(after["ip"], Decimal("0.000000000000000001"))
            self.assertEqual(after["future"]["colors"][0], Decimal("0.123456789012345678901"))
            for key in ("p", "u", "e"):
                after["assets"][0][key] = before["assets"][0][key]
            self.assertEqual(after, before)
            self.assertEqual(source.read_bytes(), raw)

    @unittest.skipUnless(hasattr(os, "link"), "hard-link fixture")
    def test_canonical_identical_hard_link_output_refuses_source_alias(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, image, output = [root / n for n in ("source.json", "image.png", "out.json")]
            candidate = lottie_images.embed_png(fixture(), "photo", png())
            raw = lottie_images.encode_document(candidate)
            source.write_bytes(raw)
            image.write_bytes(png())
            os.link(source, output)
            with patch("sys.stderr", stream := io.StringIO()):
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
                    1,
                )
            self.assertIn("not linked", json.loads(stream.getvalue())["error"])
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(output.read_bytes(), raw)

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
            b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", 2147483648, 1, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", b"a")
            + chunk(b"IEND", b""),
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
            with patch("sys.stdout", stream), patch("sys.stderr", diagnostic := io.StringIO()):
                self.assertEqual(
                    lottie_images.main(["inspect", str(source), "--require-embedded"]), 1
                )
            self.assertFalse(json.loads(stream.getvalue())["imageAssetsEmbedded"])
            refusal = json.loads(diagnostic.getvalue())
            self.assertFalse(refusal["ok"])
            self.assertIn("embedding requirement", refusal["error"])
            self.assertIn("inspect unresolved", refusal["action"])
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
                patch.object(
                    os, "fstat", side_effect=[source.stat(), source.stat(), before, changed]
                ),
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

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX pipe fixture")
    def test_source_pipe_is_refused_without_waiting_for_a_writer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            pipe = Path(directory) / "source.json"
            os.mkfifo(pipe)
            with patch("sys.stderr", stream := io.StringIO()):
                self.assertEqual(lottie_images.main(["inspect", str(pipe)]), 1)
            report = json.loads(stream.getvalue())
            self.assertIn("regular Lottie source JSON", report["error"])
            self.assertIn("select", report["action"])

    def test_cli_source_image_json_and_output_errors_include_specific_actions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, image = root / "source.json", root / "image.png"

            def failure(command: list[str]) -> dict:
                with patch("sys.stderr", stream := io.StringIO()):
                    self.assertEqual(lottie_images.main(command), 1)
                report = json.loads(stream.getvalue())
                self.assertFalse(report["ok"])
                return report

            report = failure(["inspect", str(source)])
            self.assertIn("existing readable Lottie", report["action"])
            source.write_text("{invalid JSON}")
            self.assertIn("repair", failure(["inspect", str(source)])["error"])
            source.write_bytes(project.encode_document(fixture()))
            command = [
                "embed",
                str(source),
                "--asset-id",
                "photo",
                "--image",
                str(image),
                "--output",
            ]
            self.assertIn("readable PNG", failure([*command, str(root / "out.json")])["action"])
            image.write_bytes(png())
            self.assertIn(
                "create the output parent",
                failure([*command, str(root / "absent/out.json")])["action"],
            )

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
