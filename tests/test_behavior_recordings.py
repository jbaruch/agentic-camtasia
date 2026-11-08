from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_animation_freezes import owner_document, RATE
from test_animations import visual
from test_behaviors import native, fixture as linked_fixture
import behaviors
import effects
import project

KINDS = ("ScreenVMFile", "ScreenIMFile", "StitchedMedia")


def donor(kind):
    doc = owner_document(kind)
    owner = visual(doc)
    duration = (8 if kind == "StitchedMedia" else 4) * RATE
    owner.update(
        start=4 * RATE if kind == "ScreenIMFile" else 0,
        duration=duration,
        mediaStart=3504480000 if kind == "ScreenIMFile" else RATE,
        mediaDuration=1 if kind == "ScreenIMFile" else duration,
        scalar=1,
    )
    behavior = native("fade")
    behavior["metadata"].pop("effectIndex")
    behavior.update(start=0 if kind == "ScreenIMFile" else RATE, duration=duration)
    for phase in ("in", "out"):
        behavior[phase]["attributes"].update(
            suggestedDurationPerCharacter=RATE, offsetBetweenCharacters=35280000
        )
    owner["effects"] = [behavior]
    owner.setdefault("metadata", {})["effectApplied"] = "fade"
    return doc


def recipient(kind):
    doc = donor(kind)
    visual(doc)["effects"] = [dict(effectName="CursorHilight", opaque=["retain"])]
    visual(doc)["metadata"]["effectApplied"] = "CursorHilight"
    doc["sourceBin"][0]["opaqueProcessing"] = ["retain source processing"]
    project.scene_tracks(doc)[0].append(
        dict(
            trackIndex=1,
            medias=[
                dict(
                    id=90,
                    _type="AMFile",
                    start=0,
                    duration=1000,
                    mediaStart=0,
                    mediaDuration=1000,
                    scalar=1,
                    effects=[dict(effectName="Denoise", opaque=["retain audio"])],
                    parameters=dict(volume=0.7),
                )
            ],
        )
    )
    return doc


