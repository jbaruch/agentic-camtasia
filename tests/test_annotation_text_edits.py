from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_annotations import fixture, clip
from test_annotation_rich_ranges import document, expected_native, canonical, values, ORANGE, CYAN
import annotations
import project


def mixed():
    return expected_native(document())


def spec(edits, **extra):
    return dict(schema_version=3, text_edits=edits, **extra)


def edit(start, end, expected, text, style_from=None):
    result = dict(start=start, end=end, expected=expected, text=text)
    if style_from is not None:
        result["style_from"] = style_from
    return result


def expected(doc, text, partitions):
    result = copy.deepcopy(doc)
    definition = clip(result)["def"]
    definition["text"] = text
    frame = definition["textAttributes"]["keyframes"][0]
    if not text:
        frame["value"] = None
        return result
    samples = {}
    for run in values(doc):
        samples.setdefault(run["name"], run)
    output = []
    for name, run in samples.items():
        for start, end, value in partitions.get(
            name, [(0, len(text.encode("utf-8")), run["value"])]
        ):
            item = copy.deepcopy(run)
            item.update(rangeStart=start, rangeEnd=end, value=value)
            output.append(item)
    frame["value"] = output
    return result


def style():
    return dict(
        fontName="Helvetica",
        fontSize=12,
        fontWeight=400,
        fontItalic=0,
        underline=0,
        strikethrough=0,
        fgColor="(255,255,255,255)",
    )


def empty_document():
    doc = mixed()
    clip(doc)["def"]["text"] = ""
    clip(doc)["def"]["textAttributes"]["keyframes"][0]["value"] = None
    return doc


