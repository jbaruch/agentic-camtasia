from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

from test_annotation_text_layout import document, leaf
import animations
import project


def fixture(depth=0):
    doc = document(depth)
    node = leaf(doc)
    node["parameters"]["translation0"] = 0.0
    node["def"].update(
        {
            "text-stroke-width": 0.0,
            "text-stroke-color-red": 0.0,
            "text-stroke-color-green": 0.0,
            "text-stroke-color-blue": 0.0,
            "text-stroke-color-alpha": 1.0,
        }
    )
    return doc


def spec(**changes: Any) -> dict[str, Any]:
    return dict(
        schema_version=2,
        start=1,
        end=2,
        definition={
            "text-stroke-width": 10,
            "text-stroke-color-red": 1,
            "text-stroke-color-green": 0.501960784313725,
            "text-stroke-color-alpha": 0.5,
        },
        **changes,
    )


def frame(value, start=1000, end=2000, **fields):
    return dict(time=start, endTime=end, duration=end - start, value=value, **fields)


class TextOutlineAnimationTests(unittest.TestCase):
    def test_blue_channel_boundaries_preserve_null_and_later_rich_states(self):
        doc = fixture(2)
        rich = leaf(doc)["def"]["textAttributes"]["keyframes"]
        later = copy.deepcopy(rich[0])
        later.update(time=2500, endTime=2500)
        rich[0]["value"] = None
        rich.append(later)
        expected = copy.deepcopy(doc)
        leaf(expected)["def"]["text-stroke-color-blue"] = dict(
            type="double", defaultValue=0.0, keyframes=[frame(1.0), frame(0.0, 3000, 4000)]
        )
        leaf(expected)["animationTracks"]["visual"] = [
            dict(endTime=2000, duration=1000),
            dict(endTime=4000, duration=1000),
        ]
        result = doc
        for start, end, value in [(1, 2, 1), (3, 4, 0)]:
            result = animations.edit_interval(
                result,
                3,
                dict(
                    schema_version=2,
                    start=start,
                    end=end,
                    definition={"text-stroke-color-blue": value},
                ),
            )
        self.assertEqual(result, expected)

    def test_fixed_native_definition_shapes_preserve_the_rest_of_the_project(self):
        doc = fixture()
        before = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        for name, target in spec()["definition"].items():
            leaf(expected)["def"][name] = dict(
                type="double", defaultValue=leaf(doc)["def"][name], keyframes=[frame(float(target))]
            )
        leaf(expected)["animationTracks"]["visual"] = [dict(endTime=2000, duration=1000)]
        result = animations.edit_interval(doc, 3, spec())
        self.assertEqual(result, expected)
        self.assertEqual(doc, before)
        self.assertEqual(animations.edit_interval(result, 3, spec()), result)

    def test_mixed_definition_geometry_easing_and_removal_are_coupled(self):
        doc = fixture()
        result = animations.edit_interval(
            doc, 3, spec(values={"translation0": 80}, easing="linear")
        )
        expected = copy.deepcopy(doc)
        for name, target in spec()["definition"].items():
            leaf(expected)["def"][name] = dict(
                type="double",
                defaultValue=leaf(doc)["def"][name],
                keyframes=[frame(float(target), interp="linr")],
            )
        leaf(expected)["parameters"]["translation0"] = dict(
            type="double", defaultValue=0.0, keyframes=[frame(80.0, interp="linr")]
        )
        leaf(expected)["animationTracks"]["visual"] = [
            dict(endTime=2000, duration=1000, interp="linr")
        ]
        self.assertEqual(result, expected)
        removed = animations.remove_interval(result, 3, 1, 2)
        expected = copy.deepcopy(doc)
        del leaf(expected)["parameters"]["translation0"]
        self.assertEqual(removed, expected)
        self.assertEqual(animations.remove_interval(removed, 3, 1, 2), removed)

    def test_legacy_ease_updates_native_definition_frames_but_keeps_rich_points(self):
        doc = animations.edit_interval(fixture(), 3, spec())
        for easing, code in [
            ("auto", None),
            ("linear", "linr"),
            ("exponential", "eioe"),
            ("bounce", "bnce"),
            ("spring", "sprg"),
        ]:
            with self.subTest(easing=easing):
                result = animations.edit_interval(
                    doc, 3, dict(schema_version=1, start=1, end=2, values={}, easing=easing)
                )
                expected = copy.deepcopy(doc)
                owners = [leaf(expected)["animationTracks"]["visual"][0]]
                owners += [
                    leaf(expected)["def"][name]["keyframes"][0] for name in spec()["definition"]
                ]
                for owner in owners:
                    if code is not None:
                        owner["interp"] = code
                self.assertEqual(result, expected)

    def test_group_ancestors_and_trimmed_speed_clock_stay_unchanged(self):
        for depth in [0, 1, 3]:
            doc = fixture(depth)
            leaf(doc).update(mediaStart=3000, scalar="1/2", start=57000)
            expected = copy.deepcopy(doc)
            leaf(expected)["def"]["text-stroke-width"] = dict(
                type="double", defaultValue=0.0, keyframes=[frame(5.0, 5000, 7000)]
            )
            leaf(expected)["animationTracks"]["visual"] = [dict(endTime=7000, duration=2000)]
            with self.subTest(depth=depth):
                result = animations.edit_interval(
                    doc,
                    3,
                    dict(schema_version=2, start=1, end=2, definition={"text-stroke-width": 5}),
                )
                self.assertEqual(result, expected)

    def test_new_outline_curve_inherits_existing_marker_easing(self):
        doc = fixture()
        leaf(doc)["animationTracks"]["visual"] = [dict(endTime=2000, duration=1000, interp="sprg")]
        result = animations.edit_interval(doc, 3, spec())
        self.assertEqual(
            [leaf(result)["def"][n]["keyframes"][0]["interp"] for n in spec()["definition"]],
            ["sprg"] * 4,
        )

    def test_second_interval_and_typed_metadata_survive_edit_ease_and_removal(self):
        doc = animations.edit_interval(fixture(), 3, spec())
        parameter = leaf(doc)["def"]["text-stroke-width"]
        parameter.update(interp="eioe", opaque={"keep": [1]}, valueBounds={"minValue": 0})
        parameter["keyframes"][0]["opaque"] = ["retain"]
        second = dict(schema_version=2, start=3, end=4, definition={"text-stroke-width": 0})
        doc = animations.edit_interval(doc, 3, second)
        before = copy.deepcopy(doc)
        changed = animations.edit_interval(
            doc, 3, dict(schema_version=1, start=1, end=2, values={}, easing="bounce")
        )
        self.assertEqual(
            leaf(changed)["def"]["text-stroke-width"]["keyframes"][1],
            frame(0.0, 3000, 4000),
        )
        self.assertEqual(doc, before)
        result = animations.remove_interval(changed, 3, 1, 2)
        self.assertEqual(
            leaf(result)["def"]["text-stroke-width"],
            dict(
                type="double",
                defaultValue=0.0,
                interp="eioe",
                opaque={"keep": [1]},
                valueBounds={"minValue": 0},
                keyframes=[frame(0.0, 3000, 4000)],
            ),
        )
        result = animations.remove_interval(result, 3, 3, 4)
        self.assertEqual(
            leaf(result)["def"]["text-stroke-width"],
            dict(
                type="double",
                defaultValue=0.0,
                interp="eioe",
                opaque={"keep": [1]},
                valueBounds={"minValue": 0},
            ),
        )

    def test_unknown_nested_definition_coupling_refuses_ease_and_removal_atomically(self):
        for name in ["future", "textAttributes", "stroke-width"]:
            doc = animations.edit_interval(fixture(), 3, spec())
            leaf(doc)["def"][name] = {
                "nested": dict(type="double", defaultValue=0, keyframes=[frame(1)])
            }
            before = copy.deepcopy(doc)
            for action in [
                lambda: animations.remove_interval(doc, 3, 1, 2),
                lambda: animations.edit_interval(
                    doc, 3, dict(schema_version=1, start=1, end=2, values={}, easing="linear")
                ),
            ]:
                with (
                    self.subTest(name=name),
                    self.assertRaisesRegex(ValueError, "unknown definition"),
                ):
                    action()
                self.assertEqual(doc, before)

    def test_orphan_definition_frames_refuse_empty_marker_and_absent_removal(self):
        doc = animations.edit_interval(fixture(), 3, spec())
        del leaf(doc)["animationTracks"]["visual"]
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "orphaned"):
            animations.edit_interval(
                doc, 3, dict(schema_version=1, start=1, end=2, values={}), allow_empty=True
            )
        with self.assertRaisesRegex(ValueError, "orphaned"):
            animations.remove_interval(doc, 3, 1, 2)
        self.assertEqual(doc, before)

    def test_invalid_values_missing_fields_types_and_schema_refuse_atomically(self):
        cases = [
            dict(schema_version=2, start=1, end=2, definition={name: value})
            for name, value in [
                ("text-stroke-width", -1),
                ("text-stroke-width", True),
                ("text-stroke-width", float("inf")),
                ("text-stroke-color-blue", -0.1),
                ("text-stroke-color-alpha", 1.1),
                ("text-stroke-alignment", 1),
                ("word-wrap", 0),
                ("font", 32),
            ]
        ]
        cases += [
            dict(schema_version=1, start=1, end=2, values={}, definition={"text-stroke-width": 2}),
            dict(schema_version=2, start=1, end=2, definition=[]),
        ]
        for request in cases:
            doc = fixture()
            with self.subTest(request=request), self.assertRaises(ValueError):
                animations.edit_interval(doc, 3, request)
            self.assertEqual(doc, fixture())
        for replacement in [
            None,
            {"type": "int", "defaultValue": 0},
            {"type": "double", "defaultValue": -1},
        ]:
            doc = fixture()
            if replacement is None:
                del leaf(doc)["def"]["text-stroke-width"]
            else:
                leaf(doc)["def"]["text-stroke-width"] = replacement
            before = copy.deepcopy(doc)
            with self.subTest(replacement=replacement), self.assertRaises(ValueError):
                animations.edit_interval(doc, 3, spec())
            self.assertEqual(doc, before)

    def test_unverified_owner_and_non_group_ancestor_refuse(self):
        for field, value in [("_type", "IMFile"), ("kind", "TypeWinSVG"), ("text", None)]:
            doc = fixture()
            (leaf(doc) if field == "_type" else leaf(doc)["def"])[field] = value
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "remix text"):
                animations.edit_interval(doc, 3, spec())
        doc = fixture(1)
        project.scene_tracks(doc)[0][0]["medias"][0]["_type"] = "StitchedMedia"
        with self.assertRaisesRegex(ValueError, "Group-only"):
            animations.edit_interval(doc, 3, spec())

    def test_point_duplicate_and_overlapping_known_definition_frames_refuse(self):
        for frames in [[frame(4, 1000, 1000)], [frame(4), frame(5)], [frame(4, 500, 1500)]]:
            doc = fixture()
            leaf(doc)["def"]["text-stroke-width"] = dict(
                type="double", defaultValue=0, keyframes=frames
            )
            before = copy.deepcopy(doc)
            with self.subTest(frames=frames), self.assertRaises(ValueError):
                animations.edit_interval(doc, 3, spec())
            self.assertEqual(doc, before)

    def test_inventory_exposes_definition_curves_without_a_visual_marker(self):
        doc = animations.edit_interval(fixture(), 3, spec())
        del leaf(doc)["animationTracks"]["visual"]
        item = next(x for x in animations.inventory(doc) if x["clipId"] == 3)
        self.assertEqual(item["visualIntervals"], [])
        self.assertEqual(
            set(item["definitionCurves"]), set(spec()["definition"]) | {"textAttributes"}
        )

    def test_cli_stages_outline_candidate_without_mutating_source_and_reports_inventory(self):
        with tempfile.TemporaryDirectory() as temp:
            source, request, output = [
                Path(temp) / name for name in ["source.json", "spec.json", "candidate.json"]
            ]
            source.write_bytes(project.encode_document(fixture()))
            request.write_text(json.dumps(spec()))
            before = source.read_bytes()
            stream = io.StringIO()
            with patch("sys.stdout", stream):
                status = animations.main(
                    [
                        "set-interval",
                        str(source),
                        "--clip-id",
                        "3",
                        "--spec",
                        str(request),
                        "--output",
                        str(output),
                    ]
                )
            self.assertEqual(status, 0)
            report = json.loads(stream.getvalue())
            self.assertTrue(report["written"])
            self.assertFalse(report["nativeVerified"])
            self.assertIn("definitionCurves", report["animations"][0])
            self.assertEqual(source.read_bytes(), before)
            self.assertEqual(
                json.loads(output.read_bytes()), animations.edit_interval(fixture(), 3, spec())
            )
