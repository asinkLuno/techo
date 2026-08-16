import unittest
from pathlib import Path
from unittest import mock

from techo import sizes
from techo.build import build_edition, compile_tex, write_spread
from techo.texutil import tex_escape


class TexEscapeTests(unittest.TestCase):
    def test_escapes_ten_special_characters(self) -> None:
        self.assertEqual(
            tex_escape("a\\b&c%d$e#f_g{h}i~j^k"),
            "a\\textbackslash{}b\\&c\\%d\\$e\\#f\\_g\\{h\\}i\\textasciitilde{}j"
            "\\textasciicircum{}k",
        )

    def test_empty_and_none(self) -> None:
        self.assertEqual(tex_escape(""), "")
        self.assertEqual(tex_escape(None), "")

    def test_plain_text_unchanged(self) -> None:
        self.assertEqual(tex_escape("Inception 2010"), "Inception 2010")


class CompileTexTests(unittest.TestCase):
    def test_runs_xelatex_requested_passes_with_flags(self) -> None:
        with mock.patch("techo.build.subprocess.run") as run:
            compile_tex("book.tex", Path("/tmp/out"), passes=2)
        self.assertEqual(run.call_count, 2)
        for call in run.call_args_list:
            args, kwargs = call
            self.assertEqual(
                args[0],
                ["xelatex", "-interaction=nonstopmode", "-halt-on-error", "book.tex"],
            )
            self.assertEqual(kwargs["cwd"], Path("/tmp/out"))
            self.assertTrue(kwargs["check"])
            self.assertIsNotNone(kwargs["stdout"])

    def test_default_is_one_pass(self) -> None:
        with mock.patch("techo.build.subprocess.run") as run:
            compile_tex("page.tex", Path("."))
        self.assertEqual(run.call_count, 1)

    def test_quiet_silences_stdout(self) -> None:
        with mock.patch("techo.build.subprocess.run") as run:
            compile_tex("page.tex", Path("."), quiet=False)
        self.assertIsNone(run.call_args.kwargs["stdout"])


class BuildEditionTests(unittest.TestCase):
    def test_writes_sizes_tex_content_and_wrapper(self) -> None:
        with mock.patch("techo.build.compile_tex") as compile_, mock.patch(
            "techo.build.OUTPUTS", Path("/tmp/editions")
        ):
            out = build_edition(
                "demo-a5",
                ["\\thispagestyle{empty}%", "\\null"],
                "../../src/techo/midori_grid/midori_grid.tex",
                defs={"EDITION": "a5", "BINDING": 15},
            )
        self.assertEqual(out, Path("/tmp/editions/demo-a5"))
        self.assertEqual(
            (out / "content.tex").read_text(),
            "\\thispagestyle{empty}%\n\\null\n",
        )
        self.assertEqual(
            (out / "demo-a5.tex").read_text(),
            "\\def\\EDITION{a5}%\n\\def\\BINDING{15}%\n"
            "\\input{../../src/techo/midori_grid/midori_grid.tex}%\n",
        )
        compile_.assert_called_once_with(
            "demo-a5.tex", Path("/tmp/editions/demo-a5"), passes=1, quiet=True
        )

    def test_string_content_and_no_content(self) -> None:
        with mock.patch("techo.build.compile_tex"), mock.patch(
            "techo.build.OUTPUTS", Path("/tmp/editions")
        ):
            out = build_edition("s1", "body\\clearpage", "../../x.tex", compile=False)
            self.assertEqual((out / "content.tex").read_text(), "body\\clearpage\n")
            # template with no content.tex (e.g. tn-cover)
            out2 = build_edition("s2", None, "../../x.tex", compile=False)
            self.assertFalse((out2 / "content.tex").exists())

    def test_compile_false_skips_xelatex(self) -> None:
        with mock.patch("techo.build.compile_tex") as compile_:
            build_edition("s3", [], "../../x.tex", compile=False)
        compile_.assert_not_called()

    def test_defs_rendered_in_wrapper(self) -> None:
        with mock.patch("techo.build.compile_tex"), mock.patch(
            "techo.build.OUTPUTS", Path("/tmp/editions")
        ):
            out = build_edition("s4", [], "../../x.tex", defs={"CJKFONTPATH": "src/"})
            self.assertEqual(
                (out / "s4.tex").read_text(),
                "\\def\\CJKFONTPATH{src/}%\n\\input{../../x.tex}%\n",
            )


class WriteSpreadTests(unittest.TestCase):
    def setUp(self) -> None:
        self.out = Path("/tmp/editions/demo")
        self.out.mkdir(parents=True, exist_ok=True)

    def test_2up_spread(self) -> None:
        with mock.patch("techo.build.compile_tex") as compile_:
            pdf = write_spread(self.out, "demo", 67.0, 105.0)
        self.assertEqual(pdf, self.out / "spread.pdf")
        tex = (self.out / "spread.tex").read_text()
        self.assertIn("paperwidth=134.0mm, paperheight=105.0mm", tex)
        self.assertIn("\\includepdf[pages={1,2}, nup=2x1, width=67.0mm, height=105.0mm]{demo.pdf}", tex)
        compile_.assert_called_once_with("spread.tex", self.out, quiet=True)

    def test_booklet_spread(self) -> None:
        with mock.patch("techo.build.compile_tex"):
            write_spread(self.out, "demo", 67.0, 105.0, booklet=True)
        tex = (self.out / "spread.tex").read_text()
        self.assertIn("\\includepdf[pages=-, booklet=true, landscape]{demo.pdf}", tex)


class SizesAccessorTests(unittest.TestCase):
    def test_resolved_layouts_unchanged(self) -> None:
        # spot-check values that come from defaults vs overrides
        self.assertEqual(sizes.GREEN_DOT["74m5"]["binding"], 12)  # pure default
        self.assertEqual(sizes.GREEN_DOT["a4"]["binding"], 20)  # override
        self.assertEqual(sizes.MIDORI_GRID["a6per"]["gap_size"], 1.0)  # default
        self.assertEqual(sizes.MOVIE_REPORT["a5fc"]["compact"], False)  # default
        self.assertEqual(sizes.MOVIE_REPORT["a7l"]["dither_px"], 170)  # override

    def test_accessors_return_same_as_tables(self) -> None:
        for size in ("a4", "67m5"):
            self.assertEqual(sizes.green_dot(size), sizes.GREEN_DOT[size])
            self.assertEqual(sizes.nightowl(size), sizes.NIGHTOWL[size])
            self.assertEqual(sizes.midori_grid(size), sizes.MIDORI_GRID[size])
            self.assertEqual(sizes.movie_report(size), sizes.MOVIE_REPORT[size])

    def test_missing_size_friendly_error(self) -> None:
        with self.assertRaisesRegex(ValueError, "no green-dot layout"):
            sizes.green_dot("a7l")  # a7l is a page size but has no green-dot layout
        with self.assertRaisesRegex(ValueError, "supported sizes"):
            sizes.nightowl("tnp")
        with self.assertRaisesRegex(ValueError, "no movie-report layout"):
            sizes.movie_report("nope")


if __name__ == "__main__":
    unittest.main()
