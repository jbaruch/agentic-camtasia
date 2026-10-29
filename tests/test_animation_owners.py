from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_animations import fixture, spec, visual
import animations
import project


def owner_document(kind: str) -> dict:
    doc = fixture()
    node = visual(doc)
    node["_type"] = kind
    node["attributes"] = {"ident": "Synthetic owner", "future": [1, 2]}
    node["parameters"] = {f"geometryCrop{i}": 0.0 for i in range(4)}
    if kind == "IMFile":
        node.update(mediaDuration=1, src=1)
        node["parameters"].update(scale0=3.125, scale1=3.125)
    if kind == "Callout":
        node["def"] = {"kind": "remix", "shape": "ellipse", "fill-style": "solid"}
    if kind == "Group":
        node.pop("src", None)
        node["parameters"]["volume"] = 0.8
        node["tracks"] = [
            {
                "trackIndex": 0,
                "medias": [
                    {"id": 8, "_type": "Callout", "def": {"text": "Keep child"}},
                    {"id": 9, "_type": "AMFile", "parameters": {"volume": 0.3}},
                ],
            }
        ]
    return doc


class AnimationOwnerTests(unittest.TestCase):
    def test_add_ease_remove_preserves_entire_image_callout_and_group(self):
        for kind in ["IMFile", "Callout", "Group"]:
            with self.subTest(kind=kind):
                doc = owner_document(kind)
                before = copy.deepcopy(doc)
                initial = 3.125 if kind == "IMFile" else 1
                target = 4 if kind == "IMFile" else 1.5
                authored = animations.edit_interval(
                    doc,
                    3,
                    spec(
                        values={"scale0": target, "scale1": target},
                        initial={} if kind == "IMFile" else {"scale0": 1, "scale1": 1},
                    ),
                )
                for name in ["scale0", "scale1"]:
                    self.assertEqual(
                        visual(authored)["parameters"][name],
                        {
                            "type": "double",
                            "defaultValue": initial,
                            "keyframes": [
                                {"time": 3000, "endTime": 4000, "duration": 1000, "value": target}
                            ],
                        },
                    )
                eased = animations.edit_interval(
                    authored, 3, spec(values={}, initial={}, easing="bounce")
                )
                self.assertEqual(
                    visual(eased)["animationTracks"],
                    {"visual": [{"endTime": 4000, "duration": 1000, "interp": "bnce"}]},
                )
                self.assertEqual(animations.remove_interval(eased, 3, 3, 4), before)
                self.assertEqual(doc, before)
                for key in ["def", "tracks", "attributes", "src", "mediaDuration"]:
                    self.assertEqual(visual(authored).get(key), visual(doc).get(key))
                self.assertEqual(authored.get("sourceBin"), doc.get("sourceBin"))

    def test_retimed_group_uses_its_source_clock_not_child_or_root_placement(self):
        doc = owner_document("Group")
        visual(doc).update(start=1000, duration=4000, mediaDuration=8000, scalar="1/2")
        result = animations.edit_interval(doc, 3, spec(start=2, end=3, easing="bounce"))
        self.assertEqual(
            visual(result)["animationTracks"],
            {"visual": [{"endTime": 6000, "duration": 2000, "interp": "bnce"}]},
        )
        self.assertEqual(
            visual(result)["parameters"]["scale0"]["keyframes"],
            [{"time": 4000, "endTime": 6000, "duration": 2000, "value": 1.25, "interp": "bnce"}],
        )
        self.assertEqual(visual(result)["tracks"], visual(doc)["tracks"])
        self.assertEqual(animations.remove_interval(result, 3, 2, 3), doc)

    def test_nested_child_can_be_edited_without_touching_parent_animation_or_sibling_audio(self):
        doc = owner_document("Group")
        parent = visual(doc)
        parent["tracks"][0]["medias"][0] = copy.deepcopy(visual(owner_document("Callout")))
        parent["tracks"][0]["medias"][0]["id"] = 8
        doc = animations.edit_interval(doc, 3, spec())
        frozen_parent = copy.deepcopy(visual(doc))
        result = animations.edit_interval(doc, 8, spec(start=1, end=2))
        expected_parent = copy.deepcopy(frozen_parent)
        expected_parent["tracks"][0]["medias"][0] = visual(result)["tracks"][0]["medias"][0]
        self.assertEqual(visual(result), expected_parent)
        self.assertEqual(animations.remove_interval(result, 8, 1, 2), doc)

    def test_unknown_coupled_image_parameter_refuses_easing_without_mutation(self):
        doc = animations.edit_interval(owner_document("IMFile"), 3, spec(initial={}))
        visual(doc)["parameters"]["future"] = {
            "type": "double",
            "defaultValue": 0,
            "keyframes": [{"time": 3000, "endTime": 4000, "duration": 1000, "value": 1}],
        }
        frozen = copy.deepcopy(doc)
        with self.assertRaisesRegex(ValueError, "coupled"):
            animations.edit_interval(doc, 3, spec(values={}, initial={}, easing="linear"))
        self.assertEqual(doc, frozen)

    def test_image_cli_retains_still_source_duration_and_stages_only(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, payload, output = [root / n for n in ["source.json", "spec.json", "out.json"]]
            raw = project.encode_document(owner_document("IMFile"))
            source.write_bytes(raw)
            payload.write_text(json.dumps(spec(initial={})))
            with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                code = animations.main(
                    [
                        "set-interval",
                        str(source),
                        "--clip-id",
                        "3",
                        "--spec",
                        str(payload),
                        "--output",
                        str(output),
                    ]
                )
            self.assertEqual(code, 0)
            self.assertFalse(json.loads(stdout.getvalue())["nativeVerified"])
            self.assertEqual(source.read_bytes(), raw)
            candidate, _ = project.load(output)
            self.assertEqual(visual(candidate)["mediaDuration"], 1)
            self.assertEqual(candidate["sourceBin"], owner_document("IMFile")["sourceBin"])


if __name__ == "__main__":
    unittest.main()
