import os
import sys
import tempfile
import zipfile
import threading
import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.task.task_manager import TaskManager
from src.utils.logger import setup_logger

logger = setup_logger(__name__)

class MainWindow:
    def __init__(self, root):
        self.root = root
        self.root.title('PDF转EPUB工具')
        self.root.geometry('1000x700')
        
        self.pdf_paths = []
        self.output_dir = None
        self.task_manager = None
        self.overwrite_mode = 'ask'
        
        self.setup_styles()
        self.create_widgets()
    
    def setup_styles(self):
        style = ttk.Style()
        
        style.theme_use('clam')
        
        style.configure('Main.TFrame', background='#f5f7fa')
        style.configure('Sidebar.TFrame', background='#ffffff')
        style.configure('Card.TFrame', background='#ffffff', relief='solid', borderwidth=1)
        
        style.configure('Title.TLabel', font=('Microsoft YaHei', 14, 'bold'), foreground='#2c3e50')
        style.configure('Header.TLabel', font=('Microsoft YaHei', 11, 'bold'), foreground='#34495e')
        style.configure('Normal.TLabel', font=('Microsoft YaHei', 10), foreground='#5d6d7e')
        style.configure('Status.TLabel', font=('Microsoft YaHei', 10), foreground='#27ae60')
        style.configure('Warning.TLabel', font=('Microsoft YaHei', 10), foreground='#f39c12')
        style.configure('Error.TLabel', font=('Microsoft YaHei', 10), foreground='#e74c3c')
        
        style.configure('Primary.TButton', 
                       background='#3498db', 
                       foreground='white',
                       font=('Microsoft YaHei', 10, 'bold'),
                       padding=6)
        style.map('Primary.TButton',
                  background=[('active', '#2980b9'), ('disabled', '#bdc3c7')],
                  foreground=[('disabled', '#7f8c8d')])
        
        style.configure('Success.TButton', 
                       background='#27ae60', 
                       foreground='white',
                       font=('Microsoft YaHei', 10, 'bold'),
                       padding=6)
        style.map('Success.TButton',
                  background=[('active', '#2ecc71'), ('disabled', '#bdc3c7')],
                  foreground=[('disabled', '#7f8c8d')])
        
        style.configure('Danger.TButton', 
                       background='#e74c3c', 
                       foreground='white',
                       font=('Microsoft YaHei', 10, 'bold'),
                       padding=6)
        style.map('Danger.TButton',
                  background=[('active', '#c0392b'), ('disabled', '#bdc3c7')],
                  foreground=[('disabled', '#7f8c8d')])
        
        style.configure('Info.TButton', 
                       background='#17a2b8', 
                       foreground='white',
                       font=('Microsoft YaHei', 10, 'bold'),
                       padding=6)
        style.map('Info.TButton',
                  background=[('active', '#138496'), ('disabled', '#bdc3c7')],
                  foreground=[('disabled', '#7f8c8d')])
        
        style.configure('Progress.Horizontal.TProgressbar',
                       background='#ecf0f1',
                       troughcolor='#ecf0f1',
                       bordercolor='#bdc3c7',
                       lightcolor='#3498db',
                       darkcolor='#2980b9')
        
        style.configure('Treeview',
                       background='#ffffff',
                       foreground='#2c3e50',
                       font=('Microsoft YaHei', 10))
        style.configure('Treeview.Heading',
                       background='#3498db',
                       foreground='white',
                       font=('Microsoft YaHei', 10, 'bold'))
        style.map('Treeview',
                  background=[('selected', '#3498db')],
                  foreground=[('selected', 'white')])
        
        style.configure('TLabelframe',
                       background='#ffffff',
                       labelcolor='#2c3e50',
                       font=('Microsoft YaHei', 11, 'bold'))
        style.configure('TLabelframe.Label',
                       font=('Microsoft YaHei', 11, 'bold'),
                       foreground='#2c3e50')
        
        self.root.configure(bg='#f5f7fa')
    
    def create_widgets(self):
        main_frame = ttk.Frame(self.root, style='Main.TFrame', padding=15)
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        header_frame = ttk.Frame(main_frame, style='Sidebar.TFrame')
        header_frame.pack(fill=tk.X, pady=(0, 10))
        
        title_label = ttk.Label(header_frame, text='📚 PDF转EPUB工具', style='Title.TLabel')
        title_label.pack(anchor=tk.W)
        
        subtitle_label = ttk.Label(header_frame, text='快速、高效地将PDF文件转换为EPUB格式', style='Normal.TLabel')
        subtitle_label.pack(anchor=tk.W, pady=(2, 0))
        
        content_frame = ttk.Frame(main_frame, style='Main.TFrame')
        content_frame.pack(fill=tk.BOTH, expand=True)
        
        left_frame = ttk.Frame(content_frame, width=320, style='Sidebar.TFrame')
        left_frame.pack(side=tk.LEFT, fill=tk.Y, padx=(0, 10))
        left_frame.pack_propagate(False)
        
        right_frame = ttk.Frame(content_frame, style='Main.TFrame')
        right_frame.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True)
        
        upload_frame = ttk.LabelFrame(left_frame, text='上传PDF文件', padding=10)
        upload_frame.pack(fill=tk.X, pady=(0, 10))
        
        btn_frame = ttk.Frame(upload_frame)
        btn_frame.pack(fill=tk.X)
        
        self.upload_single_btn = ttk.Button(btn_frame, text='📄 选择单个', command=self.upload_single_pdf, style='Primary.TButton')
        self.upload_single_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        self.upload_batch_btn = ttk.Button(btn_frame, text='📁 选择多个', command=self.upload_batch_pdf, style='Info.TButton')
        self.upload_batch_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True)
        
        self.output_btn = ttk.Button(upload_frame, text='📂 选择输出目录', command=self.select_output_dir, style='Primary.TButton')
        self.output_btn.pack(fill=tk.X, pady=(5, 0))
        
        self.output_label = ttk.Label(upload_frame, text='未选择输出目录', style='Normal.TLabel', wraplength=280)
        self.output_label.pack(pady=(5, 0))
        
        self.files_list = tk.Listbox(upload_frame, height=6, 
                                     bg='#fafafa', 
                                     fg='#2c3e50', 
                                     font=('Microsoft YaHei', 9),
                                     bd=1,
                                     relief=tk.SUNKEN)
        self.files_list.pack(fill=tk.X, pady=(8, 0))
        
        list_btn_frame = ttk.Frame(upload_frame)
        list_btn_frame.pack(fill=tk.X, pady=(5, 0))
        
        self.remove_btn = ttk.Button(list_btn_frame, text='移除选中', command=self.remove_selected, style='Info.TButton')
        self.remove_btn.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 3))
        
        self.clear_btn = ttk.Button(list_btn_frame, text='清空列表', command=self.clear_files, style='Danger.TButton')
        self.clear_btn.pack(side=tk.RIGHT, fill=tk.X, expand=True, padx=(3, 0))
        
        mode_frame = ttk.LabelFrame(left_frame, text='覆盖模式', padding=10)
        mode_frame.pack(fill=tk.X, pady=(0, 10))
        
        self.mode_var = tk.StringVar(value='ask')
        
        ask_radio = ttk.Radiobutton(mode_frame, text='询问替换', variable=self.mode_var, value='ask')
        ask_radio.pack(anchor=tk.W)
        
        overwrite_radio = ttk.Radiobutton(mode_frame, text='直接覆盖', variable=self.mode_var, value='overwrite')
        overwrite_radio.pack(anchor=tk.W)
        
        rename_radio = ttk.Radiobutton(mode_frame, text='自动重命名', variable=self.mode_var, value='rename')
        rename_radio.pack(anchor=tk.W)
        
        convert_frame = ttk.LabelFrame(left_frame, text='转换控制', padding=10)
        convert_frame.pack(fill=tk.X)
        
        self.convert_btn = ttk.Button(convert_frame, text='🚀 开始转换', command=self.start_convert, state=tk.DISABLED, style='Success.TButton')
        self.convert_btn.pack(fill=tk.X)
        
        self.cancel_btn = ttk.Button(convert_frame, text='⏹ 取消转换', command=self.cancel_convert, state=tk.DISABLED, style='Danger.TButton')
        self.cancel_btn.pack(fill=tk.X, pady=(5, 0))
        
        self.progress_bar = ttk.Progressbar(convert_frame, orient=tk.HORIZONTAL, length=280, mode='determinate', style='Progress.Horizontal.TProgressbar')
        self.progress_bar.pack(fill=tk.X, pady=(10, 0))
        self.progress_bar['value'] = 0
        
        self.status_label = ttk.Label(convert_frame, text='状态: 就绪', style='Status.TLabel')
        self.status_label.pack(pady=(8, 0))
        
        self.stats_label = ttk.Label(convert_frame, text='', style='Normal.TLabel')
        self.stats_label.pack(pady=(2, 0))
        
        right_notebook = ttk.Notebook(right_frame)
        right_notebook.pack(fill=tk.BOTH, expand=True)
        
        info_tab = ttk.Frame(right_notebook, style='Sidebar.TFrame')
        right_notebook.add(info_tab, text='📋 转换信息')
        
        self.info_text = scrolledtext.ScrolledText(info_tab, 
                                                   wrap=tk.WORD,
                                                   bg='#fafafa',
                                                   fg='#2c3e50',
                                                   font=('Microsoft YaHei', 10),
                                                   bd=1,
                                                   relief=tk.SUNKEN)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        self.info_text.insert(tk.END, '欢迎使用 PDF转EPUB工具\n\n')
        self.info_text.insert(tk.END, '✨ 功能特点：\n')
        self.info_text.insert(tk.END, '  • 支持PDF章节智能提取\n')
        self.info_text.insert(tk.END, '  • 自动生成可跳转EPUB目录\n')
        self.info_text.insert(tk.END, '  • 图片正确转换与显示\n')
        self.info_text.insert(tk.END, '  • 排版样式精确保留\n')
        self.info_text.insert(tk.END, '  • 多文件批量并行转换\n')
        self.info_text.insert(tk.END, '  • EPUB文件预览功能\n\n')
        self.info_text.insert(tk.END, '📖 使用说明：\n')
        self.info_text.insert(tk.END, '  1. 点击"选择PDF文件"上传一个或多个PDF\n')
        self.info_text.insert(tk.END, '  2. 选择输出目录\n')
        self.info_text.insert(tk.END, '  3. 设置覆盖模式\n')
        self.info_text.insert(tk.END, '  4. 点击"开始转换"按钮\n')
        self.info_text.insert(tk.END, '  5. 在任务列表查看进度\n')
        self.info_text.config(state=tk.DISABLED)
        
        preview_frame = ttk.Frame(right_notebook, style='Sidebar.TFrame')
        right_notebook.add(preview_frame, text='👁 预览')
        
        preview_inner = ttk.Frame(preview_frame)
        preview_inner.pack(fill=tk.BOTH, expand=True)
        
        preview_splitter = ttk.PanedWindow(preview_inner, orient=tk.HORIZONTAL)
        preview_splitter.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.chapter_list_frame = ttk.Frame(preview_splitter, width=200)
        preview_splitter.add(self.chapter_list_frame, weight=1)
        
        self.chapter_list = ttk.Treeview(self.chapter_list_frame, show='tree')
        self.chapter_list.pack(fill=tk.BOTH, expand=True)
        self.chapter_list.bind('<<TreeviewSelect>>', self.on_chapter_select)
        
        self.content_frame = ttk.Frame(preview_splitter)
        preview_splitter.add(self.content_frame, weight=4)
        
        self.content_text = scrolledtext.ScrolledText(self.content_frame,
                                                     wrap=tk.WORD,
                                                     bg='#ffffff',
                                                     fg='#2c3e50',
                                                     font=('Microsoft YaHei', 11),
                                                     bd=1,
                                                     relief=tk.SUNKEN)
        self.content_text.pack(fill=tk.BOTH, expand=True)
        self.content_text.config(state=tk.DISABLED)
        
        self.last_epub_path = None
        self.epub_chapters = []
        
        self.preview_btn = ttk.Button(preview_inner, text='📖 加载EPUB', command=self.preview_epub, state=tk.DISABLED, style='Primary.TButton')
        self.preview_btn.pack(side=tk.BOTTOM, fill=tk.X, padx=10, pady=5)
        
        preview_tip = ttk.Label(preview_inner, text='提示：EPUB文件生成后，点击加载按钮查看内容', style='Normal.TLabel')
        preview_tip.pack(side=tk.BOTTOM, pady=(0, 5))
        
        task_list_frame = ttk.Frame(right_notebook, style='Sidebar.TFrame')
        right_notebook.add(task_list_frame, text='📊 任务列表')
        
        self.task_tree = ttk.Treeview(task_list_frame, columns=('文件名', '状态', '进度', '章节', '图片'))
        self.task_tree.heading('#0', text='序号')
        self.task_tree.heading('文件名', text='文件名')
        self.task_tree.heading('状态', text='状态')
        self.task_tree.heading('进度', text='进度')
        self.task_tree.heading('章节', text='章节数')
        self.task_tree.heading('图片', text='图片数')
        self.task_tree.column('#0', width=50, anchor=tk.CENTER)
        self.task_tree.column('文件名', width=200, anchor=tk.W)
        self.task_tree.column('状态', width=80, anchor=tk.CENTER)
        self.task_tree.column('进度', width=80, anchor=tk.CENTER)
        self.task_tree.column('章节', width=60, anchor=tk.CENTER)
        self.task_tree.column('图片', width=60, anchor=tk.CENTER)
        self.task_tree.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        self.task_tree.tag_configure('completed', foreground='#27ae60')
        self.task_tree.tag_configure('failed', foreground='#e74c3c')
        self.task_tree.tag_configure('running', foreground='#3498db')
        self.task_tree.tag_configure('pending', foreground='#95a5a6')
    
    def add_info(self, text):
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, text + '\n')
        self.info_text.see(tk.END)
        self.info_text.config(state=tk.DISABLED)
    
    def upload_single_pdf(self):
        file_path = filedialog.askopenfilename(
            title='选择PDF文件',
            filetypes=[('PDF文件', '*.pdf')]
        )
        if file_path and file_path not in self.pdf_paths:
            self.pdf_paths.append(file_path)
            self.update_files_list()
            self.check_convert_ready()
    
    def upload_batch_pdf(self):
        file_paths = filedialog.askopenfilenames(
            title='选择多个PDF文件',
            filetypes=[('PDF文件', '*.pdf')]
        )
        for file_path in file_paths:
            if file_path and file_path not in self.pdf_paths:
                self.pdf_paths.append(file_path)
        self.update_files_list()
        self.check_convert_ready()
    
    def select_output_dir(self):
        output_dir = filedialog.askdirectory(title='选择输出目录')
        if output_dir:
            self.output_dir = output_dir
            self.output_label.config(text=f'输出目录: {os.path.basename(output_dir)}')
            self.check_convert_ready()
    
    def update_files_list(self):
        self.files_list.delete(0, tk.END)
        for pdf_path in self.pdf_paths:
            self.files_list.insert(tk.END, os.path.basename(pdf_path))
    
    def remove_selected(self):
        selected = self.files_list.curselection()
        for idx in reversed(selected):
            del self.pdf_paths[idx]
        self.update_files_list()
        self.check_convert_ready()
    
    def clear_files(self):
        self.pdf_paths = []
        self.update_files_list()
        self.check_convert_ready()
    
    def check_convert_ready(self):
        ready = len(self.pdf_paths) > 0 and self.output_dir is not None
        self.convert_btn.config(state=tk.NORMAL if ready else tk.DISABLED)
    
    def check_existing_files(self):
        existing_files = []
        for pdf_path in self.pdf_paths:
            filename = os.path.splitext(os.path.basename(pdf_path))[0] + '.epub'
            output_path = os.path.join(self.output_dir, filename)
            if os.path.exists(output_path):
                existing_files.append(filename)
        
        if not existing_files:
            return True
        
        mode = self.mode_var.get()
        
        if mode == 'overwrite':
            self.add_info(f"检测到 {len(existing_files)} 个同名文件，将覆盖")
            return True
        
        if mode == 'rename':
            self.add_info(f"检测到 {len(existing_files)} 个同名文件，将自动重命名")
            return True
        
        msg = f"检测到以下文件已存在：\n\n{chr(10).join(existing_files)}\n\n请选择处理方式："
        result = messagebox.askyesnocancel('文件已存在', msg)
        
        if result is True:
            self.add_info("用户选择覆盖现有文件")
            return True
        elif result is False:
            new_names = []
            for pdf_path in self.pdf_paths:
                filename = os.path.splitext(os.path.basename(pdf_path))[0] + '.epub'
                output_path = os.path.join(self.output_dir, filename)
                if os.path.exists(output_path):
                    base, ext = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(os.path.join(self.output_dir, f"{base}_{counter}{ext}")):
                        counter += 1
                    new_names.append(f"{base}_{counter}{ext}")
                else:
                    new_names.append(filename)
            self.add_info(f"自动重命名 {len([n for n in new_names if '_' in n])} 个文件")
            return True
        else:
            return False
    
    def start_convert(self):
        if not self.pdf_paths or not self.output_dir:
            return
        
        if not self.check_existing_files():
            return
        
        self.task_manager = TaskManager(max_workers=4)
        self.task_manager.add_tasks(self.pdf_paths, self.output_dir)
        
        self.convert_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.upload_single_btn.config(state=tk.DISABLED)
        self.upload_batch_btn.config(state=tk.DISABLED)
        self.output_btn.config(state=tk.DISABLED)
        
        self.add_info(f"🚀 开始转换 {len(self.pdf_paths)} 个文件...")
        self.status_label.config(text='状态: 转换中')
        self.status_label.config(style='Warning.TLabel')
        
        self.update_task_tree()
        
        self.task_manager.execute(callback=self.update_progress)
        
        self.monitor_thread = threading.Thread(target=self.monitor_tasks)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()
    
    def monitor_tasks(self):
        while True:
            summary = self.task_manager.get_summary()
            if summary['running'] == 0:
                self.finalize_convert()
                break
            self.root.after(100, self.update_progress, summary)
            import time
            time.sleep(0.5)
    
    def update_progress(self, summary):
        self.progress_bar['value'] = summary['avg_progress']
        
        status_text = f"状态: 运行中 ({summary['running']})"
        if summary['running'] == 0:
            status_text = f"状态: 完成 (成功:{summary['completed']}, 失败:{summary['failed']})"
        
        if summary['failed'] > 0:
            self.status_label.config(style='Error.TLabel')
        elif summary['running'] > 0:
            self.status_label.config(style='Warning.TLabel')
        else:
            self.status_label.config(style='Status.TLabel')
        
        self.status_label.config(text=status_text)
        
        stats_text = f"总计: {summary['total']} | 完成: {summary['completed']} | 失败: {summary['failed']} | 运行: {summary['running']}"
        self.stats_label.config(text=stats_text)
        
        self.update_task_tree()
    
    def update_task_tree(self):
        if not self.task_manager:
            return
        
        for item in self.task_tree.get_children():
            self.task_tree.delete(item)
        
        for i, task in enumerate(self.task_manager.tasks):
            status_text = {
                'pending': '等待',
                'running': '运行中',
                'completed': '完成',
                'failed': '失败',
                'cancelled': '已取消'
            }.get(task.status, task.status)
            
            tag = task.status
            
            chapters = len(task.chapters) if task.chapters else '-'
            images = task.image_count if task.image_count > 0 else '-'
            
            self.task_tree.insert(
                '', tk.END, iid=str(i), text=str(i+1),
                values=(os.path.basename(task.pdf_path), status_text, f"{task.progress}%", chapters, images),
                tags=(tag,)
            )
    
    def finalize_convert(self):
        summary = self.task_manager.get_summary()
        
        if summary['failed'] > 0:
            self.add_info(f"⚠️ 转换完成! 成功: {summary['completed']}, 失败: {summary['failed']}")
        else:
            self.add_info(f"✅ 转换完成! 成功: {summary['completed']}")
        
        if summary['completed'] > 0:
            last_completed = [t for t in summary['tasks'] if t.status == 'completed'][-1]
            self.last_epub_path = last_completed.output_path
            self.preview_btn.config(state=tk.NORMAL)
        
        self.convert_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.upload_single_btn.config(state=tk.NORMAL)
        self.upload_batch_btn.config(state=tk.NORMAL)
        self.output_btn.config(state=tk.NORMAL)
        
        self.status_label.config(text=f'状态: 完成')
        self.status_label.config(style='Status.TLabel')
    
    def cancel_convert(self):
        if self.task_manager:
            self.task_manager.cancel_all()
            self.add_info("⏹ 转换已取消")
            self.status_label.config(text='状态: 已取消')
            self.status_label.config(style='Warning.TLabel')
            self.convert_btn.config(state=tk.NORMAL)
            self.cancel_btn.config(state=tk.DISABLED)
            self.upload_single_btn.config(state=tk.NORMAL)
            self.upload_batch_btn.config(state=tk.NORMAL)
            self.output_btn.config(state=tk.NORMAL)
    
    def preview_epub(self):
        if not self.last_epub_path:
            return
        
        try:
            self.preview_btn.config(state=tk.DISABLED, text='⏳ 加载中...')
            self.root.update()
            
            self.epub_chapters = []
            self._epub_temp_dir = tempfile.mkdtemp(prefix='epub_preview_')
            self._epub_images = {}
            
            with zipfile.ZipFile(self.last_epub_path, 'r') as zf:
                files = zf.namelist()
                
                content_opf = [f for f in files if f.endswith('.opf')][0]
                opf_base = os.path.dirname(content_opf)
                
                with zf.open(content_opf) as f:
                    opf_content = f.read().decode('utf-8')
                
                from xml.etree import ElementTree as ET
                import re
                tree = ET.ElementTree(ET.fromstring(opf_content))
                ns = {'opf': 'http://www.idpf.org/2007/opf'}
                manifest = tree.find('.//opf:manifest', ns)
                spine = tree.find('.//opf:spine', ns)
                
                manifest_map = {}
                for item in manifest.findall('opf:item', ns):
                    item_id = item.get('id')
                    href = item.get('href')
                    media_type = item.get('media-type', '')
                    manifest_map[item_id] = {'href': href, 'media_type': media_type}
                
                for item in manifest.findall('opf:item', ns):
                    href = item.get('href')
                    media_type = item.get('media-type', '')
                    if 'image' in media_type:
                        full_path = self._resolve_epub_path(href, opf_base, files)
                        if full_path:
                            try:
                                img_data = zf.read(full_path)
                                img_path = os.path.join(self._epub_temp_dir, os.path.basename(href))
                                with open(img_path, 'wb') as imgf:
                                    imgf.write(img_data)
                                self._epub_images[href] = img_path
                                self._epub_images[os.path.basename(href)] = img_path
                            except Exception as e:
                                logger.warning(f"提取图片失败: {href}, {e}")
                
                ordered_hrefs = []
                if spine is not None:
                    for itemref in spine.findall('opf:itemref', ns):
                        ref_id = itemref.get('idref')
                        if ref_id in manifest_map:
                            mi = manifest_map[ref_id]
                            if mi['href'].endswith('.xhtml') or mi['href'].endswith('.html'):
                                ordered_hrefs.append(mi['href'])
                
                if not ordered_hrefs:
                    for item in manifest.findall('opf:item', ns):
                        href = item.get('href')
                        if href.endswith('.xhtml') or href.endswith('.html'):
                            if href not in ordered_hrefs:
                                ordered_hrefs.append(href)
                
                for href in ordered_hrefs:
                    full_path = self._resolve_epub_path(href, opf_base, files)
                    if not full_path:
                        logger.warning(f"文件不存在: {href}")
                        continue
                    
                    with zf.open(full_path) as f:
                        raw_content = f.read().decode('utf-8')
                    
                    title = self._extract_title_from_html(raw_content)
                    is_nav = 'nav' in href.lower()
                    
                    self.epub_chapters.append({
                        'title': title,
                        'html': raw_content,
                        'href': href,
                        'is_nav': is_nav
                    })
            
            for item in self.chapter_list.get_children():
                self.chapter_list.delete(item)
            
            for i, chapter in enumerate(self.epub_chapters):
                prefix = '📑 ' if chapter['is_nav'] else ''
                self.chapter_list.insert('', tk.END, iid=str(i), text=prefix + chapter['title'])
            
            self.add_info(f"📖 已加载EPUB: {os.path.basename(self.last_epub_path)}")
            self.add_info(f"   章节/页面数: {len(self.epub_chapters)}")
            self.add_info(f"   图片数: {len(self._epub_images)}")
            
            if self.epub_chapters:
                self.chapter_list.selection_set('0')
                self._render_chapter(0)
            
            self.preview_btn.config(state=tk.NORMAL, text='📖 加载EPUB')
                
        except Exception as e:
            self.preview_btn.config(state=tk.NORMAL, text='📖 加载EPUB')
            messagebox.showerror('加载失败', str(e))
            import traceback
            traceback.print_exc()
    
    def _resolve_epub_path(self, href, opf_base, files):
        if href in files:
            return href
        full = opf_base + '/' + href if opf_base else href
        if full in files:
            return full
        for f in files:
            if f.endswith('/' + href) or f == href:
                return f
        return None
    
    def _extract_title_from_html(self, html):
        import re
        match = re.search(r'<h1[^>]*>(.*?)</h1>', html, re.IGNORECASE | re.DOTALL)
        if match:
            title = match.group(1).strip()
            title = re.sub(r'<[^>]+>', '', title)
            return title
        match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        if match:
            title = match.group(1).strip()
            title = re.sub(r'<[^>]+>', '', title)
            return title
        return '未命名'
    
    def _render_chapter(self, index):
        if not 0 <= index < len(self.epub_chapters):
            return
        
        chapter = self.epub_chapters[index]
        html = chapter['html']
        
        self.content_text.config(state=tk.NORMAL)
        self.content_text.delete(1.0, tk.END)
        
        import re
        body_match = re.search(r'<body[^>]*>(.*?)</body>', html, re.IGNORECASE | re.DOTALL)
        if body_match:
            body = body_match.group(1)
        else:
            body = html
        
        body = re.sub(r'<script[^>]*>[\s\S]*?</script>', '', body, flags=re.IGNORECASE)
        body = re.sub(r'<style[^>]*>[\s\S]*?</style>', '', body, flags=re.IGNORECASE)
        
        segments = re.split(r'(<img[^>]*?>)', body, flags=re.IGNORECASE)
        
        for seg in segments:
            if re.match(r'<img[^>]*?>', seg, re.IGNORECASE):
                src_match = re.search(r'src=["\']([^"\']+)["\']', seg, re.IGNORECASE)
                if src_match:
                    src = src_match.group(1)
                    img_path = self._epub_images.get(src) or self._epub_images.get(os.path.basename(src))
                    if img_path and os.path.exists(img_path):
                        try:
                            from PIL import Image, ImageTk
                            pil_img = Image.open(img_path)
                            max_w = self.content_text.winfo_width() - 40
                            if max_w < 100:
                                max_w = 500
                            if pil_img.width > max_w:
                                ratio = max_w / pil_img.width
                                new_h = int(pil_img.height * ratio)
                                pil_img = pil_img.resize((max_w, new_h), Image.LANCZOS)
                            self._tk_images = getattr(self, '_tk_images', [])
                            tk_img = ImageTk.PhotoImage(pil_img)
                            self._tk_images.append(tk_img)
                            self.content_text.image_create(tk.END, image=tk_img)
                            self.content_text.insert(tk.END, '\n')
                        except Exception as e:
                            self.content_text.insert(tk.END, f'[图片: {src}]\n')
                    else:
                        self.content_text.insert(tk.END, f'[图片: {src}]\n')
            else:
                text = re.sub(r'<[^>]+>', '', seg)
                text = re.sub(r'&nbsp;', ' ', text)
                text = re.sub(r'&amp;', '&', text)
                text = re.sub(r'&lt;', '<', text)
                text = re.sub(r'&gt;', '>', text)
                text = re.sub(r'&quot;', '"', text)
                text = re.sub(r'\n\s*\n', '\n', text)
                if text.strip():
                    self.content_text.insert(tk.END, text)
        
        self.content_text.config(state=tk.DISABLED)
    
    def on_chapter_select(self, event):
        selected = self.chapter_list.selection()
        if selected:
            index = int(selected[0])
            self._render_chapter(index)

if __name__ == '__main__':
    root = tk.Tk()
    app = MainWindow(root)
    root.mainloop()
