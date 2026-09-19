import tempfile
from pathlib import Path
import unittest

from demo.parser import parse_document, enrich_ocr

ROOT = Path(__file__).resolve().parents[1]


class ParsingTests(unittest.TestCase):
    def parse(self, filename):
        with tempfile.TemporaryDirectory(dir=ROOT / "data") as folder:
            return parse_document(ROOT / "samples" / filename, Path(folder))

    def test_ppt_slide_location_and_picture(self):
        pages = self.parse("06-synthetic-research.pptx")
        self.assertEqual(len(pages), 2)
        self.assertEqual(pages[0]["location"], "投影片 1")
        self.assertIn("48°C", pages[0]["text"])
        self.assertEqual(pages[0]["images"], ["image-1.png"])
        self.assertIn("不能直接", pages[1]["text"])

    def test_docx_does_not_invent_page_numbers(self):
        pages = self.parse("07-synthetic-summary.docx")
        self.assertIn("未計算", pages[0]["location"])
        self.assertTrue(pages[0]["images"])

    def test_excel_cells_keep_units_and_conditions(self):
        pages = self.parse("08-synthetic-results.xlsx")
        self.assertIn("實驗比較", pages[0]["location"])
        self.assertIn("B2=25", pages[0]["text"])
        self.assertIn("B3=35", pages[0]["text"])
        self.assertIn("倍率", pages[0]["text"])

    def test_picture_without_llm_does_not_claim_ocr(self):
        pages = self.parse("synthetic-temperature-chart.png")
        self.assertEqual(pages[0]["text"], "")
        self.assertEqual(len(pages[0]["images"]), 1)

    def test_ocr_and_scanned_pdf_source_page(self):
        with tempfile.TemporaryDirectory(dir=ROOT / "data") as folder:
            pages = parse_document(ROOT / "samples/09-synthetic-scanned-chart.pdf", Path(folder))
            self.assertEqual(pages[0]["location"], "PDF 第 1 頁")
            self.assertEqual(enrich_ocr(pages, Path(folder)), [])
            self.assertIn("48", pages[0]["text"])
            self.assertIn("OCR", pages[0]["text"])


if __name__ == "__main__":
    unittest.main()
