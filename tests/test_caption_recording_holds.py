from __future__ import annotations

import copy
import unittest

import captions
from test_captions import closed, point, words
from test_caption_recording_stitches import recording_stitch
from test_caption_stitches import parent

R = 705600000


def held_recording(*, middle=False, group=False):
    doc = recording_stitch(group=group)
    stitch = parent(doc)
    first, last = stitch["medias"]
    hold = dict(
        id=7,
        _type="ScreenIMFile",
        src=1,
        trackNumber=0,
        start=4 * R,
        duration=(2 if middle else 3602) * R,
        mediaStart=4 * R - R // 30,
        mediaDuration=1,
        scalar=1,
        attributes=dict(ident="Frame of speech", opaque=["retain"]),
        parameters=dict(cursorLocation=dict(type="point", keyframes=[point(-1, [1, 2, 0])])),
        animationTracks={},
    )
    stitch["medias"] = [first, hold]
    if middle:
        for node, ident in zip((last, last["video"], last["audio"]), (8, 9, 10)):
            node.update(id=ident, start=6 * R)
        stitch["medias"].append(last)
        stitch.update(duration=10 * R, mediaDuration=10 * R)
    if group:
        container = doc["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]
        container.update(
            duration=stitch["duration"], mediaStart=0, mediaDuration=stitch["duration"]
        )
    return doc


class RecordingHoldCaptionTests(unittest.TestCase):
    def test_trailing_silent_hold_extends_last_word_without_inventing_source_onsets(self):
        doc = held_recording()
        before = copy.deepcopy(doc)
        mapped = captions.map_captions(doc, 3)
        self.assertEqual([r["value"] for r in mapped["words"]], ["First", "useful"])
        useful = mapped["words"][-1]
        self.assertEqual((useful["timelineStartTicks"], useful["timelineEndTicks"]), (2 * R, 8 * R))
        self.assertEqual(
            (useful["sourceTime"], useful["sourceClipId"], useful["audioClipId"]), (2 * R, 4, 6)
        )
        self.assertEqual(mapped["words"], mapped["displayWords"])
        self.assertEqual(words(doc), words(before))
        self.assertEqual(doc, before)

    def test_middle_hold_joins_words_and_preserves_final_moving_projection(self):
        doc = held_recording(middle=True)
        parent(doc).update(start=R, duration=5 * R, scalar="1/2")
        mapped = captions.map_captions(doc, 3)
        nominal = {r["value"]: r for r in mapped["words"]}
        displayed = {r["value"]: r for r in mapped["displayWords"]}
        self.assertEqual(nominal["useful"]["timelineEndTicks"], 4 * R)
        self.assertEqual(nominal["last."]["timelineStartTicks"], 4 * R)
        self.assertEqual(nominal["%GAP"]["timelineStartTicks"], 5 * R)
        self.assertEqual(displayed["%GAP"]["timelineStartTicks"], 9 * R // 2)
        self.assertEqual(
            (nominal["last."]["stitchTime"], nominal["last."]["sourceTime"]), (6 * R, 4 * R)
        )
        self.assertEqual(
            (nominal["last."]["sourceClipId"], nominal["last."]["audioClipId"]), (8, 10)
        )

    def test_group_crop_carries_held_word_while_source_trim_omits_prior_onsets(self):
        doc = held_recording(group=True)
        group = doc["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]
        group.update(start=R, duration=2 * R, mediaStart=6 * R, mediaDuration=2 * R)
        mapped = captions.map_captions(doc, 3)
        self.assertEqual([r["value"] for r in mapped["words"]], ["useful"])
        self.assertEqual(
            (mapped["words"][0]["timelineStartTicks"], mapped["words"][0]["timelineEndTicks"]),
            (R, 3 * R),
        )
        root = held_recording()
        trimmed = captions.retime(
            root, 3, dict(schema_version=1, start=0, duration=2, media_start=6, scalar=1)
        )
        self.assertEqual(captions.map_captions(trimmed, 3)["words"], [])
        self.assertEqual(captions.map_captions(trimmed, 3)["displayWords"], [])

    def test_parent_retime_preserves_frozen_frame_cursor_and_every_source_field(self):
        doc = held_recording()
        before = copy.deepcopy(doc)
        result = captions.retime(
            doc, 3, dict(schema_version=1, start=1, duration=5, media_start=0, scalar="1/2")
        )
        expected = copy.deepcopy(doc)
        parent(expected).update(
            start=R, duration=5 * R, mediaStart=0, mediaDuration=10 * R, scalar="1/2"
        )
        self.assertEqual(result, expected)
        self.assertEqual(parent(result)["medias"], parent(before)["medias"])
        self.assertEqual(result["sourceBin"], before["sourceBin"])
        self.assertEqual(
            captions.map_captions(result, 3)["words"],
            captions.map_captions(result, 3)["displayWords"],
        )
        self.assertEqual(doc, before)

    def test_parent_cues_can_be_authored_inside_silent_hold(self):
        doc = held_recording()
        before = copy.deepcopy(doc)
        result = captions.set_cues(
            doc,
            3,
            dict(
                schema_version=1, clock="timeline", cues=[dict(start=5, end=7, text="HELD PICTURE")]
            ),
        )
        self.assertEqual(
            [r["value"] for r in captions.map_captions(result, 3)["closed"]],
            ["", "HELD PICTURE", ""],
        )
        self.assertEqual(parent(result)["medias"], parent(doc)["medias"])
        self.assertEqual(result["sourceBin"], doc["sourceBin"])
        self.assertEqual(doc, before)
        for ident in (4, 6, 7):
            with self.subTest(ident=ident), self.assertRaises(ValueError):
                captions.map_captions(doc, ident)

    def test_recognized_holds_need_no_closed_parameter(self):
        doc = held_recording(middle=True, group=True)
        parent(doc)["parameters"].pop("captions")
        mapped = captions.map_captions(doc, 3)
        self.assertEqual(mapped["closed"], [])
        self.assertEqual(
            [r["value"] for r in mapped["words"]], ["First", "useful", "last.", "%GAP"]
        )

    def test_malformed_or_unrelated_frozen_owners_refuse_without_mutation(self):
        def hold(doc):
            return parent(doc)["medias"][1]

        mutations = (
            lambda d: hold(d).update(id=6),
            lambda d: hold(d).update(id=True),
            lambda d: hold(d).update(src=2),
            lambda d: hold(d).update(trackNumber=1),
            lambda d: hold(d).update(start=3 * R),
            lambda d: hold(d).update(duration=0),
            lambda d: hold(d).update(mediaDuration=2),
            lambda d: hold(d).update(scalar="1/2"),
            lambda d: hold(d).update(mediaStart=8 * R),
            lambda d: hold(d).update(mediaStart=-1),
            lambda d: hold(d)["parameters"].update(captions=closed(recording_stitch())),
            lambda d: parent(d)["medias"][0]["video"].update(_type="VMFile"),
            lambda d: parent(d)["medias"].reverse(),
        )
        for mutate in mutations:
            doc = held_recording()
            mutate(doc)
            before = copy.deepcopy(doc)
            with self.subTest(mutation=mutate), self.assertRaises(ValueError):
                captions.map_captions(doc, 3)
            self.assertEqual(doc, before)


if __name__ == "__main__":
    unittest.main()
