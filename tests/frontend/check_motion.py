"""Observe real CSS/WAAPI motion for a full cycle; only invented personal data."""

import base64
import json
import os
import time
from pathlib import Path
from urllib.parse import urlparse

from playwright.sync_api import sync_playwright

from tests.frontend.presentation_fixture import common_route


def background_contrast(page):
    """Sample rendered gradient/glass pixels, including compositing, without Pillow."""
    results = []
    for theme in ("light", "dark"):
        page.locator(f'[data-theme-choice="{theme}"]').click()
        for seconds in (0, 10, 20, 30):
            page.locator(".ambient-orb").evaluate_all(
                "(nodes,t)=>nodes.forEach(n=>n.getAnimations().forEach(a=>{a.pause();a.currentTime=t}))",
                seconds * 1000)
            nodes = page.evaluate("""() => ['#tab-dashboard .dashboard-heading p:last-child','.page-context',
              '#analytics-status','.selector-label','.sidebar-profile span','.tab-btn:not(.active)'].map(selector=>{
                const n=document.querySelector(selector), r=n.getBoundingClientRect(), color=getComputedStyle(n).color;
                n.style.visibility='hidden'; return {selector,x:r.x,y:r.y,width:r.width,height:r.height,color};
              })""")
            png = base64.b64encode(page.screenshot()).decode()
            try:
                values = page.evaluate("""async ({png,nodes})=>{
                  const image=new Image();image.src='data:image/png;base64,'+png;await image.decode();
                  const canvas=document.createElement('canvas');canvas.width=image.width;canvas.height=image.height;
                  const context=canvas.getContext('2d');context.drawImage(image,0,0);
                  const lum=rgb=>rgb.slice(0,3).map(v=>{v/=255;return v<=.04045?v/12.92:((v+.055)/1.055)**2.4})
                    .reduce((s,v,i)=>s+v*[.2126,.7152,.0722][i],0);
                  return nodes.map(n=>{const foreground=lum(n.color.match(/[0-9.]+/g).map(Number));let minimum=100;
                    for(let x=n.x+2;x<n.x+n.width-2;x+=8)for(let y=n.y+2;y<n.y+n.height-2;y+=4){
                      const background=lum([...context.getImageData(Math.floor(x),Math.floor(y),1,1).data]);
                      minimum=Math.min(minimum,(Math.max(foreground,background)+.05)/(Math.min(foreground,background)+.05));
                    }return {selector:n.selector,minimum:Math.round(minimum*100)/100};
                  });
                }""", {"png": png, "nodes": nodes})
            finally:
                page.evaluate('(nodes)=>nodes.forEach(n=>document.querySelector(n.selector).style.visibility="")', nodes)
            results.extend({"theme": theme, "phase_seconds": seconds, **value} for value in values)
    assert min(row["minimum"] for row in results) >= 4.5, results
    return results


