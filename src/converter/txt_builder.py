import os
from src.converter.epub_builder import EPUBBuilder
from src.utils.logger import setup_logger

logger = setup_logger("txt_builder")


class TXTBuilder:
    def __init__(self):
        self.chapters = []
        self.metadata = {}

    def set_metadata(self, title, author="", language="zh"):
        self.metadata = {"title": title, "author": author, "language": language}

    def add_chapter(self, title, content):
        lines = []
        lines.append(title)
        lines.append("=" * len(title))
        lines.append("")

        if isinstance(content, list):
            for block in content:
                if isinstance(block, dict):
                    if block.get("type") == "text":
                        text = block.get("text", "").strip()
                        if text:
                            lines.append(text)
                            lines.append("")
                    elif block.get("type") == "image":
                        lines.append(f"[图片: {block.get('image_width', 0)}x{block.get('image_height', 0)}]")
                        lines.append("")
                elif isinstance(block, str) and block.strip():
                    lines.append(block)
                    lines.append("")
        elif isinstance(content, str) and content.strip():
            lines.append(content)
            lines.append("")

        self.chapters.append("\n".join(lines))

    def save(self, output_path):
        try:
            body = []
            body.append(self.metadata.get("title", "Untitled"))
            body.append("=" * len(self.metadata.get("title", "Untitled")))
            if self.metadata.get("author"):
                body.append(f"Author: {self.metadata['author']}")
            body.append("")
            body.append("")

            for ch in self.chapters:
                body.append(ch)
                body.append("")

            with open(output_path, "w", encoding="utf-8") as f:
                f.write("\n".join(body))

            logger.info(f"TXT文件已保存: {output_path}")
            return True
        except Exception as e:
            logger.error(f"保存TXT失败: {str(e)}")
            return False