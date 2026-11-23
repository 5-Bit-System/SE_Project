const assert = require('node:assert/strict');
const test = require('node:test');
const {
  citationURL,
  citationLabel,
  displayReply,
  generationInfo,
  escapeHtml,
  formatInlineMarkdown,
  renderSafeMarkdown,
  groupCitations,
} = require('../../app/static/hus-rag-demo.js');
const {
  isFollowUpCourseQuery,
  extractCourseCode,
} = require('../../app/static/hus-lookup.js');
const origin = 'http://127.0.0.1:8000';
const sha = 'a'.repeat(64);
const pdf = page => ({evidence_kind:'pdf', availability:'available', document_sha256:sha,
  pdf_page:page, open_url:`/hus/sources/${sha}?page=${page}#page=${page}`});

test('web citation opens only its original safe HTTP URL', () => {
  const c = {evidence_kind:'web', source_url:'https://example.test/source', open_url:'https://example.test/source'};
  assert.equal(citationURL(c, origin), c.source_url);
  for (const url of ['javascript:alert(1)', 'https://user:password@example.test/source', 'https://other.test/source']) {
    assert.equal(citationURL({...c, open_url:url}, origin), null);
  }
});

test('PDF links bind the served source hash and physical page', () => {
  assert.equal(citationURL(pdf(13), origin), origin + pdf(13).open_url);
  assert.equal(citationURL({...pdf(13), document_sha256:'b'.repeat(64)}, origin), null);
  assert.equal(citationURL({...pdf(13), pdf_page:12}, origin), null);
  assert.equal(citationURL({...pdf(13), open_url:'https://other.test/source.pdf'}, origin), null);
});

test('AI evidence retains its label without a source URL', () => {
  for (const evidence_kind of ['ai', 'pdf']) {
    const c = {...pdf(13), evidence_kind, content_origin:'generated', display_label:'source'};
    assert.equal(citationLabel(c), 'kiến thức AI');
    assert.equal(citationURL(c, origin), null);
  }
});

test('same PDF on two pages retains distinct link identities', () => {
  assert.notEqual(citationURL(pdf(13), origin), citationURL(pdf(12), origin));
  assert.equal(citationURL({...pdf(13), open_url:`/hus/sources/${sha}?page=13#page=12`}, origin), null);
});

test('missing files have no fake open target, and DOCX stays a file', () => {
  assert.equal(citationURL({...pdf(1), availability:'missing'}, origin), null);
  const doc = {evidence_kind:'file', availability:'available', document_sha256:sha,
    display_label:'Source.docx', open_url:`/hus/sources/${sha}`};
  assert.equal(citationLabel(doc), 'Source.docx');
  assert.equal(citationURL(doc, origin), origin + doc.open_url);
});

test('escapeHtml sanitizes XSS characters and handles edge cases', () => {
  assert.equal(escapeHtml("<script>alert('xss')</script>"), '&lt;script&gt;alert(&#39;xss&#39;)&lt;/script&gt;');
  assert.equal(escapeHtml('<img src=x onerror="alert(1)">'), '&lt;img src=x onerror=&quot;alert(1)&quot;&gt;');
  assert.equal(escapeHtml('Tom & Jerry'), 'Tom &amp; Jerry');
  assert.equal(escapeHtml(null), '');
  assert.equal(escapeHtml(undefined), '');
  assert.equal(escapeHtml(123), '123');
});

test('formatInlineMarkdown transforms bold, citations, and code while preserving XSS safety', () => {
  const input = '**Mã học phần:** `MAT3507` và nội dung [1] [2].';
  const output = formatInlineMarkdown(input);
  assert.equal(
    output,
    '<strong>Mã học phần:</strong> <code class="rag-inline-code">MAT3507</code> và nội dung <span class="rag-inline-cite" title="Trích dẫn nguồn [1]">[1]</span> <span class="rag-inline-cite" title="Trích dẫn nguồn [2]">[2]</span>.'
  );

  // XSS attack within markdown formatting
  const xss = '**<script>alert(1)</script>** `x="1" & y="2"` [3]';
  const safeOutput = formatInlineMarkdown(xss);
  assert.ok(!safeOutput.includes('<script>'));
  assert.ok(safeOutput.includes('<strong>&lt;script&gt;alert(1)&lt;/script&gt;</strong>'));
  assert.ok(safeOutput.includes('&quot;1&quot; &amp; y=&quot;2&quot;'));
  assert.ok(safeOutput.includes('title="Trích dẫn nguồn [3]"'));
});

