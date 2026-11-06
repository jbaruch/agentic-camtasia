from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

from test_behavior_linked_recordings import donor, entry_spec, native_fade, recipient
from test_behaviors import native as native_behavior
from test_effect_grouped_recordings import grouped, node
import behaviors
import effects
import project


def fixture(depth=1, applied=False):
    doc = donor() if applied else recipient()
    return grouped(doc, depth) if depth else doc


class GroupedRecordingBehaviorTests(unittest.TestCase):
    def test_native_constructor_between_root_single_and_nested_groups_and_both_aliases(self):
        for source_depth in (0, 1, 2):
            for dest_depth in (0, 1, 2):
                source = fixture(source_depth, True)
                dest = fixture(dest_depth)
                originals = copy.deepcopy(source), copy.deepcopy(dest)
                expected = copy.deepcopy(dest)
                for ident in (10, 3):
                    node(expected, ident)["effects"] = [native_fade()]
                node(expected, 10)["metadata"]["effectApplied"] = "fade"
                for source_id in (10, 3):
                    for dest_id in (10, 3):
                        with self.subTest(source=source_depth, dest=dest_depth):
                            self.assertEqual(
                                behaviors.add_behavior(dest, dest_id, source, source_id, "fade"),
                                expected,
                            )
                self.assertEqual((source, dest), originals)

    def test_native_phase_ticks_and_timeline_reset_preserve_complete_group_documents(self):
        for depth in (1, 2):
            doc = fixture(depth, True)
            original = copy.deepcopy(doc)
            expected = copy.deepcopy(doc)
            for ident in (10, 3):
                node(expected, ident)["effects"][0]["in"]["attributes"][
                    "suggestedDurationPerCharacter"
                ] = 4233600000
            node(expected, 10)["metadata"]["default-Speed-fade"] = "352800000"
            for ident in (10, 3):
                result = behaviors.edit_behavior(doc, ident, "fade", entry_spec())
                self.assertEqual(result, expected)
                self.assertEqual(
                    behaviors.edit_behavior(result, ident, "fade", entry_spec()), result
                )
            self.assertEqual(doc, original)

    def test_edited_template_keeps_source_interval_resets_and_role_specific_payload(self):
        source = fixture(2, True)
        for ident, role in ((10, "wrapper"), (3, "video")):
            value = node(source, ident)["effects"][0]
            value["in"]["attributes"]["suggestedDurationPerCharacter"] = 4233600000
            value["metadata"]["opaque"] = [role]
        node(source, 10)["metadata"].update(
            {"default-Speed-fade": "352800000", "unrelatedTemplate": "omit"}
        )
        dest = fixture()
        expected = copy.deepcopy(dest)
        for ident in (10, 3):
            node(expected, ident)["effects"] = copy.deepcopy(node(source, ident)["effects"])
        node(expected, 10)["metadata"].update(
            {"effectApplied": "fade", "default-Speed-fade": "352800000"}
        )
        originals = copy.deepcopy(source), copy.deepcopy(dest)
        self.assertEqual(behaviors.add_behavior(dest, 3, source, 10, "fade"), expected)
        self.assertEqual((source, dest), originals)

    def test_bypass_removal_and_absent_noop_preserve_parent_geometry_audio_and_reset(self):
        doc = fixture(2, True)
        node(doc, 10)["metadata"]["default-Speed-fade"] = "352800000"
        original = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        for ident in (10, 3):
            node(expected, ident)["effects"][0]["bypassed"] = True
        bypass = behaviors.edit_behavior(doc, 3, "fade", dict(schema_version=1, bypassed=True))
        self.assertEqual(bypass, expected)
        for ident in (10, 3):
            node(expected, ident)["effects"] = []
        removed = behaviors.remove_behavior(bypass, 10, "fade")
        self.assertEqual(removed, expected)
        self.assertEqual(behaviors.remove_behavior(removed, 3, "fade"), removed)
        self.assertEqual(doc, original)

    def test_fresh_tokens_include_audio_without_importing_parent_effect_identities(self):
        source, dest = fixture(2, True), fixture()
        node(dest, 100)["effects"] = [dict(effectName="Parent", metadata=dict(effectIndex="99"))]
        node(dest, 11)["effects"] = [dict(effectName="Audio", metadata=dict(effectIndex="7"))]
        expected = copy.deepcopy(dest)
        for ident in (10, 3):
            value = native_fade()
            value["metadata"]["effectIndex"] = "8"
            node(expected, ident)["effects"] = [value]
        node(expected, 10)["metadata"]["effectApplied"] = "fade"
        self.assertEqual(behaviors.add_behavior(dest, 10, source, 3, "fade"), expected)

    def test_parent_clocks_can_differ_but_each_complete_child_clock_must_match_template(self):
        source, dest = fixture(2, True), fixture()
        node(source, 101)["start"] = 2116800000
        expected = copy.deepcopy(dest)
        for ident in (10, 3):
            node(expected, ident)["effects"] = [native_fade()]
        node(expected, 10)["metadata"]["effectApplied"] = "fade"
        self.assertEqual(behaviors.add_behavior(dest, 10, source, 3, "fade"), expected)
        for field in effects.CLOCK_FIELDS:
            broken = copy.deepcopy(dest)
            for ident in (10, 3):
                node(broken, ident)[field] = project.number(node(broken, ident)[field]) + 1
            original = copy.deepcopy(broken)
            with self.subTest(field=field), self.assertRaises(ValueError):
                behaviors.add_behavior(broken, 10, source, 3, "fade")
            self.assertEqual(broken, original)

    def test_existing_reset_values_survive_and_fractional_new_reset_ticks_refuse(self):
        doc = fixture(2, True)
        node(doc, 10)["metadata"]["default-Speed-fade"] = "352800000"
        expected = copy.deepcopy(doc)
        for ident in (10, 3):
            node(expected, ident)["effects"][0]["in"]["attributes"][
                "suggestedDurationPerCharacter"
            ] = 1411200000
        self.assertEqual(behaviors.edit_behavior(doc, 10, "fade", entry_spec(2)), expected)
        node(doc, 10)["metadata"].pop("default-Speed-fade")
        for ident in (10, 3):
            node(doc, ident)["effects"][0]["in"]["attributes"]["suggestedDurationPerCharacter"] = 1
        original = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "integral native timeline reset"):
            behaviors.edit_behavior(doc, 3, "fade", entry_spec())
        self.assertEqual(doc, original)

    def test_center_static_controls_keep_descriptors_and_mixed_clock_units_in_groups(self):
        doc = fixture(2)
        for ident in (10, 3):
            behavior = native_behavior("jumpAndFall")
            behavior.update(start=1411200000, duration=5644800000)
            node(doc, ident)["effects"] = [behavior]
        original = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        for ident in (10, 3):
            center = node(expected, ident)["effects"][0]["center"]
            center["attributes"].update(
                secondsPerLoop="3/2", numberOfLoops=2, delayBetweenLoops=176400000
            )
            center["parameters"]["jump"]["defaultValue"] = 0.75
        settings = dict(
            schema_version=1,
            phases={
                "center": dict(
                    attributes=dict(secondsPerLoop="3/2", numberOfLoops=2, delayBetweenLoops="1/4"),
                    parameters=dict(jump="3/4"),
                )
            },
        )
        self.assertEqual(behaviors.edit_behavior(doc, 3, "jumpAndFall", settings), expected)
        self.assertEqual(doc, original)

    def test_unverified_containers_audio_held_stitched_scenes_and_clock_conflicts_refuse(self):
        for change in (
            "StitchedMedia",
            "UnifiedMedia",
            "Unknown",
            "held",
            "stitched",
            "audio",
            "scenes",
            "clock",
        ):
            doc = fixture(2, True)
            if change == "held":
                node(doc, 3)["_type"] = "ScreenIMFile"
            elif change == "stitched":
                node(doc, 3)["_type"] = "StitchedMedia"
            elif change == "audio":
                node(doc, 11)["src"] = 99
            elif change == "scenes":
                doc["timeline"]["sceneTrack"]["scenes"].append(dict(csml=dict(tracks=[])))
            elif change == "clock":
                node(doc, 3)["mediaStart"] += 1
            else:
                node(doc, 101)["_type"] = change
            original = copy.deepcopy(doc)
            for action in (
                lambda: behaviors.add_behavior(doc, 10, fixture(applied=True), 3, "fade"),
                lambda: behaviors.edit_behavior(doc, 3, "fade", entry_spec()),
                lambda: behaviors.remove_behavior(doc, 10, "fade"),
            ):
                with self.subTest(change=change), self.assertRaises(ValueError):
                    action()
                self.assertEqual(doc, original)

    def test_mirror_conflicts_and_ambiguous_tokens_refuse_without_mutation(self):
        for change in ("missing", "token", "controls", "duplicate"):
            doc = fixture(2, True)
            if change == "missing":
                node(doc, 3)["effects"] = []
            elif change == "token":
                node(doc, 3)["effects"][0]["metadata"]["effectIndex"] = "1"
            elif change == "controls":
                node(doc, 3)["effects"][0]["out"]["attributes"]["movement"] = 1
            else:
                node(doc, 3)["effects"].append(native_fade())
            original = copy.deepcopy(doc)
            with self.subTest(change=change), self.assertRaises(ValueError):
                behaviors.edit_behavior(doc, 10, "fade", entry_spec())
            self.assertEqual(doc, original)

    def test_late_invalid_phase_and_conflicting_constructor_resets_are_atomic(self):
        doc = fixture(2, True)
        original = copy.deepcopy(doc)
        spec: dict[str, Any] = entry_spec()
        spec["phases"]["center"] = dict(attributes=dict(secondsPerLoop=2))
        with self.assertRaisesRegex(ValueError, "inactive none"):
            behaviors.edit_behavior(doc, 3, "fade", spec)
        self.assertEqual(doc, original)
        source, dest = fixture(applied=True), fixture(2)
        node(source, 10)["metadata"]["default-Speed-fade"] = "352800000"
        node(dest, 10)["metadata"]["default-Speed-fade"] = "42"
        original = copy.deepcopy(dest)
        with self.assertRaisesRegex(ValueError, "conflicting destination reset"):
            behaviors.add_behavior(dest, 10, source, 3, "fade")
        self.assertEqual(dest, original)

    def test_cli_construct_repeat_edit_and_remove_preserve_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, dest, settings, added, edited, removed = [
                root / name
                for name in (
                    "source.json",
                    "dest.json",
                    "spec.json",
                    "add.json",
                    "edit.json",
                    "remove.json",
                )
            ]
            source.write_bytes(project.encode_document(fixture(2, True)))
            dest.write_bytes(project.encode_document(fixture()))
            originals = source.read_bytes(), dest.read_bytes()
            add = [
                "add",
                str(dest),
                "--clip-id",
                "3",
                "--behavior",
                "fade",
                "--template-project",
                str(source),
                "--template-clip-id",
                "10",
                "--output",
                str(added),
            ]
            for written in (True, False):
                with patch("sys.stdout", new_callable=io.StringIO) as stream:
                    self.assertEqual(behaviors.main(add), 0)
                result = json.loads(stream.getvalue())
                self.assertEqual(result["written"], written)
                self.assertFalse(result["nativeVerified"])
            spec: dict[str, Any] = entry_spec()
            spec["bypassed"] = True
            settings.write_text(json.dumps(spec))
            for args in (
                [
                    "set",
                    str(added),
                    "--clip-id",
                    "10",
                    "--behavior",
                    "fade",
                    "--spec",
                    str(settings),
                    "--output",
                    str(edited),
                ],
                [
                    "remove",
                    str(edited),
                    "--clip-id",
                    "3",
                    "--behavior",
                    "fade",
                    "--output",
                    str(removed),
                ],
            ):
                with patch("sys.stdout", new_callable=io.StringIO):
                    self.assertEqual(behaviors.main(args), 0)
            expected = fixture()
            node(expected, 10)["metadata"].update(
                {"effectApplied": "fade", "default-Speed-fade": "352800000"}
            )
            self.assertEqual(project.load(removed)[0], expected)
            self.assertEqual((source.read_bytes(), dest.read_bytes()), originals)

    def test_cli_late_invalid_control_creates_no_candidate(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, settings, output = [
                root / name for name in ("source.json", "spec.json", "out.json")
            ]
            source.write_bytes(project.encode_document(fixture(2, True)))
            original = source.read_bytes()
            spec: dict[str, Any] = entry_spec()
            spec["phases"]["center"] = dict(attributes=dict(secondsPerLoop=2))
            settings.write_text(json.dumps(spec))
            with (
                patch("sys.stdout", new_callable=io.StringIO),
                patch("sys.stderr", new_callable=io.StringIO),
            ):
                self.assertEqual(
                    behaviors.main(
                        [
                            "set",
                            str(source),
                            "--clip-id",
                            "3",
                            "--behavior",
                            "fade",
                            "--spec",
                            str(settings),
                            "--output",
                            str(output),
                        ]
                    ),
                    1,
                )
            self.assertFalse(output.exists())
            self.assertEqual(source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
