from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

from test_animations import fixture, visual
import animations
import hotspots
import project

RATE = 705600000
INITIAL = 0.211640211640212
TARGET = 0.300000011920929


def owner_document(kind: str) -> dict[str, Any]:
    doc = fixture()
    doc["editRate"] = RATE
    owner = visual(doc)
    owner.update(
        _type=kind,
        start=8 * RATE if kind == "ScreenIMFile" else 0,
        duration=2 * RATE if kind == "ScreenIMFile" else 10 * RATE,
        mediaStart=5621280000 if kind == "ScreenIMFile" else 0,
        mediaDuration=1 if kind == "ScreenIMFile" else 10 * RATE,
        scalar=1,
    )
    parameters: dict[str, Any] = {
        name: dict(type="double", defaultValue=INITIAL, interp="eioe")
        if kind == "ScreenIMFile"
        else INITIAL
        for name in ["scale0", "scale1"]
    }
    parameters["cursorLocation"] = dict(
        type="point",
        keyframes=[dict(time=-5607991200, endTime=-5607991200, duration=0, value=[1463, 1406, 0])],
    )
    parameters["cursorImagePath"] = "native-cursor/0"
    owner["parameters"] = parameters
    if kind == "StitchedMedia":
        owner.pop("src", None)
        owner.pop("trackNumber", None)
        owner["minMediaStart"] = 0.0
        owner["medias"] = [
            dict(
                id=4,
                _type="ScreenVMFile",
                src=1,
                trackNumber=0,
                start=0,
                duration=8 * RATE,
                mediaStart=0,
                mediaDuration=8 * RATE,
                scalar=1,
                parameters=dict(cursorScale=0),
                effects=[],
                animationTracks={},
            ),
            dict(
                id=5,
                _type="ScreenIMFile",
                src=1,
                trackNumber=0,
                start=8 * RATE,
                duration=2540183520000,
                mediaStart=5621280000,
                mediaDuration=1,
                scalar=1,
                trimStartSum=0,
                parameters=dict(cursorImagePath="native-cursor/0"),
                effects=[],
                animationTracks={},
            ),
        ]
    return doc


def payload(kind: str) -> dict[str, Any]:
    return dict(
        schema_version=1,
        start=0 if kind == "ScreenIMFile" else 2,
        end=1 if kind == "ScreenIMFile" else 3,
        values=dict(scale0=TARGET, scale1=TARGET),
        easing="linear",
    )