test('renderSafeMarkdown parses course cards, headings, lists, and paragraphs', () => {
  const markdown = [
    '### Phần 1: Thông tin học phần',
    '- Mã học phần: MAT3507 [1]',
    '- Tên học phần: Cơ sở dữ liệu',
    '- Số tín chỉ: 4',
    '',
    '### Phần 2: Tổng quan môn học',
    'Môn học này là môn nền tảng.',
    '- Khái niệm cơ bản',
    '- Chuẩn hóa dữ liệu [2]',
  ].join('\n');

  const container = {
    children: [],
    appendChild(child) {
      this.children.push(child);
      return child;
    },
  };

  renderSafeMarkdown(markdown, container);

  // 1. First element is .rag-course-card
  const card = container.children[0];
  assert.equal(card.className, 'rag-course-card');
  assert.equal(card.children[0].className, 'rag-course-card-header');
  assert.ok(card.children[0].innerHTML.includes('Thông tin học phần'));

  // Course card list
  const cardList = card.children[1];
  assert.equal(cardList.className, 'rag-course-card-list');
  assert.equal(cardList.children.length, 3);
  assert.ok(cardList.children[0].innerHTML.includes('class="rag-inline-cite"'));

  // 2. Second element is .rag-heading
  const heading = container.children[1];
  assert.equal(heading.className, 'rag-heading');
  assert.ok(heading.innerHTML.includes('Phần 2: Tổng quan môn học'));

  // 3. Third element is paragraph
  const para = container.children[2];
  assert.equal(para.className, 'rag-para');
  assert.equal(para.innerHTML, 'Môn học này là môn nền tảng.');

  // 4. Fourth element is content list outside card
  const contentList = container.children[3];
  assert.equal(contentList.className, 'rag-content-list');
  assert.equal(contentList.children.length, 2);
  assert.ok(contentList.children[1].innerHTML.includes('title="Trích dẫn nguồn [2]"'));
});

test('renderSafeMarkdown closes course card when followed directly by narrative paragraph', () => {
  const markdown = [
    '### Thông tin học phần',
    '- **Mã học phần:** FLF1107 [1]',
    '- **Tên học phần:** Tiếng Anh B1 [1]',
    '- **Số tín chỉ:** 5 [1]',
    '',
    'Nội dung môn Tiếng Anh B1 tập trung vào kỹ năng giao tiếp.',
    '',
    'Bên cạnh đó, các mục tiêu tham khảo giúp sinh viên tự tin hơn.',
  ].join('\n');

  const container = {
    children: [],
    appendChild(child) {
      this.children.push(child);
      return child;
    },
  };

  renderSafeMarkdown(markdown, container);

  // 1. First element is .rag-course-card
  const card = container.children[0];
  assert.equal(card.className, 'rag-course-card');
  assert.equal(card.children[0].className, 'rag-course-card-header');
  assert.ok(card.children[0].innerHTML.includes('Thông tin học phần'));

  const cardList = card.children[1];
  assert.equal(cardList.className, 'rag-course-card-list');
  assert.equal(cardList.children.length, 3);
  // Course card must NOT contain narrative paragraphs
  assert.equal(card.children.length, 2);

  // 2. Second element is paragraph in container outside card
  const para1 = container.children[1];
  assert.equal(para1.className, 'rag-para');
  assert.ok(para1.innerHTML.includes('Nội dung môn Tiếng Anh B1'));

  // 3. Third element is second paragraph
  const para2 = container.children[2];
  assert.equal(para2.className, 'rag-para');
  assert.ok(para2.innerHTML.includes('Bên cạnh đó'));
});

test('groupCitations deduplicates citations with same URL and groups citation IDs', () => {
  const origin = 'http://127.0.0.1:8000';
  const c1 = {evidence_kind:'web', source_url:'https://example.test/source1', open_url:'https://example.test/source1', citation_id:'3'};
  const c2 = {evidence_kind:'web', source_url:'https://example.test/source1', open_url:'https://example.test/source1', citation_id:'4'};
  const c3 = {evidence_kind:'web', source_url:'https://example.test/source1', open_url:'https://example.test/source1', citation_id:'5'};
  const c4 = {evidence_kind:'web', source_url:'https://example.test/source2', open_url:'https://example.test/source2', citation_id:'6'};

  const grouped = groupCitations([c1, c2, c3, c4], origin);
  assert.equal(grouped.length, 2);
  assert.equal(grouped[0].citation_id, '3, 4, 5');
  assert.deepEqual(grouped[0].citation_ids, ['3', '4', '5']);
  assert.equal(grouped[1].citation_id, '6');
});

