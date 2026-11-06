from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

from test_annotations import fixture, clip
import annotations
import project


def document():
    doc = fixture()
    clip(doc)["def"] = {
        "kind": "MacKey",
        "shape": "",
        "style": "",
        "height": 64.0,
        "width": 90.1111111111111,
        "corner-radius": 6.0,
        "keyStyle": 0.0,
        "showKeyBackg": 1.0,
        "showKeyHint": 0.0,
        "keys": "⌘ A",
        "name": "⌘ A",
        "opaque": ["retain"],
    }
    clip(doc)["metadata"].update({"default-callout-keys": "⌘ A"})
    return doc


class AnnotationKeystrokeTests(unittest.TestCase):
    def test_native_key_string_and_explicit_geometry_preserve_labels_resets_and_other_payload(self):
        doc = document()
        before = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        clip(expected)["def"].update(keys="⇧ ⌘ K", width=130.182454427083)
        settings = dict(schema_version=1, definition={"keys": "⇧ ⌘ K", "width": 130.182454427083})
        result = annotations.edit_annotation(doc, 3, settings)
        self.assertEqual(result, expected)
        self.assertEqual(doc, before)
        self.assertEqual(annotations.edit_annotation(result, 3, settings), result)
        self.assertEqual(clip(result)["def"]["name"], "⌘ A")

    def test_each_style_and_both_flags_edit_existing_saved_numeric_fields(self):
        for style in range(5):
            doc = document()
            expected = copy.deepcopy(doc)
            clip(expected)["def"].update(keyStyle=float(style), showKeyBackg=0.0, showKeyHint=1.0)
            with self.subTest(style=style):
                self.assertEqual(
                    annotations.edit_annotation(
                        doc,
                        3,
                        dict(
                            schema_version=2,
                            definition={"keyStyle": style, "showKeyBackg": 0, "showKeyHint": 1},
                        ),
                    ),
                    expected,
                )

    def test_omitted_width_and_labels_are_not_inferred_from_key_text(self):
        doc = document()
        expected = copy.deepcopy(doc)
        clip(expected)["def"]["keys"] = "⇧ ⌘ K"
        self.assertEqual(
            annotations.edit_annotation(
                doc, 3, dict(schema_version=3, definition={"keys": "⇧ ⌘ K"})
            ),
            expected,
        )

    def test_numeric_static_descriptors_are_preserved_and_unknown_animation_refuses(self):
        for name in ("keyStyle", "showKeyBackg", "showKeyHint"):
            doc = document()
            parameter: dict[str, Any] = dict(
                type="double", defaultValue=0.0, interp="linr", keyframes=[], opaque=[1]
            )
            clip(doc)["def"][name] = parameter
            expected = copy.deepcopy(doc)
            clip(expected)["def"][name]["defaultValue"] = 1.0
            self.assertEqual(
                annotations.edit_annotation(doc, 3, dict(schema_version=1, definition={name: 1})),
                expected,
            )
            parameter["keyframes"] = [dict(time=0, duration=1000, endTime=1000, value=1.0)]
            before = copy.deepcopy(doc)
            with self.subTest(name=name), self.assertRaisesRegex(ValueError, "animated"):
                annotations.edit_annotation(doc, 3, dict(schema_version=1, definition={name: 1}))
            self.assertEqual(doc, before)

    def test_invalid_keys_choices_flags_and_missing_fields_refuse_atomically(self):
        for name, value in [
            ("keys", ""),
            ("keys", "⌘\nK"),
            ("keys", "⌘\x00K"),
            ("keys", 7),
            ("keys", True),
            ("keyStyle", -1),
            ("keyStyle", 5),
            ("keyStyle", "1/2"),
            ("keyStyle", False),
            ("showKeyHint", True),
            ("showKeyHint", 2),
            ("showKeyBackg", -1),
        ]:
            doc = document()
            before = copy.deepcopy(doc)
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                annotations.edit_annotation(
                    doc, 3, dict(schema_version=1, definition={"width": 192, name: value})
                )
            self.assertEqual(doc, before)
        for name, value in [
            ("keys", "⌘ K"),
            ("keyStyle", 2),
            ("showKeyBackg", 0),
            ("showKeyHint", 1),
        ]:
            doc = document()
            clip(doc)["def"].pop(name)
            before = copy.deepcopy(doc)
            with self.subTest(missing=name), self.assertRaisesRegex(ValueError, "capture"):
                annotations.edit_annotation(
                    doc, 3, dict(schema_version=1, definition={name: value})
                )
            self.assertEqual(doc, before)
        doc = document()
        clip(doc)["def"]["keys"] = {"type": "string", "defaultValue": "⌘ A"}
        before = copy.deepcopy(doc)
        with self.assertRaises(ValueError):
            annotations.edit_annotation(doc, 3, dict(schema_version=1, definition={"keys": "⌘ K"}))
        self.assertEqual(doc, before)

    def test_keystroke_fields_do_not_become_generic_annotation_controls(self):
        for kind in ("remix", "TypeWinBlur", "TypeWinHighlighter"):
            for name, value in [
                ("keys", "⌘ K"),
                ("keyStyle", 2),
                ("showKeyBackg", 0),
                ("showKeyHint", 1),
            ]:
                doc = document()
                clip(doc)["def"]["kind"] = kind
                before = copy.deepcopy(doc)
                with (
                    self.subTest(kind=kind, name=name),
                    self.assertRaisesRegex(ValueError, "supported existing"),
                ):
                    annotations.edit_annotation(
                        doc, 3, dict(schema_version=1, definition={name: value})
                    )
                self.assertEqual(doc, before)

    def test_group_contained_keystroke_controls_refuse_without_mutating_any_owner(self):
        for name, value in [
            ("keys", "⇧ ⌘ K"),
            ("keyStyle", 2),
            ("showKeyBackg", 0),
            ("showKeyHint", 1),
        ]:
            doc = document()
            owner = clip(doc)
            project.scene_tracks(doc)[0][0]["medias"] = [
                dict(_type="Group", id=10, tracks=[dict(medias=[owner])])
            ]
            before = copy.deepcopy(doc)
            with (
                self.subTest(name=name),
                self.assertRaisesRegex(ValueError, "standalone root MacKey"),
            ):
                annotations.edit_annotation(
                    doc, 3, dict(schema_version=1, definition={"width": 192, name: value})
                )
            self.assertEqual(doc, before)

    def test_cli_candidate_repeat_invalid_no_output_and_untouched_input_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, spec, output = (
                root / name for name in ("source.json", "spec.json", "candidate.json")
            )
            source.write_bytes(project.encode_document(document()))
            original = source.read_bytes()
            spec.write_text(
                json.dumps(
                    dict(
                        schema_version=1,
                        definition={"keys": "⇧ ⌘ K", "keyStyle": 2, "width": 192, "showKeyHint": 1},
                    )
                )
            )
            args = [
                "set",
                str(source),
                "--clip-id",
                "3",
                "--spec",
                str(spec),
                "--output",
                str(output),
            ]
            for written in (True, False):
                with patch("sys.stdout", new_callable=io.StringIO) as stream:
                    self.assertEqual(annotations.main(args), 0)
                report = json.loads(stream.getvalue())
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
            expected = document()
            clip(expected)["def"].update(keys="⇧ ⌘ K", keyStyle=2.0, width=192.0, showKeyHint=1.0)
            self.assertEqual(project.load(output)[0], expected)
            self.assertEqual(source.read_bytes(), original)
            spec.write_text(json.dumps(dict(schema_version=1, definition={"keys": "⌘\nK"})))
            missing = root / "missing.json"
            with patch("sys.stderr", new_callable=io.StringIO):
                self.assertEqual(annotations.main(args[:-1] + [str(missing)]), 1)
            self.assertFalse(missing.exists())
            self.assertEqual(source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
