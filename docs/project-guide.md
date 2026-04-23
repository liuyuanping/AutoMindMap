# Auto Mind Map 详细解读

## 项目概述

Auto Mind Map 是一个文档关系分析与可视化工具，通过递归扫描 Markdown 文件、提取内容块、计算块之间的语义相似度，最终以力导向图形式展示文档间的关联关系。

## 核心功能流程

```
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  文档目录    │───▶│  Markdown  │───▶│   分块      │───▶│  相似度    │
│  (data/)    │    │   解析      │    │  (blocks)   │    │  计算       │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
                                                               │
                                                               ▼
┌─────────────┐    ┌─────────────┐    ┌─────────────┐    ┌─────────────┐
│  力导向图    │◀───│  JSON 图    │◀───│   图数据    │◀───│  节点/边    │
│  可视化      │    │   输出      │    │  构建       │    │  生成       │
└─────────────┘    └─────────────┘    └─────────────┘    └─────────────┘
```

## 分块机制 (parser.py)

### 分块策略

每个 Markdown 文件被分解为以下类型的块：

1. **顶级段落块** - 文件开头到第一个标题之间的内容
2. **标题块** - 每个 `#` 到 `######` 标题及其内容
3. **段落块** - 标题下的连续非空段落

### 块的数据结构

```python
Block(
    id="data/demo/ai-history-simple.md:block:5",
    doc_path="data/demo/ai-history-simple.md",
    chapter_index=3,        # 第3章
    section_index=0,
    title="深度学习革命",    # 标题文本
    content="神经网络自1950...",  # 从标题行到下一同级标题之前
    start_line=53,
    end_line=65,
    level=1,               # 1 = # 标题
    parent_id="data/demo/ai-history-simple.md:block:2"  # 第一章的块
)
```

### 父子关系构建

```python
# 伪代码：找父标题
for idx, title in enumerate(titles):
    for pidx in range(idx - 1, -1, -1):
        if titles[pidx]['level'] < title['level']:
            parent_id = title_to_block_id[pidx]
            break
```

这确保了：
- `# 标题` 的父标题是顶级段落块
- `## 标题` 的父标题是 `# 标题`
- `### 标题` 的父标题是 `## 标题`
- 以此类推

## 相似度算法 (analyzer.py)

### Jaccard 算法

```python
def compute_simple_similarity(blocks):
    # 1. 提取关键词
    keywords_i = set(text.lower().split()) - stopwords

    # 2. 计算 Jaccard 系数
    score = |keywords_i ∩ keywords_j| / |keywords_i ∪ keywords_j|

    # 3. 阈值过滤
    if score >= threshold:
        relations.append(...)
```

**特点**：
- 计算速度快
- 基于词形重叠
- 无法捕捉语义相似性

### TF-IDF Cosine 算法

```python
def compute_tfidf_cosine_similarity(blocks):
    # 1. 构建 TF-IDF 向量
    vectorizer = TfidfVectorizer(ngram_range=(1, 2))
    tfidf_matrix = vectorizer.fit_transform(texts)

    # 2. 计算余弦相似度矩阵
    similarity_matrix = cosine_similarity(tfidf_matrix)

    # 3. 提取边
    for i, j in combinations(range(n), 2):
        if similarity_matrix[i][j] >= threshold:
            relations.append(...)
```

**特点**：
- 考虑词频和逆文档频率
- bigram 捕捉短语
- 比 Jaccard 更准确

### Claude API 算法

```python
async def compute_similarity_with_claude(blocks):
    # 1. 获取文本嵌入
    for text in texts:
        embedding = await client.embeddings.create(
            model="embed-english-v2.0",
            input=text[:8192]
        )

    # 2. 计算余弦相似度
    for i, j in combinations(range(n), 2):
        score = cosine_similarity(embeddings[i], embeddings[j])
        if score >= threshold:
            relations.append(...)
```

**特点**：
- 基于语义理解
- 效果最好
- 需要 API Key，有成本

## 可视化原理 (graph.js)

### D3.js 力导向图

