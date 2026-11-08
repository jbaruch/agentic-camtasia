from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_captions import closed, dynamic, fixture
import captions
import project


def document(form="linked"):
    doc = dynamic() if form == "dynamic" else fixture(form)
    doc["timeline"]["captionAttributes"].update(
        fontName="Arial",
        fontSize=32,
        foregroundColor=[255, 255, 255, 255],
        backgroundColor=[0, 0, 0, 204],
        lang="en",
        alignment=0,
        defaultFontSize=True,
        opacity=0.5,
        backgroundEnabled=True,
        backgroundOnlyAroundText=True,
    )
    return doc


def attributes(doc):
    return doc["timeline"]["captionAttributes"]


def spec() -> dict:
    return dict(
        schema_version=1,
        style=dict(
            fontName="Trebuchet MS",
            fontSize=48,
            foregroundColor=[255, 128, 64, 255],
            backgroundColor=[32, 48, 96, 128],
        ),
    )


class CaptionStyleTests(unittest.TestCase):
    def test_all_caption_help_is_versioned_json_without_loading_a_project(self):
        for command in [
            [],
            ["inspect"],
            ["map"],
            ["set-text"],
            ["set-cues"],
            ["correct-words"],
            ["retime"],
            ["set-display"],
            ["set-style"],
        ]:
            with (
                self.subTest(command=command),
                patch("sys.stdout", new_callable=io.StringIO) as stream,
                patch.object(
                    project, "load", side_effect=AssertionError("help must not load files")
                ),
                self.assertRaises(SystemExit) as error,
            ):
                captions.main([*command, "--help"])
            self.assertEqual(error.exception.code, 0)
            report = json.loads(stream.getvalue())
            self.assertEqual(report["schema_version"], 1)
            self.assertEqual(report["owner"], "camtasia-captions")
            self.assertTrue(report["ok"])
            self.assertIn("usage:", report["help"])
            self.assertIn("--help", report["help"])
            self.assertIn(command[0] if command else "set-style", report["help"])

    def test_literal_global_style_preserves_complete_cues_clocks_sources_and_dynamic_displays(self):
        for form in ["audio", "linked", "imported", "dynamic"]:
            doc = document(form)
            closed(doc)["keyframes"][0]["value"]["text"] = r"{\rtf1\ansi First caf\'e9}"
            closed(doc)["keyframes"][0]["opaque"] = ["point metadata"]
            before = copy.deepcopy(doc)
            wanted = copy.deepcopy(doc)
            attributes(wanted).update(
                fontName="Trebuchet MS",
                fontSize=48,
                foregroundColor=[255, 128, 64, 255],
                backgroundColor=[32, 48, 96, 128],
            )
            with self.subTest(form=form):
                result = captions.set_style(doc, spec())
                self.assertEqual(result, wanted)
                self.assertEqual(captions.set_style(result, spec()), result)
                self.assertEqual(doc, before)

    def test_partial_edits_keep_other_style_fields_and_all_legacy_companions(self):
        for name, value in [
            ("fontName", "Arial"),
            ("fontName", "Trebuchet MS"),
            ("fontName", "Verdana"),
            ("fontSize", 40),
            ("foregroundColor", [255, 128, 64, 128]),
            ("backgroundColor", [32, 48, 96, 0]),
        ]:
            doc = document()
            wanted = copy.deepcopy(doc)
            attributes(wanted)[name] = value
            with self.subTest(name=name, value=value):
                result = captions.set_style(doc, dict(schema_version=1, style={name: value}))
                self.assertEqual(result, wanted)
                self.assertFalse(attributes(result)["enabled"])
                self.assertEqual(attributes(result)["opacity"], 0.5)
                self.assertTrue(attributes(result)["defaultFontSize"])

    def test_requested_color_lists_are_not_shared_with_result_or_original(self):
        doc, request = document(), spec()
        result = captions.set_style(doc, request)
        request["style"]["foregroundColor"][0] = 1
        attributes(result)["backgroundColor"][0] = 2
        self.assertEqual(attributes(doc)["foregroundColor"], [255, 255, 255, 255])
        self.assertEqual(attributes(result)["foregroundColor"], [255, 128, 64, 255])
        self.assertEqual(request["style"]["backgroundColor"], [32, 48, 96, 128])

    def test_future_cue_authoring_preserves_selected_global_style(self):
        doc = captions.set_style(document("imported"), spec())
        result = captions.set_cues(
            doc,
            3,
            dict(schema_version=1, clock="media", cues=[dict(start=1, end=3, text="Later café")]),
        )
        wanted = copy.deepcopy(attributes(doc))
        wanted["enabled"] = True
        self.assertEqual(attributes(result), wanted)
        self.assertEqual(closed(result)["keyframes"][1]["value"]["text"], "Later café")

    def test_style_does_not_choose_or_retime_unknown_nested_and_multiscene_owners(self):
        doc = document("imported")
        scene = doc["timeline"]["sceneTrack"]["scenes"][0]
        owner = scene["csml"]["tracks"][0]["medias"][0]
        scene["csml"]["tracks"][0]["medias"] = [
            dict(id=90, _type="FutureContainer", medias=[owner], opaque="retained")
        ]
        doc["timeline"]["sceneTrack"]["scenes"].append(dict(csml=dict(tracks=[])))
        wanted = copy.deepcopy(doc)
        attributes(wanted).update(spec()["style"])
        self.assertEqual(captions.set_style(doc, spec()), wanted)

    def test_missing_attributes_or_requested_field_are_not_reconstructed(self):
        for key in [None, "fontSize", "backgroundColor"]:
            doc = document()
            if key is None:
                doc["timeline"].pop("captionAttributes")
            else:
                attributes(doc).pop(key)
            before = copy.deepcopy(doc)
            with self.subTest(key=key), self.assertRaises(ValueError):
                captions.set_style(doc, spec())
            self.assertEqual(doc, before)

    def test_invalid_spec_shapes_and_unsupported_attributes_refuse_atomically(self):
        for request in [
            {},
            dict(schema_version=True, style=dict(fontSize=40)),
            dict(schema_version=2, style=dict(fontSize=40)),
            dict(schema_version=1, style={}),
            dict(schema_version=1, style=[]),
            dict(schema_version=1, style=dict(fontSize=40), other=True),
            dict(schema_version=1, style=dict(opacity=0.7)),
            dict(schema_version=1, style=dict(defaultFontSize=False)),
            dict(schema_version=1, style=dict(enabled=True)),
            dict(schema_version=1, style=dict(fontSize=40, future=2)),
        ]:
            doc = document()
            before = copy.deepcopy(doc)
            with self.subTest(request=request), self.assertRaises(ValueError):
                captions.set_style(doc, request)
            self.assertEqual(doc, before)

    def test_font_choices_and_size_require_native_values(self):
        for name, values in [
            ("fontName", [None, True, "", "Arial Bold", "ArialMT", "Missing Font"]),
            ("fontSize", [None, True, "48", 48.0, 0, -1, float("nan"), float("inf")]),
        ]:
            for value in values:
                with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                    captions.set_style(document(), dict(schema_version=1, style={name: value}))

    def test_color_values_require_four_integer_bytes_not_normalized_channels_or_booleans(self):
        for name in ["foregroundColor", "backgroundColor"]:
            for value in [
                None,
                "#FF8040",
                [1, 2, 3],
                [1, 2, 3, 4, 5],
                [True, 2, 3, 4],
                [1.0, 2, 3, 4],
                [0, 0, 0, -1],
                [0, 0, 0, 256],
            ]:
                doc = document()
                before = copy.deepcopy(doc)
                with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                    captions.set_style(doc, dict(schema_version=1, style={name: value}))
                self.assertEqual(doc, before)

    def test_malformed_existing_changed_fields_refuse_without_touching_input(self):
        for name, value in [
            ("fontName", None),
            ("fontSize", 32.0),
            ("foregroundColor", [1, 2, 3]),
            ("backgroundColor", dict(type="color", keyframes=[])),
        ]:
            doc = document()
            attributes(doc)[name] = value
            before = copy.deepcopy(doc)
            with self.subTest(name=name), self.assertRaises(ValueError):
                captions.set_style(doc, spec())
            self.assertEqual(doc, before)

    def test_omitted_unfamiliar_font_and_opaque_global_fields_survive(self):
        doc = document()
        attributes(doc).update(fontName="Captured Future Font", future=dict(keyframes=["opaque"]))
        wanted = copy.deepcopy(doc)
        attributes(wanted)["fontSize"] = 40
        self.assertEqual(
            captions.set_style(doc, dict(schema_version=1, style=dict(fontSize=40))), wanted
        )

    def test_style_stays_with_its_observed_editor_build(self):
        for format_, version in [("9.0", "2025.0.3"), ("10.0", "2026.2.6")]:
            doc = document()
            doc["version"] = format_
            doc["authoringClientName"]["version"] = version
            with self.subTest(version=version), self.assertRaises(ValueError):
                captions.set_style(doc, spec())

    def test_inventory_exposes_complete_style_without_sharing_it_or_inventing_defaults(self):
        doc = document()
        report = captions.inventory(doc)
        self.assertEqual(report["captionAttributes"], attributes(doc))
        report["captionAttributes"]["foregroundColor"][0] = 0
        self.assertEqual(attributes(doc)["foregroundColor"], [255, 255, 255, 255])
        doc["timeline"].pop("captionAttributes")
        self.assertIsNone(captions.inventory(doc)["captionAttributes"])
        doc["timeline"] = None
        self.assertIsNone(captions.inventory(doc)["captionAttributes"])

    def test_cli_stages_global_style_repeat_and_refusal_without_clip_selector_or_source_writes(
        self,
    ):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, request, output = [
                root / name for name in ["source.json", "spec.json", "candidate.json"]
            ]
            doc = document()
            source.write_bytes(project.encode_document(doc))
            original = source.read_bytes()
            request.write_text(json.dumps(spec()))
            argv = ["set-style", str(source), "--spec", str(request), "--output", str(output)]
            for written in [True, False]:
                stream = io.StringIO()
                with patch("sys.stdout", stream):
                    self.assertEqual(captions.main(argv), 0)
                report = json.loads(stream.getvalue())
                self.assertEqual(report["written"], written)
                self.assertTrue(report["changed"])
                self.assertFalse(report["nativeVerified"])
                self.assertEqual(
                    report["captionAttributes"], attributes(captions.set_style(doc, spec()))
                )
            self.assertEqual(json.loads(output.read_bytes()), captions.set_style(doc, spec()))
            request.write_text(json.dumps(dict(schema_version=1, style=dict(fontSize=0))))
            before = output.read_bytes()
            with patch("sys.stderr", io.StringIO()):
                self.assertEqual(captions.main(argv), 1)
            self.assertEqual(output.read_bytes(), before)
            self.assertEqual(source.read_bytes(), original)
