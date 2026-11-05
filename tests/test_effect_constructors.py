from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_effects import fixture, node
import effects
import project


def document(linked=False):
    doc = fixture(linked)
    owners = [node(doc)]
    if linked:
        owners.append(node(doc)["video"])
    for owner in owners:
        owner.update(start=0, duration=8000, mediaStart=2000, mediaDuration=12000, scalar="3/2")
    return doc


def template(linked=False):
    doc = document(linked)
    owners = [node(doc), node(doc)["video"]] if linked else [node(doc)]
    for owner in owners:
        owner["effects"] = [
            dict(
                effectName="Sepia",
                category="categoryVisualEffects",
                bypassed=False,
                parameters={
                    "intensity": {
                        "type": "double",
                        "defaultValue": 1.0,
                        "interp": "linr",
                        "uiHints": {"userInterfaceType": 0, "unitType": 0},
                        "keyframes": [],
                    }
                },
                metadata={"effectIndex": "7", "default-Sepia-intensity": "1", "future": ["keep"]},
                opaque={"future": "retained"},
            )
        ]
        owner.setdefault("metadata", {}).update(
            {"effectApplied": "Sepia", "default-Sepia-intensity": "1", "unrelated": "template-only"}
        )
    return doc


def owners(doc, linked):
    return [node(doc), node(doc)["video"]] if linked else [node(doc)]


