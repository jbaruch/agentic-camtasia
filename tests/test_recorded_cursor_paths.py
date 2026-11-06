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
from test_cursor_paths import point, spec
import cursor_paths
import project


def fixture():
    doc = owner_document("ScreenVMFile")
    clip = visual(doc)
    clip.update(start=0, duration=3 * RATE, mediaStart=RATE, mediaDuration=6 * RATE, scalar="1/2")
    clip["parameters"].pop("cursorLocation")
    clip["parameters"].update(
        cursorScale=dict(type="double", defaultValue=5.0, interp="linr"),
        cursorOpacity=1.0,
        smoothCursorAcrossEditDuration=235200000,
        cursorAction=dict(edits=[dict(time=2822400000, value=1)], deletions=[5]),
        rotation2=0.25,
    )
    clip["animationTracks"] = {"visual": [dict(endTime=3528000000, duration=RATE, interp="line")]}
    clip["effects"] = [
        dict(
            effectName="Sepia",
            category="categoryVisualEffects",
            bypassed=False,
            parameters=dict(intensity=0.5),
        )
    ]
    doc["sourceBin"][0]["opaqueSourceProcessing"] = ["retain recording metadata"]
    project.scene_tracks(doc)[0].append(
        dict(
            trackIndex=1,
            medias=[
                dict(
                    id=70,
                    _type="AMFile",
                    src=1,
                    trackNumber=1,
                    start=0,
                    duration=3 * RATE,
                    mediaStart=0,
                    mediaDuration=3 * RATE,
                    scalar=1,
                    parameters=dict(volume=0.7),
                    effects=[],
                )
            ],
        )
    )
    return doc


def edit(time, value, interp=None):
    result = dict(time=time, value=value)
    if interp is not None:
        result["interp"] = interp
    return result


def native_created():
    return [
        edit(2116800000, [604.8, 589.75, 0]),
        edit(
            3528000000,
            [2419.2, 1440.25, 0],
            dict(bezier=[[1512, 589.75, 0], [1512, 1440.25, 0], "eioe"]),
        ),
    ]


def native_moved():
    return [
        edit(2116800000, [793.016, 685.949, 0]),
        edit(
            3528000000,
            [2419.2, 1440.25, 0],
            dict(bezier=[[1700.22, 685.949, 0], [1512, 1440.25, 0], "eioe"]),
        ),
    ]


def points_for_created():
    return [
        point(1, [604.8, 589.75, 0]),
        point(
            2, [2419.2, 1440.25, 0], dict(bezier=[[1512, 589.75, 0], [1512, 1440.25, 0], "eioe"])
        ),
    ]


def expected(doc, edits):
    result = copy.deepcopy(doc)
    if edits is None:
        visual(result)["parameters"].pop("cursorLocation", None)
    else:
        visual(result)["parameters"]["cursorLocation"] = dict(
            ignoreSource=True, edits=copy.deepcopy(edits)
        )
    return result


