import os
import tempfile
from src.utils.logger import setup_logger
from src.utils.exceptions import OCRError

logger = setup_logger("ocr_engine")


class OCREngine:
    def __init__(self, language="eng", dpi=300):
        self.language = language
        self.dpi = dpi
        self._tesseract_available = None

    @property
    def available(self):
        if self._tesseract_available is None:
            try:
                import pytesseract
                pytesseract.get_tesseract_version()
                self._tesseract_available = True
            except Exception:
                self._tesseract_available = False
        return self._tesseract_available

    def recognize_page(self, page, page_num=0):
        if not self.available:
            raise OCRError("Tesseract OCR 未安装或不可用")

        try:
            import pytesseract
            from PIL import Image
            import fitz

            pix = page.get_pixmap(dpi=self.dpi)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)

            text = pytesseract.image_to_string(img, lang=self.language)

            data = pytesseract.image_to_data(img, lang=self.language, output_type=pytesseract.Output.DICT)

            blocks = []
            for i in range(len(data["text"])):
                if data["text"][i].strip():
                    blocks.append({
                        "type": "text",
                        "text": data["text"][i],
                        "font_size": data["height"][i],
                        "bold": data["conf"][i] > 60,
                        "page": page_num,
                        "x0": data["left"][i],
                        "y0": data["top"][i],
                        "x1": data["left"][i] + data["width"][i],
                        "y1": data["top"][i] + data["height"][i],
                    })

            return {"text": text, "blocks": blocks, "confidence": sum(data["conf"]) / max(len(data["conf"]), 1)}

        except ImportError:
            raise OCRError("pytesseract 未安装，请运行: pip install pytesseract")
        except Exception as e:
            raise OCRError(f"OCR识别失败: {str(e)}")

    def recognize_document(self, doc, pages=None):
        if not self.available:
            raise OCRError("Tesseract OCR 未安装或不可用")

        import fitz

        all_text = []
        all_blocks = []

        if pages is None:
            pages = range(len(doc))

        for page_num in pages:
            page = doc[page_num]
            result = self.recognize_page(page, page_num)
            all_text.append(result["text"])
            all_blocks.extend(result["blocks"])
            logger.info(f"OCR页面 {page_num + 1}/{len(doc)}")

        return {"text": "\n".join(all_text), "blocks": all_blocks}