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
import captions
import project


INITIAL = {
    "horizontal-alignment": "center",
    "vertical-alignment": "center",
    "resize-behavior": "resizeCallout",
    "enable-ligatures": 1.0,
    "word-wrap": 1.0,
    "text-stroke-alignment": 2.0,
    "line-spacing": 0.0,
}
CHANGES = {
    "horizontal-alignment": "left",
    "vertical-alignment": "top",
    "resize-behavior": "resizeText",
    "enable-ligatures": 0,
    "word-wrap": 0,
    "text-stroke-alignment": 1,
    "line-spacing": 1.5,
}


def fixture():
    doc = transition_fixture("", 1.0, 0.8)
    definition = selected(doc)["def"]
    definition.update(INITIAL)
    definition.update(width=600.0, height=160.0)
    selected(doc).setdefault("metadata", {})["default-callout-line-spacing"] = "0"
    definition["textAttributes"]["keyframes"][0]["value"].extend(
        [
            dict(name="strikethrough", rangeStart=0, rangeEnd=1, valueType="int", value=0),
            dict(name="kerning", rangeStart=0, rangeEnd=3, valueType="double", value=-0.02),
        ]
    )
    return doc


class CaptionLayoutTests(unittest.TestCase):
    def test_current_box_and_explicit_font_edits_preserve_words_styles_and_group_bounds(self):
        for wrap in (lambda d: d, grouped):
            doc = fixture()
            doc["authoringClientName"]["version"] = "2026.2.5"
            font = next(
                r
                for r in selected(doc)["def"]["textAttributes"]["keyframes"][0]["value"]
                if r["name"] == "fontSize"
            )
            font["value"] = 96.0
            doc = wrap(doc)
            if wrap is grouped:
                group = next(n for _, n in project.objects(doc) if n.get("_type") == "Group")
                group["attributes"].update(widthAttr=608.0, heightAttr=168.0)
                group["parameters"].update(translation1=-338.0, volume=1.0)
            before = copy.deepcopy(doc)
            for width, height in ((600.0, 40.0), (240.0, 160.0), (240.0, 40.0)):
                geometry = dict(schema_version=1, definition={"width": width, "height": height})
                style = dict(schema_version=1, rich={"fontSize": 32})
                expected = copy.deepcopy(doc)
                selected(expected)["def"].update(width=width, height=height)
                next(
                    r
                    for r in selected(expected)["def"]["textAttributes"]["keyframes"][0]["value"]
                    if r["name"] == "fontSize"
                )["value"] = 32.0
                with self.subTest(grouped=wrap is grouped, width=width, height=height):
                    candidate = annotations.edit_annotation(doc, 6, geometry)
                    result = captions.set_display(candidate, 6, style)
                    self.assertEqual(result, expected)
                    self.assertEqual(doc, before)
                    self.assertEqual(
                        captions.set_display(
                            annotations.edit_annotation(result, 6, geometry), 6, style
                        ),
                        result,
                    )

    def test_caption_box_edits_refuse_invalid_or_missing_dimensions_without_source_changes(self):
        for name, value in (
            ("width", 0),
            ("width", True),
            ("height", "-1/2"),
            ("height", float("nan")),
        ):
            doc = fixture()
            before = copy.deepcopy(doc)
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                annotations.edit_annotation(
                    doc, 6, dict(schema_version=1, definition={name: value})
                )
            self.assertEqual(doc, before)
        doc = fixture()
        del selected(doc)["def"]["height"]
        before = copy.deepcopy(doc)
        with self.assertRaises(ValueError):
            annotations.edit_annotation(doc, 6, dict(schema_version=1, definition={"height": 40}))
        self.assertEqual(doc, before)

    def test_current_alignment_choices_preserve_partial_styles_resets_and_group_geometry(self):
        for wrap in (lambda d: d, grouped):
            doc = fixture()
            doc["authoringClientName"]["version"] = "2026.2.5"
            selected(doc).setdefault("metadata", {}).update(
                {
                    "default-text": r"{\rtf1\ansi ABC}",
                    "default-callout-vertical-alignment": "center",
                }
            )
            doc = wrap(doc)
            before = copy.deepcopy(doc)
            for horizontal, vertical in (
                ("left", "top"),
                ("right", "bottom"),
                ("center", "center"),
            ):
                changes = {"horizontal-alignment": horizontal, "vertical-alignment": vertical}
                expected = copy.deepcopy(doc)
                selected(expected)["def"].update(changes)
                with self.subTest(grouped=wrap is grouped, changes=changes):
                    result = annotations.edit_annotation(
                        doc, 6, dict(schema_version=1, definition=changes)
                    )
                    self.assertEqual(result, expected)
                    self.assertEqual(doc, before)
                    self.assertEqual(
                        annotations.edit_annotation(
                            result, 6, dict(schema_version=1, definition=changes)
                        ),
                        result,
                    )
                    self.assertEqual(
                        annotations.edit_annotation(
                            result,
                            6,
                            dict(
                                schema_version=1,
                                definition={
                                    "horizontal-alignment": "center",
                                    "vertical-alignment": "center",
                                },
                            ),
                        ),
                        before,
                    )

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
            ("line-spacing", -1),
            ("line-spacing", "31/10"),
            ("line-spacing", True),
        ):
            doc = fixture()
            before = copy.deepcopy(doc)
            request = dict(CHANGES)
            request[name] = value
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                annotations.edit_annotation(doc, 6, dict(schema_version=1, definition=request))
            self.assertEqual(doc, before)
        for name, initial, changed in (("word-wrap", 1.0, 0.0), ("line-spacing", 0.0, 1.5)):
            for value in (
                None,
                {"type": "double"},
                {"type": "double", "defaultValue": 1, "keyframes": [{"time": 0, "value": 1}]},
            ):
                doc = fixture()
                if value is None:
                    del selected(doc)["def"][name]
                else:
                    selected(doc)["def"][name] = value
                before = copy.deepcopy(doc)
                with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                    annotations.edit_annotation(doc, 6, dict(schema_version=1, definition=CHANGES))
                self.assertEqual(doc, before)
            doc = fixture()
            selected(doc)["def"][name] = dict(
                type="double", defaultValue=initial, keyframes=[], opaque=["keep"]
            )
            expected = copy.deepcopy(doc)
            selected(expected)["def"][name]["defaultValue"] = changed
            self.assertEqual(
                annotations.edit_annotation(
                    doc, 6, dict(schema_version=1, definition={name: changed})
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


class CaptionSpacingTests(unittest.TestCase):
    def current(self):
        doc = fixture()
        doc["authoringClientName"]["version"] = "2026.2.5"
        return doc

    def kerning(self, doc):
        return next(
            r
            for r in selected(doc)["def"]["textAttributes"]["keyframes"][0]["value"]
            if r["name"] == "kerning"
        )

    def test_current_root_and_group_spacing_preserves_partial_styles_sources_and_clocks(self):
        for wrap in (lambda d: d, grouped):
            doc = wrap(self.current())
            before = copy.deepcopy(doc)
            for value, expected_value in [("1/10", 0.1), ("-1/50", -0.02), (0, 0.0)]:
                expected = copy.deepcopy(doc)
                self.kerning(expected)["value"] = expected_value
                with self.subTest(grouped=wrap is grouped, value=value):
                    result = captions.set_display(
                        doc, 6, dict(schema_version=1, rich={"kerning": value})
                    )
                    self.assertEqual(result, expected)
                    self.assertEqual(doc, before)
                    self.assertEqual(
                        captions.set_display(
                            result, 6, dict(schema_version=1, rich={"kerning": value})
                        ),
                        result,
                    )
                    restored = captions.set_display(
                        result, 6, dict(schema_version=1, rich={"kerning": "-1/50"})
                    )
                    self.assertEqual(restored, before)

    def test_spacing_requires_one_existing_full_static_property_and_supported_build(self):
        for value in [True, None, "bad", float("nan"), float("inf")]:
            doc = self.current()
            before = copy.deepcopy(doc)
            with self.subTest(value=value), self.assertRaises(ValueError):
                captions.set_display(doc, 6, dict(schema_version=1, rich={"kerning": value}))
            self.assertEqual(doc, before)
        for change in ("missing", "partial", "duplicate", "type", "animated", "legacy"):
            doc = self.current()
            values = selected(doc)["def"]["textAttributes"]["keyframes"][0]["value"]
            target = self.kerning(doc)
            if change == "missing":
                values.remove(target)
            elif change == "partial":
                target["rangeEnd"] = 1
            elif change == "duplicate":
                values.append(copy.deepcopy(target))
            elif change == "type":
                target["valueType"] = "int"
            elif change == "animated":
                selected(doc)["def"]["textAttributes"]["keyframes"][0]["duration"] = 1
            else:
                doc["authoringClientName"]["version"] = "2026.2.4"
            before = copy.deepcopy(doc)
            with self.subTest(change=change), self.assertRaises(ValueError):
                captions.set_display(doc, 6, dict(schema_version=1, rich={"kerning": 0.1}))
            self.assertEqual(doc, before)
        legacy = fixture()
        self.assertEqual(
            selected(
                captions.set_display(legacy, 6, dict(schema_version=1, rich={"fontSize": 48}))
            )["def"]["textAttributes"]["keyframes"][0]["value"][0]["value"],
            48.0,
        )

    def test_caption_cli_stages_spacing_exclusively_and_retains_original_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, request, output = [
                root / name for name in ("source.json", "spec.json", "candidate.json")
            ]
            source.write_bytes(project.encode_document(self.current()))
            original = source.read_bytes()
            request.write_text(json.dumps(dict(schema_version=1, rich={"kerning": "1/10"})))
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
                expected = self.current()
                self.kerning(expected)["value"] = 0.1
                self.assertEqual(project.load(output)[0], expected)
                self.assertEqual(source.read_bytes(), original)
            output.unlink()
            request.write_text(json.dumps(dict(schema_version=1, rich={"kerning": True})))
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(captions.main(args), 1)
            self.assertFalse(output.exists())
            self.assertEqual(source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
