# Auto Mind Map

文档关系分析与可视化工具。

## 功能

- 递归读取目录下所有 `.md` 文档
- 智能分块：标题、段落均独立成块，记录层级关系
- 三种相似度算法可选：Jaccard、TF-IDF Cosine、Claude API
- 可视化力导向图展示文档关系
- 支持按文档筛选节点
- 保存/加载关系图

## 安装

```bash
pip install -r requirements.txt
```

## 运行

```bash
cd app
python3 -m uvicorn main:app --host 0.0.0.0 --port 8000
```

浏览器访问 http://localhost:8000

## 使用

1. 输入文档目录路径（如 `data/demo`）
2. 选择相似度算法和阈值
3. 点击"分析文档"
4. 在右侧边栏筛选文档，点击节点查看详情

## 文档

- [项目架构](docs/architecture.md) - 系统架构图和模块设计
- [详细解读](docs/project-guide.md) - 核心功能原理和数据流

## 配置

- `ANTHROPIC_API_KEY`: 使用 Claude API 时需设置

## 协议

MIT License