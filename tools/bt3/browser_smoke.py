"""Real browser fetch -> loopback app -> synthetic JSON repository, no route interception."""

import json

from playwright.sync_api import sync_playwright

from tools.bt3.http_experiment import synthetic_server
from tools.bt3.run_evidence import EVIDENCE


def main():
    with synthetic_server() as base, sync_playwright() as playwright:
        browser = playwright.chromium.launch(channel="chrome", headless=True)
        page = browser.new_page()
        page.goto(base + "/health")
        result = page.evaluate("""async () => {
          const old = await fetch('/courses?program_id=bt3_search');
          const fresh = await fetch('/courses/search?program_id=bt3_search&q=bridge&page=2&page_size=5');
          const empty = await fetch('/courses/search?program_id=bt3_search&q=not-present');
          const invalid = await fetch('/courses/search?program_id=bt3_search&page=0');
          const rows = await old.json(), data = await fresh.json();
          if (old.status !== 200 || !Array.isArray(rows) || rows.length !== 240 || rows[0].code !== 'S0239') throw Error('legacy contract');
          if (fresh.status !== 200 || data.total !== 24 || data.page !== 2 || data.page_size !== 5 || data.items.map(x=>x.code).join(',') !== 'S0050,S0060,S0070,S0080,S0090') throw Error('new contract');
          if (empty.status !== 200 || (await empty.json()).total !== 0 || invalid.status !== 422) throw Error('empty/validation contract');
          return {legacy_status: old.status, legacy_count: rows.length, search: data,
                  empty_status: empty.status, invalid_status: invalid.status};
        }""")
        result.update(browser_version=browser.version, mock_routes=False,
                      scope="Browser API smoke; not VNU UI/login or a new search screen")
        (EVIDENCE / "browser-results.json").write_text(
            json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
        browser.close()
        print("Real browser HTTP contracts: legacy array, filtered page, empty and 422 passed")


if __name__ == "__main__":
    main()
