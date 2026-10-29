from __future__ import annotations

import copy
import hashlib
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch
from contextlib import redirect_stdout

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/camtasia-project/scripts"))
import schema_audit  # noqa: E402


def schema() -> dict:
    return {
        "type": "object",
        "required": ["version", "sourceBin", "timeline"],
        "properties": {
            "version": {"type": "string"},
            "authoringClientName": {"type": "object"},
            "sourceBin": {"type": "array"},
            "timeline": {"$ref": "#/definitions/timeline"},
        },
        "additionalProperties": False,
        "definitions": {
            "GenericBehaviorEffect": {
                "type": "object",
                "properties": {
                    "effectName": {"type": "string", "enum": ["reveal"]},
                    **{
                        phase: {
                            "type": "object",
                            "properties": {
                                "attributes": {
                                    "type": "object",
                                    "properties": {
                                        "name": {
                                            "type": "string",
                                            "enum": [
                                                "fadeIn",
                                                "fadeOut",
                                                "fading",
                                                "flyIn",
                                                "flyOut",
                                                "grow",
                                                "hinge",
                                                "none",
                                                "pulsate",
                                                "reveal",
                                                "shifting",
                                                "shrink",
                                                "sliding",
                                                "tremble",
                                            ],
                                        }
                                    },
                                }
                            },
                        }
                        for phase in ("in", "center", "out")
                    },
                },
            },
            "timeline": {
                "type": "object",
                "properties": {
                    "effect": {"$ref": "#/definitions/effect"},
                    "clip": {"$ref": "#/definitions/media"},
                    "track": {"$ref": "#/definitions/track"},
                },
                "additionalProperties": False,
            },
            "effect": {
                "type": "object",
                "properties": {
                    "effectName": {"type": "string", "enum": ["Glow"]},
                    "category": {
                        "type": "string",
                        "enum": ["categoryVisualEffects", "categoryCursorEffects"],
                    },
                },
                "required": ["effectName"],
                "additionalProperties": False,
            },
            "animationTracks": {"type": "object"},
            "track": {
                "type": "object",
                "properties": {
                    "transitions": {
                        "type": "array",
                        "items": {
                            "type": "object",
                            "required": ["name", "duration"],
                            "properties": {
                                "name": {
                                    "type": "string",
                                    "enum": [
                                        "CardFlip",
                                        "Fade",
                                        "FadeThroughBlack",
                                        "Glitch3",
                                        "LinearBlur",
                                        "PaintArcs",
                                        "SlideLeft",
                                        "SlideRight",
                                        "SphericalSpin",
                                        "Stretch",
                                    ],
                                },
                                "duration": {"type": "integer"},
                                "leftMedia": {"type": ["integer", "null"]},
                                "rightMedia": {"type": ["integer", "null"]},
                                "attributes": {"type": "object"},
                            },
                            "additionalProperties": False,
                        },
                    }
                },
            },
            "calloutDef": {
                "type": "object",
                "properties": {
                    "kind": {"enum": ["remix", "TypeWinBlur"]},
                    "shape": {
                        "enum": [
                            "",
                            "arrow",
                            "shape-ellipse",
                            "shape-rectangle",
                            "shape-triangle",
                            "text",
                            "text-arrow2",
                            "text-rectangle",
                        ]
                    },
                },
            },
            "Callout": {
                "type": "object",
                "required": ["_type", "def"],
                "properties": {
                    "_type": {"const": "Callout"},
                    "def": {"$ref": "#/definitions/calloutDef"},
                },
                "additionalProperties": False,
            },
            "media": {"oneOf": [{"type": "object", "properties": {"_type": {"const": "VMFile"}}}]},
        },
    }


