from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import sys
import tempfile
from typing import Any
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "skills/camtasia-project/scripts"))
import project  # noqa: E402
import quizzes  # noqa: E402


def document() -> dict:
    return {
        "version": "10.0",
        "authoringClientName": {"name": "Camtasia", "platform": "Mac", "version": "2026.2.4"},
        "editRate": 1000,
        "width": 1280,
        "height": 720,
        "sourceBin": [{"id": 1, "src": "absent-media-is-not-read.mp4", "opaque": ["keep"]}],
        "metadata": {"keep": "metadata"},
        "timeline": {
            "id": 2,
            "parameters": {"opaque": {"future": True}},
            "sceneTrack": {
                "scenes": [
                    {
                        "csml": {
                            "tracks": [
                                {
                                    "medias": [
                                        {
                                            "id": 3,
                                            "_type": "VMFile",
                                            "src": 1,
                                            "parameters": {},
                                            "attributes": {"future": "keep"},
                                        }
                                    ]
                                }
                            ]
                        }
                    }
                ]
            },
        },
        "future": {"payload": [True, None, "日本語"]},
    }


def spec(qid: int = 1001) -> dict:
    return {
        "schema_version": 1,
        "owner": "camtasia-quiz-spec",
        "id": qid,
        "name": "Café & <JSON> — quiz",
        "questions": [
            {
                "id": 101,
                "kind": "multiple-choice",
                "text": 'Pick "four" & 4 < 5',
                "answers": [
                    {"id": 1, "text": "4", "correct": True},
                    {"id": 2, "text": "5", "correct": False},
                ],
            },
            {"id": 103, "kind": "true-false", "text": "Five is even.", "true": False},
            {
                "id": 105,
                "kind": "fill-blank",
                "text": "Two plus two is...",
                "answers": [
                    {"id": 1, "text": "4", "correct": True},
                    {"id": 2, "text": "four", "correct": True},
                ],
            },
            {"id": 107, "kind": "short-answer", "text": "Explain — café & <brackets>."},
        ],
    }


def root(doc: dict):
    return quizzes.xml_root(
        quizzes.parse_xml(doc["timeline"]["parameters"]["quiz"]["keyframes"][0]["value"])
    )


def survey_spec() -> dict:
    item = spec()
    item.update(schema_version=3, graded=False)
    for answer in item["questions"][0]["answers"]:
        del answer["correct"]
    del item["questions"][1]["true"]
    del item["questions"][2]["answers"]
    return item


def linked_document() -> dict:
    doc = document()
    medias = project.scene_tracks(doc)[0][0]["medias"]
    video = medias[0]
    video.update(start=2000, duration=6000, mediaStart=1000, mediaDuration=6000, scalar=1)
    medias[0] = {
        "id": 9,
        "_type": "UnifiedMedia",
        "start": 2000,
        "duration": 6000,
        "mediaStart": 1000,
        "mediaDuration": 6000,
        "scalar": 1,
        "video": video,
        "audio": {"id": 10, "_type": "AMFile", "parameters": {}, "opaque": "keep"},
    }
    return doc


