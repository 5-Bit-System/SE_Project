"""Interactive real-provider preference extraction against a selected catalog."""

import argparse
import json

from app.catalog import load_catalog
from app.config import get_settings
from app.recommendation.feature_extractor import (
    CatalogFeatureExtractor,
    ChatFeatures,
    validate_labels,
)
from app.recommendation.llm import _llm_text, _parse_json_response


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program", required=True, help="ID ngành trong catalog hiện tại")
    parser.add_argument("--message", help="Câu cần trích xuất; bỏ qua để nhập tương tác")
    args = parser.parse_args()
    settings = get_settings()
    if not settings.recommendation_llm_enabled or not settings.gemini_api_key:
        parser.exit(1, "Cần bật RECOMMENDATION_LLM_ENABLED và đặt GEMINI_API_KEY trong .env.\n")
    catalog = load_catalog(args.program)
    print("Vocabulary của ngành:")
    print(json.dumps(catalog.vocabulary or {}, ensure_ascii=False, indent=2))
    print("Mỗi câu sẽ gọi API LLM thật theo cấu hình .env. Ctrl+C để thoát.")

    while True:
        message = args.message if args.message is not None else input("Bạn: ").strip()
        if not message:
            return
        state = {"source": "fallback", "reason": None}

        def provider(prompt: str) -> str:
            try:
                raw = _llm_text(prompt)
            except Exception as exc:
                state["reason"] = type(exc).__name__
                raise
            print("Phản hồi gốc từ LLM:")
            print(raw)
            try:
                validate_labels(ChatFeatures.model_validate(_parse_json_response(raw)), catalog)
            except Exception as exc:
                state["reason"] = type(exc).__name__
                raise
            state["source"] = "llm"
            return raw

        result = CatalogFeatureExtractor(catalog, provider=provider).extract(message)
        print("Kết quả đã chuẩn hóa:")
        print(json.dumps({**state, "preference": result.model_dump()}, ensure_ascii=False, indent=2))
        if args.message is not None:
            return


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nĐã thoát.")
