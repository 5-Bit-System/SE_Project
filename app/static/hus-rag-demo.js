/* Local HUS RAG demo. Conversation stays in this tab; no academic product context. */
(function () {
  'use strict';

  function isAI(citation) {
    return citation.evidence_kind === 'ai' || citation.content_origin === 'generated';
  }

  function citationURL(citation, origin) {
    if (!citation || isAI(citation) || typeof citation.open_url !== 'string') return null;
    const raw = citation.open_url;
    if (/\s|[\u0000-\u001f\u007f]/u.test(raw)) return null;
    try {
      const url = new URL(raw, origin);
      if (citation.evidence_kind === 'web') {
        return raw === citation.source_url && /^https?:\/\//i.test(raw)
          && ['http:', 'https:'].includes(url.protocol) && !url.username && !url.password
          ? url.href : null;
      }
      if (!['pdf', 'file'].includes(citation.evidence_kind)
          || citation.availability !== 'available' || url.origin !== origin) return null;
      const match = /^\/hus\/sources\/([0-9a-f]{64})(?:\?page=([1-9]\d*))?(?:#page=([1-9]\d*))?$/.exec(raw);
      if (!match || (citation.document_sha256 && match[1] !== citation.document_sha256)
          || (match[2] && match[3] && match[2] !== match[3])) return null;
      if (citation.pdf_page != null && String(citation.pdf_page) !== (match[2] || match[3])) return null;
      return url.href;
    } catch {
      return null;
    }
  }

  function citationLabel(citation) {
    if (isAI(citation)) return 'kiến thức AI';
    return citation.display_label || citation.label || 'Nguồn dữ liệu';
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {citationURL, citationLabel};
  }
  if (typeof document === 'undefined') return;

  const major = document.getElementById('rag-major');
  const version = document.getElementById('rag-version');
  const question = document.getElementById('rag-question');
  const send = document.getElementById('rag-send');
  const generated = document.getElementById('rag-generated');
  const messages = document.getElementById('rag-messages');
  const status = document.getElementById('rag-status');
  const form = document.getElementById('rag-form');
  const catalog = document.getElementById('rag-catalog');
  const catalogSearch = document.getElementById('rag-catalog-search');
  const catalogStatus = document.getElementById('rag-catalog-status');
  const catalogGroups = document.getElementById('rag-catalog-groups');
  const catalogRetry = document.getElementById('rag-catalog-retry');
  let config = null;
  let busy = false;
  let scopeGeneration = 0;
  let requestController = null;
  let catalogController = null;
  let catalogEntries = [];

  function currentMajor() {
    return config?.majors.find(item => item.id === major.value) || null;
  }

  function setStatus(message, error = false) {
    status.textContent = message;
    status.dataset.state = error ? 'error' : 'ready';
  }

  function updateControls() {
    const unavailable = !currentMajor();
    major.disabled = unavailable;
    question.disabled = unavailable || busy;
    generated.disabled = unavailable || busy;
    send.disabled = unavailable || busy || !question.value.trim();
    send.firstChild.textContent = busy ? 'Đang trả lời ' : 'Gửi ';
    form.setAttribute('aria-busy', String(busy));
    for (const {button, item} of catalogEntries) {
      button.disabled = unavailable || busy || (item.requires_ai && !generated.checked);
    }
  }

  function searchable(text) {
    return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/gi, 'd').toLowerCase();
  }

  function filterCatalog() {
    const terms = searchable(catalogSearch.value).trim().split(/\s+/).filter(Boolean);
    let visible = 0;
    for (const {button, item} of catalogEntries) {
      const text = searchable([item.question, item.course_label, item.scope_label].join(' '));
      button.hidden = !terms.every(term => text.includes(term));
      if (!button.hidden) visible += 1;
    }
    for (const section of catalogGroups.querySelectorAll('.rag-catalog-section')) {
      section.hidden = !section.querySelector('.rag-catalog-question:not([hidden])');
      if (terms.length && !section.hidden) section.open = true;
    }
    for (const group of catalogGroups.children) {
      group.hidden = !group.querySelector('.rag-catalog-question:not([hidden])');
      if (terms.length && !group.hidden) group.open = true;
    }
    catalogStatus.textContent = visible
      ? visible + ' / ' + catalogEntries.length + ' câu hỏi · Bấm để hỏi'
      : 'Không có câu hỏi phù hợp. Thử tên hoặc mã môn khác.';
  }

  function renderCatalog(value) {
    catalogGroups.replaceChildren();
    catalogEntries = [];
    for (const group of value.groups) {
      const details = document.createElement('details');
      details.className = 'rag-catalog-group';
      details.dataset.family = group.id;
      details.open = group.id === 'f1';
      const summary = document.createElement('summary');
      summary.textContent = group.title + ' (' + group.questions.length + ')';
      const note = document.createElement('p');
      note.className = 'rag-catalog-note';
      note.textContent = group.note;
      details.append(summary, note);
      const sections = new Map();
      for (const item of group.questions) {
        const label = item.course_label || item.scope_label;
        let section = sections.get(label);
        if (!section) {
          section = document.createElement('details');
          section.className = 'rag-catalog-section';
          section.open = group.id === 'help';
          const title = document.createElement('summary');
          title.textContent = label;
          section.appendChild(title);
          sections.set(label, section);
          details.appendChild(section);
        }
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'rag-catalog-question';
        button.textContent = item.question;
        if (item.requires_ai) button.title = 'Cần bật Cho phép kiến thức AI tham khảo';
        const epoch = scopeGeneration;
        button.addEventListener('click', () => {
          if (epoch !== scopeGeneration || button.disabled) return;
          question.value = item.question;
          submit(null, item.request);
        });
        section.appendChild(button);
        catalogEntries.push({button, item});
      }
      catalogGroups.appendChild(details);
    }
    filterCatalog();
    updateControls();
  }

  async function loadCatalog() {
    catalogController?.abort();
    const selected = currentMajor();
    if (!selected) return;
    const epoch = scopeGeneration;
    const controller = new AbortController();
    catalogController = controller;
    catalogEntries = [];
    catalogGroups.replaceChildren();
    catalogSearch.disabled = true;
    catalogRetry.hidden = true;
    catalog.removeAttribute('data-major');
    catalogStatus.textContent = 'Đang tải danh mục theo ngành đã chọn…';
    try {
      const params = new URLSearchParams({major: selected.id, version: selected.version});
      const response = await fetch('/hus/questions?' + params, {cache: 'no-store', signal: controller.signal});
      if (!response.ok) throw new Error('catalog_unavailable');
      const value = await response.json();
      if (epoch !== scopeGeneration || catalogController !== controller) return;
      if (value.major !== selected.id || value.version !== selected.version
          || value.release_sha256 !== config.release_sha256 || !Array.isArray(value.groups)) {
        throw new Error('invalid_catalog');
      }
      renderCatalog(value);
      catalog.dataset.major = selected.id;
      catalogSearch.disabled = false;
    } catch (error) {
      if (epoch !== scopeGeneration || catalogController !== controller || error.name === 'AbortError') return;
      catalogEntries = [];
      catalogGroups.replaceChildren();
      catalogStatus.textContent = 'Không tải được danh mục. Bạn vẫn có thể nhập câu hỏi bên cạnh.';
      catalogRetry.hidden = false;
    }
  }

  function appendCitation(container, citation) {
    if (!citation || typeof citation !== 'object') return;
    const ai = isAI(citation);
    const card = document.createElement('div');
    card.className = 'rag-citation' + (ai ? ' rag-citation-ai' : '');
    const heading = document.createElement('p');
    heading.className = 'rag-citation-title';
    const kind = document.createElement('span');
    kind.className = 'rag-citation-kind';
    kind.textContent = ai ? 'AI' : ({pdf: 'PDF', web: 'WEB', file: 'TỆP'}[citation.evidence_kind] || 'NGUỒN');
    heading.appendChild(kind);
    const url = citationURL(citation, window.location.origin);
    const label = document.createElement(url ? 'a' : 'span');
    label.textContent = citationLabel(citation);
    if (url) {
      label.href = url;
      label.target = '_blank';
      label.rel = 'noopener noreferrer';
    }
    heading.appendChild(label);
    card.appendChild(heading);
    const details = [];
    if (citation.pdf_page) details.push('Trang ' + citation.pdf_page);
    if (ai) details.push('Nội dung tham khảo do AI sinh; không phải nguồn chính thức.');
    else if (!url) details.push(citation.availability_note || 'Chưa có liên kết nguồn khả dụng.');
    if (citation.review_status) details.push('Trạng thái nguồn: ' + citation.review_status);
    if (details.length) {
      const detail = document.createElement('p');
      detail.className = 'rag-citation-detail';
      detail.textContent = details.join(' · ');
      card.appendChild(detail);
    }
    container.appendChild(card);
  }

  function appendMessage(role, reply, citations = []) {
    const article = document.createElement('article');
    article.className = 'rag-message rag-message-' + role;
    const avatar = document.createElement('span');
    avatar.className = 'rag-avatar';
    avatar.setAttribute('aria-hidden', 'true');
    avatar.textContent = role === 'user' ? 'BẠN' : 'H';
    const body = document.createElement('div');
    body.className = 'rag-message-content';
    const speaker = document.createElement('p');
    speaker.className = 'rag-message-speaker';
    speaker.textContent = role === 'user' ? 'Bạn' : 'Hỏi đáp HUS';
    const text = document.createElement('p');
    text.className = 'rag-message-text';
    text.textContent = reply;
    body.append(speaker, text);
    if (Array.isArray(citations) && citations.length) {
      const sources = document.createElement('div');
      sources.className = 'rag-citations';
      sources.setAttribute('aria-label', 'Dẫn chứng');
      for (const citation of citations) appendCitation(sources, citation);
      body.appendChild(sources);
    }
    article.append(avatar, body);
    messages.appendChild(article);
    messages.scrollTop = messages.scrollHeight;
  }

  function resetScope() {
    scopeGeneration += 1;
    requestController?.abort();
    requestController = null;
    busy = false;
    generated.checked = false;
    catalogSearch.value = '';
    question.value = '';
    messages.replaceChildren();
    const selected = currentMajor();
    version.textContent = selected?.version || 'Chưa có dữ liệu';
    if (selected) {
      appendMessage('assistant', 'Xin chào! Bạn đang tra cứu ngành ' + selected.label
        + '. Bạn có thể hỏi giới thiệu ngành, tín chỉ, môn tiên quyết hoặc nội dung học phần.');
      setStatus('Đã chọn ' + selected.label + '. Đổi ngành sẽ bắt đầu hội thoại mới.');
    }
    updateControls();
    loadCatalog();
  }

  async function submit(event, catalogRequest = null) {
    event?.preventDefault();
    const text = question.value.trim();
    const selected = currentMajor();
    if (!selected || !text || busy) return;
    const epoch = scopeGeneration;
    const controller = new AbortController();
    requestController = controller;
    const payload = {...(catalogRequest || {}), question: text, major: selected.id,
      version: catalogRequest?.version || selected.version,
      allow_generated_reference: generated.checked === true};
    appendMessage('user', text);
    question.value = '';
    busy = true;
    updateControls();
    setStatus('Đang tìm thông tin trong dữ liệu của ngành đã chọn…');
    try {
      const response = await fetch('/hus/chat', {method: 'POST',
        headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload),
        signal: controller.signal, cache: 'no-store'});
      if (!response.ok) throw new Error('http_' + response.status);
      const result = await response.json();
      if (epoch !== scopeGeneration || requestController !== controller) return;
      if (!['basic_chat', 'hus_rag'].includes(result.mode) || typeof result.reply !== 'string'
          || !result.reply.trim()) throw new Error('invalid_response');
      appendMessage('assistant', result.reply,
        result.mode === 'hus_rag' ? result.hus_answer?.citations : []);
      if (result.mode === 'basic_chat') {
        setStatus('Đã phản hồi hội thoại.');
      } else if (result.hus_answer?.status === 'needs_clarification') {
        setStatus('Cần làm rõ câu hỏi; xem hướng dẫn trong phản hồi.');
      } else if (result.hus_answer?.status === 'no_information') {
        setStatus('Chưa có thông tin đủ căn cứ trong phạm vi đã chọn.');
      } else if (result.hus_answer?.status === 'answered') {
        setStatus(result.hus_answer.facts?.field === 'prerequisites'
          && result.hus_answer.facts?.prerequisite_status === 'unknown'
          ? 'Đã đối chiếu nguồn; điều kiện tiên quyết vẫn chưa rõ.'
          : 'Đã trả lời theo phạm vi dữ liệu đã chọn.');
      } else {
        throw new Error('invalid_response');
      }
    } catch (error) {
      if (epoch !== scopeGeneration || requestController !== controller || error.name === 'AbortError') return;
      const unavailable = error.message === 'http_503';
      setStatus(unavailable ? 'Dữ liệu HUS chưa sẵn sàng. Hãy kiểm tra máy chủ trước khi hỏi lại.'
        : 'Không nhận được câu trả lời. Bạn có thể nhập và gửi lại câu hỏi.', true);
    } finally {
      if (epoch === scopeGeneration && requestController === controller) {
        requestController = null;
        busy = false;
        updateControls();
        question.focus();
      }
    }
  }

  form.addEventListener('submit', submit);
  question.addEventListener('input', updateControls);
  question.addEventListener('keydown', event => {
    if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
      event.preventDefault();
      form.requestSubmit();
    }
  });
  major.addEventListener('change', resetScope);
  generated.addEventListener('change', updateControls);
  catalogSearch.addEventListener('input', filterCatalog);
  catalogRetry.addEventListener('click', loadCatalog);

  async function initialize() {
    try {
      const response = await fetch('/hus/config', {cache: 'no-store'});
      if (!response.ok) throw new Error('config_unavailable');
      const value = await response.json();
      const ids = new Set();
      if (!Array.isArray(value.majors) || value.majors.length !== 4
          || !value.majors.every(item => {
            if (!item || typeof item.id !== 'string' || !item.id || ids.has(item.id)
                || typeof item.label !== 'string' || !item.label
                || typeof item.version !== 'string' || !item.version) return false;
            ids.add(item.id);
            return true;
          })) throw new Error('invalid_config');
      config = value;
      major.replaceChildren();
      for (const item of config.majors) {
        const option = document.createElement('option');
        option.value = item.id;
        option.textContent = item.label;
        major.appendChild(option);
      }
      const dataScience = config.majors.find(item => item.id === 'data_science');
      if (dataScience) major.value = dataScience.id;
      resetScope();
    } catch {
      config = null;
      major.replaceChildren();
      const option = document.createElement('option');
      option.textContent = 'Dữ liệu chưa sẵn sàng';
      major.appendChild(option);
      version.textContent = 'Không tải được';
      setStatus('Không tải được cấu hình dữ liệu HUS. Kiểm tra máy chủ rồi tải lại trang.', true);
      updateControls();
    }
  }

  initialize();
}());
