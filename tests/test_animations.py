from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

from test_quizzes import document
import animations
import project


def fixture() -> dict:
    doc = document()
    visual(doc).update(
        start=0,
        duration=8000,
        mediaStart=0,
        mediaDuration=8000,
        scalar=1,
        effects=[],
        animationTracks={},
    )
    return doc


def visual(doc: dict) -> dict:
    node = project.scene_tracks(doc)[0][0]["medias"][0]
    return node["video"] if node["_type"] == "UnifiedMedia" else node


def spec(**changes: Any) -> dict:
    return {
        "schema_version": 1,
        "start": 3,
        "end": 4,
        "values": {"scale0": 1.25, "scale1": 1.25},
        "initial": {"scale0": 1, "scale1": 1},
        **changes,
    }


class AnimationTests(unittest.TestCase):
    def test_add_creates_the_fixed_native_parameter_and_interval_shapes(self) -> None:
        doc = fixture()
        result = animations.edit_interval(doc, 3, spec())
        self.assertEqual(
            visual(result)["parameters"],
            {
                name: {
                    "type": "double",
                    "defaultValue": 1.0,
                    "keyframes": [{"time": 3000, "endTime": 4000, "duration": 1000, "value": 1.25}],
                }
                for name in ("scale0", "scale1")
            },
        )
        self.assertEqual(
            visual(result)["animationTracks"], {"visual": [{"endTime": 4000, "duration": 1000}]}
        )
        self.assertEqual(doc, fixture())
        self.assertEqual(animations.edit_interval(result, 3, spec()), result)

    def test_all_five_easing_codes_belong_to_both_arrow_and_keyframes(self) -> None:
        for name, code in (
            ("auto", None),
            ("linear", "linr"),
            ("exponential", "eioe"),
            ("bounce", "bnce"),
            ("spring", "sprg"),
        ):
            with self.subTest(name=name):
                result = animations.edit_interval(fixture(), 3, spec(easing=name))
                owners = [
                    visual(result)["animationTracks"]["visual"][0],
                    *[p["keyframes"][0] for p in visual(result)["parameters"].values()],
                ]
                self.assertEqual([owner.get("interp") for owner in owners], [code, code, code])
                if code is None:
                    self.assertTrue(all("interp" not in owner for owner in owners))

    def test_easing_update_changes_every_matching_known_curve_and_keeps_other_intervals(
        self,
    ) -> None:
        doc = animations.edit_interval(fixture(), 3, spec(start=1, end=2, easing="bounce"))
        doc = animations.edit_interval(doc, 3, spec(easing="spring"))
        result = animations.edit_interval(
            doc, 3, {"schema_version": 1, "start": 3, "end": 4, "values": {}, "easing": "linear"}
        )
        for parameter in visual(result)["parameters"].values():
            self.assertEqual([f["interp"] for f in parameter["keyframes"]], ["bnce", "linr"])
        self.assertEqual(
            [f["interp"] for f in visual(result)["animationTracks"]["visual"]], ["bnce", "linr"]
        )

    def test_missing_initial_and_conflicting_existing_defaults_are_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "explicit initial"):
            animations.edit_interval(fixture(), 3, spec(initial={}))
        doc = fixture()
        visual(doc)["parameters"]["scale0"] = 2.0
        with self.assertRaisesRegex(ValueError, "existing initial"):
            animations.edit_interval(doc, 3, spec())

    def test_bare_parameters_promote_without_inferred_new_defaults(self) -> None:
        doc = fixture()
        visual(doc)["parameters"].update(scale0=0.5, scale1=0.5)
        result = animations.edit_interval(doc, 3, spec(initial={}))
        self.assertEqual(
            [p["defaultValue"] for p in visual(result)["parameters"].values()], [0.5, 0.5]
        )

    def test_typed_parameter_and_frame_opaque_data_survive_target_changes(self) -> None:
        doc = animations.edit_interval(fixture(), 3, spec(easing="bounce"))
        parameter = visual(doc)["parameters"]["scale0"]
        parameter.update(uiHints={"future": [1]}, future="retain")
        parameter["keyframes"][0]["future"] = {"keep": True}
        result = animations.edit_interval(doc, 3, spec(values={"scale0": 2}, initial={}))
        expected = copy.deepcopy(doc)
        visual(expected)["parameters"]["scale0"]["keyframes"][0]["value"] = 2.0
        self.assertEqual(result, expected)

    def test_new_property_inherits_existing_interval_interpolation(self) -> None:
        doc = animations.edit_interval(fixture(), 3, spec(easing="spring"))
        result = animations.edit_interval(
            doc, 3, spec(values={"opacity": 0}, initial={"opacity": 1})
        )
        self.assertEqual(visual(result)["parameters"]["opacity"]["keyframes"][0]["interp"], "sprg")

    def test_multiple_intervals_preserve_order_and_other_parameter_curves(self) -> None:
        doc = animations.edit_interval(fixture(), 3, spec())
        result = animations.edit_interval(
            doc, 3, spec(start=1, end=2, values={"scale0": 1.5}, initial={})
        )
        self.assertEqual(
            [p["endTime"] for p in visual(result)["animationTracks"]["visual"]], [2000, 4000]
        )
        self.assertEqual(
            [p["value"] for p in visual(result)["parameters"]["scale0"]["keyframes"]], [1.5, 1.25]
        )
        self.assertEqual(
            visual(result)["parameters"]["scale1"], visual(doc)["parameters"]["scale1"]
        )

    def test_source_position_clock_ignores_parent_placement_and_audio_rate(self) -> None:
        doc = fixture()
        visual(doc).update(mediaStart=1000, scalar="2/3", start=99000)
        result = animations.edit_interval(doc, 3, spec(start=2, end=3))
        self.assertEqual(
            visual(result)["animationTracks"]["visual"], [{"endTime": 5500, "duration": 1500}]
        )
        frame = visual(result)["parameters"]["scale0"]["keyframes"][0]
        self.assertEqual((frame["time"], frame["endTime"], frame["duration"]), (4000, 5500, 1500))

    def test_negative_bounds_and_subframe_positions_are_not_rounded_or_clamped(self) -> None:
        doc = fixture()
        doc["editRate"] = 30000
        result = animations.edit_interval(doc, 3, spec(start="-23/30", end="7/30"))
        frame = visual(result)["parameters"]["scale0"]["keyframes"][0]
        self.assertEqual(
            (frame["time"], frame["endTime"], frame["duration"]), (-23000, 7000, 30000)
        )
        with self.assertRaisesRegex(ValueError, "exact native"):
            animations.edit_interval(fixture(), 3, spec(start="1/3000"))

    def test_partial_overlap_and_duplicate_intervals_refuse_without_input_mutation(self) -> None:
        original = animations.edit_interval(fixture(), 3, spec())
        for bounds in ((2, 3.5), (3.5, 5)):
            doc = copy.deepcopy(original)
            with self.subTest(bounds=bounds), self.assertRaisesRegex(ValueError, "nonoverlapping"):
                animations.edit_interval(doc, 3, spec(start=bounds[0], end=bounds[1]))
            self.assertEqual(doc, original)
        doc = copy.deepcopy(original)
        visual(doc)["animationTracks"]["visual"] *= 2
        with self.assertRaisesRegex(ValueError, "unique"):
            animations.edit_interval(doc, 3, spec())

    def test_invalid_specs_and_unknown_properties_are_refused(self) -> None:
        for payload in (
            {},
            {**spec(), "schema_version": True},
            {**spec(), "schema_version": 2},
            {**spec(), "extra": 1},
            spec(values={"invented": 3}),
            spec(initial={"opacity": 1}),
            spec(parameterEasing={"opacity": "linear"}),
            spec(values=[]),
            spec(start=True),
            spec(start=4, end=3),
            spec(easing="invented"),
            spec(values={}, initial={}),
        ):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                animations.edit_interval(fixture(), 3, payload)
        with self.assertRaisesRegex(ValueError, "existing interval"):
            animations.edit_interval(fixture(), 3, spec(values={}, initial={}, easing="linear"))

    def test_unsupported_owner_and_build_leave_data_unchanged(self) -> None:
        for kind in ("FutureMedia", "PlaceholderMedia", "AMFile"):
            doc = fixture()
            visual(doc)["_type"] = kind
            frozen = copy.deepcopy(doc)
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                animations.edit_interval(doc, 3, spec())
            self.assertEqual(doc, frozen)
        doc = fixture()
        doc["authoringClientName"]["version"] = "2025.0.3"
        with self.assertRaises(ValueError):
            animations.edit_interval(doc, 3, spec())

    def test_unknown_and_effect_owned_coupled_curves_block_global_easing(self) -> None:
        for effect_owned in (False, True):
            doc = animations.edit_interval(fixture(), 3, spec())
            curve = {
                "type": "double",
                "defaultValue": 1,
                "keyframes": [{"time": 3000, "endTime": 4000, "duration": 1000, "value": 0.5}],
            }
            if effect_owned:
                visual(doc)["effects"] = [
                    {"effectName": "MediaMatte", "parameters": {"intensity": curve}}
                ]
            else:
                visual(doc)["parameters"]["future"] = curve
            frozen = copy.deepcopy(doc)
            with (
                self.subTest(effect_owned=effect_owned),
                self.assertRaisesRegex(ValueError, "coupled|effect-owned"),
            ):
                animations.edit_interval(doc, 3, spec(easing="linear"))
            self.assertEqual(doc, frozen)

    def test_independent_point_cues_survive_an_easing_change(self) -> None:
        doc = animations.edit_interval(fixture(), 3, spec())
        cue = {
            "type": "string",
            "keyframes": [{"time": 3500, "endTime": 3500, "duration": 0, "value": "retain"}],
        }
        visual(doc)["parameters"]["toc"] = copy.deepcopy(cue)
        visual(doc)["effects"] = [{"parameters": {"point": copy.deepcopy(cue)}}]
        result = animations.edit_interval(doc, 3, spec(easing="bounce"))
        self.assertEqual(visual(result)["parameters"]["toc"], cue)
        self.assertEqual(visual(result)["effects"], visual(doc)["effects"])

    def test_parameter_level_interpolation_is_explicit_and_survives_auto(self) -> None:
        doc = fixture()
        visual(doc)["_type"] = "ScreenVMFile"
        result = animations.edit_interval(
            doc, 3, spec(parameterEasing={"scale0": "exponential", "scale1": "exponential"})
        )
        changed = animations.edit_interval(result, 3, spec(easing="auto"))
        for parameter in visual(changed)["parameters"].values():
            self.assertEqual(parameter["interp"], "eioe")
            self.assertNotIn("interp", parameter["keyframes"][0])
        self.assertNotIn("interp", visual(changed)["animationTracks"]["visual"][0])

    def test_malformed_parameter_and_frame_shapes_are_refused(self) -> None:
        for value in (
            {"type": "point", "defaultValue": [0, 0]},
            {"type": "double", "defaultValue": 1, "keyframes": "bad"},
            {
                "type": "double",
                "defaultValue": 1,
                "keyframes": [{"time": 2, "endTime": 4, "duration": 1, "value": 1}],
            },
            {
                "type": "double",
                "defaultValue": 1,
                "keyframes": [{"time": 3200, "endTime": 4200, "duration": 1000, "value": 1}],
            },
        ):
            doc = fixture()
            visual(doc)["parameters"]["scale0"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                animations.edit_interval(doc, 3, spec())

    def test_opacity_and_nonfinite_values_refuse_before_staging(self) -> None:
        for value in (-0.1, 1.1, True, "nan", "inf", "1e1000"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                animations.edit_interval(
                    fixture(), 3, spec(values={"opacity": value}, initial={"opacity": 1})
                )

    def test_linked_ids_edit_only_video_and_preserve_audio_wrapper_effects(self) -> None:
        doc = fixture()
        child = visual(doc)
        wrapper = {
            "id": 10,
            "_type": "UnifiedMedia",
            "video": child,
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
        result = animations.edit_interval(doc, 10, spec())
        self.assertEqual(result, animations.edit_interval(doc, 3, spec()))
        after = project.scene_tracks(result)[0][0]["medias"][0]
        self.assertEqual(after["audio"], wrapper["audio"])
        self.assertEqual(after["effects"], wrapper["effects"])
        self.assertNotIn("parameters", after)
        self.assertNotIn("animationTracks", after)

    def test_inspection_reports_physical_owner_and_does_not_restrict_reading(self) -> None:
        doc = animations.edit_interval(fixture(), 3, spec())
        visual(doc)["_type"] = "Callout"
        report = animations.inventory(doc)
        self.assertEqual(
            (report[0]["clipId"], report[0]["type"], len(report[0]["visualIntervals"])),
            (3, "Callout", 1),
        )
        visual(doc)["animationTracks"] = []
        with self.assertRaisesRegex(ValueError, "malformed"):
            animations.inventory(doc)

    def test_cli_stages_and_changes_easing_with_unchanged_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, payload, output, eased = [
                root / name
                for name in ("project.json", "spec.json", "candidate.json", "eased.json")
            ]
            source.write_bytes(project.encode_document(fixture()))
            payload.write_text(json.dumps(spec()))
            original = source.read_bytes()
            for written in (True, False):
                stream = io.StringIO()
                with patch("sys.stdout", stream):
                    self.assertEqual(
                        animations.main(
                            [
                                "set-interval",
                                str(source),
                                "--clip-id",
                                "3",
                                "--spec",
                                str(payload),
                                "--output",
                                str(output),
                            ]
                        ),
                        0,
                    )
                self.assertEqual(
                    (
                        json.loads(stream.getvalue())["written"],
                        json.loads(stream.getvalue())["nativeVerified"],
                    ),
                    (written, False),
                )
            with patch("sys.stdout", io.StringIO()):
                self.assertEqual(
                    animations.main(
                        [
                            "ease-interval",
                            str(output),
                            "--clip-id",
                            "3",
                            "--start",
                            "3",
                            "--end",
                            "4",
                            "--easing",
                            "bounce",
                            "--output",
                            str(eased),
                        ]
                    ),
                    0,
                )
            self.assertEqual(
                visual(json.loads(eased.read_text()))["animationTracks"]["visual"][0]["interp"],
                "bnce",
            )
            self.assertEqual(source.read_bytes(), original)
            with patch("sys.stderr", io.StringIO()):
                self.assertEqual(
                    animations.main(
                        [
                            "set-interval",
                            str(source),
                            "--clip-id",
                            "3",
                            "--spec",
                            str(payload),
                            "--output",
                            str(eased),
                        ]
                    ),
                    1,
                )


if __name__ == "__main__":
    unittest.main()
