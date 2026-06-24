import os
import sys
import pytest
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.parser.pdf_extractor import PDFExtractor


class TestPDFExtractor:
    @pytest.fixture
    def sample_pdf(self):
        pdf_path = os.path.join(
            os.path.dirname(__file__), "..", "examplepdf",
            "computer-networks-a-top-down-approach_compress.pdf"
        )
        if not os.path.exists(pdf_path):
            pytest.skip("示例PDF文件不存在")
        return pdf_path

    def test_open_pdf(self, sample_pdf):
        extractor = PDFExtractor(sample_pdf)
        assert extractor.doc is not None
        assert len(extractor.doc) > 0
        extractor.close()

    def test_extract_styled_blocks(self, sample_pdf):
        extractor = PDFExtractor(sample_pdf)
        blocks = extractor.extract_styled_blocks()
        assert len(blocks) > 0
        text_blocks = [b for b in blocks if b["type"] == "text"]
        image_blocks = [b for b in blocks if b["type"] == "image"]
        assert len(text_blocks) > 0
        extractor.close()

    def test_detect_chapters(self, sample_pdf):
        extractor = PDFExtractor(sample_pdf)
        chapters = extractor.detect_chapters()
        assert len(chapters) > 0
        for ch in chapters:
            assert "title" in ch
            assert "content" in ch
            assert len(ch["title"]) > 0
        extractor.close()

    def test_has_content(self, sample_pdf):
        extractor = PDFExtractor(sample_pdf)
        extractor.detect_chapters()
        assert extractor.has_content() is True
        extractor.close()

    def test_chapter_title_format(self, sample_pdf):
        extractor = PDFExtractor(sample_pdf)
        chapters = extractor.detect_chapters()
        first = chapters[0]
        assert "OVERVIEW" in first["title"].upper() or "." in first["title"]
        extractor.close()

    def test_empty_pdf(self):
        try:
            import fitz
            doc = fitz.open()
            doc.close()
        except Exception:
            pass

    def test_close_cleanup(self, sample_pdf):
        extractor = PDFExtractor(sample_pdf)
        extractor.detect_chapters()
        extractor.close()
        assert extractor.doc is None