# Auto Mind Map 项目架构

## 1. 系统架构图

```
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                    用户界面层                                    │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                          index.html (单页应用)                           │   │
│  │  ┌──────────────┐  ┌──────────────────────────────────┐  ┌───────────┐   │   │
│  │  │   Controls   │  │          Graph Container        │  │  Sidebar  │   │
│  │  │  - dirPath   │  │                                  │  │  - 参数设置│   │
│  │  │  - analyzeBtn│  │        D3.js Force Graph        │  │  - 文档选择│   │
│  │  │  - saveBtn   │  │                                  │  │  - 节点详情│   │
│  │  │  - loadBtn   │  │                                  │  │  - 保存列表│   │
│  │  └──────────────┘  └──────────────────────────────────┘  └───────────┘   │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        │ HTTP/REST
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                  FastAPI 服务层                                  │
│  ┌─────────────────────────────────────────────────────────────────────────┐   │
│  │                              app/main.py                                │   │
│  │                                                                          │   │
│  │  GET  /              → 返回 index.html                                   │   │
│  │  POST /api/analyze   → 分析文档目录，返回图数据                           │   │
│  │  POST /api/save      → 保存图到 output/ 目录                             │   │
│  │  GET  /api/load      → 从 output/ 目录加载图                              │   │
│  │  GET  /api/files     → 列出已保存的图文件                                 │   │
│  │                                                                          │   │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌────────────────┐  │   │
│  │  │  parser.py  │  │ analyzer.py │  │ schemas.py  │  │ output/*.json  │  │   │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └────────────────┘  │   │
│  └─────────────────────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                   数据处理层                                     │
│                                                                                  │
│  ┌─────────────────────────────┐    ┌──────────────────────────────────────┐   │
│  │       parser.py              │    │            analyzer.py               │   │
│  │                             │    │                                       │   │
│  │  parse_markdown_files()     │    │  compute_simple_similarity()         │   │
│  │  └─ parse_single_file()     │    │  (Jaccard 关键词重叠)                 │   │
│  │       │                     │    │                                       │   │
│  │       ▼                     │    │  compute_tfidf_cosine_similarity()   │   │
│  │  Block(id, doc_path,        │    │  (TF-IDF + Cosine)                   │   │
│  │         title, content,     │    │                                       │   │
│  │         level, parent_id)    │    │  compute_similarity_with_claude()    │   │
│  │                             │    │  (Claude Embeddings API)              │   │
│  └─────────────────────────────┘    └──────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
                                        │
                                        ▼
┌─────────────────────────────────────────────────────────────────────────────────┐
│                                    文件系统                                     │
│                                                                                  │
│  ┌─────────────────────────────┐    ┌──────────────────────────────────────┐   │
│  │   data/*.md                  │    │  output/*.json                       │   │
│  │   (Markdown 源文档)           │    │  (保存的图数据)                        │   │
│  └─────────────────────────────┘    └──────────────────────────────────────┘   │
│                                                                                  │
└─────────────────────────────────────────────────────────────────────────────────┘
```

## 2. 前端架构 (static/)

### 2.1 文件结构

```
static/
├── index.html    # 主页面 HTML
├── style.css     # 样式表
└── graph.js      # D3.js 可视化逻辑
```

### 2.2 HTML 结构

```
index.html
├── header (标题)
├── controls (控制面板)
│   ├── dirPath (文档目录输入)
│   ├── analyzeBtn (分析按钮)
│   ├── saveBtn (保存按钮)
│   └── loadBtn (加载按钮)
├── stats (统计信息)
├── main-content
│   ├── graph-container (D3.js 画布)
│   │   └── #graph
│   └── sidebar
│       ├── 参数设置 (threshold, algorithm, tooltipOffset, parentDepth)
│       ├── 文档选择 (docSelector)
│       ├── 节点详情 (nodeDetail)
│       └── 保存的图表 (savedFiles)
└── loading (加载遮罩)
```

### 2.3 graph.js 核心模块

| 模块 | 职责 |
|------|------|
| `currentGraph` | 当前图数据缓存 |
| `simulation` | D3 力导向模拟器 |
| `selectedNodeId` | 当前选中的节点 ID |
| `selectedDocs` | 选中的文档集合 |
| `renderGraph()` | 渲染力导向图 |
| `buildDocSelector()` | 构建文档选择器 |
| `showNodeDetail()` | 显示节点详情 |

