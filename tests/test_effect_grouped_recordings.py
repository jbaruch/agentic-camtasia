from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_effect_linked_recordings import native_template
from test_matte_linked_recordings import fixture
from test_animation_freezes import RATE
import behaviors
import effects
import hotspots
import mattes
import project


def node(doc, ident):
    return next(value for _, value in hotspots.clips(doc) if value.get("id") == ident)


def grouped(doc=None, depth=1):
    doc = copy.deepcopy(fixture() if doc is None else doc)
    child = node(doc, 10)
    for owner in (child, child["video"], child["audio"]):
        owner.update(start=0, duration=4 * RATE, mediaStart=2 * RATE, mediaDuration=8 * RATE)
    child["video"]["animationTracks"] = {}
    content = child
    for i in range(depth):
        content = dict(
            id=100 + i,
            _type="Group",
            start=RATE if i == depth - 1 else 0,
            duration=4 * RATE,
            mediaStart=0.0,
            mediaDuration=float(4 * RATE),
            scalar=1,
            attributes=dict(ident="Group 1", widthAttr=364.0, heightAttr=236.0, gain=1.0),
            parameters=dict(volume=1.0, translation0=17.0),
            animationTracks={},
            effects=[],
            metadata=dict(effectApplied="none", opaqueParent=["keep", i]),
            tracks=[dict(trackIndex=0, medias=[content])],
        )
    project.scene_tracks(doc)[0][0]["medias"] = [content]
    return doc


def timed_template(depth=1):
    doc = grouped(native_template(), depth)
    for owner in (node(doc, 10), node(doc, 3)):
        owner["effects"][0]["parameters"]["intensity"] = dict(
            type="double",
            defaultValue=0.0,
            uiHints=dict(userInterfaceType=0, unitType=0),
            keyframes=[
                dict(
                    time=1411200000,
                    endTime=2822400000,
                    duration=1411200000,
                    value=1.0,
                    interp="linr",
                )
            ],
        )
    node(doc, 10)["metadata"]["default-Sepia-intensity"] = "1"
    return doc


