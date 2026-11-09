"""Interactive real-provider intent resolution; state stays in this process only."""

import argparse
import json

from app.catalog import load_catalog
from app.recommendation.llm import configured_adapters
from app.services.study_intent_service import resolve_study_intent


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program", required=True)
    parser.add_argument("--message")
    args = parser.parse_args()
    catalog = load_catalog(args.program)
    extractor, _ = configured_adapters(catalog)
    print("Gọi API thật nếu đã cấu hình LLM; nếu không dùng quy tắc. /reset để bắt đầu lại.")
    state = None
    while True:
        message = args.message if args.message is not None else input("Bạn: ").strip()
        if not message:
            return
        if message == "/reset":
            state = None
            continue
        result = resolve_study_intent(message, catalog, previous_state=state, extractor=extractor,
                                      max_credits=30, max_courses=20)
        state = result.state
        print(json.dumps({"preference": result.preference.model_dump(),
                          "intent": result.diagnostics.model_dump(),
                          "effective_limits": {"credits": result.max_credits, "courses": result.max_courses}},
                         ensure_ascii=False, indent=2))
        if args.message is not None:
            return


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nĐã thoát.")
