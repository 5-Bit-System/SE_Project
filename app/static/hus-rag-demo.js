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

  function onlyAI(citations) {
    return Array.isArray(citations) && citations.length > 0 && citations.every(isAI);
  }

  function diagnosticInfo(diagnostic) {
    const labels = {
      routing_unknown: ['Chưa hiểu yêu cầu', 'Hãy nêu rõ ngành/môn và loại thông tin cần hỏi.'],
      scope_conflict: ['Chọn lại phạm vi', 'Kiểm tra ngành và phiên bản đang chọn theo hướng dẫn trong câu trả lời.'],
      unsupported_operation: ['Chưa hỗ trợ thao tác này', 'Yêu cầu này chưa được triển khai; không phải lỗi kết nối Gemini.'],
      retrieval_empty: ['Chưa tìm thấy dữ liệu', 'Xem chi tiết trong câu trả lời.'],
      evidence_rejected: ['Chưa đủ căn cứ trả lời', 'Đã tìm thấy đoạn liên quan nhưng chưa đáp ứng đủ yêu cầu/điều kiện. Hãy làm rõ ý hỏi.'],
      evidence_unavailable: ['Chưa có thông tin nguồn', 'Dữ liệu hiện có chưa cung cấp thông tin cần hỏi.'],
      clarification_required: ['Cần làm rõ câu hỏi', 'Bổ sung ngành/mã môn/phiên bản hoặc chọn một ý cần hỏi.'],
      permission_required: ['Chưa cho phép nội dung AI', 'Bật quyền kiến thức AI tham khảo nếu muốn dùng F3.'],
      output_rejected: ['Phản hồi AI bị chặn', 'AI đã phản hồi nhưng đầu ra chưa đạt kiểm tra nội dung/định dạng. Không hiển thị câu trả lời bị chặn.'],
      provider_error: ['Lỗi dịch vụ AI', 'Dịch vụ AI chưa kết nối được hoặc tạm thời chưa sẵn sàng. Hãy kiểm tra mạng hoặc thử lại sau.'],
      configuration_error: ['Cần kiểm tra cấu hình AI', 'Kiểm tra key/project ở backend; không gửi key qua chat.'],
      context_budget: ['Cần thu hẹp câu hỏi', 'Bằng chứng chưa gửi được tới AI vì vượt giới hạn hoặc không phù hợp. Hãy hỏi phạm vi hẹp hơn.'],
      busy: ['AI đang bận', 'Đang xử lý yêu cầu AI khác; hãy thử lại sau.'],
      quota: ['AI chạm hạn mức', 'Đang dùng RAG offline sau429; khởi động lại khi hạn mức hồi phục.'],
    };
    if (!diagnostic || !Object.hasOwn(labels, diagnostic.code)) return null;
    let [label, message] = labels[diagnostic.code];
    if (diagnostic.code === 'provider_error' && [401, 403].includes(diagnostic.http_status)) {
      label = 'Lỗi quyền truy cập AI';
      message = 'Kiểm tra key/project và quyền dịch vụ ở backend; không gửi key qua chat.';
    }
    return {label, message};
  }

  function displayReply(reply, answer, keepMarkdown = false) {
    if (answer?.status !== 'answered') return reply;
    const citations = answer.citations || [];
    const ids = new Set(citations.map(citation => String(citation.citation_id)));
    const aiIds = new Set(citations.filter(isAI).map(citation => String(citation.citation_id)));
    const reviewNotices = new Set([
      'Nguồn được duyệt trên Markdown; chưa đối chiếu PDF/DOCX gốc.',
      'Chỉ mô tả theo nguồn đã lưu; chưa xác minh hiệu lực hiện tại.',
      'Trạng thái: verified theo sign-off cấp dự án đã ghi trong nguồn; không phải chứng nhận của trường.',
    ]);
    const aiNotice = /^Nội dung tham khảo do AI (?:biên soạn|sinh)[;,.]/;
    const notices = new Set((answer.warnings || []).filter(warning =>
      reviewNotices.has(warning) || /^Trạng thái (?:xác minh|review):/.test(warning)
      || (aiIds.size > 0 && aiNotice.test(warning))));
    const text = !keepMarkdown && answer.dataset === 'f2' && typeof answer.reply === 'string'
      ? answer.reply : reply;
    const compact = text.split(/\r?\n/).filter(line => {
      const trimmed = line.trim();
      const footer = /^Nguồn \[(\d+)\]:/.exec(trimmed);
      return !notices.has(trimmed) && !(footer && ids.has(footer[1]));
    }).map(line => (keepMarkdown ? line : line.replace(/^(\s*(?:\[\d+\][ \t]+)?)#{1,6}[ \t]+/, '$1'))
      .replace(/\[(\d+)\]/g, (marker, id) => aiIds.has(id) ? '' : marker)
      .trimEnd()
    ).join('\n').replace(/\n{3,}/g, '\n\n').trim();
    return compact || reply;
  }

  function generationInfo(result, requested) {
    const metadata = result.generation;
    const answered = result.mode === 'hus_rag' && result.hus_answer?.status === 'answered';
    const aiOnly = onlyAI(result.hus_answer?.citations);
    if (metadata != null && (typeof metadata !== 'object' || typeof metadata.used !== 'boolean')) {
      throw new Error('invalid_generation');
    }
    if (metadata?.used === true) {
      if (!requested || !answered || typeof metadata.model !== 'string' || !metadata.model.trim()
          || metadata.fallback_reason != null) throw new Error('invalid_generation');
      return {kind: 'used', label: aiOnly ? 'AI diễn đạt' : 'AI diễn đạt từ nguồn'};
    }
    if (!requested || !answered || (metadata == null && result.generation_mode === 'grounded_llm')) return null;
    const reasons = {
      busy: 'Dịch vụ AI đang bận; hiển thị bản trích nguồn.',
      timeout: 'Dịch vụ AI vượt thời gian chờ; hiển thị bản trích nguồn.',
      http_error: metadata?.http_status === 429
        ? 'Dịch vụ AI đã chạm hạn mức; hiển thị bản trích nguồn.'
        : [401, 403].includes(metadata?.http_status)
          ? 'Cấu hình hoặc quyền truy cập dịch vụ AI chưa hợp lệ; hiển thị bản trích nguồn.'
          : metadata?.http_status === 503
            ? 'Dịch vụ AI tạm thời chưa sẵn sàng; hiển thị bản trích nguồn.'
            : 'Không kết nối được dịch vụ AI; hiển thị bản trích nguồn.',
      transport_error: 'Không kết nối được dịch vụ AI; hiển thị bản trích nguồn.',
      prompt_budget: 'Bằng chứng vượt giới hạn diễn đạt; hiển thị bản trích nguồn.',
      output_budget: 'Phản hồi AI vượt giới hạn; hiển thị bản trích nguồn.',
      invalid_output: 'Phản hồi AI chưa đạt kiểm tra; hiển thị bản trích nguồn.',
      evidence_coverage: 'Phản hồi AI chưa đạt kiểm tra; hiển thị bản trích nguồn.',
      invalid_response: 'Phản hồi AI chưa đạt kiểm tra; hiển thị bản trích nguồn.',
      invalid_result: 'Phản hồi AI chưa đạt kiểm tra; hiển thị bản trích nguồn.',
    };
    const note = Object.hasOwn(reasons, metadata?.fallback_reason) ? reasons[metadata.fallback_reason]
      : 'AI chưa sẵn sàng; hiển thị bản trích nguồn.';
    return {kind: 'fallback', label: aiOnly ? 'Nội dung AI tham khảo' : 'Bản trích nguồn',
      note: aiOnly ? note.replace('bản trích nguồn', 'nội dung AI tham khảo đã lưu') : note};
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

  if (typeof module !== 'undefined' && module.exports) {
    module.exports = {
      citationURL,
      citationLabel,
      generationInfo,
      displayReply,
      escapeHtml,
      formatInlineMarkdown,
      renderSafeMarkdown,
      groupCitations,
    };
  }
  if (typeof document === 'undefined') return;

  const major = document.getElementById('rag-major');
  const version = document.getElementById('rag-version');
  const question = document.getElementById('rag-question');
  const send = document.getElementById('rag-send');
  const generated = document.getElementById('rag-generated');
  const rewrite = document.getElementById('rag-rewrite');
  const rewriteUnavailable = document.getElementById('rag-rewrite-unavailable');
  const autoNote = document.getElementById('rag-auto-note');
  const disclosure = document.getElementById('rag-rewrite-disclosure');
  const manualDisclosure = disclosure.textContent;
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
    const auto = config?.llm_auto === true;
    rewrite.parentElement.hidden = auto;
    autoNote.hidden = !auto;
    autoNote.textContent = config?.llm_quota_exhausted
      ? 'Gemini đã báo chạm hạn mức (429); đang trả lời offline từ RAG. Khởi động lại server để thử Gemini khi hạn mức được khôi phục.'
      : 'Tự động dùng Gemini. Chỉ chuyển sang RAG offline khi dịch vụ báo chạm hạn mức (429); lỗi khác sẽ được thông báo.';
    disclosure.textContent = auto
      ? 'Khi hỏi, câu hỏi và bằng chứng phù hợp sẽ được gửi tới Google Gemini. Khi cần hiểu ý hỏi, AI cũng nhận ngành/phiên bản và danh mục mã/tên môn. Không gửi lịch sử hội thoại, tài khoản hay bảng điểm. Đổi ngành tắt quyền F3; chế độ Gemini tự động vẫn giữ.'
      : manualDisclosure;
    major.disabled = unavailable;
    question.disabled = unavailable || busy;
    generated.disabled = unavailable || busy;
    rewrite.disabled = unavailable || busy || config?.llm_rewrite_available !== true;
    rewriteUnavailable.hidden = auto || config?.llm_rewrite_available === true;
    rewrite.setAttribute('aria-describedby', 'rag-rewrite-disclosure'
      + (rewriteUnavailable.hidden ? '' : ' rag-rewrite-unavailable'));
    send.disabled = unavailable || busy || !question.value.trim();
    send.firstChild.textContent = busy ? 'Đang trả lời ' : 'Gửi ';
    form.setAttribute('aria-busy', String(busy));
    for (const {button, item} of catalogEntries) {
      button.disabled = unavailable || busy || (item.requires_ai && !generated.checked);
    }
    for (const button of messages.querySelectorAll('.rag-source-choice')) {
      button.disabled = unavailable || busy;
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

  function groupCitations(citations, origin) {
    if (!Array.isArray(citations) || !citations.length) return [];
    const groups = new Map();
    for (const citation of citations) {
      if (!citation || typeof citation !== 'object') continue;
      const url = citationURL(citation, origin);
      const scope = citation.metadata?.scope;
      const key = JSON.stringify([
        url, citation.evidence_kind, citation.source_id, citationLabel(citation),
        citation.document_sha256, citation.pdf_page, citation.pdf_pages,
        citation.availability, citation.availability_note, citation.review_status,
        scope?.curriculum_version || citation.metadata?.program_version, scope?.program_variant,
      ]);

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

  function appendCitation(container, citation) {
    const card = document.createElement('div');
    card.className = 'rag-citation';
    const heading = document.createElement('p');
    heading.className = 'rag-citation-title';
    if (citation.citation_id) {
      const num = document.createElement('span');
      num.className = 'rag-citation-num';
      num.textContent = `[${citation.citation_id}]`;
      heading.appendChild(num);
    }
    const kind = document.createElement('span');
    kind.className = 'rag-citation-kind';
    kind.textContent = ({pdf: 'PDF', web: 'WEB', file: 'TỆP'}[citation.evidence_kind] || 'NGUỒN');
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
    const details = [];
    if (citation.pdf_pages?.length) details.push('Trang ' + citation.pdf_pages.join(', '));
    else if (citation.pdf_page) details.push('Trang ' + citation.pdf_page);
    if (citation.dataset === 'f1') {
      const scope = citation.metadata?.scope;
      const edition = scope?.curriculum_version || citation.metadata?.program_version;
      const variant = {standard: 'Hệ chuẩn', high_quality: 'Hệ chất lượng cao',
        talent: 'Hệ tài năng', advanced: 'Hệ tiên tiến'}[scope?.program_variant];
      if (edition && edition !== 'unknown') details.push(edition);
      if (variant) details.push(variant);
    }
    if (!url) details.push(citation.availability_note || 'Chưa có liên kết nguồn khả dụng.');
    if (citation.review_status) details.push('Trạng thái nguồn: ' + citation.review_status);
    if (details.length) {
      const detail = document.createElement('span');
      detail.className = 'rag-citation-detail';
      detail.textContent = details.join(' · ');
      heading.appendChild(detail);
    }
    card.appendChild(heading);
    container.appendChild(card);
  }

  function appendMessage(role, reply, answer = null, legacyMarkdown = false) {
    const citations = answer?.citations || [];
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
    if (legacyMarkdown) {
      const badge = document.createElement('span');
      badge.className = 'rag-badge-llm';
      badge.textContent = 'Trợ lý AI HUS';
      speaker.appendChild(badge);
    }
    const text = document.createElement(legacyMarkdown ? 'div' : 'p');
    text.className = 'rag-message-text';
    const visibleReply = displayReply(reply, answer, legacyMarkdown);
    if (legacyMarkdown) renderSafeMarkdown(visibleReply, text);
    else text.textContent = visibleReply;
    body.append(speaker, text);
    if (citations.some(isAI)) {
      const notice = document.createElement('p');
      notice.className = 'rag-ai-notice';
      notice.textContent = 'kiến thức AI · tham khảo';
      body.insertBefore(notice, text);
    }
    const visibleCitations = groupCitations(citations.filter(citation => !isAI(citation)),
      window.location.origin);
    if (visibleCitations.length) {
      const sources = document.createElement('div');
      sources.className = 'rag-citations';
      sources.setAttribute('aria-label', 'Nguồn');
      for (const citation of visibleCitations) appendCitation(sources, citation);
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
    rewrite.checked = false;
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
    const wantsRewrite = config.llm_auto === true
      || (rewrite.checked === true && config.llm_rewrite_available === true);
    // Catalog requests supply scope hints, never permission to send data externally.
    if (wantsRewrite) payload.allow_llm_rewrite = true;
    else delete payload.allow_llm_rewrite;
    appendMessage('user', text);
    question.value = '';
    busy = true;
    updateControls();
    setStatus('Đang tìm thông tin trong dữ liệu của ngành đã chọn…');
    try {
      const response = await fetch('/hus/chat', {method: 'POST',
        headers: {'Content-Type': 'application/json'}, body: JSON.stringify(payload),
        signal: controller.signal, cache: 'no-store'});
      if (!response.ok) {
        const error = new Error('http_' + response.status);
        if (response.status === 502) {
          try {
            const body = await response.json();
            if (diagnosticInfo(body?.detail?.diagnostic)) error.diagnostic = body.detail.diagnostic;
          } catch { /* Keep the safe generic error; never render a raw error body. */ }
        }
        throw error;
      }
      const result = await response.json();
      if (epoch !== scopeGeneration || requestController !== controller) return;
      if (!['basic_chat', 'hus_rag'].includes(result.mode) || typeof result.reply !== 'string'
          || !result.reply.trim()) throw new Error('invalid_response');
      const answer = result.mode === 'hus_rag' ? result.hus_answer : null;
      if (result.mode === 'hus_rag' && !['answered', 'needs_clarification', 'no_information']
        .includes(answer?.status)) throw new Error('invalid_response');
      const info = generationInfo(result, wantsRewrite);
      if (config.llm_auto && result.generation?.used === true) config.llm_quota_exhausted = false;
      if (config.llm_auto && [result.generation, result.interpretation].some(
        item => item?.fallback_reason === 'http_error' && item.http_status === 429)) {
        config.llm_quota_exhausted = true;
      }
      const legacyMarkdown = answer?.status === 'answered'
        && result.generation_mode === 'grounded_llm' && result.generation == null;
      appendMessage('assistant', result.reply, answer, legacyMarkdown);
      if (answer?.status === 'needs_clarification' && Array.isArray(answer.source_choices)) {
        const choices = document.createElement('div');
        choices.className = 'rag-source-choices';
        choices.setAttribute('aria-label', 'Chọn nguồn thông tin');
        for (const choice of answer.source_choices) {
          if (typeof choice?.source_id !== 'string' || typeof choice.version !== 'string'
              || typeof choice.label !== 'string' || typeof choice.review_status !== 'string') continue;
          const button = document.createElement('button');
          button.type = 'button';
          button.className = 'rag-source-choice';
          const variants = {standard: 'Hệ chuẩn', high_quality: 'Hệ chất lượng cao',
            talent: 'Hệ tài năng', advanced: 'Hệ tiên tiến', unknown: 'Chưa rõ hệ'};
          button.textContent = choice.label + ' · ' + choice.version + ' · '
            + (variants[choice.program_variant] || 'Chưa rõ hệ') + ' · ' + choice.review_status;
          button.addEventListener('click', () => {
            if (busy || epoch !== scopeGeneration || selected.id !== currentMajor()?.id) return;
            question.value = text;
            submit(null, {...payload, source_id: choice.source_id, version: choice.version,
              program_variant: choice.program_variant});
          });
          choices.appendChild(button);
        }
        if (choices.childElementCount) messages.lastElementChild.querySelector('.rag-message-content').appendChild(choices);
      }
      let message = '';
      if (result.mode === 'basic_chat') {
        message = 'Đã phản hồi hội thoại.';
      } else if (answer.status === 'needs_clarification') {
        message = 'Cần làm rõ câu hỏi; xem hướng dẫn trong phản hồi.';
      } else if (answer.status === 'no_information') {
        message = 'Chưa có thông tin đủ căn cứ trong phạm vi đã chọn.';
      } else {
        message = answer.facts?.field === 'prerequisites'
          && answer.facts?.prerequisite_status === 'unknown'
          ? 'Đã đối chiếu nguồn; điều kiện tiên quyết vẫn chưa rõ.'
          : 'Đã trả lời theo phạm vi dữ liệu đã chọn.';
      }
      const diagnosis = diagnosticInfo(answer?.diagnostic);
      const statusMessage = [message, diagnosis?.message, info?.label,
        info?.kind === 'fallback' ? info.note : null].filter(Boolean).join(' ');
      if (statusMessage) setStatus(statusMessage);
    } catch (error) {
      if (epoch !== scopeGeneration || requestController !== controller || error.name === 'AbortError') return;
      const unavailable = error.message === 'http_503';
      if (error.message === 'http_502' && config.llm_auto) {
        const diagnosis = diagnosticInfo(error.diagnostic);
        const note = diagnosis?.message || 'AI chưa trả lời được. Kiểm tra kết nối, cấu hình hoặc thử lại sau.';
        appendMessage('assistant', note);
        setStatus(diagnosis?.label || note, true);
        return;
      }
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
