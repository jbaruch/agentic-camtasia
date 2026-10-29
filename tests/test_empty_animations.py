import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_animation_owners import owner_document
from test_animations import visual
import animations
import project


class EmptyAnimationTests(unittest.TestCase):
    def test_custom_marker_changes_only_interval_and_supports_each_verified_owner(self):
        for kind in ["VMFile", "ScreenVMFile", "IMFile", "Callout", "Group"]:
            doc = owner_document(kind)
            expected = copy.deepcopy(doc)
            visual(expected)["animationTracks"] = {"visual": [{"endTime": 4000, "duration": 1000}]}
            result = animations.edit_interval(
                doc, 3, dict(schema_version=1, start=3, end=4, values={}), allow_empty=True
            )
            self.assertEqual(result, expected)
            self.assertEqual(animations.remove_interval(result, 3, 3, 4), doc)
            self.assertEqual(
                animations.edit_interval(
                    result, 3, dict(schema_version=1, start=3, end=4, values={}), allow_empty=True
                ),
                result,
            )

    def test_empty_retimed_marker_and_explicit_easing_use_source_clock(self):
        doc = owner_document("Group")
        visual(doc).update(start=1000, scalar="1/2", duration=4000, mediaDuration=8000)
        result = animations.edit_interval(
            doc,
            3,
            dict(schema_version=1, start=2, end=3, values={}, easing="bounce"),
            allow_empty=True,
        )
        self.assertEqual(
            visual(result)["animationTracks"],
            {"visual": [{"endTime": 6000, "duration": 2000, "interp": "bnce"}]},
        )
        self.assertEqual(visual(result)["parameters"], visual(doc)["parameters"])

    def test_marker_creation_refuses_orphaned_coupled_geometry(self):
        doc = owner_document("Callout")
        visual(doc)["parameters"]["scale0"] = {
            "type": "double",
            "defaultValue": 1,
            "keyframes": [{"time": 3000, "endTime": 4000, "duration": 1000, "value": 1.5}],
        }
        with self.assertRaisesRegex(ValueError, "orphaned"):
            animations.edit_interval(
                doc, 3, dict(schema_version=1, start=3, end=4, values={}), allow_empty=True
            )

    def test_set_cli_creates_marker_but_ease_cli_refuses_missing_interval(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, payload, out = [root / n for n in ["source.json", "spec.json", "out.json"]]
            raw = project.encode_document(owner_document("IMFile"))
            source.write_bytes(raw)
            payload.write_text(json.dumps(dict(schema_version=1, start=3, end=4, values={})))
            with patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(
                    animations.main(
                        [
                            "set-interval",
                            str(source),
                            "--clip-id",
                            "3",
                            "--spec",
                            str(payload),
                            "--output",
                            str(out),
                        ]
                    ),
                    0,
                )
            with patch("sys.stderr", new_callable=io.StringIO):
                self.assertEqual(
                    animations.main(
                        [
                            "ease-interval",
                            str(source),
                            "--clip-id",
                            "3",
                            "--start",
                            "3",
                            "--end",
                            "4",
                            "--easing",
                            "linear",
                            "--output",
                            str(root / "missing.json"),
                        ]
                    ),
                    1,
                )
            self.assertEqual(source.read_bytes(), raw)


if __name__ == "__main__":
    unittest.main()
