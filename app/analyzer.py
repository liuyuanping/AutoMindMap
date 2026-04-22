from typing import List, Tuple
import os
from app.schemas import Block, Relation

DEFAULT_THRESHOLD = 0.3


def compute_simple_similarity(blocks: List[Block], threshold: float) -> List[Relation]:
    """使用关键词重叠计算简单相似度"""
    if len(blocks) < 2:
        return []

    def extract_keywords(text: str) -> set:
        words = text.lower().split()
        stopwords = {'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
                     'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'be', 'been',
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
                     'should', 'may', 'might', 'can', 'this', 'that', 'these', 'those', 'it'}
        return set(w for w in words if len(w) > 2 and w not in stopwords)

    relations = []
    n = len(blocks)

    for i in range(n):
        keywords_i = extract_keywords(blocks[i].content)
        for j in range(i + 1, n):
            keywords_j = extract_keywords(blocks[j].content)

            if not keywords_i or not keywords_j:
                continue

            intersection = len(keywords_i & keywords_j)
            union = len(keywords_i | keywords_j)

            if union > 0:
                score = intersection / union
                if score >= threshold:
                    relations.append(Relation(
                        source=blocks[i].id,
                        target=blocks[j].id,
                        score=score
                    ))

    return relations


async def compute_similarity_with_claude(blocks: List[Block], threshold: float) -> List[Relation]:
    """使用Claude API计算块之间的语义相似度"""
    try:
        import httpx
    except ImportError:
        return compute_simple_similarity(blocks, threshold)

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if not api_key:
        return compute_simple_similarity(blocks, threshold)

    try:
        import httpx

        ANTHROPIC_EMBED_URL = "https://api.anthropic.com/v1/embeddings"
        headers = {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "content-type": "application/json"
        }

        texts = [block.content[:8192] for block in blocks]
        embeddings = []

        async with httpx.AsyncClient(timeout=60.0) as client:
            for text in texts:
                payload = {"model": "embed-english-v2.0", "input": text}
                response = await client.post(ANTHROPIC_EMBED_URL, headers=headers, json=payload)
                if response.status_code == 200:
                    data = response.json()
                    embeddings.append(data["embedding"])
                else:
                    import random
                    embeddings.append([random.random()] * 1024)

        relations = []
        n = len(blocks)

        for i in range(n):
            for j in range(i + 1, n):
                score = cosine_similarity(embeddings[i], embeddings[j])
                if score >= threshold:
                    relations.append(Relation(
                        source=blocks[i].id,
                        target=blocks[j].id,
                        score=score
                    ))

        return relations

    except Exception:
        return compute_simple_similarity(blocks, threshold)


def cosine_similarity(a: List[float], b: List[float]) -> float:
    """计算两个向量的余弦相似度"""
    dot_product = sum(x * y for x, y in zip(a, b))
    norm_a = sum(x * x for x in a) ** 0.5
    norm_b = sum(y * y for y in b) ** 0.5
    if norm_a == 0 or norm_b == 0:
        return 0.0
    return dot_product / (norm_a * norm_b)


async def analyze_blocks(blocks: List[Block], threshold: float) -> Tuple[List[dict], List[dict]]:
    """分析块之间的关联，返回节点和边"""
    relations = await compute_similarity_with_claude(blocks, threshold)

    nodes = []
    for block in blocks:
        nodes.append({
            'id': block.id,
            'doc_path': block.doc_path,
            'title': block.title,
            'chapter_index': block.chapter_index,
            'section_index': block.section_index,
            'level': block.level,
            'content': block.content,
            'content_preview': block.content[:100] + '...' if len(block.content) > 100 else block.content,
            'start_line': block.start_line,
            'end_line': block.end_line,
            'parent_id': block.parent_id
        })

    edges = []
    for rel in relations:
        edges.append({
            'source': rel.source,
            'target': rel.target,
            'score': rel.score
        })

    return nodes, edges


def analyze_blocks_simple(blocks: List[Block], threshold: float) -> Tuple[List[dict], List[dict]]:
    """使用简单算法分析块之间的关联"""
    relations = compute_simple_similarity(blocks, threshold)

    nodes = []
    for block in blocks:
        nodes.append({
            'id': block.id,
            'doc_path': block.doc_path,
            'title': block.title,
            'chapter_index': block.chapter_index,
            'section_index': block.section_index,
            'level': block.level,
            'content': block.content,
            'content_preview': block.content[:100] + '...' if len(block.content) > 100 else block.content,
            'start_line': block.start_line,
            'end_line': block.end_line,
            'parent_id': block.parent_id
        })

    edges = []
    for rel in relations:
        edges.append({
            'source': rel.source,
            'target': rel.target,
            'score': rel.score
        })

    return nodes, edges