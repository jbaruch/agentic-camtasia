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
from test_behaviors import fixture as behavior_fixture
from test_effect_constructors import template as linked_template
import behaviors
import effects
import project

KINDS = ("ScreenVMFile", "ScreenIMFile", "StitchedMedia")


def template(kind):
    doc = owner_document(kind)
    visual(doc)["effects"] = [
        dict(
            effectName="Sepia",
            category="categoryVisualEffects",
            bypassed=False,
            parameters=dict(
                intensity=dict(
                    type="double",
                    defaultValue=0.5,
                    interp="linr",
                    uiHints=dict(userInterfaceType=0, unitType=0),
                )
            ),
            opaque=["retain effect data"],
        )
    ]
    visual(doc).setdefault("metadata", {}).update(
        {
            "effectApplied": "Sepia",
            "default-Sepia-intensity": "1",
            "unrelatedTemplate": ["omit"],
        }
    )
    return doc


def recipient(kind):
    doc = owner_document(kind)
    visual(doc)["effects"] = [dict(effectName="CursorHilight", opaque=["retain"])]
    visual(doc).setdefault("metadata", {})["unrelatedRecipient"] = ["retain"]
    doc["sourceBin"][0]["opaqueProcessing"] = ["retain"]
    project.scene_tracks(doc)[0].append(
        dict(
            trackIndex=1,
            medias=[
                dict(
                    id=90,
                    _type="AMFile",
                    start=0,
                    duration=1000,
                    mediaStart=500,
                    mediaDuration=1000,
                    scalar=1,
                    effects=[dict(effectName="Denoise", opaque=["retain audio"])],
                    parameters=dict(volume=0.7),
                )
            ],
        )
    )
    return doc


