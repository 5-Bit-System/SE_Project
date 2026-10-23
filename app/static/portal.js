(() => {
  'use strict';
  const $ = id => document.getElementById(`portal-${id}`);
  const copy = {
    vi: {
      heading: 'Hồ sơ học tập', open: 'Đăng nhập VNU', profile: 'Hồ sơ của tôi', intro: 'Đăng nhập bằng tài khoản VNU để xem bảng điểm đã lưu. Mật khẩu chỉ dùng cho lần kết nối này.',
      username: 'Tài khoản VNU', password: 'Mật khẩu VNU', show: 'Hiện mật khẩu', hide: 'Ẩn mật khẩu', login: 'Đăng nhập',
      sync: 'Cập nhật hồ sơ và bảng điểm', logout: 'Đăng xuất', delete: 'Xóa dữ liệu đã lưu', cancel: 'Hủy cập nhật', keep: 'Giữ dữ liệu',
      confirm: 'Xóa bảng điểm và thông tin hồ sơ đã lưu? Thao tác này sẽ đăng xuất tài khoản.',
      unknown: 'Chưa xác minh độ đầy đủ của bảng điểm. Thông tin hồ sơ chỉ hiển thị khi đọc được từ nguồn VNU.',
      separate: 'Bảng điểm nguồn được lưu riêng; chưa dùng để tính GPA, tiến độ hoặc gợi ý môn.',
      unparsed: 'Các hàng nguồn cần kiểm tra', waiting: 'Đang kết nối VNU. Có thể mất đến 2 phút…',
      saved: 'Đã tải hồ sơ.', empty: 'Chưa có bảng điểm đã lưu. Chọn cập nhật để lấy từ VNU.',
      updated: 'Lần cập nhật', account: 'Tài khoản đã xác minh', close: 'Đóng', table: 'Bảng điểm nguồn',
      columns: ['Mã môn', 'Tên học phần', 'Tín chỉ', 'Hệ 10', 'Chữ', 'Hệ 4'],
      back: 'Về Dashboard', source: 'Nguồn VNU', name: 'Họ và tên', program: 'Ngành học', cohort: 'Khóa học', unavailable: 'Chưa có thông tin',
      welcomeTitle: 'Hồ sơ học tập của riêng bạn.', welcomeDescription: 'Một nơi để xem lại kết quả từ VNU qua từng học kỳ.', welcomeSource: 'Giữ nguyên điểm và thông tin nguồn', welcomeSync: 'Chủ động cập nhật khi cần', welcomeOwner: 'Quản lý dữ liệu theo tài khoản',
      transcript: 'Bảng điểm nguồn', newest: 'Theo năm học và học kỳ, mới nhất trước.', search: 'Tìm mã hoặc tên học phần', term: 'Học kỳ', allTerms: 'Tất cả học kỳ', rows: 'lượt học', noResults: 'Không có học phần phù hợp.',
      errors: {identity_unverified: 'Chưa xác minh được danh tính từ VNU. Dữ liệu chưa được lưu.',
        interaction_required: 'VNU yêu cầu CAPTCHA hoặc mã xác thực. Lần kết nối này chưa hỗ trợ bước đó. Bảng điểm đã lưu được giữ nguyên.',
        incomplete_snapshot: 'Lần đọc mới chưa được xác minh đầy đủ. Giữ nguyên bảng điểm đã lưu.',
        session_expired: 'Phiên đã hết hạn. Vui lòng đăng nhập lại.', origin_rejected: 'Hãy mở hệ thống tại http://127.0.0.1:8000.',
        cancelled: 'Đã hủy cập nhật.', busy: 'Đang có lượt kết nối. Vui lòng chờ rồi thử lại.',
        storage_unavailable: 'Chưa kết nối được kho hồ sơ. Kiểm tra database và migration.',
        browser_unavailable: 'Chưa cài thành phần kết nối VNU trên máy chủ.',
        worker_failed: 'Hệ thống gặp lỗi xử lý bảng điểm. Vui lòng thử lại.',
        worker_output_invalid: 'Hệ thống chưa đọc được kết quả bảng điểm. Vui lòng thử lại.',
        timeout: 'Kết nối quá thời gian chờ. Bảng điểm đã lưu được giữ nguyên.',
        fallback: 'Chưa lấy được dữ liệu từ VNU. Kiểm tra tài khoản hoặc thử lại sau; dữ liệu đã lưu được giữ nguyên.'}
    },
    en: {
      heading: 'Academic profile', open: 'Sign in with VNU', profile: 'My profile', intro: 'Sign in with your VNU account to view saved grades. Your password is used for this connection only.',
      username: 'VNU account', password: 'VNU password', show: 'Show password', hide: 'Hide password', login: 'Sign in',
      sync: 'Update profile and transcript', logout: 'Sign out', delete: 'Delete saved data', cancel: 'Cancel update', keep: 'Keep data',
      confirm: 'Delete saved transcript and profile information? This also signs you out.',
      unknown: 'Transcript completeness is unverified. Profile details appear only when supplied by VNU.',
      separate: 'Source grades are saved separately and are not used for GPA, progress or recommendations.',
      unparsed: 'Source rows requiring review', waiting: 'Connecting to VNU. This may take up to 2 minutes…',
      saved: 'Profile loaded.', empty: 'No saved transcript. Choose update to retrieve it from VNU.',
      updated: 'Last updated', account: 'Verified account', close: 'Close', table: 'Source transcript',
      columns: ['Course code', 'Course name', 'Credits', '10-point', 'Letter', '4-point'],
      back: 'Back to Dashboard', source: 'VNU source', name: 'Full name', program: 'Program', cohort: 'Cohort', unavailable: 'Unavailable',
      welcomeTitle: 'Your own academic profile.', welcomeDescription: 'A place to revisit your VNU results, semester by semester.', welcomeSource: 'Original grades and source information', welcomeSync: 'Update whenever you need', welcomeOwner: 'Data managed under your account',
      transcript: 'Source transcript', newest: 'By academic year and semester, newest first.', search: 'Search course code or name', term: 'Semester', allTerms: 'All semesters', rows: 'attempts', noResults: 'No matching courses.',
      errors: {identity_unverified: 'VNU identity could not be verified. No data was saved.',
        interaction_required: 'VNU requires a CAPTCHA or verification code. This connection cannot complete that step yet. Your saved transcript was retained.',
        incomplete_snapshot: 'The new transcript is not verified complete. Your saved transcript was retained.',
        session_expired: 'Session expired. Please sign in again.', origin_rejected: 'Open http://127.0.0.1:8000.',
        cancelled: 'Update cancelled.', busy: 'A connection is running. Please try again shortly.',
        storage_unavailable: 'Profile storage is unavailable. Check database migrations.',
        browser_unavailable: 'The VNU browser connector is not installed on the server.',
        worker_failed: 'The system could not process your transcript. Please try again.',
        worker_output_invalid: 'The system could not read the transcript result. Please try again.',
        timeout: 'Connection timed out. Your saved transcript was retained.',
        fallback: 'Could not retrieve VNU data. Check your account or try again later. Saved data was retained.'}
    }
  };
  let profile = null, job = null, epoch = 0, loadSequence = 0, busy = false, messageKey = '', errorKey = '', expiryTimer;
  const text = () => copy[window.workspaceI18n.language === 'en' ? 'en' : 'vi'];
  function status(key = '', error = '') { messageKey = key; errorKey = error; $('status').textContent = error ? (text().errors[error] || text().errors.fallback) : (text()[key] || ''); }
  function reset() {
    clearTimeout(expiryTimer);
    epoch++; profile = null; job = null; $('table').replaceChildren(); $('summary').textContent = '';
    $('unparsed').querySelector('pre').textContent = ''; $('identity').textContent = ''; $('updated').textContent = '';
    ['name', 'program', 'cohort'].forEach(key => { $(key).textContent = ''; });
    $('search').value = ''; $('term').replaceChildren(); $('row-count').textContent = '';
    $('profile').hidden = true; $('login').hidden = false; $('confirm').hidden = true; $('cancel').hidden = true;
    $('login').reset(); $('password').type = 'password'; $('show').setAttribute('aria-pressed', 'false');
    render();
    document.dispatchEvent(new CustomEvent('workspace:portal-data', {detail: null}));
  }
  async function api(path, method = 'GET', body) {
    const current = epoch;
    const response = await fetch(path, {method, credentials: 'same-origin', cache: 'no-store',
      headers: body ? {'Content-Type': 'application/json'} : {}, body: body ? JSON.stringify(body) : undefined});
    const result = await response.json();
    if (!response.ok) { if (current === epoch && response.status === 401 && path !== '/auth/portal') reset(); throw new Error(result.detail); }
    return result;
  }
  function cell(row, value, tag = 'td') { const node = document.createElement(tag); node.textContent = value ?? ''; row.append(node); return node; }
  function render() {
    const t = text(); $('heading').textContent = t.heading;
    $('close').textContent = t.back; document.querySelector('#portal-dialog .portal-table-scroll').setAttribute('aria-label', t.table);
    $('welcome').hidden = Boolean(profile);
    document.querySelectorAll('[data-portal-copy]').forEach(node => { node.textContent = t[node.dataset.portalCopy]; });
    $('show').textContent = $('password').type === 'password' ? t.show : t.hide;
    status(messageKey, errorKey);
    if (!profile) return;
    ['name', 'program', 'cohort'].forEach(key => {
      const value = profile.profile?.[key];
      $(key).textContent = typeof value === 'string' && value.trim() ? value : t.unavailable;
    });
    $('identity').textContent = profile.subject;
    $('updated').textContent = `${t.updated}: ${profile.fetched_at ? new Date(profile.fetched_at).toLocaleString() : '—'}`;
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
    const selected = $('term').value, query = $('search').value.trim().toLocaleLowerCase();
    $('term').replaceChildren(new Option(t.allTerms, ''));
    sorted.forEach(([term]) => $('term').add(new Option(term, term)));
    $('term').value = [...groups.keys()].includes(selected) ? selected : '';
    let shown = 0;
    sorted.forEach(([term, sourceRows]) => {
      if ($('term').value && $('term').value !== term) return;
      const rows = sourceRows.filter(row => !query || `${row.code} ${row.name}`.toLocaleLowerCase().includes(query));
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
    const current = epoch, sequence = ++loadSequence, result = await api('/me/profile');
    if (current !== epoch || sequence !== loadSequence) return;
    profile = result; $('login').hidden = true; $('profile').hidden = false; render(); status(profile.snapshot ? 'saved' : 'empty');
    document.dispatchEvent(new CustomEvent('workspace:portal-data', {detail: {
      snapshot: result.snapshot, fetched_at: result.fetched_at,
      profile: {program: result.profile?.program, cohort: result.profile?.cohort}
    }}));
    clearTimeout(expiryTimer);
    if (Number.isFinite(result.expires_in)) expiryTimer = setTimeout(() => { reset(); status('', 'session_expired'); }, result.expires_in * 1000);
  }
  function lock(value) { busy = value; $('submit').disabled = value; $('sync').disabled = value; }
  async function openProfile() { render(); if (busy || profile) return; lock(true); try { await load(); } catch (err) { if (err.message !== 'session_expired') status('', err.message); else status(); } finally { lock(false); } }
  $('close').onclick = () => window.workspaceNavigate('tab-dashboard');
  document.addEventListener('workspace:navigate', event => {
    if (event.detail === 'portal-dialog') openProfile();
    else $('password').value = '';
  });
  document.addEventListener('workspace:portal-refresh', () => openProfile());
  document.addEventListener('workspace:session-expired', () => { reset(); status('', 'session_expired'); });
  $('search').addEventListener('input', render);
  $('term').addEventListener('change', render);
  $('show').onclick = () => { const visible = $('password').type === 'password'; $('password').type = visible ? 'text' : 'password'; $('show').setAttribute('aria-pressed', String(visible)); render(); };
  $('login').onsubmit = async event => {
    event.preventDefault(); if (busy) return;
    const updating = Boolean(profile), current = epoch;
    const submitted = {username: $('username').value, password: $('password').value};
    $('password').value = ''; lock(true); status('waiting');
    try {
      const result = await api(updating ? '/me/portal-sync' : '/auth/portal', 'POST', submitted);
      if (current !== epoch) return;
      if (updating) { job = result.id; $('login').hidden = true; $('cancel').hidden = false; poll(current); }
      else { await load(); if (result.warning) status('', result.warning); }
    } catch (err) { if (current === epoch || err.message === 'session_expired') status('', err.message); }
    finally { submitted.password = ''; lock(false); }
  };
  async function poll(current) {
    if (!job || current !== epoch) return;
    try {
      const result = await api(`/me/portal-sync/${encodeURIComponent(job)}`);
      if (current !== epoch) return;
      if (['running', 'saving'].includes(result.state)) { setTimeout(() => poll(current), 1000); return; }
      job = null; $('cancel').hidden = true; await load();
      if (result.error || result.state === 'cancelled') status('', result.error || 'cancelled');
    } catch (err) { status('', err.message); job = null; $('cancel').hidden = true; }
  }
  $('sync').onclick = () => { if (job) return; $('login').hidden = false; $('username').value = profile.subject; $('password').focus(); };
  $('cancel').onclick = async () => { try { if (job) await api(`/me/portal-sync/${encodeURIComponent(job)}`, 'DELETE'); } catch (err) { status('', err.message); } };
  $('logout').onclick = async () => {
    reset(); lock(true); status();
    try { await api('/auth/logout', 'POST'); }
    catch (err) { status('', err.message); }
    finally { lock(false); }
  };
  $('delete').onclick = () => { $('confirm').hidden = false; $('confirm').querySelector('button').focus(); };
  $('keep').onclick = () => { $('confirm').hidden = true; };
  $('confirm').onsubmit = async event => { event.preventDefault(); try { await api('/me/portal-data', 'DELETE'); reset(); status(); } catch (err) { status('', err.message); } };
  document.addEventListener('workspace:language-change', render);
  document.addEventListener('visibilitychange', async () => { if (!document.hidden && profile) { try { await load(); } catch (err) { status('', err.message); } } });
  render();
})();
