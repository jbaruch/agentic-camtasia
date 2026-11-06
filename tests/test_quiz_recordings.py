from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_hotspot_recordings import fixture as recording_document
from test_animations import visual
import project
import quizzes

RATE = 705600000
NATIVE_XML = (
    '<Quiz id="1001" name="Quiz 1"><Options feedback="1" graded="1"/><Questions>'
    '<ShortAnswer id="101" text="Default Question Text" collapsed="0" feedback="0" '
    'fb_correct="" fb_correct_action="" fb_correct_jumptime_ms="0" fb_correct_url="" '
    'fb_correct_marker="" fb_correct_marker_time="0" fb_wrong="" fb_wrong_action="" '
    'fb_wrong_jumptime_ms="0" fb_wrong_url="" fb_wrong_marker="" fb_wrong_marker_time="0">'
    "</ShortAnswer></Questions></Quiz>"
)


def fixture(kind: str, *, retimed: bool = False) -> dict:
    doc = recording_document(kind)
    owner = visual(doc)
    global_time = 6350400000
    if retimed:
        if kind == "ScreenIMFile":
            owner.update(duration=RATE, scalar="1/2")
            global_time = 5997600000
        else:
            owner.update(start=10 * RATE, duration=4 * RATE, mediaStart=2 * RATE, scalar="1/2")
            global_time = 9525600000
    doc["timeline"]["parameters"]["quiz"] = {
        "type": "string",
        "keyframes": [
            {"time": global_time, "endTime": global_time, "duration": 0, "value": NATIVE_XML}
        ],
    }
    doc["metadata"]["QuizCount"] = {"type": "int", "value": 1}
    return doc


def short_answer(quiz_id: int = 1001) -> dict:
    return {
        "schema_version": 1,
        "owner": "camtasia-quiz-spec",
        "id": quiz_id,
        "name": "Edited quiz — café",
        "questions": [{"id": 101, "kind": "short-answer", "text": "Retained & edited?"}],
    }


