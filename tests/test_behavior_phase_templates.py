from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

from test_behavior_grouped_recordings import fixture
from test_behavior_recordings import donor as direct_donor, KINDS
from test_effect_grouped_recordings import node
import behaviors
import effects
import project


def grow():
    return dict(
        attributes=dict(
            name="grow",
            type=0,
            characterOrder=6,
            offsetBetweenCharacters=23520000,
            suggestedDurationPerCharacter=423360000,
            overlapProportion="3/4",
            movement=30,
            springDamping=5.0,
            springStiffness=50.0,
            bounceBounciness=0.45,
        )
    )


def pulsate():
    return dict(
        attributes=dict(
            name="pulsate",
            type=0,
            characterOrder=6,
            offsetBetweenCharacters=49392000,
            secondsPerLoop=1,
            numberOfLoops=-1,
            delayBetweenLoops=0,
        ),
        parameters=dict(
            movement=dict(
                type="int",
                valueBounds=dict(minValue=0, maxValue=31, defaultValue=27),
                uiHints=dict(userInterfaceType=4, unitType=0),
                keyframes=[dict(endTime=0, time=0, value=27, duration=0)],
            ),
            scale=dict(
                type="double",
                defaultValue=1.08,
                valueBounds=dict(minValue=0.01, maxValue=2.0, defaultValue=1.08),
                uiHints=dict(userInterfaceType=1, unitType=1),
            ),
        ),
    )


def shrink():
    return dict(
        attributes=dict(
            name="shrink",
            type=0,
            characterOrder=6,
            offsetBetweenCharacters=23520000,
            suggestedDurationPerCharacter=341040000,
            overlapProportion="1/10",
            movement=11,
            springDamping=5.0,
            springStiffness=50.0,
            bounceBounciness=0.45,
        )
    )


def phase_source(phase, depth=0):
    doc = fixture(depth, True)
    value = {"in": grow, "center": pulsate, "out": shrink}[phase]()
    for ident in (10, 3):
        node(doc, ident)["effects"][0][phase] = copy.deepcopy(value)
    return doc


