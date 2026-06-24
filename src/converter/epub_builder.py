from ebooklib import epub
import os
import uuid
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class EPUBBuilder:
    def __init__(self):
        self.book = epub.EpubBook()
        self.toc = []
        self.spine = ['nav']
        self.images = []
        self.stylesheets = []
    
    def set_metadata(self, title, author="Unknown", language="zh"):
        self.book.set_title(title)
        self.book.set_language(language)
        self.book.add_author(author)
        logger.info(f"设置EPUB元数据: 标题={title}, 作者={author}")
    
    def add_stylesheet(self, css_content):
        style = epub.EpubItem(
            uid=f'style_{uuid.uuid4().hex}',
            file_name=f'style/style_{len(self.stylesheets)}.css',
            media_type='text/css',
            content=css_content
        )
        self.book.add_item(style)
        self.stylesheets.append(style)
        return style
    
    def create_chapter_html(self, title, styled_content, chapter_num):
        chapter_id = f'chapter_{chapter_num}'
        
        html_parts = []
        for block in styled_content:
            if isinstance(block, dict):
                if block.get("type") == "image":
                    page = block.get("page", 0)
                    img_id = f"img_{chapter_num}_{page}_{len(html_parts)}"
                    img_name = block.get("image_name", f"image_{page}_{block.get('image_width', 0)}x{block.get('image_height', 0)}.{block.get('image_ext', 'png')}")
                    html_parts.append(
                        f'<div style="text-align:center; margin:1em 0;">'
                        f'<img id="{img_id}" src="images/{img_name}" '
                        f'alt="Figure" style="max-width:100%; height:auto;"/>'
                        f'</div>'
                    )
                    continue
                
                if "text" in block:
                    text = block["text"]
                    font_size = block.get("font_size", 12)
                    bold = block.get("bold", False)
                    italic = block.get("italic", False)
                    
                    style_attrs = []
                    if font_size > 16:
                        style_attrs.append(f'font-size: {font_size}px')
                    if bold:
                        style_attrs.append('font-weight: bold')
                    if italic:
                        style_attrs.append('font-style: italic')
                    
                    style_str = '; '.join(style_attrs) if style_attrs else ''
                    
                    if font_size > 16:
                        html_parts.append(f'<h2 style="{style_str}">{text}</h2>')
                    elif font_size > 14:
                        html_parts.append(f'<h3 style="{style_str}">{text}</h3>')
                    else:
                        p_style = 'text-indent: 2em; margin: 0.5em 0;'
                        if style_str:
                            p_style += f' {style_str}'
                        html_parts.append(f'<p style="{p_style}">{text}</p>')
            else:
                text = str(block) if block else ''
                if text.strip():
                    html_parts.append(f'<p style="text-indent: 2em; margin: 0.5em 0;">{text}</p>')
        
        body_content = f'<h1 id="{chapter_id}">{title}</h1>\n{chr(10).join(html_parts)}'
        
        return body_content
    
    def add_chapter(self, title, styled_content, chapter_num):
        body_content = self.create_chapter_html(title, styled_content, chapter_num)
        
        if not body_content.strip():
            logger.warning(f"跳过空章节: {title}")
            return False
        
        if len(body_content) < 10:
            logger.warning(f"章节 {title} 内容过短，跳过")
            return False
        
        chapter = epub.EpubHtml(
            title=title,
            file_name=f'chapter_{chapter_num}.xhtml',
            lang='zh'
        )
        chapter.content = body_content
        
        self.book.add_item(chapter)
        self.spine.append(chapter)
        
        self.toc.append(
            epub.Link(f'chapter_{chapter_num}.xhtml', title, f'chapter_{chapter_num}')
        )
        logger.info(f"添加章节: {title}")
        return True
    
    def add_image(self, image_path, image_name):
        try:
            with open(image_path, 'rb') as f:
                image_content = f.read()
            self._add_image_bytes(image_content, image_name)
        except Exception as e:
            logger.warning(f"添加图片失败: {str(e)}")
    
    def add_image_bytes(self, image_bytes, image_name):
        self._add_image_bytes(image_bytes, image_name)
    
    def _add_image_bytes(self, image_content, image_name):
        ext = image_name.split(".")[-1].lower() if "." in image_name else "png"
        media_type_map = {
            'png': 'image/png',
            'jpg': 'image/jpeg',
            'jpeg': 'image/jpeg',
            'gif': 'image/gif',
            'svg': 'image/svg+xml',
            'webp': 'image/webp',
        }
        media_type = media_type_map.get(ext, f'image/{ext}')
        
        img = epub.EpubItem(
            uid=f'image_{uuid.uuid4().hex}',
            file_name=f'images/{image_name}',
            media_type=media_type,
            content=image_content
        )
        self.book.add_item(img)
        self.images.append(img)
        logger.info(f"添加图片: {image_name}")
    
    def generate_toc(self):
        self.book.toc = tuple(self.toc)
        self.book.add_item(epub.EpubNcx())
        self.book.add_item(epub.EpubNav())
        self.book.spine = self.spine
        logger.info("生成目录完成")
    
    def save(self, output_path):
        try:
            logger.info(f"保存EPUB前检查: spine长度={len(self.spine)}, toc长度={len(self.toc)}")
            
            if not self.spine or len(self.spine) <= 1:
                logger.error("无法保存EPUB: 文档为空（没有章节）")
                return False
            
            self.generate_toc()
            
            book_items = [item.get_name() for item in self.book.get_items()]
            logger.info(f"book中的项目数量: {len(book_items)}")
            
            spine_items = [str(item) for item in self.book.spine]
            logger.info(f"spine项目数量: {len(spine_items)}")
            
            import ebooklib
            docs = [item for item in self.book.get_items_of_type(ebooklib.ITEM_DOCUMENT) if not isinstance(item, ebooklib.epub.EpubNav)]
            logger.info(f"文档类型项目数量: {len(docs)}")
            
            for i, doc in enumerate(docs):
                content = doc.get_body_content()
                if not content or not content.strip():
                    logger.error(f"文档 {i} ({doc.get_name()}) body内容为空")
                else:
                    logger.debug(f"文档 {i} ({doc.get_name()}) body内容长度: {len(content)}")
            
            epub.write_epub(output_path, self.book, {})
            logger.info(f"EPUB文件已保存: {output_path}")
            return True
        except Exception as e:
            logger.error(f"保存EPUB失败: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
