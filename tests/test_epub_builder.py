import os
import sys
import pytest
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from src.converter.epub_builder import EPUBBuilder


class TestEPUBBuilder:
    @pytest.fixture
    def builder(self):
        builder = EPUBBuilder()
        builder.set_metadata("Test Book")
        return builder

    def test_set_metadata(self, builder):
        assert builder.book is not None
        assert builder.book.title == "Test Book"

    def test_add_chapter(self, builder):
        content = [{"type": "text", "text": "Hello World", "font_size": 12}]
        result = builder.add_chapter("Chapter 1", content, 1)
        assert result is True

    def test_add_chapter_empty(self, builder):
        content = []
        result = builder.add_chapter("Empty", content, 1)
        assert result is True

    def test_add_chapter_only_spaces(self, builder):
        content = [{"type": "text", "text": "   ", "font_size": 12}]
        builder.add_chapter("Spaces", content, 1)
        assert len(builder.spine) == 2

    def test_add_image_bytes(self, builder):
        import struct
        fake_png = (
            b'\x89PNG\r\n\x1a\n' +
            b'\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde' +
            b'\x00\x00\x00\x0cIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N' +
            b'\x00\x00\x00\x00IEND\xaeB`\x82'
        )
        builder.add_image_bytes(fake_png, "test.png")
        assert len(builder.images) == 1

    def test_save_epub(self, builder):
        content = [{"type": "text", "text": "Test content", "font_size": 12}]
        builder.add_chapter("Chapter 1", content, 1)

        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            output_path = f.name

        try:
            result = builder.save(output_path)
            assert result is True
            assert os.path.exists(output_path)
            assert os.path.getsize(output_path) > 0
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_save_empty_epub(self, builder):
        with tempfile.NamedTemporaryFile(suffix=".epub", delete=False) as f:
            output_path = f.name

        try:
            result = builder.save(output_path)
            assert result is False
        finally:
            if os.path.exists(output_path):
                os.unlink(output_path)

    def test_create_chapter_html_with_image(self, builder):
        content = [
            {"type": "text", "text": "Some text", "font_size": 12},
            {"type": "image", "page": 1, "image_width": 100, "image_height": 50,
             "image_ext": "png", "image_name": "image_0001_100x50.png"},
        ]
        html = builder.create_chapter_html("Test", content, 1)
        assert "<img" in html
        assert "image_0001_100x50.png" in html
        assert "<h1" in html