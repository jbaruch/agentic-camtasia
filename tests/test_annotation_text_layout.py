from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_annotations import clip, fixture
import annotations
import project


def document(depth=0):
    doc = fixture()
    lane = project.scene_tracks(doc)[0][0]
    node = clip(doc)
    node["def"].update({"word-wrap": 1.0, "text-stroke-alignment": 2.0, "text-stroke-width": 20.0})
    transitions = lane.pop("transitions")
    for level in range(depth):
        node = dict(
            _type="Group",
            id=100 + level,
            start=0,
            duration=6000,
            mediaStart=0.0,
            mediaDuration=6000.0,
            scalar=1,
            tracks=[dict(trackIndex=0, medias=[node], transitions=transitions, parameters={})],
            attributes=dict(
                widthAttr=640.0,
                heightAttr=360.0,
                assetProperties=[
                    dict(
                        type=0,
                        name="Text",
                        objects=[3],
                        themeMappings={"font-color": "foreground-1"},
                    )
                ],
            ),
            parameters={"translation0": 60.0, "volume": 0.4},
            metadata={"isOpen": {"type": "bool", "value": False}, "opaque": ["retain"]},
            effects=[],
            animationTracks={"opaque": ["retain"]},
        )
        transitions = []
    lane["medias"] = [node]
    lane["transitions"] = transitions
    return doc


def leaf(doc):
    return annotations.target(doc, 3)


