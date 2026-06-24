import os
import hashlib
import concurrent.futures
from threading import Lock
from src.parser.pdf_extractor import PDFExtractor
from src.converter.epub_builder import EPUBBuilder
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class ConvertTask:
    def __init__(self, pdf_path, output_path):
        self.pdf_path = pdf_path
        self.output_path = output_path
        self.status = 'pending'
        self.progress = 0
        self.error = None
        self.chapters = []
        self.image_count = 0
    
    def __repr__(self):
        return f"ConvertTask({os.path.basename(self.pdf_path)}, {self.status})"

class TaskManager:
    def __init__(self, max_workers=4):
        self.tasks = []
        self.max_workers = max_workers
        self.executor = None
        self.callback = None
        self.lock = Lock()
    
    def add_task(self, pdf_path, output_path):
        task = ConvertTask(pdf_path, output_path)
        self.tasks.append(task)
        logger.info(f"添加任务: {os.path.basename(pdf_path)}")
        return task
    
    def add_tasks(self, pdf_paths, output_dir):
        tasks = []
        for pdf_path in pdf_paths:
            filename = os.path.splitext(os.path.basename(pdf_path))[0] + '.epub'
            output_path = os.path.join(output_dir, filename)
            task = self.add_task(pdf_path, output_path)
            tasks.append(task)
        return tasks
    
    def convert_single(self, task):
        try:
            with self.lock:
                task.status = 'running'
            
            logger.info(f"开始转换: {os.path.basename(task.pdf_path)}")
            
            extractor = PDFExtractor(task.pdf_path)
            
            with self.lock:
                task.progress = 15
            
            chapters = extractor.detect_chapters()
            task.chapters = chapters
            
            logger.info(f"检测到章节数: {len(chapters)}")
            
            with self.lock:
                task.progress = 30
            
            has_content = extractor.has_content()
            logger.info(f"是否有内容: {has_content}")
            
            if not chapters or not has_content:
                extractor.close()
                with self.lock:
                    task.status = 'failed'
                    task.progress = 100
                    task.error = "PDF文件为空或无法提取内容"
                logger.error(f"任务失败 {os.path.basename(task.pdf_path)}: PDF文件为空或无法提取内容")
                if self.callback:
                    self.callback(self.get_summary())
                return
            
            with self.lock:
                task.progress = 45
            
            epub_builder = EPUBBuilder()
            pdf_name = os.path.splitext(os.path.basename(task.pdf_path))[0]
            epub_builder.set_metadata(pdf_name)
            
            with self.lock:
                task.progress = 60
            
            valid_chapters = []
            added_count = 0
            seen_image_hashes = {}
            img_counter = 0
            
            for i, chapter in enumerate(chapters):
                chapter_content = chapter.get("content", [])
                has_text = False
                
                if isinstance(chapter_content, list):
                    for block in chapter_content:
                        if isinstance(block, dict):
                            if block.get("type") == "text" and block.get("text", "").strip():
                                has_text = True
                            elif block.get("type") == "image":
                                img_bytes = block.get("image_bytes", b"")
                                img_hash = hashlib.md5(img_bytes).hexdigest()[:12]
                                
                                if img_hash in seen_image_hashes:
                                    img_name = seen_image_hashes[img_hash]
                                else:
                                    img_counter += 1
                                    ext = block.get("image_ext", "png")
                                    width = block.get("image_width", 0)
                                    height = block.get("image_height", 0)
                                    img_name = f"image_{img_counter:04d}_{width}x{height}.{ext}"
                                    epub_builder.add_image_bytes(img_bytes, img_name)
                                    seen_image_hashes[img_hash] = img_name
                                
                                block["image_name"] = img_name
                                has_text = True
                        elif isinstance(block, str) and block.strip():
                            has_text = True
                elif isinstance(chapter_content, str) and chapter_content.strip():
                    has_text = True
                
                if has_text:
                    valid_chapters.append(chapter)
                    result = epub_builder.add_chapter(chapter["title"], chapter["content"], len(valid_chapters))
                    if result:
                        added_count += 1
                    with self.lock:
                        task.progress = 60 + int((added_count + 1) / max(len(chapters), 1) * 30)
            
            task.image_count = len(seen_image_hashes)
            logger.info(f"有效章节数: {len(valid_chapters)}, 图片数: {task.image_count}")
            
            if not valid_chapters:
                extractor.close()
                with self.lock:
                    task.status = 'failed'
                    task.progress = 100
                    task.error = "PDF文件无法提取有效内容"
                logger.error(f"任务失败 {os.path.basename(task.pdf_path)}: PDF文件无法提取有效内容")
                if self.callback:
                    self.callback(self.get_summary())
                return
            
            with self.lock:
                task.progress = 95
            
            success = epub_builder.save(task.output_path)
            
            with self.lock:
                task.progress = 100
            
            if success:
                task.status = 'completed'
                logger.info(f"任务完成: {os.path.basename(task.pdf_path)}")
            else:
                task.status = 'failed'
                task.error = "保存EPUB失败"
            
            extractor.close()
            
        except Exception as e:
            with self.lock:
                task.status = 'failed'
                task.error = str(e)
            logger.error(f"任务失败 {os.path.basename(task.pdf_path)}: {str(e)}")
        
        if self.callback:
            self.callback(self.get_summary())
    
    def get_summary(self):
        with self.lock:
            total = len(self.tasks)
            completed = sum(1 for t in self.tasks if t.status == 'completed')
            failed = sum(1 for t in self.tasks if t.status == 'failed')
            running = sum(1 for t in self.tasks if t.status == 'running')
            pending = sum(1 for t in self.tasks if t.status == 'pending')
            
            avg_progress = 0
            if total > 0:
                avg_progress = sum(t.progress for t in self.tasks) / total
            
            return {
                'total': total,
                'completed': completed,
                'failed': failed,
                'running': running,
                'pending': pending,
                'avg_progress': avg_progress,
                'tasks': self.tasks.copy()
            }
    
    def execute(self, callback=None):
        self.callback = callback

        if not self.tasks:
            logger.warning("没有任务需要执行")
            return

        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers)

        for task in self.tasks:
            future = self.executor.submit(self.convert_single, task)
            logger.info(f"提交任务到线程池: {os.path.basename(task.pdf_path)} (future={id(future)})")

        self.executor.shutdown(wait=False)
        logger.info(f"任务执行开始: 共 {len(self.tasks)} 个任务")
    
    def wait_completion(self):
        if self.executor:
            self.executor.shutdown(wait=True)
    
    def cancel_all(self):
        if self.executor:
            self.executor.shutdown(wait=False)
        with self.lock:
            for task in self.tasks:
                if task.status == 'running':
                    task.status = 'cancelled'
        logger.info("所有任务已取消")
    
    def clear_tasks(self):
        with self.lock:
            self.tasks = []
        logger.info("任务列表已清空")
