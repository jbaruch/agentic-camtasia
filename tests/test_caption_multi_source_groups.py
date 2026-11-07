from __future__ import annotations

import copy
import unittest

import captions
from test_caption_groups import one_group
from test_caption_recording_stitches import recording_stitch
from test_caption_stitches import parent
from test_captions import point, value

R = 705600000


def composition():
    doc = one_group()
    group = doc["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]
    first = group["tracks"][0]["medias"][0]
    first["video"]["_type"] = "ScreenVMFile"
    for node in (first, first["video"], first["audio"]):
        node.update(start=0, duration=4 * R, mediaStart=0, mediaDuration=4 * R, scalar=1)
    first["audio"]["parameters"]["captions"]["keyframes"] = [
        point(0, value("FIRST")),
        point(2, value("VOICE")),
        point(4, value("")),
    ]
    for stream in doc["sourceBin"][0]["sourceTracks"]:
        stream.update(editRate=44100, range=[0, 8 * 44100])
    second_source = copy.deepcopy(doc["sourceBin"][0])
    second_source.update(id=2, src="second.wav", rect=[0, 0, 0, 0])
    second_source["sourceTracks"] = [copy.deepcopy(second_source["sourceTracks"][1])]
    stream = second_source["sourceTracks"][0]
    stream.update(editRate=32000, range=[0, 8 * 32000])
    stream["parameters"]["transcription"]["keyframes"] = [
        dict(time=R + 1, endTime=R + 1, duration=0, value="OTHER"),
        point(3, "WORDS"),
        dict(time=39 * R // 10 + 1, endTime=39 * R // 10 + 1, duration=0, value="%GAP"),
    ]
    doc["sourceBin"].append(second_source)
    second = copy.deepcopy(first["audio"])
    second.update(id=7, src=2, trackNumber=0, start=4 * R)
    second["parameters"]["captions"]["keyframes"] = [
        point(0, value("SECOND")),
        point(2, value("NEXT")),
        point(4, value("")),
    ]
    group["tracks"][0]["medias"].append(second)
    return doc


def group_of(doc):
    return doc["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]


def second_of(doc):
    return group_of(doc)["tracks"][0]["medias"][1]


class MultiSourceGroupCaptionTests(unittest.TestCase):
    def test_inventory_and_maps_bind_each_logical_owner_to_its_actual_source_stream(self):
        doc = composition()
        before = copy.deepcopy(doc)
        uses = captions.inventory(doc)["audioUses"]
        self.assertEqual(
            [(r["clipId"], r["audioClipId"], r["sourceId"], r["sourceTrack"]) for r in uses],
            [(3, 5, 1, 1), (7, 7, 2, 0)],
        )
        first = captions.map_captions(doc, 3)
        second = captions.map_captions(doc, 7)
        self.assertEqual([r["value"] for r in first["words"]], ["First", "useful"])
        self.assertEqual([r["value"] for r in second["words"]], ["OTHER", "WORDS", "%GAP"])
        self.assertEqual(second["words"][0]["sourceTime"], R + 1)
        self.assertEqual(second["words"][0]["timelineStartTicks"], 6 * R + 1)
        self.assertEqual([r["value"] for r in second["closed"]], ["SECOND", "NEXT"])
        self.assertEqual(doc, before)

    def test_common_speed_and_crop_preserve_independent_source_onsets(self):
        doc = composition()
        group_of(doc).update(duration=4 * R, mediaDuration=8 * R, scalar="1/2")
        second = captions.map_captions(doc, 7)
        self.assertEqual(second["words"][0]["timelineStartTicks"], "4939200001/2")
        self.assertEqual(second["closed"][0]["timelineStartTicks"], 3 * R)
        cropped = composition()
        group_of(cropped).update(duration=2 * R, mediaStart=6 * R, mediaDuration=2 * R)
        self.assertEqual(captions.map_captions(cropped, 3)["words"], [])
        held = captions.map_captions(cropped, 7)["words"][0]
        self.assertEqual(
            (
                held["value"],
                held["sourceTime"],
                held["timelineStartTicks"],
                held["timelineEndTicks"],
            ),
            ("OTHER", R + 1, R, 2 * R),
        )

    def test_occurrence_correction_changes_only_the_selected_source_value(self):
        doc = composition()
        before = copy.deepcopy(doc)
        result = captions.correct_words(
            doc,
            2,
            0,
            dict(schema_version=1, edits=[dict(index=0, expected="OTHER", text="SECOND")]),
        )
        expected = copy.deepcopy(doc)
        expected["sourceBin"][1]["sourceTracks"][0]["parameters"]["transcription"]["keyframes"][0][
            "value"
        ] = "SECOND"
        self.assertEqual(result, expected)
        self.assertEqual(captions.map_captions(result, 3), captions.map_captions(doc, 3))
        self.assertEqual(doc, before)

    def test_global_cue_authoring_inverts_common_group_speed_for_only_its_owner(self):
        doc = composition()
        group_of(doc).update(duration=4 * R, mediaDuration=8 * R, scalar="1/2")
        before = copy.deepcopy(doc)
        result = captions.set_cues(
            doc,
            7,
            dict(
                schema_version=1,
                clock="timeline",
                cues=[dict(start="13/4", end="15/4", text="SOURCE TWO")],
            ),
        )
        frames = second_of(result)["parameters"]["captions"]["keyframes"]
        self.assertEqual(
            [(f["time"], f["value"]["text"]) for f in frames],
            [(0, ""), (R // 2, "SOURCE TWO"), (3 * R // 2, "")],
        )
        self.assertEqual(
            group_of(result)["tracks"][0]["medias"][0], group_of(doc)["tracks"][0]["medias"][0]
        )
        self.assertEqual(result["sourceBin"], doc["sourceBin"])
        self.assertEqual(doc, before)

    def test_selected_source_trim_omits_earlier_onsets_and_preserves_the_other_clip(self):
        doc = composition()
        before = copy.deepcopy(doc)
        result = captions.retime(
            doc,
            7,
            dict(
                schema_version=1,
                clock="parent",
                start=4,
                duration="5/2",
                media_start="3/2",
                scalar=1,
            ),
        )
        mapped = captions.map_captions(result, 7)
        self.assertEqual([r["value"] for r in mapped["words"]], ["WORDS", "%GAP"])
        self.assertEqual(mapped["words"][0]["timelineStartTicks"], 13 * R // 2)
        self.assertEqual(
            group_of(result)["tracks"][0]["medias"][0], group_of(doc)["tracks"][0]["medias"][0]
        )
        self.assertEqual(result["sourceBin"], doc["sourceBin"])
        self.assertEqual(doc, before)

    def test_wrong_stream_or_stale_expected_word_refuses_without_mutation(self):
        doc = composition()
        before = copy.deepcopy(doc)
        for source, track, expected in ((2, 1, "OTHER"), (2, 0, "stale"), (1, 0, "OTHER")):
            with self.subTest(source=source, track=track), self.assertRaises(ValueError):
                captions.correct_words(
                    doc,
                    source,
                    track,
                    dict(schema_version=1, edits=[dict(index=0, expected=expected, text="NEW")]),
                )
        self.assertEqual(doc, before)

    def test_mixed_source_stitch_refusal_routes_to_native_group_workflow(self):
        doc = recording_stitch()
        source = copy.deepcopy(doc["sourceBin"][0])
        source["id"] = 2
        doc["sourceBin"].append(source)
        for node in (parent(doc)["medias"][1]["video"], parent(doc)["medias"][1]["audio"]):
            node["src"] = 2
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "use a Group"):
            captions.map_captions(doc, 3)
        self.assertEqual(doc, before)


if __name__ == "__main__":
    unittest.main()
