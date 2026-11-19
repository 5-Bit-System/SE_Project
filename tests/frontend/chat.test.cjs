const assert = require('node:assert/strict');
const test = require('node:test');
const {citationURL, citationLabel, displayReply} = require('../../app/static/hus-rag-demo.js');
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
