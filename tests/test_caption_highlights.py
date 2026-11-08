from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from test_caption_backgrounds import fixture as background_fixture
from test_captions import display, spec
import captions
import project


NATIVE_DEFAULTS = {
    "dynamic-caption-current-word-stroke-color-red": 1.0,
    "dynamic-caption-current-word-stroke-color-green": 1.0,
    "dynamic-caption-current-word-stroke-color-blue": 1.0,
    "dynamic-caption-current-word-stroke-color-alpha": 1.0,
    "dynamic-caption-current-word-glow-radius": 0.0,
}
REQUEST = {
    "dynamic-caption-current-word-stroke-color-red": "32/255",
    "dynamic-caption-current-word-stroke-color-green": "80/255",
    "dynamic-caption-current-word-stroke-color-blue": "208/255",
    "dynamic-caption-current-word-stroke-color-alpha": "13/20",
    "dynamic-caption-current-word-glow-radius": 20,
}
EXPECTED = {
    "dynamic-caption-current-word-stroke-color-red": 32 / 255,
    "dynamic-caption-current-word-stroke-color-green": 80 / 255,
    "dynamic-caption-current-word-stroke-color-blue": 208 / 255,
    "dynamic-caption-current-word-stroke-color-alpha": 0.65,
    "dynamic-caption-current-word-glow-radius": 20.0,
}


def fixture():
    doc = background_fixture()
    node = display(doc)
    node.update(duration=8 * captions.RATE, mediaDuration=8 * captions.RATE)
    node["def"].update(NATIVE_DEFAULTS)
    node["def"].update(
        {
            "dynamic-caption-current-word-stroke-extra-width": 8.0,
            "text-stroke-width": 2.0,
            "text-stroke-color-red": 1.0,
        }
    )
    return doc


def selected(doc):
    return next(n for _, n in project.objects(doc) if n.get("id") == 6)


class CaptionHighlightTests(unittest.TestCase):
    def test_root_and_group_edits_preserve_sources_clocks_backgrounds_and_text_outline(self):
        for grouped in (False, True):
            doc = fixture()
            if grouped:
                tracks = project.scene_tracks(doc)[0]
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
                                mediaStart=0,
                                mediaDuration=8 * captions.RATE,
                                scalar="1/2",
                                tracks=children,
                                attributes={"opaque": ["retain"]},
                                metadata={"opaque": ["group"]},
                                parameters={},
                            )
                        ],
                    )
                ]
            before = copy.deepcopy(doc)
            expected = copy.deepcopy(doc)
            selected(expected)["def"].update(EXPECTED)
            with self.subTest(grouped=grouped):
                result = captions.set_display(doc, 6, spec(definition=REQUEST))
                self.assertEqual(result, expected)
                self.assertEqual(doc, before)
                self.assertEqual(captions.set_display(result, 6, spec(definition=REQUEST)), result)

    def test_color_and_glow_edits_do_not_enable_disabled_highlighting_or_stroke_width(self):
        doc = fixture()
        display(doc)["def"].update(
            {
                "dynamic-caption-current-word-enabled": 0.0,
                "dynamic-caption-current-word-stroke-extra-width": 0.0,
            }
        )
        expected = copy.deepcopy(doc)
        display(expected)["def"].update(EXPECTED)
        self.assertEqual(captions.set_display(doc, 6, spec(definition=REQUEST)), expected)
        for field in NATIVE_DEFAULTS:
            result = captions.set_display(doc, 6, spec(definition={field: 0}))
            expected = copy.deepcopy(doc)
            display(expected)["def"][field] = 0.0
            self.assertEqual(result, expected)

    def test_invalid_values_and_unknown_controls_are_atomic(self):
        for name in NATIVE_DEFAULTS:
            values = [-0.01, True, None, "bad", float("inf")]
            if "-color-" in name:
                values.append(1.01)
            for value in values:
                doc = fixture()
                before = copy.deepcopy(doc)
                request = dict(REQUEST)
                request[name] = value
                with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                    captions.set_display(doc, 6, spec(definition=request))
                self.assertEqual(doc, before)
        with self.assertRaisesRegex(ValueError, "supported"):
            captions.set_display(fixture(), 6, spec(definition={"word-glow": 20}))

    def test_missing_and_unfamiliar_fields_are_not_inserted_or_flattened(self):
        name = "dynamic-caption-current-word-glow-radius"
        for representation in (
            None,
            "resource",
            {"type": "double"},
            {"type": "double", "defaultValue": 0.0, "keyframes": [{"time": 0, "value": 0.0}]},
        ):
            doc = fixture()
            if representation is None:
                del display(doc)["def"][name]
            else:
                display(doc)["def"][name] = representation
            before = copy.deepcopy(doc)
            with self.subTest(representation=representation), self.assertRaises(ValueError):
                captions.set_display(doc, 6, spec(definition=REQUEST))
            self.assertEqual(doc, before)

    def test_static_typed_field_retains_bounds_and_unknown_metadata(self):
        doc = fixture()
        name = "dynamic-caption-current-word-glow-radius"
        display(doc)["def"][name] = dict(
            type="double",
            defaultValue=0.0,
            keyframes=[],
            valueBounds={"maxValue": 25},
            opaque=["retain"],
        )
        expected = copy.deepcopy(doc)
        display(expected)["def"][name]["defaultValue"] = 20.0
        self.assertEqual(captions.set_display(doc, 6, spec(definition={name: 20})), expected)
        with self.assertRaisesRegex(ValueError, "bounds"):
            captions.set_display(doc, 6, spec(definition={name: 30}))

    def test_cli_stages_exclusively_and_refuses_invalid_input_without_creating_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, request, output = [
                Path(tmp) / n for n in ("source.json", "spec.json", "out.json")
            ]
            source.write_bytes(project.encode_document(fixture()))
            original = source.read_bytes()
            request.write_text(json.dumps(spec(definition=REQUEST)))
            args = [
                "set-display",
                str(source),
                "--clip-id",
                "6",
                "--spec",
                str(request),
                "--output",
                str(output),
            ]
            for _ in range(2):
                stdout, stderr = io.StringIO(), io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    self.assertEqual(captions.main(args), 0, stderr.getvalue())
                self.assertFalse(json.loads(stdout.getvalue())["nativeVerified"])
                expected = fixture()
                display(expected)["def"].update(EXPECTED)
                self.assertEqual(project.load(output)[0], expected)
                self.assertEqual(source.read_bytes(), original)
            output.unlink()
            request.write_text(
                json.dumps(spec(definition={"dynamic-caption-current-word-glow-radius": -1}))
            )
            stdout, stderr = io.StringIO(), io.StringIO()
            with redirect_stdout(stdout), redirect_stderr(stderr):
                self.assertEqual(captions.main(args), 1)
            self.assertFalse(output.exists())
            self.assertEqual(source.read_bytes(), original)


if __name__ == "__main__":
    unittest.main()
