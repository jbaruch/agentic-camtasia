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
from test_mattes import linked_fixture
import hotspots
import mattes
import project


class RecordingMatteTests(unittest.TestCase):
    def test_native_direct_constructors_preserve_cursor_sources_children_and_audio(self):
        for kind in ("ScreenVMFile", "ScreenIMFile", "StitchedMedia"):
            doc = owner_document(kind)
            project.scene_tracks(doc)[0].append(
                {
                    "trackIndex": 1,
                    "medias": [
                        dict(
                            id=20,
                            _type="AMFile",
                            src=1,
                            trackNumber=1,
                            start=0,
                            duration=1000,
                            mediaStart=500,
                            mediaDuration=1000,
                            scalar=1,
                            parameters=dict(volume=0.7),
                            effects=[dict(effectName="Denoise", opaque=["retain processing"])],
                        )
                    ],
                }
            )
            frozen = copy.deepcopy(doc)
            result = mattes.edit_media(doc, 3, mode="alpha")
            effect = visual(result)["effects"].pop()
            self.assertEqual(
                effect,
                {
                    "effectName": "MediaMatte",
                    "category": "categoryVisualEffects",
                    "bypassed": False,
                    "parameters": {
                        "matteMode": 1,
                        "trackDepth": 10002,
                        "intensity": {
                            "type": "double",
                            "defaultValue": 1.0,
                            "interp": "linr",
                            "uiHints": {"userInterfaceType": 0, "unitType": 0},
                        },
                    },
                },
            )
            self.assertEqual(result, frozen)
            self.assertEqual(doc, frozen)

    def test_frozen_intensity_uses_local_zero_independently_of_held_source_frame(self):
        doc = owner_document("ScreenIMFile")
        original = copy.deepcopy(doc)
        spec = dict(
            schema_version=2,
            defaultValue=0,
            segments=[dict(start=0, end=1, value=1, easing="spring")],
        )
        result = mattes.edit_intensity_curve(doc, 3, spec)
        parameter = visual(result)["effects"][0]["parameters"]["intensity"]
        self.assertEqual(
            parameter,
            {
                "type": "double",
                "defaultValue": 0.0,
                "uiHints": {"userInterfaceType": 0, "unitType": 0},
                "keyframes": [
                    dict(time=0, endTime=705600000, duration=705600000, value=1.0, interp="sprg")
                ],
            },
        )
        self.assertEqual(visual(result)["mediaStart"], 5621280000)
        self.assertEqual(visual(result)["mediaDuration"], 1)
        visual(result)["effects"].clear()
        self.assertEqual(result, original)
        self.assertEqual(doc, original)

    def test_retimed_moving_and_stitched_clocks_retain_source_inpoints(self):
        for kind in ("ScreenVMFile", "StitchedMedia"):
            doc = owner_document(kind)
            visual(doc).update(mediaStart=2 * RATE, scalar="1/2", start=30 * RATE)
            before = copy.deepcopy(doc)
            result = mattes.edit_intensity_curve(
                doc,
                3,
                dict(schema_version=1, defaultValue=1, segments=[dict(start=1, end=2, value=0)]),
            )
            self.assertEqual(
                visual(result)["effects"][0]["parameters"]["intensity"]["keyframes"],
                [
                    dict(
                        time=2822400000,
                        endTime=4233600000,
                        duration=1411200000,
                        value=0.0,
                        interp="linr",
                    )
                ],
            )
            visual(result)["effects"].clear()
            self.assertEqual(result, before)
            self.assertEqual(doc, before)

    def test_retimed_frozen_curves_keep_source_selection_separate(self):
        for scalar, bounds in (("1/2", (1411200000, 2822400000)), (2, (352800000, 705600000))):
            doc = owner_document("ScreenIMFile")
            visual(doc)["scalar"] = scalar
            before = copy.deepcopy(doc)
            result = mattes.edit_intensity_curve(
                doc,
                3,
                dict(
                    schema_version=2,
                    defaultValue=0,
                    segments=[dict(start=1, end=2, value=1, easing="bounce")],
                ),
            )
            start, end = bounds
            self.assertEqual(
                visual(result)["effects"][0]["parameters"]["intensity"]["keyframes"],
                [dict(time=start, endTime=end, duration=end - start, value=1.0, interp="bnce")],
            )
            visual(result)["effects"].clear()
            self.assertEqual(result, before)

    def test_recording_lifecycle_preserves_other_effects_and_cursor_tracks(self):
        for kind in ("ScreenVMFile", "ScreenIMFile", "StitchedMedia"):
            doc = owner_document(kind)
            visual(doc)["effects"] = [dict(effectName="CursorHilight", opaque=["keep"])]
            visual(doc)["animationTracks"] = dict(
                visual=[dict(endTime=RATE, duration=RATE, interp="linr")]
            )
            before = copy.deepcopy(doc)
            added = mattes.edit_media(
                doc,
                3,
                mode="luminosity-invert",
                intensity="1/2",
                ease_in="1/2",
                ease_out="1/4",
                bypass=True,
            )
            effect = visual(added)["effects"][1]
            self.assertEqual(effect["parameters"]["matteMode"], 4)
            self.assertEqual(effect["parameters"]["intensity"]["defaultValue"], 0.5)
            self.assertEqual(effect["leftEdgeMods"][0]["duration"], 352800000)
            self.assertEqual(effect["rightEdgeMods"][0]["duration"], 176400000)
            self.assertTrue(effect["bypassed"])
            animated = mattes.edit_intensity_curve(
                added,
                3,
                dict(
                    schema_version=2,
                    defaultValue=0,
                    segments=[dict(start=0, end=1, value=1, easing="exponential")],
                ),
            )
            cleared = mattes.clear_intensity_curve(animated, 3, "1/4")
            parameter = visual(cleared)["effects"][1]["parameters"]["intensity"]
            self.assertNotIn("keyframes", parameter)
            self.assertEqual(parameter["defaultValue"], 0.25)
            self.assertEqual(mattes.edit_media(cleared, 3, mode="none"), before)
            self.assertEqual(doc, before)

    def test_stitched_child_target_does_not_edit_parent_or_other_descendants(self):
        doc = owner_document("StitchedMedia")
        before = copy.deepcopy(doc)
        result = mattes.edit_media(doc, 5, mode="alpha-invert")
        child = visual(result)["medias"][1]
        self.assertEqual(child["effects"][0]["parameters"]["matteMode"], 2)
        child["effects"].clear()
        self.assertEqual(result, before)
        for kind in ("ScreenIMFile", "StitchedMedia"):
            with self.assertRaisesRegex(ValueError, "verified"):
                hotspots.visual_target(owner_document(kind), 3)

    def test_linked_held_and_stitched_mirrors_require_their_own_native_contract(self):
        for kind in ("ScreenIMFile", "StitchedMedia"):
            doc = linked_fixture()
            project.scene_tracks(doc)[0][0]["medias"][0]["video"]["_type"] = kind
            before = copy.deepcopy(doc)
            with self.assertRaisesRegex(ValueError, "linked recording matte mirrors"):
                mattes.edit_media(doc, 3, mode="alpha")
            self.assertEqual(doc, before)

    def test_cli_stages_frozen_curve_and_removal_with_unchanged_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, spec, output, removed = [
                root / name
                for name in ("source.json", "curve.json", "candidate.json", "removed.json")
            ]
            doc = owner_document("ScreenIMFile")
            source.write_bytes(project.encode_document(doc))
            raw = source.read_bytes()
            spec.write_text(
                json.dumps(
                    dict(
                        schema_version=2,
                        defaultValue=0,
                        segments=[dict(start=0, end=1, value=1, easing="spring")],
                    )
                )
            )
            with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                self.assertEqual(
                    mattes.main(
                        [
                            "set-intensity-curve",
                            str(source),
                            "--clip-id",
                            "3",
                            "--curve",
                            str(spec),
                            "--output",
                            str(output),
                        ]
                    ),
                    0,
                )
                self.assertFalse(json.loads(stdout.getvalue())["nativeVerified"])
            with patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(
                    mattes.main(
                        [
                            "set-media",
                            str(output),
                            "--clip-id",
                            "3",
                            "--mode",
                            "none",
                            "--output",
                            str(removed),
                        ]
                    ),
                    0,
                )
            self.assertEqual(project.load(removed)[0], doc)
            self.assertEqual(source.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
