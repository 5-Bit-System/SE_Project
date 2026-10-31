"""Study motion with intercepted accounts, personal plans and source jobs."""

import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from tests.frontend.check_course_status import course
from tests.frontend.presentation_fixture import common_route


def book_clearance(page):
    """Independently check all text and controls, not the placement candidate list."""
    return page.evaluate("""() => {
      const book=document.querySelector('.study-book'), box=book.getBoundingClientRect();
      const visible=book.dataset.visible==='true' && getComputedStyle(book).display!=='none';
      if(!visible)return {visible:false,overlaps:[]};
      const hits=[],overlaps=r=>r.width>0 && r.height>0 && box.left<r.right && box.right>r.left && box.top<r.bottom && box.bottom>r.top;
      const panel=document.querySelector('.tab-panel.active');
      panel.querySelectorAll('button,input,select,textarea,table,progress,.workspace-surface,.academic-readiness,.profile-identity-strip').forEach(n=>{
        if(n.getClientRects().length && overlaps(n.getBoundingClientRect()))hits.push(n.id||n.className||n.tagName);
      });
      const walker=document.createTreeWalker(panel,NodeFilter.SHOW_TEXT);
      for(let n=walker.nextNode();n;n=walker.nextNode()){
        if(!n.textContent.trim()||n.parentElement.closest('[aria-hidden=true]'))continue;
        const range=document.createRange();range.selectNodeContents(n);
        if([...range.getClientRects()].some(overlaps))hits.push(n.parentElement.id||n.parentElement.tagName);
      }
      return {visible,width:box.width,height:box.height,overlaps:[...new Set(hits)]};
    }""")


