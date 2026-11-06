from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_annotations import fixture as annotation_fixture
from test_captions import fixture as av_fixture
import media_replacement as media
import project
import quick_properties as quick

R = 705600000


def spec(**kwargs):
    return dict(schema_version=1, **kwargs)


def roots(doc):
    return project.scene_tracks(doc)[0][0]["medias"]


def group(doc):
    return roots(doc)[0]


def rows(doc):
    return group(doc)["attributes"]["assetProperties"]


def children(doc):
    return group(doc)["tracks"][0]["medias"]


def text_fixture():
    doc = annotation_fixture()
    first = copy.deepcopy(roots(doc)[0])
    first.update(start=0, duration=5000)
    second = copy.deepcopy(first)
    second["id"] = 8
    second["def"]["text"] = "XYZ"
    group_node = dict(
        id=30,
        _type="Group",
        attributes=dict(
            assetProperties=[
                dict(
                    type=0,
                    name="Heading",
                    objects=[3],
                    opaque={"keep": True},
                    themeMappings={"font-color": "foreground-1"},
                ),
                dict(type=0, name="Subheading", objects=[8], opaque={"keep": True}),
            ]
        ),
        tracks=[dict(trackIndex=0, medias=[first, second])],
        metadata={"keep": [1]},
        start=0,
        duration=5000,
    )
    roots(doc)[:] = [group_node]
    project.scene_tracks(doc)[0][0].pop("transitions", None)
    return doc


def media_fixture():
    doc = av_fixture()
    old = roots(doc)[0]
    for node in (old, old["video"], old["audio"]):
        node.update(start=0, duration=4 * R, mediaStart=2 * R, mediaDuration=4 * R, scalar=1)
    old["video"]["parameters"] = dict(
        scale0=0.75, scale1=0.75, translation0=32.0, translation1=-16.0, opacity=0.75
    )
    old["audio"]["parameters"] = {}
    old["audio"]["attributes"].update(gain=0.25, sourceFileOffset=0)
    old["metadata"] = {"old-reset": "native", "opaque": ["native operation replaces this metadata"]}
    donor = copy.deepcopy(old)
    donor.update(id=100, metadata={})
    for index, node in enumerate((donor, donor["video"], donor["audio"])):
        node.update(id=100 + index, start=0, duration=2 * R, mediaStart=0, mediaDuration=2 * R)
        node["effects"] = []
        node["animationTracks"] = {}
    donor["video"]["parameters"] = {}
    donor["audio"]["attributes"]["gain"] = 1.0
    donor["video"].update(src=20, trackNumber=0)
    donor["audio"].update(src=20, trackNumber=1)
    donor["video"].setdefault("attributes", {})["ident"] = "portrait"
    doc["sourceBin"] += [
        dict(
            id=20,
            src="portrait-not-read.mp4",
            sourceTracks=[
                dict(
                    type=0,
                    editRate=96000,
                    range=[0, 192000],
                    trackRect=[0, 0, 320, 480],
                    sampleRate=30,
                ),
                dict(
                    type=2,
                    editRate=96000,
                    range=[0, 192000],
                    trackRect=[0, 0, 0, 0],
                    sampleRate=32000,
                ),
            ],
        ),
        dict(
            id=21,
            src="image-not-read.png",
            sourceTracks=[dict(type=1, editRate=600, range=[0, 1], trackRect=[0, 0, 64, 64])],
        ),
    ]
    # Fixed independent video dimensions, separate from its track clock.
    doc["sourceBin"][0]["sourceTracks"][0]["trackRect"] = [0, 0, 640, 360]
    image = dict(
        id=200,
        _type="IMFile",
        src=21,
        trackNumber=0,
        attributes={"ident": "square"},
        parameters={},
        effects=[],
        animationTracks={},
        start=0,
        duration=4 * R,
        mediaStart=0,
        mediaDuration=1,
        scalar=1,
    )
    container = dict(
        id=30,
        _type="Group",
        attributes=dict(assetProperties=[dict(type=2, name="Footage", objects=[3])]),
        tracks=[dict(trackIndex=0, medias=[old])],
        start=0,
        duration=4 * R,
        mediaStart=0,
        mediaDuration=4 * R,
        scalar=1,
        metadata={"keep": "group"},
    )
    roots(doc)[:] = [container, donor, image]
    return doc


