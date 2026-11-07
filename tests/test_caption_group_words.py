from __future__ import annotations

import copy
from fractions import Fraction
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

from test_captions import dynamic, words
from test_caption_groups import child_clock, grouped, leaf, one_group, row
import captions
import project

R = 705600000


def word_source(doc):
    owner = leaf(doc)
    audio = owner["audio"] if owner["_type"] == "UnifiedMedia" else owner
    audio["parameters"].pop("captions")
    return doc


def grouped_display():
    doc = word_source(grouped())
    display = copy.deepcopy(project.scene_tracks(dynamic())[0][1]["medias"][0])
    display.update(start=0, duration=8 * R, mediaDuration=8 * R)
    inner = next(n for _, n in project.objects(doc) if n.get("id") == 100)
    inner["tracks"].append(
        dict(trackIndex=1, medias=[display], parameters={}, metadata={"opaque": ["lane"]})
    )
    return doc


def display_of(doc):
    return next(
        n for _, n in project.objects(doc) if n.get("id") == 6 and n.get("_type") == "Callout"
    )


class GroupWordTests(unittest.TestCase):
    def test_inspection_selects_a_recognized_group_owner_without_closed_captions_or_duplicate_audio(
        self,
    ):
        doc = word_source(grouped())
        before = copy.deepcopy(doc)
        self.assertEqual(
            captions.inventory(doc)["audioUses"],
            [
                dict(
                    clipId=3,
                    audioClipId=5,
                    ownerType="UnifiedMedia",
                    path="/timeline/sceneTrack/scenes/0/csml/tracks/0/medias/0/tracks/0/medias/0/tracks/0/medias/0/tracks/0/medias/0",
                    sourceId=1,
                    sourceTrack=1,
                    clocks=dict(
                        start=R, duration=3 * R, mediaStart=2 * R, mediaDuration=6 * R, scalar="1/2"
                    ),
                    containers=[
                        dict(clipId=100, ownerType="Group"),
                        dict(clipId=101, ownerType="Group"),
                        dict(clipId=102, ownerType="Group"),
                    ],
                )
            ],
        )
        self.assertEqual(doc, before)

    def test_inspection_lists_standalone_audio_and_retains_raw_unknown_clock_fields(self):
        doc = word_source(one_group("audio"))
        leaf(doc)["start"] = "unknown native placement"
        uses = captions.inventory(doc)["audioUses"]
        self.assertEqual(len(uses), 1)
        self.assertEqual(
            (uses[0]["clipId"], uses[0]["audioClipId"], uses[0]["ownerType"]), (3, 3, "AMFile")
        )
        self.assertEqual(uses[0]["clocks"]["start"], "unknown native placement")
        with self.assertRaises(ValueError):
            captions.map_captions(doc, 3)

    def test_standalone_audio_uses_its_saved_stream_and_the_same_parent_clock(self):
        linked = word_source(one_group(inpoint=3, duration=5))
        standalone = word_source(one_group("audio", inpoint=3, duration=5))
        before = copy.deepcopy(standalone)
        self.assertEqual(captions.map_captions(standalone, 3), captions.map_captions(linked, 3))
        result = captions.retime(
            standalone,
            3,
            dict(schema_version=1, clock="parent", start=0, duration=5, media_start=3, scalar=1),
        )
        self.assertEqual(leaf(result)["mediaStart"], 3 * R)
        self.assertEqual(words(result), words(before))
        self.assertEqual(standalone, before)

    def test_parent_trim_carries_the_active_word_with_its_original_source_onset(self):
        doc = word_source(one_group(inpoint=3, duration=5))
        before = copy.deepcopy(doc)
        result = captions.map_captions(doc, 3)
        self.assertEqual(
            result,
            dict(
                clipId=3,
                clock=R,
                closed=[],
                ancestors=[100],
                words=[
                    row(1, "useful", 2, "1", "2"),
                    row(2, "last.", 4, "2", "4"),
                    row(3, "%GAP", 6, "4", "6"),
                ],
            ),
        )
        self.assertEqual(doc, before)
        self.assertEqual(captions.map_captions(doc, 5), result)

    def test_selected_audio_trim_omits_earlier_onsets_before_parent_composition(self):
        doc = word_source(one_group(duration=5))
        child_clock(doc, start=0, duration=5 * R, mediaStart=3 * R, mediaDuration=5 * R)
        self.assertEqual(
            captions.map_captions(doc, 3)["words"],
            [row(2, "last.", 4, "2", "4"), row(3, "%GAP", 6, "4", "6")],
        )

    def test_three_parent_windows_crop_word_holds_without_reapplying_linked_mirrors(self):
        doc = word_source(grouped())
        self.assertEqual(
            captions.map_captions(doc, 3)["words"],
            [
                row(1, "useful", 2, "1", "3/2"),
                row(2, "last.", 4, "3/2", "5/2"),
                row(3, "%GAP", 6, "5/2", "7/2"),
            ],
        )
        self.assertEqual(captions.map_captions(doc, 3)["ancestors"], [100, 101, 102])

    def test_group_speed_and_odd_tick_gap_keep_exact_rationals(self):
        doc = word_source(one_group(scalar="1/2", duration=4))
        self.assertEqual(
            captions.map_captions(doc, 3)["words"],
            [
                row(0, "First", Fraction(1, 50), "101/100", "2"),
                row(1, "useful", 2, "2", "3"),
                row(2, "last.", 4, "3", "4"),
                row(3, "%GAP", 6, "4", "5"),
            ],
        )
        gap = words(doc)["keyframes"][-1]
        gap.update(time=6 * R + 1, endTime=6 * R + 1)
        last = captions.map_captions(doc, 3)["words"][-1]
        self.assertEqual(last["timelineStartTicks"], "5644800001/2")
        self.assertEqual(last["timelineStartSeconds"], "5644800001/1411200000")
        self.assertEqual(last["timelineEndTicks"], 5 * R)

    def test_signed_relative_owner_placement_is_cropped_by_the_parent(self):
        doc = word_source(one_group(duration=5))
        child_clock(doc, start=-3 * R)
        self.assertEqual(
            captions.map_captions(doc, 3)["words"],
            [
                row(1, "useful", 2, "1", "2"),
                row(2, "last.", 4, "2", "4"),
                row(3, "%GAP", 6, "4", "6"),
            ],
        )

    def test_recognition_and_closed_only_remain_distinct_and_refusals_are_read_only(self):
        for mutation in ["missing", "flag", "shape", "offset", "source-bound"]:
            doc = word_source(one_group())
            stream = doc["sourceBin"][0]["sourceTracks"][1]
            if mutation == "missing":
                stream["parameters"].pop("transcription")
            elif mutation == "flag":
                stream["transcriptionSet"] = False
            elif mutation == "shape":
                words(doc)["keyframes"][1]["duration"] = 1
            elif mutation == "offset":
                leaf(doc)["audio"]["attributes"]["sourceFileOffset"] = 1
            else:
                child_clock(doc, duration=9 * R, mediaDuration=9 * R)
            before = copy.deepcopy(doc)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                captions.map_captions(doc, 3)
            self.assertEqual(doc, before)
        with self.assertRaisesRegex(ValueError, "saved closed captions"):
            captions.map_captions(word_source(one_group()), 3, closed_only=True)

    def test_parent_clock_retime_accepts_actual_transcription_without_closed_cues(self):
        doc = word_source(grouped())
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
        result = captions.retime(
            doc,
            5,
            dict(
                schema_version=1, clock="parent", start=2, duration=2, media_start=4, scalar="1/2"
            ),
        )
        self.assertEqual(result, expected)
        self.assertEqual(
            captions.map_captions(result, 3)["words"],
            [row(2, "last.", 4, "3/2", "5/2"), row(3, "%GAP", 6, "5/2", "7/2")],
        )
        self.assertEqual(doc, before)
        with self.assertRaisesRegex(ValueError, "clock parent"):
            captions.retime(
                doc, 3, dict(schema_version=1, start=2, duration=2, media_start=4, scalar="1/2")
            )

    def test_group_display_bounds_change_only_selected_clock_fields(self):
        doc = grouped_display()
        before = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        display_of(expected).update(start=R, duration=2 * R, mediaDuration=2 * R)
        result = captions.set_display(
            doc, 6, dict(schema_version=1, clock="parent", start=1, duration=2)
        )
        self.assertEqual(result, expected)
        self.assertEqual(doc, before)
        self.assertEqual(
            captions.set_display(
                result, 6, dict(schema_version=1, clock="parent", start=1, duration=2)
            ),
            result,
        )

    def test_malformed_owner_parameter_objects_refuse_retiming_without_mutation(self):
        for parameters in [None, [], 1]:
            doc = word_source(grouped())
            leaf(doc)["audio"]["parameters"] = parameters
            before = copy.deepcopy(doc)
            with (
                self.subTest(parameters=parameters),
                self.assertRaisesRegex(ValueError, "parameter objects"),
            ):
                captions.retime(
                    doc,
                    3,
                    dict(
                        schema_version=1,
                        clock="parent",
                        start=0,
                        duration=2,
                        media_start=4,
                        scalar=1,
                    ),
                )
            self.assertEqual(doc, before)

    def test_negative_group_display_bounds_preserve_parent_extents_and_all_rich_ranges(self):
        doc = grouped_display()
        expected = copy.deepcopy(doc)
        display_of(expected).update(start=-R, duration=6 * R, mediaDuration=6 * R)
        result = captions.set_display(
            doc, 6, dict(schema_version=1, clock="parent", start=-1, duration=6)
        )
        self.assertEqual(result, expected)
        with self.assertRaisesRegex(ValueError, "nonnegative root"):
            captions.set_display(dynamic(), 6, dict(schema_version=1, start=-1))

    def test_group_display_requires_explicit_parent_clock_and_meaningful_edits(self):
        for request in [
            dict(schema_version=1, start=1),
            dict(schema_version=1, clock="timeline", start=1),
            dict(schema_version=1, clock="parent"),
        ]:
            doc = grouped_display()
            before = copy.deepcopy(doc)
            with self.subTest(request=request), self.assertRaises(ValueError):
                captions.set_display(doc, 6, request)
            self.assertEqual(doc, before)

    def test_display_collision_and_transition_fit_are_checked_in_the_child_lane(self):
        doc = grouped_display()
        inner = next(n for _, n in project.objects(doc) if n.get("id") == 100)
        lane = inner["tracks"][1]
        lane["medias"].append(dict(id=99, _type="Callout", start=2 * R, duration=R))
        with self.assertRaisesRegex(ValueError, "lane siblings"):
            captions.set_display(
                doc, 6, dict(schema_version=1, clock="parent", start=1, duration=2)
            )
        self.assertEqual(
            display_of(
                captions.set_display(
                    doc, 6, dict(schema_version=1, clock="parent", start=1, duration=1)
                )
            )["duration"],
            R,
        )
        lane["medias"].pop()
        lane["transitions"] = [dict(name="Fade", duration=R, leftMedia=6)]
        with self.assertRaises(ValueError):
            captions.set_display(doc, 6, dict(schema_version=1, clock="parent", duration="1/2"))

    def test_unsupported_display_clocks_and_ancestor_shapes_refuse_atomically(self):
        for mutation in [
            "trim",
            "speed",
            "effect",
            "animation",
            "fractional",
            "drift",
            "unknown-container",
            "root-start",
        ]:
            doc = grouped_display()
            display = display_of(doc)
            request = dict(schema_version=1, clock="parent", start=0, duration=2)
            if mutation == "trim":
                display["mediaStart"] = R
            elif mutation == "speed":
                display["scalar"] = "1/2"
            elif mutation == "effect":
                display["effects"] = [dict(effectName="Fade")]
            elif mutation == "animation":
                display["animationTracks"] = {"opaque": []}
            elif mutation == "fractional":
                request["start"] = "1/100"
            elif mutation == "root-start":
                project.scene_tracks(doc)[0][0]["medias"][0]["start"] = -R
            else:
                inner = next(n for _, n in project.objects(doc) if n.get("id") == 100)
                if mutation == "drift":
                    inner["scalar"] = 2
                else:
                    inner["_type"] = "FutureContainer"
            before = copy.deepcopy(doc)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                captions.set_display(doc, 6, request)
            self.assertEqual(doc, before)

    def test_cli_word_mapping_and_parent_display_staging_are_json_and_preserve_inputs(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source, spec, output = [
                root / name for name in ["source.json", "spec.json", "candidate.json"]
            ]
            source.write_text(json.dumps(grouped_display()))
            before = source.read_bytes()
            with redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(captions.main(["map", str(source), "--clip-id", "5"]), 0)
                result = json.loads(stdout.getvalue())
                self.assertEqual(result["mapping"]["ancestors"], [100, 101, 102])
                self.assertEqual(result["mapping"]["words"][0]["value"], "useful")
            spec.write_text(
                json.dumps(dict(schema_version=1, clock="parent", start=-1, duration=6))
            )
            with redirect_stdout(io.StringIO()) as stdout:
                self.assertEqual(
                    captions.main(
                        [
                            "set-display",
                            str(source),
                            "--clip-id",
                            "6",
                            "--spec",
                            str(spec),
                            "--output",
                            str(output),
                        ]
                    ),
                    0,
                )
                self.assertTrue(json.loads(stdout.getvalue())["written"])
            self.assertEqual(display_of(json.loads(output.read_text()))["start"], -R)
            spec.write_text(json.dumps(dict(schema_version=1, start=1)))
            with redirect_stderr(io.StringIO()) as stderr:
                self.assertEqual(
                    captions.main(
                        [
                            "set-display",
                            str(source),
                            "--clip-id",
                            "6",
                            "--spec",
                            str(spec),
                            "--output",
                            str(root / "refused.json"),
                        ]
                    ),
                    1,
                )
                self.assertIn("clock parent", json.loads(stderr.getvalue())["error"])
            self.assertEqual(source.read_bytes(), before)
            self.assertFalse((root / "refused.json").exists())


if __name__ == "__main__":
    unittest.main()
