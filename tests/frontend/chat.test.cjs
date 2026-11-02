const assert = require('node:assert/strict');
const test = require('node:test');
const {citationURL, citationLabel} = require('../../app/static/hus-rag-demo.js');
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
