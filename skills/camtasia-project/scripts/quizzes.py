#!/usr/bin/env python3
"""Inspect and stage native timeline/media quizzes without opening Camtasia.

Mac 2026.2.4, format 10.0. Quiz points contain native XML, not question JSON.
Authoring specs are schema_version 1, 2 or 3, owner camtasia-quiz-spec: id (positive
integer), name, questions; optional graded/feedback booleans. Each question has
id, kind and text. QUESTION_TAGS owns kind names. Multiple-choice and fill-blank
questions have answers [{id, text, correct}]; true-false has a true boolean.
Short answers have no answer key. IDs are unique within their native parent.
Schema 2 adds optional question.feedback patches: enabled (bool), correct/wrong
objects with optional text and action. Actions continue, url, time, marker use
no destination, url (text), seconds (exact nonnegative milliseconds), or marker
(existing native markerIdentifier), respectively. Omitted feedback fields retain
their native values, including inactive destinations. Marker time is resolved
from the project's existing point/owner clock; no marker is created or retimed.
Root feedback controls viewer results; question.feedback controls responses.
Multiple-choice questions require exactly one correct answer: the observed
native exporter silently retains only the last when several are marked.
Schema 3 permits omitted grading keys only with explicit graded:false. Choice
answers may all omit correct: retain a single surviving inactive native key,
otherwise store the first choice as the key required by the Mac exporter.
Never store zero choice keys: the native export omits its player configuration.
True/false may omit true (retain the native value; new questions use false).
Fill-blank may omit answers (retain existing; new questions use an empty list),
or explicitly use [] to clear its keys. Supplied fill-blank answers may omit
correct and default to true. Schema 1/2 keep their original strict key contract.

Upsert replaces the selected quiz's known question/answer lists. Reused IDs
retain unfamiliar attributes/children; unfamiliar element types and namespace
prefixes survive. Changing an existing question's kind requires a new ID.
Root options omitted by the spec retain existing values. Other quiz owners,
source media and unrelated JSON survive. Existing quizzes retain their owner
unless --owner-id selects a different timeline/visual owner. New quizzes default
to the timeline. --time is seconds in the chosen owner's parameter clock, not
always global time. Linked video storage uses its UnifiedMedia clock once.
Owner IDs from inspect remain physical parameter-owner IDs; a UnifiedMedia ID
can also select its video. The observed visual constructors are VISUAL_TYPES.
Native XML comments/PIs survive. DTD-bearing input requires manual inspection.

CLI: inspect PROJECT; upsert PROJECT --spec JSON --time SECONDS --output FILE
[--owner-id ID];
remove PROJECT --quiz-id ID --output FILE. Times are exact rational seconds.
move PROJECT --quiz-id ID --owner-id ID --output FILE preserves global time
and the exact XML string by default. Optional --time OWNER_SECONDS or
--global-time SECONDS selects a new point; the two options are exclusive.
Candidate files never replace originals; identical reruns are no-ops. Stdout
schema_version 1, owner camtasia-quizzes, hashes/outcome, nativeVerified false.
Exit 0 success, 1 input/I/O refusal, 2 argument syntax. Apply staged candidates
through project.py's ordinary guarded workflow, then verify native player/LMS.
This does not render, export, contact an LMS or certify SCORM conformance.
"""

from __future__ import annotations

import argparse
import copy
import json
from pathlib import Path
import sys
from typing import Any, cast
from xml.dom import minidom
from xml.parsers.expat import ExpatError

import hotspots
import project

QUESTION_TAGS = {
    "multiple-choice": "MultipleChoice",
    "true-false": "Logical",
    "fill-blank": "FillBlank",
    "short-answer": "ShortAnswer",
}
FEEDBACK_ACTIONS = {
    "continue": "",
    "url": "fb_GoToURL",
    "time": "fb_JumpToTime",
    "marker": "fb_JumpToMarker",
}
QUESTION_ATTRIBUTES = {
    "collapsed": "0",
    "feedback": "0",
    **{
        f"fb_{outcome}{suffix}": value
        for outcome in ("correct", "wrong")
        for suffix, value in (
            ("", ""),
            ("_action", ""),
            ("_jumptime_ms", "0"),
            ("_url", ""),
            ("_marker", ""),
            ("_marker_time", "0"),
        )
    },
}
MIN_CANVAS = (640, 480)
VISUAL_TYPES = frozenset({"VMFile", "IMFile", "ScreenVMFile", "Callout", "Group"})


