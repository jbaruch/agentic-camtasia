from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_quizzes import document
import annotations
import project


def clip(doc):
    return project.scene_tracks(doc)[0][0]["medias"][0]


def fixture(rich=True):
    doc = document()
    node = clip(doc)
    node.clear()
    node.update(
        id=3,
        _type="Callout",
        start=1000,
        duration=5000,
        mediaStart=0,
        mediaDuration=5000,
        scalar=1,
        effects=[],
        parameters={"opacity": 0.8},
        attributes={"autoRotateText": True},
        metadata={"opaque": ["retain"]},
        animationTracks={"future": {"retain": True}},
        leftEdgeMods=[
            {
                "group": "DrawPercentageFade",
                "duration": 1000,
                "parameters": [{"name": "DrawTime", "func": "FadeInFunc"}],
            }
        ],
        **{
            "def": {
                "kind": "remix",
                "shape": "text-rectangle",
                "style": "urban",
                "text": "ABC",
                "width": 350.0,
                "height": 150.0,
                "fill-color-opacity": 1.0,
                "stroke-width": 2.0,
                "horizontal-alignment": "center",
                "line-spacing": 0.0,
                "font": {"name": "Montserrat", "size": 64.0, "weight": "Regular"},
                "tail-x": {"type": "double", "defaultValue": 0.0, "interp": "eioe", "opaque": [1]},
                "opaque": {"keep": True},
            }
        },
    )
    if rich:
        values = [
            ("fontName", "string", "Arial"),
            ("fontSize", "double", 64.0),
            ("fontWeight", "int", 400),
            ("fontItalic", "int", 0),
            ("fgColor", "color", "(47,59,68,255)"),
            ("kerning", "double", 0.0),
            ("underline", "int", 0),
            ("strikethrough", "int", 0),
        ]
        node["def"]["textAttributes"] = {
            "type": "textAttributeList",
            "opaque": ["list"],
            "keyframes": [
                {
                    "time": 0,
                    "duration": 0,
                    "endTime": 0,
                    "opaque": ["frame"],
                    "value": [
                        dict(
                            name=n,
                            valueType=t,
                            value=v,
                            rangeStart=0,
                            rangeEnd=3,
                            styleId="native-" + n,
                        )
                        for n, t, v in values
                    ],
                }
            ],
        }
    project.scene_tracks(doc)[0][0]["transitions"] = [
        dict(name="Fade", duration=500, leftMedia=3, attributes={"opaque": True})
    ]
    return doc


def spec(**values):
    return dict(schema_version=1, **values)


def destination():
    doc = document()
    project.scene_tracks(doc)[0][0]["medias"] = []
    project.scene_tracks(doc)[0][0]["parameters"] = {"opaque": "destination"}
    return doc


