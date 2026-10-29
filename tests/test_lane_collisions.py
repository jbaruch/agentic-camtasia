from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_project import clip, document, project


class LaneCollisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.doc = document()
        self.doc["version"] = "10.0"
        self.doc["authoringClientName"]["version"] = "2026.2.4"
        self.tracks = self.doc["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"]

    def test_simultaneous_panels_are_rejected_before_replacement(self) -> None:
        self.tracks[0]["medias"] = [clip(10, "Callout"), clip(11, "Callout", duration=50)]
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "media").mkdir()
            (root / "media/source.mp4").write_bytes(b"source existence fixture")
            baseline = copy.deepcopy(self.doc)
            baseline["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"].pop()
            original = project.encode_document(baseline)
            target, candidate = root / "project.tscproj", root / "candidate.json"
            target.write_bytes(original)
            candidate.write_bytes(project.encode_document(self.doc))
            with patch.object(project, "ensure_closed"):
                result = project.apply_candidate(
                    target, candidate, project.digest(original), [], []
                )
            self.assertFalse(result["changed"])
            self.assertFalse(result["validation"]["ok"])
            self.assertTrue(
                any("overlaps media" in error for error in result["validation"]["errors"])
            )
            self.assertEqual(target.read_bytes(), original)
            self.assertEqual(list(root.glob("project.before-*")), [])

    def test_gaps_adjacent_endpoints_and_unsorted_storage_are_legal(self) -> None:
        self.tracks[0]["medias"] = [
            clip(12, start="250/3", duration="10/3"),
            clip(10, start=-10, duration=20),
            clip(11, start=10, duration="100/3"),
        ]
        self.assertEqual(project.native_hazards(self.doc), [])

    def test_nested_overlap_reports_the_containing_long_interval(self) -> None:
        self.tracks[0]["medias"] = [
            clip(10, duration=100),
            clip(11, start=10, duration=10),
            clip(12, start=30, duration=10),
        ]
        errors = project.native_hazards(self.doc)
        self.assertEqual(len(errors), 2)
        self.assertTrue(all("overlaps media 0" in error for error in errors))

    def test_simultaneous_clips_on_separate_lanes_and_scenes_are_legal(self) -> None:
        self.tracks.append({"trackIndex": 1, "medias": [clip(11)]})
        self.doc["timeline"]["sceneTrack"]["scenes"].append(
            {"csml": {"tracks": [{"medias": [clip(12)]}]}}
        )
        self.assertEqual(project.native_hazards(self.doc), [])

    def test_linked_children_and_internal_stitched_offsets_are_not_flattened(self) -> None:
        self.tracks[0]["medias"] = [
            clip(10, "UnifiedMedia", video=clip(11), audio=clip(12, "AMFile")),
            clip(20, "StitchedMedia", start=100, medias=[clip(21), clip(22, start=-20)]),
        ]
        self.assertEqual(project.native_hazards(self.doc), [])

    def test_unfamiliar_build_and_clip_semantics_are_not_assumed(self) -> None:
        self.tracks[0]["medias"].append(clip(11, "FutureMedia"))
        self.assertEqual(project.native_hazards(self.doc), [])
        self.tracks[0]["medias"][1]["_type"] = "Callout"
        self.doc["authoringClientName"]["version"] = "2026.2.5"
        self.assertEqual(project.native_hazards(self.doc), [])

    def test_invalid_timing_is_reported_by_structural_validation(self) -> None:
        self.tracks[0]["medias"] = [clip(10, start="invalid"), clip(11, duration=False)]
        report = project.validate(self.doc, Path("/nonexistent"))
        self.assertFalse(report["ok"])
        self.assertTrue(any("/start:" in error for error in report["errors"]))
        self.assertTrue(any("/duration:" in error for error in report["errors"]))

    def test_invalid_clip_type_does_not_crash_the_native_guard(self) -> None:
        invalid = clip(10)
        invalid["_type"] = []
        self.tracks[0]["medias"] = [invalid]
        report = project.validate(self.doc, Path("/nonexistent"))
        self.assertFalse(report["ok"])
        self.assertTrue(any("/_type:" in error for error in report["errors"]))


if __name__ == "__main__":
    unittest.main()
