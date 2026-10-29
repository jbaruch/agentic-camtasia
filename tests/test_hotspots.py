from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/camtasia-project/scripts"))
import hotspots  # noqa: E402
import project  # noqa: E402


def document() -> dict:
    video = {
        "id": 41,
        "_type": "VMFile",
        "src": 1,
        "start": 0,
        "duration": 8000,
        "parameters": {
            "toc": {
                "type": "string",
                "keyframes": [{"time": 2000, "endTime": 2000, "duration": 0, "value": "Same"}],
            }
        },
        "attributes": {"futureAttribute": ["retain", 1]},
        "effects": [{"effectName": "unfamiliar", "opaque": {"x": True}}],
    }
    linked = {
        "id": 40,
        "_type": "UnifiedMedia",
        "start": 1000,
        "duration": 4000,
        "video": video,
        "audio": {"id": 42, "_type": "AMFile", "src": 1, "attributes": {"gain": 0.7}},
    }
    return {
        "version": "10.0",
        "authoringClientName": {"name": "Camtasia", "platform": "Mac", "version": "2026.2.4"},
        "editRate": 1000,
        "sourceBin": [{"id": 1, "src": "missing-is-not-read.mp4", "opaque": [1, 2]}],
        "timeline": {
            "id": 2,
            "parameters": {
                "toc": {
                    "type": "string",
                    "keyframes": [
                        {"time": 4000, "endTime": 4000, "duration": 0, "value": "Same"},
                        {"time": 6000, "endTime": 6000, "duration": 0, "value": "Last →"},
                    ],
                }
            },
            "sceneTrack": {"scenes": [{"csml": {"tracks": [{"medias": [linked]}]}}]},
        },
        "opaque": {"nested": [False, None, "日本語"]},
    }


def video(doc: dict) -> dict:
    return doc["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"][0]["video"]


def hotspot(doc: dict) -> dict:
    return video(doc)["attributes"]["hotspot"]


