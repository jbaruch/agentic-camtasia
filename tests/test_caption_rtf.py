from __future__ import annotations

import copy
import io
import json
from pathlib import Path
import tempfile
import unittest
from contextlib import redirect_stdout, redirect_stderr

import captions
from test_captions import closed, fixture


# Independently fixed text-only native Cocoa spelling, including header text
# that must never enter cue coordinates, scoped styles and escaped characters.
HEADER = (
    r"{\rtf1\ansi\ansicpg1252\cocoartf2870"
    "\n"
    r"\cocoatextscaling0\cocoaplatform0"
    r"{\fonttbl\f0\fswiss\fcharset0 ArialMT;\f1\fswiss\fcharset0 Arial-BoldMT;}"
    "\n"
    r"{\colortbl;\red255\green255\blue255;}"
    r"{\*\expandedcolortbl;;}"
    r"\pard\tx560\pardirnatural\partightenfactor0\f0\fs36 \cf0 "
)
NATIVE = HEADER + "First \n" + r"\f1\b caf\'e9" + "\n" + r"\f0\b0  & \i timing}"


def visible(text):
    return "".join(c for c, _ in captions.rtf_characters(text))


def change(start, end, text):
    return dict(start=start, end=end, text=text)


def spec(expected="First café & timing", replacements=None, index=0) -> dict:
    return dict(
        schema_version=1,
        edits=[
            dict(
                index=index,
                expected=expected,
                replacements=replacements
                if replacements is not None
                else [change(6, 10, "COFFEE")],
            )
        ],
    )


