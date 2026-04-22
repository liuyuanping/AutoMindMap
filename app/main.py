from fastapi import FastAPI, HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pathlib import Path
from datetime import datetime
import os
import json
from app.parser import parse_markdown_files
from app.analyzer import analyze_blocks_simple
from app.schemas import AnalyzeRequest

app = FastAPI(title="Document Mind Map")

static_path = Path(__file__).parent.parent / "static"
app.mount("/static", StaticFiles(directory=str(static_path)), name="static")

output_path = Path(__file__).parent.parent / "output"
output_path.mkdir(exist_ok=True)


@app.get("/")
async def index():
    return FileResponse(str(static_path / "index.html"))


@app.post("/api/analyze")
async def analyze(request: AnalyzeRequest):
    # 相对路径从项目根目录解析
    project_root = Path(__file__).parent.parent
    if Path(request.dir_path).is_absolute():
        dir_path = Path(request.dir_path)
    else:
        dir_path = (project_root / request.dir_path).resolve()

    if not dir_path.exists():
        raise HTTPException(status_code=400, detail="Directory does not exist")

    if not dir_path.is_dir():
        raise HTTPException(status_code=400, detail="Path is not a directory")

    blocks = parse_markdown_files(str(dir_path))

    if not blocks:
        raise HTTPException(status_code=400, detail="No markdown files found")

    threshold = request.threshold
    nodes, edges = analyze_blocks_simple(blocks, threshold)

    doc_paths = set(block.doc_path for block in blocks)

    graph = {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "created_at": datetime.now().isoformat(),
            "doc_count": len(doc_paths),
            "block_count": len(blocks),
            "algorithm": "simple"
        }
    }

    return {
        "blocks": [b.model_dump() for b in blocks],
        "relations": edges,
        "graph": graph
    }


@app.post("/api/save")
async def save_graph(data: dict):
    filename = data.get("filename", "graph.json")

    if not filename.endswith(".json"):
        filename += ".json"

    save_path = output_path / filename

    with open(save_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

    return {"success": True, "path": str(save_path)}


@app.get("/api/load")
async def load_graph(path: str):
    project_root = Path(__file__).parent.parent
    if Path(path).is_absolute():
        file_path = Path(path)
    else:
        file_path = (project_root / path).resolve()

    if not file_path.exists():
        raise HTTPException(status_code=400, detail="File does not exist")

    with open(file_path, 'r', encoding='utf-8') as f:
        graph = json.load(f)

    return {"graph": graph}


@app.get("/api/files")
async def list_saved_graphs():
    files = []
    for f in output_path.glob("*.json"):
        files.append({
            "name": f.name,
            "path": str(f.relative_to(project_root)),
            "size": f.stat().st_size,
            "modified": datetime.fromtimestamp(f.stat().st_mtime).isoformat()
        })
    return {"files": files}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)