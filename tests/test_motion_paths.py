from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_animations import fixture, visual
import motion_paths
import project


def linked_document() -> dict:
    doc = fixture()
    video = visual(doc)
    clocks = {
        key: video[key] for key in ["start", "duration", "mediaStart", "mediaDuration", "scalar"]
    }
    wrapper = dict(
        id=10,
        _type="UnifiedMedia",
        video=video,
        audio=dict(id=11, _type="AMFile", src=1, parameters={"volume": 0.8}, effects=[], **clocks),
        effects=[],
        metadata={"effectApplied": "none", "keep": "wrapper"},
        **clocks,
    )
    project.scene_tracks(doc)[0][0]["medias"] = [wrapper]
    return doc


def wrapper(doc: dict) -> dict:
    return project.scene_tracks(doc)[0][0]["medias"][0]


def spec() -> dict:
    return {
        "schema_version": 1,
        "points": [
            {"time": 1, "position": [0, 0, 0]},
            {
                "time": 2,
                "position": [256, 144, 0],
                "interpolation": {"bezier": [[128, 0, 0], [128, 144, 0], "eioe"]},
            },
        ],
    }


class MotionPathTests(unittest.TestCase):
    def test_constructor_matches_fixed_native_mirrors_without_touching_audio_or_sources(self):
        doc = linked_document()
        frozen = copy.deepcopy(doc)
        result = motion_paths.set_path(doc, 10, spec())
        expected = {
            "effectName": "MediaPath",
            "bypassed": False,
            "category": "categoryVisualEffects",
            "metadata": {"effectIndex": "0"},
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
        self.assertEqual(wrapper(result)["effects"], [expected])
        self.assertEqual(visual(result)["effects"], [expected])
        self.assertEqual(
            wrapper(result)["metadata"], {"effectApplied": "MediaPath", "keep": "wrapper"}
        )
        self.assertEqual(wrapper(result)["audio"], wrapper(doc)["audio"])
        self.assertEqual(result["sourceBin"], doc["sourceBin"])
        self.assertEqual(result, motion_paths.set_path(doc, 3, spec()))
        self.assertEqual(doc, frozen)
        self.assertEqual(result, motion_paths.set_path(result, 3, spec()))

    def test_all_literal_timings_and_optional_bezier_timing_remain_distinct(self):
        for timing in ["eioe", "esIn", "esOt", "linr"]:
            for spatial in [
                timing,
                {"bezier": [[64.2896, 0, 0], [96.2889, 36.3265, 0]]},
                {"bezier": [[64, 0, 0], [128, 144, 0], timing]},
            ]:
                payload = spec()
                payload["points"][1]["interpolation"] = spatial
                result = motion_paths.set_path(linked_document(), 3, payload)
                self.assertEqual(
                    visual(result)["effects"][0]["parameters"]["mediaLocation"]["keyframes"][1][
                        "interp"
                    ],
                    spatial,
                )

    def test_retimed_and_subframe_points_use_exact_source_project_ticks(self):
        doc = linked_document()
        for owner in [wrapper(doc), visual(doc), wrapper(doc)["audio"]]:
            owner.update(
                start=1000, mediaStart=1000, scalar="1/2", duration=4000, mediaDuration=8000
            )
        payload = spec()
        payload["points"][0]["time"] = "-1/4"
        payload["points"][1]["time"] = "1001/2000"
        result = motion_paths.set_path(doc, 3, payload)
        frames = visual(result)["effects"][0]["parameters"]["mediaLocation"]["keyframes"]
        self.assertEqual([f["time"] for f in frames], [500, 2001])
        self.assertEqual(visual(result)["start"], 1000)

    def test_explicit_point_replacement_retains_opaque_matching_frame_and_parameter_fields(self):
        doc = motion_paths.set_path(linked_document(), 3, spec())
        for owner in [wrapper(doc), visual(doc)]:
            curve = owner["effects"][0]["parameters"]["mediaLocation"]
            curve["opaque"] = {"keep": [1, 2]}
            curve["keyframes"][1]["opaque"] = "retain"
        payload = spec()
        payload["points"].insert(1, {"time": "3/2", "position": [128.434, 72.4887, 0]})
        payload["points"][2].pop("interpolation")
        result = motion_paths.set_path(doc, 3, payload)
        curve = visual(result)["effects"][0]["parameters"]["mediaLocation"]
        self.assertEqual(curve["opaque"], {"keep": [1, 2]})
        self.assertEqual(curve["keyframes"][2]["opaque"], "retain")
        self.assertNotIn("interp", curve["keyframes"][2])
        self.assertEqual([f["time"] for f in curve["keyframes"]], [1000, 1500, 2000])
        payload["points"] = [payload["points"][0], {"time": 3, "position": [73.2026, -86.5882, 0]}]
        removed = motion_paths.set_path(result, 3, payload)
        self.assertEqual(
            [
                f["time"]
                for f in visual(removed)["effects"][0]["parameters"]["mediaLocation"]["keyframes"]
            ],
            [1000, 3000],
        )
        self.assertEqual(wrapper(removed)["audio"], wrapper(doc)["audio"])

    def test_auto_orient_companions_and_preserved_reset_when_disabled(self):
        payload = {**spec(), "autoOrient": True}
        result = motion_paths.set_path(linked_document(), 3, payload)
        self.assertEqual(wrapper(result)["metadata"]["default-MediaPath-mediaPathAutoOrient"], "0")
        self.assertEqual(visual(result)["parameters"]["rotation2"], 0.0)
        self.assertEqual(visual(result)["effects"][0]["parameters"]["mediaPathAutoOrient"], 1)
        off = motion_paths.set_path(result, 3, {**spec(), "autoOrient": False})
        self.assertEqual(visual(off)["effects"][0]["parameters"]["mediaPathAutoOrient"], 0)
        self.assertEqual(wrapper(off)["metadata"], wrapper(result)["metadata"])
        self.assertNotIn("rotation2", visual(off)["parameters"])
        for rotation in [0.2, False, {"type": "double", "defaultValue": 0, "keyframes": []}]:
            doc = linked_document()
            visual(doc)["parameters"]["rotation2"] = rotation
            with self.assertRaisesRegex(ValueError, "rotation"):
                motion_paths.set_path(doc, 3, payload)

    def test_new_effect_token_accounts_for_audio_and_preserves_sparse_other_effects(self):
        doc = linked_document()
        border = {
            "effectName": "Border",
            "parameters": {"opaque": 1},
            "metadata": {"effectIndex": "1"},
        }
        wrapper(doc)["effects"] = [copy.deepcopy(border)]
        visual(doc)["effects"] = [copy.deepcopy(border)]
        wrapper(doc)["audio"]["effects"] = [
            {"effectName": "AudioNoiseRemoval", "metadata": {"effectIndex": "4"}}
        ]
        result = motion_paths.set_path(doc, 3, spec())
        self.assertEqual(visual(result)["effects"][0], border)
        self.assertEqual(visual(result)["effects"][1]["metadata"]["effectIndex"], "5")
        self.assertEqual(wrapper(result)["audio"], wrapper(doc)["audio"])

    def test_invalid_specs_refuse_before_mutation(self):
        for payload in [
            {},
            {**spec(), "schema_version": True},
            {**spec(), "extra": 1},
            {**spec(), "autoOrient": 1},
            {**spec(), "points": []},
            {**spec(), "points": "bad"},
        ]:
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                motion_paths.set_path(linked_document(), 3, payload)
        for bad in [
            {"time": 2, "position": [0, 0]},
            {"time": True, "position": [0, 0, 0]},
            {"time": 2, "position": [0, "nan", 0]},
            {"time": "1/3000", "position": [0, 0, 0]},
            {"time": 1, "position": [0, 0, 0]},
            {"time": 2, "position": [0, 0, 0], "interpolation": "easeout"},
            {
                "time": 2,
                "position": [0, 0, 0],
                "interpolation": {"bezier": [[0, 0, 0], [1, 1, 0], "sprg"]},
            },
        ]:
            payload = spec()
            payload["points"][1] = bad
            with self.subTest(point=bad), self.assertRaises(ValueError):
                motion_paths.set_path(linked_document(), 3, payload)

    def test_conflicting_mirrors_tokens_clocks_and_unknown_owner_refuse(self):
        for mutation in ["missing", "token", "controls", "clock", "duplicate", "owner"]:
            doc = motion_paths.set_path(linked_document(), 3, spec())
            if mutation == "missing":
                wrapper(doc)["effects"] = []
            if mutation == "token":
                wrapper(doc)["effects"][0]["metadata"]["effectIndex"] = "2"
            if mutation == "controls":
                wrapper(doc)["effects"][0]["bypassed"] = True
            if mutation == "clock":
                wrapper(doc)["scalar"] = "1/2"
            if mutation == "duplicate":
                wrapper(doc)["effects"] *= 2
            if mutation == "owner":
                visual(doc)["_type"] = "IMFile"
            frozen = copy.deepcopy(doc)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                motion_paths.set_path(doc, 3, spec())
            self.assertEqual(doc, frozen)

    def test_unfamiliar_curve_shapes_and_other_build_are_refused(self):
        for curve in [
            {"type": "double"},
            {"type": "point", "keyframes": "bad"},
            {
                "type": "point",
                "keyframes": [{"time": 1, "endTime": 2, "duration": 1, "value": [0, 0, 0]}],
            },
        ]:
            doc = motion_paths.set_path(linked_document(), 3, spec())
            for owner in [wrapper(doc), visual(doc)]:
                owner["effects"][0]["parameters"]["mediaLocation"] = copy.deepcopy(curve)
            with self.assertRaises(ValueError):
                motion_paths.set_path(doc, 3, spec())
        doc = linked_document()
        doc["version"] = "9.0"
        with self.assertRaises(ValueError):
            motion_paths.set_path(doc, 3, spec())

    def test_cli_stages_inspects_and_rejects_overwrite_without_changing_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, payload, out = [root / n for n in ["source.json", "spec.json", "out.json"]]
            raw = project.encode_document(linked_document())
            source.write_bytes(raw)
            payload.write_text(json.dumps(spec()))
            args = [
                "set-path",
                str(source),
                "--clip-id",
                "3",
                "--spec",
                str(payload),
                "--output",
                str(out),
            ]
            with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                self.assertEqual(motion_paths.main(args), 0)
            self.assertFalse(json.loads(stdout.getvalue())["nativeVerified"])
            self.assertEqual(source.read_bytes(), raw)
            with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                self.assertEqual(motion_paths.main(["inspect", str(out)]), 0)
            self.assertEqual([p["clipId"] for p in json.loads(stdout.getvalue())["paths"]], [10, 3])
            out.write_text("{}")
            with patch("sys.stderr", new_callable=io.StringIO) as stderr:
                self.assertEqual(motion_paths.main(args), 1)
            self.assertFalse(json.loads(stderr.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()
