"""Headed, session-only exploration of the VNU student portal."""



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




