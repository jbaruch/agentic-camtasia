from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_animations import fixture, visual
import animations
import project


def removal_fixture() -> dict:
    """Fixed native-shaped oracle, independent of the interval authoring helper."""
    doc = fixture()
    visual(doc)["parameters"] = {
        "scale0": {
            "type": "double",
            "defaultValue": 1.0,
            "keyframes": [{"time": 3000, "endTime": 4000, "duration": 1000, "value": 1.25}],
        },
        "scale1": {
            "type": "double",
            "defaultValue": 1.0,
            "keyframes": [{"time": 3000, "endTime": 4000, "duration": 1000, "value": 1.25}],
        },
        "geometryCrop0": 0.0,
        "geometryCrop1": 0.0,
        "geometryCrop2": 0.0,
        "geometryCrop3": 0.0,
    }
    visual(doc)["animationTracks"] = {"visual": [{"endTime": 4000, "duration": 1000}]}
    return doc


class AnimationRemovalTests(unittest.TestCase):
    def test_recording_owner_keeps_stream_binding_and_recorded_cursor_data(self):
        doc = removal_fixture()
        visual(doc).update(_type="ScreenVMFile", src=9, trackNumber=2)
        visual(doc)["parameters"]["cursorScale"] = 5.0
        result = animations.remove_interval(doc, 3, 3, 4)
        owner = visual(result)
        self.assertEqual(
            (owner["_type"], owner["src"], owner["trackNumber"]), ("ScreenVMFile", 9, 2)
        )
        self.assertEqual(owner["parameters"]["cursorScale"], 5.0)
        self.assertEqual(owner["animationTracks"], {})

    def test_single_removal_restores_native_defaults_and_preserves_whole_document(self):
        doc = removal_fixture()
        before = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        visual(expected)["parameters"] = {
            "geometryCrop0": 0.0,
            "geometryCrop1": 0.0,
            "geometryCrop2": 0.0,
            "geometryCrop3": 0.0,
        }
        visual(expected)["animationTracks"] = {}
        actual = animations.remove_interval(doc, 3, 3, 4)
        self.assertEqual(actual, expected)
        self.assertEqual(doc, before)
        self.assertEqual(animations.remove_interval(actual, 3, 3, 4), actual)

    def test_last_frame_preserves_nondefault_initial_values_across_all_known_properties(self):
        doc = removal_fixture()
        initial = {
            "scale0": 0.625,
            "scale1": 0.625,
            "opacity": 0.8,
            "translation0": 15.0,
            "translation1": -10.0,
            "rotation1": 0.1,
            "geometryCrop0": 1.0,
            "geometryCrop1": 2.0,
            "geometryCrop2": 3.0,
            "geometryCrop3": 4.0,
        }
        visual(doc)["parameters"] = {
            key: {
                "type": "double",
                "defaultValue": value,
                "keyframes": [{"time": 3000, "endTime": 4000, "duration": 1000, "value": 0.5}],
            }
            for key, value in initial.items()
        }
        actual = animations.remove_interval(doc, 3, 3, 4)
        self.assertEqual(visual(actual)["parameters"], initial)

    def test_native_zero_crop_parameters_survive_while_other_default_fields_disappear(self):
        doc = removal_fixture()
        values = {
            "scale0": 1.0,
            "scale1": 1.0,
            "opacity": 1.0,
            "translation0": 0.0,
            "translation1": 0.0,
            "rotation1": 0.0,
            "geometryCrop0": 0.0,
            "geometryCrop1": 0.0,
            "geometryCrop2": 0.0,
            "geometryCrop3": 0.0,
        }
        visual(doc)["parameters"] = {
            key: {
                "type": "double",
                "defaultValue": value,
                "keyframes": [{"time": 3000, "endTime": 4000, "duration": 1000, "value": 0.5}],
            }
            for key, value in values.items()
        }
        self.assertEqual(
            visual(animations.remove_interval(doc, 3, 3, 4))["parameters"],
            {
                "geometryCrop0": 0.0,
                "geometryCrop1": 0.0,
                "geometryCrop2": 0.0,
                "geometryCrop3": 0.0,
            },
        )

    def test_removing_first_middle_or_last_interval_preserves_every_other_frame(self):
        for start, end in [(1, 2), (3, 4), (5, 6)]:
            doc = removal_fixture()
            v = visual(doc)
            v["animationTracks"]["visual"] = [
                {"endTime": 2000, "duration": 1000, "interp": "linr", "future": 1},
                {"endTime": 4000, "duration": 1000, "interp": "bnce"},
                {"endTime": 6000, "duration": 1000, "interp": "sprg"},
            ]
            for name in ["scale0", "scale1"]:
                v["parameters"][name]["keyframes"] = [
                    {
                        "time": 1000,
                        "endTime": 2000,
                        "duration": 1000,
                        "value": 1.25,
                        "future": "retain",
                    },
                    {"time": 3000, "endTime": 4000, "duration": 1000, "value": 0.8},
                    {"time": 5000, "endTime": 6000, "duration": 1000, "value": 1.5},
                ]
            expected = copy.deepcopy(doc)
            ev = visual(expected)
            ev["animationTracks"]["visual"] = [
                f for f in ev["animationTracks"]["visual"] if f["endTime"] != end * 1000
            ]
            for name in ["scale0", "scale1"]:
                ev["parameters"][name]["keyframes"] = [
                    f for f in ev["parameters"][name]["keyframes"] if f["endTime"] != end * 1000
                ]
            with self.subTest(start=start):
                self.assertEqual(animations.remove_interval(doc, 3, start, end), expected)

    def test_parameter_interpolation_and_opaque_fields_survive_last_frame_removal(self):
        doc = removal_fixture()
        p = visual(doc)["parameters"]["scale0"]
        p.update(interp="eioe", uiHints={"future": True}, future=[1, 2])
        expected = {k: v for k, v in p.items() if k != "keyframes"}
        result = animations.remove_interval(doc, 3, 3, 4)
        self.assertEqual(visual(result)["parameters"]["scale0"], expected)

    def test_other_animation_track_and_independent_point_cues_are_preserved(self):
        doc = removal_fixture()
        cue = {
            "type": "string",
            "keyframes": [{"time": 3500, "endTime": 3500, "duration": 0, "value": "keep"}],
        }
        v = visual(doc)
        v["parameters"]["toc"] = copy.deepcopy(cue)
        v["animationTracks"]["future"] = [{"value": "keep"}]
        v["effects"] = [{"parameters": {"point": copy.deepcopy(cue)}}]
        actual = animations.remove_interval(doc, 3, 3, 4)
        self.assertEqual(visual(actual)["parameters"]["toc"], cue)
        self.assertEqual(visual(actual)["animationTracks"], {"future": [{"value": "keep"}]})
        self.assertEqual(visual(actual)["effects"], v["effects"])

    def test_retimed_selection_maps_clip_relative_time_to_exact_source_ticks(self):
        doc = removal_fixture()
        v = visual(doc)
        v.update(mediaStart=1000, scalar="2/3", start=99000)
        v["animationTracks"] = {"visual": [{"endTime": 5500, "duration": 1500}]}
        for name in ["scale0", "scale1"]:
            v["parameters"][name]["keyframes"] = [
                {"time": 4000, "endTime": 5500, "duration": 1500, "value": 1.25}
            ]
        result = animations.remove_interval(doc, 3, 2, 3)
        self.assertEqual(visual(result)["animationTracks"], {})
        self.assertNotIn("scale0", visual(result)["parameters"])
        self.assertEqual(visual(result)["mediaStart"], 1000)
        self.assertEqual(visual(result)["start"], 99000)

    def test_negative_animation_bounds_are_not_clipped_to_visible_media(self):
        doc = removal_fixture()
        doc["editRate"] = 30000
        v = visual(doc)
        v["animationTracks"] = {"visual": [{"endTime": 7000, "duration": 30000}]}
        for name in ["scale0", "scale1"]:
            v["parameters"][name]["keyframes"] = [
                {"time": -23000, "endTime": 7000, "duration": 30000, "value": 1.25}
            ]
        self.assertEqual(
            visual(animations.remove_interval(doc, 3, "-23/30", "7/30"))["animationTracks"], {}
        )

    def test_missing_interval_with_orphaned_frames_refuses_instead_of_silent_noop(self):
        doc = removal_fixture()
        visual(doc)["animationTracks"] = {}
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "orphaned"):
            animations.remove_interval(doc, 3, 3, 4)
        self.assertEqual(doc, before)

    def test_unknown_and_effect_owned_coupled_curves_refuse_without_mutation(self):
        for effect in [False, True]:
            doc = removal_fixture()
            v = visual(doc)
            curve = copy.deepcopy(v["parameters"]["scale0"])
            if effect:
                v["effects"] = [{"effectName": "MediaMatte", "parameters": {"intensity": curve}}]
            else:
                v["parameters"]["future"] = curve
            before = copy.deepcopy(doc)
            with self.subTest(effect=effect), self.assertRaisesRegex(ValueError, "coupled"):
                animations.remove_interval(doc, 3, 3, 4)
            self.assertEqual(doc, before)

    def test_duplicate_overlapping_or_malformed_intervals_refuse(self):
        for extra in [
            {"endTime": 4000, "duration": 1000},
            {"endTime": 4500, "duration": 1000},
            {"endTime": 4000, "duration": 0},
        ]:
            doc = removal_fixture()
            visual(doc)["animationTracks"]["visual"].append(extra)
            before = copy.deepcopy(doc)
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                animations.remove_interval(doc, 3, 3, 4)
            self.assertEqual(doc, before)

    def test_geometry_point_frames_and_overlapping_frames_refuse(self):
        for extra in [
            {"time": 3500, "endTime": 3500, "duration": 0, "value": 1},
            {"time": 3500, "endTime": 4500, "duration": 1000, "value": 1},
            {"time": 3000, "endTime": 4000, "duration": 1000, "value": 1.5},
        ]:
            doc = removal_fixture()
            visual(doc)["parameters"]["scale0"]["keyframes"].append(extra)
            before = copy.deepcopy(doc)
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                animations.remove_interval(doc, 3, 3, 4)
            self.assertEqual(doc, before)

    def test_linked_wrapper_audio_sources_and_unrelated_effects_survive(self):
        doc = removal_fixture()
        v = visual(doc)
        wrapper = {
            "id": 10,
            "_type": "UnifiedMedia",
            "video": v,
            "audio": {
                "id": 11,
                "_type": "AMFile",
                "parameters": {"volume": 0.8},
                "effects": [{"effectName": "AudioNoiseRemoval"}],
            },
            "effects": [{"effectName": "Border"}],
            "metadata": {"keep": "wrapper"},
        }
        project.scene_tracks(doc)[0][0]["medias"] = [wrapper]
        result = animations.remove_interval(doc, 10, 3, 4)
        self.assertEqual(result, animations.remove_interval(doc, 3, 3, 4))
        after = project.scene_tracks(result)[0][0]["medias"][0]
        self.assertEqual(after["audio"], wrapper["audio"])
        self.assertEqual(after["effects"], wrapper["effects"])
        self.assertEqual(result.get("sourceBin"), doc.get("sourceBin"))

    def test_unsupported_owner_build_and_inexact_or_reversed_bounds_refuse(self):
        for kind in ["FutureMedia", "PlaceholderMedia", "AMFile"]:
            doc = removal_fixture()
            visual(doc)["_type"] = kind
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                animations.remove_interval(doc, 3, 3, 4)
        doc = removal_fixture()
        doc["version"] = "9.0"
        with self.assertRaises(ValueError):
            animations.remove_interval(doc, 3, 3, 4)
        for start, end in [(4, 3), (3, 3), ("1/3000", 4), (True, 4)]:
            with self.subTest(start=start), self.assertRaises(ValueError):
                animations.remove_interval(removal_fixture(), 3, start, end)

    def test_cli_stages_once_retains_original_and_reports_absent_interval_as_no_change(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, out, noop = [root / n for n in ["source.json", "removed.json", "noop.json"]]
            raw = project.encode_document(removal_fixture())
            source.write_bytes(raw)
            for written in [True, False]:
                stream = io.StringIO()
                with patch("sys.stdout", stream):
                    self.assertEqual(
                        animations.main(
                            [
                                "remove-interval",
                                str(source),
                                "--clip-id",
                                "3",
                                "--start",
                                "3",
                                "--end",
                                "4",
                                "--output",
                                str(out),
                            ]
                        ),
                        0,
                    )
                result = json.loads(stream.getvalue())
                self.assertEqual(
                    (result["written"], result["changed"], result["nativeVerified"]),
                    (written, True, False),
                )
            stream = io.StringIO()
            with patch("sys.stdout", stream):
                self.assertEqual(
                    animations.main(
                        [
                            "remove-interval",
                            str(out),
                            "--clip-id",
                            "3",
                            "--start",
                            "3",
                            "--end",
                            "4",
                            "--output",
                            str(noop),
                        ]
                    ),
                    0,
                )
            self.assertFalse(json.loads(stream.getvalue())["changed"])
            self.assertEqual(source.read_bytes(), raw)
            with patch("sys.stderr", io.StringIO()):
                self.assertEqual(
                    animations.main(
                        [
                            "remove-interval",
                            str(source),
                            "--clip-id",
                            "3",
                            "--start",
                            "3",
                            "--end",
                            "4",
                            "--output",
                            str(source),
                        ]
                    ),
                    1,
                )
            self.assertEqual(source.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
