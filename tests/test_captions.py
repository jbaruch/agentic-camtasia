from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_quizzes import document
import captions
import project

R = 705600000


def point(seconds, value, **extra) -> dict:
    return dict(time=int(seconds * R), endTime=int(seconds * R), duration=0, value=value, **extra)


def value(text) -> dict:
    return dict(text=text, textAttributes=None)


def lane(doc, index=0):
    return project.scene_tracks(doc)[0][index]


def root(doc):
    return lane(doc)["medias"][0]


def audio(doc):
    owner = root(doc)
    return owner["audio"] if owner["_type"] == "UnifiedMedia" else owner


def closed(doc):
    owner = audio(doc)
    return owner["parameters"]["captionData" if owner["_type"] == "Caption" else "captions"]


def words(doc):
    return doc["sourceBin"][0]["sourceTracks"][1]["parameters"]["transcription"]


def fixture(form="linked") -> dict:
    doc = document()
    doc["editRate"] = R
    doc["timeline"]["captionAttributes"] = dict(
        enabled=False, fontName="Arial", fontSize=32, opaque=["global"]
    )
    doc["sourceBin"][0]["sourceTracks"] = [
        dict(type=0, editRate=48000, range=[0, 384000], parameters={}),
        dict(
            type=2,
            editRate=48000,
            range=[0, 384000],
            transcriptionSet=True,
            parameters={
                "transcription": dict(
                    type="string",
                    opaque=["source"],
                    keyframes=[
                        point(0.02, "First", confidence="retained"),
                        point(2, "useful"),
                        point(4, "last."),
                        point(6, "%GAP"),
                    ],
                )
            },
            opaque=["stream"],
        ),
    ]
    clock = dict(start=0, duration=8 * R, mediaStart=0, mediaDuration=8 * R, scalar=1)
    owner: dict = dict(
        id=3,
        _type="AMFile",
        src=1,
        trackNumber=1,
        parameters={
            "captions": dict(
                type="caption",
                opaque=["parameter"],
                keyframes=[
                    point(0, value("First café")),
                    point(4, value("Second → text")),
                    point(8, value("")),
                ],
            )
        },
        effects=[],
        animationTracks={},
        metadata={"keep": "owner"},
        attributes={"keep": [1]},
        **clock,
    )
    if form == "imported":
        owner["_type"] = "Caption"
        owner["parameters"]["captionData"] = owner["parameters"].pop("captions")
        owner.pop("src")
        owner.pop("trackNumber")
        owner.pop("attributes")
        owner.update(maxMediaDuration=8.0 * R, allowTrimOut=False)
    elif form == "linked":
        owner["id"] = 5
        video = dict(
            id=4,
            _type="VMFile",
            src=1,
            trackNumber=0,
            parameters={"opaque": ["video"]},
            effects=[],
            animationTracks={},
            **clock,
        )
        owner = dict(
            id=3,
            _type="UnifiedMedia",
            video=video,
            audio=owner,
            metadata={"keep": "wrapper"},
            effects=[],
            animationTracks={},
            **clock,
        )
    lane(doc)["medias"] = [owner]
    return doc


def display(doc):
    return lane(doc, 1)["medias"][0]


def dynamic() -> dict:
    doc = fixture()
    node = dict(
        id=6,
        _type="Callout",
        start=0,
        duration=60 * R,
        mediaStart=0,
        mediaDuration=60 * R,
        scalar=1,
        parameters={"scale0": 0.5},
        effects=[],
        animationTracks={},
        metadata={"keep": "display"},
        **{
            "def": {
                "kind": "remix",
                "modifier": "dynamicCaption",
                "text": "ABC",
                "style": "caption",
                "dynamic-caption-preset-ID": "native-style-token",
                "dynamic-caption-new-paragraph-for-each-sentence": 0.0,
                "dynamic-caption-current-word-color-red": 0.8,
                "dynamic-caption-current-word-enabled": 1.0,
                "font": {"name": "Default Native Font", "size": 128},
                "textAttributes": {
                    "type": "textAttributeList",
                    "keyframes": [
                        {
                            "time": 0,
                            "duration": 0,
                            "endTime": 0,
                            "value": [
                                dict(
                                    name="fontSize",
                                    rangeStart=0,
                                    rangeEnd=3,
                                    valueType="double",
                                    value=96.0,
                                    opaque=["style"],
                                ),
                                dict(
                                    name="fgColor",
                                    rangeStart=0,
                                    rangeEnd=3,
                                    valueType="color",
                                    value="(0,0,0,255)",
                                ),
                                dict(
                                    name="fontName",
                                    rangeStart=0,
                                    rangeEnd=3,
                                    valueType="string",
                                    value="Native Family",
                                ),
                                dict(
                                    name="underline",
                                    rangeStart=0,
                                    rangeEnd=1,
                                    valueType="int",
                                    value=0,
                                ),
                            ],
                        }
                    ],
                },
            }
        },
    )
    project.scene_tracks(doc)[0].append(dict(trackIndex=1, medias=[node], parameters={}))
    return doc


