from __future__ import annotations

import copy
from contextlib import redirect_stderr, redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from test_caption_highlights import fixture as highlight_fixture, selected
from test_captions import spec
import captions
import project

NAME = "dynamic-caption-block-transition-name"
REVERSE = "dynamic-caption-block-transition-reverse"
DURATION = "dynamic-caption-block-transition-duration"


def fixture(name="", reverse=0.0, duration=0.5):
    doc = highlight_fixture()
    selected(doc)["def"].update({NAME: name, REVERSE: reverse, DURATION: duration})
    selected(doc)["metadata"] = {"default-callout-" + NAME: "old", "opaque": ["retain"]}
    return doc


def grouped(doc):
    result = copy.deepcopy(doc)
    tracks = project.scene_tracks(result)[0]
    children = copy.deepcopy(tracks)
    tracks[:] = [
        dict(
            trackIndex=0,
            parameters={},
            medias=[
                dict(
                    id=20,
                    _type="Group",
                    start=captions.RATE,
                    duration=4 * captions.RATE,
                    mediaStart=captions.RATE,
                    mediaDuration=8 * captions.RATE,
                    scalar="1/2",
                    tracks=children,
                    attributes={"opaque": ["group"]},
                    parameters={},
                )
            ],
        )
    ]
    return result


