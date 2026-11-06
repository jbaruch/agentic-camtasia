from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

from test_matte_linked_recordings import fixture as linked_fixture
from test_effect_grouped_recordings import node
import mattes
import project


def effect(intensity: float | dict[str, Any] = 1.0):
    return dict(
        effectName="MediaMatte",
        bypassed=False,
        category="categoryVisualEffects",
        parameters=dict(matteMode=1, intensity=intensity, trackDepth=10002),
    )


def descriptor(value):
    return dict(
        type="double",
        defaultValue=value,
        interp="linr",
        uiHints=dict(userInterfaceType=0, unitType=0),
    )


def fixture(applied=False):
    doc = linked_fixture()
    moving = node(doc, 10)
    for owner in (moving, moving["video"], moving["audio"]):
        owner.update(start=0, duration=7056000000, mediaStart=0, mediaDuration=7056000000, scalar=1)
    frozen = dict(
        id=50,
        _type="ScreenIMFile",
        src=1,
        trackNumber=0,
        trimStartSum=0,
        start=7056000000,
        duration=5081731200000,
        mediaStart=7008960000,
        mediaDuration=1,
        scalar=1,
        attributes=dict(ident="Frame of recording", isPathEdited=False),
        parameters=dict(
            cursorOpacity=descriptor(0),
            cursorScale=descriptor(0),
            cursorTrackLevel=descriptor(0),
            cursorImagePath="recorded-cursor/0",
            smoothCursorAcrossEditDuration=0,
            cursorLocation=dict(
                type="point",
                keyframes=[
                    dict(time=-7002962400, endTime=-7002962400, duration=0, value=[701, 777, 0]),
                    dict(time=0, endTime=0, duration=0, value=[702, 778, 0]),
                    dict(time=23520000, endTime=23520000, duration=0, value=[703, 779, 0]),
                ],
            ),
        ),
        effects=[],
        animationTracks={},
        opaqueFrozen=["retain"],
    )
    parent = dict(
        id=100,
        _type="StitchedMedia",
        minMediaStart=0.0,
        start=705600000,
        duration=4233600000,
        mediaStart=1411200000,
        mediaDuration=8467200000,
        scalar="1/2",
        attributes=dict(
            ident="Linked freeze target",
            gain=1.0,
            mixToMono=False,
            loudnessNormalization=True,
            sourceFileOffset=0,
        ),
        parameters=dict(
            scale0=0.12,
            scale1=0.12,
            volume=1.0,
            cursorOpacity=1.0,
            cursorTrackLevel=10000.0,
            cursorScale=1.0,
            smoothCursorAcrossEditDuration=0,
        ),
        effects=[effect()] if applied else [],
        metadata=dict(effectApplied="none", parentOpaque=["retain"]),
        animationTracks={},
        medias=[moving, frozen],
    )
    project.scene_tracks(doc)[0][0]["medias"] = [parent]
    return doc


def unstitched(applied=False):
    doc = fixture()
    parent = node(doc, 100)
    moving, held = parent["medias"]
    for owner in (moving, moving["video"], moving["audio"]):
        owner.update(
            start=705600000,
            duration=2822400000,
            mediaStart=1411200000,
            mediaDuration=5644800000,
            scalar="1/2",
        )
    held.update(start=3528000000, duration=1411200000, scalar="1/2")
    held["effects"] = [effect()] if applied else []
    project.scene_tracks(doc)[0][0]["medias"] = [moving, held]
    return doc


