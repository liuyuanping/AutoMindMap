# Auto Mind Map

文档关系分析与可视化工具。

## 功能

- 递归读取目录下所有 `.md` 文档
- 智能分块：标题、段落均独立成块，记录层级关系
- 三种相似度算法可选：Jaccard、TF-IDF Cosine、Claude API
- 可视化力导向图展示文档关系
- 支持按文档/层级筛选节点
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

1. 输入文档目录路径（如 `data`）
2. 选择相似度算法和阈值
3. 点击"分析文档"
4. 点击节点查看详情，点击空白处恢复全图

## 配置

- `ANTHROPIC_API_KEY`: 使用 Claude API 时需设置

## 协议

MIT License