class SchemaAuditTests(unittest.TestCase):
    def setUp(self) -> None:
        self.profile = schema_audit.read_document(schema_audit.PROFILE_FILE)
        self.doc = {
            "version": "9.0",
            "authoringClientName": copy.deepcopy(self.profile["appliesTo"]["authoringClient"]),
            "timeline": {"metadata": {}, "effect": {"effectName": "Border"}},
        }

    def test_auditor_reads_native_silent_loudness_without_weakening_json_reader(self) -> None:
        doc = {
            "version": "10.0",
            "authoringClientName": {"name": "Camtasia", "platform": "Mac", "version": "2026.2.4"},
            "sourceBin": [{"sourceTracks": [{"type": 2, "integratedLUFS": "native-lufs"}]}],
            "timeline": {},
        }
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "native.json"
            path.write_text(json.dumps(doc).replace('"native-lufs"', "-1.79769313486232e+308"))
            loaded = schema_audit.read_document(path)
            self.assertTrue(schema_audit.audit(loaded, schema())["ok"])
            path.write_text('{"x": 1, "x": 2}')
            with self.assertRaisesRegex(ValueError, "duplicate JSON key"):
                schema_audit.read_document(path)
            path.write_text('{"x": -Infinity}')
            with self.assertRaisesRegex(ValueError, "non-finite"):
                schema_audit.read_document(path)

    def test_auditor_rejects_nonfinite_values_in_programmatic_documents(self) -> None:
        doc = {"version": "9.0", "sourceBin": [], "timeline": {}}
        for value in (float("inf"), float("-inf"), float("nan")):
            doc["sourceBin"] = [{"unknown": [value]}]
            result = schema_audit.audit(doc, schema())
            self.assertFalse(result["ok"])
            self.assertTrue(result["nativeCompatibilityErrors"])

    def test_profile_accepts_observed_native_shapes_without_altering_upstream(self) -> None:
        original = schema()
        before = copy.deepcopy(original)
        for name in (
            "Border",
            "Colorize",
            "CursorPath",
            "MediaPath",
            "ChromaKey",
            "CursorHilight",
            "DeviceFrameEffect",
            "BlurRegion",
            "Tonal",
            "FreezeRegion",
            "Pixelate",
            "MediaPath",
            "Sketch",
            "Reflection",
            "Sepia",
        ):
            doc = copy.deepcopy(self.doc)
            doc["timeline"]["effect"]["effectName"] = name
            with self.subTest(name=name):
                report = schema_audit.audit(doc, original, self.profile)
                self.assertTrue(report["ok"])
                self.assertGreater(len(report["upstreamErrors"]), 0)
        self.assertEqual(original, before)

    def test_profile_retains_type_and_unknown_property_rejections(self) -> None:
        for change in ("type", "unknown-root", "unknown-effect"):
            with self.subTest(change=change):
                doc = copy.deepcopy(self.doc)
                if change == "type":
                    doc["timeline"]["metadata"] = []
                elif change == "unknown-root":
                    doc["madeUpRoot"] = 1
                else:
                    doc["timeline"]["effect"]["effectName"] = "InventedEffect"
                self.assertFalse(schema_audit.audit(doc, schema(), self.profile)["ok"])

    def test_profile_validates_native_srt_caption_without_relaxing_other_media(self) -> None:
        caption = {
            "id": 6,
            "_type": "Caption",
            "allowTrimOut": False,
            "maxMediaDuration": 5644800000.0,
            "start": 0,
            "duration": 5644800000,
            "mediaStart": 0,
            "mediaDuration": 5644800000,
            "scalar": 1,
            "effects": [],
            "metadata": {},
            "animationTracks": {},
            "parameters": {
                "captionData": {
                    "type": "caption",
                    "keyframes": [
                        {
                            "time": 0,
                            "endTime": 0,
                            "duration": 0,
                            "value": {"text": "Caption one", "textAttributes": None},
                        },
                        {
                            "time": 2822400000,
                            "endTime": 2822400000,
                            "duration": 0,
                            "value": {"text": "Caption two", "textAttributes": None},
                        },
                    ],
                }
            },
        }
        doc = copy.deepcopy(self.doc)
        doc["timeline"]["clip"] = caption
        self.assertFalse(schema_audit.audit(doc, schema())["ok"])
        self.assertTrue(schema_audit.audit(doc, schema(), self.profile)["ok"])
        for scalar, accepted in (("1/2", True), ("0/2", False), ("1/0", False), (-1, False)):
            candidate = copy.deepcopy(doc)
            candidate["timeline"]["clip"]["scalar"] = scalar
            with self.subTest(scalar=scalar):
                self.assertEqual(
                    schema_audit.audit(candidate, schema(), self.profile)["ok"], accepted
                )
        for mutation in ("missing-data", "wrong-text", "unknown-field", "unknown-family"):
            candidate = copy.deepcopy(doc)
            node = candidate["timeline"]["clip"]
            if mutation == "missing-data":
                del node["parameters"]["captionData"]
            elif mutation == "wrong-text":
                node["parameters"]["captionData"]["keyframes"][0]["value"]["text"] = 23
            elif mutation == "unknown-field":
                node["madeUp"] = True
            else:
                node["_type"] = "InventedCaption"
            with self.subTest(mutation=mutation):
                self.assertFalse(schema_audit.audit(candidate, schema(), self.profile)["ok"])

    def test_profile_refuses_another_editor_or_format(self) -> None:
        for key in ("version", "authoringClientName"):
            doc = copy.deepcopy(self.doc)
            doc[key] = "another version" if key == "version" else {"platform": "Windows"}
            with self.assertRaisesRegex(ValueError, "does not match"):
                schema_audit.audit(doc, schema(), self.profile)

    def current_profile_fixture(self) -> tuple[dict, dict, dict]:
        profile = schema_audit.read_document(schema_audit.PROFILE_FILES["mac-2026.2.4"])
        baseline = schema()
        baseline["definitions"]["sourceTrack"] = {
            "type": "object",
            "properties": {},
            "additionalProperties": False,
        }
        baseline["definitions"]["timeline"]["properties"]["sourceTrack"] = {
            "$ref": "#/definitions/sourceTrack"
        }
        doc = {
            "version": "10.0",
            "authoringClientName": copy.deepcopy(profile["appliesTo"]["authoringClient"]),
            "sourceBin": [],
            "timeline": {
                "effect": {"effectName": "CursorSmoothing"},
                "sourceTrack": {"transcriptionSet": True},
            },
        }
        return baseline, doc, profile

    def sketch_fixture(self) -> tuple[dict, dict, dict]:
        baseline, doc, profile = self.current_profile_fixture()
        baseline["definitions"]["timeline"]["properties"]["callout"] = {
            "$ref": "#/definitions/Callout"
        }
        doc["timeline"]["callout"] = {
            "_type": "Callout",
            "def": {"kind": "TypeWinSVG"},
            "leftEdgeMods": [
                {
                    "group": "DrawPercentageFade",
                    "duration": 705600000,
                    "parameters": [{"name": "DrawTime", "func": "FadeInFunc"}],
                }
            ],
        }
        return baseline, doc, profile

    def test_native_sketch_kind_and_draw_modifier_keep_raw_schema_errors(self) -> None:
        baseline, doc, profile = self.sketch_fixture()
        before = copy.deepcopy(baseline)
        result = schema_audit.audit(doc, baseline, profile)
        self.assertTrue(result["ok"])
        self.assertEqual(result["errors"], [])
        self.assertTrue(result["upstreamErrors"])
        self.assertEqual(baseline, before)

    def test_native_text_callout_shapes_are_scoped_without_unknown_shape_admission(self) -> None:
        baseline, doc, profile = self.sketch_fixture()
        clip = doc["timeline"]["callout"]
        clip.pop("leftEdgeMods")
        for shape in (
            "speech-bubble",
            "speech-bubble2",
            "thought-bubble",
            "thought-bubble2",
            "text-arrow",
        ):
            clip["def"] = {"kind": "remix", "shape": shape}
            with self.subTest(shape=shape):
                result = schema_audit.audit(doc, baseline, profile)
                self.assertTrue(result["ok"])
                self.assertTrue(result["upstreamErrors"])
        clip["def"]["shape"] = "UnobservedCalloutShape"
        self.assertFalse(schema_audit.audit(doc, baseline, profile)["ok"])

    def test_text_callout_shape_correction_preserves_type_and_media_field_checks(self) -> None:
        baseline, original, profile = self.sketch_fixture()
        original["timeline"]["callout"] = {
            "_type": "Callout",
            "def": {"kind": "remix", "shape": "speech-bubble"},
        }
        for mutation in ("shape-type", "kind", "media-property"):
            doc = copy.deepcopy(original)
            clip = doc["timeline"]["callout"]
            if mutation == "shape-type":
                clip["def"]["shape"] = 1
            elif mutation == "kind":
                clip["def"]["kind"] = "UnobservedCalloutKind"
            else:
                clip["unrelated"] = True
            with self.subTest(mutation=mutation):
                self.assertFalse(schema_audit.audit(doc, baseline, profile)["ok"])

    def test_native_shape_presets_keep_community_errors_and_exact_identifiers(self) -> None:
        baseline, doc, profile = self.sketch_fixture()
        clip = doc["timeline"]["callout"]
        clip.pop("leftEdgeMods")
        for shape in ("shape-star", "shape-octagon"):
            clip["def"] = {"kind": "remix", "shape": shape}
            with self.subTest(shape=shape):
                self.assertFalse(schema_audit.audit(doc, baseline)["ok"])
                result = schema_audit.audit(doc, baseline, profile)
                self.assertTrue(result["ok"])
                self.assertTrue(result["upstreamErrors"])
        for shape in ("star", "octagon", "shape-star2", "Shape-Star", 1):
            clip["def"]["shape"] = shape
            with self.subTest(shape=shape):
                self.assertFalse(schema_audit.audit(doc, baseline, profile)["ok"])

    def test_native_shape_extension_keeps_kind_and_callout_payload_constraints(self) -> None:
        baseline, original, profile = self.sketch_fixture()
        original["timeline"]["callout"] = {
            "_type": "Callout",
            "def": {"kind": "remix", "shape": "shape-octagon"},
        }
        for mutation in ("kind", "media-property"):
            doc = copy.deepcopy(original)
            clip = doc["timeline"]["callout"]
            if mutation == "kind":
                clip["def"]["kind"] = "InventedShapeKind"
            else:
                clip["unrelated"] = True
            with self.subTest(mutation=mutation):
                self.assertFalse(schema_audit.audit(doc, baseline, profile)["ok"])

    def test_remaining_annotation_kinds_keep_raw_errors_and_exact_names(self) -> None:
        baseline, doc, profile = self.sketch_fixture()
        clip = doc["timeline"]["callout"]
        clip.pop("leftEdgeMods")
        for kind in ("TypeWinHighlighter", "TypeWinSpotlight", "TypeWinPixelate", "MacKey"):
            clip["def"] = {"kind": kind}
            with self.subTest(kind=kind):
                self.assertFalse(schema_audit.audit(doc, baseline)["ok"])
                result = schema_audit.audit(doc, baseline, profile)
                self.assertTrue(result["ok"])
                self.assertTrue(result["upstreamErrors"])
        for kind in ("Highlighter", "TypeWinSpotLight", "TypeWinPixelate2", "mackey", 1):
            clip["def"]["kind"] = kind
            with self.subTest(kind=kind):
                self.assertFalse(schema_audit.audit(doc, baseline, profile)["ok"])

    def test_remaining_annotation_kinds_preserve_media_payload_constraints(self) -> None:
        baseline, doc, profile = self.sketch_fixture()
        clip = doc["timeline"]["callout"]
        clip.pop("leftEdgeMods")
        for kind in ("TypeWinHighlighter", "TypeWinSpotlight", "TypeWinPixelate", "MacKey"):
            clip["def"] = {"kind": kind}
            clip["unrelated"] = True
            with self.subTest(kind=kind):
                self.assertFalse(schema_audit.audit(doc, baseline, profile)["ok"])

    def test_sketch_correction_retains_modifier_and_unknown_payload_rejections(self) -> None:
        baseline, original, profile = self.sketch_fixture()
        for mutation in (
            "kind",
            "group",
            "duration",
            "negative",
            "func",
            "name",
            "extra",
            "empty",
            "multiple",
            "missing",
            "unrelated",
        ):
            doc = copy.deepcopy(original)
            clip = doc["timeline"]["callout"]
            modifier = clip["leftEdgeMods"][0]
            if mutation == "kind":
                clip["def"]["kind"] = "UnobservedSketchKind"
            elif mutation == "group":
                modifier["group"] = "UnobservedGroup"
            elif mutation == "duration":
                modifier["duration"] = "705600000"
            elif mutation == "negative":
                modifier["duration"] = -1
            elif mutation in {"func", "name"}:
                modifier["parameters"][0][mutation] = "UnobservedValue"
            elif mutation == "extra":
                modifier["extra"] = True
            elif mutation == "empty":
                clip["leftEdgeMods"] = []
            elif mutation == "multiple":
                clip["leftEdgeMods"].append(copy.deepcopy(modifier))
            elif mutation == "missing":
                del modifier["parameters"][0]["func"]
            else:
                clip["unrelated"] = True
            with self.subTest(mutation=mutation):
                self.assertFalse(schema_audit.audit(doc, baseline, profile)["ok"])

    def test_format_ten_profile_is_independent_and_keeps_type_constraints(self) -> None:
        baseline, doc, profile = self.current_profile_fixture()
        for name in (
            "CursorSmoothing",
            "Tiling",
            "tapGestureEffect",
            "doubleTapGestureEffect",
            "tapAndHoldGestureEffect",
            "pinchGestureEffect",
            "swipeGestureEffect",
            "WinCompression",
            "Pitch",
            "CRT Monitor",
            "Static Noise",
            "Torn Edge",
            "Vignette",
            "CursorColor",
            "CursorGlow",
            "CursorHilight",
            "CursorMagnify",
            "CursorSpotlight",
            "Cursor Isolation",
            "Gradient",
            "Lens",
            "Negative",
            "Keystroke",
            "FrontMostWindowHighlight",
            "CursorPath",
        ):
            doc["timeline"]["effect"]["effectName"] = name
            self.assertFalse(schema_audit.audit(doc, baseline)["ok"])
            self.assertTrue(schema_audit.audit(doc, baseline, profile)["ok"])
        doc["timeline"]["sourceTrack"]["transcriptionSet"] = "yes"
        self.assertFalse(schema_audit.audit(doc, baseline, profile)["ok"])
        doc["timeline"]["sourceTrack"]["transcriptionSet"] = True
        doc["timeline"]["effect"]["effectName"] = "InventedEffect"
        self.assertFalse(schema_audit.audit(doc, baseline, profile)["ok"])
        with self.assertRaisesRegex(ValueError, "does not match"):
            schema_audit.audit(doc, baseline, self.profile)
        doc["version"] = "9.0"
        with self.assertRaisesRegex(ValueError, "does not match"):
            schema_audit.audit(doc, baseline, profile)

    def test_native_gesture_category_does_not_relax_other_category_values(self) -> None:
        baseline, doc, profile = self.current_profile_fixture()
        effect = doc["timeline"]["effect"]
        effect.update(effectName="tapGestureEffect", category="categoryGestureEffects")
        self.assertFalse(schema_audit.audit(doc, baseline)["ok"])
        self.assertTrue(schema_audit.audit(doc, baseline, profile)["ok"])
        for category in ("categoryInvented", 1):
            effect["category"] = category
            with self.subTest(category=category):
                self.assertFalse(schema_audit.audit(doc, baseline, profile)["ok"])

    def test_current_transition_identifiers_keep_the_upstream_enum_unchanged(self) -> None:
        baseline, doc, profile = self.current_profile_fixture()
        original = copy.deepcopy(baseline)
        transition = {"name": "Accordion", "duration": 352800000, "leftMedia": 6, "rightMedia": 7}
        doc["timeline"]["track"] = {"transitions": [transition]}
        for name in (
            "Accordion",
            "ActionWipe",
            "AngledLineWipe",
            "AngledSliders",
            "AnimatedMosaic",
            "ArrowSlice",
            "Arrows",
            "ArrowsSolid",
            "BarWipe",
            "BarnDoor",
            "Bars",
            "Blinds",
            "Blob",
            "Blob2",
            "BlurZoom",
            "Bounce",
            "BoxIris",
            "Bubbles",
            "Bubbles2",
            "Burn",
            "BurnThroughFade",
            "BurstingHeart",
            "CardFlip",
            "CardFlipSwap",
            "CardSlide",
            "CardSwap",
            "CascadingSquares",
            "CellZoom",
            "CenterSlice",
            "CheckerBoard",
            "Chevrons",
            "CircleBloom",
            "CircleCrop",
            "CircleOffset",
            "CircleReveal",
            "CircleSlice2",
            "CircleStretch",
            "Circles",
            "ColorBurn",
            "ColorDistance",
            "ColorSpinDoor",
            "ColorWipe",
            "ConcentricRings",
            "CrossZoom",
            "Cube",
            "CubeRotate",
            "DiagonalMove",
            "DiagonalSlice",
            "DialWipe",
            "Diamonds",
            "Digital",
            "Dissolve",
            "DistortedFall",
            "Doorway",
            "Drawbridge",
            "Drop",
            "Drops",
            "ExpandingSquares",
            "Fade",
            "FadeThroughBlack",
            "Fall",
            "FallingHearts",
            "Fan",
            "Flare",
            "Flare2",
            "Flashback",
            "Flip",
            "Fold",
            "FoldShut",
            "FourColorIris",
            "FourColorWipe",
            "FourSquares",
            "GeometricSlice1",
            "BlurSlide",
            "Glitch",
            "Glitch2",
            "Glitch3",
            "Glow",
            "GradientDoor",
            "GradientWipe",
            "GridFlip",
            "GrowingSquares",
            "HeartFlips",
            "HeartOffset",
            "HeartPops",
            "HexMagnify",
            "HexSpinCascade",
            "Hexagonalize",
            "Hexagons",
            "HitchPush",
            "BlurStretch",
            "BlurStretch2",
            "ImplodingHexagons",
            "ImplodingSquares",
            "Inset",
            "Interference",
            "InvertedPageCurl",
            "InwardSlice",
            "Iris",
            "JaggedWipe",
            "LikesNLoves",
            "LineWipe",
            "LinearBlur",
            "LuminanceFadeIn",
            "LuminanceFadeOut",
            "Morph",
            "MultiplyBlend",
            "Noise",
            "OpacitySquares",
            "PageRoll",
            "PageTurn",
            "PaintArcs",
            "PaintDrip",
            "PaintStrokes",
            "PaintSwipe",
            "PerlinBlobs",
            "Pixelate",
            "Portal",
            "PrismWipe",
            "PurpleTriangles",
            "Push",
            "Puzzle",
            "QuarterSplit",
            "RadialBlur",
            "RadialWipe",
            "RandomBars",
            "RandomDissolve",
            "RandomSquares",
            "RhombusDots",
            "Ripple",
            "RollingSquares",
            "RoundedSquares",
            "Shatter",
            "ShiftingHearts",
            "Shockwave",
            "ShuffleSlice",
            "ShutterSnap",
            "Shutters",
            "SimpleZoom",
            "SlamShut",
            "SlantShutters",
            "SlideLeft",
            "SlideRight",
            "SlidingBars",
            "SlidingTriangles",
            "Smileys",
            "SmoothSlide",
            "SnapShot",
            "Spin",
            "SpinFlip",
            "SpinView",
            "SpinView2",
            "BlurSpin",
            "SpinningBlinds",
            "SpinningColorWipe",
            "Spiral",
            "SquareDrops",
            "SquarePops",
            "SquaresRotateAway",
            "Static",
            "Stretch",
            "Strips",
            "Swap",
            "Swing",
            "SwirlSpin",
            "Tile",
            "Transmission",
            "Unfold",
            "BlurOffset",
            "Vortex",
            "WalkingWipe",
            "Waves",
            "Waves2",
            "Wheel",
            "SphericalSpin",
            "ZigZag",
            "ZoomBlur",
            "ZoomFade",
            "ZoomIn",
        ):
            transition["name"] = name
            with self.subTest(name=name):
                self.assertTrue(schema_audit.audit(doc, baseline, profile)["ok"])
        self.assertEqual(baseline, original)
        legacy = schema_audit.apply_profile(baseline, self.profile)
        names = legacy["definitions"]["track"]["properties"]["transitions"]["items"]["properties"][
            "name"
        ]["enum"]
        self.assertNotIn("ActionWipe", names)

    def test_transition_overlay_preserves_name_type_field_and_build_rejection(self) -> None:
        baseline, doc, profile = self.current_profile_fixture()
        valid = {"name": "ActionWipe", "duration": 352800000, "leftMedia": 6, "rightMedia": 7}
        for key, value in (
            ("name", "InventedTransition"),
            ("name", 1),
            ("duration", "352800000"),
            ("leftMedia", "6"),
            ("unexpected", True),
        ):
            transition = dict(valid)
            transition[key] = value
            doc["timeline"]["track"] = {"transitions": [transition]}
            with self.subTest(key=key, value=value):
                self.assertFalse(schema_audit.audit(doc, baseline, profile)["ok"])
        doc["timeline"]["track"] = {"transitions": [valid]}
        doc["authoringClientName"]["version"] = "2026.2.5"
        with self.assertRaisesRegex(ValueError, "does not match"):
            schema_audit.audit(doc, baseline, profile)

    def test_click_effects_are_build_scoped_and_preserve_unknown_identifier_rejection(self) -> None:
        baseline, doc, profile = self.current_profile_fixture()
        # The pinned upstream already admits LeftClickScaling and its category.
        baseline["definitions"]["effect"]["properties"]["effectName"]["enum"].append(
            "LeftClickScaling"
        )
        baseline["definitions"]["effect"]["properties"]["category"]["enum"].append(
            "categoryClickEffects"
        )
        doc["timeline"]["effect"]["category"] = "categoryClickEffects"
        for side in ("Left", "Right"):
            for preset in (
                "Rings",
                "Ripple",
                "Scaling",
                "Scope",
                "Target",
                "Warp",
                "Burst1",
                "Burst2",
                "Burst3",
                "Burst4",
                "Zoom",
                "Sound",
            ):
                name = side + "Click" + preset
                doc["timeline"]["effect"]["effectName"] = name
                with self.subTest(effect=name):
                    self.assertTrue(schema_audit.audit(doc, baseline, profile)["ok"])
        for name in ("LeftClickBurst5", "RightClickRing", "rightClickSound", 4):
            doc["timeline"]["effect"]["effectName"] = name
            self.assertFalse(schema_audit.audit(doc, baseline, profile)["ok"])
        doc["timeline"]["effect"]["effectName"] = "RightClickSound"
        with self.assertRaisesRegex(ValueError, "does not match"):
            schema_audit.audit(doc, baseline, self.profile)

    def test_recording_event_category_is_build_scoped_and_keeps_enum_types(self) -> None:
        baseline, doc, profile = self.current_profile_fixture()
        effect = doc["timeline"]["effect"]
        effect.update(effectName="Keystroke", category="categoryScreenRecordingEffects")
        self.assertFalse(schema_audit.audit(doc, baseline)["ok"])
        self.assertTrue(schema_audit.audit(doc, baseline, profile)["ok"])
        effect["effectName"] = "FrontMostWindowHighlight"
        self.assertTrue(schema_audit.audit(doc, baseline, profile)["ok"])
        for category in ("categoryInvented", 1):
            effect["category"] = category
            self.assertFalse(schema_audit.audit(doc, baseline, profile)["ok"])
        effect["category"] = "categoryScreenRecordingEffects"
        with self.assertRaisesRegex(ValueError, "does not match"):
            schema_audit.audit(doc, baseline, self.profile)

    def test_current_behaviors_keep_distinct_native_phase_names_and_build_scope(self) -> None:
        baseline, doc, profile = self.current_profile_fixture()
        baseline["definitions"]["GenericBehaviorEffect"]["properties"]["effectName"]["enum"] = [
            "fade",
            "flyIn",
            "popUp",
            "pulsating",
            "reveal",
            "shifting",
            "sliding",
        ]
        baseline["definitions"]["timeline"]["properties"]["behavior"] = {
            "$ref": "#/definitions/GenericBehaviorEffect"
        }
        matrix = [
            ("drifting", "drifting", "drifting", "drifting"),
            ("explode", "implode", "none", "explode"),
            ("fade", "fadeIn", "none", "fadeOut"),
            ("flyIn", "flyIn", "none", "flyOut"),
            ("jumpAndFall", "bounceIn", "jump", "drop"),
            ("popUp", "hinge", "popUp", "hinge"),
            ("pulsating", "grow", "pulsate", "shrink"),
            ("reveal", "reveal", "reveal", "reveal"),
            ("scale", "grow", "none", "shrink"),
            ("shifting", "shifting", "shifting", "shifting"),
            ("sliding", "sliding", "fading", "sliding"),
            ("tremble", "none", "tremble", "none"),
            ("wiggle", "none", "wiggle", "none"),
        ]
        for name, entry, center, exit_name in matrix:
            doc["timeline"] = {
                "behavior": {
                    "effectName": name,
                    "in": {"attributes": {"name": entry}},
                    "center": {"attributes": {"name": center}},
                    "out": {"attributes": {"name": exit_name}},
                }
            }
            with self.subTest(behavior=name):
                self.assertTrue(schema_audit.audit(doc, baseline, profile)["ok"])
        behavior = doc["timeline"]["behavior"]
        for phase, wrong in (("in", "wiggle"), ("center", "implode"), ("out", "dropAndFall")):
            candidate = copy.deepcopy(doc)
            candidate["timeline"]["behavior"][phase]["attributes"]["name"] = wrong
            self.assertFalse(schema_audit.audit(candidate, baseline, profile)["ok"])
        behavior["effectName"] = "InventedBehavior"
        self.assertFalse(schema_audit.audit(doc, baseline, profile)["ok"])
        behavior["effectName"] = "wiggle"
        with self.assertRaisesRegex(ValueError, "does not match"):
            schema_audit.audit(doc, baseline, self.profile)

    def test_fresh_format_ten_recording_metadata_keeps_object_and_unknown_field_checks(
        self,
    ) -> None:
        baseline, doc, profile = self.current_profile_fixture()
        doc["timeline"]["metadata"] = {"RecordingWidth": "3024", "RecordingHeight": "1898"}
        self.assertFalse(schema_audit.audit(doc, baseline)["ok"])
        self.assertTrue(schema_audit.audit(doc, baseline, profile)["ok"])
        doc["timeline"]["metadata"] = "3024x1898"
        self.assertFalse(schema_audit.audit(doc, baseline, profile)["ok"])
        doc["timeline"]["metadata"] = {}
        doc["timeline"]["invented"] = True
        self.assertFalse(schema_audit.audit(doc, baseline, profile)["ok"])

    def test_format_ten_native_empty_save_can_omit_source_bin(self) -> None:
        baseline, doc, profile = self.current_profile_fixture()
        doc.pop("sourceBin")
        doc["timeline"] = {}
        self.assertFalse(schema_audit.audit(doc, baseline)["ok"])
        self.assertTrue(schema_audit.audit(doc, baseline, profile)["ok"])

    def test_format_ten_vtt_caption_accepts_text_but_rejects_unobserved_styles(self) -> None:
        baseline, doc, profile = self.current_profile_fixture()
        caption = {
            "id": 6,
            "_type": "Caption",
            "allowTrimOut": False,
            "maxMediaDuration": 5644800000.0,
            "start": 0,
            "duration": 5644800000,
            "mediaStart": 0,
            "mediaDuration": 5644800000,
            "scalar": 1,
            "effects": [],
            "metadata": {},
            "animationTracks": {},
            "parameters": {"captionData": {"type": "caption", "keyframes": []}},
        }
        value = {"text": 'VTT café "quoted" & timing', "textAttributes": None}
        caption["parameters"]["captionData"]["keyframes"].append(
            {"time": 0, "endTime": 0, "duration": 0, "value": value}
        )
        doc["timeline"] = {"clip": caption}
        self.assertFalse(schema_audit.audit(doc, baseline)["ok"])
        self.assertTrue(schema_audit.audit(doc, baseline, profile)["ok"])
        value["textAttributes"] = {"font": "Unobserved style"}
        self.assertFalse(schema_audit.audit(doc, baseline, profile)["ok"])

    def test_cli_selects_the_requested_format_ten_profile(self) -> None:
        baseline, doc, profile = self.current_profile_fixture()
        raw = json.dumps(baseline).encode()
        with tempfile.TemporaryDirectory() as temp:
            schema_path = Path(temp) / "schema.json"
            schema_path.write_bytes(raw)
            project_path = Path(temp) / "project.tscproj"
            project_path.write_text(json.dumps(doc))
            output = io.StringIO()
            with (
                patch.object(schema_audit, "UPSTREAM_SHA256", hashlib.sha256(raw).hexdigest()),
                redirect_stdout(output),
            ):
                code = schema_audit.main(
                    [
                        "check",
                        "--schema",
                        str(schema_path),
                        "--profile",
                        "mac-2026.2.4",
                        str(project_path),
                    ]
                )
            self.assertEqual(code, 0)
            result = json.loads(output.getvalue())
            self.assertTrue(result["ok"])
            self.assertEqual(result["projects"][0]["profile"], profile["id"])

    def test_format_ten_native_colorize_enum_preserves_restrictive_validation(self) -> None:
        baseline, doc, profile = self.current_profile_fixture()
        original = copy.deepcopy(baseline)
        doc["timeline"]["effect"] = {
            "effectName": "Colorize",
            "category": "categoryVisualEffects",
        }
        result = schema_audit.audit(doc, baseline, profile)
        self.assertTrue(result["ok"])
        self.assertTrue(result["upstreamErrors"])
        self.assertEqual(baseline, original)
        for change in [
            {"effectName": "InventedColorize"},
            {"category": "InventedCategory"},
            {"unexpected": True},
            {"effectName": 1},
        ]:
            candidate = copy.deepcopy(doc)
            candidate["timeline"]["effect"].update(change)
            with self.subTest(change=change):
                self.assertFalse(schema_audit.audit(candidate, baseline, profile)["ok"])
        doc["authoringClientName"]["version"] = "2026.2.5"
        with self.assertRaises(ValueError):
            schema_audit.audit(doc, baseline, profile)

    def test_profile_accepts_native_pixelate_and_highlighter_kinds_only(self) -> None:
        baseline = schema()
        baseline["definitions"]["timeline"]["properties"]["annotation"] = {
            "$ref": "#/definitions/calloutDef"
        }
        for kind in ("TypeWinPixelate", "TypeWinHighlighter", "InventedRedaction"):
            doc = copy.deepcopy(self.doc)
            doc["timeline"]["annotation"] = {"kind": kind}
            with self.subTest(kind=kind):
                self.assertFalse(schema_audit.audit(doc, baseline)["ok"])
                self.assertEqual(
                    schema_audit.audit(doc, baseline, self.profile)["ok"],
                    kind != "InventedRedaction",
                )

    def test_profile_keeps_native_rejected_behavior_names_outside_enum(self) -> None:
        baseline = schema()
        baseline["definitions"]["timeline"]["properties"]["behavior"] = {
            "$ref": "#/definitions/GenericBehaviorEffect"
        }
        for name in ("flyOut", "emphasize", "jiggle"):
            with self.subTest(name=name):
                doc = copy.deepcopy(self.doc)
                doc["timeline"]["behavior"] = {"effectName": name}
                result = schema_audit.audit(doc, baseline, self.profile)
                self.assertFalse(result["ok"])
                self.assertTrue(any(name in error["message"] for error in result["errors"]))

    def test_raw_audit_never_silently_applies_corrections(self) -> None:
        report = schema_audit.audit(self.doc, schema())
        self.assertFalse(report["ok"])
        self.assertIsNone(report["profile"])
        self.assertEqual(report["upstreamErrors"], report["errors"])

    def test_union_diagnostics_select_actual_clip_family(self) -> None:
        union = {
            "oneOf": [{"$ref": "#/definitions/VMFile"}, {"$ref": "#/definitions/Callout"}],
            "definitions": {
                "VMFile": {
                    "type": "object",
                    "required": ["src"],
                    "properties": {"_type": {"const": "VMFile"}},
                },
                "Callout": {
                    "type": "object",
                    "required": ["def"],
                    "properties": {"_type": {"const": "Callout"}},
                },
            },
        }
        errors = schema_audit.errors_for(union, {"_type": "VMFile"})
        self.assertEqual(len(errors), 1)
        self.assertIn("src", errors[0]["message"])
        self.assertNotIn("def", errors[0]["message"])

    def test_fetch_rejects_changed_bytes_before_writing(self) -> None:
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "schema.json"
            result = subprocess.CompletedProcess([], 0, b"{}", b"")
            with patch.object(schema_audit.subprocess, "run", return_value=result):
                with self.assertRaisesRegex(ValueError, "hash differs"):
                    schema_audit.fetch_schema(output)
            self.assertFalse(output.exists())

    def test_fetch_is_idempotent_and_preserves_unrelated_existing_file(self) -> None:
        import hashlib

        data = json.dumps(schema()).encode()
        with tempfile.TemporaryDirectory() as temp:
            output = Path(temp) / "schema.json"
            result = subprocess.CompletedProcess([], 0, data, b"")
            with (
                patch.object(schema_audit.subprocess, "run", return_value=result),
                patch.object(schema_audit, "UPSTREAM_SHA256", hashlib.sha256(data).hexdigest()),
            ):
                schema_audit.fetch_schema(output)
                schema_audit.fetch_schema(output)
                self.assertEqual(output.read_bytes(), data)
                output.write_bytes(b"unrelated")
                with self.assertRaisesRegex(ValueError, "different data"):
                    schema_audit.fetch_schema(output)
                self.assertEqual(output.read_bytes(), b"unrelated")


if __name__ == "__main__":
    unittest.main()
