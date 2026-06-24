import argparse
import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from src.parser.pdf_extractor import PDFExtractor
from src.converter.epub_builder import EPUBBuilder
from src.converter.txt_builder import TXTBuilder
from src.task.task_manager import TaskManager
from src.utils.config import load_config, get_config
from src.utils.logger import setup_logger
import hashlib

logger = setup_logger("cli")


def cmd_convert(args):
    pdf_path = args.input
    output_path = args.output
    fmt = args.format

    if not os.path.exists(pdf_path):
        logger.error(f"PDF文件不存在: {pdf_path}")
        sys.exit(1)

    if not output_path:
        base = os.path.splitext(os.path.basename(pdf_path))[0]
        output_path = f"{base}.{fmt}"

    logger.info(f"转换: {pdf_path} -> {output_path} (格式: {fmt})")

    extractor = PDFExtractor(pdf_path)
    chapters = extractor.detect_chapters()

    if not chapters or not extractor.has_content():
        logger.error("PDF无法提取内容")
        extractor.close()
        sys.exit(1)

    if fmt == "epub":
        builder = EPUBBuilder()
        builder.set_metadata(os.path.splitext(os.path.basename(pdf_path))[0])
        seen_hashes = {}
        img_counter = 0

        valid_count = 0
        for i, ch in enumerate(chapters):
            has_text = False
            for block in ch.get("content", []):
                if isinstance(block, dict):
                    if block.get("type") == "text" and block.get("text", "").strip():
                        has_text = True
                    elif block.get("type") == "image":
                        img_bytes = block.get("image_bytes", b"")
                        img_hash = hashlib.md5(img_bytes).hexdigest()[:12]
                        if img_hash in seen_hashes:
                            img_name = seen_hashes[img_hash]
                        else:
                            img_counter += 1
                            w = block.get("image_width", 0)
                            h = block.get("image_height", 0)
                            ext = block.get("image_ext", "png")
                            img_name = f"image_{img_counter:04d}_{w}x{h}.{ext}"
                            builder.add_image_bytes(img_bytes, img_name)
                            seen_hashes[img_hash] = img_name
                        block["image_name"] = img_name
                        has_text = True

            if has_text:
                valid_count += 1
                builder.add_chapter(ch["title"], ch["content"], valid_count)

        logger.info(f"章节: {valid_count}, 图片: {len(seen_hashes)}")
        success = builder.save(output_path)

    elif fmt == "txt":
        builder = TXTBuilder()
        builder.set_metadata(os.path.splitext(os.path.basename(pdf_path))[0])
        for ch in chapters:
            builder.add_chapter(ch["title"], ch["content"])
        success = builder.save(output_path)

    else:
        logger.error(f"不支持的格式: {fmt}")
        extractor.close()
        sys.exit(1)

    extractor.close()

    if success:
        size = os.path.getsize(output_path) if os.path.exists(output_path) else 0
        logger.info(f"转换成功: {output_path} ({size:,} bytes)")
    else:
        logger.error("转换失败")
        sys.exit(1)


def cmd_batch(args):
    input_dir = args.input_dir
    output_dir = args.output_dir or input_dir
    fmt = args.format
    workers = args.workers or get_config("conversion.max_workers", 4)

    if not os.path.isdir(input_dir):
        logger.error(f"目录不存在: {input_dir}")
        sys.exit(1)

    os.makedirs(output_dir, exist_ok=True)

    pdf_files = [f for f in os.listdir(input_dir) if f.lower().endswith(".pdf")]
    if not pdf_files:
        logger.error(f"目录中没有PDF文件: {input_dir}")
        sys.exit(1)

    logger.info(f"批量转换: {len(pdf_files)} 个文件, {workers} 线程")

    manager = TaskManager(max_workers=workers)
    for pdf_file in pdf_files:
        pdf_path = os.path.join(input_dir, pdf_file)
        base = os.path.splitext(pdf_file)[0]
        output_path = os.path.join(output_dir, f"{base}.{fmt}")
        manager.add_task(pdf_path, output_path)

    manager.convert_all()

    while manager.has_running():
        time.sleep(0.5)

    summary = manager.get_summary()
    completed = sum(1 for t in summary if t["status"] == "completed")
    failed = sum(1 for t in summary if t["status"] == "failed")

    logger.info(f"批量转换完成: 成功 {completed}, 失败 {failed}")


def main():
    parser = argparse.ArgumentParser(
        prog="pdf2epub",
        description="PDF转EPUB/TXT工具"
    )
    subparsers = parser.add_subparsers(dest="command", help="可用命令")

    convert_parser = subparsers.add_parser("convert", help="转换单个PDF文件")
    convert_parser.add_argument("-i", "--input", required=True, help="输入PDF文件路径")
    convert_parser.add_argument("-o", "--output", help="输出文件路径")
    convert_parser.add_argument("-f", "--format", default="epub", choices=["epub", "txt"], help="输出格式 (默认: epub)")

    batch_parser = subparsers.add_parser("batch", help="批量转换PDF文件")
    batch_parser.add_argument("-i", "--input-dir", required=True, help="输入目录")
    batch_parser.add_argument("-o", "--output-dir", help="输出目录")
    batch_parser.add_argument("-f", "--format", default="epub", choices=["epub", "txt"], help="输出格式")
    batch_parser.add_argument("-w", "--workers", type=int, help="并行线程数")

    args = parser.parse_args()

    if args.command == "convert":
        cmd_convert(args)
    elif args.command == "batch":
        cmd_batch(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()