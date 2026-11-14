"""Verify the exact word count of the Engineering Reflection section."""

import re
from pathlib import Path

HTML_PATH = Path(__file__).resolve().parent.parent / "deliverables" / "BT3_23001939_VT-099.html"

def main():
    html = HTML_PATH.read_text(encoding="utf-8")
    m = re.search(r'<div class="reflection-block">([\s\S]*?)</div>', html)
    if not m:
        print("ERROR: reflection-block not found in HTML!")
        return 1

    content = m.group(1)
    text = re.sub(r"<[^>]+>", " ", content)
    words = text.split()
    count = len(words)
    print(f"Reflection word count: {count} words")
    if 250 <= count <= 350:
        print("VERDICT: PASSED (Within required 250-350 range)")
        return 0
    else:
        print("VERDICT: FAILED (Outside required 250-350 range)")
        return 1

if __name__ == "__main__":
    raise SystemExit(main())
