from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_mattes import clip, curve_fixture, curve_spec, fixture, linked_fixture
import mattes
import project


def composition() -> dict:
    return {
        "schema_version": 1,
        "media": [{"clipId": 3, "mode": "alpha-invert"}],
        "tracks": [{"track": 0, "mode": "alpha"}],
    }


class MatteCompositionTests(unittest.TestCase):
    def test_combined_controls_preserve_content_and_are_idempotent(self) -> None:
        doc = fixture()
        spec = composition()
        spec["media"][0].update(intensity="1/2", easeIn="1/4", easeOut="3/4", bypass=True)
        result = mattes.edit_composition(doc, spec)
        effect = clip(result)["effects"][0]
        self.assertEqual(effect["parameters"]["matteMode"], 2)
        self.assertEqual(effect["parameters"]["intensity"]["defaultValue"], 0.5)
        self.assertEqual(effect["leftEdgeMods"][0]["duration"], 250)
        self.assertEqual(effect["rightEdgeMods"][0]["duration"], 750)
        self.assertTrue(effect["bypassed"])
        self.assertEqual(result["timeline"]["trackAttributes"][0]["matte"], 1)
        self.assertEqual(mattes.edit_composition(result, spec), result)
        clip(result)["effects"] = []
        result["timeline"]["trackAttributes"][0]["matte"] = 0
        self.assertEqual(result, doc)
        self.assertEqual(doc, fixture())

    def test_linked_visual_mirrors_share_identity_and_audio_survives(self) -> None:
        doc = linked_fixture()
        result = mattes.edit_composition(doc, composition())
        wrapper = clip(result)
        self.assertEqual(wrapper["effects"], wrapper["video"]["effects"])
        self.assertEqual(wrapper["effects"][0]["metadata"], {"effectIndex": "0"})
        self.assertEqual(wrapper["audio"], clip(doc)["audio"])
        updated = mattes.edit_composition(result, composition())
        self.assertEqual(updated, result)
        spec = composition()
        spec["media"][0]["mode"] = "none"
        spec["tracks"][0]["mode"] = "none"
        self.assertEqual(mattes.edit_composition(result, spec), doc)

    def test_root_and_group_tracks_are_independent_scopes(self) -> None:
        doc = fixture()
        child = copy.deepcopy(clip(doc))
        clip(doc).clear()
        clip(doc).update(
            id=9,
            _type="Group",
            effects=[],
            tracks=[{"trackIndex": 0, "matte": 0, "medias": [child], "opaque": [4]}],
        )
        spec = composition()
        spec["tracks"].append({"track": 0, "mode": "luminosity-invert", "groupId": 9})
        result = mattes.edit_composition(doc, spec)
        self.assertEqual(result["timeline"]["trackAttributes"][0]["matte"], 1)
        self.assertEqual(clip(result)["tracks"][0]["matte"], 4)
        self.assertEqual(clip(result)["tracks"][0]["opaque"], [4])
        self.assertEqual(clip(doc)["tracks"][0]["medias"][0]["effects"], [])

    def test_mode_only_preserves_curves_and_scalar_edit_refuses_flattening(self) -> None:
        doc = mattes.edit_intensity_curve(curve_fixture(), 3, curve_spec())
        parameter = copy.deepcopy(clip(doc)["effects"][0]["parameters"]["intensity"])
        result = mattes.edit_composition(doc, composition())
        self.assertEqual(clip(result)["effects"][0]["parameters"]["intensity"], parameter)
        spec = composition()
        spec["media"][0]["intensity"] = 0.5
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "animated"):
            mattes.edit_composition(doc, spec)
        self.assertEqual(doc, before)

    def test_duplicate_media_and_linked_aliases_are_refused(self) -> None:
        for doc, alias in ((fixture(), 3), (linked_fixture(), 4)):
            spec = composition()
            spec["media"].append({"clipId": alias, "bypass": True})
            before = copy.deepcopy(doc)
            with self.assertRaisesRegex(ValueError, "each physical media"):
                mattes.edit_composition(doc, spec)
            self.assertEqual(doc, before)

    def test_duplicate_track_is_refused_even_for_identical_values(self) -> None:
        for group_id in (None, 9):
            doc = fixture()
            spec = composition()
            if group_id is not None:
                child = copy.deepcopy(clip(doc))
                clip(doc).clear()
                clip(doc).update(
                    id=group_id,
                    _type="Group",
                    tracks=[{"trackIndex": 0, "matte": 0, "medias": [child]}],
                )
                spec["tracks"][0]["groupId"] = group_id
            spec["tracks"].append(copy.deepcopy(spec["tracks"][0]))
            before = copy.deepcopy(doc)
            with self.assertRaisesRegex(ValueError, "each physical track"):
                mattes.edit_composition(doc, spec)
            self.assertEqual(doc, before)

    def test_malformed_specs_refuse_without_mutation(self) -> None:
        cases = [
            {},
            {**composition(), "schema_version": True},
            {**composition(), "schema_version": 2},
            {**composition(), "future": 1},
            {**composition(), "media": []},
            {**composition(), "tracks": None},
        ]
        for item in (
            None,
            {},
            {"clipId": 3},
            {"clipId": True, "mode": "alpha"},
            {"clipId": 3, "mode": []},
            {"clipId": 3, "bypass": None},
            {"clipId": 3, "future": 1},
            {"clipId": 3, "intensity": True},
        ):
            cases.append({**composition(), "media": [item]})
        for item in (
            None,
            {},
            {"track": 0},
            {"track": True, "mode": "alpha"},
            {"track": 0, "mode": {}},
            {"track": 0, "mode": "alpha", "groupId": None},
            {"track": 0, "mode": "alpha", "groupId": True},
            {"track": 0, "mode": "alpha", "future": 1},
        ):
            cases.append({**composition(), "tracks": [item]})
        for spec in cases:
            with self.subTest(spec=spec):
                doc = fixture()
                with self.assertRaises(ValueError):
                    mattes.edit_composition(doc, spec)
                self.assertEqual(doc, fixture())

    def test_cli_stages_complete_candidate_and_refuses_partial_output(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, spec_path, output = (
                root / name for name in ("source.json", "spec.json", "out.json")
            )
            source.write_bytes(project.encode_document(fixture()))
            original = source.read_bytes()
            spec_path.write_text(json.dumps(composition()))
            command = [
                "set-composition",
                str(source),
                "--spec",
                str(spec_path),
                "--output",
                str(output),
            ]
            for written in (True, False):
                stream = io.StringIO()
                with patch("sys.stdout", stream):
                    self.assertEqual(mattes.main(command), 0)
                report = json.loads(stream.getvalue())
                self.assertEqual((report["written"], report["nativeVerified"]), (written, False))
            candidate = json.loads(output.read_text())
            self.assertEqual(clip(candidate)["effects"][0]["parameters"]["matteMode"], 2)
            self.assertEqual(candidate["timeline"]["trackAttributes"][0]["matte"], 1)
            saved = output.read_bytes()
            spec = composition()
            spec["tracks"][0]["mode"] = "luminosity"
            spec_path.write_text(json.dumps(spec))
            with patch("sys.stderr", io.StringIO()):
                self.assertEqual(mattes.main(command), 1)
            self.assertEqual(output.read_bytes(), saved)
            output.unlink()
            spec["tracks"].append({"track": 99, "mode": "alpha"})
            spec_path.write_text(json.dumps(spec))
            with patch("sys.stderr", io.StringIO()):
                self.assertEqual(mattes.main(command), 1)
            self.assertFalse(output.exists())
            self.assertEqual(source.read_bytes(), original)
