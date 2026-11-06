from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

from test_animation_freezes import RATE
from test_effect_curve_linked_recordings import fixture as root_fixture, spec
from test_effect_grouped_recordings import grouped, node
import behaviors
import effect_curves
import project


def fixture(depth=1):
    return grouped(root_fixture(), depth)


def edit(doc, settings=None, clip=10, **kwargs):
    return effect_curves.edit_curve(
        doc, clip, "Sepia", "intensity", spec() if settings is None else settings, **kwargs
    )


class GroupedRecordingCurveTests(unittest.TestCase):
    def test_fixed_native_linear_source_ticks_and_both_aliases_preserve_complete_group_documents(
        self,
    ):
        for depth in (1, 2):
            doc = fixture(depth)
            original = copy.deepcopy(doc)
            expected = copy.deepcopy(doc)
            for ident in (10, 3):
                node(expected, ident)["effects"][0]["parameters"]["intensity"]["keyframes"] = [
                    dict(
                        time=1411200000,
                        endTime=2822400000,
                        duration=1411200000,
                        value=1.0,
                        interp="linr",
                    )
                ]
            node(expected, 3)["animationTracks"] = dict(
                visual=[dict(endTime=2822400000, duration=1411200000, interp="linr")]
            )
            self.assertEqual(edit(doc), expected)
            self.assertEqual(edit(doc, clip=3), expected)
            self.assertEqual(doc, original)

    def test_explicit_easing_codes_keep_ancestor_geometry_and_its_independent_clock(self):
        for easing, code in (
            ("linear", "linr"),
            ("exponential", "eioe"),
            ("bounce", "bnce"),
            ("spring", "sprg"),
        ):
            doc = fixture(2)
            parent = node(doc, 101)
            parent["start"] = 30 * RATE
            parent["parameters"]["translation0"] = dict(
                type="double",
                defaultValue=0,
                keyframes=[dict(time=0, endTime=RATE, duration=RATE, value=10, interp="linr")],
            )
            parent["animationTracks"] = dict(
                visual=[dict(endTime=RATE, duration=RATE, interp="linr")]
            )
            original = copy.deepcopy(doc)
            result = edit(doc, spec(easing))
            expected = copy.deepcopy(doc)
            for ident in (10, 3):
                node(expected, ident)["effects"][0]["parameters"]["intensity"]["keyframes"] = [
                    dict(
                        time=1411200000,
                        endTime=2822400000,
                        duration=1411200000,
                        value=1.0,
                        interp=code,
                    )
                ]
            node(expected, 3)["animationTracks"] = dict(
                visual=[dict(endTime=2822400000, duration=1411200000, interp=code)]
            )
            with self.subTest(easing=easing):
                self.assertEqual(result, expected)
            self.assertEqual(doc, original)

    def test_spring_retains_matching_linear_child_geometry_and_cursor_payload(self):
        doc = fixture(2)
        child = node(doc, 3)
        child["animationTracks"] = dict(
            visual=[dict(endTime=2822400000, duration=1411200000, interp="linr", opaque=["keep"])]
        )
        child["parameters"]["translation0"] = dict(
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
        original = copy.deepcopy(doc)
        result = edit(doc, spec("spring"))
        self.assertEqual(node(result, 3)["animationTracks"], child["animationTracks"])
        self.assertEqual(node(result, 3)["parameters"], child["parameters"])
        for ident in (10, 3):
            self.assertEqual(
                node(result, ident)["effects"][0]["parameters"]["intensity"]["keyframes"],
                [
                    dict(
                        time=1411200000,
                        endTime=2822400000,
                        duration=1411200000,
                        value=1.0,
                        interp="sprg",
                    )
                ],
            )
        self.assertEqual(doc, original)

    def test_version_one_linear_parameter_interpolation_and_clear_remain_native(self):
        doc = edit(fixture(), spec(version=1))
        expected = copy.deepcopy(doc)
        for ident in (10, 3):
            descriptor = node(expected, ident)["effects"][0]["parameters"]["intensity"]
            self.assertEqual(descriptor["interp"], "linr")
            descriptor.pop("keyframes")
            descriptor["defaultValue"] = 0.25
        self.assertEqual(effect_curves.clear_curve(doc, 3, "Sepia", "intensity", "1/4"), expected)

    def test_nonlinear_clear_is_idempotent_and_preserves_all_other_group_audio_and_source_state(
        self,
    ):
        doc = edit(fixture(2), spec("spring"))
        original = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        for ident in (10, 3):
            descriptor = node(expected, ident)["effects"][0]["parameters"]["intensity"]
            descriptor.pop("keyframes")
            descriptor["defaultValue"] = 0.0
        result = effect_curves.clear_curve(doc, 10, "Sepia", "intensity", 0)
        self.assertEqual(result, expected)
        self.assertEqual(effect_curves.clear_curve(result, 3, "Sepia", "intensity", 0), expected)
        self.assertEqual(doc, original)

    def test_repeated_tokens_select_only_one_effect_and_keep_ancestor_effects(self):
        doc = fixture(2)
        node(doc, 100)["effects"] = [dict(effectName="Sepia", parameters=dict(intensity=0.5))]
        for ident in (10, 3):
            other = copy.deepcopy(node(doc, ident)["effects"][0])
            other["metadata"]["effectIndex"] = "4"
            node(doc, ident)["effects"].append(other)
        with self.assertRaisesRegex(ValueError, "unique effectIndex"):
            edit(doc)
        original = copy.deepcopy(doc)
        result = edit(doc, token="4")
        for ident in (10, 3):
            self.assertEqual(node(result, ident)["effects"][0], node(doc, ident)["effects"][0])
        self.assertEqual(node(result, 100)["effects"], node(doc, 100)["effects"])
        self.assertEqual(doc, original)

    def test_gaps_use_child_source_ticks_and_parent_duration_does_not_extend_child_bounds(self):
        doc = fixture()
        node(doc, 100)["duration"] = 30 * RATE
        settings: dict[str, Any] = dict(
            schema_version=2,
            defaultValue=0,
            segments=[
                dict(start=0, end=1, value=0.5, easing="bounce"),
                dict(start=2, end=3, value=1, easing="spring"),
            ],
        )
        result = edit(doc, settings)
        expected = [
            dict(
                time=1411200000, endTime=2822400000, duration=1411200000, value=0.5, interp="bnce"
            ),
            dict(
                time=4233600000, endTime=5644800000, duration=1411200000, value=1.0, interp="sprg"
            ),
        ]
        self.assertEqual(
            node(result, 3)["effects"][0]["parameters"]["intensity"]["keyframes"], expected
        )
        settings["segments"][-1]["end"] = 5
        with self.assertRaisesRegex(ValueError, "within the displayed clip"):
            edit(doc, settings)

    def test_non_group_ancestors_missing_audio_and_conflicting_child_clocks_refuse_set_and_clear(
        self,
    ):
        for change in (
            "StitchedMedia",
            "UnifiedMedia",
            "Unknown",
            "audio",
            "clock",
            "scenes",
            "held",
        ):
            doc = fixture(2)
            if change == "audio":
                node(doc, 11)["src"] = 99
            elif change == "clock":
                node(doc, 3)["mediaStart"] += 1
            elif change == "scenes":
                doc["timeline"]["sceneTrack"]["scenes"].append(dict(csml=dict(tracks=[])))
            elif change == "held":
                node(doc, 3)["_type"] = "ScreenIMFile"
            else:
                node(doc, 101)["_type"] = change
            original = copy.deepcopy(doc)
            for action in (
                lambda: edit(doc),
                lambda: effect_curves.clear_curve(doc, 3, "Sepia", "intensity", 0),
            ):
                with self.subTest(change=change), self.assertRaises(ValueError):
                    action()
                self.assertEqual(doc, original)

    def test_other_feature_helpers_keep_their_group_scope(self):
        doc = fixture()
        for action in (lambda: behaviors.behavior_owners(doc, 3),):
            with self.assertRaises(ValueError):
                action()

    def test_cli_set_repeat_and_clear_preserve_inputs_and_native_verification_status(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, settings, output, cleared = [
                root / name for name in ("source.json", "spec.json", "curve.json", "clear.json")
            ]
            source.write_bytes(project.encode_document(fixture(2)))
            original = source.read_bytes()
            settings.write_text(json.dumps(spec("spring")))
            command = [
                "set",
                str(source),
                "--clip-id",
                "3",
                "--effect",
                "Sepia",
                "--parameter",
                "intensity",
                "--spec",
                str(settings),
                "--output",
                str(output),
            ]
            for written in (True, False):
                with patch("sys.stdout", new_callable=io.StringIO) as stream:
                    self.assertEqual(effect_curves.main(command), 0)
                report = json.loads(stream.getvalue())
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
            with patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(
                    effect_curves.main(
                        [
                            "clear",
                            str(output),
                            "--clip-id",
                            "10",
                            "--effect",
                            "Sepia",
                            "--parameter",
                            "intensity",
                            "--value",
                            "0",
                            "--output",
                            str(cleared),
                        ]
                    ),
                    0,
                )
            expected = edit(fixture(2), spec("spring"))
            for ident in (10, 3):
                node(expected, ident)["effects"][0]["parameters"]["intensity"].pop("keyframes")
            self.assertEqual(project.load(cleared)[0], expected)
            self.assertEqual(source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
