from __future__ import annotations

import copy
from pathlib import Path
import tempfile
import unittest

from test_project import document
import project


def native_document():
    doc = document()
    doc.update(
        version="10.0",
        authoringClientName=dict(name="Camtasia", platform="Mac", version="2026.2.4"),
    )
    node = project.scene_tracks(doc)[0][0]["medias"][0]
    node["parameters"] = {
        name: dict(
            type="double",
            defaultValue=0.0,
            keyframes=[dict(time=100, endTime=100, duration=0, value=value)],
        )
        for name, value in [("translation0", 128), ("translation1", 72)]
    }
    return doc


class GeometryPointWarningTests(unittest.TestCase):
    def test_warns_each_native_translation_parameter_without_mutation_or_rejection(self):
        doc = native_document()
        frozen = copy.deepcopy(doc)
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "media").mkdir()
            (root / "media/source.mp4").write_bytes(b"fixed unused media")
            report = project.validate(doc, root)
        self.assertTrue(report["ok"], report["errors"])
        self.assertEqual(len(report["warnings"]), 2)
        self.assertTrue(
            all(
                "positive-duration animation intervals" in warning for warning in report["warnings"]
            )
        )
        self.assertIn("/parameters/translation0:", report["warnings"][0])
        self.assertEqual(doc, frozen)

    def test_mixed_and_marker_curves_warn_but_motion_path_and_cursor_points_do_not(self):
        doc = native_document()
        node = project.scene_tracks(doc)[0][0]["medias"][0]
        node["animationTracks"] = dict(visual=[dict(endTime=300, duration=100)])
        for parameter in node["parameters"].values():
            parameter["keyframes"].append(dict(time=200, endTime=300, duration=100, value=-128))
        self.assertEqual(len(project.native_geometry_warnings(doc)), 2)
        node["effects"] = [
            dict(
                effectName="MediaPath",
                parameters=dict(
                    mediaLocation=dict(
                        type="point",
                        keyframes=[dict(time=100, endTime=100, duration=0, value=[128, 72, 0])],
                    )
                ),
            )
        ]
        node["parameters"] = dict(
            cursorScale=dict(
                type="double",
                defaultValue=1,
                keyframes=[dict(time=100, endTime=100, duration=0, value=4)],
            )
        )
        self.assertEqual(project.native_geometry_warnings(doc), [])

    def test_scope_does_not_claim_other_builds_formats_owners_or_properties(self):
        for changes in [
            dict(version="9.0"),
            dict(authoringClientName=dict(name="Camtasia", platform="Mac", version="2025.0.3")),
            dict(authoringClientName=dict(name="Camtasia", platform="Windows", version="2026.2.4")),
        ]:
            doc = native_document()
            doc.update(changes)
            self.assertEqual(project.native_geometry_warnings(doc), [])
        for kind in ["IMFile", "Group", "ScreenVMFile", "Callout"]:
            doc = native_document()
            project.scene_tracks(doc)[0][0]["medias"][0]["_type"] = kind
            self.assertEqual(project.native_geometry_warnings(doc), [])
        doc = native_document()
        node = project.scene_tracks(doc)[0][0]["medias"][0]
        node["parameters"] = dict(rotation2=node["parameters"]["translation0"])
        self.assertEqual(project.native_geometry_warnings(doc), [])

    def test_positive_intervals_and_malformed_point_shapes_do_not_match_observed_shape(self):
        for frame in [
            dict(time=100, endTime=200, duration=100, value=128),
            dict(time=100, endTime=100, duration=False, value=128),
            dict(time=100, endTime=100, duration=0.0, value=128),
            dict(time=100, endTime=200, duration=0, value=128),
            dict(endTime=100, duration=0, value=128),
            dict(time=100, endTime=100, duration=0, value=False),
            dict(time=100, endTime=100, duration=0, value={"unknown": 128}),
            dict(time=100, endTime=100, duration=0),
        ]:
            doc = native_document()
            node = project.scene_tracks(doc)[0][0]["medias"][0]
            node["parameters"] = dict(
                translation0=dict(type="double", defaultValue=0, keyframes=[frame])
            )
            self.assertEqual(project.native_geometry_warnings(doc), [])


if __name__ == "__main__":
    unittest.main()
