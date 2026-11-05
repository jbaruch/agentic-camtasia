from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_effect_constructors import document, owners
from test_effects import node
import behaviors


def native(name="fade") -> dict:
    phases = {
        "fade": ("fadeIn", "none", "fadeOut"),
        "jumpAndFall": ("bounceIn", "jump", "drop"),
        "pulsating": ("grow", "pulsate", "shrink"),
    }
    entry, center, exit = phases[name]
    return dict(
        _type="GenericBehaviorEffect",
        effectName=name,
        bypassed=False,
        start=0,
        duration=8000,
        **{
            "in": dict(
                attributes=dict(
                    name=entry,
                    type=0,
                    characterOrder=6,
                    offsetBetweenCharacters=50,
                    suggestedDurationPerCharacter=1000,
                    overlapProportion="-1/5",
                    movement=-1,
                    future=["retain"],
                )
            ),
            "center": dict(
                attributes=dict(
                    name=center,
                    type=0,
                    characterOrder=6,
                    offsetBetweenCharacters=0,
                    secondsPerLoop="4/5",
                    numberOfLoops=-1,
                    delayBetweenLoops=100,
                ),
                parameters={
                    "jump": dict(
                        type="double",
                        defaultValue=0.5,
                        interp="linr",
                        valueBounds=dict(minValue=0, maxValue=1, defaultValue=0.5),
                        uiHints=dict(future=1),
                        future=["keep"],
                    )
                },
            ),
            "out": dict(
                attributes=dict(
                    name=exit,
                    type=0,
                    characterOrder=6,
                    offsetBetweenCharacters=50,
                    suggestedDurationPerCharacter=1000,
                    overlapProportion="23/60",
                    movement=0,
                )
            ),
        },
        metadata=dict(effectIndex="7", future=["effect"]),
        opaque=["preserve"],
    )


def fixture(linked=False, name="fade") -> dict:
    doc = document(linked)
    for index, owner in enumerate(owners(doc, linked)):
        behavior = native(name)
        if not linked:
            behavior["metadata"].pop("effectIndex")
        behavior["metadata"]["role"] = index
        owner["effects"].append(behavior)
        if index == 0:
            owner.setdefault("metadata", {}).update(effectApplied=name)
    return doc


def spec() -> dict:
    return dict(
        schema_version=1,
        phases={
            "in": dict(attributes=dict(suggestedDurationPerCharacter=3)),
            "out": dict(attributes=dict(offsetBetweenCharacters="1/4")),
        },
    )


