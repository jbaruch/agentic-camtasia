from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_effect_constructors import owners
from test_effect_curves import fixture
from test_effects import node
import effect_curves


def spec() -> dict:
    return {
        "schema_version": 2,
        "defaultValue": "1/4",
        "segments": [
            {"start": 0, "end": "3/2", "value": 1},
            {"start": "3/2", "end": 3, "value": 0, "easing": "exponential"},
            {"start": 3, "end": "9/2", "value": 1, "easing": "bounce"},
            {"start": "9/2", "end": 6, "value": 0, "easing": "spring"},
        ],
    }


class EffectCurveEasingTests(unittest.TestCase):
    def test_mixed_easing_exact_clock_mirrors_and_unrelated_payload(self) -> None:
        for linked in (False, True):
            doc = fixture(linked)
            result = effect_curves.edit_curve(
                doc, 10 if linked else 3, "Sepia", "intensity", spec()
            )
            expected = copy.deepcopy(doc)
            for owner in owners(expected, linked):
                parameter = owner["effects"][0]["parameters"]["intensity"]
                parameter.pop("interp")
                parameter.update(
                    defaultValue=0.25,
                    keyframes=[
                        dict(time=2000, endTime=3000, duration=1000, value=1.0, interp="linr"),
                        dict(time=3000, endTime=4000, duration=1000, value=0.0, interp="eioe"),
                        dict(time=4000, endTime=5000, duration=1000, value=1.0, interp="bnce"),
                        dict(time=5000, endTime=6000, duration=1000, value=0.0, interp="sprg"),
                    ],
                )
            owners(expected, linked)[-1]["animationTracks"]["visual"].extend(
                [
                    dict(endTime=4000, duration=1000, interp="eioe"),
                    dict(endTime=5000, duration=1000, interp="bnce"),
                    dict(endTime=6000, duration=1000, interp="sprg"),
                ]
            )
            self.assertEqual(result, expected)
            self.assertEqual(doc, fixture(linked))
            self.assertEqual(
                result, effect_curves.edit_curve(result, 3, "Sepia", "intensity", spec())
            )

    def test_known_shared_easing_survives_independent_effect_frame(self) -> None:
        for easing in (None, "linr", "eioe", "bnce", "sprg"):
            doc = fixture()
            interval = node(doc)["animationTracks"]["visual"][0]
            if easing is not None:
                interval["interp"] = easing
            before = copy.deepcopy(doc)
            request = {
                "schema_version": 2,
                "defaultValue": 0,
                "segments": [{"start": 0, "end": "3/2", "value": 1, "easing": "spring"}],
            }
            result = effect_curves.edit_curve(doc, 3, "Sepia", "intensity", request)
            self.assertEqual(node(result)["animationTracks"], node(doc)["animationTracks"])
            self.assertEqual(node(result)["parameters"], node(doc)["parameters"])
            self.assertEqual(
                node(result)["effects"][0]["parameters"]["intensity"]["keyframes"][0]["interp"],
                "sprg",
            )
            self.assertEqual(doc, before)

    def test_unknown_shared_easing_refuses_without_mutation(self) -> None:
        doc = fixture()
        node(doc)["animationTracks"]["visual"][0]["interp"] = "future"
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "shared interval easing"):
            effect_curves.edit_curve(doc, 3, "Sepia", "intensity", spec())
        self.assertEqual(doc, before)

    def test_nonlinear_frames_retain_static_owner_holds_and_children(self) -> None:
        for kind in ("IMFile", "Callout", "Group"):
            doc = fixture()
            owner = node(doc)
            owner.update(_type=kind, mediaStart=0, mediaDuration=1, scalar="1/2")
            owner["animationTracks"]["visual"] = []
            owner["tracks"] = [{"medias": [{"id": 30, "opaque": ["child"]}]}]
            result = effect_curves.edit_curve(doc, 3, "Sepia", "intensity", spec())
            frames = node(result)["effects"][0]["parameters"]["intensity"]["keyframes"]
            self.assertEqual(
                [(f["time"], f["endTime"]) for f in frames],
                [(0, 3000), (3000, 6000), (6000, 9000), (9000, 12000)],
            )
            self.assertEqual(node(result)["tracks"], owner["tracks"])
            self.assertEqual(node(result)["mediaDuration"], 1)

    def test_invalid_easing_versions_and_targets_preserve_source(self) -> None:
        requests = []
        for easing in ("auto", "eioe", "unknown", None, True, {}, []):
            request = spec()
            request["segments"][0]["easing"] = easing
            requests.append(request)
        for version in (True, 0, 3):
            request = spec()
            request["schema_version"] = version
            requests.append(request)
        request = spec()
        request["schema_version"] = 1
        requests.append(request)
        request = spec()
        request["segments"][0]["value"] = 1.1
        requests.append(request)
        request = spec()
        request["segments"][0]["future"] = True
        requests.append(request)
        for request in requests:
            doc = fixture()
            with self.subTest(request=request), self.assertRaises(ValueError):
                effect_curves.edit_curve(doc, 3, "Sepia", "intensity", request)
            self.assertEqual(doc, fixture())

    def test_clear_preserves_nonlinear_visual_intervals_and_opaque_descriptor(self) -> None:
        doc = effect_curves.edit_curve(fixture(True), 10, "Sepia", "intensity", spec())
        expected = copy.deepcopy(doc)
        for owner in owners(expected, True):
            parameter = owner["effects"][0]["parameters"]["intensity"]
            parameter.pop("keyframes")
            parameter["defaultValue"] = 0.5
        result = effect_curves.clear_curve(doc, 10, "Sepia", "intensity", "1/2")
        self.assertEqual(result, expected)
        self.assertEqual(result, effect_curves.clear_curve(result, 3, "Sepia", "intensity", 0.5))

    def test_v2_cli_noop_collision_and_late_refusal(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, settings, output = (
                root / name for name in ("source.json", "spec.json", "out.json")
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
            for written in (True, False):
                stream = io.StringIO()
                with patch("sys.stdout", stream):
                    self.assertEqual(effect_curves.main(command), 0)
                self.assertEqual(json.loads(stream.getvalue())["written"], written)
            candidate = output.read_bytes()
            changed = spec()
            changed["defaultValue"] = 0.5
            settings.write_text(json.dumps(changed))
            with patch("sys.stderr", io.StringIO()):
                self.assertEqual(effect_curves.main(command), 1)
            self.assertEqual(output.read_bytes(), candidate)
            output.unlink()
            changed["segments"][-1]["easing"] = "unknown"
            settings.write_text(json.dumps(changed))
            with patch("sys.stderr", io.StringIO()):
                self.assertEqual(effect_curves.main(command), 1)
            self.assertFalse(output.exists())
            self.assertEqual(source.read_bytes(), original)
