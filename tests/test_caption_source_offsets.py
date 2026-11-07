from __future__ import annotations

import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
from fractions import Fraction
import unittest

import captions
import project
from test_caption_groups import leaf, one_group
from test_caption_recordings import recording
from test_caption_stitches import parent, stitched
from test_captions import audio, fixture, root, words

R = 705600000


def with_offset(doc, samples=48000):
    for stream in doc["sourceBin"][0]["sourceTracks"]:
        if stream["type"] == 2:
            stream["sampleRate"] = stream["editRate"]
    owner = (
        leaf(doc) if any(n.get("_type") == "Group" for _, n in project.objects(doc)) else root(doc)
    )
    physical = owner["audio"] if owner["_type"] == "UnifiedMedia" else owner
    physical.setdefault("attributes", {})["sourceFileOffset"] = samples
    for n in (
        (owner, owner["video"], owner["audio"]) if owner["_type"] == "UnifiedMedia" else (owner,)
    ):
        n.update(duration=4 * R, mediaDuration=4 * R)
    return doc


class CaptionSourceOffsetTests(unittest.TestCase):
    def test_offsets_report_physical_samples_without_shifting_caption_or_word_clocks(self):
        for make, samples in [
            (fixture, 48000),
            (lambda: fixture("audio"), 1),
            (one_group, 48000),
            (recording, 44100),
            (lambda: recording(True), 44100),
        ]:
            with self.subTest(make=make, samples=samples):
                doc = with_offset(make(), samples)
                before = copy.deepcopy(doc)
                use = captions.inventory(doc)["audioUses"][0]
                self.assertEqual(use["sourceFileOffset"], samples)
                mapped = captions.map_captions(doc, use["clipId"])
                offsets = mapped.pop("audioFileOffsets")
                control = copy.deepcopy(doc)
                captions.selected(control, use["audioClipId"])[1]["attributes"][
                    "sourceFileOffset"
                ] = 0
                self.assertEqual(mapped, captions.map_captions(control, use["clipId"]))
                rate = doc["sourceBin"][0]["sourceTracks"][1]["sampleRate"]
                self.assertEqual(
                    offsets,
                    [
                        dict(
                            audioClipId=use["audioClipId"],
                            sourceId=1,
                            sourceTrack=1,
                            samples=samples,
                            sampleRate=rate,
                            ticks=captions.exact(Fraction(samples * R, rate)),
                        )
                    ],
                )
                self.assertEqual(doc, before)

    def test_audio_offset_uses_sample_rate_independently_of_source_range_edit_rate(self):
        doc = with_offset(fixture(), 32000)
        stream = doc["sourceBin"][0]["sourceTracks"][1]
        stream["sampleRate"] = 32000
        self.assertEqual(captions.map_captions(doc, 3)["audioFileOffsets"][0]["ticks"], R)
        self.assertEqual(captions.capacity(doc, audio(doc)), 7 * R)

    def test_offset_physical_bounds_constrain_mapping_and_retiming(self):
        doc = with_offset(fixture())
        before = copy.deepcopy(doc)
        for duration, trim in [(8, 0), (4, 4)]:
            with (
                self.subTest(duration=duration),
                self.assertRaisesRegex(ValueError, "source bounds"),
            ):
                captions.retime(
                    doc,
                    3,
                    dict(schema_version=1, start=0, duration=duration, media_start=trim, scalar=1),
                )
        audio(doc)["duration"] = 8 * R
        root(doc)["duration"] = 8 * R
        root(doc)["video"]["duration"] = 8 * R
        with self.assertRaisesRegex(ValueError, "source bounds"):
            captions.map_captions(doc, 3)
        self.assertEqual(before["sourceBin"], doc["sourceBin"])

    def test_retiming_and_cue_edits_preserve_offsets_and_all_source_points(self):
        doc = with_offset(fixture())
        result = captions.retime(
            doc, 3, dict(schema_version=1, start=1, duration=2, media_start=1, scalar="1/2")
        )
        result = captions.set_cues(
            result,
            3,
            dict(
                schema_version=1,
                clock="timeline",
                cues=[dict(start=1, end=2, text="OFFSET"), dict(start=2, end=3, text="SECOND")],
            ),
        )
        self.assertEqual(audio(result)["attributes"], audio(doc)["attributes"])
        self.assertEqual(result["sourceBin"], doc["sourceBin"])
        mapped = captions.map_captions(result, 3)
        self.assertEqual(
            [
                (r["value"], r["timelineStartSeconds"], r["timelineEndSeconds"])
                for r in mapped["closed"]
            ],
            [("OFFSET", "1", "2"), ("SECOND", "2", "3")],
        )
        self.assertEqual(mapped["words"][0]["value"], "useful")
        self.assertEqual(mapped["words"][0]["timelineStartSeconds"], "3/2")
        self.assertEqual(
            captions.retime(
                result, 3, dict(schema_version=1, start=1, duration=2, media_start=1, scalar="1/2")
            ),
            result,
        )

    def test_closed_only_mapping_keeps_the_offset_report(self):
        doc = with_offset(one_group())
        report = captions.map_captions(doc, 3, closed_only=True)
        self.assertEqual(report["scope"], "closed")
        self.assertEqual(report["audioFileOffsets"][0]["ticks"], R)
        self.assertNotIn("words", report)

    def test_stitched_children_report_offsets_without_changing_parent_or_word_clocks(self):
        doc = stitched(group=True)
        stream = doc["sourceBin"][0]["sourceTracks"][1]
        stream.update(sampleRate=48000, range=[0, 10 * 48000])
        before = copy.deepcopy(doc)
        for child in parent(doc)["medias"]:
            child["audio"]["attributes"]["sourceFileOffset"] = 48000
        mapped = captions.map_captions(doc, 3)
        offsets = mapped.pop("audioFileOffsets")
        self.assertEqual(mapped, captions.map_captions(before, 3))
        self.assertEqual([r["audioClipId"] for r in offsets], [6, 9])
        self.assertEqual([r["ticks"] for r in offsets], [R, R])
        self.assertEqual(parent(doc)["parameters"], parent(before)["parameters"])

    def test_invalid_or_unmeasured_offsets_and_rates_refuse(self):
        for samples in [-1, "1/2", True, {}, 8 * 48000]:
            doc = with_offset(fixture(), samples)
            with self.subTest(samples=samples), self.assertRaises(ValueError):
                captions.map_captions(doc, 3)
        for rate in [None, 0, -48000, "1/2", True]:
            doc = with_offset(fixture())
            doc["sourceBin"][0]["sourceTracks"][1]["sampleRate"] = rate
            with self.subTest(rate=rate), self.assertRaisesRegex(ValueError, "sampleRate"):
                captions.map_captions(doc, 3)
        doc = with_offset(fixture())
        doc["authoringClientName"]["version"] = "2025.0.3"
        with self.assertRaises(ValueError):
            captions.map_captions(doc, 3)

    def test_cli_map_reports_samples_and_preserves_the_input_bytes(self):
        doc = with_offset(fixture(), 1)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "offset.tscproj"
            raw = project.encode_document(doc)
            path.write_bytes(raw)
            output = io.StringIO()
            with redirect_stdout(output):
                status = captions.main(["map", str(path), "--clip-id", "3"])
            self.assertEqual(status, 0)
            report = json.loads(output.getvalue())
            self.assertEqual(report["mapping"]["audioFileOffsets"][0]["samples"], 1)
            self.assertEqual(report["mapping"]["audioFileOffsets"][0]["ticks"], 14700)
            self.assertEqual(path.read_bytes(), raw)

    def test_source_correction_preserves_every_owner_offset_and_point_time(self):
        doc = with_offset(fixture())
        result = captions.correct_words(
            doc,
            1,
            1,
            dict(schema_version=1, edits=[dict(index=1, expected="useful", text="USEFUL")]),
        )
        self.assertEqual(result["timeline"], doc["timeline"])
        self.assertEqual(
            [p["time"] for p in words(result)["keyframes"]],
            [p["time"] for p in words(doc)["keyframes"]],
        )
        self.assertEqual(words(result)["keyframes"][1]["value"], "USEFUL")


if __name__ == "__main__":
    unittest.main()
