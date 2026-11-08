from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_effect_grouped_recordings import node
from test_matte_stitched_linked_recordings import fixture as native_parent
import hotspots
import project


def document():
    doc = native_parent()
    doc["authoringClientName"]["version"] = "2026.2.5"
    node(doc, 100)["parameters"]["toc"] = dict(
        type="string",
        keyframes=[
            dict(
                time=8373120000,
                endTime=8373120000,
                duration=0,
                value="Held destination",
                metadata={"markerIdentifier": "retain-native-marker-identity"},
            )
        ],
    )
    return doc


def default_hotspot():
    return dict(
        action=0,
        gotoTime=0,
        pauseAtEnd=True,
        url="",
        openURLInNewWindow=True,
        markerParametricId=0,
        markerTime=-1,
        lastMarkerGlobalTime=0,
    )


class StitchedLinkedRecordingHotspotTests(unittest.TestCase):
    def test_constructor_and_lifecycle_change_only_parent_hotspot(self):
        doc = document()
        before = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        expected_payload = default_hotspot()
        node(expected, 100)["attributes"]["hotspot"] = expected_payload
        actual = hotspots.edit_hotspot(doc, 100, "continue")
        self.assertEqual(actual, expected)
        actual = hotspots.edit_hotspot(actual, 100, "time", time="1/2")
        expected_payload.update(action=1, gotoTime=352800000)
        self.assertEqual(actual, expected)
        actual = hotspots.edit_hotspot(
            actual, 100, "url", url="http://127.0.0.1:8766/destination.html", new_window=False
        )
        expected_payload.update(
            action=2, url="http://127.0.0.1:8766/destination.html", openURLInNewWindow=False
        )
        self.assertEqual(actual, expected)
        actual = hotspots.edit_hotspot(
            actual, 100, "marker", marker_owner=100, marker_time="178/15"
        )
        expected_payload.update(
            action=3,
            markerParametricId=100,
            markerTime=8373120000,
            lastMarkerGlobalTime=4186560000,
        )
        self.assertEqual(actual, expected)
        self.assertEqual(node(actual, 100)["medias"], node(before, 100)["medias"])
        removed = hotspots.edit_hotspot(actual, 100, "remove")
        self.assertEqual(removed, before)
        self.assertEqual(hotspots.edit_hotspot(removed, 100, "remove"), before)
        self.assertEqual(doc, before)

    def test_parent_marker_identity_and_clock_ignore_linked_child_mirrors(self):
        doc = document()
        before = copy.deepcopy(doc)
        self.assertEqual(
            hotspots.markers(doc),
            [
                dict(
                    ownerId=100,
                    parameterOwnerId=100,
                    path="/timeline/sceneTrack/scenes/0/csml/tracks/0/medias/0/parameters/toc/keyframes/0",
                    time=8373120000,
                    label="Held destination",
                    timelineMarker=False,
                )
            ],
        )
        self.assertEqual(hotspots.marker_global_ticks(doc, 100, 8373120000), 4186560000)
        self.assertEqual(node(doc, 50)["mediaStart"], 7008960000)
        self.assertEqual(node(doc, 50)["mediaDuration"], 1)
        self.assertEqual(doc, before)

    def test_hidden_linked_wrapper_video_audio_and_hold_are_not_hotspot_owners(self):
        doc = document()
        before = copy.deepcopy(doc)
        moving = node(doc, 10)
        child_ids = [moving["id"], moving["video"]["id"], moving["audio"]["id"], 50]
        for clip_id in child_ids:
            for action in ("continue", "remove"):
                with self.subTest(clip_id=clip_id, action=action), self.assertRaises(ValueError):
                    hotspots.edit_hotspot(doc, clip_id, action)
        self.assertEqual(doc, before)

    def test_marker_destination_on_earlier_parent_uses_destination_clock(self):
        doc = document()
        target = copy.deepcopy(node(doc, 100))
        target["id"] = 200
        target["start"] = 40219200000
        for _, child in project.objects(target):
            if child.get("id") in (10, 3, 4, 50):
                child["id"] += 1000
        project.scene_tracks(doc)[0][0]["medias"].append(target)
        before = copy.deepcopy(doc)
        actual = hotspots.edit_hotspot(doc, 200, "marker", marker_owner=100, marker_time="178/15")
        expected = copy.deepcopy(doc)
        node(expected, 200)["attributes"]["hotspot"] = {
            **default_hotspot(),
            "action": 3,
            "markerParametricId": 100,
            "markerTime": 8373120000,
            "lastMarkerGlobalTime": 4186560000,
        }
        self.assertEqual(actual, expected)
        self.assertEqual(doc, before)

    def test_cli_preserves_source_and_existing_candidate_bytes(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, output = root / "source.json", root / "candidate.json"
            source.write_bytes(project.encode_document(document()))
            before = source.read_bytes()
            command = [
                "set",
                str(source),
                "--clip-id",
                "100",
                "--action",
                "marker",
                "--marker-owner",
                "100",
                "--marker-time",
                "178/15",
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
                self.assertEqual(report["hotspot"]["lastMarkerGlobalTime"], 4186560000)
            candidate = output.read_bytes()
            with patch("sys.stderr", io.StringIO()):
                self.assertEqual(
                    hotspots.main(
                        ["remove", str(source), "--clip-id", "100", "--output", str(output)]
                    ),
                    1,
                )
            self.assertEqual(output.read_bytes(), candidate)
            self.assertEqual(source.read_bytes(), before)
