"""Only known AI reference markers are hidden; real references remain visible."""
from pathlib import Path

from tests.hus.test_question_catalog_ui import browser_app  # noqa: F401


def test_ai_and_real_references_are_separated_without_changing_evidence(browser_app):  # noqa: F811
    browser, _ = browser_app
    page = browser.new_page()
    source = (Path(__file__).resolve().parents[2] / 'app/static/hus-rag-demo.js').read_text(encoding='utf-8')
    result = page.evaluate('''source => {
      const module = {exports: {}};
      new Function('module', 'document', source)(module, undefined);
      const citations = [{citation_id: '1', evidence_kind: 'ai', content_origin: 'generated'},
        {citation_id: '2', evidence_kind: 'pdf', content_origin: 'structured_source_draft'}];
      const original = '[1] Ý AI: 42. [1]\\nNguồn [1]: kiến thức AI\\n'
        + '[2] Dữ kiện: 4 tín chỉ. [2]\\nNguồn [2]: PDF\\nGiữ ký hiệu [99].';
      return {clean: module.exports.displayReply(original, citations),
        original, realOnly: module.exports.displayReply(original, [citations[1]]),
        noEvidence: module.exports.displayReply(original, []), citations};
    }''', source)
    page.close()
    assert '[1]' not in result['clean'] and 'Nguồn [1]' not in result['clean']
    assert 'Ý AI: 42.' in result['clean']
    assert '[2] Dữ kiện: 4 tín chỉ. [2]' in result['clean']
    assert 'Nguồn [2]: PDF' in result['clean'] and '[99]' in result['clean']
    assert result['realOnly'] == result['noEvidence'] == result['original']
    assert len(result['citations']) == 2
