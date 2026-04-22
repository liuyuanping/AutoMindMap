import re
from pathlib import Path
from typing import List
from app.schemas import Block


def parse_markdown_files(dir_path: str) -> List[Block]:
    blocks = []
    dir_path = Path(dir_path).resolve()

    for md_file in sorted(dir_path.rglob("*.md")):
        rel_path = md_file.relative_to(dir_path)
        file_blocks = parse_single_file(str(md_file), str(rel_path))
        blocks.extend(file_blocks)

    return blocks


def parse_single_file(file_path: str, doc_path: str) -> List[Block]:
    """解析单个md文件

    每节的content = 从当前标题到下一同级节（或小节）前的所有内容
    包括子标题行也要作为内容进行相似度分析
    """
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # 找到所有标题行
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

    blocks = []
    block_id_counter = 0
    title_to_block_id = {}

    # 处理文件开头的顶级内容
    if titles and titles[0]['line_index'] > 0:
        top_lines = []
        for i in range(titles[0]['line_index']):
            stripped = lines[i].strip()
            if stripped and not stripped.startswith('#'):
                top_lines.append(lines[i].rstrip())
        if top_lines:
            block_id_counter += 1
            block = Block(
                id=f"{doc_path}:block:{block_id_counter}",
                doc_path=doc_path,
                chapter_index=0,
                section_index=0,
                title='',
                content='\n'.join(top_lines),
                start_line=1,
                end_line=titles[0]['line_index'],
                level=0,
                parent_id=None
            )
            blocks.append(block)

    # 处理每个标题
    for idx, t in enumerate(titles):
        block_id_counter += 1
        block_id = f"{doc_path}:block:{block_id_counter}"
        title_to_block_id[idx] = block_id

        # 找父标题（最近的前一个更低级别的标题）
        parent_id = None
        for pidx in range(idx - 1, -1, -1):
            if titles[pidx]['level'] < t['level']:
                parent_id = title_to_block_id[pidx]
                break

        # 找内容的结束位置：下一个同级或更高级标题
        # 如果是 h2，则找下一个 h1 或 h2
        # 如果是 h3，则找下一个 h1/h2/h3
        content_end_line = len(lines)  # 默认到文件结尾
        for next_idx in range(idx + 1, len(titles)):
            if titles[next_idx]['level'] <= t['level']:
                content_end_line = titles[next_idx]['line_index']
                break

        # 收集从当前标题之后到content_end_line之前的所有非空行
        # 包括子标题行（以#开头的）
        content_lines = []
        for line_idx in range(t['line_index'] + 1, content_end_line):
            line_stripped = lines[line_idx].strip()
            # 只跳过完全空的行（空行或只有空格）
            if line_stripped == '':
                continue
            content_lines.append(lines[line_idx].rstrip())

        content = '\n'.join(content_lines).strip()

        block = Block(
            id=block_id,
            doc_path=doc_path,
            chapter_index=idx + 1,
            section_index=0,
            title=t['title'],
            content=content,
            start_line=t['start_line'],
            end_line=content_end_line,
            level=t['level'],
            parent_id=parent_id
        )
        blocks.append(block)

    return blocks