from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_animation_freezes import owner_document
from test_animations import visual
import hotspots
import project

RATE = 705600000


def fixture(kind: str) -> dict:
    doc = owner_document(kind)
    owner = visual(doc)
    owner["attributes"] = {"future": ["retain"]}
    point = RATE if kind == "ScreenIMFile" else 9 * RATE
    owner["parameters"]["toc"] = {
        "type": "string",
        "keyframes": [
            {
                "time": point,
                "endTime": point,
                "duration": 0,
                "value": "Native point",
                "metadata": {"markerIdentifier": "existing-identity"},
            }
        ],
    }
    project.scene_tracks(doc)[0].append(
        {
            "trackIndex": 1,
            "medias": [
                {
                    "id": 70,
                    "_type": "AMFile",
                    "src": 1,
                    "parameters": {"volume": 0.7},
                    "effects": [{"effectName": "AudioCompression", "opaque": ["audio"]}],
                },
            ],
        }
    )
    return doc


class HotspotRecordingTests(unittest.TestCase):
    def test_default_constructor_keeps_cursor_children_sources_and_audio(self) -> None:
        for kind in ("ScreenIMFile", "StitchedMedia"):
            doc = fixture(kind)
            before = copy.deepcopy(doc)
            result = hotspots.edit_hotspot(doc, 3, "continue")
            self.assertEqual(
                visual(result)["attributes"].pop("hotspot"),
                {
                    "action": 0,
                    "gotoTime": 0,
                    "pauseAtEnd": True,
                    "url": "",
                    "openURLInNewWindow": True,
                    "markerParametricId": 0,
                    "markerTime": -1,
                    "lastMarkerGlobalTime": 0,
                },
            )
            self.assertEqual(result, before)
            self.assertEqual(doc, before)

    def test_native_local_and_trimmed_parent_marker_clocks(self) -> None:
        cases = [
            ("ScreenIMFile", 1, 8 * RATE, 0, 2 * RATE, RATE, 6350400000),
            ("ScreenIMFile", "1/2", 8 * RATE, 0, RATE, RATE, 5997600000),
            ("StitchedMedia", "1/2", 10 * RATE, 2 * RATE, 4 * RATE, 9 * RATE, 9525600000),
        ]
        for kind, scalar, start, media_start, duration, point, expected in cases:
            doc = fixture(kind)
            owner = visual(doc)
            owner.update(start=start, duration=duration, scalar=scalar)
            if kind == "StitchedMedia":
                owner["mediaStart"] = media_start
            before = copy.deepcopy(doc)
            result = hotspots.edit_hotspot(
                doc, 3, "marker", marker_owner=3, marker_time=1 if kind == "ScreenIMFile" else 9
            )
            effect = visual(result)["attributes"]["hotspot"]
            self.assertEqual(
                (
                    effect["markerParametricId"],
                    effect["markerTime"],
                    effect["lastMarkerGlobalTime"],
                ),
                (3, point, expected),
            )
            self.assertEqual(hotspots.marker_global_ticks(doc, 3, point), expected)
            self.assertEqual(doc, before)

    def test_held_source_frame_is_independent_of_marker_origin(self) -> None:
        for source_frame in (5621280000, 2822400000):
            doc = fixture("ScreenIMFile")
            visual(doc)["mediaStart"] = source_frame
            result = hotspots.edit_hotspot(doc, 3, "marker", marker_owner=3, marker_time=1)
            self.assertEqual(visual(result)["mediaStart"], source_frame)
            self.assertEqual(visual(result)["mediaDuration"], 1)
            self.assertEqual(
                visual(result)["attributes"]["hotspot"]["lastMarkerGlobalTime"], 6350400000
            )
            self.assertEqual(visual(result)["parameters"], visual(doc)["parameters"])

    def test_group_ancestry_uses_local_hold_clock_then_parent_transform(self) -> None:
        doc = fixture("ScreenIMFile")
        held = visual(doc)
        held["start"] = 2 * RATE
        group = {
            "id": 80,
            "_type": "Group",
            "start": 20 * RATE,
            "duration": 4 * RATE,
            "mediaStart": 0,
            "mediaDuration": 8 * RATE,
            "scalar": "1/2",
            "tracks": [{"medias": [held]}],
            "parameters": {},
            "attributes": {},
        }
        project.scene_tracks(doc)[0][0]["medias"] = [group]
        result = hotspots.edit_hotspot(doc, 3, "marker", marker_owner=3, marker_time=1)
        target = project.scene_tracks(result)[0][0]["medias"][0]["tracks"][0]["medias"][0]
        self.assertEqual(target["attributes"]["hotspot"]["lastMarkerGlobalTime"], 15170400000)
        self.assertNotIn("hotspot", group["attributes"])

    def test_conflicting_explicit_cache_refuses_unchanged_document(self) -> None:
        for kind, scalar, wrong in (("ScreenIMFile", "1/2", 9), ("StitchedMedia", 1, 8)):
            doc = fixture(kind)
            visual(doc)["scalar"] = scalar
            before = copy.deepcopy(doc)
            with self.assertRaisesRegex(ValueError, "conflicts"):
                hotspots.edit_hotspot(
                    doc,
                    3,
                    "marker",
                    marker_owner=3,
                    marker_time=1 if kind == "ScreenIMFile" else 9,
                    marker_global_time=wrong,
                )
            self.assertEqual(doc, before)

    def test_trimmed_out_and_fractional_mappings_are_not_guessed(self) -> None:
        doc = fixture("ScreenIMFile")
        with self.assertRaisesRegex(ValueError, "outside"):
            hotspots.marker_global_ticks(doc, 3, 3 * RATE)
        visual(doc)["scalar"] = "1/3"
        with self.assertRaisesRegex(ValueError, "between project ticks"):
            hotspots.marker_global_ticks(doc, 3, 1)
        doc = fixture("StitchedMedia")
        visual(doc).update(mediaStart=2 * RATE, duration=4 * RATE, scalar="1/2")
        with self.assertRaisesRegex(ValueError, "outside"):
            hotspots.marker_global_ticks(doc, 3, RATE)

    def test_stitched_children_cannot_be_edited_as_independent_hotspots(self) -> None:
        doc = fixture("StitchedMedia")
        before = copy.deepcopy(doc)
        for child_id in (4, 5):
            for action in ("continue", "remove"):
                with (
                    self.subTest(child=child_id, action=action),
                    self.assertRaisesRegex(ValueError, "stitched parent"),
                ):
                    hotspots.edit_hotspot(doc, child_id, action)
        self.assertEqual(doc, before)

    def test_new_owner_wrappers_and_shared_visual_scope_remain_refused(self) -> None:
        for kind in ("ScreenIMFile", "StitchedMedia"):
            doc = fixture(kind)
            with self.assertRaisesRegex(ValueError, "verified"):
                hotspots.visual_target(doc, 3)
            owner = visual(doc)
            wrapper = {
                "id": 80,
                "_type": "UnifiedMedia",
                "video": owner,
                "audio": {"id": 81, "_type": "AMFile", "parameters": {}, "effects": []},
            }
            project.scene_tracks(doc)[0][0]["medias"] = [wrapper]
            before = copy.deepcopy(doc)
            for alias in (3, 80):
                with self.assertRaisesRegex(ValueError, "linked hotspot binding"):
                    hotspots.edit_hotspot(doc, alias, "continue")
            with self.assertRaisesRegex(ValueError, "linked held/stitched marker clocks"):
                hotspots.marker_global_ticks(doc, 80, RATE)
            self.assertEqual(doc, before)

    def test_action_lifecycle_retains_inactive_fields_and_marker_identity(self) -> None:
        for kind in ("ScreenIMFile", "StitchedMedia"):
            doc = fixture(kind)
            result = hotspots.edit_hotspot(doc, 3, "time", time="13/2", pause=False)
            result = hotspots.edit_hotspot(
                result, 3, "url", url="https://example.test/destination", new_window=False
            )
            saved = visual(result)["attributes"]["hotspot"]
            self.assertEqual(saved["gotoTime"], 4586400000)
            self.assertFalse(saved["pauseAtEnd"])
            self.assertFalse(saved["openURLInNewWindow"])
            result = hotspots.edit_hotspot(
                result, 3, "marker", marker_owner=3, marker_time=1 if kind == "ScreenIMFile" else 9
            )
            self.assertEqual(visual(result)["parameters"], visual(doc)["parameters"])
            result = hotspots.edit_hotspot(result, 3, "remove")
            self.assertEqual(result, doc)
            self.assertEqual(hotspots.edit_hotspot(result, 3, "remove"), doc)

    def test_cli_inspection_marker_staging_noop_collision_and_removal(self) -> None:
        for kind in ("ScreenIMFile", "StitchedMedia"):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source = root / "source.json"
                output = root / "out.json"
                source.write_bytes(project.encode_document(fixture(kind)))
                original = source.read_bytes()
                command = [
                    "set",
                    str(source),
                    "--clip-id",
                    "3",
                    "--action",
                    "marker",
                    "--marker-owner",
                    "3",
                    "--marker-time",
                    "1" if kind == "ScreenIMFile" else "9",
                    "--output",
                    str(output),
                ]
                for written in (True, False):
                    stream = io.StringIO()
                    with patch("sys.stdout", stream):
                        self.assertEqual(hotspots.main(command), 0)
                    report = json.loads(stream.getvalue())
                    self.assertEqual(report["written"], written)
                    self.assertFalse(report["nativeVerified"])
                saved = output.read_bytes()
                with patch("sys.stderr", io.StringIO()):
                    self.assertEqual(
                        hotspots.main(
                            ["remove", str(source), "--clip-id", "3", "--output", str(output)]
                        ),
                        1,
                    )
                self.assertEqual(output.read_bytes(), saved)
                stream = io.StringIO()
                with patch("sys.stdout", stream):
                    self.assertEqual(hotspots.main(["inspect", str(output)]), 0)
                report = json.loads(stream.getvalue())
                self.assertEqual(report["markers"][0]["ownerId"], 3)
                self.assertEqual(report["hotspots"][0]["clipId"], 3)
                cleared = root / "clear.json"
                with patch("sys.stdout", io.StringIO()):
                    self.assertEqual(
                        hotspots.main(
                            ["remove", str(output), "--clip-id", "3", "--output", str(cleared)]
                        ),
                        0,
                    )
                self.assertEqual(project.load(cleared)[0], fixture(kind))
                self.assertEqual(source.read_bytes(), original)
