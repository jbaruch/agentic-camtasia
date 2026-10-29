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
import mattes
import project


def fixture() -> dict:
    doc = document()
    doc["timeline"]["trackAttributes"] = [{"matte": 0, "metadata": {"future": "keep"}}]
    project.scene_tracks(doc)[0][0]["medias"] = [
        {
            "id": 3,
            "_type": "Callout",
            "effects": [],
            "parameters": {},
            "def": {"shape": "shape-ellipse", "fill-style": "solid"},
            "opaque": ["retain"],
        }
    ]
    return doc


def clip(doc: dict) -> dict:
    return project.scene_tracks(doc)[0][0]["medias"][0]


def linked_fixture() -> dict:
    doc = fixture()
    wrapper = {
        "id": 3,
        "_type": "UnifiedMedia",
        "effects": [],
        "metadata": {"future": "wrapper"},
        "video": {"id": 4, "_type": "VMFile", "effects": [], "parameters": {"future": "video"}},
        "audio": {
            "id": 5,
            "_type": "AMFile",
            "effects": [],
            "parameters": {"volume": 0.7},
            "metadata": {"future": "audio"},
        },
    }
    project.scene_tracks(doc)[0][0]["medias"] = [wrapper]
    return doc


def curve_spec() -> dict:
    return {
        "schema_version": 1,
        "defaultValue": 0,
        "segments": [
            {"start": "1/2", "end": "3/2", "value": 1},
            {"start": 2, "end": "11/4", "value": 0},
        ],
    }


def curve_fixture(linked: bool = False) -> dict:
    doc = linked_fixture() if linked else fixture()
    clip(doc).update(mediaStart=0, scalar=1)
    if linked:
        clip(doc)["video"].update(mediaStart=0, scalar=1)
    return doc


