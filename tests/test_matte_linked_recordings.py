from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

from test_animation_freezes import owner_document, RATE
from test_animations import visual
import mattes
import project


def fixture():
    doc = owner_document("ScreenVMFile")
    video = visual(doc)
    video["effects"] = []
    video.update(
        start=30 * RATE,
        duration=3 * RATE,
        mediaStart=2 * RATE,
        mediaDuration=6 * RATE,
        scalar="1/2",
    )
    video["parameters"].update(
        cursorScale=5, cursorAction=dict(edits=[dict(time=3 * RATE, value=1)], deletions=[0])
    )
    video["animationTracks"] = {"visual": [dict(endTime=3 * RATE, duration=RATE, interp="line")]}
    audio = dict(
        id=11,
        _type="AMFile",
        src=1,
        trackNumber=1,
        channelNumber="0,1",
        attributes=dict(
            ident="", gain=0.7, mixToMono=False, loudnessNormalization=True, sourceFileOffset=0
        ),
        parameters=dict(volume=0.7),
        effects=[],
        animationTracks={},
    )
    for name in ["start", "duration", "mediaStart", "mediaDuration", "scalar"]:
        audio[name] = video[name]
    wrapper = dict(
        id=10,
        _type="UnifiedMedia",
        video=video,
        audio=audio,
        effects=[],
        metadata={
            "audiateLinkedSession": "",
            "clipSpeedAttribute": dict(type="bool", value=False),
            "default-scale": "0.549898",
            "effectApplied": "none",
            "opaqueWrapper": ["keep"],
        },
    )
    for name in ["start", "duration", "mediaStart", "mediaDuration", "scalar"]:
        wrapper[name] = video[name]
    project.scene_tracks(doc)[0][0]["medias"] = [wrapper]
    doc["sourceBin"][0].update(
        src="synthetic-recording.trec",
        opaqueSourceProcessing={"keep": ["recorded audio/video"]},
        sourceTracks=[
            dict(
                type=0, range=[0, 1189304], editRate=44100, sampleRate="36293/1250", numChannels=0
            ),
            dict(type=2, range=[0, 1188518], editRate=44100, sampleRate=44100, numChannels=2),
        ],
    )
    doc["timeline"]["trackAttributes"] = [dict(matte=0, metadata={"trackHeight": "78"})]
    return doc


def wrapper(doc):
    return project.scene_tracks(doc)[0][0]["medias"][0]


def native_effect() -> dict[str, Any]:
    return dict(
        effectName="MediaMatte",
        bypassed=False,
        category="categoryVisualEffects",
        parameters=dict(
            matteMode=1,
            intensity=dict(
                type="double",
                defaultValue=1.0,
                interp="linr",
                uiHints=dict(userInterfaceType=0, unitType=0),
            ),
            trackDepth=10002,
        ),
        metadata=dict(effectIndex="0"),
    )


def with_matte(doc):
    result = copy.deepcopy(doc)
    for owner in [wrapper(result), visual(result)]:
        owner["effects"].append(native_effect())
    return result


