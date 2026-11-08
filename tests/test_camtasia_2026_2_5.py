from __future__ import annotations

import copy
import json
import plistlib
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_annotations import clip, fixture as annotation_fixture
from test_caption_block_transitions import fixture as caption_fixture, selected, NAME
from test_captions import spec
from test_project import clip as media_clip, document
import test_schema_audit as schema_fixtures
import annotations
import captions
import effects
import project
import schema_audit
import luts
import transition_presets
from test_luts import app_fixture as lut_app
from test_transition_presets import app_fixture as transition_app


def current(doc):
    doc["authoringClientName"]["version"] = "2026.2.5"
    return doc


class Camtasia202625Tests(unittest.TestCase):
    def test_resources_accept_exact_new_build_and_refuse_crossed_build_pairs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            apps = [lut_app(root), transition_app(root)]
            readers = [
                lambda app: luts.resources(app, root / "no-user-resources"),
                transition_presets.installed,
            ]
            for app, reader in zip(apps, readers):
                path = app / "Contents/Info.plist"
                info = plistlib.loads(path.read_bytes())
                before = reader(app)
                info.update(CFBundleShortVersionString="2026.2.5", CFBundleVersion="2026.136")
                path.write_bytes(plistlib.dumps(info))
                self.assertEqual(reader(app), before)
                for version, build in [
                    ("2026.2.5", "2026.132"),
                    ("2026.2.4", "2026.136"),
                    ("2026.2.6", "2026.136"),
                    (["2026.2.5"], "2026.136"),
                ]:
                    info.update(CFBundleShortVersionString=version, CFBundleVersion=build)
                    path.write_bytes(plistlib.dumps(info))
                    with self.subTest(version=version, build=build), self.assertRaises(ValueError):
                        reader(app)

    def test_identity_requires_exact_platform_build_and_format(self):
        doc = current(annotation_fixture())
        self.assertTrue(project.is_native_format10(doc))
        for key, value in (("version", "2026.2.6"), ("platform", "Windows"), ("name", "Other")):
            other = copy.deepcopy(doc)
            other["authoringClientName"][key] = value
            with self.subTest(key=key):
                self.assertFalse(project.is_native_format10(other))
                with self.assertRaises(ValueError):
                    annotations.require_native(other)
                with self.assertRaises(ValueError):
                    effects.require_native(other)
        doc["version"] = "9.0"
        self.assertFalse(project.is_native_format10(doc))
        with self.assertRaises(ValueError):
            annotations.require_native(doc)

    def test_caption_and_annotation_edits_preserve_current_authoring_identity(self):
        doc = current(caption_fixture("Fade"))
        donor = current(caption_fixture("SlideLeft"))
        before, donor_before = copy.deepcopy(doc), copy.deepcopy(donor)
        result = captions.copy_block_transition(doc, 6, donor, 6)
        expected = copy.deepcopy(doc)
        selected(expected)["def"][NAME] = "SlideLeft"
        self.assertEqual(result, expected)
        result = captions.set_display(
            doc, 6, spec(definition={"dynamic-caption-current-word-glow-radius": 12})
        )
        expected = copy.deepcopy(doc)
        selected(expected)["def"]["dynamic-caption-current-word-glow-radius"] = 12.0
        self.assertEqual(result, expected)
        self.assertEqual(doc, before)
        self.assertEqual(donor, donor_before)
        annotation = current(annotation_fixture())
        expected = copy.deepcopy(annotation)
        clip(expected)["def"]["horizontal-alignment"] = "left"
        self.assertEqual(
            annotations.edit_annotation(
                annotation, 3, {"schema_version": 1, "definition": {"horizontal-alignment": "left"}}
            ),
            expected,
        )

    def test_cross_build_native_templates_are_refused_without_mutating_inputs(self):
        doc, donor = current(caption_fixture()), caption_fixture("SlideLeft")
        before, source = copy.deepcopy(doc), copy.deepcopy(donor)
        with self.assertRaisesRegex(ValueError, "same authoring build"):
            captions.copy_block_transition(doc, 6, donor, 6)
        self.assertEqual(doc, before)
        self.assertEqual(donor, source)
        with self.assertRaisesRegex(ValueError, "same authoring build"):
            project.require_same_authoring_build(donor, doc)

    def test_known_parser_and_save_guards_continue_in_new_build(self):
        doc = current(document())
        doc["version"] = "10.0"
        tracks = project.scene_tracks(doc)[0]
        tracks[0]["medias"] = [media_clip(10, "Callout"), media_clip(11, "Callout")]
        self.assertTrue(any("overlaps media" in e for e in project.native_hazards(doc)))
        tracks[0]["medias"].pop()
        doc["timeline"]["sceneTrack"]["scenes"].append({"csml": {"tracks": []}})
        self.assertTrue(any("drops later scenes" in e for e in project.native_hazards(doc)))

    def test_profile_reuses_corrections_but_keeps_exact_build_and_type_checks(self):
        baseline, doc, previous = schema_fixtures.SchemaAuditTests().current_profile_fixture()
        profile = schema_audit.read_profile("mac-2026.2.5")
        self.assertEqual(profile["changes"][:-1], previous["changes"])
        self.assertEqual(profile["changes"][-1]["value"], "Border")
        with self.assertRaisesRegex(ValueError, "does not match"):
            schema_audit.audit(doc, baseline, profile)
        current(doc)
        result = schema_audit.audit(doc, baseline, profile)
        self.assertTrue(result["ok"], result)
        self.assertEqual(result["profile"], "mac-2026.2.5-format-10")
        self.assertTrue(result["upstreamErrors"])
        doc["timeline"]["effect"] = {"effectName": "Border"}
        self.assertTrue(schema_audit.audit(doc, baseline, profile)["ok"])
        self.assertNotIn(
            "Border",
            schema_audit.apply_profile(baseline, previous)["definitions"]["effect"]["properties"][
                "effectName"
            ]["enum"],
        )
        doc["timeline"]["effect"]["effectName"] = "InventedEffect"
        self.assertFalse(schema_audit.audit(doc, baseline, profile)["ok"])
        doc["timeline"]["effect"]["effectName"] = "Border"
        doc["timeline"]["sourceTrack"]["transcriptionSet"] = "true"
        self.assertFalse(schema_audit.audit(doc, baseline, profile)["ok"])
        self.assertEqual(schema_audit.read_profile("mac-2026.2.4"), previous)

    def test_profile_correction_reference_rejects_unknown_nested_or_different_schema(self):
        current_profile = schema_audit.read_document(schema_audit.PROFILE_FILES["mac-2026.2.5"])
        previous = schema_audit.read_profile("mac-2026.2.4")
        cases = [
            (dict(current_profile, changesFrom="../../other"), previous),
            (dict(current_profile, changes=[]), previous),
            (current_profile, dict(previous, changesFrom="mac-2026.2.5")),
            (dict(current_profile, upstreamSha256="different"), previous),
        ]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            paths = {name: root / (name + ".json") for name in ("mac-2026.2.4", "mac-2026.2.5")}
            for child, base in cases:
                paths["mac-2026.2.4"].write_text(json.dumps(base))
                paths["mac-2026.2.5"].write_text(json.dumps(child))
                with (
                    self.subTest(child=child.get("changesFrom")),
                    patch.object(schema_audit, "PROFILE_FILES", paths),
                    self.assertRaises(ValueError),
                ):
                    schema_audit.read_profile("mac-2026.2.5")


if __name__ == "__main__":
    unittest.main()
