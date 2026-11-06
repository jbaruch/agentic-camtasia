from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

from test_effect_linked_recordings import native_template
from test_matte_linked_recordings import wrapper
from test_animations import visual
import effect_curves
import project


def fixture():
    doc = native_template()
    visual(doc)["animationTracks"] = {}
    for owner in (wrapper(doc), visual(doc)):
        owner["effects"][0]["parameters"]["intensity"] = dict(
            type="double", defaultValue=0.0, uiHints=dict(userInterfaceType=0, unitType=0)
        )
    wrapper(doc)["metadata"]["default-Sepia-intensity"] = "1"
    return doc


def spec(easing="linear", version=2) -> dict[str, Any]:
    segment: dict[str, Any] = dict(start=0, end=1, value=1)
    if version == 2:
        segment["easing"] = easing
    return dict(schema_version=version, defaultValue=0, segments=[segment])


def edit(doc, settings=None, clip=10, **kwargs):
    return effect_curves.edit_curve(
        doc, clip, "Sepia", "intensity", spec() if settings is None else settings, **kwargs
    )


class LinkedRecordingEffectCurveTests(unittest.TestCase):
    def test_fixed_native_linear_source_clock_and_complete_document_match_both_aliases(self):
        doc = fixture()
        before = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        frame = dict(
            time=1411200000, endTime=2822400000, duration=1411200000, value=1.0, interp="linr"
        )
        for owner in (wrapper(expected), visual(expected)):
            owner["effects"][0]["parameters"]["intensity"]["keyframes"] = [copy.deepcopy(frame)]
        visual(expected)["animationTracks"] = dict(
            visual=[dict(endTime=2822400000, duration=1411200000, interp="linr")]
        )
        self.assertEqual(edit(doc), expected)
        self.assertEqual(edit(doc, clip=3), expected)
        self.assertEqual(doc, before)
        self.assertEqual(wrapper(expected)["audio"], wrapper(doc)["audio"])
        self.assertEqual(expected["sourceBin"], doc["sourceBin"])

    def test_explicit_easing_codes_preserve_both_native_descriptors_and_other_effect_fields(self):
        for easing, code in (
            ("linear", "linr"),
            ("exponential", "eioe"),
            ("bounce", "bnce"),
            ("spring", "sprg"),
        ):
            doc = fixture()
            for owner, role in ((wrapper(doc), "wrapper"), (visual(doc), "video")):
                owner["effects"][0]["metadata"]["opaque"] = [role]
                owner["effects"][0]["parameters"]["intensity"]["opaque"] = ["keep"]
            expected = copy.deepcopy(doc)
            for owner in (wrapper(expected), visual(expected)):
                owner["effects"][0]["parameters"]["intensity"]["keyframes"] = [
                    dict(
                        time=1411200000,
                        endTime=2822400000,
                        duration=1411200000,
                        value=1.0,
                        interp=code,
                    )
                ]
            visual(expected)["animationTracks"] = dict(
                visual=[dict(endTime=2822400000, duration=1411200000, interp=code)]
            )
            with self.subTest(easing=easing):
                self.assertEqual(edit(doc, spec(easing)), expected)

    def test_spring_preserves_matching_linear_geometry_interval_and_cursor_payload(self):
        doc = fixture()
        owner = visual(doc)
        owner["animationTracks"] = dict(
            visual=[dict(endTime=2822400000, duration=1411200000, interp="linr", opaque=[7])]
        )
        owner["parameters"]["translation0"] = dict(
            type="double",
            defaultValue=-60.0,
            keyframes=[
                dict(
                    time=1411200000,
                    endTime=2822400000,
                    duration=1411200000,
                    value=60.0,
                    interp="linr",
                )
            ],
        )
        before = copy.deepcopy(doc)
        result = edit(doc, spec("spring"))
        self.assertEqual(visual(result)["parameters"], owner["parameters"])
        self.assertEqual(visual(result)["animationTracks"], owner["animationTracks"])
        for target in (wrapper(result), visual(result)):
            self.assertEqual(
                target["effects"][0]["parameters"]["intensity"]["keyframes"],
                [
                    dict(
                        time=1411200000,
                        endTime=2822400000,
                        duration=1411200000,
                        value=1.0,
                        interp="sprg",
                    )
                ],
            )
        self.assertEqual(doc, before)

    def test_version_one_retains_linear_parameter_interpolation_and_clear_preserves_it(self):
        doc = fixture()
        result = edit(doc, spec(version=1))
        for owner in (wrapper(result), visual(result)):
            self.assertEqual(owner["effects"][0]["parameters"]["intensity"]["interp"], "linr")
        expected = copy.deepcopy(result)
        for owner in (wrapper(expected), visual(expected)):
            parameter = owner["effects"][0]["parameters"]["intensity"]
            parameter.pop("keyframes")
            parameter["defaultValue"] = 0.25
        cleared = effect_curves.clear_curve(result, 3, "Sepia", "intensity", "1/4")
        self.assertEqual(cleared, expected)
        self.assertEqual(
            effect_curves.clear_curve(cleared, 10, "Sepia", "intensity", "1/4"), cleared
        )

    def test_clear_nonlinear_mirrors_preserves_all_other_timing_reset_and_audio_state(self):
        doc = edit(fixture(), spec("spring"))
        before = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        for owner in (wrapper(expected), visual(expected)):
            parameter = owner["effects"][0]["parameters"]["intensity"]
            parameter.pop("keyframes")
            parameter["defaultValue"] = 0.0
        self.assertEqual(effect_curves.clear_curve(doc, 10, "Sepia", "intensity", 0), expected)
        self.assertEqual(doc, before)

    def test_ordered_segments_keep_exact_gaps_source_positions_and_repeat_is_unchanged(self):
        doc = fixture()
        settings = dict(
            schema_version=2,
            defaultValue=0,
            segments=[
                dict(start=0, end=1, value=0.5, easing="bounce"),
                dict(start=2, end=3, value=1, easing="spring"),
            ],
        )
        result = edit(doc, settings)
        expected = [
            dict(
                time=1411200000, endTime=2822400000, duration=1411200000, value=0.5, interp="bnce"
            ),
            dict(
                time=4233600000, endTime=5644800000, duration=1411200000, value=1.0, interp="sprg"
            ),
        ]
        for owner in (wrapper(result), visual(result)):
            self.assertEqual(owner["effects"][0]["parameters"]["intensity"]["keyframes"], expected)
        self.assertEqual(edit(result, settings), result)

    def test_repeated_effects_require_token_and_leave_the_other_identity_unchanged(self):
        doc = fixture()
        for owner in (wrapper(doc), visual(doc)):
            other = copy.deepcopy(owner["effects"][0])
            other["metadata"]["effectIndex"] = "4"
            owner["effects"].append(other)
        with self.assertRaisesRegex(ValueError, "unique effectIndex"):
            edit(doc)
        before = copy.deepcopy(doc)
        result = edit(doc, token="4")
        self.assertEqual(wrapper(result)["effects"][0], wrapper(doc)["effects"][0])
        self.assertEqual(visual(result)["effects"][0], visual(doc)["effects"][0])
        self.assertIn("keyframes", wrapper(result)["effects"][1]["parameters"]["intensity"])
        self.assertEqual(doc, before)

    def test_missing_conflicting_boolean_and_nonpositive_clocks_refuse_without_mutation(self):
        for field in ("start", "duration", "mediaStart", "mediaDuration", "scalar"):
            for change in ("missing", "conflict", "boolean"):
                doc = fixture()
                if change == "missing":
                    visual(doc).pop(field)
                else:
                    visual(doc)[field] = (
                        True
                        if change == "boolean"
                        else 2
                        if field == "scalar"
                        else visual(doc)[field] + 1
                    )
                before = copy.deepcopy(doc)
                for operation in (
                    lambda: edit(doc),
                    lambda: effect_curves.clear_curve(doc, 3, "Sepia", "intensity", 0),
                ):
                    with self.subTest(field=field, change=change), self.assertRaises(ValueError):
                        operation()
                    self.assertEqual(doc, before)
        for field in ("editRate", "scalar"):
            doc = fixture()
            if field == "editRate":
                doc[field] = 0
            else:
                for owner in (wrapper(doc), visual(doc)):
                    owner[field] = 0
            with self.assertRaisesRegex(ValueError, "positive"):
                edit(doc)

    def test_unknown_audio_held_stitched_and_multiple_scene_owners_refuse(self):
        for change in (
            "missing-audio",
            "audio-kind",
            "audio-source",
            "boolean-source",
            "held",
            "stitched",
            "scenes",
        ):
            doc = fixture()
            if change == "missing-audio":
                wrapper(doc).pop("audio")
            elif change == "audio-kind":
                wrapper(doc)["audio"]["_type"] = "VMFile"
            elif change in ("audio-source", "boolean-source"):
                wrapper(doc)["audio"]["src"] = True if change == "boolean-source" else 2
            elif change in ("held", "stitched"):
                visual(doc)["_type"] = "ScreenIMFile" if change == "held" else "StitchedMedia"
            else:
                doc["timeline"]["sceneTrack"]["scenes"].append(dict(csml=dict(tracks=[])))
            before = copy.deepcopy(doc)
            for operation in (
                lambda: edit(doc),
                lambda: effect_curves.clear_curve(doc, 10, "Sepia", "intensity", 0),
            ):
                with self.subTest(change=change), self.assertRaises(ValueError):
                    operation()
                self.assertEqual(doc, before)

    def test_missing_duplicate_or_conflicting_mirrors_and_scalar_parameters_refuse(self):
        for change in ("missing", "token", "duplicate", "controls", "scalar", "point"):
            doc = fixture()
            if change == "missing":
                visual(doc)["effects"] = []
            elif change == "token":
                visual(doc)["effects"][0]["metadata"]["effectIndex"] = "1"
            elif change == "duplicate":
                visual(doc)["effects"].append(copy.deepcopy(visual(doc)["effects"][0]))
            elif change == "controls":
                visual(doc)["effects"][0]["bypassed"] = True
            else:
                for owner in (wrapper(doc), visual(doc)):
                    if change == "scalar":
                        owner["effects"][0]["parameters"]["intensity"] = 1.0
                    else:
                        owner["effects"][0]["parameters"]["intensity"]["keyframes"] = [
                            dict(
                                time=1411200000,
                                endTime=1411200000,
                                duration=0,
                                value=1,
                                interp="linr",
                            )
                        ]
            before = copy.deepcopy(doc)
            with self.subTest(change=change), self.assertRaises(ValueError):
                edit(doc)
            self.assertEqual(doc, before)

    def test_cli_stage_repeat_clear_and_invalid_later_segment_leave_input_files_unchanged(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, settings, output, cleared, badout = [
                root / name
                for name in (
                    "source.json",
                    "curve.json",
                    "candidate.json",
                    "cleared.json",
                    "bad.json",
                )
            ]
            source.write_bytes(project.encode_document(fixture()))
            original = source.read_bytes()
            settings.write_text(json.dumps(spec("spring")))
            common = ["--clip-id", "10", "--effect", "Sepia", "--parameter", "intensity"]
            args = ["set", str(source), *common, "--spec", str(settings), "--output", str(output)]
            for written in (True, False):
                with patch("sys.stdout", new_callable=io.StringIO) as stream:
                    self.assertEqual(effect_curves.main(args), 0)
                report = json.loads(stream.getvalue())
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
            with patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(
                    effect_curves.main(
                        ["clear", str(output), *common, "--value", "0", "--output", str(cleared)]
                    ),
                    0,
                )
            self.assertNotIn(
                "keyframes",
                wrapper(project.load(cleared)[0])["effects"][0]["parameters"]["intensity"],
            )
            invalid = spec()
            invalid["segments"].append(dict(start=1, end=4, value=0.5))
            settings.write_text(json.dumps(invalid))
            with patch("sys.stderr", new_callable=io.StringIO) as stream:
                self.assertEqual(
                    effect_curves.main(
                        [
                            "set",
                            str(source),
                            *common,
                            "--spec",
                            str(settings),
                            "--output",
                            str(badout),
                        ]
                    ),
                    1,
                )
            self.assertFalse(json.loads(stream.getvalue())["ok"])
            self.assertFalse(badout.exists())
            self.assertEqual(source.read_bytes(), original)

    def test_top_level_and_each_subcommand_help_emit_versioned_json(self):
        for command in ([], ["inspect"], ["set"], ["clear"]):
            with (
                patch("sys.stdout", new_callable=io.StringIO) as stream,
                self.assertRaises(SystemExit) as raised,
            ):
                effect_curves.main([*command, "--help"])
            self.assertEqual(raised.exception.code, 0)
            value = json.loads(stream.getvalue())
            self.assertEqual(
                (value["schema_version"], value["owner"], value["ok"]),
                (1, "camtasia-effect-curves", True),
            )
            self.assertIn("usage:", value["help"])


if __name__ == "__main__":
    unittest.main()
