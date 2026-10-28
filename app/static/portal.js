(() => {
  'use strict';
  const $ = id => document.getElementById(`portal-${id}`);
  const copy = {
    vi: {
      heading: 'Hồ sơ học tập', open: 'Đăng nhập VNU', profile: 'Hồ sơ của tôi', intro: 'Đăng nhập bằng tài khoản VNU để xem bảng điểm đã lưu. Mật khẩu chỉ dùng cho lần kết nối này.',
      username: 'Tài khoản VNU', password: 'Mật khẩu VNU', show: 'Hiện mật khẩu', hide: 'Ẩn mật khẩu', login: 'Kết nối VNU', processing: 'Đang lấy dữ liệu…',
      sync: 'Cập nhật bảng điểm', logout: 'Ngắt phiên VNU', delete: 'Xóa bảng điểm VNU', cancel: 'Hủy cập nhật', keep: 'Giữ dữ liệu',
      disconnected: 'Đã ngắt phiên VNU. Bạn vẫn xem được bảng điểm đã lưu.',
      refreshTitle: 'Bảng điểm VNU', refreshDue: 'Đến lúc cập nhật bảng điểm',
      refreshSignedOut: 'Đăng nhập để cập nhật bảng điểm. Bạn sẽ được nhắc cập nhật sau mỗi 7 ngày.',
      refreshMissing: 'Chưa xác định lần cập nhật thành công. Hãy cập nhật bảng điểm từ VNU.',
      refreshReminder: 'Đã ít nhất 7 ngày từ lần đồng bộ thành công. Cập nhật để kiểm tra điểm mới.',
      refreshNext: 'Nhắc cập nhật tiếp theo: ', refreshLast: 'Đồng bộ thành công gần nhất: ',
      reauthIntro: 'Phiên kết nối VNU không còn hiệu lực. Xác thực lại để cập nhật; bảng điểm đã lưu vẫn được giữ.',
      reauthSubmit: 'Xác thực lại và cập nhật', reauthDismiss: 'Để sau',
      confirm: 'Xóa bảng điểm và thông tin VNU đã lưu? Tài khoản Sổ học tập vẫn được giữ.',
      unknown: 'Chưa xác minh độ đầy đủ của bảng điểm. Thông tin hồ sơ chỉ hiển thị khi đọc được từ nguồn VNU.',
      separate: 'Điểm nguồn được giữ nguyên. Điều kiện học chỉ sử dụng bảng điểm và chương trình đã đối chiếu.',
      unparsed: 'Các hàng nguồn cần kiểm tra', waiting: 'Đang đăng nhập VNU và lấy hồ sơ, bảng điểm. Vui lòng chờ, quá trình có thể mất đến 2 phút…',
      saved: 'Đã tải hồ sơ.', empty: 'Chưa có bảng điểm đã lưu. Chọn cập nhật để lấy từ VNU.',
      updated: 'Bảng điểm lưu lúc', account: 'Tài khoản đã xác minh', close: 'Đóng', table: 'Bảng điểm nguồn',
      columns: ['Mã môn', 'Tên học phần', 'Tín chỉ', 'Hệ 10', 'Chữ', 'Hệ 4'],
      back: 'Về Dashboard', source: 'Nguồn VNU', name: 'Họ và tên', program: 'Ngành học', cohort: 'Khóa học',
      earnedCredits: 'Tổng tín chỉ tích lũy', gpa4: 'Điểm trung bình tích lũy hệ 4', unavailable: 'Chưa có thông tin',
      welcomeTitle: 'Hồ sơ học tập của riêng bạn.', welcomeDescription: 'Một nơi để xem lại kết quả từ VNU qua từng học kỳ.', welcomeSource: 'Giữ nguyên điểm và thông tin nguồn', welcomeSync: 'Chủ động cập nhật khi cần', welcomeOwner: 'Quản lý dữ liệu theo tài khoản',
      transcript: 'Bảng điểm nguồn', newest: 'Theo năm học và học kỳ, mới nhất trước.', search: 'Tìm mã hoặc tên học phần', term: 'Học kỳ', allTerms: 'Tất cả học kỳ', rows: 'lượt học', noResults: 'Không có học phần phù hợp.',
      errors: {source_unavailable: 'Đã đăng nhập VNU, nhưng chưa tải được bảng điểm mới. Bạn có thể cập nhật lại; dữ liệu đã lưu vẫn được giữ.',
        identity_unverified: 'Chưa xác minh được danh tính từ VNU. Dữ liệu chưa được lưu.',
        vnu_not_connected: 'Bạn chưa kết nối VNU để lấy bảng điểm.', vnu_already_linked: 'Tài khoản VNU đã có liên kết khác. Không thể tự chuyển quyền sở hữu.',
        vnu_reauth_required: 'Phiên VNU đã hết hạn. Xác thực lại để cập nhật bảng điểm.',
        interaction_required: 'VNU yêu cầu CAPTCHA hoặc mã xác thực. Lần kết nối này chưa hỗ trợ bước đó. Bảng điểm đã lưu được giữ nguyên.',
        incomplete_snapshot: 'Lần đọc mới chưa được xác minh đầy đủ. Giữ nguyên bảng điểm đã lưu.',
        session_expired: 'Phiên đã hết hạn. Vui lòng đăng nhập lại.', origin_rejected: 'Hãy mở hệ thống tại http://127.0.0.1:8000.',
        cancelled: 'Đã hủy cập nhật.', busy: 'Đang có lượt kết nối. Vui lòng chờ rồi thử lại.',
        storage_unavailable: 'Chưa kết nối được kho hồ sơ. Kiểm tra database và migration.',
        browser_unavailable: 'Không khởi động được trình duyệt kết nối VNU. Vui lòng thử lại hoặc kiểm tra Chrome trên máy chủ.',
        portal_unavailable: 'Kết nối VNU gặp lỗi kỹ thuật. Vui lòng thử lại sau; dữ liệu đã lưu được giữ nguyên.',
        structure_changed: 'Bố cục bảng điểm VNU chưa được nhận diện. Dữ liệu đã lưu được giữ nguyên.',
        worker_failed: 'Hệ thống gặp lỗi xử lý bảng điểm. Vui lòng thử lại.',
        worker_output_invalid: 'Hệ thống chưa đọc được kết quả bảng điểm. Vui lòng thử lại.',
        timeout: 'Kết nối quá thời gian chờ. Bảng điểm đã lưu được giữ nguyên.',
        fallback: 'Chưa lấy được dữ liệu từ VNU. Kiểm tra tài khoản hoặc thử lại sau; dữ liệu đã lưu được giữ nguyên.'}
    },
    en: {
      heading: 'Academic profile', open: 'Sign in with VNU', profile: 'My profile', intro: 'Sign in with your VNU account to view saved grades. Your password is used for this connection only.',
      username: 'VNU account', password: 'VNU password', show: 'Show password', hide: 'Hide password', login: 'Connect VNU', processing: 'Retrieving your data…',
      sync: 'Update transcript', logout: 'Disconnect VNU session', delete: 'Delete VNU data', cancel: 'Cancel update', keep: 'Keep data',
      disconnected: 'VNU session disconnected. Your saved transcript remains available.',
      refreshTitle: 'VNU transcript', refreshDue: 'Time to update your transcript',
      refreshSignedOut: 'Sign in to update your transcript. You will be reminded every 7 days.',
      refreshMissing: 'The last successful update is unknown. Update your transcript from VNU.',
      refreshReminder: 'It has been at least 7 days since the last successful sync. Update to check for new grades.',
      refreshNext: 'Next update reminder: ', refreshLast: 'Last successful sync: ',
      reauthIntro: 'The VNU connection is no longer valid. Verify again to update; your saved transcript is retained.',
      reauthSubmit: 'Verify and update', reauthDismiss: 'Later',
      confirm: 'Delete your saved VNU transcript and profile? Your study account is retained.',
      unknown: 'Transcript completeness is unverified. Profile details appear only when supplied by VNU.',
      separate: 'Source grades stay unchanged. Course eligibility uses reviewed transcript and curriculum context.',
      unparsed: 'Source rows requiring review', waiting: 'Signing in to VNU and retrieving your profile and grades. Please wait; this may take up to 2 minutes…',
      saved: 'Profile loaded.', empty: 'No saved transcript. Choose update to retrieve it from VNU.',
      updated: 'Transcript saved', account: 'Verified account', close: 'Close', table: 'Source transcript',
      columns: ['Course code', 'Course name', 'Credits', '10-point', 'Letter', '4-point'],
      back: 'Back to Dashboard', source: 'VNU source', name: 'Full name', program: 'Program', cohort: 'Cohort',
      earnedCredits: 'Accumulated credits', gpa4: 'Cumulative GPA (4-point scale)', unavailable: 'Unavailable',
      welcomeTitle: 'Your own academic profile.', welcomeDescription: 'A place to revisit your VNU results, semester by semester.', welcomeSource: 'Original grades and source information', welcomeSync: 'Update whenever you need', welcomeOwner: 'Data managed under your account',
      transcript: 'Source transcript', newest: 'By academic year and semester, newest first.', search: 'Search course code or name', term: 'Semester', allTerms: 'All semesters', rows: 'attempts', noResults: 'No matching courses.',
      errors: {source_unavailable: 'VNU sign-in succeeded, but the latest transcript could not be retrieved. Try updating again; your saved data is retained.',
        identity_unverified: 'VNU identity could not be verified. No data was saved.',
        vnu_not_connected: 'Connect VNU to retrieve your transcript.', vnu_already_linked: 'This VNU identity has another account link. Ownership cannot be transferred automatically.',
        vnu_reauth_required: 'Your VNU session expired. Verify again to update your transcript.',
        interaction_required: 'VNU requires a CAPTCHA or verification code. This connection cannot complete that step yet. Your saved transcript was retained.',
        incomplete_snapshot: 'The new transcript is not verified complete. Your saved transcript was retained.',
        session_expired: 'Session expired. Please sign in again.', origin_rejected: 'Open http://127.0.0.1:8000.',
        cancelled: 'Update cancelled.', busy: 'A connection is running. Please try again shortly.',
        storage_unavailable: 'Profile storage is unavailable. Check database migrations.',
        browser_unavailable: 'The VNU browser could not start. Try again or check Chrome on the server.',
        portal_unavailable: 'The VNU connection encountered a technical error. Please try again later; saved data was retained.',
        structure_changed: 'The VNU transcript layout was not recognized. Your saved data was retained.',
        worker_failed: 'The system could not process your transcript. Please try again.',
        worker_output_invalid: 'The system could not read the transcript result. Please try again.',
        timeout: 'Connection timed out. Your saved transcript was retained.',
        fallback: 'Could not retrieve VNU data. Check your account or try again later. Saved data was retained.'}
    }
  };
  let profile = null, job = null, epoch = 0, loadSequence = 0, busy = false, messageKey = '', errorKey = '', expiryTimer;
  let signedOut = false;
  let requestedTerm = null, requestedLetter = null;
  let accountId = null;
  let reminderTimer;
  const reminderInterval = 7 * 24 * 60 * 60 * 1000;
  const text = () => copy[window.workspaceI18n.language === 'en' ? 'en' : 'vi'];
  function status(key = '', error = '') {
    messageKey = key; errorKey = error;
    const loading = key === 'waiting' && !error;
    $('status').textContent = error ? (text().errors[error] || text().errors.fallback) : (text()[key] || '');
    $('status').classList.toggle('is-loading', loading);
    $('submit').classList.toggle('is-loading', loading);
    $('submit').textContent = loading ? text().processing : text().login;
    $('login').setAttribute('aria-busy', String(loading));
    $('reauth').setAttribute('aria-busy', String(loading));
    $('reauth-submit').textContent = loading ? text().processing : text().reauthSubmit;
  }
  function reset() {
    clearTimeout(expiryTimer); clearTimeout(reminderTimer);
    requestedTerm = null; requestedLetter = null;
    epoch++; profile = null; job = null; signedOut = true; lock(false); $('table').replaceChildren(); $('summary').textContent = '';
    $('unparsed').querySelector('pre').textContent = ''; $('identity').textContent = ''; $('updated').textContent = '';
    ['name', 'program', 'cohort', 'earned-credits', 'gpa4'].forEach(key => { $(key).textContent = ''; });
    $('search').value = ''; $('term').replaceChildren(); $('row-count').textContent = '';
    $('profile').hidden = true; $('login').hidden = false; $('confirm').hidden = true; $('cancel').hidden = true;
    $('login').reset(); $('password').type = 'password'; $('show').setAttribute('aria-pressed', 'false');
    $('reauth').reset(); $('reauth').hidden = true;
    render();
    document.dispatchEvent(new CustomEvent('workspace:portal-data', {detail: null}));
  }
  async function api(path, method = 'GET', body) {
    const current = epoch;
    const response = await fetch(path, {method, credentials: 'same-origin', cache: 'no-store',
      headers: {...(body ? {'Content-Type': 'application/json'} : {}), ...(method !== 'GET' && window.systemAuth?.csrf ? {'X-CSRF-Token': window.systemAuth.csrf} : {})}, body: body ? JSON.stringify(body) : undefined});
    const result = await response.json();
    if (!response.ok) {
      if (current === epoch && response.status === 401) { reset(); window.systemAuth?.expire(); status('', 'session_expired'); }
      throw new Error(result.detail);
    }
    return result;
  }
  function cell(row, value, tag = 'td') { const node = document.createElement(tag); node.textContent = value ?? ''; row.append(node); return node; }
  function sourceSummaryValue(rows, label) {
    for (const row of rows || []) {
      for (let index = 0; index < row.length; index++) {
        const value = String(row[index] ?? '').trim();
        if (!value.startsWith(label)) continue;
        const inline = value.slice(label.length).replace(/^\s*[:：]?\s*/, '').trim();
        if (inline) return inline;
        const adjacent = row.slice(index + 1).find(item => String(item ?? '').trim());
        if (adjacent !== undefined) return String(adjacent).trim();
      }
    }
    return '—';
  }
  function renderReminder() {
    clearTimeout(reminderTimer);
    const t = text(), now = Date.now();
    const last = Date.parse(profile?.last_synced_at || profile?.fetched_at || '');
    const known = Boolean(profile?.snapshot) && Number.isFinite(last) && last <= now;
    const due = known && now - last >= reminderInterval;
    const locale = window.workspaceI18n.language === 'en' ? 'en-GB' : 'vi-VN';
    $('refresh-title').textContent = due ? t.refreshDue : t.refreshTitle;
    $('refresh-time').textContent = known ? t.refreshLast + new Date(last).toLocaleString(locale) : '';
    $('refresh-message').textContent = !profile ? t.refreshSignedOut : !known ? t.refreshMissing
      : due ? t.refreshReminder : t.refreshNext + new Date(last + reminderInterval).toLocaleString(locale);
    document.querySelector('.transcript-refresh-bar').classList.toggle('is-due', due);
    if (known && !due) reminderTimer = setTimeout(renderReminder, last + reminderInterval - now);
  }
  function render() {
    const t = text(); $('heading').textContent = t.heading;
    $('close').textContent = t.back; document.querySelector('#portal-dialog .portal-table-scroll').setAttribute('aria-label', t.table);
    $('welcome').hidden = Boolean(profile);
    document.querySelectorAll('[data-portal-copy]').forEach(node => { node.textContent = t[node.dataset.portalCopy]; });
    $('show').textContent = $('password').type === 'password' ? t.show : t.hide;
    status(messageKey, errorKey);
    renderReminder();
    const review = $('collection-review');
    review.replaceChildren();
    const messages = window.workspaceI18n.collectionReviewMessages(profile?.latest_collection);
    review.hidden = !messages.length;
    messages.forEach(message => { const row = document.createElement('p'); row.textContent = message; review.append(row); });
    $('reauth-account').value = profile?.subject || '';
    if (!profile) return;
    ['name', 'program', 'cohort'].forEach(key => {
      const value = profile.profile?.[key];
      $(key).textContent = typeof value === 'string' && value.trim() ? value : t.unavailable;
    });
    $('earned-credits').textContent = sourceSummaryValue(profile.snapshot?.source_summary, 'Tổng tín chỉ tích lũy');
    $('gpa4').textContent = sourceSummaryValue(profile.snapshot?.source_summary, 'Điểm trung bình tích lũy hệ 4');
    $('identity').textContent = profile.subject;
    $('updated').textContent = `${t.updated}: ${profile.fetched_at ? new Date(profile.fetched_at).toLocaleString(window.workspaceI18n.language === 'en' ? 'en-GB' : 'vi-VN') : '—'}`;
    $('table').replaceChildren(); const head = $('table').createTHead().insertRow();
    t.columns.forEach(value => cell(head, value, 'th').scope = 'col');
    const body = $('table').createTBody(), snap = profile.snapshot;
    $('summary').textContent = (snap?.source_summary || []).map(row => window.workspaceI18n.formatSourceSummary(row)).join('\n');
    const groups = new Map();
    (snap?.attempts || []).forEach(row => { const key = row.term || '—'; if (!groups.has(key)) groups.set(key, []); groups.get(key).push(row); });
    function termOrder(term) {
      const year = term.match(/\d{4}\s*[-–]\s*\d{4}/)?.[0].slice(0, 4) || '0';
      const semester = term.match(/(?:KỲ|KÌ)\s*(\d+)/i)?.[1] || '0';
      return Number(year) * 10 + Number(semester);
    }
    const sorted = [...groups].sort((a, b) => termOrder(b[0]) - termOrder(a[0]));
    const selected = requestedTerm ?? $('term').value, query = $('search').value.trim().toLocaleLowerCase();
    $('term').replaceChildren(new Option(t.allTerms, ''));
    sorted.forEach(([term]) => $('term').add(new Option(term, term)));
    $('term').value = [...groups.keys()].includes(selected) ? selected : '';
    requestedTerm = null;
    let shown = 0;
    sorted.forEach(([term, sourceRows]) => {
      if ($('term').value && $('term').value !== term) return;
      const rows = sourceRows.filter(row => (requestedLetter === null || String(row.letter ?? '').trim() === requestedLetter)
        && (!query || `${row.code} ${row.name}`.toLocaleLowerCase().includes(query)));
      if (!rows.length) return;
      shown += rows.length;
      const heading = body.insertRow(); heading.className = 'portal-term'; cell(heading, term).colSpan = 6;
      rows.forEach(attempt => { const row = body.insertRow(); ['code', 'name', 'credits', 'grade10', 'letter', 'grade4'].forEach(key => cell(row, attempt[key])); });
    });
    $('row-count').textContent = `${shown} / ${snap?.attempts?.length || 0} ${t.rows}`;
    if (!shown) cell(body.insertRow(), t.noResults).colSpan = 6;
    $('unparsed').hidden = !snap?.unknown_rows?.length;
    $('unparsed').querySelector('pre').textContent = (snap?.unknown_rows || []).map(row => row.cells.join(' | ')).join('\n');
  }
  async function load() {
    const current = epoch, sequence = ++loadSequence;
    let state, result;
    try {
      state = await api('/auth/session');
      if (current !== epoch || sequence !== loadSequence) return;
      if (state.authenticated !== true) {
        const expired = Boolean(profile);
        reset(); status('', expired ? 'session_expired' : ''); return;
      }
      result = await api('/me/profile');
    } catch (err) {
      if (current !== epoch || sequence !== loadSequence) return;
      throw err;
    }
    if (current !== epoch || sequence !== loadSequence) return;
    if (!result.subject) {
      profile = null; $('login').hidden = false; $('profile').hidden = true; render(); status('empty');
      document.dispatchEvent(new CustomEvent('workspace:portal-data', {detail: null})); return;
    }
    profile = result; $('login').hidden = true; $('profile').hidden = false; render();
    if (!errorKey && $('reauth').hidden) status(profile.latest_collection?.save_status === 'retained' ? '' : profile.snapshot ? 'saved' : 'empty', profile.latest_collection?.save_status === 'retained' ? 'incomplete_snapshot' : '');
    document.dispatchEvent(new CustomEvent('workspace:portal-data', {detail: {
      snapshot: result.snapshot, fetched_at: result.fetched_at, latest_collection: result.latest_collection,
      profile: {program: result.profile?.program, cohort: result.profile?.cohort}
    }}));
    clearTimeout(expiryTimer);
    if (Number.isFinite(result.expires_in)) expiryTimer = setTimeout(() => window.systemAuth?.refresh().catch(() => {}), result.expires_in * 1000);
  }
  function lock(value) {
    busy = value; $('submit').disabled = value; $('sync').disabled = value;
    $('reauth-submit').disabled = value; $('reauth-dismiss').disabled = value;
  }
  function syncError(code) {
    if (code === 'vnu_reauth_required') status('reauthIntro');
    else status('', code);
    if (code === 'vnu_reauth_required' && profile) {
      $('reauth').hidden = false; $('reauth-account').value = profile.subject;
      $('reauth-password').value = ''; $('reauth-password').focus();
      $('reauth').scrollIntoView({block: 'center'});
    }
  }
  function beginPolling(result, current) {
    if (result.state === 'reauth_required') { syncError('vnu_reauth_required'); return; }
    job = result.id; $('reauth').hidden = true; $('reauth').reset();
    $('cancel').hidden = false; poll(current);
  }
  async function openProfile() {
    if (window.systemAuth?.ready) await window.systemAuth.ready;
    if (window.systemAuth && (!window.systemAuth.account || window.systemAuth.account.must_change_password)) return;
    render(); if (busy || profile || signedOut) return;
    const current = epoch;
    lock(true);
    try { await load(); }
    catch (err) { if (current === epoch) status('', err.message === 'session_expired' ? '' : err.message); }
    finally { if (current === epoch) lock(false); }
  }
  $('close').onclick = () => window.workspaceNavigate('tab-dashboard');
  document.addEventListener('workspace:open-transcript-term', event => {
    const term = event.detail?.term;
    if (typeof term !== 'string' || !term) return;
    requestedTerm = term;
    $('search').value = '';
    window.workspaceNavigate('portal-dialog');
    if (profile) render();
  });
  document.addEventListener('workspace:open-transcript-grade', event => {
    const letter = event.detail?.letter;
    if (typeof letter !== 'string') return;
    requestedLetter = letter;
    requestedTerm = '';
    $('search').value = '';
    window.workspaceNavigate('portal-dialog');
    if (profile) render();
  });
  document.addEventListener('workspace:navigate', event => {
    if (event.detail === 'portal-dialog') openProfile();
    else { requestedLetter = null; $('password').value = ''; $('reauth-password').value = ''; }
  });
  document.addEventListener('workspace:portal-refresh', () => openProfile());
  document.addEventListener('workspace:vnu-login', async event => {
    const current = epoch;
    if (!event.detail?.warning) return;
    try { await load(); if (current === epoch) status('', event.detail.warning); }
    catch (err) { if (current === epoch) status('', err.message); }
  });
  document.addEventListener('workspace:session-expired', () => { reset(); status('', 'session_expired'); });
  document.addEventListener('workspace:account-change', event => {
    const id = event.detail && !event.detail.must_change_password ? event.detail.account_id + ':' + event.detail.session_id : null;
    if (id !== accountId) { accountId = id; reset(); if (id) { signedOut = false; openProfile(); } }
    if (!id) reset();
  });
  $('search').addEventListener('input', render);
  $('term').addEventListener('change', render);
  $('show').onclick = () => { const visible = $('password').type === 'password'; $('password').type = visible ? 'text' : 'password'; $('show').setAttribute('aria-pressed', String(visible)); render(); };
  $('login').onsubmit = async event => {
    event.preventDefault(); if (busy || profile) return;
    const current = epoch;
    const submitted = {username: $('username').value, password: $('password').value};
    $('password').value = ''; lock(true); status('waiting');
    try {
      const result = await api('/me/portal-connection', 'POST', submitted);
      if (current !== epoch) return;
      signedOut = false; await load(); if (current === epoch && result.warning) status('', result.warning);
    } catch (err) { if (current === epoch || err.message === 'session_expired') status('', err.message); }
    finally { submitted.password = ''; if (current === epoch) lock(Boolean(job)); }
  };
  async function poll(current) {
    if (!job || current !== epoch) return;
    try {
      const result = await api(`/me/portal-sync/${encodeURIComponent(job)}`);
      if (current !== epoch) return;
      if (['running', 'saving'].includes(result.state)) { setTimeout(() => poll(current), 1000); return; }
      job = null; $('cancel').hidden = true; await load();
      if (current !== epoch) return;
      if (result.error || result.state === 'cancelled') syncError(result.error || 'cancelled');
    } catch (err) { if (current !== epoch) return; status('', err.message); job = null; $('cancel').hidden = true; }
    finally { if (current === epoch && !job) lock(false); }
  }
  $('sync').onclick = async () => {
    if (busy || job) return;
    window.workspaceNavigate('portal-dialog');
    if (!profile) { $('username').focus(); $('login').scrollIntoView({block: 'center'}); return; }
    const current = epoch;
    lock(true); status('waiting');
    try {
      const result = await api('/me/portal-sync', 'POST');
      if (current === epoch) beginPolling(result, current);
    } catch (err) { if (current === epoch) syncError(err.message); }
    finally { if (current === epoch) lock(Boolean(job)); }
  };
  $('reauth').onsubmit = async event => {
    event.preventDefault(); if (busy || !profile) return;
    const current = epoch, submitted = {password: $('reauth-password').value};
    $('reauth-password').value = ''; lock(true); status('waiting');
    try {
      const result = await api('/me/portal-reauth', 'POST', submitted);
      if (current === epoch) beginPolling(result, current);
    } catch (err) { if (current === epoch) syncError(err.message); }
    finally { submitted.password = ''; if (current === epoch) lock(Boolean(job)); }
  };
  $('reauth-dismiss').onclick = () => { $('reauth').hidden = true; $('reauth').reset(); status(); };
  $('cancel').onclick = async () => { try { if (job) await api(`/me/portal-sync/${encodeURIComponent(job)}`, 'DELETE'); } catch (err) { status('', err.message); } };
  $('logout').onclick = async () => {
    lock(true); status();
    try { await api('/me/portal-connection', 'DELETE'); status('disconnected'); }
    catch (err) { status('', err.message); }
    finally { lock(false); }
  };
  $('delete').onclick = () => { $('confirm').hidden = false; $('confirm').querySelector('button').focus(); };
  $('keep').onclick = () => { $('confirm').hidden = true; };
  $('confirm').onsubmit = async event => { event.preventDefault(); try { await api('/me/portal-data', 'DELETE'); reset(); signedOut = false; await load(); } catch (err) { status('', err.message); } };
  document.addEventListener('workspace:language-change', render);
  document.addEventListener('workspace:portal-begin-sync', () => { if (!busy && !job) $('sync').click(); });
  document.addEventListener('visibilitychange', async () => { if (!document.hidden && profile && !busy && $('reauth').hidden) { try { await load(); } catch (err) { status('', err.message); } } });
  render();
})();
