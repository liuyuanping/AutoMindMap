# API文档

## 概述

Document Mind Map 提供RESTful API接口用于文档分析。

## 接口列表

### POST /api/analyze

分析指定目录下的所有Markdown文档。

**请求参数**

```json
{
  "dir_path": "/path/to/docs",
  "threshold": 0.3
}
```

- `dir_path`: 文档目录路径（必填）
- `threshold`: 相关度阈值，0.0-1.0（可选，默认0.3）

**响应**

```json
{
  "blocks": [...],
  "relations": [...],
  "graph": {...}
}
```

### POST /api/save

保存关系图到本地文件。

**请求参数**

```json
{
  "graph": {...},
  "filename": "my-graph.json"
}
```

### GET /api/load

从本地加载已保存的关系图。

**查询参数**

- `path`: 图文件路径

### GET /api/files

列出所有已保存的图文件。

## 返回码

- 200: 成功
- 400: 请求参数错误
- 500: 服务器内部错误