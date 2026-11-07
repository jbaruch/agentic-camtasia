from __future__ import annotations

import copy
from contextlib import redirect_stderr, redirect_stdout
from fractions import Fraction
import io
import json
from pathlib import Path
import tempfile
from typing import Any
import unittest

from test_captions import fixture, point, value, root, closed, words
from test_caption_groups import row
import captions
import project

R = 705600000


def stitched(*, skip=False, group=False):
    doc = fixture()
    original = root(doc)
    left, right = copy.deepcopy(original), copy.deepcopy(original)
    duration = 3 if skip else 4
    for owner, ids, start, inpoint in [
        (left, (4, 5, 6), 0, 0),
        (right, (7, 8, 9), duration, 5 if skip else 4),
    ]:
        for node, ident in zip((owner, owner["video"], owner["audio"]), ids):
            node.update(
                id=ident,
                start=start * R,
                duration=duration * R,
                mediaStart=inpoint * R,
                mediaDuration=duration * R,
                scalar=1,
            )
        owner["audio"]["parameters"].pop("captions")
    parent: dict[str, Any] = dict(
        id=3,
        _type="StitchedMedia",
        minMediaStart=0.0,
        start=0,
        duration=duration * 2 * R,
        mediaStart=0,
        mediaDuration=duration * 2 * R,
        scalar=1,
        attributes=dict(sourceFileOffset=0, opaque=["parent"]),
        parameters=dict(captions=copy.deepcopy(closed(doc)), volume=0.7),
        effects=[],
        animationTracks={},
        metadata=dict(opaque=["native"]),
        medias=[left, right],
    )
    if skip:
        parent["parameters"]["captions"]["keyframes"] = [
            point(t, value(text))
            for t, text in [(0, "ONE"), (2, "TWO"), (3, "THREE"), (4, "FOUR"), (5, "")]
        ]
    project.scene_tracks(doc)[0][0]["medias"] = [parent]
    if group:
        project.scene_tracks(doc)[0][0]["medias"] = [
            dict(
                id=100,
                _type="Group",
                start=R,
                duration=6 * R,
                mediaStart=R,
                mediaDuration=6 * R,
                scalar=1,
                tracks=[dict(trackIndex=0, medias=[parent], parameters={})],
                attributes=dict(opaque=["group"]),
                parameters={},
                effects=[],
                animationTracks={},
            )
        ]
    return doc


def parent(doc):
    return next(n for _, n in project.objects(doc) if n.get("_type") == "StitchedMedia")


def source_row(index, text, source_seconds, begin, end, child, audio, stitch_seconds):
    return dict(
        row(index, text, source_seconds, begin, end),
        stitchTime=int(stitch_seconds * R),
        sourceClipId=child,
        audioClipId=audio,
        sourceId=1,
        sourceTrack=1,
    )


