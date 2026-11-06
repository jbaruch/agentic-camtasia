from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_annotations import fixture, clip, destination
import annotations
import project

TEXT = "Alpha café — omega\nBeta 42"
CYAN = "(32,192,240,255)"
ORANGE = "(255,128,64,255)"


def document():
    doc = fixture()
    project.scene_tracks(doc)[0].append(
        dict(
            trackIndex=1,
            medias=[
                dict(
                    id=90,
                    _type="AMFile",
                    src=1,
                    trackNumber=0,
                    start=0,
                    duration=5000,
                    mediaStart=0,
                    mediaDuration=5000,
                    scalar=1,
                    parameters=dict(volume=0.7),
                    effects=[dict(effectName="Denoise", opaque=["retain audio"])],
                )
            ],
        )
    )
    definition = clip(doc)["def"]
    definition["text"] = TEXT
    for run in values(doc):
        run["rangeEnd"] = 29
        if run["name"] == "fontName":
            run["value"] = "Montserrat"
        elif run["name"] == "fontSize":
            run["value"] = 96.0
        elif run["name"] == "fgColor":
            run["value"] = "(255,255,255,255)"
    return doc


def values(doc):
    return clip(doc)["def"]["textAttributes"]["keyframes"][0]["value"]


def canonical(doc):
    doc = copy.deepcopy(doc)
    values(doc).sort(key=lambda r: (r["name"], r["rangeStart"], r["rangeEnd"]))
    return doc


def request(**changes):
    return dict(schema_version=2, **changes)


def native_spec():
    return request(
        rich=dict(fontSize=36, underline=1, fgColor=CYAN),
        rich_ranges=[
            dict(start=6, end=10, rich=dict(fontWeight=700)),
            dict(start=13, end=18, rich=dict(fontItalic=2)),
            dict(start=19, end=26, rich=dict(fontSize=28, underline=0)),
            dict(start=0, end=5, rich=dict(fgColor=ORANGE)),
        ],
    )


def expected_native(doc):
    doc = copy.deepcopy(doc)
    partitions = {
        "fontWeight": [(0, 6, 400), (6, 11, 700), (11, 29, 400)],
        "fontItalic": [(0, 16, 0), (16, 21, 2), (21, 29, 0)],
        "fontSize": [(0, 22, 36.0), (22, 29, 28.0)],
        "underline": [(0, 22, 1), (22, 29, 0)],
        "fgColor": [(0, 5, ORANGE), (5, 29, CYAN)],
    }
    result = []
    for run in values(doc):
        for start, end, value in partitions.get(run["name"], [(0, 29, run["value"])]):
            item = copy.deepcopy(run)
            item.update(rangeStart=start, rangeEnd=end, value=value)
            result.append(item)
    values(doc)[:] = result
    return doc