test('groupCitations keeps PDF citations on different pages separate while merging same page', () => {
  const origin = 'http://127.0.0.1:8000';
  const sha = 'a'.repeat(64);
  const pdf1 = {evidence_kind:'pdf', availability:'available', document_sha256:sha, pdf_page:10, open_url:`/hus/sources/${sha}?page=10#page=10`, citation_id:'1'};
  const pdf2 = {evidence_kind:'pdf', availability:'available', document_sha256:sha, pdf_page:12, open_url:`/hus/sources/${sha}?page=12#page=12`, citation_id:'2'};
  const pdf3 = {evidence_kind:'pdf', availability:'available', document_sha256:sha, pdf_page:10, open_url:`/hus/sources/${sha}?page=10#page=10`, citation_id:'3'};

  const grouped = groupCitations([pdf1, pdf2, pdf3], origin);
  assert.equal(grouped.length, 2);
  assert.equal(grouped[0].citation_id, '1, 3');
  assert.equal(grouped[0].pdf_page, 10);
  assert.equal(grouped[1].citation_id, '2');
  assert.equal(grouped[1].pdf_page, 12);
});

test('isFollowUpCourseQuery detects follow-up course pronouns and rejects specific/major queries', () => {
  assert.equal(isFollowUpCourseQuery('môn đó có mấy tín chỉ'), true);
  assert.equal(isFollowUpCourseQuery('học phần này học kỳ mấy'), true);
  assert.equal(isFollowUpCourseQuery('môn này có tiên quyết không'), true);
  assert.equal(isFollowUpCourseQuery('môn đó học như thế nào'), true);
  assert.equal(isFollowUpCourseQuery('môn đấy có khó không'), true);
  assert.equal(isFollowUpCourseQuery('môn này có khó k'), true);
  assert.equal(isFollowUpCourseQuery('Có khó ko?'), true);
  // Negative cases: contains specific course code or name
  assert.equal(isFollowUpCourseQuery('môn MAT1041 có mấy tín chỉ'), false);
  assert.equal(isFollowUpCourseQuery('môn này hay mat1041 khó hơn?'), false);
  assert.equal(isFollowUpCourseQuery('môn Giải tích 1 có mấy tín chỉ'), false);
  assert.equal(isFollowUpCourseQuery('giới thiệu ngành khoa học dữ liệu'), false);
  assert.equal(isFollowUpCourseQuery('tổng tín chỉ chương trình'), false);
  assert.equal(isFollowUpCourseQuery(''), false);
  assert.equal(isFollowUpCourseQuery(null), false);
});

test('extractCourseCode extracts uppercase course codes from reply and facts', () => {
  assert.equal(extractCourseCode('CME1000 — Giáo dục quốc phòng'), 'CME1000');
  assert.equal(extractCourseCode('Môn học MAT3507 (Lập trình nâng cao)'), 'MAT3507');
  assert.equal(extractCourseCode('Không có mã môn ở đây'), null);
  assert.equal(extractCourseCode(null), null);
});

test('F1 shows content and reference markers without repeated source information', () => {
  const warning = 'Nguồn được duyệt trên Markdown; chưa đối chiếu PDF/DOCX gốc.';
  const notice = 'Chỉ mô tả theo nguồn đã lưu; chưa xác minh hiệu lực hiện tại.';
  const reply = [warning, notice, '## 4. Nghề nghiệp [1]\n- Nếu đủ điều kiện, có thể giảng dạy. [1]',
    'Nguồn [1]: Khoa Toán', 'Xem ký hiệu [99].'].join('\n\n');
  const answer = {status: 'answered', dataset: 'f1', warnings: [warning, notice],
    citations: [{citation_id: '1', evidence_kind: 'web'}]};
  assert.equal(displayReply(reply, answer),
    '4. Nghề nghiệp [1]\n- Nếu đủ điều kiện, có thể giảng dạy. [1]\n\nXem ký hiệu [99].');
});

