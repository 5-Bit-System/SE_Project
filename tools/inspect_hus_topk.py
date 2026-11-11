"""CLI inspector for HUS RAG Top-K chunk retrieval, intent routing, and course alias resolution.

Usage:
    python -m tools.inspect_hus_topk --suite
    python -m tools.inspect_hus_topk --question "Môn CSDL học gì?" --major computer_science
    python -m tools.inspect_hus_topk --question "Môn CSDL học gì?" --json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Sequence

from app.schemas.hus import HUSMajor, HUSQuestion, HUSRetrievalBundle
from app.services.hus_service import get_hus_answerer

SUITE_CASES: tuple[tuple[str, HUSMajor], ...] = (
    ("Môn CSDL bao nhiêu tín?", "computer_science"),
    ("Điều kiện tiên quyết của GT1 là gì?", "computer_science"),
    ("Môn ĐSTT học mấy tiết?", "computer_science"),
    ("Nội dung môn TTNT dạy những kiến thức cốt lõi gì?", "computer_science"),
    ("Khung chương trình chia thành những khối kiến thức nào?", "computer_science"),
    ("Sinh viên tốt nghiệp ra trường có thể làm nghề gì?", "computer_science"),
    ("Môn XSTK ở ngành KHDL có bao nhiêu tín chỉ?", "data_science"),
    ("Môn ĐSTT bao nhiêu tín?", "mathematics"),
)


def _ensure_utf8_stdout() -> None:
    reconfigure = getattr(sys.stdout, "reconfigure", None)
    if callable(reconfigure):
        reconfigure(encoding="utf-8")


def _format_bundle(bundle: HUSRetrievalBundle) -> str:
    lines: list[str] = [
        "=" * 88,
        f"QUESTION : {bundle.question}",
        f"NORM_Q   : {bundle.normalized_question}",
        f"SCOPE    : major={bundle.major} | version={bundle.version}",
        f"INTENT   : dataset={bundle.dataset} | field={bundle.field} "
        f"| source={bundle.intent_source} | confidence={bundle.intent_confidence:.2f}",
    ]
    if bundle.resolved_courses:
        courses_str = ", ".join(
            f"{c['course_code']} ({c['course_name']} [{c['match_type']}])"
            for c in bundle.resolved_courses
        )
        lines.append(
            f"COURSES  : resolved={bundle.resolved_course_code} | matches=[{courses_str}]"
        )
    else:
        lines.append("COURSES  : (no course matched)")

    if "course" in bundle.structured_data:
        c = bundle.structured_data["course"]
        lines.append(
            f"F2_FACT  : {c['course_code']} — {c['course_name']} | "
            f"credits={c['credits']} | hours={c['hours']} | "
            f"prereq_status={c['prerequisite_status']} | review={c['review_status']}"
        )
    elif "program" in bundle.structured_data:
        p = bundle.structured_data["program"]
        group_cnt = len(p.get("group_rules", []))
        lines.append(
            f"F2_PROG  : {p['program_id']} ({p['major_name']}) | "
            f"credits_required={p['credits_required']} | groups={group_cnt} | review={p['review_status']}"
        )

    lines.append(f"TOP-{bundle.top_k} CHUNKS ({len(bundle.top_k_chunks)} returned):")
    for chunk in bundle.top_k_chunks:
        snippet = " ".join(chunk.body.split())
        if len(snippet) > 120:
            snippet = snippet[:117] + "..."
        gate_label = "PASS" if chunk.passed_support_gate else "info"
        code_part = f" [{chunk.course_code}]" if chunk.course_code else ""
        lines.append(
            f"  #{chunk.rank} [{chunk.dataset}/{chunk.field}{code_part}] "
            f"score={chunk.score:.4f} gate={gate_label} id={chunk.chunk_id}"
        )
        lines.append(f"     {snippet}")
    return "\n".join(lines)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect HUS RAG Top-K chunk retrieval, intent routing, and course aliases."
    )
    parser.add_argument(
        "--question",
        "-q",
        type=str,
        default=None,
        help="Question to inspect.",
    )
    parser.add_argument(
        "--major",
        "-m",
        type=str,
        default="computer_science",
        choices=("mathematics", "mathematics_informatics", "computer_science", "data_science"),
        help="Target HUS major (default: computer_science).",
    )
    parser.add_argument(
        "--version",
        "-v",
        type=str,
        default=None,
        help="Curriculum version (optional, auto-resolved from major if omitted).",
    )
    parser.add_argument(
        "--top-k",
        "-k",
        type=int,
        default=5,
        help="Number of top chunks to retrieve (1..20, default: 5).",
    )
    parser.add_argument(
        "--allow-ai",
        dest="allow_ai",
        action="store_true",
        default=True,
        help="Allow AI-generated F3 reference chunks (default: True).",
    )
    parser.add_argument(
        "--no-allow-ai",
        dest="allow_ai",
        action="store_false",
        help="Disable AI-generated F3 reference chunks.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output raw JSON of HUSRetrievalBundle(s).",
    )
    parser.add_argument(
        "--suite",
        action="store_true",
        help="Run built-in test suite of diverse HUS queries.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    _ensure_utf8_stdout()
    parser = build_parser()
    args = parser.parse_args(list(argv) if argv is not None else None)

    answerer = get_hus_answerer()
    if args.suite or not args.question:
        bundles: list[HUSRetrievalBundle] = []
        for q_text, major in SUITE_CASES:
            req = HUSQuestion(
                question=q_text,
                major=major,
                version=args.version,
                allow_generated_reference=args.allow_ai,
            )
            bundles.append(answerer.retrieve_context(req, top_k=args.top_k))
        if args.json:
            print(
                json.dumps(
                    [b.model_dump(mode="json") for b in bundles],
                    ensure_ascii=False,
                    indent=2,
                )
            )
        else:
            for bundle in bundles:
                print(_format_bundle(bundle))
            print("=" * 88)
        return 0

    req = HUSQuestion(
        question=args.question,
        major=args.major,
        version=args.version,
        allow_generated_reference=args.allow_ai,
    )
    bundle = answerer.retrieve_context(req, top_k=args.top_k)
    if args.json:
        print(json.dumps(bundle.model_dump(mode="json"), ensure_ascii=False, indent=2))
    else:
        print(_format_bundle(bundle))
        print("=" * 88)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
