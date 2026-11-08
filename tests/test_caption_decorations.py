from __future__ import annotations

import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from test_caption_block_transitions import grouped
from test_caption_highlights import selected
from test_caption_layout import fixture as layout_fixture
import captions
import project


def fixture():
    doc = layout_fixture()
    doc["authoringClientName"]["version"] = "2026.2.5"
    selected(doc).setdefault("metadata", {})["default-text"] = r"{\rtf1\ansi ABC}"
    return doc


def values(doc):
    return selected(doc)["def"]["textAttributes"]["keyframes"][0]["value"]


def run(doc, name):
    return next(r for r in values(doc) if r["name"] == name)


def spec(**changes):
    return dict(schema_version=1, rich=changes)


class CaptionDecorationTests(unittest.TestCase):
    def test_enable_changes_only_requested_style_and_preserves_words_resets_and_ancestors(self):
        for wrap in (lambda d: d, grouped):
            doc = wrap(fixture())
            before = copy.deepcopy(doc)
            for requested in (
                {"underline": 1},
                {"strikethrough": 1},
                {"underline": 1, "strikethrough": 1},
            ):
                expected = copy.deepcopy(doc)
                for name in requested:
                    run(expected, name).update(value=1, rangeEnd=3)
                with self.subTest(grouped=wrap is grouped, requested=requested):
                    result = captions.set_display(doc, 6, spec(**requested))
                    self.assertEqual(result, expected)
                    self.assertEqual(doc, before)
                    self.assertEqual(captions.set_display(result, 6, spec(**requested)), result)

    def test_clear_keeps_inactive_prefixes_and_retains_full_ranges_after_enable(self):
        for wrap in (lambda d: d, grouped):
            doc = wrap(fixture())
            clear = spec(underline=0, strikethrough=0)
            result = captions.set_display(doc, 6, clear)
            self.assertEqual(project.encode_document(result), project.encode_document(doc))
            enabled = captions.set_display(doc, 6, spec(underline=1, strikethrough=1))
            expected = copy.deepcopy(doc)
            for name in ("underline", "strikethrough"):
                run(expected, name)["rangeEnd"] = 3
            cleared = captions.set_display(enabled, 6, clear)
            self.assertEqual(cleared, expected)
            self.assertEqual(captions.set_display(cleared, 6, clear), cleared)

    def test_native_caption_flags_reject_signed_annotation_codes_and_noninteger_inputs(self):
        for name in ("underline", "strikethrough"):
            for value in (-1, 2, True, False, 1.0, "1", None):
                doc = fixture()
                before = copy.deepcopy(doc)
                with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                    captions.set_display(doc, 6, spec(**{name: value}))
                self.assertEqual(doc, before)

    def test_ambiguous_or_unverified_targets_refuse_without_partial_changes(self):
        for shape in (
            "missing",
            "duplicate",
            "active-prefix",
            "other-prefix",
            "nonzero-start",
            "range-type",
            "value-type",
            "missing-value",
            "signed-value",
            "bool-value",
            "float-value",
            "animated",
            "nonzero-time",
            "empty",
            "split-character",
        ):
            doc = fixture()
            target = run(doc, "strikethrough")
            if shape == "missing":
                values(doc).remove(target)
            elif shape == "duplicate":
                values(doc).append(copy.deepcopy(target))
            elif shape == "active-prefix":
                target["value"] = 1
            elif shape == "other-prefix":
                target["rangeEnd"] = 2
            elif shape == "nonzero-start":
                target.update(rangeStart=1, rangeEnd=3)
            elif shape == "range-type":
                target["rangeEnd"] = 3.0
            elif shape == "value-type":
                target["valueType"] = "double"
            elif shape == "missing-value":
                del target["value"]
            elif shape == "signed-value":
                target["value"] = -1
            elif shape == "bool-value":
                target["value"] = False
            elif shape == "float-value":
                target["value"] = 0.0
            elif shape == "animated":
                frames = selected(doc)["def"]["textAttributes"]["keyframes"]
                frames.append(copy.deepcopy(frames[0]))
            elif shape == "nonzero-time":
                selected(doc)["def"]["textAttributes"]["keyframes"][0]["time"] = 1
            elif shape == "empty":
                selected(doc)["def"]["text"] = ""
            elif shape == "split-character":
                selected(doc)["def"]["text"] = "éZ"
                run(doc, "underline")["rangeEnd"] = 3
            before = copy.deepcopy(doc)
            with self.subTest(shape=shape), self.assertRaises(ValueError):
                captions.set_display(doc, 6, spec(underline=1, strikethrough=1))
            self.assertEqual(doc, before)

    def test_full_unicode_ranges_and_build_gate_leave_existing_font_support_intact(self):
        doc = fixture()
        selected(doc)["def"]["text"] = "éZ"
        for name in ("underline", "strikethrough"):
            run(doc, name)["rangeEnd"] = 3
        expected = copy.deepcopy(doc)
        for name in ("underline", "strikethrough"):
            run(expected, name)["value"] = 1
        self.assertEqual(captions.set_display(doc, 6, spec(underline=1, strikethrough=1)), expected)
        doc = fixture()
        doc["authoringClientName"]["version"] = "2026.2.4"
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "2026.2.5"):
            captions.set_display(doc, 6, spec(fontSize=64, underline=1))
        self.assertEqual(doc, before)
        expected = copy.deepcopy(doc)
        run(expected, "fontSize")["value"] = 64.0
        self.assertEqual(captions.set_display(doc, 6, spec(fontSize=64)), expected)

    def test_cli_stages_idempotently_and_refuses_without_writing_source_or_candidate(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, request, output = [
                Path(tmp) / n for n in ("source.json", "spec.json", "out.json")
            ]
            source.write_bytes(project.encode_document(fixture()))
            before = source.read_bytes()
            request.write_text(json.dumps(spec(underline=1, strikethrough=1)))
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
                for name in ("underline", "strikethrough"):
                    run(expected, name).update(value=1, rangeEnd=3)
                self.assertEqual(project.load(output)[0], expected)
                self.assertEqual(source.read_bytes(), before)
            output.unlink()
            request.write_text(json.dumps(spec(underline=1, strikethrough=-1)))
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(captions.main(args), 1)
            self.assertFalse(output.exists())
            self.assertEqual(source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