```javascript
simulation = d3.forceSimulation(visibleNodes)
    .force('link', d3.forceLink(visibleLinks).id(d => d.id).distance(...))
    .force('charge', d3.forceManyBody().strength(-200))  // 节点互斥
    .force('center', d3.forceCenter(width / 2, height / 2))  // 向中心吸引
    .force('collision', d3.forceCollide().radius(30))  // 防止重叠
```

**力导向图物理模拟**：
- **中心力** - 所有节点被拉向画布中心
- **电荷力** - 节点之间互相排斥（避免重叠）
- **链接力** - 相连的节点被弹簧拉扯（保持距离）
- **碰撞力** - 防止节点重叠

### 边类型区分

| 边类型 | 样式 | 来源 |
|--------|------|------|
| 父子边 | 实线，灰色 #888 | parent_id 关系 |
| 相似度边 | 虚线，紫色 #667eea | 相似度计算 |

### 节点三层圆

```
       ┌───────────────────────┐
       │      外圈 (白)         │  opacity 变化表示选中状态
       │    ┌───────────┐     │
       │    │  中圈 (彩) │     │  docColor - 文档颜色
       │    │ ┌───────┐ │     │
       │    │ │内圈   │ │     │  getNodeColor(level) - 层级颜色
       │    │ └───────┘ │     │
       │    └───────────┘     │
       └───────────────────────┘
```

### 文档筛选逻辑

```javascript
// 筛选条件：
// 1. 选中文档的节点必须显示
// 2. 未选中文档的节点：只有当它与选中节点有相似度边且分数 >= 阈值时才显示
if (selectedDocs.size < totalDocs) {
    const selectedDocNodes = new Set(selectedDocs中的节点IDs);

    // 找出通过相似度边连接的未选中文档节点
    edges.forEach(e => {
        if (e.score >= threshold) {
            if (selectedDocNodes.has(e.source)) thresholdConnected.add(e.target);
            if (selectedDocNodes.has(e.target)) thresholdConnected.add(e.source);
        }
    });

    visibleNodes = nodes.filter(n =>
        selectedDocNodes.has(n.id) || thresholdConnected.has(n.id)
    );
}
```

## API 设计 (app/main.py)

### POST /api/analyze

**请求**：
```json
{
    "dir_path": "data/demo",
    "threshold": 0.3,
    "algorithm": "jaccard"
}
```

**响应**：
```json
{
    "blocks": [...],
    "relations": [...],
    "graph": {
        "nodes": [
            {
                "id": "data/demo/ai-history-simple.md:block:5",
                "doc_path": "data/demo/ai-history-simple.md",
                "title": "深度学习革命",
                "level": 1,
                "parent_id": "...",
                "content": "...",
                "start_line": 53,
                "end_line": 65
            }
        ],
        "edges": [
            {
                "source": "data/demo/ai-history-simple.md:block:5",
                "target": "data/demo/ai-application-simple.md:block:12",
                "score": 0.342
            }
        ],
        "metadata": {
            "created_at": "2026-04-23T10:30:00",
            "doc_count": 2,
            "block_count": 401,
            "algorithm": "jaccard"
        }
    }
}
```

## 状态管理 (graph.js)

| 变量 | 作用域 | 用途 |
|------|--------|------|
| `currentGraph` | 全局 | 缓存当前图数据 |
| `simulation` | 全局 | D3 力模拟实例 |
| `selectedNodeId` | 全局 | 当前选中的节点 |
| `selectedDocs` | 全局 | 选中的文档集合 |
| `docColors` | 全局 | 文档→颜色映射（持久） |

## 依赖分析

### Python 依赖

| 包 | 用途 |
|----|------|
| fastapi | Web 框架 |
| uvicorn | ASGI 服务器 |
| pydantic | 数据验证 |
| sklearn | TF-IDF 向量化 |
| httpx | Claude API 请求 |

### 前端依赖

| 库 | 用途 |
|----|------|
| D3.js v7 | 力导向图可视化 |
| Marked.js | Markdown 渲染 |

## 使用场景

1. **技术文档分析** - 分析多个相关文档之间的关系
2. **知识图谱构建** - 从文档集合提取知识点关联
3. **内容去重** - 发现相似内容
4. **文档推荐** - 基于相似度推荐相关文档
5. **代码审查** - 分析代码结构关系
