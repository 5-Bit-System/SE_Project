"""Render only the curriculum section of the four supplied scan PDFs.

Optional helper: requires PyMuPDF; output images stay outside the repository.
"""

import argparse
from pathlib import Path
import tempfile

import fitz


SECTIONS = {"101": (7, 14), "103": (7, 12), "104": (8, 13), "105": (8, 13)}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="Directory containing the four source PDFs")
    parser.add_argument("--output", type=Path)
    parser.add_argument("--dpi", type=int, default=150)
    args = parser.parse_args()
    output = args.output or Path(tempfile.mkdtemp(prefix="se-curriculum-"))
    output.mkdir(parents=True, exist_ok=True)
    for prefix, (first, last) in SECTIONS.items():
        matches = list(args.source.glob(f"{prefix}.*.pdf")) + list(args.source.glob(f"{prefix}-*.pdf"))
        matches = list(dict.fromkeys(matches))
        if len(matches) != 1:
            raise ValueError(f"Expected one PDF for {prefix}; found {len(matches)}")
        with fitz.open(matches[0]) as document:
            for number in range(first, last + 1):
                document[number - 1].get_pixmap(dpi=args.dpi).save(output / f"{prefix}-{number:02}.png")
    print(output)


if __name__ == "__main__":
    main()
