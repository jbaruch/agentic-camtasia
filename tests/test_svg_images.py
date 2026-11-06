from __future__ import annotations

import base64
import io
import json
import os
from pathlib import Path
import sys
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/camtasia-project/scripts"))
import project  # noqa: E402
import svg_images  # noqa: E402
from test_lottie_images import png  # noqa: E402


def svg(href: bytes = b"photo.png", *, attributes: bytes = b"", children: bytes = b"") -> bytes:
    return (
        b'\xef\xbb\xbf<?xml version="1.0" encoding="UTF-8"?>\r\n<?keep untouched?>\r\n'
        b'<s:svg xmlns:s="http://www.w3.org/2000/svg" xmlns:l="http://www.w3.org/1999/xlink" '
        b'width="640" height="360" viewBox="0 0 640 360" version="1.2" baseProfile="tiny">\r\n'
        + "<s:title>Café — 漢字</s:title>".encode()
        + b'<!-- <s:image id="fake" l:href="unused.png"/> -->\r\n'
        b'<s:g transform="translate(0.123456789012345678901 2)">'
        b'<s:image id="photo" width="13" height="17" x="1.00000000000000000001" '
        b"data-note='a > b &quot; untouched' l:href = '"
        + href
        + b"' "
        + attributes
        + b">"
        + children
        + b'</s:image></s:g><s:text font-family="Uninstalled" '
        b'style="font-weight:600">ABC</s:text></s:svg>\r\n'
    )


def uri() -> bytes:
    return b"data:image/png;base64," + base64.b64encode(png())


