from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import plistlib
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

from test_effect_constructors import document, owners
from test_effects import node
import luts
import project

CUBE = """# Synthetic owned data; no vendor asset
TITLE "Different title # retained"
LUT_3D_SIZE 2
DOMAIN_MIN 0 0 0
DOMAIN_MAX 1 1 1
0 0 0
1 0 0
0 1 0
1 1 0
0 0 1
1 0 1
0 1 1
1 1 1
"""


def app_fixture(root):
    app = root / "Camtasia.app"
    directory = app / "Contents/Resources/Color LUTs"
    directory.mkdir(parents=True)
    (app / "Contents/Info.plist").write_bytes(
        plistlib.dumps(
            {
                "CFBundleIdentifier": "com.techsmith.camtasia",
                "CFBundleShortVersionString": "2026.2.4",
                "CFBundleVersion": "2026.132",
            }
        )
    )
    (directory / "Owned.cube").write_text(CUBE)
    return app


def fixture(linked=False, typed=False):
    doc = document(linked)
    for owner in owners(doc, linked):
        parameters: dict[str, Any] = dict(
            lutSource="Original.cube",
            lut_intensity=1,
            channel=0,
            shadowRampStart=0,
            shadowRampEnd=0,
            highlightRampStart=1,
            highlightRampEnd=1,
        )
        if typed:
            for name in [
                "lut_intensity",
                "shadowRampStart",
                "shadowRampEnd",
                "highlightRampStart",
                "highlightRampEnd",
            ]:
                parameters[name] = dict(
                    type="double",
                    defaultValue=parameters[name],
                    interp="linr",
                    uiHints={"userInterfaceType": 0, "unitType": 0},
                    keyframes=[],
                    valueBounds={"minValue": 0, "maxValue": 1},
                    future=["keep"],
                )
        metadata = {
            "presetName": "Original preset",
            "default-LutEffect-lutSource": "Original.cube",
            "default-easeIn": "0",
            "default-easeOut": "0",
            "future": ["keep"],
        }
        if linked:
            metadata["effectIndex"] = "7"
        owner["effects"].append(
            dict(
                effectName="LutEffect",
                category="categoryVisualEffects",
                bypassed=False,
                parameters=parameters,
                metadata=metadata,
                future={"opaque": [1]},
            )
        )
    return doc


def lut(doc, linked=False):
    return owners(doc, linked)[-1]["effects"][1]


def spec(**fields):
    return dict(schema_version=1, **fields)


