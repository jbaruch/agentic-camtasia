from __future__ import annotations

import copy
import unittest

from test_animation_owners import owner_document
from test_animations import visual
from test_motion_paths import linked_document, spec, wrapper
import motion_paths


def sources():
    return [
        (owner_document(kind), 3, kind)
        for kind in ["VMFile", "IMFile", "Callout", "Group", "ScreenVMFile"]
    ] + [(linked_document(), 10, "VMFile")]


class MotionOrientationTests(unittest.TestCase):
    def test_native_bypass_removes_companion_and_enable_restores_typed_or_plain_zero(self):
        for source, clip_id, kind in sources():
            oriented = motion_paths.set_path(source, clip_id, {**spec(), "autoOrient": True})
            frozen = copy.deepcopy(oriented)
            native_zero = (
                dict(type="double", defaultValue=0.0, interp="eioe")
                if kind == "ScreenVMFile"
                else 0.0
            )
            self.assertEqual(visual(oriented)["parameters"]["rotation2"], native_zero)
            expected = copy.deepcopy(oriented)
            for target in motion_paths.visual_targets(expected, clip_id):
                target["effects"][0]["bypassed"] = True
            visual(expected)["parameters"].pop("rotation2")
            bypassed = motion_paths.set_bypass(oriented, clip_id, True)
            self.assertEqual(bypassed, expected)
            self.assertEqual(motion_paths.set_bypass(bypassed, clip_id, False), oriented)
            self.assertEqual(motion_paths.set_bypass(oriented, clip_id, False), oriented)
            self.assertEqual(oriented, frozen)

    def test_orientation_edits_while_bypassed_keep_companion_absent_and_reset_metadata(self):
        for source, clip_id, _ in sources():
            oriented = motion_paths.set_path(source, clip_id, {**spec(), "autoOrient": True})
            bypassed = motion_paths.set_bypass(oriented, clip_id, True)
            off = motion_paths.set_path(bypassed, clip_id, {**spec(), "autoOrient": False})
            on = motion_paths.set_path(off, clip_id, {**spec(), "autoOrient": True})
            self.assertEqual(on, bypassed)
            self.assertNotIn("rotation2", visual(off)["parameters"])
            self.assertEqual(motion_paths.set_path(on, clip_id, spec()), on)
            self.assertEqual(motion_paths.set_bypass(on, clip_id, False), oriented)

    def test_unfamiliar_orientation_or_rotation_refuses_without_mutation(self):
        for source, clip_id, _ in sources():
            oriented = motion_paths.set_path(source, clip_id, {**spec(), "autoOrient": True})
            visual(oriented)["parameters"]["rotation2"] = 0.25
            before = copy.deepcopy(oriented)
            with self.assertRaisesRegex(ValueError, "rotation"):
                motion_paths.set_bypass(oriented, clip_id, True)
            self.assertEqual(oriented, before)
            for node in motion_paths.visual_targets(oriented, clip_id):
                node["effects"][0]["parameters"]["mediaPathAutoOrient"] = True
            before = copy.deepcopy(oriented)
            with self.assertRaisesRegex(ValueError, "orientation"):
                motion_paths.set_bypass(oriented, clip_id, True)
            self.assertEqual(oriented, before)

    def test_linked_changes_keep_audio_sources_tokens_and_unknown_fields(self):
        oriented = motion_paths.set_path(linked_document(), 10, {**spec(), "autoOrient": True})
        for node in [wrapper(oriented), visual(oriented)]:
            node["effects"][0]["future"] = dict(keep=[1, 2])
        before = copy.deepcopy(oriented)
        bypassed = motion_paths.set_bypass(oriented, 3, True)
        self.assertEqual(wrapper(bypassed)["audio"], wrapper(before)["audio"])
        self.assertEqual(bypassed["sourceBin"], before["sourceBin"])
        self.assertEqual(wrapper(bypassed)["metadata"], wrapper(before)["metadata"])
        for node in [wrapper(bypassed), visual(bypassed)]:
            self.assertEqual(node["effects"][0]["metadata"], dict(effectIndex="0"))
            self.assertEqual(node["effects"][0]["future"], dict(keep=[1, 2]))
        self.assertEqual(motion_paths.set_bypass(bypassed, 10, False), before)


if __name__ == "__main__":
    unittest.main()
