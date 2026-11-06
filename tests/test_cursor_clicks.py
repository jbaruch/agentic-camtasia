from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_animations import visual
from test_cursor_paths import fixture as path_fixture, frame
from test_motion_paths import wrapper
from test_recorded_cursor_paths import fixture as recording_fixture
import cursor_clicks
import project

RATE = 705600000


def generated(*, retimed=True, linked=True):
    doc = path_fixture(retimed=retimed, linked=linked)
    for node in owners(doc):
        node["effects"][0]["parameters"]["cursorAction"]["keyframes"] = [frame(0, 0)]
    return doc


def recorded():
    doc = recording_fixture()
    visual(doc)["parameters"].pop("cursorAction")
    visual(doc)["start"] = 3 * RATE
    return doc


def owners(doc):
    first = project.scene_tracks(doc)[0][0]["medias"][0]
    return [first, first["video"]] if first["_type"] == "UnifiedMedia" else [first]


def action(doc):
    return visual(doc)["effects"][0]["parameters"]["cursorAction"]


def expected_generated(doc, frames):
    result = copy.deepcopy(doc)
    for node in owners(result):
        node["effects"][0]["parameters"]["cursorAction"]["keyframes"] = copy.deepcopy(frames)
    return result


def expected_recorded(doc, edits):
    result = copy.deepcopy(doc)
    if edits:
        visual(result)["parameters"]["cursorAction"] = dict(edits=copy.deepcopy(edits))
    else:
        visual(result)["parameters"].pop("cursorAction", None)
    return result


def spec(*clicks):
    return dict(schema_version=1, clicks=[dict(time=t, button=b) for t, b in clicks])


