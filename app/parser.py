import re
from pathlib import Path
from typing import List, Optional, Dict
from app.schemas import Block


def parse_markdown_files(dir_path: str) -> List[Block]:
    """递归解析目录下所有md文档，返回所有层级块"""
    blocks = []
    dir_path = Path(dir_path).resolve()

    for md_file in sorted(dir_path.rglob("*.md")):
        rel_path = md_file.relative_to(dir_path)
        file_blocks = parse_single_file(str(md_file), str(rel_path))
        blocks.extend(file_blocks)

    return blocks


def parse_single_file(file_path: str, doc_path: str) -> List[Block]:
    """解析单个md文件，提取所有层级块

    块结构：
    - 每个标题是一个块
    - 父块的内容 = 自身内容 + 所有子块内容（递归合并）
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 解析所有标题
    titles = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if match:
            titles.append({
                'line_index': i,
                'level': len(match.group(1)),
                'title': match.group(2).strip(),
                'start_line': i + 1
            })

    # 确定每个标题的结束行
    for idx, t in enumerate(titles):
        if idx + 1 < len(titles):
            t['end_line'] = titles[idx + 1]['line_index']
        else:
            t['end_line'] = len(lines)

    blocks = []
    block_id_counter = 0
    title_to_block_id = {}

    # 处理文件开头的顶级内容
    first_title_line = titles[0]['line_index'] if titles else len(lines)
    top_content_lines = []
    if first_title_line > 0:
        for i in range(first_title_line):
            stripped = lines[i].strip()
            if stripped and not stripped.startswith('#'):
                top_content_lines.append(lines[i].rstrip())

    has_top_content = len(top_content_lines) > 0
    if has_top_content:
        block_id_counter += 1
        top_block = Block(
            id=f"{doc_path}:block:{block_id_counter}",
            doc_path=doc_path,
            chapter_index=0,
            section_index=0,
            title='',
            content='\n'.join(top_content_lines),
            start_line=1,
            end_line=first_title_line,
            level=0,
            parent_id=None
        )
        blocks.append(top_block)

    # 为每个标题创建块
    for idx, t in enumerate(titles):
        block_id_counter += 1
        block_id = f"{doc_path}:block:{block_id_counter}"
        title_to_block_id[idx] = block_id

        # 找父标题
        parent_id = None
        for pidx in range(idx - 1, -1, -1):
            if titles[pidx]['level'] < t['level']:
                parent_id = title_to_block_id[pidx]
                break

        # 收集该标题下的非子标题内容
        content_lines = []
        for line_idx in range(t['line_index'] + 1, t['end_line']):
            stripped = lines[line_idx].strip()
            if stripped.startswith('#'):
                continue
            if stripped:
                content_lines.append(lines[line_idx].rstrip())

        block = Block(
            id=block_id,
            doc_path=doc_path,
            chapter_index=idx + 1,
            section_index=0,
            title=t['title'],
            content='\n'.join(content_lines).strip(),
            start_line=t['start_line'],
            end_line=t['end_line'],
            level=t['level'],
            parent_id=parent_id
        )
        blocks.append(block)

    # 构建树结构，父子关系用block的id关联
    # 已经是 parent_id 了，不需要额外处理

    # 现在计算每个块的完整内容（包含所有子块内容）
    # 从叶子节点向上累加
    # 先建立 id -> block 的映射
    id_to_block = {b.id: b for b in blocks}

    # 找所有叶子节点（没有子块的块）
    # 由于 blocks 是按文件顺序创建的，子块总是在父块之后
    # 所以从后向前遍历，把子块内容加到父块

    for i in range(len(blocks) - 1, -1, -1):
        block = blocks[i]
        children_contents = []

        # 找到这个块的所有直接子块
        for j in range(i + 1, len(blocks)):
            child = blocks[j]
            if child.parent_id == block.id:
                # 这是直接子块，把它的（已合并的）内容加上
                children_contents.append(child.content)

        # 父块内容 = 自身内容 + 所有子块内容
        if children_contents:
            child_text = '\n'.join(children_contents)
            if block.content:
                block.content = block.content + '\n' + child_text
            else:
                block.content = child_text

    return blocks