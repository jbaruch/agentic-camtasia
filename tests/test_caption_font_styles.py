from __future__ import annotations

import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from test_caption_block_transitions import grouped
from test_caption_decorations import fixture as decoration_fixture, run, spec, values
from test_caption_highlights import selected
import captions
import project


def fixture():
    doc = decoration_fixture()
    values(doc).extend(
        dict(name=name, rangeStart=0, rangeEnd=3, valueType="int", value=value)
        for name, value in (("fontWeight", 400), ("fontItalic", 0))
    )
    run(doc, "fontName")["value"] = "Arial"
    return doc


class CaptionFontStyleTests(unittest.TestCase):
    def test_independent_styles_combination_and_regular_reset_preserve_entire_root_or_group(self):
        for wrap in (lambda d: d, grouped):
            doc = wrap(fixture())
            before = copy.deepcopy(doc)
            both = dict(fontWeight=700, fontItalic=2)
            for changes in ({"fontWeight": 700}, {"fontItalic": 2}, both):
                expected = copy.deepcopy(doc)
                for name, value in changes.items():
                    run(expected, name)["value"] = value
                with self.subTest(grouped=wrap is grouped, changes=changes):
                    result = captions.set_display(doc, 6, spec(**changes))
                    self.assertEqual(result, expected)
                    self.assertEqual(captions.set_display(result, 6, spec(**changes)), result)
                    self.assertEqual(doc, before)
            combined = captions.set_display(doc, 6, spec(**both))
            for changes in ({"fontWeight": 400}, {"fontItalic": 0}):
                expected = copy.deepcopy(combined)
                for name, value in changes.items():
                    run(expected, name)["value"] = value
                self.assertEqual(captions.set_display(combined, 6, spec(**changes)), expected)
            reset = captions.set_display(combined, 6, spec(fontWeight=400, fontItalic=0))
            self.assertEqual(project.encode_document(reset), project.encode_document(doc))

    def test_request_and_existing_codes_require_observed_integers(self):
        for name, invalid in (
            ("fontWeight", (0, 100, 600, 900, True, False, 700.0, "700", None)),
            ("fontItalic", (-1, 1, 3, True, False, 2.0, "2", None)),
        ):
            for value in invalid:
                for existing in (False, True):
                    doc = fixture()
                    if existing:
                        run(doc, name)["value"] = value
                    before = copy.deepcopy(doc)
                    request = (
                        {name: 700 if name == "fontWeight" else 2} if existing else {name: value}
                    )
                    with self.subTest(name=name, value=value, existing=existing):
                        with self.assertRaises(ValueError):
                            captions.set_display(doc, 6, spec(**request))
                        self.assertEqual(doc, before)

    def test_missing_ambiguous_partial_or_animated_targets_refuse_atomically(self):
        for name in ("fontWeight", "fontItalic"):
            for shape in (
                "missing",
                "duplicate",
                "partial",
                "start",
                "range-type",
                "type",
                "missing-value",
                "animated",
                "nonzero-time",
                "empty",
            ):
                doc = fixture()
                target = run(doc, name)
                if shape == "missing":
                    values(doc).remove(target)
                elif shape == "duplicate":
                    values(doc).append(copy.deepcopy(target))
                elif shape == "partial":
                    target["rangeEnd"] = 1
                elif shape == "start":
                    target["rangeStart"] = 1
                elif shape == "range-type":
                    target["rangeEnd"] = 3.0
                elif shape == "type":
                    target["valueType"] = "double"
                elif shape == "missing-value":
                    del target["value"]
                elif shape == "animated":
                    frames = selected(doc)["def"]["textAttributes"]["keyframes"]
                    frames.append(copy.deepcopy(frames[0]))
                elif shape == "nonzero-time":
                    selected(doc)["def"]["textAttributes"]["keyframes"][0]["time"] = 1
                elif shape == "empty":
                    selected(doc)["def"]["text"] = ""
                    target["rangeEnd"] = 0
                before = copy.deepcopy(doc)
                with self.subTest(name=name, shape=shape), self.assertRaises(ValueError):
                    captions.set_display(doc, 6, spec(fontWeight=700, fontItalic=2))
                self.assertEqual(doc, before)

    def test_full_utf8_ranges_preserve_unrequested_partial_decorations_and_rtf(self):
        doc = fixture()
        selected(doc)["def"]["text"] = "éZ"
        expected = copy.deepcopy(doc)
        run(expected, "fontWeight")["value"] = 700
        run(expected, "fontItalic")["value"] = 2
        self.assertEqual(captions.set_display(doc, 6, spec(fontWeight=700, fontItalic=2)), expected)
        self.assertEqual(run(expected, "underline")["rangeEnd"], 1)
        self.assertEqual(run(expected, "strikethrough")["rangeEnd"], 1)
        self.assertEqual(selected(expected)["metadata"]["default-text"], r"{\rtf1\ansi ABC}")

    def test_build_gate_preserves_existing_font_edits_on_earlier_build(self):
        doc = fixture()
        doc["authoringClientName"]["version"] = "2026.2.4"
        before = copy.deepcopy(doc)
        for name, value in (("fontWeight", 700), ("fontItalic", 2)):
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "2026.2.5"):
                captions.set_display(doc, 6, spec(fontSize=48, **{name: value}))
            self.assertEqual(doc, before)
        expected = copy.deepcopy(doc)
        run(expected, "fontSize")["value"] = 48.0
        self.assertEqual(captions.set_display(doc, 6, spec(fontSize=48)), expected)

    def test_cli_stages_idempotently_and_failed_combination_leaves_no_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, request, output = [
                Path(tmp) / n for n in ("source.json", "spec.json", "out.json")
            ]
            source.write_bytes(project.encode_document(fixture()))
            before = source.read_bytes()
            request.write_text(json.dumps(spec(fontWeight=700, fontItalic=2)))
            args = [
                "set-display",
                str(source),
                "--clip-id",
                "6",
                "--spec",
                str(request),
                "--output",
                str(output),
            ]
            for _ in range(2):
                stdout, stderr = io.StringIO(), io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    self.assertEqual(captions.main(args), 0, stderr.getvalue())
                self.assertFalse(json.loads(stdout.getvalue())["nativeVerified"])
                expected = fixture()
                run(expected, "fontWeight")["value"] = 700
                run(expected, "fontItalic")["value"] = 2
                self.assertEqual(project.load(output)[0], expected)
                self.assertEqual(source.read_bytes(), before)
            output.unlink()
            request.write_text(json.dumps(spec(fontWeight=700, fontItalic=1)))
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(captions.main(args), 1)
            self.assertFalse(output.exists())
            self.assertEqual(source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
