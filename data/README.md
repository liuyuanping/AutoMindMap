# 项目概述

这是一个文档关系分析工具，用于分析Markdown文档之间的关联性。

## 主要功能

- 递归读取目录下所有.md文档
- 提取文档块结构（章节和小节）
- 计算块之间的TF-IDF余弦相似度
- 生成可视化关系图
- 支持保存和加载关系图

## 安装

```bash
pip install -r requirements.txt
```

## 使用方法

```bash
cd app
python main.py
```

然后在浏览器打开 http://localhost:8000