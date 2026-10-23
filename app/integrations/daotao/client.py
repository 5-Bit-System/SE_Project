"""Headed, session-only exploration of the VNU student portal."""

from time import monotonic, sleep
from urllib.parse import parse_qs, urlsplit

from app.integrations.daotao.parser import normalize_rows
from app.integrations.daotao.snapshot import PortalFailure, source_profile

LOGIN_URL = "https://daotao.vnu.edu.vn/dkmh/login.asp"
PROFILE_URL = "https://daotao.vnu.edu.vn/dkmh/default.asp"
# The header repeats the same title; only divList3 contains actual course rows.
TRANSCRIPT_CELL = '#divList3 td[title="Mã môn học"]'
PROFILE_MENU = ('[id^="PortalModule_"][title="Hồ sơ sinh viên"], '
                '[id^="PortalModule_"]:text-is("Hồ sơ sinh viên")')
PROFILE_LABELS = ("Họ và tên", "Họ tên", "Ngành học", "Ngành", "Khóa học", "Khoá học")
ENROLLMENT_MENU = ('[id^="PortalModule_"][title="Cập nhật hồ sơ sinh viên"], '
                   '[id^="PortalModule_"]:text-is("Cập nhật hồ sơ sinh viên")')


class DaotaoClient:
    """Operate inside a caller-owned, ephemeral Playwright browser context."""

    def __init__(self, context):
        self.context = context
        self.page = context.new_page()

    def login(self, username: str, password: str, timeout_ms: int = 30000) -> str:
        """Bind the submitted account to a fresh, accepted portal login transaction.

        A grade table alone is never authentication evidence. Existing cookies,
        pre-authenticated menus, missing/mismatched form POSTs and a remaining
        login form all fail closed.
        """
        if self.context.cookies(LOGIN_URL):
            raise PortalFailure("identity_unverified")
        self.page.goto(LOGIN_URL, wait_until="domcontentloaded")
        self._check_interaction()
        menu_selector = '#PortalModule_374[title="Xem điểm sinh viên"]'
        if self.page.locator(menu_selector).is_visible():
            raise PortalFailure("identity_unverified")
        form = self.page.locator("#frmLogin")
        target = form.evaluate("form => ({action: form.action, method: form.method})")
        action = urlsplit(target["action"])
        if (action.scheme != "https" or action.hostname != "daotao.vnu.edu.vn"
                or target["method"].casefold() != "post"):
            raise PortalFailure("identity_unverified")
        username_field = self.page.locator("#txtLoginId")
        field_name = username_field.get_attribute("name")
        if not field_name:
            raise PortalFailure("identity_unverified")
        username_field.fill(username)
        self.page.locator("#txtPassword").fill(password)
        def is_login_response(response):
            url = urlsplit(response.url)
            return (response.request.method == "POST" and url.scheme == "https"
                    and url.hostname == action.hostname and url.path == action.path)

        with self.page.expect_response(is_login_response, timeout=timeout_ms) as accepted:
            self.page.locator('#frmLogin input[type="submit"]').click()
        response = accepted.value
        submitted = parse_qs(response.request.post_data or "")
        if (not 200 <= response.status < 400
                or submitted.get(field_name) != [username]):
            raise PortalFailure("identity_unverified")
        self.page.wait_for_load_state("domcontentloaded")
        self._wait_for_element(menu_selector, timeout_ms)
        form.wait_for(state="hidden", timeout=timeout_ms)
        return username.strip().casefold()

    def _wait_for_element(self, selector: str, timeout_ms: int):
        """Find a visible element even when showApp loads it in a child frame."""
        from playwright.sync_api import Error, TimeoutError

        deadline = monotonic() + timeout_ms / 1000
        while monotonic() < deadline:
            self._check_interaction()
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

    def _check_interaction(self):
        """Recognize explicit visible challenges without guessing from body text."""
        from playwright.sync_api import Error

        selector = ('input[autocomplete="one-time-code"], '
                    'input[name*="captcha" i], input[id*="captcha" i], '
                    'iframe[src*="recaptcha"], iframe[src*="hcaptcha"], '
                    '.g-recaptcha, .h-captcha')
        for page in self.context.pages:
            for frame in page.frames:
                try:
                    if any(node.is_visible() for node in frame.locator(selector).all()):
                        raise PortalFailure("interaction_required")
                except Error:
                    if not frame.is_detached() and not page.is_closed():
                        raise

    def open_transcript(self, timeout_ms: int = 30000) -> None:
        """Wait for the authenticated menu and invoke its existing showApp handler."""
        menu = self._wait_for_element(
            '#PortalModule_374[title="Xem điểm sinh viên"]', timeout_ms
        )
        menu.click(timeout=timeout_ms)
        self._wait_for_element(TRANSCRIPT_CELL, timeout_ms)

    def read_profile_texts(self, timeout_ms: int = 30000) -> list[str]:
        """Open the source student profile before opening the transcript.

        Keep source text in worker memory only. The URL is fixed, never supplied
        by a browser request. No profile values are authentication evidence.
        """
        if self.page.url != PROFILE_URL:
            self.page.goto(PROFILE_URL, wait_until="domcontentloaded")
        self._wait_for_element('#PortalModule_374[title="Xem điểm sinh viên"]', timeout_ms)
        texts = [frame.locator("body").inner_text() for frame in self.page.frames]
        # default.asp is a shell: its existing menu handler loads the profile.
        # Use the observed menu label, never guess a module ID or frame URL.
        menus = [node for page in self.context.pages for frame in page.frames
                 for node in frame.locator(PROFILE_MENU).all() if node.is_visible()]
        if menus:
            menus[0].click(timeout=timeout_ms)
            deadline = monotonic() + timeout_ms / 1000
            while monotonic() < deadline:
                self._check_interaction()
                details = self._profile_cell_texts()
                if source_profile(details)["name"]:
                    texts.extend(details)
                    texts.extend(frame.locator("body").inner_text()
                                 for page in self.context.pages for frame in page.frames)
                    return [*texts, *self._enrollment_texts(timeout_ms)]
                sleep(0.2)
            from playwright.sync_api import TimeoutError

            raise TimeoutError("Student profile fields did not load.")
        # Preserve support for a landing page that already contains the profile.
        return [*texts, *self._profile_cell_texts(), *self._enrollment_texts(timeout_ms)]

    def _enrollment_texts(self, timeout_ms: int) -> list[str]:
        """Read the disabled management-class select; never edit/submit the form."""
        menus = [node for page in self.context.pages for frame in page.frames
                 for node in frame.locator(ENROLLMENT_MENU).all() if node.is_visible()]
        if not menus:
            return []
        menus[0].click(timeout=timeout_ms)
        deadline = monotonic() + timeout_ms / 1000
        while monotonic() < deadline:
            self._check_interaction()
            details = self._profile_cell_texts(labels=("Lớp quản lý",))
            if details:
                return details
            sleep(0.2)
        from playwright.sync_api import TimeoutError

        raise TimeoutError("Student enrollment fields did not load.")

    def _profile_cell_texts(self, labels=PROFILE_LABELS) -> list[str]:
        """Read allowlisted adjacent cells, including multi-column layout rows.

        Never flatten a whole row: it can contain unrelated personal fields.
        Nested layout cells and hidden controls are not profile values.
        """
        from playwright.sync_api import Error

        texts = []
        for page in self.context.pages:
            for frame in page.frames:
                try:
                    texts.extend(frame.locator("body").evaluate(r"""(body, labels) => {
                        const normalize = s => s.replace(/\s+/g, ' ').trim();
                        const results = [];
                        for (const cell of body.querySelectorAll('td, th')) {
                            if (!cell.getClientRects().length || cell.querySelector('table')) continue;
                            const label = normalize(cell.innerText).replace(/[:：]$/, '').trim();
                            if (!labels.includes(label)) continue;
                            const next = cell.nextElementSibling;
                            if (!next || !['TD', 'TH'].includes(next.tagName)
                                || !next.getClientRects().length || next.querySelector('table')) continue;
                            const controls = [...next.querySelectorAll('input, select, textarea')]
                                .filter(node => node.getClientRects().length && node.type !== 'hidden');
                            let value;
                            if (controls.length === 1) {
                                const node = controls[0];
                                if (node.tagName === 'SELECT') {
                                    value = node.selectedOptions.length === 1
                                        && node.selectedOptions[0].value
                                        ? node.selectedOptions[0].text : '';
                                } else if (node.tagName === 'TEXTAREA'
                                           || ['text', ''].includes(node.type)) value = node.value;
                            } else if (!controls.length) value = next.innerText;
                            if (value && !/[\r\n\t:：]/.test(value.trim())) {
                                results.push(label + '\t' + value.trim());
                            } else if (!value && label === 'Lớp quản lý') {
                                results.push(label + '\t');
                            }
                        }
                        return results;
                    }""", labels))
                except Error:
                    if not frame.is_detached() and not page.is_closed():
                        raise
        return texts

    def read_transcript(self, timeout_ms: int = 30000) -> list[list[str]]:
        """Read only the grade table, including semester headings and totals."""
        cell = self._wait_for_element(TRANSCRIPT_CELL, timeout_ms)
        table = cell.locator("xpath=ancestor::table[1]")
        rows = table.evaluate("""table => Array.from(table.rows)
            .filter(row => row.closest('table') === table)
            .map(row => Array.from(row.cells).map(cell => cell.innerText))""")
        return normalize_rows(rows)

    def read_tables(self, selector: str = "table") -> list[dict]:
        """Read visible tables from all open pages and their frames, in memory."""
        tables = []
        for page_index, page in enumerate(self.context.pages):
            for frame_index, frame in enumerate(page.frames):
                for table_index, table in enumerate(frame.locator(selector).all()):
                    if not table.is_visible():
                        continue
                    # Keep nested layout tables from duplicating their children's rows.
                    rows = table.evaluate("""table => Array.from(table.rows)
                        .filter(row => row.closest('table') === table)
                        .map(row => Array.from(row.cells).map(cell => cell.innerText))""")
                    rows = normalize_rows(rows)
                    if rows:
                        tables.append({
                            "page_index": page_index,
                            "frame_index": frame_index,
                            "table_index": table_index,
                            "rows": rows,
                        })
        return tables
