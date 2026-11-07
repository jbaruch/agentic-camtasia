from __future__ import annotations

import copy
from fractions import Fraction
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

from test_captions import fixture, point, value, words
import captions
import project

R = 705600000


def leaf(doc):
    return next(n for _, n in project.objects(doc) if n.get("id") == 3 and "_type" in n)


def parameter(doc):
    node = leaf(doc)
    if node["_type"] == "UnifiedMedia":
        node = node["audio"]
    return node["parameters"]["captionData" if node["_type"] == "Caption" else "captions"]


def child_clock(doc, **clock):
    node = leaf(doc)
    for n in [node, node["video"], node["audio"]] if node["_type"] == "UnifiedMedia" else [node]:
        n.update(clock)


def grouped(form="linked", depth=3):
    doc = fixture(form)
    parameter(doc)["keyframes"] = [
        point(0, value("ONE")),
        point(2, value("TWO")),
        point(4, value("THREE")),
        point(6, value("FOUR")),
        point(7, value("")),
    ]
    child_clock(doc, start=R, duration=3 * R, mediaStart=2 * R, mediaDuration=6 * R, scalar="1/2")
    node = leaf(doc)
    for level, (start, inpoint) in enumerate([(R // 2, 3 * R // 2), (R, R // 2), (R, R)][:depth]):
        node = dict(
            _type="Group",
            id=100 + level,
            start=start,
            duration=5 * R // 2,
            mediaStart=inpoint,
            mediaDuration=5.0 * R / 2,
            scalar=1,
            tracks=[
                dict(trackIndex=0, medias=[node], parameters={}, metadata={"IsLocked": "False"})
            ],
            attributes=dict(widthAttr=640.0, heightAttr=360.0, assetProperties=[], opaque=[level]),
            parameters={"translation0": 60.0, "volume": 0.4},
            metadata={"isOpen": {"type": "bool", "value": False}, "opaque": [level]},
            effects=[],
            animationTracks={"opaque": ["keep"]},
        )
    project.scene_tracks(doc)[0][0]["medias"] = [node]
    return doc


def one_group(form="linked", *, scalar: int | str = 1, inpoint=0, duration=8):
    doc = grouped(form, 1)
    child_clock(doc, start=0, duration=8 * R, mediaStart=0, mediaDuration=8 * R, scalar=1)
    parent = project.scene_tracks(doc)[0][0]["medias"][0]
    parent.update(
        start=R,
        duration=int(Fraction(duration) * R),
        mediaStart=inpoint * R,
        mediaDuration=int(Fraction(duration) * R / Fraction(scalar)),
        scalar=scalar,
    )
    return doc


def row(index, text, source, start, end):
    start_ticks, end_ticks = Fraction(start) * R, Fraction(end) * R
    return dict(
        index=index,
        value=text,
        sourceTime=source * R,
        timelineStartTicks=int(start_ticks) if start_ticks.denominator == 1 else str(start_ticks),
        timelineEndTicks=int(end_ticks) if end_ticks.denominator == 1 else str(end_ticks),
        timelineStartSeconds=start,
        timelineEndSeconds=end,
    )


NESTED_ROWS = [
    row(1, "TWO", 2, "1", "3/2"),
    row(2, "THREE", 4, "3/2", "5/2"),
    row(3, "FOUR", 6, "5/2", "3"),
    row(4, "", 7, "3", "7/2"),
]


def retime_spec(**changes):
    return dict(
        schema_version=1,
        clock="parent",
        start=2,
        duration=2,
        media_start=4,
        scalar="1/2",
        **changes,
    )


class GroupCaptionTests(unittest.TestCase):
    def test_three_group_intersections_preserve_raw_hold_onsets_and_owner_identity(self):
        for form in ["linked", "audio", "imported"]:
            doc = grouped(form)
            before = copy.deepcopy(doc)
            with self.subTest(form=form):
                result = captions.map_captions(doc, 3, closed_only=True)
                self.assertEqual(
                    result,
                    dict(
                        clipId=3,
                        clock=R,
                        closed=NESTED_ROWS,
                        scope="closed",
                        ancestors=[100, 101, 102],
                    ),
                )
                self.assertEqual(doc, before)
                self.assertNotIn("words", result)

    def test_linked_audio_selection_does_not_add_its_mirrored_clock(self):
        doc = grouped()
        self.assertEqual(
            captions.map_captions(doc, 5, closed_only=True),
            dict(clipId=3, clock=R, closed=NESTED_ROWS, scope="closed", ancestors=[100, 101, 102]),
        )

    def test_parent_placement_trim_and_both_inverse_speeds_have_fixed_global_ranges(self):
        cases = [
            (
                1,
                1,
                6,
                [
                    row(0, "ONE", 0, "1", "2"),
                    row(1, "TWO", 2, "2", "4"),
                    row(2, "THREE", 4, "4", "6"),
                    row(3, "FOUR", 6, "6", "7"),
                ],
            ),
            (
                "1/2",
                0,
                4,
                [
                    row(0, "ONE", 0, "1", "2"),
                    row(1, "TWO", 2, "2", "3"),
                    row(2, "THREE", 4, "3", "4"),
                    row(3, "FOUR", 6, "4", "9/2"),
                    row(4, "", 7, "9/2", "5"),
                ],
            ),
            (
                2,
                0,
                16,
                [
                    row(0, "ONE", 0, "1", "5"),
                    row(1, "TWO", 2, "5", "9"),
                    row(2, "THREE", 4, "9", "13"),
                    row(3, "FOUR", 6, "13", "15"),
                    row(4, "", 7, "15", "17"),
                ],
            ),
        ]
        for scalar, inpoint, duration, expected in cases:
            doc = one_group(scalar=scalar, inpoint=inpoint, duration=duration)
            with self.subTest(scalar=scalar):
                self.assertEqual(
                    captions.map_captions(doc, 3, closed_only=True)["closed"], expected
                )

    def test_fractional_global_ticks_are_reported_without_rounding(self):
        doc = one_group(scalar="1/2", duration=4)
        parameter(doc)["keyframes"] = [
            point(0, value("ODD")),
            dict(time=1, endTime=1, duration=0, value=value("REST")),
        ]
        result = captions.map_captions(doc, 3, closed_only=True)["closed"][0]
        self.assertEqual(result["timelineStartTicks"], R)
        self.assertEqual(result["timelineEndTicks"], "1411200001/2")
        self.assertEqual(result["timelineEndSeconds"], "1411200001/1411200000")

    def test_signed_child_placement_maps_authors_and_retimes_without_changing_parents(self):
        expected_rows = [
            row(0, "ONE", 0, "1", "2"),
            row(1, "TWO", 2, "2", "4"),
            row(2, "THREE", 4, "4", "6"),
            row(3, "FOUR", 6, "6", "7"),
            row(4, "", 7, "7", "8"),
        ]
        for form in ["linked", "audio", "imported"]:
            doc = one_group(form, duration=7)
            child_clock(doc, start=-R)
            before = copy.deepcopy(doc)
            with self.subTest(form=form):
                self.assertEqual(
                    captions.map_captions(doc, 3, closed_only=True)["closed"], expected_rows
                )
                candidate = captions.set_cues(
                    doc,
                    3,
                    dict(schema_version=1, clock="timeline", cues=[dict(start=1, end=2, text="A")]),
                )
                expected = copy.deepcopy(doc)
                expected["timeline"]["captionAttributes"]["enabled"] = True
                parameter(expected)["keyframes"] = [
                    point(0, value("")),
                    point(1, value("A")),
                    point(2, value("")),
                ]
                self.assertEqual(candidate, expected)
                candidate = captions.set_cues(
                    doc,
                    3,
                    dict(schema_version=1, clock="media", cues=[dict(start=0, end=2, text="A")]),
                )
                expected = copy.deepcopy(doc)
                expected["timeline"]["captionAttributes"]["enabled"] = True
                parameter(expected)["keyframes"] = [point(0, value("A")), point(2, value(""))]
                self.assertEqual(candidate, expected)
                request = dict(
                    schema_version=1, clock="parent", start=-2, duration=8, media_start=0, scalar=1
                )
                expected = copy.deepcopy(doc)
                child_clock(expected, start=-2 * R)
                result = captions.retime(doc, 3, request)
                self.assertEqual(result, expected)
                self.assertEqual(
                    captions.map_captions(result, 3, closed_only=True)["closed"],
                    [
                        row(1, "TWO", 2, "1", "3"),
                        row(2, "THREE", 4, "3", "5"),
                        row(3, "FOUR", 6, "5", "6"),
                        row(4, "", 7, "6", "7"),
                    ],
                )
                request["start"] = "-1/705600001"
                with self.assertRaises(ValueError):
                    captions.retime(doc, 3, request)
                self.assertEqual(doc, before)
        with self.assertRaisesRegex(ValueError, "nonnegative root"):
            captions.retime(
                fixture(), 3, dict(schema_version=1, start=-1, duration=8, media_start=0, scalar=1)
            )

    def test_signed_inner_group_offsets_crop_before_nonnegative_root_placement(self):
        doc = one_group(duration=7)
        outer = project.scene_tracks(doc)[0][0]["medias"][0]
        inner = copy.deepcopy(outer)
        inner.update(id=101, start=-R, duration=8 * R, mediaDuration=8 * R)
        outer["tracks"][0]["medias"] = [inner]
        before = copy.deepcopy(doc)
        self.assertEqual(
            captions.map_captions(doc, 3, closed_only=True)["closed"],
            [
                row(0, "ONE", 0, "1", "2"),
                row(1, "TWO", 2, "2", "4"),
                row(2, "THREE", 4, "4", "6"),
                row(3, "FOUR", 6, "6", "7"),
                row(4, "", 7, "7", "8"),
            ],
        )
        self.assertEqual(doc, before)
        outer["start"] = -R
        with self.assertRaisesRegex(ValueError, "ancestor Group clocks"):
            captions.map_captions(doc, 3, closed_only=True)

    def test_closed_only_does_not_parse_or_map_recognition(self):
        doc = grouped()
        words(doc)["keyframes"][0]["value"] = None
        self.assertEqual(captions.map_captions(doc, 3, closed_only=True)["closed"], NESTED_ROWS)
        with self.assertRaises(ValueError):
            captions.map_captions(doc, 3)
        root_doc = fixture()
        self.assertIn("words", captions.map_captions(root_doc, 3))
        self.assertNotIn("words", captions.map_captions(root_doc, 3, closed_only=True))

    def test_wholly_cropped_child_returns_no_visible_intervals(self):
        doc = one_group()
        parent = project.scene_tracks(doc)[0][0]["medias"][0]
        child_clock(doc, start=0, duration=2 * R, mediaStart=0, mediaDuration=2 * R, scalar=1)
        sibling = copy.deepcopy(leaf(doc))
        sibling["id"] = 20
        sibling["video"]["id"], sibling["audio"]["id"] = 21, 22
        for node in [sibling, sibling["video"], sibling["audio"]]:
            node.update(start=0, duration=8 * R, mediaStart=0, mediaDuration=8 * R, scalar=1)
        parent["tracks"].append(dict(trackIndex=1, medias=[sibling], parameters={}))
        parent.update(mediaStart=3 * R, duration=2 * R, mediaDuration=2 * R)
        self.assertEqual(captions.map_captions(doc, 3, closed_only=True)["closed"], [])
        request = dict(schema_version=1, clock="timeline", cues=[dict(start=1, end=2, text="x")])
        with self.assertRaisesRegex(ValueError, "visible window"):
            captions.set_cues(doc, 3, request)
        request["clock"] = "media"
        self.assertEqual(
            parameter(captions.set_cues(doc, 3, request))["keyframes"],
            [point(0, value("")), point(1, value("x")), point(2, value(""))],
        )

    def test_media_cues_preserve_every_parent_binding_clock_and_source_word(self):
        for form in ["linked", "audio", "imported"]:
            doc = grouped(form)
            before = copy.deepcopy(doc)
            expected = copy.deepcopy(doc)
            parameter(expected)["keyframes"] = [
                point(0, value("")),
                point(2, value("NEW")),
                point(4, value("")),
            ]
            expected["timeline"]["captionAttributes"]["enabled"] = True
            with self.subTest(form=form):
                result = captions.set_cues(
                    doc,
                    3,
                    dict(schema_version=1, clock="media", cues=[dict(start=2, end=4, text="NEW")]),
                )
                self.assertEqual(result, expected)
                self.assertEqual(doc, before)

    def test_timeline_cues_invert_all_three_group_clocks_before_authoring(self):
        doc = grouped()
        expected = copy.deepcopy(doc)
        parameter(expected)["keyframes"] = [
            point(0, value("")),
            point(3, value("A")),
            point(4, value("B")),
            point(6, value("")),
        ]
        expected["timeline"]["captionAttributes"]["enabled"] = True
        spec = dict(
            schema_version=1,
            clock="timeline",
            cues=[dict(start=1, end="3/2", text="A"), dict(start="3/2", end="5/2", text="B")],
        )
        result = captions.set_cues(doc, 3, spec)
        self.assertEqual(result, expected)
        self.assertEqual(captions.set_cues(result, 3, spec), result)

    def test_late_out_of_window_cue_and_fractional_source_ticks_refuse_atomically(self):
        doc = grouped()
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "visible window"):
            captions.set_cues(
                doc,
                3,
                dict(
                    schema_version=1,
                    clock="timeline",
                    cues=[
                        dict(start=1, end="3/2", text="valid"),
                        dict(start=3, end=4, text="outside"),
                    ],
                ),
            )
        self.assertEqual(doc, before)
        doc = one_group(scalar=2, duration=16)
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "exact media ticks"):
            captions.set_cues(
                doc,
                3,
                dict(
                    schema_version=1,
                    clock="timeline",
                    cues=[dict(start="705600001/705600000", end=2, text="fractional")],
                ),
            )
        self.assertEqual(doc, before)

    def test_empty_cue_array_clears_without_expanding_or_retiming_any_group(self):
        doc = grouped()
        expected = copy.deepcopy(doc)
        parameter(expected)["keyframes"] = [point(0, value(""))]
        expected["timeline"]["captionAttributes"]["enabled"] = True
        self.assertEqual(
            captions.set_cues(doc, 3, dict(schema_version=1, clock="media", cues=[])), expected
        )

    def test_parent_clock_retime_preserves_all_ancestors_and_complete_source_points(self):
        for form in ["linked", "audio", "imported"]:
            doc = grouped(form)
            before = copy.deepcopy(doc)
            expected = copy.deepcopy(doc)
            child_clock(
                expected,
                start=2 * R,
                duration=2 * R,
                mediaStart=4 * R,
                mediaDuration=4 * R,
                scalar="1/2",
            )
            with self.subTest(form=form):
                result = captions.retime(doc, 3, retime_spec())
                self.assertEqual(result, expected)
                self.assertEqual(doc, before)
                self.assertEqual(
                    captions.map_captions(result, 3, closed_only=True)["closed"],
                    [
                        row(2, "THREE", 4, "3/2", "5/2"),
                        row(3, "FOUR", 6, "5/2", "3"),
                        row(4, "", 7, "3", "7/2"),
                    ],
                )

    def test_audio_child_retime_targets_the_complete_linked_clock(self):
        doc = grouped()
        self.assertEqual(
            captions.retime(doc, 5, retime_spec()), captions.retime(doc, 3, retime_spec())
        )

    def test_shorter_child_keeps_its_parent_duration_and_crops_later_cues(self):
        doc = one_group()
        request = dict(
            schema_version=1, clock="parent", start=0, duration=6, media_start=0, scalar=1
        )
        result = captions.retime(doc, 3, request)
        parent = project.scene_tracks(result)[0][0]["medias"][0]
        self.assertEqual(parent["duration"], 8 * R)
        self.assertEqual(
            captions.map_captions(result, 3, closed_only=True)["closed"],
            [row(0, "ONE", 0, "1", "3"), row(1, "TWO", 2, "3", "5"), row(2, "THREE", 4, "5", "7")],
        )

    def test_group_retime_requires_an_explicit_parent_clock(self):
        doc = grouped()
        for clock in [None, "timeline", "media", "unknown"]:
            request = retime_spec()
            if clock is None:
                request.pop("clock")
            else:
                request["clock"] = clock
            with self.subTest(clock=clock), self.assertRaisesRegex(ValueError, "parent"):
                captions.retime(doc, 3, request)

    def test_local_lane_collision_refuses_but_touching_endpoints_remain_valid(self):
        doc = grouped()
        parent = next(n for _, n in project.objects(doc) if n.get("id") == 100)
        sibling = dict(
            id=20,
            _type="AMFile",
            start=4 * R,
            duration=R,
            mediaStart=0,
            mediaDuration=R,
            scalar=1,
            src=1,
            trackNumber=1,
            parameters={},
            effects=[],
            animationTracks={},
        )
        parent["tracks"][0]["medias"].append(sibling)
        before = copy.deepcopy(doc)
        request = retime_spec()
        request.update(duration=3, media_start=2, scalar=1)
        with self.assertRaisesRegex(ValueError, "lane siblings"):
            captions.retime(doc, 3, request)
        self.assertEqual(doc, before)
        self.assertEqual(leaf(captions.retime(doc, 3, retime_spec()))["duration"], 2 * R)

    def test_bad_transition_and_selected_child_effects_still_refuse(self):
        for mutation in ["transition", "effect", "animation", "bounds", "frame"]:
            doc = grouped()
            parent = next(n for _, n in project.objects(doc) if n.get("id") == 100)
            request = retime_spec()
            if mutation == "transition":
                parent["tracks"][0]["transitions"] = [
                    dict(name="Fade", leftMedia=3, duration=4 * R)
                ]
            elif mutation == "effect":
                leaf(doc)["audio"]["effects"] = [dict(effectName="keep")]
            elif mutation == "animation":
                leaf(doc)["animationTracks"] = {"keep": [1]}
            elif mutation == "bounds":
                request["media_start"] = 7
            else:
                request["start"] = "1/31"
            before = copy.deepcopy(doc)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                captions.retime(doc, 3, request)
            self.assertEqual(doc, before)

    def test_unsupported_ancestry_build_offsets_and_clock_shapes_refuse_without_mutation(self):
        for mutation in [
            "stitched",
            "container",
            "scenes",
            "old-build",
            "offset",
            "mirror",
            "group-id",
            "group-start",
            "group-inpoint",
            "group-duration",
            "group-scalar",
        ]:
            doc = grouped()
            group = next(n for _, n in project.objects(doc) if n.get("id") == 100)
            if mutation == "group-start":
                group = project.scene_tracks(doc)[0][0]["medias"][0]
            if mutation in ["stitched", "container"]:
                group["_type"] = "StitchedMedia" if mutation == "stitched" else "FutureContainer"
            elif mutation == "scenes":
                doc["timeline"]["sceneTrack"]["scenes"].append(
                    copy.deepcopy(doc["timeline"]["sceneTrack"]["scenes"][0])
                )
            elif mutation == "old-build":
                doc["version"] = "9.0"
                doc["authoringClientName"]["version"] = "2025.0.3"
            elif mutation == "offset":
                leaf(doc)["audio"]["attributes"]["sourceFileOffset"] = -1
            elif mutation == "mirror":
                leaf(doc)["audio"]["start"] = 0
            else:
                field = {
                    "group-id": "id",
                    "group-start": "start",
                    "group-inpoint": "mediaStart",
                    "group-duration": "duration",
                    "group-scalar": "scalar",
                }[mutation]
                group[field] = (
                    True if field == "id" else -1 if field in ["start", "mediaStart"] else 0
                )
            before = copy.deepcopy(doc)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                captions.map_captions(doc, 3, closed_only=True)
            self.assertEqual(doc, before)

    def test_known_group_reload_drift_refuses_only_when_on_the_selected_path(self):
        for scalar in ["1/2", 2]:
            doc = grouped()
            group = next(n for _, n in project.objects(doc) if n.get("id") == 100)
            group["scalar"] = scalar
            with self.subTest(scalar=scalar), self.assertRaisesRegex(ValueError, "native reopen"):
                captions.map_captions(doc, 3, closed_only=True)
        doc = grouped()
        extra = copy.deepcopy(project.scene_tracks(doc)[0][0]["medias"][0])
        extra["id"] = 999
        extra["scalar"] = 2
        extra["tracks"] = []
        project.scene_tracks(doc)[0].append(dict(trackIndex=1, medias=[extra], parameters={}))
        self.assertEqual(captions.map_captions(doc, 3, closed_only=True)["closed"], NESTED_ROWS)

    def test_opaque_or_rtf_cues_remain_readable_but_refuse_whole_cue_replacement(self):
        for mutation in ["point", "style", "rtf"]:
            doc = grouped()
            frame = parameter(doc)["keyframes"][1]
            if mutation == "point":
                frame["opaque"] = ["keep"]
            elif mutation == "style":
                frame["value"]["textAttributes"] = {"keep": True}
            else:
                frame["value"]["text"] = r"{\rtf1 native}"
            before = copy.deepcopy(doc)
            self.assertEqual(
                captions.map_captions(doc, 3, closed_only=True)["closed"][0]["sourceTime"], 2 * R
            )
            with self.assertRaises(ValueError):
                captions.set_cues(doc, 3, dict(schema_version=1, clock="media", cues=[]))
            self.assertEqual(doc, before)

    def test_closed_mapping_requires_a_saved_closed_parameter(self):
        doc = grouped()
        leaf(doc)["audio"]["parameters"].pop("captions")
        with self.assertRaisesRegex(ValueError, "saved closed captions"):
            captions.map_captions(doc, 3, closed_only=True)

    def test_cli_closed_mapping_parent_retime_and_refusal_use_json_without_source_writes(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            source, spec, output = (
                base / name for name in ["source.json", "spec.json", "out.json"]
            )
            doc = grouped()
            source.write_text(json.dumps(doc))
            raw = source.read_bytes()
            spec.write_text(json.dumps(retime_spec()))
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(
                    captions.main(["map", str(source), "--clip-id", "5", "--closed-only"]), 0
                )
                self.assertEqual(json.loads(out.getvalue())["mapping"]["closed"], NESTED_ROWS)
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(
                    captions.main(
                        [
                            "retime",
                            str(source),
                            "--clip-id",
                            "3",
                            "--spec",
                            str(spec),
                            "--output",
                            str(output),
                        ]
                    ),
                    0,
                )
                self.assertTrue(json.loads(out.getvalue())["written"])
            self.assertEqual(leaf(json.loads(output.read_text()))["mediaStart"], 4 * R)
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(captions.main(["map", str(source), "--clip-id", "3"]), 0)
                mapped = json.loads(out.getvalue())["mapping"]
                self.assertEqual(mapped["ancestors"], [100, 101, 102])
                self.assertEqual(mapped["words"][0]["value"], "useful")
            with redirect_stderr(io.StringIO()) as err:
                self.assertEqual(captions.main(["map", str(source), "--clip-id", "999"]), 1)
                self.assertIn("unique saved clip ID", json.loads(err.getvalue())["error"])
            self.assertEqual(source.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
