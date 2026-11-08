from __future__ import annotations

from contextlib import redirect_stdout
import copy
import io
import json
from pathlib import Path
import tempfile
from typing import Any
import unittest

from test_animations import visual
from test_effect_grouped_recordings import grouped
from test_matte_linked_recordings import fixture as recorded, wrapper
from test_matte_stitched_linked_recordings import fixture as stitched
from test_motion_paths import spec
import motion_paths
import project

RATE = 705600000


def fixture():
    doc = recorded()
    doc["authoringClientName"]["version"] = "2026.2.5"
    for owner in (wrapper(doc), visual(doc), wrapper(doc)["audio"]):
        owner.update(start=RATE, duration=4 * RATE, mediaStart=2 * RATE, mediaDuration=8 * RATE)
    return doc


def native_effect() -> dict[str, Any]:
    return dict(
        effectName="MediaPath",
        bypassed=False,
        category="categoryVisualEffects",
        parameters=dict(
            mediaLocation=dict(
                type="point",
                keyframes=[
                    dict(time=2822400000, endTime=2822400000, duration=0, value=[0, 0, 0]),
                    dict(
                        time=4233600000,
                        endTime=4233600000,
                        duration=0,
                        value=[256, 144, 0],
                        interp=dict(bezier=[[128, 0, 0], [128, 144, 0], "eioe"]),
                    ),
                ],
            ),
            mediaPathAutoOrient=0,
        ),
        metadata=dict(effectIndex="0"),
    )


class LinkedRecordingMotionPathTests(unittest.TestCase):
    def test_native_constructor_and_aliases_preserve_audio_cursors_and_sources(self):
        doc = fixture()
        before = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        for owner in (wrapper(expected), visual(expected)):
            owner["effects"] = [native_effect()]
        wrapper(expected)["metadata"]["effectApplied"] = "MediaPath"
        for clip_id in (10, 3):
            actual = motion_paths.set_path(doc, clip_id, spec())
            self.assertEqual(actual, expected)
            self.assertEqual(motion_paths.set_path(actual, clip_id, spec()), actual)
        self.assertEqual(doc, before)

    def test_orientation_bypass_enable_and_removal_match_native_companions(self):
        plain = motion_paths.set_path(fixture(), 10, spec())
        expected = copy.deepcopy(plain)
        for owner in (wrapper(expected), visual(expected)):
            owner["effects"][0]["parameters"]["mediaPathAutoOrient"] = 1
        wrapper(expected)["metadata"]["default-MediaPath-mediaPathAutoOrient"] = "0"
        visual(expected)["parameters"]["rotation2"] = dict(
            type="double", defaultValue=0.0, interp="eioe"
        )
        oriented = motion_paths.set_path(plain, 3, {**spec(), "autoOrient": True})
        self.assertEqual(oriented, expected)
        before = copy.deepcopy(oriented)
        bypassed = motion_paths.set_bypass(oriented, 10, True)
        for owner in (wrapper(expected), visual(expected)):
            owner["effects"][0]["bypassed"] = True
        visual(expected)["parameters"].pop("rotation2")
        self.assertEqual(bypassed, expected)
        off = motion_paths.set_path(bypassed, 3, {**spec(), "autoOrient": False})
        self.assertNotIn("rotation2", visual(off)["parameters"])
        self.assertEqual(motion_paths.set_path(off, 10, {**spec(), "autoOrient": True}), bypassed)
        self.assertEqual(motion_paths.set_bypass(bypassed, 3, False), oriented)
        removed = motion_paths.remove_path(oriented, 10)
        expected = copy.deepcopy(oriented)
        for owner in (wrapper(expected), visual(expected)):
            owner["effects"] = []
        visual(expected)["parameters"].pop("rotation2")
        self.assertEqual(removed, expected)
        self.assertEqual(motion_paths.remove_path(removed, 3), removed)
        self.assertEqual(oriented, before)

    def test_audio_tokens_reserve_new_identity_without_changing_other_effects(self):
        doc = fixture()
        for owner in (wrapper(doc), visual(doc)):
            owner["effects"] = [dict(effectName="Other", metadata=dict(effectIndex="2"))]
        wrapper(doc)["audio"]["effects"] = [
            dict(effectName="AudioOther", metadata=dict(effectIndex="7"), opaque=["keep"])
        ]
        expected = copy.deepcopy(doc)
        for owner in (wrapper(expected), visual(expected)):
            effect = native_effect()
            effect["metadata"]["effectIndex"] = "8"
            owner["effects"].append(effect)
        wrapper(expected)["metadata"]["effectApplied"] = "MediaPath"
        self.assertEqual(motion_paths.set_path(doc, 10, spec()), expected)

    def test_unverified_containers_and_audio_clock_bindings_refuse_without_mutation(self):
        invalid = [(grouped(fixture()), "root linked"), (stitched(), "root linked")]
        for fault in ("missing-audio", "source", "missing-clock", "clock", "token"):
            doc = fixture()
            if fault == "missing-audio":
                wrapper(doc).pop("audio")
            elif fault == "source":
                wrapper(doc)["audio"]["src"] = 2
            elif fault == "missing-clock":
                visual(doc).pop("mediaStart")
            elif fault == "clock":
                visual(doc)["mediaStart"] += RATE
            else:
                visual(doc)["effects"] = [dict(effectName="Other", metadata=dict(effectIndex="x"))]
            invalid.append((doc, "audio|source|clocks|token"))
        for doc, message in invalid:
            before = copy.deepcopy(doc)
            for operation in (
                lambda: motion_paths.set_path(doc, 10, spec()),
                lambda: motion_paths.set_bypass(doc, 3, True),
                lambda: motion_paths.remove_path(doc, 10),
            ):
                with self.subTest(message=message), self.assertRaisesRegex(ValueError, message):
                    operation()
                self.assertEqual(doc, before)

    def test_conflicting_path_mirrors_and_nonzero_rotation_refuse(self):
        doc = motion_paths.set_path(fixture(), 10, spec())
        visual(doc)["effects"][0]["parameters"]["mediaPathAutoOrient"] = 1
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "conflicting"):
            motion_paths.set_path(doc, 10, spec())
        self.assertEqual(doc, before)
        doc = motion_paths.set_path(fixture(), 10, spec())
        visual(doc)["parameters"]["rotation2"] = 0.25
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "rotation"):
            motion_paths.set_path(doc, 3, {**spec(), "autoOrient": True})
        self.assertEqual(doc, before)

    def test_cli_stages_separate_candidates_and_repeats_as_noop(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, request, output = (
                root / name for name in ("input.json", "spec.json", "candidate.json")
            )
            source.write_bytes(project.encode_document(fixture()))
            request.write_text(json.dumps(spec()))
            before = source.read_bytes()
            args = [
                "set-path",
                str(source),
                "--clip-id",
                "10",
                "--spec",
                str(request),
                "--output",
                str(output),
            ]
            for written in (True, False):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(motion_paths.main(args), 0)
                report = json.loads(stdout.getvalue())
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
            self.assertEqual(project.load(output)[0], motion_paths.set_path(fixture(), 10, spec()))
            self.assertEqual(source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
