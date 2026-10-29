from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_quizzes import document
import project
import transitions


def fixture():
    doc = document()
    track = project.scene_tracks(doc)[0][0]
    first = track["medias"][0]
    first.update(start=0, duration=4000, mediaStart=2000, mediaDuration=6000, scalar="2/3")
    second = copy.deepcopy(first)
    second.update(id=4, start=4000, mediaStart=8000)
    track["medias"].append(second)
    return doc


def track(doc):
    return project.scene_tracks(doc)[0][0]


def spec(**changes):
    return dict(schema_version=1, **changes)


class TransitionTests(unittest.TestCase):
    def test_shared_constructor_uses_half_displayed_duration_and_preserves_everything_else(self):
        doc = fixture()
        result = transitions.add_fade(doc, 3, 4, "3/2")
        expected = copy.deepcopy(doc)
        track(expected)["transitions"] = [
            dict(
                name="Fade",
                duration=750,
                leftMedia=3,
                rightMedia=4,
                attributes=dict(
                    bypass=False,
                    reverse=False,
                    trivial=False,
                    useAudioPreRoll=True,
                    useVisualPreRoll=True,
                ),
            )
        ]
        self.assertEqual(result, expected)
        self.assertEqual(doc, fixture())

    def test_single_edges_use_full_duration_and_preserve_omission(self):
        result = transitions.add_fade(fixture(), None, 3, 1)
        result = transitions.add_fade(result, 4, None, "3/2")
        first, last = track(result)["transitions"]
        self.assertEqual(first["duration"], 1000)
        self.assertEqual(last["duration"], 1500)
        self.assertNotIn("leftMedia", first)
        self.assertNotIn("rightMedia", last)
        self.assertEqual(transitions.window(track(result), first), (0, 1000))
        self.assertEqual(transitions.window(track(result), last), (6500, 8000))

    def test_native_duration_bypass_reverse_and_independent_preroll_patches(self):
        doc = transitions.add_fade(fixture(), 3, 4, 1)
        result = transitions.set_transition(
            doc,
            3,
            4,
            spec(duration=2, attributes=dict(bypass=True, reverse=True, useAudioPreRoll=False)),
        )
        expected = copy.deepcopy(doc)
        value = track(expected)["transitions"][0]
        value["duration"] = 1000
        value["attributes"].update(bypass=True, reverse=True, useAudioPreRoll=False)
        self.assertEqual(result, expected)
        self.assertTrue(value["attributes"]["useVisualPreRoll"])
        self.assertEqual(transitions.set_transition(result, 3, 4, spec(duration=2)), result)

    def test_existing_preset_numeric_controls_keep_kinds_and_opaque_payload(self):
        doc = transitions.add_fade(fixture(), 3, 4, 1)
        value = track(doc)["transitions"][0]
        value.update(name="ExistingNativePreset", opaque=dict(future=[1, "日本語"]))
        value["attributes"].update(Angle=0.5, Count=3, resource="untouched")
        result = transitions.set_transition(doc, 3, 4, spec(attributes=dict(Angle="3/4", Count=4)))
        self.assertEqual(track(result)["transitions"][0]["attributes"]["Angle"], 0.75)
        self.assertIs(type(track(result)["transitions"][0]["attributes"]["Angle"]), float)
        self.assertIs(type(track(result)["transitions"][0]["attributes"]["Count"]), int)
        self.assertEqual(track(result)["transitions"][0]["opaque"], value["opaque"])
        self.assertEqual(track(result)["medias"], track(doc)["medias"])
        self.assertEqual(result["sourceBin"], doc["sourceBin"])

    def test_remove_keeps_other_transition_and_omits_empty_array_like_native(self):
        doc = transitions.add_fade(fixture(), None, 3, 1)
        both = transitions.add_fade(doc, 3, 4, 1)
        self.assertEqual(transitions.remove_transition(both, 3, 4), doc)
        empty = transitions.remove_transition(doc, None, 3)
        self.assertEqual(empty, fixture())
        self.assertEqual(transitions.remove_transition(empty, None, 3), empty)
        self.assertEqual(both["sourceBin"], empty["sourceBin"])

    def test_nonpositive_fractional_or_oversize_extents_refuse_unchanged_input(self):
        doc = fixture()
        for duration in [0, -1, "1/3000", 9, True, "NaN"]:
            with self.subTest(duration=duration), self.assertRaises(ValueError):
                transitions.add_fade(doc, 3, 4, duration)
        self.assertEqual(doc, fixture())
        self.assertEqual(
            track(transitions.add_fade(doc, 3, 4, 8))["transitions"][0]["duration"], 4000
        )

    def test_overlapping_transition_or_clip_windows_and_gapped_join_refuse(self):
        doc = transitions.add_fade(fixture(), None, 3, 3)
        with self.assertRaisesRegex(ValueError, "overlapping transitions"):
            transitions.add_fade(doc, 3, 4, 4)
        gap = fixture()
        track(gap)["medias"][1]["start"] = 5000
        with self.assertRaisesRegex(ValueError, "adjacent"):
            transitions.add_fade(gap, 3, 4, 1)
        overlap = fixture()
        track(overlap)["medias"].append(dict(id=6, _type="Callout", start=3500, duration=1000))
        with self.assertRaisesRegex(ValueError, "overlapping clips"):
            transitions.add_fade(overlap, 3, 4, 1)

    def test_unique_root_visual_selector_refuses_children_audio_duplicates_and_cross_tracks(self):
        doc = fixture()
        for left, right in [(None, None), (True, 4), (-1, 4), (3, 3), (30, 4)]:
            with self.assertRaises(ValueError):
                transitions.add_fade(doc, left, right, 1)
        tracks = project.scene_tracks(doc)[0]
        tracks.append(dict(medias=[track(doc)["medias"].pop()]))
        with self.assertRaisesRegex(ValueError, "same root track"):
            transitions.add_fade(doc, 3, 4, 1)
        tracks[1]["medias"].append(copy.deepcopy(tracks[1]["medias"][0]))
        with self.assertRaisesRegex(ValueError, "unique root"):
            transitions.add_fade(doc, None, 4, 1)
        tracks[1]["medias"] = [dict(id=9, _type="AMFile", start=0, duration=4000)]
        with self.assertRaisesRegex(ValueError, "visual"):
            transitions.add_fade(doc, None, 9, 1)

    def test_duplicate_and_null_transition_endpoints_require_repair(self):
        doc = transitions.add_fade(fixture(), 3, 4, 1)
        with self.assertRaisesRegex(ValueError, "existing transition"):
            transitions.add_fade(doc, 3, 4, 1)
        track(doc)["transitions"].append(copy.deepcopy(track(doc)["transitions"][0]))
        with self.assertRaisesRegex(ValueError, "duplicate"):
            transitions.remove_transition(doc, 3, 4)
        track(doc)["transitions"][0]["rightMedia"] = None
        with self.assertRaisesRegex(ValueError, "null"):
            transitions.remove_transition(doc, 3, 4)

    def test_invalid_specs_and_unknown_fields_refuse_without_mutation(self):
        doc = transitions.add_fade(fixture(), 3, 4, 1)
        before = copy.deepcopy(doc)
        for value in [
            {},
            spec(),
            dict(schema_version=True, duration=1),
            dict(schema_version=2, duration=1),
            spec(unknown=1),
            spec(attributes={}),
            spec(attributes=dict(bypass=1)),
            spec(attributes=dict(newControl=0)),
            spec(attributes=dict(bypass={})),
            spec(attributes=dict(reverse="false")),
        ]:
            with self.subTest(spec=value), self.assertRaises(ValueError):
                transitions.set_transition(doc, 3, 4, value)
            self.assertEqual(doc, before)
        doc["version"] = "9.0"
        with self.assertRaisesRegex(ValueError, "2026.2.4"):
            transitions.remove_transition(doc, 3, 4)

    def test_cli_exclusive_staging_inspection_set_removal_and_unchanged_source(self):
        with tempfile.TemporaryDirectory() as temporary:
            folder = Path(temporary)
            source, output = folder / "source.json", folder / "candidate.json"
            raw = project.encode_document(fixture())
            source.write_bytes(raw)
            args = [
                "add-fade",
                str(source),
                "--left-id",
                "3",
                "--right-id",
                "4",
                "--duration",
                "1",
                "--output",
                str(output),
            ]
            for written in [True, False]:
                stream = io.StringIO()
                with patch("sys.stdout", stream):
                    self.assertEqual(transitions.main(args), 0)
                report = json.loads(stream.getvalue())
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
                self.assertEqual(report["owner"], "camtasia-transitions")
            self.assertEqual(source.read_bytes(), raw)
            stream = io.StringIO()
            with patch("sys.stdout", stream):
                self.assertEqual(transitions.main(["inspect", str(output)]), 0)
            self.assertEqual(len(json.loads(stream.getvalue())["transitions"]), 1)
            settings = folder / "spec.json"
            settings.write_text(json.dumps(spec(duration=2)))
            edited = folder / "edited.json"
            with patch("sys.stdout", io.StringIO()):
                self.assertEqual(
                    transitions.main(
                        [
                            "set",
                            str(output),
                            "--left-id",
                            "3",
                            "--right-id",
                            "4",
                            "--spec",
                            str(settings),
                            "--output",
                            str(edited),
                        ]
                    ),
                    0,
                )
                self.assertEqual(
                    transitions.main(
                        [
                            "remove",
                            str(edited),
                            "--left-id",
                            "3",
                            "--right-id",
                            "4",
                            "--output",
                            str(folder / "removed.json"),
                        ]
                    ),
                    0,
                )
            self.assertEqual(project.load(folder / "removed.json")[0], fixture())
            output.write_text("occupied")
            with patch("sys.stderr", io.StringIO()):
                self.assertEqual(transitions.main(args), 1)
            self.assertEqual(output.read_text(), "occupied")
            with patch("sys.stderr", io.StringIO()):
                self.assertEqual(transitions.main([*args[:-1], str(source)]), 1)
            self.assertEqual(source.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