test('F2 uses the direct answer and keeps meaningful prerequisite uncertainty', () => {
  const warning = 'Trạng thái: verified theo sign-off cấp dự án đã ghi trong nguồn; không phải chứng nhận của trường.';
  const uncertainty = 'Có mâu thuẫn điều kiện tiên quyết giữa các dòng nguồn; chưa kết luận điều kiện đúng.';
  const text = 'MAT1202 — Lập trình hướng đối tượng\nĐiều kiện tiên quyết theo dòng nguồn: chưa rõ.';
  const canonical = [text, warning, uncertainty, 'Nguồn [1]: Khung chương trình'].join('\n\n');
  const rewrite = 'Thông tin theo nguồn đã chọn:\n\n' + canonical;
  const answer = {status: 'answered', dataset: 'f2', reply: canonical, warnings: [warning, uncertainty],
    citations: [{...pdf(10), citation_id: '1'}]};
  assert.equal(displayReply(rewrite, answer), text + '\n\n' + uncertainty);
  assert.equal(answer.reply, canonical);
});

test('an answer without sources keeps its actual reply', () => {
  const reply = 'Chưa tìm thấy môn này trong ngành đã chọn.';
  assert.equal(displayReply(reply, {status: 'no_information', citations: []}), reply);
  assert.equal(displayReply('Xin chào!', null), 'Xin chào!');
});

function answer(generation, status = 'answered') {
  return {mode: 'hus_rag', hus_answer: {status}, generation};
}

test('default and non-answer replies have no generation badge', () => {
  assert.equal(generationInfo(answer(undefined), false), null);
  assert.equal(generationInfo(answer({used: false, fallback_reason: 'not_answered'}, 'no_information'), true), null);
  assert.equal(generationInfo(answer({used: false}, 'needs_clarification'), true), null);
  assert.equal(generationInfo({mode: 'basic_chat', generation: {used: false}}, true), null);
});

test('AI badge requires actual use, answered RAG and explicit request consent', () => {
  const used = answer({used: true, model: 'actual-model', fallback_reason: null});
  assert.equal(generationInfo(used, true).kind, 'used');
  assert.equal(generationInfo(used, true).label, 'AI diễn đạt từ nguồn');
  assert.throws(() => generationInfo(used, false));
  assert.throws(() => generationInfo({...used, mode: 'basic_chat'}, true));
  assert.throws(() => generationInfo(answer(used.generation, 'no_information'), true));
  assert.throws(() => generationInfo(answer({used: true, model: ''}), true));
  assert.throws(() => generationInfo(answer({used: true, model: 'm', fallback_reason: 'timeout'}), true));
  assert.throws(() => generationInfo(answer({used: 'true'}), true));
});

test('requested canonical fallbacks use stable, safe human messages', () => {
  const cases = [
    [{used: false, fallback_reason: 'busy'}, /bận/],
    [{used: false, fallback_reason: 'timeout'}, /thời gian/],
    [{used: false, fallback_reason: 'http_error', http_status: 429}, /hạn mức/],
    [{used: false, fallback_reason: 'http_error', http_status: 503}, /tạm thời/],
    [{used: false, fallback_reason: 'prompt_budget'}, /giới hạn/],
    [{used: false, fallback_reason: 'output_budget'}, /giới hạn/],
    [{used: false, fallback_reason: 'invalid_output'}, /kiểm tra/],
    [{used: false, fallback_reason: '<private-body-key>'}, /sẵn sàng/],
    [undefined, /sẵn sàng/],
  ];
  for (const [metadata, note] of cases) {
    const info = generationInfo(answer(metadata), true);
    assert.equal(info.kind, 'fallback');
    assert.equal(info.label, 'Bản trích nguồn');
    assert.match(info.note, note);
    assert.doesNotMatch(JSON.stringify(info), /private-body-key/);
  }
});

test('groupCitations preserves distinct source editions and review states on a shared URL', () => {
  const first = {
    citation_id: '1',
    evidence_kind: 'web',
    source_id: 'shared',
    source_url: 'https://example.test/source',
    open_url: 'https://example.test/source',
    review_status: 'reviewed',
    metadata: {scope: {curriculum_version: '2023', program_variant: 'standard'}},
  };
  const otherEdition = {
    ...first,
    citation_id: '2',
    metadata: {scope: {...first.metadata.scope, curriculum_version: '2024'}},
  };
  const otherReview = {...first, citation_id: '3', review_status: 'unreviewed'};
  assert.deepEqual(
    groupCitations([first, otherEdition, otherReview], origin).map(citation => citation.citation_id),
    ['1', '2', '3'],
  );
});
