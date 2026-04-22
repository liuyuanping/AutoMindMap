# Document Mind Map - 文档关系分析软件

## 1. 项目概述

- **项目名称**: Document Mind Map
- **类型**: 文档分析与可视化工具
- **核心功能**: 递归读取目录下所有.md文档，提取文档块并分析块之间的相关性，生成关系图
- **目标用户**: 需要分析文档结构和关系的用户

## 2. 功能需求

### 2.1 文档读取
- 递归读取指定目录下的所有.md文件
- 解析文档内容，提取块结构
- 记录每个块的元信息：文档路径、块编号、起始行号、结束行号

### 2.2 块结构定义
- **大块 (Chapter)**: 顶级标题下的内容区域（# 标题）
- **小块 (Section)**: 大块内的子标题区域（## 及以下标题）或独立段落
- 层级关系：大块包含小块
- 块ID格式：`{文档相对路径}:{大块序号}.{小块序号}`

### 2.3 相关度计算
- 算法选项：
  1. **余弦相似度**: 基于TF-IDF向量化
  2. **语义相似度**: 基于句子嵌入(可选，需API支持)
- 可调节阈值：0.0 ~ 1.0，默认0.3
- 相关度计算时：大大块、大小块、小块、小块均可互相比

### 2.4 关系图生成
- 节点：每个块（显示文档名+块标题）
- 边：相关度超过阈值的块之间的连接
- 边的权重：相关度数值

### 2.5 Web展示
- 使用D3.js力导向图或类似库
- 节点可点击查看详情
- 边可显示相关度数值
- 支持缩放、拖拽

### 2.6 数据持久化
- 导出：保存关系图为JSON文件
- 导入：从本地JSON文件加载关系图

## 3. 技术栈

- **后端**: Python (FastAPI)
- **前端**: HTML + JavaScript (D3.js)
- **文本分析**: scikit-learn (TF-IDF + 余弦相似度)
- **数据存储**: JSON

## 4. 项目结构

```
/home/ubuntu/github/AutoMindMap/
├── app/
│   ├── main.py           # FastAPI入口
│   ├── parser.py         # 文档解析器
│   ├── analyzer.py       # 相关度分析器
│   └── schemas.py        # 数据模型
├── static/
│   ├── index.html        # 前端页面
│   ├── graph.js          # 图形渲染
│   └── style.css         # 样式
├── data/                 # 测试文档目录
├── output/               # 输出目录
└── requirements.txt
```

## 5. API 设计

### GET /
- 返回前端页面

### POST /api/analyze
- 请求体: `{ "dir_path": string, "threshold": float }`
- 响应: `{ "blocks": [...], "relations": [...], "graph": {...} }`

### POST /api/save
- 请求体: `{ "graph": {...}, "filename": string }`
- 响应: `{ "success": true, "path": string }`

### GET /api/load?path={path}
- 响应: `{ "graph": {...} }`

### 6. 数据模型

### Block
```json
{
  "id": "docs/readme.md:1.2",
  "doc_path": "docs/readme.md",
  "chapter_index": 1,
  "section_index": 2,
  "title": "Installation",
  "content": "...",
  "start_line": 10,
  "end_line": 25,
  "level": 2
}
```

### Relation
```json
{
  "source": "block_id_1",
  "target": "block_id_2",
  "score": 0.85
}
```

### Graph
```json
{
  "nodes": [...],
  "edges": [...],
  "metadata": {
    "created_at": "...",
    "doc_count": 5,
    "block_count": 20
  }
}
```