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
import effects
import project


def node(doc: dict) -> dict:
    return project.scene_tracks(doc)[0][0]["medias"][0]


def fixture(linked: bool = False) -> dict:
    doc = document()
    visual = node(doc)
    visual["effects"] = [
        {
            "effectName": "Border",
            "category": "categoryVisualEffects",
            "bypassed": False,
            "parameters": {"width": 10.0, "type": 0},
            "metadata": {"effectIndex": "0", "future": ["keep"]},
            "future": {"keep": True},
        }
    ]
    if linked:
        project.scene_tracks(doc)[0][0]["medias"] = [
            {
                "id": 10,
                "_type": "UnifiedMedia",
                "video": visual,
                "audio": {
                    "id": 11,
                    "_type": "AMFile",
                    "effects": [],
                    "parameters": {"volume": 0.8},
                },
                "effects": copy.deepcopy(visual["effects"]),
                "metadata": {"effectApplied": "Border", "future": "keep"},
            }
        ]
    return doc


def spec(**changes: Any) -> dict:
    return {"schema_version": 1, **changes}


class EffectTests(unittest.TestCase):
    def test_static_numeric_controls_and_bypass_change_only_requested_fields(self) -> None:
        doc = fixture()
        result = effects.edit_effect(
            doc, 3, "Border", spec(parameters={"width": "1/2", "type": "2"}, bypassed=True)
        )
        expected = copy.deepcopy(doc)
        node(expected)["effects"][0]["parameters"].update(width=0.5, type=2)
        node(expected)["effects"][0]["bypassed"] = True
        self.assertEqual(result, expected)
        self.assertEqual(doc, fixture())
        self.assertIs(type(node(result)["effects"][0]["parameters"]["width"]), float)
        self.assertIs(type(node(result)["effects"][0]["parameters"]["type"]), int)

    def test_typed_static_values_preserve_interpolation_hints_bounds_and_future_state(self) -> None:
        doc = fixture()
        parameter = {
            "type": "double",
            "defaultValue": 10.0,
            "interp": "linr",
            "uiHints": {"future": [1]},
            "valueBounds": {"minValue": 0, "maxValue": 20, "defaultValue": 10},
            "future": "keep",
            "keyframes": [],
        }
        node(doc)["effects"][0]["parameters"]["width"] = parameter
        result = effects.edit_effect(doc, 3, "Border", spec(parameters={"width": 12.5}))
        wanted = copy.deepcopy(parameter)
        wanted["defaultValue"] = 12.5
        self.assertEqual(node(result)["effects"][0]["parameters"]["width"], wanted)
        self.assertEqual(parameter["defaultValue"], 10.0)

    def test_native_numeric_bounds_are_enforced_without_rewriting_them(self) -> None:
        for value in (-1, 21):
            doc = fixture()
            node(doc)["effects"][0]["parameters"]["width"] = {
                "type": "double",
                "defaultValue": 10,
                "valueBounds": {"minValue": 0, "maxValue": 20},
            }
            frozen = copy.deepcopy(doc)
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "inside.*bounds"):
                effects.edit_effect(doc, 3, "Border", spec(parameters={"width": value}))
            self.assertEqual(doc, frozen)

    def test_boolean_types_do_not_coerce_numbers_or_strings(self) -> None:
        values = {
            "Top": True,
            "typed": {
                "type": "bool",
                "defaultValue": False,
                "valueBounds": {"minValue": False, "maxValue": True},
            },
        }
        effects.patch_parameter(values, "Top", False)
        effects.patch_parameter(values, "typed", True)
        self.assertIs(values["Top"], False)
        self.assertIs(values["typed"]["defaultValue"], True)
        for value in (0, 1, "false"):
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "boolean"):
                effects.patch_parameter(values, "Top", value)

    def test_integer_parameters_reject_fractions_and_booleans(self) -> None:
        for typed in (False, True):
            parameter = {"type": "int", "defaultValue": 0} if typed else 0
            for value in (0.5, True):
                doc = fixture()
                node(doc)["effects"][0]["parameters"]["type"] = copy.deepcopy(parameter)
                with self.subTest(typed=typed, value=value), self.assertRaises(ValueError):
                    effects.edit_effect(doc, 3, "Border", spec(parameters={"type": value}))
            values = {"number": copy.deepcopy(parameter)}
            effects.patch_parameter(values, "number", "3/1")
            self.assertEqual(values["number"], {"type": "int", "defaultValue": 3} if typed else 3)

    def test_animated_and_unfamiliar_keyframes_are_never_flattened(self) -> None:
        for frames in (
            [{"time": 0, "endTime": 1000, "duration": 1000, "value": 0.5}],
            None,
            "curve",
        ):
            doc = fixture()
            node(doc)["effects"][0]["parameters"]["width"] = {
                "type": "double",
                "defaultValue": 10.0,
                "keyframes": frames,
            }
            frozen = copy.deepcopy(doc)
            with (
                self.subTest(frames=frames),
                self.assertRaisesRegex(ValueError, "animated|keyframe"),
            ):
                effects.edit_effect(doc, 3, "Border", spec(parameters={"width": 12}))
            self.assertEqual(doc, frozen)

    def test_strings_resources_points_and_missing_defaults_require_the_feature_contract(
        self,
    ) -> None:
        for value in (
            "path.cube",
            [1, 2],
            None,
            {"type": "point", "keyframes": []},
            {"type": "double"},
            {"type": [], "defaultValue": 0},
        ):
            doc = fixture()
            node(doc)["effects"][0]["parameters"]["width"] = copy.deepcopy(value)
            with self.subTest(value=value), self.assertRaises(ValueError):
                effects.edit_effect(doc, 3, "Border", spec(parameters={"width": 1}))

    def test_new_parameter_names_and_missing_effect_constructors_are_refused(self) -> None:
        with self.assertRaisesRegex(ValueError, "existing native parameter"):
            effects.edit_effect(fixture(), 3, "Border", spec(parameters={"invented": 1}))
        with self.assertRaisesRegex(ValueError, "no constructor"):
            effects.edit_effect(fixture(), 3, "Glow", spec(bypassed=True))

    def test_linked_parameters_patch_both_visuals_and_keep_audio_and_role_metadata(self) -> None:
        doc = fixture(True)
        node(doc)["effects"][0]["wrapperFuture"] = [1]
        node(doc)["video"]["effects"][0]["videoFuture"] = [2]
        result = effects.edit_effect(
            doc, 10, "Border", spec(parameters={"width": 2}, bypassed=True)
        )
        self.assertEqual(
            result,
            effects.edit_effect(doc, 3, "Border", spec(parameters={"width": 2}, bypassed=True)),
        )
        self.assertEqual(node(result)["audio"], node(doc)["audio"])
        self.assertEqual(node(result)["effects"][0]["wrapperFuture"], [1])
        self.assertEqual(node(result)["video"]["effects"][0]["videoFuture"], [2])
        self.assertEqual(node(result)["effects"][0]["parameters"]["width"], 2.0)
        self.assertEqual(node(result)["video"]["effects"][0]["parameters"]["width"], 2.0)

    def test_missing_and_conflicting_linked_mirrors_refuse_all_mutations(self) -> None:
        for kind in ("wrapper", "video", "token", "control"):
            doc = fixture(True)
            if kind == "wrapper":
                node(doc)["effects"] = []
            elif kind == "video":
                node(doc)["video"]["effects"] = []
            elif kind == "token":
                node(doc)["effects"][0]["metadata"]["effectIndex"] = "4"
            else:
                node(doc)["effects"][0]["parameters"]["width"] = 9.0
            frozen = copy.deepcopy(doc)
            for operation in (
                lambda: effects.edit_effect(doc, 10, "Border", spec(parameters={"width": 2})),
                lambda: effects.remove_effect(doc, 10, "Border"),
            ):
                with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "linked"):
                    operation()
            self.assertEqual(doc, frozen)

    def test_duplicate_names_require_a_stable_token_not_an_array_index(self) -> None:
        doc = fixture(True)
        for role in (node(doc), node(doc)["video"]):
            second = copy.deepcopy(role["effects"][0])
            second["metadata"]["effectIndex"] = "7"
            role["effects"].append(second)
        with self.assertRaisesRegex(ValueError, "unique effectIndex"):
            effects.edit_effect(doc, 10, "Border", spec(parameters={"width": 2}))
        result = effects.edit_effect(doc, 10, "Border", spec(parameters={"width": 2}), token="7")
        self.assertEqual(node(result)["effects"][0], node(doc)["effects"][0])
        self.assertEqual(node(result)["effects"][1]["parameters"]["width"], 2.0)

    def test_removal_keeps_other_tokens_order_audio_and_reset_metadata(self) -> None:
        doc = fixture(True)
        for role in (node(doc), node(doc)["video"]):
            role["effects"].append(
                {
                    "effectName": "Glow",
                    "category": effects.CATEGORY,
                    "metadata": {"effectIndex": "3"},
                    "parameters": {"radius": 4},
                    "bypassed": False,
                }
            )
        result = effects.remove_effect(doc, 10, "Border")
        self.assertEqual([e["metadata"]["effectIndex"] for e in node(result)["effects"]], ["3"])
        self.assertEqual(node(result)["effects"], node(result)["video"]["effects"])
        self.assertEqual(node(result)["audio"], node(doc)["audio"])
        self.assertEqual(node(result)["metadata"], node(doc)["metadata"])
        self.assertEqual(effects.remove_effect(result, 10, "Border"), result)

    def test_legacy_unique_effects_without_tokens_keep_both_mirrors(self) -> None:
        doc = fixture(True)
        doc.update(
            version="9.0",
            authoringClientName={"name": "Camtasia", "platform": "Mac", "version": "2025.0.3"},
        )
        for role in (node(doc), node(doc)["video"]):
            role["effects"][0]["metadata"].pop("effectIndex")
        result = effects.edit_effect(doc, 10, "Border", spec(parameters={"width": 4}))
        self.assertEqual(node(result)["effects"], node(result)["video"]["effects"])
        self.assertNotIn("effectIndex", node(result)["effects"][0]["metadata"])

    def test_invalid_tokens_builds_and_specs_are_refused(self) -> None:
        tokens: tuple[Any, ...] = ("01", "-1", 0, "future")
        for token in tokens:
            with self.subTest(token=token), self.assertRaises(ValueError):
                effects.remove_effect(fixture(), 3, "Border", token=token)
        for version in ({}, "unknown", "2025.0.3"):
            doc = fixture()
            doc["authoringClientName"]["version"] = version
            with self.subTest(version=version), self.assertRaises(ValueError):
                effects.remove_effect(doc, 3, "Border")
        for payload in (
            {},
            spec(),
            spec(parameters=[]),
            spec(bypassed=1),
            spec(parameters={}),
            spec(parameters={"width": 1}, extra=True),
            {**spec(bypassed=True), "schema_version": True},
        ):
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                effects.edit_effect(fixture(), 3, "Border", payload)

    def test_other_effect_categories_are_not_reported_as_successful_removals(self) -> None:
        doc = fixture()
        node(doc)["effects"][0]["category"] = "categoryAudioEffects"
        with self.assertRaisesRegex(ValueError, "only for categoryVisualEffects"):
            effects.remove_effect(doc, 3, "Border")

    def test_inspection_keeps_physical_positions_and_stable_tokens_distinct(self) -> None:
        doc = fixture(True)
        for role in (node(doc), node(doc)["video"]):
            role["effects"][0]["metadata"]["effectIndex"] = "7"
        rows = effects.inventory(doc)
        self.assertEqual(
            [(r["clipId"], r["arrayPosition"], r["effectToken"]) for r in rows],
            [(10, 0, "7"), (3, 0, "7")],
        )
        self.assertTrue(rows[1]["path"].endswith("/video/effects/0"))

    def test_nonfinite_values_and_malformed_typed_defaults_are_refused(self) -> None:
        for value in (True, "nan", "inf", "1e1000"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                effects.edit_effect(fixture(), 3, "Border", spec(parameters={"width": value}))
        for old in (
            {"type": "double", "defaultValue": True},
            {"type": "bool", "defaultValue": 0},
            {"type": "double", "defaultValue": 1, "valueBounds": []},
        ):
            doc = fixture()
            node(doc)["effects"][0]["parameters"]["width"] = old
            with self.subTest(old=old), self.assertRaises(ValueError):
                effects.edit_effect(doc, 3, "Border", spec(parameters={"width": 2}))

    def test_cli_sets_and_removes_without_touching_inputs_and_accepts_identical_staging(
        self,
    ) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, payload, output, removed = [
                root / name
                for name in ("project.json", "spec.json", "candidate.json", "removed.json")
            ]
            source.write_bytes(project.encode_document(fixture(True)))
            payload.write_text(json.dumps(spec(parameters={"width": 2})))
            original = source.read_bytes()
            for written in (True, False):
                stream = io.StringIO()
                with patch("sys.stdout", stream):
                    self.assertEqual(
                        effects.main(
                            [
                                "set",
                                str(source),
                                "--clip-id",
                                "10",
                                "--effect",
                                "Border",
                                "--spec",
                                str(payload),
                                "--output",
                                str(output),
                            ]
                        ),
                        0,
                    )
                report = json.loads(stream.getvalue())
                self.assertEqual(
                    (report["written"], report["nativeVerified"], report["owner"]),
                    (written, False, "camtasia-effects"),
                )
            with patch("sys.stdout", io.StringIO()):
                self.assertEqual(
                    effects.main(
                        [
                            "remove",
                            str(output),
                            "--clip-id",
                            "10",
                            "--effect",
                            "Border",
                            "--output",
                            str(removed),
                        ]
                    ),
                    0,
                )
            self.assertEqual(node(json.loads(removed.read_text()))["effects"], [])
            self.assertEqual(source.read_bytes(), original)

    def test_cli_refuses_input_aliases_and_unrelated_existing_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            payload = root / "spec.json"
            occupied = root / "occupied.json"
            source.write_bytes(project.encode_document(fixture()))
            payload.write_text(json.dumps(spec(bypassed=True)))
            occupied.write_text("retain")
            for target in (source, occupied):
                with self.subTest(target=target.name), patch("sys.stderr", io.StringIO()):
                    self.assertEqual(
                        effects.main(
                            [
                                "set",
                                str(source),
                                "--clip-id",
                                "3",
                                "--effect",
                                "Border",
                                "--spec",
                                str(payload),
                                "--output",
                                str(target),
                            ]
                        ),
                        1,
                    )
            self.assertEqual(occupied.read_text(), "retain")


if __name__ == "__main__":
    unittest.main()
