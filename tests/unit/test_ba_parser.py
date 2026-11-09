import shutil
import tempfile
import unittest
from pathlib import Path
from unittest import mock

from tests.helpers import FIXTURES  # noqa: F401  (sets sys.path)
from s2s import ba_parser
from s2s.common import Spec2ShipError

BA = FIXTURES / "ba"


class MarkdownTests(unittest.TestCase):
    def setUp(self):
        self.ir = ba_parser.parse_document(BA / "customer-management.md")

    def test_structure(self):
        self.assertEqual(self.ir["format"], "markdown")
        self.assertEqual(self.ir["language"], "en")
        types = [b["type"] for b in self.ir["blocks"]]
        for t in ("heading", "paragraph", "list_item", "table"):
            self.assertIn(t, types)

    def test_section_and_line_refs(self):
        b = next(b for b in self.ir["blocks"] if b["text"].startswith("Sales staff can search"))
        self.assertEqual(b["section"], "3.1")
        self.assertEqual(b["section_title"], "3.1 Search customer")
        self.assertEqual(b["line"], 18)
        self.assertEqual(b["section_path"][-1], "3.1 Search customer")

    def test_table_cells(self):
        t = next(b for b in self.ir["blocks"] if b["type"] == "table")
        self.assertEqual(t["header"], ["Field", "Rule"])
        self.assertEqual(t["rows"][0], ["Name", "Partial, case-insensitive"])

    def test_injection_text_is_data_with_notice(self):
        self.assertIn("untrusted", self.ir["notice"])
        self.assertTrue(any("Ignore all previous instructions" in b.get("text", "") for b in self.ir["blocks"]))

    def test_links_and_code(self):
        ir = ba_parser.parse_markdown_text("# T\n\nSee [spec](https://x.test/a).\n\n```\n# not a heading\n```\n")
        self.assertEqual(ir["links"][0]["url"], "https://x.test/a")
        self.assertEqual([b["type"] for b in ir["blocks"]], ["heading", "paragraph", "code"])


class DocxTests(unittest.TestCase):
    def setUp(self):
        self.ir = ba_parser.parse_document(BA / "quan-ly-khach-hang.docx")

    def test_vietnamese_detected(self):
        self.assertEqual(self.ir["language"], "vi")

    def test_headings_sections_tables(self):
        heads = [b for b in self.ir["blocks"] if b["type"] == "heading"]
        self.assertEqual(heads[2]["text"], "1.1 Tìm theo tên hoặc số điện thoại")
        self.assertEqual(heads[2]["level"], 2)
        table = next(b for b in self.ir["blocks"] if b["type"] == "table")
        self.assertEqual(table["header"], ["Trường", "Quy tắc"])
        self.assertEqual(table["rows"][1], ["Số điện thoại", "Khớp chính xác"])

    def test_list_and_page_estimate(self):
        li = next(b for b in self.ir["blocks"] if b["type"] == "list_item")
        self.assertIn("20 khách hàng", li["text"])
        create = next(b for b in self.ir["blocks"] if b.get("text", "").startswith("2 Tạo"))
        self.assertEqual(create["page"], 2)
        self.assertTrue(any("estimated" in w for w in self.ir["warnings"]))

    def test_hyperlink(self):
        self.assertEqual(self.ir["links"][0]["url"], "https://example.com/glossary")

    def test_invalid_docx(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            bad = tmp / "bad.docx"
            bad.write_text("not a zip", encoding="utf-8")
            with self.assertRaises(Spec2ShipError):
                ba_parser.parse_document(bad)
        finally:
            shutil.rmtree(tmp)


class PdfTests(unittest.TestCase):
    def test_text_pdf_pages(self):
        ir = ba_parser.parse_document(BA / "customer-management.pdf")
        self.assertEqual(ir["pages"], 3)
        self.assertFalse(ir["ocr_required"])
        b = next(b for b in ir["blocks"] if "search customers by name" in b.get("text", ""))
        self.assertEqual(b["page"], 2)
        self.assertEqual(b["section"], "3.1")

    def test_builtin_extractor_fallback(self):
        with mock.patch.object(ba_parser, "_pdf_pages_pdftotext", return_value=None), \
             mock.patch.object(ba_parser, "_pdf_pages_pypdf", return_value=None):
            ir = ba_parser.parse_document(BA / "customer-management.pdf")
        self.assertEqual(ir["extractor"], "builtin")
        self.assertEqual(ir["pages"], 3)
        self.assertTrue(any("limited built-in" in w for w in ir["warnings"]))
        sec = next(b for b in ir["blocks"] if b.get("section") == "3.2")
        self.assertEqual(sec["page"], 3)

    def test_scanned_pdf_requires_ocr(self):
        ir = ba_parser.parse_document(BA / "scanned.pdf")
        self.assertTrue(ir["ocr_required"])
        self.assertTrue(any(w.startswith("OCR_REQUIRED") for w in ir["warnings"]))

    def test_scanned_pdf_builtin(self):
        with mock.patch.object(ba_parser, "_pdf_pages_pdftotext", return_value=None), \
             mock.patch.object(ba_parser, "_pdf_pages_pypdf", return_value=None):
            ir = ba_parser.parse_document(BA / "scanned.pdf")
        self.assertTrue(ir["ocr_required"])


class InputErrors(unittest.TestCase):
    def test_missing_and_unsupported(self):
        with self.assertRaises(Spec2ShipError):
            ba_parser.parse_document(BA / "nope.md")
        with self.assertRaisesRegex(Spec2ShipError, "Unsupported"):
            ba_parser.parse_document(FIXTURES / "run" / "tasks.json")

    def test_language(self):
        self.assertEqual(ba_parser.detect_language("Người dùng có thể tìm kiếm khách hàng"), "vi")
        self.assertEqual(ba_parser.detect_language("The user can search the customer list"), "en")
        self.assertEqual(ba_parser.detect_language("12345"), "unknown")


if __name__ == "__main__":
    unittest.main()
