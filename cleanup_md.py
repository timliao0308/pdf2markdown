"""Clean up image-text bleed from docling markdown output.

Targets the dominant cruft patterns we observed:
- Slide footer "Proprietary + Confidential[l...]" appearing on its own line, as a
  prefix, suffix, or even doubled inside a paragraph.
- Standalone "Google Cloud" branding lines (when not preceded by content that
  would make it part of a sentence).
- Stray single-character lines like "/" or ":".
- Leftover footer markers combined with brand: "Proprietary + Confidential Google Cloud".

This is intentionally conservative — diagram labels and short single-word lines
that *might* be image-text bleed are left alone, because they could also be
legitimate slide headings or callouts.
"""

import re
from pathlib import Path

ROOT = Path(__file__).parent
TARGET_DIR = ROOT / "output_md_docling"

# Footer / brand patterns we want to nuke.
FOOTER_RE = re.compile(r"Proprietary\s*\+\s*Confidentiall*", re.IGNORECASE)
BRAND_LINE_RE = re.compile(r"^Google Cloud$")
STRAY_LINE_RE = re.compile(r"^[\W_]{1,3}$")  # "/", ":", "-", "—", "8 XA"-ish? No, that has letters.

# Whole lines to remove outright (after trimming).
WHOLE_LINE_REMOVE = [
    # Slide footers / branding
    re.compile(r"^Proprietary\s*\+\s*Confidentiall*\s*(Google Cloud)?\s*$", re.IGNORECASE),
    re.compile(r"^Confidentiall*$", re.IGNORECASE),
    re.compile(r"^Google Cloud$"),
    # Stray punctuation lines
    re.compile(r"^[/:\-—]$"),
    # OCR truncations of "Google Cloud" header bar
    re.compile(r"^o+gle Cloud(?:\s+(?:cons|Platform.*))?$", re.IGNORECASE),
    re.compile(r"^=\s*\d+\s+o+gle Cloud Platform.*$", re.IGNORECASE),
    re.compile(r"^ole\.cloud\.gooale.*$", re.IGNORECASE),
    # Standalone UI labels often picked up from console screenshots
    re.compile(r"^(SSH|Connect|External IP|Internal IP|Name\s*\^?|Zone)$"),
    # Google Play / App Store badge text
    re.compile(r"^(GET IT ON|Download on the|Google Play App Store|App Store|Google Play)$"),
    # Bare IP addresses, optionally with "(nicO)" / "(nic0)" / "(nic1)" suffix
    re.compile(r"^\d{1,3}(?:\.\d{1,3}){3}(?:\s*\(nic[O0-9]+\))?$"),
]


def clean_line(line: str) -> str:
    """Strip embedded footer markers from a content line.

    Cases handled:
      - "Proprietary + Confidential X..."   -> "X..."
      - "...X Proprietary + Confidential"   -> "...X"
      - "X Proprietary + Confidential Y"    -> "X Y" (collapses inner footer)
      - "Proprietary + Confidential Google Cloud X" -> "X"
    """
    # Remove "Proprietary + Confidential[l...] (Google Cloud)?" wherever it appears
    cleaned = re.sub(
        r"\bProprietary\s*\+\s*Confidentiall*\s*(?:Google Cloud)?\b",
        "",
        line,
        flags=re.IGNORECASE,
    )
    # Collapse double spaces left behind
    cleaned = re.sub(r"[ \t]{2,}", " ", cleaned).strip()
    return cleaned


def clean_text(text: str) -> str:
    out_lines: list[str] = []
    for raw in text.splitlines():
        line = raw.rstrip()

        # Drop if it matches any whole-line removal pattern.
        if any(p.match(line.strip()) for p in WHOLE_LINE_REMOVE):
            continue

        # Image / heading lines: keep as-is.
        if line.startswith("![") or line.startswith("#"):
            out_lines.append(line)
            continue

        # Strip embedded footer markers from content lines.
        if "Proprietary" in line or "Confidential" in line.lower():
            cleaned = clean_line(line)
            # If after cleaning the line became empty or trivial, skip.
            if not cleaned or any(p.match(cleaned) for p in WHOLE_LINE_REMOVE):
                continue
            out_lines.append(cleaned)
        else:
            out_lines.append(line)

    # Collapse 3+ blank lines to a single blank line, and trim trailing blanks.
    result: list[str] = []
    blank_run = 0
    for ln in out_lines:
        if ln.strip() == "":
            blank_run += 1
            if blank_run <= 1:
                result.append("")
        else:
            blank_run = 0
            result.append(ln)
    while result and result[-1] == "":
        result.pop()
    return "\n".join(result) + "\n"


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