class RecordingEffectConstructorTests(unittest.TestCase):
    def test_behavior_owner_scope_stays_ordinary_for_donors_recipients_and_lifecycle(self):
        for kind in KINDS:
            for linked in (False, True):
                ordinary = behavior_fixture(linked)
                recording = copy.deepcopy(ordinary)
                owner = project.scene_tracks(recording)[0][0]["medias"][0]
                if linked:
                    owner = owner["video"]
                owner["_type"] = kind
                before = copy.deepcopy(ordinary), copy.deepcopy(recording)
                for clip in (3, 10) if linked else (3,):
                    calls = [
                        lambda: behaviors.add_behavior(recording, clip, ordinary, clip, "fade"),
                        lambda: behaviors.add_behavior(ordinary, clip, recording, clip, "fade"),
                        lambda: behaviors.edit_behavior(
                            recording, clip, "fade", dict(schema_version=1, bypassed=True)
                        ),
                        lambda: behaviors.remove_behavior(recording, clip, "fade"),
                    ]
                    for call in calls:
                        with self.subTest(kind=kind, linked=linked, clip=clip):
                            with self.assertRaisesRegex(ValueError, "verified"):
                                call()
                self.assertEqual((ordinary, recording), before)

    def test_native_template_appends_complete_payload_and_only_selected_reset_metadata(self):
        for kind in KINDS:
            source, dest = template(kind), recipient(kind)
            before = copy.deepcopy(source), copy.deepcopy(dest)
            result = effects.add_effect(dest, 3, source, 3, "Sepia")
            expected = copy.deepcopy(dest)
            visual(expected)["effects"].append(copy.deepcopy(visual(source)["effects"][0]))
            visual(expected)["metadata"].update(
                effectApplied="Sepia", **{"default-Sepia-intensity": "1"}
            )
            self.assertEqual(result, expected)
            self.assertEqual((source, dest), before)
            self.assertIsNone(effects.token_of(visual(result)["effects"][-1]))

    def test_static_templates_transfer_between_clocks_without_rewriting_source_selection(self):
        for kind in KINDS:
            source, dest = template(kind), recipient(kind)
            visual(dest).update(start=9000, duration=5000, mediaStart=2000, scalar="1/2")
            before = copy.deepcopy(dest)
            result = effects.add_effect(dest, 3, source, 3, "Sepia")
            actual = visual(result)["effects"].pop()
            self.assertEqual(actual, visual(source)["effects"][0])
            visual(result)["metadata"] = visual(before)["metadata"]
            self.assertEqual(result, before)

    def test_timed_payloads_keep_frames_edges_resources_and_opaque_fields_verbatim(self):
        for kind in KINDS:
            source, dest = template(kind), recipient(kind)
            effect = visual(source)["effects"][0]
            effect["parameters"]["intensity"]["keyframes"] = [
                dict(
                    time=0,
                    endTime=705600000,
                    duration=705600000,
                    value=1.0,
                    interp="sprg",
                    opaque=["retain frame"],
                )
            ]
            effect["parameters"]["resource"] = "never-follow-this.cube"
            effect["leftEdgeMods"] = [dict(duration=352800000, opaque=["retain edge"])]
            before = copy.deepcopy(source), copy.deepcopy(dest)
            result = effects.add_effect(dest, 3, source, 3, "Sepia")
            self.assertEqual(visual(result)["effects"][-1], effect)
            self.assertEqual(
                visual(result).get("animationTracks"), visual(dest).get("animationTracks")
            )
            self.assertEqual((source, dest), before)
            for field in effects.CLOCK_FIELDS:
                changed = copy.deepcopy(dest)
                visual(changed)[field] = 123456
                with (
                    self.subTest(kind=kind, field=field),
                    self.assertRaisesRegex(ValueError, "clocks"),
                ):
                    effects.add_effect(changed, 3, source, 3, "Sepia")

    def test_static_edit_bypass_and_removal_preserve_complete_audio_cursor_and_child_state(self):
        for kind in KINDS:
            source, dest = template(kind), recipient(kind)
            added = effects.add_effect(dest, 3, source, 3, "Sepia")
            before = copy.deepcopy(added)
            edited = effects.edit_effect(
                added,
                3,
                "Sepia",
                dict(schema_version=1, parameters=dict(intensity="3/4"), bypassed=True),
            )
            expected = copy.deepcopy(added)
            effect = visual(expected)["effects"][-1]
            effect["parameters"]["intensity"]["defaultValue"] = 0.75
            effect["bypassed"] = True
            self.assertEqual(edited, expected)
            self.assertEqual(added, before)
            removed = effects.remove_effect(edited, 3, "Sepia")
            visual(expected)["effects"].pop()
            self.assertEqual(removed, expected)
            self.assertEqual(removed, effects.remove_effect(removed, 3, "Sepia"))
            self.assertEqual(visual(removed)["metadata"]["default-Sepia-intensity"], "1")

    def test_reset_conflicts_and_mismatched_owner_kinds_refuse_without_mutation(self):
        for kind in KINDS:
            source, dest = template(kind), recipient(kind)
            visual(dest)["metadata"]["default-Sepia-intensity"] = "different"
            before = copy.deepcopy(source), copy.deepcopy(dest)
            with self.assertRaisesRegex(ValueError, "reset defaults"):
                effects.add_effect(dest, 3, source, 3, "Sepia")
            self.assertEqual((source, dest), before)
            visual(dest)["metadata"].pop("default-Sepia-intensity")
            visual(dest)["_type"] = "Callout"
            with self.assertRaisesRegex(ValueError, "matching native visual owner"):
                effects.add_effect(dest, 3, source, 3, "Sepia")

    def test_linked_recordings_refuse_as_donors_recipients_and_lifecycle_targets(self):
        for kind in KINDS:
            linked = linked_template(True)
            linked["editRate"] = RATE
            wrapper = project.scene_tracks(linked)[0][0]["medias"][0]
            wrapper["video"]["_type"] = kind
            before = copy.deepcopy(linked)
            for clip in (3, 10):
                calls = [
                    lambda: effects.add_effect(recipient(kind), 3, linked, clip, "Sepia"),
                    lambda: effects.add_effect(linked, clip, template(kind), 3, "Sepia"),
                    lambda: effects.edit_effect(
                        linked, clip, "Sepia", dict(schema_version=1, bypassed=True)
                    ),
                    lambda: effects.remove_effect(linked, clip, "Sepia"),
                ]
                for call in calls:
                    with self.assertRaisesRegex(ValueError, "linked recording"):
                        call()
            self.assertEqual(linked, before)

    def test_new_frozen_stitched_mutations_require_the_verified_build_even_for_absent_effects(self):
        for kind in ("ScreenIMFile", "StitchedMedia"):
            doc = recipient(kind)
            doc.update(
                version="9.0",
                authoringClientName=dict(name="Camtasia", platform="Mac", version="2025.0.3"),
            )
            before = copy.deepcopy(doc)
            with self.assertRaisesRegex(ValueError, "2026.2.4"):
                effects.edit_effect(doc, 3, "Missing", dict(schema_version=1, bypassed=True))
            with self.assertRaisesRegex(ValueError, "2026.2.4"):
                effects.remove_effect(doc, 3, "Missing")
            self.assertEqual(doc, before)

    def test_motion_path_lifecycle_uses_its_dedicated_rotation_contract(self):
        for kind in (*KINDS, "VMFile"):
            doc = template("ScreenVMFile")
            visual(doc)["_type"] = kind
            visual(doc)["effects"][0]["effectName"] = "MediaPath"
            visual(doc)["parameters"]["rotation2"] = 0.0
            before = copy.deepcopy(doc)
            for call in [
                lambda: effects.edit_effect(
                    doc, 3, "MediaPath", dict(schema_version=1, bypassed=True)
                ),
                lambda: effects.remove_effect(doc, 3, "MediaPath"),
            ]:
                with self.assertRaisesRegex(ValueError, "motion_paths.py"):
                    call()
            self.assertEqual(doc, before)

    def test_cli_add_edit_remove_use_installed_capable_paths_and_preserve_inputs(self):
        for kind in KINDS:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                donor, dest, added, edited, removed, spec = [
                    root / name
                    for name in (
                        "donor.json",
                        "dest.json",
                        "added.json",
                        "edited.json",
                        "removed.json",
                        "spec.json",
                    )
                ]
                donor.write_bytes(project.encode_document(template(kind)))
                dest.write_bytes(project.encode_document(recipient(kind)))
                original = donor.read_bytes(), dest.read_bytes()
                common = ["--clip-id", "3", "--effect", "Sepia"]
                add = [
                    "add",
                    str(dest),
                    *common,
                    "--template-project",
                    str(donor),
                    "--template-clip-id",
                    "3",
                    "--output",
                    str(added),
                ]
                for written in (True, False):
                    with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                        self.assertEqual(effects.main(add), 0)
                    report = json.loads(stdout.getvalue())
                    self.assertEqual(report["written"], written)
                    self.assertFalse(report["nativeVerified"])
                spec.write_text(
                    json.dumps(
                        dict(schema_version=1, parameters=dict(intensity="3/4"), bypassed=True)
                    )
                )
                with patch("sys.stdout", new_callable=io.StringIO):
                    self.assertEqual(
                        effects.main(
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
                        effects.main(["remove", str(edited), *common, "--output", str(removed)]), 0
                    )
                result = project.load(removed)[0]
                expected = recipient(kind)
                visual(expected)["metadata"].update(
                    effectApplied="Sepia", **{"default-Sepia-intensity": "1"}
                )
                self.assertEqual(result, expected)
                self.assertEqual((donor.read_bytes(), dest.read_bytes()), original)


if __name__ == "__main__":
    unittest.main()
