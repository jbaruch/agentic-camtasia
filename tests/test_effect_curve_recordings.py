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
from test_effect_curves import fixture
import effect_curves
import effects
import project


def document(kind):
    doc = owner_document(kind)
    visual(doc)["effects"] = [
        dict(
            effectName="Sepia",
            category="categoryVisualEffects",
            bypassed=False,
            parameters=dict(
                intensity=dict(
                    type="double",
                    defaultValue=0.0,
                    interp="linr",
                    uiHints=dict(userInterfaceType=0, unitType=0),
                    opaque=["retain"],
                ),
            ),
        ),
        dict(effectName="CursorHilight", opaque=["retain other effect"]),
    ]
    return doc


def spec(start=0, end=1, easing=None):
    segment = dict(start=start, end=end, value=1)
    if easing is not None:
        segment["easing"] = easing
    return dict(schema_version=2 if easing else 1, defaultValue=0, segments=[segment])


class RecordingEffectCurveTests(unittest.TestCase):
    def test_native_recording_owner_curves_preserve_the_complete_unrelated_document(self):
        for kind, bounds in (
            ("ScreenVMFile", (0, 705600000)),
            ("ScreenIMFile", (0, 705600000)),
            ("StitchedMedia", (0, 705600000)),
        ):
            with self.subTest(kind=kind):
                doc = document(kind)
                before = copy.deepcopy(doc)
                result = effect_curves.edit_curve(doc, 3, "Sepia", "intensity", spec())
                expected = copy.deepcopy(doc)
                start, end = bounds
                visual(expected)["effects"][0]["parameters"]["intensity"].update(
                    defaultValue=0.0,
                    keyframes=[
                        dict(
                            time=start, endTime=end, duration=end - start, value=1.0, interp="linr"
                        )
                    ],
                )
                visual(expected).setdefault("animationTracks", {})["visual"] = [
                    dict(endTime=end, duration=end - start, interp="linr"),
                ]
                self.assertEqual(result, expected)
                self.assertEqual(doc, before)
                self.assertEqual(
                    result, effect_curves.edit_curve(result, 3, "Sepia", "intensity", spec())
                )

    def test_source_position_and_local_zero_clocks_remain_distinct_under_retiming(self):
        for kind, bounds in (
            ("ScreenVMFile", (2822400000, 4233600000)),
            ("StitchedMedia", (2822400000, 4233600000)),
            ("ScreenIMFile", (1411200000, 2822400000)),
        ):
            doc = document(kind)
            visual(doc).update(
                start=30 * RATE, mediaStart=2 * RATE, scalar="1/2", duration=4 * RATE
            )
            before = copy.deepcopy(doc)
            result = effect_curves.edit_curve(doc, 3, "Sepia", "intensity", spec(1, 2, "spring"))
            parameter = visual(result)["effects"][0]["parameters"]["intensity"]
            start, end = bounds
            self.assertEqual(
                parameter["keyframes"],
                [
                    dict(time=start, endTime=end, duration=end - start, value=1.0, interp="sprg"),
                ],
            )
            self.assertNotIn("interp", parameter)
            self.assertEqual(visual(result)["mediaStart"], 2 * RATE)
            self.assertEqual(visual(result)["mediaDuration"], visual(doc)["mediaDuration"])
            self.assertEqual(doc, before)

    def test_clear_preserves_geometry_cursor_children_audio_and_source_processing(self):
        for kind in ("ScreenVMFile", "ScreenIMFile", "StitchedMedia"):
            doc = document(kind)
            doc["sourceBin"][0]["opaqueProcessing"] = ["retain source processing"]
            animated = effect_curves.edit_curve(doc, 3, "Sepia", "intensity", spec(0, 1, "bounce"))
            before = copy.deepcopy(animated)
            expected = copy.deepcopy(animated)
            parameter = visual(expected)["effects"][0]["parameters"]["intensity"]
            parameter.pop("keyframes")
            parameter["defaultValue"] = 0.25
            result = effect_curves.clear_curve(animated, 3, "Sepia", "intensity", "1/4")
            self.assertEqual(result, expected)
            self.assertEqual(animated, before)
            self.assertEqual(
                result, effect_curves.clear_curve(result, 3, "Sepia", "intensity", "1/4")
            )

    def test_matching_interval_retains_independent_geometry_easing_and_cursor_companions(self):
        doc = document("ScreenIMFile")
        owner = visual(doc)
        owner["animationTracks"] = dict(
            visual=[dict(endTime=RATE, duration=RATE, interp="linr", future=[1])]
        )
        owner["parameters"]["translation0"] = dict(
            type="double",
            defaultValue=-60.0,
            keyframes=[dict(time=0, endTime=RATE, duration=RATE, value=60.0, interp="linr")],
        )
        before = copy.deepcopy(doc)
        result = effect_curves.edit_curve(doc, 3, "Sepia", "intensity", spec(0, 1, "spring"))
        self.assertEqual(visual(result)["animationTracks"], owner["animationTracks"])
        self.assertEqual(visual(result)["parameters"], owner["parameters"])
        self.assertEqual(doc, before)

    def test_linked_held_and_stitched_mirrors_are_refused_for_wrapper_and_visual_ids(self):
        for kind in ("ScreenIMFile", "StitchedMedia"):
            doc = fixture(True)
            visual_owner = project.scene_tracks(doc)[0][0]["medias"][0]["video"]
            visual_owner["_type"] = kind
            before = copy.deepcopy(doc)
            for clip_id in (3, 10):
                with (
                    self.subTest(kind=kind, clip_id=clip_id),
                    self.assertRaisesRegex(ValueError, "linked recording"),
                ):
                    effect_curves.edit_curve(doc, clip_id, "Sepia", "intensity", spec())
                with self.assertRaisesRegex(ValueError, "linked recording"):
                    effect_curves.clear_curve(doc, clip_id, "Sepia", "intensity", 0)
            self.assertEqual(doc, before)

    def test_general_effect_operations_keep_their_original_owner_scope(self):
        for kind in ("ScreenIMFile", "StitchedMedia"):
            with self.assertRaisesRegex(ValueError, "verified"):
                effects.targets(document(kind), 3, "Sepia", None)

    def test_cli_all_recording_owners_stage_clear_and_preserve_source_bytes(self):
        for kind in ("ScreenVMFile", "ScreenIMFile", "StitchedMedia"):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source, settings, output, cleared = [
                    root / name
                    for name in ("source.json", "spec.json", "candidate.json", "cleared.json")
                ]
                source.write_bytes(project.encode_document(document(kind)))
                original = source.read_bytes()
                settings.write_text(json.dumps(spec(0, 1, "exponential")))
                common = ["--clip-id", "3", "--effect", "Sepia", "--parameter", "intensity"]
                for written in (True, False):
                    with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                        self.assertEqual(
                            effect_curves.main(
                                [
                                    "set",
                                    str(source),
                                    *common,
                                    "--spec",
                                    str(settings),
                                    "--output",
                                    str(output),
                                ]
                            ),
                            0,
                        )
                    report = json.loads(stdout.getvalue())
                    self.assertEqual(report["written"], written)
                    self.assertFalse(report["nativeVerified"])
                    self.assertEqual(report["candidateSha256"], project.digest(output.read_bytes()))
                with patch("sys.stdout", new_callable=io.StringIO):
                    self.assertEqual(
                        effect_curves.main(
                            [
                                "clear",
                                str(output),
                                *common,
                                "--value",
                                "1/4",
                                "--output",
                                str(cleared),
                            ]
                        ),
                        0,
                    )
                self.assertEqual(
                    visual(project.load(cleared)[0])["effects"][0]["parameters"]["intensity"][
                        "defaultValue"
                    ],
                    0.25,
                )
                self.assertEqual(source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
