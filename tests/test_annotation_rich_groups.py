from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_annotation_text_layout import document, leaf
import animations
import annotations
import project


def fixture(depth=1):
    doc = document(depth)
    node = leaf(doc)
    node.update(start=500, duration=4000, mediaStart=1000, mediaDuration=8000, scalar="1/2")
    node["def"]["text"] = "A café"
    for run in node["def"]["textAttributes"]["keyframes"][0]["value"]:
        run["rangeEnd"] = 7
    return doc


def spec():
    return dict(
        schema_version=1,
        initial=dict(rich=dict(fontSize=32)),
        steps=[
            dict(at="1/2", rich=dict(fontSize=64, fgColor="(255,128,64,255)")),
            dict(
                at="3/2",
                rich_ranges=[
                    dict(start=2, end=6, rich=dict(fontWeight=700, fgColor="(32,192,240,255)"))
                ],
            ),
        ],
    )


def frames(doc):
    return leaf(doc)["def"]["textAttributes"]["keyframes"]


def expected(doc):
    result = copy.deepcopy(doc)
    first = frames(result)[0]
    for run in first["value"]:
        if run["name"] == "fontSize":
            run["value"] = 32.0
    second = copy.deepcopy(first["value"])
    for run in second:
        if run["name"] == "fontSize":
            run["value"] = 64.0
        if run["name"] == "fgColor":
            run["value"] = "(255,128,64,255)"
    third = []
    for run in second:
        if run["name"] in ("fontWeight", "fgColor"):
            prefix, suffix = copy.deepcopy(run), copy.deepcopy(run)
            prefix["rangeEnd"] = 2
            suffix.update(
                rangeStart=2, value=700 if run["name"] == "fontWeight" else "(32,192,240,255)"
            )
            third.extend([prefix, suffix])
        else:
            third.append(copy.deepcopy(run))
    frames(result).extend(
        [
            dict(time=2000, endTime=2000, duration=0, value=second),
            dict(time=4000, endTime=4000, duration=0, value=third),
        ]
    )
    return result


