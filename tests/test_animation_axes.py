from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from test_animations import fixture, visual
from test_motion_paths import linked_document, wrapper
import animations
import project


VALUES = {"rotation0": 0.698131700797732, "rotation2": 0.523598775598299, "translation2": 200}


def axis_spec():
    return dict(
        schema_version=1, start=1, end=2, values=VALUES, initial={name: 0 for name in VALUES}
    )


class AnimationAxisTests(unittest.TestCase):
    def test_axes_save_fixed_native_double_curves_without_changing_linked_audio(self):
        doc = linked_document()
        frozen = copy.deepcopy(doc)
        result = animations.edit_interval(doc, 10, axis_spec())
        for name, value in VALUES.items():
            self.assertEqual(
                visual(result)["parameters"][name],
                {
                    "type": "double",
                    "defaultValue": 0.0,
                    "keyframes": [
                        {"time": 1000, "endTime": 2000, "duration": 1000, "value": value}
                    ],
                },
            )
        self.assertEqual(
            visual(result)["animationTracks"], {"visual": [{"endTime": 2000, "duration": 1000}]}
        )
        self.assertEqual(wrapper(result)["audio"], wrapper(doc)["audio"])
        self.assertEqual(wrapper(result)["metadata"], wrapper(doc)["metadata"])
        self.assertEqual(result["sourceBin"], doc["sourceBin"])
        self.assertEqual(doc, frozen)

    def test_global_easing_updates_new_axes_and_preserves_parameter_level_easing(self):
        payload = axis_spec()
        payload["parameterEasing"] = {"rotation2": "exponential"}
        doc = animations.edit_interval(fixture(), 3, payload)
        result = animations.edit_interval(
            doc, 3, dict(schema_version=1, start=1, end=2, values={}, easing="linear")
        )
        for name in VALUES:
            self.assertEqual(visual(result)["parameters"][name]["keyframes"][0]["interp"], "linr")
        self.assertEqual(visual(result)["parameters"]["rotation2"]["interp"], "eioe")
        self.assertEqual(visual(result)["animationTracks"]["visual"][0]["interp"], "linr")

    def test_removal_omits_zero_axes_retains_nondefault_initial_and_other_intervals(self):
        doc = fixture()
        result = animations.remove_interval(animations.edit_interval(doc, 3, axis_spec()), 3, 1, 2)
        self.assertEqual(visual(result)["parameters"], visual(doc)["parameters"])
        for name in VALUES:
            initial = fixture()
            visual(initial)["parameters"][name] = 0.125
            payload = dict(schema_version=1, start=1, end=2, values={name: VALUES[name]})
            animated = animations.edit_interval(initial, 3, payload)
            self.assertEqual(
                visual(animations.remove_interval(animated, 3, 1, 2))["parameters"][name], 0.125
            )
            other = animations.edit_interval(animated, 3, {**payload, "start": 3, "end": 4})
            removed = animations.remove_interval(other, 3, 1, 2)
            self.assertEqual(
                visual(removed)["parameters"][name]["keyframes"],
                [{"time": 3000, "endTime": 4000, "duration": 1000, "value": VALUES[name]}],
            )

    def test_new_axes_keep_exact_trimmed_retimed_source_positions(self):
        doc = fixture()
        visual(doc).update(
            start=1000, mediaStart=1000, scalar="2/3", duration=4000, mediaDuration=6000
        )
        result = animations.edit_interval(doc, 3, axis_spec())
        for name in VALUES:
            self.assertEqual(
                visual(result)["parameters"][name]["keyframes"][0],
                {"time": 2500, "endTime": 4000, "duration": 1500, "value": VALUES[name]},
            )
        self.assertEqual(visual(result)["start"], 1000)

    def test_cli_stages_axis_candidates_and_removal_without_mutating_input(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            source, spec, candidate, removed = [
                root / name
                for name in ["source.json", "spec.json", "candidate.json", "removed.json"]
            ]
            raw = project.encode_document(fixture())
            source.write_bytes(raw)
            spec.write_text(json.dumps(axis_spec()))
            with patch("sys.stdout", new_callable=io.StringIO) as stdout:
                self.assertEqual(
                    animations.main(
                        [
                            "set-interval",
                            str(source),
                            "--clip-id",
                            "3",
                            "--spec",
                            str(spec),
                            "--output",
                            str(candidate),
                        ]
                    ),
                    0,
                )
                self.assertFalse(json.loads(stdout.getvalue())["nativeVerified"])
            with patch("sys.stdout", new_callable=io.StringIO):
                self.assertEqual(
                    animations.main(
                        [
                            "remove-interval",
                            str(candidate),
                            "--clip-id",
                            "3",
                            "--start",
                            "1",
                            "--end",
                            "2",
                            "--output",
                            str(removed),
                        ]
                    ),
                    0,
                )
            self.assertEqual(source.read_bytes(), raw)
            self.assertEqual(
                visual(project.load(removed)[0])["parameters"], visual(fixture())["parameters"]
            )


if __name__ == "__main__":
    unittest.main()