class CursorClickTests(unittest.TestCase):
    def test_top_level_and_every_subcommand_help_emit_versioned_json(self):
        for command in [[], ["inspect"], ["set-path-clicks"], ["set-recorded-clicks"]]:
            with (
                self.subTest(command=command),
                patch("sys.stdout", new_callable=io.StringIO) as stream,
                self.assertRaises(SystemExit) as error,
            ):
                cursor_clicks.main([*command, "--help"])
            self.assertEqual(error.exception.code, 0)
            report = json.loads(stream.getvalue())
            self.assertEqual(report["schema_version"], 1)
            self.assertEqual(report["owner"], "camtasia-cursor-clicks")
            self.assertTrue(report["ok"])
            self.assertIn("usage:", report["help"])
            self.assertIn("--help", report["help"])
            if command:
                self.assertIn(command[0], report["help"])
            else:
                self.assertIn("set-recorded-clicks", report["help"])

    def test_recorded_path_override_and_original_source_fields_survive_click_authoring(self):
        doc = recorded()
        visual(doc)["parameters"]["cursorLocation"] = dict(
            ignoreSource=True,
            edits=[dict(time=2116800000, value=[793.016, 685.949, 0])],
        )
        before = copy.deepcopy(doc)
        result = cursor_clicks.set_recorded_clicks(doc, 3, spec((1, "right")))
        self.assertEqual(result, expected_recorded(doc, [dict(time=2116800000, value=4)]))
        self.assertEqual(doc, before)

    def test_native_trimmed_linked_create_replace_remove_clear_and_start_replays(self):
        doc = generated()
        cases = [
            (spec((1, "left")), [frame(0, 0), frame(2116800000, 1)]),
            (
                spec((1, "left"), (2, "right")),
                [frame(0, 0), frame(2116800000, 1), frame(3528000000, 4)],
            ),
            (
                spec((1, "left"), (2, "left")),
                [frame(0, 0), frame(2116800000, 1), frame(3528000000, 1)],
            ),
            (spec((1, "left")), [frame(0, 0), frame(2116800000, 1)]),
            (spec(), [frame(0, 0)]),
            (spec((0, "left")), [frame(0, 0), frame(705600000, 1)]),
        ]
        for request, frames in cases:
            before = copy.deepcopy(doc)
            result = cursor_clicks.set_path_clicks(doc, 10, request)
            self.assertEqual(result, expected_generated(doc, frames))
            self.assertEqual(doc, before)
            doc = result

    def test_native_recorded_create_replace_remove_clear_and_start_replays(self):
        doc = recorded()
        cases = [
            (spec((1, "left")), [dict(time=2116800000, value=1)]),
            (
                spec((1, "left"), (2, "right")),
                [dict(time=2116800000, value=1), dict(time=3528000000, value=4)],
            ),
            (
                spec((1, "left"), (2, "left")),
                [dict(time=2116800000, value=1), dict(time=3528000000, value=1)],
            ),
            (spec((1, "left")), [dict(time=2116800000, value=1)]),
            (spec(), []),
            (spec((0, "left")), [dict(time=705600000, value=1)]),
        ]
        for request, edits in cases:
            before = copy.deepcopy(doc)
            result = cursor_clicks.set_recorded_clicks(doc, 3, request)
            self.assertEqual(result, expected_recorded(doc, edits))
            self.assertEqual(doc, before)
            doc = result

    def test_standalone_video_and_both_linked_selectors_agree(self):
        doc = generated()
        self.assertEqual(
            cursor_clicks.set_path_clicks(doc, 3, spec((1, "right"))),
            cursor_clicks.set_path_clicks(doc, 10, spec((1, "right"))),
        )
        single = generated(linked=False)
        self.assertEqual(
            cursor_clicks.set_path_clicks(single, 3, spec((1, "right"))),
            expected_generated(single, [frame(0, 0), frame(2116800000, 4)]),
        )

    def test_source_zero_click_replaces_anchor_and_clear_restores_native_zero(self):
        doc = generated(retimed=False)
        result = cursor_clicks.set_path_clicks(doc, 3, spec((0, "left"), (1, "right")))
        self.assertEqual(result, expected_generated(doc, [frame(0, 1), frame(RATE, 4)]))
        self.assertEqual(cursor_clicks.set_path_clicks(result, 10, spec()), doc)
        self.assertEqual(
            cursor_clicks.set_path_clicks(result, 3, spec((0, "right"))),
            expected_generated(doc, [frame(0, 4)]),
        )

    def test_exact_fractional_and_out_of_trim_source_times_do_not_add_owner_start(self):
        for doc, command, clip in [
            (generated(), cursor_clicks.set_path_clicks, 3),
            (recorded(), cursor_clicks.set_recorded_clicks, 3),
        ]:
            for owner in owners(doc):
                owner["start"] = 30 * RATE
            if len(owners(doc)) == 2:
                wrapper(doc)["audio"]["start"] = 30 * RATE
            result = command(doc, clip, spec(("-1/2", "left"), ("1/120", "right"), (4, "left")))
            expected = [
                dict(time=0, value=1),
                dict(time=717360000, value=4),
                dict(time=6350400000, value=1),
            ]
            if command is cursor_clicks.set_path_clicks:
                for event in expected:
                    event.update(endTime=event["time"], duration=0)
                self.assertEqual(action(result)["keyframes"], expected)
            else:
                self.assertEqual(visual(result)["parameters"]["cursorAction"]["edits"], expected)
            self.assertEqual(visual(result)["start"], 30 * RATE)

    def test_generated_same_time_opaque_fields_and_descriptor_survive_retiming(self):
        doc = generated()
        for owner in owners(doc):
            curve = owner["effects"][0]["parameters"]["cursorAction"]
            curve["nativeHint"] = {"opaque": [7]}
            curve["keyframes"] = [
                dict(frame(0, 0), anchorHint="keep"),
                dict(frame(2116800000, 1), eventHint="keep"),
            ]
        result = cursor_clicks.set_path_clicks(doc, 3, spec((1, "right"), (2, "left")))
        self.assertEqual(action(result)["nativeHint"], {"opaque": [7]})
        self.assertEqual(action(result)["keyframes"][0]["anchorHint"], "keep")
        self.assertEqual(action(result)["keyframes"][1]["eventHint"], "keep")
        self.assertNotIn("eventHint", action(result)["keyframes"][2])
        retimed = cursor_clicks.set_path_clicks(doc, 3, spec(("3/2", "right")))
        self.assertNotIn("eventHint", action(retimed)["keyframes"][1])

    def test_recorded_deletions_and_opaque_fields_survive_replacement_and_clear(self):
        doc = recorded()
        visual(doc)["parameters"]["cursorAction"] = {
            "edits": [dict(time=2116800000, value=1, eventHint={"keep": True})],
            "deletions": [0, 7],
            "nativeHint": ["keep"],
        }
        before = copy.deepcopy(doc)
        result = cursor_clicks.set_recorded_clicks(doc, 3, spec((1, "right"), (2, "left")))
        override = visual(result)["parameters"]["cursorAction"]
        self.assertEqual(override["deletions"], [0, 7])
        self.assertEqual(override["nativeHint"], ["keep"])
        self.assertEqual(override["edits"][0]["eventHint"], {"keep": True})
        self.assertNotIn("eventHint", override["edits"][1])
        cleared = cursor_clicks.set_recorded_clicks(result, 3, spec())
        self.assertEqual(
            visual(cleared)["parameters"]["cursorAction"],
            dict(edits=[], deletions=[0, 7], nativeHint=["keep"]),
        )
        self.assertEqual(doc, before)

    def test_repeated_lists_and_absent_recorded_clear_are_identical(self):
        for doc, command in [
            (generated(), cursor_clicks.set_path_clicks),
            (recorded(), cursor_clicks.set_recorded_clicks),
        ]:
            first = command(doc, 3, spec((1, "left"), (2, "right")))
            self.assertEqual(command(first, 3, spec((1, "left"), (2, "right"))), first)
            self.assertEqual(command(doc, 3, spec()), doc)

    def test_invalid_specs_buttons_order_and_inexact_ticks_refuse_without_mutation(self):
        invalid = [
            None,
            {},
            dict(schema_version=True, clicks=[]),
            dict(schema_version=2, clicks=[]),
            dict(schema_version=1, clicks=None),
            dict(spec(), extra=True),
            spec((1, "middle")),
            spec((1, 1)),
            spec((True, "left")),
            spec(("1/1000000001", "left")),
            spec((-1, "left")),
            spec((2, "left"), (1, "right")),
            spec((1, "left"), (1, "right")),
            dict(schema_version=1, clicks=[{}]),
            dict(schema_version=1, clicks=[dict(time=1, button="left", value=1)]),
        ]
        for request in invalid:
            for doc, command in [
                (generated(), cursor_clicks.set_path_clicks),
                (recorded(), cursor_clicks.set_recorded_clicks),
            ]:
                before = copy.deepcopy(doc)
                with (
                    self.subTest(request=request, command=command.__name__),
                    self.assertRaises(ValueError),
                ):
                    command(doc, 3, request)
                self.assertEqual(doc, before)

    def test_unknown_generated_descriptors_and_frame_shapes_refuse(self):
        mutations = [
            lambda c: c.update(type="double"),
            lambda c: c.update(keyframes=[]),
            lambda c: c.update(interp="linr"),
            lambda c: c.update(ignoreSource=True),
            lambda c: c.update(defaultValue=0),
            lambda c: c.update(edits=[]),
            lambda c: c.update(deletions=[]),
            lambda c: c["keyframes"][0].update(time=1, endTime=1),
            lambda c: c["keyframes"][0].update(time=-1, endTime=-1),
            lambda c: c["keyframes"][0].update(time=True),
            lambda c: c["keyframes"][0].update(duration=1),
            lambda c: c["keyframes"][0].update(endTime=1),
            lambda c: c["keyframes"][0].update(value=True),
            lambda c: c["keyframes"][0].update(value=2),
            lambda c: c["keyframes"][0].update(interp="linr"),
            lambda c: c["keyframes"].append(frame(RATE, 0)),
            lambda c: c["keyframes"].append(frame(0, 1)),
            lambda c: c["keyframes"].__setitem__(0, None),
        ]
        for mutate in mutations:
            doc = generated(linked=False)
            mutate(action(doc))
            before = copy.deepcopy(doc)
            with self.assertRaises(ValueError):
                cursor_clicks.set_path_clicks(doc, 3, spec())
            self.assertEqual(doc, before)

    def test_unknown_recording_descriptors_indices_and_events_refuse(self):
        invalid = [
            None,
            {},
            dict(edits=None),
            dict(edits=[], type="int"),
            dict(edits=[], ignoreSource=True),
            dict(edits=[], keyframes=[]),
            dict(edits=[], interp="linr"),
            dict(edits=[], defaultValue=0),
        ]
        invalid += [dict(edits=[], deletions=v) for v in [None, [True], [-1], [1, 1], [1.0], ["0"]]]
        invalid += [
            dict(edits=v)
            for v in [
                [None],
                [dict(time=True, value=1)],
                [dict(time=-1, value=1)],
                [dict(time=0, value=0)],
                [dict(time=0, value=True)],
                [dict(time=0, value=2)],
                [dict(time=0, value=1, interp="linr")],
                [dict(time=0, value=1, duration=0)],
                [dict(time=0, value=1, endTime=0)],
                [dict(value=1)],
                [dict(time=1, value=1), dict(time=0, value=4)],
                [dict(time=1, value=1), dict(time=1, value=4)],
            ]
        ]
        for override in invalid:
            doc = recorded()
            visual(doc)["parameters"]["cursorAction"] = override
            before = copy.deepcopy(doc)
            with self.subTest(override=override), self.assertRaises(ValueError):
                cursor_clicks.set_recorded_clicks(doc, 3, spec())
            self.assertEqual(doc, before)

    def test_generated_mirrors_and_tokens_must_agree(self):
        for change in ["controls", "clock", "token", "missing", "duplicate"]:
            doc = generated()
            if change == "controls":
                action(doc)["keyframes"].append(frame(RATE, 1))
            elif change == "clock":
                visual(doc)["mediaStart"] = 0
            elif change == "token":
                visual(doc)["effects"][0]["metadata"]["effectIndex"] = "8"
            elif change == "missing":
                visual(doc)["effects"].pop(0)
            else:
                visual(doc)["effects"].insert(0, copy.deepcopy(visual(doc)["effects"][0]))
            with self.assertRaises(ValueError):
                cursor_clicks.set_path_clicks(doc, 10, spec((1, "left")))

    def test_wrong_owners_builds_and_nested_clocks_refuse(self):
        for doc, command in [
            (generated(), cursor_clicks.set_path_clicks),
            (recorded(), cursor_clicks.set_recorded_clicks),
        ]:
            for mutation in ["version", "client", "owner", "rate", "scalar", "nested"]:
                changed = copy.deepcopy(doc)
                if mutation == "version":
                    changed["version"] = "9.0"
                elif mutation == "client":
                    changed["authoringClientName"]["version"] = "unknown"
                elif mutation == "owner":
                    visual(changed)["_type"] = "ScreenIMFile"
                elif mutation == "rate":
                    changed["editRate"] = 0
                elif mutation == "scalar":
                    visual(changed)["scalar"] = 0
                else:
                    tracks = project.scene_tracks(changed)[0]
                    old = tracks[0]["medias"]
                    tracks[0]["medias"] = [
                        dict(id=40, _type="Group", tracks=[dict(trackIndex=0, medias=old)])
                    ]
                with (
                    self.subTest(command=command.__name__, mutation=mutation),
                    self.assertRaises(ValueError),
                ):
                    command(changed, 3, spec((1, "left")))

    def test_recorded_linked_and_created_effect_combination_refuse(self):
        doc = recorded()
        visual(doc)["effects"].append(dict(effectName="CursorPath"))
        with self.assertRaises(ValueError):
            cursor_clicks.set_recorded_clicks(doc, 3, spec())
        doc = recorded()
        node = visual(doc)
        project.scene_tracks(doc)[0][0]["medias"] = [
            dict(id=10, _type="UnifiedMedia", video=node, audio=dict(id=20, _type="AMFile"))
        ]
        for clip in [3, 10]:
            with self.assertRaises(ValueError):
                cursor_clicks.set_recorded_clicks(doc, clip, spec())

    def test_inventory_is_raw_inspection_and_returns_independent_payloads(self):
        doc = generated()
        doc["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"].append(
            dict(trackIndex=1, medias=[copy.deepcopy(visual(recorded()))])
        )
        before = copy.deepcopy(doc)
        rows = cursor_clicks.inventories(doc)
        self.assertEqual(len(rows["paths"]), 2)
        self.assertEqual(len(rows["recordings"]), 1)
        self.assertIsNone(rows["recordings"][0]["cursorAction"])
        rows["paths"][0]["cursorAction"]["keyframes"].clear()
        self.assertEqual(doc, before)
        visual(doc)["effects"][0]["parameters"] = None
        with self.assertRaises(ValueError):
            cursor_clicks.inventories(doc)
        doc = recorded()
        visual(doc)["parameters"] = None
        with self.assertRaises(ValueError):
            cursor_clicks.inventories(doc)

    def test_cli_stage_repeat_inspect_and_clear_preserve_input_and_refuse_conflicting_output(self):
        for initial, command in [
            (generated(), "set-path-clicks"),
            (recorded(), "set-recorded-clicks"),
        ]:
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = root / "source.json"
                request = root / "spec.json"
                output = root / "candidate.json"
                cleared = root / "cleared.json"
                source.write_bytes(project.encode_document(initial))
                baseline = source.read_bytes()
                request.write_text(json.dumps(spec((1, "left"), (2, "right"))))
                args = [
                    command,
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
                        self.assertEqual(cursor_clicks.main(args), 0)
                    report = json.loads(stream.getvalue())
                    self.assertEqual(report["schema_version"], 1)
                    self.assertEqual(report["owner"], "camtasia-cursor-clicks")
                    self.assertEqual(report["written"], written)
                    self.assertFalse(report["nativeVerified"])
                    self.assertTrue(report["changed"])
                with patch("sys.stdout", new_callable=io.StringIO) as stream:
                    self.assertEqual(cursor_clicks.main(["inspect", str(output)]), 0)
                self.assertTrue(json.loads(stream.getvalue())["ok"])
                request.write_text(json.dumps(spec()))
                with patch("sys.stderr", new_callable=io.StringIO) as stream:
                    self.assertEqual(cursor_clicks.main(args), 1)
                self.assertIn("candidate", json.loads(stream.getvalue())["error"])
                args[1] = str(output)
                args[-1] = str(cleared)
                with patch("sys.stdout", new_callable=io.StringIO):
                    self.assertEqual(cursor_clicks.main(args), 0)
                self.assertEqual(project.load(cleared)[0], initial)
                self.assertEqual(source.read_bytes(), baseline)

    def test_cli_bad_json_and_syntax_are_structured_refusals(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "bad.json"
            source.write_text("{")
            with patch("sys.stderr", new_callable=io.StringIO) as stream:
                self.assertEqual(cursor_clicks.main(["inspect", str(source)]), 1)
            self.assertFalse(json.loads(stream.getvalue())["ok"])
        with (
            patch("sys.stderr", new_callable=io.StringIO) as stream,
            self.assertRaises(SystemExit) as error,
        ):
            cursor_clicks.main(["set-recorded-clicks"])
        self.assertEqual(error.exception.code, 2)
        self.assertFalse(json.loads(stream.getvalue())["ok"])


if __name__ == "__main__":
    unittest.main()
