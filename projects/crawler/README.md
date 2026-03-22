# 🕷️ Universal Web Crawler

通用网页爬虫框架，支持从代码开源网站、图片开源网站和通用网页提取内容。

## 功能特性

- 🌐 支持多种网站类型：
  - 代码开源网站（GitHub）
  - 图片开源网站（Unsplash, Pexels, Pixabay 等）
  - 通用网页
- 📝 内容提取：
  - 标题 + 正文
  - 图片下载链接
  - 元数据（描述、作者、发布时间等）
- 💾 多种导出格式：
  - JSON
  - CSV
  - Markdown
  - PDF（通过 Markdown）
  - PNG/JPG（图片下载）
- ⚡ JavaScript 渲染支持（通过 Playwright）
  - 支持 Bilibili、抖音、微博等动态网站

## 环境配置

### 使用 Conda

```bash
# 创建环境
conda env create -f environment.yml

# 激活环境
conda activate crawler
```

### 使用 pip

```bash
python3 -m pip install -r requirements.txt
```

### 依赖兼容说明

- `requirements.txt` 会自动加载 `constraints.txt`，约束 `requests / urllib3 / charset-normalizer / chardet` 的兼容区间。
- 如果你把 crawler 和其他抓取工具装在同一个 Python 解释器里，优先用独立虚拟环境；否则某些包升级后可能重新触发 `RequestsDependencyWarning`。

## 使用方法

### 命令行

```bash
# 基本用法
python main.py <URL>

# 指定导出格式
python main.py <URL> -f json csv markdown

# 指定输出文件名
python main.py <URL> -f json -o my_output

# 输出到 ~/Downloads
python main.py <URL> -f json -d downloads

# 使用 Playwright 渲染 JavaScript 页面（B站、抖音等）
python main.py <URL> -f json --playwright

# 查看支持的格式
python main.py --list-formats
```

### 示例

```bash
# 爬取通用网页
python main.py https://example.com -f json

# 爬取 GitHub 仓库
python main.py https://github.com/python/cpython -f json markdown

# 爬取图片网站
python main.py https://unsplash.com -f json
```

### Python API

```python
from src.crawler import crawl

# 简单用法
result = crawl("https://example.com", formats=["json"])

# 获取详细结果
result = crawl(
    url="https://example.com",
    formats=["json", "csv", "markdown"],
    filename="my_crawl",
    output_dir=None  # 默认项目 output 目录
)

print(result["content"]["title"])
print(result["exports"])
```

## 项目结构

```
crawler/
├── src/
│   ├── __init__.py
│   ├── config.py       # 配置
│   ├── crawler.py      # 爬虫核心
│   ├── extractors.py   # 内容提取器
│   └── exporters.py   # 导出器
├── output/             # 爬取结果输出目录
├── tests/             # 测试目录
├── main.py            # CLI 入口
├── environment.yml    # Conda 环境配置
├── requirements.txt   # pip 依赖
└── README.md
```

## 输出路径

- 项目目录：`~/ai-group-1/projects/crawler/`（只包含代码）
- 爬取结果：`~/Downloads/crawler-output/`
- Downloads：`~/Downloads/`

## TODO

- [x] 添加 Playwright 支持（JavaScript 渲染页面）
- [ ] 添加代理支持
- [ ] 添加爬取速率限制
- [ ] 添加更多网站专用提取器
- [ ] 添加 PDF 真正生成（使用 weasyprint）
- [ ] 添加批量爬取功能
