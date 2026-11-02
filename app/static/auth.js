/* VNU student sign-in and independent local administrator authentication. */
(() => {
  'use strict';
  const $ = id => document.getElementById(id);
  const copy = {
    vi: {eyebrow:'Tài khoản Sổ học tập',headline:'Một nơi cho hành trình học tập của bạn.',description:'Đăng nhập Sổ học tập để quản lý hồ sơ. Kết nối VNU khi bạn muốn lấy bảng điểm từ cổng đào tạo.',login:'Đăng nhập',register:'Đăng ký',loginTitle:'Chào mừng bạn quay lại',registerTitle:'Tạo tài khoản Sổ học tập',email:'Email',password:'Mật khẩu Sổ học tập',name:'Tên hiển thị',confirmPassword:'Xác nhận mật khẩu',passwordHint:'Dùng cụm mật khẩu từ 6 đến 128 ký tự.',resend:'Gửi lại email xác thực',sendEmail:'Gửi email',verifyTitle:'Xác thực email của bạn',verifyDescription:'Xác nhận để hoàn tất đăng ký. Nếu dùng thiết bị khác, bạn sẽ được yêu cầu đặt mật khẩu để bảo vệ tài khoản.',verify:'Xác nhận email',changePassword:'Đổi mật khẩu',changeHint:'Tài khoản có mật khẩu tạm cần đổi mật khẩu trước khi sử dụng.',currentPassword:'Mật khẩu hiện tại',newPassword:'Mật khẩu mới',savePassword:'Lưu mật khẩu',workspace:'Sổ học tập',admin:'Quản trị',logout:'Đăng xuất hệ thống',adminTitle:'Quản lý tài khoản',searchUsers:'Tìm email hoặc tên',search:'Tìm kiếm',previous:'Trước',next:'Tiếp',adminRole:'Quản trị viên',studentRole:'Người dùng',active:'Hoạt động',disabled:'Đã khóa',disable:'Khóa',enable:'Mở khóa',role:'Vai trò',status:'Trạng thái',actions:'Thao tác',confirmChange:'Xác nhận thay đổi tài khoản này?',pending:'Chờ xác thực',accepted:'Nếu email hợp lệ, thư xác thực sẽ được gửi. Hãy kiểm tra hộp thư; liên kết có hiệu lực 30 phút.',verified:'Đã xác thực email. Bạn có thể đăng nhập.',changed:'Đã đổi mật khẩu.',mismatch:'Hai mật khẩu chưa khớp.',loading:'Đang xử lý…',invalid_login:'Email hoặc mật khẩu chưa đúng.',email_not_verified:'Bạn cần xác thực email trước khi đăng nhập.',account_disabled:'Tài khoản đã bị khóa hoặc chưa được phép sử dụng.',weak_password:'Mật khẩu cần đủ 6–128 ký tự và không quá phổ biến.',invalid_email:'Địa chỉ email chưa hợp lệ.',invalid_display_name:'Tên hiển thị cần từ 1 đến 100 ký tự.',verification_invalid:'Liên kết không hợp lệ, đã dùng hoặc hết hạn. Vui lòng gửi lại email xác thực.',verification_password_required:'Hãy đặt mật khẩu để hoàn tất xác thực trên thiết bị này.',rate_limited:'Bạn thao tác quá nhiều lần. Vui lòng chờ rồi thử lại.',session_expired:'Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.',csrf_rejected:'Phiên bảo vệ đã thay đổi. Tải lại trang rồi thử lại.',forbidden:'Tài khoản của bạn không có quyền thực hiện thao tác này.',last_admin:'Cần giữ ít nhất một quản trị viên hoạt động.',cannot_disable_self:'Bạn không thể tự khóa hoặc hạ quyền tài khoản đang dùng.',storage_unavailable:'Chưa kết nối được hệ thống tài khoản. Vui lòng thử lại sau.',invalid_auth_request:'Thông tin gửi lên chưa hợp lệ.',fallback:'Thao tác chưa thành công. Vui lòng thử lại.'},
    en: {eyebrow:'Your study workspace',headline:'A home for your academic journey.',description:'Sign in to manage your profile. Connect VNU when you want to retrieve your transcript from the student portal.',login:'Sign in',register:'Create account',loginTitle:'Welcome back',registerTitle:'Create your study account',email:'Email',password:'Study account password',name:'Display name',confirmPassword:'Confirm password',passwordHint:'Use a passphrase of 6–128 characters.',resend:'Resend verification email',sendEmail:'Send email',verifyTitle:'Verify your email',verifyDescription:'Confirm to finish registration. On another device, you will be asked to set a password to protect your account.',verify:'Verify email',changePassword:'Change password',changeHint:'Accounts with a temporary password must change it before continuing.',currentPassword:'Current password',newPassword:'New password',savePassword:'Save password',workspace:'Workspace',admin:'Admin',logout:'Sign out',adminTitle:'Account management',searchUsers:'Search email or name',search:'Search',previous:'Previous',next:'Next',adminRole:'Administrator',studentRole:'User',active:'Active',disabled:'Disabled',disable:'Disable',enable:'Enable',role:'Role',status:'Status',actions:'Actions',confirmChange:'Confirm this account change?',pending:'Pending verification',accepted:'If the email is eligible, a verification message will be sent. Check your inbox; the link expires in 30 minutes.',verified:'Email verified. You can now sign in.',changed:'Password changed.',mismatch:'The passwords do not match.',loading:'Processing…',invalid_login:'The email or password is incorrect.',email_not_verified:'Verify your email before signing in.',account_disabled:'This account is disabled or unavailable.',weak_password:'Use 6–128 characters and avoid common passwords.',invalid_email:'Enter a valid email address.',invalid_display_name:'Display name must contain 1–100 characters.',verification_invalid:'This link is invalid, used or expired. Request another verification email.',verification_password_required:'Set a password to finish verification on this device.',rate_limited:'Too many attempts. Please wait and try again.',session_expired:'Your session expired. Please sign in again.',csrf_rejected:'Your security session changed. Reload and try again.',forbidden:'You do not have permission for this action.',last_admin:'At least one active administrator is required.',cannot_disable_self:'You cannot disable or demote your current account.',storage_unavailable:'Account storage is unavailable. Please try again later.',invalid_auth_request:'The submitted information is invalid.',fallback:'The action could not be completed. Please try again.'}
  };
  let restoringSession = true;
  let account = null, csrfToken = '', mode = 'student', busy = false, epoch = 0, noticeKey = '', noticeError = false, adminPage = 1, adminTotal = 0, adminRows = [];
  Object.assign(copy.vi, {
    restoringSession:'Đang khôi phục phiên đăng nhập…', eyebrow:'Không gian học tập của sinh viên VNU', headline:'Mỗi học kỳ,\nmột bước tiến rõ ràng.', description:'Bảng điểm và thông tin học tập của bạn, gọn trong một không gian. Theo dõi hành trình và chủ động lên kế hoạch cho kỳ tiếp theo.',
    featureTranscript:'Bảng điểm theo học kỳ', featurePlans:'Kế hoạch học tập cá nhân', visualKicker:'MINH HỌA GIAO DIỆN', visualTitle:'Hồ sơ học tập của bạn', visualFoot:'Thông tin được sắp xếp theo từng học kỳ',
    authKicker:'ĐĂNG NHẬP AN TOÀN', authWelcome:'Chào mừng bạn', authTypePrompt:'Chọn loại tài khoản để tiếp tục vào không gian học tập.', authFooter:'ĐHKHTN · Đại học Quốc gia Hà Nội', showPassword:'Hiện mật khẩu', hidePassword:'Ẩn mật khẩu',
    vnuUsernamePlaceholder:'Nhập tài khoản VNU', adminUsernamePlaceholder:'Nhập tài khoản quản trị', passwordPlaceholder:'Nhập mật khẩu',
    studentTab:'Sinh viên VNU', adminTab:'Quản trị viên', studentTitle:'Đăng nhập bằng VNU',
    studentHint:'Nhập tài khoản bạn dùng tại cổng đào tạo VNU. Hồ sơ được tạo tự động sau khi xác thực thành công.',
    vnuUsername:'Tài khoản VNU', vnuPassword:'Mật khẩu VNU', vnuLogin:'Đăng nhập bằng VNU',
    privacyHint:'Mật khẩu VNU chỉ dùng cho lần xác thực này và không được lưu. Quá trình có thể mất đến 2 phút.',
    loginTitle:'Đăng nhập quản trị', adminUsername:'Tài khoản quản trị', password:'Mật khẩu quản trị', studentRole:'Sinh viên',
    email:'Tài khoản', searchUsers:'Tìm tài khoản VNU, email hoặc tên',
    identity_unverified:'Tài khoản, mật khẩu VNU chưa đúng hoặc chưa xác minh được danh tính. Vui lòng kiểm tra lại.',
    interaction_required:'VNU yêu cầu CAPTCHA hoặc mã xác thực. Ứng dụng chưa hỗ trợ bước này.',
    network_access_denied:'Máy chủ đang bị chặn truy cập VNU. Vui lòng liên hệ quản trị viên kiểm tra quyền truy cập mạng.',
    portal_unavailable:'Chưa kết nối được VNU. Vui lòng thử lại sau.', timeout:'Kết nối VNU quá thời gian chờ. Vui lòng thử lại.',
    browser_unavailable:'Chưa khởi động được kết nối VNU. Vui lòng thử lại sau.', busy:'Đang có nhiều lượt kết nối. Vui lòng thử lại sau.',
    worker_failed:'Kết nối VNU gặp lỗi xử lý. Vui lòng thử lại.', worker_output_invalid:'Chưa xác minh được phản hồi VNU. Vui lòng thử lại.',
    invalid_credentials:'Vui lòng nhập tài khoản và mật khẩu VNU hợp lệ.', invalid_login:'Tài khoản hoặc mật khẩu quản trị chưa đúng.',
    vnu_already_linked:'Danh tính VNU đang có liên kết khác. Vui lòng liên hệ quản trị viên.',
    admin_credentials_required:'Tài khoản này chưa có thông tin đăng nhập quản trị riêng.', use_vnu_password:'Mật khẩu VNU được quản lý tại VNU.'
  });
  Object.assign(copy.en, {
    eyebrow:'A study space for VNU students', headline:'Every semester,\na clearer next step.', description:'Your transcript and study information, together in one place. Follow your progress and plan ahead for the next semester.',
    featureTranscript:'Transcript by semester', featurePlans:'Personal study plans', visualKicker:'INTERFACE PREVIEW', visualTitle:'Your study profile', visualFoot:'Information organized by semester',
    authKicker:'SECURE SIGN IN', authWelcome:'Welcome', authTypePrompt:'Choose an account type to continue to your study space.', authFooter:'VNU University of Science · Vietnam National University', showPassword:'Show password', hidePassword:'Hide password',
    vnuUsernamePlaceholder:'Enter your VNU account', adminUsernamePlaceholder:'Enter your administrator account', passwordPlaceholder:'Enter your password',
    studentTab:'VNU student', adminTab:'Administrator', studentTitle:'Sign in with VNU',
    studentHint:'Use your VNU student portal credentials. Your profile is created after successful verification.',
    vnuUsername:'VNU account', vnuPassword:'VNU password', vnuLogin:'Sign in with VNU',
    privacyHint:'Your VNU password is used only for this verification and is never saved. This can take up to 2 minutes.',
    loginTitle:'Administrator sign-in', adminUsername:'Administrator account', password:'Administrator password', studentRole:'Student',
    email:'Account', searchUsers:'Search VNU account, email or name',
    identity_unverified:'The VNU credentials are incorrect or identity could not be verified. Please check and try again.',
    interaction_required:'VNU requires a CAPTCHA or verification code. This step is not supported yet.',
    network_access_denied:'The server is blocked from accessing VNU. Contact the administrator to check network permissions.',
    portal_unavailable:'VNU is unavailable. Please try again later.', timeout:'The VNU connection timed out. Please try again.',
    browser_unavailable:'The VNU connection could not start. Please try again later.', busy:'Connections are busy. Please try again later.',
    worker_failed:'The VNU connection could not be processed. Please try again.', worker_output_invalid:'The VNU response could not be verified. Please try again.',
    invalid_credentials:'Enter valid VNU credentials.', invalid_login:'The administrator account or password is incorrect.',
    vnu_already_linked:'This VNU identity has a conflicting account link. Please contact an administrator.',
    admin_credentials_required:'This account does not have separate administrator credentials.', use_vnu_password:'Your VNU password is managed by VNU.'
  });
  copy.en.restoringSession = 'Restoring your session…';
  const t = key => copy[window.workspaceI18n.language === 'en' ? 'en' : 'vi'][key] || copy.vi[key] || copy.vi.fallback;
  function notice(key = '', error = false) { noticeKey = key; noticeError = error; $('auth-notice').textContent = key ? t(key) : ''; $('auth-notice').classList.toggle('is-error', error); }
  function clearSecrets() {
    document.querySelectorAll('#system-auth input[type=password], #system-auth input[data-secret]').forEach(input => {
      input.value = '';
      if (input.hasAttribute('data-secret')) input.type = 'password';
    });
    document.querySelectorAll('#system-auth [data-reveal-target]').forEach(button => {
      button.setAttribute('aria-label', t('showPassword'));
      button.title = t('showPassword');
    });
  }
  function emit() { document.dispatchEvent(new CustomEvent('workspace:account-change', {detail: account})); }
  function expire(reason = '') { restoringSession = false; epoch++; account = null; csrfToken = ''; adminRows = []; adminTotal = 0; mode = 'student'; clearSecrets(); $('admin-users').replaceChildren(); notice(reason, Boolean(reason)); render(); emit(); }
  function lock(value) { busy = value; document.querySelectorAll('#system-auth button, #system-logout').forEach(node => { node.disabled = value; }); }
  async function request(path, method = 'GET', body) {
    const current = epoch;
    const response = await fetch(path, {method, credentials:'same-origin', cache:'no-store', headers:{...(body ? {'Content-Type':'application/json'} : {}), ...(method !== 'GET' && csrfToken ? {'X-CSRF-Token':csrfToken} : {})}, body:body ? JSON.stringify(body) : undefined});
    const result = await response.json();
    if (!response.ok) { if (current === epoch && response.status === 401 && !['/auth/login','/auth/vnu','/me/password'].includes(path)) expire('session_expired'); throw new Error(result.detail || 'fallback'); }
    return result;
  }
  async function refresh() {
    const current = epoch, result = await request('/auth/session');
    if (current !== epoch) return;
    restoringSession = false;
    if (!result.authenticated) { if (account) expire('session_expired'); else { account = null; csrfToken = ''; render(); } }
    else { if(account && account.session_id !== result.account.session_id) epoch++; account = result.account; csrfToken = result.csrf_token; mode = account.must_change_password ? 'password' : ['password','admin'].includes(mode) ? mode : 'workspace'; if (mode === 'admin' && account.role !== 'admin') mode = 'workspace'; render(); emit(); }
    return account;
  }
  function render() {
    document.querySelectorAll('[data-auth-copy]').forEach(node => { node.textContent = t(node.dataset.authCopy); });
    document.querySelectorAll('[data-auth-placeholder]').forEach(node => { node.placeholder = t(node.dataset.authPlaceholder); });
    document.querySelectorAll('[data-reveal-target]').forEach(button => {
      const input = $(button.dataset.revealTarget), key = input?.type === 'text' ? 'hidePassword' : 'showPassword';
      button.setAttribute('aria-label', t(key)); button.title = t(key);
    });
    $('system-session-loading').setAttribute('aria-busy', String(restoringSession));
    document.body.dataset.authState = restoringSession ? 'loading' : mode === 'admin' && account ? 'admin' : mode === 'workspace' && account ? 'workspace' : 'auth';
    $('system-account').hidden = !account; $('system-account-name').textContent = account ? (account.vnu_subject || account.email || account.display_name) + ' · ' + t(account.role === 'admin' ? 'adminRole':'studentRole') : '';
    $('system-admin-open').hidden = !account || account.role !== 'admin' || account.must_change_password;
    $('system-password').hidden = !account || account.role !== 'admin' || account.must_change_password;
    $('system-home').hidden = !account || account.must_change_password;
    $('system-admin').hidden = mode !== 'admin' || !account || account.role !== 'admin';
    for (const key of ['student','login','password']) $(`auth-${key}-form`).hidden = mode !== key;
    $('auth-login-tab').hidden = Boolean(account); $('auth-student-tab').hidden = Boolean(account);
    $('auth-login-tab').setAttribute('aria-pressed', String(mode === 'login')); $('auth-student-tab').setAttribute('aria-pressed', String(mode === 'student'));
    notice(noticeKey, noticeError);
    if (mode === 'admin') renderAdmin();
  }
  function switchMode(value) { mode = value; clearSecrets(); notice(); render(); }
  async function submit(form, action) {
    if (busy) return;
    const current = epoch; lock(true); notice('loading');
    try { await action(current); }
    catch (error) { if (current === epoch) { notice(error.message, true);  } }
    finally { clearSecrets(); lock(false); }
  }
  $('auth-login-tab').onclick = () => switchMode('login');
  $('auth-student-tab').onclick = () => switchMode('student');
  document.querySelectorAll('[data-reveal-target]').forEach(button => { button.onclick = () => {
    const input = $(button.dataset.revealTarget); if (!input || busy) return;
    input.type = input.type === 'password' ? 'text' : 'password';
    button.setAttribute('aria-label', t(input.type === 'text' ? 'hidePassword' : 'showPassword'));
    button.title = t(input.type === 'text' ? 'hidePassword' : 'showPassword');
  }; });
  $('auth-login-form').onsubmit = event => { event.preventDefault(); submit(event.target, async current => {
    const body = {username:$('auth-login-email').value,password:$('auth-login-password').value}; clearSecrets();
    try { await request('/auth/login','POST',body); if (current === epoch) { notice(); mode='admin'; await refresh(); if (account?.role==='admin' && !account.must_change_password) await loadAdmin(); } } finally { body.password=''; }
  }); };
  $('auth-student-form').onsubmit = event => { event.preventDefault(); submit(event.target, async current => {
    const body = {username:$('auth-vnu-username').value,password:$('auth-vnu-password').value}; clearSecrets();
    try { const result=await request('/auth/vnu','POST',body); if (current===epoch) { mode='workspace'; await refresh(); if (result.warning) window.workspaceNavigate?.('portal-dialog'); document.dispatchEvent(new CustomEvent('workspace:vnu-login',{detail:{warning:result.warning}})); } } finally { body.password=''; }
  }); };
  $('auth-password-form').onsubmit = event => { event.preventDefault(); submit(event.target, async current => {
    if($('auth-new-password').value!==$('auth-new-confirm').value) throw new Error('mismatch'); const body={current_password:$('auth-current-password').value,new_password:$('auth-new-password').value}; clearSecrets();
    try { await request('/me/password','POST',body); if(current===epoch) { mode='workspace'; notice('changed'); await refresh(); } } finally { body.current_password=''; body.new_password=''; }
  }); };
  $('system-logout').onclick = async () => { if(busy) return; const pending = request('/auth/logout','POST'); expire(); lock(true); try { await pending; } catch(error) { notice(error.message,true); } finally { lock(false); } };
  $('system-home').onclick = $('admin-back').onclick = () => { mode='workspace'; render(); };
  $('system-password').onclick = () => { mode='password'; notice(); render(); };
  async function loadAdmin() { const current=epoch; try { const result=await request(`/admin/users?page=${adminPage}&q=${encodeURIComponent($('admin-query').value)}`); if(current!==epoch || account?.role!=='admin') return; adminRows=result.items; adminTotal=result.total; renderAdmin(); } catch(error) { if(current===epoch) $('admin-notice').textContent=t(error.message); } }
  function renderAdmin() {
    const table=$('admin-users'); table.replaceChildren(); const head=table.createTHead().insertRow(); [t('email'),t('name'),t('role'),t('status'),t('actions')].forEach(label=>{const th=document.createElement('th');th.scope='col';th.textContent=label;head.append(th);}); const body=table.createTBody();
    adminRows.forEach(user=>{const row=body.insertRow();row.insertCell().textContent=user.vnu_subject || user.email || '';row.insertCell().textContent=user.display_name;
      const select=document.createElement('select'); select.setAttribute('aria-label',t('role')+' '+(user.vnu_subject || user.email || '')); for(const role of ['student','admin']) select.add(new Option(t(role==='admin'?'adminRole':'studentRole'),role));select.value=user.role;select.disabled=user.id===account.account_id || (user.role==='student' && !user.email_verified_at); row.insertCell().append(select);
      row.insertCell().textContent=!user.is_active?t('disabled'):!user.email_verified_at && !user.vnu_subject?t('pending'):t('active'); const button=document.createElement('button');button.className='portal-button';button.textContent=t(user.is_active?'disable':'enable');button.disabled=user.id===account.account_id; row.insertCell().append(button);
      const update=async changes=>{if(!confirm(t('confirmChange'))) {renderAdmin();return;} try {await request('/admin/users/'+encodeURIComponent(user.id),'PATCH',changes);await loadAdmin();} catch(error){$('admin-notice').textContent=t(error.message);renderAdmin();}};select.onchange=()=>update({role:select.value});button.onclick=()=>update({is_active:!user.is_active});
    }); $('admin-total').textContent=`${adminTotal} · ${adminPage}`; $('admin-prev').disabled=adminPage<=1;$('admin-next').disabled=adminPage*25>=adminTotal;
  }
  $('system-admin-open').onclick=()=>{mode='admin';adminPage=1;render();loadAdmin();}; $('admin-search-form').onsubmit=event=>{event.preventDefault();adminPage=1;loadAdmin();};$('admin-prev').onclick=()=>{adminPage--;loadAdmin();};$('admin-next').onclick=()=>{adminPage++;loadAdmin();};
  document.addEventListener('workspace:language-change',render);
  document.addEventListener('visibilitychange',()=>{if(!document.hidden && account && !busy) refresh().catch(error=>notice(error.message,true));});
  window.systemAuth={get account(){return account;},get csrf(){return csrfToken;},request,refresh,expire};
  render(); window.systemAuth.ready=refresh().catch(error=>{restoringSession=false;notice(error.message,true);render();});
})();