def spec(**values) -> dict:
    return dict(schema_version=1, **values)


def edits(index=0, expected="First café", text="Edited café → now") -> dict:
    return spec(edits=[dict(index=index, expected=expected, text=text)])


def retime_spec():
    return spec(start=1, duration=3, media_start=2, scalar="1/2")


class CaptionTests(unittest.TestCase):
    def test_closed_correction_preserves_complete_points_styles_sources_and_other_forms(self):
        for form in ("audio", "linked", "imported"):
            doc = fixture(form)
            closed(doc)["keyframes"][0]["future"] = ["retain point"]
            closed(doc)["keyframes"][0]["value"]["future"] = ["retain value"]
            before = copy.deepcopy(doc)
            result = captions.correct_text(doc, 3, edits())
            expected = copy.deepcopy(doc)
            closed(expected)["keyframes"][0]["value"]["text"] = "Edited café → now"
            self.assertEqual(result, expected)
            self.assertEqual(doc, before)
            self.assertEqual(captions.correct_text(result, 3, edits()), result)

    def test_linked_audio_child_and_wrapper_select_the_same_physical_parameter(self):
        doc = fixture()
        self.assertEqual(
            captions.correct_text(doc, 3, edits()), captions.correct_text(doc, 5, edits())
        )
        with self.assertRaises(ValueError):
            captions.correct_text(doc, 4, edits())

    def test_actual_word_correction_retains_all_onsets_pause_markers_and_display(self):
        doc = dynamic()
        before = copy.deepcopy(doc)
        request = edits(1, "useful", "HELPFUL")
        result = captions.correct_words(doc, 1, 1, request)
        expected = copy.deepcopy(doc)
        words(expected)["keyframes"][1]["value"] = "HELPFUL"
        self.assertEqual(result, expected)
        self.assertEqual(doc, before)
        self.assertEqual(captions.correct_words(result, 1, 1, request), result)
        self.assertEqual(words(result)["keyframes"][3]["value"], "%GAP")

    def test_word_correction_affects_shared_source_without_copying_or_editing_uses(self):
        doc = dynamic()
        other = copy.deepcopy(root(doc))
        other["id"], other["video"]["id"], other["audio"]["id"] = 20, 21, 22
        project.scene_tracks(doc)[0].append(dict(medias=[other]))
        result = captions.correct_words(doc, 1, 1, edits(1, "useful", "HELPFUL"))
        self.assertEqual(result["timeline"], doc["timeline"])
        self.assertEqual(len(result["sourceBin"]), 1)

    def test_missing_recognition_and_pause_or_multiword_edits_refuse(self):
        for mutation in ("absent", "unset", "empty", "gap", "new-gap", "space", "stale", "stream"):
            doc, request = dynamic(), edits(1, "useful", "HELPFUL")
            stream = doc["sourceBin"][0]["sourceTracks"][1]
            if mutation == "absent":
                stream["parameters"].pop("transcription")
            elif mutation == "unset":
                stream["transcriptionSet"] = False
            elif mutation == "empty":
                words(doc)["keyframes"] = []
            elif mutation == "gap":
                request = edits(3, "%GAP", "word")
            elif mutation == "new-gap":
                request["edits"][0]["text"] = "%GAP"
            elif mutation == "space":
                request["edits"][0]["text"] = "two words"
            elif mutation == "stale":
                request["edits"][0]["expected"] = "elsewhere"
            else:
                stream["type"] = 0
            before = copy.deepcopy(doc)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                captions.correct_words(doc, 1, 1, request)
            self.assertEqual(doc, before)

    def test_native_plain_cue_authoring_inserts_gaps_final_clear_and_preserves_style(self):
        doc = fixture("imported")
        result = captions.set_cues(
            doc,
            3,
            spec(
                clock="media",
                cues=[
                    dict(start=1, end=2, text="Café & one"),
                    dict(start=3, end=4, text="日本語 → two"),
                    dict(start=4, end=6, text="Adjacent"),
                ],
            ),
        )
        expected = copy.deepcopy(doc)
        closed(expected)["keyframes"] = [
            point(0, value("")),
            point(1, value("Café & one")),
            point(2, value("")),
            point(3, value("日本語 → two")),
            point(4, value("Adjacent")),
            point(6, value("")),
        ]
        expected["timeline"]["captionAttributes"]["enabled"] = True
        self.assertEqual(result, expected)
        self.assertEqual(
            captions.set_cues(
                result,
                3,
                spec(
                    clock="media",
                    cues=[
                        dict(start=1, end=2, text="Café & one"),
                        dict(start=3, end=4, text="日本語 → two"),
                        dict(start=4, end=6, text="Adjacent"),
                    ],
                ),
            ),
            result,
        )

    def test_empty_cue_spec_explicitly_clears_without_removing_native_parameter(self):
        result = captions.set_cues(fixture(), 3, spec(clock="media", cues=[]))
        self.assertEqual(closed(result)["keyframes"], [point(0, value(""))])
        self.assertEqual(closed(result)["opaque"], ["parameter"])

    def test_cue_replacement_refuses_dropping_opaque_points_rtf_and_styles(self):
        for mutation in ("point", "value", "rtf", "styled", "new-rtf"):
            doc = fixture("imported")
            request = spec(clock="media", cues=[dict(start=0, end=2, text="New")])
            frame = closed(doc)["keyframes"][0]
            if mutation == "point":
                frame["opaque"] = [1]
            elif mutation == "value":
                frame["value"]["opaque"] = [1]
            elif mutation == "rtf":
                frame["value"]["text"] = "{\\rtf1 native}"
            elif mutation == "styled":
                frame["value"]["textAttributes"] = {"keep": 1}
            else:
                request["cues"][0]["text"] = "{\\rtf1 native}"
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                captions.set_cues(doc, 3, request)
        with self.assertRaises(ValueError):
            captions.correct_text(fixture(), 3, edits(text="{\\rtf1 new}"))

    def test_closed_and_word_mapping_uses_project_ticks_not_source_stream_rate(self):
        for form in ("audio", "linked", "imported"):
            doc = captions.retime(fixture(form), 3, retime_spec())
            mapped = captions.map_captions(doc, 3)
            self.assertEqual(
                [
                    (c["value"], c["timelineStartSeconds"], c["timelineEndSeconds"])
                    for c in mapped["closed"]
                ],
                [("First café", "1", "2"), ("Second → text", "2", "4")],
            )
            if form != "imported":
                self.assertEqual(
                    [
                        (w["value"], w["timelineStartSeconds"], w["timelineEndSeconds"])
                        for w in mapped["words"]
                    ],
                    [("useful", "1", "2"), ("last.", "2", "3"), ("%GAP", "3", "4")],
                )

    def test_retime_changes_only_complete_mirrored_clocks_and_preserves_cue_word_payload(self):
        for form in ("audio", "linked", "imported"):
            doc = fixture(form)
            result = captions.retime(doc, 3, retime_spec())
            expected = copy.deepcopy(doc)
            nodes = (
                [root(expected)]
                if form != "linked"
                else [root(expected), root(expected)["video"], audio(expected)]
            )
            for n in nodes:
                n.update(
                    start=R, duration=3 * R, mediaStart=2 * R, mediaDuration=6 * R, scalar="1/2"
                )
            self.assertEqual(result, expected)
            self.assertEqual(captions.retime(result, 3, retime_spec()), result)

    def test_timeline_clock_cues_invert_trim_offset_and_inverse_speed_exactly(self):
        doc = captions.retime(fixture(), 3, retime_spec())
        result = captions.set_cues(
            doc,
            3,
            spec(
                clock="timeline",
                cues=[dict(start=1, end=2, text="One"), dict(start=2, end=4, text="Two")],
            ),
        )
        self.assertEqual(
            closed(result)["keyframes"],
            [
                point(0, value("")),
                point(2, value("One")),
                point(4, value("Two")),
                point(8, value("")),
            ],
        )

    def test_stream_clock_differences_do_not_rescale_transcription_points(self):
        doc = fixture()
        stream = doc["sourceBin"][0]["sourceTracks"][1]
        stream.update(editRate=384000, range=[0, 3072000], sampleRate=48000)
        self.assertEqual(captions.map_captions(doc, 3)["words"][1]["timelineStartSeconds"], "2")

    def test_trim_carries_closed_cue_but_omits_partly_trimmed_dynamic_word(self):
        doc = fixture()
        words(doc)["keyframes"] = [
            point(0.02, "First"),
            point(1.5, "We"),
            point(2.25, "build"),
            point(4, "last."),
            point(6, "%GAP"),
        ]
        mapped = captions.map_captions(captions.retime(doc, 3, retime_spec()), 3)
        self.assertEqual(mapped["closed"][0]["value"], "First café")
        self.assertEqual(mapped["closed"][0]["timelineStartSeconds"], "1")
        self.assertEqual(mapped["words"][0]["value"], "build")
        self.assertEqual(mapped["words"][0]["timelineStartSeconds"], "9/8")
        self.assertNotIn("We", [w["value"] for w in mapped["words"]])

    def test_trimmed_silent_tail_has_valid_empty_word_mapping_and_idempotent_retime(self):
        doc = fixture()
        audio(doc)["parameters"].pop("captions")
        request = spec(start=0, duration=1, media_start=7, scalar=1)
        result = captions.retime(doc, 3, request)
        mapped = captions.map_captions(result, 3)
        self.assertEqual(mapped["words"], [])
        self.assertEqual(mapped["closed"], [])
        self.assertEqual(captions.retime(result, 3, request), result)
        self.assertEqual(words(result), words(doc))

    def test_source_file_offsets_need_an_independent_caption_clock_contract(self):
        doc = fixture()
        audio(doc)["attributes"]["sourceFileOffset"] = 48000
        with self.assertRaisesRegex(ValueError, "sourceFileOffset"):
            captions.map_captions(doc, 3)
        with self.assertRaisesRegex(ValueError, "sourceFileOffset"):
            captions.retime(doc, 3, retime_spec())
        result = captions.correct_words(doc, 1, 1, edits(1, "useful", "HELPFUL"))
        self.assertEqual(result["timeline"], doc["timeline"])

    def test_subframe_word_onsets_and_fractional_mapped_ticks_are_not_quantized(self):
        doc = fixture()
        words(doc)["keyframes"][1].update(time=2 * R + 1, endTime=2 * R + 1)
        result = captions.retime(doc, 3, retime_spec())
        mapped = next(w for w in captions.map_captions(result, 3)["words"] if w["index"] == 1)
        self.assertEqual(mapped["sourceTime"], 2 * R + 1)
        self.assertEqual(mapped["timelineStartTicks"], "1411200001/2")

    def test_dynamic_style_edits_preserve_placeholder_partial_ranges_and_defaults(self):
        doc = dynamic()
        result = captions.set_display(
            doc,
            6,
            spec(
                start=1,
                duration=3,
                definition={
                    "dynamic-caption-new-paragraph-for-each-sentence": 1,
                    "dynamic-caption-current-word-color-red": "3/4",
                },
                rich={"fontName": "Arial", "fontSize": 48, "fgColor": "(255,255,255,255)"},
            ),
        )
        expected = copy.deepcopy(doc)
        node = display(expected)
        node.update(start=R, duration=3 * R, mediaDuration=3 * R)
        node["def"].update(
            {
                "dynamic-caption-new-paragraph-for-each-sentence": 1.0,
                "dynamic-caption-current-word-color-red": 0.75,
            }
        )
        for run in node["def"]["textAttributes"]["keyframes"][0]["value"]:
            if run["name"] in {"fontName", "fontSize", "fgColor"}:
                run["value"] = {
                    "fontName": "Arial",
                    "fontSize": 48.0,
                    "fgColor": "(255,255,255,255)",
                }[run["name"]]
        self.assertEqual(result, expected)
        self.assertEqual(display(result)["def"]["text"], "ABC")
        self.assertEqual(captions.set_display(result, 6, spec(duration=3)), result)

    def test_display_styling_refuses_selected_partial_duplicate_animated_runs(self):
        for mutation in ("partial", "duplicate", "animated", "unknown", "placeholder", "preset"):
            doc = dynamic()
            request = spec(rich={"fontSize": 48})
            frame = display(doc)["def"]["textAttributes"]["keyframes"][0]
            if mutation == "partial":
                frame["value"][0]["rangeEnd"] = 1
            elif mutation == "duplicate":
                frame["value"].append(copy.deepcopy(frame["value"][0]))
            elif mutation == "animated":
                frame["time"] = R
            elif mutation == "unknown":
                request = spec(rich={"future": 1})
            elif mutation == "placeholder":
                request = spec(text="Transcript")
            else:
                request = spec(definition={"dynamic-caption-preset-ID": "replace"})
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                captions.set_display(doc, 6, request)

    def test_retime_refuses_nested_multiscene_mirror_conflicts_bounds_and_collisions(self):
        for mutation in (
            "nested",
            "scenes",
            "mirror",
            "bounds",
            "effect",
            "animation",
            "collision",
            "transition",
            "no-captions",
        ):
            doc = fixture()
            request = retime_spec()
            if mutation == "nested":
                lane(doc)["medias"] = [
                    dict(id=99, _type="Group", tracks=[dict(medias=[root(doc)])])
                ]
            elif mutation == "scenes":
                doc["timeline"]["sceneTrack"]["scenes"].append(
                    copy.deepcopy(doc["timeline"]["sceneTrack"]["scenes"][0])
                )
            elif mutation == "mirror":
                audio(doc)["start"] = R
            elif mutation == "bounds":
                request["duration"] = 4
            elif mutation == "effect":
                audio(doc)["effects"] = [dict(effectName="Keep")]
            elif mutation == "animation":
                root(doc)["animationTracks"] = {"keep": [1]}
            elif mutation == "collision":
                lane(doc)["medias"].append(dict(id=99, _type="Callout", start=R, duration=R))
            elif mutation == "transition":
                lane(doc)["transitions"] = [dict(name="Fade", leftMedia=3, duration=4 * R)]
            else:
                audio(doc)["parameters"].pop("captions")
                doc["sourceBin"][0]["sourceTracks"][1]["transcriptionSet"] = False
            before = copy.deepcopy(doc)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                captions.retime(doc, 3, request)
            self.assertEqual(doc, before)

    def test_display_bounds_reject_modified_clocks_effects_overlaps_and_bad_fades(self):
        for mutation in ("trim", "scalar", "effect", "edge", "collision", "transition"):
            doc = dynamic()
            node = display(doc)
            if mutation == "trim":
                node["mediaStart"] = R
            elif mutation == "scalar":
                node["scalar"] = "1/2"
            elif mutation == "effect":
                node["effects"] = [dict(effectName="Keep")]
            elif mutation == "edge":
                node["leftEdgeMods"] = [dict(group="Keep")]
            elif mutation == "collision":
                lane(doc, 1)["medias"].append(dict(id=99, _type="Callout", start=R, duration=R))
            else:
                lane(doc, 1)["transitions"] = [dict(name="Fade", leftMedia=6, duration=4 * R)]
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                captions.set_display(doc, 6, spec(duration=3))

    def test_plain_closed_text_and_retime_work_on_observed_format_nine(self):
        doc = fixture()
        doc["sourceBin"][0]["sourceTracks"][1]["transcriptionSet"] = False
        doc["sourceBin"][0]["sourceTracks"][1]["parameters"].pop("transcription")
        doc.update(
            version="9.0",
            authoringClientName={"name": "Camtasia", "platform": "Mac", "version": "2025.0.3"},
        )
        self.assertEqual(
            closed(captions.correct_text(doc, 3, edits()))["keyframes"][0]["value"]["text"],
            "Edited café → now",
        )
        self.assertEqual(root(captions.retime(doc, 3, retime_spec()))["scalar"], "1/2")
        with self.assertRaises(ValueError):
            captions.correct_words(doc, 1, 1, edits(1, "useful", "HELPFUL"))

    def test_unknown_build_or_clock_and_malformed_points_refuse(self):
        for mutation in ("build", "clock", "duration", "end", "order", "bool", "value"):
            doc = fixture()
            frames = closed(doc)["keyframes"]
            if mutation == "build":
                doc["authoringClientName"]["version"] = "2027.0"
            elif mutation == "clock":
                doc["editRate"] = 48000
            elif mutation == "duration":
                frames[0]["duration"] = 1
            elif mutation == "end":
                frames[0]["endTime"] = 1
            elif mutation == "order":
                frames.reverse()
            elif mutation == "bool":
                frames[0]["time"] = False
            else:
                frames[0]["value"] = None
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                captions.correct_text(doc, 3, edits())

    def test_invalid_cues_and_corrections_are_atomic_and_actionable(self):
        invalid = [
            spec(clock="media", cues=[dict(start=2, end=1, text="x")]),
            spec(clock="media", cues=[dict(start=0, end=9, text="x")]),
            spec(
                clock="media", cues=[dict(start=0, end=4, text="x"), dict(start=3, end=5, text="y")]
            ),
            spec(clock="sample", cues=[]),
            spec(clock="media", cues=[dict(start=0, end=1, text="")]),
            spec(clock="media", cues=[dict(start="1/705600001", end=1, text="x")]),
        ]
        for request in invalid:
            doc = fixture()
            before = copy.deepcopy(doc)
            with self.subTest(request=request), self.assertRaises(ValueError):
                captions.set_cues(doc, 3, request)
            self.assertEqual(doc, before)
        for request in [
            spec(edits=[]),
            spec(edits=[dict(index=True, expected="First café", text="x")]),
            spec(
                edits=[
                    dict(index=0, expected="First café", text="x"),
                    dict(index=0, expected="First café", text="y"),
                ]
            ),
            spec(edits=[dict(index=0, expected="stale", text="x")]),
        ]:
            with self.assertRaises(ValueError):
                captions.correct_text(fixture(), 3, request)

    def test_inventory_keeps_all_three_ownership_forms_separate(self):
        rows = captions.inventory(dynamic())
        self.assertEqual(rows["closed"][0]["clipId"], 5)
        self.assertEqual(rows["transcriptions"][0]["sourceId"], 1)
        self.assertEqual(rows["transcriptions"][0]["sourceTrack"], 1)
        self.assertEqual(rows["displays"][0]["clipId"], 6)
        for malformed in [None, {}, [None]]:
            doc = fixture()
            doc["sourceBin"] = malformed
            with self.assertRaises(ValueError):
                captions.inventory(doc)

    def test_cli_commands_stage_exclusively_preserve_inputs_and_report_native_status(self):
        with tempfile.TemporaryDirectory() as tmp:
            root_path = Path(tmp)
            source = root_path / "source.json"
            request = root_path / "spec.json"
            output = root_path / "candidate.json"
            source.write_bytes(project.encode_document(dynamic()))
            raw = source.read_bytes()
            cases = [
                ("set-text", ["--clip-id", "3"], edits()),
                (
                    "set-cues",
                    ["--clip-id", "3"],
                    spec(clock="media", cues=[dict(start=1, end=2, text="Café → cue")]),
                ),
                (
                    "correct-words",
                    ["--source-id", "1", "--source-track", "1"],
                    edits(1, "useful", "HELPFUL"),
                ),
                ("retime", ["--clip-id", "3"], retime_spec()),
                (
                    "set-display",
                    ["--clip-id", "6"],
                    spec(duration=8, rich={"fgColor": "(255,255,255,255)"}),
                ),
            ]
            for command, selectors, body in cases:
                output.unlink(missing_ok=True)
                request.write_text(json.dumps(body))
                args = [
                    command,
                    str(source),
                    *selectors,
                    "--spec",
                    str(request),
                    "--output",
                    str(output),
                ]
                for written in (True, False):
                    stdout = io.StringIO()
                    with patch("sys.stdout", stdout):
                        self.assertEqual(captions.main(args), 0)
                    report = json.loads(stdout.getvalue())
                    self.assertEqual(report["written"], written)
                    self.assertFalse(report["nativeVerified"])
                    self.assertEqual(report["candidateSha256"], project.digest(output.read_bytes()))
            for args in [["inspect", str(source)], ["map", str(source), "--clip-id", "3"]]:
                with patch("sys.stdout", io.StringIO()):
                    self.assertEqual(captions.main(args), 0)
            self.assertEqual(source.read_bytes(), raw)

    def test_cli_argument_errors_are_json_and_bad_input_is_not_written(self):
        stderr = io.StringIO()
        with patch("sys.stderr", stderr), self.assertRaises(SystemExit) as failure:
            captions.main(["retime", "x"])
        self.assertEqual(failure.exception.code, 2)
        self.assertFalse(json.loads(stderr.getvalue())["ok"])
        with tempfile.TemporaryDirectory() as tmp:
            source = Path(tmp) / "bad.json"
            source.write_text("{bad")
            stderr = io.StringIO()
            with patch("sys.stderr", stderr):
                self.assertEqual(captions.main(["inspect", str(source)]), 1)
            self.assertFalse(json.loads(stderr.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()
