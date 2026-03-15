# 设计方案评审报告

**任务ID**: crawler-enhancement  
**方案版本**: v1.0  
**评审角色**: Calamitas (代码侦察员)  
**评审时间**: 2026-03-15

---

## 评审结论

| 评审项 | 结论 |
|--------|------|
| 1. 架构可行性 | ✓ 通过 |
| 2. 数据模型完整性 | ✓ 通过 |
| 3. 实现难度 | ✓ 通过 |
| 4. 测试覆盖度 | ✓ 通过 |
| 5. 风险点 | ⚠️ 需关注 |

---

## 逐项评审

### 1. 架构可行性 - 提取器接口、注册机制是否合理 ✓ 通过

**通过理由**:
- `BaseExtractor` 基类设计清晰，抽象方法 `extract()` 定义明确
- `pre_validate()` 钩子设计合理，支持域名匹配后的二次确认
- `ExtractorRegistry` 注册机制完善：支持精确匹配、域名匹配、通配符匹配、优先级排序
- `ExtractionResult` 数据类设计完整，字段覆盖全面
- 旧接口 `get_extractor()` 保持兼容，符合不可破坏项要求

---

### 2. 数据模型完整性 - 是否覆盖各类网站 ✓ 通过

| 网站类型 | 覆盖情况 |
|----------|----------|
| 视频网站（封面图、视频、文字） | ✓ DouyinExtractor, BilibiliExtractor |
| 非视频网站（图片、文字） | ✓ ImageExtractor, WikiExtractor |
| 搜索/百科 | ✓ BaiduExtractor, WikiExtractor |
| 新闻/文章 | ✓ SohuExtractor |

**字段覆盖**:
- `videos`: url, cover, duration, format
- `images`: url, alt, type
- `content`: 主文本内容
- `meta`: description, author, published_time
- `extra`: 站点特定扩展数据

---

### 3. 实现难度 - 各提取器实现复杂度评估 ✓ 通过

| 提取器 | 复杂度 | 说明 |
|--------|--------|------|
| DouyinExtractor | 中 | 正则提取视频数据，需 Playwright |
| BaiduExtractor | 中 | 多模式 (搜索/百科/知道) 适配 |
| SohuExtractor | 低 | 静态 HTML，BeautifulSoup 即可 |
| QuarkExtractor | 中 | 待验证 JS 需求 |
| WikiExtractor | 中 | 多站点适配 |

---

### 4. 测试覆盖度 - 测试用例是否足够 ✓ 通过

- **正常场景**: 10 个测试用例覆盖主流站点
- **边界条件**: 空 HTML、无效 URL、404、超大页面、特殊字符、无内容页面、重定向、二进制内容
- **回归测试**: 提供检查清单验证旧接口兼容

---

### 5. 风险点 - 潜在问题 ⚠️ 需关注

| 风险项 | 风险等级 | 建议 |
|--------|----------|------|
| 抖音反爬 | 中 | 已预留 Playwright 方案 |
| 百度搜索 AJAX 加载 | 中 | 文档建议默认启用 Playwright |
| 夸克 JS 需求待验证 | 低 | 方案已标注"需验证" |
| 百度百科匹配冲突 | **高** | 见下方 ✗ |

---

## 需修改项 ✗

### 问题 1: 百度百科匹配冲突

**问题描述**:
- `BaiduExtractor` 注册为 `baidu.com` (优先级 80)
- `WikiExtractor` 也注册了 `baike.baidu.com` (优先级 70)
- 由于优先级设置，`baike.baidu.com` 会先被 `BaiduExtractor` (80) 匹配，而非 `WikiExtractor` (70)

**影响**:
- 百度百科词条会路由到 `BaiduExtractor` 而非 `WikiExtractor`
- 百度百科的提取逻辑在 `BaiduExtractor._extract_baike()` 中已有实现，与 `WikiExtractor._extract_baidu_baike()` 存在功能重复
- 但 `WikiExtractor` 的 `_extract_baidu_baike()` 更专业，可能导致百度百科提取效果不如预期

**建议修改**:
```python
# 方案 A: 提高 WikiExtractor 的 baike.baidu.com 优先级
@register_extractor("baike.baidu.com", priority=90, match_type="domain")
class WikiExtractor(BaseExtractor):
    ...

# 方案 B: 在 BaiduExtractor.pre_validate() 中排除百科页面
def pre_validate(self, url: str, html: str) -> bool:
    from urllib.parse import urlparse
    parsed = urlparse(url)
    
    # 百度百科由 WikiExtractor 处理
    if "baike.baidu.com" in parsed.netloc:
        return False  # 拒绝匹配，由 WikiExtractor 处理
    
    # 继续原有逻辑...
```

**推荐方案 A**，简单直接，避免逻辑侵入。

---

### 问题 2: 夸克搜索 NEEDS_JAVASCRIPT 待验证

**问题描述**:
- 方案中 `QuarkExtractor` 设置 `NEEDS_JAVASCRIPT = True`，但注释标明"需验证"

**建议**:
- 实施阶段先设为 `False`，实际验证后再调整
- 或者保持 `True` 作为安全降级方案

---

## 风险项 ⚠️

### 风险 1: 抖音反爬机制

- **描述**: 抖音视频页面可能有验证码、IP 限流、签名验证等反爬措施
- **缓解**: 方案已包含 Playwright + 代理建议

### 风险 2: 页面结构变更

- **描述**: 各站点页面结构可能随版本更新变化，导致提取逻辑失效
- **缓解**: 方案预留 `pre_validate()` 机制，可快速适配

### 风险 3: 性能瓶颈

- **描述**: 多个 `NEEDS_JAVASCRIPT=True` 的站点并发抓取时，Playwright 开销较大
- **缓解**: 方案建议考虑异步机制

---

## 验收结论

| 类别 | 数量 |
|------|------|
| ✓ 通过项 | 4 |
| ✗ 需修改项 | 1 |
| ⚠️ 风险项 | 3 |

**总体结论**: 方案设计良好，**需修改 1 处后通过**

**修改要求**:
1. 修复百度百科匹配冲突：将 `WikiExtractor` 对 `baike.baidu.com` 的优先级提高到 90，或在 `BaiduExtractor.pre_validate()` 中排除百科页面

---

*评审完成 - 返回 solin 修订*