class GroupedRecordingEffectTests(unittest.TestCase):
    def test_static_constructor_and_aliases_preserve_complete_single_and_nested_groups(self):
        for depth in (1, 2):
            dest, source = grouped(depth=depth), grouped(native_template(), 2)
            original = copy.deepcopy(dest), copy.deepcopy(source)
            expected = copy.deepcopy(dest)
            for ident in (10, 3):
                node(expected, ident)["effects"] = [
                    dict(
                        effectName="Sepia",
                        bypassed=False,
                        category="categoryVisualEffects",
                        parameters=dict(intensity=1.0),
                        metadata=dict(effectIndex="0"),
                    )
                ]
            node(expected, 10)["metadata"]["effectApplied"] = "Sepia"
            for source_id in (10, 3):
                for dest_id in (10, 3):
                    self.assertEqual(
                        effects.add_effect(dest, dest_id, source, source_id, "Sepia"), expected
                    )
            self.assertEqual((dest, source), original)

    def test_static_edit_bypass_and_removal_keep_every_ancestor_and_audio_field(self):
        doc = grouped(native_template(), 2)
        node(doc, 10)["metadata"]["default-Sepia-intensity"] = "1"
        original = copy.deepcopy(doc)
        expected = copy.deepcopy(doc)
        for ident in (10, 3):
            node(expected, ident)["effects"][0].update(
                bypassed=True, parameters=dict(intensity=0.5)
            )
        edited = effects.edit_effect(
            doc, 3, "Sepia", dict(schema_version=1, parameters=dict(intensity=0.5), bypassed=True)
        )
        self.assertEqual(edited, expected)
        for ident in (10, 3):
            node(expected, ident)["effects"] = []
        removed = effects.remove_effect(edited, 10, "Sepia")
        self.assertEqual(removed, expected)
        self.assertEqual(effects.remove_effect(removed, 3, "Sepia"), expected)
        self.assertEqual(doc, original)

    def test_timed_native_payload_and_reset_copy_without_copying_ancestor_or_visual_intervals(self):
        source, dest = timed_template(2), grouped()
        node(source, 100)["parameters"]["translation0"] = 99
        node(source, 101)["start"] = 10 * RATE
        node(source, 3)["animationTracks"] = {
            "visual": [dict(endTime=2822400000, duration=1411200000, interp="linr")]
        }
        original = copy.deepcopy(source), copy.deepcopy(dest)
        expected = copy.deepcopy(dest)
        for ident in (10, 3):
            node(expected, ident)["effects"] = copy.deepcopy(node(source, ident)["effects"])
        node(expected, 10)["metadata"].update(
            {"effectApplied": "Sepia", "default-Sepia-intensity": "1"}
        )
        self.assertEqual(effects.add_effect(dest, 10, source, 3, "Sepia"), expected)
        self.assertEqual((source, dest), original)
        self.assertEqual(node(expected, 3)["animationTracks"], {})

    def test_root_and_grouped_donors_and_recipients_share_child_source_clock_contract(self):
        grouped_source = timed_template()
        root_source = copy.deepcopy(grouped_source)
        project.scene_tracks(root_source)[0][0]["medias"] = [node(root_source, 10)]
        for source in (root_source, grouped_source):
            for depth in (0, 1, 2):
                dest = grouped(depth=max(depth, 1))
                if depth == 0:
                    project.scene_tracks(dest)[0][0]["medias"] = [node(dest, 10)]
                result = effects.add_effect(dest, 3, source, 10, "Sepia")
                self.assertEqual(node(result, 3)["effects"], node(source, 3)["effects"])
                self.assertEqual(node(result, 11), node(dest, 11))

    def test_timed_copy_refuses_each_mismatching_child_clock_before_mutation(self):
        for field in effects.CLOCK_FIELDS:
            source, dest = timed_template(), grouped(depth=2)
            for ident in (10, 3):
                owner = node(dest, ident)
                owner[field] = 1 if field == "scalar" else owner[field] + 1
            original = copy.deepcopy(dest)
            with self.subTest(field=field), self.assertRaisesRegex(ValueError, "matching complete"):
                effects.add_effect(dest, 3, source, 10, "Sepia")
            self.assertEqual(dest, original)

    def test_child_tokens_avoid_audio_without_importing_ancestor_token_scope(self):
        source, dest = grouped(native_template()), grouped(depth=2)
        node(dest, 100)["effects"] = [dict(effectName="Parent", metadata=dict(effectIndex="99"))]
        node(dest, 11)["effects"] = [dict(effectName="Audio", metadata=dict(effectIndex="7"))]
        expected = copy.deepcopy(dest)
        for ident in (10, 3):
            value = copy.deepcopy(node(source, ident)["effects"][0])
            value["metadata"]["effectIndex"] = "8"
            node(expected, ident)["effects"] = [value]
        node(expected, 10)["metadata"]["effectApplied"] = "Sepia"
        self.assertEqual(effects.add_effect(dest, 3, source, 10, "Sepia"), expected)

    def test_other_container_kinds_and_multiple_scenes_refuse_all_operations(self):
        for kind in ("StitchedMedia", "UnifiedMedia", "Unknown", "scenes"):
            doc = grouped(native_template(), 2)
            if kind == "scenes":
                doc["timeline"]["sceneTrack"]["scenes"].append(dict(csml=dict(tracks=[])))
            else:
                node(doc, 101)["_type"] = kind
            original = copy.deepcopy(doc)
            for action in (
                lambda: effects.add_effect(doc, 10, grouped(native_template()), 3, "Sepia"),
                lambda: effects.edit_effect(doc, 3, "Sepia", dict(schema_version=1, bypassed=True)),
                lambda: effects.remove_effect(doc, 10, "Sepia"),
            ):
                with self.subTest(kind=kind), self.assertRaises(ValueError):
                    action()
                self.assertEqual(doc, original)

    def test_missing_audio_conflicting_mirrors_and_clocks_still_refuse(self):
        for change in ("audio", "mirror", "clock", "token"):
            doc = grouped(native_template())
            if change == "audio":
                node(doc, 11)["src"] = 99
            elif change == "mirror":
                node(doc, 3)["effects"][0]["parameters"]["intensity"] = 0.5
            elif change == "clock":
                node(doc, 3)["mediaStart"] += 1
            else:
                node(doc, 3)["effects"][0]["metadata"].pop("effectIndex")
            original = copy.deepcopy(doc)
            with self.subTest(change=change), self.assertRaises(ValueError):
                effects.edit_effect(doc, 10, "Sepia", dict(schema_version=1, bypassed=True))
            self.assertEqual(doc, original)

    def test_shared_resolver_other_features_and_explicit_opt_in_remain_separate(self):
        doc = grouped(native_template())
        for kwargs in ({}, dict(linked_recordings=True), dict(grouped_recordings=True)):
            with self.assertRaises(ValueError):
                effects.constructor_owners(doc, 3, visual_types=effects.EFFECT_TYPES, **kwargs)
        self.assertEqual(
            effects.constructor_owners(
                doc,
                3,
                visual_types=effects.EFFECT_TYPES,
                linked_recordings=True,
                grouped_recordings=True,
            ),
            [node(doc, 10), node(doc, 3)],
        )
        for action in (
            lambda: behaviors.behavior_owners(doc, 3),
            lambda: mattes.media_targets(doc, 3),
        ):
            with self.assertRaises(ValueError):
                action()

    def test_cli_construct_repeat_edit_and_remove_preserve_both_inputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, dest, added, spec, edited, removed = [
                root / name
                for name in (
                    "source.json",
                    "dest.json",
                    "add.json",
                    "spec.json",
                    "edit.json",
                    "remove.json",
                )
            ]
            source.write_bytes(project.encode_document(grouped(native_template())))
            dest.write_bytes(project.encode_document(grouped(depth=2)))
            original = source.read_bytes(), dest.read_bytes()
            add = [
                "add",
                str(dest),
                "--clip-id",
                "3",
                "--effect",
                "Sepia",
                "--template-project",
                str(source),
                "--template-clip-id",
                "10",
                "--output",
                str(added),
            ]
            for written in (True, False):
                with patch("sys.stdout", new_callable=io.StringIO) as stream:
                    self.assertEqual(effects.main(add), 0)
                self.assertEqual(json.loads(stream.getvalue())["written"], written)
            spec.write_text(json.dumps(dict(schema_version=1, parameters=dict(intensity=0.5))))
            for command in (
                [
                    "set",
                    str(added),
                    "--clip-id",
                    "10",
                    "--effect",
                    "Sepia",
                    "--spec",
                    str(spec),
                    "--output",
                    str(edited),
                ],
                [
                    "remove",
                    str(edited),
                    "--clip-id",
                    "3",
                    "--effect",
                    "Sepia",
                    "--output",
                    str(removed),
                ],
            ):
                with patch("sys.stdout", new_callable=io.StringIO):
                    self.assertEqual(effects.main(command), 0)
            expected = grouped(depth=2)
            node(expected, 10)["metadata"]["effectApplied"] = "Sepia"
            self.assertEqual(project.load(removed)[0], expected)
            self.assertEqual((source.read_bytes(), dest.read_bytes()), original)


if __name__ == "__main__":
    unittest.main()
