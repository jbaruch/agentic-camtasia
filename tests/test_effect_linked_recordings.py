from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_matte_linked_recordings import fixture, wrapper
from test_animations import visual
import behaviors
import effect_curves
import effects
import project


def native_template():
    doc = fixture()
    effect = dict(
        effectName="Sepia",
        bypassed=False,
        category="categoryVisualEffects",
        parameters=dict(intensity=1.0),
        metadata=dict(effectIndex="0"),
    )
    for owner in (wrapper(doc), visual(doc)):
        owner["effects"] = [copy.deepcopy(effect)]
    wrapper(doc)["metadata"]["effectApplied"] = "Sepia"
    return doc


class LinkedRecordingEffectTests(unittest.TestCase):
    def test_native_constructor_matches_complete_document_and_aliases_preserve_inputs(self):
        source, dest = native_template(), fixture()
        before = copy.deepcopy(source), copy.deepcopy(dest)
        expected = copy.deepcopy(dest)
        for owner in (wrapper(expected), visual(expected)):
            owner["effects"] = [
                dict(
                    effectName="Sepia",
                    bypassed=False,
                    category="categoryVisualEffects",
                    parameters=dict(intensity=1.0),
                    metadata=dict(effectIndex="0"),
                )
            ]
        wrapper(expected)["metadata"]["effectApplied"] = "Sepia"
        for donor_id in (10, 3):
            for recipient_id in (10, 3):
                self.assertEqual(
                    effects.add_effect(dest, recipient_id, source, donor_id, "Sepia"), expected
                )
        self.assertEqual((source, dest), before)
        self.assertEqual(wrapper(expected)["audio"], wrapper(dest)["audio"])
        self.assertEqual(expected["sourceBin"], dest["sourceBin"])

    def test_role_specific_opaque_effect_fields_and_selected_reset_companions_copy(self):
        source, dest = native_template(), fixture()
        wrapper(source)["metadata"].update(
            {"default-Sepia-intensity": "1", "unrelatedTemplate": "omit"}
        )
        for owner, role in ((wrapper(source), "wrapper"), (visual(source), "video")):
            effect = owner["effects"][0]
            effect["parameters"]["intensity"] = 0.5
            effect["metadata"]["opaque"] = [role]
            effect["opaqueEffect"] = {"role": role}
        expected = copy.deepcopy(dest)
        for target, original in (
            (wrapper(expected), wrapper(source)),
            (visual(expected), visual(source)),
        ):
            target["effects"] = copy.deepcopy(original["effects"])
        wrapper(expected)["metadata"].update(
            {"effectApplied": "Sepia", "default-Sepia-intensity": "1"}
        )
        self.assertEqual(effects.add_effect(dest, 10, source, 3, "Sepia"), expected)

    def test_new_token_avoids_audio_and_other_effects_without_reordering(self):
        source, dest = native_template(), fixture()
        for owner in (wrapper(dest), visual(dest)):
            owner["effects"] = [dict(effectName="Other", metadata=dict(effectIndex="2"))]
        wrapper(dest)["audio"]["effects"] = [
            dict(effectName="AudioOther", metadata=dict(effectIndex="7"), opaque=["keep"])
        ]
        expected = copy.deepcopy(dest)
        for target, original in (
            (wrapper(expected), wrapper(source)),
            (visual(expected), visual(source)),
        ):
            effect = copy.deepcopy(original["effects"][0])
            effect["metadata"]["effectIndex"] = "8"
            target["effects"].append(effect)
        wrapper(expected)["metadata"]["effectApplied"] = "Sepia"
        self.assertEqual(effects.add_effect(dest, 3, source, 10, "Sepia"), expected)

    def test_static_template_retains_recipient_trim_speed_and_audio_clocks(self):
        source, dest = native_template(), fixture()
        for owner in (wrapper(dest), visual(dest), wrapper(dest)["audio"]):
            owner.update(
                start=0,
                duration=2116800000,
                mediaStart=705600000,
                mediaDuration=2116800000,
                scalar=1,
            )
        expected = copy.deepcopy(dest)
        for owner in (wrapper(expected), visual(expected)):
            owner["effects"] = copy.deepcopy(wrapper(source)["effects"])
        wrapper(expected)["metadata"]["effectApplied"] = "Sepia"
        self.assertEqual(effects.add_effect(dest, 10, source, 10, "Sepia"), expected)

    def test_timed_template_copies_complete_payload_only_with_matching_clocks(self):
        source, dest = native_template(), fixture()
        for owner in (wrapper(source), visual(source)):
            owner["effects"][0]["parameters"]["intensity"] = dict(
                type="double",
                defaultValue=0.0,
                keyframes=[
                    dict(
                        time=1411200000,
                        endTime=2822400000,
                        duration=1411200000,
                        value=1.0,
                        interp="linr",
                    )
                ],
            )
        result = effects.add_effect(dest, 10, source, 10, "Sepia")
        self.assertEqual(wrapper(result)["effects"], wrapper(source)["effects"])
        self.assertEqual(visual(result)["animationTracks"], visual(dest)["animationTracks"])
        before = copy.deepcopy(source), copy.deepcopy(dest)
        for field in effects.CLOCK_FIELDS:
            changed = copy.deepcopy(dest)
            for owner in (wrapper(changed), visual(changed)):
                owner[field] = 2 if field == "scalar" else owner[field] + 1
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "matching complete"):
                effects.add_effect(changed, 3, source, 3, "Sepia")
        self.assertEqual((source, dest), before)

    def test_half_edit_bypass_remove_and_repeat_remove_preserve_complete_payload(self):
        doc = native_template()
        wrapper(doc)["metadata"]["default-Sepia-intensity"] = "1"
        before = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        for owner in (wrapper(expected), visual(expected)):
            owner["effects"][0]["parameters"]["intensity"] = 0.5
        half = effects.edit_effect(
            doc, 3, "Sepia", dict(schema_version=1, parameters=dict(intensity=0.5))
        )
        self.assertEqual(half, expected)
        for owner in (wrapper(expected), visual(expected)):
            owner["effects"][0]["bypassed"] = True
        bypass = effects.edit_effect(half, 10, "Sepia", dict(schema_version=1, bypassed=True))
        self.assertEqual(bypass, expected)
        for owner in (wrapper(expected), visual(expected)):
            owner["effects"] = []
        removed = effects.remove_effect(bypass, 3, "Sepia")
        self.assertEqual(removed, expected)
        self.assertEqual(effects.remove_effect(removed, 10, "Sepia"), removed)
        self.assertEqual(doc, before)

    def test_repeated_names_need_explicit_stable_selector_and_leave_other_token_unchanged(self):
        doc = native_template()
        for owner in (wrapper(doc), visual(doc)):
            duplicate = copy.deepcopy(owner["effects"][0])
            duplicate["metadata"]["effectIndex"] = "4"
            owner["effects"].append(duplicate)
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "unique effectIndex"):
            effects.remove_effect(doc, 10, "Sepia")
        expected = copy.deepcopy(doc)
        for owner in (wrapper(expected), visual(expected)):
            owner["effects"][1]["bypassed"] = True
        result = effects.edit_effect(
            doc, 3, "Sepia", dict(schema_version=1, bypassed=True), token="4"
        )
        self.assertEqual(result, expected)
        self.assertEqual(doc, before)

    def test_missing_conflicting_and_duplicate_mirrors_refuse_without_mutation(self):
        for change in ("missing", "token", "controls", "duplicate-token", "missing-token"):
            doc = native_template()
            if change == "missing":
                visual(doc)["effects"] = []
            elif change == "token":
                visual(doc)["effects"][0]["metadata"]["effectIndex"] = "1"
            elif change == "controls":
                visual(doc)["effects"][0]["parameters"]["intensity"] = 0.5
            elif change == "duplicate-token":
                visual(doc)["effects"].append(copy.deepcopy(visual(doc)["effects"][0]))
            else:
                for owner in (wrapper(doc), visual(doc)):
                    owner["effects"][0]["metadata"].pop("effectIndex")
            before = copy.deepcopy(doc)
            with self.subTest(change=change), self.assertRaises(ValueError):
                effects.edit_effect(doc, 10, "Sepia", dict(schema_version=1, bypassed=True))
            self.assertEqual(doc, before)

    def test_complete_matching_clocks_are_required_on_donor_and_recipient(self):
        source, dest = native_template(), fixture()
        for field in effects.CLOCK_FIELDS:
            for change in ("missing", "conflict", "boolean"):
                for role in ("source", "destination"):
                    a, b = copy.deepcopy(source), copy.deepcopy(dest)
                    selected = a if role == "source" else b
                    if change == "missing":
                        visual(selected).pop(field)
                    else:
                        visual(selected)[field] = (
                            True
                            if change == "boolean"
                            else 2
                            if field == "scalar"
                            else visual(selected)[field] + 1
                        )
                    before = copy.deepcopy(a), copy.deepcopy(b)
                    with (
                        self.subTest(field=field, change=change, role=role),
                        self.assertRaises(ValueError),
                    ):
                        effects.add_effect(b, 10, a, 3, "Sepia")
                    self.assertEqual((a, b), before)

    def test_unknown_audio_bindings_and_nonpositive_clocks_refuse_all_lifecycle_paths(self):
        for change in (
            "missing-audio",
            "wrong-kind",
            "wrong-source",
            "bool-source",
            "missing-source",
            "rate",
            "speed",
        ):
            doc = native_template()
            if change == "missing-audio":
                wrapper(doc).pop("audio")
            elif change == "wrong-kind":
                wrapper(doc)["audio"]["_type"] = "VMFile"
            elif change in ("wrong-source", "bool-source"):
                wrapper(doc)["audio"]["src"] = True if change == "bool-source" else 2
            elif change == "missing-source":
                visual(doc).pop("src")
            elif change == "rate":
                doc["editRate"] = 0
            else:
                for owner in (wrapper(doc), visual(doc)):
                    owner["scalar"] = 0
            before = copy.deepcopy(doc)
            for operation in (
                lambda: effects.add_effect(doc, 10, native_template(), 10, "Sepia"),
                lambda: effects.edit_effect(doc, 3, "Sepia", dict(schema_version=1, bypassed=True)),
                lambda: effects.remove_effect(doc, 10, "Sepia"),
            ):
                with self.subTest(change=change), self.assertRaises(ValueError):
                    operation()
                self.assertEqual(doc, before)

    def test_unsupported_linked_variants_scenes_builds_and_other_feature_callers_refuse(self):
        for change in ("held", "stitched", "nested", "scenes", "build"):
            doc = native_template()
            if change in ("held", "stitched"):
                visual(doc)["_type"] = "ScreenIMFile" if change == "held" else "StitchedMedia"
            elif change == "nested":
                old = wrapper(doc)
                project.scene_tracks(doc)[0][0]["medias"] = [
                    dict(id=20, _type="Group", tracks=[dict(trackIndex=0, medias=[old])])
                ]
            elif change == "scenes":
                doc["timeline"]["sceneTrack"]["scenes"].append(dict(csml=dict(tracks=[])))
            else:
                doc["version"] = "9.0"
                doc["authoringClientName"]["version"] = "2025.0.3"
            with self.subTest(change=change), self.assertRaises(ValueError):
                effects.remove_effect(doc, 3, "Sepia")
        doc = native_template()
        with self.assertRaisesRegex(ValueError, "linked recording"):
            effects.constructor_owners(doc, 3, visual_types=effects.EFFECT_TYPES)
        with self.assertRaisesRegex(ValueError, "linked recording"):
            behaviors.behavior_owners(doc, 3)
        with self.assertRaisesRegex(ValueError, "linked recording effect-curve"):
            effect_curves.selected(doc, 3, "Sepia", None)

    def test_conflicting_reset_defaults_and_flattening_animated_parameters_refuse(self):
        source, dest = native_template(), fixture()
        wrapper(source)["metadata"]["default-Sepia-intensity"] = "1"
        wrapper(dest)["metadata"]["default-Sepia-intensity"] = "0.5"
        with self.assertRaisesRegex(ValueError, "conflicting existing reset"):
            effects.add_effect(dest, 10, source, 10, "Sepia")
        for owner in (wrapper(source), visual(source)):
            owner["effects"][0]["parameters"]["intensity"] = dict(
                type="double",
                defaultValue=0,
                keyframes=[
                    dict(
                        time=1411200000,
                        endTime=2822400000,
                        duration=1411200000,
                        value=1,
                        interp="linr",
                    )
                ],
            )
        before = copy.deepcopy(source)
        with self.assertRaisesRegex(ValueError, "preserve animated"):
            effects.edit_effect(
                source, 3, "Sepia", dict(schema_version=1, parameters=dict(intensity=0.5))
            )
        self.assertEqual(source, before)

    def test_cli_constructor_edit_bypass_remove_repeat_and_input_preservation(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            src, dst, candidate, spec, edited, removed = [
                root / name
                for name in (
                    "source.json",
                    "destination.json",
                    "candidate.json",
                    "spec.json",
                    "edited.json",
                    "removed.json",
                )
            ]
            src.write_bytes(project.encode_document(native_template()))
            dst.write_bytes(project.encode_document(fixture()))
            original = src.read_bytes(), dst.read_bytes()
            add = [
                "add",
                str(dst),
                "--clip-id",
                "10",
                "--effect",
                "Sepia",
                "--template-project",
                str(src),
                "--template-clip-id",
                "3",
                "--output",
                str(candidate),
            ]
            for written in (True, False):
                with patch("sys.stdout", new_callable=io.StringIO) as stream:
                    self.assertEqual(effects.main(add), 0)
                report = json.loads(stream.getvalue())
                self.assertEqual(
                    (report["schema_version"], report["owner"]), (1, "camtasia-effects")
                )
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
            spec.write_text(
                json.dumps(dict(schema_version=1, parameters=dict(intensity=0.5), bypassed=True))
            )
            for command in (
                [
                    "set",
                    str(candidate),
                    "--clip-id",
                    "3",
                    "--effect",
                    "Sepia",
                    "--spec",
                    str(spec),
                    "--output",
                    str(edited),
                ],
                [
                    "remove",
                    str(edited),
                    "--clip-id",
                    "10",
                    "--effect",
                    "Sepia",
                    "--output",
                    str(removed),
                ],
            ):
                with patch("sys.stdout", new_callable=io.StringIO):
                    self.assertEqual(effects.main(command), 0)
            expected = fixture()
            wrapper(expected)["metadata"]["effectApplied"] = "Sepia"
            self.assertEqual(project.load(removed)[0], expected)
            self.assertEqual((src.read_bytes(), dst.read_bytes()), original)

    def test_all_help_responses_emit_versioned_json(self):
        for command in ([], ["inspect"], ["add"], ["set"], ["remove"]):
            with (
                patch("sys.stdout", new_callable=io.StringIO) as stream,
                self.assertRaises(SystemExit) as raised,
            ):
                effects.main([*command, "--help"])
            self.assertEqual(raised.exception.code, 0)
            response = json.loads(stream.getvalue())
            self.assertEqual(
                (response["schema_version"], response["owner"], response["ok"]),
                (1, "camtasia-effects", True),
            )
            self.assertIn("usage:", response["help"])


if __name__ == "__main__":
    unittest.main()
