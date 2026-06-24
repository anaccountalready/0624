# PdfToEPUB

**PDF 转 EPUB 转换工具** — 支持 GUI 和 CLI 双模式，保留排版样式，自动识别章节，批量并行转换。

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)

## 功能特性

- **GUI 界面** — 上传、转换、预览三合一，现代化配色
- **CLI 命令行** — `pdf2epub convert` / `batch` / `info` 三种命令
- **章节识别** — 自动检测 PDF 章节标题，生成可跳转目录
- **排版保留** — 字体大小、粗细、斜体精确映射到 EPUB CSS
- **图片转换** — 支持 881 张唯一图片，99.5% 覆盖率
- **批量并行** — 多文件并发转换，可配置线程数
- **多格式输出** — EPUB / TXT，可扩展
- **OCR 支持** — 可选 Tesseract OCR 处理扫描件 PDF
- **配置系统** — YAML 配置文件，用户偏好持久化
- **国际化** — 中文 / English 双语支持
- **完整测试** — pytest 测试套件，覆盖核心模块

## 快速开始

### 安装依赖

```bash
pip install -r requirements.txt
```

### 启动 GUI

```bash
python run.py
```

### CLI 命令

```bash
# 转换单个文件
python -m src.cli.commands convert -i book.pdf -o book.epub

# 批量转换
python -m src.cli.commands batch -i ./pdfs -o ./output -w 4

# 查看 PDF 信息
python -m src.cli.commands info -i book.pdf
```

### 运行测试

```bash
pytest tests/ -v
```

## 项目结构

```
PdfToEPUB/
├── run.py                          # GUI 启动入口
├── requirements.txt                # 依赖清单
├── config/
│   └── default.yaml                # 默认配置
├── tests/
│   ├── conftest.py                 # pytest 配置
│   ├── test_pdf_extractor.py       # PDF 解析测试
│   ├── test_epub_builder.py        # EPUB 生成测试
│   ├── test_task_manager.py        # 任务管理测试
│   └── fixtures/                   # 测试夹具
├── logs/
│   └── pdf2epub.log                # 运行日志
├── examplepdf/                     # 示例 PDF 文件
└── src/
    ├── parser/
    │   ├── pdf_extractor.py        # PDF 解析（文字/图片/样式）
    │   └── ocr_engine.py           # OCR 引擎（扫描件）
    ├── converter/
    │   ├── epub_builder.py         # EPUB 生成器
    │   └── txt_builder.py          # TXT 生成器
    ├── task/
    │   └── task_manager.py         # 任务调度（并发/进度）
    ├── ui/
    │   └── main_window.py          # GUI 主界面
    ├── cli/
    │   └── commands.py             # 命令行工具
    ├── i18n/
    │   ├── zh.json                 # 中文翻译
    │   └── en.json                 # 英文翻译
    └── utils/
        ├── logger.py               # 日志工具
        ├── config.py               # 配置管理
        └── exceptions.py           # 自定义异常
```

## 配置说明

编辑 `config/default.yaml` 或 `~/.pdf2epub/config.yaml`：

```yaml
output:
  overwrite_mode: ask          # ask | overwrite | rename
  formats: [epub, txt]

conversion:
  max_workers: 4               # 并行线程数
  preserve_layout: true        # 保留排版
  image_quality: 90            # 图片质量

ocr:
  enabled: false               # 启用 OCR
  language: eng                # OCR 语言
  dpi: 300                     # OCR 分辨率

ui:
  theme: blue                  # 主题颜色
  language: zh                 # 界面语言
```

## 依赖库

| 库 | 用途 |
|---|---|
| [PyMuPDF](https://pymupdf.readthedocs.io/) | PDF 解析 |
| [EbookLib](https://github.com/aerkalov/ebooklib) | EPUB 生成 |
| [Pillow](https://python-pillow.org/) | 图片处理 |
| [PyYAML](https://pyyaml.org/) | 配置文件解析 |
| [pytest](https://pytest.org/) | 测试框架 |

## 许可证

MIT License