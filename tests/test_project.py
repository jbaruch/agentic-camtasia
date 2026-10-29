from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/camtasia-project/scripts"))
import project  # noqa: E402


def clip(cid: int = 10, kind: str = "VMFile", **changes: object) -> dict:
    result = {
        "id": cid,
        "_type": kind,
        "src": 1,
        "trackNumber": 0,
        "start": 0,
        "duration": 100,
        "mediaStart": 0,
        "mediaDuration": 100,
        "scalar": 1,
        "parameters": {},
        "effects": [],
    }
    result.update(changes)
    return result


def document() -> dict:
    return {
        "version": "9.0",
        "editRate": 100,
        "width": 1920,
        "height": 1080,
        "authoringClientName": {"name": "Camtasia", "platform": "Mac", "version": "2025.0.3"},
        "sourceBin": [{"id": 1, "src": "./media/source.mp4", "sourceTracks": []}],
        "timeline": {
            "trackAttributes": [{"ident": "Narration", "audioMuted": False}],
            "sceneTrack": {
                "scenes": [{"csml": {"tracks": [{"trackIndex": 0, "medias": [clip()]}]}}]
            },
        },
        "opaque": {"futureFeature": [1, "keep me"]},
    }


class ProjectTests(unittest.TestCase):
    def test_duplicate_native_sibling_track_indices_are_refused(self) -> None:
        doc = document()
        doc.update(
            version="10.0",
            authoringClientName={"name": "Camtasia", "platform": "Mac", "version": "2026.2.4"},
        )
        tracks = project.scene_tracks(doc)[0]
        tracks.extend([{"trackIndex": 1, "medias": []}, {"trackIndex": 1, "medias": []}])
        report = project.validate(doc, self.root)
        self.assertFalse(report["ok"])
        self.assertTrue(any("duplicate sibling track index 1" in e for e in report["errors"]))
        tracks[2]["trackIndex"] = 7
        self.assertEqual(project.native_duplicate_track_indices(doc), [])

    def test_group_track_indices_are_scoped_to_their_own_siblings(self) -> None:
        doc = document()
        doc.update(
            version="10.0",
            authoringClientName={"name": "Camtasia", "platform": "Mac", "version": "2026.2.4"},
        )
        group = {
            "id": 20,
            "_type": "Group",
            "tracks": [{"trackIndex": 0, "medias": []}, {"trackIndex": 1, "medias": []}],
        }
        project.scene_tracks(doc)[0][0]["medias"].append(group)
        self.assertEqual(project.native_duplicate_track_indices(doc), [])
        group["tracks"][1]["trackIndex"] = 0
        self.assertEqual(len(project.native_duplicate_track_indices(doc)), 1)
        doc["authoringClientName"]["version"] = "2027.0.0"
        self.assertEqual(project.native_duplicate_track_indices(doc), [])

    def setUp(self) -> None:
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        (self.root / "media").mkdir()
        (self.root / "media/source.mp4").write_bytes(b"media existence fixture")
        self.doc = document()
        self.target = self.root / "project.tscproj"
        self.raw = (json.dumps(self.doc, indent=2) + "\n").encode()
        self.target.write_bytes(self.raw)
        self.candidate = self.root / "candidate.json"

    def lane(self, doc: dict | None = None) -> dict:
        return project.selected_track(self.doc if doc is None else doc, "0:0")

    def stage(self) -> dict:
        candidate = copy.deepcopy(self.doc)
        candidate["title"] = "Changed"
        self.candidate.write_bytes(project.encode_document(candidate))
        return candidate

    def apply(self, expected: str | None = None, preserve: list[str] | None = None) -> dict:
        with patch.object(project, "ensure_closed"):
            return project.apply_candidate(
                self.target,
                self.candidate,
                expected or project.digest(self.raw),
                preserve or [],
                [],
            )

    def test_inspection_does_not_mutate_bytes(self) -> None:
        report = project.inventory(self.doc, self.raw, self.root)
        self.assertTrue(report["validation"]["ok"])
        self.assertEqual(report["clipTypes"], {"VMFile": 1})
        self.assertEqual(self.target.read_bytes(), self.raw)

    def test_inspection_exposes_logical_assets_without_requiring_fake_bundle_files(self) -> None:
        frame = {
            "effectName": "DeviceFrameEffect",
            "parameters": {"deviceFrameSource": "Desktop_1.mp4"},
        }
        cursor = {
            "effectName": "CursorPath",
            "parameters": {"cursorImagePath": "Mac/pointer"},
        }
        self.lane()["medias"][0]["effects"] = [frame, cursor]
        self.doc["sourceBin"][0]["sourceEffects"] = [copy.deepcopy(frame)]
        before = copy.deepcopy(self.doc)
        report = project.inventory(self.doc, self.raw, self.root)
        self.assertTrue(report["validation"]["ok"])
        refs = report["assetReferences"]
        self.assertEqual(len(refs), 3)
        self.assertEqual({r["reference"] for r in refs}, {"Desktop_1.mp4", "Mac/pointer"})
        self.assertEqual(len({r["path"] for r in refs}), 3)
        self.assertTrue(any(r["path"].startswith("/sourceBin/") for r in refs))
        self.assertEqual(self.doc, before)

    def test_asset_inspection_does_not_guess_from_unrelated_path_like_text(self) -> None:
        self.lane()["medias"][0]["effects"] = [
            {"effectName": "FutureEffect", "parameters": {"cursorImagePath": "opaque"}},
            {"effectName": "CursorPath", "parameters": None},
            {"effectName": [], "parameters": {"cursorImagePath": "opaque"}},
        ]
        self.doc["opaque"] = {"text": "Desktop_1.mp4", "cursorImagePath": "Mac/pointer"}
        self.assertEqual(project.inventory(self.doc, self.raw, self.root)["assetReferences"], [])

    def test_nested_containers_and_multiple_scenes_are_seen(self) -> None:
        group = clip(20, "Group", tracks=[{"medias": [clip(21, start=-50)]}])
        group.pop("src")
        self.lane()["medias"].append(group)
        self.doc["timeline"]["sceneTrack"]["scenes"].append(
            {"csml": {"tracks": [{"medias": [clip(30, "AMFile")]}]}}
        )
        report = project.inventory(self.doc, self.raw, self.root)
        self.assertTrue(report["validation"]["ok"], report)
        self.assertEqual(report["clipTypes"], {"VMFile": 2, "Group": 1, "AMFile": 1})

    def test_current_trimmed_two_times_group_drift_is_refused_without_mutating_payload(
        self,
    ) -> None:
        self.doc["version"] = "10.0"
        self.doc["authoringClientName"]["version"] = "2026.2.4"
        group = clip(
            20,
            "Group",
            duration=200,
            mediaStart=100,
            mediaDuration=400,
            scalar="1/2",
            tracks=[
                {"medias": [clip(21, start=100, duration=400, mediaStart=200, mediaDuration=400)]}
            ],
        )
        group.pop("src")
        self.lane()["medias"] = [group]
        before = copy.deepcopy(self.doc)
        report = project.validate(self.doc, self.root)
        self.assertFalse(report["ok"])
        self.assertTrue(any("grows on native reopen" in error for error in report["errors"]))
        self.assertEqual(self.doc, before)
        group["mediaStart"] = 0
        group["tracks"][0]["medias"][0]["start"] = 0
        self.assertTrue(project.validate(self.doc, self.root)["ok"])

    def test_group_drift_guard_stays_with_its_observed_build_and_speed(self) -> None:
        group = clip(20, "Group", duration=200, mediaStart=100, mediaDuration=400, scalar="1/2")
        group.pop("src")
        self.lane()["medias"] = [group]
        self.assertEqual(project.native_group_reopen_hazards(self.doc), [])
        self.doc["version"] = "10.0"
        self.doc["authoringClientName"]["version"] = "2026.2.4"
        for scalar, media_start in ((1, 100), ("1/2", 0), ("1/4", 100)):
            group.update(scalar=scalar, mediaStart=media_start)
            self.assertEqual(project.native_group_reopen_hazards(self.doc), [])

    def test_behavior_is_not_misclassified_as_a_clip(self) -> None:
        self.lane()["medias"][0]["effects"] = [
            {"_type": "GenericBehaviorEffect", "start": 0, "duration": 10, "effectName": "Fade"}
        ]
        report = project.inventory(self.doc, self.raw, self.root)
        self.assertTrue(report["validation"]["ok"], report)
        self.assertEqual(report["clipTypes"], {"VMFile": 1})
        self.assertEqual(report["effects"], {"Fade": 1})

    def test_unknown_clip_is_preserved_with_warning(self) -> None:
        self.lane()["medias"][0]["_type"] = "FutureMedia"
        before = copy.deepcopy(self.doc)
        report = project.validate(self.doc, self.root)
        self.assertTrue(report["ok"])
        self.assertTrue(any("FutureMedia" in w for w in report["warnings"]))
        self.assertEqual(before, self.doc)

    def test_native_caption_clip_needs_no_source_bin_reference(self) -> None:
        caption = clip(12, "Caption")
        del caption["src"]
        self.lane()["medias"].append(caption)
        report = project.inventory(self.doc, self.raw, self.root)
        self.assertTrue(report["validation"]["ok"], report)
        self.assertEqual(report["clipTypes"], {"VMFile": 1, "Caption": 1})
        self.assertFalse(
            any("unrecognized clip type" in w for w in report["validation"]["warnings"])
        )

    def test_native_unicode_ranges_use_byte_coverage_without_mutating_text(self) -> None:
        text = "Unicode: café — 日本語"
        callout = clip(
            11,
            "Callout",
            **{
                "def": {
                    "text": text,
                    "textAttributes": {
                        "keyframes": [{"value": [{"rangeStart": 0, "rangeEnd": len(text)}]}]
                    },
                }
            },
        )
        callout.pop("src")
        self.lane()["medias"].append(callout)
        before = copy.deepcopy(self.doc)
        result = project.validate(self.doc, self.root)
        self.assertTrue(result["ok"])
        self.assertTrue(any("UTF-8 byte length 28" in w for w in result["warnings"]))
        self.assertEqual(before, self.doc)
        callout["def"]["textAttributes"]["keyframes"][0]["value"][0]["rangeEnd"] = 28
        self.assertFalse(project.validate(self.doc, self.root)["warnings"])

    def test_unicode_warning_is_limited_to_the_exercised_native_build(self) -> None:
        self.doc["authoringClientName"]["platform"] = "Windows"
        self.lane()["medias"].append(
            clip(
                11,
                "Callout",
                **{
                    "def": {
                        "text": "日本語",
                        "textAttributes": {"keyframes": [{"value": [{"rangeEnd": 3}]}]},
                    }
                },
            )
        )
        self.assertFalse(project.validate(self.doc, self.root)["warnings"])

    def test_rational_source_duration_and_still_hold(self) -> None:
        self.lane()["medias"][0].update(_type="IMFile", mediaDuration=1, duration=100000)
        self.lane()["medias"].append(clip(11, start=100000, mediaDuration="100/3", scalar="1/3"))
        self.assertTrue(project.validate(self.doc, self.root)["ok"])

    def test_duplicate_clip_and_source_ids_are_errors(self) -> None:
        self.lane()["medias"].append(clip())
        self.doc["sourceBin"].append(copy.deepcopy(self.doc["sourceBin"][0]))
        report = project.validate(self.doc, self.root)
        self.assertFalse(report["ok"])
        self.assertTrue(any("duplicate source" in e for e in report["errors"]))
        self.assertTrue(any("duplicate clip" in e for e in report["errors"]))

    def test_missing_media_and_dangling_source_are_errors(self) -> None:
        (self.root / "media/source.mp4").unlink()
        self.lane()["medias"][0]["src"] = 99
        report = project.validate(self.doc, self.root)
        self.assertFalse(report["ok"])
        self.assertEqual(len(report["errors"]), 2)

    def test_foreign_windows_source_is_unchecked_not_misresolved(self) -> None:
        self.doc["sourceBin"][0]["src"] = r"C:\Assets\take.trec"
        with patch.object(project.os, "name", "posix"):
            report = project.validate(self.doc, self.root)
        self.assertTrue(report["ok"])
        self.assertTrue(any("not checked" in w for w in report["warnings"]))

    def test_transition_ids_are_track_local_not_source_ids(self) -> None:
        self.lane()["transitions"] = [{"name": "Fade", "duration": 10, "rightMedia": 10}]
        self.assertTrue(project.validate(self.doc, self.root)["ok"])
        self.lane()["transitions"][0]["rightMedia"] = 1
        self.assertFalse(project.validate(self.doc, self.root)["ok"])

    def test_continuity_is_opt_in(self) -> None:
        self.lane()["medias"].append(clip(11, start=200))
        self.assertTrue(project.validate(self.doc, self.root)["ok"])
        self.assertFalse(project.validate(self.doc, self.root, ["0:0"])["ok"])
        self.lane()["medias"][1]["start"] = 100
        self.assertTrue(project.validate(self.doc, self.root, ["0:0"])["ok"])

    def test_nonfinite_and_boolean_timing_are_rejected(self) -> None:
        for value in (True, float("inf"), "1/0"):
            with self.subTest(value=value):
                self.lane()["medias"][0]["duration"] = value
                self.assertFalse(project.validate(self.doc, self.root)["ok"])

    def test_duplicate_keys_and_nan_are_not_silently_loaded(self) -> None:
        for text in ('{"x": 1, "x": 2}', '{"x": NaN}'):
            self.candidate.write_text(text)
            with self.assertRaises(ValueError):
                project.load(self.candidate)

    def silent_current_text(self) -> str:
        doc = copy.deepcopy(self.doc)
        doc["version"] = "10.0"
        doc["authoringClientName"]["version"] = "2026.2.4"
        doc["sourceBin"][0]["sourceTracks"] = [{"type": 2, "integratedLUFS": "native-lufs"}]
        return json.dumps(doc).replace('"native-lufs"', "-1.79769313486232e+308")

    def test_native_silent_loudness_is_preserved_during_inspection_and_apply(self) -> None:
        self.raw = self.silent_current_text().encode()
        self.target.write_bytes(self.raw)
        self.doc, original = project.load(self.target)
        report = project.inventory(self.doc, original, self.root)
        self.assertTrue(report["validation"]["ok"], report)
        json.dumps(report, allow_nan=False)
        self.assertEqual(self.target.read_bytes(), original)
        candidate = self.stage()
        candidate_raw = self.candidate.read_bytes()
        result = self.apply(preserve=["0:0"])
        self.assertTrue(result["changed"], result)
        self.assertEqual(Path(result["backup"]).read_bytes(), original)
        self.assertEqual(self.target.read_bytes(), candidate_raw)
        self.assertEqual(project.load(self.target)[0], candidate)
        self.assertIn(b'"integratedLUFS":-1.79769313486232e+308', candidate_raw)
        self.assertNotIn(b"Infinity", candidate_raw)

    def test_native_loudness_value_is_limited_to_audio_field_and_editor(self) -> None:
        text = self.silent_current_text()
        for old, new in (
            ('"type": 2', '"type": 0'),
            ('"type": 2', '"type": "2"'),
            ('"integratedLUFS"', '"peakLevel"'),
            ('"2026.2.4"', '"2025.0.3"'),
            ('"10.0"', '"9.0"'),
        ):
            self.candidate.write_text(text.replace(old, new))
            with (
                self.subTest(change=new),
                self.assertRaisesRegex(ValueError, "native loudness sentinel"),
            ):
                project.load(self.candidate)

    def test_observed_legacy_native_loudness_decimal_remains_readable(self) -> None:
        text = self.silent_current_text().replace('"2026.2.4"', '"2025.0.3"')
        self.candidate.write_text(text.replace('"10.0"', '"9.0"'))
        doc, _ = project.load(self.candidate)
        self.assertTrue(project.validate(doc, self.root)["ok"])
        encoded = project.encode_document(doc)
        self.assertIn(b"-1.79769313486232e+308", encoded)

    def test_nonfinite_tokens_and_other_overflow_are_rejected_in_loudness_field(self) -> None:
        text = self.silent_current_text()
        for token in ("NaN", "Infinity", "-Infinity", "-1e999", "1e999"):
            self.candidate.write_text(text.replace("-1.79769313486232e+308", token))
            with self.subTest(token=token), self.assertRaisesRegex(ValueError, "non-finite"):
                project.load(self.candidate)
        self.candidate.write_text(text.replace('"duration": 100', '"duration": -Infinity'))
        with self.assertRaisesRegex(ValueError, "non-finite"):
            project.load(self.candidate)

    def test_native_numeric_encoding_keeps_types_and_lookalike_strings(self) -> None:
        self.candidate.write_text(self.silent_current_text())
        loaded, _ = project.load(self.candidate)
        loaded["opaque"] = {
            "text": "-1.79769313486232e+308",
            "quoted/é": 'café\n"quoted"',
            "values": [None, False, True, 2, 1.25, [], {}],
        }
        self.candidate.write_bytes(project.encode_document(loaded))
        reloaded, _ = project.load(self.candidate)
        self.assertEqual(reloaded, loaded)
        self.assertEqual(reloaded["opaque"]["text"], "-1.79769313486232e+308")
        self.assertFalse(project.nonfinite_errors(copy.deepcopy(reloaded)))
        loaded["opaque"]["invalid"] = float("inf")
        with self.assertRaisesRegex(ValueError, "non-finite"):
            project.encode_document(loaded)

    def test_diff_escapes_json_pointers_and_bounds_previews(self) -> None:
        changes = list(project.differences({"a/b~c": "old"}, {"a/b~c": "x" * 1000}))
        self.assertEqual(changes[0]["path"], "/a~1b~0c")
        self.assertLess(len(changes[0]["after"]), 200)

    def test_apply_keeps_exact_backup_and_opaque_state(self) -> None:
        candidate = self.stage()
        report = self.apply(preserve=["0:0"])
        self.assertTrue(report["changed"])
        self.assertEqual(Path(report["backup"]).read_bytes(), self.raw)
        self.assertEqual(project.load(self.target)[0], candidate)
        self.assertEqual(project.load(self.target)[0]["opaque"], self.doc["opaque"])
        self.assertEqual(list(self.root.glob("*.writing")), [])

    def test_identical_rerun_is_a_noop(self) -> None:
        self.stage()
        self.apply()
        report = self.apply()
        self.assertFalse(report["changed"])
        self.assertEqual(len(list(self.root.glob("*.before-*.tscproj"))), 1)

    def test_stale_baseline_refuses_without_backup(self) -> None:
        self.stage()
        with self.assertRaisesRegex(ValueError, "changed since inspection"):
            self.apply(expected="0" * 64)
        self.assertEqual(self.target.read_bytes(), self.raw)
        self.assertEqual(list(self.root.glob("*.before-*")), [])

    def test_preserved_track_source_and_audio_settings_are_protected(self) -> None:
        for mutation in ("effect", "source", "settings", "timeline-gain", "mute"):
            with self.subTest(mutation=mutation):
                candidate = self.stage()
                if mutation == "effect":
                    self.lane(candidate)["medias"][0]["effects"] = [{"effectName": "changed"}]
                elif mutation == "source":
                    candidate["sourceBin"][0]["parameters"] = {"transcription": "changed"}
                elif mutation == "settings":
                    candidate["targetLoudness"] = -12
                elif mutation == "timeline-gain":
                    candidate["timeline"]["gain"] = 0.5
                else:
                    candidate["timeline"]["trackAttributes"][0]["audioMuted"] = True
                self.candidate.write_text(json.dumps(candidate))
                with self.assertRaisesRegex(ValueError, "preserved track"):
                    self.apply(preserve=["0:0"])
                self.assertEqual(self.target.read_bytes(), self.raw)

    def test_format_identity_cannot_be_upgraded_by_relabeling(self) -> None:
        candidate = self.stage()
        candidate["version"] = "10.0"
        self.candidate.write_text(json.dumps(candidate))
        with self.assertRaisesRegex(ValueError, "format identity"):
            self.apply()

    def test_invalid_candidate_is_not_applied(self) -> None:
        candidate = self.stage()
        candidate["sourceBin"][0]["src"] = "absent.mp4"
        self.candidate.write_text(json.dumps(candidate))
        self.assertFalse(self.apply()["validation"]["ok"])
        self.assertEqual(self.target.read_bytes(), self.raw)

    def test_file_clip_requires_source_reference(self) -> None:
        self.lane()["medias"][0].pop("src")
        report = project.validate(self.doc, self.root)
        self.assertFalse(report["ok"])
        self.assertTrue(any("source-bin reference" in e for e in report["errors"]))

    def test_native_empty_project_can_omit_source_bin(self) -> None:
        self.doc.pop("sourceBin")
        self.lane()["medias"] = []
        self.assertTrue(project.validate(self.doc, self.root)["ok"])
        self.lane()["medias"] = [clip()]
        self.assertFalse(project.validate(self.doc, self.root)["ok"])

    def test_native_behavior_crash_shape_is_rejected_without_mutation(self) -> None:
        parameter = {
            "type": "double",
            "defaultValue": 1.08,
            "keyframes": [{"time": 0, "endTime": 0, "duration": 0, "value": 1.08}],
        }
        behavior = {
            "_type": "GenericBehaviorEffect",
            "center": {"parameters": {"scale": parameter}},
        }
        self.lane()["medias"][0]["effects"] = [behavior]
        self.assertTrue(any("crash" in e for e in project.validate(self.doc, self.root)["errors"]))
        self.assertIn("keyframes", parameter)
        parameter.pop("keyframes")
        self.assertTrue(project.validate(self.doc, self.root)["ok"])

    def test_existing_backup_collision_refuses_without_overwrite(self) -> None:
        self.stage()
        backup = self.target.with_name(f"project.before-{project.digest(self.raw)}.tscproj")
        backup.write_bytes(b"preserve this separate file")
        with self.assertRaisesRegex(ValueError, "backup collision"):
            self.apply()
        self.assertEqual(backup.read_bytes(), b"preserve this separate file")
        self.assertEqual(self.target.read_bytes(), self.raw)

    def test_change_during_ownership_probe_refuses_replacement(self) -> None:
        self.stage()
        modified = self.raw + b" "
        with patch.object(
            project, "ensure_closed", side_effect=lambda _: self.target.write_bytes(modified)
        ):
            with self.assertRaisesRegex(ValueError, "changed during validation"):
                project.apply_candidate(
                    self.target, self.candidate, project.digest(self.raw), [], []
                )
        self.assertEqual(self.target.read_bytes(), modified)

    def test_replace_failure_retains_original_and_backup(self) -> None:
        self.stage()
        with patch.object(project.os, "replace", side_effect=PermissionError("refused")):
            with self.assertRaises(PermissionError):
                self.apply()
        self.assertEqual(self.target.read_bytes(), self.raw)
        self.assertEqual(len(list(self.root.glob("*.before-*"))), 1)
        self.assertEqual(list(self.root.glob("*.writing")), [])

    def test_live_marker_refuses_even_without_process_check(self) -> None:
        marker = self.target.with_name("~project.tscproj")
        marker.write_text("recovery")
        with self.assertRaisesRegex(ValueError, "recovery/live"):
            project.ensure_closed(self.target)
        self.assertEqual(marker.read_text(), "recovery")

    def test_empty_marker_does_not_bypass_live_process_probe(self) -> None:
        self.target.with_name("~project.tscproj").touch()
        running = subprocess.CompletedProcess([], 0, "123\n", "")
        handles = subprocess.CompletedProcess([], 0, f"p123\nn{self.target}\n", "")
        with (
            patch.object(project.sys, "platform", "darwin"),
            patch.object(project.shutil, "which", return_value="/bin/tool"),
            patch.object(project.subprocess, "run", side_effect=[running, handles]),
        ):
            with self.assertRaisesRegex(ValueError, "holds"):
                project.ensure_closed(self.target)

    def test_probe_failure_is_not_treated_as_closed(self) -> None:
        running = subprocess.CompletedProcess([], 2, "", "probe failed")
        with (
            patch.object(project.sys, "platform", "darwin"),
            patch.object(project.shutil, "which", return_value="/bin/tool"),
            patch.object(project.subprocess, "run", return_value=running),
        ):
            with self.assertRaisesRegex(ValueError, "cannot check"):
                project.ensure_closed(self.target)

    def test_cli_validation_failure_is_structured(self) -> None:
        output = io.StringIO()
        error = io.StringIO()
        with patch("sys.stdout", output), patch("sys.stderr", error):
            status = project.main(["validate", str(self.root / "missing.json")])
        self.assertEqual(status, 1)
        self.assertFalse(json.loads(output.getvalue())["ok"])
        self.assertIn("Camtasia project", error.getvalue())


if __name__ == "__main__":
    unittest.main()