class MatteCurveTests(unittest.TestCase):
    def test_bare_native_intensity_promotes_to_the_observed_typed_curve(self) -> None:
        doc = mattes.edit_media(curve_fixture(), 3, mode="alpha")
        clip(doc)["effects"][0]["parameters"]["intensity"] = 0.6
        result = mattes.edit_intensity_curve(doc, 3, curve_spec())
        parameter = clip(result)["effects"][0]["parameters"]["intensity"]
        self.assertEqual(parameter["type"], "double")
        self.assertEqual(parameter["defaultValue"], 0.0)
        self.assertEqual(parameter["uiHints"], {"userInterfaceType": 0, "unitType": 0})
        self.assertEqual([f["value"] for f in parameter["keyframes"]], [1.0, 0.0])
        self.assertEqual(clip(doc)["effects"][0]["parameters"]["intensity"], 0.6)

    def test_linear_segments_have_fixed_native_bounds_and_defaults(self) -> None:
        doc = curve_fixture()
        result = mattes.edit_intensity_curve(doc, 3, curve_spec())
        self.assertEqual(
            clip(result)["effects"][0]["parameters"]["intensity"],
            {
                "type": "double",
                "defaultValue": 0.0,
                "uiHints": {"userInterfaceType": 0, "unitType": 0},
                "keyframes": [
                    {
                        "time": 500,
                        "endTime": 1500,
                        "duration": 1000,
                        "value": 1.0,
                        "interp": "linr",
                    },
                    {
                        "time": 2000,
                        "endTime": 2750,
                        "duration": 750,
                        "value": 0.0,
                        "interp": "linr",
                    },
                ],
            },
        )
        self.assertEqual(doc, curve_fixture())
        self.assertEqual(mattes.edit_intensity_curve(result, 3, curve_spec()), result)

    def test_retimed_clock_uses_source_positions_in_project_ticks(self) -> None:
        doc = curve_fixture()
        clip(doc).update(mediaStart=2000, scalar="1/2", start=9000)
        result = mattes.edit_intensity_curve(doc, 3, curve_spec())
        frames = clip(result)["effects"][0]["parameters"]["intensity"]["keyframes"]
        self.assertEqual(
            [(f["time"], f["endTime"], f["duration"]) for f in frames],
            [(3000, 5000, 2000), (6000, 7500, 1500)],
        )

    def test_negative_local_bounds_remain_exact_and_are_never_clamped(self) -> None:
        spec = {
            "schema_version": 1,
            "defaultValue": "1/4",
            "segments": [{"start": -1, "end": 0, "value": "3/4"}],
        }
        result = mattes.edit_intensity_curve(curve_fixture(), 3, spec)
        parameter = clip(result)["effects"][0]["parameters"]["intensity"]
        self.assertEqual(parameter["defaultValue"], 0.25)
        self.assertEqual(
            parameter["keyframes"],
            [{"time": -1000, "endTime": 0, "duration": 1000, "value": 0.75, "interp": "linr"}],
        )

    def test_linked_animation_mirrors_visuals_without_changing_audio_or_aliasing(self) -> None:
        doc = curve_fixture(True)
        result = mattes.edit_intensity_curve(doc, 3, curve_spec())
        self.assertEqual(clip(result)["effects"], clip(result)["video"]["effects"])
        self.assertEqual(clip(result)["audio"], clip(doc)["audio"])
        self.assertEqual(result, mattes.edit_intensity_curve(doc, 4, curve_spec()))
        clip(result)["effects"][0]["parameters"]["intensity"]["keyframes"][0]["value"] = 0.1
        self.assertEqual(
            clip(result)["video"]["effects"][0]["parameters"]["intensity"]["keyframes"][0]["value"],
            1.0,
        )

    def test_conflicting_linked_clocks_are_refused_without_mutation(self) -> None:
        for field, value in (("scalar", "1/2"), ("mediaStart", 1000)):
            doc = curve_fixture(True)
            clip(doc)["video"][field] = value
            frozen = copy.deepcopy(doc)
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "source clocks"):
                mattes.edit_intensity_curve(doc, 3, curve_spec())
            self.assertEqual(doc, frozen)

    def test_existing_controls_opaque_state_and_other_animations_survive(self) -> None:
        doc = mattes.edit_media(
            curve_fixture(), 3, mode="luminosity-invert", bypass=True, ease_in=1
        )
        effect = clip(doc)["effects"][0]
        effect["parameters"]["intensity"]["future"] = ["keep"]
        effect["metadata"] = {"future": "keep"}
        clip(doc)["animationTracks"] = {"visual": [{"endTime": 4000, "duration": 1000}]}
        clip(doc)["parameters"]["opacity"] = {
            "type": "double",
            "defaultValue": 1,
            "keyframes": [{"time": 3000, "endTime": 4000, "duration": 1000, "value": 0.5}],
        }
        result = mattes.edit_intensity_curve(doc, 3, curve_spec())
        expected = copy.deepcopy(doc)
        expected_parameter = expected["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0][
            "medias"
        ][0]["effects"][0]["parameters"]["intensity"]
        expected_parameter.pop("interp")
        expected_parameter.update(
            defaultValue=0.0,
            keyframes=[
                {"time": 500, "endTime": 1500, "duration": 1000, "value": 1.0, "interp": "linr"},
                {"time": 2000, "endTime": 2750, "duration": 750, "value": 0.0, "interp": "linr"},
            ],
        )
        self.assertEqual(result, expected)

    def test_clear_removes_only_intensity_keyframes_and_keeps_visual_intervals(self) -> None:
        doc = mattes.edit_intensity_curve(curve_fixture(), 3, curve_spec())
        clip(doc)["animationTracks"] = {"visual": [{"endTime": 1500, "duration": 1000}]}
        result = mattes.clear_intensity_curve(doc, 3, "3/4")
        expected = copy.deepcopy(doc)
        parameter = clip(expected)["effects"][0]["parameters"]["intensity"]
        parameter.pop("keyframes")
        parameter["defaultValue"] = 0.75
        self.assertEqual(result, expected)
        self.assertEqual(mattes.clear_intensity_curve(result, 3, "3/4"), result)
        with self.assertRaisesRegex(ValueError, "animated"):
            mattes.edit_media(doc, 3, intensity=0.75)

    def test_clear_keeps_linked_mirrors_and_other_effects(self) -> None:
        doc = mattes.edit_intensity_curve(curve_fixture(True), 3, curve_spec())
        for target in (clip(doc), clip(doc)["video"]):
            target["effects"].append({"effectName": "Border", "metadata": {"effectIndex": "1"}})
        result = mattes.clear_intensity_curve(doc, 4, 0.5)
        self.assertEqual(clip(result)["effects"], clip(result)["video"]["effects"])
        self.assertEqual(clip(result)["effects"][1], clip(doc)["effects"][1])
        self.assertEqual(clip(result)["audio"], clip(doc)["audio"])

    def test_bad_specs_segment_order_bounds_and_values_are_refused(self) -> None:
        specs = [
            {},
            {**curve_spec(), "schema_version": True},
            {**curve_spec(), "schema_version": 2},
            {**curve_spec(), "future": 1},
            {**curve_spec(), "defaultValue": True},
            {**curve_spec(), "segments": []},
            {**curve_spec(), "segments": "curve"},
        ]
        for segment in (
            {"start": 1, "end": 1, "value": 1},
            {"start": 2, "end": 1, "value": 1},
            {"start": True, "end": 2, "value": 1},
            {"start": 1, "end": 2, "value": 2},
            {"start": "nan", "end": 2, "value": 1},
            {"start": 1, "end": 2, "value": 1, "future": 0},
        ):
            specs.append({**curve_spec(), "segments": [segment]})
        specs.append({**curve_spec(), "segments": list(reversed(curve_spec()["segments"]))})
        specs.append(
            {
                **curve_spec(),
                "segments": [
                    {"start": 0, "end": 2, "value": 1},
                    {"start": 1, "end": 3, "value": 0},
                ],
            }
        )
        for spec in specs:
            doc = curve_fixture()
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                mattes.edit_intensity_curve(doc, 3, spec)
            self.assertEqual(doc, curve_fixture())

    def test_fractional_ticks_and_invalid_source_clocks_are_refused(self) -> None:
        spec = {**curve_spec(), "segments": [{"start": "1/3000", "end": 1, "value": 1}]}
        with self.assertRaisesRegex(ValueError, "exact native"):
            mattes.edit_intensity_curve(curve_fixture(), 3, spec)
        for field, value in (("editRate", 0), ("scalar", 0), ("scalar", "-1/2")):
            doc = curve_fixture()
            (doc if field == "editRate" else clip(doc))[field] = value
            with self.subTest(field=field, value=value), self.assertRaises(ValueError):
                mattes.edit_intensity_curve(doc, 3, curve_spec())

    def test_clear_absent_or_unfamiliar_intensity_is_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "existing media matte"):
            mattes.clear_intensity_curve(curve_fixture(), 3, 1)
        for field, value in (
            ("category", "unknown"),
            ("intensity", {"type": "point"}),
            ("intensity", "unknown"),
        ):
            doc = mattes.edit_media(curve_fixture(), 3, mode="alpha")
            effect = clip(doc)["effects"][0]
            (effect if field == "category" else effect["parameters"])[field] = value
            for operation in (
                lambda: mattes.edit_intensity_curve(doc, 3, curve_spec()),
                lambda: mattes.clear_intensity_curve(doc, 3, 1),
            ):
                with self.subTest(field=field), self.assertRaises(ValueError):
                    operation()

    def test_cli_sets_and_clears_a_curve_without_touching_inputs(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, spec, output, cleared = [
                root / name
                for name in ("project.json", "curve.json", "candidate.json", "cleared.json")
            ]
            source.write_bytes(project.encode_document(curve_fixture()))
            spec.write_text(json.dumps(curve_spec()))
            original = (source.read_bytes(), spec.read_bytes())
            with patch("sys.stdout", io.StringIO()):
                self.assertEqual(
                    mattes.main(
                        [
                            "set-intensity-curve",
                            str(source),
                            "--clip-id",
                            "3",
                            "--curve",
                            str(spec),
                            "--output",
                            str(output),
                        ]
                    ),
                    0,
                )
                self.assertEqual(
                    mattes.main(
                        [
                            "clear-intensity-curve",
                            str(output),
                            "--clip-id",
                            "3",
                            "--intensity",
                            "1/2",
                            "--output",
                            str(cleared),
                        ]
                    ),
                    0,
                )
            parameter = clip(json.loads(cleared.read_text()))["effects"][0]["parameters"][
                "intensity"
            ]
            self.assertNotIn("keyframes", parameter)
            self.assertEqual(parameter["defaultValue"], 0.5)
            self.assertEqual((source.read_bytes(), spec.read_bytes()), original)


class MatteTests(unittest.TestCase):
    def test_factory_constructor_supports_video_image_and_group_without_flattening(self) -> None:
        for kind in ("VMFile", "IMFile", "Group"):
            with self.subTest(kind=kind):
                doc = fixture()
                clip(doc)["_type"] = kind
                if kind == "Group":
                    clip(doc)["tracks"] = [{"trackIndex": 0, "medias": [], "matte": 0}]
                result = mattes.edit_media(doc, 3, mode="alpha")
                effect = clip(result)["effects"].pop()
                self.assertEqual(
                    effect["parameters"]["intensity"],
                    {
                        "type": "double",
                        "defaultValue": 1.0,
                        "interp": "linr",
                        "uiHints": {"userInterfaceType": 0, "unitType": 0},
                    },
                )
                self.assertEqual(result, doc)

    def test_linked_creation_mirrors_only_wrapper_and_video(self) -> None:
        doc = linked_fixture()
        result = mattes.edit_media(doc, 3, mode="alpha", intensity="1/2", ease_in=1)
        wrapper = clip(result)
        self.assertEqual(wrapper["effects"], wrapper["video"]["effects"])
        self.assertEqual(wrapper["effects"][0]["metadata"], {"effectIndex": "0"})
        self.assertEqual(wrapper["effects"][0]["parameters"]["intensity"]["defaultValue"], 0.5)
        self.assertEqual(wrapper["audio"], clip(doc)["audio"])
        self.assertEqual(doc, linked_fixture())
        self.assertEqual(
            result, mattes.edit_media(doc, 4, mode="alpha", intensity="1/2", ease_in=1)
        )

    def test_linked_tokens_survive_removal_and_new_token_uses_maximum(self) -> None:
        doc = mattes.edit_media(linked_fixture(), 3, mode="alpha")
        border = {
            "effectName": "Border",
            "category": "categoryVisualEffects",
            "parameters": {"width": 2},
            "metadata": {"effectIndex": "1"},
            "opaque": "retain",
        }
        clip(doc)["effects"].append(copy.deepcopy(border))
        clip(doc)["video"]["effects"].append(copy.deepcopy(border))
        removed = mattes.edit_media(doc, 4, mode="none")
        self.assertEqual(clip(removed)["effects"], [border])
        self.assertEqual(clip(removed)["video"]["effects"], [border])
        restored = mattes.edit_media(removed, 3, mode="alpha")
        self.assertEqual(clip(restored)["effects"][0], border)
        self.assertEqual(clip(restored)["effects"][1]["metadata"]["effectIndex"], "2")
        self.assertEqual(clip(restored)["audio"], clip(doc)["audio"])

    def test_linked_existing_controls_keep_role_specific_opaque_state(self) -> None:
        doc = mattes.edit_media(linked_fixture(), 3, mode="alpha")
        clip(doc)["effects"][0]["wrapperFuture"] = ["keep"]
        clip(doc)["video"]["effects"][0]["videoFuture"] = {"keep": True}
        result = mattes.edit_media(doc, 4, mode="luminosity-invert", bypass=True)
        self.assertEqual(clip(result)["effects"][0]["wrapperFuture"], ["keep"])
        self.assertEqual(clip(result)["video"]["effects"][0]["videoFuture"], {"keep": True})
        self.assertTrue(clip(result)["effects"][0]["bypassed"])
        self.assertTrue(clip(result)["video"]["effects"][0]["bypassed"])

    def test_mismatched_linked_mirrors_and_missing_tokens_are_refused(self) -> None:
        for problem in ("missing", "token", "control", "unindexed"):
            with self.subTest(problem=problem):
                doc = mattes.edit_media(linked_fixture(), 3, mode="alpha")
                if problem == "missing":
                    clip(doc)["video"]["effects"] = []
                elif problem == "token":
                    clip(doc)["video"]["effects"][0]["metadata"]["effectIndex"] = "7"
                elif problem == "control":
                    clip(doc)["video"]["effects"][0]["parameters"]["matteMode"] = 4
                else:
                    doc = linked_fixture()
                    clip(doc)["effects"] = [{"effectName": "Unknown"}]
                before = copy.deepcopy(doc)
                with self.assertRaises(ValueError):
                    mattes.edit_media(doc, 3, mode="alpha")
                self.assertEqual(doc, before)

    def test_typed_intensity_preserves_unknown_ui_state_and_bare_legacy_values(self) -> None:
        doc = mattes.edit_media(fixture(), 3, mode="alpha")
        parameter = clip(doc)["effects"][0]["parameters"]["intensity"]
        parameter["uiHints"]["future"] = [3]
        parameter["future"] = "keep"
        result = mattes.edit_media(doc, 3, intensity="1/4")
        expected = copy.deepcopy(parameter)
        expected["defaultValue"] = 0.25
        self.assertEqual(clip(result)["effects"][0]["parameters"]["intensity"], expected)
        clip(doc)["effects"][0]["parameters"]["intensity"] = 1.0
        result = mattes.edit_media(doc, 3, intensity="1/4")
        self.assertEqual(clip(result)["effects"][0]["parameters"]["intensity"], 0.25)

    def test_animated_native_intensity_is_never_flattened(self) -> None:
        doc = mattes.edit_media(fixture(), 3, mode="alpha")
        parameter = clip(doc)["effects"][0]["parameters"]["intensity"]
        parameter["keyframes"] = [{"time": 1000, "endTime": 1000, "duration": 0, "value": 0.5}]
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "animated"):
            mattes.edit_media(doc, 3, intensity=0.2)
        self.assertEqual(doc, before)

    def test_four_modes_create_the_fixed_native_effect_without_other_edits(self) -> None:
        doc = fixture()
        for mode, expected in (
            ("alpha", 1),
            ("alpha-invert", 2),
            ("luminosity", 3),
            ("luminosity-invert", 4),
        ):
            with self.subTest(mode=mode):
                result = mattes.edit_media(doc, 3, mode=mode)
                effect = clip(result)["effects"][0]
                self.assertEqual(
                    effect["parameters"],
                    {
                        "matteMode": expected,
                        "intensity": {
                            "type": "double",
                            "defaultValue": 1.0,
                            "interp": "linr",
                            "uiHints": {"userInterfaceType": 0, "unitType": 0},
                        },
                        "trackDepth": 10002,
                    },
                )
                self.assertEqual(effect["category"], "categoryVisualEffects")
                self.assertFalse(effect["bypassed"])
                clip(result)["effects"] = []
                self.assertEqual(result, doc)
        self.assertEqual(doc, fixture())

    def test_updates_retain_effect_order_opaque_payload_and_depth(self) -> None:
        doc = mattes.edit_media(fixture(), 3, mode="alpha")
        effect = clip(doc)["effects"][0]
        effect.update(opaque={"future": [True, None]})
        effect["parameters"].update(trackDepth=2, future=9)
        effect.setdefault("metadata", {})["future"] = "keep"
        clip(doc)["effects"].insert(0, {"effectName": "Border", "opaque": True})
        result = mattes.edit_media(doc, 3, intensity="1/2", bypass=True)
        expected = copy.deepcopy(doc)
        clip(expected)["effects"][1]["parameters"]["intensity"]["defaultValue"] = 0.5
        clip(expected)["effects"][1]["bypassed"] = True
        self.assertEqual(result, expected)
        self.assertEqual(mattes.edit_media(result, 3, intensity="1/2", bypass=True), result)

    def test_ease_uses_exact_ticks_and_distinct_native_functions(self) -> None:
        result = mattes.edit_media(fixture(), 3, ease_in="3/2", ease_out="1/2")
        effect = clip(result)["effects"][0]
        self.assertEqual(
            effect["leftEdgeMods"],
            [
                {
                    "group": "Video",
                    "duration": 1500,
                    "parameters": [{"name": "intensity", "func": "FadeInFunc"}],
                }
            ],
        )
        self.assertEqual(
            effect["rightEdgeMods"],
            [
                {
                    "group": "Video",
                    "duration": 500,
                    "parameters": [{"name": "intensity", "func": "FadeOutFunc"}],
                }
            ],
        )
        for value in ("1/3000", -1, True):
            with self.subTest(value=value), self.assertRaises(ValueError):
                mattes.edit_media(fixture(), 3, ease_in=value)

    def test_zero_ease_removes_only_the_known_intensity_fade(self) -> None:
        doc = mattes.edit_media(fixture(), 3, ease_in=1)
        cleared = mattes.edit_media(doc, 3, ease_in=0)
        self.assertNotIn("leftEdgeMods", clip(cleared)["effects"][0])
        clip(doc)["effects"][0]["leftEdgeMods"].append(
            {
                "group": "Video",
                "duration": 2000,
                "future": True,
                "parameters": [{"name": "future", "func": "KeepFunc"}],
            }
        )
        result = mattes.edit_media(doc, 3, ease_in=0)
        self.assertEqual(
            clip(result)["effects"][0]["leftEdgeMods"],
            [
                {
                    "group": "Video",
                    "duration": 2000,
                    "future": True,
                    "parameters": [{"name": "future", "func": "KeepFunc"}],
                }
            ],
        )
        self.assertEqual(clip(doc)["effects"][0]["leftEdgeMods"][0]["duration"], 1000)

    def test_shared_edge_clock_is_preserved_or_refused(self) -> None:
        doc = mattes.edit_media(fixture(), 3, ease_in=1)
        modifier = clip(doc)["effects"][0]["leftEdgeMods"][0]
        modifier["parameters"].append({"name": "other", "func": "OtherFunc"})
        self.assertEqual(mattes.edit_media(doc, 3, ease_in=1), doc)
        with self.assertRaisesRegex(ValueError, "shared edge timing"):
            mattes.edit_media(doc, 3, ease_in=2)
        modifier["parameters"][0]["func"] = "Unfamiliar"
        with self.assertRaisesRegex(ValueError, "unfamiliar intensity"):
            mattes.edit_media(doc, 3, ease_in=1)

    def test_removal_is_idempotent_and_keeps_other_effects_and_metadata(self) -> None:
        doc = mattes.edit_media(fixture(), 3, mode="alpha")
        clip(doc)["effects"].append({"effectName": "Blur", "opaque": True})
        result = mattes.edit_media(doc, 3, mode="none")
        self.assertEqual(clip(result)["effects"], [{"effectName": "Blur", "opaque": True}])
        self.assertEqual(mattes.edit_media(result, 3, mode="none"), result)
        with self.assertRaises(ValueError):
            mattes.edit_media(doc, 3, mode="none", bypass=True)

    def test_invalid_scalar_bypass_modes_and_empty_requests_are_refused(self) -> None:
        for value in (True, -0.1, "1.1", "nan", "inf", None):
            with self.subTest(value=value), self.assertRaises(ValueError):
                mattes.edit_media(fixture(), 3, intensity=value)
        cases: list[dict[str, Any]] = [{"mode": "invented"}, {"bypass": 1}, {}]
        for kwargs in cases:
            with self.subTest(kwargs=kwargs), self.assertRaises(ValueError):
                mattes.edit_media(fixture(), 3, **kwargs)

    def test_unobserved_owners_builds_ambiguous_effects_and_curves_are_preserved(self) -> None:
        for kind in ("ScreenVMFile", "Caption", "AMFile"):
            doc = fixture()
            clip(doc)["_type"] = kind
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                mattes.edit_media(doc, 3, mode="alpha")
        doc = fixture()
        doc["authoringClientName"]["version"] = "2025.0.3"
        with self.assertRaises(ValueError):
            mattes.edit_media(doc, 3, mode="alpha")
        doc = mattes.edit_media(fixture(), 3, mode="alpha")
        clip(doc)["effects"].append(copy.deepcopy(clip(doc)["effects"][0]))
        with self.assertRaises(ValueError):
            mattes.edit_media(doc, 3, mode="alpha")
        clip(doc)["effects"].pop()
        clip(doc)["effects"][0]["parameters"]["intensity"] = {"type": "double", "keyframes": []}
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "animated"):
            mattes.edit_media(doc, 3, intensity=0.5)
        self.assertEqual(doc, before)

    def test_root_track_modes_change_only_the_selected_attribute(self) -> None:
        doc = fixture()
        for mode, expected in (
            ("none", 0),
            ("alpha", 1),
            ("alpha-invert", 2),
            ("luminosity", 3),
            ("luminosity-invert", 4),
        ):
            result = mattes.edit_track(doc, 0, mode)
            self.assertEqual(result["timeline"]["trackAttributes"][0]["matte"], expected)
            result["timeline"]["trackAttributes"][0]["matte"] = 0
            self.assertEqual(result, doc)

    def test_nested_group_track_ownership_is_separate(self) -> None:
        doc = fixture()
        child = copy.deepcopy(clip(doc))
        clip(doc).clear()
        clip(doc).update(
            id=9,
            _type="Group",
            tracks=[{"trackIndex": 0, "matte": 0, "medias": [child], "future": "keep"}],
        )
        result = mattes.edit_track(doc, 0, "luminosity-invert", group_id=9)
        self.assertEqual(result["timeline"]["trackAttributes"][0]["matte"], 0)
        self.assertEqual(clip(result)["tracks"][0]["matte"], 4)
        self.assertEqual(clip(result)["tracks"][0]["medias"], [child])
        self.assertEqual(clip(result)["tracks"][0]["future"], "keep")

    def test_track_ambiguity_and_unknown_codes_are_refused(self) -> None:
        for index in (True, -1, 1):
            with self.subTest(index=index), self.assertRaises(ValueError):
                mattes.edit_track(fixture(), index, "alpha")
        doc = fixture()
        doc["timeline"]["trackAttributes"][0]["matte"] = 99
        with self.assertRaises(ValueError):
            mattes.edit_track(doc, 0, "alpha")
        doc = fixture()
        doc["timeline"]["trackAttributes"] = []
        with self.assertRaises(ValueError):
            mattes.edit_track(doc, 0, "alpha")
        with self.assertRaises(ValueError):
            mattes.edit_track(fixture(), 0, "alpha", group_id=3)

    def test_inspection_lists_physical_effect_and_track_paths(self) -> None:
        doc = mattes.edit_media(fixture(), 3, mode="alpha")
        report = mattes.inventory(doc)
        self.assertEqual(report["mediaMattes"][0]["clipId"], 3)
        self.assertEqual(
            report["mediaMattes"][0]["path"],
            "/timeline/sceneTrack/scenes/0/csml/tracks/0/medias/0/effects/0",
        )
        self.assertEqual(
            report["trackMattes"], [{"path": "/timeline/trackAttributes/0/matte", "code": 0}]
        )
        clip(doc)["effects"] = None
        with self.assertRaises(ValueError):
            mattes.inventory(doc)

    def test_cli_stages_both_forms_and_refuses_output_collisions(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "project.json"
            source.write_bytes(project.encode_document(fixture()))
            original = source.read_bytes()
            output = Path(directory) / "candidate.json"
            command = [
                "set-media",
                str(source),
                "--clip-id",
                "3",
                "--mode",
                "alpha-invert",
                "--output",
                str(output),
            ]
            for written in (True, False):
                stream = io.StringIO()
                with patch("sys.stdout", stream):
                    self.assertEqual(mattes.main(command), 0)
                report = json.loads(stream.getvalue())
                self.assertEqual(
                    (
                        report["schema_version"],
                        report["owner"],
                        report["written"],
                        report["nativeVerified"],
                    ),
                    (1, "camtasia-mattes", written, False),
                )
            error = io.StringIO()
            with patch("sys.stderr", error):
                self.assertEqual(
                    mattes.main(
                        [
                            "set-track",
                            str(source),
                            "--track",
                            "0",
                            "--mode",
                            "alpha",
                            "--output",
                            str(output),
                        ]
                    ),
                    1,
                )
            self.assertIn("different data", error.getvalue())
            track_output = Path(directory) / "track.json"
            with patch("sys.stdout", io.StringIO()):
                self.assertEqual(
                    mattes.main(
                        [
                            "set-track",
                            str(source),
                            "--track",
                            "0",
                            "--mode",
                            "alpha",
                            "--output",
                            str(track_output),
                        ]
                    ),
                    0,
                )
            self.assertEqual(
                json.loads(track_output.read_text())["timeline"]["trackAttributes"][0]["matte"], 1
            )
            self.assertEqual(source.read_bytes(), original)
