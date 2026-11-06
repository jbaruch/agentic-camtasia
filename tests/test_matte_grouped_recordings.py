from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_effect_grouped_recordings import grouped, node
from test_matte_linked_recordings import native_effect
import mattes
import project


def fixture(depth=1):
    doc = grouped(depth=depth)
    for i in range(depth):
        for track in node(doc, 100 + i)["tracks"]:
            track["matte"] = 0
    owner = node(doc, 100)
    owner["tracks"][0]["trackIndex"] = 1
    owner["tracks"].insert(
        0,
        dict(
            trackIndex=0,
            matte=0,
            medias=[
                dict(
                    id=50,
                    _type="Callout",
                    effects=[],
                    parameters=dict(opacity=1),
                    def_opaque=["lower layer"],
                )
            ],
            metadata=dict(IsLocked="False"),
        ),
    )
    return doc


def with_matte(depth=1):
    doc = fixture(depth)
    for ident in (10, 3):
        node(doc, ident)["effects"] = [native_effect()]
    return doc


def curve(easing="linear"):
    return dict(
        schema_version=2, defaultValue=0, segments=[dict(start=0, end=1, value=1, easing=easing)]
    )


class GroupedRecordingMatteTests(unittest.TestCase):
    def test_native_constructor_and_both_aliases_preserve_complete_single_and_nested_groups(self):
        for depth in (1, 2):
            doc = fixture(depth)
            original = copy.deepcopy(doc)
            expected = copy.deepcopy(doc)
            for ident in (10, 3):
                node(expected, ident)["effects"] = [native_effect()]
            for ident in (10, 3):
                self.assertEqual(mattes.edit_media(doc, ident, mode="alpha"), expected)
            self.assertEqual(doc, original)

    def test_static_mode_intensity_bypass_and_removal_leave_ancestor_lower_layer_audio_and_resets(
        self,
    ):
        doc = with_matte(2)
        node(doc, 10)["metadata"]["default-MediaMatte-intensity"] = "1"
        expected = copy.deepcopy(doc)
        for ident in (10, 3):
            effect = node(expected, ident)["effects"][0]
            effect["bypassed"] = True
            effect["parameters"]["matteMode"] = 2
            effect["parameters"]["intensity"]["defaultValue"] = 0.5
        original = copy.deepcopy(doc)
        result = mattes.edit_media(doc, 3, mode="alpha-invert", intensity=0.5, bypass=True)
        self.assertEqual(result, expected)
        for ident in (10, 3):
            node(expected, ident)["effects"] = []
        self.assertEqual(mattes.edit_media(result, 10, mode="none"), expected)
        self.assertEqual(doc, original)

    def test_native_source_position_curve_keeps_group_clock_and_independent_geometry(self):
        doc = with_matte(2)
        node(doc, 3)["parameters"]["translation0"] = dict(
            type="double",
            defaultValue=-60.0,
            keyframes=[
                dict(
                    time=1411200000,
                    endTime=2822400000,
                    duration=1411200000,
                    value=60.0,
                    interp="linr",
                )
            ],
        )
        node(doc, 3)["animationTracks"] = dict(
            visual=[dict(endTime=2822400000, duration=1411200000, interp="linr")]
        )
        original = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        for ident in (10, 3):
            descriptor = node(expected, ident)["effects"][0]["parameters"]["intensity"]
            descriptor.pop("interp")
            descriptor.update(
                defaultValue=0.0,
                keyframes=[
                    dict(
                        time=1411200000,
                        endTime=2822400000,
                        duration=1411200000,
                        value=1.0,
                        interp="linr",
                    )
                ],
            )
        self.assertEqual(mattes.edit_intensity_curve(doc, 10, curve()), expected)
        self.assertEqual(doc, original)

    def test_all_nonlinear_codes_and_repeat_preserve_wrapper_video_and_ancestor_state(self):
        for easing, code in (
            ("linear", "linr"),
            ("exponential", "eioe"),
            ("bounce", "bnce"),
            ("spring", "sprg"),
        ):
            doc = fixture(2)
            expected = copy.deepcopy(doc)
            for ident in (10, 3):
                value = native_effect()
                descriptor = value["parameters"]["intensity"]
                descriptor.pop("interp")
                descriptor.update(
                    defaultValue=0.0,
                    keyframes=[
                        dict(
                            time=1411200000,
                            endTime=2822400000,
                            duration=1411200000,
                            value=1.0,
                            interp=code,
                        )
                    ],
                )
                node(expected, ident)["effects"] = [value]
            result = mattes.edit_intensity_curve(doc, 3, curve(easing))
            with self.subTest(easing=easing):
                self.assertEqual(result, expected)
            self.assertEqual(mattes.edit_intensity_curve(result, 10, curve(easing)), expected)

    def test_clear_retains_native_descriptors_intervals_cursor_audio_and_other_payload(self):
        doc = mattes.edit_intensity_curve(with_matte(2), 3, curve("spring"))
        node(doc, 3)["animationTracks"] = dict(
            visual=[dict(endTime=2822400000, duration=1411200000, interp="linr")]
        )
        expected = copy.deepcopy(doc)
        for ident in (10, 3):
            descriptor = node(expected, ident)["effects"][0]["parameters"]["intensity"]
            descriptor.pop("keyframes")
            descriptor["defaultValue"] = 0.5
        original = copy.deepcopy(doc)
        result = mattes.clear_intensity_curve(doc, 10, 0.5)
        self.assertEqual(result, expected)
        self.assertEqual(mattes.clear_intensity_curve(result, 3, 0.5), expected)
        self.assertEqual(doc, original)

    def test_composition_changes_only_selected_media_and_inner_group_track(self):
        doc = mattes.edit_intensity_curve(fixture(2), 3, curve())
        original = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        for ident in (10, 3):
            node(expected, ident)["effects"][0]["parameters"]["matteMode"] = 2
        node(expected, 100)["tracks"][1]["matte"] = 1
        settings = dict(
            schema_version=1,
            media=[dict(clipId=10, mode="alpha-invert")],
            tracks=[dict(track=1, groupId=100, mode="alpha")],
        )
        self.assertEqual(mattes.edit_composition(doc, settings), expected)
        self.assertEqual(doc, original)
        self.assertEqual(node(expected, 101)["tracks"][0]["matte"], 0)

    def test_composition_aliases_and_invalid_later_tracks_refuse_atomically(self):
        for media, tracks in (
            (
                [dict(clipId=10, mode="alpha"), dict(clipId=3, mode="alpha")],
                [dict(track=1, groupId=100, mode="alpha")],
            ),
            (
                [dict(clipId=10, mode="alpha")],
                [dict(track=1, groupId=100, mode="alpha"), dict(track=1, groupId=100, mode="none")],
            ),
            ([dict(clipId=10, mode="alpha")], [dict(track=1, groupId=999, mode="alpha")]),
        ):
            doc = fixture(2)
            original = copy.deepcopy(doc)
            with self.assertRaises(ValueError):
                mattes.edit_composition(doc, dict(schema_version=1, media=media, tracks=tracks))
            self.assertEqual(doc, original)

    def test_fresh_child_tokens_include_audio_and_preserve_independent_parent_tokens(self):
        doc = fixture()
        node(doc, 100)["effects"] = [dict(effectName="Parent", metadata=dict(effectIndex="99"))]
        node(doc, 11)["effects"] = [dict(effectName="Audio", metadata=dict(effectIndex="7"))]
        expected = copy.deepcopy(doc)
        for ident in (10, 3):
            value = native_effect()
            value["metadata"]["effectIndex"] = "8"
            node(expected, ident)["effects"] = [value]
        self.assertEqual(mattes.edit_media(doc, 10, mode="alpha"), expected)

    def test_other_containers_held_stitched_scenes_audio_and_clock_conflicts_refuse_every_path(
        self,
    ):
        for change in (
            "StitchedMedia",
            "UnifiedMedia",
            "Unknown",
            "held",
            "stitched",
            "scenes",
            "audio",
            "clock",
        ):
            doc = with_matte(2)
            if change == "held":
                node(doc, 3)["_type"] = "ScreenIMFile"
            elif change == "stitched":
                node(doc, 3)["_type"] = "StitchedMedia"
            elif change == "scenes":
                doc["timeline"]["sceneTrack"]["scenes"].append(dict(csml=dict(tracks=[])))
            elif change == "audio":
                node(doc, 11)["src"] = 99
            elif change == "clock":
                node(doc, 3)["mediaStart"] += 1
            else:
                node(doc, 101)["_type"] = change
            original = copy.deepcopy(doc)
            for action in (
                lambda: mattes.edit_media(doc, 10, mode="alpha"),
                lambda: mattes.edit_intensity_curve(doc, 3, curve()),
                lambda: mattes.clear_intensity_curve(doc, 10, 0),
            ):
                with self.subTest(change=change), self.assertRaises(ValueError):
                    action()
                self.assertEqual(doc, original)

    def test_missing_conflicting_and_duplicate_effect_mirrors_still_refuse(self):
        for change in ("missing", "controls", "duplicate", "token"):
            doc = with_matte()
            if change == "missing":
                node(doc, 3)["effects"] = []
            elif change == "controls":
                node(doc, 3)["effects"][0]["bypassed"] = True
            elif change == "duplicate":
                node(doc, 3)["effects"].append(native_effect())
            else:
                node(doc, 3)["effects"][0]["metadata"].pop("effectIndex")
            with self.subTest(change=change), self.assertRaises(ValueError):
                mattes.edit_media(doc, 10, intensity=0.5)

    def test_cli_curve_repeat_clear_and_input_preservation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, settings, output, cleared = [
                root / name for name in ("source.json", "spec.json", "curve.json", "clear.json")
            ]
            source.write_bytes(project.encode_document(fixture(2)))
            original = source.read_bytes()
            settings.write_text(json.dumps(curve("spring")))
            command = [
                "set-intensity-curve",
                str(source),
                "--clip-id",
                "3",
                "--curve",
                str(settings),
                "--output",
                str(output),
            ]
            for written in (True, False):
                with patch("sys.stdout", new_callable=io.StringIO) as stream:
                    self.assertEqual(mattes.main(command), 0)
                report = json.loads(stream.getvalue())
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
            with patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(
                    mattes.main(
                        [
                            "clear-intensity-curve",
                            str(output),
                            "--clip-id",
                            "10",
                            "--intensity",
                            "0.5",
                            "--output",
                            str(cleared),
                        ]
                    ),
                    0,
                )
            expected = mattes.clear_intensity_curve(
                mattes.edit_intensity_curve(fixture(2), 3, curve("spring")), 10, 0.5
            )
            self.assertEqual(project.load(cleared)[0], expected)
            self.assertEqual(source.read_bytes(), original)

    def test_cli_composition_failure_has_no_partial_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, settings, output = [
                root / name for name in ("source.json", "spec.json", "output.json")
            ]
            source.write_bytes(project.encode_document(fixture(2)))
            original = source.read_bytes()
            settings.write_text(
                json.dumps(
                    dict(
                        schema_version=1,
                        media=[dict(clipId=10, mode="alpha")],
                        tracks=[dict(groupId=100, track=99, mode="alpha")],
                    )
                )
            )
            with (
                patch("sys.stdout", new_callable=io.StringIO),
                patch("sys.stderr", new_callable=io.StringIO),
            ):
                self.assertEqual(
                    mattes.main(
                        [
                            "set-composition",
                            str(source),
                            "--spec",
                            str(settings),
                            "--output",
                            str(output),
                        ]
                    ),
                    1,
                )
            self.assertFalse(output.exists())
            self.assertEqual(source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
