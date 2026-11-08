from __future__ import annotations

import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from test_caption_block_transitions import fixture as transition_fixture, grouped
from test_caption_highlights import selected
import annotations
import project


INITIAL = {
    "horizontal-alignment": "center",
    "vertical-alignment": "center",
    "resize-behavior": "resizeCallout",
    "enable-ligatures": 1.0,
    "word-wrap": 1.0,
    "text-stroke-alignment": 2.0,
}
CHANGES = {
    "horizontal-alignment": "left",
    "vertical-alignment": "top",
    "resize-behavior": "resizeText",
    "enable-ligatures": 0,
    "word-wrap": 0,
    "text-stroke-alignment": 1,
}


def fixture():
    doc = transition_fixture("", 1.0, 0.8)
    definition = selected(doc)["def"]
    definition.update(INITIAL)
    definition.update(width=600.0, height=160.0)
    definition["textAttributes"]["keyframes"][0]["value"].extend(
        [
            dict(name="strikethrough", rangeStart=0, rangeEnd=1, valueType="int", value=0),
            dict(name="kerning", rangeStart=0, rangeEnd=3, valueType="double", value=-0.02),
        ]
    )
    return doc


class CaptionLayoutTests(unittest.TestCase):
    def test_root_and_group_layout_only_edits_preserve_partial_styles_and_all_other_payload(self):
        for wrap in (lambda d: d, grouped):
            doc = wrap(fixture())
            before = copy.deepcopy(doc)
            expected = copy.deepcopy(doc)
            selected(expected)["def"].update(CHANGES)
            with self.subTest(grouped=wrap is grouped):
                result = annotations.edit_annotation(
                    doc, 6, dict(schema_version=1, definition=CHANGES)
                )
                self.assertEqual(result, expected)
                self.assertEqual(doc, before)
                restored = annotations.edit_annotation(
                    result, 6, dict(schema_version=1, definition=INITIAL)
                )
                self.assertEqual(restored, before)
                self.assertEqual(
                    annotations.edit_annotation(
                        result, 6, dict(schema_version=1, definition=CHANGES)
                    ),
                    result,
                )

    def test_dynamic_layout_refusals_are_atomic_and_keep_existing_parameter_forms(self):
        for name, value in (
            ("horizontal-alignment", "start"),
            ("vertical-alignment", "middle"),
            ("resize-behavior", "fit"),
            ("enable-ligatures", True),
            ("enable-ligatures", 0.5),
            ("word-wrap", -1),
            ("word-wrap", None),
            ("text-stroke-alignment", 3),
            ("text-stroke-alignment", float("nan")),
        ):
            doc = fixture()
            before = copy.deepcopy(doc)
            request = dict(CHANGES)
            request[name] = value
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                annotations.edit_annotation(doc, 6, dict(schema_version=1, definition=request))
            self.assertEqual(doc, before)
        for value in (
            None,
            {"type": "double"},
            {"type": "double", "defaultValue": 1, "keyframes": [{"time": 0, "value": 1}]},
        ):
            doc = fixture()
            if value is None:
                del selected(doc)["def"]["word-wrap"]
            else:
                selected(doc)["def"]["word-wrap"] = value
            before = copy.deepcopy(doc)
            with self.subTest(value=value), self.assertRaises(ValueError):
                annotations.edit_annotation(doc, 6, dict(schema_version=1, definition=CHANGES))
            self.assertEqual(doc, before)
        doc = fixture()
        selected(doc)["def"]["word-wrap"] = dict(
            type="double", defaultValue=1.0, keyframes=[], opaque=["keep"]
        )
        expected = copy.deepcopy(doc)
        selected(expected)["def"]["word-wrap"]["defaultValue"] = 0.0
        self.assertEqual(
            annotations.edit_annotation(
                doc, 6, dict(schema_version=1, definition={"word-wrap": 0})
            ),
            expected,
        )

    def test_uniform_rich_edit_still_refuses_partial_caption_ranges_without_flattening(self):
        doc = fixture()
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "partial|coverage"):
            annotations.edit_annotation(doc, 6, dict(schema_version=1, rich={"fontSize": 48}))
        self.assertEqual(doc, before)

    def test_existing_annotation_cli_stages_caption_layout_without_writing_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, request, output = [
                Path(tmp) / n for n in ("source.json", "spec.json", "out.json")
            ]
            source.write_bytes(project.encode_document(fixture()))
            original = source.read_bytes()
            request.write_text(json.dumps(dict(schema_version=1, definition=CHANGES)))
            args = [
                "set",
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
                    self.assertEqual(annotations.main(args), 0, stderr.getvalue())
                self.assertFalse(json.loads(stdout.getvalue())["nativeVerified"])
                expected = fixture()
                selected(expected)["def"].update(CHANGES)
                self.assertEqual(project.load(output)[0], expected)
                self.assertEqual(source.read_bytes(), original)
            output.unlink()
            request.write_text(json.dumps(dict(schema_version=1, definition={"word-wrap": True})))
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(annotations.main(args), 1)
            self.assertFalse(output.exists())
            self.assertEqual(source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