def children(node: minidom.Element, tag: str | None = None) -> list[minidom.Element]:
    return [
        child
        for child in node.childNodes
        if isinstance(child, minidom.Element) and (tag is None or child.tagName == tag)
    ]


def one_child(node: minidom.Element, tag: str) -> minidom.Element:
    matches = children(node, tag)
    if len(matches) > 1:
        raise ValueError(f"inspect ambiguous native {tag} elements before editing")
    if matches:
        return matches[0]
    document = node.ownerDocument
    if document is None:
        raise ValueError("parse a complete native Quiz XML document before editing")
    child = document.createElement(tag)
    node.appendChild(child)
    return child


def xml_root(document: minidom.Document) -> minidom.Element:
    root = document.documentElement
    if root is None:
        raise ValueError("use a complete native Quiz XML document")
    return root


def parse_xml(value: Any) -> minidom.Document:
    if not isinstance(value, str):
        raise ValueError("repair the quiz point's XML string before editing")
    try:
        document = minidom.parseString(value)
    except (ExpatError, UnicodeError) as exc:
        raise ValueError(f"repair malformed quiz XML: {exc}") from exc
    if document.doctype is not None:
        raise ValueError("inspect DTD-bearing quiz XML instead of rewriting it automatically")
    root = xml_root(document)
    if root.tagName != "Quiz" or not root.getAttribute("id"):
        raise ValueError("use native Quiz XML with an explicit id")
    return document


