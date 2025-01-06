import re


def __is_inside_code_block__(text: str, index: int):
    code_blocks = re.finditer(r'(^|\s|\\n)```.*?[\s\S]*?```(\\n|\s|$)', text)
    
    for code_block in code_blocks:
        if code_block.start() < index < code_block.end():
            return True
        elif index < code_block.start():
            break

    return False

def __find_split_index__(markdown: str, max_size: int) -> int:
    sections = re.finditer(r'(\n\n+)', markdown)
    indices = [0]
    for section in sections:
        if section.start() > max_size:
            break
        if not __is_inside_code_block__(markdown, section.start()):
            indices.append(section.start())
    return max(indices)

def split_md(markdown: str, max_slice_size: int = 4000):

    if len(markdown) <= max_slice_size:
        return [markdown]
    
    chunks: list[str] = []
    while len(markdown) > max_slice_size:
        split_index = __find_split_index__(markdown, max_slice_size)
        if split_index == 0:
            break
        chunks.append(markdown[:split_index].strip())
        markdown = markdown[split_index:].strip()
    
    chunks.append(markdown.strip())

    return chunks