class AnnotationTextEditTests(unittest.TestCase):
    def test_fixed_native_replace_insert_cross_boundary_delete_and_empty_replays(self):
        doc = mixed()
        cases = [
            (
                edit(6, 10, "café", "résumé", 6),
                "Alpha résumé — omega\nBeta 42",
                {
                    "fontWeight": [(0, 6, 400), (6, 14, 700), (14, 32, 400)],
                    "fontItalic": [(0, 19, 0), (19, 24, 2), (24, 32, 0)],
                    "fontSize": [(0, 25, 36.0), (25, 32, 28.0)],
                    "underline": [(0, 25, 1), (25, 32, 0)],
                    "fgColor": [(0, 5, ORANGE), (5, 32, CYAN)],
                },
            ),
            (
                edit(12, 12, "", " très", 11),
                "Alpha résumé très — omega\nBeta 42",
                {
                    "fontWeight": [(0, 6, 400), (6, 20, 700), (20, 38, 400)],
                    "fontItalic": [(0, 25, 0), (25, 30, 2), (30, 38, 0)],
                    "fontSize": [(0, 31, 36.0), (31, 38, 28.0)],
                    "underline": [(0, 31, 1), (31, 38, 0)],
                    "fgColor": [(0, 5, ORANGE), (5, 38, CYAN)],
                },
            ),
            (
                edit(0, 17, "Alpha résumé très", "Résumé", 0),
                "Résumé — omega\nBeta 42",
                {
                    "fontWeight": [(0, 26, 400)],
                    "fontItalic": [(0, 13, 0), (13, 18, 2), (18, 26, 0)],
                    "fontSize": [(0, 19, 36.0), (19, 26, 28.0)],
                    "underline": [(0, 19, 1), (19, 26, 0)],
                    "fgColor": [(0, 8, ORANGE), (8, 26, CYAN)],
                },
            ),
            (
                edit(6, 14, " — omega", ""),
                "Résumé\nBeta 42",
                {
                    "fontWeight": [(0, 16, 400)],
                    "fontItalic": [(0, 16, 0)],
                    "fontSize": [(0, 9, 36.0), (9, 16, 28.0)],
                    "underline": [(0, 9, 1), (9, 16, 0)],
                    "fgColor": [(0, 8, ORANGE), (8, 16, CYAN)],
                },
            ),
            (edit(0, 14, "Résumé\nBeta 42", ""), "", {}),
        ]
        for operation, text, partitions in cases:
            before = copy.deepcopy(doc)
            result = annotations.edit_annotation(doc, 3, spec([operation]))
            wanted = expected(doc, text, partitions)
            self.assertEqual(
                canonical(result) if text else result, canonical(wanted) if text else wanted
            )
            self.assertEqual(doc, before)
            doc = result

    def test_empty_initialization_uses_explicit_native_style_and_paragraph_request(self):
        doc = empty_document()
        before = copy.deepcopy(doc)
        result = annotations.edit_annotation(
            doc,
            3,
            spec(
                [edit(0, 0, "", "Reborn café", 0)],
                text_style=style(),
                definition={"horizontal-alignment": "left"},
            ),
        )
        wanted = copy.deepcopy(doc)
        definition = clip(wanted)["def"]
        definition["text"] = "Reborn café"
        definition["horizontal-alignment"] = "left"
        definition["textAttributes"]["keyframes"][0]["value"] = [
            dict(
                name=name,
                valueType=annotations.RICH_TYPES[name],
                value=value,
                rangeStart=0,
                rangeEnd=12,
            )
            for name, value in style().items()
        ]
        self.assertEqual(canonical(result), canonical(wanted))
        self.assertEqual(doc, before)
        self.assertEqual(definition["font"], clip(doc)["def"]["font"])
        self.assertNotIn("kerning", {r["name"] for r in values(result)})

    def test_multiple_disjoint_edits_use_original_coordinates_in_either_input_order(self):
        doc = mixed()
        edits = [edit(6, 10, "café", "tea", 6), edit(19, 26, "Beta 42", "Go", 19)]
        wanted = expected(
            doc,
            "Alpha tea — omega\nGo",
            {
                "fontWeight": [(0, 6, 400), (6, 9, 700), (9, 22, 400)],
                "fontItalic": [(0, 14, 0), (14, 19, 2), (19, 22, 0)],
                "fontSize": [(0, 20, 36.0), (20, 22, 28.0)],
                "underline": [(0, 20, 1), (20, 22, 0)],
                "fgColor": [(0, 5, ORANGE), (5, 22, CYAN)],
            },
        )
        for operations in (edits, list(reversed(edits))):
            self.assertEqual(
                canonical(annotations.edit_annotation(doc, 3, spec(operations))), canonical(wanted)
            )

    def test_boundary_insertion_precedes_adjacent_replacement_without_losing_characters(self):
        doc = annotations.edit_annotation(
            fixture(),
            3,
            dict(schema_version=2, rich_ranges=[dict(start=1, end=2, rich=dict(fontWeight=700))]),
        )
        edits = [edit(1, 2, "B", "YZ", 1), edit(1, 1, "", "x", 0), edit(2, 2, "", "!", 2)]
        result = annotations.edit_annotation(doc, 3, spec(edits))
        self.assertEqual(clip(result)["def"]["text"], "AxYZ!C")
        self.assertEqual(
            [
                (r["rangeStart"], r["rangeEnd"], r["value"])
                for r in values(result)
                if r["name"] == "fontWeight"
            ],
            [(0, 2, 400), (2, 4, 700), (4, 6, 400)],
        )

    def test_explicit_anchor_is_resolved_independently_for_each_property(self):
        doc = mixed()
        result = annotations.edit_annotation(doc, 3, spec([edit(0, 10, "Alpha café", "Tea", 6)]))
        self.assertEqual(clip(result)["def"]["text"], "Tea — omega\nBeta 42")
        for name, value in [
            ("fontWeight", 700),
            ("fgColor", CYAN),
            ("fontSize", 36.0),
            ("underline", 1),
            ("fontItalic", 0),
        ]:
            first = next(r for r in values(result) if r["name"] == name and r["rangeStart"] == 0)
            self.assertEqual(first["value"], value)

    def test_selected_opaque_payloads_survive_splitting_and_prevent_false_merges(self):
        doc = mixed()
        for run in values(doc):
            if run["name"] == "fontWeight" and run["rangeStart"] == 6:
                run["nativeReset"] = {"opaque": "bold"}
        result = annotations.edit_annotation(doc, 3, spec([edit(8, 9, "f", "FF", 8)]))
        bold = [r for r in values(result) if r["name"] == "fontWeight" and r["value"] == 700]
        self.assertEqual(len(bold), 1)
        self.assertEqual((bold[0]["rangeStart"], bold[0]["rangeEnd"]), (6, 12))
        self.assertEqual(bold[0]["nativeReset"], {"opaque": "bold"})
        self.assertEqual(clip(result)["effects"], clip(doc)["effects"])
        self.assertEqual(project.scene_tracks(result)[0][1], project.scene_tracks(doc)[0][1])

    def test_astral_combining_and_crlf_offsets_compile_to_exact_utf8_slices(self):
        doc = fixture()
        clip(doc)["def"]["text"] = "Aé日😀e\u0301\r\nZ"
        for run in values(doc):
            run["rangeEnd"] = 16
        result = annotations.edit_annotation(doc, 3, spec([edit(2, 4, "日😀", "éß", 2)]))
        self.assertEqual(clip(result)["def"]["text"], "Aééße\u0301\r\nZ")
        self.assertTrue(all(r["rangeStart"] == 0 and r["rangeEnd"] == 13 for r in values(result)))

    def test_result_range_styles_and_definition_controls_run_after_text_edits(self):
        doc = mixed()
        result = annotations.edit_annotation(
            doc,
            3,
            spec(
                [edit(6, 10, "café", "résumé", 6)],
                rich_ranges=[dict(start=6, end=12, rich=dict(fgColor="(1,2,3,255)"))],
                definition={"width": 400},
            ),
        )
        color = next(
            r for r in values(result) if r["name"] == "fgColor" and r["value"] == "(1,2,3,255)"
        )
        self.assertEqual((color["rangeStart"], color["rangeEnd"]), (6, 14))
        self.assertEqual(clip(result)["def"]["width"], 400.0)

    def test_identical_replacement_is_noop_and_stale_expectation_refuses(self):
        doc = mixed()
        same = annotations.edit_annotation(doc, 3, spec([edit(6, 10, "café", "café", 6)]))
        self.assertEqual(same, doc)
        operation = spec([edit(6, 10, "café", "résumé", 6)])
        changed = annotations.edit_annotation(doc, 3, operation)
        before = copy.deepcopy(changed)
        with self.assertRaisesRegex(ValueError, "expected"):
            annotations.edit_annotation(changed, 3, operation)
        self.assertEqual(changed, before)

    def test_invalid_coordinates_expectations_anchors_and_shapes_refuse_without_mutation(self):
        valid = edit(6, 10, "café", "tea", 6)
        bad = [
            None,
            {},
            [],
            [None],
            [dict(valid, start=True)],
            [dict(valid, end=10.0)],
            [dict(valid, start=-1)],
            [dict(valid, end=27)],
            [dict(valid, start=11, end=10)],
            [dict(valid, expected="CAFE")],
            [dict(valid, end=11)],
            [dict(valid, text="bad\x00text")],
            [dict(valid, text=5)],
            [dict(valid, style_from=True)],
            [dict(valid, style_from=26)],
            [dict(valid, style_from=-1)],
            [dict(valid, future=1)],
            [{k: v for k, v in valid.items() if k != "style_from"}],
        ]
        for operations in bad:
            doc = mixed()
            before = copy.deepcopy(doc)
            with self.subTest(operations=operations), self.assertRaises(ValueError):
                annotations.edit_annotation(doc, 3, spec(operations))
            self.assertEqual(doc, before)

    def test_overlapping_edits_and_duplicate_insertions_refuse(self):
        for operations in (
            [edit(0, 10, "Alpha café", "X", 0), edit(6, 10, "café", "Y", 6)],
            [edit(0, 10, "Alpha café", "X", 0), edit(6, 6, "", "Y", 6)],
            [edit(6, 6, "", "X", 6), edit(6, 6, "", "Y", 6)],
        ):
            doc = mixed()
            before = copy.deepcopy(doc)
            with self.assertRaisesRegex(ValueError, "nonoverlapping"):
                annotations.edit_annotation(doc, 3, spec(operations))
            self.assertEqual(doc, before)

    def test_empty_input_requires_explicit_valid_styles_and_static_frame(self):
        operations = [edit(0, 0, "", "Go", 0)]
        bad_styles = [
            None,
            {},
            dict(style(), fontSize=0),
            dict(style(), fgColor="red"),
            dict(style(), future=1),
            {k: v for k, v in style().items() if k != "fontName"},
        ]
        for changes in bad_styles:
            doc = empty_document()
            before = copy.deepcopy(doc)
            with self.assertRaises(ValueError):
                annotations.edit_annotation(doc, 3, spec(operations, text_style=changes))
            self.assertEqual(doc, before)
        with self.assertRaisesRegex(ValueError, "text_style"):
            annotations.edit_annotation(empty_document(), 3, spec(operations))
        for mutation in ("time", "frames", "missing-value", "absent"):
            doc = empty_document()
            attrs = clip(doc)["def"]["textAttributes"]
            if mutation == "time":
                attrs["keyframes"][0]["time"] = 1
            elif mutation == "frames":
                attrs["keyframes"].append(copy.deepcopy(attrs["keyframes"][0]))
            elif mutation == "missing-value":
                attrs["keyframes"][0].pop("value")
            else:
                clip(doc)["def"].pop("textAttributes")
            with self.assertRaises(ValueError):
                annotations.edit_annotation(doc, 3, spec(operations, text_style=style()))

    def test_legacy_versions_keep_their_contract_and_version_three_fields_do_not_leak(self):
        for version in (1, 2):
            with self.assertRaisesRegex(ValueError, "schema_version"):
                annotations.edit_annotation(
                    mixed(),
                    3,
                    dict(schema_version=version, text_edits=[edit(6, 10, "café", "tea", 6)]),
                )
            with self.assertRaises(ValueError):
                annotations.edit_annotation(
                    empty_document(), 3, dict(schema_version=version, text="Go")
                )
        for changes in (dict(text="Go"), dict(text_style=style())):
            if "text" in changes:
                with self.assertRaises(ValueError):
                    annotations.edit_annotation(
                        mixed(), 3, spec([edit(6, 10, "café", "tea", 6)], **changes)
                    )
            else:
                with self.assertRaises(ValueError):
                    annotations.edit_annotation(mixed(), 3, dict(schema_version=3, **changes))
        with self.assertRaises(ValueError):
            annotations.edit_annotation(
                mixed(), 3, spec([edit(6, 10, "café", "tea", 6)], text_style=style())
            )

    def test_cli_exclusive_staging_repeat_and_stale_refusal_preserve_input_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, request, output = (
                root / name for name in ("source.json", "edit.json", "candidate.json")
            )
            source.write_bytes(project.encode_document(mixed()))
            before = source.read_bytes()
            request.write_text(json.dumps(spec([edit(6, 10, "café", "résumé", 6)])))
            command = [
                "set",
                str(source),
                "--clip-id",
                "3",
                "--spec",
                str(request),
                "--output",
                str(output),
            ]
            for written in (True, False):
                with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                    self.assertEqual(annotations.main(command), 0)
                report = json.loads(stdout.getvalue())
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
            self.assertEqual(
                clip(project.load(output)[0])["def"]["text"], "Alpha résumé — omega\nBeta 42"
            )
            self.assertEqual(source.read_bytes(), before)
            request.write_text(json.dumps(spec([edit(6, 10, "wrong", "tea", 6)])))
            target = output.read_bytes()
            with patch("sys.stderr", new_callable=io.StringIO):
                self.assertEqual(annotations.main(command), 1)
            self.assertEqual(output.read_bytes(), target)
            self.assertEqual(source.read_bytes(), before)


if __name__ == "__main__":
    unittest.main()
