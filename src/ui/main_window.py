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
from src.utils.config import load_config, save_config, get_config
from src.i18n import t, load_translations, get_available_languages

logger = setup_logger(__name__)


class MainWindow:
    def __init__(self, root):
        self.root = root
        self.config = load_config()
        self.root.title(t('app.title', 'PDF转EPUB工具'))
        self.root.geometry('1100x800')
        self.root.minsize(950, 700)

        self.pdf_paths = []
        self.output_dir = os.path.join(os.path.expanduser('~'), 'Desktop')
        self.task_manager = None
        self.output_format = tk.StringVar(value='epub')
        self.ocr_enabled = tk.BooleanVar(value=False)
        self.overwrite_mode = tk.StringVar(value='overwrite')
        self.lang_var = tk.StringVar(value='zh')

        self.completed_files = []

        self.setup_styles()
        self.create_widgets()
        self._load_config_to_ui()
        self.root.protocol('WM_DELETE_WINDOW', self._on_close)

    def _load_config_to_ui(self):
        self.overwrite_mode.set(get_config('output.overwrite_mode', 'ask'))
        self.output_format.set(get_config('output.formats', ['epub'])[0])
        lang = get_config('ui.language', 'zh')
        self.lang_var.set(lang)
        load_translations(lang)
        self._apply_translations()

    def _save_config(self):
        self.config['output']['overwrite_mode'] = self.overwrite_mode.get()
        self.config['output']['formats'] = [self.output_format.get()]
        self.config['ocr']['enabled'] = self.ocr_enabled.get()
        self.config['ui']['language'] = self.lang_var.get()
        save_config(self.config)

    def _on_close(self):
        self._save_config()
        self.root.destroy()

    def setup_styles(self):
        style = ttk.Style()
        style.theme_use('clam')

        bg_main = '#f1f5f9'
        bg_card = '#ffffff'
        text_primary = '#1e293b'
        text_secondary = '#64748b'
        accent = '#6366f1'

        style.configure('Main.TFrame', background=bg_main)
        style.configure('Sidebar.TFrame', background=bg_card)
        style.configure('Card.TFrame', background=bg_card, relief='flat')
        style.configure('Header.TFrame', background='#4f46e5')

        style.configure('Normal.TLabel',
                       font=('Segoe UI', 10),
                       foreground=text_primary,
                       background=bg_card)
        style.configure('Muted.TLabel',
                       font=('Segoe UI', 9),
                       foreground=text_secondary,
                       background=bg_card)
        style.configure('Status.TLabel',
                       font=('Segoe UI', 10, 'bold'),
                       foreground='#10b981',
                       background=bg_main)
        style.configure('Warning.TLabel',
                       font=('Segoe UI', 10, 'bold'),
                       foreground='#f59e0b',
                       background=bg_main)
        style.configure('Error.TLabel',
                       font=('Segoe UI', 10, 'bold'),
                       foreground='#ef4444',
                       background=bg_main)

        style.configure('Primary.TButton',
                       background=accent,
                       foreground='white',
                       font=('Segoe UI', 9),
                       padding=(6, 3))
        style.map('Primary.TButton',
                  background=[('active', '#4f46e5'), ('disabled', '#a5b4fc')],
                  foreground=[('disabled', '#ffffff')])

        style.configure('Success.TButton',
                       background='#10b981',
                       foreground='white',
                       font=('Segoe UI', 9, 'bold'),
                       padding=(8, 4))
        style.map('Success.TButton',
                  background=[('active', '#059669'), ('disabled', '#6ee7b7')],
                  foreground=[('disabled', '#ffffff')])

        style.configure('Danger.TButton',
                       background='#ef4444',
                       foreground='white',
                       font=('Segoe UI', 9),
                       padding=(6, 3))
        style.map('Danger.TButton',
                  background=[('active', '#dc2626'), ('disabled', '#fca5a5')],
                  foreground=[('disabled', '#ffffff')])

        style.configure('Info.TButton',
                       background='#3b82f6',
                       foreground='white',
                       font=('Segoe UI', 9),
                       padding=(6, 3))
        style.map('Info.TButton',
                  background=[('active', '#2563eb'), ('disabled', '#93c5fd')],
                  foreground=[('disabled', '#ffffff')])

        style.configure('Outline.TButton',
                       background=bg_card,
                       foreground=text_primary,
                       font=('Segoe UI', 8),
                       padding=(4, 2),
                       relief='solid',
                       borderwidth=1)
        style.map('Outline.TButton',
                  background=[('active', '#f1f5f9'), ('pressed', '#e2e8f0')])

        style.configure('SmallBtn.TButton',
                       background='#eef2ff',
                       foreground=accent,
                       font=('Segoe UI', 8),
                       padding=(4, 2))
        style.map('SmallBtn.TButton',
                  background=[('active', '#ddd6fe')])

        style.configure('Progress.Horizontal.TProgressbar',
                       troughcolor='#e2e8f0',
                       bordercolor='#e2e8f0',
                       lightcolor=accent,
                       darkcolor='#4f46e5',
                       background=accent)

        style.configure('Treeview',
                       background=bg_card,
                       foreground=text_primary,
                       font=('Segoe UI', 10),
                       rowheight=30,
                       borderwidth=0)
        style.configure('Treeview.Heading',
                       background='#f1f5f9',
                       foreground=text_primary,
                       font=('Segoe UI', 10, 'bold'),
                       relief='flat')
        style.map('Treeview',
                  background=[('selected', '#eef2ff')],
                  foreground=[('selected', accent)])
        style.layout('Treeview', [
            ('Treeview.treearea', {'sticky': 'nswe'})
        ])

        style.configure('Notebook',
                       background=bg_main,
                       tabmargins=[0, 8, 0, 0])
        style.configure('Notebook.Tab',
                       background='#e2e8f0',
                       foreground=text_secondary,
                       padding=[20, 8],
                       font=('Segoe UI', 10, 'bold'))
        style.map('Notebook.Tab',
                  background=[('selected', bg_card)],
                  foreground=[('selected', accent)],
                  expand=[('selected', [1, 1, 1, 0])])

        self.root.configure(bg=bg_main)

    def create_widgets(self):
        main_frame = ttk.Frame(self.root, style='Main.TFrame')
        main_frame.pack(fill=tk.BOTH, expand=True)

        controls_outer = ttk.Frame(main_frame, style='Main.TFrame')
        controls_outer.pack(fill=tk.X, padx=12, pady=(6, 4))

        row1 = tk.Frame(controls_outer, bg='#ffffff', highlightbackground='#e2e8f0',
                        highlightthickness=1)
        row1.pack(fill=tk.X, pady=(0, 3))

        r1_inner = tk.Frame(row1, bg='#ffffff')
        r1_inner.pack(fill=tk.X, padx=8, pady=5)

        self.upload_single_btn = ttk.Button(r1_inner, text=t('upload.single', '📄 选择单个'),
                                           command=self.upload_single_pdf, style='Primary.TButton')
        self.upload_single_btn.pack(side=tk.LEFT, padx=(0, 4))

        self.upload_batch_btn = ttk.Button(r1_inner, text=t('upload.batch', '📁 批量选择'),
                                          command=self.upload_batch_pdf, style='Info.TButton')
        self.upload_batch_btn.pack(side=tk.LEFT, padx=(0, 4))

        self.output_btn = ttk.Button(r1_inner, text=t('upload.output', '📂 输出目录'),
                                    command=self.select_output_dir, style='Outline.TButton')
        self.output_btn.pack(side=tk.LEFT)

        self.output_label = ttk.Label(controls_outer, text=os.path.basename(self.output_dir),
                                     style='Muted.TLabel')
        self.output_label.pack(pady=(2, 0), anchor=tk.W, padx=10)

        row2 = tk.Frame(controls_outer)
        row2.pack(fill=tk.X, pady=(2, 0))

        fmt_frame = tk.Frame(row2, bg='#ffffff', highlightbackground='#e2e8f0',
                             highlightthickness=1)
        fmt_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 3))
        fi = tk.Frame(fmt_frame, bg='#ffffff')
        fi.pack(padx=6, pady=4)
        tk.Label(fi, text=t('format.title', '输出格式'), font=('Segoe UI', 8, 'bold'),
                fg='#4f46e5', bg='#ffffff').pack(anchor=tk.W)
        fr = tk.Frame(fi, bg='#ffffff')
        fr.pack(anchor=tk.W, pady=(2, 0))
        self.fmt_epub_rb = ttk.Radiobutton(fr, text=t('format.epub', 'EPUB'),
                                          variable=self.output_format, value='epub')
        self.fmt_epub_rb.pack(side=tk.LEFT, padx=(0, 6))
        self.fmt_txt_rb = ttk.Radiobutton(fr, text=t('format.txt', 'TXT'),
                                         variable=self.output_format, value='txt')
        self.fmt_txt_rb.pack(side=tk.LEFT)

        opt_frame = tk.Frame(row2, bg='#ffffff', highlightbackground='#e2e8f0',
                              highlightthickness=1)
        opt_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=(0, 3))
        oi = tk.Frame(opt_frame, bg='#ffffff')
        oi.pack(padx=6, pady=4)
        tk.Label(oi, text=t('options.title', '选项'), font=('Segoe UI', 8, 'bold'),
                fg='#4f46e5', bg='#ffffff').pack(anchor=tk.W)
        orow = tk.Frame(oi, bg='#ffffff')
        orow.pack(anchor=tk.W, pady=(2, 0))
        self.ow_ask_rb = ttk.Radiobutton(orow, text=t('overwrite.ask', '询问'),
                                        variable=self.overwrite_mode, value='ask')
        self.ow_ask_rb.pack(side=tk.LEFT, padx=(0, 4))
        self.ow_overwrite_rb = ttk.Radiobutton(orow, text=t('overwrite.overwrite', '覆盖'),
                                               variable=self.overwrite_mode, value='overwrite')
        self.ow_overwrite_rb.pack(side=tk.LEFT, padx=(0, 4))
        self.ow_rename_rb = ttk.Radiobutton(orow, text=t('overwrite.rename', '重命名'),
                                           variable=self.overwrite_mode, value='rename')
        self.ow_rename_rb.pack(side=tk.LEFT)

        cvt_frame = tk.Frame(row2, bg='#ffffff', highlightbackground='#e2e8f0',
                              highlightthickness=1)
        cvt_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        ci = tk.Frame(cvt_frame, bg='#ffffff')
        ci.pack(padx=6, pady=4, fill=tk.X)
        self.ocr_check = ttk.Checkbutton(ci, text=t('options.ocr', 'OCR'),
                                         variable=self.ocr_enabled)
        self.ocr_check.pack(side=tk.LEFT)
        self.lang_combo = ttk.Combobox(ci, textvariable=self.lang_var,
                                     values=get_available_languages(), width=4,
                                     state='readonly')
        self.lang_combo.pack(side=tk.LEFT, padx=(6, 0))
        self.lang_combo.bind('<<ComboboxSelected>>', self._on_lang_change)

        row3 = tk.Frame(controls_outer, bg='#ffffff', highlightbackground='#e2e8f0',
                        highlightthickness=1)
        row3.pack(fill=tk.X, pady=(3, 0))

        r3i = tk.Frame(row3, bg='#ffffff')
        r3i.pack(padx=8, pady=4, fill=tk.X)

        self.convert_btn = ttk.Button(r3i, text=t('convert.start', '🚀 转换'),
                                    command=self.start_convert, state=tk.DISABLED,
                                    style='Success.TButton')
        self.convert_btn.pack(side=tk.LEFT, padx=(0, 6))

        self.cancel_btn = ttk.Button(r3i, text=t('convert.cancel', '⏹ 取消'),
                                    command=self.cancel_convert, state=tk.DISABLED,
                                    style='Danger.TButton')
        self.cancel_btn.pack(side=tk.LEFT, padx=(0, 10))

        self.progress_bar = ttk.Progressbar(r3i, orient=tk.HORIZONTAL,
                                          mode='determinate', style='Progress.Horizontal.TProgressbar',
                                          length=120)
        self.progress_bar.pack(side=tk.LEFT)

        self.status_label = ttk.Label(r3i, text=t('convert.ready', '就绪'), style='Status.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=(8, 0))

        files_row = tk.Frame(controls_outer, bg='#ffffff', highlightbackground='#e2e8f0',
                            highlightthickness=1)
        files_row.pack(fill=tk.X, pady=(3, 0))

        fri = tk.Frame(files_row, bg='#ffffff')
        fri.pack(fill=tk.X, padx=6, pady=4)
        self.files_list = tk.Listbox(fri, bg='#f8fafc', fg='#1e293b',
                                    font=('Segoe UI', 9), bd=0, height=2,
                                    selectbackground='#eef2ff', selectforeground='#4f46e5',
                                    activestyle='none')
        files_scroll = ttk.Scrollbar(fri, orient=tk.VERTICAL, command=self.files_list.yview)
        self.files_list.configure(yscrollcommand=files_scroll.set)
        self.files_list.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 4))
        files_scroll.pack(side=tk.LEFT, fill=tk.Y)
        self.remove_btn = ttk.Button(fri, text=t('upload.remove', '移除'),
                                    command=self.remove_selected, style='Outline.TButton')
        self.remove_btn.pack(side=tk.LEFT, padx=(0, 3))
        self.clear_btn = ttk.Button(fri, text=t('upload.clear', '清空'),
                                   command=self.clear_files, style='Outline.TButton')
        self.clear_btn.pack(side=tk.LEFT)

        content_area = ttk.Frame(main_frame, style='Main.TFrame')
        content_area.pack(fill=tk.BOTH, expand=True, padx=12, pady=4)

        self.right_notebook = ttk.Notebook(content_area)
        self.right_notebook.pack(fill=tk.BOTH, expand=True)

        info_tab = ttk.Frame(self.right_notebook, style='Sidebar.TFrame')
        self.right_notebook.add(info_tab, text=t('tab.info', '📋 转换信息'))

        self.info_text = scrolledtext.ScrolledText(info_tab,
                                                   wrap=tk.WORD,
                                                   bg='#f8fafc',
                                                   fg='#334155',
                                                   font=('Consolas', 10),
                                                   bd=0,
                                                   padx=12, pady=12)
        self.info_text.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)
        self._refresh_info_text()
        self.info_text.config(state=tk.DISABLED)

        preview_frame = ttk.Frame(self.right_notebook, style='Sidebar.TFrame')
        self.right_notebook.add(preview_frame, text=t('tab.preview', '👁 预览'))

        self.preview_container = ttk.Frame(preview_frame, style='Sidebar.TFrame')
        self.preview_container.pack(fill=tk.BOTH, expand=True, padx=8, pady=8)

        self._build_preview_file_list()
        self._build_preview_content()

    def _build_preview_file_list(self):
        self.preview_list_frame = ttk.Frame(self.preview_container)
        self.list_header = tk.Label(self.preview_list_frame, text=t('preview.filelist_title', '转换完成的文件'),
                                   font=('Segoe UI', 11, 'bold'), fg='#1e293b', bg='#ffffff',
                                   justify=tk.LEFT)
        self.list_header.pack(anchor=tk.W, pady=(0, 8))

        columns = ('filename', 'chapters', 'action')
        self.file_list_tree = ttk.Treeview(self.preview_list_frame, columns=columns,
                                           show='headings', selectmode='browse', height=8)
        self.file_list_tree.heading('filename', text=t('task.filename', '文件名'))
        self.file_list_tree.heading('chapters', text=t('task.chapters', '章节数'))
        self.file_list_tree.heading('action', text='')
        self.file_list_tree.column('filename', width=280, anchor=tk.W)
        self.file_list_tree.column('chapters', width=80, anchor=tk.CENTER)
        self.file_list_tree.column('action', width=80, anchor=tk.CENTER)
        self.file_list_tree.pack(fill=tk.BOTH, expand=True)

        self.file_list_empty_label = ttk.Label(self.preview_list_frame,
                                               text=t('preview.empty_hint', '暂无已转换的文件，请先执行转换操作'),
                                               style='Muted.TLabel')
        self.file_list_empty_label.pack(pady=30)

    def _build_preview_content(self):
        self.preview_content_frame = ttk.Frame(self.preview_container)

        nav_bar = tk.Frame(self.preview_content_frame, bg='#f1f5f9')
        nav_bar.pack(fill=tk.X)

        self.back_btn = ttk.Button(nav_bar, text='◀ ' + t('preview.back', '返回列表'),
                                  command=self._preview_back_to_list, style='Outline.TButton')
        self.back_btn.pack(side=tk.LEFT, padx=4, pady=4)

        self.preview_filename_label = tk.Label(nav_bar, text='',
                                             font=('Segoe UI', 10, 'bold'),
                                             fg='#4f46e5', bg='#f1f5f9')
        self.preview_filename_label.pack(side=tk.LEFT, padx=8, pady=4)

        body = ttk.Frame(self.preview_content_frame, style='Sidebar.TFrame')
        body.pack(fill=tk.BOTH, expand=True)

        splitter = ttk.PanedWindow(body, orient=tk.HORIZONTAL)
        splitter.pack(fill=tk.BOTH, expand=True)

        self.chapter_list_frame = ttk.Frame(splitter, width=220)
        splitter.add(self.chapter_list_frame, weight=1)

        ch_header = tk.Frame(self.chapter_list_frame, bg='#f1f5f9')
        ch_header.pack(fill=tk.X)
        tk.Label(ch_header, text='  Chapters', font=('Segoe UI', 9, 'bold'),
                fg='#64748b', bg='#f1f5f9').pack(side=tk.LEFT, pady=4, padx=8)

        self.chapter_list = ttk.Treeview(self.chapter_list_frame, show='tree')
        self.chapter_list.pack(fill=tk.BOTH, expand=True, padx=4, pady=(0, 4))
        self.chapter_list.bind('<<TreeviewSelect>>', self.on_chapter_select)

        self.content_frame = ttk.Frame(splitter)
        splitter.add(self.content_frame, weight=4)

        ct_header = tk.Frame(self.content_frame, bg='#f1f5f9')
        ct_header.pack(fill=tk.X)
        tk.Label(ct_header, text='  Content', font=('Segoe UI', 9, 'bold'),
                fg='#64748b', bg='#f1f5f9').pack(side=tk.LEFT, pady=4, padx=8)

        self.content_text = scrolledtext.ScrolledText(self.content_frame,
                                                     wrap=tk.WORD,
                                                     bg='#ffffff',
                                                     fg='#334155',
                                                     font=('Segoe UI', 11),
                                                     bd=0,
                                                     padx=16, pady=12)
        self.content_text.pack(fill=tk.BOTH, expand=True)
        self.content_text.config(state=tk.DISABLED)

        self.last_epub_path = None
        self.epub_chapters = []

    def _show_preview_list_mode(self):
        self.preview_content_frame.forget()
        self.preview_list_frame.pack(fill=tk.BOTH, expand=True)

    def _show_preview_content_mode(self):
        self.preview_list_frame.forget()
        self.preview_content_frame.pack(fill=tk.BOTH, expand=True)

    def _preview_back_to_list(self):
        self._show_preview_list_mode()
        self.last_epub_path = None
        self.epub_chapters = []

    def _on_lang_change(self, event=None):
        lang = self.lang_var.get()
        load_translations(lang)
        self._apply_translations()
        self._save_config()

    def _apply_translations(self):
        self.root.title(t('app.title', 'PDF转EPUB工具'))

        self.upload_single_btn.config(text=t('upload.single', '📄 选择单个'))
        self.upload_batch_btn.config(text=t('upload.batch', '📁 批量选择'))
        self.output_btn.config(text=t('upload.output', '📂 输出目录'))
        self.remove_btn.config(text=t('upload.remove', '移除'))
        self.clear_btn.config(text=t('upload.clear', '清空'))

        self.fmt_epub_rb.config(text=t('format.epub', 'EPUB'))
        self.fmt_txt_rb.config(text=t('format.txt', 'TXT'))

        self.ow_ask_rb.config(text=t('overwrite.ask', '询问'))
        self.ow_overwrite_rb.config(text=t('overwrite.overwrite', '覆盖'))
        self.ow_rename_rb.config(text=t('overwrite.rename', '重命名'))

        self.ocr_check.config(text=t('options.ocr', 'OCR'))

        self.convert_btn.config(text=t('convert.start', '🚀 转换'))
        self.cancel_btn.config(text=t('convert.cancel', '⏹ 取消'))

        self.status_label.config(text=t('convert.ready', '就绪'))

        self.right_notebook.tab(0, text=t('tab.info', '📋 Info'))
        self.right_notebook.tab(1, text=t('tab.preview', '👁 Preview'))

        self.back_btn.config(text='◀ ' + t('preview.back', '返回列表'))
        self.list_header.config(text=t('preview.filelist_title', '转换完成的文件'))
        self.file_list_empty_label.config(text=t('preview.empty_hint', '暂无已转换的文件，请先执行转换操作'))

        self._refresh_info_text()

    def _refresh_info_text(self):
        self.info_text.config(state=tk.NORMAL)
        self.info_text.delete(1.0, tk.END)
        self.info_text.insert(tk.END, f"{'='*50}\n")
        self.info_text.insert(tk.END, f"  {t('app.welcome', 'Welcome to PDF to EPUB Converter')}\n")
        self.info_text.insert(tk.END, f"{'='*50}\n\n")
        self.info_text.insert(tk.END, f"{t('info.features', 'Features:')}\n")
        self.info_text.insert(tk.END, f"  {'\u2022'} {t('info.feature1', 'Smart PDF chapter detection')}\n")
        self.info_text.insert(tk.END, f"  {'\u2022'} {t('info.feature2', 'Auto-generate navigable EPUB TOC')}\n")
        self.info_text.insert(tk.END, f"  {'\u2022'} {t('info.feature3', 'Correct image conversion & display')}\n")
        self.info_text.insert(tk.END, f"  {'\u2022'} {t('info.feature4', 'Precise layout preservation')}\n")
        self.info_text.insert(tk.END, f"  {'\u2022'} {t('info.feature5', 'Multi-format output (EPUB / TXT)')}\n")
        self.info_text.insert(tk.END, f"  {'\u2022'} {t('info.feature6', 'Batch parallel conversion')}\n")
        self.info_text.insert(tk.END, f"  {'\u2022'} {t('info.feature7', 'EPUB in-app preview')}\n")
        self.info_text.insert(tk.END, f"  {'\u2022'} {t('info.feature8', 'OCR scanned document support')}\n\n")
        self.info_text.insert(tk.END, f"{t('info.usage', 'Instructions:')}\n")
        self.info_text.insert(tk.END, f"  1. {t('info.step1', 'Click \"Select PDF\" to upload one or more PDFs')}\n")
        self.info_text.insert(tk.END, f"  2. {t('info.step2', 'Choose output format (EPUB/TXT)')}\n")
        self.info_text.insert(tk.END, f"  3. {t('info.step3', 'Select output directory')}\n")
        self.info_text.insert(tk.END, f"  4. {t('info.step4', 'Configure overwrite mode and options')}\n")
        self.info_text.insert(tk.END, f"  5. {t('info.step5', 'Click \"Start Convert\" button')}\n")
        self.info_text.config(state=tk.DISABLED)

    def add_info(self, text):
        self.info_text.config(state=tk.NORMAL)
        self.info_text.insert(tk.END, text + '\n')
        self.info_text.see(tk.END)
        self.info_text.config(state=tk.DISABLED)

    def upload_single_pdf(self):
        file_path = filedialog.askopenfilename(
            title=t('upload.file_dialog', 'Select PDF File'),
            filetypes=[(t('upload.file_type', 'PDF Files'), '*.pdf')]
        )
        if file_path and file_path not in self.pdf_paths:
            self.pdf_paths.append(file_path)
            self.update_files_list()
            self.check_convert_ready()

    def upload_batch_pdf(self):
        file_paths = filedialog.askopenfilenames(
            title=t('upload.file_dialog_batch', 'Select Multiple PDF Files'),
            filetypes=[(t('upload.file_type', 'PDF Files'), '*.pdf')]
        )
        for file_path in file_paths:
            if file_path and file_path not in self.pdf_paths:
                self.pdf_paths.append(file_path)
        self.update_files_list()
        self.check_convert_ready()

    def select_output_dir(self):
        output_dir = filedialog.askdirectory(title=t('upload.output_dialog', 'Select Output Directory'))
        if output_dir:
            self.output_dir = output_dir
            self.output_label.config(text=os.path.basename(output_dir))
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
        fmt = self.output_format.get()
        ext = 'epub' if fmt == 'epub' else 'txt'
        existing_files = []
        for pdf_path in self.pdf_paths:
            filename = os.path.splitext(os.path.basename(pdf_path))[0] + f'.{ext}'
            output_path = os.path.join(self.output_dir, filename)
            if os.path.exists(output_path):
                existing_files.append(filename)

        if not existing_files:
            return True

        mode = self.overwrite_mode.get()

        if mode == 'overwrite':
            self.add_info(t('convert.existing_warn', 'Found {0} existing files, will overwrite').format(len(existing_files)))
            return True

        if mode == 'rename':
            self.add_info(t('convert.existing_info', 'Found {0} existing files, will auto rename').format(len(existing_files)))
            return True

        msg = t('convert.existing_msg', 'The following files already exist:\n\n{0}\n\nHow would you like to proceed?').format(chr(10).join(existing_files))
        result = messagebox.askyesnocancel(t('convert.existing_title', 'File Exists'), msg)

        if result is True:
            self.add_info(t('convert.user_overwrite', 'User chose to overwrite'))
            return True
        elif result is False:
            for pdf_path in self.pdf_paths:
                filename = os.path.splitext(os.path.basename(pdf_path))[0] + f'.{ext}'
                output_path = os.path.join(self.output_dir, filename)
                if os.path.exists(output_path):
                    base, file_ext = os.path.splitext(filename)
                    counter = 1
                    while os.path.exists(os.path.join(self.output_dir, f"{base}_{counter}{file_ext}")):
                        counter += 1
            self.add_info(t('convert.auto_rename', 'Files auto renamed'))
            return True
        else:
            return False

    def start_convert(self):
        if not self.pdf_paths or not self.output_dir:
            return

        if not self.check_existing_files():
            return

        self.completed_files = []
        self._clear_preview_file_list()

        fmt = self.output_format.get()
        self.task_manager = TaskManager(max_workers=4)

        if fmt == 'txt':
            self._convert_txt_batch()
        else:
            self._convert_epub_batch()

    def _convert_epub_batch(self):
        self.task_manager.add_tasks(self.pdf_paths, self.output_dir)
        self._run_conversion()

    def _convert_txt_batch(self):
        from src.converter.txt_builder import TXTBuilder
        from src.parser.pdf_extractor import PDFExtractor

        def convert_to_txt(task):
            try:
                with self.task_manager.lock:
                    task.status = 'running'
                    task.progress = 10

                extractor = PDFExtractor(task.pdf_path)
                chapters = extractor.detect_chapters()
                task.chapters = chapters

                with self.task_manager.lock:
                    task.progress = 40

                builder = TXTBuilder()
                builder.set_metadata(os.path.splitext(os.path.basename(task.pdf_path))[0])

                for ch in chapters:
                    builder.add_chapter(ch['title'], ch.get('content', []))

                with self.task_manager.lock:
                    task.progress = 80

                success = builder.save(task.output_path)

                with self.task_manager.lock:
                    task.progress = 100
                    if success:
                        task.status = 'completed'
                    else:
                        task.status = 'failed'
                        task.error = t('task.save_txt_failed', 'Failed to save TXT')

                extractor.close()

            except Exception as e:
                with self.task_manager.lock:
                    task.status = 'failed'
                    task.error = str(e)

            self.root.after(0, lambda: self._on_task_callback())

        for pdf_path in self.pdf_paths:
            filename = os.path.splitext(os.path.basename(pdf_path))[0] + '.txt'
            output_path = os.path.join(self.output_dir, filename)
            task = self.task_manager.add_task(pdf_path, output_path)

        self._run_txt_conversion(convert_to_txt)

    def _run_txt_conversion(self, convert_fn):
        self._pre_convert_setup()

        self.task_manager.executor = __import__('concurrent.futures').futures.ThreadPoolExecutor(max_workers=4)
        for task in self.task_manager.tasks:
            self.task_manager.executor.submit(convert_fn, task)
        self.task_manager.executor.shutdown(wait=False)

        self.monitor_thread = threading.Thread(target=self.monitor_tasks)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def _run_conversion(self):
        self._pre_convert_setup()

        safe_callback = lambda s: self.root.after(0, lambda: self.update_progress(s))
        self.task_manager.execute(callback=safe_callback)

        self.monitor_thread = threading.Thread(target=self.monitor_tasks)
        self.monitor_thread.daemon = True
        self.monitor_thread.start()

    def _on_task_callback(self):
        self.update_progress(self.task_manager.get_summary())

    def _pre_convert_setup(self):
        self.convert_btn.config(state=tk.DISABLED)
        self.cancel_btn.config(state=tk.NORMAL)
        self.upload_single_btn.config(state=tk.DISABLED)
        self.upload_batch_btn.config(state=tk.DISABLED)
        self.output_btn.config(state=tk.DISABLED)

        fmt = self.output_format.get().upper()
        self.add_info(t('convert.start_msg', '[CONVERT] Converting {0} file(s) to {1}...').format(len(self.pdf_paths), fmt))
        self.status_label.config(text=t('convert.running', 'Status: Converting...'))
        self.status_label.config(style='Warning.TLabel')

    def monitor_tasks(self):
        while True:
            summary = self.task_manager.get_summary()
            if summary['pending'] == 0 and summary['running'] == 0:
                self.root.after(0, self.finalize_convert)
                break
            self.root.after(0, lambda s=summary: self.update_progress(s))
            import time
            time.sleep(0.5)

    def update_progress(self, summary):
        self.progress_bar['value'] = summary['avg_progress']

        if summary['running'] == 0:
            status_text = t('convert.done_fmt', 'Done (OK:{0}, Fail:{1})').format(summary['completed'], summary['failed'])
        else:
            status_text = t('convert.running_fmt', 'Running ({0})').format(summary['running'])

        if summary['failed'] > 0:
            self.status_label.config(style='Error.TLabel')
        elif summary['running'] > 0:
            self.status_label.config(style='Warning.TLabel')
        else:
            self.status_label.config(style='Status.TLabel')

        self.status_label.config(text=status_text)

        stats_text = t('convert.stats', 'Total:{0} | Done:{1} | Fail:{2} | Run:{3}').format(
            summary['total'], summary['completed'], summary['failed'], summary['running'])
        self.stats_label.config(text=stats_text)

    def finalize_convert(self):
        summary = self.task_manager.get_summary()

        if summary['failed'] > 0:
            self.add_info(t('convert.complete_warn', '[WARN] Complete! OK:{0}, Fail:{1}').format(summary['completed'], summary['failed']))
        else:
            self.add_info(t('convert.complete_msg', '[OK] Conversion complete! Success: {0}').format(summary['completed']))

        completed_tasks = [t for t in summary['tasks'] if t.status == 'completed']
        fmt = self.output_format.get()
        ext = 'epub' if fmt == 'epub' else 'txt'

        seen_names = set()
        for task in completed_tasks:
            out_path = task.output_path
            if not os.path.exists(out_path):
                base = os.path.splitext(os.path.basename(out_path))[0]
                candidate = os.path.join(self.output_dir, f"{base}.{ext}")
                if os.path.exists(candidate) and candidate != out_path:
                    out_path = candidate
                    logger.info(f"修正输出路径: {task.output_path} -> {out_path}")

            name = os.path.basename(out_path)
            if name in seen_names:
                base, file_ext = os.path.splitext(name)
                counter = 1
                while f"{base}_{counter}{file_ext}" in seen_names:
                    counter += 1
                name = f"{base}_{counter}{file_ext}"

            if os.path.exists(out_path):
                seen_names.add(name)
                self.completed_files.append({
                    'name': name,
                    'path': out_path,
                    'chapters': len(task.chapters) if task.chapters else 0
                })
                logger.info(f"已完成文件: {name} ({out_path})")
            else:
                logger.warning(f"任务完成但文件不存在: {out_path}")

        actual_in_dir = []
        if os.path.isdir(self.output_dir):
            for f in os.listdir(self.output_dir):
                if f.endswith(f'.{ext}') and not any(cf['name'] == f for cf in self.completed_files):
                    full = os.path.join(self.output_dir, f)
                    actual_in_dir.append({'name': f, 'path': full, 'chapters': '-'})
                    logger.info(f"目录中发现额外文件: {f}")

        self.completed_files.extend(actual_in_dir)

        self._populate_preview_file_list()

        previewable = [cf for cf in self.completed_files if cf['path'].endswith('.epub')]
        if len(previewable) == 1:
            self.last_epub_path = previewable[0]['path']
            self.right_notebook.select(1)
            self._show_preview_content_mode()
            self.preview_filename_label.config(text=previewable[0]['name'])
            self.root.after(200, self.preview_epub)
        elif len(previewable) > 1:
            self.right_notebook.select(1)
            self._show_preview_list_mode()

        self._reset_convert_ui()

    def _reset_convert_ui(self):
        self.convert_btn.config(state=tk.NORMAL)
        self.cancel_btn.config(state=tk.DISABLED)
        self.upload_single_btn.config(state=tk.NORMAL)
        self.upload_batch_btn.config(state=tk.NORMAL)
        self.output_btn.config(state=tk.NORMAL)
        self.status_label.config(text=t('convert.done', 'Status: Done'))
        self.status_label.config(style='Status.TLabel')

    def cancel_convert(self):
        if self.task_manager:
            self.task_manager.cancel_all()
            self.add_info(t('convert.cancelled_msg', '[CANCEL] Conversion cancelled'))
            self.status_label.config(text=t('convert.cancelled', 'Status: Cancelled'))
            self.status_label.config(style='Warning.TLabel')
            self._reset_convert_ui()

    def _clear_preview_file_list(self):
        for item in self.file_list_tree.get_children():
            self.file_list_tree.delete(item)
        self.file_list_empty_label.pack(pady=30)

    def _populate_preview_file_list(self):
        for item in self.file_list_tree.get_children():
            self.file_list_tree.delete(item)

        if not self.completed_files:
            self.file_list_empty_label.pack(pady=30)
            return

        self.file_list_empty_label.pack_forget()

        for i, finfo in enumerate(self.completed_files):
            ext = 'epub' if finfo['path'].endswith('.epub') else ''
            btn_text = t('preview.view_btn', '预览') if ext else '-'
            self.file_list_tree.insert('', tk.END, iid=str(i),
                                       values=(finfo['name'], finfo['chapters'], btn_text))

        self.file_list_tree.bind('<Double-1>', self._on_file_list_double_click)

    def _on_file_list_double_click(self, event):
        selected = self.file_list_tree.selection()
        if selected:
            idx = int(selected[0])
            self._preview_file_at(idx)

    def _preview_file_at(self, idx):
        if idx < 0 or idx >= len(self.completed_files):
            return
        finfo = self.completed_files[idx]
        path = finfo['path']
        if not path.endswith('.epub'):
            messagebox.showinfo(t('preview.error', '提示'),
                               f"{finfo['name']}\n\n{t('preview.txt_hint', 'TXT 文件不支持在界面中预览，请直接用文本编辑器打开。')}")
            return
        if not os.path.exists(path):
            messagebox.showerror(t('preview.error', '文件不存在'),
                                f"{finfo['name']}\n\n{t('preview.not_found', '文件路径不存在：')}\n{path}")
            return
        self.last_epub_path = path
        self._show_preview_content_mode()
        self.preview_filename_label.config(text=finfo['name'])
        self.preview_epub()

    def preview_epub(self):
        if not self.last_epub_path:
            return

        try:
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

            self.add_info(t('preview.loaded', '[PREVIEW] Loaded: {0}').format(os.path.basename(self.last_epub_path)))
            self.add_info(t('preview.chapters', '         Chapters/Pages: {0}').format(len(self.epub_chapters)))
            self.add_info(t('preview.images', '         Images: {0}').format(len(self._epub_images)))

            if self.epub_chapters:
                self.chapter_list.selection_set('0')
                self._render_chapter(0)

        except Exception as e:
            messagebox.showerror(t('preview.error', 'Load Failed'), str(e))

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
        return t('preview.unnamed', 'Untitled')

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
                            self.content_text.insert(tk.END, f'[Image: {src}]\n')
                    else:
                        self.content_text.insert(tk.END, f'[Image: {src}]\n')
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