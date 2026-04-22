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

    块结构：
    - 每个标题行是一个块
    - 每个非标题段落也是一个块（最小粒度）
    - 块包含从自身行到下一同级/更高级标题之前的所有内容
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

    # 确定每个标题的结束行（下一个同级或更高级标题之前）
    for idx, t in enumerate(titles):
        if idx + 1 < len(titles):
            t['end_line'] = titles[idx + 1]['line_index']
        else:
            t['end_line'] = len(lines)

    # 处理文件开头的顶级内容（第一个标题之前）
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

        # 收集从当前标题行到end_line之前的所有非空行
        content_lines = []
        for line_idx in range(t['line_index'], t['end_line']):
            stripped = lines[line_idx].strip()
            if stripped == '':
                if content_lines and content_lines[-1] != '':
                    content_lines.append('')
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
            end_line=t['end_line'],
            level=t['level'],
            parent_id=parent_id
        )
        blocks.append(block)

        # 在标题块之后，创建该标题下的每个段落块
        # 段落是连续的非标题行组成
        para_start = None
        para_lines = []

        for line_idx in range(t['line_index'] + 1, t['end_line']):
            stripped = lines[line_idx].strip()

            # 如果是标题行或者是空行（段分隔符）
            is_heading = stripped.startswith('#')
            is_empty = stripped == ''

            if is_heading:
                # 保存之前的段落
                if para_lines:
                    block_id_counter += 1
                    para_block = Block(
                        id=f"{doc_path}:block:{block_id_counter}",
                        doc_path=doc_path,
                        chapter_index=idx + 1,
                        section_index=block_id_counter,
                        title='',
                        content='\n'.join(para_lines).strip(),
                        start_line=para_start + 1,
                        end_line=line_idx,
                        level=t['level'] + 1,
                        parent_id=block_id
                    )
                    blocks.append(para_block)
                    para_start = None
                    para_lines = []
            elif is_empty:
                # 空行，分隔段落
                if para_lines:
                    block_id_counter += 1
                    para_block = Block(
                        id=f"{doc_path}:block:{block_id_counter}",
                        doc_path=doc_path,
                        chapter_index=idx + 1,
                        section_index=block_id_counter,
                        title='',
                        content='\n'.join(para_lines).strip(),
                        start_line=para_start + 1,
                        end_line=line_idx,
                        level=t['level'] + 1,
                        parent_id=block_id
                    )
                    blocks.append(para_block)
                    para_start = None
                    para_lines = []
            else:
                # 正常段落行
                if para_start is None:
                    para_start = line_idx
                para_lines.append(lines[line_idx].rstrip())

        # 处理最后一段
        if para_lines:
            block_id_counter += 1
            para_block = Block(
                id=f"{doc_path}:block:{block_id_counter}",
                doc_path=doc_path,
                chapter_index=idx + 1,
                section_index=block_id_counter,
                title='',
                content='\n'.join(para_lines).strip(),
                start_line=para_start + 1,
                end_line=t['end_line'],
                level=t['level'] + 1,
                parent_id=block_id
            )
            blocks.append(para_block)

    return blocks