class QuizTests(unittest.TestCase):
    def setUp(self) -> None:
        self.doc = document()

    def test_new_survey_keys_follow_native_export_contract(self) -> None:
        result = quizzes.upsert(self.doc, survey_spec(), 1)
        questions = quizzes.children(quizzes.children(root(result), "Questions")[0])
        choices = quizzes.children(quizzes.children(questions[0], "Answers")[0], "Answer")
        self.assertEqual([a.getAttribute("iscorrect") for a in choices], ["1", "0"])
        self.assertEqual(questions[1].getAttribute("istrue"), "0")
        self.assertEqual(quizzes.children(quizzes.children(questions[2], "Answers")[0]), [])
        self.assertEqual(result["sourceBin"], self.doc["sourceBin"])
        self.assertEqual(result["timeline"]["sceneTrack"], self.doc["timeline"]["sceneTrack"])
        self.assertEqual(quizzes.upsert(result, survey_spec(), 1), result)

    def test_survey_omissions_preserve_existing_inactive_keys_and_opaque_data(self) -> None:
        keyed = spec()
        keyed["questions"][0]["answers"][0]["correct"] = False
        keyed["questions"][0]["answers"][1]["correct"] = True
        keyed["questions"][1]["true"] = True
        baseline = quizzes.upsert(self.doc, keyed, 1)
        entry = quizzes.entries(baseline)[0]
        questions = quizzes.children(
            quizzes.children(quizzes.xml_root(entry["xml"]), "Questions")[0]
        )
        answer = quizzes.children(quizzes.children(questions[2], "Answers")[0])[0]
        answer.setAttribute("future", "retain")
        entry["frame"]["value"] = entry["xml"].toxml()
        item = survey_spec()
        item["questions"][0]["answers"].reverse()
        result = quizzes.upsert(baseline, item, 1)
        qs = quizzes.children(quizzes.children(root(result), "Questions")[0])
        self.assertEqual(qs[1].getAttribute("istrue"), "1")
        choices = quizzes.children(quizzes.children(qs[0], "Answers")[0])
        self.assertEqual(
            [(a.getAttribute("id"), a.getAttribute("iscorrect")) for a in choices],
            [("2", "1"), ("1", "0")],
        )
        blanks = quizzes.children(quizzes.children(qs[2], "Answers")[0])
        self.assertEqual([a.getAttribute("text") for a in blanks], ["4", "four"])
        self.assertEqual(blanks[0].getAttribute("future"), "retain")
        item["questions"][2]["answers"] = []
        cleared = quizzes.upsert(result, item, 1)
        blank = quizzes.children(quizzes.children(root(cleared), "Questions")[0])[2]
        self.assertEqual(quizzes.children(quizzes.children(blank, "Answers")[0]), [])

    def test_survey_removed_choice_key_uses_first_retained_choice(self) -> None:
        baseline = quizzes.upsert(self.doc, spec(), 1)
        item = survey_spec()
        item["questions"][0]["answers"] = [{"id": 2, "text": "5"}, {"id": 3, "text": "6"}]
        result = quizzes.upsert(baseline, item, 1)
        choice = quizzes.children(quizzes.children(root(result), "Questions")[0])[0]
        self.assertEqual(
            [
                a.getAttribute("iscorrect")
                for a in quizzes.children(quizzes.children(choice, "Answers")[0])
            ],
            ["1", "0"],
        )

    def test_keyless_spec_requires_schema_three_and_explicit_ungraded(self) -> None:
        for version, grading in ((1, False), (2, False), (3, True), (3, None)):
            with self.subTest(version=version, grading=grading):
                item = survey_spec()
                item["schema_version"] = version
                if grading is None:
                    del item["graded"]
                else:
                    item["graded"] = grading
                with self.assertRaises(ValueError):
                    quizzes.upsert(self.doc, item, 1)

    def test_survey_explicit_invalid_keys_never_reach_native_export(self) -> None:
        for keys in ((False, False), (True, True), (True, None), (None, False), (None, "yes")):
            with self.subTest(keys=keys):
                item = survey_spec()
                for answer, key in zip(item["questions"][0]["answers"], keys, strict=True):
                    if key is not None:
                        answer["correct"] = key
                with self.assertRaises(ValueError):
                    quizzes.upsert(self.doc, item, 1)
        item = survey_spec()
        item["questions"][2]["answers"] = None
        with self.assertRaises(ValueError):
            quizzes.upsert(self.doc, item, 1)

    def test_survey_supplied_blank_answers_default_to_accepted(self) -> None:
        item = survey_spec()
        item["questions"][2]["answers"] = [{"id": 1, "text": "four"}]
        result = quizzes.upsert(self.doc, item, 1)
        blank = quizzes.children(quizzes.children(root(result), "Questions")[0])[2]
        self.assertEqual(
            quizzes.children(quizzes.children(blank, "Answers")[0])[0].getAttribute("iscorrect"),
            "1",
        )
        item["questions"][2]["answers"][0]["correct"] = False
        with self.assertRaises(ValueError):
            quizzes.upsert(self.doc, item, 1)

    def test_reenable_scoring_requires_explicit_keys_and_preserves_feedback(self) -> None:
        item = survey_spec()
        item["questions"][0]["feedback"] = {"enabled": True, "wrong": {"text": "Retain response"}}
        baseline = quizzes.upsert(self.doc, item, 1)
        item["graded"] = True
        with self.assertRaises(ValueError):
            quizzes.upsert(baseline, item, 1)
        keyed = spec()
        keyed.update(schema_version=3, graded=True)
        result = quizzes.upsert(baseline, keyed, 1)
        choice = quizzes.children(quizzes.children(root(result), "Questions")[0])[0]
        self.assertEqual(choice.getAttribute("fb_wrong"), "Retain response")
        self.assertEqual(quizzes.children(root(result), "Options")[0].getAttribute("graded"), "1")

    def test_feedback_actions_use_native_codes_milliseconds_and_escaped_text(self) -> None:
        item = spec()
        item["schema_version"] = 2
        item["questions"][0]["feedback"] = {
            "enabled": True,
            "correct": {"text": "Correct — café & <XML>.", "action": "time", "seconds": "13/2"},
            "wrong": {
                "text": "Try again.",
                "action": "url",
                "url": "https://example.test/?a=1&b=2",
            },
        }
        result = quizzes.upsert(self.doc, item, 1)
        q = quizzes.children(quizzes.children(root(result), "Questions")[0])[0]
        expected = {
            "feedback": "1",
            "fb_correct": "Correct — café & <XML>.",
            "fb_correct_action": "fb_JumpToTime",
            "fb_correct_jumptime_ms": "6500",
            "fb_wrong": "Try again.",
            "fb_wrong_action": "fb_GoToURL",
            "fb_wrong_url": "https://example.test/?a=1&b=2",
        }
        self.assertEqual({k: q.getAttribute(k) for k in expected}, expected)
        self.assertEqual(self.doc, document())
        self.assertEqual(quizzes.upsert(result, item, 1), result)

    def test_feedback_patches_preserve_inactive_destinations_and_legacy_omissions(self) -> None:
        item = spec()
        item["schema_version"] = 2
        item["questions"][0]["feedback"] = {
            "enabled": True,
            "correct": {"text": "Keep", "action": "url", "url": "https://example.test/"},
        }
        result = quizzes.upsert(self.doc, item, 1)
        item["questions"][0]["feedback"] = {"enabled": False, "correct": {"action": "continue"}}
        result = quizzes.upsert(result, item, 1)
        result = quizzes.upsert(result, spec(), 1)
        q = quizzes.children(quizzes.children(root(result), "Questions")[0])[0]
        self.assertEqual(
            [
                q.getAttribute(k)
                for k in ("feedback", "fb_correct", "fb_correct_action", "fb_correct_url")
            ],
            ["0", "Keep", "", "https://example.test/"],
        )
        item["questions"][0]["feedback"] = {"correct": {"text": ""}}
        result = quizzes.upsert(result, item, 1)
        q = quizzes.children(quizzes.children(root(result), "Questions")[0])[0]
        self.assertEqual(q.getAttribute("fb_correct"), "")
        self.assertEqual(q.getAttribute("fb_correct_url"), "https://example.test/")

    def test_feedback_marker_resolves_existing_timeline_and_trimmed_linked_clocks(self) -> None:
        item = spec()
        item["schema_version"] = 2
        item["questions"][0]["feedback"] = {
            "enabled": True,
            "wrong": {"action": "marker", "marker": "829723BB-68EE-4A61-B779-B7A6F844D814"},
        }
        for owner in ("timeline", "linked"):
            with self.subTest(owner=owner):
                doc = linked_document()
                node = (
                    doc["timeline"]
                    if owner == "timeline"
                    else project.scene_tracks(doc)[0][0]["medias"][0]["video"]
                )
                node["parameters"]["toc"] = {
                    "type": "string",
                    "keyframes": [
                        {
                            "time": 6000,
                            "endTime": 6000,
                            "duration": 0,
                            "value": "Target",
                            "metadata": {
                                "markerIdentifier": "829723BB-68EE-4A61-B779-B7A6F844D814"
                            },
                        }
                    ],
                }
                before = copy.deepcopy(doc)
                result = quizzes.upsert(doc, item, 1)
                q = quizzes.children(quizzes.children(root(result), "Questions")[0])[0]
                self.assertEqual(q.getAttribute("fb_wrong_action"), "fb_JumpToMarker")
                self.assertEqual(
                    q.getAttribute("fb_wrong_marker_time"),
                    "6000" if owner == "timeline" else "7000",
                )
                self.assertEqual(
                    q.getAttribute("fb_wrong_marker"), "829723BB-68EE-4A61-B779-B7A6F844D814"
                )
                self.assertEqual(doc, before)

    def test_feedback_refuses_missing_duplicate_and_fractional_marker_targets(self) -> None:
        item = spec()
        item["schema_version"] = 2
        item["questions"][0]["feedback"] = {"correct": {"action": "marker", "marker": "target"}}
        doc = document()
        with self.assertRaisesRegex(ValueError, "unique existing markerIdentifier"):
            quizzes.upsert(doc, item, 1)
        point = {
            "time": 1,
            "endTime": 1,
            "duration": 0,
            "value": "Target",
            "metadata": {"markerIdentifier": "target"},
        }
        doc["timeline"]["parameters"]["toc"] = {
            "type": "string",
            "keyframes": [point, copy.deepcopy(point)],
        }
        with self.assertRaisesRegex(ValueError, "unique existing markerIdentifier"):
            quizzes.upsert(doc, item, 1)
        doc["timeline"]["parameters"]["toc"]["keyframes"].pop()
        doc["editRate"] = 3000
        with self.assertRaisesRegex(ValueError, "exact millisecond"):
            quizzes.upsert(doc, item, 1)

    def test_feedback_invalid_shapes_targets_and_schema_one_are_refused(self) -> None:
        invalid = [
            True,
            {"enabled": 1},
            {"unknown": True},
            {"wrong": []},
            {"correct": {"text": 3}},
            {"correct": {"action": "unknown"}},
            {"correct": {"action": None}},
            {"correct": {"url": "https://example.test"}},
            {"correct": {"action": "continue", "seconds": 0}},
            {"correct": {"action": "time", "seconds": "1/3000"}},
            {"correct": {"action": "time", "seconds": -1}},
            {"correct": {"action": "time", "seconds": True}},
            {"correct": {"action": "url", "url": ""}},
            {"correct": {"action": "marker", "marker": ""}},
            {"correct": {"action": "url", "url": "x", "marker": "y"}},
        ]
        for value in invalid:
            with self.subTest(value=value), self.assertRaises(ValueError):
                item = spec()
                item["schema_version"] = 2
                item["questions"][0]["feedback"] = value
                quizzes.upsert(self.doc, item, 1)
        item = spec()
        item["questions"][0]["feedback"] = {}
        with self.assertRaises(ValueError):
            quizzes.upsert(self.doc, item, 1)
        self.assertEqual(self.doc, document())

    def test_all_native_question_types_escape_text_and_encode_answer_keys(self) -> None:
        before = copy.deepcopy(self.doc)
        result = quizzes.upsert(self.doc, spec(), "3/2")
        quiz = root(result)
        self.assertEqual(quiz.getAttribute("name"), "Café & <JSON> — quiz")
        questions = quizzes.children(quizzes.children(quiz, "Questions")[0])
        self.assertEqual(
            [q.tagName for q in questions],
            ["MultipleChoice", "Logical", "FillBlank", "ShortAnswer"],
        )
        self.assertEqual(questions[0].getAttribute("text"), 'Pick "four" & 4 < 5')
        self.assertEqual(questions[1].getAttribute("istrue"), "0")
        self.assertEqual(
            [
                a.getAttribute("iscorrect")
                for a in quizzes.children(quizzes.children(questions[0], "Answers")[0])
            ],
            ["1", "0"],
        )
        self.assertEqual(
            [
                a.getAttribute("text")
                for a in quizzes.children(quizzes.children(questions[2], "Answers")[0])
            ],
            ["4", "four"],
        )
        self.assertEqual(quizzes.children(questions[-1], "Answers"), [])
        frame = result["timeline"]["parameters"]["quiz"]["keyframes"][0]
        self.assertEqual((frame["time"], frame["endTime"], frame["duration"]), (1500, 1500, 0))
        self.assertEqual(result["metadata"]["QuizCount"], {"type": "int", "value": 1})
        self.assertEqual(self.doc, before)
        self.assertEqual(quizzes.remove(result, "1001"), before)

    def test_multiple_quizzes_retime_in_order_and_count_quizzes_not_questions(self) -> None:
        result = quizzes.upsert(self.doc, spec(), 3)
        result = quizzes.upsert(result, spec(1002), 1)
        self.assertEqual(
            [(q["id"], q["time"]) for q in quizzes.inventory(result)],
            [("1002", 1000), ("1001", 3000)],
        )
        result = quizzes.upsert(result, spec(1002), 5)
        self.assertEqual(
            [(q["id"], q["time"]) for q in quizzes.inventory(result)],
            [("1001", 3000), ("1002", 5000)],
        )
        self.assertEqual(result["metadata"]["QuizCount"]["value"], 2)
        removed = quizzes.remove(result, "1001")
        self.assertEqual(removed["metadata"]["QuizCount"]["value"], 1)
        self.assertEqual(quizzes.remove(removed, "1002"), self.doc)

    def test_upsert_and_remove_are_idempotent(self) -> None:
        result = quizzes.upsert(self.doc, spec(), 1)
        self.assertEqual(quizzes.upsert(result, spec(), 1), result)
        self.assertEqual(quizzes.remove(result, "absent"), result)
        self.assertEqual(quizzes.remove(self.doc, "1001"), self.doc)

    def test_survey_flags_are_explicit_and_omitted_options_preserve_existing_values(self) -> None:
        survey = spec()
        survey.update(graded=False, feedback=False)
        result = quizzes.upsert(self.doc, survey, 1)
        result = quizzes.upsert(result, spec(), 1)
        options = quizzes.children(root(result), "Options")[0]
        self.assertEqual(
            (options.getAttribute("graded"), options.getAttribute("feedback")), ("0", "0")
        )

    def test_unknown_xml_namespaces_attributes_children_comments_and_pis_survive(self) -> None:
        doc = quizzes.upsert(self.doc, spec(), 1)
        original_xml = """<?native keep?><Quiz xmlns:x="urn:future" id="1001" name="Old" x:flag="x:Value"><Options graded="0" feedback="0" x:kind="x:Kind"/><!--retain--><x:RootThing/><Questions><MultipleChoice id="101" text="Old" x:mode="x:Mode" feedback="1"><Answers x:order="retain"><Answer id="1" text="old" iscorrect="0" x:weight="keep"/><x:AnswerThing/></Answers><x:QuestionThing/></MultipleChoice><x:FutureQuestion id="900" text="unfamiliar"/></Questions></Quiz>"""
        frame = doc["timeline"]["parameters"]["quiz"]["keyframes"][0]
        frame.update(value=original_xml, opaque={"keep": "frame"})
        doc["timeline"]["parameters"]["quiz"]["futureParameter"] = "keep"
        doc["metadata"]["QuizCount"]["futureCount"] = "keep"
        result = quizzes.upsert(doc, spec(), 2)
        xml = result["timeline"]["parameters"]["quiz"]["keyframes"][0]["value"]
        for token in (
            "<?native keep?>",
            'xmlns:x="urn:future"',
            'x:flag="x:Value"',
            "<!--retain-->",
            "<x:RootThing/>",
            "<x:QuestionThing/>",
            "<x:AnswerThing/>",
            'x:weight="keep"',
            '<x:FutureQuestion id="900"',
        ):
            self.assertIn(token, xml)
        self.assertEqual(result["timeline"]["parameters"]["quiz"]["futureParameter"], "keep")
        self.assertEqual(
            result["timeline"]["parameters"]["quiz"]["keyframes"][0]["opaque"], {"keep": "frame"}
        )
        self.assertEqual(result["metadata"]["QuizCount"]["futureCount"], "keep")
        self.assertEqual(
            doc["timeline"]["parameters"]["quiz"]["keyframes"][0]["value"], original_xml
        )

    def test_known_cohorts_are_replaced_in_requested_order(self) -> None:
        result = quizzes.upsert(self.doc, spec(), 1)
        changed = spec()
        changed["questions"] = [changed["questions"][2], changed["questions"][0]]
        changed["questions"][1]["answers"] = list(reversed(changed["questions"][1]["answers"]))
        result = quizzes.upsert(result, changed, 1)
        questions = quizzes.children(quizzes.children(root(result), "Questions")[0])
        self.assertEqual([q.getAttribute("id") for q in questions], ["105", "101"])
        self.assertEqual(
            [
                a.getAttribute("id")
                for a in quizzes.children(quizzes.children(questions[1], "Answers")[0])
            ],
            ["2", "1"],
        )

    def test_question_kind_changes_require_explicit_new_identity(self) -> None:
        result = quizzes.upsert(self.doc, spec(), 1)
        changed = spec()
        changed["questions"][0] = {"id": 101, "kind": "short-answer", "text": "Replacement"}
        with self.assertRaisesRegex(ValueError, "new question ID"):
            quizzes.upsert(result, changed, 1)
        changed["questions"][0]["id"] = 109
        self.assertEqual(
            quizzes.inventory(quizzes.upsert(result, changed, 1))[0]["questions"][0]["id"], "109"
        )

    def test_media_owned_quizzes_are_counted_preserved_edited_and_removed(self) -> None:
        doc = copy.deepcopy(self.doc)
        media = project.scene_tracks(doc)[0][0]["medias"][0]
        media.update(start=1000, duration=5000, mediaStart=1000, mediaDuration=5000, scalar=1)
        media["parameters"]["quiz"] = {
            "type": "string",
            "keyframes": [
                {
                    "time": 2000,
                    "endTime": 2000,
                    "duration": 0,
                    "value": quizzes.build_xml(spec(2001)),
                }
            ],
        }
        result = quizzes.upsert(doc, spec(), 1)
        self.assertEqual(result["metadata"]["QuizCount"]["value"], 2)
        self.assertEqual(
            project.scene_tracks(result)[0][0]["medias"], project.scene_tracks(doc)[0][0]["medias"]
        )
        edited = quizzes.upsert(result, spec(2001), 3)
        media_quiz = next(q for q in quizzes.inventory(edited) if q["id"] == "2001")
        self.assertEqual((media_quiz["ownerId"], media_quiz["time"]), (3, 3000))
        removed = quizzes.remove(edited, "2001")
        self.assertEqual([q["id"] for q in quizzes.inventory(removed)], ["1001"])
        self.assertEqual(removed["metadata"]["QuizCount"]["value"], 1)

    def test_pin_and_unpin_preserve_xml_identity_and_unrelated_linked_fields(self) -> None:
        original = quizzes.upsert(linked_document(), spec(), 4)
        frozen = copy.deepcopy(original)
        pinned = quizzes.upsert(original, spec(), 3, owner_id=9)
        self.assertEqual(original, frozen)
        self.assertNotIn("quiz", pinned["timeline"]["parameters"])
        inventory = quizzes.inventory(pinned)
        self.assertEqual(
            (inventory[0]["id"], inventory[0]["ownerId"], inventory[0]["time"]), ("1001", 3, 3000)
        )
        self.assertTrue(inventory[0]["ownerPath"].endswith("/video"))
        self.assertEqual(
            quizzes.entries(pinned)[0]["frame"]["value"],
            quizzes.entries(original)[0]["frame"]["value"],
        )
        self.assertEqual(quizzes.upsert(pinned, spec(), 4, owner_id=2), original)
        self.assertEqual(quizzes.remove(pinned, "1001"), linked_document())

    def test_physical_video_and_wrapper_ids_select_one_parameter_owner(self) -> None:
        doc = linked_document()
        self.assertEqual(
            quizzes.upsert(doc, spec(), 3, owner_id=3), quizzes.upsert(doc, spec(), 3, owner_id=9)
        )
        pinned = quizzes.upsert(doc, spec(), 3, owner_id=9)
        retimed = quizzes.upsert(pinned, spec(), "7/2")
        self.assertEqual(quizzes.inventory(retimed)[0]["time"], 3500)
        self.assertEqual(quizzes.inventory(retimed)[0]["ownerId"], 3)
        self.assertEqual(quizzes.upsert(retimed, spec(), "7/2"), retimed)
        for point in (0, 8):
            with self.subTest(point=point), self.assertRaisesRegex(ValueError, "visible"):
                quizzes.upsert(pinned, spec(), point)

    def test_move_preserves_global_time_and_exact_xml_without_reauthoring_questions(self) -> None:
        doc = quizzes.upsert(linked_document(), spec(), "9/2")
        frame = quizzes.entries(doc)[0]["frame"]
        frame["value"] = frame["value"].replace(
            "<Questions>",
            '<Questions><!-- exact whitespace -->\n<x:Future xmlns:x="urn:future" id="999"/>',
        )
        frame["extension"] = {"keep": True}
        frozen = copy.deepcopy(doc)
        moved = quizzes.move(doc, "1001", 9)
        entry = quizzes.entries(moved)[0]
        self.assertEqual((entry["ownerId"], entry["time"]), (3, 3500))
        self.assertEqual(entry["frame"]["value"], frame["value"])
        self.assertEqual(entry["frame"]["extension"], {"keep": True})
        self.assertEqual(quizzes.move(moved, "1001", 2), doc)
        self.assertEqual(quizzes.move(moved, "1001", 9), moved)
        self.assertEqual(doc, frozen)

    def test_move_can_choose_explicit_global_or_owner_time(self) -> None:
        doc = quizzes.upsert(linked_document(), spec(), 4)
        by_global = quizzes.move(doc, "1001", 9, global_seconds="9/2")
        by_owner = quizzes.move(doc, "1001", 9, seconds="7/2")
        self.assertEqual(by_global, by_owner)
        self.assertEqual(quizzes.inventory(by_global)[0]["time"], 3500)
        with self.assertRaisesRegex(ValueError, "not both"):
            quizzes.move(doc, "1001", 9, seconds=3, global_seconds=4)
        with self.assertRaisesRegex(ValueError, "existing quiz"):
            quizzes.move(doc, "absent", 9)
        invalid_owners: tuple[Any, ...] = (None, True, 999, 10)
        for owner in invalid_owners:
            with self.subTest(owner=owner), self.assertRaises(ValueError):
                quizzes.move(doc, "1001", owner)

    def test_move_inverse_maps_trimmed_and_retimed_nested_clocks_exactly(self) -> None:
        doc = linked_document()
        medias = project.scene_tracks(doc)[0][0]["medias"]
        linked = medias[0]
        for node in (linked, linked["video"]):
            node.update(start=0, duration=4000, mediaStart=2000, mediaDuration=4000)
        medias[0] = {
            "id": 20,
            "_type": "Group",
            "start": 8000,
            "duration": 2000,
            "mediaStart": 0,
            "mediaDuration": 4000,
            "scalar": "1/2",
            "parameters": {},
            "tracks": [{"medias": [linked]}],
        }
        original = quizzes.upsert(doc, spec(), "17/2")
        moved = quizzes.move(original, "1001", 3)
        self.assertEqual(quizzes.inventory(moved)[0]["time"], 3000)
        self.assertEqual(quizzes.move(moved, "1001", 2), original)
        for target in (7, 11):
            with self.subTest(target=target), self.assertRaisesRegex(ValueError, "visible"):
                quizzes.move(original, "1001", 3, global_seconds=target)
        # A 2/3 scalar maps an odd global tick to a fractional source tick.
        medias = project.scene_tracks(doc)[0][0]["medias"]
        medias[0]["scalar"] = "2/3"
        fractional = quizzes.upsert(doc, spec(), "8001/1000")
        with self.assertRaisesRegex(ValueError, "between owner ticks"):
            quizzes.move(fractional, "1001", 3)

    def test_clip_transfer_preserves_extension_fields_on_empty_original_parameter(self) -> None:
        doc = quizzes.upsert(linked_document(), spec(), 4)
        parameter = doc["timeline"]["parameters"]["quiz"]
        parameter["future"] = {"keep": True}
        parameter["keyframes"][0]["futurePoint"] = "keep"
        pinned = quizzes.upsert(doc, spec(), 3, owner_id=9)
        self.assertEqual(
            pinned["timeline"]["parameters"]["quiz"],
            {"type": "string", "keyframes": [], "future": {"keep": True}},
        )
        self.assertEqual(quizzes.entries(pinned)[0]["frame"]["futurePoint"], "keep")
        self.assertEqual(quizzes.upsert(pinned, spec(), 4, owner_id=2), doc)

    def test_owner_transfer_refuses_collision_unknown_audio_or_ambiguous_ids(self) -> None:
        doc = quizzes.upsert(linked_document(), spec(), 3, owner_id=9)
        doc = quizzes.upsert(doc, spec(1002), 5)
        frozen = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "unoccupied"):
            quizzes.upsert(doc, spec(1002), 3, owner_id=9)
        for owner in (10, 999, True):
            with self.subTest(owner=owner), self.assertRaises(ValueError):
                quizzes.upsert(doc, spec(1003), 3, owner_id=owner)
        self.assertEqual(doc, frozen)
        ambiguous = linked_document()
        project.scene_tracks(ambiguous)[0][0]["medias"][0]["id"] = 2
        with self.assertRaisesRegex(ValueError, "unique"):
            quizzes.upsert(ambiguous, spec(), 3, owner_id=2)
        unsupported = quizzes.upsert(linked_document(), spec(), 3, owner_id=9)
        project.scene_tracks(unsupported)[0][0]["medias"][0]["video"]["_type"] = "ScreenIMFile"
        for operation in (
            lambda: quizzes.upsert(unsupported, spec(), 4, owner_id=2),
            lambda: quizzes.remove(unsupported, "1001"),
        ):
            with self.assertRaisesRegex(ValueError, "constructor"):
                operation()

    def test_nested_group_clock_is_checked_without_flattening_or_double_mirroring(self) -> None:
        doc = linked_document()
        medias = project.scene_tracks(doc)[0][0]["medias"]
        linked = medias[0]
        for node in (linked, linked["video"]):
            node.update(start=0, duration=4000, mediaStart=2000, mediaDuration=4000)
        medias[0] = {
            "id": 20,
            "_type": "Group",
            "start": 8000,
            "duration": 2000,
            "mediaStart": 0,
            "mediaDuration": 4000,
            "scalar": "1/2",
            "parameters": {},
            "tracks": [{"medias": [linked]}],
        }
        frozen = copy.deepcopy(doc)
        result = quizzes.upsert(doc, spec(), 3, owner_id=9)
        self.assertEqual(quizzes.inventory(result)[0]["time"], 3000)
        self.assertEqual(doc, frozen)
        self.assertEqual(quizzes.remove(result, "1001"), doc)
        with self.assertRaisesRegex(ValueError, "visible"):
            quizzes.upsert(doc, spec(), 1, owner_id=9)

    def test_multiple_scene_clocks_require_native_mapping_before_media_edit(self) -> None:
        doc = linked_document()
        doc["timeline"]["sceneTrack"]["scenes"].append({"csml": {"tracks": []}})
        with self.assertRaisesRegex(ValueError, "multiple scene"):
            quizzes.upsert(doc, spec(), 3, owner_id=9)

    def test_duplicate_quiz_ids_and_occupied_times_refuse_without_changes(self) -> None:
        result = quizzes.upsert(self.doc, spec(), 1)
        before = copy.deepcopy(result)
        with self.assertRaisesRegex(ValueError, "unoccupied"):
            quizzes.upsert(result, spec(1002), 1)
        self.assertEqual(result, before)
        parameter = result["timeline"]["parameters"]["quiz"]
        parameter["keyframes"].append(copy.deepcopy(parameter["keyframes"][0]))
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            quizzes.inventory(result)

    def test_invalid_spec_shapes_types_ids_and_answer_keys_are_rejected(self) -> None:
        cases: list[dict[str, Any]] = []
        for key, value in (
            ("schema_version", True),
            ("schema_version", 4),
            ("owner", "other"),
            ("id", True),
            ("id", 0),
            ("name", ""),
            ("graded", 1),
            ("feedback", "0"),
            ("questions", []),
            ("misspelled", True),
        ):
            item = spec()
            item[key] = value
            cases.append(item)
        for mutation in (
            "duplicate-question",
            "duplicate-answer",
            "missing-correct",
            "no-correct",
            "multiple-correct",
            "wrong-kind",
            "wrong-true",
            "blank-wrong",
            "short-answers",
            "unknown-question-field",
        ):
            item = spec()
            if mutation == "duplicate-question":
                item["questions"][1]["id"] = 101
            elif mutation == "duplicate-answer":
                item["questions"][0]["answers"][1]["id"] = 1
            elif mutation == "missing-correct":
                item["questions"][0]["answers"][0].pop("correct")
            elif mutation == "no-correct":
                item["questions"][0]["answers"][0]["correct"] = False
            elif mutation == "multiple-correct":
                item["questions"][0]["answers"][1]["correct"] = True
            elif mutation == "wrong-kind":
                item["questions"][0]["kind"] = []
            elif mutation == "wrong-true":
                item["questions"][1]["true"] = "false"
            elif mutation == "blank-wrong":
                item["questions"][2]["answers"][0]["correct"] = False
            elif mutation == "short-answers":
                item["questions"][3]["answers"] = []
            else:
                item["questions"][0]["typo"] = True
            cases.append(item)
        for item in cases:
            with self.subTest(spec=item), self.assertRaises(ValueError):
                quizzes.upsert(self.doc, item, 1)
        self.assertEqual(self.doc, document())

    def test_native_xml_ambiguity_malformed_points_and_dtds_are_not_overwritten(self) -> None:
        for xml in (
            "<Quiz",
            '<Other id="1"/>',
            "<Quiz/>",
            '<!DOCTYPE Quiz [<!ENTITY x "x">]><Quiz id="1"/>',
        ):
            with self.subTest(xml=xml), self.assertRaises(ValueError):
                quizzes.parse_xml(xml)
        for field, value in (("duration", 1), ("endTime", 3000), ("value", None)):
            result = quizzes.upsert(self.doc, spec(), 1)
            result["timeline"]["parameters"]["quiz"]["keyframes"][0][field] = value
            with self.assertRaises(ValueError):
                quizzes.upsert(result, spec(), 1)
        result = quizzes.upsert(self.doc, spec(), 1)
        result["timeline"]["parameters"]["quiz"]["keyframes"][0]["value"] = (
            '<Quiz id="1001"><Options/><Options/><Questions/></Quiz>'
        )
        with self.assertRaisesRegex(ValueError, "ambiguous"):
            quizzes.upsert(result, spec(), 1)

    def test_unknown_question_id_collision_and_duplicate_native_answers_are_refused(self) -> None:
        for xml in (
            '<Quiz id="1001"><Questions><Future id="101"/></Questions></Quiz>',
            '<Quiz id="1001"><Questions><MultipleChoice id="101"><Answers><Answer id="1"/><Answer id="1"/></Answers></MultipleChoice></Questions></Quiz>',
        ):
            result = quizzes.upsert(self.doc, spec(), 1)
            result["timeline"]["parameters"]["quiz"]["keyframes"][0]["value"] = xml
            with self.assertRaises(ValueError):
                quizzes.upsert(result, spec(), 1)

    def test_invalid_xml_characters_are_refused_instead_of_emitting_broken_xml(self) -> None:
        for value in ("bad\x00text", "bad\ud800text"):
            item = spec()
            item["questions"][0]["text"] = value
            with self.subTest(value=repr(value)), self.assertRaises(ValueError):
                quizzes.upsert(self.doc, item, 1)

    def test_build_canvas_and_fractional_tick_boundaries_are_explicit(self) -> None:
        for key, value in (("version", "9.0"), ("width", 639), ("height", 479)):
            doc = copy.deepcopy(self.doc)
            doc[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                quizzes.upsert(doc, spec(), 1)
        for value in (True, -1, "1/3", "1/0"):
            with self.subTest(value=value), self.assertRaises(ValueError):
                quizzes.upsert(self.doc, spec(), value)

    def test_count_extension_metadata_survives_last_quiz_removal(self) -> None:
        result = quizzes.upsert(self.doc, spec(), 1)
        result["metadata"]["QuizCount"]["future"] = "keep"
        removed = quizzes.remove(result, "1001")
        self.assertEqual(
            removed["metadata"]["QuizCount"], {"type": "int", "value": 0, "future": "keep"}
        )


class QuizCLITests(unittest.TestCase):
    def test_cli_schema_two_feedback_stages_native_xml_without_rewriting_input(self) -> None:
        item = spec()
        item["schema_version"] = 2
        item["questions"][0]["feedback"] = {
            "enabled": True,
            "wrong": {"text": "Try café & <XML>.", "action": "time", "seconds": "13/2"},
        }
        self.spec.write_text(json.dumps(item))
        status, out, err = self.invoke(
            "upsert",
            str(self.source),
            "--spec",
            str(self.spec),
            "--time",
            "1",
            "--output",
            str(self.output),
        )
        self.assertEqual((status, err), (0, ""))
        self.assertFalse(json.loads(out)["nativeVerified"])
        result = project.load(self.output)[0]
        q = quizzes.children(quizzes.children(root(result), "Questions")[0])[0]
        self.assertEqual(q.getAttribute("fb_wrong_action"), "fb_JumpToTime")
        self.assertEqual(q.getAttribute("fb_wrong_jumptime_ms"), "6500")
        self.assertEqual(q.getAttribute("fb_wrong"), "Try café & <XML>.")
        self.assertEqual(self.file.read_bytes(), self.raw)
        self.assertEqual(json.loads(self.spec.read_text()), item)

    def test_cli_move_pins_and_unpins_without_a_question_spec(self) -> None:
        original = quizzes.upsert(linked_document(), spec(), "9/2")
        self.file.write_bytes(project.encode_document(original))
        status, out, err = self.invoke(
            "move",
            str(self.source),
            "--quiz-id",
            "1001",
            "--owner-id",
            "9",
            "--output",
            str(self.output),
        )
        self.assertEqual((status, err), (0, ""))
        self.assertEqual(json.loads(out)["quizzes"][0]["time"], 3500)
        restored = self.output.with_name("restored.json")
        status, out, err = self.invoke(
            "move",
            str(self.output),
            "--quiz-id",
            "1001",
            "--owner-id",
            "2",
            "--output",
            str(restored),
        )
        self.assertEqual((status, err), (0, ""))
        self.assertEqual(project.load(restored)[0], original)
        self.assertEqual(project.load(self.file)[0], original)

    def test_cli_selects_a_media_owner_then_transfers_to_timeline_without_source_changes(
        self,
    ) -> None:
        self.file.write_bytes(project.encode_document(linked_document()))
        frozen = self.file.read_bytes()
        status, out, err = self.invoke(
            "upsert",
            str(self.source),
            "--spec",
            str(self.spec),
            "--time",
            "3",
            "--owner-id",
            "9",
            "--output",
            str(self.output),
        )
        self.assertEqual((status, err), (0, ""))
        row = json.loads(out)["quizzes"][0]
        self.assertEqual((row["ownerId"], row["time"]), (3, 3000))
        destination = self.output.with_name("timeline.json")
        status, out, err = self.invoke(
            "upsert",
            str(self.output),
            "--spec",
            str(self.spec),
            "--time",
            "4",
            "--owner-id",
            "2",
            "--output",
            str(destination),
        )
        self.assertEqual((status, err), (0, ""))
        row = json.loads(out)["quizzes"][0]
        self.assertEqual((row["ownerPath"], row["time"]), ("/timeline", 4000))
        self.assertEqual(self.file.read_bytes(), frozen)

    def setUp(self) -> None:
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.root = Path(temp.name)
        self.source = self.root / "film.cmproj"
        self.source.mkdir()
        self.file = self.source / "project.tscproj"
        self.doc = document()
        self.raw = project.encode_document(self.doc)
        self.file.write_bytes(self.raw)
        self.spec = self.root / "spec.json"
        self.spec.write_text(json.dumps(spec()))
        self.output = self.root / "candidate.json"

    def invoke(self, *args: str):
        out, err = io.StringIO(), io.StringIO()
        with patch("sys.stdout", out), patch("sys.stderr", err):
            status = quizzes.main(list(args))
        return status, out.getvalue(), err.getvalue()

    def test_cli_stages_and_reruns_without_reading_media_or_changing_original(self) -> None:
        args = (
            "upsert",
            str(self.source),
            "--spec",
            str(self.spec),
            "--time",
            "1",
            "--output",
            str(self.output),
        )
        status, out, err = self.invoke(*args)
        self.assertEqual((status, err), (0, ""))
        report = json.loads(out)
        self.assertEqual((report["schema_version"], report["owner"]), (1, "camtasia-quizzes"))
        self.assertTrue(report["written"])
        self.assertFalse(report["nativeVerified"])
        self.assertEqual(report["projectSha256"], project.digest(self.raw))
        status, out, _ = self.invoke(*args)
        self.assertEqual(status, 0)
        self.assertFalse(json.loads(out)["written"])
        self.assertEqual(self.file.read_bytes(), self.raw)
        status, out, err = self.invoke("inspect", str(self.output))
        self.assertEqual((status, err), (0, ""))
        self.assertEqual(len(json.loads(out)["quizzes"][0]["questions"]), 4)

    def test_cli_remove_restores_payload_and_refuses_output_collisions(self) -> None:
        self.file.write_bytes(project.encode_document(quizzes.upsert(self.doc, spec(), 1)))
        status, out, err = self.invoke(
            "remove", str(self.source), "--quiz-id", "1001", "--output", str(self.output)
        )
        self.assertEqual((status, err), (0, ""))
        self.assertEqual(project.load(self.output)[0], self.doc)
        for output in (self.file, self.output):
            status, out, err = self.invoke(
                "upsert",
                str(self.source),
                "--spec",
                str(self.spec),
                "--time",
                "2",
                "--output",
                str(output),
            )
            self.assertEqual((status, out), (1, ""))
            self.assertFalse(json.loads(err)["ok"])

    def test_cli_errors_are_json_and_create_no_partial_candidate(self) -> None:
        self.spec.write_text('{"schema_version":1,"id":1,"id":2}')
        status, out, err = self.invoke(
            "upsert",
            str(self.source),
            "--spec",
            str(self.spec),
            "--time",
            "1",
            "--output",
            str(self.output),
        )
        self.assertEqual((status, out), (1, ""))
        self.assertIn("duplicate JSON key", json.loads(err)["error"])
        self.assertFalse(self.output.exists())
        self.assertEqual(self.file.read_bytes(), self.raw)

    def test_native_loudness_literal_and_unrelated_unicode_survive_staging(self) -> None:
        self.doc["sourceBin"][0]["sourceTracks"] = [
            {"type": 2, "integratedLUFS": project.NativeLoudnessSentinel("-1.79769313486232e+308")}
        ]
        self.file.write_bytes(project.encode_document(self.doc))
        status, _, err = self.invoke(
            "upsert",
            str(self.source),
            "--spec",
            str(self.spec),
            "--time",
            "1",
            "--output",
            str(self.output),
        )
        self.assertEqual((status, err), (0, ""))
        self.assertIn(b'"integratedLUFS":-1.79769313486232e+308', self.output.read_bytes())
        self.assertEqual(project.load(self.output)[0]["future"], self.doc["future"])


if __name__ == "__main__":
    unittest.main()