class CaptionRtfTests(unittest.TestCase):
    def test_native_header_styles_and_ansi_are_not_visible(self):
        self.assertEqual(visible(NATIVE), "First café & timing")
        self.assertEqual(
            visible(NATIVE.replace("fcharset0", "fcharset0\\cpg1252")), "First café & timing"
        )
        chars = captions.rtf_characters(NATIVE)
        self.assertEqual(NATIVE[slice(*chars[9][1][0])], r"\'e9")

    def test_replace_retains_every_format_control_and_suffix(self):
        result = captions.replace_rtf(NATIVE, "First café & timing", [change(6, 10, "COFFEE")])
        expected = HEADER + "First \n" + r"\f1\b {\uc0 COFFEE}{}" + "\n" + r"\f0\b0  & \i timing}"
        self.assertEqual(result, expected)
        self.assertEqual(visible(result), "First COFFEE & timing")

    def test_cross_group_deletion_keeps_nested_groups_and_controls(self):
        original = HEADER + r"A{\b BC}D{\i EF}G}"
        result = captions.replace_rtf(original, "ABCDEFG", [change(2, 6, "X")])
        self.assertEqual(result, HEADER + r"A{\b B{\uc0 X}{}}{}{\i {}}G}")
        self.assertEqual(visible(result), "ABXG")

    def test_insertion_before_following_style_and_at_end(self):
        original = HEADER + r"A{\b B}C}"
        result = captions.replace_rtf(original, "ABC", [change(1, 1, "X"), change(3, 3, "Y")])
        self.assertEqual(result, HEADER + r"A{\b {\uc0 X}B}C{\uc0 Y}}")
        self.assertEqual(visible(result), "AXBCY")

    def test_adjacent_replacements_use_original_coordinates(self):
        result = captions.replace_rtf(
            HEADER + "abcd}", "abcd", [change(0, 2, "X"), change(2, 4, "YZ")]
        )
        self.assertEqual(result, HEADER + r"{\uc0 X}{}{\uc0 YZ}{}}")

    def test_unicode_fallback_counts_are_scoped_and_deleted_together(self):
        original = HEADER + r"A\u233?{\uc2\u26085??}\u8594?Z}"
        self.assertEqual(visible(original), "Aé日→Z")
        result = captions.replace_rtf(original, "Aé日→Z", [change(1, 4, "é")])
        self.assertEqual(result, HEADER + r"A{\uc0 \u233 }{}{\uc2{}}{}Z}")
        self.assertEqual(visible(result), "AéZ")
        self.assertEqual(visible(HEADER + r"\uc0 A\plain\u8594 X}"), "A→X")

    def test_surrogate_pair_is_one_code_point_with_noncontiguous_spans(self):
        original = HEADER + r"A\u-10179?{\b \u-8704?}B}"
        self.assertEqual(visible(original), "A😀B")
        self.assertEqual(
            captions.replace_rtf(original, "A😀B", [change(1, 2, "X")]),
            HEADER + r"A{\uc0 X}{}{\b {}}B}",
        )
        self.assertEqual(visible(HEADER + r"\uc0\u55357 \u56832 }"), "😀")

    def test_fallback_escape_counts_as_one_character(self):
        original = HEADER + r"\u123\{\u125\}\u92\\\u233\'e9}"
        self.assertEqual(visible(original), "{}\\é")
        result = captions.replace_rtf(original, "{}\\é", [change(0, 4, "")])
        self.assertEqual(result, HEADER + "{}}")

    def test_newline_tabs_escaped_braces_and_unicode_encoding(self):
        text = "café 日 😀 {x} \\ →\nline\tend"
        encoded = captions.rtf_encode(text)
        self.assertEqual(visible(HEADER + encoded + "}"), text)
        self.assertIn(r"\u-10179 \u-8704 ", encoded)
        original = HEADER + "a\\\nb\\par c\\line d\\tab e\\~\\_\\-}"
        self.assertEqual(visible(original), "a\nb\nc\nd\te\u00a0‑\u00ad")

    def test_noop_does_not_reencode_native_text(self):
        self.assertEqual(
            captions.replace_rtf(NATIVE, "First café & timing", [change(6, 10, "café")]), NATIVE
        )

    def test_delete_all_retains_header_and_formatting(self):
        result = captions.replace_rtf(NATIVE, "First café & timing", [change(0, 19, "")])
        self.assertEqual(result, HEADER + "{}\n" + r"\f1\b {}" + "\n" + r"\f0\b0 {}\i {}}")
        self.assertEqual(visible(result), "")

    def test_empty_rtf_insertion_requires_native_style(self):
        with self.assertRaisesRegex(ValueError, "establish its style"):
            captions.replace_rtf(HEADER + "}", "", [change(0, 0, "X")])

    def test_deletion_separates_tokens_at_every_removed_chunk(self):
        for control, token, decoded in [
            (r"\b", r"\par ", "\n"),
            (r"\b0", r"\line ", "\n"),
            (r"\f1", r"\tab ", "\t"),
            (r"\i", r"\{", "{"),
        ]:
            with self.subTest(control=control, token=token):
                original = HEADER + control + token + "text}"
                result = captions.replace_rtf(original, decoded + "text", [change(0, 1, "")])
                self.assertEqual(result, HEADER + control + "{}text}")
                self.assertEqual(visible(result), "text")
        original = HEADER + r"\b\par first\i\par last}"
        result = captions.replace_rtf(original, "\nfirst\nlast", [change(0, 7, "")])
        self.assertEqual(result, HEADER + r"\b{}\i{}last}")
        self.assertEqual(visible(result), "last")
        result = captions.replace_rtf(original, "\nfirst\nlast", [change(0, 7, "X")])
        self.assertEqual(result, HEADER + r"\b{\uc0 X}{}\i{}last}")
        self.assertEqual(visible(result), "Xlast")

    def test_cli_stages_parseable_cue_after_control_token_deletion(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            doc = fixture()
            closed(doc)["keyframes"][0]["value"]["text"] = HEADER + r"\b\par text}"
            source, request, target = (
                root / name for name in ["source.json", "spec.json", "out.json"]
            )
            source.write_text(json.dumps(doc))
            request.write_text(json.dumps(spec("\ntext", [change(0, 1, "")])))
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(
                    captions.main(
                        [
                            "set-rtf-text",
                            str(source),
                            "--clip-id",
                            "3",
                            "--spec",
                            str(request),
                            "--output",
                            str(target),
                        ]
                    ),
                    0,
                )
                self.assertTrue(json.loads(out.getvalue())["written"])
            staged = json.loads(target.read_text())
            self.assertEqual(closed(staged)["keyframes"][0]["value"]["text"], HEADER + r"\b{}text}")
            self.assertEqual(captions.inspect_rtf(staged, 3), [dict(index=0, text="text")])
            self.assertEqual(json.loads(source.read_text()), doc)

    def test_malformed_or_complex_rtf_refuses(self):
        invalid = [
            "plain",
            HEADER + "bad",
            HEADER + "}}",
            HEADER + "}x}",
            HEADER + r"\bin3 abc}",
            HEADER + r"{\pict abc}}",
            HEADER + r"{\object abc}}",
            HEADER + r"{\field abc}}",
            HEADER + r"{\*\unknown abc}}",
            HEADER + r"\v hidden}",
            HEADER + r"\upr abc}",
            HEADER + r"\u-10179?}",
            HEADER + r"\u-8704?}",
            HEADER + r"\uc-1\u233?}",
            HEADER + r"\u65536?}",
            HEADER + r"\u?}",
            HEADER + r"\ansicpg932 x}",
            HEADER + r"\'81}",
            HEADER + "é}",
            HEADER + r"\'xx}",
            HEADER + "\\}",
            HEADER.replace("fcharset0", "fcharset2") + "x}",
            HEADER.replace("fcharset0", "fcharset0\\cpg932") + "x}",
        ]
        for text in invalid:
            with self.subTest(text=text), self.assertRaises(ValueError):
                captions.rtf_characters(text)

    def test_invalid_ranges_and_text_refuse(self):
        invalid = [
            [],
            {},
            [change(True, 1, "X")],
            [change(1, 0, "X")],
            [change(0, 20, "X")],
            [change(0, 2, "X"), change(1, 3, "Y")],
            [change(0, 0, "X"), change(0, 0, "Y")],
            [change(1, 2, None)],
            [dict(start=0, end=1, text="X", extra=True)],
            [change(0, 1, "\x00")],
            [change(0, 1, "\r")],
            [change(0, 1, "\ud800")],
        ]
        for edits in invalid:
            with self.subTest(edits=repr(edits)), self.assertRaises(ValueError):
                captions.replace_rtf(NATIVE, "First café & timing", edits)
        with self.assertRaisesRegex(ValueError, "differs from expected"):
            captions.replace_rtf(NATIVE, "other", [change(0, 1, "X")])

    def test_project_edits_both_owner_forms_and_only_text(self):
        for form, clip_id in [("linked", 3), ("audio", 3), ("imported", 3)]:
            doc = fixture(form)
            frames = closed(doc)["keyframes"]
            frames[0]["value"].update(text=NATIVE, opaque=["value"])
            frames[0]["keep"] = ["point"]
            original = copy.deepcopy(doc)
            result = captions.correct_rtf(doc, clip_id, spec())
            expected = copy.deepcopy(original)
            closed(expected)["keyframes"][0]["value"]["text"] = (
                HEADER + "First \n" + r"\f1\b {\uc0 COFFEE}{}" + "\n" + r"\f0\b0  & \i timing}"
            )
            self.assertEqual(result, expected)
            self.assertEqual(doc, original)
            self.assertEqual(
                captions.inspect_rtf(doc, clip_id), [dict(index=0, text="First café & timing")]
            )

    def test_atomic_late_failure_and_bad_cue_specs(self):
        doc = fixture()
        closed(doc)["keyframes"][0]["value"]["text"] = NATIVE
        original = copy.deepcopy(doc)
        bad = [
            dict(schema_version=2, edits=[]),
            dict(schema_version=1, edits=[]),
            dict(schema_version=1, edits=[dict(index=0)]),
            spec(index=True),
            spec(index=99),
            spec(expected="stale"),
            dict(schema_version=1, edits=spec()["edits"] * 2),
            dict(schema_version=1, edits=spec()["edits"] + spec(index=2)["edits"]),
        ]
        for requested in bad:
            with self.subTest(requested=requested), self.assertRaises(ValueError):
                captions.correct_rtf(doc, 3, requested)
            self.assertEqual(doc, original)
        closed(doc)["keyframes"][0]["value"]["textAttributes"] = {}
        with self.assertRaises(ValueError):
            captions.correct_rtf(doc, 3, spec())

    def test_json_cli_help_inspection_staging_and_refusal(self):
        for command in ["rtf-text", "set-rtf-text"]:
            with self.subTest(command=command), redirect_stdout(io.StringIO()) as out:
                with self.assertRaises(SystemExit) as raised:
                    captions.main([command, "--help"])
                self.assertEqual(raised.exception.code, 0)
                self.assertEqual(json.loads(out.getvalue())["owner"], "camtasia-captions")
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            doc = fixture()
            closed(doc)["keyframes"][0]["value"]["text"] = NATIVE
            source, request, target = (
                root / name for name in ["project.json", "spec.json", "output.json"]
            )
            source.write_text(json.dumps(doc))
            request.write_text(json.dumps(spec()))
            args = [str(source), "--clip-id", "3"]
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(captions.main(["rtf-text", *args]), 0)
                self.assertEqual(
                    json.loads(out.getvalue())["cues"], [dict(index=0, text="First café & timing")]
                )
            with redirect_stdout(io.StringIO()) as out:
                self.assertEqual(
                    captions.main(
                        ["set-rtf-text", *args, "--spec", str(request), "--output", str(target)]
                    ),
                    0,
                )
                self.assertTrue(json.loads(out.getvalue())["written"])
            self.assertEqual(
                visible(closed(json.loads(target.read_text()))["keyframes"][0]["value"]["text"]),
                "First COFFEE & timing",
            )
            request.write_text(json.dumps(spec(expected="stale")))
            with redirect_stderr(io.StringIO()) as err:
                self.assertEqual(
                    captions.main(
                        [
                            "set-rtf-text",
                            *args,
                            "--spec",
                            str(request),
                            "--output",
                            str(root / "bad.json"),
                        ]
                    ),
                    1,
                )
                self.assertIn("expected", json.loads(err.getvalue())["error"])
            self.assertFalse((root / "bad.json").exists())


if __name__ == "__main__":
    unittest.main()
