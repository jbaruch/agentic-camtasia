from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import plistlib
import tempfile
import unittest
from unittest.mock import patch

from test_transitions import fixture, track
import project
import transition_presets
import transitions


# Synthetic metadata exercises the installed representation without shipping a
# vendor definition or shader. Expected attributes below are independent values.
DEFINITION = r"""{
  "name": "SyntheticPreset", "localizedName": {"en": "Synthetic label"},
  "type": "transition", "attributes": [
    {"name": "Number", "type": "double", "defaultValue": 8.},
    {"name": "Angle", "type": "double", "defaultValue": 0.4,
     "minValue": 0., "maxValue": 0.},
    {"name": "FlipX", "type": "bool", "defaultValue": false},
    {"name": "Color0", "type": "Color", "value": "0055FF"}
  ], "code": "keep 8. and \"0.\" and slash \\ verbatim"
}"""


def app_fixture(folder: Path) -> Path:
    app = folder / "Selected App.app"
    resources = app / "Contents/Resources/Transitions"
    resources.mkdir(parents=True)
    (app / "Contents/Info.plist").write_bytes(
        plistlib.dumps(
            dict(
                CFBundleIdentifier="com.techsmith.camtasia",
                CFBundleShortVersionString="2026.2.4",
                CFBundleVersion="2026.132",
            )
        )
    )
    (resources / "synthetic.tsceffect").write_text(DEFINITION)
    return app.resolve()