class AnnotationTests(unittest.TestCase):
    def test_unicode_replacement_updates_all_byte_ranges_and_preserves_style_ids(self):
        doc = fixture()
        before = copy.deepcopy(doc)
        result = annotations.edit_annotation(doc, 3, spec(text="Build →\n日本語 café"))
        expected = copy.deepcopy(doc)
        definition = clip(expected)["def"]
        definition["text"] = "Build →\n日本語 café"
        for run in definition["textAttributes"]["keyframes"][0]["value"]:
            run["rangeEnd"] = 25
        self.assertEqual(result, expected)
        self.assertEqual(doc, before)
        self.assertEqual(
            result, annotations.edit_annotation(result, 3, spec(text="Build →\n日本語 café"))
        )

    def test_uniform_rich_edit_retains_defaults_native_codes_and_opaque_payload(self):
        doc = fixture()
        changes = {
            "fontName": "Georgia",
            "fontSize": 48,
            "fontWeight": 700,
            "fontItalic": 2,
            "underline": 1,
            "strikethrough": -1,
            "fgColor": "(60,20,180,255)",
            "kerning": "3/2",
        }
        result = annotations.edit_annotation(doc, 3, spec(rich=changes))
        expected = copy.deepcopy(doc)
        for run in clip(expected)["def"]["textAttributes"]["keyframes"][0]["value"]:
            run["value"] = 1.5 if run["name"] == "kerning" else changes[run["name"]]
        self.assertEqual(result, expected)
        self.assertEqual(clip(result)["def"]["font"], clip(doc)["def"]["font"])

    def test_five_property_native_set_is_supported_without_injecting_others(self):
        doc = fixture()
        runs = clip(doc)["def"]["textAttributes"]["keyframes"][0]["value"]
        runs[:] = [r for r in runs if r["name"] not in {"fontItalic", "underline", "strikethrough"}]
        result = annotations.edit_annotation(doc, 3, spec(text="Together → Go"))
        self.assertEqual(len(clip(result)["def"]["textAttributes"]["keyframes"][0]["value"]), 5)

    def test_plain_text_keeps_font_and_absent_rich_representation(self):
        doc = fixture(False)
        result = annotations.edit_annotation(doc, 3, spec(text="Unicode → Go"))
        expected = copy.deepcopy(doc)
        clip(expected)["def"]["text"] = "Unicode → Go"
        self.assertEqual(result, expected)
        with self.assertRaisesRegex(ValueError, "existing rich"):
            annotations.edit_annotation(doc, 3, spec(rich={"fontSize": 48}))

    def test_mixed_partial_duplicate_animated_unknown_runs_refuse_without_mutation(self):
        for mutation in (
            "partial",
            "duplicate",
            "unknown",
            "type",
            "time",
            "frames",
            "bool-range",
            "missing",
        ):
            doc = fixture()
            attributes = clip(doc)["def"]["textAttributes"]
            frame = attributes["keyframes"][0]
            run = frame["value"][0]
            if mutation == "partial":
                run["rangeEnd"] = 2
            elif mutation == "duplicate":
                frame["value"].append(copy.deepcopy(run))
            elif mutation == "unknown":
                run["name"] = "future"
            elif mutation == "type":
                run["valueType"] = "double"
            elif mutation == "time":
                frame["time"] = 1
            elif mutation == "frames":
                attributes["keyframes"].append(copy.deepcopy(frame))
            elif mutation == "bool-range":
                run["rangeStart"] = False
            else:
                frame.pop("duration")
            before = copy.deepcopy(doc)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                annotations.edit_annotation(doc, 3, spec(text="new → text"))
            self.assertEqual(doc, before)

    def test_empty_text_uses_zero_byte_uniform_runs(self):
        result = annotations.edit_annotation(fixture(), 3, spec(text=""))
        self.assertTrue(
            all(
                r["rangeEnd"] == 0
                for r in clip(result)["def"]["textAttributes"]["keyframes"][0]["value"]
            )
        )
        self.assertEqual(
            clip(annotations.edit_annotation(result, 3, spec(text="→")))["def"]["text"], "→"
        )

    def test_definition_controls_preserve_typed_tail_defaults_and_reset_metadata(self):
        doc = fixture()
        result = annotations.edit_annotation(
            doc,
            3,
            spec(
                definition={
                    "width": 400,
                    "height": 180,
                    "fill-color-opacity": "3/4",
                    "stroke-width": 5,
                    "tail-x": 25,
                    "horizontal-alignment": "left",
                    "line-spacing": "6/5",
                }
            ),
        )
        expected = copy.deepcopy(doc)
        clip(expected)["def"].update(
            width=400.0,
            height=180.0,
            **{
                "fill-color-opacity": 0.75,
                "stroke-width": 5.0,
                "horizontal-alignment": "left",
                "line-spacing": 1.2,
            },
        )
        clip(expected)["def"]["tail-x"]["defaultValue"] = 25.0
        self.assertEqual(result, expected)

    def test_constructor_copies_whole_annotation_and_fade_with_only_identity_remap(self):
        doc, template = destination(), fixture()
        before = copy.deepcopy(doc), copy.deepcopy(template)
        result = annotations.add_annotation(doc, "0:0", 10, template, 3)
        expected = copy.deepcopy(doc)
        track = project.scene_tracks(expected)[0][0]
        track["medias"] = [copy.deepcopy(clip(template))]
        track["medias"][0]["id"] = 10
        track["transitions"] = [
            dict(name="Fade", duration=500, leftMedia=10, attributes={"opaque": True})
        ]
        self.assertEqual(result, expected)
        self.assertEqual((doc, template), before)
        self.assertEqual(annotations.add_annotation(result, "0:0", 10, template, 3), result)

    def test_constructor_refuses_occupied_lane_reused_id_and_clock_canvas_mismatch(self):
        for mutation in (
            "occupied",
            "id",
            "rate",
            "width",
            "height",
            "client",
            "scenes",
            "clock",
            "sibling",
        ):
            doc, template = destination(), fixture()
            if mutation == "occupied":
                project.scene_tracks(doc)[0][0]["medias"] = [dict(id=90)]
            elif mutation == "id":
                doc["future"]["id"] = 10
            elif mutation == "rate":
                template["editRate"] = 2000
            elif mutation in {"width", "height"}:
                template[mutation] = 100
            elif mutation == "client":
                template["authoringClientName"]["version"] = "2025.0.3"
            elif mutation == "scenes":
                template["timeline"]["sceneTrack"]["scenes"].append(
                    copy.deepcopy(template["timeline"]["sceneTrack"]["scenes"][0])
                )
            elif mutation == "clock":
                clip(template).pop("scalar")
            else:
                project.scene_tracks(template)[0][0]["medias"].append(dict(id=91))
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                annotations.add_annotation(doc, "0:0", 10, template, 3)

    def test_constructor_refuses_external_references_and_shared_transitions(self):
        for mutation in ("src", "effect", "quiz", "marker", "shared", "foreign"):
            template = fixture()
            if mutation == "src":
                clip(template)["src"] = 1
            elif mutation == "effect":
                clip(template)["effects"] = [dict(effectName="MediaMatte")]
            elif mutation == "quiz":
                clip(template)["parameters"]["quiz"] = {}
            elif mutation == "marker":
                clip(template)["parameters"]["toc"] = {}
            elif mutation == "shared":
                project.scene_tracks(template)[0][0]["transitions"][0]["rightMedia"] = 4
            else:
                project.scene_tracks(template)[0][0]["transitions"][0]["leftMedia"] = 4
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                annotations.add_annotation(destination(), "0:0", 10, template, 3)

    def test_svg_constructor_preserves_drawing_and_refuses_external_content(self):
        template = fixture(False)
        clip(template)["def"] = dict(
            kind="TypeWinSVG",
            xmlContent='<svg xmlns="http://www.w3.org/2000/svg"><path d="M0 0 L1 1"/></svg>',
        )
        result = annotations.add_annotation(destination(), "0:0", 10, template, 3)
        self.assertEqual(clip(result)["leftEdgeMods"], clip(template)["leftEdgeMods"])
        for xml in (
            "<svg><image href='file.png'/></svg>",
            "<svg><script/></svg>",
            "<svg><path fill='url(x)'/></svg>",
            "<svg>",
        ):
            clip(template)["def"]["xmlContent"] = xml
            with self.assertRaises(ValueError):
                annotations.add_annotation(destination(), "0:0", 10, template, 3)

    def test_constructor_rejects_native_attribute_hotspots_without_copying_targets(self):
        for hotspot in (
            {
                "action": 3,
                "markerParametricId": 999,
                "markerTime": 2000,
                "lastMarkerGlobalTime": 3000,
                "pauseAtEnd": True,
            },
            {"action": 0, "pauseAtEnd": False},
            None,
        ):
            template, doc = fixture(), destination()
            clip(template)["attributes"]["hotspot"] = hotspot
            before = copy.deepcopy(template), copy.deepcopy(doc)
            with self.subTest(hotspot=hotspot), self.assertRaisesRegex(ValueError, "hotspots"):
                annotations.add_annotation(doc, "0:0", 10, template, 3)
            self.assertEqual((template, doc), before)

    def test_invalid_edits_and_signed_native_codes_refuse(self):
        invalid = [
            spec(text=None),
            spec(text="bad\x00"),
            spec(rich={"fontItalic": 1}),
            spec(rich={"strikethrough": 1}),
            spec(rich={"underline": True}),
            spec(rich={"fontSize": 0}),
            spec(rich={"fontName": ""}),
            spec(rich={"fgColor": "(256,0,0,0)"}),
            spec(rich={"fgColor": [0, 0, 0, 255]}),
            spec(definition={"width": 0}),
            spec(definition={"height": -1}),
            spec(definition={"fill-color-opacity": 2}),
            spec(definition={"line-spacing": 4}),
            spec(definition={"shape": "shape-star"}),
            spec(definition={"horizontal-alignment": "middle"}),
            spec(definition={"missing": 1}),
            spec(rich={}),
            {"schema_version": True, "text": "x"},
            spec(),
            spec(future=True),
        ]
        for request in invalid:
            with self.subTest(request=request), self.assertRaises(ValueError):
                annotations.edit_annotation(fixture(), 3, request)

    def test_animated_definition_controls_refuse_instead_of_flattening(self):
        doc = fixture()
        clip(doc)["def"]["tail-x"]["keyframes"] = [dict(time=0, value=1)]
        with self.assertRaises(ValueError):
            annotations.edit_annotation(doc, 3, spec(definition={"tail-x": 5}))

    def test_inspection_reports_declared_fonts_without_claiming_dependency_closure(self):
        row = annotations.inventory(fixture())[0]
        self.assertEqual(row["declaredFonts"], ["Arial", "Montserrat"])
        self.assertFalse(row["fontFilesVerified"])
        self.assertEqual(row["definition"]["style"], "urban")

    def test_cli_stages_exclusively_reports_hashes_and_refuses_input_overwrite(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, request, output = [
                root / name for name in ("source.json", "spec.json", "candidate.json")
            ]
            raw = project.encode_document(fixture())
            source.write_bytes(raw)
            request.write_text(json.dumps(spec(text="Build → Buy")))
            args = [
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
                stdout = io.StringIO()
                with patch("sys.stdout", stdout):
                    self.assertEqual(annotations.main(args), 0)
                report = json.loads(stdout.getvalue())
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
                self.assertEqual(report["candidateSha256"], project.digest(output.read_bytes()))
            self.assertEqual(source.read_bytes(), raw)
            with patch("sys.stderr", io.StringIO()):
                self.assertEqual(annotations.main(args[:-1] + [str(source)]), 1)

    def test_cli_bad_arguments_are_json_exit_two(self):
        stderr = io.StringIO()
        with patch("sys.stderr", stderr), self.assertRaises(SystemExit) as error:
            annotations.main(["set", "x"])
        self.assertEqual(error.exception.code, 2)
        self.assertFalse(json.loads(stderr.getvalue())["ok"])

    def test_cli_constructor_and_inspection_use_read_only_native_templates(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source, template, output = [
                root / name for name in ("source.json", "template.json", "copy.json")
            ]
            source.write_bytes(project.encode_document(destination()))
            template.write_bytes(project.encode_document(fixture()))
            before = source.read_bytes(), template.read_bytes()
            args = [
                "add",
                str(source),
                "--track",
                "0:0",
                "--new-clip-id",
                "10",
                "--template-project",
                str(template),
                "--template-clip-id",
                "3",
                "--output",
                str(output),
            ]
            with patch("sys.stdout", io.StringIO()):
                self.assertEqual(annotations.main(args), 0)
            stdout = io.StringIO()
            with patch("sys.stdout", stdout):
                self.assertEqual(annotations.main(["inspect", str(output)]), 0)
            row = json.loads(stdout.getvalue())["annotations"][0]
            self.assertEqual(row["clipId"], 10)
            self.assertEqual(row["definition"]["style"], "urban")
            self.assertEqual(before, (source.read_bytes(), template.read_bytes()))

    def test_constructor_refuses_missing_canvas_lane_controls_duplicate_ids_and_bad_fades(self):
        for mutation in ("canvas", "lane", "duration", "overlap", "repeat-id"):
            doc, template = destination(), fixture()
            if mutation == "canvas":
                doc.pop("width")
                template.pop("width")
            elif mutation == "lane":
                project.scene_tracks(template)[0][0]["parameters"] = {"opacity": 0.5}
            elif mutation == "duration":
                project.scene_tracks(template)[0][0]["transitions"][0]["duration"] = 6000
            elif mutation == "overlap":
                transitions = project.scene_tracks(template)[0][0]["transitions"]
                transitions.append(copy.deepcopy(transitions[0]))
            else:
                doc = annotations.add_annotation(doc, "0:0", 10, template, 3)
                doc["future"]["id"] = 10
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                annotations.add_annotation(doc, "0:0", 10, template, 3)


if __name__ == "__main__":
    unittest.main()