def main():
    evidence = Path("backups/frontend_motion_20261029")
    evidence.mkdir(parents=True, exist_ok=True)
    profile = {
        "subject": "synthetic-motion-only", "expires_in": 1800,
        "profile": {"name": "Sinh viên kiểm thử", "program": "Chương trình minh họa", "cohort": "79"},
        "snapshot": {"completeness": "complete", "source_summary": [], "unknown_rows": [],
            "attempts": [
                {"term": "HỌC KỲ 1 - 2099-2100", "code": "TEST001", "name": "Học phần minh họa A",
                 "credits": "3", "grade10": "8,5", "letter": "B+", "grade4": "3,5"},
                {"term": "HỌC KỲ 1 - 2100-2101", "code": "TEST002", "name": "Học phần minh họa B",
                 "credits": "3", "grade10": "7", "letter": "B", "grade4": "3"}]},
    }
    pending, errors, outside = [], [], []
    source_ready = False

    def intercept(route):
        parsed = urlparse(route.request.url)
        if parsed.hostname == "127.0.0.1" and common_route(route):
            return
        if parsed.hostname != "127.0.0.1":
            outside.append(parsed.hostname)
            route.abort()
        elif parsed.path == "/me/profile":
            if source_ready:
                route.fulfill(content_type="application/json", body=json.dumps(profile))
            else:
                pending.append(route)
        elif parsed.path.startswith(("/me/", "/auth/")):
            route.fulfill(content_type="application/json", body=json.dumps({
                "status": "needs_source_review", "courses": None,
                "blocking_reasons": ["program_binding_unverified"]}))
        elif parsed.path == "/" or parsed.path.startswith(("/static/", "/curricula/reference")):
            route.continue_()
        else:
            route.abort()

    audit = """(() => {
      window.motionCalls = [];
      const original = Element.prototype.animate;
      Element.prototype.animate = function(frames, options) {
        window.motionCalls.push({target: this.id || this.getAttribute('class'),
          duration: options.duration, delay: options.delay || 0, keys: Object.keys(frames[0])});
        return original.call(this, frames, options);
      };
    })();"""
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome", headless=True)
        context = browser.new_context(viewport={"width": 1440, "height": 900},
            reduced_motion="no-preference", color_scheme="light",
            **({"record_video_dir": str(evidence / "recording"), "record_video_size": {"width": 1280, "height": 800}} if os.environ.get("UI_RECORD_VIDEO") == "1" else {}))
        page = context.new_page()
        page.add_init_script(audit)
        page.on("pageerror", lambda error: errors.append(str(error)))
        page.route("**/*", intercept)
        page.goto("http://127.0.0.1:8000/?ui=ambient-motion#dashboard", wait_until="domcontentloaded")
        assert page.locator("html").get_attribute("data-ui-revision") == "20261029-study-desk"
        assert page.locator(".ambient-background").get_attribute("aria-hidden") == "true"
        assert page.locator(".ambient-background").evaluate("n => n.inert && getComputedStyle(n).pointerEvents === 'none'")
        assert page.locator(".ambient-orb").count() == 3
        assert page.locator(".ambient-orb").evaluate_all(
            "nodes => nodes.every(n => n.getAnimations().length === 1 && getComputedStyle(n).animationPlayState === 'running')")
        assert page.locator(".workspace-sidebar").evaluate(
            "n => parseFloat(getComputedStyle(n).backdropFilter.replace(/[^0-9.]/g,'')) === 12")
        page.wait_for_function("motionCalls.some(call => call.duration === 420 && call.delay === 60)")
        page.wait_for_function("document.querySelector('.navigation-indicator').clientWidth > 0")
        source_ready = True
        for route in pending:
            route.fulfill(content_type="application/json", body=json.dumps(profile))
        page.wait_for_function("motionCalls.some(call => call.target === 'chart-trend-line' && call.duration === 700)")
        assert page.evaluate("motionCalls.some(call => call.target === 'credit-chart-bar' && call.duration === 650)")
        assert page.evaluate("motionCalls.some(call => call.target === null && call.duration === 650)")
        page.wait_for_timeout(950)
        before_hover = page.evaluate("motionCalls.length")
        page.locator(".chart-point").first.hover()
        page.wait_for_timeout(100)
        assert page.evaluate("motionCalls.length") == before_hover
        page.mouse.move(0, 0)

        # Real wall time, not a sped-up animation clock: longest background period is 30s.
        samples, start = [], time.monotonic()
        for frame in range(7):
            due = start + frame * 5
            page.wait_for_timeout(max(1, (due - time.monotonic()) * 1000))
            samples.append(page.locator(".ambient-orb").evaluate_all("""nodes => nodes.map(n => ({
              transform: getComputedStyle(n).transform, time: n.getAnimations()[0].currentTime,
              duration: n.getAnimations()[0].effect.getTiming().duration
            }))"""))
            page.screenshot(path=str(evidence / f"cycle-{frame * 5:02d}s.png"))
            print(f"Background observed: {frame * 5}s", flush=True)
        elapsed = time.monotonic() - start
        assert elapsed >= 30
        for index, duration in enumerate((24000, 28000, 30000)):
            assert samples[0][index]["duration"] == duration
            assert samples[-1][index]["time"] - samples[0][index]["time"] >= 29900
            assert len({sample[index]["transform"] for sample in samples}) >= 5
        assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
        background_box = page.locator(".ambient-background").bounding_box()
        page.evaluate("scrollTo(0, document.body.scrollHeight)")
        assert page.locator(".ambient-background").bounding_box() == background_box
        page.screenshot(path=str(evidence / "scrolled-background.png"))
        page.evaluate("scrollTo(0,0)")

        page.locator("#tab-btn-profile").click()
        assert page.locator("#tab-btn-profile").get_attribute("aria-selected") == "true"
        page.wait_for_timeout(260)
        indicator = page.locator(".navigation-indicator").bounding_box()
        selected = page.locator("#tab-btn-profile").bounding_box()
        assert abs(indicator["y"] - selected["y"]) < 1
        assert "8,5" in page.locator("#portal-table").inner_text()
        button = page.locator("#portal-sync")
        button.hover()
        page.wait_for_timeout(240)
        assert button.evaluate("n => getComputedStyle(n).boxShadow !== 'none'")
        box = button.bounding_box()
        page.mouse.move(box["x"] + 10, box["y"] + 10)
        page.mouse.down()
        page.wait_for_timeout(200)
        assert button.evaluate("n => getComputedStyle(n).transform !== 'none'")
        page.mouse.move(0, 0)
        page.mouse.up()

        page.locator("#tab-btn-dashboard").click()
        page.wait_for_timeout(300)
        page.locator("#analytics-year").select_option("2099–2100")
        page.wait_for_timeout(50)
        assert page.locator("#tab-dashboard .dashboard-heading").evaluate("n => n.getAnimations().length === 0")
        page.locator("#analytics-year").select_option("")
        page.locator(".analytics-data-table summary").click()
        page.wait_for_timeout(260)
        assert page.locator("#analytics-table").is_visible()
        page.locator(".analytics-data-table summary").click()
        page.wait_for_timeout(260)
        assert page.locator("#analytics-table").is_hidden()

        for width in (1440, 1024, 390):
            page.set_viewport_size({"width": width, "height": 900})
            for theme in ("light", "dark"):
                page.locator(f'[data-theme-choice="{theme}"]').click()
                page.locator("#tab-btn-dashboard").click()
                page.wait_for_timeout(260)
                assert page.evaluate("document.documentElement.scrollWidth <= innerWidth")
                if width == 390:
                    assert page.locator(".ambient-rose").evaluate("n => getComputedStyle(n).display === 'none'")
                page.evaluate("scrollTo(0,0)")
                page.screenshot(path=str(evidence / f"motion-{theme}-{width}.png"))
        page.emulate_media(reduced_motion="reduce")
        page.wait_for_timeout(50)
        assert page.locator(".ambient-orb").evaluate_all("nodes => nodes.every(n => n.getAnimations().length === 0 && getComputedStyle(n).transform === 'none')")
        assert page.locator(".navigation-indicator").evaluate("n => getComputedStyle(n).transitionDuration === '0s'")
        baseline = page.evaluate("motionCalls.length")
        page.locator("#tab-btn-profile").click()
        assert page.locator("#portal-heading").evaluate("n => getComputedStyle(n).opacity === '1'")
        assert page.evaluate("motionCalls.length") == baseline
        page.screenshot(path=str(evidence / "reduced-motion-390.png"))
        calls = page.evaluate("motionCalls")
        video = page.video
        context.close()
        if video:
            video.save_as(str(evidence / "ambient-cycle-and-interactions.webm"))

        # If the enhancement script cannot load, the existing UI stays visible/usable.
        fallback = browser.new_page(viewport={"width": 1024, "height": 900})
        fallback.route("**/*", intercept)
        fallback.route("**/static/motion.js*", lambda route: route.abort())
        fallback.goto("http://127.0.0.1:8000/#dashboard")
        assert fallback.locator("#tab-dashboard .dashboard-heading").is_visible()
        assert fallback.locator("#tab-dashboard .dashboard-heading").evaluate("n => getComputedStyle(n).opacity === '1'")
        fallback.locator("#tab-btn-profile").click()
        assert fallback.locator("#portal-heading").is_visible()
        fallback.locator("#tab-btn-dashboard").click()
        fallback.wait_for_selector(".chart-trend-line")
        fallback.wait_for_function("document.fonts.status === 'loaded'")
        contrast = background_contrast(fallback)
        browser.close()
    assert not errors, errors
    assert not outside, outside
    (evidence / "rendered-background-contrast.json").write_text(json.dumps(contrast, indent=2), encoding="utf-8")
    (evidence / "verification.json").write_text(json.dumps({
        "real_observation_seconds": elapsed, "samples": samples, "animation_calls": calls,
        "outbound_requests": 0, "privacy": "invented records only; no VNU calls",
        "rendered_text_contrast_minimum": min(row["minimum"] for row in contrast),
        "verified": ["ambient cycle", "glass", "entrance", "navigation indicator", "buttons",
                     "SVG line/bar/donut", "no hover replay", "no filter entrance replay", "accordion",
                     "scroll continuity", "mobile/themes", "reduced motion", "JS fallback"],
    }, indent=2), encoding="utf-8")
    print("Motion: full 30s cycle observed; glass, interaction, charts, focus, mobile, reduced motion and fallback passed")


if __name__ == "__main__":
    main()
