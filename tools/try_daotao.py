"""Run with: python -m tools.try_daotao (requires optional Playwright setup)."""

import argparse
import json
from getpass import getpass

from app.integrations.daotao.client import DaotaoClient


def main() -> int:
    parser = argparse.ArgumentParser(description="Thử đọc bảng điểm VNU; không ghi database/file.")
    parser.add_argument("--selector", help="Đọc bảng tùy chọn thay vì bảng điểm mặc định")
    parser.add_argument("--show-transcript", action="store_true",
                        help="Hiện dữ liệu cá nhân ra terminal; không dùng với log chia sẻ")
    args = parser.parse_args()
    try:
        from playwright.sync_api import Error, sync_playwright
    except ImportError:
        print("Cài dependencies theo app/integrations/daotao/README.md trước khi chạy.")
        return 1

    username = input("Tên đăng nhập VNU: ").strip()
    password = getpass("Mật khẩu VNU (ẩn): ")
    if not username or not password:
        print("Tên đăng nhập và mật khẩu không được để trống.")
        return 1

    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            try:
                context = browser.new_context(accept_downloads=False)
                client = DaotaoClient(context)
                client.login(username, password)
                password = ""
                client.open_transcript()
                tables = (
                    client.read_tables(args.selector)
                    if args.selector else client.read_transcript()
                )
                print("Đã đọc bảng; đây là ô văn bản thô, chưa ánh xạ điểm.")
                if args.show_transcript:
                    print(json.dumps(tables, ensure_ascii=False, indent=2))
                return 0 if tables else 1
            finally:
                browser.close()
    except Error:
        # Do not print Playwright call logs that could contain submitted credentials.
        print("Không thể hoàn tất thao tác trình duyệt. Kiểm tra mạng, trang và Chromium.")
        return 1
    except (KeyboardInterrupt, EOFError):
        print("Đã dừng phiên thử.")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
