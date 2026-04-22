# 开发指南

## 项目结构

```
AutoMindMap/
├── app/           # 后端代码
├── static/        # 前端静态文件
├── data/          # 测试文档
└── output/         # 输出目录
```

## 技术栈

### 后端

- FastAPI: Web框架
- scikit-learn: TF-IDF向量化

### 前端

- D3.js: 可视化
- 原生JavaScript

## API接口

### POST /api/analyze

分析文档目录

### POST /api/save

保存关系图

### GET /api/load

加载关系图