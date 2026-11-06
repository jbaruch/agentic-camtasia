from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_annotations import fixture, clip
import annotations
import project


def document():
    doc = fixture()
    doc["editRate"] = 1000
    owner = clip(doc)
    owner.update(start=9000, duration=4000, mediaStart=2000, mediaDuration=8000, scalar="1/2")
    owner["def"]["text"] = "A café"
    for run in owner["def"]["textAttributes"]["keyframes"][0]["value"]:
        run["rangeEnd"] = 7
    return doc


def setting():
    return dict(
        schema_version=1,
        initial=dict(rich=dict(fontSize=32)),
        steps=[
            dict(at=1, rich=dict(fontSize=64, fgColor="(255,128,64,255)")),
            dict(at=2, rich_ranges=[dict(start=2, end=6, rich=dict(fontWeight=700))]),
        ],
    )


def attributes(doc):
    return clip(doc)["def"]["textAttributes"]


class RichStepTests(unittest.TestCase):
    def test_complete_states_use_source_ticks_and_preserve_every_other_owner_field(self):
        doc = document()
        before = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        first = attributes(expected)["keyframes"][0]
        for run in first["value"]:
            if run["name"] == "fontSize":
                run["value"] = 32.0
        second = copy.deepcopy(first["value"])
        for run in second:
            if run["name"] == "fontSize":
                run["value"] = 64.0
            if run["name"] == "fgColor":
                run["value"] = "(255,128,64,255)"
        third = []
        for run in second:
            if run["name"] == "fontWeight":
                a, b = copy.deepcopy(run), copy.deepcopy(run)
                a["rangeEnd"] = 2
                b.update(rangeStart=2, value=700)
                third.extend([a, b])
            else:
                third.append(copy.deepcopy(run))
        attributes(expected)["keyframes"] += [
            dict(time=4000, endTime=4000, duration=0, value=second),
            dict(time=6000, endTime=6000, duration=0, value=third),
        ]
        result = annotations.set_rich_steps(doc, 3, setting())
        self.assertEqual(result, expected)
        self.assertEqual(doc, before)
        self.assertEqual(annotations.set_rich_steps(result, 3, setting()), result)
        self.assertIsNot(
            attributes(result)["keyframes"][1]["value"], attributes(result)["keyframes"][2]["value"]
        )

    def test_clear_selects_whole_state_at_boundary_and_preserves_geometry_and_initial_opaque(self):
        doc = annotations.set_rich_steps(document(), 3, setting())
        for at, index in [(0, 0), ("999/1000", 0), (1, 1), ("3/2", 1), (2, 2), ("3999/1000", 2)]:
            with self.subTest(at=at):
                expected = copy.deepcopy(doc)
                first = attributes(expected)["keyframes"][0]
                first["value"] = copy.deepcopy(attributes(doc)["keyframes"][index]["value"])
                attributes(expected)["keyframes"] = [first]
                result = annotations.clear_rich_steps(doc, 3, at)
                self.assertEqual(result, expected)
                self.assertEqual(annotations.clear_rich_steps(result, 3, at), result)

    def test_step_changes_are_cumulative_with_independent_unicode_property_partitions(self):
        doc = document()
        doc = annotations.edit_annotation(
            doc,
            3,
            dict(
                schema_version=2,
                rich_ranges=[
                    dict(start=0, end=2, rich=dict(fgColor="(255,0,0,255)")),
                ],
            ),
        )
        result = annotations.set_rich_steps(
            doc,
            3,
            dict(
                schema_version=1,
                steps=[
                    dict(at="1/2", rich_ranges=[dict(start=3, end=5, rich=dict(fontSize=48))]),
                    dict(at=1, rich=dict(fontWeight=700)),
                ],
            ),
        )
        frames = attributes(result)["keyframes"]
        sizes = [
            (r["rangeStart"], r["rangeEnd"], r["value"])
            for r in frames[1]["value"]
            if r["name"] == "fontSize"
        ]
        self.assertEqual(sizes, [(0, 3, 64.0), (3, 5, 48.0), (5, 7, 64.0)])
        self.assertEqual(
            [r for r in frames[2]["value"] if r["name"] == "fontSize"],
            [r for r in frames[1]["value"] if r["name"] == "fontSize"],
        )
        self.assertEqual(
            [r for r in frames[2]["value"] if r["name"] == "fgColor"],
            [r for r in frames[0]["value"] if r["name"] == "fgColor"],
        )

    def test_static_edit_refuses_timed_text_until_explicit_clear(self):
        doc = annotations.set_rich_steps(document(), 3, setting())
        before = copy.deepcopy(doc)
        with self.assertRaises(ValueError):
            annotations.edit_annotation(doc, 3, dict(schema_version=2, rich=dict(fontSize=20)))
        self.assertEqual(doc, before)
        cleared = annotations.clear_rich_steps(doc, 3, 0)
        self.assertEqual(
            clip(
                annotations.edit_annotation(
                    cleared,
                    3,
                    dict(
                        schema_version=3,
                        text_edits=[dict(start=0, end=1, expected="A", text="B", style_from=0)],
                    ),
                )
            )["def"]["text"],
            "B café",
        )

    def test_fractional_native_ticks_positive_visible_times_and_order_are_required(self):
        for steps in (
            [dict(at=0, rich=dict(fontSize=40))],
            [dict(at=-1, rich=dict(fontSize=40))],
            [dict(at=4, rich=dict(fontSize=40))],
            [dict(at="1/3001", rich=dict(fontSize=40))],
            [dict(at=2, rich=dict(fontSize=40)), dict(at=1, rich=dict(fontSize=50))],
            [dict(at=1, rich=dict(fontSize=40)), dict(at=1, rich=dict(fontSize=50))],
            [dict(at=True, rich=dict(fontSize=40))],
        ):
            doc = document()
            before = copy.deepcopy(doc)
            with self.subTest(steps=steps), self.assertRaises(ValueError):
                annotations.set_rich_steps(doc, 3, dict(schema_version=1, steps=steps))
            self.assertEqual(doc, before)
        for at in (-1, 4, True, "1/3001"):
            with self.subTest(clear=at), self.assertRaises(ValueError):
                annotations.clear_rich_steps(document(), 3, at)

    def test_unknown_content_controls_and_bad_specs_refuse_atomically(self):
        for spec in (
            {},
            dict(schema_version=True, steps=[]),
            dict(schema_version=1, steps=[]),
            dict(schema_version=1, initial=None, steps=[dict(at=1, rich=dict(fontSize=40))]),
            dict(schema_version=1, steps=[dict(at=1, text="new")]),
            dict(schema_version=1, steps=[dict(at=1, rich=dict(fontSize=40), easing="linear")]),
            dict(schema_version=1, steps=[dict(at=1, rich=dict(missing=1))]),
            dict(
                schema_version=1,
                steps=[dict(at=1, rich=dict(fontSize=40)), dict(at=2, rich=dict(fgColor="red"))],
            ),
        ):
            doc = document()
            before = copy.deepcopy(doc)
            with self.subTest(spec=spec), self.assertRaises(ValueError):
                annotations.set_rich_steps(doc, 3, spec)
            self.assertEqual(doc, before)

    def test_all_existing_states_must_have_valid_complete_partitions_and_point_clocks(self):
        base = annotations.set_rich_steps(document(), 3, setting())
        for mutation in (
            "interval",
            "missing-zero",
            "unordered",
            "partial",
            "unknown-type",
            "wrong-kind",
            "empty",
        ):
            doc = copy.deepcopy(base)
            frames = attributes(doc)["keyframes"]
            if mutation == "interval":
                frames[1].update(time=3000, duration=1000)
            elif mutation == "missing-zero":
                frames.pop(0)
            elif mutation == "unordered":
                frames.reverse()
            elif mutation == "partial":
                frames[1]["value"][0]["rangeEnd"] = 5
            elif mutation == "unknown-type":
                attributes(doc)["type"] = "point"
            elif mutation == "wrong-kind":
                clip(doc)["def"]["kind"] = "TypeWinSVG"
            else:
                frames.clear()
            before = copy.deepcopy(doc)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                annotations.set_rich_steps(doc, 3, setting())
            with self.subTest(clear=mutation), self.assertRaises(ValueError):
                annotations.clear_rich_steps(doc, 3, 1)
            self.assertEqual(doc, before)

    def test_rate_speed_and_unverified_nested_clocks_refuse(self):
        for field, value in [("editRate", 0), ("scalar", 0), ("duration", 0), ("mediaStart", -1)]:
            doc = document()
            (doc if field == "editRate" else clip(doc))[field] = value
            with self.subTest(field=field), self.assertRaises(ValueError):
                annotations.set_rich_steps(doc, 3, setting())
        doc = document()
        owner = clip(doc)
        project.scene_tracks(doc)[0][0]["medias"] = [
            dict(_type="Group", id=10, tracks=[dict(medias=[owner])])
        ]
        with self.assertRaisesRegex(ValueError, "root annotation"):
            annotations.set_rich_steps(doc, 3, setting())

    def test_cli_stages_repeat_clear_and_refusal_without_writing_original_or_partial_output(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source = root / "source.json"
            spec = root / "spec.json"
            out = root / "out.json"
            clear = root / "clear.json"
            source.write_bytes(project.encode_document(document()))
            before = source.read_bytes()
            spec.write_text(json.dumps(setting()))
            args = [
                "set-rich-steps",
                str(source),
                "--clip-id",
                "3",
                "--spec",
                str(spec),
                "--output",
                str(out),
            ]
            for written in (True, False):
                with patch("sys.stdout", new_callable=io.StringIO) as stream:
                    self.assertEqual(annotations.main(args), 0)
                result = json.loads(stream.getvalue())
                self.assertEqual(result["written"], written)
                self.assertFalse(result["nativeVerified"])
            with patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(
                    annotations.main(
                        [
                            "clear-rich-steps",
                            str(out),
                            "--clip-id",
                            "3",
                            "--at",
                            "2",
                            "--output",
                            str(clear),
                        ]
                    ),
                    0,
                )
            self.assertEqual(
                project.load(clear)[0], annotations.clear_rich_steps(project.load(out)[0], 3, 2)
            )
            spec.write_text(
                json.dumps(
                    dict(
                        schema_version=1,
                        steps=[
                            dict(at=1, rich=dict(fontSize=40)),
                            dict(at=2, rich=dict(fontSize=-1)),
                        ],
                    )
                )
            )
            missing = root / "missing.json"
            with patch("sys.stderr", new_callable=io.StringIO):
                self.assertEqual(annotations.main(args[:-1] + [str(missing)]), 1)
            self.assertFalse(missing.exists())
            self.assertEqual(source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
