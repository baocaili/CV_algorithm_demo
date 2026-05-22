# CV 教学软件 / CV Learning Lab

[中文说明](#中文说明) · [English](#english)

---

## 中文说明

面向机器视觉课程练习的桌面小工具：用 OpenCV 跑常见图像/视频算子，结果以「子图卡牌」排布；正面为效果图，背面为教材式说明（文案随包数据加载，可改包内数据文件后重启生效）。需要离线阅读长文时，可直接打开 `docs/algorithms.md`。

主界面为 **Tkinter**。另有 **Streamlit** 页面：可做图像算子预览；**视频**页为各视频算法的文字说明，不做实时摄像头或文件播放。

### 功能要点

| 模块     | 说明                                                                                                   |
| ------ | ---------------------------------------------------------------------------------------------------- |
| 图像     | 打开/保存 BGR 图；按勾选算法生成多张结果卡牌。                                                                           |
| 视频与摄像头 | 多算法共用同一时间轴；播放/暂停；仅文件视频可拖进度条。MeanShift / CamShift 各自维护状态。Windows 上摄像头优先 DirectShow，并尝试 640×480 与较小缓冲。 |
| YOLO   | Ultralytics；默认 `yolo11n.pt`，路径在视频参数中修改。                                                              |
| 画图     | 白板练习；与图像/视频/摄像头互斥。                                                                                   |
| 语言     | 默认英文；菜单「设置 → 语言」切换中英文界面与卡牌标题。                                                                        |
| 日志     | 有操作后出现；可按级别筛选。                                                                                       |

### 环境

Python 3.10+，建议虚拟环境。依赖见 `requirements.txt`。卡牌背面优先用 TkinterWeb 渲染 Markdown；不可用时退回纯文本。

```bash
python -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
```

### 启动

```bash
cd /path/to/cv_course
python -m cv_course
```

```bash
streamlit run cv_course/ui_streamlit/app.py
```

### Tk 操作摘要

用工具栏或菜单「操作」打开图像、视频或摄像头。子图卡牌**右键**翻面看说明，再右键回到正面；背面说明在**首次翻到背面**时再加载，减轻启动等待。背面滚轮阅读长文；多牌时外层画布可滚动。在「设置」里勾选要展示的算法、调整卡牌最大边长（默认约 600 px）。

### 修改卡牌与标题文案

编辑包内 `cv_course/data/algo_descriptions.csv`（UTF-8，可带 BOM）：列包括 `algorithm_id`、`lang`（`zh` / `en`）、`title`、`principle`、`function_desc`、`example`、`usage_py`、可选 `extension`；支持多行与 Markdown。也可用环境变量 `CV_COURSE_ALGO_CSV` 指向另一份路径，便于做课程定制。改后重启程序或切换语言触发重载（以程序行为为准）。

### 仓库文件树（全路径）

```
cv_course/                              # 仓库根目录
├── README.md
├── requirements.txt
├── cv_course_demo.md
├── PACKAGING_OMIT.md
├── docs/
│   └── algorithms.md
└── cv_course/                          # Python 包
    ├── __init__.py
    ├── __main__.py
    ├── util_cv.py
    ├── state.py
    ├── i18n.py
    ├── algo_descriptions.py
    ├── algo_text_en.py
    ├── algo_doc_layout.py
    ├── md_plain.py
    ├── md_html.py
    ├── edu_merge.py
    ├── data/
    │   └── algo_descriptions.csv
    ├── algorithms/
    │   ├── __init__.py
    │   ├── registry.py
    │   ├── subcategories.py
    │   ├── image_handlers.py
    │   ├── video_handlers.py
    │   └── hist_vis.py
    ├── ui_tk/
    │   ├── __init__.py
    │   ├── app.py
    │   ├── toolbar_icons.py
    │   └── algorithm_picker.py
    ├── ui_streamlit/
        ├── __init__.py
        └── app.py
```

### 文件说明（运行与教材数据）

- **`README.md`**  
  本说明：安装、启动、界面操作、目录与文件职责。

- **`requirements.txt`**  
  第三方依赖及版本下限，供 `pip install -r` 使用。

- **`cv_course_demo.md`**  
  早期设计备忘与需求摘录，保留作背景资料，不参与 import。

- **`PACKAGING_OMIT.md`**  
  列出建议从发行包中省略的维护脚本及处理注意点；若你不希望对外展示维护流程，发布前可连同该说明一并删除。

- **`docs/algorithms.md`**  
  离线算法参考手册：中英分块、按算法 id 分节，正文以围栏代码块保留版式。可与 Tk 程序配合阅读。

- **`cv_course/__init__.py`**  
  包版本号 `__version__`，供菜单「关于」与构建脚本读取。

- **`cv_course/__main__.py`**  
  入口：`python -m cv_course` 时启动 Tk 主程序。

- **`cv_course/util_cv.py`**  
  BGR 与显示用图像转换、`np_to_photoimage`、尺寸适配等通用图像工具。

- **`cv_course/state.py`**  
  应用状态：当前模式、路径、图像/视频参数对象、布局与语言等。

- **`cv_course/i18n.py`**  
  Tk 界面中英文字符串表。

- **`cv_course/algo_descriptions.py`**  
  加载算法说明数据（默认读包内 CSV），按 id 与语言取标题、段落；支持切换语言时重载。

- **`cv_course/algo_text_en.py`**  
  算法英文短标题等静态映射，供注册表与界面展示用。

- **`cv_course/algo_doc_layout.py`**  
  将说明正文拆成「原理 / 功能 / 用法」等展示块，并做标题与围栏规范化。

- **`cv_course/md_plain.py`**  
  Markdown 转纯文本，供卡牌背面无 Web 组件时的退路。

- **`cv_course/md_html.py`**  
  Markdown 转 HTML 文档片段、围栏单元格等，供 TkinterWeb 背面使用。

- **`cv_course/edu_merge.py`**  
  中英文字段富化、从已有行补全等逻辑；供 `cv_course/tools` 下维护脚本 import，主程序运行时不依赖。

- **`cv_course/data/algo_descriptions.csv`**  
  各算法 id 的中英文标题与长文说明数据源；Tk 卡牌背面与标题依赖此文件（或 `CV_COURSE_ALGO_CSV` 覆盖路径）。

- **`cv_course/algorithms/__init__.py`**  
  算法子包占位。

- **`cv_course/algorithms/registry.py`**  
  算法 id 注册、`AlgorithmSpec`、图像/视频调度入口 `apply_*`、迭代器。

- **`cv_course/algorithms/subcategories.py`**  
  算法在界面勾选器中的子类分组（中文子类名等）。

- **`cv_course/algorithms/image_handlers.py`**  
  各图像类 `algorithm_id` 的 OpenCV 实现。

- **`cv_course/algorithms/video_handlers.py`**  
  各视频类 `algorithm_id` 的实现及 `VideoEngine`（跨帧状态如 MOG2、YOLO 模型句柄）。

- **`cv_course/algorithms/hist_vis.py`**  
  直方图相关绘制与辅助。

- **`cv_course/ui_tk/__init__.py`**  
  Tk 子包占位。

- **`cv_course/ui_tk/app.py`**  
  Tk 主窗口：菜单、工具栏、画布与卡牌网格、视频控制条、日志、设置对话框、录制与模式切换等。

- **`cv_course/ui_tk/toolbar_icons.py`**  
  工具栏位图资源构建。

- **`cv_course/ui_tk/algorithm_picker.py`**  
  按子类勾选展示算法的对话框。

- **`cv_course/ui_streamlit/__init__.py`**  
  Streamlit 子包占位。

- **`cv_course/ui_streamlit/app.py`**  
  Streamlit 多页应用：上传图像、参数侧栏、图像结果预览、视频算法文字页。

- **`cv_course/tools/__init__.py`**  
  工具子包占位；删除同目录维护脚本后建议保留本文件。

版本与联系方式见程序内 **关于** 菜单。

---

## English

OpenCV teaching utility with **Tkinter** as the main UI and an optional **Streamlit** front-end (image demos; video tab is text-only). Flip cards show outputs on the front and teaching prose on the back (loaded from packaged data; restart or language toggle may reload). For offline reading, open **`docs/algorithms.md`**.

### Features

| Area           | Notes                                                                                                                                                             |
| -------------- | ----------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| Images         | Load/save BGR; one card per enabled operator.                                                                                                                     |
| Video / camera | Shared timeline; play/pause; seek on files only. Separate MeanShift / CamShift state. Windows camera prefers DirectShow and requests 640×480 plus a small buffer. |
| YOLO           | Ultralytics; default `yolo11n.pt`.                                                                                                                                |
| Drawing        | Whiteboard; exclusive with other modes.                                                                                                                           |
| Language       | English by default; Settings → Language.                                                                                                                          |
| Log            | After first operation; filter by level.                                                                                                                           |

### Install & run

Python 3.10+, `pip install -r requirements.txt`. Run `python -m cv_course` or `streamlit run cv_course/ui_streamlit/app.py`.

### Editing teaching copy

Edit **`cv_course/data/algo_descriptions.csv`** (UTF-8, BOM allowed): columns `algorithm_id`, `lang`, `title`, `principle`, `function_desc`, `example`, `usage_py`, optional `extension`. Override path with **`CV_COURSE_ALGO_CSV`** if needed. Restart the app (or use the language toggle where applicable) after changes.

### Repository layout

```
c_course/
├── README.md
├── requirements.txt
├── cv_course_demo.md
├── PACKAGING_OMIT.md
├── algorithms.md
├── __init__.py
├── __main__.py
├── util_cv.py
├── state.py
├── i18n.py
├── algo_descriptions.py
├── algo_text_en.py
├── algo_doc_layout.py
├── md_plain.py
├── md_html.py
├── edu_merge.py
├── data/
│   └── algo_descriptions.csv
├── algorithms/
│   ├── __init__.py
│   ├── registry.py
│   ├── subcategories.py
│   ├── image_handlers.py
│   ├── video_handlers.py
│   └── hist_vis.py
├── ui_tk/
│   ├── __init__.py
│   ├── app.py
│   ├── toolbar_icons.py
│   └── algorithm_picker.py
└─ ui_streamlit/
    ├── __init__.py
    └── app.py
```

The three scripts under `cv_course/tools/` (excluding `__init__.py`) are optional for deployment; see **`PACKAGING_OMIT.md`**. The following file notes mirror the Chinese section and omit per-script detail for those three.

### File notes

- **`README.md`** — This document.  
- **`requirements.txt`** — Pip dependencies.  
- **`cv_course_demo.md`** — Legacy design notes.  
- **`PACKAGING_OMIT.md`** — What to strip from a release tarball; you may delete this file itself when publishing.  
- **`docs/algorithms.md`** — Offline algorithm reference (Chinese then English by id).  
- **`cv_course/__init__.py`** — Package version.  
- **`cv_course/__main__.py`** — Launches the Tk app (`python -m cv_course`).  
- **`cv_course/util_cv.py`** — BGR/RGB helpers, PhotoImage conversion, sizing.  
- **`cv_course/state.py`** — App state objects and layout settings.  
- **`cv_course/i18n.py`** — UI string tables.  
- **`cv_course/algo_descriptions.py`** — Loads teaching copy for cards (default CSV path, reload on language change).  
- **`cv_course/algo_text_en.py`** — Static English titles and similar maps.  
- **`cv_course/algo_doc_layout.py`** — Normalizes doc sections for display.  
- **`cv_course/md_plain.py`** — Markdown to plain text (fallback card back).  
- **`cv_course/md_html.py`** — Markdown/HTML helpers for TkinterWeb.  
- **`cv_course/edu_merge.py`** — Text enrichment helpers used only by `cv_course/tools` maintenance scripts, not by the runtime UI.  
- **`cv_course/data/algo_descriptions.csv`** — Teaching copy source for titles and card backs.  
- **`cv_course/algorithms/__init__.py`** — Subpackage marker.  
- **`cv_course/algorithms/registry.py`** — Algorithm specs and `apply_image_algorithm` / `apply_video_algorithm`.  
- **`cv_course/algorithms/subcategories.py`** — Subgroup labels for the picker UI.  
- **`cv_course/algorithms/image_handlers.py`** — Image operator implementations.  
- **`cv_course/algorithms/video_handlers.py`** — Video operators and `VideoEngine`.  
- **`cv_course/algorithms/hist_vis.py`** — Histogram helpers.  
- **`cv_course/ui_tk/__init__.py`** — Tk subpackage marker.  
- **`cv_course/ui_tk/app.py`** — Main Tk window and behavior.  
- **`cv_course/ui_tk/toolbar_icons.py`** — Toolbar images.  
- **`cv_course/ui_tk/algorithm_picker.py`** — Subgroup algorithm picker dialog.  
- **`cv_course/ui_streamlit/__init__.py`** — Streamlit subpackage marker.  
- **`cv_course/ui_streamlit/app.py`** — Streamlit pages.  
- **`cv_course/tools/__init__.py`** — Keep when removing other files under `tools/`.

Version and contact: **About** in the Tk app.