class StitchedLinkedRecordingMatteTests(unittest.TestCase):
    def test_constructor_adds_only_one_parent_effect_and_keeps_linked_and_held_descendants(self):
        doc = fixture()
        original = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        node(expected, 100)["effects"] = [effect(descriptor(1.0))]
        self.assertEqual(mattes.edit_media(doc, 100, mode="alpha"), expected)
        self.assertEqual(doc, original)
        self.assertNotIn("metadata", node(expected, 100)["effects"][0])

    def test_static_controls_bypass_and_removal_preserve_every_descendant_audio_clock_and_reset(
        self,
    ):
        doc = fixture(True)
        node(doc, 100)["metadata"]["default-MediaMatte-intensity"] = "1"
        original = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        node(expected, 100)["effects"][0].update(
            bypassed=True, parameters=dict(matteMode=2, intensity=0.5, trackDepth=10002)
        )
        edited = mattes.edit_media(doc, 100, mode="alpha-invert", intensity=0.5, bypass=True)
        self.assertEqual(edited, expected)
        node(expected, 100)["effects"] = []
        removed = mattes.edit_media(edited, 100, mode="none")
        self.assertEqual(removed, expected)
        self.assertEqual(mattes.edit_media(removed, 100, mode="none"), removed)
        self.assertEqual(doc, original)

    def test_curve_crossing_moving_to_held_boundary_uses_stitched_source_positions(self):
        doc = fixture(True)
        original = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        node(expected, 100)["effects"][0]["parameters"]["intensity"] = dict(
            type="double",
            defaultValue=0.0,
            uiHints=dict(userInterfaceType=0, unitType=0),
            keyframes=[
                dict(
                    time=6350400000,
                    endTime=7761600000,
                    duration=1411200000,
                    value=1.0,
                    interp="linr",
                )
            ],
        )
        settings = dict(
            schema_version=2,
            defaultValue=0,
            segments=[dict(start="7/2", end="9/2", value=1, easing="linear")],
        )
        result = mattes.edit_intensity_curve(doc, 100, settings)
        self.assertEqual(result, expected)
        self.assertEqual(mattes.edit_intensity_curve(result, 100, settings), result)
        self.assertEqual(doc, original)

    def test_nonlinear_curve_and_clear_keep_parent_geometry_intervals_and_frozen_cursor_points(
        self,
    ):
        doc = fixture(True)
        parent = node(doc, 100)
        parent["parameters"]["translation0"] = dict(
            type="double",
            defaultValue=-10.0,
            keyframes=[
                dict(
                    time=6350400000,
                    endTime=7761600000,
                    duration=1411200000,
                    value=10.0,
                    interp="linr",
                )
            ],
        )
        parent["animationTracks"] = {
            "visual": [dict(endTime=7761600000, duration=1411200000, interp="linr")]
        }
        original = copy.deepcopy(doc)
        curved = mattes.edit_intensity_curve(
            doc,
            100,
            dict(
                schema_version=2,
                defaultValue=0,
                segments=[dict(start="7/2", end="9/2", value=1, easing="spring")],
            ),
        )
        expected = copy.deepcopy(doc)
        node(expected, 100)["effects"][0]["parameters"]["intensity"] = dict(
            type="double", defaultValue=0.5, uiHints=dict(userInterfaceType=0, unitType=0)
        )
        self.assertEqual(mattes.clear_intensity_curve(curved, 100, 0.5), expected)
        self.assertEqual(doc, original)

    def test_parent_edits_keep_child_effects_tokens_audio_processing_and_source_metadata(self):
        doc = fixture(True)
        for ident in (10, 3):
            node(doc, ident)["effects"] = [
                dict(effectName="ChildEffect", metadata=dict(effectIndex="9"), opaque=["keep"])
            ]
        node(doc, 11)["effects"] = [
            dict(effectName="AudioEffect", metadata=dict(effectIndex="7"), opaque=["keep"])
        ]
        expected = copy.deepcopy(doc)
        node(expected, 100)["effects"][0]["parameters"]["intensity"] = 0.25
        self.assertEqual(mattes.edit_media(doc, 100, intensity=0.25), expected)

    def test_linked_child_and_audio_are_not_substitutes_for_the_stitched_parent(self):
        doc = fixture(True)
        original = copy.deepcopy(doc)
        for ident in (10, 3, 11):
            with self.subTest(clip=ident), self.assertRaises(ValueError):
                mattes.edit_media(doc, ident, intensity=0.5)
        self.assertEqual(doc, original)

    def test_native_unstitched_held_constructor_preserves_independent_moving_audio(self):
        doc = unstitched()
        expected = copy.deepcopy(doc)
        node(expected, 50)["effects"] = [effect(descriptor(1.0))]
        self.assertEqual(mattes.edit_media(doc, 50, mode="alpha"), expected)
        self.assertEqual(node(doc, 11)["duration"], 2822400000)
        self.assertEqual(node(expected, 50)["mediaStart"], 7008960000)

    def test_unstitched_held_curve_uses_local_zero_independent_of_its_selected_source_frame(self):
        doc = unstitched(True)
        expected = copy.deepcopy(doc)
        node(expected, 50)["effects"][0]["parameters"]["intensity"] = dict(
            type="double",
            defaultValue=0.0,
            uiHints=dict(userInterfaceType=0, unitType=0),
            keyframes=[
                dict(time=0, endTime=1411200000, duration=1411200000, value=1.0, interp="linr")
            ],
        )
        self.assertEqual(
            mattes.edit_intensity_curve(
                doc,
                50,
                dict(schema_version=1, defaultValue=0, segments=[dict(start=0, end=1, value=1)]),
            ),
            expected,
        )

    def test_invalid_curve_and_ambiguous_parent_effects_refuse_without_mutation(self):
        doc = fixture(True)
        original = copy.deepcopy(doc)
        with self.assertRaises(ValueError):
            mattes.edit_intensity_curve(
                doc,
                100,
                dict(schema_version=1, defaultValue=0, segments=[dict(start=4, end=3, value=1)]),
            )
        self.assertEqual(doc, original)
        node(doc, 100)["effects"].append(effect())
        original = copy.deepcopy(doc)
        with self.assertRaises(ValueError):
            mattes.edit_media(doc, 100, intensity=0.5)
        self.assertEqual(doc, original)

    def test_cli_curve_repeat_clear_and_source_bytes_preserve_the_complete_compound_owner(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, settings, curved, cleared = [
                root / name for name in ("source.json", "spec.json", "curve.json", "clear.json")
            ]
            source.write_bytes(project.encode_document(fixture(True)))
            original = source.read_bytes()
            settings.write_text(
                json.dumps(
                    dict(
                        schema_version=1,
                        defaultValue=0,
                        segments=[dict(start="7/2", end="9/2", value=1)],
                    )
                )
            )
            args = [
                "set-intensity-curve",
                str(source),
                "--clip-id",
                "100",
                "--curve",
                str(settings),
                "--output",
                str(curved),
            ]
            for written in (True, False):
                with patch("sys.stdout", new_callable=io.StringIO) as stream:
                    self.assertEqual(mattes.main(args), 0)
                result = json.loads(stream.getvalue())
                self.assertEqual(result["written"], written)
                self.assertFalse(result["nativeVerified"])
            with patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(
                    mattes.main(
                        [
                            "clear-intensity-curve",
                            str(curved),
                            "--clip-id",
                            "100",
                            "--intensity",
                            "0.5",
                            "--output",
                            str(cleared),
                        ]
                    ),
                    0,
                )
            expected = fixture(True)
            node(expected, 100)["effects"][0]["parameters"]["intensity"] = dict(
                type="double", defaultValue=0.5, uiHints=dict(userInterfaceType=0, unitType=0)
            )
            self.assertEqual(project.load(cleared)[0], expected)
            self.assertEqual(source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
