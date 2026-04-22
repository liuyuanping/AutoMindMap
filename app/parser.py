import re
from pathlib import Path
from typing import List, Optional, Tuple
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
    """解析单个md文件，提取所有层级块（标题+段落）"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    blocks = []
    block_counter = 0

    # 找出所有标题行
    titles = []
    for i, line in enumerate(lines):
        stripped = line.strip()
        match = re.match(r'^(#{1,6})\s+(.+)$', stripped)
        if match:
            level = len(match.group(1))
            title = match.group(2).strip()
            titles.append({
                'line_index': i,
                'level': level,
                'title': title,
                'start_line': i + 1
            })

    # 确定每个标题的结束行（下一个同级或更高级标题之前）
    for idx, t in enumerate(titles):
        if idx + 1 < len(titles):
            t['end_line'] = titles[idx + 1]['line_index']
        else:
            t['end_line'] = len(lines)

    # 创建标题块
    title_blocks = []
    for idx, t in enumerate(titles):
        block_counter += 1
        # 找到父标题（最近的高级别标题）
        parent_id = None
        for parent_idx in range(idx - 1, -1, -1):
            if titles[parent_idx]['level'] < t['level']:
                parent_id = f"{doc_path}:title:{parent_idx + 1}"
                break

        # 收集该标题下的所有内容行（不含子标题）
        content_lines = []
        for line_idx in range(t['line_index'] + 1, t['end_line']):
            line_stripped = lines[line_idx].strip()
            # 跳过子标题行
            if not line_stripped or re.match(r'^#{1,6}\s+', line_stripped):
                continue
            content_lines.append(lines[line_idx].rstrip())

        block = Block(
            id=f"{doc_path}:title:{idx + 1}",
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
        title_blocks.append(block)
        blocks.append(block)

    # 创建段落块 - 每个非标题段落独立成块
    paragraph_blocks = []
    current_title_idx = -1  # 当前段落所属的标题索引

    for idx, t in enumerate(titles):
        # 确定该标题范围内的段落
        start = t['line_index'] + 1
        end = t['end_line']

        para_in_title = []
        para_start = None
        para_lines = []

        for line_idx in range(start, end):
            line = lines[line_idx]
            stripped = line.strip()

            # 跳过空行和子标题
            if not stripped or re.match(r'^#{1,6}\s+', stripped):
                if para_lines:
                    para_in_title.append((para_start, para_lines))
                    para_start = None
                    para_lines = []
                continue

            if para_start is None:
                para_start = line_idx

            para_lines.append(line.rstrip())

        if para_lines:
            para_in_title.append((para_start, para_lines))

        # 为每个段落创建块
        for para_start_line, para_content in para_in_title:
            if not para_content:
                continue

            block_counter += 1
            content = '\n'.join(para_content).strip()
            if not content:
                continue

            # 该段落属于哪个标题
            parent_id = f"{doc_path}:title:{idx + 1}"

            block = Block(
                id=f"{doc_path}:para:{block_counter}",
                doc_path=doc_path,
                chapter_index=idx + 1,
                section_index=len(paragraph_blocks) + 1,
                title='',
                content=content,
                start_line=para_start_line + 1,
                end_line=para_start_line + len(para_content),
                level=t['level'] + 1,  # 段落级别比标题高一級
                parent_id=parent_id
            )
            paragraph_blocks.append(block)
            blocks.append(block)

    # 如果文件开头没有标题，创建顶级段落块
    if titles and titles[0]['line_index'] > 0:
        # 文件开头段落
        para_lines = []
        para_start = None
        for line_idx in range(0, titles[0]['line_index']):
            line = lines[line_idx]
            stripped = line.strip()
            if not stripped:
                continue
            if para_start is None:
                para_start = line_idx
            para_lines.append(line.rstrip())

        if para_lines:
            block_counter += 1
            content = '\n'.join(para_lines).strip()
            block = Block(
                id=f"{doc_path}:para:{block_counter}",
                doc_path=doc_path,
                chapter_index=0,
                section_index=0,
                title='',
                content=content,
                start_line=1,
                end_line=titles[0]['line_index'],
                level=0,  # 顶级段落
                parent_id=None
            )
            blocks.append(block)

    # 顶级段落（文件中间没有标题的区域）
    last_end = 0
    for t in titles:
        if t['line_index'] > last_end and last_end > 0:
            # 有顶级内容
            para_lines = []
            para_start = None
            for line_idx in range(last_end, t['line_index']):
                line = lines[line_idx]
                stripped = line.strip()
                if not stripped:
                    continue
                if para_start is None:
                    para_start = line_idx
                para_lines.append(line.rstrip())

            if para_lines:
                block_counter += 1
                content = '\n'.join(para_lines).strip()
                block = Block(
                    id=f"{doc_path}:para:{block_counter}",
                    doc_path=doc_path,
                    chapter_index=0,
                    section_index=0,
                    title='',
                    content=content,
                    start_line=last_end + 1,
                    end_line=t['line_index'],
                    level=0,
                    parent_id=None
                )
                blocks.append(block)
        last_end = t['end_line']

    return blocks