class EffectConstructorTests(unittest.TestCase):
    def test_static_constructor_appends_full_payload_and_reset_companions_only(self):
        source, destination = template(), document()
        node(destination)["duration"] = 4000
        node(destination)["mediaStart"] = 500
        node(destination)["metadata"] = {"existing": ["retain"], "effectApplied": "Border"}
        before = copy.deepcopy(source), copy.deepcopy(destination)
        result = effects.add_effect(destination, 3, source, 3, "Sepia")
        expected = copy.deepcopy(destination)
        added = copy.deepcopy(node(source)["effects"][0])
        added["metadata"]["effectIndex"] = "1"
        node(expected)["effects"].append(added)
        node(expected)["metadata"].update(effectApplied="Sepia", **{"default-Sepia-intensity": "1"})
        self.assertEqual(result, expected)
        self.assertEqual((source, destination), before)
        self.assertNotIn("unrelated", node(result)["metadata"])
        self.assertEqual(node(result)["effects"][1]["parameters"]["intensity"]["keyframes"], [])

    def test_linked_constructor_preserves_role_payloads_and_allocates_past_audio_tokens(self):
        source, destination = template(True), document(True)
        node(source)["effects"][0]["wrapperFuture"] = [1]
        node(source)["video"]["effects"][0]["videoFuture"] = [2]
        node(destination)["audio"]["effects"] = [
            {"effectName": "NoiseReduction", "metadata": {"effectIndex": "15"}, "opaque": ["audio"]}
        ]
        before = copy.deepcopy(source), copy.deepcopy(destination)
        result = effects.add_effect(destination, 10, source, 10, "Sepia")
        self.assertEqual(result, effects.add_effect(destination, 3, source, 3, "Sepia"))
        self.assertEqual(node(result)["audio"], node(destination)["audio"])
        expected = copy.deepcopy(destination)
        for src, target in zip(owners(source, True), owners(expected, True)):
            addition = copy.deepcopy(src["effects"][0])
            addition["metadata"]["effectIndex"] = "16"
            target["effects"].append(addition)
            target.setdefault("metadata", {}).update(
                effectApplied="Sepia", **{"default-Sepia-intensity": "1"}
            )
        self.assertEqual(result, expected)
        self.assertEqual((source, destination), before)

    def test_complete_resource_and_curve_payloads_survive_with_matching_clocks(self):
        source, destination = template(True), document(True)
        curve = {
            "type": "double",
            "defaultValue": 0.25,
            "interp": "linr",
            "keyframes": [
                {"time": 2000, "endTime": 3500, "duration": 1500, "value": 0.75, "opaque": [1]},
            ],
            "future": {"retain": True},
        }
        for owner in owners(source, True):
            effect = owner["effects"][0]
            effect["parameters"].update(resource="local-owned.cube", intensity=copy.deepcopy(curve))
            effect["leftEdgeMods"] = [
                {
                    "group": "Video",
                    "duration": 1000,
                    "parameters": [{"name": "intensity", "func": "FadeInFunc"}],
                }
            ]
            effect.update(start=0, duration=8000)
        before = copy.deepcopy(source), copy.deepcopy(destination)
        result = effects.add_effect(destination, 10, source, 10, "Sepia")
        for src, target in zip(owners(source, True), owners(result, True)):
            expected = copy.deepcopy(src["effects"][0])
            expected["metadata"]["effectIndex"] = "1"
            self.assertEqual(target["effects"][1], expected)
        self.assertEqual((source, destination), before)

    def test_timed_effects_refuse_clock_changes_or_missing_fields_without_mutation(self):
        for timed in [
            {"leftEdgeMods": []},
            {"duration": 4000},
            {"leftEdgeMods": [{"duration": 1000}]},
            {
                "parameters": {
                    "intensity": {"type": "double", "keyframes": [{"time": 2000, "value": 1}]}
                }
            },
        ]:
            source = template()
            node(source)["effects"][0].update(copy.deepcopy(timed))
            # An empty edge list carries no timing and can move across clocks.
            if timed == {"leftEdgeMods": []}:
                dest = document()
                node(dest)["duration"] = 4000
                effects.add_effect(dest, 3, source, 3, "Sepia")
                continue
            for key in effects.CLOCK_FIELDS:
                for missing in [False, True]:
                    dest = document()
                    if missing:
                        node(dest).pop(key)
                    else:
                        node(dest)[key] = 1234
                    before = copy.deepcopy(source), copy.deepcopy(dest)
                    with (
                        self.subTest(timed=timed, key=key, missing=missing),
                        self.assertRaisesRegex(ValueError, "clocks"),
                    ):
                        effects.add_effect(dest, 3, source, 3, "Sepia")
                    self.assertEqual((source, dest), before)

    def test_timed_linked_effects_check_both_wrapper_and_visual_clocks(self):
        source, destination = template(True), document(True)
        for owner in owners(source, True):
            owner["effects"][0]["rightEdgeMods"] = [{"duration": 1000}]
        node(destination)["duration"] = 6000
        with self.assertRaisesRegex(ValueError, "clocks"):
            effects.add_effect(destination, 10, source, 10, "Sepia")

    def test_same_project_duplicate_creation_keeps_old_tokens_and_order(self):
        doc = template()
        before = copy.deepcopy(doc)
        result = effects.add_effect(doc, 3, doc, 3, "Sepia", template_token="7")
        self.assertEqual(node(result)["effects"][0], node(doc)["effects"][0])
        self.assertEqual([effects.token_of(e) for e in node(result)["effects"]], ["7", "8"])
        self.assertEqual(doc, before)

    def test_repeated_template_names_require_their_stable_token(self):
        source = template()
        second = copy.deepcopy(node(source)["effects"][0])
        second["metadata"]["effectIndex"] = "12"
        second["parameters"]["intensity"]["defaultValue"] = 0.5
        node(source)["effects"].append(second)
        with self.assertRaisesRegex(ValueError, "unique effectIndex"):
            effects.add_effect(document(), 3, source, 3, "Sepia")
        result = effects.add_effect(document(), 3, source, 3, "Sepia", template_token="12")
        self.assertEqual(node(result)["effects"][1]["parameters"]["intensity"]["defaultValue"], 0.5)

    def test_reset_companions_preserve_unrelated_owner_metadata_and_refuse_conflicts(self):
        source = template()
        node(source)["metadata"].update(**{"default-easeIn": "0", "default-easeOut": "0"})
        result = effects.add_effect(document(), 3, source, 3, "Sepia")
        self.assertEqual(
            node(result)["metadata"],
            {
                "effectApplied": "Sepia",
                "default-Sepia-intensity": "1",
                "default-easeIn": "0",
                "default-easeOut": "0",
            },
        )
        for key in ["default-Sepia-intensity", "default-easeIn", "default-easeOut"]:
            dest = document()
            node(dest)["metadata"] = {key: "different", "retain": [1]}
            before = copy.deepcopy(source), copy.deepcopy(dest)
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "reset defaults"):
                effects.add_effect(dest, 3, source, 3, "Sepia")
            self.assertEqual((source, dest), before)
        node(source)["metadata"]["effectApplied"] = "Border"
        with self.assertRaisesRegex(ValueError, "last native applied"):
            effects.add_effect(document(), 3, source, 3, "Sepia")

    def test_constructor_refuses_unindexed_duplicate_or_noncanonical_destination_tokens(self):
        for bad in [None, "01", "-1", 3]:
            dest = document()
            metadata = node(dest)["effects"][0]["metadata"]
            if bad is None:
                metadata.pop("effectIndex")
            else:
                metadata["effectIndex"] = bad
            before = copy.deepcopy(dest)
            with self.subTest(bad=bad), self.assertRaises(ValueError):
                effects.add_effect(dest, 3, template(), 3, "Sepia")
            self.assertEqual(dest, before)
        dest = document()
        node(dest)["effects"].append(copy.deepcopy(node(dest)["effects"][0]))
        with self.assertRaisesRegex(ValueError, "unique native"):
            effects.add_effect(dest, 3, template(), 3, "Sepia")

    def test_existing_equal_reset_defaults_keep_their_original_representation(self):
        source, dest = template(), document()
        node(source)["metadata"]["default-Sepia-intensity"] = 1.0
        node(dest)["metadata"] = {"default-Sepia-intensity": 1}
        result = effects.add_effect(dest, 3, source, 3, "Sepia")
        self.assertIs(type(node(result)["metadata"]["default-Sepia-intensity"]), int)

    def test_empty_destination_allocates_zero_and_does_not_require_source_token(self):
        source, dest = template(), document()
        node(source)["effects"][0]["metadata"].pop("effectIndex")
        node(dest).pop("effects")
        result = effects.add_effect(dest, 3, source, 3, "Sepia")
        self.assertEqual(effects.token_of(node(result)["effects"][0]), "0")

    def test_constructor_rejects_build_rate_owner_or_link_layout_mismatches(self):
        for change in ["build", "format", "rate", "type", "linked", "audio", "recording"]:
            source, dest, target_id = template(), document(), 3
            if change == "build":
                source.update(
                    version="9.0",
                    authoringClientName={
                        "name": "Camtasia",
                        "platform": "Mac",
                        "version": "2025.0.3",
                    },
                )
            elif change == "format":
                dest["version"] = "9.0"
            elif change == "rate":
                dest["editRate"] = 2000
            elif change == "type":
                node(dest)["_type"] = "IMFile"
            elif change == "linked":
                dest, target_id = document(True), 10
            elif change == "audio":
                dest, target_id = document(True), 11
            else:
                node(dest)["_type"] = "ScreenVMFile"
            before = copy.deepcopy(source), copy.deepcopy(dest)
            with self.subTest(change=change), self.assertRaises(ValueError):
                effects.add_effect(dest, target_id, source, 3, "Sepia")
            self.assertEqual((source, dest), before)

    def test_broken_source_mirrors_metadata_or_category_are_refused(self):
        for change in [
            "missing",
            "conflict",
            "metadata",
            "category",
            "parameters",
            "owner-metadata",
        ]:
            source = template(True)
            if change == "missing":
                node(source)["effects"] = []
            elif change == "conflict":
                node(source)["effects"][0]["bypassed"] = True
            elif change == "owner-metadata":
                node(source)["metadata"] = []
            else:
                for owner in owners(source, True):
                    owner["effects"][0][change] = []
            before = copy.deepcopy(source)
            with self.subTest(change=change), self.assertRaises(ValueError):
                effects.add_effect(document(True), 10, source, 10, "Sepia")
            self.assertEqual(source, before)

    def test_motion_path_creation_routes_to_its_rotation_companion_helper(self):
        source, dest = template(), document()
        node(source)["effects"][0]["effectName"] = "MediaPath"
        node(source)["effects"][0]["parameters"] = {"mediaPathAutoOrient": 1}
        before = copy.deepcopy(source), copy.deepcopy(dest)
        with self.assertRaisesRegex(ValueError, "motion_paths.py.*rotation"):
            effects.add_effect(dest, 3, source, 3, "MediaPath")
        self.assertEqual((source, dest), before)

    def test_construction_does_not_extend_to_the_legacy_static_editor_profile(self):
        source, dest = template(), document()
        for doc in [source, dest]:
            doc.update(
                version="9.0",
                authoringClientName={"name": "Camtasia", "platform": "Mac", "version": "2025.0.3"},
            )
        with self.assertRaisesRegex(ValueError, "2026.2.4"):
            effects.add_effect(dest, 3, source, 3, "Sepia")

    def test_cli_stages_copies_without_touching_project_template_or_existing_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, native, output = [
                root / x for x in ["source.json", "template.json", "candidate.json"]
            ]
            source.write_bytes(project.encode_document(document(True)))
            native.write_bytes(project.encode_document(template(True)))
            before = source.read_bytes(), native.read_bytes()
            args = [
                "add",
                str(source),
                "--clip-id",
                "10",
                "--effect",
                "Sepia",
                "--template-project",
                str(native),
                "--template-clip-id",
                "10",
                "--template-effect-token",
                "7",
                "--output",
                str(output),
            ]
            for written in [True, False]:
                with patch("sys.stdout", new_callable=io.StringIO) as stream:
                    self.assertEqual(effects.main(args), 0)
                report = json.loads(stream.getvalue())
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
                self.assertEqual(
                    [(r["arrayPosition"], r["effectToken"]) for r in report["effects"]],
                    [(0, "0"), (1, "1"), (0, "0"), (1, "1")],
                )
            for path in [source, native]:
                with patch("sys.stderr", io.StringIO()):
                    self.assertEqual(effects.main([*args[:-1], str(path)]), 1)
            output.write_text("occupied")
            with patch("sys.stderr", io.StringIO()):
                self.assertEqual(effects.main(args), 1)
            self.assertEqual(output.read_text(), "occupied")
            self.assertEqual((source.read_bytes(), native.read_bytes()), before)


if __name__ == "__main__":
    unittest.main()
