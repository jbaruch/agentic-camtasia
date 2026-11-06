from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_motion_paths import linked_document, wrapper
from test_animations import visual
import cursor_paths
import project

RATE = 705600000


def frame(time, position, interpolation=None):
    result = dict(time=time, endTime=time, duration=0, value=position)
    if interpolation is not None:
        result["interp"] = interpolation
    return result


def fixture(*, retimed=False, linked=True):
    doc = linked_document()
    doc["editRate"] = RATE
    video = visual(doc)
    outer = wrapper(doc)
    for node in [outer, video, outer["audio"]]:
        node.update(
            start=0,
            duration=(3 if retimed else 8) * RATE,
            mediaStart=RATE if retimed else 0,
            mediaDuration=(6 if retimed else 8) * RATE,
            scalar="1/2" if retimed else 1,
        )
    effect = dict(
        effectName="CursorPath",
        category="categoryVisualEffects",
        bypassed=False,
        metadata=dict(effectIndex="7", opaque="preserve"),
        parameters=dict(
            cursorLocation=dict(
                type="point",
                keyframes=[
                    frame(RATE, [128, 90, 0]),
                    frame(
                        2 * RATE, [512, 270, 0], dict(bezier=[[320, 90, 0], [320, 270, 0], "eioe"])
                    ),
                ],
            ),
            cursorAction=dict(
                type="int",
                uiHints={"userInterfaceType": 0, "unitType": 0},
                keyframes=[frame(0, 0), frame(RATE, 1)],
            ),
            cursorImagePath="Mac/pointer",
            smoothCursorAcrossEditDuration=235200000,
            cursorScale=dict(type="double", defaultValue=1.0, interp="linr"),
            cursorOpacity=dict(type="double", defaultValue=1.0, interp="linr"),
            cursorTrackLevel=dict(type="double", defaultValue=10000.0, interp="linr"),
        ),
    )
    for node in [outer, video]:
        node["effects"] = [
            copy.deepcopy(effect),
            {"effectName": "FutureEffect", "opaque": [1, 2, 3]},
        ]
    video["parameters"]["rotation2"] = 0.25
    video["animationTracks"] = {"visual": [{"startTime": RATE, "duration": RATE, "interp": "line"}]}
    if not linked:
        project.scene_tracks(doc)[0][0]["medias"] = [video, outer["audio"]]
    return doc


def spec(points):
    return dict(schema_version=1, points=points)


def point(time, position, interpolation=None):
    result = dict(time=time, position=position)
    if interpolation is not None:
        result["interpolation"] = interpolation
    return result


def curve(doc):
    return visual(doc)["effects"][0]["parameters"]["cursorLocation"]


def expected(doc, frames):
    result = copy.deepcopy(doc)
    visual(result)["effects"][0]["parameters"]["cursorLocation"]["keyframes"] = copy.deepcopy(
        frames
    )
    first = project.scene_tracks(result)[0][0]["medias"][0]
    if first["_type"] == "UnifiedMedia":
        first["effects"][0]["parameters"]["cursorLocation"]["keyframes"] = copy.deepcopy(frames)
    return result


def base_points():
    return [
        point(1, [128, 90, 0]),
        point(2, [512, 270, 0], dict(bezier=[[320, 90, 0], [320, 270, 0], "eioe"])),
    ]