class LutTests(unittest.TestCase):
    def test_native_scalar_halves_and_bypass_preserve_everything_else(self):
        for linked in [False, True]:
            doc = fixture(linked)
            before = copy.deepcopy(doc)
            result, resource = luts.edit_lut(
                doc, 10 if linked else 3, spec(intensity="1/2", bypassed=True)
            )
            expected = copy.deepcopy(doc)
            for owner in owners(expected, linked):
                owner["effects"][1]["parameters"]["lut_intensity"] = 0.5
                owner["effects"][1]["bypassed"] = True
            self.assertEqual(result, expected)
            self.assertEqual(doc, before)
            self.assertIsNone(resource)
            self.assertIs(type(lut(result, linked)["parameters"]["lut_intensity"]), float)

    def test_typed_double_descriptors_keep_bounds_hints_and_reset_data(self):
        doc = fixture(True, True)
        result, _ = luts.edit_lut(doc, 10, spec(intensity=0.5))
        expected = copy.deepcopy(doc)
        for owner in owners(expected, True):
            owner["effects"][1]["parameters"]["lut_intensity"]["defaultValue"] = 0.5
        self.assertEqual(result, expected)
        self.assertEqual(node(result)["audio"], node(doc)["audio"])

    def test_all_thirteen_native_range_choices_have_independent_expected_channels_and_ramps(self):
        cases = {
            "grey-all": (0, [0, 0, 1, 1]),
            "grey-shadows": (0, [0, 0, 0.25, 0.5]),
            "red-shadows": (1, [0, 0, 0.25, 0.5]),
            "green-shadows": (2, [0, 0, 0.25, 0.5]),
            "blue-shadows": (3, [0, 0, 0.25, 0.5]),
            "grey-midtones": (0, [0.25, 0.4, 0.6, 0.75]),
            "red-midtones": (1, [0.25, 0.4, 0.6, 0.75]),
            "green-midtones": (2, [0.25, 0.4, 0.6, 0.75]),
            "blue-midtones": (3, [0.25, 0.4, 0.6, 0.75]),
            "grey-highlights": (0, [0.5, 0.75, 1, 1]),
            "red-highlights": (1, [0.5, 0.75, 1, 1]),
            "green-highlights": (2, [0.5, 0.75, 1, 1]),
            "blue-highlights": (3, [0.5, 0.75, 1, 1]),
        }
        for typed in [False, True]:
            doc = fixture(True, typed)
            for name, (channel, ramps) in cases.items():
                with self.subTest(typed=typed, name=name):
                    result, _ = luts.edit_lut(doc, 10, spec(range=name))
                    expected = copy.deepcopy(doc)
                    for owner in owners(expected, True):
                        p = owner["effects"][1]["parameters"]
                        p["channel"] = channel
                        for key, value in zip(
                            [
                                "shadowRampStart",
                                "shadowRampEnd",
                                "highlightRampStart",
                                "highlightRampEnd",
                            ],
                            ramps,
                        ):
                            if typed:
                                p[key]["defaultValue"] = value
                            else:
                                p[key] = value
                    self.assertEqual(result, expected)

    def test_edge_authoring_uses_project_ticks_and_keeps_native_zero_duration_records(self):
        doc = fixture(True)
        before = copy.deepcopy(doc)
        result, _ = luts.edit_lut(doc, 10, spec(easeIn=1, easeOut="3/2"))
        for owner in owners(result, True):
            effect = owner["effects"][1]
            self.assertEqual(
                effect["leftEdgeMods"],
                [
                    {
                        "group": "Video",
                        "duration": 1000,
                        "parameters": [{"name": "lut_intensity", "func": "FadeInFunc"}],
                    }
                ],
            )
            self.assertEqual(
                effect["rightEdgeMods"],
                [
                    {
                        "group": "Video",
                        "duration": 1500,
                        "parameters": [{"name": "lut_intensity", "func": "FadeOutFunc"}],
                    }
                ],
            )
        cleared, _ = luts.edit_lut(result, 10, spec(easeIn=0, easeOut=0))
        for owner in owners(cleared, True):
            effect = owner["effects"][1]
            self.assertEqual(effect["leftEdgeMods"][0]["duration"], 0)
            self.assertEqual(effect["rightEdgeMods"][0]["duration"], 0)
            self.assertEqual(effect["metadata"], lut(doc, True)["metadata"])
        self.assertEqual(doc, before)
        self.assertEqual(luts.edit_lut(doc, 10, spec(easeIn=0))[0], doc)

    def test_shared_edge_duration_and_unrelated_modifiers_are_preserved(self):
        doc = fixture()
        edges = [
            {
                "group": "Video",
                "duration": 500,
                "parameters": [
                    {"name": "other", "func": "FadeInFunc"},
                    {"name": "lut_intensity", "func": "FadeInFunc"},
                ],
                "future": ["keep"],
            },
            {
                "group": "Video",
                "duration": 600,
                "parameters": [{"name": "opacity", "func": "FadeInFunc"}],
            },
        ]
        lut(doc)["leftEdgeMods"] = edges
        self.assertEqual(luts.edit_lut(doc, 3, spec(easeIn="1/2"))[0], doc)
        for value in [0, 1]:
            with self.assertRaisesRegex(ValueError, "shared edge timing"):
                luts.edit_lut(doc, 3, spec(easeIn=value))
        self.assertEqual(lut(doc)["leftEdgeMods"], edges)

    def test_unknown_duplicate_or_malformed_edge_controls_refuse_without_mutation(self):
        for value in [
            None,
            "edge",
            [None],
            [{"parameters": {}}],
            [{"parameters": [None]}],
            [
                {
                    "group": "Video",
                    "duration": 500,
                    "parameters": [{"name": "lut_intensity", "func": "UnknownFunc"}],
                }
            ],
            [
                {
                    "group": "Video",
                    "duration": 500,
                    "parameters": [{"name": "lut_intensity", "func": "FadeInFunc"}],
                }
            ]
            * 2,
        ]:
            doc = fixture()
            lut(doc)["leftEdgeMods"] = copy.deepcopy(value)
            before = copy.deepcopy(doc)
            with self.subTest(value=value), self.assertRaises(ValueError):
                luts.edit_lut(doc, 3, spec(easeIn=1))
            self.assertEqual(doc, before)

    def test_curves_survive_unrelated_edits_and_refuse_static_flattening(self):
        for parameter, change in [
            ("lut_intensity", spec(intensity=0.5)),
            ("shadowRampEnd", spec(range="grey-all")),
        ]:
            doc = fixture(True, True)
            for owner in owners(doc, True):
                owner["effects"][1]["parameters"][parameter]["keyframes"] = [
                    {"time": 0, "endTime": 1000, "duration": 1000, "value": 0.5, "future": [1]}
                ]
            before = copy.deepcopy(doc)
            with self.assertRaisesRegex(ValueError, "animated"):
                luts.edit_lut(doc, 10, change)
            result, _ = luts.edit_lut(doc, 10, spec(bypassed=True))
            self.assertEqual(lut(result, True)["parameters"], lut(doc, True)["parameters"])
            self.assertEqual(doc, before)

    def test_resource_selection_uses_filename_keeps_presets_and_never_copies_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            app = app_fixture(root)
            user = root / "user"
            user.mkdir()
            (user / "Owned.cube").write_text(CUBE)
            before = {p: p.read_bytes() for p in root.rglob("*") if p.is_file()}
            doc = fixture(True, True)
            result, resource = luts.edit_lut(
                doc, 10, spec(source="Owned.cube"), app=app, user_root=user
            )
            self.assertEqual(lut(result, True)["parameters"]["lutSource"], "Owned.cube")
            self.assertEqual(lut(result, True)["metadata"], lut(doc, True)["metadata"])
            self.assertEqual(node(result)["audio"], node(doc)["audio"])
            assert resource is not None
            self.assertEqual(resource["title"], "Different title # retained")
            self.assertEqual(resource["gridSize"], 2)
            self.assertEqual(resource["rows"], 8)
            self.assertEqual(resource["sha256"], project.digest(CUBE.encode()))
            self.assertEqual(len(resource["locations"]), 2)
            self.assertEqual(resource["closure"], "selected-file-only")
            self.assertEqual(before, {p: p.read_bytes() for p in root.rglob("*") if p.is_file()})

    def test_conflicting_missing_or_path_resource_selectors_refuse(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            app = app_fixture(root)
            user = root / "user"
            user.mkdir()
            (user / "Owned.cube").write_text(CUBE + "# different bytes\n")
            with self.assertRaisesRegex(ValueError, "conflicting"):
                luts.edit_lut(fixture(), 3, spec(source="Owned.cube"), app=app, user_root=user)
            for name in ["absent.cube", "../Owned.cube", "/Owned.cube", "folder\\Owned.cube", None]:
                with self.subTest(name=name), self.assertRaises(ValueError):
                    luts.resolve_resource(app, name, root / "absent")
            with self.assertRaisesRegex(ValueError, "--app"):
                luts.edit_lut(fixture(), 3, spec(source="Owned.cube"))

    def test_cube_parser_rejects_incomplete_nonfinite_and_unobserved_structures(self):
        self.assertEqual(luts.cube_metadata(b"\xef\xbb\xbf" + CUBE.encode())["rows"], 8)
        for text in [
            "",
            CUBE.replace("1 1 1\n", ""),
            CUBE + "0 0 0\n",
            CUBE.replace("0 0 0\n", "nan 0 0\n"),
            CUBE.replace("LUT_3D_SIZE 2", "LUT_1D_SIZE 2"),
            CUBE.replace("DOMAIN_MAX 1 1 1", "DOMAIN_MAX 0 1 1"),
            CUBE.replace("LUT_3D_SIZE 2", "LUT_3D_SIZE 1"),
            CUBE.replace("LUT_3D_SIZE 2", "LUT_3D_SIZE 2\nLUT_3D_SIZE 2"),
            CUBE + 'TITLE "late"\n',
            CUBE.replace("DOMAIN_MAX 1 1 1", "DOMAIN_MAX inf 1 1"),
        ]:
            with self.subTest(text=text), self.assertRaises(ValueError):
                luts.cube_metadata(text.encode())

    def test_case_aliases_with_different_bytes_are_ambiguous(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            app = app_fixture(root)
            user = root / "user"
            user.mkdir()
            (user / "owned.cube").write_text(CUBE + "# different resource\n")
            records = luts.resources(app, user)
            self.assertTrue(all(row["ambiguous"] for row in records))
            self.assertEqual(records[0]["aliases"], ["Owned.cube", "owned.cube"])
            with self.assertRaisesRegex(ValueError, "conflicting"):
                luts.resolve_resource(app, "Owned.cube", user)

    def test_malformed_selected_cube_refuses_with_its_path_and_recovery_action(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            app = app_fixture(root)
            path = app / "Contents/Resources/Color LUTs/Owned.cube"
            path.write_text(CUBE.replace("1 0 0", "1 invalid 0"))
            with self.assertRaisesRegex(ValueError, "Owned.cube.*select a complete finite 3D"):
                luts.resolve_resource(app, "Owned.cube", root / "absent")

    def test_app_build_and_malformed_plist_are_refused(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            app = app_fixture(root)
            info = app / "Contents/Info.plist"
            before = info.read_bytes()
            for key in ["CFBundleIdentifier", "CFBundleShortVersionString", "CFBundleVersion"]:
                changed = plistlib.loads(before)
                changed[key] = "different"
                info.write_bytes(plistlib.dumps(changed))
                with self.assertRaisesRegex(ValueError, "2026.2.4"):
                    luts.resources(app, root / "absent")
            for raw in [b"bad plist", b'<?xml version="1.0"?><plist>broken']:
                info.write_bytes(raw)
                with self.assertRaisesRegex(ValueError, "Info.plist"):
                    luts.resources(app, root / "absent")

    def test_invalid_specs_values_clocks_and_control_representations_refuse(self):
        for payload in [
            {},
            spec(),
            spec(intensity=True),
            spec(intensity=-1),
            spec(intensity="inf"),
            spec(intensity=2),
            spec(range="red-all"),
            spec(range=[]),
            spec(bypassed=1),
            spec(easeIn=True),
            spec(easeOut=-1),
            spec(easeIn=9),
            spec(easeIn="1/3000"),
            spec(extra=1),
            {"schema_version": True, "bypassed": True},
        ]:
            doc = fixture()
            before = copy.deepcopy(doc)
            with self.subTest(payload=payload), self.assertRaises(ValueError):
                luts.edit_lut(doc, 3, payload)
            self.assertEqual(doc, before)
        for name, value, change in [
            ("lut_intensity", True, spec(intensity=0.5)),
            ("lut_intensity", {"type": "int", "defaultValue": 1}, spec(intensity=0.5)),
            ("channel", True, spec(range="grey-all")),
        ]:
            doc = fixture()
            lut(doc)["parameters"][name] = value
            with self.assertRaises(ValueError):
                luts.edit_lut(doc, 3, change)
        doc = fixture()
        doc["authoringClientName"]["version"] = "2025.0.3"
        with self.assertRaises(ValueError):
            luts.edit_lut(doc, 3, spec(bypassed=True))

    def test_mirror_conflicts_and_ambiguous_tokens_refuse_and_explicit_tokens_select(self):
        doc = fixture(True)
        for owner in owners(doc, True):
            second = copy.deepcopy(owner["effects"][1])
            second["metadata"]["effectIndex"] = "9"
            owner["effects"].append(second)
        with self.assertRaisesRegex(ValueError, "unique effectIndex"):
            luts.edit_lut(doc, 10, spec(intensity=0.5))
        result, _ = luts.edit_lut(doc, 10, spec(intensity=0.5), token="9")
        self.assertEqual(node(result)["effects"][1], node(doc)["effects"][1])
        self.assertEqual(node(result)["effects"][2]["parameters"]["lut_intensity"], 0.5)
        node(doc)["effects"][1]["bypassed"] = True
        with self.assertRaisesRegex(ValueError, "linked"):
            luts.edit_lut(doc, 10, spec(intensity=0.5), token="7")

    def test_cli_resource_inspection_staging_and_exclusive_outputs(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            app = app_fixture(root)
            source, settings, output = [
                root / n for n in ["source.json", "spec.json", "candidate.json"]
            ]
            source.write_bytes(project.encode_document(fixture(True, True)))
            settings.write_text(
                json.dumps(
                    spec(
                        source="Owned.cube",
                        intensity="1/2",
                        range="grey-shadows",
                        easeIn=1,
                        easeOut="3/2",
                    )
                )
            )
            before = source.read_bytes()
            args = [
                "set",
                str(source),
                "--clip-id",
                "10",
                "--effect-token",
                "7",
                "--spec",
                str(settings),
                "--app",
                str(app),
                "--output",
                str(output),
            ]
            with patch.object(Path, "home", return_value=root / "home"):
                with patch("sys.stdout", new_callable=io.StringIO) as stream:
                    self.assertEqual(luts.main(["resources", "--app", str(app)]), 0)
                self.assertEqual(
                    json.loads(stream.getvalue())["resources"][0]["name"], "Owned.cube"
                )
                for written in [True, False]:
                    with patch("sys.stdout", new_callable=io.StringIO) as stream:
                        self.assertEqual(luts.main(args), 0)
                    report = json.loads(stream.getvalue())
                    self.assertEqual(report["written"], written)
                    self.assertFalse(report["nativeVerified"])
                    self.assertEqual(report["owner"], "camtasia-luts")
                    self.assertEqual(report["resource"]["name"], "Owned.cube")
                with patch("sys.stdout", new_callable=io.StringIO) as stream:
                    self.assertEqual(luts.main(["inspect", str(output)]), 0)
                self.assertEqual(len(json.loads(stream.getvalue())["effects"]), 2)
                output.write_text("occupied")
                for path in [source, output]:
                    with patch("sys.stderr", io.StringIO()):
                        self.assertEqual(luts.main([*args[:-1], str(path)]), 1)
                self.assertEqual(output.read_text(), "occupied")
                self.assertEqual(source.read_bytes(), before)

    def test_cli_corrupt_effect_names_refuse_as_json_before_inspection_or_staging(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            source, settings, output = [
                root / n for n in ["source.json", "spec.json", "candidate.json"]
            ]
            settings.write_text(json.dumps(spec(intensity=0.5)))
            for value in [None, "", [], 0]:
                doc = fixture()
                if value is None:
                    node(doc)["effects"][0].pop("effectName")
                else:
                    node(doc)["effects"][0]["effectName"] = value
                source.write_bytes(project.encode_document(doc))
                original = source.read_bytes()
                for args in [
                    ["inspect", str(source)],
                    [
                        "set",
                        str(source),
                        "--clip-id",
                        "3",
                        "--spec",
                        str(settings),
                        "--output",
                        str(output),
                    ],
                ]:
                    with (
                        self.subTest(value=value, command=args[0]),
                        patch("sys.stderr", new_callable=io.StringIO) as stream,
                    ):
                        self.assertEqual(luts.main(args), 1)
                    error = json.loads(stream.getvalue())
                    self.assertFalse(error["ok"])
                    self.assertIn("effectName", error["error"])
                    self.assertFalse(output.exists())
                    self.assertEqual(source.read_bytes(), original)

    def test_cli_syntax_errors_are_json_on_stderr_with_exit_two(self):
        for args in [
            [],
            ["inspect"],
            ["set"],
            ["resources"],
            ["unknown"],
            [
                "set",
                "source.json",
                "--clip-id",
                "not-an-integer",
                "--spec",
                "spec.json",
                "--output",
                "candidate.json",
            ],
        ]:
            with (
                self.subTest(args=args),
                patch("sys.stderr", new_callable=io.StringIO) as errors,
                patch("sys.stdout", new_callable=io.StringIO) as output,
            ):
                with self.assertRaises(SystemExit) as stopped:
                    luts.main(args)
            self.assertEqual(stopped.exception.code, 2)
            self.assertFalse(json.loads(errors.getvalue())["ok"])
            self.assertTrue(json.loads(errors.getvalue())["error"])
            self.assertEqual(output.getvalue(), "")

    def test_cli_help_remains_plaintext_without_an_error(self):
        with (
            patch("sys.stderr", new_callable=io.StringIO) as errors,
            patch("sys.stdout", new_callable=io.StringIO) as output,
        ):
            with self.assertRaises(SystemExit) as stopped:
                luts.main(["--help"])
        self.assertEqual(stopped.exception.code, 0)
        self.assertIn("usage:", output.getvalue())
        self.assertEqual(errors.getvalue(), "")


if __name__ == "__main__":
    unittest.main()
