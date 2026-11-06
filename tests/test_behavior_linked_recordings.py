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
from test_animations import visual
from test_matte_linked_recordings import fixture as linked_fixture, wrapper
import behaviors
import effects
import project


def recipient():
    doc = linked_fixture()
    for owner in (wrapper(doc), visual(doc), wrapper(doc)["audio"]):
        owner.update(
            start=0, duration=4 * RATE, mediaStart=2 * RATE, mediaDuration=8 * RATE, scalar="1/2"
        )
    return doc


def native_fade() -> dict[str, Any]:
    attributes = dict(
        type=0,
        characterOrder=6,
        offsetBetweenCharacters=35280000,
        suggestedDurationPerCharacter=705600000,
        overlapProportion=0,
        movement=0,
        springDamping=5.0,
        springStiffness=50.0,
        bounceBounciness=0.45,
    )
    return dict(
        _type="GenericBehaviorEffect",
        effectName="fade",
        bypassed=False,
        start=1411200000,
        duration=5644800000,
        **{
            "in": dict(attributes=dict(name="fadeIn", **attributes)),
            "center": dict(
                attributes=dict(
                    name="none",
                    type=0,
                    characterOrder=6,
                    offsetBetweenCharacters=0,
                    secondsPerLoop=1,
                    numberOfLoops=-1,
                    delayBetweenLoops=0,
                )
            ),
            "out": dict(attributes=dict(name="fadeOut", **attributes)),
        },
        metadata=dict(effectIndex="0"),
    )


def donor():
    doc = recipient()
    for owner in (wrapper(doc), visual(doc)):
        owner["effects"] = [native_fade()]
    wrapper(doc)["metadata"]["effectApplied"] = "fade"
    return doc


def entry_spec(seconds=6):
    return dict(
        schema_version=1,
        phases={"in": dict(attributes=dict(suggestedDurationPerCharacter=seconds))},
    )