class AnimationFreezeTests(unittest.TestCase):
    def test_native_constant_cursor_companion_follows_easing_and_removal(self):
        for kind in ["StitchedMedia", "ScreenIMFile"]:
            doc = owner_document(kind)
            visual(doc)["parameters"]["cursorScale"] = 5.0
            spec = payload(kind)
            start, end = spec["start"], spec["end"]
            animated = animations.edit_interval(doc, 3, spec)
            companion = dict(
                type="double",
                defaultValue=5.0,
                keyframes=[
                    dict(
                        time=start * RATE,
                        endTime=end * RATE,
                        duration=RATE,
                        value=5.0,
                        interp="linr",
                    )
                ],
            )
            visual(animated)["parameters"]["cursorScale"] = companion
            eased = animations.edit_interval(
                animated,
                3,
                dict(schema_version=1, start=start, end=end, values={}, easing="spring"),
            )
            self.assertEqual(
                visual(eased)["parameters"]["cursorScale"]["keyframes"][0]["interp"], "sprg"
            )
            self.assertEqual(
                visual(eased)["parameters"]["cursorScale"]["keyframes"][0]["value"], 5.0
            )
            self.assertEqual(animations.remove_interval(eased, 3, start, end), doc)

    def test_dynamic_or_point_cursor_scaling_still_refuses_interval_coupling(self):
        for frame in [
            dict(time=2 * RATE, endTime=3 * RATE, duration=RATE, value=6.0),
            dict(time=2 * RATE, endTime=2 * RATE, duration=0, value=5.0),
        ]:
            doc = animations.edit_interval(
                owner_document("StitchedMedia"), 3, payload("StitchedMedia")
            )
            frames = [dict(time=2 * RATE, endTime=3 * RATE, duration=RATE, value=5.0), frame]
            visual(doc)["parameters"]["cursorScale"] = dict(
                type="double", defaultValue=5.0, keyframes=frames
            )
            frozen = copy.deepcopy(doc)
            with self.assertRaisesRegex(ValueError, "unknown curves"):
                animations.edit_interval(
                    doc, 3, dict(schema_version=1, start=2, end=3, values={}, easing="spring")
                )
            with self.assertRaisesRegex(ValueError, "unknown curves"):
                animations.remove_interval(doc, 3, 2, 3)
            self.assertEqual(doc, frozen)

    def test_native_hold_and_stitched_curves_keep_exact_source_clocks_and_children(self):
        for kind in ["ScreenIMFile", "StitchedMedia"]:
            doc = owner_document(kind)
            frozen = copy.deepcopy(doc)
            result = animations.edit_interval(doc, 3, payload(kind))
            start, end = (0, RATE) if kind == "ScreenIMFile" else (2 * RATE, 3 * RATE)
            for name in ["scale0", "scale1"]:
                expected = dict(
                    type="double",
                    defaultValue=INITIAL,
                    keyframes=[
                        dict(time=start, endTime=end, duration=RATE, value=TARGET, interp="linr")
                    ],
                )
                if kind == "ScreenIMFile":
                    expected["interp"] = "eioe"
                self.assertEqual(visual(result)["parameters"][name], expected)
            self.assertEqual(
                visual(result)["animationTracks"],
                dict(visual=[dict(endTime=end, duration=RATE, interp="linr")]),
            )
            self.assertEqual(visual(result).get("medias"), visual(doc).get("medias"))
            self.assertEqual(
                visual(result)["parameters"]["cursorLocation"],
                visual(doc)["parameters"]["cursorLocation"],
            )
            self.assertEqual(
                visual(result)["mediaDuration"], 1 if kind == "ScreenIMFile" else 10 * RATE
            )
            self.assertEqual(doc, frozen)

    def test_native_fast_and_slow_frozen_clocks_keep_source_selection_independent(self):
        for scalar, start, end in [("1/2", 1411200000, 2822400000), (2, 352800000, 705600000)]:
            doc = owner_document("ScreenIMFile")
            visual(doc)["scalar"] = scalar
            visual(doc)["mediaStart"] = 2822400000
            frozen = copy.deepcopy(doc)
            spec = {**payload("ScreenIMFile"), "start": 1, "end": 2, "easing": "bounce"}
            result = animations.edit_interval(doc, 3, spec)
            self.assertEqual(
                visual(result)["animationTracks"]["visual"],
                [dict(endTime=end, duration=end - start, interp="bnce")],
            )
            self.assertEqual(
                visual(result)["parameters"]["scale0"]["keyframes"],
                [dict(time=start, endTime=end, duration=end - start, value=TARGET, interp="bnce")],
            )
            self.assertEqual(visual(result)["mediaStart"], 2822400000)
            self.assertEqual(visual(result)["mediaDuration"], 1)
            self.assertEqual(animations.remove_interval(result, 3, 1, 2), doc)
            self.assertEqual(doc, frozen)

    def test_easing_preserves_typed_initial_interpolation_and_frozen_cursor_data(self):
        for kind in ["ScreenIMFile", "StitchedMedia"]:
            before = animations.edit_interval(owner_document(kind), 3, payload(kind))
            spec = {**payload(kind), "values": {}, "easing": "bounce"}
            result = animations.edit_interval(before, 3, spec)
            for name in ["scale0", "scale1"]:
                parameter = visual(result)["parameters"][name]
                self.assertEqual(parameter["keyframes"][0]["interp"], "bnce")
                self.assertEqual(
                    parameter.get("interp"), "eioe" if kind == "ScreenIMFile" else None
                )
            self.assertEqual(visual(result).get("medias"), visual(before).get("medias"))
            self.assertEqual(result["sourceBin"], before["sourceBin"])

    def test_retimed_native_constant_companions_ease_and_remove_at_local_clock_bounds(self):
        doc = owner_document("ScreenIMFile")
        owner = visual(doc)
        owner["scalar"] = 2
        owner["parameters"]["scale0"] = INITIAL
        owner["parameters"]["scale1"] = INITIAL
        owner["parameters"]["cursorScale"] = 5.0
        baseline = copy.deepcopy(doc)
        marker = dict(endTime=705600000, duration=352800000, interp="bnce")
        owner["animationTracks"] = dict(visual=[marker])
        for name, initial, target in [
            ("scale0", INITIAL, TARGET),
            ("scale1", INITIAL, TARGET),
            ("cursorScale", 5.0, 5.0),
        ]:
            owner["parameters"][name] = dict(
                type="double",
                defaultValue=initial,
                keyframes=[
                    dict(
                        time=352800000,
                        endTime=705600000,
                        duration=352800000,
                        value=target,
                        interp="bnce",
                    )
                ],
            )
        frozen = copy.deepcopy(doc)
        eased = animations.edit_interval(
            doc, 3, dict(schema_version=1, start=1, end=2, values={}, easing="linear")
        )
        expected = copy.deepcopy(doc)
        visual(expected)["animationTracks"]["visual"][0]["interp"] = "linr"
        for name in ["scale0", "scale1", "cursorScale"]:
            visual(expected)["parameters"][name]["keyframes"][0]["interp"] = "linr"
        self.assertEqual(eased, expected)
        self.assertEqual(animations.remove_interval(eased, 3, 1, 2), baseline)
        self.assertEqual(doc, frozen)

    def test_removal_restores_native_typed_hold_and_bare_stitched_initials(self):
        for kind in ["ScreenIMFile", "StitchedMedia"]:
            doc = owner_document(kind)
            spec = payload(kind)
            animated = animations.edit_interval(doc, 3, spec)
            removed = animations.remove_interval(animated, 3, spec["start"], spec["end"])
            self.assertEqual(removed, doc)
            self.assertEqual(
                animations.remove_interval(removed, 3, spec["start"], spec["end"]), removed
            )

    def test_empty_markers_do_not_invent_geometry_or_rewrite_frozen_source_duration(self):
        for kind in ["ScreenIMFile", "StitchedMedia"]:
            doc = owner_document(kind)
            spec = {**payload(kind), "values": {}}
            result = animations.edit_interval(doc, 3, spec, allow_empty=True)
            self.assertEqual(visual(result)["parameters"], visual(doc)["parameters"])
            self.assertEqual(visual(result).get("medias"), visual(doc).get("medias"))
            self.assertEqual(visual(result)["mediaDuration"], visual(doc)["mediaDuration"])

    def test_animation_owner_extension_does_not_widen_hotspot_constructors(self):
        for kind in ["ScreenIMFile", "StitchedMedia"]:
            doc = owner_document(kind)
            with self.assertRaisesRegex(ValueError, "verified"):
                hotspots.visual_target(doc, 3)
        doc = owner_document("StitchedMedia")
        frozen = copy.deepcopy(doc)
        result = animations.edit_interval(
            doc,
            4,
            dict(schema_version=1, start=1, end=2, values=dict(scale0=0.5), initial=dict(scale0=1)),
        )
        self.assertEqual(visual(result)["parameters"], visual(doc)["parameters"])
        self.assertEqual(visual(result)["medias"][1], visual(doc)["medias"][1])
        self.assertEqual(doc, frozen)

    def test_cli_stages_both_native_owners_and_removal_without_input_writes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for kind in ["ScreenIMFile", "StitchedMedia"]:
                source, spec, output, removed = [
                    root / f"{kind}-{name}.json"
                    for name in ["source", "spec", "candidate", "removed"]
                ]
                document = owner_document(kind)
                raw = project.encode_document(document)
                source.write_bytes(raw)
                spec.write_text(json.dumps(payload(kind)))
                with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                    self.assertEqual(
                        animations.main(
                            [
                                "set-interval",
                                str(source),
                                "--clip-id",
                                "3",
                                "--spec",
                                str(spec),
                                "--output",
                                str(output),
                            ]
                        ),
                        0,
                    )
                    self.assertFalse(json.loads(stdout.getvalue())["nativeVerified"])
                bounds = payload(kind)
                with patch("sys.stdout", new_callable=io.StringIO):
                    self.assertEqual(
                        animations.main(
                            [
                                "remove-interval",
                                str(output),
                                "--clip-id",
                                "3",
                                "--start",
                                str(bounds["start"]),
                                "--end",
                                str(bounds["end"]),
                                "--output",
                                str(removed),
                            ]
                        ),
                        0,
                    )
                self.assertEqual(project.load(removed)[0], document)
                self.assertEqual(source.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