class LinkedRecordingMatteTests(unittest.TestCase):
    def test_fixed_native_constructor_matches_both_mirrors_and_preserves_complete_project(self):
        doc = fixture()
        before = copy.deepcopy(doc)
        result = mattes.edit_media(doc, 10, mode="alpha")
        self.assertEqual(result, with_matte(doc))
        self.assertEqual(doc, before)
        self.assertEqual(wrapper(result)["audio"], wrapper(doc)["audio"])
        self.assertEqual(result["sourceBin"], doc["sourceBin"])

    def test_wrapper_and_video_ids_resolve_the_same_native_mirrors(self):
        doc = fixture()
        self.assertEqual(
            mattes.edit_media(doc, 10, mode="alpha"), mattes.edit_media(doc, 3, mode="alpha")
        )
        self.assertEqual([n["id"] for n in mattes.media_targets(doc, 3)], [10, 3])

    def test_native_half_edit_preserves_existing_reset_metadata_and_other_fields(self):
        doc = with_matte(fixture())
        wrapper(doc)["metadata"]["default-MediaMatte-intensity"] = "1"
        for owner in [wrapper(doc), visual(doc)]:
            owner["effects"][0]["parameters"]["intensity"]["defaultValue"] = 0.5
            owner["effects"][0]["metadata"]["opaque"] = {"keep": [7]}
        before = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        for owner in [wrapper(expected), visual(expected)]:
            owner["effects"][0]["parameters"]["intensity"]["defaultValue"] = 0.75
        result = mattes.edit_media(doc, 3, intensity=0.75)
        self.assertEqual(result, expected)
        self.assertEqual(doc, before)
        self.assertEqual(wrapper(result)["metadata"]["default-MediaMatte-intensity"], "1")

    def test_native_bypass_removal_and_repeat_removal_preserve_linked_audio_and_cursor(self):
        original = fixture()
        doc = with_matte(original)
        expected = copy.deepcopy(doc)
        for owner in [wrapper(expected), visual(expected)]:
            owner["effects"][0]["bypassed"] = True
        bypass = mattes.edit_media(doc, 10, bypass=True)
        self.assertEqual(bypass, expected)
        self.assertEqual(mattes.edit_media(bypass, 3, mode="none"), original)
        self.assertEqual(mattes.edit_media(original, 10, mode="none"), original)

    def test_new_token_avoids_unrelated_wrapper_video_and_audio_effects_without_reordering(self):
        doc = fixture()
        for owner in [wrapper(doc), visual(doc)]:
            owner["effects"] = [
                dict(effectName="Existing", metadata=dict(effectIndex="2"), opaque=["keep"])
            ]
        wrapper(doc)["audio"]["effects"] = [
            dict(effectName="AudioExisting", metadata=dict(effectIndex="7"), opaque={"audio": True})
        ]
        result = mattes.edit_media(doc, 3, mode="alpha")
        expected = copy.deepcopy(doc)
        for owner in [wrapper(expected), visual(expected)]:
            effect = native_effect()
            effect["metadata"]["effectIndex"] = "8"
            owner["effects"].append(effect)
        self.assertEqual(result, expected)

    def test_fixed_source_position_curve_clocks_and_unrelated_visual_intervals_survive(self):
        doc = with_matte(fixture())
        before = copy.deepcopy(doc)
        result = mattes.edit_intensity_curve(
            doc,
            10,
            dict(
                schema_version=2,
                defaultValue=0,
                segments=[dict(start=0, end=1, value=1, easing="spring")],
            ),
        )
        expected = copy.deepcopy(doc)
        for owner in [wrapper(expected), visual(expected)]:
            owner["effects"][0]["parameters"]["intensity"] = {
                "type": "double",
                "defaultValue": 0.0,
                "uiHints": {"userInterfaceType": 0, "unitType": 0},
                "keyframes": [
                    dict(
                        time=1411200000,
                        endTime=2822400000,
                        duration=1411200000,
                        value=1.0,
                        interp="sprg",
                    )
                ],
            }
        self.assertEqual(result, expected)
        self.assertEqual(doc, before)
        self.assertEqual(visual(result)["animationTracks"], visual(doc)["animationTracks"])

    def test_curve_constructor_and_clear_change_only_intensity_on_both_mirrors(self):
        doc = fixture()
        curve = dict(schema_version=1, defaultValue=1, segments=[dict(start=1, end=2, value=0)])
        result = mattes.edit_intensity_curve(doc, 3, curve)
        expected = with_matte(doc)
        for owner in [wrapper(expected), visual(expected)]:
            p = owner["effects"][0]["parameters"]["intensity"]
            p.pop("interp")
            p["keyframes"] = [
                dict(
                    time=2822400000,
                    endTime=4233600000,
                    duration=1411200000,
                    value=0.0,
                    interp="linr",
                )
            ]
        self.assertEqual(result, expected)
        cleared = mattes.clear_intensity_curve(result, 10, 0.5)
        for owner in [wrapper(expected), visual(expected)]:
            p = owner["effects"][0]["parameters"]["intensity"]
            p.pop("keyframes")
            p["defaultValue"] = 0.5
        self.assertEqual(cleared, expected)

    def test_native_linear_interval_at_trimmed_double_speed_matches_both_mirrors(self):
        doc = with_matte(fixture())
        before = copy.deepcopy(doc)
        result = mattes.edit_intensity_curve(
            doc,
            10,
            dict(schema_version=1, defaultValue=0, segments=[dict(start=0, end=1, value=1)]),
        )
        expected = copy.deepcopy(doc)
        for owner in [wrapper(expected), visual(expected)]:
            owner["effects"][0]["parameters"]["intensity"] = {
                "type": "double",
                "defaultValue": 0.0,
                "uiHints": {"userInterfaceType": 0, "unitType": 0},
                "keyframes": [
                    dict(
                        time=1411200000,
                        endTime=2822400000,
                        duration=1411200000,
                        value=1.0,
                        interp="linr",
                    )
                ],
            }
        self.assertEqual(result, expected)
        self.assertEqual(doc, before)

    def test_composition_preserves_curve_audio_and_selects_each_physical_owner_once(self):
        doc = mattes.edit_intensity_curve(
            fixture(),
            3,
            dict(
                schema_version=2,
                defaultValue=0,
                segments=[dict(start=0, end=1, value=1, easing="bounce")],
            ),
        )
        before = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        for owner in [wrapper(expected), visual(expected)]:
            owner["effects"][0]["parameters"]["matteMode"] = 2
        expected["timeline"]["trackAttributes"][0]["matte"] = 1
        result = mattes.edit_composition(
            doc,
            dict(
                schema_version=1,
                media=[dict(clipId=10, mode="alpha-invert")],
                tracks=[dict(track=0, mode="alpha")],
            ),
        )
        self.assertEqual(result, expected)
        self.assertEqual(doc, before)
        for items in [
            [dict(clipId=10, mode="alpha"), dict(clipId=3, mode="alpha")],
            [dict(clipId=10, mode="alpha"), dict(clipId=999, mode="alpha")],
        ]:
            with self.assertRaises(ValueError):
                mattes.edit_composition(
                    doc, dict(schema_version=1, media=items, tracks=[dict(track=0, mode="alpha")])
                )
            self.assertEqual(doc, before)

    def test_missing_and_conflicting_recording_clocks_refuse_all_edit_paths(self):
        commands = [
            lambda d: mattes.edit_media(d, 10, mode="alpha"),
            lambda d: mattes.edit_intensity_curve(
                d,
                3,
                dict(schema_version=1, defaultValue=0, segments=[dict(start=0, end=1, value=1)]),
            ),
            lambda d: mattes.clear_intensity_curve(d, 10, 0.5),
        ]
        for field in ["start", "duration", "mediaStart", "mediaDuration", "scalar"]:
            for change in ["missing", "conflict", "boolean"]:
                doc = with_matte(fixture())
                if change == "missing":
                    visual(doc).pop(field)
                elif change == "conflict":
                    visual(doc)[field] = 2 if field == "scalar" else visual(doc)[field] + 1
                else:
                    visual(doc)[field] = True
                before = copy.deepcopy(doc)
                for command in commands:
                    with self.subTest(field=field, change=change), self.assertRaises(ValueError):
                        command(doc)
                    self.assertEqual(doc, before)

    def test_nonpositive_project_rate_and_recording_speed_refuse_before_staging(self):
        for field in ["editRate", "scalar"]:
            doc = fixture()
            if field == "editRate":
                doc[field] = 0
            else:
                for owner in [wrapper(doc), visual(doc)]:
                    owner["scalar"] = 0
            with self.assertRaisesRegex(ValueError, "positive"):
                mattes.edit_media(doc, 3, mode="alpha")

    def test_unknown_audio_children_and_source_bindings_refuse_without_mutation(self):
        for change in [
            "missing",
            "null",
            "wrong-kind",
            "source",
            "boolean-source",
            "missing-source",
        ]:
            doc = fixture()
            if change == "missing":
                wrapper(doc).pop("audio")
            elif change == "null":
                wrapper(doc)["audio"] = None
            elif change == "wrong-kind":
                wrapper(doc)["audio"]["_type"] = "VMFile"
            elif change == "source":
                wrapper(doc)["audio"]["src"] = 2
            elif change == "boolean-source":
                wrapper(doc)["audio"]["src"] = True
            else:
                visual(doc).pop("src")
            before = copy.deepcopy(doc)
            with (
                self.subTest(change=change),
                self.assertRaisesRegex(ValueError, "linked recording audio"),
            ):
                mattes.edit_media(doc, 10, mode="alpha")
            self.assertEqual(doc, before)

    def test_held_stitched_nested_and_multiple_scene_linked_recordings_refuse(self):
        for kind in ["ScreenIMFile", "StitchedMedia"]:
            doc = fixture()
            visual(doc)["_type"] = kind
            with self.assertRaisesRegex(ValueError, "linked recording matte mirrors"):
                mattes.edit_media(doc, 10, mode="alpha")
        doc = fixture()
        old = wrapper(doc)
        project.scene_tracks(doc)[0][0]["medias"] = [
            dict(id=20, _type="Group", tracks=[dict(trackIndex=0, medias=[old])])
        ]
        with self.assertRaisesRegex(ValueError, "root linked"):
            mattes.edit_media(doc, 3, mode="alpha")
        doc = fixture()
        doc["timeline"]["sceneTrack"]["scenes"].append(
            copy.deepcopy(doc["timeline"]["sceneTrack"]["scenes"][0])
        )
        doc["timeline"]["sceneTrack"]["scenes"][1]["csml"]["tracks"][0]["medias"] = []
        with self.assertRaisesRegex(ValueError, "root linked"):
            mattes.edit_media(doc, 3, mode="alpha")

    def test_missing_conflicting_and_duplicate_native_effect_mirrors_refuse(self):
        for change in ["missing", "token", "controls", "bypass", "duplicate"]:
            doc = with_matte(fixture())
            if change == "missing":
                visual(doc)["effects"].clear()
            elif change == "token":
                visual(doc)["effects"][0]["metadata"]["effectIndex"] = "1"
            elif change == "controls":
                visual(doc)["effects"][0]["parameters"]["trackDepth"] = 3
            elif change == "bypass":
                visual(doc)["effects"][0]["bypassed"] = True
            else:
                visual(doc)["effects"].append(copy.deepcopy(visual(doc)["effects"][0]))
            before = copy.deepcopy(doc)
            with self.subTest(change=change), self.assertRaises(ValueError):
                mattes.edit_media(doc, 10, intensity=0.5)
            self.assertEqual(doc, before)

    def test_cli_staging_repeat_curve_clear_removal_and_invalid_input_preserve_files(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            output = root / "candidate.json"
            curve = root / "curve.json"
            curved = root / "curved.json"
            cleared = root / "cleared.json"
            removed = root / "removed.json"
            doc = fixture()
            source.write_bytes(project.encode_document(doc))
            original = source.read_bytes()
            args = [
                "set-media",
                str(source),
                "--clip-id",
                "10",
                "--mode",
                "alpha",
                "--output",
                str(output),
            ]
            for written in [True, False]:
                with patch("sys.stdout", new_callable=io.StringIO) as stream:
                    self.assertEqual(mattes.main(args), 0)
                report = json.loads(stream.getvalue())
                self.assertEqual(report["owner"], "camtasia-mattes")
                self.assertEqual(report["schema_version"], 1)
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
                self.assertEqual(len(report["mediaMattes"]), 2)
            curve.write_text(
                json.dumps(
                    dict(
                        schema_version=2,
                        defaultValue=0,
                        segments=[dict(start=0, end=1, value=1, easing="spring")],
                    )
                )
            )
            for command in [
                [
                    "set-intensity-curve",
                    str(output),
                    "--clip-id",
                    "3",
                    "--curve",
                    str(curve),
                    "--output",
                    str(curved),
                ],
                [
                    "clear-intensity-curve",
                    str(curved),
                    "--clip-id",
                    "10",
                    "--intensity",
                    ".5",
                    "--output",
                    str(cleared),
                ],
                [
                    "set-media",
                    str(cleared),
                    "--clip-id",
                    "3",
                    "--mode",
                    "none",
                    "--output",
                    str(removed),
                ],
            ]:
                with patch("sys.stdout", new_callable=io.StringIO):
                    self.assertEqual(mattes.main(command), 0)
            self.assertEqual(project.load(removed)[0], doc)
            self.assertEqual(source.read_bytes(), original)
            bad = root / "bad.json"
            broken = fixture()
            visual(broken)["scalar"] = 2
            bad.write_bytes(project.encode_document(broken))
            candidate = root / "refused.json"
            with patch("sys.stderr", new_callable=io.StringIO) as stream:
                self.assertEqual(
                    mattes.main(
                        [
                            "set-media",
                            str(bad),
                            "--clip-id",
                            "10",
                            "--mode",
                            "alpha",
                            "--output",
                            str(candidate),
                        ]
                    ),
                    1,
                )
            self.assertFalse(json.loads(stream.getvalue())["ok"])
            self.assertFalse(candidate.exists())

    def test_top_level_and_all_matte_subcommand_help_emit_versioned_json(self):
        for command in [
            [],
            ["inspect"],
            ["set-media"],
            ["set-track"],
            ["set-composition"],
            ["set-intensity-curve"],
            ["clear-intensity-curve"],
        ]:
            with (
                self.subTest(command=command),
                patch("sys.stdout", new_callable=io.StringIO) as stream,
                self.assertRaises(SystemExit) as error,
            ):
                mattes.main([*command, "--help"])
            self.assertEqual(error.exception.code, 0)
            report = json.loads(stream.getvalue())
            self.assertEqual(report["schema_version"], 1)
            self.assertEqual(report["owner"], "camtasia-mattes")
            self.assertTrue(report["ok"])
            self.assertIn("usage:", report["help"])


if __name__ == "__main__":
    unittest.main()
