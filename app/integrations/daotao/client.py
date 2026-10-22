"""Headed, session-only exploration of the VNU student portal."""

from time import monotonic, sleep


LOGIN_URL = "https://daotao.vnu.edu.vn/dkmh/login.asp"
# The header repeats the same title; only divList3 contains actual course rows.
TRANSCRIPT_CELL = '#divList3 td[title="Mã môn học"]'


class DaotaoClient:
    """Operate inside a caller-owned, ephemeral Playwright browser context."""

    def __init__(self, context):
        self.context = context
        self.page = context.new_page()

    def login(self, username: str, password: str) -> None:
        """Submit the observed public form once; success needs user verification."""
        self.page.goto(LOGIN_URL, wait_until="domcontentloaded")
        self.page.locator("#txtLoginId").fill(username)
        self.page.locator("#txtPassword").fill(password)
        self.page.locator('#frmLogin input[type="submit"]').click()
        self.page.wait_for_load_state("domcontentloaded")

    def _wait_for_element(self, selector: str, timeout_ms: int):
        """Find a visible element even when showApp loads it in a child frame."""
        from playwright.sync_api import Error, TimeoutError

        deadline = monotonic() + timeout_ms / 1000
        while monotonic() < deadline:
            for page in self.context.pages:
                for frame in page.frames:
                    try:
                        for element in frame.locator(selector).all():
                            if element.is_visible():
                                return element
                    except Error:
                        if not frame.is_detached() and not page.is_closed():
                            raise
            sleep(0.2)
        raise TimeoutError("Không thấy mục xem điểm hoặc bảng điểm trong thời gian chờ.")

    def open_transcript(self, timeout_ms: int = 30000) -> None:
        """Wait for the authenticated menu and invoke its existing showApp handler."""
        menu = self._wait_for_element(
            '#PortalModule_374[title="Xem điểm sinh viên"]', timeout_ms
        )
        menu.click(timeout=timeout_ms)
        self._wait_for_element(TRANSCRIPT_CELL, timeout_ms)