class QuizRecordingTests(unittest.TestCase):
    def test_native_pin_unpin_preserves_complete_xml_points_cursor_children_and_audio(self) -> None:
        for kind in ("ScreenIMFile", "StitchedMedia"):
            for retimed in (False, True):
                with self.subTest(kind=kind, retimed=retimed):
                    doc = fixture(kind, retimed=retimed)
                    before = copy.deepcopy(doc)
                    expected = copy.deepcopy(doc)
                    parameter = expected["timeline"]["parameters"].pop("quiz")
                    point = RATE if kind == "ScreenIMFile" else 9 * RATE
                    parameter["keyframes"][0].update(time=point, endTime=point)
                    visual(expected)["parameters"]["quiz"] = parameter
                    pinned = quizzes.move(doc, "1001", 3)
                    self.assertEqual(pinned, expected)
                    self.assertEqual(quizzes.move(pinned, "1001", 2), doc)
                    self.assertEqual(quizzes.move(pinned, "1001", 3), pinned)
                    self.assertEqual(doc, before)

    def test_transfer_keeps_opaque_frame_fields_and_exact_xml_whitespace(self) -> None:
        doc = fixture("ScreenIMFile", retimed=True)
        frame = doc["timeline"]["parameters"]["quiz"]["keyframes"][0]
        frame["value"] = NATIVE_XML.replace("<Questions>", "<Questions><!-- retain -->\n")
        frame["future"] = {"opaque": [True, None, "日本語"]}
        pinned = quizzes.move(doc, "1001", 3)
        entry = quizzes.entries(pinned)[0]
        self.assertEqual(entry["frame"]["value"], frame["value"])
        self.assertEqual(entry["frame"]["future"], frame["future"])
        self.assertEqual(quizzes.move(pinned, "1001", 2), doc)

    def test_upsert_retains_existing_owner_and_removal_restores_unrelated_payload(self) -> None:
        for kind in ("ScreenIMFile", "StitchedMedia"):
            doc = fixture(kind)
            original = copy.deepcopy(doc)
            local = 1 if kind == "ScreenIMFile" else 9
            pinned = quizzes.move(doc, "1001", 3)
            edited = quizzes.upsert(pinned, short_answer(), local)
            entry = quizzes.entries(edited)[0]
            self.assertEqual((entry["ownerId"], entry["time"]), (3, local * RATE))
            question = quizzes.children(
                quizzes.children(quizzes.xml_root(entry["xml"]), "Questions")[0]
            )[0]
            self.assertEqual(question.getAttribute("text"), "Retained & edited?")
            cleared = quizzes.remove(edited, "1001")
            expected = copy.deepcopy(doc)
            expected["timeline"]["parameters"].pop("quiz")
            expected["metadata"].pop("QuizCount")
            self.assertEqual(cleared, expected)
            authored = quizzes.upsert(cleared, short_answer(1002), local, owner_id=3)
            self.assertEqual(quizzes.inventory(authored)[0]["ownerId"], 3)
            self.assertEqual(quizzes.remove(authored, "1002"), cleared)
            self.assertEqual(quizzes.remove(cleared, "1001"), cleared)
            self.assertEqual(doc, original)

    def test_explicit_global_and_owner_times_use_independent_native_origins(self) -> None:
        cases = [
            ("ScreenIMFile", "33/4", "1/2", 352800000),
            ("StitchedMedia", "53/4", "17/2", 5997600000),
        ]
        for kind, global_time, local_time, expected in cases:
            doc = fixture(kind, retimed=True)
            global_result = quizzes.move(doc, "1001", 3, global_seconds=global_time)
            local_result = quizzes.move(doc, "1001", 3, seconds=local_time)
            self.assertEqual(global_result, local_result)
            self.assertEqual(quizzes.inventory(global_result)[0]["time"], expected)

    def test_frozen_source_frame_does_not_shift_quiz_origin(self) -> None:
        for source_frame in (5621280000, 2822400000):
            doc = fixture("ScreenIMFile", retimed=True)
            visual(doc)["mediaStart"] = source_frame
            result = quizzes.move(doc, "1001", 3)
            self.assertEqual(quizzes.inventory(result)[0]["time"], RATE)
            self.assertEqual(visual(result)["mediaStart"], source_frame)
            self.assertEqual(visual(result)["mediaDuration"], 1)
            self.assertEqual(quizzes.move(result, "1001", 2), doc)

    def test_group_transform_applies_after_local_frozen_point(self) -> None:
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
            "parameters": {},
            "tracks": [{"medias": [held]}],
        }
        project.scene_tracks(doc)[0][0]["medias"] = [group]
        doc["timeline"]["parameters"]["quiz"]["keyframes"][0].update(
            time=15170400000, endTime=15170400000
        )
        pinned = quizzes.move(doc, "1001", 3)
        self.assertEqual(quizzes.inventory(pinned)[0]["time"], RATE)
        self.assertEqual(quizzes.move(pinned, "1001", 2), doc)

    def test_linked_new_variants_and_stitched_children_refuse_without_mutation(self) -> None:
        for kind in ("ScreenIMFile", "StitchedMedia"):
            doc = fixture(kind)
            owner = visual(doc)
            project.scene_tracks(doc)[0][0]["medias"] = [
                {
                    "id": 80,
                    "_type": "UnifiedMedia",
                    "video": owner,
                    "audio": {"id": 81, "_type": "AMFile", "parameters": {}},
                }
            ]
            before = copy.deepcopy(doc)
            for alias in (3, 80):
                with self.assertRaisesRegex(ValueError, "linked held/stitched quiz constructor"):
                    quizzes.move(doc, "1001", alias)
            self.assertEqual(doc, before)
        doc = fixture("StitchedMedia")
        before = copy.deepcopy(doc)
        for child in (4, 5):
            with self.assertRaisesRegex(ValueError, "stitched parent"):
                quizzes.move(doc, "1001", child)
        self.assertEqual(doc, before)

    def test_invisible_fractional_and_occupied_destinations_refuse(self) -> None:
        for kind, point in (("ScreenIMFile", 3), ("StitchedMedia", 1)):
            doc = fixture(kind, retimed=True)
            before = copy.deepcopy(doc)
            with self.assertRaisesRegex(ValueError, "visible"):
                quizzes.move(doc, "1001", 3, seconds=point)
            pinned = quizzes.move(doc, "1001", 3)
            other = quizzes.upsert(
                pinned, short_answer(1002), "17/2" if kind == "ScreenIMFile" else "27/2"
            )
            with self.assertRaisesRegex(ValueError, "unoccupied"):
                quizzes.move(other, "1002", 3)
            self.assertEqual(doc, before)
        doc = fixture("ScreenIMFile")
        visual(doc)["scalar"] = "2/3"
        with self.assertRaisesRegex(ValueError, "between owner ticks"):
            quizzes.move(doc, "1001", 3, global_seconds="5644800001/705600000")

    def test_cli_stages_inspects_noops_collisions_and_unpins_unchanged_xml(self) -> None:
        for kind in ("ScreenIMFile", "StitchedMedia"):
            with tempfile.TemporaryDirectory() as directory:
                root = Path(directory)
                source, output, unpinned = [
                    root / n for n in ("source.json", "pin.json", "unpin.json")
                ]
                source.write_bytes(project.encode_document(fixture(kind, retimed=True)))
                original = source.read_bytes()
                command = [
                    "move",
                    str(source),
                    "--quiz-id",
                    "1001",
                    "--owner-id",
                    "3",
                    "--output",
                    str(output),
                ]
                for written in (True, False):
                    stream = io.StringIO()
                    with patch("sys.stdout", stream):
                        self.assertEqual(quizzes.main(command), 0)
                    report = json.loads(stream.getvalue())
                    self.assertEqual(report["written"], written)
                    self.assertFalse(report["nativeVerified"])
                saved = output.read_bytes()
                with patch("sys.stderr", io.StringIO()):
                    self.assertEqual(
                        quizzes.main(
                            ["remove", str(source), "--quiz-id", "1001", "--output", str(output)]
                        ),
                        1,
                    )
                self.assertEqual(output.read_bytes(), saved)
                stream = io.StringIO()
                with patch("sys.stdout", stream):
                    self.assertEqual(quizzes.main(["inspect", str(output)]), 0)
                self.assertEqual(json.loads(stream.getvalue())["quizzes"][0]["ownerId"], 3)
                with patch("sys.stdout", io.StringIO()):
                    self.assertEqual(
                        quizzes.main(
                            [
                                "move",
                                str(output),
                                "--quiz-id",
                                "1001",
                                "--owner-id",
                                "2",
                                "--output",
                                str(unpinned),
                            ]
                        ),
                        0,
                    )
                self.assertEqual(project.load(unpinned)[0], fixture(kind, retimed=True))
                self.assertEqual(source.read_bytes(), original)