class AnnotationRichRangeTests(unittest.TestCase):
    def test_fixed_native_partitions_preserve_complete_document_and_opaque_run_fields(self):
        doc = document()
        before = copy.deepcopy(doc)
        result = annotations.edit_annotation(doc, 3, native_spec())
        self.assertEqual(canonical(result), canonical(expected_native(doc)))
        self.assertEqual(doc, before)
        self.assertEqual(clip(result)["def"]["font"], clip(doc)["def"]["font"])
        self.assertEqual(annotations.edit_annotation(result, 3, native_spec()), result)

    def test_crossing_existing_color_boundary_changes_only_requested_property_slice(self):
        doc = expected_native(document())
        before = copy.deepcopy(doc)
        result = annotations.edit_annotation(
            doc,
            3,
            request(rich_ranges=[dict(start=2, end=10, rich=dict(fgColor="(128,224,64,255)"))]),
        )
        actual = [r for r in values(result) if r["name"] == "fgColor"]
        self.assertEqual(
            [(r["rangeStart"], r["rangeEnd"], r["value"]) for r in actual],
            [(0, 2, ORANGE), (2, 11, "(128,224,64,255)"), (11, 29, CYAN)],
        )
        self.assertEqual(
            [r for r in values(result) if r["name"] != "fgColor"],
            [r for r in values(doc) if r["name"] != "fgColor"],
        )
        self.assertEqual(doc, before)

    def test_partial_bold_reset_inside_a_run_coalesces_with_the_equal_following_run(self):
        doc = expected_native(document())
        result = annotations.edit_annotation(
            doc, 3, request(rich_ranges=[dict(start=8, end=10, rich=dict(fontWeight=400))])
        )
        self.assertEqual(
            [
                (r["rangeStart"], r["rangeEnd"], r["value"])
                for r in values(result)
                if r["name"] == "fontWeight"
            ],
            [(0, 6, 400), (6, 8, 700), (8, 29, 400)],
        )
        self.assertEqual(
            [r for r in values(result) if r["name"] != "fontWeight"],
            [r for r in values(doc) if r["name"] != "fontWeight"],
        )

    def test_whole_property_edit_and_partial_reset_coalesce_without_flattening_other_styles(self):
        doc = expected_native(document())
        for spec in (
            request(rich=dict(fontWeight=400)),
            request(rich_ranges=[dict(start=6, end=10, rich=dict(fontWeight=400))]),
        ):
            result = annotations.edit_annotation(doc, 3, spec)
            weight = [r for r in values(result) if r["name"] == "fontWeight"]
            self.assertEqual(len(weight), 1)
            self.assertEqual(
                (weight[0]["rangeStart"], weight[0]["rangeEnd"], weight[0]["value"]), (0, 29, 400)
            )
            self.assertEqual(
                [r for r in values(result) if r["name"] != "fontWeight"],
                [r for r in values(doc) if r["name"] != "fontWeight"],
            )

    def test_distinct_opaque_payloads_do_not_merge_when_values_become_equal(self):
        doc = expected_native(document())
        for run in values(doc):
            if run["name"] == "fontWeight" and run["rangeStart"] == 6:
                run["opaqueNative"] = dict(reset="retain")
        result = annotations.edit_annotation(doc, 3, request(rich=dict(fontWeight=400)))
        weight = [r for r in values(result) if r["name"] == "fontWeight"]
        self.assertEqual(len(weight), 3)
        self.assertEqual(weight[1]["opaqueNative"], dict(reset="retain"))
        self.assertEqual(
            [(r["rangeStart"], r["rangeEnd"]) for r in weight], [(0, 6), (6, 11), (11, 29)]
        )

    def test_code_point_offsets_cover_multibyte_astral_combining_and_newline_characters(self):
        doc = fixture()
        text = "Aé日😀e\u0301\r\nZ"
        clip(doc)["def"]["text"] = text
        for run in values(doc):
            run["rangeEnd"] = 16
        result = annotations.edit_annotation(
            doc, 3, request(rich_ranges=[dict(start=2, end=4, rich=dict(fontWeight=700))])
        )
        self.assertEqual(
            [
                (r["rangeStart"], r["rangeEnd"], r["value"])
                for r in values(result)
                if r["name"] == "fontWeight"
            ],
            [(0, 3, 400), (3, 10, 700), (10, 16, 400)],
        )
        self.assertEqual(clip(result)["def"]["text"], text)

    def test_disjoint_same_property_requests_and_overlapping_different_properties_commute(self):
        edits = [
            dict(start=0, end=5, rich=dict(fontWeight=700)),
            dict(start=19, end=26, rich=dict(fontWeight=700)),
            dict(start=3, end=21, rich=dict(fontItalic=2)),
        ]
        forward = annotations.edit_annotation(document(), 3, request(rich_ranges=edits))
        reverse = annotations.edit_annotation(
            document(), 3, request(rich_ranges=list(reversed(edits)))
        )
        self.assertEqual(canonical(forward), canonical(reverse))
        for ranges in (
            [
                dict(start=0, end=6, rich=dict(fontWeight=700)),
                dict(start=5, end=8, rich=dict(fontWeight=400)),
            ],
            [edits[0], edits[0]],
        ):
            with self.assertRaisesRegex(ValueError, "non-overlapping"):
                annotations.edit_annotation(document(), 3, request(rich_ranges=ranges))

    def test_invalid_range_requests_refuse_without_mutation(self):
        valid = dict(start=0, end=5, rich=dict(fontWeight=700))
        bad = [
            None,
            {},
            [],
            [None],
            [dict(valid, start=True)],
            [dict(valid, end=5.0)],
            [dict(valid, start=-1)],
            [dict(valid, end=27)],
            [dict(valid, end=0)],
            [dict(valid, future=True)],
            [dict(valid, rich={})],
            [dict(valid, rich=dict(future=1))],
            [dict(valid, rich=dict(fontWeight=500))],
            [dict(valid, rich=dict(fgColor="red"))],
            [dict(valid, rich=dict(fontSize=0))],
        ]
        for changes in bad:
            doc = document()
            before = copy.deepcopy(doc)
            with self.subTest(changes=changes), self.assertRaises(ValueError):
                annotations.edit_annotation(doc, 3, request(rich_ranges=changes))
            self.assertEqual(doc, before)
        with self.assertRaisesRegex(ValueError, "schema_version"):
            annotations.edit_annotation(document(), 3, dict(schema_version=1, rich_ranges=[valid]))

    def test_invalid_native_partitions_refuse_without_mutation(self):
        for mutation in (
            "gap",
            "overlap",
            "duplicate",
            "inside-utf8",
            "zero",
            "reversed",
            "bool",
            "unknown",
            "type",
            "missing-value",
            "animated",
            "frames",
        ):
            doc = expected_native(document())
            attrs = clip(doc)["def"]["textAttributes"]
            frame = attrs["keyframes"][0]
            run = next(
                r for r in frame["value"] if r["name"] == "fontWeight" and r["rangeStart"] == 6
            )
            if mutation == "gap":
                run["rangeStart"] = 7
            elif mutation == "overlap":
                run["rangeStart"] = 5
            elif mutation == "duplicate":
                frame["value"].append(copy.deepcopy(run))
            elif mutation == "inside-utf8":
                run["rangeEnd"] = 10
            elif mutation == "zero":
                run["rangeEnd"] = 6
            elif mutation == "reversed":
                run["rangeEnd"] = 5
            elif mutation == "bool":
                run["rangeStart"] = True
            elif mutation == "unknown":
                run["name"] = "future"
            elif mutation == "type":
                run["valueType"] = "double"
            elif mutation == "missing-value":
                run.pop("value")
            elif mutation == "animated":
                frame["time"] = 1
            else:
                attrs["keyframes"].append(copy.deepcopy(frame))
            before = copy.deepcopy(doc)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                annotations.edit_annotation(
                    doc, 3, request(rich_ranges=[dict(start=0, end=5, rich=dict(fontWeight=700))])
                )
            self.assertEqual(doc, before)

    def test_text_replacement_uses_resulting_offsets_and_preserves_mixed_noop(self):
        spec = request(
            text="Go café", rich_ranges=[dict(start=3, end=7, rich=dict(fontWeight=700))]
        )
        doc = document()
        result = annotations.edit_annotation(doc, 3, spec)
        self.assertEqual(clip(result)["def"]["text"], "Go café")
        self.assertEqual(
            [(r["rangeStart"], r["rangeEnd"]) for r in values(result) if r["name"] == "fontWeight"],
            [(0, 3), (3, 8)],
        )
        self.assertEqual(result, annotations.edit_annotation(result, 3, spec))
        for spec in (request(text="different"), dict(schema_version=1, rich=dict(fontSize=36))):
            with self.assertRaisesRegex(ValueError, "mixed"):
                annotations.edit_annotation(result, 3, spec)

    def test_empty_text_and_absent_rich_properties_keep_existing_boundaries(self):
        doc = annotations.edit_annotation(document(), 3, dict(schema_version=1, text=""))
        result = annotations.edit_annotation(doc, 3, request(rich=dict(fontSize=48)))
        self.assertEqual(len(values(result)), 8)
        self.assertTrue(all(r["rangeStart"] == r["rangeEnd"] == 0 for r in values(result)))
        self.assertEqual(next(r["value"] for r in values(result) if r["name"] == "fontSize"), 48.0)
        doc = fixture(False)
        with self.assertRaisesRegex(ValueError, "existing rich"):
            annotations.edit_annotation(
                doc, 3, request(rich_ranges=[dict(start=0, end=1, rich=dict(fontSize=48))])
            )

    def test_mixed_template_constructor_preserves_all_styles_and_fade_identity(self):
        template = expected_native(document())
        before = copy.deepcopy(template)
        result = annotations.add_annotation(destination(), "0:0", 10, template, 3)
        expected = copy.deepcopy(clip(template))
        expected["id"] = 10
        self.assertEqual(clip(result), expected)
        self.assertEqual(project.scene_tracks(result)[0][0]["transitions"][0]["leftMedia"], 10)
        self.assertEqual(template, before)

    def test_cli_stages_v2_exclusively_and_identically_without_mutating_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, spec, output = (
                root / n for n in ("source.json", "spec.json", "candidate.json")
            )
            source.write_bytes(project.encode_document(document()))
            spec.write_text(json.dumps(native_spec()))
            before = source.read_bytes()
            command = [
                "set",
                str(source),
                "--clip-id",
                "3",
                "--spec",
                str(spec),
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
                canonical(project.load(output)[0]), canonical(expected_native(document()))
            )
            self.assertEqual(source.read_bytes(), before)
            output.write_text("occupied")
            with patch("sys.stderr", new_callable=io.StringIO):
                self.assertEqual(annotations.main(command), 1)
            self.assertEqual(output.read_text(), "occupied")


if __name__ == "__main__":
    unittest.main()
