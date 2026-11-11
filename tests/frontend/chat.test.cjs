const assert = require('node:assert/strict');
const test = require('node:test');
const {
  citationURL,
  citationLabel,
  escapeHtml,
  formatInlineMarkdown,
  renderSafeMarkdown,
  groupCitations,
} = require('../../app/static/hus-rag-demo.js');
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
