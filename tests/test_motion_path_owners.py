from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

from test_animation_owners import owner_document
from test_animations import visual
from test_motion_paths import linked_document, spec, wrapper
import motion_paths
import project


class MotionOwnerTests(unittest.TestCase):
    def test_direct_constructors_have_one_effect_and_retain_the_entire_owner(self):
        for kind in ["VMFile", "IMFile", "Callout", "Group", "ScreenVMFile"]:
            doc = owner_document(kind)
            frozen = copy.deepcopy(doc)
            result = motion_paths.set_path(doc, 3, spec())
            node = visual(result)
            expected = {
                "effectName": "MediaPath",
                "category": "categoryVisualEffects",
                "bypassed": False,
                "parameters": {
                    "mediaPathAutoOrient": 0,
                    "mediaLocation": {
                        "type": "point",
                        "keyframes": [
                            {"time": 1000, "endTime": 1000, "duration": 0, "value": [0, 0, 0]},
                            {
                                "time": 2000,
                                "endTime": 2000,
                                "duration": 0,
                                "value": [256, 144, 0],
                                "interp": {"bezier": [[128, 0, 0], [128, 144, 0], "eioe"]},
                            },
                        ],
                    },
                },
            }
            with self.subTest(kind=kind):
                self.assertEqual(node["effects"], [expected])
                self.assertNotIn("metadata", node["effects"][0])
                self.assertEqual(node["metadata"]["effectApplied"], "MediaPath")
                for key in ["def", "tracks", "parameters", "attributes", "src", "mediaDuration"]:
                    self.assertEqual(node.get(key), visual(doc).get(key))
                self.assertEqual(result["sourceBin"], doc["sourceBin"])
                self.assertEqual(doc, frozen)

    def test_bypass_and_enable_preserve_every_field_except_effect_switches(self):
        for source, clip_id in [
            (linked_document(), 10),
            (owner_document("Group"), 3),
            (owner_document("ScreenVMFile"), 3),
        ]:
            before = motion_paths.set_path(source, clip_id, spec())
            expected = copy.deepcopy(before)
            for node in motion_paths.visual_targets(expected, clip_id):
                node["effects"][0]["bypassed"] = True
            bypassed = motion_paths.set_bypass(before, clip_id, True)
            self.assertEqual(bypassed, expected)
            self.assertEqual(motion_paths.set_bypass(bypassed, clip_id, False), before)
            self.assertEqual(motion_paths.set_bypass(bypassed, clip_id, True), bypassed)

    def test_removal_retains_reset_metadata_child_audio_and_static_geometry(self):
        for kind in ["VMFile", "IMFile", "Callout", "Group", "ScreenVMFile"]:
            source = owner_document(kind)
            animated = motion_paths.set_path(source, 3, {**spec(), "autoOrient": True})
            removed = motion_paths.remove_path(animated, 3)
            expected = copy.deepcopy(source)
            visual(expected).setdefault("metadata", {})["effectApplied"] = "MediaPath"
            visual(expected)["metadata"]["default-MediaPath-mediaPathAutoOrient"] = "0"
            with self.subTest(kind=kind):
                self.assertEqual(removed, expected)
                self.assertNotIn("rotation2", visual(removed)["parameters"])
                self.assertEqual(motion_paths.remove_path(removed, 3), removed)

    def test_linked_removal_keeps_tokens_order_and_opaque_other_effects(self):
        doc = motion_paths.set_path(linked_document(), 3, {**spec(), "autoOrient": True})
        first = {"effectName": "Border", "metadata": {"effectIndex": "1"}, "opaque": {"keep": 1}}
        last = {"effectName": "Reflection", "metadata": {"effectIndex": "3"}}
        for node in [wrapper(doc), visual(doc)]:
            node["effects"] = [copy.deepcopy(first), node["effects"][0], copy.deepcopy(last)]
        result = motion_paths.remove_path(doc, 10)
        self.assertEqual(wrapper(result)["effects"], [first, last])
        self.assertEqual(visual(result)["effects"], [first, last])
        self.assertEqual(wrapper(result)["audio"], wrapper(doc)["audio"])
        self.assertEqual(wrapper(result)["metadata"], wrapper(doc)["metadata"])

    def test_recording_orientation_uses_the_native_typed_zero_and_preserves_cursor(self):
        doc = owner_document("ScreenVMFile")
        cursor = {
            "type": "double",
            "defaultValue": 1,
            "keyframes": [{"time": 100, "endTime": 100, "duration": 0, "value": 2}],
        }
        visual(doc)["parameters"]["cursorScale"] = cursor
        result = motion_paths.set_path(doc, 3, {**spec(), "autoOrient": True})
        self.assertEqual(
            visual(result)["parameters"]["rotation2"],
            {"type": "double", "defaultValue": 0.0, "interp": "eioe"},
        )
        self.assertEqual(visual(result)["parameters"]["cursorScale"], cursor)
        off = motion_paths.set_path(result, 3, {**spec(), "autoOrient": False})
        self.assertNotIn("rotation2", visual(off)["parameters"])
        self.assertEqual(visual(off)["parameters"]["cursorScale"], cursor)

    def test_unfamiliar_rotation_companions_block_removal_without_mutation(self):
        for value in [
            False,
            0.25,
            {"type": "double", "defaultValue": False, "interp": "eioe"},
            {"type": "double", "defaultValue": 0.0, "interp": "eioe", "opaque": 1},
        ]:
            doc = motion_paths.set_path(
                owner_document("ScreenVMFile"), 3, {**spec(), "autoOrient": True}
            )
            visual(doc)["parameters"]["rotation2"] = value
            frozen = copy.deepcopy(doc)
            with self.subTest(value=value), self.assertRaisesRegex(ValueError, "rotation"):
                motion_paths.remove_path(doc, 3)
            self.assertEqual(doc, frozen)

    def test_retimed_group_curve_keeps_child_clocks_and_initial_volume(self):
        doc = owner_document("Group")
        visual(doc).update(
            start=1000, mediaStart=0, scalar="1/2", duration=4000, mediaDuration=8000
        )
        result = motion_paths.set_path(doc, 3, spec())
        frames = visual(result)["effects"][0]["parameters"]["mediaLocation"]["keyframes"]
        self.assertEqual([f["time"] for f in frames], [2000, 4000])
        self.assertEqual(visual(result)["tracks"], visual(doc)["tracks"])
        self.assertEqual(visual(motion_paths.remove_path(result, 3))["duration"], 4000)
        self.assertEqual(visual(result)["parameters"]["volume"], 0.8)

    def test_absent_path_invalid_switch_and_conflicting_linked_mirrors_are_refused(self):
        with self.assertRaisesRegex(ValueError, "add a Motion Path"):
            motion_paths.set_bypass(owner_document("Callout"), 3, True)
        invalid_switch: Any = 1
        with self.assertRaisesRegex(ValueError, "boolean"):
            motion_paths.set_bypass(owner_document("Callout"), 3, invalid_switch)
        for action in [
            lambda d: motion_paths.set_bypass(d, 3, True),
            lambda d: motion_paths.remove_path(d, 3),
        ]:
            doc = motion_paths.set_path(linked_document(), 3, spec())
            wrapper(doc)["effects"][0]["metadata"]["effectIndex"] = "9"
            with self.assertRaisesRegex(ValueError, "tokens"):
                action(doc)

    def test_single_point_is_explicit_and_preserves_the_other_geometry(self):
        doc = owner_document("VMFile")
        result = motion_paths.set_path(
            doc, 3, dict(schema_version=1, points=[dict(time=1, position=[128, 72, 0])])
        )
        self.assertEqual(
            visual(result)["effects"][0]["parameters"]["mediaLocation"]["keyframes"],
            [{"time": 1000, "endTime": 1000, "duration": 0, "value": [128, 72, 0]}],
        )
        self.assertEqual(visual(result)["parameters"], visual(doc)["parameters"])

    def test_lifecycle_cli_stages_and_keeps_original_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, bypassed, enabled, removed = [
                root / n for n in ["source.json", "bypass.json", "enabled.json", "removed.json"]
            ]
            doc = motion_paths.set_path(owner_document("Callout"), 3, spec())
            raw = project.encode_document(doc)
            source.write_bytes(raw)
            for args in [
                [
                    "set-bypass",
                    str(source),
                    "--clip-id",
                    "3",
                    "--bypass",
                    "--output",
                    str(bypassed),
                ],
                [
                    "set-bypass",
                    str(bypassed),
                    "--clip-id",
                    "3",
                    "--no-bypass",
                    "--output",
                    str(enabled),
                ],
                ["remove-path", str(enabled), "--clip-id", "3", "--output", str(removed)],
            ]:
                with patch("sys.stdout", new_callable=io.StringIO) as out:
                    self.assertEqual(motion_paths.main(args), 0)
                self.assertFalse(json.loads(out.getvalue())["nativeVerified"])
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(project.load(enabled)[0], doc)
            self.assertEqual(visual(project.load(removed)[0])["effects"], [])


if __name__ == "__main__":
    unittest.main()