def entries(doc: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    seen = set()
    for path, node in project.objects(doc.get("timeline", {}), "/timeline"):
        parameters = node.get("parameters")
        if not isinstance(parameters, dict) or "quiz" not in parameters:
            continue
        parameter = parameters["quiz"]
        if (
            not isinstance(parameter, dict)
            or parameter.get("type") != "string"
            or not isinstance(parameter.get("keyframes"), list)
        ):
            raise ValueError(f"{path}: inspect unfamiliar quiz parameter encoding")
        for index, frame in enumerate(parameter["keyframes"]):
            if not isinstance(frame, dict):
                raise ValueError(f"{path}: repair quiz point {index}")
            time = project.number(frame.get("time"))
            if (
                time < 0
                or time.denominator != 1
                or project.number(frame.get("endTime")) != time
                or project.number(frame.get("duration")) != 0
            ):
                raise ValueError(f"{path}: inspect unsupported quiz point timing")
            xml = parse_xml(frame.get("value"))
            qid = xml_root(xml).getAttribute("id")
            if qid in seen:
                raise ValueError(f"quiz id {qid} is ambiguous; repair duplicate quiz IDs")
            seen.add(qid)
            result.append(
                {
                    "ownerPath": path,
                    "ownerId": node.get("id"),
                    "frame": frame,
                    "index": index,
                    "time": time.numerator,
                    "id": qid,
                    "xml": xml,
                }
            )
    return result


def inventory(doc: dict[str, Any]) -> list[dict[str, Any]]:
    result = []
    for entry in entries(doc):
        root = xml_root(entry["xml"])
        questions = children(root, "Questions")
        if len(questions) > 1:
            raise ValueError("inspect ambiguous Questions elements")
        result.append(
            {
                "id": entry["id"],
                "name": root.getAttribute("name"),
                "ownerId": entry["ownerId"],
                "ownerPath": entry["ownerPath"],
                "time": entry["time"],
                "questions": [
                    {"id": q.getAttribute("id"), "type": q.tagName, "text": q.getAttribute("text")}
                    for q in children(questions[0])
                ]
                if questions
                else [],
            }
        )
    return result


def identifier(value: Any, label: str) -> str:
    if type(value) is not int or value <= 0:
        raise ValueError(f"{label}: supply a positive integer ID")
    return str(value)


def text(value: Any, label: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{label}: supply nonempty text")
    return value


def milliseconds(value: Any) -> str:
    result = project.number(value) * 1000
    if result < 0 or result.denominator != 1:
        raise ValueError("choose nonnegative feedback seconds on an exact millisecond")
    return str(result.numerator)


def validate_feedback(value: Any) -> None:
    if not isinstance(value, dict) or set(value) - {"enabled", "correct", "wrong"}:
        raise ValueError("use feedback enabled/correct/wrong fields")
    if "enabled" in value and type(value["enabled"]) is not bool:
        raise ValueError("feedback enabled must be a boolean")
    for outcome in ("correct", "wrong"):
        if outcome not in value:
            continue
        branch = value[outcome]
        if not isinstance(branch, dict) or set(branch) - {
            "text",
            "action",
            "url",
            "seconds",
            "marker",
        }:
            raise ValueError("use documented feedback text/action/destination fields")
        if "text" in branch and not isinstance(branch["text"], str):
            raise ValueError("feedback text must be a string; empty clears it")
        action = branch.get("action")
        targets = set(branch) & {"url", "seconds", "marker"}
        if "action" not in branch and not targets:
            continue
        if not isinstance(action, str) or action not in FEEDBACK_ACTIONS:
            raise ValueError("choose a documented feedback action")
        expected = {"url": "url", "time": "seconds", "marker": "marker"}.get(action)
        if targets != ({expected} if expected else set()):
            raise ValueError("supply only the chosen feedback action's required destination")
        if action == "time":
            milliseconds(branch["seconds"])
        elif expected:
            text(branch[expected], "feedback destination")


def feedback_marker(doc: dict[str, Any], identifier: str) -> str:
    matches = []
    for marker in hotspots.markers(doc):
        frame: Any = doc
        for part in marker["path"].strip("/").split("/"):
            frame = frame[int(part)] if isinstance(frame, list) else frame[part]
        metadata = frame.get("metadata", {})
        if not isinstance(metadata, dict):
            raise ValueError("inspect unfamiliar marker metadata before selecting feedback targets")
        if metadata.get("markerIdentifier") == identifier:
            matches.append(marker)
    if len(matches) != 1:
        raise ValueError("select a unique existing markerIdentifier from the native project")
    marker = matches[0]
    point = (
        marker["time"]
        if marker["timelineMarker"]
        else hotspots.marker_global_ticks(doc, marker["ownerId"], marker["time"])
    )
    rate = project.number(doc["editRate"])
    if rate <= 0:
        raise ValueError("use a positive project edit rate for feedback marker clocks")
    return milliseconds(str(project.number(point) / rate))


def apply_feedback(
    node: minidom.Element, value: dict[str, Any], doc: dict[str, Any] | None
) -> None:
    if "enabled" in value:
        node.setAttribute("feedback", "1" if value["enabled"] else "0")
    for outcome in ("correct", "wrong"):
        branch = value.get(outcome, {})
        prefix = f"fb_{outcome}"
        if "text" in branch:
            node.setAttribute(prefix, branch["text"])
        if "action" not in branch:
            continue
        action = branch["action"]
        node.setAttribute(prefix + "_action", FEEDBACK_ACTIONS[action])
        if action == "url":
            node.setAttribute(prefix + "_url", branch["url"])
        elif action == "time":
            node.setAttribute(prefix + "_jumptime_ms", milliseconds(branch["seconds"]))
        elif action == "marker":
            if doc is None:
                raise ValueError("supply the native project to resolve feedback marker clocks")
            node.setAttribute(prefix + "_marker", branch["marker"])
            node.setAttribute(prefix + "_marker_time", feedback_marker(doc, branch["marker"]))


def validate_spec(spec: dict[str, Any]) -> None:
    if (
        type(spec.get("schema_version")) is not int
        or spec["schema_version"] not in (1, 2, 3)
        or spec.get("owner") != "camtasia-quiz-spec"
    ):
        raise ValueError("use schema_version 1, 2 or 3 and owner camtasia-quiz-spec")
    if set(spec) - {"schema_version", "owner", "id", "name", "questions", "graded", "feedback"}:
        raise ValueError("remove unknown authoring fields; inspect the quiz-spec contract")
    identifier(spec.get("id"), "quiz")
    text(spec.get("name"), "quiz name")
    for option in ("graded", "feedback"):
        if option in spec and type(spec[option]) is not bool:
            raise ValueError(f"{option}: use a boolean")
    questions = spec.get("questions")
    if not isinstance(questions, list) or not questions:
        raise ValueError("supply at least one question, or remove the entire quiz")
    question_ids = set()
    survey = spec["schema_version"] == 3 and spec.get("graded") is False
    for question in questions:
        fields = {
            "id",
            "kind",
            "text",
            "answers",
            "true",
        }
        if spec["schema_version"] >= 2:
            fields.add("feedback")
        if not isinstance(question, dict) or set(question) - fields:
            raise ValueError("use a question object with the documented authoring fields")
        if "feedback" in question:
            validate_feedback(question["feedback"])
        qid = identifier(question.get("id"), "question")
        if qid in question_ids:
            raise ValueError("question IDs must be unique within the quiz")
        question_ids.add(qid)
        kind = question.get("kind")
        if not isinstance(kind, str) or kind not in QUESTION_TAGS:
            raise ValueError("choose a question kind from QUESTION_TAGS")
        text(question.get("text"), "question text")
        if kind == "true-false":
            if (
                ("true" in question or not survey) and type(question.get("true")) is not bool
            ) or "answers" in question:
                raise ValueError("true-false questions require a true boolean and no answer list")
        elif "true" in question:
            raise ValueError("supply true only for true-false questions")
        if kind in ("multiple-choice", "fill-blank"):
            if kind == "fill-blank" and survey and "answers" not in question:
                continue
            answers = question.get("answers")
            if not isinstance(answers, list) or len(answers) < (
                2 if kind == "multiple-choice" else (0 if survey else 1)
            ):
                raise ValueError("supply the question's answer choices or accepted blank answers")
            ids = set()
            correct = 0
            omitted_keys = 0
            for answer in answers:
                if not isinstance(answer, dict) or (
                    set(answer) != {"id", "text", "correct"}
                    and not (survey and set(answer) == {"id", "text"})
                ):
                    raise ValueError("answers require id, text and correct fields")
                aid = identifier(answer["id"], "answer")
                if aid in ids:
                    raise ValueError("answer IDs must be unique within their question")
                ids.add(aid)
                text(answer["text"], "answer text")
                if "correct" not in answer:
                    omitted_keys += 1
                elif type(answer["correct"]) is not bool:
                    raise ValueError("answer correct must be a boolean")
                correct += answer.get("correct", kind == "fill-blank")
                if kind == "fill-blank" and not answer.get("correct", True):
                    raise ValueError("fill-blank lists accepted answers; each must be correct")
            if kind == "multiple-choice" and omitted_keys:
                if omitted_keys != len(answers):
                    raise ValueError("omit all survey choice keys or supply every correct boolean")
                continue
            if not correct and not (survey and kind == "fill-blank"):
                raise ValueError("mark at least one correct answer")
            if kind == "multiple-choice" and correct != 1:
                raise ValueError(
                    "mark exactly one correct multiple-choice answer; native export keeps only the last"
                )
        elif "answers" in question:
            raise ValueError("this question kind takes no answer list")


def replace_known(parent: minidom.Element, tags: set[str], fresh: list[minidom.Element]) -> None:
    old = [node for node in children(parent) if node.tagName in tags]
    siblings = list(parent.childNodes)
    anchor = (
        next((node for node in siblings[siblings.index(old[0]) + 1 :] if node not in old), None)
        if old
        else None
    )
    for node in old:
        parent.removeChild(node)
    for node in fresh:
        parent.insertBefore(node, anchor) if anchor is not None else parent.appendChild(node)


def unique_children(parent: minidom.Element, tags: set[str]) -> dict[str, minidom.Element]:
    result = {}
    for child in children(parent):
        if child.tagName not in tags:
            continue
        cid = child.getAttribute("id")
        if not cid or cid in result:
            raise ValueError("repair missing or duplicate native question/answer IDs")
        result[cid] = child
    return result


def build_xml(
    spec: dict[str, Any],
    existing: minidom.Document | None = None,
    *,
    doc: dict[str, Any] | None = None,
) -> str:
    validate_spec(spec)
    document = parse_xml(existing.toxml()) if existing is not None else minidom.Document()
    if existing is None:
        root = document.createElement("Quiz")
        document.appendChild(root)
    else:
        root = xml_root(document)
    root.setAttribute("id", str(spec["id"]))
    root.setAttribute("name", spec["name"])
    options = one_child(root, "Options")
    for key in ("feedback", "graded"):
        if key in spec or not options.hasAttribute(key):
            options.setAttribute(key, "1" if spec.get(key, True) else "0")
    questions = one_child(root, "Questions")
    old = unique_children(questions, set(QUESTION_TAGS.values()))
    unknown_ids = {
        q.getAttribute("id") for q in children(questions) if q.tagName not in QUESTION_TAGS.values()
    }
    fresh = []
    for question in spec["questions"]:
        qid = str(question["id"])
        tag = QUESTION_TAGS[question["kind"]]
        if qid in unknown_ids:
            raise ValueError("preserve unfamiliar question types; choose a different new ID")
        if qid in old and old[qid].tagName != tag:
            raise ValueError("use a new question ID when changing its kind")
        node = (
            cast(minidom.Element, old[qid].cloneNode(deep=True))
            if qid in old
            else document.createElement(tag)
        )
        node.setAttribute("id", qid)
        node.setAttribute("text", question["text"])
        for key, value in QUESTION_ATTRIBUTES.items():
            if not node.hasAttribute(key):
                node.setAttribute(key, value)
        if "feedback" in question:
            apply_feedback(node, question["feedback"], doc)
        if tag == "Logical":
            if "true" in question or not node.hasAttribute("istrue"):
                node.setAttribute("istrue", "1" if question.get("true", False) else "0")
        if tag in ("MultipleChoice", "FillBlank"):
            answers = one_child(node, "Answers")
            prior = unique_children(answers, {"Answer"})
            if "answers" not in question:
                fresh.append(node)
                continue
            inactive_key = None
            if tag == "MultipleChoice" and all("correct" not in a for a in question["answers"]):
                retained = [
                    str(a["id"])
                    for a in question["answers"]
                    if str(a["id"]) in prior
                    and prior[str(a["id"])].getAttribute("iscorrect") == "1"
                ]
                inactive_key = (
                    retained[0] if len(retained) == 1 else str(question["answers"][0]["id"])
                )
            new_answers = []
            for answer in question["answers"]:
                aid = str(answer["id"])
                child = (
                    cast(minidom.Element, prior[aid].cloneNode(deep=True))
                    if aid in prior
                    else document.createElement("Answer")
                )
                for key, value in {
                    "id": aid,
                    "text": answer["text"],
                    "iscorrect": "1"
                    if answer.get("correct", tag == "FillBlank" or aid == inactive_key)
                    else "0",
                }.items():
                    child.setAttribute(key, value)
                new_answers.append(child)
            replace_known(answers, {"Answer"}, new_answers)
        fresh.append(node)
    replace_known(questions, set(QUESTION_TAGS.values()), fresh)
    encoded = document.toxml()
    parse_xml(encoded)  # Also reject invalid XML characters introduced by spec text.
    return encoded


def require_supported(doc: dict[str, Any]) -> None:
    if doc.get("version") != "10.0" or doc.get("authoringClientName") != hotspots.NATIVE_CLIENT:
        raise ValueError("use the observed Mac 2026.2.4 format-10 quiz contract")


def update_count(doc: dict[str, Any]) -> None:
    metadata = doc.get("metadata")
    if not isinstance(metadata, dict):
        raise ValueError("inspect the native project metadata object before editing quizzes")
    count = len(entries(doc))
    previous = metadata.get("QuizCount", {"type": "int", "value": 0})
    if not isinstance(previous, dict) or previous.get("type") != "int":
        raise ValueError("inspect unfamiliar QuizCount metadata before replacing it")
    if count or set(previous) - {"type", "value"}:
        metadata["QuizCount"] = {**previous, "value": count}
    else:
        metadata.pop("QuizCount", None)


def resolve_owner(
    doc: dict[str, Any], owner_id: int | None
) -> tuple[str, dict[str, Any], int | None]:
    timeline = doc.get("timeline")
    if not isinstance(timeline, dict) or not isinstance(timeline.get("parameters"), dict):
        raise ValueError("inspect the native timeline parameter owner before editing")
    if owner_id is None:
        return "/timeline", timeline, None
    if type(owner_id) is not int:
        raise ValueError("select a numeric owner ID from inspection")
    clips = hotspots.clips(doc)
    matches = [
        (path, node)
        for path, node in [("/timeline", timeline), *clips]
        if node.get("id") == owner_id
    ]
    if len(matches) != 1:
        raise ValueError("select a unique existing timeline/visual owner ID")
    path, node = matches[0]
    if path == "/timeline":
        return path, node, None
    logical_id = owner_id
    if node.get("_type") == "UnifiedMedia":
        path, node = project.pointer(path, "video"), node.get("video")
    else:
        parent = next(
            (
                parent
                for parent_path, parent in clips
                if parent.get("_type") == "UnifiedMedia"
                and path == project.pointer(parent_path, "video")
            ),
            None,
        )
        if parent is not None:
            logical_id = parent.get("id")
    if not isinstance(node, dict) or node.get("_type") not in VISUAL_TYPES:
        raise ValueError("retain this quiz owner until its visual constructor is verified")
    if not isinstance(node.get("parameters"), dict) or type(logical_id) is not int:
        raise ValueError("repair the native visual parameter owner and logical ID")
    return path, node, logical_id


def detach(doc: dict[str, Any], entry: dict[str, Any]) -> None:
    owners = [
        node
        for path, node in project.objects(doc.get("timeline", {}), "/timeline")
        if path == entry["ownerPath"]
    ]
    if len(owners) != 1:
        raise ValueError("recover the quiz's unique physical parameter owner")
    parameters = owners[0]["parameters"]
    parameter = parameters["quiz"]
    parameter["keyframes"].remove(entry["frame"])
    if not parameter["keyframes"] and not set(parameter) - {"type", "keyframes"}:
        parameters.pop("quiz")


def place_frame(
    doc: dict[str, Any],
    existing: dict[str, Any] | None,
    path: str,
    owner: dict[str, Any],
    time: int,
    quiz_id: str,
    value: str | None = None,
) -> None:
    if any(
        entry["ownerPath"] == path and entry["time"] == time and entry["id"] != quiz_id
        for entry in entries(doc)
    ):
        raise ValueError("choose an unoccupied quiz time on this owner")
    moved = existing is not None and existing["ownerPath"] != path
    if moved and existing is not None:
        detach(doc, existing)
    parameter = owner["parameters"].setdefault("quiz", {"type": "string", "keyframes": []})
    frame = existing["frame"] if existing is not None else {}
    frame.update(time=time, endTime=time, duration=0)
    if value is not None:
        frame["value"] = value
    if "value" not in frame:
        raise ValueError("supply native quiz XML when creating a new point")
    if existing is None or moved:
        parameter["keyframes"].append(frame)
    parameter["keyframes"].sort(key=lambda point: project.number(point["time"]))
    update_count(doc)


def point_from_global(doc: dict[str, Any], logical_id: int | None, global_time: int) -> int:
    if logical_id is None:
        return global_time
    clips = hotspots.clips(doc)
    matches = [(path, node) for path, node in clips if node.get("id") == logical_id]
    if len(matches) != 1:
        raise ValueError("recover the unique visual clock owner")
    path, owner = matches[0]
    ancestors = sorted(
        [(p, n) for p, n in clips if path.startswith(p + "/")],
        key=lambda item: len(item[0]),
        reverse=True,
    )
    point = project.number(global_time)
    for _, node in reversed([(path, owner), *ancestors]):
        scalar = project.number(node.get("scalar"))
        if scalar <= 0:
            raise ValueError("use a positive native owner clock scalar")
        point = (
            project.number(node.get("mediaStart"))
            + (point - project.number(node.get("start"))) / scalar
        )
    if point.denominator != 1:
        raise ValueError("global target falls between owner ticks; choose an exact native point")
    result = point.numerator
    # The independently verified forward mapper owns supported containers,
    # scene count and visible bounds; inversion cannot relax those checks.
    if hotspots.marker_global_ticks(doc, logical_id, result) != global_time:
        raise ValueError("reconcile the native owner/global clock mapping")
    return result


def move(
    doc: dict[str, Any],
    quiz_id: str,
    owner_id: int,
    *,
    seconds: Any = None,
    global_seconds: Any = None,
) -> dict[str, Any]:
    require_supported(doc)
    if type(owner_id) is not int:
        raise ValueError("select a numeric destination owner ID from inspection")
    if seconds is not None and global_seconds is not None:
        raise ValueError("choose owner time or global time, not both")
    candidate = copy.deepcopy(doc)
    existing = next((entry for entry in entries(candidate) if entry["id"] == quiz_id), None)
    if existing is None:
        raise ValueError("select an existing quiz ID from inspection")
    old_path, _, old_logical = resolve_owner(candidate, existing["ownerId"])
    if old_path != existing["ownerPath"]:
        raise ValueError("inspect the quiz's unfamiliar physical parameter owner")
    path, owner, logical = resolve_owner(candidate, owner_id)
    if seconds is not None:
        time = hotspots.ticks(candidate, seconds)
        if logical is not None:
            hotspots.marker_global_ticks(candidate, logical, time)
    else:
        if global_seconds is not None:
            global_time = hotspots.ticks(candidate, global_seconds)
        elif old_logical is not None:
            global_time = hotspots.marker_global_ticks(candidate, old_logical, existing["time"])
        else:
            global_time = existing["time"]
        time = point_from_global(candidate, logical, global_time)
    place_frame(candidate, existing, path, owner, time, quiz_id)
    return candidate


def upsert(
    doc: dict[str, Any], spec: dict[str, Any], seconds: Any, *, owner_id: int | None = None
) -> dict[str, Any]:
    require_supported(doc)
    validate_spec(spec)
    if (
        project.number(doc.get("width")) < MIN_CANVAS[0]
        or project.number(doc.get("height")) < MIN_CANVAS[1]
    ):
        raise ValueError(
            "resize a separate candidate to the native quiz canvas requirement before authoring"
        )
    time = hotspots.ticks(doc, seconds)
    candidate = copy.deepcopy(doc)
    all_entries = entries(candidate)
    existing = next((entry for entry in all_entries if entry["id"] == str(spec["id"])), None)
    if existing is not None and existing["ownerPath"] != "/timeline":
        previous_path, _, _ = resolve_owner(candidate, existing["ownerId"])
        if previous_path != existing["ownerPath"]:
            raise ValueError("inspect the quiz's unfamiliar physical parameter owner")
    selected_id = owner_id
    if selected_id is None and existing is not None and existing["ownerPath"] != "/timeline":
        selected_id = existing["ownerId"]
        if type(selected_id) is not int:
            raise ValueError("repair the quiz's physical owner ID before editing")
    path, owner, logical_id = resolve_owner(candidate, selected_id)
    if logical_id is not None:
        hotspots.marker_global_ticks(candidate, logical_id, time)
    place_frame(
        candidate,
        existing,
        path,
        owner,
        time,
        str(spec["id"]),
        build_xml(spec, existing["xml"] if existing else None, doc=candidate),
    )
    return candidate


def remove(doc: dict[str, Any], quiz_id: str) -> dict[str, Any]:
    require_supported(doc)
    candidate = copy.deepcopy(doc)
    found = next((entry for entry in entries(candidate) if entry["id"] == quiz_id), None)
    if found is None:
        return candidate
    if found["ownerPath"] != "/timeline":
        path, _, _ = resolve_owner(candidate, found["ownerId"])
        if path != found["ownerPath"]:
            raise ValueError("inspect the quiz's unfamiliar physical parameter owner")
    detach(candidate, found)
    update_count(candidate)
    return candidate


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    commands = parser.add_subparsers(dest="command", required=True)
    inspect = commands.add_parser("inspect")
    inspect.add_argument("project", type=Path)
    for command in ("upsert", "remove", "move"):
        edit = commands.add_parser(command)
        edit.add_argument("project", type=Path)
        edit.add_argument("--output", type=Path, required=True)
        if command == "upsert":
            edit.add_argument("--spec", type=Path, required=True)
            edit.add_argument("--time", required=True)
            edit.add_argument("--owner-id", type=int)
        else:
            edit.add_argument("--quiz-id", required=True)
            if command == "move":
                edit.add_argument("--owner-id", required=True, type=int)
                time_options = edit.add_mutually_exclusive_group()
                time_options.add_argument("--time")
                time_options.add_argument("--global-time")
    args = parser.parse_args(argv)
    try:
        doc, raw = project.load(args.project)
        report = {
            "schema_version": 1,
            "owner": "camtasia-quizzes",
            "ok": True,
            "projectSha256": project.digest(raw),
        }
        if args.command == "inspect":
            report["quizzes"] = inventory(doc)
        else:
            if args.command == "upsert":
                candidate = upsert(
                    doc, project.load(args.spec)[0], args.time, owner_id=args.owner_id
                )
            elif args.command == "move":
                candidate = move(
                    doc,
                    args.quiz_id,
                    args.owner_id,
                    seconds=args.time,
                    global_seconds=args.global_time,
                )
            else:
                candidate = remove(doc, args.quiz_id)
            report.update(
                output=str(args.output),
                written=hotspots.stage(args.project, args.output, candidate),
                candidateSha256=project.digest(project.encode_document(candidate)),
                changed=candidate != doc,
                quizzes=inventory(candidate),
                nativeVerified=False,
            )
        print(json.dumps(report, ensure_ascii=False))
        return 0
    except (OSError, ValueError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