class StitchedCaptionTests(unittest.TestCase):
    def test_owner_speed_keeps_source_words_distinct_from_native_display_holds(self):
        doc = stitched()
        parent(doc).update(start=R, duration=4 * R, scalar="1/2")
        before = copy.deepcopy(doc)
        mapped = captions.map_captions(doc, 3)
        self.assertEqual(
            mapped["words"],
            [
                source_row(0, "First", Fraction(1, 50), "101/100", "2", 4, 6, Fraction(1, 50)),
                source_row(1, "useful", 2, "2", "3", 4, 6, 2),
                source_row(2, "last.", 4, "3", "4", 7, 9, 4),
                source_row(3, "%GAP", 6, "4", "5", 7, 9, 6),
            ],
        )
        self.assertEqual(
            mapped["displayWords"],
            [
                source_row(0, "First", Fraction(1, 50), "101/100", "2", 4, 6, Fraction(1, 50)),
                source_row(1, "useful", 2, "2", "3", 4, 6, 2),
                source_row(2, "last.", 4, "3", "7/2", 7, 9, 4),
                source_row(3, "%GAP", 6, "7/2", "5", 7, 9, 6),
            ],
        )
        self.assertEqual(doc, before)

    def test_final_window_projection_rebases_inside_a_parent_trim(self):
        doc = stitched()
        words(doc)["keyframes"] = [
            point(t, text)
            for t, text in [
                (Fraction(1, 50), "First"),
                (2, "useful"),
                (Fraction(17, 4), "before"),
                (Fraction(11, 2), "Blue"),
                (6, "Rivers"),
                (7, "%GAP"),
            ]
        ]
        parent(doc).update(
            start=R, duration=3 * R // 2, mediaStart=5 * R, mediaDuration=3 * R, scalar="1/2"
        )
        mapped = captions.map_captions(doc, 3)
        self.assertEqual(
            mapped["words"],
            [
                source_row(3, "Blue", Fraction(11, 2), "5/4", "3/2", 7, 9, Fraction(11, 2)),
                source_row(4, "Rivers", 6, "3/2", "2", 7, 9, 6),
                source_row(5, "%GAP", 7, "2", "5/2", 7, 9, 7),
            ],
        )
        self.assertEqual(
            mapped["displayWords"],
            [
                source_row(3, "Blue", Fraction(11, 2), "9/8", "5/4", 7, 9, Fraction(11, 2)),
                source_row(4, "Rivers", 6, "5/4", "3/2", 7, 9, 6),
                source_row(5, "%GAP", 7, "3/2", "5/2", 7, 9, 7),
            ],
        )

    def test_display_can_include_a_projected_onset_outside_the_consumed_audio_window(self):
        doc = stitched()
        words(doc)["keyframes"].insert(3, point(Fraction(11, 2), "future"))
        parent(doc).update(start=R, duration=5 * R // 2, mediaDuration=5 * R, scalar="1/2")
        mapped = captions.map_captions(doc, 3)
        self.assertEqual([h["value"] for h in mapped["words"]], ["First", "useful", "last."])
        self.assertEqual(
            mapped["displayWords"][-1],
            source_row(3, "future", Fraction(11, 2), "27/8", "7/2", 7, 9, Fraction(11, 2)),
        )
        self.assertEqual(mapped["words"][-1]["timelineEndSeconds"], "7/2")

    def test_projection_uses_the_final_child_not_the_child_count_or_first_join(self):
        doc = stitched()
        p = parent(doc)
        middle = copy.deepcopy(p["medias"][0])
        for offset, node in enumerate([middle, middle["video"], middle["audio"]]):
            node.update(
                id=10 + offset, start=2 * R, duration=2 * R, mediaStart=2 * R, mediaDuration=2 * R
            )
        for node in [p["medias"][0], p["medias"][0]["video"], p["medias"][0]["audio"]]:
            node.update(duration=2 * R, mediaDuration=2 * R)
        p["medias"].insert(1, middle)
        p.update(start=R, duration=4 * R, scalar="1/2")
        mapped = captions.map_captions(doc, 3)
        self.assertEqual(mapped["displayWords"][1], source_row(1, "useful", 2, "2", "3", 10, 12, 2))
        self.assertEqual(mapped["displayWords"][-1], source_row(3, "%GAP", 6, "7/2", "5", 7, 9, 6))

    def test_outer_group_speed_does_not_introduce_or_cancel_owner_projection(self):
        doc = stitched(group=True)
        group = project.scene_tracks(doc)[0][0]["medias"][0]
        group.update(duration=4 * R, mediaStart=0, mediaDuration=8 * R, scalar="1/2")
        mapped = captions.map_captions(doc, 3)
        self.assertEqual(mapped["words"], mapped["displayWords"])
        parent(doc).update(duration=16 * R, mediaDuration=8 * R, scalar=2)
        group.update(duration=8 * R, mediaDuration=16 * R)
        mapped = captions.map_captions(doc, 3)
        self.assertEqual(mapped["words"][-1], source_row(3, "%GAP", 6, "7", "9", 7, 9, 6))
        self.assertEqual(mapped["displayWords"][-1], source_row(2, "last.", 4, "5", "9", 7, 9, 4))
        self.assertEqual(mapped["displayWords"][0]["timelineStartSeconds"], "51/50")

    def test_display_projection_keeps_odd_ticks_exact(self):
        doc = stitched()
        parent(doc).update(start=R, duration=4 * R, scalar="1/2")
        words(doc)["keyframes"][-1].update(time=6 * R + 1, endTime=6 * R + 1)
        mapped = captions.map_captions(doc, 3)
        self.assertEqual(mapped["words"][-1]["timelineStartTicks"], "5644800001/2")
        self.assertEqual(mapped["displayWords"][-1]["timelineStartTicks"], "9878400001/4")
        self.assertEqual(mapped["displayWords"][-1]["stitchTime"], 6 * R + 1)

    def test_parent_captions_and_source_onsets_have_distinct_owners_and_exact_rows(self):
        doc = stitched()
        before = copy.deepcopy(doc)
        mapped = captions.map_captions(doc, 3)
        self.assertEqual(mapped.pop("displayWords"), mapped["words"])
        self.assertEqual(
            mapped,
            dict(
                clipId=3,
                clock=R,
                closed=[row(0, "First café", 0, "0", "4"), row(1, "Second → text", 4, "4", "8")],
                words=[
                    source_row(0, "First", Fraction(1, 50), "1/50", "2", 4, 6, Fraction(1, 50)),
                    source_row(1, "useful", 2, "2", "4", 4, 6, 2),
                    source_row(2, "last.", 4, "4", "6", 7, 9, 4),
                    source_row(3, "%GAP", 6, "6", "8", 7, 9, 6),
                ],
            ),
        )
        self.assertEqual(doc, before)

    def test_source_skip_composes_onsets_then_carries_last_retained_word_across_join(self):
        doc = stitched(skip=True)
        self.assertEqual(
            captions.map_captions(doc, 3)["words"],
            [
                source_row(0, "First", Fraction(1, 50), "1/50", "2", 4, 6, Fraction(1, 50)),
                source_row(1, "useful", 2, "2", "4", 4, 6, 2),
                source_row(3, "%GAP", 6, "4", "6", 7, 9, 4),
            ],
        )
        self.assertEqual(
            captions.map_captions(doc, 3, closed_only=True),
            dict(
                clipId=3,
                clock=R,
                scope="closed",
                ancestors=[],
                closed=[
                    row(0, "ONE", 0, "0", "2"),
                    row(1, "TWO", 2, "2", "3"),
                    row(2, "THREE", 3, "3", "4"),
                    row(3, "FOUR", 4, "4", "5"),
                    row(4, "", 5, "5", "6"),
                ],
            ),
        )

    def test_parent_source_trim_omits_earlier_word_onsets_but_carries_closed_cues(self):
        doc = stitched()
        parent(doc).update(start=R, duration=6 * R, mediaStart=R, mediaDuration=6 * R)
        mapped = captions.map_captions(doc, 3)
        self.assertEqual(
            mapped["closed"],
            [row(0, "First café", 0, "1", "4"), row(1, "Second → text", 4, "4", "7")],
        )
        self.assertEqual(
            mapped["words"],
            [
                source_row(1, "useful", 2, "2", "4", 4, 6, 2),
                source_row(2, "last.", 4, "4", "6", 7, 9, 4),
                source_row(3, "%GAP", 6, "6", "7", 7, 9, 6),
            ],
        )

    def test_group_crop_carries_a_stitched_word_and_parent_speed_preserves_subframes(self):
        doc = stitched(group=True)
        self.assertEqual(captions.map_captions(doc, 3)["ancestors"], [100])
        first = captions.map_captions(doc, 3)["words"][0]
        self.assertEqual(
            first, source_row(0, "First", Fraction(1, 50), "1", "2", 4, 6, Fraction(1, 50))
        )
        doc = stitched()
        parent(doc).update(start=R, duration=4 * R, scalar="1/2")
        self.assertEqual(
            captions.map_captions(doc, 3)["words"][0],
            source_row(0, "First", Fraction(1, 50), "101/100", "2", 4, 6, Fraction(1, 50)),
        )
        gap = words(doc)["keyframes"][-1]
        gap.update(time=6 * R + 1, endTime=6 * R + 1)
        mapped = captions.map_captions(doc, 3)["words"][-1]
        self.assertEqual(mapped["stitchTime"], 6 * R + 1)
        self.assertEqual(mapped["timelineStartTicks"], "5644800001/2")

    def test_parent_retime_changes_only_the_parent_clocks_and_preserves_every_child(self):
        doc = stitched()
        before = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        parent(expected).update(
            start=R, duration=3 * R, mediaStart=2 * R, mediaDuration=6 * R, scalar="1/2"
        )
        result = captions.retime(
            doc, 3, dict(schema_version=1, start=1, duration=3, media_start=2, scalar="1/2")
        )
        self.assertEqual(result, expected)
        self.assertEqual(doc, before)
        self.assertEqual(
            captions.retime(
                result, 3, dict(schema_version=1, start=1, duration=3, media_start=2, scalar="1/2")
            ),
            result,
        )

    def test_group_parent_retime_requires_explicit_immediate_parent_clock(self):
        doc = stitched(group=True)
        spec = dict(schema_version=1, start=0, duration=4, media_start=0, scalar="1/2")
        with self.assertRaisesRegex(ValueError, "clock parent"):
            captions.retime(doc, 3, spec)
        expected = copy.deepcopy(doc)
        parent(expected).update(start=0, duration=4 * R, mediaDuration=8 * R, scalar="1/2")
        self.assertEqual(captions.retime(doc, 3, dict(spec, clock="parent")), expected)

    def test_media_and_global_cue_authoring_edit_the_parent_parameter_only(self):
        doc = stitched(group=True)
        before = copy.deepcopy(doc)
        media = captions.set_cues(
            doc, 3, dict(schema_version=1, clock="media", cues=[dict(start=2, end=4, text="CUE")])
        )
        timeline = captions.set_cues(
            doc,
            3,
            dict(schema_version=1, clock="timeline", cues=[dict(start=2, end=4, text="CUE")]),
        )
        expected = copy.deepcopy(doc)
        parent(expected)["parameters"]["captions"]["keyframes"] = [
            point(0, value("")),
            point(2, value("CUE")),
            point(4, value("")),
        ]
        expected["timeline"]["captionAttributes"]["enabled"] = True
        self.assertEqual(media, expected)
        self.assertEqual(timeline, expected)
        self.assertEqual(doc, before)
        self.assertEqual(
            captions.correct_text(
                doc,
                3,
                dict(schema_version=1, edits=[dict(index=0, expected="First café", text="FIRST")]),
            )["timeline"]["captionAttributes"],
            doc["timeline"]["captionAttributes"],
        )

    def test_trimmed_root_stitch_rejects_timeline_cues_outside_visible_window(self):
        doc = stitched()
        parent(doc).update(start=R, duration=4 * R, mediaStart=2 * R, mediaDuration=4 * R)
        before = copy.deepcopy(doc)
        for begin, end in [(0, 2), (4, 6), (5, 6)]:
            with (
                self.subTest(begin=begin, end=end),
                self.assertRaisesRegex(ValueError, "visible window"),
            ):
                captions.set_cues(
                    doc,
                    3,
                    dict(
                        schema_version=1,
                        clock="timeline",
                        cues=[dict(start=begin, end=end, text="CUE")],
                    ),
                )
            self.assertEqual(doc, before)
        timeline = captions.set_cues(
            doc,
            3,
            dict(schema_version=1, clock="timeline", cues=[dict(start=1, end=5, text="CUE")]),
        )
        media = captions.set_cues(
            doc, 3, dict(schema_version=1, clock="media", cues=[dict(start=2, end=6, text="CUE")])
        )
        self.assertEqual(timeline, media)
        self.assertEqual(doc, before)

    def test_words_only_stitch_and_closed_only_remain_independent_of_recognition(self):
        doc = stitched()
        parent(doc)["parameters"].pop("captions")
        self.assertEqual(captions.map_captions(doc, 3)["closed"], [])
        self.assertEqual(len(captions.map_captions(doc, 3)["words"]), 4)
        result = captions.retime(
            doc, 3, dict(schema_version=1, start=0, duration=8, media_start=0, scalar=1)
        )
        self.assertEqual(result, doc)
        with self.assertRaisesRegex(ValueError, "saved closed captions"):
            captions.map_captions(doc, 3, closed_only=True)
        doc = stitched()
        words(doc)["keyframes"][0]["duration"] = 1
        self.assertTrue(captions.map_captions(doc, 3, closed_only=True)["closed"])
        with self.assertRaises(ValueError):
            captions.map_captions(doc, 3)

    def test_inspection_exposes_parent_closed_cues_and_child_source_uses(self):
        doc = stitched()
        inventory = captions.inventory(doc)
        self.assertEqual(inventory["closed"][0]["clipId"], 3)
        self.assertEqual([u["clipId"] for u in inventory["audioUses"]], [4, 7])
        self.assertEqual([u["audioClipId"] for u in inventory["audioUses"]], [6, 9])
        self.assertTrue(
            all(
                u["containers"] == [dict(clipId=3, ownerType="StitchedMedia")]
                for u in inventory["audioUses"]
            )
        )
        for ident in [4, 6, 7, 9]:
            with self.subTest(ident=ident), self.assertRaisesRegex(ValueError, "stitched parent"):
                captions.map_captions(doc, ident)

    def test_unknown_internal_layouts_and_sources_refuse_atomically(self):
        for mutation in [
            "empty",
            "one",
            "gap",
            "overlap",
            "speed",
            "mirror",
            "source",
            "offset",
            "bounds",
            "kind",
            "origin",
            "client",
            "duplicate",
            "audio-duplicate",
            "child-captions",
            "child-parameters",
        ]:
            doc = stitched()
            p = parent(doc)
            child = p["medias"][1]
            if mutation == "empty":
                p["medias"] = []
            elif mutation == "one":
                p["medias"].pop()
            elif mutation in ["gap", "overlap", "speed", "bounds"]:
                for node in [child, child["video"], child["audio"]]:
                    if mutation == "gap":
                        node["start"] += R
                    elif mutation == "overlap":
                        node["start"] -= R
                    elif mutation == "speed":
                        node["scalar"] = "1/2"
                    else:
                        node["mediaStart"] = 7 * R
            elif mutation == "mirror":
                child["audio"]["start"] += 1
            elif mutation == "source":
                child["audio"]["src"] = 2
            elif mutation == "offset":
                child["audio"]["attributes"]["sourceFileOffset"] = -1
            elif mutation == "kind":
                child["video"]["_type"] = "ScreenVMFile"
            elif mutation == "origin":
                p["minMediaStart"] = R
            elif mutation == "client":
                doc["authoringClientName"]["version"] = "2026.2.5"
            elif mutation == "audio-duplicate":
                child["audio"]["id"] = 6
            elif mutation == "child-captions":
                child["audio"]["parameters"]["captions"] = copy.deepcopy(
                    p["parameters"]["captions"]
                )
            elif mutation == "child-parameters":
                child["audio"]["parameters"] = []
            else:
                child["id"] = 4
            before = copy.deepcopy(doc)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                captions.map_captions(doc, 3)
            self.assertEqual(doc, before)

    def test_bad_parent_clock_parameters_and_animated_retime_refuse_atomically(self):
        for mutation in ["outside", "frame", "effect", "parameters", "negative"]:
            doc = stitched()
            request: dict[str, Any] = dict(
                schema_version=1, start=0, duration=8, media_start=0, scalar=1
            )
            if mutation == "outside":
                request["duration"] = 9
            elif mutation == "frame":
                request["start"] = "1/100"
            elif mutation == "effect":
                parent(doc)["effects"] = [dict(effectName="Fade")]
            elif mutation == "parameters":
                parent(doc)["parameters"] = []
            else:
                request["start"] = -1
            before = copy.deepcopy(doc)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                captions.retime(doc, 3, request)
            self.assertEqual(doc, before)

    def test_cli_parent_map_and_staging_are_json_and_leave_original_bytes_unchanged(self):
        with tempfile.TemporaryDirectory() as folder:
            source, spec, output = [
                Path(folder) / n for n in ["source.json", "spec.json", "candidate.json"]
            ]
            source.write_text(json.dumps(stitched()))
            before = source.read_bytes()
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(captions.main(["map", str(source), "--clip-id", "3"]), 0)
                mapped = json.loads(out.getvalue())["mapping"]
                self.assertEqual(mapped["words"][0]["sourceClipId"], 4)
                self.assertEqual(mapped["displayWords"], mapped["words"])
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(
                    captions.main(["map", str(source), "--clip-id", "3", "--closed-only"]), 0
                )
                mapped = json.loads(out.getvalue())["mapping"]
                self.assertNotIn("displayWords", mapped)
                self.assertNotIn("words", mapped)
            spec.write_text(
                json.dumps(dict(schema_version=1, start=1, duration=4, media_start=0, scalar="1/2"))
            )
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
            self.assertEqual(parent(json.loads(output.read_text()))["scalar"], "1/2")
            with redirect_stderr(io.StringIO()) as err:
                self.assertEqual(captions.main(["map", str(source), "--clip-id", "7"]), 1)
                self.assertIn("stitched parent", json.loads(err.getvalue())["error"])
            self.assertEqual(source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