class HotspotTests(unittest.TestCase):
    def setUp(self) -> None:
        self.doc = document()

    def test_native_default_constructor_only_changes_visual_hotspot(self) -> None:
        before = copy.deepcopy(self.doc)
        result = hotspots.edit_hotspot(self.doc, 40, "continue")
        self.assertEqual(
            hotspot(result),
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
        self.assertEqual(self.doc, before)
        video(result)["attributes"].pop("hotspot")
        self.assertEqual(result, before)

    def test_linked_wrapper_and_video_child_select_same_target(self) -> None:
        wrapper = hotspots.edit_hotspot(self.doc, 40, "time", time="13/4", pause=False)
        child = hotspots.edit_hotspot(self.doc, 41, "time", time="13/4", pause=False)
        self.assertEqual(wrapper, child)
        self.assertEqual(hotspot(child)["gotoTime"], 3250)
        self.assertEqual(hotspot(child)["action"], 1)
        self.assertFalse(hotspot(child)["pauseAtEnd"])

    def test_observed_visual_types_keep_source_hold_geometry_and_children(self) -> None:
        for kind in ("IMFile", "Callout", "ScreenVMFile", "Group"):
            doc = document()
            target = {
                "id": 50,
                "_type": kind,
                "attributes": {"ident": "visual"},
                "start": 1000,
                "duration": 5000,
                "mediaDuration": 1,
                "parameters": {"scale0": 0.5, "translation1": -25},
                "opaque": ["keep me"],
            }
            if kind == "Group":
                target["tracks"] = [{"medias": [video(doc)]}]
            elif kind == "Callout":
                target["def"] = {"kind": "remix", "text": "café → 日本語"}
            else:
                target["src"] = 1
            doc["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"] = [target]
            before = copy.deepcopy(doc)
            with self.subTest(kind=kind):
                result = hotspots.edit_hotspot(doc, 50, "time", time=4)
                changed = project.scene_tracks(result)[0][0]["medias"][0]
                self.assertEqual(changed["attributes"].pop("hotspot")["gotoTime"], 4000)
                self.assertEqual(result, before)
                self.assertEqual(doc, before)

    def test_group_hotspot_does_not_replace_or_remove_child_hotspot(self) -> None:
        child = video(self.doc)
        child["attributes"]["hotspot"] = {"action": 2, "url": "https://example.test/child"}
        group = {"id": 50, "_type": "Group", "attributes": {}, "tracks": [{"medias": [child]}]}
        self.doc["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"] = [group]
        before = copy.deepcopy(self.doc)
        result = hotspots.edit_hotspot(self.doc, 50, "time", time=4)
        result = hotspots.edit_hotspot(result, 50, "remove")
        self.assertEqual(result, before)

    def test_unobserved_visual_types_are_preserved_without_constructor_claims(self) -> None:
        for kind in ("AMFile", "Caption", "ScreenIMFile", "StitchedMedia", "PlaceholderMedia"):
            doc = document()
            target = {"id": 50, "_type": kind, "attributes": {"future": True}}
            doc["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0]["medias"] = [target]
            before = copy.deepcopy(doc)
            with self.subTest(kind=kind), self.assertRaisesRegex(ValueError, "verified"):
                hotspots.edit_hotspot(doc, 50, "continue")
            self.assertEqual(doc, before)

    def test_action_changes_preserve_inactive_fields_and_unknown_payload(self) -> None:
        existing = {
            "action": 3,
            "gotoTime": 7000,
            "pauseAtEnd": False,
            "url": "https://example.test/old",
            "openURLInNewWindow": False,
            "markerParametricId": 2,
            "markerTime": 4000,
            "lastMarkerGlobalTime": 4000,
            "future": {"nested": ["keep", True]},
        }
        video(self.doc)["attributes"]["hotspot"] = existing
        candidate = hotspots.edit_hotspot(self.doc, 40, "url", url="https://example.test/é?q=1&b=2")
        expected = {**existing, "action": 2, "url": "https://example.test/é?q=1&b=2"}
        self.assertEqual(hotspot(candidate), expected)
        self.assertEqual(hotspot(self.doc), existing)
        candidate = hotspots.edit_hotspot(candidate, 40, "continue")
        self.assertEqual(hotspot(candidate), {**expected, "action": 0, "pauseAtEnd": True})

    def test_url_window_choice_and_pause_are_independent(self) -> None:
        result = hotspots.edit_hotspot(
            self.doc,
            40,
            "url",
            url="http://127.0.0.1:48766/destination",
            new_window=False,
            pause=False,
        )
        self.assertEqual(hotspot(result)["action"], 2)
        self.assertFalse(hotspot(result)["openURLInNewWindow"])
        self.assertFalse(hotspot(result)["pauseAtEnd"])

    def test_marker_inventory_retains_logical_linked_owner_and_unicode(self) -> None:
        points = hotspots.markers(self.doc)
        self.assertEqual(
            [(p["ownerId"], p["time"]) for p in points], [(2, 4000), (2, 6000), (40, 2000)]
        )
        self.assertEqual(points[-1]["parameterOwnerId"], 41)
        self.assertTrue(points[-1]["path"].endswith("/video/parameters/toc/keyframes/0"))
        self.assertEqual(points[1]["label"], "Last →")

    def test_timeline_marker_uses_owner_and_point_not_label_or_ordinal(self) -> None:
        candidate = hotspots.edit_hotspot(self.doc, 40, "marker", marker_owner=2, marker_time=6)
        self.assertEqual(
            {
                k: hotspot(candidate)[k]
                for k in ("action", "markerParametricId", "markerTime", "lastMarkerGlobalTime")
            },
            {
                "action": 3,
                "markerParametricId": 2,
                "markerTime": 6000,
                "lastMarkerGlobalTime": 6000,
            },
        )

    def test_media_marker_requires_explicit_global_time_without_guessing_trim(self) -> None:
        with self.assertRaisesRegex(ValueError, "global-time"):
            hotspots.edit_hotspot(self.doc, 40, "marker", marker_owner=40, marker_time=2)
        candidate = hotspots.edit_hotspot(
            self.doc, 40, "marker", marker_owner=40, marker_time=2, marker_global_time="7/2"
        )
        self.assertEqual(hotspot(candidate)["markerParametricId"], 40)
        self.assertEqual(hotspot(candidate)["markerTime"], 2000)
        self.assertEqual(hotspot(candidate)["lastMarkerGlobalTime"], 3500)
        with self.assertRaisesRegex(ValueError, "missing or ambiguous"):
            hotspots.edit_hotspot(
                self.doc, 40, "marker", marker_owner=41, marker_time=2, marker_global_time=2
            )

    def test_marker_mismatch_duplicate_and_conflicting_cache_are_rejected(self) -> None:
        cases: list[dict[str, Any]] = [
            {"marker_owner": 99, "marker_time": 4},
            {"marker_owner": 2, "marker_time": 5},
            {"marker_owner": 2, "marker_time": 4, "marker_global_time": 5},
        ]
        for options in cases:
            with self.subTest(options=options), self.assertRaises(ValueError):
                hotspots.edit_hotspot(self.doc, 40, "marker", **options)
        frames = self.doc["timeline"]["parameters"]["toc"]["keyframes"]
        frames.append(copy.deepcopy(frames[0]))
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            hotspots.edit_hotspot(self.doc, 40, "marker", marker_owner=2, marker_time=4)

    def test_nested_and_second_scene_clips_are_selected_by_id(self) -> None:
        linked = self.doc["timeline"]["sceneTrack"]["scenes"][0]["csml"]["tracks"][0][
            "medias"
        ].pop()
        self.doc["timeline"]["sceneTrack"]["scenes"].append(
            {
                "csml": {
                    "tracks": [
                        {"medias": [{"id": 50, "_type": "Group", "tracks": [{"medias": [linked]}]}]}
                    ]
                }
            }
        )
        candidate = hotspots.edit_hotspot(self.doc, 40, "time", time=4)
        nested = candidate["timeline"]["sceneTrack"]["scenes"][1]["csml"]["tracks"][0]["medias"][0][
            "tracks"
        ][0]["medias"][0]
        self.assertEqual(nested["video"]["attributes"]["hotspot"]["gotoTime"], 4000)

    def test_remove_is_idempotent_and_preserves_every_other_value(self) -> None:
        candidate = hotspots.edit_hotspot(self.doc, 40, "time", time=4)
        removed = hotspots.edit_hotspot(candidate, 41, "remove")
        self.assertEqual(removed, self.doc)
        self.assertEqual(hotspots.edit_hotspot(removed, 40, "remove"), self.doc)

    def test_no_target_is_silently_chosen_for_wrong_or_ambiguous_id(self) -> None:
        bad_ids: list[Any] = [None, True, 99, 42]
        for cid in bad_ids:
            with self.subTest(cid=cid), self.assertRaises(ValueError):
                hotspots.edit_hotspot(self.doc, cid, "continue")
        video(self.doc)["id"] = 40
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            hotspots.edit_hotspot(self.doc, 40, "continue")

    def test_unobserved_build_and_format_are_not_relabelled(self) -> None:
        for key, value in (("version", "9.0"), ("authoringClientName", {"platform": "Windows"})):
            bad = copy.deepcopy(self.doc)
            bad[key] = value
            with self.assertRaisesRegex(ValueError, "capture other builds"):
                hotspots.edit_hotspot(bad, 40, "continue")

    def test_exact_rational_ticks_and_invalid_times(self) -> None:
        self.doc["editRate"] = 705600000
        candidate = hotspots.edit_hotspot(self.doc, 40, "time", time="1/3")
        self.assertEqual(hotspot(candidate)["gotoTime"], 235200000)
        for time in (-1, True, "1/0", "1/11", float("inf")):
            with self.subTest(time=time), self.assertRaises(ValueError):
                hotspots.edit_hotspot(self.doc, 40, "time", time=time)

    def test_bad_targets_and_incompatible_options_refuse_before_mutation(self) -> None:
        cases: list[tuple[str, dict[str, Any]]] = [
            ("continue", {"pause": False}),
            ("continue", {"time": 4}),
            ("time", {}),
            ("time", {"time": 4, "new_window": True}),
            ("marker", {"marker_time": 4}),
            ("remove", {"pause": False}),
            ("url", {"url": ""}),
            ("url", {"url": " https://example.test"}),
            ("url", {"url": "https://example.test/\x00invalid"}),
            ("url", {"url": 5}),
            ("url", {"url": "https://example.test/\n"}),
            ("continue", {"pause": 1}),
        ]
        for action, options in cases:
            before = copy.deepcopy(self.doc)
            with self.subTest(action=action, options=options), self.assertRaises(ValueError):
                hotspots.edit_hotspot(self.doc, 40, action, **options)
            self.assertEqual(self.doc, before)

    def test_malformed_attributes_hotspot_and_marker_encoding_are_not_overwritten(self) -> None:
        for malformed in ([], "opaque", None):
            bad = copy.deepcopy(self.doc)
            video(bad)["attributes"] = malformed
            with self.assertRaises(ValueError):
                hotspots.edit_hotspot(bad, 40, "continue")
            video(bad)["attributes"] = {"hotspot": malformed}
            with self.assertRaises(ValueError):
                hotspots.edit_hotspot(bad, 40, "continue")
        self.doc["timeline"]["parameters"]["toc"]["keyframes"][0]["duration"] = 1
        with self.assertRaisesRegex(ValueError, "unsupported marker point"):
            hotspots.markers(self.doc)


class MarkerClockTests(unittest.TestCase):
    def node(
        self,
        kind="VMFile",
        *,
        cid=50,
        start=22,
        media_start=1,
        duration=4,
        scalar: int | str = 1,
        point=3,
    ):
        return {
            "id": cid,
            "_type": kind,
            "start": start * 1000,
            "mediaStart": media_start * 1000,
            "duration": duration * 1000,
            "scalar": scalar,
            "attributes": {"ident": "point owner"},
            "parameters": {
                "toc": {
                    "type": "string",
                    "keyframes": [
                        {
                            "time": point * 1000,
                            "endTime": point * 1000,
                            "duration": 0,
                            "value": "Point",
                        }
                    ],
                }
            },
        }

    def doc(self, node):
        doc = document()
        trigger = {"id": 80, "_type": "VMFile", "attributes": {}, "parameters": {}}
        project.scene_tracks(doc)[0][0]["medias"] = [node, trigger]
        return doc

    def target(self, doc, owner=50, point=3, **options):
        result = hotspots.edit_hotspot(
            doc, 80, "marker", marker_owner=owner, marker_time=point, **options
        )
        return project.scene_tracks(result)[0][0]["medias"][-1]["attributes"]["hotspot"]

    def test_native_hold_callout_recording_offset_and_speed_destinations(self):
        cases = [
            ("IMFile", 0, 0, 5, 1, 2, 2000),
            ("Callout", 5, 0, 5, 1, 2, 7000),
            ("ScreenVMFile", 15, 10, 5, 1, 12, 17000),
            ("VMFile", 22, 1, 4, 1, 3, 24000),
            ("VMFile", 28, 4, 2, "1/2", 6, 29000),
        ]
        for kind, start, media_start, duration, scalar, point, expected in cases:
            node = self.node(
                kind,
                start=start,
                media_start=media_start,
                duration=duration,
                scalar=scalar,
                point=point,
            )
            if kind == "IMFile":
                node["mediaDuration"] = 1
            doc = self.doc(node)
            before = copy.deepcopy(doc)
            with self.subTest(kind=kind, scalar=scalar):
                result = self.target(doc, point=point)
                self.assertEqual(result["lastMarkerGlobalTime"], expected)
                self.assertEqual(result["markerTime"], point * 1000)
                self.assertEqual(doc, before)

    def test_trimmed_and_sped_up_groups_transform_the_child_point(self):
        for start, duration, scalar, expected in ((32, 4, 1, 33000), (38, 2, "1/2", 38500)):
            child = self.node(start=1, media_start=2, duration=4, point=3)
            group = self.node(
                "Group", cid=60, start=start, media_start=1, duration=duration, scalar=scalar
            )
            group["parameters"] = {}
            group["tracks"] = [{"medias": [child]}]
            with self.subTest(scalar=scalar):
                self.assertEqual(self.target(self.doc(group))["lastMarkerGlobalTime"], expected)

    def test_nested_group_transforms_are_applied_inside_out(self):
        child = self.node(start=1, media_start=2, point=3)
        inner = self.node("Group", cid=60, start=1, media_start=1)
        outer = self.node("Group", cid=61, start=42, media_start=1)
        for group in (inner, outer):
            group["parameters"] = {}
        inner["tracks"] = [{"medias": [child]}]
        outer["tracks"] = [{"medias": [inner]}]
        self.assertEqual(self.target(self.doc(outer))["lastMarkerGlobalTime"], 43000)

    def test_group_owned_marker_uses_its_own_source_clock(self):
        group = self.node("Group", start=32, media_start=1, point=2)
        group["tracks"] = [{"medias": []}]
        self.assertEqual(self.target(self.doc(group), point=2)["lastMarkerGlobalTime"], 33000)

    def test_linked_child_mirrors_do_not_double_the_wrapper_transform(self):
        wrapper = self.node(
            "UnifiedMedia", start=48, media_start=4, duration=2, scalar="1/2", point=6
        )
        child = copy.deepcopy(wrapper)
        child.update(id=51, _type="VMFile")
        wrapper["video"] = child
        wrapper["audio"] = {
            "id": 52,
            "_type": "AMFile",
            "start": 48000,
            "mediaStart": 4000,
            "scalar": "1/2",
        }
        wrapper["parameters"] = {}
        result = self.target(self.doc(wrapper), point=6)
        self.assertEqual(result["markerParametricId"], 50)
        self.assertEqual(result["lastMarkerGlobalTime"], 49000)

    def test_conflicting_explicit_cache_is_rejected_for_a_known_clock(self):
        doc = self.doc(self.node())
        with self.assertRaisesRegex(ValueError, "conflicts"):
            self.target(doc, marker_global_time=25)
        self.assertEqual(self.target(doc, marker_global_time=24)["lastMarkerGlobalTime"], 24000)

    def test_unmapped_containers_and_multiple_scenes_require_explicit_timing(self):
        container = self.node("StitchedMedia", cid=60)
        container["parameters"] = {}
        container["tracks"] = [{"medias": [self.node()]}]
        doc = self.doc(container)
        with self.assertRaisesRegex(ValueError, "supply --marker-global-time"):
            self.target(doc)
        self.assertEqual(self.target(doc, marker_global_time=24)["lastMarkerGlobalTime"], 24000)
        doc = self.doc(self.node())
        doc["timeline"]["sceneTrack"]["scenes"].append({"csml": {"tracks": []}})
        with self.assertRaisesRegex(ValueError, "multiple scene clocks"):
            self.target(doc)

    def test_trimmed_out_nonpositive_and_fractional_tick_mappings_are_not_guessed(self):
        for changes in (
            {"mediaStart": 4000},
            {"scalar": 0},
            {"duration": -1},
            {"scalar": "1/3"},
            {"scalar": True},
        ):
            node = self.node()
            node.update(changes)
            doc = self.doc(node)
            with (
                self.subTest(changes=changes),
                self.assertRaisesRegex(ValueError, "supply --marker-global-time"),
            ):
                self.target(doc)


class HotspotCLITests(unittest.TestCase):
    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / "example.cmproj"
        self.source.mkdir()
        self.file = self.source / "project.tscproj"
        self.doc = document()
        self.raw = project.encode_document(self.doc)
        self.file.write_bytes(self.raw)
        self.output = self.root / "candidate.json"

    def invoke(self, *args: str) -> tuple[int, str, str]:
        out, err = io.StringIO(), io.StringIO()
        with patch("sys.stdout", out), patch("sys.stderr", err):
            status = hotspots.main(list(args))
        return status, out.getvalue(), err.getvalue()

    def test_stage_and_rerun_are_read_only_for_source_and_do_not_require_media(self) -> None:
        args = (
            "set",
            str(self.source),
            "--clip-id",
            "40",
            "--output",
            str(self.output),
            "--action",
            "time",
            "--time",
            "4",
            "--no-pause",
        )
        status, out, err = self.invoke(*args)
        self.assertEqual((status, err), (0, ""))
        report = json.loads(out)
        self.assertEqual(report["schema_version"], 1)
        self.assertEqual(report["owner"], "camtasia-hotspots")
        self.assertEqual(report["projectSha256"], project.digest(self.raw))
        self.assertFalse(report["nativeVerified"])
        self.assertEqual(hotspot(project.load(self.output)[0])["gotoTime"], 4000)
        self.assertTrue(report["written"])
        status, out, _ = self.invoke(*args)
        self.assertEqual(status, 0)
        self.assertFalse(json.loads(out)["written"])
        self.assertEqual(self.file.read_bytes(), self.raw)

    def test_existing_different_output_and_source_alias_refuse_without_writes(self) -> None:
        self.output.write_bytes(b"unrelated data")
        for output in (self.output, self.file, self.source / "../example.cmproj/project.tscproj"):
            status, out, err = self.invoke(
                "remove", str(self.source), "--clip-id", "40", "--output", str(output)
            )
            self.assertEqual((status, out), (1, ""))
            self.assertFalse(json.loads(err)["ok"])
        self.assertEqual(self.file.read_bytes(), self.raw)
        self.assertEqual(self.output.read_bytes(), b"unrelated data")

    def test_symlink_output_is_never_followed(self) -> None:
        self.output.symlink_to(self.file)
        status, _, err = self.invoke(
            "remove", str(self.source), "--clip-id", "40", "--output", str(self.output)
        )
        self.assertEqual(status, 1)
        self.assertIn("nonsymlink", err)
        self.assertEqual(self.file.read_bytes(), self.raw)

    def test_inspection_and_error_have_separate_json_streams(self) -> None:
        status, out, err = self.invoke("inspect", str(self.source))
        self.assertEqual((status, err), (0, ""))
        self.assertEqual(len(json.loads(out)["markers"]), 3)
        status, out, err = self.invoke(
            "set",
            str(self.source),
            "--clip-id",
            "40",
            "--output",
            str(self.output),
            "--action",
            "time",
        )
        self.assertEqual((status, out), (1, ""))
        self.assertIn("supply --time", json.loads(err)["error"])
        self.assertFalse(self.output.exists())

    def test_staging_preserves_native_finite_decimal_without_rounding(self) -> None:
        self.doc["sourceBin"][0]["sourceTracks"] = [
            {"type": 2, "integratedLUFS": project.NativeLoudnessSentinel("-1.79769313486232e+308")}
        ]
        self.file.write_bytes(project.encode_document(self.doc))
        status, _, err = self.invoke(
            "set",
            str(self.source),
            "--clip-id",
            "40",
            "--output",
            str(self.output),
            "--action",
            "continue",
        )
        self.assertEqual((status, err), (0, ""))
        self.assertIn(b'"integratedLUFS":-1.79769313486232e+308', self.output.read_bytes())
        loaded, _ = project.load(self.output)
        self.assertEqual(loaded["sourceBin"], self.doc["sourceBin"])


if __name__ == "__main__":
    unittest.main()
