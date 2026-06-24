import fitz
import os
import re
from PIL import Image
import io
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class PDFExtractor:
    def __init__(self, pdf_path):
        self.pdf_path = pdf_path
        self.doc = None
        self.chapters = []
        self.images = []
        self.styled_blocks = []
        self.open_pdf()
    
    def open_pdf(self):
        try:
            self.doc = fitz.open(self.pdf_path)
            logger.info(f"成功打开PDF文件: {self.pdf_path}")
        except Exception as e:
            logger.error(f"无法打开PDF文件: {str(e)}")
            raise Exception(f"无法打开PDF文件: {str(e)}")
    
    def extract_images(self):
        self.images = []
        for page_num in range(len(self.doc)):
            try:
                page = self.doc[page_num]
                img_list = page.get_images(full=True)
                for img_index, img in enumerate(img_list):
                    try:
                        xref = img[0]
                        base_image = self.doc.extract_image(xref)
                        if base_image and "image" in base_image:
                            image_bytes = base_image["image"]
                            image_ext = base_image.get("ext", "png")
                            img_data = {
                                "page": page_num,
                                "index": img_index,
                                "bytes": image_bytes,
                                "ext": image_ext,
                                "width": base_image.get("width", 0),
                                "height": base_image.get("height", 0)
                            }
                            self.images.append(img_data)
                    except Exception as e:
                        logger.warning(f"提取图片失败 (页{page_num}, 索引{img_index}): {str(e)}")
            except Exception as e:
                logger.warning(f"处理页面{page_num}图片失败: {str(e)}")
        logger.info(f"共提取到 {len(self.images)} 张图片")
        return self.images
    
    def extract_styled_blocks(self):
        self.styled_blocks = []
        for page_num in range(len(self.doc)):
            try:
                page = self.doc[page_num]
                blocks = page.get_text("dict")["blocks"]
                
                combined_blocks = []
                for block in blocks:
                    if block["type"] == 0:
                        for line in block["lines"]:
                            for span in line["spans"]:
                                entry = {
                                    "type": "text",
                                    "text": span["text"].strip(),
                                    "font": span.get("font", ""),
                                    "font_size": span.get("size", 12),
                                    "bold": "Bold" in span.get("font", ""),
                                    "italic": "Italic" in span.get("font", ""),
                                    "color": span.get("color", 0),
                                    "page": page_num,
                                    "x0": span.get("x0", 0),
                                    "y0": span.get("y0", 0),
                                    "x1": span.get("x1", 0),
                                    "y1": span.get("y1", 0),
                                }
                                combined_blocks.append(entry)
                    elif block["type"] == 1:
                        if "image" in block and block["image"]:
                            entry = {
                                "type": "image",
                                "page": page_num,
                                "x0": block["bbox"][0],
                                "y0": block["bbox"][1],
                                "x1": block["bbox"][2],
                                "y1": block["bbox"][3],
                                "image_bytes": block["image"],
                                "image_ext": block.get("ext", "png"),
                                "image_width": block.get("width", 0),
                                "image_height": block.get("height", 0),
                            }
                            combined_blocks.append(entry)
                
                combined_blocks.sort(key=lambda b: (b["y0"], b["x0"]))
                
                for entry in combined_blocks:
                    if entry["type"] == "text":
                        if entry["text"]:
                            self.styled_blocks.append(entry)
                    elif entry["type"] == "image":
                        self.styled_blocks.append(entry)
                        
            except Exception as e:
                logger.warning(f"处理页面{page_num}失败: {str(e)}")
        
        text_count = sum(1 for b in self.styled_blocks if b["type"] == "text")
        img_count = sum(1 for b in self.styled_blocks if b["type"] == "image")
        logger.info(f"共提取到 {text_count} 个文本块, {img_count} 个图片块")
        return self.styled_blocks
    
    def detect_chapters(self):
        if not self.styled_blocks:
            self.extract_styled_blocks()
        
        CHAPTER_NUM_PATTERN = re.compile(
            r'^(第[\u4e00-\u9fa5\d]+章|Chapter\s+\d+|\d+(\.\d+)*)\s*$'
        )
        
        chapters = []
        current_chapter = {
            "title": "",
            "content": [],
            "start_page": 0,
            "end_page": 0,
            "level": 1
        }
        
        title_patterns = [
            r'^第[\u4e00-\u9fa5\d]+章',
            r'^Chapter\s+\d+',
            r'^\d+\.\s+.+',
            r'^[\u4e00-\u9fa5]+篇',
            r'^[\u4e00-\u9fa5]+章',
            r'^\d+\s*[、.]?\s*.+',
        ]
        
        i = 0
        blocks = self.styled_blocks
        while i < len(blocks):
            block = blocks[i]
            
            if block["type"] == "image":
                if current_chapter["title"] or len(chapters) == 0:
                    current_chapter["content"].append(block)
                i += 1
                continue
            
            text = block["text"]
            font_size = block["font_size"]
            
            is_title = False
            level = 1
            
            if font_size > 16:
                level = 1
                is_title = any(re.match(pattern, text) for pattern in title_patterns)
            elif font_size > 14:
                level = 2
                is_title = any(re.match(pattern, text) for pattern in title_patterns)
            
            if is_title and len(text) > 0 and len(text) < 100:
                if current_chapter["title"]:
                    current_chapter["end_page"] = block["page"]
                    chapters.append(current_chapter.copy())
                
                title_parts = [text]
                j = i + 1
                while j < len(blocks) and j < i + 6:
                    next_block = blocks[j]
                    if next_block["type"] != "text":
                        break
                    next_text = next_block["text"]
                    next_font = next_block["font_size"]
                    if next_font > 14 and not CHAPTER_NUM_PATTERN.match(next_text):
                        if not any(re.match(pattern, next_text) for pattern in title_patterns):
                            title_parts.append(next_text)
                            j += 1
                            continue
                    break
                
                full_title = " ".join(title_parts)
                
                current_chapter = {
                    "title": full_title,
                    "content": [],
                    "start_page": block["page"],
                    "end_page": block["page"],
                    "level": level
                }
                i = j
                continue
            else:
                if current_chapter["title"] or len(chapters) == 0:
                    current_chapter["content"].append(block)
            
            i += 1
        
        if current_chapter["title"] or (len(current_chapter["content"]) > 0 and len(chapters) == 0):
            current_chapter["end_page"] = self.styled_blocks[-1]["page"] if self.styled_blocks else 0
            if not current_chapter["title"]:
                current_chapter["title"] = "内容"
            chapters.append(current_chapter)
        
        if not chapters:
            all_text = ""
            for page_num in range(len(self.doc)):
                try:
                    page = self.doc[page_num]
                    all_text += page.get_text()
                except Exception as e:
                    logger.warning(f"提取页面{page_num}文本失败: {str(e)}")
            
            if all_text.strip():
                chapters.append({
                    "title": "内容",
                    "content": [{"type": "text", "text": all_text}],
                    "start_page": 0,
                    "end_page": len(self.doc) - 1,
                    "level": 1
                })
        
        self.chapters = chapters
        logger.info(f"共识别到 {len(chapters)} 个章节")
        for ch in chapters:
            logger.debug(f"  章节: {ch['title']}")
        return chapters
    
    def has_content(self):
        if not self.chapters:
            logger.debug("has_content: 章节列表为空")
            return False
        
        for i, chapter in enumerate(self.chapters):
            content = chapter.get("content")
            if not content:
                continue
            
            if isinstance(content, list):
                for block in content:
                    if isinstance(block, dict):
                        if block.get("type") == "text" and block.get("text", "").strip():
                            return True
                        elif block.get("type") == "image":
                            return True
                    elif isinstance(block, str) and block.strip():
                        return True
            elif isinstance(content, str) and content.strip():
                return True
        
        logger.debug("has_content: 所有章节内容都为空")
        return False
    
    def save_image(self, img_data, output_dir):
        os.makedirs(output_dir, exist_ok=True)
        filename = f"image_{img_data['page']}_{img_data['index']}.{img_data['ext']}"
        filepath = os.path.join(output_dir, filename)
        
        try:
            img = Image.open(io.BytesIO(img_data["bytes"]))
            img.save(filepath)
            return filename
        except Exception as e:
            logger.warning(f"保存图片失败: {str(e)}")
            return None
    
    def get_page_dimensions(self):
        if self.doc and len(self.doc) > 0:
            rect = self.doc[0].rect
            return rect.width, rect.height
        return 612, 792
    
    def close(self):
        if self.doc:
            self.doc.close()
            self.doc = None
            logger.info("PDF文件已关闭")