### 2.4 节点渲染机制

每个节点用三层同心圆表示：

```
     ┌─────────────────┐
     │   外圈 (白)      │  ← 选中状态指示
     │  ┌───────────┐  │
     │  │ 中圈 (彩)  │  │  ← 文档颜色
     │  │ ┌─────┐  │  │
     │  │ │内圈 │  │  │  ← 层级颜色
     │  │ └─────┘  │  │
     │  └───────────┘  │
     └─────────────────┘
```

| 层级 | 颜色 |
|------|------|
| 0 (顶级段落) | #6366f1 靛蓝 |
| 1 (# 标题) | #8b5cf6 紫色 |
| 2 (## 标题) | #06b6d4 青色 |
| 3 (### 标题) | #10b981 绿色 |
| 4 (#### 标题) | #f59e0b 琥珀 |
| 5 (##### 标题) | #ef4444 红色 |
| 6 (###### 标题) | #ec4899 粉色 |

## 3. 后端架构 (app/)

### 3.1 API 端点

| 方法 | 路径 | 描述 |
|------|------|------|
| GET | `/` | 返回 index.html |
| POST | `/api/analyze` | 分析文档目录 |
| POST | `/api/save` | 保存图数据 |
| GET | `/api/load` | 加载图数据 |
| GET | `/api/files` | 列出已保存的图 |

### 3.2 核心数据模型

**Block (parser.py)**
```python
class Block(BaseModel):
    id: str              # 格式: "doc_path:block:N"
    doc_path: str        # 相对路径
    chapter_index: int   # 章索引
    section_index: int   # 节索引
    title: str           # 标题文本
    content: str         # 完整内容
    start_line: int      # 起始行号
    end_line: int        # 结束行号
    level: int           # 标题级别 (0-6)
    parent_id: str       # 父块 ID
```

**Relation (analyzer.py)**
```python
class Relation(BaseModel):
    source: str    # 源块 ID
    target: str    # 目标块 ID
    score: float   # 相似度分数
```

### 3.3 相似度算法

#### Jaccard (默认)
- 基于关键词重叠度
- 停用词过滤
- 适合快速原型

#### TF-IDF Cosine
- 使用 sklearn 的 TfidfVectorizer
- 计算文本向量余弦相似度
- 支持 bigram

#### Claude API
- 使用 Anthropic Embeddings API
- 需要设置 `ANTHROPIC_API_KEY` 环境变量
- 提供语义级别的相似度

## 4. 数据流

```
用户输入目录
     │
     ▼
parse_markdown_files()  ──→  Block[]
     │
     ▼
analyze_blocks_*()  ──→  nodes[], edges[]
     │
     ▼
Graph = {nodes, edges, metadata}
     │
     ├──→ 返回给前端 (JSON)
     │
     ▼
D3.js renderGraph()  ──→  SVG 力导向图
```

## 5. 文件组织

```
AutoMindMap/
├── app/
│   ├── __init__.py
│   ├── main.py       # FastAPI 应用入口
│   ├── parser.py     # Markdown 解析
│   ├── analyzer.py   # 相似度计算
│   └── schemas.py    # Pydantic 数据模型
├── static/
│   ├── index.html    # 前端页面
│   ├── style.css     # 样式
│   └── graph.js      # D3.js 可视化
├── data/             # Markdown 文档目录
│   └── demo/         # 示例文档
├── output/           # 保存的图数据
├── docs/             # 项目文档
├── requirements.txt  # Python 依赖
├── README.md         # 项目说明
└── SPEC.md           # 功能规格
```

## 6. 关键设计决策

### 6.1 父子关系
- 每个块记录 `parent_id`，指向直接父标题
- 构建树状层级结构
- 渲染时用实线连接

### 6.2 文档颜色稳定性
- `docColors` 对象全局维护
- 只在首次遇到文档时分配颜色
- 不在重渲染时重置

### 6.3 节点筛选
- `selectedDocs` 跟踪选中的文档
- 筛选时保留：选中文档的节点 + 超过阈值的关联节点
- 通过 `visibleLinks` 过滤确保边的端点都可见
