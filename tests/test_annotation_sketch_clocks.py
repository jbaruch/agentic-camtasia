from __future__ import annotations

import copy
import unittest

from test_annotation_sketch import document
import annotations
import project


def leaf(doc):
    return annotations.target(doc, 3)


def grouped(depth=3):
    doc = document()
    lane = project.scene_tracks(doc)[0][0]
    node = lane["medias"][0]
    node.update(start=250, duration=2000, mediaStart=1500, mediaDuration=4000, scalar="1/2")
    node["def"]["borderWidth"] = dict(type="double", defaultValue=3.0, interp="linr")
    node["def"]["DrawTime"] = dict(type="double", defaultValue=1.0, interp="linr")
    transitions = lane.pop("transitions")
    for level in range(depth):
        node = dict(
            _type="Group",
            id=100 + level,
            start=1250 if level == depth - 1 else 250,
            duration=1750,
            mediaStart=250.0,
            mediaDuration=1750.0,
            scalar=1,
            tracks=[dict(trackIndex=0, medias=[node], transitions=transitions, parameters={})],
            attributes=dict(
                widthAttr=640.0,
                heightAttr=360.0,
                assetProperties=[dict(objects=[dict(media=3, parameters=["borderColorRed"])])],
            ),
            parameters={"translation0": 60.0, "volume": 0.4},
            metadata={"isOpen": {"type": "bool", "value": False}, "opaque": ["retain"]},
            animationTracks={"opaque": ["retain"]},
            effects=[],
        )
        transitions = []
    lane["medias"] = [node]
    return doc


class SketchClockTests(unittest.TestCase):
    def test_trimmed_fast_and_slow_root_edits_use_clip_timeline_not_source_ticks(self):
        for scalar, duration in [("1/2", 2000), (2, 8000)]:
            doc = document()
            leaf(doc).update(mediaStart=1000, scalar=scalar, duration=duration, mediaDuration=4000)
            expected = copy.deepcopy(doc)
            leaf(expected)["leftEdgeMods"][0]["duration"] = 1500
            with self.subTest(scalar=scalar):
                self.assertEqual(
                    annotations.edit_annotation(doc, 3, dict(schema_version=1, draw_time="3/2")),
                    expected,
                )

    def test_missing_or_empty_drawing_list_gets_only_the_native_companion(self):
        for present in [False, True]:
            doc = document()
            del leaf(doc)["leftEdgeMods"]
            leaf(doc).update(mediaStart=1000, duration=4000, mediaDuration=4000)
            if present:
                leaf(doc)["leftEdgeMods"] = []
            before = copy.deepcopy(doc)
            expected = copy.deepcopy(doc)
            leaf(expected)["leftEdgeMods"] = [
                dict(
                    group="DrawPercentageFade",
                    duration=2000,
                    parameters=[dict(name="DrawTime", func="FadeInFunc")],
                )
            ]
            spec = dict(schema_version=1, draw_time=2)
            with self.subTest(present=present):
                result = annotations.edit_annotation(doc, 3, spec)
                self.assertEqual(result, expected)
                self.assertEqual(doc, before)
                self.assertEqual(annotations.edit_annotation(result, 3, spec), result)

    def test_stroke_only_edit_does_not_create_a_trimmed_off_drawing(self):
        doc = document()
        del leaf(doc)["leftEdgeMods"]
        leaf(doc)["mediaStart"] = 1000
        expected = copy.deepcopy(doc)
        leaf(expected)["def"]["borderWidth"] = 7.0
        self.assertEqual(
            annotations.edit_annotation(
                doc, 3, dict(schema_version=1, definition={"borderWidth": 7})
            ),
            expected,
        )

    def test_grouped_compound_edit_preserves_all_ancestors_bindings_and_companions(self):
        for depth in [1, 3]:
            doc = grouped(depth)
            before = copy.deepcopy(doc)
            expected = copy.deepcopy(doc)
            leaf(expected)["leftEdgeMods"][0]["duration"] = 800
            leaf(expected)["def"]["borderWidth"]["defaultValue"] = 9.0
            leaf(expected)["def"].update(
                borderColorRed=1.0, borderColorGreen=0.5, borderColorBlue=0.0
            )
            spec = dict(
                schema_version=2,
                draw_time="4/5",
                definition=dict(
                    borderWidth=9, borderColorRed=1, borderColorGreen="1/2", borderColorBlue=0
                ),
            )
            with self.subTest(depth=depth):
                result = annotations.edit_annotation(doc, 3, spec)
                self.assertEqual(result, expected)
                self.assertEqual(doc, before)
                self.assertEqual(annotations.edit_annotation(result, 3, spec), result)

    def test_child_can_outlast_parent_without_expanding_or_retiming_any_ancestor(self):
        doc = grouped()
        leaf(doc).update(duration=8000, scalar=2)
        expected = copy.deepcopy(doc)
        leaf(expected)["leftEdgeMods"][0]["duration"] = 3200
        self.assertEqual(
            annotations.edit_annotation(doc, 3, dict(schema_version=3, draw_time="16/5")),
            expected,
        )

    def test_timing_limits_use_leaf_duration_without_ui_rounding_or_parent_clamping(self):
        doc = grouped()
        expected = copy.deepcopy(doc)
        leaf(expected)["leftEdgeMods"][0]["duration"] = 2000
        self.assertEqual(
            annotations.edit_annotation(doc, 3, dict(schema_version=1, draw_time=2)), expected
        )
        leaf(expected)["leftEdgeMods"][0]["duration"] = 750
        self.assertEqual(
            annotations.edit_annotation(doc, 3, dict(schema_version=1, draw_time="3/4")), expected
        )
        with self.assertRaisesRegex(ValueError, "inside the clip"):
            annotations.edit_annotation(doc, 3, dict(schema_version=1, draw_time="2001/1000"))

    def test_non_group_ancestor_anywhere_in_chain_refuses_both_edit_forms(self):
        for kind in ["StitchedMedia", "UnifiedMedia"]:
            for change in [dict(draw_time=1), dict(definition={"borderWidth": 7})]:
                doc = grouped()
                parent = project.scene_tracks(doc)[0][0]["medias"][0]
                child = parent["tracks"][0]["medias"][0]
                parent["tracks"][0]["medias"][0] = dict(
                    id=90,
                    _type=kind,
                    **({"medias": [child]} if kind == "StitchedMedia" else {"video": child}),
                )
                before = copy.deepcopy(doc)
                with (
                    self.subTest(kind=kind, change=change),
                    self.assertRaisesRegex(ValueError, "Group-only"),
                ):
                    annotations.edit_annotation(doc, 3, dict(schema_version=1, **change))
                self.assertEqual(doc, before)

    def test_missing_companion_and_bad_stroke_refuse_atomically(self):
        doc = grouped()
        del leaf(doc)["leftEdgeMods"]
        before = copy.deepcopy(doc)
        with self.assertRaises(ValueError):
            annotations.edit_annotation(
                doc, 3, dict(schema_version=1, draw_time=1, definition={"borderWidth": -1})
            )
        self.assertEqual(doc, before)


if __name__ == "__main__":
    unittest.main()
