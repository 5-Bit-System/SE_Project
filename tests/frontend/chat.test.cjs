const assert = require("node:assert/strict");
const { readFileSync } = require("node:fs");
const path = require("node:path");
const test = require("node:test");
const vm = require("node:vm");

function element(tag) {
  return {
    tag, children: [], textContent: "", disabled: false,
    classList: { add() {} },
    get childElementCount() { return this.children.length; },
    appendChild(child) { child.parent = this; this.children.push(child); },
    replaceChildren() { this.children = []; },
    remove() {
      if (this.parent) this.parent.children = this.parent.children.filter(child => child !== this);
    },
  };
}

function setup() {
  const source = readFileSync(path.join(__dirname, "../../app/static/app.js"), "utf8");
  // Execute the actual chat event handler/render helpers, without bootstrapping the page.
  const block = source.slice(source.indexOf('dom.advisorChatForm.addEventListener("submit"'),
                             source.indexOf("// Prompt Chips"));
  assert.ok(block.length > 100);
  let submit;
  const pending = [];
  const state = { currentProgramId: "old", chatContextId: 0, chatHistory: [], transcript: new Map() };
  const dom = {
    advisorChatForm: { addEventListener(name, handler) { submit = handler; } },
    advisorInputText: { value: "Giới thiệu ngành" }, btnSendChat: element("button"),
    husGeneratedOptIn: { checked: false },
    chatMessagesContainer: element("div"),
  };
  const context = vm.createContext({ state, dom, URL, document: { createElement: element, baseURI: "http://localhost:8000/" },
    api: (url, options) => new Promise(resolve => pending.push({ resolve, body: JSON.parse(options.body) })),
  });
  vm.runInContext(block, context);
  return { state, dom, context, pending, submit: () => submit({ preventDefault() {} }) };
}

test("citations use text and HTTP(S) links only, without duplicate source links", () => {
  const { dom, context } = setup();
  const good = { citation_id: "1", label: "<img onerror=alert(1)>", evidence_kind: "web",
    source_url: "https://example.test/source", open_url: "https://example.test/source" };
  context.appendChatMessage("advisor", "<script>not executed</script>", false, [
    good, good, { ...good, source_url: "javascript:alert(1)" }, { ...good, source_url: null },
  ]);
  const bubble = dom.chatMessagesContainer.children[0].children[0];
  assert.equal(bubble.textContent, "<script>not executed</script>");
  const links = bubble.children[0].children.filter(item => item.children[0].tag === "a");
  assert.equal(links.length, 1);
  const link = links[0].children[0];
  assert.equal(link.href, "https://example.test/source");
  assert.match(link.rel, /noopener/);
  assert.ok(link.textContent.includes(good.label));
});

test("AI and unavailable evidence remain visible; PDF pages do not collapse", () => {
  const { dom, context } = setup();
  const sha = "a".repeat(64);
  const pdf = { citation_id: "1", label: "PDF", source_id: sha, document_sha256: sha,
    evidence_kind: "pdf", availability: "available", pdf_pages: [3],
    open_url: `/hus/sources/${sha}?page=3#page=3` };
  context.appendChatMessage("advisor", "Answer", false, [pdf, pdf,
    { ...pdf, citation_id: "2", pdf_pages: [4], open_url: `/hus/sources/${sha}?page=4#page=4` },
    { ...pdf, citation_id: "3", content_origin: "generated", evidence_kind: "pdf" },
    { ...pdf, citation_id: "4", availability: "missing", open_url: null, availability_note: "Missing binary" },
    { ...pdf, citation_id: "5", open_url: `https://evil.test/hus/sources/${sha}` },
  ]);
  const items = dom.chatMessagesContainer.children[0].children[0].children[0].children;
  const links = items.map(item => item.children[0]).filter(item => item.tag === "a");
  assert.equal(links.length, 2);
  assert.match(links[0].href, /page=3#page=3$/);
  assert.match(links[1].href, /page=4#page=4$/);
  const textItems = items.map(item => item.children[0]).filter(item => item.tag === "span");
  assert.ok(textItems.some(item => item.textContent.includes("kiến thức AI")));
  assert.ok(textItems.some(item => item.textContent.includes("Missing binary")));
});

test("a successful API response renders AI evidence with explicit null open_url", async () => {
  const { dom, pending, submit } = setup();
  const response = submit();
  pending[0].resolve({ mode: "hus_rag", reply: "Nội dung tham khảo có cảnh báo", hus_answer: {
    citations: [{ citation_id: "1", label: "kiến thức AI — MAT3533", display_label: "kiến thức AI",
      dataset: "f3", evidence_kind: "ai", content_origin: "generated", availability: "available",
      source_url: null, open_url: null, document_sha256: null, pdf_page: null, pdf_pages: [],
      metadata: { course_code: "MAT3533" }, review_status: "needs_review" }],
  }});
  await response;
  const message = dom.chatMessagesContainer.children.at(-1);
  const items = message.children[0].children[0].children;
  assert.equal(items.length, 1);
  assert.equal(items[0].children[0].tag, "span");
  assert.equal(items[0].children[0].href, undefined);
  assert.match(items[0].children[0].textContent, /kiến thức AI.*MAT3533.*needs_review/);
});

test("old-context replies cannot restore history or enable a newer pending request", async () => {
  const { state, dom, context, pending, submit } = setup();
  const first = submit();
  state.currentProgramId = "new";
  context.resetChatContext();
  dom.advisorInputText.value = "Nội dung MAT3533";
  const second = submit();
  assert.equal(pending[0].body.program_id, "old");
  assert.equal(pending[1].body.program_id, "new");
  pending[0].resolve({ mode: "hus_rag", reply: "STALE ANSWER" });
  await first;
  assert.equal(dom.btnSendChat.disabled, true);
  assert.ok(!state.chatHistory.some(message => message.content === "STALE ANSWER"));
  pending[1].resolve({ mode: "hus_rag", reply: "F3 do AI sinh — NEW ANSWER", hus_answer: { citations: [] } });
  await second;
  assert.equal(dom.btnSendChat.disabled, false);
  assert.equal(state.chatHistory.length, 2);
  assert.equal(state.chatHistory[1].content, "F3 do AI sinh — NEW ANSWER");
  assert.equal(dom.chatMessagesContainer.children.length, 2);
});

test("generated reference opt-in is explicit and reset with the conversation context", async () => {
  const { dom, context, pending, submit } = setup();
  const first = submit();
  assert.equal(pending[0].body.allow_generated_reference, false);
  pending[0].resolve({ mode: "hus_rag", reply: "Reference disabled" });
  await first;
  dom.husGeneratedOptIn.checked = true;
  dom.advisorInputText.value = "Nội dung MAT3533";
  const second = submit();
  assert.equal(pending[1].body.allow_generated_reference, true);
  pending[1].resolve({ mode: "hus_rag", reply: "Reference allowed" });
  await second;
  context.resetChatContext();
  assert.equal(dom.husGeneratedOptIn.checked, false);
});
