from __future__ import annotations

import copy
import unittest

import captions
from test_captions import point, words
from test_caption_stitches import parent, stitched

R = 705600000


def recording_stitch(*, group=False, trailing=False, skip=False):
    doc = stitched(group=group, skip=skip)
    for child in parent(doc)["medias"]:
        child["video"]["_type"] = "ScreenVMFile"
        child["video"]["parameters"].update(cursorTrackLevel=10000, opaqueCursor=["retain"])
        child["audio"]["channelNumber"] = "0,1"
    for stream in doc["sourceBin"][0]["sourceTracks"]:
        stream.update(
            editRate=44100, range=[0, (12 if trailing else 8) * 44100], metaData="speech.trec;"
        )
    if trailing:
        child = parent(doc)["medias"][-1]
        for node in (child, child["video"], child["audio"]):
            node.update(
                duration=12 * R - child["mediaStart"],
                mediaDuration=12 * R - child["mediaStart"],
            )
        words(doc)["keyframes"].append(point(9, "Later"))
    return doc


class RecordingStitchTests(unittest.TestCase):
    def test_recognized_recording_stitches_do_not_require_closed_cues(self):
        doc = recording_stitch(group=True, trailing=True)
        parent(doc)["parameters"].pop("captions")
        before = copy.deepcopy(doc)
        mapped = captions.map_captions(doc, 3)
        self.assertEqual(mapped["closed"], [])
        self.assertTrue(mapped["words"])
        result = captions.retime(
            doc,
            3,
            dict(
                schema_version=1, clock="parent", start=0, duration=4, media_start=0, scalar="1/2"
            ),
        )
        self.assertEqual(parent(result)["medias"], parent(doc)["medias"])
        self.assertEqual(result["sourceBin"], doc["sourceBin"])
        self.assertNotIn("captions", parent(result)["parameters"])
        self.assertEqual(doc, before)

    def test_source_skip_keeps_a_joined_word_hold_and_original_recording_onsets(self):
        doc = recording_stitch(skip=True)
        before = copy.deepcopy(doc)
        mapped = captions.map_captions(doc, 3)
        useful = next(row for row in mapped["words"] if row["value"] == "useful")
        self.assertEqual(
            (useful["sourceTime"], useful["timelineStartTicks"], useful["timelineEndTicks"]),
            (2 * R, 2 * R, 4 * R),
        )
        self.assertEqual((useful["sourceClipId"], useful["audioClipId"]), (4, 6))
        self.assertNotIn("last.", [row["value"] for row in mapped["words"]])
        self.assertEqual(doc, before)

    def test_root_and_group_mappings_keep_source_and_child_provenance(self):
        for group in (False, True):
            with self.subTest(group=group):
                doc = recording_stitch(group=group)
                before = copy.deepcopy(doc)
                self.assertEqual(
                    captions.map_captions(doc, 3), captions.map_captions(stitched(group=group), 3)
                )
                final = captions.map_captions(doc, 3)["words"][-1]
                self.assertEqual(
                    (final["sourceClipId"], final["audioClipId"], final["sourceTrack"]), (7, 9, 1)
                )
                self.assertEqual(doc, before)

    def test_native_trailing_child_can_exceed_the_visible_parent(self):
        doc = recording_stitch(trailing=True)
        before = copy.deepcopy(doc)
        mapped = captions.map_captions(doc, 3)
        self.assertNotIn("Later", [r["value"] for r in mapped["words"]])
        fast = captions.retime(
            doc, 3, dict(schema_version=1, start=1, duration=4, media_start=0, scalar="1/2")
        )
        mapped = captions.map_captions(fast, 3)
        self.assertNotIn("Later", [r["value"] for r in mapped["words"]])
        later = next(r for r in mapped["displayWords"] if r["value"] == "Later")
        self.assertEqual(
            (later["sourceTime"], later["stitchTime"], later["timelineStartTicks"]),
            (9 * R, 9 * R, 17 * R // 4),
        )
        self.assertEqual(parent(fast)["medias"], parent(doc)["medias"])
        self.assertEqual(doc, before)

    def test_projected_short_tail_keeps_exact_ticks_between_video_frames(self):
        doc = recording_stitch(trailing=True)
        words(doc)["keyframes"].append(
            dict(time=8423629200, endTime=8423629200, duration=0, value="follows")
        )
        fast = captions.retime(
            doc,
            3,
            dict(schema_version=1, start=1, duration=4, media_start=0, scalar="1/2"),
        )
        mapped = captions.map_captions(fast, 3)
        tail = mapped["displayWords"][-1]
        self.assertEqual(tail["value"], "follows")
        self.assertEqual(tail["timelineStartTicks"], 3517107300)
        self.assertEqual(tail["timelineEndTicks"], 5 * R)
        self.assertEqual(tail["sourceTime"], 8423629200)
        self.assertNotIn("follows", [row["value"] for row in mapped["words"]])
        self.assertEqual(words(fast), words(doc))

    def test_retime_changes_only_parent_clocks_and_checks_real_internal_capacity(self):
        for group in (False, True):
            with self.subTest(group=group):
                doc = recording_stitch(group=group, trailing=True)
                spec = dict(schema_version=1, start=0, duration=5, media_start=1, scalar="1/2")
                if group:
                    spec["clock"] = "parent"
                result = captions.retime(doc, 3, spec)
                expected = copy.deepcopy(doc)
                parent(expected).update(
                    start=0, duration=5 * R, mediaStart=R, mediaDuration=10 * R, scalar="1/2"
                )
                self.assertEqual(result, expected)
                self.assertEqual(words(result), words(doc))
        with self.assertRaises(ValueError):
            captions.retime(
                recording_stitch(trailing=True),
                3,
                dict(schema_version=1, start=0, duration=13, media_start=0, scalar=1),
            )

    def test_cue_authoring_selects_parent_and_preserves_recording_children(self):
        doc = recording_stitch()
        before = copy.deepcopy(doc)
        result = captions.set_cues(
            doc,
            3,
            dict(
                schema_version=1,
                clock="timeline",
                cues=[dict(start=1, end=3, text="RECORDING EDIT")],
            ),
        )
        self.assertEqual(parent(result)["medias"], parent(doc)["medias"])
        self.assertEqual(result["sourceBin"], doc["sourceBin"])
        self.assertEqual(
            [r["value"] for r in captions.map_captions(result, 3)["closed"]],
            ["", "RECORDING EDIT", ""],
        )
        for child_id in (4, 6, 7, 9):
            with self.subTest(child_id=child_id), self.assertRaises(ValueError):
                captions.map_captions(doc, child_id)
        self.assertEqual(doc, before)

    def test_mixed_frozen_mirrored_and_source_bound_failures_refuse(self):
        mutations = (
            lambda d: parent(d)["medias"][1]["audio"].update(_type="Caption"),
            lambda d: parent(d)["medias"][1]["video"].update(_type="VMFile"),
            lambda d: parent(d)["medias"][1]["video"].update(_type="ScreenIMFile"),
            lambda d: parent(d)["medias"][1]["video"].update(src=2),
            lambda d: parent(d)["medias"][1]["video"].update(trackNumber=1),
            lambda d: parent(d)["medias"][1]["audio"].update(start=R),
            lambda d: d["sourceBin"][0]["sourceTracks"][0].update(range=[0, 7 * 44100]),
            lambda d: parent(d)["medias"][1]["audio"]["attributes"].update(sourceFileOffset=-1),
        )
        for mutate in mutations:
            doc = recording_stitch()
            mutate(doc)
            before = copy.deepcopy(doc)
            with self.assertRaises(ValueError):
                captions.map_captions(doc, 3)
            self.assertEqual(doc, before)


if __name__ == "__main__":
    unittest.main()
