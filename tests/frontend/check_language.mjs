// Browser regression: Node 22+ and an existing Chrome DevTools endpoint.
// Run with the app on APP_URL and Chrome on CDP_URL (defaults below).
import assert from 'node:assert/strict';
const appUrl = process.env.APP_URL || 'http://127.0.0.1:8000/';
const cdpUrl = process.env.CDP_URL || 'http://127.0.0.1:19222';
const targets = await (await fetch(cdpUrl + '/json')).json();
const target = targets.find(item => item.type === 'page');
assert.ok(target, 'Chrome needs an open page');
const ws = new WebSocket(target.webSocketDebuggerUrl);
await new Promise(resolve => ws.addEventListener('open', resolve, {once: true}));
let id = 0;
const pending = new Map(), errors = [];
ws.addEventListener('message', event => {
  const message = JSON.parse(event.data);
  if (message.method === 'Runtime.exceptionThrown') errors.push(message.params);
  if (!message.id) return;
  const task = pending.get(message.id);
  pending.delete(message.id);
  message.error ? task.reject(message.error) : task.resolve(message.result);
});
const call = (method, params = {}) => new Promise((resolve, reject) => {
  const next = ++id; pending.set(next, {resolve, reject});
  ws.send(JSON.stringify({id: next, method, params}));
});
const evaluate = async expression => {
  const result = await call('Runtime.evaluate', {expression, awaitPromise: true, returnByValue: true});
  assert.ok(!result.exceptionDetails, JSON.stringify(result.exceptionDetails));
  return result.result.value;
};
const wait = async expression => {
  for (let attempt = 0; attempt < 100; attempt++) {
    if (await evaluate(expression)) return;
    await new Promise(resolve => setTimeout(resolve, 100));
  }
  assert.fail('Timed out: ' + expression);
};
const language = async value => {
  await evaluate(`dom.courseLanguageSelect.value='${value}';dom.courseLanguageSelect.dispatchEvent(new Event('change'))`);
  await wait(`document.documentElement.lang==='${value}'`);
};

try {
  await call('Runtime.enable'); await call('Page.enable');
  await call('Emulation.setDeviceMetricsOverride', {width: 1440, height: 1080, deviceScaleFactor: 1, mobile: false});
  await call('Page.navigate', {url: appUrl});
  await wait('typeof state!=="undefined" && state.courses.length>0');
  await language('vi');
  assert.equal(await evaluate('document.getElementById("appearance-label").textContent'), 'Giao diện');
  await evaluate('document.querySelector("#course-checklist-container .btn-ghost").click();dom.recGoal.value="Keep my original goal"');
  await wait('state.transcript.size===1');
  const original = await evaluate('JSON.stringify([...state.transcript])');
  for (let iteration = 0; iteration < 3; iteration++) {
    await language('en');
    assert.equal(await evaluate('document.getElementById("appearance-label").textContent'), 'Appearance');
    assert.equal(await evaluate('document.querySelector(".app-title").textContent'), 'Study workspace');
    assert.equal(await evaluate('document.querySelector("#semester-tables thead th").textContent'), 'No.');
    assert.equal(await evaluate('document.querySelector("[data-theme-choice=dark]").getAttribute("aria-label")'), 'Dark appearance');
    assert.equal(await evaluate('JSON.stringify([...state.transcript])'), original);
    assert.equal(await evaluate('dom.recGoal.value'), 'Keep my original goal');
    await language('vi');
    assert.equal(await evaluate('document.querySelector(".app-title").textContent'), 'Sổ học tập');
    assert.equal(await evaluate('document.querySelector("#semester-tables thead th").textContent'), 'STT');
  }
  await language('en');
  await wait('dom.rulesBlockedList.textContent.includes("Missing prerequisites:")');
  // Confirm both the sourced English name and the explicit fallback branch.
  await evaluate('state.courses[0].name_en="Synthetic English title";renderCourseChecklist()');
  assert.equal(await evaluate('document.querySelector("#semester-tables .course-code-name").textContent'), 'Synthetic English title');
  await evaluate('state.courses[0].name_en=null;renderCourseChecklist()');
  assert.equal(await evaluate('document.querySelector("#semester-tables .course-code-name").textContent===state.courses[0].name'), true);
  assert.equal(await evaluate('document.getElementById("course-language-note").hidden'), false);
  await evaluate('document.querySelector("#term-year").value="2025";document.querySelector("#term-number").value="2";document.querySelector("#btn-add-term").click()');
  await wait('termSelect.selectedOptions[0].textContent.includes("Semester 2")');
  // Source course titles and grades must not be translated or collapsed.
  await evaluate('showPortalTranscript({terms:[{year:2025,semester:2,code:"252",courses:[{code:"TEST001",name:"Sáng",credits:3,grade:4.9,letter:"D",grade4:1}]}]})');
  await wait('document.querySelector(".portal-term-heading").textContent.includes("Term code 252")');
  assert.equal(await evaluate('document.querySelector(".portal-transcript-table td:nth-child(3)").textContent'), 'Sáng');
  assert.equal(await evaluate('document.querySelector(".portal-transcript-table td:nth-child(5)").textContent'), '4.9');
  await language('vi'); await language('en');
  assert.equal(await evaluate('document.querySelector(".portal-transcript-table td:nth-child(3)").textContent'), 'Sáng');
  await evaluate('document.querySelector("#btn-manual-transcript").click();dom.programSelect.selectedIndex=1;dom.programSelect.dispatchEvent(new Event("change"))');
  await wait('state.courses.length>0 && state.transcript.size===0 && !document.querySelector(".portal-transcript-table")');
  await wait('dom.profileSelect.options[0].textContent.includes("No demo")');
  await evaluate('document.getElementById("tab-btn-recommend").click();dom.recommendForm.requestSubmit()');
  await wait('!document.getElementById("btn-run-recommend").disabled && document.querySelectorAll(".recommendation-card").length>0');
  await wait('dom.recBadgeCount.textContent.includes("recommendations")');
  assert.equal(await evaluate('document.querySelector(".rec-reason").textContent.startsWith("Eligibility:")'), true);
  await evaluate('dom.btnRunWhatIf.click()');
  await wait('!dom.btnRunWhatIf.disabled && dom.recommendationSummary.textContent.includes("Mode")');
  await evaluate('dom.advisorBubbleBtn.click();dom.btnMaximizeChat.click()');
  await wait('dom.btnMaximizeChat.getAttribute("aria-label")==="Restore"');
  await evaluate('dom.btnCloseChat.click();document.querySelector("[data-theme-choice=dark]").click()');
  await call('Emulation.setDeviceMetricsOverride', {width: 390, height: 844, deviceScaleFactor: 1, mobile: true});
  assert.equal(await evaluate('document.documentElement.scrollWidth>innerWidth'), false);
  await call('Page.reload');
  await wait('typeof state!=="undefined" && state.courses.length>0 && document.documentElement.lang==="en"');
  assert.equal(await evaluate('state.courseLanguage'), 'en');
  assert.equal(await evaluate('dom.courseLanguageSelect.value'), 'en');
  assert.equal(await evaluate('document.querySelector(".app-title").textContent'), 'Study workspace');
  assert.equal(await evaluate('document.documentElement.dataset.theme'), 'dark');
  assert.deepEqual(errors, []);
  console.log('PASS: labels, English/Vietnamese UI, source fallback, async content, source preservation, persistence and mobile layout');
} finally {
  ws.close();
}
