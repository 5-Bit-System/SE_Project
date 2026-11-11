/* Academic workspace integration for HUS RAG lookup ("Tra cứu thông tin"). */
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

  function escapeHtml(str) {
    if (str == null) return '';
    return String(str)
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;')
      .replace(/"/g, '&quot;')
      .replace(/'/g, '&#39;');
  }

  function formatInlineMarkdown(raw) {
    if (!raw) return '';
    const safe = escapeHtml(raw);
    return safe
      .replace(/`([^`]+)`/g, '<code class="rag-inline-code">$1</code>')
      .replace(/\*\*([^*]+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\[(\d+)\]/g, '<span class="rag-inline-cite" title="Trích dẫn nguồn [$1]">[$1]</span>');
  }

  function createElement(tag, className) {
    if (typeof document !== 'undefined') {
      const el = document.createElement(tag);
      if (className) el.className = className;
      return el;
    }
    return {
      tagName: tag.toUpperCase(),
      className: className || '',
      innerHTML: '',
      children: [],
      appendChild(child) {
        this.children.push(child);
        return child;
      },
      get textContent() {
        return this.innerHTML.replace(/<[^>]+>/g, '');
      },
    };
  }

  function renderSafeMarkdown(text, container) {
    if (!container || typeof text !== 'string') return;
    const lines = text.split(/\r?\n/);
    let inCourseCard = false;
    let courseCardEl = null;
    let cardHasList = false;
    let currentList = null;
    let currentPara = null;

    for (let i = 0; i < lines.length; i++) {
      const line = lines[i];
      const trimmed = line.trim();

      if (!trimmed) {
        currentList = null;
        currentPara = null;
        if (inCourseCard && cardHasList) {
          inCourseCard = false;
          courseCardEl = null;
        }
        continue;
      }

      const headingMatch = /^(#{1,4})\s*(.*)$/.exec(trimmed);
      if (headingMatch) {
        currentList = null;
        currentPara = null;
        const headingText = headingMatch[2].trim();
        const isCourseCardHeading = /(?:Phần\s*\d+\s*[:.-]?\s*)?Thông tin (?:học phần|môn học)/i.test(headingText);

        if (isCourseCardHeading) {
          inCourseCard = true;
          courseCardEl = createElement('div', 'rag-course-card');
          cardHasList = false;
          const header = createElement('div', 'rag-course-card-header');
          header.innerHTML = formatInlineMarkdown(headingText);
          courseCardEl.appendChild(header);
          container.appendChild(courseCardEl);
        } else {
          inCourseCard = false;
          courseCardEl = null;
          const h = createElement('h4', 'rag-heading');
          h.innerHTML = formatInlineMarkdown(headingText);
          container.appendChild(h);
        }
        continue;
      }

      const listMatch = /^[-*]\s+(.*)$/.exec(trimmed);
      if (listMatch) {
        currentPara = null;
        const itemContent = listMatch[1].trim();
        if (inCourseCard && courseCardEl) {
          cardHasList = true;
          if (!currentList || currentList.className !== 'rag-course-card-list') {
            currentList = createElement('ul', 'rag-course-card-list');
            courseCardEl.appendChild(currentList);
          }
        } else {
          if (!currentList || currentList.className !== 'rag-content-list') {
            currentList = createElement('ul', 'rag-content-list');
            container.appendChild(currentList);
          }
        }
        const li = createElement('li');
        li.innerHTML = formatInlineMarkdown(itemContent);
        currentList.appendChild(li);
        continue;
      }

      // If text line arrives after course card list is already built, exit course card
      if (inCourseCard && cardHasList) {
        inCourseCard = false;
        courseCardEl = null;
      }

      currentList = null;
      const target = (inCourseCard && courseCardEl) ? courseCardEl : container;
      if (!currentPara) {
        currentPara = createElement('p', 'rag-para');
        currentPara.innerHTML = formatInlineMarkdown(trimmed);
        target.appendChild(currentPara);
      } else {
        currentPara.innerHTML += ' ' + formatInlineMarkdown(trimmed);
      }
    }
  }

  function groupCitations(citations, origin) {
    if (!Array.isArray(citations) || !citations.length) return [];
    const groups = new Map();
    for (const citation of citations) {
      if (!citation || typeof citation !== 'object') continue;
      const url = citationURL(citation, origin);
      const key = url
        ? `url:${url}`
        : `meta:${citation.evidence_kind || ''}:${citation.source_id || ''}:${citationLabel(citation)}:${citation.pdf_page || ''}`;

      const existing = groups.get(key);
      if (existing) {
        if (citation.citation_id && !existing.ids.includes(String(citation.citation_id))) {
          existing.ids.push(String(citation.citation_id));
        }
      } else {
        const ids = citation.citation_id ? [String(citation.citation_id)] : [];
        groups.set(key, { citation, ids });
      }
    }
    return Array.from(groups.values()).map(g => ({
      ...g.citation,
      citation_ids: g.ids,
      citation_id: g.ids.join(', '),
    }));
  }

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      citationURL,
      citationLabel,
      escapeHtml,
      formatInlineMarkdown,
      renderSafeMarkdown,
      groupCitations,
    };
  }
  if (typeof document === 'undefined') return;

  const PROGRAM_TO_MAJOR = {
    'Khoa học máy tính và thông tin': 'computer_science',
    'Khoa học dữ liệu': 'data_science',
    'Toán tin': 'mathematics_informatics',
    'Toán học': 'mathematics',
  };

  function resolveProgramMajor(text) {
    if (!text || typeof text !== 'string') return null;
    const clean = text.trim();
    if (PROGRAM_TO_MAJOR[clean]) return PROGRAM_TO_MAJOR[clean];
    for (const [key, id] of Object.entries(PROGRAM_TO_MAJOR)) {
      if (clean.includes(key)) return id;
    }
    return null;
  }

  const major = document.getElementById('lookup-major');
  const version = document.getElementById('lookup-version');
  const question = document.getElementById('lookup-question');
  const send = document.getElementById('lookup-send');
  const generated = document.getElementById('lookup-generated');
  const messages = document.getElementById('lookup-messages');
  const status = document.getElementById('lookup-status');
  const form = document.getElementById('lookup-form');
  const catalog = document.getElementById('lookup-catalog');
  const catalogSearch = document.getElementById('lookup-catalog-search');
  const catalogStatus = document.getElementById('lookup-catalog-status');
  const catalogGroups = document.getElementById('lookup-catalog-groups');
  const catalogRetry = document.getElementById('lookup-catalog-retry');

  let config = null;
  let busy = false;
  let scopeGeneration = 0;
  let requestController = null;
  let catalogController = null;
  let catalogEntries = [];
  let userChangedMajor = false;
  let latestPortalProgram = null;
  let initialized = false;
  let initializing = false;

  function currentMajor() {
    return config?.majors.find(item => item.id === major.value) || null;
  }

  function setStatus(message, error = false) {
    if (!status) return;
    status.textContent = message;
    status.dataset.state = error ? 'error' : 'ready';
  }

  function updateControls() {
    const unavailable = !currentMajor();
    if (major) major.disabled = unavailable;
    if (question) question.disabled = unavailable || busy;
    if (generated) generated.disabled = unavailable || busy;
    if (send) {
      send.disabled = unavailable || busy || !question.value.trim();
      if (send.firstChild) send.firstChild.textContent = busy ? 'Đang trả lời ' : 'Gửi ';
    }
    if (form) form.setAttribute('aria-busy', String(busy));
    for (const {button, item} of catalogEntries) {
      button.disabled = unavailable || busy || (item.requires_ai && !generated.checked);
    }
  }

  function searchable(text) {
    return text.normalize('NFD').replace(/[\u0300-\u036f]/g, '').replace(/đ/gi, 'd').toLowerCase();
  }

  function filterCatalog() {
    if (!catalogSearch || !catalogStatus || !catalogGroups) return;
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
    if (!catalogGroups) return;
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
    if (catalogGroups) catalogGroups.replaceChildren();
    if (catalogSearch) catalogSearch.disabled = true;
    if (catalogRetry) catalogRetry.hidden = true;
    if (catalog) catalog.removeAttribute('data-major');
    if (catalogStatus) catalogStatus.textContent = 'Đang tải danh mục theo ngành đã chọn…';
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
      if (catalog) catalog.dataset.major = selected.id;
      if (catalogSearch) catalogSearch.disabled = false;
    } catch (error) {
      if (epoch !== scopeGeneration || catalogController !== controller || error.name === 'AbortError') return;
      catalogEntries = [];
      if (catalogGroups) catalogGroups.replaceChildren();
      if (catalogStatus) catalogStatus.textContent = 'Không tải được danh mục. Bạn vẫn có thể nhập câu hỏi bên cạnh.';
      if (catalogRetry) catalogRetry.hidden = false;
    }
  }

  function appendCitation(container, citation) {
    if (!citation || typeof citation !== 'object') return;
    const ai = isAI(citation);
    const card = document.createElement('div');
    card.className = 'rag-citation' + (ai ? ' rag-citation-ai' : '');
    const heading = document.createElement('p');
    heading.className = 'rag-citation-title';
    const numText = citation.citation_id || (Array.isArray(citation.citation_ids) ? citation.citation_ids.join(', ') : '');
    if (numText) {
      const num = document.createElement('span');
      num.className = 'rag-citation-num';
      num.textContent = `[${numText}]`;
      heading.appendChild(num);
    }
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

  function appendMessage(role, reply, citations = [], generationMode = 'extractive') {
    if (!messages) return;
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
    const isAssistant = role === 'assistant';
    const isLLM = isAssistant && (generationMode === 'grounded_llm' || reply.includes('###') || (!generationMode && (reply.includes('**') || reply.includes('[1]'))));
    if (isLLM) {
      const badge = document.createElement('span');
      badge.className = 'rag-badge-llm';
      badge.textContent = '✨ Trợ lý AI HUS';
      speaker.appendChild(badge);
    }
    const text = document.createElement(isAssistant ? 'div' : 'p');
    text.className = 'rag-message-text';
    if (isAssistant) {
      renderSafeMarkdown(reply, text);
    } else {
      text.textContent = reply;
    }
    body.append(speaker, text);
    if (Array.isArray(citations) && citations.length) {
      const sources = document.createElement('div');
      sources.className = 'rag-citations';
      sources.setAttribute('aria-label', 'Dẫn chứng');
      const origin = typeof window !== 'undefined' ? window.location.origin : 'http://127.0.0.1:8000';
      const uniqueCitations = groupCitations(citations, origin);
      for (const citation of uniqueCitations) appendCitation(sources, citation);
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
    if (generated) generated.checked = false;
    if (catalogSearch) catalogSearch.value = '';
    if (question) question.value = '';
    if (messages) messages.replaceChildren();
    const selected = currentMajor();
    if (version) version.textContent = selected?.version || 'Chưa có dữ liệu';
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
    if (!question) return;
    const text = question.value.trim();
    const selected = currentMajor();
    if (!selected || !text || busy) return;
    const epoch = scopeGeneration;
    const controller = new AbortController();
    requestController = controller;
    const payload = {...(catalogRequest || {}), question: text, major: selected.id,
      version: catalogRequest?.version || selected.version,
      allow_generated_reference: generated?.checked === true};
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
        result.mode === 'hus_rag' ? result.hus_answer?.citations : [],
        result.generation_mode);
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

  if (form) form.addEventListener('submit', submit);
  if (question) {
    question.addEventListener('input', updateControls);
    question.addEventListener('keydown', event => {
      if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) {
        event.preventDefault();
        form?.requestSubmit();
      }
    });
  }
  if (major) {
    major.addEventListener('change', () => {
      userChangedMajor = true;
      resetScope();
    });
  }
  if (generated) generated.addEventListener('change', updateControls);
  if (catalogSearch) catalogSearch.addEventListener('input', filterCatalog);
  if (catalogRetry) catalogRetry.addEventListener('click', loadCatalog);

  document.addEventListener('workspace:portal-data', event => {
    const program = event.detail?.profile?.program || document.getElementById('workspace-program')?.textContent;
    if (program) latestPortalProgram = program;
    if (config && !userChangedMajor && program && major) {
      const target = resolveProgramMajor(program);
      if (target && config.majors.some(item => item.id === target) && major.value !== target) {
        major.value = target;
        resetScope();
      }
    }
  });

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
      if (major) {
        major.replaceChildren();
        for (const item of config.majors) {
          const option = document.createElement('option');
          option.value = item.id;
          option.textContent = item.label;
          major.appendChild(option);
        }
        let selectedMajorId = null;
        if (!userChangedMajor) {
          const currentProgram = latestPortalProgram || document.getElementById('workspace-program')?.textContent;
          const resolved = resolveProgramMajor(currentProgram);
          if (resolved && config.majors.some(item => item.id === resolved)) {
            selectedMajorId = resolved;
          }
        }
        if (!selectedMajorId) {
          const dataScience = config.majors.find(item => item.id === 'data_science');
          selectedMajorId = dataScience ? dataScience.id : config.majors[0]?.id;
        }
        if (selectedMajorId) major.value = selectedMajorId;
      }
      resetScope();
    } catch {
      config = null;
      if (major) {
        major.replaceChildren();
        const option = document.createElement('option');
        option.textContent = 'Dữ liệu chưa sẵn sàng';
        major.appendChild(option);
      }
      if (version) version.textContent = 'Không tải được';
      setStatus('Không tải được cấu hình dữ liệu HUS. Kiểm tra máy chủ rồi tải lại trang.', true);
      updateControls();
    }
  }

  function ensureInitialized() {
    if (initialized || initializing) return;
    const tabLookup = document.getElementById('tab-lookup');
    if (!tabLookup) return;
    const isActive = tabLookup.classList.contains('active')
      || (typeof location !== 'undefined' && location.hash === '#lookup');
    if (isActive) {
      initializing = true;
      initialize().finally(() => {
        initializing = false;
        initialized = true;
      });
    }
  }

  document.addEventListener('workspace:navigate', event => {
    if (event.detail === 'tab-lookup' && !initialized && !initializing) {
      initializing = true;
      initialize().finally(() => {
        initializing = false;
        initialized = true;
      });
    }
  });

  const tabBtn = document.getElementById('tab-btn-lookup');
  if (tabBtn) {
    tabBtn.addEventListener('click', () => {
      if (!initialized && !initializing) {
        initializing = true;
        initialize().finally(() => {
          initializing = false;
          initialized = true;
        });
      }
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', ensureInitialized);
  } else {
    ensureInitialized();
  }
}());