class CaptionBlockTransitionTests(unittest.TestCase):
    def test_copy_name_only_preserves_complete_root_group_and_donor_payloads(self):
        for wrap in (lambda d: d, grouped):
            for choice in ("SlideLeft", "SavedNativeChoice"):
                destination = wrap(fixture("Fade", 1.0, 0.75))
                donor = wrap(fixture(choice, 0.0, 2.0))
                before, source_before = copy.deepcopy(destination), copy.deepcopy(donor)
                expected = copy.deepcopy(destination)
                selected(expected)["def"][NAME] = choice
                with self.subTest(grouped=wrap is grouped, choice=choice):
                    result = captions.copy_block_transition(destination, 6, donor, 6)
                    self.assertEqual(result, expected)
                    self.assertEqual(destination, before)
                    self.assertEqual(donor, source_before)
                    self.assertEqual(captions.copy_block_transition(result, 6, donor, 6), result)

    def test_native_none_clears_only_name_retaining_reverse_duration_and_reset_data(self):
        destination = fixture("SlideLeft", 1.0, 0.75)
        donor = fixture("", 0.0, 0.5)
        expected = copy.deepcopy(destination)
        selected(expected)["def"][NAME] = ""
        self.assertEqual(captions.copy_block_transition(destination, 6, donor, 6), expected)

    def test_copy_refuses_missing_structured_wrong_owner_build_and_ambiguous_ids(self):
        for side in ("target", "donor"):
            for bad in (None, 1, False, [], {"type": "string", "defaultValue": "Fade"}):
                target, donor = fixture(), fixture("SlideLeft")
                changed = target if side == "target" else donor
                if bad is None:
                    del selected(changed)["def"][NAME]
                else:
                    selected(changed)["def"][NAME] = bad
                before = copy.deepcopy((target, donor))
                with self.subTest(side=side, value=bad), self.assertRaises(ValueError):
                    captions.copy_block_transition(target, 6, donor, 6)
                self.assertEqual((target, donor), before)
            for mode in ("modifier", "type", "build", "duplicate", "missing"):
                target, donor = fixture(), fixture("SlideLeft")
                changed = target if side == "target" else donor
                if mode == "modifier":
                    selected(changed)["def"]["modifier"] = "ordinary"
                elif mode == "type":
                    selected(changed)["_type"] = "IMFile"
                elif mode == "build":
                    changed["authoringClientName"] = "Unknown"
                elif mode == "duplicate":
                    project.scene_tracks(changed)[0][1]["medias"].append(
                        copy.deepcopy(selected(changed))
                    )
                else:
                    selected(changed)["id"] = 99
                before = copy.deepcopy((target, donor))
                with self.subTest(side=side, mode=mode), self.assertRaises(ValueError):
                    captions.copy_block_transition(target, 6, donor, 6)
                self.assertEqual((target, donor), before)

    def test_reverse_and_duration_are_independent_atomic_static_patches(self):
        doc = grouped(fixture("SlideLeft"))
        expected = copy.deepcopy(doc)
        selected(expected)["def"].update({REVERSE: 1.0, DURATION: 0.75})
        self.assertEqual(
            captions.set_display(doc, 6, spec(definition={REVERSE: 1, DURATION: "3/4"})),
            expected,
        )
        for name, bad_values in (
            (REVERSE, (-1, 0.5, 2, True, None, "bad", float("nan"))),
            (DURATION, (-0.01, True, None, "bad", float("inf"))),
        ):
            for bad in bad_values:
                before = copy.deepcopy(doc)
                with self.subTest(name=name, bad=bad), self.assertRaises(ValueError):
                    captions.set_display(doc, 6, spec(definition={REVERSE: 1, name: bad}))
                self.assertEqual(doc, before)
        for name in (REVERSE, DURATION):
            expected = copy.deepcopy(doc)
            selected(expected)["def"][name] = 0.0
            self.assertEqual(captions.set_display(doc, 6, spec(definition={name: 0})), expected)
        with self.assertRaises(ValueError):
            captions.set_display(doc, 6, spec(definition={NAME: "SlideLeft"}))

    def test_reverse_retains_static_representation_and_refuses_missing_or_animation(self):
        doc = fixture("SlideLeft")
        selected(doc)["def"][REVERSE] = dict(
            type="double", defaultValue=0.0, keyframes=[], opaque=["keep"]
        )
        expected = copy.deepcopy(doc)
        selected(expected)["def"][REVERSE]["defaultValue"] = 1.0
        self.assertEqual(captions.set_display(doc, 6, spec(definition={REVERSE: 1})), expected)
        for value in (
            None,
            {"type": "double"},
            {"type": "double", "defaultValue": 0, "keyframes": [{"time": 0, "value": 0}]},
        ):
            doc = fixture()
            if value is None:
                del selected(doc)["def"][REVERSE]
            else:
                selected(doc)["def"][REVERSE] = value
            before = copy.deepcopy(doc)
            with self.subTest(value=value), self.assertRaises(ValueError):
                captions.set_display(doc, 6, spec(definition={REVERSE: 1}))
            self.assertEqual(doc, before)

    def test_cli_copy_stages_exclusively_without_changing_either_input(self):
        with tempfile.TemporaryDirectory() as tmp:
            target, donor, output = [
                Path(tmp) / n for n in ("target.json", "donor.json", "out.json")
            ]
            target.write_bytes(project.encode_document(fixture("Fade", 1.0, 0.75)))
            donor.write_bytes(project.encode_document(fixture("SlideLeft")))
            original, source = target.read_bytes(), donor.read_bytes()
            args = [
                "copy-block-transition",
                str(target),
                "--clip-id",
                "6",
                "--template-project",
                str(donor),
                "--template-clip-id",
                "6",
                "--output",
                str(output),
            ]
            for _ in range(2):
                stdout, stderr = io.StringIO(), io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    self.assertEqual(captions.main(args), 0, stderr.getvalue())
                report = json.loads(stdout.getvalue())
                self.assertEqual(report["templateSha256"], project.digest(source))
                self.assertFalse(report["nativeVerified"])
                expected = fixture("SlideLeft", 1.0, 0.75)
                self.assertEqual(project.load(output)[0], expected)
                self.assertEqual((target.read_bytes(), donor.read_bytes()), (original, source))
            output.write_text("occupied")
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(captions.main(args), 1)
            self.assertEqual(output.read_text(), "occupied")
            output.unlink()
            invalid = fixture()
            del selected(invalid)["def"][NAME]
            donor.write_bytes(project.encode_document(invalid))
            with redirect_stdout(io.StringIO()), redirect_stderr(io.StringIO()):
                self.assertEqual(captions.main(args), 1)
            self.assertFalse(output.exists())
            self.assertEqual(target.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
