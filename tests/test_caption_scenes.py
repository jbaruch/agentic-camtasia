from __future__ import annotations

import copy
from contextlib import redirect_stdout
import io
import json
from pathlib import Path
import tempfile
import unittest

from test_captions import audio, fixture, root
from test_caption_groups import one_group
from test_caption_recording_holds import held_recording
import captions
import project

R = 705600000


def scenes(form="linked"):
    doc = fixture(form)
    owner = root(doc)
    nodes = [owner, owner["video"], owner["audio"]] if owner["_type"] == "UnifiedMedia" else [owner]
    for n in nodes:
        n.update(duration=4 * R, mediaDuration=4 * R)
    scene = doc["timeline"]["sceneTrack"]["scenes"][0]
    scene["csml"]["tracks"][0]["trackIndex"] = 0
    scene["csml"]["tracks"][0]["metadata"] = {"local": "retain"}
    second = copy.deepcopy(scene)
    for _, n in project.objects(second):
        if type(n.get("id")) is int:
            n["id"] += 10
    doc["timeline"]["sceneTrack"]["scenes"].append(second)
    doc["timeline"]["trackAttributes"] = [
        dict(
            ident="Speech",
            audioMuted=False,
            videoHidden=False,
            magnetic=True,
            matte=0,
            solo=False,
            metadata={"IsLocked": "True", "trackHeight": "96", "opaque": ["keep"]},
        )
    ]
    return doc


def groups(doc):
    return project.scene_tracks(doc)[0][0]["medias"]