class RecordedCursorPathTests(unittest.TestCase):
    def test_fixed_native_new_path_uses_recording_edits_and_exact_trimmed_double_speed_clock(self):
        doc = fixture()
        before = copy.deepcopy(doc)
        result = cursor_paths.set_recorded_path(doc, 3, spec(points_for_created()))
        self.assertEqual(result, expected(doc, native_created()))
        self.assertEqual(doc, before)
        self.assertEqual(visual(result)["effects"], visual(doc)["effects"])
        self.assertNotIn("type", visual(result)["parameters"]["cursorLocation"])
        self.assertTrue(
            all(
                "duration" not in p and "endTime" not in p
                for p in visual(result)["parameters"]["cursorLocation"]["edits"]
            )
        )

    def test_fixed_native_move_insert_delete_and_hold_replays_preserve_complete_documents(self):
        doc = expected(fixture(), native_created())
        cases = [
            (
                [
                    point(1, [793.016, 685.949, 0]),
                    point(
                        2,
                        [2419.2, 1440.25, 0],
                        dict(bezier=[[1700.22, 685.949, 0], [1512, 1440.25, 0], "eioe"]),
                    ),
                ],
                native_moved(),
            ),
            (
                [
                    point(1, [793.016, 685.949, 0]),
                    point(
                        "3/2",
                        [1606.11, 1063.1, 0],
                        dict(bezier=[[1246.62, 685.949, 0], [1426.36, 874.524, 0], "esIn"]),
                    ),
                    point(
                        2,
                        [2419.2, 1440.25, 0],
                        dict(bezier=[[1785.85, 1251.67, 0], [1965.6, 1440.25, 0], "esOt"]),
                    ),
                ],
                [
                    edit(2116800000, [793.016, 685.949, 0]),
                    edit(
                        2822400000,
                        [1606.11, 1063.1, 0],
                        dict(bezier=[[1246.62, 685.949, 0], [1426.36, 874.524, 0], "esIn"]),
                    ),
                    edit(
                        3528000000,
                        [2419.2, 1440.25, 0],
                        dict(bezier=[[1785.85, 1251.67, 0], [1965.6, 1440.25, 0], "esOt"]),
                    ),
                ],
            ),
            (
                [
                    point(1, [793.016, 685.949, 0]),
                    point(
                        2,
                        [2419.2, 1440.25, 0],
                        dict(bezier=[[1246.62, 685.949, 0], [1965.6, 1440.25, 0], "esOt"]),
                    ),
                ],
                [
                    edit(2116800000, [793.016, 685.949, 0]),
                    edit(
                        3528000000,
                        [2419.2, 1440.25, 0],
                        dict(bezier=[[1246.62, 685.949, 0], [1965.6, 1440.25, 0], "esOt"]),
                    ),
                ],
            ),
            ([point(1, [793.016, 685.949, 0])], [edit(2116800000, [793.016, 685.949, 0])]),
        ]
        for points, edits in cases:
            before = copy.deepcopy(doc)
            result = cursor_paths.set_recorded_path(doc, 3, spec(points))
            self.assertEqual(result, expected(doc, edits))
            self.assertEqual(doc, before)
            doc = result

    def test_native_restore_removes_only_the_override_and_repeated_restore_is_noop(self):
        original = fixture()
        doc = expected(original, native_moved())
        before = copy.deepcopy(doc)
        result = cursor_paths.restore_recorded_path(doc, 3)
        self.assertEqual(result, original)
        self.assertEqual(doc, before)
        self.assertEqual(cursor_paths.restore_recorded_path(result, 3), result)

    def test_same_time_edit_metadata_and_opaque_override_fields_survive(self):
        doc = expected(fixture(), native_created())
        override = visual(doc)["parameters"]["cursorLocation"]
        override["nativeHint"] = {"opaque": [1, 2]}
        override["edits"][0]["nativeTag"] = ["retain"]
        result = cursor_paths.set_recorded_path(
            doc, 3, spec([point(1, [100, 200, 0]), point(2, [300, 400, 0], "linr")])
        )
        updated = visual(result)["parameters"]["cursorLocation"]
        self.assertEqual(updated["nativeHint"], override["nativeHint"])
        self.assertEqual(updated["edits"][0]["nativeTag"], ["retain"])
        retimed = cursor_paths.set_recorded_path(doc, 3, spec([point(0, [100, 200, 0])]))
        self.assertNotIn("nativeTag", visual(retimed)["parameters"]["cursorLocation"]["edits"][0])
        self.assertEqual(
            visual(retimed)["parameters"]["cursorLocation"]["nativeHint"], override["nativeHint"]
        )

    def test_identical_complete_replacement_is_noop(self):
        doc = expected(fixture(), native_created())
        self.assertEqual(cursor_paths.set_recorded_path(doc, 3, spec(points_for_created())), doc)

    def test_owner_start_is_not_added_and_subframe_source_ticks_are_exact(self):
        doc = fixture()
        visual(doc)["start"] = 30 * RATE
        result = cursor_paths.set_recorded_path(
            doc, 3, spec([point("-1/2", [1, 2, 0]), point("1/120", [3, 4, 0]), point(4, [5, 6, 0])])
        )
        self.assertEqual(
            visual(result)["parameters"]["cursorLocation"]["edits"],
            [edit(0, [1, 2, 0]), edit(717360000, [3, 4, 0]), edit(6350400000, [5, 6, 0])],
        )
        self.assertEqual(visual(result)["start"], 30 * RATE)

    def test_partial_source_edits_deletions_typed_and_empty_overrides_refuse_set_and_restore(self):
        bad = [
            None,
            {},
            dict(edits=native_created()),
            dict(ignoreSource=False, edits=native_created()),
            dict(ignoreSource=1, edits=native_created()),
            dict(ignoreSource=True, edits=[]),
            dict(ignoreSource=True, edits="invalid"),
        ]
        for key in ["deletions", "keyframes", "type", "defaultValue", "interp"]:
            bad.append(dict(ignoreSource=True, edits=native_created(), **{key: []}))
        for override in bad:
            doc = fixture()
            visual(doc)["parameters"]["cursorLocation"] = override
            before = copy.deepcopy(doc)
            for command in [
                lambda: cursor_paths.set_recorded_path(doc, 3, spec(points_for_created())),
                lambda: cursor_paths.restore_recorded_path(doc, 3),
            ]:
                with self.subTest(override=override), self.assertRaises(ValueError):
                    command()
                self.assertEqual(doc, before)

    def test_malformed_existing_recording_edits_refuse_without_mutation(self):
        mutations = [
            lambda edits: edits.append(copy.deepcopy(edits[0])),
            lambda edits: edits[0].update(time=-1),
            lambda edits: edits[0].update(time=True),
            lambda edits: edits[0].update(value=[1, 2, 1]),
            lambda edits: edits[0].update(interp="future"),
            lambda edits: edits[0].update(duration=0),
            lambda edits: edits[0].pop("time"),
            lambda edits: edits.__setitem__(0, None),
        ]
        for mutate in mutations:
            doc = expected(fixture(), native_created())
            mutate(visual(doc)["parameters"]["cursorLocation"]["edits"])
            before = copy.deepcopy(doc)
            with self.assertRaises(ValueError):
                cursor_paths.set_recorded_path(doc, 3, spec(points_for_created()))
            self.assertEqual(doc, before)

    def test_input_spec_versions_order_coordinates_and_interpolation_refuse(self):
        invalid = [
            None,
            {},
            dict(schema_version=2, points=points_for_created()),
            dict(schema_version=True, points=points_for_created()),
            dict(schema_version=1, points=points_for_created(), ignoreSource=False),
        ]
        invalid.extend(
            spec(p)
            for p in [
                [],
                None,
                [{}],
                [point(1, [1, 2])],
                [point(1, [1, 2, 1])],
                [point(1, [float("inf"), 2, 0])],
                [point(1, [True, 2, 0])],
                [point(1, [1, 2, 0], "future")],
                [point(1, [1, 2, 0], dict(bezier=[[1, 2, 3], [4, 5, 0]]))],
                [point(-1, [1, 2, 0])],
                [point("1/1000000001", [1, 2, 0])],
                [point(2, [1, 2, 0]), point(1, [3, 4, 0])],
                [point(1, [1, 2, 0]), point(1, [3, 4, 0])],
            ]
        )
        for request in invalid:
            doc = fixture()
            before = copy.deepcopy(doc)
            with self.subTest(request=request), self.assertRaises(ValueError):
                cursor_paths.set_recorded_path(doc, 3, request)
            self.assertEqual(doc, before)

    def test_other_owner_builds_and_audio_refuse(self):
        for kind in [
            "VMFile",
            "ScreenIMFile",
            "StitchedMedia",
            "IMFile",
            "Callout",
            "Group",
            "AMFile",
        ]:
            doc = fixture()
            visual(doc)["_type"] = kind
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                cursor_paths.set_recorded_path(doc, 3, spec(points_for_created()))
        for mutation in ["version", "client", "audio", "duplicate"]:
            doc = fixture()
            if mutation == "version":
                doc["version"] = "9.0"
            elif mutation == "client":
                doc["authoringClientName"]["version"] = "future"
            elif mutation == "audio":
                visual(doc)["id"] = 70
            else:
                project.scene_tracks(doc)[0][1]["medias"][0]["id"] = 3
            with self.assertRaises(ValueError):
                cursor_paths.restore_recorded_path(doc, 3)

    def test_linked_grouped_and_stitched_descendants_refuse(self):
        for kind in ["UnifiedMedia", "Group", "StitchedMedia"]:
            doc = fixture()
            owner = visual(doc)
            container = dict(id=20, _type=kind, parameters={}, effects=[])
            if kind == "UnifiedMedia":
                container.update(video=owner, audio=dict(id=21, _type="AMFile", src=1))
            elif kind == "Group":
                container["tracks"] = [dict(trackIndex=0, medias=[owner])]
            else:
                container["medias"] = [owner]
            project.scene_tracks(doc)[0][0]["medias"] = [container]
            for target in [3, 20]:
                with self.assertRaises(ValueError):
                    cursor_paths.set_recorded_path(doc, target, spec(points_for_created()))

    def test_bad_parameters_clock_and_created_cursor_effect_refuse(self):
        for mutation in ["parameters", "scalar", "rate", "effect"]:
            doc = fixture()
            if mutation == "parameters":
                visual(doc)["parameters"] = None
            elif mutation == "scalar":
                visual(doc)["scalar"] = 0
            elif mutation == "rate":
                doc["editRate"] = 0
            else:
                visual(doc)["effects"].append(dict(effectName="CursorPath"))
            with self.assertRaises(ValueError):
                cursor_paths.set_recorded_path(doc, 3, spec(points_for_created()))

    def test_recording_inventory_reports_raw_override_without_owning_it(self):
        doc = expected(fixture(), native_created())
        before = copy.deepcopy(doc)
        rows = cursor_paths.recording_inventory(doc)
        self.assertEqual(
            rows,
            [
                dict(
                    clipId=3,
                    type="ScreenVMFile",
                    path="/timeline/sceneTrack/scenes/0/csml/tracks/0/medias/0",
                    override=dict(ignoreSource=True, edits=native_created()),
                )
            ],
        )
        rows[0]["override"]["edits"].clear()
        self.assertEqual(doc, before)
        self.assertIsNone(cursor_paths.recording_inventory(fixture())[0]["override"])

    def test_cli_version_two_retains_created_inventory_and_adds_recordings(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.json"
            source.write_bytes(project.encode_document(fixture()))
            with patch("sys.stdout", new_callable=io.StringIO) as stream:
                self.assertEqual(cursor_paths.main(["inspect", str(source)]), 0)
            report = json.loads(stream.getvalue())
            self.assertEqual(report["schema_version"], 2)
            self.assertEqual(report["owner"], "camtasia-cursor-paths")
            self.assertEqual(report["paths"], [])
            self.assertEqual(report["recordings"][0]["clipId"], 3)

    def test_cli_create_repeat_restore_and_bad_spec_preserve_source_and_output_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            request = root / "spec.json"
            output = root / "candidate.json"
            restored = root / "restored.json"
            source.write_bytes(project.encode_document(fixture()))
            original = source.read_bytes()
            request.write_text(json.dumps(spec(points_for_created())))
            command = [
                "set-recorded-path",
                str(source),
                "--clip-id",
                "3",
                "--spec",
                str(request),
                "--output",
                str(output),
            ]
            for written in [True, False]:
                with patch("sys.stdout", new_callable=io.StringIO) as stream:
                    self.assertEqual(cursor_paths.main(command), 0)
                report = json.loads(stream.getvalue())
                self.assertEqual(report["schema_version"], 2)
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
            self.assertEqual(project.load(output)[0], expected(fixture(), native_created()))
            with patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(
                    cursor_paths.main(
                        [
                            "restore-recorded-path",
                            str(output),
                            "--clip-id",
                            "3",
                            "--output",
                            str(restored),
                        ]
                    ),
                    0,
                )
            self.assertEqual(restored.read_bytes(), original)
            prior = output.read_bytes()
            request.write_text(json.dumps(spec([point(1, [1, 2, 3])])))
            with patch("sys.stderr", new_callable=io.StringIO) as stream:
                self.assertEqual(cursor_paths.main(command), 1)
            self.assertFalse(json.loads(stream.getvalue())["ok"])
            self.assertEqual(output.read_bytes(), prior)
            self.assertEqual(source.read_bytes(), original)

    def test_recorded_cli_syntax_errors_remain_json(self):
        for command in ["set-recorded-path", "restore-recorded-path"]:
            with (
                patch("sys.stderr", new_callable=io.StringIO) as stream,
                self.assertRaises(SystemExit) as error,
            ):
                cursor_paths.main([command])
            self.assertEqual(error.exception.code, 2)
            self.assertFalse(json.loads(stream.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()
