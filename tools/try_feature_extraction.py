"""Interactive real-provider preference extraction against a selected catalog."""

import argparse
import json

import httpx

from app.catalog import load_catalog
from app.config import get_settings
from app.recommendation.feature_extractor import (
    CatalogFeatureExtractor,
    ChatFeatures,
    validate_labels,
)
from app.recommendation.llm import _llm_text, _parse_json_response
from app.recommendation.vocabulary import metadata_preferences, preference_vocabulary


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--program", required=True, help="ID ngành trong catalog hiện tại")
    parser.add_argument("--message", help="Câu cần trích xuất; bỏ qua để nhập tương tác")
    args = parser.parse_args()
    settings = get_settings()
    if not settings.recommendation_llm_enabled or not settings.gemini_api_key:
        parser.exit(1, "Cần bật RECOMMENDATION_LLM_ENABLED và đặt GEMINI_API_KEY trong .env.\n")
    catalog = load_catalog(args.program)
    print("Vocabulary trích xuất theo metadata project và nhãn bổ sung của ngành:")
    print(json.dumps(preference_vocabulary(catalog), ensure_ascii=False, indent=2))
    print("Nhãn sở thích không khẳng định môn học có metadata tương ứng.")
    print("Mỗi câu sẽ gọi API LLM thật theo cấu hình .env. Ctrl+C để thoát.")

    while True:
        message = args.message if args.message is not None else input("Bạn: ").strip()
        if not message:
            return
        state = {"source": "fallback", "reason": None}

        def provider(prompt: str) -> str:
            try:
                raw = _llm_text(prompt)
            except httpx.HTTPStatusError as exc:
                status = exc.response.status_code
                hints = {
                    400: "Kiểm tra cấu hình model và định dạng request.",
                    401: "Kiểm tra API key và xác thực của nhà cung cấp.",
                    403: "Kiểm tra quyền API key, model và project.",
                    404: "Kiểm tra GEMINI_MODEL và GEMINI_BASE_URL.",
                    429: "Kiểm tra quota, giới hạn tốc độ hoặc thanh toán.",
                }
                state["reason"] = f"HTTP {status}"
                print(f"API LLM trả HTTP {status}. {hints.get(status, 'Kiểm tra dịch vụ nhà cung cấp.')}")
                # Do not print the exception URL: Gemini includes the key in its query.
                raise
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
        print(json.dumps({
            **state,
            "preference": result.model_dump(),
            "metadata_preferences": metadata_preferences(result),
        }, ensure_ascii=False, indent=2))
        if args.message is not None:
            return


if __name__ == "__main__":
    try:
        main()
    except (KeyboardInterrupt, EOFError):
        print("\nĐã thoát.")
