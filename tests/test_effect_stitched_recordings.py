from __future__ import annotations

from contextlib import redirect_stdout
import copy
import io
import json
from pathlib import Path
import tempfile
from typing import Any
import unittest

from test_effect_grouped_recordings import node
from test_matte_stitched_linked_recordings import fixture as native_parent, unstitched
import effect_curves
import effects
import project

RATE = 705600000


def document():
    doc = native_parent()
    doc["authoringClientName"]["version"] = "2026.2.5"
    return doc


def sepia(value: float | dict[str, Any] = 1.0):
    return dict(
        effectName="Sepia",
        bypassed=False,
        category="categoryVisualEffects",
        parameters=dict(intensity=value),
    )


def template(value=1.0, typed=False):
    doc = document()
    parameter = (
        dict(type="double", defaultValue=value, uiHints=dict(userInterfaceType=0, unitType=0))
        if typed
        else value
    )
    node(doc, 100)["effects"] = [sepia(parameter)]
    node(doc, 100)["metadata"].update(effectApplied="Sepia", **{"default-Sepia-intensity": "1"})
    return doc


def ramp():
    return dict(
        schema_version=2,
        defaultValue=0,
        segments=[dict(start="7/2", end="9/2", value=1, easing="spring")],
    )


class StitchedRecordingEffectTests(unittest.TestCase):
    def test_static_native_templates_add_one_parent_effect_and_selected_reset_data(self):
        for value in (1.0, 0.5):
            source, dest = template(value), document()
            node(source, 100)["metadata"]["donorOnly"] = ["omit"]
            node(dest, 100)["effects"] = [dict(effectName="Other", opaque=["retain"])]
            before = copy.deepcopy(source), copy.deepcopy(dest)
            expected = copy.deepcopy(dest)
            node(expected, 100)["effects"].append(sepia(value))
            node(expected, 100)["metadata"].update(
                effectApplied="Sepia", **{"default-Sepia-intensity": "1"}
            )
            actual = effects.add_effect(dest, 100, source, 100, "Sepia")
            self.assertEqual(actual, expected)
            self.assertIsNone(effects.token_of(node(actual, 100)["effects"][-1]))
            self.assertEqual((source, dest), before)

    def test_parent_lifecycle_preserves_moving_audio_virtual_hold_and_cursor_payload(self):
        source = template()
        before = copy.deepcopy(source)
        half = effects.edit_effect(
            source, 100, "Sepia", dict(schema_version=1, parameters={"intensity": 0.5})
        )
        expected = copy.deepcopy(source)
        node(expected, 100)["effects"][0]["parameters"]["intensity"] = 0.5
        self.assertEqual(half, expected)
        bypass = effects.edit_effect(half, 100, "Sepia", dict(schema_version=1, bypassed=True))
        node(expected, 100)["effects"][0]["bypassed"] = True
        self.assertEqual(bypass, expected)
        removed = effects.remove_effect(bypass, 100, "Sepia")
        node(expected, 100)["effects"] = []
        self.assertEqual(removed, expected)
        self.assertEqual(effects.remove_effect(removed, 100, "Sepia"), removed)
        self.assertEqual(source, before)
        for child_id in (10, 3):
            with self.subTest(child_id=child_id), self.assertRaisesRegex(ValueError, "root linked"):
                effects.edit_effect(
                    source, child_id, "Sepia", dict(schema_version=1, bypassed=True)
                )
        self.assertEqual(source, before)

    def test_cross_join_spring_authoring_matches_native_parent_source_ticks(self):
        doc = template(0.0, typed=True)
        before = copy.deepcopy(doc)
        actual = effect_curves.edit_curve(doc, 100, "Sepia", "intensity", ramp())
        expected = copy.deepcopy(doc)
        start, end = 6350400000, 7761600000
        node(expected, 100)["effects"][0]["parameters"]["intensity"]["keyframes"] = [
            dict(time=start, endTime=end, duration=1411200000, value=1.0, interp="sprg")
        ]
        node(expected, 100)["animationTracks"]["visual"] = [
            dict(endTime=end, duration=1411200000, interp="sprg")
        ]
        self.assertEqual(actual, expected)
        self.assertLess(start, node(actual, 50)["start"])
        self.assertGreater(end, node(actual, 50)["start"])
        self.assertEqual(node(actual, 50)["mediaStart"], 7008960000)
        self.assertEqual(node(actual, 50)["duration"], 5081731200000)
        self.assertEqual(
            effect_curves.edit_curve(actual, 100, "Sepia", "intensity", ramp()), actual
        )
        self.assertEqual(doc, before)

    def test_timed_template_copy_requires_complete_parent_clocks_and_keeps_descendants(self):
        source = effect_curves.edit_curve(
            template(0.0, typed=True), 100, "Sepia", "intensity", ramp()
        )
        dest = document()
        expected = copy.deepcopy(dest)
        node(expected, 100)["effects"] = copy.deepcopy(node(source, 100)["effects"])
        node(expected, 100)["metadata"].update(
            effectApplied="Sepia", **{"default-Sepia-intensity": "1"}
        )
        self.assertEqual(effects.add_effect(dest, 100, source, 100, "Sepia"), expected)
        self.assertEqual(node(expected, 100)["animationTracks"], {})
        for field in ("start", "duration", "mediaStart", "mediaDuration", "scalar"):
            changed = copy.deepcopy(dest)
            node(changed, 100)[field] = 1 if field == "scalar" else node(changed, 100)[field] + RATE
            before = copy.deepcopy(changed)
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "matching complete"):
                effects.add_effect(changed, 100, source, 100, "Sepia")
            self.assertEqual(changed, before)

    def test_clearing_keeps_independent_geometry_intervals_and_reset_history(self):
        doc = template(0.0, typed=True)
        node(doc, 100)["parameters"]["translation0"] = dict(
            type="double",
            defaultValue=-30.0,
            keyframes=[
                dict(
                    time=6350400000,
                    endTime=7761600000,
                    duration=1411200000,
                    value=30.0,
                    interp="linr",
                )
            ],
        )
        animated = effect_curves.edit_curve(doc, 100, "Sepia", "intensity", ramp())
        before = copy.deepcopy(animated)
        expected = copy.deepcopy(animated)
        parameter = node(expected, 100)["effects"][0]["parameters"]["intensity"]
        parameter.pop("keyframes")
        parameter["defaultValue"] = 0.5
        actual = effect_curves.clear_curve(animated, 100, "Sepia", "intensity", "1/2")
        self.assertEqual(actual, expected)
        self.assertEqual(
            effect_curves.clear_curve(actual, 100, "Sepia", "intensity", "1/2"), actual
        )
        self.assertEqual(animated, before)

    def test_unstitched_hold_is_direct_and_its_curve_uses_local_zero(self):
        dest = unstitched()
        source = copy.deepcopy(dest)
        node(source, 50)["effects"] = [sepia(dict(type="double", defaultValue=0.0))]
        expected = copy.deepcopy(dest)
        node(expected, 50)["effects"] = copy.deepcopy(node(source, 50)["effects"])
        built = effects.add_effect(dest, 50, source, 50, "Sepia")
        self.assertEqual(built, expected)
        spec = dict(schema_version=1, defaultValue=0, segments=[dict(start=0, end=1, value=1)])
        animated = effect_curves.edit_curve(built, 50, "Sepia", "intensity", spec)
        frames = node(animated, 50)["effects"][0]["parameters"]["intensity"]["keyframes"]
        self.assertEqual(
            frames, [dict(time=0, endTime=2 * RATE, duration=2 * RATE, value=1.0, interp="linr")]
        )
        self.assertEqual(node(animated, 50)["mediaStart"], 7008960000)
        self.assertEqual(node(animated, 10), node(dest, 10))
        self.assertEqual(animated["sourceBin"], dest["sourceBin"])

    def test_cli_stages_exclusive_candidates_and_repeats_without_input_writes(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, donor, output = (
                root / n for n in ("source.json", "donor.json", "candidate.json")
            )
            source.write_bytes(project.encode_document(document()))
            donor.write_bytes(project.encode_document(template()))
            before = source.read_bytes(), donor.read_bytes()
            args = [
                "add",
                str(source),
                "--clip-id",
                "100",
                "--effect",
                "Sepia",
                "--template-project",
                str(donor),
                "--template-clip-id",
                "100",
                "--output",
                str(output),
            ]
            for written in (True, False):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(effects.main(args), 0)
                report = json.loads(stdout.getvalue())
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
            self.assertEqual(
                project.load(output)[0],
                effects.add_effect(document(), 100, template(), 100, "Sepia"),
            )
            self.assertEqual((source.read_bytes(), donor.read_bytes()), before)


if __name__ == "__main__":
    unittest.main()
