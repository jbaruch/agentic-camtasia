from __future__ import annotations

from contextlib import redirect_stdout
import copy
import io
import json
from pathlib import Path
import tempfile
import unittest

from test_effect_grouped_recordings import grouped, node
from test_matte_stitched_linked_recordings import fixture as stitched
from test_motion_path_linked_recordings import fixture, native_effect
from test_motion_paths import spec
import motion_paths
import project


def document(depth=1):
    doc = grouped(fixture(), depth)
    for _, group in project.objects(doc):
        if isinstance(group, dict) and group.get("_type") == "Group":
            group["attributes"].update(widthAttr=640.0, heightAttr=360.0)
    return doc


class GroupedRecordingMotionPathTests(unittest.TestCase):
    def test_native_constructor_matches_both_aliases_through_single_and_nested_groups(self):
        for depth in (1, 2):
            doc = document(depth)
            before = copy.deepcopy(doc)
            expected = copy.deepcopy(doc)
            for ident in (10, 3):
                node(expected, ident)["effects"] = [native_effect()]
            node(expected, 10)["metadata"]["effectApplied"] = "MediaPath"
            for clip_id in (10, 3):
                actual = motion_paths.set_path(doc, clip_id, spec())
                self.assertEqual(actual, expected)
                self.assertEqual(motion_paths.set_path(actual, clip_id, spec()), actual)
            self.assertEqual(doc, before)

    def test_native_lifecycle_preserves_all_ancestors_and_recorded_audio(self):
        for depth in (1, 2):
            plain = motion_paths.set_path(document(depth), 10, spec())
            expected = copy.deepcopy(plain)
            for ident in (10, 3):
                node(expected, ident)["effects"][0]["parameters"]["mediaPathAutoOrient"] = 1
            node(expected, 10)["metadata"]["default-MediaPath-mediaPathAutoOrient"] = "0"
            node(expected, 3)["parameters"]["rotation2"] = dict(
                type="double", defaultValue=0.0, interp="eioe"
            )
            oriented = motion_paths.set_path(plain, 3, {**spec(), "autoOrient": True})
            self.assertEqual(oriented, expected)
            for ident in (10, 3):
                node(expected, ident)["effects"][0]["bypassed"] = True
            node(expected, 3)["parameters"].pop("rotation2")
            bypassed = motion_paths.set_bypass(oriented, 10, True)
            self.assertEqual(bypassed, expected)
            off = motion_paths.set_path(bypassed, 3, {**spec(), "autoOrient": False})
            for ident in (10, 3):
                node(expected, ident)["effects"][0]["parameters"]["mediaPathAutoOrient"] = 0
            self.assertEqual(off, expected)
            self.assertEqual(
                motion_paths.set_path(off, 10, {**spec(), "autoOrient": True}), bypassed
            )
            self.assertEqual(motion_paths.set_bypass(bypassed, 3, False), oriented)
            removed = motion_paths.remove_path(oriented, 10)
            expected = copy.deepcopy(oriented)
            for ident in (10, 3):
                node(expected, ident)["effects"] = []
            node(expected, 3)["parameters"].pop("rotation2")
            self.assertEqual(removed, expected)
            self.assertEqual(motion_paths.remove_path(removed, 3), removed)
            self.assertEqual(node(removed, 11), node(plain, 11))

    def test_point_replacement_uses_child_source_ticks_and_keeps_parent_clocks(self):
        doc = motion_paths.set_path(document(2), 10, spec())
        before = copy.deepcopy(doc)
        request = dict(
            schema_version=1,
            points=[
                dict(time="1/3", position=[-60, -30, 0]),
                dict(time="5/3", position=[60, 30, 0], interpolation="linr"),
            ],
        )
        expected = copy.deepcopy(doc)
        frames = [
            dict(time=1881600000, endTime=1881600000, duration=0, value=[-60, -30, 0]),
            dict(time=3763200000, endTime=3763200000, duration=0, value=[60, 30, 0], interp="linr"),
        ]
        for ident in (10, 3):
            node(expected, ident)["effects"][0]["parameters"]["mediaLocation"]["keyframes"] = (
                copy.deepcopy(frames)
            )
        self.assertEqual(motion_paths.set_path(doc, 3, request), expected)
        self.assertEqual(doc, before)

    def test_other_containers_and_conflicting_linked_payloads_refuse_without_mutation(self):
        invalid = [(stitched(), "root linked")]
        doc = document(2)
        node(doc, 10)["audio"]["src"] = 99
        invalid.append((doc, "shared source"))
        doc = motion_paths.set_path(document(2), 10, spec())
        node(doc, 3)["effects"][0]["parameters"]["mediaPathAutoOrient"] = 1
        invalid.append((doc, "conflicting"))
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

    def test_cli_stages_nested_candidate_and_repeats_through_video_alias(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, request, output = (
                root / n for n in ("input.json", "spec.json", "candidate.json")
            )
            source.write_bytes(project.encode_document(document(2)))
            request.write_text(json.dumps(spec()))
            before = source.read_bytes()
            for clip_id, written in ((10, True), (3, False)):
                stdout = io.StringIO()
                with redirect_stdout(stdout):
                    self.assertEqual(
                        motion_paths.main(
                            [
                                "set-path",
                                str(source),
                                "--clip-id",
                                str(clip_id),
                                "--spec",
                                str(request),
                                "--output",
                                str(output),
                            ]
                        ),
                        0,
                    )
                report = json.loads(stdout.getvalue())
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
            self.assertEqual(
                project.load(output)[0], motion_paths.set_path(document(2), 10, spec())
            )
            self.assertEqual(source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
