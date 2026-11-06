from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

from test_annotation_keystrokes import document as root_document
import annotations
import project


def document(depth=2):
    doc = root_document()
    node = project.scene_tracks(doc)[0][0]["medias"][0]
    for level in range(depth):
        node = dict(
            _type="Group",
            id=10 + level,
            start=2000,
            duration=3000,
            mediaStart=500,
            mediaDuration=6000,
            scalar="2/1",
            attributes=dict(ident="Group", widthAttr=640.0, heightAttr=360.0, assetProperties=[]),
            tracks=[
                dict(trackIndex=0, medias=[node], parameters={}, metadata={"trackHeight": "78"})
            ],
            parameters={"translation0": 60.0, "volume": 0.4},
            metadata={"isOpen": {"type": "bool", "value": False}, "opaque": ["retain"]},
            effects=[],
            animationTracks={"opaque": ["preserve"]},
        )
    project.scene_tracks(doc)[0][0]["medias"] = [node]
    return doc


def leaf(doc):
    return annotations.target(doc, 3)


class GroupKeystrokeTests(unittest.TestCase):
    def test_one_and_two_native_group_ancestors_preserve_every_unrequested_field(self):
        changes = dict(keys="⌘ B", keyStyle=2, width=128, showKeyHint=1, showKeyBackg=0)
        for depth in [1, 2]:
            doc = document(depth)
            before = copy.deepcopy(doc)
            expected = copy.deepcopy(doc)
            leaf(expected)["def"].update(
                keys="⌘ B", keyStyle=2.0, width=128.0, showKeyHint=1.0, showKeyBackg=0.0
            )
            with self.subTest(depth=depth):
                result = annotations.edit_annotation(
                    doc, 3, dict(schema_version=1, definition=changes)
                )
                self.assertEqual(result, expected)
                self.assertEqual(doc, before)
                self.assertEqual(
                    annotations.edit_annotation(
                        result, 3, dict(schema_version=1, definition=changes)
                    ),
                    result,
                )

    def test_each_control_keeps_group_bounds_transforms_clocks_and_resets(self):
        for name, value in [
            ("keys", "⌘ B"),
            ("keyStyle", 2),
            ("showKeyHint", 1),
            ("showKeyBackg", 0),
        ]:
            doc = document()
            expected = copy.deepcopy(doc)
            leaf(expected)["def"][name] = value if name == "keys" else float(value)
            with self.subTest(name=name):
                result = annotations.edit_annotation(
                    doc, 3, dict(schema_version=2, definition={name: value})
                )
                self.assertEqual(result, expected)
                self.assertEqual(leaf(result)["metadata"]["default-callout-keys"], "⌘ A")

    def test_nested_invalid_or_animated_fields_refuse_without_partial_child_or_parent_edits(self):
        for name, value in [("keys", "⌘\nB"), ("keyStyle", 9), ("showKeyHint", True)]:
            doc = document()
            before = copy.deepcopy(doc)
            with self.subTest(name=name), self.assertRaises(ValueError):
                annotations.edit_annotation(
                    doc, 3, dict(schema_version=1, definition={"width": 128, name: value})
                )
            self.assertEqual(doc, before)
        doc = document()
        leaf(doc)["def"]["keyStyle"] = dict(
            type="double",
            defaultValue=0.0,
            keyframes=[dict(time=0, endTime=1000, duration=1000, value=2.0)],
        )
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "animated"):
            annotations.edit_annotation(
                doc, 3, dict(schema_version=1, definition={"keys": "⌘ B", "keyStyle": 2})
            )
        self.assertEqual(doc, before)

    def test_non_group_container_anywhere_in_the_chain_remains_refused(self):
        for container in ["StitchedMedia", "UnifiedMedia"]:
            doc = document(1)
            group = project.scene_tracks(doc)[0][0]["medias"][0]
            child = group["tracks"][0]["medias"][0]
            wrapper: dict[str, Any] = dict(_type=container, id=20)
            wrapper.update(
                {"medias": [child]} if container == "StitchedMedia" else {"video": child}
            )
            group["tracks"][0]["medias"] = [wrapper]
            before = copy.deepcopy(doc)
            with (
                self.subTest(container=container),
                self.assertRaisesRegex(ValueError, "Group-only"),
            ):
                annotations.edit_annotation(
                    doc, 3, dict(schema_version=1, definition={"keys": "⌘ B"})
                )
            self.assertEqual(doc, before)

    def test_duplicate_leaf_ids_across_distinct_group_owners_refuse(self):
        doc = document(1)
        group = project.scene_tracks(doc)[0][0]["medias"][0]
        sibling = copy.deepcopy(group)
        sibling["id"] = 20
        project.scene_tracks(doc)[0].append(dict(trackIndex=1, medias=[sibling]))
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            annotations.edit_annotation(doc, 3, dict(schema_version=1, definition={"keys": "⌘ B"}))
        self.assertEqual(doc, before)

    def test_cli_stages_nested_candidate_repeats_and_keeps_original_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, spec, output = [
                root / n for n in ["source.json", "spec.json", "candidate.json"]
            ]
            source.write_bytes(project.encode_document(document()))
            original = source.read_bytes()
            spec.write_text(
                json.dumps(
                    dict(schema_version=1, definition={"keys": "⌘ B", "width": 128, "keyStyle": 2})
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
            for written in [True, False]:
                with patch("sys.stdout", new_callable=io.StringIO) as stream:
                    self.assertEqual(annotations.main(args), 0)
                report = json.loads(stream.getvalue())
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
            expected = document()
            leaf(expected)["def"].update(keys="⌘ B", width=128.0, keyStyle=2.0)
            self.assertEqual(project.load(output)[0], expected)
            self.assertEqual(source.read_bytes(), original)
            spec.write_text(json.dumps(dict(schema_version=1, definition={"keys": "⌘\nB"})))
            missing = root / "missing.json"
            with patch("sys.stderr", new_callable=io.StringIO):
                self.assertEqual(annotations.main(args[:-1] + [str(missing)]), 1)
            self.assertFalse(missing.exists())
            self.assertEqual(source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
