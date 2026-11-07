from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stderr, redirect_stdout

from test_captions import dynamic, display, spec
import captions
import project


# Mac 2026.2.4 UI saves, independent of the helper's supported-name set.
NATIVE_DEFAULTS = {
    "dynamic-caption-background-corner-radius": 24.0,
    "dynamic-caption-background-fill-color-red": 0.0,
    "dynamic-caption-background-fill-color-green": 0.0,
    "dynamic-caption-background-fill-color-blue": 0.0,
    "dynamic-caption-background-fill-color-alpha": 0.0,
    "dynamic-caption-word-rectangle-color-red": 1.0,
    "dynamic-caption-word-rectangle-color-green": 1.0,
    "dynamic-caption-word-rectangle-color-blue": 1.0,
    "dynamic-caption-word-rectangle-color-alpha": 0.0,
    "dynamic-caption-word-rectangle-corner-radius": 6.0,
    "dynamic-caption-word-rectangle-extra-size": 0.4,
    "dynamic-caption-word-rectangle-transition-time": 0.1,
}
CHANGES = {
    "dynamic-caption-background-corner-radius": 48,
    "dynamic-caption-background-fill-color-red": "32/255",
    "dynamic-caption-background-fill-color-green": "64/255",
    "dynamic-caption-background-fill-color-blue": "128/255",
    "dynamic-caption-background-fill-color-alpha": "7/10",
    "dynamic-caption-word-rectangle-color-red": "32/255",
    "dynamic-caption-word-rectangle-color-green": "192/255",
    "dynamic-caption-word-rectangle-color-blue": "96/255",
    "dynamic-caption-word-rectangle-color-alpha": "17/20",
    "dynamic-caption-word-rectangle-corner-radius": 18,
    "dynamic-caption-word-rectangle-extra-size": "1/5",
    "dynamic-caption-word-rectangle-transition-time": "1/4",
}
EXPECTED = [
    48.0,
    32 / 255,
    64 / 255,
    128 / 255,
    0.7,
    32 / 255,
    192 / 255,
    96 / 255,
    0.85,
    18.0,
    0.2,
    0.25,
]


def fixture():
    doc = dynamic()
    display(doc)["def"].update(NATIVE_DEFAULTS)
    return doc


class CaptionBackgroundTests(unittest.TestCase):
    def test_root_and_nested_edits_preserve_every_other_value_and_all_clocks(self):
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
                                start=705600000,
                                duration=4 * 705600000,
                                mediaStart=705600000,
                                mediaDuration=8 * 705600000,
                                scalar="1/2",
                                tracks=children,
                                metadata={"opaque": "keep"},
                                parameters={},
                            )
                        ],
                    )
                ]
            before = copy.deepcopy(doc)
            expected = copy.deepcopy(doc)
            target = next(n for _, n in project.objects(expected) if n.get("id") == 6)
            target["def"].update(zip(CHANGES, EXPECTED))
            with self.subTest(grouped=grouped):
                result = captions.set_display(doc, 6, spec(definition=CHANGES))
                self.assertEqual(result, expected)
                self.assertEqual(doc, before)
                self.assertEqual(captions.set_display(result, 6, spec(definition=CHANGES)), result)

    def test_zeroes_and_color_endpoints_are_supported_without_erasing_rgb(self):
        doc = fixture()
        request = dict(CHANGES)
        request.update({k: 0 for k in NATIVE_DEFAULTS if "-color-" not in k})
        request["dynamic-caption-background-fill-color-alpha"] = 0
        request["dynamic-caption-word-rectangle-color-alpha"] = 1
        result = captions.set_display(doc, 6, spec(definition=request))
        expected = copy.deepcopy(doc)
        display(expected)["def"].update(zip(CHANGES, EXPECTED))
        display(expected)["def"].update({k: 0.0 for k in NATIVE_DEFAULTS if "-color-" not in k})
        display(expected)["def"]["dynamic-caption-background-fill-color-alpha"] = 0.0
        display(expected)["def"]["dynamic-caption-word-rectangle-color-alpha"] = 1.0
        self.assertEqual(result, expected)

    def test_out_of_range_and_non_numeric_requests_leave_input_unchanged(self):
        for name in NATIVE_DEFAULTS:
            invalid = [-0.01, True, None, "bad", float("inf")]
            if "-color-" in name:
                invalid.append(1.01)
            for value in invalid:
                doc = fixture()
                before = copy.deepcopy(doc)
                with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                    captions.set_display(
                        doc,
                        6,
                        spec(
                            definition={"dynamic-caption-background-corner-radius": 48, name: value}
                        ),
                    )
                self.assertEqual(doc, before)

    def test_missing_animated_and_structured_fields_are_not_reconstructed(self):
        name = "dynamic-caption-word-rectangle-transition-time"
        for representation in (
            None,
            "resource",
            {"type": "double"},
            {"type": "double", "defaultValue": 0.1, "keyframes": [{"time": 0, "value": 0.1}]},
        ):
            doc = fixture()
            if representation is None:
                del display(doc)["def"][name]
            else:
                display(doc)["def"][name] = representation
            before = copy.deepcopy(doc)
            with self.subTest(representation=representation), self.assertRaises(ValueError):
                captions.set_display(doc, 6, spec(definition=CHANGES))
            self.assertEqual(doc, before)
        doc = fixture()
        display(doc)["def"][name] = dict(
            type="double",
            defaultValue=0.1,
            keyframes=[],
            valueBounds={"maxValue": 0.5},
            opaque=["keep"],
        )
        result = captions.set_display(doc, 6, spec(definition={name: "1/4"}))
        expected = copy.deepcopy(doc)
        display(expected)["def"][name]["defaultValue"] = 0.25
        self.assertEqual(result, expected)
        with self.assertRaisesRegex(ValueError, "bounds"):
            captions.set_display(doc, 6, spec(definition={name: 1}))

    def test_cli_stages_backgrounds_exclusively_and_refuses_invalid_without_output(self):
        with tempfile.TemporaryDirectory() as tmp:
            source, request, output = [
                Path(tmp) / n for n in ("source.json", "spec.json", "out.json")
            ]
            raw = project.encode_document(fixture())
            source.write_bytes(raw)
            request.write_text(json.dumps(spec(definition=CHANGES)))
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
                self.assertEqual(source.read_bytes(), raw)
                self.assertEqual(
                    display(project.load(output)[0])["def"][
                        "dynamic-caption-word-rectangle-extra-size"
                    ],
                    0.2,
                )
            saved = output.read_bytes()
            request.write_text(
                json.dumps(spec(definition={"dynamic-caption-background-fill-color-alpha": 2}))
            )
            for path_exists in (True, False):
                if not path_exists:
                    output.unlink()
                stdout, stderr = io.StringIO(), io.StringIO()
                with redirect_stdout(stdout), redirect_stderr(stderr):
                    self.assertEqual(captions.main(args), 1)
                self.assertEqual(source.read_bytes(), raw)
                self.assertEqual(
                    output.read_bytes() if path_exists else output.exists(),
                    saved if path_exists else False,
                )


if __name__ == "__main__":
    unittest.main()
