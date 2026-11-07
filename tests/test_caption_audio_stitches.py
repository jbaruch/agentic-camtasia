from __future__ import annotations

import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from test_caption_stitches import stitched, parent, R
from test_caption_groups import row
from test_captions import point, value
import captions


def audio_stitched(*, skip=False, group=False):
    doc = stitched(skip=skip, group=group)
    owner = parent(doc)
    children = []
    for ident, child in enumerate(owner["medias"], 4):
        audio = child["audio"]
        audio.update(id=ident, trackNumber=0, metadata=dict(opaque=["native-audio"]))
        children.append(audio)
    owner["medias"] = children
    source = doc["sourceBin"][0]
    source["sourceTracks"] = [source["sourceTracks"][1]]
    return doc


def audio_row(index, text, source_seconds, begin, end, child, stitch_seconds):
    return dict(
        row(index, text, source_seconds, begin, end),
        stitchTime=int(stitch_seconds * R),
        sourceClipId=child,
        audioClipId=child,
        sourceId=1,
        sourceTrack=0,
    )


class AudioStitchedCaptionTests(unittest.TestCase):
    def test_audio_parent_maps_both_clocks_with_physical_source_provenance(self):
        doc = audio_stitched()
        before = copy.deepcopy(doc)
        mapped = captions.map_captions(doc, 3)
        expected = [
            audio_row(0, "First", 0.02, "1/50", "2", 4, 0.02),
            audio_row(1, "useful", 2, "2", "4", 4, 2),
            audio_row(2, "last.", 4, "4", "6", 5, 4),
            audio_row(3, "%GAP", 6, "6", "8", 5, 6),
        ]
        self.assertEqual(mapped["words"], expected)
        self.assertEqual(mapped["displayWords"], expected)
        self.assertEqual(mapped["closed"][1]["value"], "Second → text")
        self.assertEqual(doc, before)

    def test_audio_source_skip_forms_holds_after_joining_retained_onsets(self):
        doc = audio_stitched(skip=True)
        expected = [
            audio_row(0, "First", 0.02, "1/50", "2", 4, 0.02),
            audio_row(1, "useful", 2, "2", "4", 4, 2),
            audio_row(3, "%GAP", 6, "4", "6", 5, 4),
        ]
        self.assertEqual(captions.map_captions(doc, 3)["words"], expected)
        self.assertEqual(captions.map_captions(doc, 3)["displayWords"], expected)

    def test_audio_parent_speed_keeps_nominal_words_distinct_from_display_projection(self):
        doc = audio_stitched()
        parent(doc).update(start=R, duration=4 * R, scalar="1/2")
        mapped = captions.map_captions(doc, 3)
        self.assertEqual(mapped["words"][-1], audio_row(3, "%GAP", 6, "4", "5", 5, 6))
        self.assertEqual(mapped["displayWords"][-1], audio_row(3, "%GAP", 6, "7/2", "5", 5, 6))
        self.assertEqual(mapped["words"][:2], mapped["displayWords"][:2])

    def test_audio_group_crop_carries_active_hold_and_parent_speed_composes_once(self):
        doc = audio_stitched(group=True)
        mapped = captions.map_captions(doc, 3)
        self.assertEqual(mapped["ancestors"], [100])
        self.assertEqual(mapped["words"][0], audio_row(0, "First", 0.02, "1", "2", 4, 0.02))
        group = doc["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]
        group.update(mediaStart=0, duration=4 * R, scalar="1/2")
        mapped = captions.map_captions(doc, 3)
        self.assertEqual(mapped["words"], mapped["displayWords"])
        self.assertEqual(mapped["words"][-1], audio_row(3, "%GAP", 6, "4", "5", 5, 6))

    def test_audio_parent_retime_preserves_children_and_accepts_exact_subframe_cuts(self):
        doc = audio_stitched()
        before = copy.deepcopy(doc)
        spec = dict(
            schema_version=1, start="1/100", duration="799/100", media_start="1/100", scalar=1
        )
        expected = copy.deepcopy(doc)
        parent(expected).update(
            start=R // 100,
            duration=799 * R // 100,
            mediaStart=R // 100,
            mediaDuration=799 * R // 100,
        )
        result = captions.retime(doc, 3, spec)
        self.assertEqual(result, expected)
        self.assertEqual(captions.retime(result, 3, spec), result)
        self.assertEqual(doc, before)

    def test_group_audio_retime_requires_explicit_parent_clock_and_retains_ancestors(self):
        doc = audio_stitched(group=True)
        spec = dict(schema_version=1, start="1/100", duration=4, media_start=0, scalar=2)
        with self.assertRaisesRegex(ValueError, "clock parent"):
            captions.retime(doc, 3, spec)
        expected = copy.deepcopy(doc)
        parent(expected).update(
            start=R // 100, duration=4 * R, mediaStart=0, mediaDuration=2 * R, scalar=2
        )
        self.assertEqual(captions.retime(doc, 3, dict(spec, clock="parent")), expected)

    def test_audio_parent_cue_authoring_preserves_all_children_and_rejects_cropped_timeline_cues(
        self,
    ):
        doc = audio_stitched()
        parent(doc).update(start=R, duration=4 * R, mediaStart=2 * R, mediaDuration=4 * R)
        before = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        parent(expected)["parameters"]["captions"]["keyframes"] = [
            point(0, value("")),
            point(2, value("CUE")),
            point(6, value("")),
        ]
        expected["timeline"]["captionAttributes"]["enabled"] = True
        result = captions.set_cues(
            doc,
            3,
            dict(schema_version=1, clock="timeline", cues=[dict(start=1, end=5, text="CUE")]),
        )
        self.assertEqual(result, expected)
        with self.assertRaisesRegex(ValueError, "visible window"):
            captions.set_cues(
                doc,
                3,
                dict(
                    schema_version=1, clock="timeline", cues=[dict(start=5, end=6, text="HIDDEN")]
                ),
            )
        self.assertEqual(doc, before)

    def test_audio_recognition_and_closed_only_remain_independent(self):
        doc = audio_stitched(group=True)
        parent(doc)["parameters"].pop("captions")
        before = copy.deepcopy(doc)
        self.assertEqual(len(captions.map_captions(doc, 3)["words"]), 4)
        with self.assertRaises(ValueError):
            captions.map_captions(doc, 3, closed_only=True)
        spec = dict(
            schema_version=1, start=0, duration=4, media_start=0, scalar="1/2", clock="parent"
        )
        expected = copy.deepcopy(doc)
        parent(expected).update(
            start=0, duration=4 * R, mediaStart=0, mediaDuration=8 * R, scalar="1/2"
        )
        self.assertEqual(captions.retime(doc, 3, spec), expected)
        self.assertEqual(doc, before)
        closed = audio_stitched()
        stream = closed["sourceBin"][0]["sourceTracks"][0]
        stream["transcriptionSet"] = False
        stream["parameters"].pop("transcription")
        mapped = captions.map_captions(closed, 3, closed_only=True)
        self.assertTrue(mapped["closed"])
        self.assertNotIn("displayWords", mapped)
        self.assertNotIn("words", mapped)

    def test_audio_inspection_exposes_parent_container_and_child_selection_refuses(self):
        doc = audio_stitched()
        inspection = captions.inventory(doc)
        self.assertEqual(inspection["closed"][0]["clipId"], 3)
        uses = inspection["audioUses"]
        self.assertEqual([use["clipId"] for use in uses], [4, 5])
        self.assertEqual([use["audioClipId"] for use in uses], [4, 5])
        self.assertTrue(
            all(use["containers"] == [dict(clipId=3, ownerType="StitchedMedia")] for use in uses)
        )
        with self.assertRaisesRegex(ValueError, "stitched parent"):
            captions.map_captions(doc, 4)

    def test_mixed_sources_recordings_holds_and_bad_internal_clocks_refuse_atomically(self):
        for mutation in [
            "mixed",
            "source",
            "recording",
            "held",
            "gap",
            "missing-duration",
            "consumption",
            "offset",
            "child-cues",
        ]:
            doc = audio_stitched()
            children = parent(doc)["medias"]
            if mutation == "mixed":
                children[1] = stitched()["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][
                    0
                ]["medias"][0]["medias"][1]
            elif mutation == "source":
                children[1]["src"] = 99
            elif mutation == "recording":
                children[0]["_type"] = "ScreenAMFile"
            elif mutation == "held":
                children[0]["scalar"] = 2
            elif mutation == "gap":
                children[1]["start"] += 1
            elif mutation == "missing-duration":
                children[1].pop("mediaDuration")
            elif mutation == "consumption":
                children[1]["mediaDuration"] = R
            elif mutation == "offset":
                children[0]["attributes"]["sourceFileOffset"] = 1
            else:
                children[0]["parameters"]["captions"] = copy.deepcopy(
                    parent(doc)["parameters"]["captions"]
                )
            before = copy.deepcopy(doc)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                captions.map_captions(doc, 3)
            self.assertEqual(doc, before)

    def test_audio_cli_maps_and_stages_without_changing_original_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            source, spec, output = [
                Path(directory) / name for name in ["source.json", "spec.json", "candidate.json"]
            ]
            source.write_text(json.dumps(audio_stitched()))
            before = source.read_bytes()
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(captions.main(["map", str(source), "--clip-id", "3"]), 0)
                mapped = json.loads(out.getvalue())["mapping"]
                self.assertEqual(mapped["words"], mapped["displayWords"])
                self.assertEqual(mapped["words"][-1]["audioClipId"], 5)
            spec.write_text(
                json.dumps(
                    dict(
                        schema_version=1,
                        start="1/100",
                        duration="799/100",
                        media_start="1/100",
                        scalar=1,
                    )
                )
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
            self.assertEqual(parent(json.loads(output.read_text()))["start"], R // 100)
            with redirect_stderr(io.StringIO()) as err:
                self.assertEqual(captions.main(["map", str(source), "--clip-id", "4"]), 1)
                self.assertIn("stitched parent", json.loads(err.getvalue())["error"])
            self.assertEqual(source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