class SVGImageTests(unittest.TestCase):
    def test_embedding_changes_only_the_selected_href_value_bytes(self) -> None:
        raw = svg()
        candidate, index = svg_images.embed_png(svg_images.Document(raw), png(), image_id="photo")
        self.assertEqual(index, 0)
        self.assertEqual(candidate, raw.replace(b"'photo.png'", b"'" + uri() + b"'"))
        self.assertIn(b'width="13" height="17"', candidate)
        self.assertIn(b"0.123456789012345678901", candidate)
        self.assertEqual(svg_images.Document(raw).raw, raw)

    def test_png_physical_dimensions_are_independent_of_svg_viewport_geometry(self) -> None:
        candidate, _ = svg_images.embed_png(svg_images.Document(svg()), png(7, 11), image_index=0)
        row = svg_images.inventory(svg_images.Document(candidate))["images"][0]
        self.assertEqual(row["dimensions"], [7, 11])
        self.assertIn(b'width="13" height="17"', candidate)
        self.assertTrue(row["embeddedPNG"])

    def test_inventory_reports_embedded_hashes_without_echoing_data_urls(self) -> None:
        report = svg_images.inventory(svg_images.Document(svg(uri())))
        self.assertTrue(report["imageAssetsEmbedded"])
        row = report["images"][0]
        self.assertEqual(row["imageIndex"], 0)
        self.assertEqual(row["id"], "photo")
        self.assertEqual(row["pngSha256"], project.digest(png()))
        self.assertEqual(row["sizeBytes"], len(png()))
        self.assertIsNone(row["references"][0]["value"])
        self.assertNotIn("base64", json.dumps(report))
        self.assertEqual(
            report["fontStyleDeclarations"][0]["attributes"]["font-family"], "Uninstalled"
        )

    def test_reference_kinds_are_lexical_without_opening_stored_paths(self) -> None:
        for href, kind in [
            (b"images/x.png", "relative-path"),
            (b"/original/x.png", "absolute-path"),
            (b"file:///original/x.png", "file-uri"),
            (b"https://example.test/x.png", "remote"),
            (b"C:\\media\\x.png", "windows-path"),
            (b"#internal", "fragment"),
        ]:
            with patch.object(Path, "read_bytes", side_effect=AssertionError("Unexpected read")):
                report = svg_images.inventory(svg_images.Document(svg(href)))
            self.assertEqual(report["images"][0]["references"][0]["referenceKind"], kind)
            self.assertFalse(report["imageAssetsEmbedded"])

    def test_plain_href_and_equal_dual_references_preserve_spelling(self) -> None:
        for raw in [svg().replace(b"l:href =", b"href ="), svg(attributes=b'href="photo.png"')]:
            candidate, _ = svg_images.embed_png(svg_images.Document(raw), png(), image_index=0)
            self.assertEqual(candidate, raw.replace(b"photo.png", uri()))
            self.assertTrue(
                svg_images.inventory(svg_images.Document(candidate))["imageAssetsEmbedded"]
            )

    def test_conflicting_or_missing_references_refuse_without_changing_input(self) -> None:
        for raw in [
            svg(attributes=b'href="different.png"'),
            svg().replace(b"l:href = 'photo.png'", b""),
        ]:
            document = svg_images.Document(raw)
            self.assertFalse(svg_images.inventory(document)["imageAssetsEmbedded"])
            with self.assertRaisesRegex(ValueError, "unambiguous"):
                svg_images.embed_png(document, png(), image_index=0)
            self.assertEqual(document.raw, raw)

    def test_namespace_declarations_in_attribute_order_and_entities_keep_byte_spans(self) -> None:
        raw = svg(b"photo&#x2e;png").replace(
            b"l:href =", b'xmlns:q="urn:future" q:keep="data" l:href ='
        )
        candidate, _ = svg_images.embed_png(svg_images.Document(raw), png(), image_index=0)
        self.assertEqual(candidate, raw.replace(b"photo&#x2e;png", uri()))
        self.assertEqual(
            svg_images.Document(raw).images[0].value(svg_images.XLINK_HREF), "photo.png"
        )

    def test_multiple_images_have_independent_document_order_and_selection(self) -> None:
        raw = svg().replace(
            b"</s:g>", b'<s:image xml:id="second" width="2" height="3" href="other.png"/></s:g>'
        )
        candidate, index = svg_images.embed_png(svg_images.Document(raw), png(), image_id="second")
        self.assertEqual(index, 1)
        self.assertEqual(candidate, raw.replace(b'"other.png"', b'"' + uri() + b'"'))
        report = svg_images.inventory(svg_images.Document(candidate))
        self.assertFalse(report["imageAssetsEmbedded"])
        self.assertFalse(report["images"][0]["embeddedPNG"])
        self.assertTrue(report["images"][1]["embeddedPNG"])

    def test_foreign_namespace_images_and_cdata_markup_are_not_svg_images(self) -> None:
        raw = svg(uri()).replace(
            b"</s:svg>",
            b'<q:image xmlns:q="urn:other" href="not-svg.png"/>'
            b'<s:style><![CDATA[/* <image href="not-markup.png"/> */]]></s:style></s:svg>',
        )
        report = svg_images.inventory(svg_images.Document(raw))
        self.assertEqual(len(report["images"]), 1)
        self.assertTrue(report["imageAssetsEmbedded"])
        self.assertEqual(report["otherReferences"][0]["value"], "not-svg.png")
        self.assertIn("not-markup.png", report["styleText"][0]["text"])
        self.assertIn("no full", report["limits"][0])

    def test_duplicate_ids_refuse_even_with_index_selection(self) -> None:
        raw = svg(uri()).replace(b"</s:svg>", b'<s:rect id="photo"/></s:svg>')
        document = svg_images.Document(raw)
        self.assertEqual(svg_images.inventory(document)["duplicateIds"], ["photo"])
        self.assertFalse(svg_images.inventory(document)["imageAssetsEmbedded"])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            svg_images.embed_png(document, png(), image_index=0)

    def test_same_element_id_and_xml_id_are_not_duplicate_owners(self) -> None:
        report = svg_images.inventory(svg_images.Document(svg(uri(), attributes=b'xml:id="photo"')))
        self.assertEqual(report["duplicateIds"], [])
        self.assertTrue(report["imageAssetsEmbedded"])

    def test_animated_hrefs_cannot_pass_as_static_embedded_images(self) -> None:
        for raw in [
            svg(uri(), children=b'<s:set attributeName="l:href" to="external.png"/>'),
            svg(uri()).replace(
                b"</s:svg>",
                b'<s:animate href="#photo" l:href="#photo" attributeName="href" values="a.png;b.png"/></s:svg>',
            ),
        ]:
            document = svg_images.Document(raw)
            self.assertFalse(svg_images.inventory(document)["imageAssetsEmbedded"])
            self.assertTrue(svg_images.inventory(document)["dynamicImageReferences"])
            with self.assertRaisesRegex(ValueError, "animated"):
                svg_images.embed_png(document, png(), image_index=0)

    def test_animation_of_other_attributes_or_foreign_href_does_not_change_static_reference(
        self,
    ) -> None:
        for child in [
            b'<s:animate attributeName="opacity" values="0;1"/>',
            b'<s:set xmlns:q="urn:metadata" attributeName="q:href" to="opaque"/>',
        ]:
            raw = svg(uri(), children=child)
            self.assertTrue(svg_images.inventory(svg_images.Document(raw))["imageAssetsEmbedded"])

    def test_scripts_and_event_attributes_are_not_certified_static_images(self) -> None:
        for raw in [
            svg(uri(), attributes=b'onload="changeImage()"'),
            svg(uri()).replace(b"</s:svg>", b"<s:script>unexecuted()</s:script></s:svg>"),
        ]:
            document = svg_images.Document(raw)
            self.assertFalse(svg_images.inventory(document)["imageAssetsEmbedded"])
            with self.assertRaisesRegex(ValueError, "active"):
                svg_images.embed_png(document, png(), image_index=0)

    def test_svg_handlers_and_xml_events_cannot_pass_the_static_image_gate(self) -> None:
        for child in [
            b'<s:handler xmlns:ev="http://www.w3.org/2001/xml-events" ev:event="load">'
            b"changeImage()</s:handler>",
            b'<s:handler l:href="https://example.test/handler.js"/>',
            b'<e:listener xmlns:e="http://www.w3.org/2001/xml-events" '
            b'event="load" observer="photo" handler="https://example.test/handler.svg#run"/>',
            b'<s:g xmlns:events="http://www.w3.org/2001/xml-events" '
            b'events:event="load" events:handler="https://example.test/handler.svg#run"/>',
        ]:
            with self.subTest(child=child):
                raw = svg(uri(), children=child)
                document = svg_images.Document(raw)
                report = svg_images.inventory(document)
                self.assertEqual(report["activeElementIndices"], [4])
                self.assertFalse(report["imageAssetsEmbedded"])
                with self.assertRaisesRegex(ValueError, "active"):
                    svg_images.embed_png(document, png(), image_index=0)
                self.assertEqual(document.raw, raw)

    def test_unrelated_namespace_handlers_and_event_metadata_remain_opaque(self) -> None:
        raw = svg(
            uri(),
            children=b'<q:handler xmlns:q="urn:metadata" q:event="load" q:onclick="data"/>'
            b'<q:listener xmlns:q="urn:metadata" event="load" handler="opaque"/>',
        )
        document = svg_images.Document(raw)
        report = svg_images.inventory(document)
        self.assertEqual(report["activeElementIndices"], [])
        self.assertTrue(report["imageAssetsEmbedded"])
        candidate, _ = svg_images.embed_png(document, png(), image_index=0)
        self.assertEqual(candidate, raw)

    def test_other_resource_and_stylesheet_declarations_remain_unresolved(self) -> None:
        raw = svg(uri()).replace(
            b"<?keep untouched?>", b'<?xml-stylesheet href="https://example.test/a.css"?>'
        )
        raw = raw.replace(b"</s:svg>", b'<s:font-face-uri l:href="fonts/face.svg#face"/></s:svg>')
        report = svg_images.inventory(svg_images.Document(raw))
        self.assertTrue(report["imageAssetsEmbedded"])
        self.assertIn("example.test", report["stylesheetInstructions"][0])
        self.assertEqual(report["otherReferences"][0]["value"], "fonts/face.svg#face")
        self.assertIn("unresolved", report["limits"][1])

    def test_nonpng_mime_hint_refuses_instead_of_changing_other_attributes(self) -> None:
        raw = svg(attributes=b'type="image/jpeg"')
        with self.assertRaisesRegex(ValueError, "MIME"):
            svg_images.embed_png(svg_images.Document(raw), png(), image_index=0)

    def test_invalid_xml_encodings_dtd_entities_and_unqualified_roots_refuse(self) -> None:
        for raw in [
            b"<svg/>",
            b"<not-svg/>",
            b"<svg",
            b"\xff",
            svg().decode("utf-8-sig").encode("utf-16"),
            svg().replace(b"UTF-8", b"ISO-8859-1"),
            b'<!DOCTYPE svg SYSTEM "file:///unopened.dtd"><svg xmlns="http://www.w3.org/2000/svg"/>',
            b'<!DOCTYPE svg [<!ENTITY payload "content">]><svg xmlns="http://www.w3.org/2000/svg"/>',
            b'<svg xmlns="http://www.w3.org/2000/svg" a="1" a="2"/>',
        ]:
            with self.subTest(raw=raw[:30]), self.assertRaises(ValueError):
                svg_images.Document(raw)

    def test_bad_png_and_stale_or_ambiguous_selections_refuse(self) -> None:
        document = svg_images.Document(svg())
        cases: tuple[dict[str, Any], ...] = (
            {},
            {"image_id": "missing"},
            {"image_index": -1},
            {"image_index": True},
            {"image_index": 10},
            {"image_id": "photo", "image_index": 0},
        )
        for kwargs in cases:
            with self.assertRaises(ValueError):
                svg_images.embed_png(document, png(), **kwargs)
        with self.assertRaises(ValueError):
            svg_images.embed_png(document, b"not PNG", image_index=0)

    def test_cli_staging_hashes_idempotence_and_gate_streams(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, image, output = root / "in.svg", root / "image.png", root / "out.svg"
            raw = svg()
            source.write_bytes(raw)
            image.write_bytes(png())
            with (
                patch("sys.stdout", stdout := io.StringIO()),
                patch("sys.stderr", stderr := io.StringIO()),
            ):
                self.assertEqual(svg_images.main(["inspect", str(source), "--require-embedded"]), 1)
            self.assertFalse(json.loads(stdout.getvalue())["imageAssetsEmbedded"])
            self.assertIn("inspect", json.loads(stderr.getvalue())["action"])
            command = [
                "embed",
                str(source),
                "--expected-sha256",
                project.digest(raw),
                "--image-index",
                "0",
                "--image",
                str(image),
                "--output",
                str(output),
            ]
            for written in (True, False):
                with patch("sys.stdout", stdout := io.StringIO()):
                    self.assertEqual(svg_images.main(command), 0)
                report = json.loads(stdout.getvalue())
                self.assertEqual(report["written"], written)
                self.assertTrue(report["changed"])
                self.assertEqual(report["owner"], "camtasia-svg-images")
                self.assertEqual(report["schema_version"], 1)
                self.assertFalse(report["nativeVerified"])
                self.assertEqual(report["candidateSha256"], project.digest(output.read_bytes()))
            with patch("sys.stdout", io.StringIO()):
                self.assertEqual(svg_images.main(["inspect", str(output), "--require-embedded"]), 0)
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(image.read_bytes(), png())
            source.write_bytes(raw + b"\n")
            with patch("sys.stderr", stderr := io.StringIO()):
                self.assertEqual(svg_images.main(command), 1)
            self.assertIn("changed SVG", json.loads(stderr.getvalue())["error"])

    def test_existing_candidate_source_hardlink_symlink_and_image_aliases_refuse(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.svg"
            output = root / "out.svg"
            image = root / "image.png"
            raw = svg(uri())
            source.write_bytes(raw)
            image.write_bytes(png())
            for target in (source, image):
                with self.assertRaises(ValueError):
                    svg_images.stage(source, target, raw)
            os.link(source, output)
            with self.assertRaises(ValueError):
                svg_images.stage(source, output, raw)
            output.unlink()
            output.symlink_to(root / "missing.svg")
            with self.assertRaises(ValueError):
                svg_images.stage(source, output, raw)
            output.unlink()
            output.write_bytes(b"occupied")
            with self.assertRaises(ValueError):
                svg_images.stage(source, output, raw)
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(image.read_bytes(), png())
            self.assertEqual(output.read_bytes(), b"occupied")

    def test_cli_argument_and_file_errors_include_json_actions(self) -> None:
        for command in ([], ["embed"], ["inspect"], ["bad"]):
            with (
                patch("sys.stderr", stderr := io.StringIO()),
                self.assertRaises(SystemExit) as error,
            ):
                svg_images.main(command)
            self.assertEqual(error.exception.code, 2)
            self.assertIn("help", json.loads(stderr.getvalue())["action"])
        with tempfile.TemporaryDirectory() as directory:
            with patch("sys.stderr", stderr := io.StringIO()):
                self.assertEqual(
                    svg_images.main(["inspect", str(Path(directory) / "missing.svg")]), 1
                )
            self.assertIn("readable UTF-8 SVG", json.loads(stderr.getvalue())["action"])

    def test_cli_reads_only_explicit_inputs_and_keeps_other_resource_declarations(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, image, output = root / "source.svg", root / "chosen.png", root / "out.svg"
            raw = svg(b"/unopened/original.png").replace(
                b"</s:svg>",
                b'<s:font-face-uri l:href="https://example.test/unfetched-font.svg"/></s:svg>',
            )
            source.write_bytes(raw)
            image.write_bytes(png())
            allowed = {source, image}
            reader = svg_images.lottie_images.read_file
            observed = []

            def explicit_only(path: Path, kind: str) -> bytes:
                self.assertIn(path, allowed)
                observed.append(path)
                return reader(path, kind)

            with (
                patch.object(svg_images.lottie_images, "read_file", explicit_only),
                patch("sys.stdout", io.StringIO()),
            ):
                self.assertEqual(
                    svg_images.main(
                        [
                            "embed",
                            str(source),
                            "--expected-sha256",
                            project.digest(raw),
                            "--image-id",
                            "photo",
                            "--image",
                            str(image),
                            "--output",
                            str(output),
                        ]
                    ),
                    0,
                )
            self.assertEqual(observed, [source, image])
            self.assertIn(b"https://example.test/unfetched-font.svg", output.read_bytes())
            self.assertEqual(source.read_bytes(), raw)

    @unittest.skipUnless(hasattr(os, "mkfifo"), "POSIX pipe fixture")
    def test_svg_source_fifo_refuses_without_waiting_for_a_writer(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "pipe.svg"
            os.mkfifo(source)
            with patch("sys.stderr", stderr := io.StringIO()):
                self.assertEqual(svg_images.main(["inspect", str(source)]), 1)
            self.assertIn("regular SVG source", json.loads(stderr.getvalue())["error"])


if __name__ == "__main__":
    unittest.main()
