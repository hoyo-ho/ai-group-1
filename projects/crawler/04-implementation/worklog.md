# 通用爬虫工具完善 - 实施记录

## 任务概述
根据设计文档和评审意见，实现完整的爬虫工具。

## 实施时间
2026-03-15

## 1. 评审问题修复

### 问题
- 百度百科优先级冲突：WikiExtractor 和 BaiduExtractor 都支持 baike.baidu.com

### 修复
- 将 `WikiExtractor` 优先级提高到 90（最高优先级）
- 在 `src/extractors/__init__.py` 中按优先级排序选择提取器

```python
# 优先级配置
WikiExtractor:      # Priority 90 - handles baike.baidu.com, wikipedia.org
DouyinExtractor:    # Priority 85 - Douyin/TikTok China
BilibiliExtractor:  # Priority 80 - Bilibili video
BaiduExtractor:     # Priority 70 - Baidu search results
QuarkExtractor:     # Priority 65 - Quark search/cloud
SohuExtractor:      # Priority 60 - Sohu search/article
GeneralExtractor:   # Priority 10 - general web pages
```

## 2. 代码结构拆分

### 原结构
```
src/
  extractors.py  # 单一文件包含所有提取器
```

### 新结构
```
src/extractors/
  __init__.py       # 导出和注册逻辑，优先级匹配
  base.py           # BaseExtractor, ExtractionResult
  general.py        # GeneralExtractor
  bilibili.py       # BilibiliExtractor
  douyin.py         # DouyinExtractor (新增)
  baidu.py          # BaiduExtractor
  sohu.py           # SohuExtractor (新增)
  quark.py          # QuarkExtractor (新增)
  wiki.py           # WikiExtractor
```

## 3. 新增提取器

### DouyinExtractor (抖音)
- 优先级: 85
- 支持域名: douyin.com, www.douyin.com, live.douyin.com
- 特点: 必须使用 Playwright 进行 JavaScript 渲染
- 功能:
  - 提取视频标题、描述
  - 提取作者信息
  - 提取视频统计（点赞、评论、分享）
  - 提取音乐信息
  - 提取封面图片

### SohuExtractor (搜狐搜索)
- 优先级: 60
- 支持域名: sohu.com, www.sohu.com, search.sohu.com, m.sohu.com
- 功能:
  - 搜索结果提取
  - 文章内容提取
  - 作者信息提取
  - 发布时间提取
  - 相关推荐提取

### QuarkExtractor (夸克搜索)
- 优先级: 65
- 支持域名: quark.cn, www.quark.cn, search.quark.cn, pan.quark.cn
- 功能:
  - 搜索结果提取
  - 网盘文件列表提取
  - 内容页面提取

## 4. 主程序更新

### 新增参数
```bash
--site {wiki,baike,baidu,bilibili,douyin,sohu,quark,general}
```

### 输出目录
- 默认输出: `~/Downloads/crawler/output`
- 使用 `-d downloads` 可切换到 `~/Downloads`

### 自动识别
- 基于 URL 自动检测网站类型
- Douyin 自动启用 Playwright

## 5. 验证测试

### 测试命令

#### GitHub
```bash
python3 main.py "https://github.com" -f json
# 结果: ✅ 成功 - 使用 GeneralExtractor
```

#### 百度搜索
```bash
python3 main.py "https://www.baidu.com/s?wd=python" -f json
# 结果: ✅ 成功 - 使用 BaiduExtractor
```

#### Bilibili
```bash
python3 main.py "https://www.bilibili.com/video/BV1xx411c7XD" -f json -p
# 结果: ✅ 成功 - 使用 BilibiliExtractor
```

#### 手动指定网站类型
```bash
python3 main.py "https://example.com" --site wiki -f json
# 结果: ✅ 成功 - 强制使用 WikiExtractor
```

### 提取器检测验证
```
https://github.com/test -> GeneralExtractor
https://www.bilibili.com/video/BV1234567890 -> BilibiliExtractor
https://baike.baidu.com/item/Test -> WikiExtractor (优先级90)
https://www.baidu.com/s?wd=test -> BaiduExtractor (优先级70)
https://www.douyin.com/video/123456 -> DouyinExtractor (优先级85)
https://www.sohu.com/test -> SohuExtractor (优先级60)
https://quark.cn/search?q=test -> QuarkExtractor (优先级65)
```

## 6. 文件变更

### 新增文件
- `src/extractors/__init__.py` - 提取器注册和选择逻辑
- `src/extractors/base.py` - 基础类和接口
- `src/extractors/douyin.py` - 抖音提取器
- `src/extractors/sohu.py` - 搜狐提取器
- `src/extractors/quark.py` - 夸克提取器
- `src/extractors/wiki.py` - 百科提取器
- `src/extractors/baidu.py` - 百度提取器
- `src/extractors/bilibili.py` - B站提取器
- `src/extractors/general.py` - 通用提取器

### 修改文件
- `main.py` - 添加 --site 参数
- `src/crawler.py` - 支持 site_type 参数和自动 Playwright
- `src/config.py` - 修改输出目录为 ~/Downloads/crawler/output

### 备份文件
- `src/extractors.py.bak` - 原提取器文件备份

## 7. 已知问题

1. Baidu Baike (baike.baidu.com) 返回 403 错误
   - 原因: 百度百科反爬虫机制
   - 建议: 需要使用代理或 Cookie 认证

## 8. 下一步

1. 完善 DouyinExtractor - 需要实际测试 Playwright 渲染
2. 添加更多提取器测试
3. 优化提取逻辑