class RecordingBehaviorTests(unittest.TestCase):
    def test_complete_template_constructor_preserves_clock_origins_and_unrelated_payloads(self):
        for kind in KINDS:
            source, dest = donor(kind), recipient(kind)
            before = copy.deepcopy(source), copy.deepcopy(dest)
            result = behaviors.add_behavior(dest, 3, source, 3, "fade")
            expected = copy.deepcopy(dest)
            visual(expected)["effects"].append(copy.deepcopy(visual(source)["effects"][0]))
            visual(expected)["metadata"]["effectApplied"] = "fade"
            self.assertEqual(result, expected)
            behavior = visual(result)["effects"][-1]
            self.assertEqual(behavior["start"], 0 if kind == "ScreenIMFile" else 705600000)
            self.assertEqual(
                behavior["duration"], 5644800000 if kind == "StitchedMedia" else 2822400000
            )
            self.assertIsNone(effects.token_of(behavior))
            self.assertEqual((source, dest), before)

    def test_phase_tick_edit_retains_outer_origin_duration_and_native_reset_default(self):
        for kind in KINDS:
            doc = donor(kind)
            before = copy.deepcopy(doc)
            result = behaviors.edit_behavior(
                doc,
                3,
                "fade",
                dict(
                    schema_version=1,
                    phases={
                        "in": dict(attributes=dict(suggestedDurationPerCharacter=3)),
                        "out": dict(attributes=dict(offsetBetweenCharacters="1/4")),
                    },
                ),
            )
            expected = copy.deepcopy(doc)
            visual(expected)["effects"][0]["in"]["attributes"]["suggestedDurationPerCharacter"] = (
                2116800000
            )
            visual(expected)["effects"][0]["out"]["attributes"]["offsetBetweenCharacters"] = (
                176400000
            )
            visual(expected)["metadata"]["default-Speed-fade"] = "705600000"
            self.assertEqual(result, expected)
            self.assertEqual(doc, before)

    def test_bypass_removal_and_noop_preserve_cursor_children_audio_and_reset_metadata(self):
        for kind in KINDS:
            doc = donor(kind)
            visual(doc)["metadata"]["default-Speed-fade"] = "705600000"
            visual(doc)["effects"].append(dict(effectName="CursorHilight", opaque=["retain"]))
            before = copy.deepcopy(doc)
            result = behaviors.edit_behavior(doc, 3, "fade", dict(schema_version=1, bypassed=True))
            expected = copy.deepcopy(doc)
            visual(expected)["effects"][0]["bypassed"] = True
            self.assertEqual(result, expected)
            removed = behaviors.remove_behavior(result, 3, "fade")
            visual(expected)["effects"].pop(0)
            self.assertEqual(removed, expected)
            self.assertEqual(removed, behaviors.remove_behavior(removed, 3, "fade"))
            self.assertEqual(doc, before)

    def test_constructor_refuses_each_complete_clock_mismatch_without_mutation(self):
        for kind in KINDS:
            source = donor(kind)
            for field in effects.CLOCK_FIELDS:
                dest = recipient(kind)
                visual(dest)[field] = 123456
                before = copy.deepcopy(source), copy.deepcopy(dest)
                with (
                    self.subTest(kind=kind, field=field),
                    self.assertRaisesRegex(ValueError, "clocks"),
                ):
                    behaviors.add_behavior(dest, 3, source, 3, "fade")
                self.assertEqual((source, dest), before)

    def test_linked_held_and_stitched_donors_recipients_and_lifecycle_require_native_mirrors(self):
        for kind in ("ScreenIMFile", "StitchedMedia"):
            linked = linked_fixture(True)
            linked["editRate"] = RATE
            project.scene_tracks(linked)[0][0]["medias"][0]["video"]["_type"] = kind
            before = copy.deepcopy(linked)
            for clip in (3, 10):
                for call in (
                    lambda: behaviors.add_behavior(recipient(kind), 3, linked, clip, "fade"),
                    lambda: behaviors.add_behavior(linked, clip, donor(kind), 3, "fade"),
                    lambda: behaviors.edit_behavior(
                        linked, clip, "fade", dict(schema_version=1, bypassed=True)
                    ),
                    lambda: behaviors.remove_behavior(linked, clip, "fade"),
                ):
                    with self.assertRaisesRegex(ValueError, "linked recording"):
                        call()
            self.assertEqual(linked, before)

    def test_hidden_stitched_children_refuse_donors_recipients_and_lifecycle_without_mutation(self):
        for kind, child_id in (("ScreenVMFile", 4), ("ScreenIMFile", 5)):
            hidden = donor("StitchedMedia")
            children = visual(hidden)["medias"]
            index = child_id - 4
            child = copy.deepcopy(visual(donor(kind)))
            child["id"] = child_id
            children[index] = child
            source, dest = donor(kind), recipient(kind)
            before = copy.deepcopy((hidden, source, dest))
            for call in (
                lambda: behaviors.add_behavior(hidden, child_id, source, 3, "fade"),
                lambda: behaviors.add_behavior(dest, 3, hidden, child_id, "fade"),
                lambda: behaviors.edit_behavior(
                    hidden, child_id, "fade", dict(schema_version=1, bypassed=True)
                ),
                lambda: behaviors.remove_behavior(hidden, child_id, "fade"),
            ):
                with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "stitched parent"):
                    call()
                self.assertEqual((hidden, source, dest), before)
            child["effects"] = []
            before_absent = copy.deepcopy(hidden)
            with self.assertRaisesRegex(ValueError, "stitched parent"):
                behaviors.remove_behavior(hidden, child_id, "fade")
            self.assertEqual(hidden, before_absent)

    def test_other_owners_builds_and_cross_kind_templates_remain_refused(self):
        for kind in KINDS:
            doc = donor(kind)
            doc["version"] = "9.0"
            before = copy.deepcopy(doc)
            for call in (
                lambda: behaviors.edit_behavior(
                    doc, 3, "fade", dict(schema_version=1, bypassed=True)
                ),
                lambda: behaviors.remove_behavior(doc, 3, "fade"),
            ):
                with self.assertRaisesRegex(ValueError, "verified.*format-10"):
                    call()
            self.assertEqual(doc, before)
            dest = recipient(kind)
            visual(dest)["_type"] = "PlaceholderMedia"
            with self.assertRaisesRegex(ValueError, "verified"):
                behaviors.add_behavior(dest, 3, donor(kind), 3, "fade")
            other = recipient("ScreenIMFile" if kind != "ScreenIMFile" else "ScreenVMFile")
            with self.assertRaisesRegex(ValueError, "matching native visual owner"):
                behaviors.add_behavior(other, 3, donor(kind), 3, "fade")

    def test_duplicate_direct_identity_and_conflicting_reset_metadata_are_not_guessed(self):
        for kind in KINDS:
            source = donor(kind)
            with self.assertRaisesRegex(ValueError, "unique native effectIndex"):
                behaviors.add_behavior(source, 3, source, 3, "fade")
            visual(source)["metadata"]["default-Speed-fade"] = "705600000"
            dest = recipient(kind)
            visual(dest)["metadata"]["default-Speed-fade"] = "different"
            before = copy.deepcopy(source), copy.deepcopy(dest)
            with self.assertRaisesRegex(ValueError, "reset metadata"):
                behaviors.add_behavior(dest, 3, source, 3, "fade")
            self.assertEqual((source, dest), before)

    def test_cli_construction_phase_edit_bypass_and_removal_preserve_sources(self):
        for kind in KINDS:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source, dest, added, edited, removed, spec = [
                    root / name
                    for name in (
                        "source.json",
                        "dest.json",
                        "added.json",
                        "edited.json",
                        "removed.json",
                        "spec.json",
                    )
                ]
                source.write_bytes(project.encode_document(donor(kind)))
                dest.write_bytes(project.encode_document(recipient(kind)))
                before = source.read_bytes(), dest.read_bytes()
                common = ["--clip-id", "3", "--behavior", "fade"]
                command = [
                    "add",
                    str(dest),
                    *common,
                    "--template-project",
                    str(source),
                    "--template-clip-id",
                    "3",
                    "--output",
                    str(added),
                ]
                for written in (True, False):
                    with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                        self.assertEqual(behaviors.main(command), 0)
                    report = json.loads(stdout.getvalue())
                    self.assertEqual(report["written"], written)
                    self.assertFalse(report["nativeVerified"])
                spec.write_text(
                    json.dumps(
                        dict(
                            schema_version=1,
                            phases={"in": dict(attributes=dict(suggestedDurationPerCharacter=3))},
                            bypassed=True,
                        )
                    )
                )
                with patch("sys.stdout", new_callable=io.StringIO):
                    self.assertEqual(
                        behaviors.main(
                            [
                                "set",
                                str(added),
                                *common,
                                "--spec",
                                str(spec),
                                "--output",
                                str(edited),
                            ]
                        ),
                        0,
                    )
                    self.assertEqual(
                        behaviors.main(["remove", str(edited), *common, "--output", str(removed)]),
                        0,
                    )
                result = project.load(removed)[0]
                expected = recipient(kind)
                visual(expected)["metadata"].update(
                    effectApplied="fade", **{"default-Speed-fade": "705600000"}
                )
                self.assertEqual(result, expected)
                self.assertEqual((source.read_bytes(), dest.read_bytes()), before)


if __name__ == "__main__":
    unittest.main()
