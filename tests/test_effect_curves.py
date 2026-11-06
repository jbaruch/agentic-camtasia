from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_effect_constructors import owners, template
from test_effects import node
import effect_curves


def fixture(linked=False):
    doc = template(linked)
    for owner in owners(doc, linked):
        owner.setdefault("parameters", {})["opacity"] = {
            "type": "double",
            "defaultValue": 0.8,
            "keyframes": [dict(time=2000, endTime=3000, duration=1000, value=0.5)],
        }
        owner["animationTracks"] = {
            "visual": [dict(endTime=3000, duration=1000, opaque="retain")],
            "future": [1],
        }
        owner["effects"][0]["parameters"]["intensity"].update(
            valueBounds=dict(minValue=0, maxValue=1, defaultValue=1), future=["retain"]
        )
    return doc


def spec():
    return dict(
        schema_version=1,
        defaultValue=0,
        segments=[dict(start="3/2", end=3, value=1), dict(start=6, end="15/2", value="1/4")],
    )


class EffectCurveTests(unittest.TestCase):
    def test_exact_trimmed_inverse_speed_clock_and_full_preservation(self):
        for linked in [False, True]:
            doc = fixture(linked)
            result = effect_curves.edit_curve(
                doc, 10 if linked else 3, "Sepia", "intensity", spec()
            )
            expected = copy.deepcopy(doc)
            for owner in owners(expected, linked):
                owner["effects"][0]["parameters"]["intensity"].update(
                    defaultValue=0.0,
                    interp="linr",
                    keyframes=[
                        dict(time=3000, endTime=4000, duration=1000, value=1.0, interp="linr"),
                        dict(time=6000, endTime=7000, duration=1000, value=0.25, interp="linr"),
                    ],
                )
            visual = owners(expected, linked)[-1]
            visual["animationTracks"]["visual"] += [
                dict(endTime=4000, duration=1000, interp="linr"),
                dict(endTime=7000, duration=1000, interp="linr"),
            ]
            self.assertEqual(result, expected)
            self.assertEqual(doc, fixture(linked))
            if linked:
                self.assertEqual(
                    result, effect_curves.edit_curve(doc, 3, "Sepia", "intensity", spec())
                )

    def test_still_and_group_holds_are_not_clamped_to_one_source_tick(self):
        for kind in ["IMFile", "Callout", "Group"]:
            doc = fixture()
            owner = node(doc)
            owner.update(_type=kind, mediaStart=0, mediaDuration=1, scalar=1)
            owner["animationTracks"]["visual"] = []
            owner["tracks"] = [{"medias": [{"id": 30, "opaque": "retain child"}]}]
            result = effect_curves.edit_curve(doc, 3, "Sepia", "intensity", spec())
            frames = node(result)["effects"][0]["parameters"]["intensity"]["keyframes"]
            with self.subTest(kind=kind):
                self.assertEqual(
                    [(frame["time"], frame["endTime"]) for frame in frames],
                    [(1500, 3000), (6000, 7500)],
                )
                self.assertEqual(node(result)["tracks"], owner["tracks"])
                self.assertEqual(node(result)["mediaDuration"], 1)

    def test_matching_linear_interval_and_opaque_fields_are_retained(self):
        doc = fixture()
        node(doc)["animationTracks"]["visual"].append(
            dict(endTime=4000, duration=1000, future=["keep"])
        )
        result = effect_curves.edit_curve(doc, 3, "Sepia", "intensity", spec())
        self.assertEqual(
            node(result)["animationTracks"]["visual"][1],
            dict(endTime=4000, duration=1000, future=["keep"]),
        )
        self.assertEqual(result, effect_curves.edit_curve(result, 3, "Sepia", "intensity", spec()))

    def test_clear_removes_only_selected_frames_and_retains_intervals(self):
        doc = effect_curves.edit_curve(fixture(True), 10, "Sepia", "intensity", spec())
        expected = copy.deepcopy(doc)
        for owner in owners(expected, True):
            parameter = owner["effects"][0]["parameters"]["intensity"]
            parameter.pop("keyframes")
            parameter["defaultValue"] = 0.5
        result = effect_curves.clear_curve(doc, 10, "Sepia", "intensity", "1/2")
        self.assertEqual(result, expected)
        self.assertEqual(result, effect_curves.clear_curve(result, 3, "Sepia", "intensity", 0.5))

    def test_replace_complete_selected_curve_preserves_other_curves(self):
        doc = fixture()
        parameter = node(doc)["effects"][0]["parameters"]["intensity"]
        parameter["keyframes"] = [
            dict(
                time=2000,
                endTime=3000,
                duration=1000,
                value=0.8,
                interp="eioe",
                opaque="selected-old-frame",
            )
        ]
        parameter["interp"] = "eioe"
        result = effect_curves.edit_curve(doc, 3, "Sepia", "intensity", spec())
        self.assertEqual(len(node(result)["effects"][0]["parameters"]["intensity"]["keyframes"]), 2)
        self.assertEqual(node(result)["parameters"], node(doc)["parameters"])
        self.assertEqual(
            node(result)["animationTracks"]["visual"][0], node(doc)["animationTracks"]["visual"][0]
        )

    def test_different_existing_interval_overlap_or_easing_refuses_unchanged_input(self):
        for interval in [
            dict(endTime=3500, duration=1000),
            dict(endTime=4000, duration=1000, interp="eioe"),
            dict(endTime=3000, duration=1000),
        ]:
            doc = fixture()
            node(doc)["animationTracks"]["visual"].append(interval)
            before = copy.deepcopy(doc)
            with self.subTest(interval=interval), self.assertRaises(ValueError):
                effect_curves.edit_curve(doc, 3, "Sepia", "intensity", spec())
            self.assertEqual(doc, before)

    def test_spec_bounds_values_and_exact_tick_failures_refuse_without_mutation(self):
        bad = [
            dict(schema_version=True),
            dict(schema_version=3),
            dict(segments=[]),
            dict(segments=[dict(start=0, end=1, value=2)]),
            dict(defaultValue=-1),
            dict(defaultValue=True),
            dict(segments=[dict(start=False, end=1, value=1)]),
            dict(segments=[dict(start=-1, end=1, value=1)]),
            dict(segments=[dict(start=0, end=9, value=1)]),
            dict(segments=[dict(start=1, end=1, value=1)]),
            dict(segments=[dict(start=0, end="1/7", value=0.5)]),
            dict(segments=[dict(start=3, end=4, value=0.5), dict(start=2, end=3, value=1)]),
            dict(segments=[dict(start=3, end=5, value=0.5), dict(start=4, end=6, value=1)]),
            dict(segments=[dict(start=1, end=2, value=1, extra=True)]),
            dict(extra=True),
        ]
        for changes in bad:
            doc, request = fixture(), spec()
            request.update(changes)
            before = copy.deepcopy(doc)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                effect_curves.edit_curve(doc, 3, "Sepia", "intensity", request)
            self.assertEqual(doc, before)

    def test_unfamiliar_parameter_shapes_and_points_are_not_flattened(self):
        bad = [
            1.0,
            None,
            dict(type="int", defaultValue=1),
            dict(type="double"),
            dict(type="double", defaultValue=float("inf")),
            dict(type="double", defaultValue=1, keyframes={}),
            dict(
                type="double",
                defaultValue=1,
                keyframes=[dict(time=0, endTime=0, duration=0, value=1)],
            ),
            dict(
                type="double",
                defaultValue=1,
                keyframes=[dict(time=2, endTime=4, duration=3, value=1)],
            ),
        ]
        for value in bad:
            doc = fixture()
            node(doc)["effects"][0]["parameters"]["intensity"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                effect_curves.edit_curve(doc, 3, "Sepia", "intensity", spec())
            with self.subTest(clear=value), self.assertRaises(ValueError):
                effect_curves.clear_curve(doc, 3, "Sepia", "intensity", 1)

    def test_build_owner_clock_and_mirror_refusals(self):
        for field in ["start", "duration", "mediaStart", "mediaDuration", "scalar"]:
            doc = fixture(True)
            node(doc)[field] = 123
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "clocks"):
                effect_curves.edit_curve(doc, 10, "Sepia", "intensity", spec())
        doc = fixture(True)
        node(doc)["video"]["effects"][0]["parameters"]["intensity"]["defaultValue"] = 0.5
        with self.assertRaisesRegex(ValueError, "conflicting.*controls"):
            effect_curves.edit_curve(doc, 10, "Sepia", "intensity", spec())
        for field, value in [("_type", "ScreenVMFile"), ("scalar", 0)]:
            doc = fixture()
            node(doc)[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                effect_curves.edit_curve(doc, 3, "Sepia", "intensity", spec())
        doc = fixture()
        doc["version"] = "9.0"
        with self.assertRaisesRegex(ValueError, "2026.2.4"):
            effect_curves.clear_curve(doc, 3, "Sepia", "intensity", 1)
        with self.assertRaisesRegex(ValueError, "motion_paths.py"):
            effect_curves.edit_curve(fixture(), 3, "MediaPath", "intensity", spec())

    def test_repeated_effects_require_unique_stable_tokens(self):
        doc = fixture(True)
        for owner in owners(doc, True):
            duplicate = copy.deepcopy(owner["effects"][0])
            duplicate["metadata"]["effectIndex"] = "9"
            owner["effects"].append(duplicate)
        with self.assertRaisesRegex(ValueError, "unique effectIndex"):
            effect_curves.edit_curve(doc, 10, "Sepia", "intensity", spec())
        result = effect_curves.edit_curve(doc, 10, "Sepia", "intensity", spec(), token="9")
        for original, changed in zip(owners(doc, True), owners(result, True)):
            self.assertEqual(original["effects"][0], changed["effects"][0])
            self.assertEqual(changed["effects"][1]["metadata"]["effectIndex"], "9")

    def test_cli_staging_inspection_clear_and_exclusive_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, settings, output = (
                root / "source.json",
                root / "spec.json",
                root / "candidate.json",
            )
            source.write_text(json.dumps(fixture(True)))
            original = source.read_bytes()
            settings.write_text(json.dumps(spec()))
            command = [
                "set",
                str(source),
                "--clip-id",
                "10",
                "--effect",
                "Sepia",
                "--parameter",
                "intensity",
                "--spec",
                str(settings),
                "--output",
                str(output),
            ]
            for written in [True, False]:
                stdout = io.StringIO()
                with patch("sys.stdout", stdout):
                    self.assertEqual(effect_curves.main(command), 0)
                report = json.loads(stdout.getvalue())
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
                self.assertEqual(report["owner"], "camtasia-effect-curves")
            with patch("sys.stdout", io.StringIO()) as stdout:
                self.assertEqual(effect_curves.main(["inspect", str(output)]), 0)
            self.assertEqual(len(json.loads(stdout.getvalue())["effects"]), 2)
            clear = [
                "clear",
                str(output),
                "--clip-id",
                "3",
                "--effect",
                "Sepia",
                "--parameter",
                "intensity",
                "--value",
                "1/2",
                "--output",
                str(root / "clear.json"),
            ]
            with patch("sys.stdout", io.StringIO()):
                self.assertEqual(effect_curves.main(clear), 0)
            output.write_text("occupied")
            with patch("sys.stderr", io.StringIO()) as stderr:
                self.assertEqual(effect_curves.main(command), 1)
            self.assertFalse(json.loads(stderr.getvalue())["ok"])
            self.assertEqual(output.read_text(), "occupied")
            self.assertEqual(source.read_bytes(), original)

    def test_cli_misuse_returns_json_exit_two_and_help_plaintext(self):
        for argv in [[], ["set"], ["inspect"], ["unknown"]]:
            with (
                patch("sys.stderr", io.StringIO()) as stderr,
                patch("sys.stdout", io.StringIO()) as stdout,
                self.assertRaises(SystemExit) as raised,
            ):
                effect_curves.main(argv)
            self.assertEqual(raised.exception.code, 2)
            self.assertFalse(json.loads(stderr.getvalue())["ok"])
            self.assertEqual(stdout.getvalue(), "")
        with patch("sys.stdout", io.StringIO()) as stdout, self.assertRaises(SystemExit) as raised:
            effect_curves.main(["--help"])
        self.assertEqual(raised.exception.code, 0)
        self.assertIn("usage:", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