def main():
    evidence = Path("backups/study_desk_motion_20261029")
    evidence.mkdir(parents=True, exist_ok=True)
    source = {"subject": "synthetic-study-only", "expires_in": 1800,
        "profile": {"name": "Sinh viên kiểm thử", "program": "Chương trình minh họa", "cohort": "79"},
        "snapshot": {"completeness": "complete", "unknown_rows": [], "source_summary": [], "attempts": [
            {"term": "HỌC KỲ 1 - 2099-2100", "code": "TEST001", "name": "Môn minh họa A",
             "credits": "3", "grade10": "8,5", "letter": "B+", "grade4": "3,5"},
            {"term": "HỌC KỲ 2 - 2099-2100", "code": "TEST002", "name": "Môn minh họa B",
             "credits": "3", "grade10": "7", "letter": "B", "grade4": "3"}]}}
    state = {"job": "running", "review": None}
    board = {"status": "ready", "context_revision": "synthetic-motion", "plan_basis": "a" * 64,
        "blocking_reasons": [], "selections": {}, "program_id": "synthetic-only",
        "courses": {"completed": [], "blocked": [], "eligible": [
            course("TEST-A", "Synthetic A", 3), course("TEST-B", "Synthetic B", 4)]},
        "progress": {"total": {"earned_credits": 0, "required_credits": 120, "remaining_credits": 120}},
        "plan": {"course_codes": ["TEST-A", "TEST-B"], "max_credits": 20, "suggested_credits": 7}}
    requests, errors, outside, clearance = [], [], [], []

    def intercept(route):
        parsed = urlparse(route.request.url)
        if parsed.hostname == "127.0.0.1" and common_route(route):
            return
        path = parsed.path
        if parsed.hostname != "127.0.0.1":
            outside.append(parsed.hostname)
            route.abort()
        elif path == "/me/profile":
            result = {**source, "latest_collection": state["review"]}
            route.fulfill(content_type="application/json", body=json.dumps(result))
        elif path == "/me/course-status":
            route.fulfill(json=board)
        elif path == "/me/portal-sync":
            requests.append("sync")
            route.fulfill(content_type="application/json", body='{"id":"synthetic-job"}')
        elif path == "/me/portal-sync/synthetic-job":
            result = {"state": state["job"]}
            if state["job"] == "failed":
                result["error"] = "incomplete_snapshot"
            route.fulfill(content_type="application/json", body=json.dumps(result))
        elif path.startswith(("/me/", "/auth/")):
            route.fulfill(content_type="application/json", body=json.dumps({
                "status": "needs_source_review", "courses": None,
                "blocking_reasons": ["program_binding_unverified"]}))
        else:
            route.abort()

    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="no-preference",
            **({"record_video_dir": str(evidence / "recording"), "record_video_size": {"width": 1280, "height": 800}} if os.environ.get("UI_RECORD_VIDEO") == "1" else {}))
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.add_init_script("""(() => {window.studyCalls=[];const original=Element.prototype.animate;
          Element.prototype.animate=function(frames,options){studyCalls.push({target:this.className?.baseVal||this.className,
            course:this.dataset?.planCourse,duration:options.duration});return original.call(this,frames,options);};})();""")
        page.route("**/*", intercept)
        page.goto("http://127.0.0.1:8000/?ui=study-desk#dashboard")
        page.wait_for_function("document.querySelector('.study-book').dataset.visible === 'true'")
        page.wait_for_timeout(650)
        assert page.locator(".study-book").count() == 1
        assert page.locator(".study-book").evaluate("n=>n.inert && getComputedStyle(n).pointerEvents==='none'")
        assert page.locator(".book-back").evaluate("n=>getComputedStyle(n).backfaceVisibility==='hidden'")
        assert page.locator(".book-turning-leaf").evaluate("n=>getComputedStyle(n).transformOrigin.startsWith('0px')")
        first = book_clearance(page)
        assert first["visible"] and not first["overlaps"], first

        # Observe at least two real front turns, 1.6s each in an 8s cycle.
        start, samples = time.monotonic(), []
        for step in range(10):
            due = start + step * 2
            page.wait_for_timeout(max(1, (due - time.monotonic()) * 1000))
            samples.append(page.locator(".book-turning-leaf").evaluate("n=>({time:n.getAnimations()[0].currentTime,transform:getComputedStyle(n).transform})"))
            page.screenshot(path=str(evidence / f"turn-{step * 2:02d}s.png"))
            print(f"Book observed: {step * 2}s", flush=True)
        assert samples[-1]["time"] - samples[0]["time"] >= 17900
        assert len({row["transform"] for row in samples}) >= 4
        observed_elapsed = time.monotonic() - start
        leaf = page.locator(".book-turning-leaf")
        page.evaluate("scrollTo(0,document.body.scrollHeight)")
        page.wait_for_function("document.querySelector('.study-book').dataset.paused === 'true'")
        assert leaf.evaluate("n=>getComputedStyle(n).animationPlayState==='paused'")
        page.evaluate("scrollTo(0,0)")

        # Keyboard and pointer ripple coordinates; repeated activation is bounded and cleaned.
        nav = page.locator("#tab-btn-profile")
        nav.focus()
        page.keyboard.press("Enter")
        ripple = nav.locator(".control-ripple")
        assert ripple.count() == 1
        assert ripple.evaluate("n=>Math.abs(parseFloat(n.style.left)-n.closest('button').clientWidth/2)<1")
        page.wait_for_timeout(450)
        target = page.locator("#tab-btn-dashboard")
        before = target.bounding_box()
        target.click(position={"x": 10, "y": 10})
        assert target.locator(".control-ripple").evaluate("n=>Math.abs(parseFloat(n.style.left)-10)<1")
        assert target.bounding_box() == before
        target.evaluate("n=>{for(let i=0;i<60;i++)n.click()}")
        assert page.locator(".control-ripple").count() <= 4
        page.wait_for_timeout(500)
        assert page.locator(".control-ripple, .control-feedback-layer").count() == 0

        for width in (1440, 1024, 390):
            page.set_viewport_size({"width": width, "height": 900})
            for theme in ("light", "dark"):
                page.locator(f'[data-theme-choice="{theme}"]').click()
                for route in ("dashboard", "profile", "rules", "recommend"):
                    page.locator(f"#tab-btn-{route}").click()
                    page.wait_for_timeout(300)
                    report = book_clearance(page)
                    clearance.append({"viewport": width, "theme": theme, "route": route, **report})
                    assert not report["overlaps"], clearance[-1]
                    assert page.evaluate("document.documentElement.scrollWidth<=innerWidth")
                    if width == 390:
                        assert page.locator(".study-book").evaluate("n=>getComputedStyle(n).display==='none'")
                    page.evaluate("scrollTo(0,0)")
                    page.screenshot(path=str(evidence / f"{route}-{theme}-{width}.png"), animations="disabled")
                    page.locator('[data-language-choice="en"]').click()
                    page.wait_for_timeout(80)
                    english = book_clearance(page)
                    assert not english['overlaps'], (width, theme, route, english)
                    page.locator('[data-language-choice="vi"]').click()
                    page.wait_for_timeout(80)
        page.set_viewport_size({"width": 1440, "height": 900})
        page.locator('[data-theme-choice="light"]').click()
        page.locator("#tab-btn-rules").click()
        page.wait_for_selector('[data-plan-course="TEST-A"]')
        assert page.locator('.course-status-columns input[type=checkbox]').count() == 0
        page.wait_for_selector('[data-plan-course="TEST-B"]')
        page.locator('[data-plan-course="TEST-A"] button').click()
        page.wait_for_selector('.plan-exit-ghost')
        assert page.locator('.plan-exit-ghost').first.evaluate("n=>n.inert && n.getAttribute('aria-hidden')==='true'")
        assert page.evaluate("studyCalls.some(x=>x.course==='TEST-B' && x.duration===220)")
        assert "4 / 20" in page.locator('.course-status-summary > div:nth-child(2) strong').inner_text()
        page.wait_for_timeout(300)
        assert page.locator('.plan-exit-ghost').count() == 0
        search = page.locator('#course-status-board input[type=search]')
        search.fill('NO-MATCH-SYNTHETIC')
        assert page.locator('.course-status-card').count() == 0
        search.fill('')

        # Loading is tied to a real mocked job; a retained/failed collection never celebrates.
        page.locator('#tab-btn-profile').click()
        assert page.locator('.status-success').count() == 0
        page.evaluate("document.dispatchEvent(new Event('workspace:portal-begin-sync'))")
        page.wait_for_selector('.book-loader')
        assert page.locator('#portal-status').get_attribute('role') == 'status'
        assert page.locator('.book-loader').get_attribute('aria-hidden') == 'true'
        assert page.locator('.status-success').count() == 0
        page.evaluate('scrollTo(0,document.body.scrollHeight)')
        page.wait_for_function("document.querySelector('.book-loader')?.dataset.paused==='true'")
        page.locator('#portal-status').scroll_into_view_if_needed()
        page.wait_for_function("document.querySelector('.book-loader')?.dataset.paused==='false'")
        page.evaluate("Object.defineProperty(document,'hidden',{configurable:true,value:true});document.dispatchEvent(new Event('visibilitychange'))")
        assert page.locator('.loader-turn').evaluate("n=>getComputedStyle(n).animationPlayState==='paused'")
        page.evaluate("delete document.hidden;document.dispatchEvent(new Event('visibilitychange'))")
        page.screenshot(path=str(evidence / 'loader.png'))
        state['review'] = {"save_status": "saved", "completeness": "complete", "unparsed_rows": 0}
        state['job'] = 'done'
        page.wait_for_selector('.status-success')
        assert page.locator('#portal-status').inner_text()
        page.screenshot(path=str(evidence / 'success.png'))
        state['job'] = 'running'
        page.evaluate("document.dispatchEvent(new Event('workspace:portal-begin-sync'))")
        page.wait_for_selector('.book-loader')
        state['review'] = {"save_status": "retained", "completeness": "unknown", "unparsed_rows": 0}
        state['job'] = 'failed'
        page.wait_for_function("document.getElementById('portal-status').dataset.feedback==='error'")
        assert page.locator('.status-success,.book-loader').count() == 0
        assert 'Giữ nguyên' in page.locator('#portal-status').inner_text()

        page.emulate_media(reduced_motion='reduce')
        page.locator('#tab-btn-dashboard').click()
        page.wait_for_timeout(50)
        assert page.locator('.book-turning-leaf').evaluate("n=>n.getAnimations().length===0")
        assert page.locator('.control-ripple').count() == 0
        assert page.locator('#tab-dashboard .dashboard-heading').evaluate("n=>getComputedStyle(n).opacity==='1'")
        for _ in range(12):
            page.locator('#tab-btn-profile').click()
            page.locator('#tab-btn-dashboard').click()
        assert page.locator('.study-book,.ambient-background,.navigation-indicator').count() == 3
        assert page.locator('.plan-exit-ghost,.control-feedback-layer').count() == 0
        page.screenshot(path=str(evidence / 'reduced-motion.png'))
        video = page.video
        context.close()
        if video:
            video.save_as(str(evidence / 'study-desk-preview.webm'))
        detail = browser.new_page(viewport={"width": 1440, "height": 900}, device_scale_factor=3)
        detail.route('**/*', intercept)
        detail.goto('http://127.0.0.1:8000/#dashboard')
        detail.wait_for_function("document.querySelector('.study-book').dataset.visible==='true'")
        detail.locator('.study-book *').evaluate_all('nodes=>nodes.forEach(n=>n.getAnimations().forEach(a=>a.pause()))')
        transforms = []
        for phase in (0, 2000, 2500, 6000, 7999):
            detail.locator('.book-turning-leaf,.book-leaf-face').evaluate_all('(nodes,t)=>nodes.forEach(n=>n.getAnimations().forEach(a=>a.currentTime=t))', phase)
            # Shading lives on the faces' pseudo elements.
            detail.evaluate('t=>document.getAnimations().filter(a=>a.effect.target.closest?.(".study-book")).forEach(a=>{if(a.animationName==="study-page-shade")a.currentTime=t})', phase)
            if phase in (0, 7999):
                transforms.append(detail.locator('.book-turning-leaf').evaluate('n=>getComputedStyle(n).transform'))
            if phase == 6000:
                assert detail.locator('.book-turning-leaf').evaluate('n=>getComputedStyle(n).opacity === "0"')
            detail.locator('.study-book').screenshot(path=str(evidence / f'book-phase-{phase}.png'))
        assert transforms[0] == transforms[1], transforms
        browser.close()
    assert not errors, errors
    assert not outside, outside
    (evidence / 'verification.json').write_text(json.dumps({
        "observed_seconds": observed_elapsed, "page_turn_samples": samples,
        "clearance": clearance, "sync_jobs": len(requests), "outbound_requests": 0,
        "privacy": "invented records; all HTTP requests intercepted",
    }, indent=2), encoding='utf-8')
    print('Study desk: two turns observed; clearance, ripples/keyboard/cleanup, plan effects, loader/success/error, mobile/themes/reduced passed')


if __name__ == '__main__':
    main()