class BehaviorPhaseTemplateTests(unittest.TestCase):
    def test_fixed_native_phase_payloads_replace_only_selected_phase_and_both_aliases(self):
        for phase, value in (("in", grow()), ("center", pulsate()), ("out", shrink())):
            source, dest = phase_source(phase), fixture(0, True)
            original = copy.deepcopy(source), copy.deepcopy(dest)
            expected = copy.deepcopy(dest)
            for ident in (10, 3):
                node(expected, ident)["effects"][0][phase] = copy.deepcopy(value)
            for source_id in (10, 3):
                for dest_id in (10, 3):
                    self.assertEqual(
                        behaviors.copy_phase(dest, dest_id, "fade", phase, source, source_id),
                        expected,
                    )
            self.assertEqual((source, dest), original)

    def test_native_none_phase_clears_active_parameters_without_removing_the_behavior(self):
        source, dest = fixture(0, True), phase_source("center")
        expected = copy.deepcopy(dest)
        for ident in (10, 3):
            node(expected, ident)["effects"][0]["center"] = dict(
                attributes=dict(
                    name="none",
                    type=0,
                    characterOrder=6,
                    offsetBetweenCharacters=0,
                    secondsPerLoop=1,
                    numberOfLoops=-1,
                    delayBetweenLoops=0,
                )
            )
        result = behaviors.copy_phase(dest, 10, "fade", "center", source, 3)
        self.assertEqual(result, expected)
        self.assertEqual(behaviors.copy_phase(result, 3, "fade", "center", source, 10), result)

    def test_parent_clocks_geometry_audio_and_cursor_payload_survive_root_group_exchanges(self):
        for source_depth in (0, 1, 2):
            for dest_depth in (0, 1, 2):
                source, dest = phase_source("in", source_depth), fixture(dest_depth, True)
                if source_depth:
                    node(source, 100 + source_depth - 1)["start"] = 2116800000
                expected = copy.deepcopy(dest)
                for ident in (10, 3):
                    node(expected, ident)["effects"][0]["in"] = grow()
                self.assertEqual(behaviors.copy_phase(dest, 3, "fade", "in", source, 10), expected)

    def test_direct_moving_held_and_stitched_owners_keep_their_independent_origins(self):
        for kind in KINDS:
            source, dest = direct_donor(kind), direct_donor(kind)
            node(source, 3)["effects"][0]["in"] = grow()
            expected = copy.deepcopy(dest)
            node(expected, 3)["effects"][0]["in"] = grow()
            with self.subTest(kind=kind):
                self.assertEqual(behaviors.copy_phase(dest, 3, "fade", "in", source, 3), expected)

    def test_target_bypass_tokens_resets_other_effects_and_opaque_owner_data_are_unchanged(self):
        source, dest = phase_source("in", 2), fixture(1, True)
        node(source, 10)["metadata"].update({"default-Speed-fade": "111", "templateOnly": True})
        node(dest, 10)["metadata"].update({"default-Speed-fade": "705600000", "targetOnly": [7]})
        for ident in (10, 3):
            node(source, ident)["effects"][0]["metadata"].update(effectIndex="7", donorOnly=True)
            effect = node(dest, ident)["effects"][0]
            effect.update(bypassed=True, targetOpaque=["keep"])
            effect["metadata"].update(effectIndex="2", targetOnly=True)
            node(dest, ident)["effects"].append(
                dict(effectName="Other", metadata=dict(effectIndex="3"))
            )
        expected = copy.deepcopy(dest)
        for ident in (10, 3):
            node(expected, ident)["effects"][0]["in"] = grow()
        self.assertEqual(
            behaviors.copy_phase(dest, 10, "fade", "in", source, 3, token="2", template_token="7"),
            expected,
        )

    def test_selected_phase_opaque_data_copies_deeply_and_does_not_alias_either_input(self):
        source, dest = phase_source("center"), fixture(2, True)
        for ident in (10, 3):
            node(source, ident)["effects"][0]["center"]["opaquePhase"] = ["saved phase"]
        originals = copy.deepcopy(source), copy.deepcopy(dest)
        result = behaviors.copy_phase(dest, 3, "fade", "center", source, 10)
        node(result, 3)["effects"][0]["center"]["opaquePhase"].append("output only")
        self.assertEqual((source, dest), originals)
        self.assertEqual(node(result, 10)["effects"][0]["center"]["opaquePhase"], ["saved phase"])

    def test_complete_owner_clock_mismatch_missing_fields_and_outer_intervals_refuse_atomically(
        self,
    ):
        for field in effects.CLOCK_FIELDS:
            for missing in (False, True):
                source, dest = phase_source("in"), fixture(0, True)
                for ident in (10, 3):
                    if missing:
                        node(source, ident).pop(field)
                    else:
                        node(source, ident)[field] = project.number(node(source, ident)[field]) + 1
                original = copy.deepcopy(dest)
                with self.subTest(field=field, missing=missing), self.assertRaises(ValueError):
                    behaviors.copy_phase(dest, 10, "fade", "in", source, 3)
                self.assertEqual(dest, original)
        for field in ("start", "duration"):
            source, dest = phase_source("in"), fixture(0, True)
            for ident in (10, 3):
                node(source, ident)["effects"][0][field] += 1
            with (
                self.subTest(field=field),
                self.assertRaisesRegex(ValueError, "behavior intervals"),
            ):
                behaviors.copy_phase(dest, 10, "fade", "in", source, 3)

    def test_build_rate_owner_kind_and_linked_layout_mismatches_refuse(self):
        for change in ("build", "rate", "kind", "layout"):
            source, dest = phase_source("in"), fixture(0, True)
            if change == "build":
                source["authoringClientName"] = "Unverified"
            elif change == "rate":
                source["editRate"] = 1000
            elif change == "kind":
                node(source, 3)["_type"] = "VMFile"
            else:
                project.scene_tracks(source)[0][0]["medias"] = [node(source, 3)]
            original = copy.deepcopy(dest)
            with self.subTest(change=change), self.assertRaises(ValueError):
                behaviors.copy_phase(dest, 10, "fade", "in", source, 3)
            self.assertEqual(dest, original)

    def test_direct_owner_requires_complete_source_and_destination_clocks(self):
        for where in ("source", "target"):
            source, dest = direct_donor("ScreenVMFile"), direct_donor("ScreenVMFile")
            broken = source if where == "source" else dest
            node(broken, 3).pop("mediaStart")
            originals = copy.deepcopy(source), copy.deepcopy(dest)
            with self.subTest(where=where), self.assertRaisesRegex(ValueError, "complete native"):
                behaviors.copy_phase(dest, 3, "fade", "in", source, 3)
            self.assertEqual((source, dest), originals)

    def test_repeated_names_require_independent_source_and_destination_tokens(self):
        source, dest = phase_source("in"), fixture(0, True)
        for doc in (source, dest):
            for ident in (10, 3):
                duplicate = copy.deepcopy(node(doc, ident)["effects"][0])
                duplicate["metadata"]["effectIndex"] = "4"
                node(doc, ident)["effects"].append(duplicate)
        expected = copy.deepcopy(dest)
        for ident in (10, 3):
            node(expected, ident)["effects"][1]["in"] = grow()
        self.assertEqual(
            behaviors.copy_phase(dest, 3, "fade", "in", source, 10, token="4", template_token="0"),
            expected,
        )
        for kwargs in (
            {},
            dict(token="4"),
            dict(template_token="0"),
            dict(token="99", template_token="0"),
        ):
            with self.assertRaises(ValueError):
                behaviors.copy_phase(dest, 3, "fade", "in", source, 10, **kwargs)

    def test_mirror_conflicts_unknown_phases_and_absent_behaviors_refuse(self):
        for where in ("source", "target"):
            source, dest = phase_source("in"), fixture(0, True)
            broken = source if where == "source" else dest
            node(broken, 3)["effects"][0]["in"]["attributes"]["movement"] = 99
            with (
                self.subTest(where=where),
                self.assertRaisesRegex(ValueError, "conflicting linked"),
            ):
                behaviors.copy_phase(dest, 3, "fade", "in", source, 10)
        invalid_phases: list[Any] = ["middle", "", None, [], 1]
        for phase in invalid_phases:
            with self.subTest(phase=phase), self.assertRaises(ValueError):
                behaviors.copy_phase(fixture(0, True), 3, "fade", phase, phase_source("in"), 10)
        dest = fixture(0)
        with self.assertRaisesRegex(ValueError, "existing native behavior"):
            behaviors.copy_phase(dest, 3, "fade", "in", phase_source("in"), 10)

    def test_reproduced_hazard_is_refused_but_native_integer_points_remain_intact(self):
        source, dest = phase_source("center"), fixture(0, True)
        for ident in (10, 3):
            node(source, ident)["effects"][0]["center"]["parameters"]["scale"]["keyframes"] = [
                dict(time=0, endTime=0, duration=0, value=1.08)
            ]
        with self.assertRaisesRegex(ValueError, "redundant static zero-point"):
            behaviors.copy_phase(dest, 10, "fade", "center", source, 3)
        self.assertNotIn("parameters", node(dest, 3)["effects"][0]["center"])

    def test_cli_copy_repeat_preserves_both_inputs_and_emits_staging_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, dest, output = [
                root / name for name in ("source.json", "dest.json", "out.json")
            ]
            source.write_bytes(project.encode_document(phase_source("center", 2)))
            dest.write_bytes(project.encode_document(fixture(1, True)))
            originals = source.read_bytes(), dest.read_bytes()
            args = [
                "copy-phase",
                str(dest),
                "--clip-id",
                "3",
                "--behavior",
                "fade",
                "--phase",
                "center",
                "--template-project",
                str(source),
                "--template-clip-id",
                "10",
                "--output",
                str(output),
            ]
            for written in (True, False):
                with patch("sys.stdout", new_callable=io.StringIO) as stream:
                    self.assertEqual(behaviors.main(args), 0)
                result = json.loads(stream.getvalue())
                self.assertTrue(result["changed"])
                self.assertEqual(result["written"], written)
                self.assertFalse(result["nativeVerified"])
                self.assertEqual(
                    (result["schema_version"], result["owner"]), (1, "camtasia-behaviors")
                )
            expected = fixture(1, True)
            for ident in (10, 3):
                node(expected, ident)["effects"][0]["center"] = pulsate()
            self.assertEqual(project.load(output)[0], expected)
            self.assertEqual((source.read_bytes(), dest.read_bytes()), originals)

    def test_cli_refusal_creates_no_candidate_and_help_is_versioned_json(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, dest, output = [
                root / name for name in ("source.json", "dest.json", "out.json")
            ]
            doc = phase_source("in")
            for ident in (10, 3):
                node(doc, ident)["effects"][0]["duration"] += 1
            source.write_bytes(project.encode_document(doc))
            dest.write_bytes(project.encode_document(fixture(0, True)))
            with (
                patch("sys.stdout", new_callable=io.StringIO),
                patch("sys.stderr", new_callable=io.StringIO) as stream,
            ):
                self.assertEqual(
                    behaviors.main(
                        [
                            "copy-phase",
                            str(dest),
                            "--clip-id",
                            "3",
                            "--behavior",
                            "fade",
                            "--phase",
                            "in",
                            "--template-project",
                            str(source),
                            "--template-clip-id",
                            "10",
                            "--output",
                            str(output),
                        ]
                    ),
                    1,
                )
            self.assertIn("matching owner clocks", json.loads(stream.getvalue())["error"])
            self.assertFalse(output.exists())
        for args in (["--help"], ["copy-phase", "--help"]):
            with (
                patch("sys.stdout", new_callable=io.StringIO) as stream,
                self.assertRaises(SystemExit) as result,
            ):
                behaviors.main(args)
            self.assertEqual(result.exception.code, 0)
            help_result = json.loads(stream.getvalue())
            self.assertEqual(
                (help_result["schema_version"], help_result["owner"], help_result["ok"]),
                (1, "camtasia-behaviors", True),
            )
            self.assertIn("copy-phase", help_result["help"])


if __name__ == "__main__":
    unittest.main()