class CaptionSceneTests(unittest.TestCase):
    def test_global_cue_and_word_maps_follow_explicit_scene_placement(self):
        doc = scenes()
        before = copy.deepcopy(doc)
        candidate = captions.sequence_scenes(doc, dict(schema_version=1, durations=[6, 4]))
        self.assertEqual(len(project.scene_tracks(candidate)), 1)
        self.assertEqual(
            [(g["start"], g["duration"]) for g in groups(candidate)], [(0, 6 * R), (6 * R, 4 * R)]
        )
        self.assertEqual(
            [r["timelineStartSeconds"] for r in captions.map_captions(candidate, 13)["closed"]],
            ["6"],
        )
        self.assertEqual(
            captions.map_captions(candidate, 13)["words"][0]["timelineStartSeconds"], "301/50"
        )
        self.assertEqual(candidate["sourceBin"], before["sourceBin"])
        self.assertEqual(
            candidate["timeline"]["captionAttributes"], before["timeline"]["captionAttributes"]
        )
        self.assertEqual(doc, before)

    def test_complete_scene_clips_sources_unknown_fields_and_linked_clocks_survive(self):
        for form in ["linked", "audio", "imported"]:
            with self.subTest(form=form):
                doc = scenes(form)
                candidate = captions.sequence_scenes(doc, dict(schema_version=1, durations=[4, 4]))
                for source, group in zip(project.scene_tracks(doc), groups(candidate)):
                    self.assertEqual(group["tracks"][0]["medias"], source[0]["medias"])
                self.assertEqual(candidate["future"], doc["future"])
                self.assertEqual(candidate["metadata"], doc["metadata"])
                self.assertEqual(candidate["timeline"]["parameters"], doc["timeline"]["parameters"])
                self.assertEqual(candidate["sourceBin"], doc["sourceBin"])

    def test_nested_groups_properties_and_held_stitches_keep_their_internal_clocks(self):
        for make in [one_group, held_recording]:
            with self.subTest(make=make):
                doc = make()
                scene = doc["timeline"]["sceneTrack"]["scenes"][0]
                lane = scene["csml"]["tracks"][0]
                lane["trackIndex"] = 0
                owner = lane["medias"][0]
                owner["start"] = 0
                if owner["_type"] == "Group":
                    owner["attributes"]["assetProperties"] = [
                        dict(type=2, name="Media", objects=[3])
                    ]
                second = copy.deepcopy(scene)
                for _, n in project.objects(second):
                    if type(n.get("id")) is int:
                        n["id"] += 1000
                    for prop in n.get("attributes", {}).get("assetProperties", []):
                        prop["objects"] = [i + 1000 for i in prop["objects"]]
                doc["timeline"]["sceneTrack"]["scenes"].append(second)
                doc["timeline"]["trackAttributes"] = [
                    dict(
                        ident="",
                        audioMuted=False,
                        videoHidden=False,
                        magnetic=False,
                        matte=0,
                        solo=False,
                        metadata={"IsLocked": "False"},
                    )
                ]
                before = copy.deepcopy(doc)
                candidate = captions.sequence_scenes(doc, dict(schema_version=1, durations=[8, 8]))
                self.assertEqual(groups(candidate)[0]["tracks"][0]["medias"], lane["medias"])
                self.assertEqual(
                    groups(candidate)[1]["tracks"][0]["medias"],
                    second["csml"]["tracks"][0]["medias"],
                )
                self.assertEqual(
                    captions.map_captions(candidate, 1003)["words"][0]["timelineStartSeconds"],
                    "401/50",
                )
                self.assertEqual(candidate["sourceBin"], doc["sourceBin"])
                self.assertEqual(doc, before)

    def test_new_ids_are_unique_and_do_not_rebind_existing_clip_or_property_ids(self):
        doc = scenes()
        doc["metadata"]["opaqueObject"] = {"id": 1000}
        candidate = captions.sequence_scenes(doc, dict(schema_version=1, durations=[4, 4]))
        self.assertEqual([g["id"] for g in groups(candidate)], [1001, 1002])
        ids = [
            n["id"] for _, n in project.objects(candidate) if n.get("_type") in project.KNOWN_CLIPS
        ]
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(groups(candidate)[1]["tracks"][0]["medias"][0]["audio"]["id"], 15)

    def test_lane_controls_and_metadata_move_inside_each_scene_without_muting_the_root(self):
        doc = scenes()
        flags = doc["timeline"]["trackAttributes"][0]
        flags.update(audioMuted=True, videoHidden=True, solo=True, matte=2)
        candidate = captions.sequence_scenes(doc, dict(schema_version=1, durations=[4, 4]))
        for group in groups(candidate):
            track = group["tracks"][0]
            for key in ["ident", "audioMuted", "videoHidden", "magnetic", "matte", "solo"]:
                self.assertEqual(track[key], flags[key])
            self.assertEqual(track["metadata"], {**flags["metadata"], "local": "retain"})
        neutral = candidate["timeline"]["trackAttributes"][0]
        self.assertFalse(neutral["audioMuted"])
        self.assertFalse(neutral["videoHidden"])
        self.assertFalse(neutral["solo"])
        self.assertEqual(neutral["matte"], 0)
        flags["metadata"]["opaque"].append("changed")
        self.assertEqual(groups(candidate)[0]["tracks"][0]["metadata"]["opaque"], ["keep"])

    def test_empty_and_trailing_blank_scenes_keep_their_explicit_duration(self):
        doc = scenes()
        doc["timeline"]["sceneTrack"]["scenes"][1]["csml"]["tracks"] = []
        candidate = captions.sequence_scenes(doc, dict(schema_version=1, durations=[6, 3]))
        self.assertEqual(
            [(g["start"], g["duration"]) for g in groups(candidate)], [(0, 6 * R), (6 * R, 3 * R)]
        )
        self.assertEqual(groups(candidate)[1]["tracks"][0]["medias"], [])
        self.assertEqual(groups(candidate)[1]["tracks"][0]["ident"], "Speech")

    def test_selected_child_edits_use_global_seconds_after_sequencing(self):
        doc = captions.sequence_scenes(scenes(), dict(schema_version=1, durations=[4, 4]))
        before = copy.deepcopy(doc)
        edited = captions.set_cues(
            doc,
            13,
            dict(
                schema_version=1, clock="timeline", cues=[dict(start=5, end=7, text="SECOND SCENE")]
            ),
        )
        rows = captions.map_captions(edited, 13)["closed"]
        self.assertEqual(
            [(r["value"], r["timelineStartSeconds"], r["timelineEndSeconds"]) for r in rows],
            [("", "4", "5"), ("SECOND SCENE", "5", "7"), ("", "7", "8")],
        )
        self.assertEqual(groups(edited)[0], groups(before)[0])
        self.assertEqual(edited["sourceBin"], before["sourceBin"])
        self.assertEqual(doc, before)

    def test_scene_dimensions_preserve_native_numeric_types_and_reject_invalid_values(self):
        doc = scenes()
        doc["width"] = 1280.0
        candidate = captions.sequence_scenes(doc, dict(schema_version=1, durations=[4, 4]))
        self.assertIs(type(groups(candidate)[0]["attributes"]["widthAttr"]), float)
        self.assertEqual(groups(candidate)[0]["attributes"]["widthAttr"], 1280.0)
        for value in [0, -1, True, "1280", None]:
            invalid = scenes()
            invalid["width"] = value
            with self.subTest(value=value), self.assertRaises(ValueError):
                captions.sequence_scenes(invalid, dict(schema_version=1, durations=[4, 4]))

    def test_exact_frame_grid_and_matching_positive_duration_specs_are_required(self):
        for durations in [[], [4], [4, 4, 4], [0, 4], [-1, 4], [3, 4], ["1/7", 4], {}, True]:
            doc = scenes()
            before = copy.deepcopy(doc)
            with self.subTest(durations=durations), self.assertRaises(ValueError):
                captions.sequence_scenes(doc, dict(schema_version=1, durations=durations))
            self.assertEqual(doc, before)
        candidate = captions.sequence_scenes(
            scenes(), dict(schema_version=1, durations=["121/30", 4])
        )
        self.assertEqual(groups(candidate)[1]["start"], 121 * R // 30)

    def test_unmeasured_scene_fields_and_interactive_destinations_refuse_without_loss(self):
        for kind in [
            "scene-title",
            "scene-duration",
            "scene-track",
            "csml",
            "marker",
            "quiz",
            "hotspot",
        ]:
            doc = scenes()
            if kind == "scene-title":
                doc["timeline"]["sceneTrack"]["scenes"][0]["title"] = "Unknown"
            elif kind == "scene-duration":
                doc["timeline"]["sceneTrack"]["scenes"][0]["duration"] = 4 * R
            elif kind == "scene-track":
                doc["timeline"]["sceneTrack"]["opaque"] = True
            elif kind == "csml":
                doc["timeline"]["sceneTrack"]["scenes"][0]["csml"]["opaque"] = True
            elif kind == "hotspot":
                root(doc).setdefault("attributes", {})["hotspot"] = {}
            else:
                audio(doc)["parameters"]["toc" if kind == "marker" else "quiz"] = {}
            before = copy.deepcopy(doc)
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                captions.sequence_scenes(doc, dict(schema_version=1, durations=[4, 4]))
            self.assertEqual(doc, before)

    def test_conflicting_flags_metadata_indices_and_duplicate_ids_refuse(self):
        for kind in [
            "metadata",
            "flags",
            "index",
            "duplicate-index",
            "clip-id",
            "global-structure",
        ]:
            doc = scenes()
            track = project.scene_tracks(doc)[0][0]
            if kind == "metadata":
                track["metadata"]["IsLocked"] = "False"
            elif kind == "flags":
                track["audioMuted"] = True
            elif kind == "index":
                track["trackIndex"] = 2
            elif kind == "duplicate-index":
                project.scene_tracks(doc)[0].append(dict(trackIndex=0, medias=[]))
            elif kind == "global-structure":
                doc["timeline"]["trackAttributes"][0]["parameters"] = {"opaque": ["retain"]}
            else:
                project.scene_tracks(doc)[1][0]["medias"][0]["id"] = 3
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                captions.sequence_scenes(doc, dict(schema_version=1, durations=[4, 4]))

    def test_sequencing_does_not_hide_an_existing_scene_lane_collision(self):
        doc = scenes()
        duplicate = copy.deepcopy(root(doc))
        duplicate["id"] = 30
        duplicate["video"]["id"] = 31
        duplicate["audio"]["id"] = 32
        project.scene_tracks(doc)[0][0]["medias"].append(duplicate)
        before = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "scene lane collisions"):
            captions.sequence_scenes(doc, dict(schema_version=1, durations=[4, 4]))
        self.assertEqual(doc, before)

    def test_native_scene_loss_guard_is_build_bound_and_clears_after_sequencing(self):
        doc = scenes()
        self.assertTrue(any("drops later scenes" in p for p in project.native_hazards(doc)))
        candidate = captions.sequence_scenes(doc, dict(schema_version=1, durations=[4, 4]))
        self.assertFalse(project.native_hazards(candidate))
        doc["authoringClientName"]["version"] = "2025.0.3"
        self.assertFalse(any("drops later scenes" in p for p in project.native_hazards(doc)))
        with self.assertRaises(ValueError):
            captions.sequence_scenes(doc, dict(schema_version=1, durations=[4, 4]))

    def test_cli_stages_an_exclusive_repeatable_candidate_and_keeps_original_bytes(self):
        with tempfile.TemporaryDirectory() as temporary:
            root_dir = Path(temporary)
            source = root_dir / "input.tscproj"
            spec = root_dir / "spec.json"
            output = root_dir / "candidate.json"
            raw = project.encode_document(scenes())
            source.write_bytes(raw)
            spec.write_text(json.dumps(dict(schema_version=1, durations=[4, 4])))
            for written in [True, False]:
                stream = io.StringIO()
                with redirect_stdout(stream):
                    status = captions.main(
                        [
                            "sequence-scenes",
                            str(source),
                            "--spec",
                            str(spec),
                            "--output",
                            str(output),
                        ]
                    )
                self.assertEqual(status, 0)
                self.assertEqual(json.loads(stream.getvalue())["written"], written)
                self.assertEqual(source.read_bytes(), raw)
            candidate = project.load(output)[0]
            self.assertEqual(
                captions.map_captions(candidate, 13)["closed"][0]["timelineStartTicks"], 4 * R
            )


if __name__ == "__main__":
    unittest.main()