class GroupRichStepTests(unittest.TestCase):
    def test_literal_source_point_states_preserve_complete_group_payload_and_unicode_ranges(self):
        for depth in [1, 3]:
            doc = fixture(depth)
            before = copy.deepcopy(doc)
            with self.subTest(depth=depth):
                result = annotations.set_rich_steps(doc, 3, spec())
                self.assertEqual(result, expected(doc))
                self.assertEqual(doc, before)
                self.assertEqual(annotations.set_rich_steps(result, 3, spec()), result)
                self.assertIsNot(frames(result)[1]["value"], frames(result)[2]["value"])

    def test_ancestor_placement_trims_and_speed_never_enter_the_selected_child_clock(self):
        for scalar, start, inpoint in [("1/2", 0, 0), (1, 9000, 250), (2, 9000, 500)]:
            doc = fixture(3)
            groups = [n for _, n in project.objects(doc) if n.get("_type") == "Group"]
            for node in groups:
                node.update(scalar=scalar, start=start, mediaStart=inpoint)
            with self.subTest(scalar=scalar, inpoint=inpoint):
                self.assertEqual(annotations.set_rich_steps(doc, 3, spec()), expected(doc))
                self.assertEqual(annotations.rich_source_time(doc, 3, "3/2"), 4000)

    def test_clear_chooses_complete_effective_state_at_exact_child_boundaries(self):
        doc = expected(fixture(3))
        for at, index in [
            (0, 0),
            ("499/1000", 0),
            ("1/2", 1),
            ("1499/1000", 1),
            ("3/2", 2),
            ("3999/1000", 2),
        ]:
            wanted = copy.deepcopy(doc)
            first = frames(wanted)[0]
            first["value"] = copy.deepcopy(frames(doc)[index]["value"])
            leaf(wanted)["def"]["textAttributes"]["keyframes"] = [first]
            with self.subTest(at=at):
                result = annotations.clear_rich_steps(doc, 3, at)
                self.assertEqual(result, wanted)
                self.assertEqual(annotations.clear_rich_steps(result, 3, at), result)

    def test_replacement_keeps_zero_fallback_opaque_metadata_and_does_not_infer_effective_initial(
        self,
    ):
        doc = expected(fixture())
        frames(doc)[0]["opaque"] = ["initial"]
        frames(doc)[1]["opaque"] = ["discarded-state"]
        wanted = copy.deepcopy(doc)
        first = copy.deepcopy(frames(wanted)[0])
        later = copy.deepcopy(first["value"])
        for run in later:
            if run["name"] == "fontSize":
                run["value"] = 48.0
        leaf(wanted)["def"]["textAttributes"]["keyframes"] = [
            first,
            dict(time=3000, endTime=3000, duration=0, value=later),
        ]
        result = annotations.set_rich_steps(
            doc, 3, dict(schema_version=1, steps=[dict(at=1, rich=dict(fontSize=48))])
        )
        self.assertEqual(result, wanted)

    def test_independent_geometry_and_continuous_outline_intervals_survive_set_and_clear(self):
        doc = animations.edit_interval(
            fixture(2),
            3,
            dict(
                schema_version=2,
                start="1/4",
                end="1/2",
                values={"translation0": 80},
                initial={"translation0": 0},
                definition={"text-stroke-width": 8},
                easing="linear",
            ),
        )
        result = annotations.set_rich_steps(doc, 3, spec())
        self.assertEqual(result, expected(doc))
        cleared = annotations.clear_rich_steps(result, 3, "1/2")
        wanted = copy.deepcopy(result)
        frames(wanted)[0]["value"] = copy.deepcopy(frames(wanted)[1]["value"])
        leaf(wanted)["def"]["textAttributes"]["keyframes"] = [frames(wanted)[0]]
        self.assertEqual(cleared, wanted)

    def test_child_local_time_can_be_cropped_by_a_retained_shorter_parent(self):
        doc = fixture()
        group = project.scene_tracks(doc)[0][0]["medias"][0]
        group.update(start=9000, duration=750, mediaStart=0, mediaDuration=750, scalar=1)
        result = annotations.set_rich_steps(doc, 3, spec())
        self.assertEqual(result, expected(doc))
        self.assertEqual(project.scene_tracks(result)[0][0]["medias"][0]["duration"], 750)

    def test_non_group_ancestors_refuse_set_and_clear_without_mutation(self):
        for kind in ["StitchedMedia", "UnifiedMedia", "FutureContainer"]:
            doc = expected(fixture())
            project.scene_tracks(doc)[0][0]["medias"][0]["_type"] = kind
            before = copy.deepcopy(doc)
            for call in [
                lambda: annotations.set_rich_steps(doc, 3, spec()),
                lambda: annotations.clear_rich_steps(doc, 3, 1),
            ]:
                with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "Group-only"):
                    call()
                self.assertEqual(doc, before)

    def test_multiple_scenes_remain_outside_the_selected_clock_contract(self):
        doc = expected(fixture())
        scene = copy.deepcopy(doc["timeline"]["sceneTrack"]["scenes"][0])
        scene["csml"]["tracks"] = []
        doc["timeline"]["sceneTrack"]["scenes"].append(scene)
        with self.assertRaisesRegex(ValueError, "single-scene"):
            annotations.set_rich_steps(doc, 3, spec())
        with self.assertRaisesRegex(ValueError, "single-scene"):
            annotations.clear_rich_steps(doc, 3, 1)

    def test_selected_child_visibility_tick_alignment_and_speed_are_still_required(self):
        for at in [-1, 4, True, "1/3001"]:
            doc = fixture(2)
            before = copy.deepcopy(doc)
            with self.subTest(at=at), self.assertRaises(ValueError):
                annotations.set_rich_steps(
                    doc, 3, dict(schema_version=1, steps=[dict(at=at, rich=dict(fontSize=40))])
                )
            with self.subTest(clear=at), self.assertRaises(ValueError):
                annotations.clear_rich_steps(doc, 3, at)
            self.assertEqual(doc, before)
        for name, value in [("scalar", 0), ("duration", 0), ("mediaStart", -1)]:
            doc = fixture()
            leaf(doc)[name] = value
            with self.subTest(name=name), self.assertRaises(ValueError):
                annotations.set_rich_steps(doc, 3, spec())

    def test_group_scope_does_not_bypass_complete_partition_and_point_frame_validation(self):
        for mutation in ["interval", "partial", "unknown-type"]:
            doc = expected(fixture())
            if mutation == "interval":
                frames(doc)[1].update(time=1000, duration=1000)
            elif mutation == "partial":
                frames(doc)[1]["value"][0]["rangeEnd"] = 6
            else:
                leaf(doc)["def"]["textAttributes"]["type"] = "double"
            before = copy.deepcopy(doc)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                annotations.set_rich_steps(doc, 3, spec())
            with self.subTest(clear=mutation), self.assertRaises(ValueError):
                annotations.clear_rich_steps(doc, 3, 1)
            self.assertEqual(doc, before)

    def test_cli_stages_grouped_states_and_clear_without_overwriting_source(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.json"
            request = root / "spec.json"
            out = root / "states.json"
            clear = root / "clear.json"
            source.write_bytes(project.encode_document(fixture(3)))
            request.write_text(json.dumps(spec()))
            before = source.read_bytes()
            stream = io.StringIO()
            with patch("sys.stdout", stream):
                status = annotations.main(
                    [
                        "set-rich-steps",
                        str(source),
                        "--clip-id",
                        "3",
                        "--spec",
                        str(request),
                        "--output",
                        str(out),
                    ]
                )
            self.assertEqual(status, 0)
            report = json.loads(stream.getvalue())
            self.assertTrue(report["written"])
            self.assertFalse(report["nativeVerified"])
            self.assertEqual(json.loads(out.read_bytes()), expected(fixture(3)))
            with patch("sys.stdout", io.StringIO()):
                self.assertEqual(
                    annotations.main(
                        [
                            "clear-rich-steps",
                            str(out),
                            "--clip-id",
                            "3",
                            "--at",
                            "3/2",
                            "--output",
                            str(clear),
                        ]
                    ),
                    0,
                )
            wanted = expected(fixture(3))
            frames(wanted)[0]["value"] = copy.deepcopy(frames(wanted)[2]["value"])
            leaf(wanted)["def"]["textAttributes"]["keyframes"] = [frames(wanted)[0]]
            self.assertEqual(json.loads(clear.read_bytes()), wanted)
            self.assertEqual(source.read_bytes(), before)