class TextLayoutTests(unittest.TestCase):
    def test_each_native_choice_changes_only_its_existing_field_and_is_idempotent(self):
        for name, value in [
            ("word-wrap", 0),
            ("word-wrap", 1),
            ("text-stroke-alignment", 0),
            ("text-stroke-alignment", 1),
            ("text-stroke-alignment", 2),
        ]:
            doc = document()
            before = copy.deepcopy(doc)
            expected = copy.deepcopy(doc)
            leaf(expected)["def"][name] = float(value)
            spec = dict(schema_version=1, definition={name: value})
            with self.subTest(name=name, value=value):
                result = annotations.edit_annotation(doc, 3, spec)
                self.assertEqual(result, expected)
                self.assertEqual(doc, before)
                self.assertEqual(annotations.edit_annotation(result, 3, spec), result)

    def test_grouped_compound_edit_preserves_every_parent_binding_clock_and_companion(self):
        for depth in [1, 3]:
            doc = document(depth)
            expected = copy.deepcopy(doc)
            leaf(expected)["def"].update({"word-wrap": 0.0, "text-stroke-alignment": 1.0})
            with self.subTest(depth=depth):
                self.assertEqual(
                    annotations.edit_annotation(
                        doc,
                        3,
                        dict(
                            schema_version=2,
                            definition={"word-wrap": 0, "text-stroke-alignment": 1},
                        ),
                    ),
                    expected,
                )

    def test_layout_only_preserves_complete_timed_rich_states_and_default_font(self):
        for depth in [0, 2]:
            doc = document(depth)
            frames = leaf(doc)["def"]["textAttributes"]["keyframes"]
            later = copy.deepcopy(frames[0])
            later.update(time=2000, endTime=2000, duration=0)
            for run in later["value"]:
                if run["name"] == "fontSize":
                    run["value"] = 32.0
            frames.append(later)
            expected = copy.deepcopy(doc)
            leaf(expected)["def"]["word-wrap"] = 0.0
            with self.subTest(depth=depth):
                self.assertEqual(
                    annotations.edit_annotation(
                        doc, 3, dict(schema_version=3, definition={"word-wrap": 0})
                    ),
                    expected,
                )

    def test_native_null_rich_frame_is_not_reconstructed_by_layout_edits(self):
        doc = document()
        leaf(doc)["def"]["textAttributes"]["keyframes"][0]["value"] = None
        expected = copy.deepcopy(doc)
        leaf(expected)["def"]["text-stroke-alignment"] = 0.0
        self.assertEqual(
            annotations.edit_annotation(
                doc, 3, dict(schema_version=1, definition={"text-stroke-alignment": 0})
            ),
            expected,
        )

    def test_static_typed_layout_parameters_keep_bounds_interpolation_and_opaque_payload(self):
        doc = document()
        for name, value, maximum in [("word-wrap", 1.0, 1.0), ("text-stroke-alignment", 2.0, 2.0)]:
            leaf(doc)["def"][name] = dict(
                type="double",
                defaultValue=value,
                interp="linr",
                keyframes=[],
                valueBounds=dict(minValue=0.0, maxValue=maximum),
                opaque=["retain"],
            )
        expected = copy.deepcopy(doc)
        leaf(expected)["def"]["word-wrap"]["defaultValue"] = 0.0
        leaf(expected)["def"]["text-stroke-alignment"]["defaultValue"] = 1.0
        self.assertEqual(
            annotations.edit_annotation(
                doc,
                3,
                dict(
                    schema_version=1,
                    definition={"word-wrap": "0/1", "text-stroke-alignment": "1/1"},
                ),
            ),
            expected,
        )

    def test_invalid_flags_enums_aliases_and_missing_fields_refuse_atomically(self):
        for name, value in [
            ("word-wrap", True),
            ("word-wrap", False),
            ("word-wrap", 0.5),
            ("word-wrap", 2),
            ("text-stroke-alignment", 3),
            ("text-stroke-alignment", -1),
            ("text-stroke-alignment", "outside"),
        ]:
            doc = document()
            before = copy.deepcopy(doc)
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                annotations.edit_annotation(
                    doc, 3, dict(schema_version=1, definition={name: value})
                )
            self.assertEqual(doc, before)
        doc = document()
        del leaf(doc)["def"]["word-wrap"]
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "capture"):
            annotations.edit_annotation(
                doc,
                3,
                dict(schema_version=1, definition={"text-stroke-alignment": 1, "word-wrap": 0}),
            )
        self.assertEqual(doc, before)

    def test_other_kinds_and_non_text_definitions_do_not_gain_layout_controls(self):
        for kind in ["MacKey", "TypeWinSVG", "TypeWinBlur"]:
            doc = document()
            leaf(doc)["def"]["kind"] = kind
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "supported existing"):
                annotations.edit_annotation(
                    doc, 3, dict(schema_version=1, definition={"word-wrap": 0})
                )
        doc = document()
        del leaf(doc)["def"]["text"]
        with self.assertRaisesRegex(ValueError, "remix text"):
            annotations.edit_annotation(doc, 3, dict(schema_version=1, definition={"word-wrap": 0}))

    def test_other_container_anywhere_in_ancestor_chain_refuses_both_fields(self):
        for kind in ["StitchedMedia", "UnifiedMedia"]:
            for name in ["word-wrap", "text-stroke-alignment"]:
                doc = document(3)
                parent = project.scene_tracks(doc)[0][0]["medias"][0]
                child = parent["tracks"][0]["medias"][0]
                parent["tracks"][0]["medias"][0] = dict(
                    id=90,
                    _type=kind,
                    **({"medias": [child]} if kind == "StitchedMedia" else {"video": child}),
                )
                before = copy.deepcopy(doc)
                with (
                    self.subTest(kind=kind, name=name),
                    self.assertRaisesRegex(ValueError, "Group-only"),
                ):
                    annotations.edit_annotation(
                        doc, 3, dict(schema_version=1, definition={name: 0})
                    )
                self.assertEqual(doc, before)

    def test_animated_defaultless_or_unknown_layout_fields_refuse_without_partial_mutation(self):
        for value in [
            dict(type="double", defaultValue=1.0, keyframes=[dict(time=0, value=1)]),
            dict(type="double", keyframes=[]),
            dict(type="future", defaultValue=1.0),
        ]:
            doc = document()
            leaf(doc)["def"]["word-wrap"] = value
            before = copy.deepcopy(doc)
            with self.subTest(value=value), self.assertRaises(ValueError):
                annotations.edit_annotation(
                    doc,
                    3,
                    dict(schema_version=1, definition={"text-stroke-alignment": 1, "word-wrap": 0}),
                )
            self.assertEqual(doc, before)

    def test_cli_stages_group_layout_exclusively_and_refuses_bad_choice_without_output(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source, spec, output = (
                root / name for name in ("source.json", "spec.json", "out.json")
            )
            data = project.encode_document(document(2))
            source.write_bytes(data)
            spec.write_text(
                json.dumps(
                    dict(schema_version=1, definition={"word-wrap": 0, "text-stroke-alignment": 1})
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
                stdout = io.StringIO()
                with patch("sys.stdout", stdout):
                    self.assertEqual(annotations.main(args), 0)
                report = json.loads(stdout.getvalue())
                self.assertTrue(report["changed"])
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
            candidate = project.load(output)[0]
            self.assertEqual(leaf(candidate)["def"]["word-wrap"], 0.0)
            self.assertEqual(leaf(candidate)["def"]["text-stroke-alignment"], 1.0)
            output.unlink()
            spec.write_text(json.dumps(dict(schema_version=1, definition={"word-wrap": True})))
            stderr = io.StringIO()
            with patch("sys.stderr", stderr):
                self.assertEqual(annotations.main(args), 1)
            self.assertFalse(json.loads(stderr.getvalue())["ok"])
            self.assertFalse(output.exists())
            self.assertEqual(source.read_bytes(), data)


if __name__ == "__main__":
    unittest.main()