class LinkedRecordingBehaviorTests(unittest.TestCase):
    def test_fixed_native_constructor_and_both_aliases_preserve_complete_documents(self):
        source, dest = donor(), recipient()
        before = copy.deepcopy(source), copy.deepcopy(dest)
        expected = copy.deepcopy(dest)
        for owner in (wrapper(expected), visual(expected)):
            owner["effects"] = [native_fade()]
        wrapper(expected)["metadata"]["effectApplied"] = "fade"
        for source_id in (10, 3):
            for dest_id in (10, 3):
                self.assertEqual(
                    behaviors.add_behavior(dest, dest_id, source, source_id, "fade"), expected
                )
        self.assertEqual((source, dest), before)
        self.assertEqual(wrapper(expected)["audio"], wrapper(dest)["audio"])
        self.assertEqual(expected["sourceBin"], dest["sourceBin"])

    def test_native_entry_edit_uses_source_phase_ticks_and_timeline_reset_ticks(self):
        doc = donor()
        before = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        for owner in (wrapper(expected), visual(expected)):
            owner["effects"][0]["in"]["attributes"]["suggestedDurationPerCharacter"] = 4233600000
        wrapper(expected)["metadata"]["default-Speed-fade"] = "352800000"
        result = behaviors.edit_behavior(doc, 3, "fade", entry_spec())
        self.assertEqual(result, expected)
        self.assertEqual(doc, before)
        self.assertEqual(behaviors.edit_behavior(result, 10, "fade", entry_spec()), result)
        self.assertEqual(wrapper(result)["effects"][0]["start"], 1411200000)
        self.assertEqual(wrapper(result)["effects"][0]["duration"], 5644800000)
        self.assertNotIn("default-Speed-fade", visual(result).get("metadata", {}))

    def test_existing_reset_companion_survives_later_duration_changes(self):
        doc = donor()
        wrapper(doc)["metadata"]["default-Speed-fade"] = "352800000"
        result = behaviors.edit_behavior(doc, 10, "fade", entry_spec(2))
        self.assertEqual(wrapper(result)["metadata"]["default-Speed-fade"], "352800000")
        for owner in (wrapper(result), visual(result)):
            self.assertEqual(
                owner["effects"][0]["in"]["attributes"]["suggestedDurationPerCharacter"], 1411200000
            )

    def test_fractional_reset_ticks_refuse_before_write_but_existing_native_defaults_are_retained(
        self,
    ):
        doc = donor()
        for owner in (wrapper(doc), visual(doc)):
            owner["effects"][0]["in"]["attributes"]["suggestedDurationPerCharacter"] = 1
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "integral native timeline reset ticks"):
            behaviors.edit_behavior(doc, 10, "fade", entry_spec())
        self.assertEqual(doc, before)
        wrapper(doc)["metadata"]["default-Speed-fade"] = "352800000"
        result = behaviors.edit_behavior(doc, 3, "fade", entry_spec())
        self.assertEqual(wrapper(result)["metadata"]["default-Speed-fade"], "352800000")

    def test_bypass_removal_and_absent_noop_preserve_reset_audio_cursor_and_source_data(self):
        doc = behaviors.edit_behavior(donor(), 10, "fade", entry_spec())
        before = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        for owner in (wrapper(expected), visual(expected)):
            owner["effects"][0]["bypassed"] = True
        bypass = behaviors.edit_behavior(doc, 3, "fade", dict(schema_version=1, bypassed=True))
        self.assertEqual(bypass, expected)
        for owner in (wrapper(expected), visual(expected)):
            owner["effects"] = []
        removed = behaviors.remove_behavior(bypass, 10, "fade")
        self.assertEqual(removed, expected)
        self.assertEqual(behaviors.remove_behavior(removed, 3, "fade"), removed)
        self.assertEqual(doc, before)

    def test_constructor_copies_role_specific_opaque_fields_and_only_selected_reset_metadata(self):
        source, dest = donor(), recipient()
        wrapper(source)["metadata"].update(
            {"default-Speed-fade": "352800000", "unrelatedTemplate": "omit"}
        )
        for owner, role in ((wrapper(source), "wrapper"), (visual(source), "video")):
            owner["effects"][0]["metadata"]["opaque"] = [role]
            owner["effects"][0]["opaqueEffect"] = {"role": role}
        expected = copy.deepcopy(dest)
        for target, original in (
            (wrapper(expected), wrapper(source)),
            (visual(expected), visual(source)),
        ):
            target["effects"] = copy.deepcopy(original["effects"])
        wrapper(expected)["metadata"].update(
            {"effectApplied": "fade", "default-Speed-fade": "352800000"}
        )
        self.assertEqual(behaviors.add_behavior(dest, 10, source, 3, "fade"), expected)
        wrapper(dest)["metadata"]["default-Speed-fade"] = "123"
        with self.assertRaisesRegex(ValueError, "conflicting destination reset"):
            behaviors.add_behavior(dest, 10, source, 10, "fade")

    def test_constructor_token_avoids_unrelated_visual_and_audio_identities(self):
        source, dest = donor(), recipient()
        for owner in (wrapper(dest), visual(dest)):
            owner["effects"] = [dict(effectName="Other", metadata=dict(effectIndex="2"))]
        wrapper(dest)["audio"]["effects"] = [
            dict(effectName="AudioOther", metadata=dict(effectIndex="7"), opaque=["keep"])
        ]
        expected = copy.deepcopy(dest)
        for owner in (wrapper(expected), visual(expected)):
            value = native_fade()
            value["metadata"]["effectIndex"] = "8"
            owner["effects"].append(value)
        wrapper(expected)["metadata"]["effectApplied"] = "fade"
        self.assertEqual(behaviors.add_behavior(dest, 3, source, 10, "fade"), expected)

    def test_repeated_behavior_names_require_explicit_token_and_do_not_renumber_others(self):
        doc = donor()
        for owner in (wrapper(doc), visual(doc)):
            other = native_fade()
            other["metadata"]["effectIndex"] = "4"
            owner["effects"].append(other)
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "unique effectIndex"):
            behaviors.remove_behavior(doc, 10, "fade")
        expected = copy.deepcopy(doc)
        for owner in (wrapper(expected), visual(expected)):
            owner["effects"].pop(1)
        self.assertEqual(behaviors.remove_behavior(doc, 3, "fade", token="4"), expected)
        self.assertEqual(doc, before)

    def test_complete_owner_clocks_must_match_both_mirrors_and_template(self):
        source, dest = donor(), recipient()
        for field in effects.CLOCK_FIELDS:
            changed = copy.deepcopy(dest)
            for owner in (wrapper(changed), visual(changed)):
                owner[field] = 1 if field == "scalar" else owner[field] + 1
            before = copy.deepcopy(changed)
            with (
                self.subTest(field=field),
                self.assertRaisesRegex(ValueError, "matching complete owner clocks"),
            ):
                behaviors.add_behavior(changed, 10, source, 3, "fade")
            self.assertEqual(changed, before)
            for change in ("missing", "conflict", "boolean"):
                broken = donor()
                if change == "missing":
                    visual(broken).pop(field)
                else:
                    visual(broken)[field] = (
                        True
                        if change == "boolean"
                        else 1
                        if field == "scalar"
                        else visual(broken)[field] + 1
                    )
                before = copy.deepcopy(broken)
                for action in (
                    lambda: behaviors.add_behavior(dest, 10, broken, 3, "fade"),
                    lambda: behaviors.edit_behavior(broken, 3, "fade", entry_spec()),
                    lambda: behaviors.remove_behavior(broken, 10, "fade"),
                ):
                    with self.subTest(field=field, change=change), self.assertRaises(ValueError):
                        action()
                    self.assertEqual(broken, before)

    def test_unknown_audio_nonpositive_clocks_and_unsupported_linked_forms_refuse(self):
        for change in (
            "missing-audio",
            "audio-kind",
            "audio-source",
            "bool-source",
            "rate",
            "speed",
            "held",
            "stitched",
            "other-container",
            "scenes",
        ):
            doc = donor()
            if change == "missing-audio":
                wrapper(doc).pop("audio")
            elif change == "audio-kind":
                wrapper(doc)["audio"]["_type"] = "VMFile"
            elif change in ("audio-source", "bool-source"):
                wrapper(doc)["audio"]["src"] = True if change == "bool-source" else 2
            elif change == "rate":
                doc["editRate"] = 0
            elif change == "speed":
                for owner in (wrapper(doc), visual(doc)):
                    owner["scalar"] = 0
            elif change in ("held", "stitched"):
                visual(doc)["_type"] = "ScreenIMFile" if change == "held" else "StitchedMedia"
            elif change == "other-container":
                old = wrapper(doc)
                project.scene_tracks(doc)[0][0]["medias"] = [
                    dict(id=20, _type="StitchedMedia", medias=[old])
                ]
            else:
                doc["timeline"]["sceneTrack"]["scenes"].append(dict(csml=dict(tracks=[])))
            before = copy.deepcopy(doc)
            for action in (
                lambda: behaviors.add_behavior(doc, 10, donor(), 10, "fade"),
                lambda: behaviors.edit_behavior(doc, 3, "fade", entry_spec()),
                lambda: behaviors.remove_behavior(doc, 10, "fade"),
            ):
                with self.subTest(change=change), self.assertRaises(ValueError):
                    action()
                self.assertEqual(doc, before)

    def test_missing_conflicting_duplicate_and_untokened_mirrors_refuse(self):
        for change in ("missing", "token", "controls", "duplicate", "untokened"):
            doc = donor()
            if change == "missing":
                visual(doc)["effects"] = []
            elif change == "token":
                visual(doc)["effects"][0]["metadata"]["effectIndex"] = "1"
            elif change == "controls":
                visual(doc)["effects"][0]["in"]["attributes"]["movement"] = 1
            elif change == "duplicate":
                visual(doc)["effects"].append(native_fade())
            else:
                for owner in (wrapper(doc), visual(doc)):
                    owner["effects"][0]["metadata"].pop("effectIndex")
            before = copy.deepcopy(doc)
            with self.subTest(change=change), self.assertRaises(ValueError):
                behaviors.edit_behavior(doc, 10, "fade", entry_spec())
            self.assertEqual(doc, before)

    def test_inactive_phase_and_conflicting_unrecorded_reset_defaults_refuse(self):
        doc = donor()
        with self.assertRaisesRegex(ValueError, "inactive none"):
            behaviors.edit_behavior(
                doc,
                3,
                "fade",
                dict(schema_version=1, phases={"center": dict(attributes=dict(secondsPerLoop=2))}),
            )
        for owner in (wrapper(doc), visual(doc)):
            owner["effects"][0]["out"]["attributes"]["suggestedDurationPerCharacter"] = 2 * RATE
        with self.assertRaisesRegex(ValueError, "differing entry/exit durations"):
            behaviors.edit_behavior(
                doc,
                10,
                "fade",
                dict(
                    schema_version=1,
                    phases={
                        "in": dict(attributes=dict(suggestedDurationPerCharacter=6)),
                        "out": dict(attributes=dict(suggestedDurationPerCharacter=6)),
                    },
                ),
            )

    def test_cli_add_repeat_phase_bypass_remove_and_source_preservation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, dest, settings, added, edited, removed = [
                root / name
                for name in (
                    "source.json",
                    "destination.json",
                    "spec.json",
                    "added.json",
                    "edited.json",
                    "removed.json",
                )
            ]
            source.write_bytes(project.encode_document(donor()))
            dest.write_bytes(project.encode_document(recipient()))
            original = source.read_bytes(), dest.read_bytes()
            args = [
                "add",
                str(dest),
                "--clip-id",
                "10",
                "--behavior",
                "fade",
                "--template-project",
                str(source),
                "--template-clip-id",
                "3",
                "--output",
                str(added),
            ]
            for written in (True, False):
                with patch("sys.stdout", new_callable=io.StringIO) as stream:
                    self.assertEqual(behaviors.main(args), 0)
                report = json.loads(stream.getvalue())
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
            changes = entry_spec()
            changes["bypassed"] = True
            settings.write_text(json.dumps(changes))
            for command in (
                [
                    "set",
                    str(added),
                    "--clip-id",
                    "3",
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
                    "10",
                    "--behavior",
                    "fade",
                    "--output",
                    str(removed),
                ],
            ):
                with patch("sys.stdout", new_callable=io.StringIO):
                    self.assertEqual(behaviors.main(command), 0)
            expected = recipient()
            wrapper(expected)["metadata"].update(
                {"effectApplied": "fade", "default-Speed-fade": "352800000"}
            )
            self.assertEqual(project.load(removed)[0], expected)
            self.assertEqual((source.read_bytes(), dest.read_bytes()), original)

    def test_all_behavior_help_responses_emit_versioned_json(self):
        for command in ([], ["inspect"], ["add"], ["set"], ["remove"]):
            with (
                patch("sys.stdout", new_callable=io.StringIO) as stream,
                self.assertRaises(SystemExit) as raised,
            ):
                behaviors.main([*command, "--help"])
            self.assertEqual(raised.exception.code, 0)
            data = json.loads(stream.getvalue())
            self.assertEqual(
                (data["schema_version"], data["owner"], data["ok"]), (1, "camtasia-behaviors", True)
            )
            self.assertIn("usage:", data["help"])


if __name__ == "__main__":
    unittest.main()