def clear_template():
    return dict(
        id=300,
        _type="Callout",
        attributes={"ident": "", "autoRotateText": True},
        parameters={},
        effects=[],
        animationTracks={},
        start=0,
        duration=4 * R,
        mediaStart=0,
        mediaDuration=4 * R,
        scalar=1,
        **{
            "def": dict(
                kind="remix",
                shape="shape-rectangle",
                style="bold",
                width=640.0,
                height=360.0,
                **{
                    "fill-style": "solid",
                    "stroke-style": "solid",
                    "fill-color-red": 0.0,
                    "fill-color-green": 0.0,
                    "fill-color-blue": 0.0,
                    "fill-color-opacity": 0.0,
                    "stroke-width": 0.0,
                },
            )
        },
    )


class QuickPropertyTests(unittest.TestCase):
    def test_active_theme_allows_labels_reorder_and_hiding_but_not_mapping_changes(self):
        doc = text_fixture()
        group(doc)["metadata"]["AppliedThemeId"] = "native-theme"
        desired = copy.deepcopy(rows(doc)[::-1])
        desired[0]["name"] = "Renamed"
        result = quick.set_bindings(doc, 30, spec(expected=rows(doc), properties=desired))
        self.assertEqual(children(result), children(doc))
        desired[1]["themeMappings"] = {"font-color": "accent-1"}
        with self.assertRaisesRegex(ValueError, "Theme Manager"):
            quick.set_bindings(doc, 30, spec(expected=rows(doc), properties=desired))

    def test_dynamic_link_requires_explicit_color_and_unlink_keeps_components(self):
        doc = text_fixture()
        for child in children(doc):
            child["sourceEffect"] = {
                "parameters": {
                    f"Color000-{c}": v
                    for c, v in zip(("red", "green", "blue", "alpha"), (1.0, 0.0, 0.0, 1.0))
                }
            }
        rows(doc)[:] = [
            dict(
                type=1,
                name="First",
                objects=[dict(media=3, property="Color000")],
                themeMappings={"fill": "accent-1"},
            ),
            dict(type=1, name="Second", objects=[dict(media=8, property="Color000")]),
        ]
        with self.assertRaisesRegex(ValueError, "four normalized"):
            quick.link_rows(doc, 30, 1, spec(expected=rows(doc)))
        linked = quick.link_rows(doc, 30, 1, spec(expected=rows(doc), color=[0, 0.5, 1, 1]))
        self.assertEqual(
            rows(linked),
            [
                dict(
                    type=1,
                    name="First",
                    objects=[
                        dict(media=3, property="Color000"),
                        dict(media=8, property="Color000"),
                    ],
                )
            ],
        )
        split = quick.link_rows(linked, 30, 0, spec(expected=rows(linked)), unlink=True)
        self.assertEqual(
            [c["sourceEffect"]["parameters"]["Color000-green"] for c in children(split)], [0.5, 0.5]
        )

    def test_bindings_cli_json_errors_exclusive_staging_and_malformed_shapes(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.json"
            request = root / "spec.json"
            output = root / "candidate.json"
            doc = text_fixture()
            source.write_bytes(project.encode_document(doc))
            before = source.read_bytes()
            desired = copy.deepcopy(rows(doc))
            desired[0]["name"] = "Published title"
            request.write_text(json.dumps(spec(expected=rows(doc), properties=desired)))
            args = [
                "bindings",
                str(source),
                "--group-id",
                "30",
                "--spec",
                str(request),
                "--output",
                str(output),
            ]
            for written in (True, False):
                stdout = io.StringIO()
                with patch("sys.stdout", stdout):
                    self.assertEqual(quick.main(args), 0)
                report = json.loads(stdout.getvalue())
                self.assertEqual(report["written"], written)
                self.assertFalse(report["nativeVerified"])
            self.assertEqual(source.read_bytes(), before)
            bad = copy.deepcopy(doc)
            group(bad)["attributes"] = None
            source.write_bytes(project.encode_document(bad))
            stderr = io.StringIO()
            with patch("sys.stderr", stderr):
                self.assertEqual(quick.main(["inspect", str(source)]), 1)
            self.assertIn("assetProperties", json.loads(stderr.getvalue())["error"])
            stderr = io.StringIO()
            with patch("sys.stderr", stderr), self.assertRaises(SystemExit) as raised:
                quick.main(["bindings", str(source)])
            self.assertEqual(raised.exception.code, 2)
            self.assertIn("error", json.loads(stderr.getvalue()))

    def test_rename_reorder_remove_readd_preserve_complete_children_and_opaque_entries(self):
        doc = text_fixture()
        desired = copy.deepcopy(rows(doc)[::-1])
        desired[0]["name"] = "Second → title"
        result = quick.set_bindings(doc, 30, spec(expected=rows(doc), properties=desired))
        self.assertEqual(rows(result), desired)
        self.assertEqual(children(result), children(doc))
        self.assertEqual(group(result)["metadata"], group(doc)["metadata"])
        removed = quick.set_bindings(
            result, 30, spec(expected=rows(result), properties=rows(result)[:1])
        )
        readded = quick.set_bindings(
            removed,
            30,
            spec(
                expected=rows(removed),
                properties=rows(removed) + [dict(type=0, name="Text", objects=[3])],
            ),
        )
        self.assertNotIn("themeMappings", rows(readded)[1])
        self.assertEqual(children(readded), children(doc))
        self.assertEqual(
            quick.set_bindings(result, 30, spec(expected=rows(doc), properties=desired)), result
        )

    def test_unicode_bound_text_updates_all_utf8_runs_and_keeps_defaults(self):
        doc = text_fixture()
        result = quick.set_value(
            doc, 30, 0, spec(expected=rows(doc)[0], text="Build → 日本語", rich={"fontSize": 48})
        )
        changed = children(result)[0]
        self.assertEqual(changed["def"]["text"], "Build → 日本語")
        self.assertEqual(changed["def"]["font"], children(doc)[0]["def"]["font"])
        runs = changed["def"]["textAttributes"]["keyframes"][0]["value"]
        self.assertTrue(all(r["rangeEnd"] == 19 for r in runs))
        self.assertEqual(next(r["value"] for r in runs if r["name"] == "fontSize"), 48)
        self.assertEqual(children(result)[1], children(doc)[1])
        self.assertEqual(changed["metadata"], children(doc)[0]["metadata"])

    def test_link_text_first_value_second_mapping_and_unlink_retains_shared_values(self):
        doc = text_fixture()
        linked = quick.link_rows(doc, 30, 1, spec(expected=rows(doc)))
        self.assertEqual(
            rows(linked), [dict(type=0, name="Heading", objects=[3, 8], opaque={"keep": True})]
        )
        self.assertEqual([c["def"]["text"] for c in children(linked)], ["ABC", "ABC"])
        edited = quick.set_value(
            linked, 30, 0, spec(expected=rows(linked)[0], text="Together → Go")
        )
        unlinked = quick.link_rows(edited, 30, 0, spec(expected=rows(edited)), unlink=True)
        self.assertEqual([r["objects"] for r in rows(unlinked)], [[3], [8]])
        self.assertEqual([c["def"]["text"] for c in children(unlinked)], ["Together → Go"] * 2)
        doc = text_fixture()
        rows(doc)[1]["themeMappings"] = {"font-family": "font-2"}
        linked = quick.link_rows(doc, 30, 1, spec(expected=rows(doc)))
        self.assertEqual(rows(linked)[0]["themeMappings"], {"font-family": "font-2"})

    def test_dynamic_colors_preserve_binding_and_typed_descriptors(self):
        doc = text_fixture()
        child = children(doc)[0]
        child["sourceEffect"] = {
            "parameters": {
                f"Color000-{name}": dict(
                    type="double", defaultValue=value, interp="linr", opaque=[1]
                )
                for name, value in zip(("red", "green", "blue", "alpha"), (1.0, 0.0, 0.0, 1.0))
            }
        }
        rows(doc)[:] = [dict(type=1, name="Fill", objects=[dict(media=3, property="Color000")])]
        result = quick.set_value(doc, 30, 0, spec(expected=rows(doc)[0], color=["1/2", 0, 1, 1]))
        self.assertEqual(
            children(result)[0]["sourceEffect"]["parameters"]["Color000-red"],
            dict(type="double", defaultValue=0.5, interp="linr", opaque=[1]),
        )
        self.assertEqual(rows(result), rows(doc))

    def test_binding_refusals_are_atomic_and_actionable(self):
        doc = text_fixture()
        bads = [
            dict(type=0, name="bad", objects=[1]),
            dict(type=0, name="bad", objects=[True]),
            dict(type=0, name="bad", objects=[3, 3]),
            dict(type=0, name="bad", objects=[]),
            dict(type=0, name="bad", objects=[3], themeMappings={"fill": "accent-1"}),
            dict(type=1, name="bad", objects=[dict(media=3, property=[])]),
        ]
        before = copy.deepcopy(doc)
        for row in bads:
            with self.subTest(row=row), self.assertRaises(ValueError):
                quick.set_bindings(doc, 30, spec(expected=rows(doc), properties=[row]))
        self.assertEqual(doc, before)
        with self.assertRaisesRegex(ValueError, "stale"):
            quick.set_bindings(doc, 30, spec(expected=[], properties=[]))
        with self.assertRaisesRegex(ValueError, "opaque"):
            altered = copy.deepcopy(rows(doc))
            altered[0].pop("opaque")
            quick.set_bindings(doc, 30, spec(expected=rows(doc), properties=altered))
        with self.assertRaisesRegex(ValueError, "shared"):
            quick.set_bindings(
                doc,
                30,
                spec(expected=rows(doc), properties=[dict(type=0, name="Text", objects=[3, 8])]),
            )

    def test_partial_rich_and_active_theme_refusals_keep_original(self):
        doc = text_fixture()
        before = copy.deepcopy(doc)
        children(doc)[0]["def"]["textAttributes"]["keyframes"][0]["value"][0]["rangeEnd"] = 1
        with self.assertRaisesRegex(ValueError, "partial"):
            quick.set_value(doc, 30, 0, spec(expected=rows(doc)[0], text="new"))
        self.assertEqual(children(doc)[0]["def"]["text"], "ABC")
        doc = before
        group(doc)["metadata"]["AppliedThemeId"] = "native-theme"
        with self.assertRaisesRegex(ValueError, "Theme Manager"):
            quick.link_rows(doc, 30, 1, spec(expected=rows(doc)))


class MediaReplacementTests(unittest.TestCase):
    def test_media_link_first_source_second_mapping_and_unlink_retains_shared_content(self):
        doc = media_fixture()
        second = roots(doc).pop(1)
        first = children(doc)[0]
        for node in (first, first["video"], first["audio"]):
            node["mediaStart"] = 0
        group(doc)["tracks"].append(dict(trackIndex=1, medias=[second]))
        rows(doc).append(
            dict(type=2, name="Second", objects=[100], themeMappings={"logo-1": "logo-1"})
        )
        linked = quick.link_rows(doc, 30, 1, spec(expected=rows(doc)))
        self.assertEqual(
            rows(linked),
            [dict(type=2, name="Footage", objects=[3, 100], themeMappings={"logo-1": "logo-1"})],
        )
        bound = [quick.selected(linked, i) for i in (3, 100)]
        self.assertEqual([c["video"]["src"] for c in bound], [1, 1])
        self.assertEqual([c["audio"]["src"] for c in bound], [1, 1])
        self.assertEqual(bound[0]["metadata"]["old-reset"], "native")
        self.assertEqual(bound[0]["video"]["parameters"]["scale0"], 0.75)
        self.assertEqual(bound[1]["video"]["parameters"]["scale0"], 0.5)
        unlinked = quick.link_rows(linked, 30, 0, spec(expected=rows(linked)), unlink=True)
        self.assertEqual([r["objects"] for r in rows(unlinked)], [[3], [100]])
        self.assertEqual([quick.selected(unlinked, i) for i in (3, 100)], bound)

    def test_colorize_mirrors_survive_type_changes_and_opaque_couplings_refuse(self):
        doc = media_fixture()
        node = children(doc)[0]
        effect = dict(
            effectName="Colorize",
            category="categoryVisualEffects",
            bypassed=False,
            parameters=dict(
                amount=dict(type="double", defaultValue=0.5, interp="linr", opaque=[1]),
                red=0.0,
                green=1.0,
                blue=0.0,
                alpha=1.0,
            ),
            metadata={"effectIndex": "6", "retain": "effect"},
        )
        node["effects"] = [copy.deepcopy(effect)]
        node["video"]["effects"] = [copy.deepcopy(effect)]
        image = media.edit_media(doc, 30, 0, spec(expected=rows(doc)[0]), roots(doc)[2])
        self.assertEqual(children(image)[0]["effects"], [effect])
        cleared = media.edit_media(image, 30, 0, spec(expected=rows(image)[0]), clear_template())
        restored = media.edit_media(cleared, 30, 0, spec(expected=rows(cleared)[0]), roots(doc)[1])
        self.assertEqual(children(restored)[0]["effects"], [effect])
        self.assertEqual(children(restored)[0]["video"]["effects"], [effect])
        for key in ("sourceEffect", "attributes", "metadata"):
            bad = media_fixture()
            visual = children(bad)[0]["video"]
            visual[key] = {"opaque": [1]}
            with self.subTest(key=key), self.assertRaises(ValueError):
                media.edit_media(bad, 30, 0, spec(expected=rows(bad)[0]), roots(bad)[2])

    def test_short_portrait_clamps_both_streams_and_retains_style_gain_and_group(self):
        doc = media_fixture()
        before = copy.deepcopy(doc)
        result = media.edit_media(doc, 30, 0, spec(expected=rows(doc)[0]), roots(doc)[1])
        node = children(result)[0]
        self.assertEqual([node["id"], node["video"]["id"], node["audio"]["id"]], [3, 4, 5])
        for part in (node, node["video"], node["audio"]):
            self.assertEqual(
                (part["start"], part["duration"], part["mediaStart"], part["mediaDuration"]),
                (0, 2 * R, 0, 2 * R),
            )
        self.assertEqual(node["video"]["src"], 20)
        self.assertEqual(node["audio"]["src"], 20)
        self.assertEqual(node["audio"]["attributes"]["gain"], 0.25)
        self.assertEqual(
            node["video"]["parameters"],
            dict(
                scale0=0.5625,
                scale1=0.5625,
                translation0=32.0,
                translation1=-16.0,
                opacity=0.75,
                geometryCrop0=0.0,
                geometryCrop1=0.0,
                geometryCrop2=0.0,
                geometryCrop3=0.0,
            ),
        )
        self.assertEqual(
            node["metadata"]["originalMediaQuickPropertyDuration"], dict(type="double", value=4 * R)
        )
        self.assertEqual(node["metadata"]["previousReplacementWidth"]["value"], 180)
        self.assertEqual(set(node["metadata"]), set(media.REPLACEMENT_FIELDS))
        self.assertEqual(group(result)["duration"], 4 * R)
        self.assertEqual(result["sourceBin"], doc["sourceBin"])
        self.assertEqual(roots(result)[1:], roots(doc)[1:])
        self.assertEqual(doc, before)

    def test_longer_replacement_restores_original_remembered_duration(self):
        doc = media_fixture()
        short = media.edit_media(doc, 30, 0, spec(expected=rows(doc)[0]), roots(doc)[1])
        long = copy.deepcopy(roots(doc)[1])
        long["video"].update(src=1, trackNumber=0)
        long["audio"].update(src=1, trackNumber=1)
        result = media.edit_media(short, 30, 0, spec(expected=rows(short)[0]), long)
        node = children(result)[0]
        self.assertEqual(node["duration"], 4 * R)
        self.assertEqual(node["video"]["parameters"]["scale0"], 0.75)
        self.assertEqual(node["audio"]["attributes"]["gain"], 0.25)
        self.assertEqual(
            media.edit_media(result, 30, 0, spec(expected=rows(result)[0]), long), result
        )

    def test_image_clear_restore_fit_holds_ids_and_unity_gain(self):
        doc = media_fixture()
        image = media.edit_media(doc, 30, 0, spec(expected=rows(doc)[0]), roots(doc)[2])
        node = children(image)[0]
        self.assertEqual((node["_type"], node["id"], node["mediaDuration"]), ("IMFile", 3, 1))
        self.assertEqual(node["parameters"]["scale0"], 4.21875)
        cleared = media.edit_media(image, 30, 0, spec(expected=rows(image)[0]), clear_template())
        node = children(cleared)[0]
        self.assertEqual(
            (node["_type"], node["id"], node["duration"], node["mediaDuration"]),
            ("Callout", 3, 4 * R, 4 * R),
        )
        self.assertEqual((node["def"]["width"], node["def"]["height"]), (64.0, 64.0))
        self.assertEqual(node["parameters"]["scale0"], 4.21875)
        restored = media.edit_media(cleared, 30, 0, spec(expected=rows(cleared)[0]), roots(doc)[1])
        node = children(restored)[0]
        self.assertEqual((node["video"]["id"], node["audio"]["id"]), (201, 202))
        self.assertEqual(node["audio"]["attributes"]["gain"], 1)
        self.assertEqual(node["duration"], 2 * R)
        self.assertEqual(rows(restored), rows(doc))
        self.assertEqual(restored["sourceBin"], doc["sourceBin"])

    def test_clear_short_av_restores_remembered_duration_and_is_idempotent(self):
        doc = media_fixture()
        short = media.edit_media(doc, 30, 0, spec(expected=rows(doc)[0]), roots(doc)[1])
        result = media.edit_media(short, 30, 0, spec(expected=rows(short)[0]), clear_template())
        self.assertEqual(children(result)[0]["duration"], 4 * R)
        self.assertEqual(children(result)[0]["def"]["width"], 320)
        self.assertEqual(children(result)[0]["parameters"]["scale0"], 0.5625)
        self.assertEqual(
            media.edit_media(result, 30, 0, spec(expected=rows(result)[0]), clear_template()),
            result,
        )

    def test_asymmetric_source_bounds_and_source_track_clock_not_sample_rate(self):
        doc = media_fixture()
        doc["sourceBin"][1]["sourceTracks"][1]["range"][1] = 96000
        result = media.edit_media(doc, 30, 0, spec(expected=rows(doc)[0]), roots(doc)[1])
        self.assertEqual(children(result)[0]["duration"], R)
        doc["sourceBin"][1]["sourceTracks"][0]["range"][1] = 1
        with self.assertRaisesRegex(ValueError, "frame-grid"):
            media.edit_media(doc, 30, 0, spec(expected=rows(doc)[0]), roots(doc)[1])

    def test_refuse_data_loss_animation_nonuniform_fit_and_removed_child_bindings(self):
        for mutation in (
            "animation",
            "crop",
            "nonuniform",
            "offset",
            "processing",
            "opaque",
            "binding",
        ):
            doc = media_fixture()
            node = children(doc)[0]
            if mutation == "animation":
                node["video"]["animationTracks"] = {"0": [1]}
            elif mutation == "crop":
                node["video"]["parameters"]["geometryCrop0"] = 1
            elif mutation == "nonuniform":
                node["video"]["parameters"]["scale1"] = 0.5
            elif mutation == "offset":
                node["audio"]["attributes"]["sourceFileOffset"] = 1
            elif mutation == "processing":
                node["audio"]["parameters"] = {"captions": {"type": "caption"}}
            elif mutation == "opaque":
                node["future-payload"] = [1]
            else:
                rows(doc).append(dict(type=0, name="child", objects=[4]))
            before = copy.deepcopy(doc)
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                media.edit_media(doc, 30, 0, spec(expected=rows(doc)[0]), roots(doc)[2])
            self.assertEqual(doc, before)

    def test_cli_stages_exclusively_keeps_inputs_and_emits_json_diagnostics(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp)
            source = root / "source.json"
            request = root / "spec.json"
            output = root / "candidate.json"
            doc = media_fixture()
            source.write_bytes(project.encode_document(doc))
            before = source.read_bytes()
            request.write_text(json.dumps(spec(expected=rows(doc)[0])))
            args = [
                "replace",
                str(source),
                "--group-id",
                "30",
                "--index",
                "0",
                "--source-clip-id",
                "100",
                "--spec",
                str(request),
                "--output",
                str(output),
            ]
            stdout = io.StringIO()
            with patch("sys.stdout", stdout):
                self.assertEqual(media.main(args), 0)
            report = json.loads(stdout.getvalue())
            self.assertTrue(report["changed"])
            self.assertTrue(report["written"])
            self.assertFalse(report["nativeVerified"])
            stdout = io.StringIO()
            with patch("sys.stdout", stdout):
                self.assertEqual(media.main(args), 0)
            self.assertFalse(json.loads(stdout.getvalue())["written"])
            self.assertEqual(source.read_bytes(), before)
            output.write_text("conflict")
            stderr = io.StringIO()
            with patch("sys.stderr", stderr):
                self.assertEqual(media.main(args), 1)
            self.assertIn("error", json.loads(stderr.getvalue()))
            self.assertEqual(output.read_text(), "conflict")


if __name__ == "__main__":
    unittest.main()
