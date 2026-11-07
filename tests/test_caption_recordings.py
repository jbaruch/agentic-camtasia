from __future__ import annotations

import copy
from fractions import Fraction
import unittest

import captions
from test_captions import audio, fixture, root, words
from test_caption_groups import leaf, one_group

R = 705600000


def recording(grouped=False):
    doc = one_group(inpoint=0, duration=8) if grouped else fixture()
    owner = leaf(doc) if grouped else root(doc)
    owner["video"]["_type"] = "ScreenVMFile"
    owner["video"]["parameters"]["cursorTrackLevel"] = 10000
    owner["audio"]["attributes"].update(sourceFileOffset=0, channelNumber="0,1")
    for stream in doc["sourceBin"][0]["sourceTracks"]:
        stream.update(editRate=44100, range=[0, 8 * 44100], metaData="capture.trec;")
    return doc


class RecordingCaptionTests(unittest.TestCase):
    def test_recorded_word_points_keep_caption_ticks_with_a_44100_hz_source(self):
        doc = recording()
        audio(doc)["parameters"].pop("captions")
        words(doc)["keyframes"] = [
            dict(time=0, endTime=0, duration=0, value="%GAP"),
            dict(time=1014123600, endTime=1014123600, duration=0, value="We"),
            dict(time=1084683600, endTime=1084683600, duration=0, value="build"),
        ]
        before = copy.deepcopy(doc)
        mapped = captions.map_captions(doc, 5)
        self.assertEqual(mapped["closed"], [])
        self.assertEqual(mapped["words"][0]["value"], "%GAP")
        self.assertEqual(mapped["words"][1]["timelineStartTicks"], 1014123600)
        self.assertEqual(mapped["words"][1]["timelineEndTicks"], 1084683600)
        retimed = captions.retime(
            doc, 3, dict(schema_version=1, start=1, duration=4, media_start=0, scalar="1/2")
        )
        self.assertEqual(words(retimed), words(doc))
        self.assertEqual(
            captions.map_captions(retimed, 3)["words"][1]["timelineStartTicks"],
            R + 507061800,
        )
        self.assertEqual(doc, before)

    def test_maps_root_and_group_recordings_without_changing_source_words(self):
        for grouped in (False, True):
            with self.subTest(grouped=grouped):
                doc = recording(grouped)
                ordinary = copy.deepcopy(doc)
                (leaf(ordinary) if grouped else root(ordinary))["video"]["_type"] = "VMFile"
                before = copy.deepcopy(doc)
                self.assertEqual(captions.map_captions(doc, 3), captions.map_captions(ordinary, 3))
                self.assertEqual(captions.map_captions(doc, 5), captions.map_captions(doc, 3))
                self.assertEqual(doc, before)

    def test_retime_changes_only_all_three_clocks_and_preserves_recording_payload(self):
        for grouped in (False, True):
            with self.subTest(grouped=grouped):
                doc = recording(grouped)
                before = copy.deepcopy(doc)
                spec = dict(schema_version=1, start=1, duration=3, media_start=2, scalar="1/2")
                if grouped:
                    spec["clock"] = "parent"
                result = captions.retime(doc, 5, spec)
                expected = copy.deepcopy(doc)
                owner = leaf(expected) if grouped else root(expected)
                for node in (owner, owner["video"], owner["audio"]):
                    node.update(
                        start=R, duration=3 * R, mediaStart=2 * R, mediaDuration=6 * R, scalar="1/2"
                    )
                self.assertEqual(result, expected)
                self.assertEqual(words(result), words(doc))
                self.assertEqual(doc, before)
                ordinary = copy.deepcopy(result)
                (leaf(ordinary) if grouped else root(ordinary))["video"]["_type"] = "VMFile"
                self.assertEqual(
                    captions.map_captions(result, 3), captions.map_captions(ordinary, 3)
                )

    def test_cues_and_text_edits_keep_recording_and_transcription(self):
        doc = recording()
        result = captions.set_cues(
            doc,
            3,
            dict(
                schema_version=1,
                clock="timeline",
                cues=[dict(start=1, end=3, text="Recorded speech")],
            ),
        )
        expected = copy.deepcopy(doc)
        expected["timeline"]["captionAttributes"]["enabled"] = True
        audio(expected)["parameters"]["captions"] = copy.deepcopy(
            audio(result)["parameters"]["captions"]
        )
        self.assertEqual(result, expected)
        self.assertEqual(
            [row["value"] for row in captions.map_captions(result, 3)["closed"]],
            ["", "Recorded speech", ""],
        )
        corrected = captions.correct_words(
            doc, 1, 1, dict(schema_version=1, edits=[dict(index=0, expected="First", text="FIRST")])
        )
        self.assertEqual(words(corrected)["keyframes"][0]["value"], "FIRST")
        self.assertEqual(root(corrected), root(doc))

    def test_requires_exact_build_shared_source_and_correct_stream_kinds(self):
        for field, value in (("version", "9.0"), ("authoringClientName", {})):
            doc = recording()
            doc[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                captions.map_captions(doc, 3)
        for mutate in (
            lambda d: root(d)["video"].update(src=2),
            lambda d: root(d)["video"].update(trackNumber=1),
            lambda d: audio(d).update(trackNumber=0),
            lambda d: root(d)["video"].update(duration=7 * R),
            lambda d: audio(d).update(mediaStart=R),
            lambda d: audio(d)["attributes"].update(sourceFileOffset=1),
        ):
            doc = recording()
            mutate(doc)
            with self.assertRaises(ValueError):
                captions.map_captions(doc, 3)

    def test_retains_hold_refusal_and_recording_video_bounds_and_frame_grid(self):
        for kind in ("ScreenVMFileFrozen", "StitchedMedia", "VMFileFrozen"):
            doc = recording()
            root(doc)["video"]["_type"] = kind
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                captions.map_captions(doc, 3)
        for start, duration, inpoint in ((0, 5, 4), (Fraction(1, 7), 3, 0)):
            doc = recording()
            with self.assertRaises(ValueError):
                captions.retime(
                    doc,
                    3,
                    dict(
                        schema_version=1,
                        start=str(start),
                        duration=duration,
                        media_start=inpoint,
                        scalar=1,
                    ),
                )
        doc = recording()
        doc["sourceBin"][0]["sourceTracks"][0]["range"][1] = 4 * 44100
        with self.assertRaises(ValueError):
            captions.retime(
                doc, 3, dict(schema_version=1, start=0, duration=5, media_start=0, scalar=1)
            )


if __name__ == "__main__":
    unittest.main()
