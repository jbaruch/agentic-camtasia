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
import hotspots
import motion_paths
import project


def spec():
    return dict(
        schema_version=1,
        points=[
            dict(time=2, position=[0, 0, 0]),
            dict(
                time=3,
                position=[256, 144, 0],
                interpolation=dict(bezier=[[128, 0, 0], [128, 144, 0], "eioe"]),
            ),
        ],
    )


class MotionFreezeTests(unittest.TestCase):
    def test_native_five_owner_speed_cases_keep_exact_local_or_source_clocks(self):
        for kind, scalar, times in [
            ("ScreenIMFile", 1, [1411200000, 2116800000]),
            ("ScreenIMFile", "1/2", [2822400000, 4233600000]),
            ("ScreenIMFile", 2, [705600000, 1058400000]),
            ("StitchedMedia", 1, [1411200000, 2116800000]),
            ("StitchedMedia", "1/2", [2822400000, 4233600000]),
        ]:
            doc = owner_document(kind)
            visual(doc)["scalar"] = scalar
            if kind == "ScreenIMFile":
                visual(doc)["mediaStart"] = 2822400000
            original = copy.deepcopy(doc)
            result = motion_paths.set_path(doc, 3, spec())
            expected = dict(
                effectName="MediaPath",
                category="categoryVisualEffects",
                bypassed=False,
                parameters=dict(
                    mediaPathAutoOrient=0,
                    mediaLocation=dict(
                        type="point",
                        keyframes=[
                            dict(time=times[0], endTime=times[0], duration=0, value=[0, 0, 0]),
                            dict(
                                time=times[1],
                                endTime=times[1],
                                duration=0,
                                value=[256, 144, 0],
                                interp=dict(bezier=[[128, 0, 0], [128, 144, 0], "eioe"]),
                            ),
                        ],
                    ),
                ),
            )
            self.assertEqual(visual(result)["effects"], [expected])
            self.assertEqual(visual(result)["parameters"], visual(doc)["parameters"])
            for key in ["medias", "mediaStart", "mediaDuration", "duration", "scalar", "start"]:
                self.assertEqual(visual(result).get(key), visual(doc).get(key))
            self.assertEqual(result["sourceBin"], doc["sourceBin"])
            self.assertEqual(doc, original)

    def test_native_orientation_bypass_and_removal_preserve_child_cursor_and_reset_state(self):
        for kind in ["ScreenIMFile", "StitchedMedia"]:
            doc = owner_document(kind)
            oriented = motion_paths.set_path(doc, 3, {**spec(), "autoOrient": True})
            self.assertEqual(visual(oriented)["parameters"]["rotation2"], 0.0)
            bypassed = motion_paths.set_bypass(oriented, 3, True)
            expected = copy.deepcopy(oriented)
            visual(expected)["effects"][0]["bypassed"] = True
            visual(expected)["parameters"].pop("rotation2")
            self.assertEqual(bypassed, expected)
            self.assertEqual(motion_paths.set_bypass(bypassed, 3, False), oriented)
            off = motion_paths.set_path(oriented, 3, {**spec(), "autoOrient": False})
            self.assertNotIn("rotation2", visual(off)["parameters"])
            expected = copy.deepcopy(doc)
            visual(expected).setdefault("metadata", {}).update(
                effectApplied="MediaPath", **{"default-MediaPath-mediaPathAutoOrient": "0"}
            )
            self.assertEqual(motion_paths.remove_path(oriented, 3), expected)
            self.assertEqual(motion_paths.remove_path(off, 3), expected)

    def test_unobserved_typed_or_dynamic_rotation_is_refused_without_changes(self):
        for kind in ["ScreenIMFile", "StitchedMedia"]:
            doc = owner_document(kind)
            visual(doc)["parameters"]["rotation2"] = dict(
                type="double", defaultValue=0.0, interp="eioe"
            )
            original = copy.deepcopy(doc)
            with self.assertRaisesRegex(ValueError, "rotation"):
                motion_paths.set_path(doc, 3, {**spec(), "autoOrient": True})
            self.assertEqual(doc, original)

    def test_bypassed_orientation_edits_keep_native_zero_companion_absent(self):
        for kind in ["ScreenIMFile", "StitchedMedia"]:
            doc = owner_document(kind)
            oriented = motion_paths.set_path(doc, 3, {**spec(), "autoOrient": True})
            bypassed = motion_paths.set_bypass(oriented, 3, True)
            off = motion_paths.set_path(bypassed, 3, {**spec(), "autoOrient": False})
            on = motion_paths.set_path(off, 3, {**spec(), "autoOrient": True})
            self.assertEqual(on, bypassed)
            self.assertNotIn("rotation2", visual(off)["parameters"])
            self.assertNotIn("rotation2", visual(on)["parameters"])
            self.assertEqual(motion_paths.set_bypass(on, 3, False), oriented)
            visual(on)["parameters"]["rotation2"] = 0.25
            original = copy.deepcopy(on)
            with self.assertRaisesRegex(ValueError, "rotation"):
                motion_paths.set_bypass(on, 3, False)
            self.assertEqual(on, original)

    def test_point_replacement_preserves_native_opaque_frames_and_other_effect_order(self):
        doc = owner_document("ScreenIMFile")
        animated = motion_paths.set_path(doc, 3, spec())
        frames = visual(animated)["effects"][0]["parameters"]["mediaLocation"]["keyframes"]
        frames[0]["opaque"] = {"keep": "native"}
        visual(animated)["effects"].append(dict(effectName="Border", opaque=True))
        replacement = dict(schema_version=1, points=[dict(time=2, position=[-128, 72, 0])])
        result = motion_paths.set_path(animated, 3, replacement)
        self.assertEqual(
            visual(result)["effects"][0]["parameters"]["mediaLocation"]["keyframes"],
            [
                dict(
                    time=2 * RATE,
                    endTime=2 * RATE,
                    duration=0,
                    value=[-128, 72, 0],
                    opaque={"keep": "native"},
                )
            ],
        )
        self.assertEqual(visual(result)["effects"][1], visual(animated)["effects"][1])

    def test_child_selection_does_not_rewrite_parent_or_other_hold(self):
        doc = owner_document("StitchedMedia")
        result = motion_paths.set_path(doc, 5, spec())
        self.assertEqual(visual(result)["parameters"], visual(doc)["parameters"])
        self.assertEqual(visual(result)["medias"][0], visual(doc)["medias"][0])
        self.assertEqual(
            visual(result)["medias"][1]["effects"][0]["parameters"]["mediaLocation"]["keyframes"][
                0
            ]["time"],
            2 * RATE,
        )
        for kind in ["ScreenIMFile", "StitchedMedia"]:
            with self.assertRaisesRegex(ValueError, "verified"):
                hotspots.visual_target(owner_document(kind), 3)

    def test_cli_stages_retimed_frozen_path_without_original_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, payload, output = [
                root / name for name in ["source.json", "spec.json", "candidate.json"]
            ]
            doc = owner_document("ScreenIMFile")
            visual(doc)["scalar"] = "1/2"
            raw = project.encode_document(doc)
            source.write_bytes(raw)
            payload.write_text(json.dumps(spec()))
            with patch("sys.stdout", new_callable=io.StringIO) as out:
                self.assertEqual(
                    motion_paths.main(
                        [
                            "set-path",
                            str(source),
                            "--clip-id",
                            "3",
                            "--spec",
                            str(payload),
                            "--output",
                            str(output),
                        ]
                    ),
                    0,
                )
            self.assertFalse(json.loads(out.getvalue())["nativeVerified"])
            self.assertEqual(project.load(output)[0], motion_paths.set_path(doc, 3, spec()))
            self.assertEqual(source.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
