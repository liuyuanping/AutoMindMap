import os
import re
from pathlib import Path
from typing import List
from app.schemas import Block


def parse_markdown_files(dir_path: str) -> List[Block]:
    """递归解析目录下所有md文档，返回块列表"""
    blocks = []
    dir_path = Path(dir_path).resolve()

    for md_file in sorted(dir_path.rglob("*.md")):
        rel_path = md_file.relative_to(dir_path)
        file_blocks = parse_single_file(str(md_file), str(rel_path))
        blocks.extend(file_blocks)

    return blocks


def parse_single_file(file_path: str, doc_path: str) -> List[Block]:
    """解析单个md文件，提取块结构"""
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    blocks = []
    current_chapter = None
    chapter_count = 0
    section_count = 0

    i = 0
    while i < len(lines):
        line = lines[i]
        line_stripped = line.strip()

        if not line_stripped:
            i += 1
            continue

        title_match = re.match(r'^(#{1,6})\s+(.+)$', line_stripped)

        if title_match:
            level = len(title_match.group(1))
            title = title_match.group(2).strip()
            start_line = i + 1

            content_lines = []
            j = i + 1
            while j < len(lines):
                next_line = lines[j].strip()
                if re.match(r'^(#{1,6})\s+', next_line):
                    next_level = len(re.match(r'^(#{1,6})', next_line).group(1))
                    if next_level <= level:
                        break
                    content_lines.append(lines[j].rstrip())
                else:
                    content_lines.append(lines[j].rstrip())
                j += 1

            content = '\n'.join(content_lines).strip()
            end_line = i + len(content_lines) if content_lines else start_line

            if level == 1:
                chapter_count += 1
                section_count = 0
                block_id = f"{doc_path}:{chapter_count}"

                block_dict = {
                    'id': block_id,
                    'doc_path': doc_path,
                    'chapter_index': chapter_count,
                    'section_index': 0,
                    'title': title,
                    'content': content,
                    'start_line': start_line,
                    'end_line': end_line,
                    'level': level,
                    'parent_id': None
                }
                current_chapter = Block(**block_dict)
                blocks.append(current_chapter)

            else:
                if current_chapter is None:
                    chapter_count = 1
                    section_count = 0
                    current_chapter = Block(
                        id=f"{doc_path}:{chapter_count}",
                        doc_path=doc_path,
                        chapter_index=chapter_count,
                        section_index=0,
                        title='',
                        content='',
                        start_line=1,
                        end_line=i,
                        level=1,
                        parent_id=None
                    )
                    blocks.append(current_chapter)

                section_count += 1
                block_id = f"{doc_path}:{chapter_count}.{section_count}"

                block = Block(
                    id=block_id,
                    doc_path=doc_path,
                    chapter_index=chapter_count,
                    section_index=section_count,
                    title=title,
                    content=content,
                    start_line=start_line,
                    end_line=end_line,
                    level=level,
                    parent_id=current_chapter.id
                )
                blocks.append(block)

            i = j
        else:
            if current_chapter and current_chapter.content == '':
                content_lines = [line.rstrip()]
                j = i + 1
                while j < len(lines):
                    next_line = lines[j].strip()
                    if re.match(r'^(#{1,6})\s+', next_line):
                        break
                    content_lines.append(lines[j].rstrip())
                    j += 1

                content = '\n'.join(content_lines).strip()
                current_chapter.content = content
                current_chapter.end_line = i + len(content_lines)

                i = j
            else:
                i += 1

    return blocks