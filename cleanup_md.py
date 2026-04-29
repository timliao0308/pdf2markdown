"""Clean up docling markdown output for Taiwanese tax PDFs.

Targets the dominant cruft patterns we observed:
- Repeated page-header H2 titles (the same "## ..." appearing on every page,
  often followed by boilerplate notice/numbered-list lines).
- Stray spaces between CJK characters caused by PDF visual line-wrapping
  (e.g. "兆豐國際商業銀 行股份有限公 司" -> "兆豐國際商業銀行股份有限公司").
- Excessive blank lines.

Conservative — does not touch table rows beyond CJK-space collapsing, and
keeps every H2 the first time it appears.
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent
TARGET_DIR = ROOT / "output_md_docling"

CJK_RANGE = r"一-鿿㐀-䶿豈-﫿　-〿＀-￯"
CJK_SPACE_RE = re.compile(rf"([{CJK_RANGE}])[ \t]+([{CJK_RANGE}])")


def collapse_cjk_spaces(text: str) -> str:
    """Repeatedly collapse single spaces between two CJK chars.

    Applied repeatedly because a single regex pass only consumes one space
    at a time (the second CJK char is needed to anchor the next match).
    """
    prev = None
    while prev != text:
        prev = text
        text = CJK_SPACE_RE.sub(r"\1\2", text)
    return text


def remove_repeated_h2_blocks(text: str) -> str:
    """Drop repeated H2 headers and the boilerplate that follows them.

    A repeated H2 is any "## X" whose exact text already appeared earlier in
    the file. When we see one, we skip it and every following non-substantive
    line until we hit a table row, an image, or a *new* H2.
    """
    lines = text.split("\n")
    seen: set[str] = set()
    out: list[str] = []
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith("## "):
            header = line.strip()
            if header in seen:
                i += 1
                while i < len(lines):
                    cur = lines[i].lstrip()
                    if cur.startswith("|") or cur.startswith("!["):
                        break
                    if lines[i].startswith("## "):
                        if lines[i].strip() in seen:
                            i += 1
                            continue
                        break
                    i += 1
                continue
            seen.add(header)
        out.append(line)
        i += 1
    return "\n".join(out)


def collapse_blank_lines(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.rstrip() + "\n"


def clean_text(text: str) -> str:
    text = remove_repeated_h2_blocks(text)
    text = collapse_cjk_spaces(text)
    text = collapse_blank_lines(text)
    return text


def main() -> None:
    md_files = sorted(TARGET_DIR.glob("*/*.md"))
    if not md_files:
        print(f"No markdowns under {TARGET_DIR}")
        return

    total_before = 0
    total_after = 0
    for md in md_files:
        original = md.read_text(encoding="utf-8")
        cleaned = clean_text(original)
        before = len(original.splitlines())
        after = len(cleaned.splitlines())
        total_before += before
        total_after += after
        md.write_text(cleaned, encoding="utf-8")
        print(f"{md.relative_to(ROOT)}: {before} -> {after} lines (-{before-after})")

    print(f"\nTotal: {total_before} -> {total_after} lines (-{total_before-total_after})")


if __name__ == "__main__":
    main()