class CursorPathTests(unittest.TestCase):
    def test_native_single_point_deletion_becomes_a_static_cursor_hold(self):
        doc = fixture()
        result = cursor_paths.set_path(doc, 10, spec([point(1, [128, 90, 0])]))
        self.assertEqual(result, expected(doc, [frame(RATE, [128, 90, 0])]))
        self.assertEqual(cursor_paths.set_path(result, 10, spec([point(1, [128, 90, 0])])), result)

    def test_fixed_native_movement_updates_both_mirrors_and_preserves_complete_document(self):
        doc = fixture()
        before = copy.deepcopy(doc)
        points = [
            point(1, [95.2476, 71.8534, 0]),
            point(2, [512, 270, 0], dict(bezier=[[287.248, 71.8534, 0], [320, 270, 0], "eioe"])),
        ]
        wanted = expected(
            doc,
            [
                frame(RATE, [95.2476, 71.8534, 0]),
                frame(
                    2 * RATE,
                    [512, 270, 0],
                    dict(bezier=[[287.248, 71.8534, 0], [320, 270, 0], "eioe"]),
                ),
            ],
        )
        self.assertEqual(cursor_paths.set_path(doc, 10, spec(points)), wanted)
        self.assertEqual(cursor_paths.set_path(doc, 3, spec(points)), wanted)
        self.assertEqual(doc, before)

    def test_native_angular_and_explicit_easing_shapes_do_not_change_geometry_intervals(self):
        doc = fixture()
        points = [point(1, [95.2476, 71.8534, 0], "linr"), point(2, [512, 270, 0], "esOt")]
        result = cursor_paths.set_path(doc, 3, spec(points))
        self.assertEqual(
            result,
            expected(
                doc,
                [
                    frame(RATE, [95.2476, 71.8534, 0], "linr"),
                    frame(2 * RATE, [512, 270, 0], "esOt"),
                ],
            ),
        )
        self.assertEqual(visual(result)["animationTracks"], visual(doc)["animationTracks"])
        self.assertEqual(visual(result)["parameters"], visual(doc)["parameters"])

    def test_fixed_native_retimed_shift_and_insert_use_source_clock(self):
        doc = fixture(retimed=True)
        points = [
            point(1, [128, 90, 0]),
            point(
                "6/5",
                [265.921, 133.5, 0],
                dict(bezier=[[204.8, 90, 0], [250.88, 118.8, 0], "esIn"]),
            ),
            point("3/2", [512, 270, 0], dict(bezier=[[350.72, 205.2, 0], [396.8, 270, 0], "esOt"])),
        ]
        wanted = expected(
            doc,
            [
                frame(2116800000, [128, 90, 0]),
                frame(
                    2399040000,
                    [265.921, 133.5, 0],
                    dict(bezier=[[204.8, 90, 0], [250.88, 118.8, 0], "esIn"]),
                ),
                frame(
                    2822400000,
                    [512, 270, 0],
                    dict(bezier=[[350.72, 205.2, 0], [396.8, 270, 0], "esOt"]),
                ),
            ],
        )
        self.assertEqual(cursor_paths.set_path(doc, 10, spec(points)), wanted)

    def test_explicit_point_deletion_keeps_only_requested_native_points_and_handles(self):
        doc = fixture(retimed=True)
        points = [
            point(1, [128, 90, 0]),
            point("3/2", [512, 270, 0], dict(bezier=[[204.8, 90, 0], [396.8, 270, 0], "esOt"])),
        ]
        wanted = expected(
            doc,
            [
                frame(2116800000, [128, 90, 0]),
                frame(
                    2822400000,
                    [512, 270, 0],
                    dict(bezier=[[204.8, 90, 0], [396.8, 270, 0], "esOt"]),
                ),
            ],
        )
        doc = cursor_paths.set_path(
            doc,
            10,
            spec(
                [
                    point(1, [128, 90, 0]),
                    point("6/5", [265.921, 133.5, 0]),
                    point("3/2", [512, 270, 0]),
                ]
            ),
        )
        self.assertEqual(cursor_paths.set_path(doc, 10, spec(points)), wanted)

    def test_fixed_native_separated_video_movement_leaves_audio_owner_intact(self):
        doc = fixture(retimed=True, linked=False)
        points = [
            point(1, [128, 90, 0]),
            point(
                "3/2",
                [447.38, 243.444, 0],
                dict(bezier=[[204.8, 90, 0], [332.18, 243.444, 0], "esOt"]),
            ),
        ]
        wanted = expected(
            doc,
            [
                frame(2116800000, [128, 90, 0]),
                frame(
                    2822400000,
                    [447.38, 243.444, 0],
                    dict(bezier=[[204.8, 90, 0], [332.18, 243.444, 0], "esOt"]),
                ),
            ],
        )
        result = cursor_paths.set_path(doc, 3, spec(points))
        self.assertEqual(result, wanted)
        self.assertEqual(
            project.scene_tracks(result)[0][0]["medias"][1],
            project.scene_tracks(doc)[0][0]["medias"][1],
        )

    def test_same_time_opaque_frame_and_descriptor_metadata_survive(self):
        doc = fixture()
        for node in [wrapper(doc), visual(doc)]:
            descriptor = node["effects"][0]["parameters"]["cursorLocation"]
            descriptor["nativeHint"] = {"opaque": 1}
            descriptor["keyframes"][0]["nativeTag"] = ["keep", 7]
        points = [point(1, [10, 20, 0]), point(2, [30, 40, 0], "linr")]
        result = cursor_paths.set_path(doc, 10, spec(points))
        self.assertEqual(curve(result)["nativeHint"], {"opaque": 1})
        self.assertEqual(curve(result)["keyframes"][0]["nativeTag"], ["keep", 7])
        self.assertNotIn("nativeTag", curve(result)["keyframes"][1])
        moved = cursor_paths.set_path(doc, 10, spec([point(0, [10, 20, 0])]))
        self.assertNotIn("nativeTag", curve(moved)["keyframes"][0])

    def test_noop_is_identical_and_missing_interpolation_stays_missing(self):
        doc = fixture()
        self.assertEqual(cursor_paths.set_path(doc, 10, spec(base_points())), doc)
        points = [point(1, [128, 90, 0]), point(2, [512, 270, 0])]
        result = cursor_paths.set_path(doc, 10, spec(points))
        self.assertNotIn("interp", curve(result)["keyframes"][1])
        self.assertEqual(cursor_paths.set_path(result, 10, spec(points)), result)

    def test_trimmed_hidden_points_and_exact_subframe_ticks_are_not_clipped(self):
        doc = fixture(retimed=True)
        result = cursor_paths.set_path(
            doc,
            10,
            spec(
                [
                    point("-1/2", [0, 0, 0]),
                    point("1/120", [10, 20, 0], "linr"),
                    point(4, [30, 40, 0]),
                ]
            ),
        )
        self.assertEqual(
            [f["time"] for f in curve(result)["keyframes"]], [0, 717360000, 6350400000]
        )
        self.assertEqual(wrapper(result)["duration"], 3 * RATE)

    def test_bad_input_versions_shapes_positions_interpolation_and_ticks_refuse_without_mutation(
        self,
    ):
        invalid = [
            None,
            {},
            dict(schema_version=True, points=base_points()),
            dict(schema_version=2, points=base_points()),
            dict(schema_version=1, points=base_points(), autoOrient=True),
        ]
        invalid += [
            spec(p)
            for p in [
                None,
                [],
                [{}],
                [point(1, [1, 2])],
                [point(1, [1, 2, 3])],
                [point(1, [True, 2, 0])],
                [point(1, [float("nan"), 2, 0])],
                [point(1, [1, 2, 0], "spring")],
                [point(1, [1, 2, 0], dict(bezier=[[1, 2, 1], [3, 4, 0]]))],
                [point(1, [1, 2, 0], dict(bezier=[[1, 2, 0]]))],
                [point("1/1000000001", [1, 2, 0])],
                [point(-1, [1, 2, 0])],
                [point(2, [1, 2, 0]), point(1, [3, 4, 0])],
                [point(1, [1, 2, 0]), point(1, [3, 4, 0])],
                [dict(point(1, [1, 2, 0]), unexpected=True)],
            ]
        ]
        for request in invalid:
            doc = fixture()
            before = copy.deepcopy(doc)
            with self.subTest(request=request), self.assertRaises(ValueError):
                cursor_paths.set_path(doc, 10, request)
            self.assertEqual(doc, before)

    def test_unknown_native_curves_and_point_shapes_refuse(self):
        mutations = [
            lambda c: c.update(interp="future"),
            lambda c: c.update(type="double"),
            lambda c: c.update(defaultValue=[0, 0, 0]),
            lambda c: c.update(ignoreSource=True),
            lambda c: c.update(keyframes=[]),
            lambda c: c["keyframes"][0].update(duration=1),
            lambda c: c["keyframes"][0].update(endTime=1),
            lambda c: c["keyframes"][0].update(time=-1, endTime=-1),
            lambda c: c["keyframes"][0].update(value=[1, 2, 1]),
            lambda c: c["keyframes"][0].update(interp="future"),
            lambda c: c["keyframes"].append(copy.deepcopy(c["keyframes"][0])),
        ]
        for mutate in mutations:
            doc = fixture(linked=False)
            mutate(curve(doc))
            before = copy.deepcopy(doc)
            with self.assertRaises(ValueError):
                cursor_paths.set_path(doc, 3, spec(base_points()))
            self.assertEqual(doc, before)

    def test_missing_duplicate_and_conflicting_mirrors_and_tokens_refuse(self):
        for change in ["missing", "duplicate", "token", "controls", "clock", "no-token"]:
            doc = fixture()
            if change == "missing":
                wrapper(doc)["effects"].pop(0)
            elif change == "duplicate":
                visual(doc)["effects"].append(copy.deepcopy(visual(doc)["effects"][0]))
            elif change == "token":
                wrapper(doc)["effects"][0]["metadata"]["effectIndex"] = "8"
            elif change == "controls":
                wrapper(doc)["effects"][0]["parameters"]["cursorImagePath"] = "Mac/hand"
            elif change == "clock":
                wrapper(doc)["mediaStart"] = 1
            else:
                for node in [wrapper(doc), visual(doc)]:
                    node["effects"][0]["metadata"].pop("effectIndex")
            before = copy.deepcopy(doc)
            with self.assertRaises(ValueError):
                cursor_paths.set_path(doc, 10, spec(base_points()))
            self.assertEqual(doc, before)

    def test_unknown_owner_build_audio_and_duplicate_ids_refuse(self):
        cases = []
        for kind in ["ScreenVMFile", "ScreenIMFile", "StitchedMedia", "IMFile", "Callout", "Group"]:
            doc = fixture(linked=False)
            visual(doc)["_type"] = kind
            cases.append((doc, 3))
        doc = fixture()
        doc["version"] = "9.0"
        cases.append((doc, 10))
        doc = fixture()
        doc["authoringClientName"]["version"] = "future"
        cases.append((doc, 10))
        doc = fixture()
        cases.append((doc, 11))
        doc = fixture()
        wrapper(doc)["audio"]["id"] = 3
        cases.append((doc, 3))
        for doc, clip_id in cases:
            before = copy.deepcopy(doc)
            with self.assertRaises(ValueError):
                cursor_paths.set_path(doc, clip_id, spec(base_points()))
            self.assertEqual(doc, before)

    def test_nested_group_and_hidden_stitched_children_refuse(self):
        for kind in ["Group", "StitchedMedia"]:
            doc = fixture(linked=False)
            video = visual(doc)
            container = dict(
                id=20,
                _type=kind,
                parameters={},
                effects=[],
                tracks=[dict(trackIndex=0, medias=[video])],
            )
            project.scene_tracks(doc)[0][0]["medias"] = [container]
            with self.assertRaises(ValueError):
                cursor_paths.set_path(doc, 3, spec(base_points()))

    def test_nonpositive_rate_or_scalar_refuses(self):
        for field in ["editRate", "scalar"]:
            doc = fixture(linked=False)
            if field == "editRate":
                doc[field] = 0
            else:
                visual(doc)[field] = 0
            with self.assertRaises(ValueError):
                cursor_paths.set_path(doc, 3, spec(base_points()))

        doc = fixture(linked=False)
        visual(doc)["effects"][0]["bypassed"] = 1
        with self.assertRaisesRegex(ValueError, "boolean"):
            cursor_paths.set_path(doc, 3, spec(base_points()))

    def test_inspection_reports_physical_owners_without_mutating(self):
        doc = fixture()
        before = copy.deepcopy(doc)
        rows = cursor_paths.inventory(doc)
        self.assertEqual({row["clipId"] for row in rows}, {3, 10})
        self.assertEqual(doc, before)

    def test_cli_stages_exclusively_and_repeat_preserves_source_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            request = root / "spec.json"
            output = root / "candidate.json"
            source.write_bytes(project.encode_document(fixture()))
            raw = source.read_bytes()
            request.write_text(
                json.dumps(spec([point(1, [128, 90, 0]), point(2, [512, 270, 0], "linr")]))
            )
            command = [
                "set-path",
                str(source),
                "--clip-id",
                "10",
                "--spec",
                str(request),
                "--output",
                str(output),
            ]
            for written in [True, False]:
                with patch("sys.stdout", new_callable=io.StringIO) as stream:
                    self.assertEqual(cursor_paths.main(command), 0)
                report = json.loads(stream.getvalue())
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
            self.assertEqual(source.read_bytes(), raw)
            before = output.read_bytes()
            request.write_text(json.dumps(spec([point(1, [1, 2, 3])])))
            with patch("sys.stderr", new_callable=io.StringIO) as stream:
                self.assertEqual(cursor_paths.main(command), 1)
            self.assertFalse(json.loads(stream.getvalue())["ok"])
            self.assertEqual(output.read_bytes(), before)
            self.assertEqual(source.read_bytes(), raw)

    def test_cli_inspection_and_syntax_errors_use_json_contract(self):
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "source.json"
            source.write_bytes(project.encode_document(fixture()))
            with patch("sys.stdout", new_callable=io.StringIO) as stream:
                self.assertEqual(cursor_paths.main(["inspect", str(source)]), 0)
            report = json.loads(stream.getvalue())
            self.assertEqual(report["owner"], "camtasia-cursor-paths")
            self.assertEqual(len(report["paths"]), 2)
        with (
            patch("sys.stderr", new_callable=io.StringIO) as stream,
            self.assertRaises(SystemExit) as error,
        ):
            cursor_paths.main(["set-path"])
        self.assertEqual(error.exception.code, 2)
        self.assertFalse(json.loads(stream.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()