class BehaviorTests(unittest.TestCase):
    def test_phase_tick_edit_matches_native_reset_owner_and_preserves_everything_else(self):
        for linked in [False, True]:
            doc = fixture(linked)
            before = copy.deepcopy(doc)
            result = behaviors.edit_behavior(doc, 10 if linked else 3, "fade", spec())
            expected = copy.deepcopy(doc)
            for owner in owners(expected, linked):
                owner["effects"][1]["in"]["attributes"]["suggestedDurationPerCharacter"] = 3000
                owner["effects"][1]["out"]["attributes"]["offsetBetweenCharacters"] = 250
            owners(expected, linked)[0].setdefault("metadata", {}).update(
                {"effectApplied": "fade", "default-Speed-fade": "1000"}
            )
            self.assertEqual(result, expected)
            self.assertEqual(doc, before)
            self.assertEqual(result, behaviors.edit_behavior(result, 3, "fade", spec()))
            if linked:
                self.assertEqual(node(result)["audio"], node(doc)["audio"])
                self.assertNotIn("default-Speed-fade", node(result)["video"].get("metadata", {}))

    def test_loop_seconds_ticks_sentinels_and_static_parameter_descriptors_remain_distinct(self):
        doc = fixture(True, "jumpAndFall")
        changes: dict = dict(
            schema_version=1,
            phases={
                "center": dict(
                    attributes=dict(
                        secondsPerLoop="3/2",
                        numberOfLoops=2,
                        delayBetweenLoops="1/4",
                        offsetBetweenCharacters=0,
                    ),
                    parameters={"jump": "3/4"},
                )
            },
            bypassed=True,
        )
        result = behaviors.edit_behavior(doc, 10, "jumpAndFall", changes)
        expected = copy.deepcopy(doc)
        for owner in owners(expected, True):
            effect = owner["effects"][1]
            effect["center"]["attributes"].update(
                secondsPerLoop="3/2",
                numberOfLoops=2,
                delayBetweenLoops=250,
                offsetBetweenCharacters=0,
            )
            effect["center"]["parameters"]["jump"]["defaultValue"] = 0.75
            effect["bypassed"] = True
        self.assertEqual(result, expected)
        changes["phases"]["center"]["attributes"]["numberOfLoops"] = -1
        self.assertEqual(
            behaviors.edit_behavior(doc, 10, "jumpAndFall", changes)["timeline"]["sceneTrack"][
                "scenes"
            ][0]["csml"]["tracks"][0]["medias"][0]["effects"][1]["center"]["attributes"][
                "numberOfLoops"
            ],
            -1,
        )

    def test_existing_reset_defaults_survive_and_differing_unrecorded_defaults_refuse(self):
        doc = fixture(True)
        node(doc)["metadata"]["default-Speed-fade"] = "prior-native-reset"
        result = behaviors.edit_behavior(doc, 10, "fade", spec())
        self.assertEqual(node(result)["metadata"]["default-Speed-fade"], "prior-native-reset")
        doc = fixture()
        node(doc)["effects"][1]["out"]["attributes"]["suggestedDurationPerCharacter"] = 2000
        request = dict(
            schema_version=1,
            phases={
                phase: dict(attributes=dict(suggestedDurationPerCharacter=3000))
                for phase in ["in", "out"]
            },
        )
        with self.assertRaisesRegex(ValueError, "differing entry/exit"):
            behaviors.edit_behavior(doc, 3, "fade", request)

    def test_native_template_constructor_retains_roles_reset_metadata_and_fresh_tokens(self):
        for linked in [False, True]:
            source, destination = fixture(linked), document(linked)
            source_owner = owners(source, linked)[0]
            source_owner["metadata"]["default-Speed-fade"] = "1000"
            source_owner["metadata"]["unrelated"] = "not copied"
            if linked:
                node(destination)["audio"]["effects"] = [
                    dict(
                        effectName="NoiseReduction",
                        metadata=dict(effectIndex="15"),
                        opaque=["audio"],
                    )
                ]
            frozen = copy.deepcopy(source), copy.deepcopy(destination)
            result = behaviors.add_behavior(
                destination, 10 if linked else 3, source, 10 if linked else 3, "fade"
            )
            expected = copy.deepcopy(destination)
            for original, target in zip(owners(source, linked), owners(expected, linked)):
                behavior = copy.deepcopy(original["effects"][1])
                if linked:
                    behavior["metadata"]["effectIndex"] = "16"
                target["effects"].append(behavior)
            owners(expected, linked)[0].setdefault("metadata", {}).update(
                {"effectApplied": "fade", "default-Speed-fade": "1000"}
            )
            self.assertEqual(result, expected)
            self.assertEqual((source, destination), frozen)

    def test_new_behavior_becomes_last_applied_even_when_template_last_applied_differs(self):
        for linked in [False, True]:
            source, destination = fixture(linked), document(linked)
            node(source)["metadata"]["effectApplied"] = "Border"
            result = behaviors.add_behavior(
                destination, 10 if linked else 3, source, 10 if linked else 3, "fade"
            )
            self.assertEqual(node(result)["metadata"]["effectApplied"], "fade")
            if linked:
                self.assertEqual(
                    node(result)["video"].get("metadata"),
                    node(destination)["video"].get("metadata"),
                )

    def test_direct_constructor_refuses_unselectable_duplicate_identities(self):
        source, destination = fixture(), fixture()
        with self.assertRaisesRegex(ValueError, "unique native effectIndex"):
            behaviors.add_behavior(destination, 3, source, 3, "fade")
        for doc in [source, destination]:
            node(doc)["effects"][1]["metadata"]["effectIndex"] = "7"
        with self.assertRaisesRegex(ValueError, "unique native effectIndex"):
            behaviors.add_behavior(destination, 3, source, 3, "fade")
        node(source)["effects"][1]["metadata"]["effectIndex"] = "9"
        result = behaviors.add_behavior(destination, 3, source, 3, "fade")
        selected = behaviors.edit_behavior(
            result, 3, "fade", {"schema_version": 1, "bypassed": True}, token="9"
        )
        self.assertFalse(node(selected)["effects"][1]["bypassed"])
        self.assertTrue(node(selected)["effects"][2]["bypassed"])

    def test_constructor_refuses_clock_layout_build_rate_and_reset_conflicts(self):
        for field in ["start", "duration", "mediaStart", "mediaDuration", "scalar"]:
            source, destination = fixture(), document()
            node(destination)[field] = 123
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "owner clocks"):
                behaviors.add_behavior(destination, 3, source, 3, "fade")
        with self.assertRaisesRegex(ValueError, "linked layouts"):
            behaviors.add_behavior(document(True), 10, fixture(), 3, "fade")
        for field, value in [("version", "9.0"), ("editRate", 2000)]:
            source, destination = fixture(), document()
            destination[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                behaviors.add_behavior(destination, 3, source, 3, "fade")
        source, destination = fixture(), document()
        node(source)["metadata"]["default-Speed-fade"] = "1000"
        node(destination).setdefault("metadata", {})["default-Speed-fade"] = "2000"
        with self.assertRaisesRegex(ValueError, "reset metadata"):
            behaviors.add_behavior(destination, 3, source, 3, "fade")

    def test_bypass_removal_and_absent_noop_leave_other_tokens_and_audio_unchanged(self):
        doc = fixture(True)
        bypassed = behaviors.edit_behavior(doc, 10, "fade", dict(schema_version=1, bypassed=True))
        expected = copy.deepcopy(doc)
        for owner in owners(expected, True):
            owner["effects"][1]["bypassed"] = True
        self.assertEqual(bypassed, expected)
        removed = behaviors.remove_behavior(doc, 10, "fade")
        for owner in owners(expected, True):
            owner["effects"].pop(1)
        self.assertEqual(removed, expected)
        self.assertEqual(removed, behaviors.remove_behavior(removed, 3, "fade"))

    def test_duplicates_require_tokens_and_mismatched_mirrors_or_clocks_refuse(self):
        doc = fixture(True)
        for owner in owners(doc, True):
            duplicate = copy.deepcopy(owner["effects"][1])
            duplicate["metadata"]["effectIndex"] = "9"
            owner["effects"].append(duplicate)
        with self.assertRaisesRegex(ValueError, "unique effectIndex"):
            behaviors.edit_behavior(doc, 10, "fade", spec())
        result = behaviors.edit_behavior(
            doc, 10, "fade", dict(schema_version=1, bypassed=True), token="9"
        )
        for original, changed in zip(owners(doc, True), owners(result, True)):
            self.assertEqual(original["effects"][1], changed["effects"][1])
            self.assertTrue(changed["effects"][2]["bypassed"])
        for mutation in ["missing", "phase", "token", "clock"]:
            doc = fixture(True)
            if mutation == "missing":
                node(doc)["video"]["effects"].pop(1)
            elif mutation == "phase":
                node(doc)["video"]["effects"][1]["in"]["attributes"]["movement"] = 1
            elif mutation == "token":
                node(doc)["video"]["effects"][1]["metadata"]["effectIndex"] = "9"
            else:
                node(doc)["video"]["mediaStart"] = 0
            before = copy.deepcopy(doc)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                behaviors.edit_behavior(doc, 10, "fade", spec())
            self.assertEqual(doc, before)

    def test_phase_names_are_not_outer_names_and_unknown_payloads_refuse(self):
        for outer in ["flyOut", "fadeIn", "none", "invented"]:
            with self.subTest(outer=outer), self.assertRaisesRegex(ValueError, "outer behavior"):
                behaviors.add_behavior(document(), 3, fixture(), 3, outer)
        for change in [
            dict(_type="effect"),
            dict(bypassed=1),
            dict(start=-1),
            dict(duration=0),
            dict(**{"in": {}}),
        ]:
            doc = fixture()
            node(doc)["effects"][1].update(change)
            with self.subTest(change=change), self.assertRaises(ValueError):
                behaviors.edit_behavior(doc, 3, "fade", spec())
        doc = fixture()
        node(doc)["effects"][1]["in"]["attributes"]["name"] = "explode"
        with self.assertRaisesRegex(ValueError, "phase identifier"):
            behaviors.edit_behavior(doc, 3, "fade", spec())

    def test_native_defaultless_integer_direction_points_survive_unrelated_edits(self):
        doc = fixture(True, "jumpAndFall")
        for owner in owners(doc, True):
            owner["effects"][1]["in"]["parameters"] = {
                "direction": {
                    "type": "int",
                    "valueBounds": {"minValue": 0, "maxValue": 3, "defaultValue": 1},
                    "keyframes": [{"time": 0, "endTime": 0, "duration": 0, "value": 1}],
                }
            }
        result = behaviors.edit_behavior(
            doc,
            10,
            "jumpAndFall",
            {"schema_version": 1, "phases": {"center": {"parameters": {"jump": "3/4"}}}},
        )
        for original, changed in zip(owners(doc, True), owners(result, True)):
            self.assertEqual(changed["effects"][1]["in"], original["effects"][1]["in"])
        copied = behaviors.add_behavior(document(True), 10, doc, 10, "jumpAndFall")
        self.assertEqual(node(copied)["effects"][1]["in"], node(doc)["effects"][1]["in"])

    def test_unsafe_zero_point_and_animated_parameters_are_not_flattened(self):
        doc = fixture(False, "pulsating")
        parameter = dict(
            type="double", defaultValue=1, keyframes=[dict(time=0, endTime=0, duration=0, value=1)]
        )
        node(doc)["effects"][1]["in"]["parameters"] = {"scale": parameter}
        with self.assertRaisesRegex(ValueError, "parser hazard"):
            behaviors.add_behavior(document(), 3, doc, 3, "pulsating")
        doc = fixture(False, "jumpAndFall")
        node(doc)["effects"][1]["center"]["parameters"]["jump"]["keyframes"] = [
            dict(time=0, endTime=1000, duration=1000, value=0.75)
        ]
        with self.assertRaisesRegex(ValueError, "animated"):
            behaviors.edit_behavior(
                doc,
                3,
                "jumpAndFall",
                dict(schema_version=1, phases={"center": dict(parameters={"jump": 0.6})}),
            )

    def test_spec_timing_and_parameter_refusals_preserve_inputs(self):
        cases = [
            dict(schema_version=True),
            dict(schema_version=2),
            dict(extra=True),
            dict(phases={}),
            dict(bypassed=1),
            dict(phases={"entry": {}}),
            dict(phases={"in": {}}),
            dict(phases={"center": dict(attributes=dict(secondsPerLoop=1))}),
            dict(phases={"in": dict(attributes=dict(name="fadeOut"))}),
            dict(phases={"in": dict(attributes=dict(suggestedDurationPerCharacter=True))}),
            dict(phases={"in": dict(attributes=dict(suggestedDurationPerCharacter="1/7"))}),
            dict(phases={"in": dict(attributes=dict(offsetBetweenCharacters=-1))}),
            dict(phases={"in": dict(parameters=dict(missing=1))}),
        ]
        for changes in cases:
            doc = fixture()
            request = dict(schema_version=1)
            request.update(changes)
            before = copy.deepcopy(doc)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                behaviors.edit_behavior(doc, 3, "fade", request)
            self.assertEqual(doc, before)
        for name, value in [
            ("secondsPerLoop", 0),
            ("numberOfLoops", -2),
            ("numberOfLoops", "1/2"),
            ("jump", 2),
        ]:
            doc = fixture(False, "jumpAndFall")
            change = {("parameters" if name == "jump" else "attributes"): {name: value}}
            with self.subTest(name=name), self.assertRaises(ValueError):
                behaviors.edit_behavior(
                    doc, 3, "jumpAndFall", dict(schema_version=1, phases={"center": change})
                )

    def test_cli_construct_set_inspect_remove_and_exclusive_output(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, template_path, settings = (
                root / "source.json",
                root / "template.json",
                root / "spec.json",
            )
            source.write_text(json.dumps(document(True)))
            template_path.write_text(json.dumps(fixture(True)))
            settings.write_text(json.dumps(spec()))
            original = source.read_bytes(), template_path.read_bytes()
            candidate, edited, removed = (
                root / "candidate.json",
                root / "edited.json",
                root / "removed.json",
            )
            command = [
                "add",
                str(source),
                "--clip-id",
                "10",
                "--behavior",
                "fade",
                "--template-project",
                str(template_path),
                "--template-clip-id",
                "10",
                "--output",
                str(candidate),
            ]
            for written in [True, False]:
                with patch("sys.stdout", io.StringIO()) as stdout:
                    self.assertEqual(behaviors.main(command), 0)
                report = json.loads(stdout.getvalue())
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
                self.assertEqual(report["owner"], "camtasia-behaviors")
            with patch("sys.stdout", io.StringIO()):
                self.assertEqual(
                    behaviors.main(
                        [
                            "set",
                            str(candidate),
                            "--clip-id",
                            "3",
                            "--behavior",
                            "fade",
                            "--spec",
                            str(settings),
                            "--output",
                            str(edited),
                        ]
                    ),
                    0,
                )
            with patch("sys.stdout", io.StringIO()) as stdout:
                self.assertEqual(behaviors.main(["inspect", str(edited)]), 0)
            self.assertEqual(len(json.loads(stdout.getvalue())["behaviors"]), 2)
            with patch("sys.stdout", io.StringIO()):
                self.assertEqual(
                    behaviors.main(
                        [
                            "remove",
                            str(edited),
                            "--clip-id",
                            "10",
                            "--behavior",
                            "fade",
                            "--output",
                            str(removed),
                        ]
                    ),
                    0,
                )
            self.assertEqual(behaviors.inventory(json.loads(removed.read_text())), [])
            candidate.write_text("occupied")
            with patch("sys.stderr", io.StringIO()) as stderr:
                self.assertEqual(behaviors.main(command), 1)
            self.assertFalse(json.loads(stderr.getvalue())["ok"])
            self.assertEqual(candidate.read_text(), "occupied")
            self.assertEqual((source.read_bytes(), template_path.read_bytes()), original)

    def test_cli_syntax_errors_are_json_exit_two_and_help_is_plaintext(self):
        for argv in [[], ["add"], ["set"], ["inspect"], ["unknown"]]:
            with (
                patch("sys.stderr", io.StringIO()) as stderr,
                patch("sys.stdout", io.StringIO()) as stdout,
                self.assertRaises(SystemExit) as raised,
            ):
                behaviors.main(argv)
            self.assertEqual(raised.exception.code, 2)
            self.assertFalse(json.loads(stderr.getvalue())["ok"])
            self.assertEqual(stdout.getvalue(), "")
        with patch("sys.stdout", io.StringIO()) as stdout, self.assertRaises(SystemExit) as raised:
            behaviors.main(["--help"])
        self.assertEqual(raised.exception.code, 0)
        self.assertIn("usage:", stdout.getvalue())


if __name__ == "__main__":
    unittest.main()