class PresetTests(unittest.TestCase):
    def test_metadata_normalizes_only_trailing_points_outside_strings(self):
        value = transition_presets.metadata(DEFINITION)
        self.assertEqual(value["attributes"][0]["defaultValue"], 8.0)
        self.assertEqual(value["code"], 'keep 8. and "0." and slash \\ verbatim')
        for text in [
            '{"a": NaN}',
            '{"a": Infinity}',
            '{"a": 1e999}',
            '{"a": 1, "a": 2}',
            '{"a": .5}',
            '{"a": 01.}',
            '{"a": 1,}',
            '//comment\n{"a": 1}',
            "[]",
        ]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                transition_presets.metadata(text)
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "project.json"
            path.write_text('{"a": 8.}')
            with self.assertRaises(ValueError):
                project.load(path)

    def test_discovery_emits_complete_defaults_without_shader_or_metadata_ranges(self):
        with tempfile.TemporaryDirectory() as temporary:
            app = app_fixture(Path(temporary))
            before = {p: p.read_bytes() for p in app.rglob("*") if p.is_file()}
            presets = transition_presets.installed(app)
            self.assertEqual(
                presets,
                [
                    dict(
                        name="SyntheticPreset",
                        label="Synthetic label",
                        definition=str(app / "Contents/Resources/Transitions/synthetic.tsceffect"),
                        attributes=dict(
                            bypass=False,
                            reverse=False,
                            trivial=False,
                            useAudioPreRoll=True,
                            useVisualPreRoll=True,
                            Number=8.0,
                            Angle=0.4,
                            FlipX=False,
                            **{"Color0-red": 0.0, "Color0-green": 1 / 3, "Color0-blue": 1.0},
                        ),
                    )
                ],
            )
            self.assertEqual(before, {p: p.read_bytes() for p in before})

    def test_unsupported_or_ambiguous_declarations_refuse_without_partial_defaults(self):
        for attrs in [
            [{"name": "File", "type": "string", "defaultValue": "path"}],
            [{"name": "N", "type": "double", "defaultValue": True}],
            [{"name": "N", "type": "double", "defaultValue": float("inf")}],
            [{"name": "B", "type": "bool", "defaultValue": 0}],
            [{"name": "C", "type": "Color", "value": "#FFFFFF"}],
            [{"name": "bypass", "type": "bool", "defaultValue": False}],
            [{"name": "N", "type": "double", "defaultValue": 1}] * 2,
            [
                {"name": "C", "type": "Color", "value": "FFFFFF"},
                {"name": "C-red", "type": "double", "defaultValue": 0},
            ],
            [None],
            [{"type": "double", "defaultValue": 1}],
        ]:
            with self.subTest(attrs=attrs), self.assertRaises(ValueError):
                transition_presets.defaults(dict(type="transition", attributes=attrs))
        self.assertEqual(
            transition_presets.defaults({"type": "transition"}),
            dict(
                bypass=False,
                reverse=False,
                trivial=False,
                useAudioPreRoll=True,
                useVisualPreRoll=True,
            ),
        )
        for value in [
            {},
            {"type": "effect", "attributes": []},
            {"type": "transition", "attributes": None},
        ]:
            with self.assertRaises(ValueError):
                transition_presets.defaults(value)

    def test_discovery_refuses_wrong_app_build_empty_inventory_and_duplicate_names(self):
        with tempfile.TemporaryDirectory() as temporary:
            app = app_fixture(Path(temporary))
            info = app / "Contents/Info.plist"
            original = info.read_bytes()
            for key in ["CFBundleIdentifier", "CFBundleShortVersionString", "CFBundleVersion"]:
                changed = plistlib.loads(original)
                changed[key] = "different"
                info.write_bytes(plistlib.dumps(changed))
                with self.assertRaises(ValueError):
                    transition_presets.installed(app)
            info.write_bytes(original)
            directory = app / "Contents/Resources/Transitions"
            duplicate = directory / "duplicate.tsceffect"
            duplicate.write_text(DEFINITION)
            with self.assertRaisesRegex(ValueError, "unique"):
                transition_presets.installed(app)
            duplicate.unlink()
            (directory / "synthetic.tsceffect").unlink()
            with self.assertRaisesRegex(ValueError, "no transition definitions"):
                transition_presets.installed(app)

    def test_template_remaps_linked_endpoints_and_target_rate_preserving_opaque_fields(self):
        source = transitions.add_fade(fixture(), 3, 4, 1)
        value = track(source)["transitions"][0]
        value.update(name="BuiltinNative", future={"nested": ["preserve", 17]})
        value["attributes"].update(Angle=0.75, resource="native-resource")
        target = fixture()
        target["editRate"] = 2000
        for index, clip in enumerate(track(target)["medias"]):
            clip.update(
                id=40 + index * 3,
                _type="UnifiedMedia",
                video={"id": 50 + index, "_type": "VMFile", "src": 1},
                audio={"id": 60 + index, "_type": "AMFile", "gain": 0.7, "opaque": ["keep"]},
            )
        original = copy.deepcopy(source)
        for left, right, expected in [
            (40, 43, {"leftMedia": 40, "rightMedia": 43}),
            (None, 40, {"rightMedia": 40}),
            (43, None, {"leftMedia": 43}),
        ]:
            result = transitions.add_transition(
                target, left, right, 1, transitions.native_template(source, 0)
            )
            added = track(result)["transitions"][0]
            self.assertEqual(added["duration"], 1000 if left and right else 2000)
            self.assertEqual(transitions.endpoints(added), expected)
            self.assertEqual(added["attributes"], value["attributes"])
            self.assertEqual(added["future"], value["future"])
            expected_doc = copy.deepcopy(target)
            track(expected_doc)["transitions"] = [added]
            self.assertEqual(result, expected_doc)
        self.assertEqual(source, original)
        self.assertEqual(target["sourceBin"], fixture()["sourceBin"])

    def test_template_selection_refuses_wrong_identity_missing_index_and_null_endpoints(self):
        doc = transitions.add_fade(fixture(), 3, 4, 1)
        for index in [-1, 1, True]:
            with self.assertRaises(ValueError):
                transitions.native_template(doc, index)
        wrong = copy.deepcopy(doc)
        wrong["authoringClientName"]["version"] = "different"
        with self.assertRaises(ValueError):
            transitions.native_template(wrong, 0)
        track(doc)["transitions"][0]["leftMedia"] = None
        with self.assertRaises(ValueError):
            transitions.native_template(doc, 0)

    def test_cli_constructs_from_each_origin_and_keeps_inputs_and_output_exclusive(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            app = app_fixture(root)
            source, template = root / "source.json", root / "template.json"
            source.write_bytes(project.encode_document(fixture()))
            native = transitions.add_fade(fixture(), 3, 4, 1)
            track(native)["transitions"][0]["name"] = "BuiltinNative"
            template.write_bytes(project.encode_document(native))
            before = source.read_bytes(), template.read_bytes()
            with patch("sys.stdout", new_callable=io.StringIO) as stream:
                self.assertEqual(transitions.main(["presets", str(source), "--app", str(app)]), 0)
                self.assertEqual(
                    json.loads(stream.getvalue())["presets"][0]["name"], "SyntheticPreset"
                )
            for origin, name in [
                (["--app", str(app), "--name", "SyntheticPreset"], "SyntheticPreset"),
                (["--template-project", str(template), "--template-index", "0"], "BuiltinNative"),
            ]:
                output = root / (name + ".json")
                args = [
                    "add",
                    str(source),
                    "--left-id",
                    "3",
                    "--right-id",
                    "4",
                    "--duration",
                    "1",
                    "--output",
                    str(output),
                    *origin,
                ]
                for written in [True, False]:
                    with patch("sys.stdout", new_callable=io.StringIO) as stream:
                        self.assertEqual(transitions.main(args), 0)
                        report = json.loads(stream.getvalue())
                        self.assertEqual(report["written"], written)
                        self.assertFalse(report["nativeVerified"])
                    self.assertEqual(track(project.load(output)[0])["transitions"][0]["name"], name)
                output.write_text("occupied")
                with patch("sys.stderr", io.StringIO()):
                    self.assertEqual(transitions.main(args), 1)
                self.assertEqual(output.read_text(), "occupied")
            self.assertEqual((source.read_bytes(), template.read_bytes()), before)

    def test_cli_rejects_mixed_origin_options_missing_presets_and_malformed_plist(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            app = app_fixture(root)
            source, output = root / "source.json", root / "candidate.json"
            source.write_bytes(project.encode_document(fixture()))
            common = [
                "add",
                str(source),
                "--right-id",
                "3",
                "--duration",
                "1",
                "--output",
                str(output),
            ]
            for origin in [
                ["--app", str(app)],
                ["--app", str(app), "--name", "Synthetic label"],
                ["--app", str(app), "--name", "SyntheticPreset", "--template-index", "0"],
                ["--template-project", str(source)],
                ["--template-project", str(source), "--template-index", "0", "--name", "x"],
            ]:
                with self.subTest(origin=origin), patch("sys.stderr", io.StringIO()):
                    self.assertEqual(transitions.main(common + origin), 1)
                    self.assertFalse(output.exists())
            for raw in [b"invalid plist", b'<?xml version="1.0"?><plist>broken']:
                (app / "Contents/Info.plist").write_bytes(raw)
                with patch("sys.stderr", io.StringIO()):
                    self.assertEqual(
                        transitions.main(["presets", str(source), "--app", str(app)]), 1
                    )


if __name__ == "__main__":
    unittest.main()
