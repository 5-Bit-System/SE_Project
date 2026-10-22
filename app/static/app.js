// ==========================================================================
// AI-07 Explainable Course Recommender — Web Client Logic
// ==========================================================================

const state = {
  courseLanguage: "vi",
  programs: [],
  profiles: [],
  currentProgramId: null,
  currentProfileId: null,
  selectedTrackId: null,
  selectedGraduationPathId: null,
  currentCatalog: null,
  courses: [],
  transcript: new Map(), // code -> { passed: bool, grade: float|null }
  eligibleCourses: [],
  blockedCourses: [],
  chatHistory: [],
  recommendationRequestId: 0,
  programRequestId: 0,
  studentRequestId: 0,
  chatRequestId: 0,
};

// --- DOM References ---
const dom = {
  courseLanguageSelect: document.querySelector("#course-language-select"),
  programSelect: document.querySelector("#program-select"),
  profileSelect: document.querySelector("#profile-select"),
  trackSelect: document.querySelector("#track-select"),
  graduationPathSelect: document.querySelector("#graduation-path-select"),
  catalogNameText: document.querySelector("#catalog-name-text"),
  
  // KPI Elements
  kpiPassedCount: document.querySelector("#kpi-passed-count"),
  kpiCredits: document.querySelector("#kpi-credits"),
  kpiTotalCreditsSub: document.querySelector("#kpi-total-credits-sub"),
  kpiGpa: document.querySelector("#kpi-gpa"),
  kpiEligibleCount: document.querySelector("#kpi-eligible-count"),
  
  // Tab 1 Elements
  courseChecklistContainer: document.querySelector("#course-checklist-container"),
  courseSearchInput: document.querySelector("#course-search-input"),
  courseBlockFilter: document.querySelector("#course-block-filter"),
  btnClearTranscript: document.querySelector("#btn-clear-transcript"),
  btnSampleFreshman: document.querySelector("#btn-sample-freshman"),
  btnSampleSophomore: document.querySelector("#btn-sample-sophomore"),
  btnSampleJunior: document.querySelector("#btn-sample-junior"),
  // Tab 2 Elements
  rulesEligibleList: document.querySelector("#rules-eligible-list"),
  rulesBlockedList: document.querySelector("#rules-blocked-list"),
  rulesStatEligible: document.querySelector("#rules-stat-eligible"),
  rulesStatBlocked: document.querySelector("#rules-stat-blocked"),
  rulesStatCompleted: document.querySelector("#rules-stat-completed"),
  
  // Recommendation tab
  recommendForm: document.querySelector("#recommend-form"),
  recGoal: document.querySelector("#rec-goal"),
  recCredits: document.querySelector("#rec-credits"),
  creditsValDisplay: document.querySelector("#credits-val-display"),
  recLimit: document.querySelector("#rec-limit"),
  limitValDisplay: document.querySelector("#limit-val-display"),
  whatIfTopicWeight: document.querySelector("#whatif-topic-weight"),
  whatIfKeywordWeight: document.querySelector("#whatif-keyword-weight"),
  whatIfTypeWeight: document.querySelector("#whatif-type-weight"),
  whatIfTopicValue: document.querySelector("#whatif-topic-value"),
  whatIfKeywordValue: document.querySelector("#whatif-keyword-value"),
  whatIfTypeValue: document.querySelector("#whatif-type-value"),
  btnRunWhatIf: document.querySelector("#btn-run-what-if"),
  recommendationsResultContainer: document.querySelector("#recommendations-result-container"),
  recBadgeCount: document.querySelector("#rec-badge-count"),
  recommendationSummary: document.querySelector("#recommendation-summary"),
  
  // Floating AI Advisor Widget Elements
  floatingAdvisorWidget: document.querySelector("#floating-advisor-widget"),
  advisorBubbleBtn: document.querySelector("#advisor-bubble-btn"),
  advisorChatWindow: document.querySelector("#advisor-chat-window"),
  btnMaximizeChat: document.querySelector("#btn-maximize-chat"),
  btnCloseChat: document.querySelector("#btn-close-chat"),
  chatMessagesContainer: document.querySelector("#chat-messages-container"),
  advisorChatForm: document.querySelector("#advisor-chat-form"),
  advisorInputText: document.querySelector("#advisor-input-text"),
  btnSendChat: document.querySelector("#btn-send-chat"),

};

// --- API Helper ---
async function api(path, options = {}) {
  let response;
  try {
    response = await fetch(path, options);
  } catch (error) {
    throw new Error("Không thể kết nối tới máy chủ. Hãy kiểm tra backend rồi thử lại.");
  }

  const responseText = await response.text();
  let data = null;
  if (responseText) {
    try {
      data = JSON.parse(responseText);
    } catch (error) {
      data = null;
    }
  }
  if (!response.ok) {
    const detail = data?.detail;
    const message = Array.isArray(detail)
      ? detail.map(item => item?.msg || item?.message || String(item)).join("; ")
      : data?.message || detail || `API trả về lỗi HTTP ${response.status}.`;
    throw new Error(message);
  }
  if (data === null) {
    throw new Error("API trả về dữ liệu không hợp lệ.");
  }
  return data;
}

// --- Tab Navigation ---
function initTabs() {
  const tabButtons = document.querySelectorAll(".tab-btn");
  const tabPanels = document.querySelectorAll(".tab-panel");

  tabButtons.forEach(btn => {
    btn.addEventListener("click", () => {
      const targetId = btn.getAttribute("data-tab");
      
      tabButtons.forEach(b => {
        b.classList.remove("active");
        b.setAttribute("aria-selected", "false");
        b.tabIndex = -1;
      });
      tabPanels.forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      btn.tabIndex = 0;
      document.querySelector(`#${targetId}`).classList.add("active");
    });
    btn.addEventListener("keydown", (event) => {
      const buttons = Array.from(tabButtons);
      const index = buttons.indexOf(btn);
      let next;
      if (["ArrowDown", "ArrowRight"].includes(event.key)) next = (index + 1) % buttons.length;
      if (["ArrowUp", "ArrowLeft"].includes(event.key)) next = (index - 1 + buttons.length) % buttons.length;
      if (event.key === "Home") next = 0;
      if (event.key === "End") next = buttons.length - 1;
      if (next === undefined) return;
      event.preventDefault();
      buttons[next].focus();
      buttons[next].click();
    });
  });
}

// --- Major / Program Loading & Isolation ---
async function loadPrograms() {
  try {
    state.programs = await api("/programs");
    dom.programSelect.replaceChildren();

    state.programs.forEach(prog => {
      const option = document.createElement("option");
      option.value = prog.program_id;
      option.textContent = prog.name;
      dom.programSelect.appendChild(option);
    });

    if (state.programs.length > 0) {
      dom.programSelect.value = state.programs[0].program_id;
      await onProgramChanged();
    }
  } catch (error) {
    console.error("Lỗi nạp danh sách ngành:", error);
    dom.catalogNameText.textContent = "Lỗi nạp chương trình: " + error.message;
  }
}

async function onProgramChanged() {
  const progId = dom.programSelect.value;
  const requestId = ++state.programRequestId;
  state.studentRequestId += 1;
  state.currentProgramId = progId;

  // RÀNG BUỘC MAJOR ISOLATION: Xóa sạch dữ liệu môn đã chọn khi đổi ngành
  state.transcript.clear();
  state.courses = [];
  state.profiles = [];
  state.eligibleCourses = [];
  state.blockedCourses = [];
  state.chatHistory = [];
  state.chatRequestId += 1;
  dom.chatMessagesContainer.replaceChildren();
  dom.btnSendChat.disabled = false;
  state.currentProfileId = null;
  state.selectedTrackId = null;
  state.selectedGraduationPathId = null;
  dom.profileSelect.value = "";
  dom.kpiPassedCount.textContent = "0";
  dom.kpiCredits.textContent = "0";
  dom.kpiGpa.textContent = "--";
  dom.kpiEligibleCount.textContent = "0";
  renderCourseChecklist();
  clearRecommendationResults("Đã đổi ngành. Hãy chạy lại đề xuất theo catalog mới.");

  const currentProgram = state.programs.find(p => p.program_id === progId);
  if (currentProgram) {
    const status = currentProgram.catalog_status || "unknown";
    const warning = status === "verified" ? "" : " · Nguồn CTĐT chưa được xác minh đầy đủ";
    const statusLabel = {verified: "Đã xác minh", draft_unverified: "Đang rà soát", unknown: "Chưa rõ trạng thái"}[status] || "Chưa rõ trạng thái";
    dom.catalogNameText.textContent = `${currentProgram.name} · ${currentProgram.total_credits} tín chỉ · ${statusLabel}${warning}`;
    dom.kpiTotalCreditsSub.textContent = `/ ${currentProgram.total_credits} Tín chỉ`;
    renderProgramChoices(currentProgram);
  }

  try {
    const courses = await api(`/courses?program_id=${encodeURIComponent(progId)}`);
    if (requestId !== state.programRequestId) return;
    state.courses = courses;
    renderCourseChecklist();
    await loadProfilesForProgram(progId, requestId);
  } catch (error) {
    if (requestId !== state.programRequestId) return;
    console.error("Lỗi nạp môn học:", error);
    const errorState = document.createElement("div");
    errorState.className = "empty-state text-rose";
    errorState.textContent = `Không thể nạp dữ liệu môn học: ${error.message}`;
    dom.courseChecklistContainer.replaceChildren(errorState);
  }
}

function renderProgramChoices(program) {
  const tracks = program?.track_selection?.tracks || [];
  const paths = program?.graduation_selection?.paths || [];

  if (dom.trackSelect) {
    dom.trackSelect.replaceChildren();
    const empty = document.createElement("option");
    empty.value = "";
    empty.textContent = tracks.length ? "Chưa chọn nhánh" : "Ngành này không chia nhánh";
    dom.trackSelect.appendChild(empty);
    tracks.forEach(track => {
      const option = document.createElement("option");
      option.value = track.id;
      option.textContent = track.name;
      dom.trackSelect.appendChild(option);
    });
    dom.trackSelect.disabled = tracks.length === 0;
  }

  if (dom.graduationPathSelect) {
    dom.graduationPathSelect.replaceChildren();
    const empty = document.createElement("option");
    empty.value = "";
    empty.textContent = paths.length ? "Chưa chọn hướng" : "Chưa có dữ liệu hướng tốt nghiệp";
    dom.graduationPathSelect.appendChild(empty);
    paths.forEach(path => {
      const option = document.createElement("option");
      option.value = path.id;
      option.textContent = path.name;
      dom.graduationPathSelect.appendChild(option);
    });
    dom.graduationPathSelect.disabled = paths.length === 0;
  }
}

async function loadProfilesForProgram(programId, requestId = state.programRequestId) {
  if (!dom.profileSelect) {
    await updateStudentState();
    return;
  }

  try {
    const profiles = await api(`/profiles?program_id=${encodeURIComponent(programId)}`);
    if (requestId !== state.programRequestId) return;
    state.profiles = profiles;
    dom.profileSelect.replaceChildren();

    const emptyOption = document.createElement("option");
    emptyOption.value = "";
    emptyOption.textContent = state.profiles.length ? "Không dùng profile demo" : "Chưa có profile demo · nhập bảng điểm thủ công";
    dom.profileSelect.appendChild(emptyOption);

    state.profiles.forEach(profile => {
      const option = document.createElement("option");
      option.value = profile.profile_id;
      option.textContent = `${profile.label} · ${profile.record_count} môn`;
      dom.profileSelect.appendChild(option);
    });

    if (state.profiles.length > 0) {
      dom.profileSelect.value = state.profiles[0].profile_id;
      await loadSelectedProfile();
    } else {
      await updateStudentState();
    }
  } catch (error) {
    if (requestId !== state.programRequestId) return;
    console.error("Lỗi nạp profile demo:", error);
    dom.profileSelect.replaceChildren();
    const option = document.createElement("option");
    option.value = "";
    option.textContent = "Không nạp được profile demo";
    dom.profileSelect.appendChild(option);
    await updateStudentState();
  }
}

async function loadSelectedProfile() {
  const profileId = dom.profileSelect?.value;
  const programId = state.currentProgramId;
  const requestId = state.programRequestId;
  state.transcript.clear();
  state.chatHistory = [];
  state.currentProfileId = profileId || null;
  state.selectedTrackId = null;
  if (dom.trackSelect) dom.trackSelect.value = "";
  clearRecommendationResults("Hồ sơ học tập đã thay đổi. Hãy chạy lại đề xuất.");

  if (!profileId) {
    renderCourseChecklist();
    await updateStudentState();
    return;
  }

  try {
    const profile = await api(`/profiles/${encodeURIComponent(profileId)}`);
    if (requestId !== state.programRequestId || profileId !== dom.profileSelect?.value) return;
    if (profile.program_id !== programId) {
      throw new Error("Profile không thuộc ngành đang chọn.");
    }

    // Nếu profile có định hướng trùng tên một nhánh, dùng làm giá trị mặc định.
    if (dom.trackSelect && profile.target_track) {
      const matchingTrack = [...dom.trackSelect.options].find(
        option => option.textContent === profile.target_track,
      );
      if (matchingTrack) {
        dom.trackSelect.value = matchingTrack.value;
        state.selectedTrackId = matchingTrack.value;
      }
    }

    profile.records.forEach(record => {
      state.transcript.set(record.course_code, {
        passed: record.passed,
        grade: record.grade,
      });
    });

    renderCourseChecklist();
    await updateStudentState();
  } catch (error) {
    if (requestId !== state.programRequestId) return;
    console.error("Lỗi nạp profile:", error);
    state.currentProfileId = null;
    dom.profileSelect.value = "";
    renderCourseChecklist();
    await updateStudentState();
  }
}

function clearProfileSelection() {
  state.currentProfileId = null;
  if (dom.profileSelect) dom.profileSelect.value = "";
}

// --- Render Course Checklist ---
function localizedCourseName(course) {
  const source = state.courses.find(item => item.code === course.code) || course;
  return state.courseLanguage === "en" ? source.name_en || source.name : source.name;
}

function setCourseTitle(element, course) {
  element.dataset.courseCode = course.code;
  element.textContent = `${course.code} — ${localizedCourseName(course)}`;
}

dom.courseLanguageSelect.addEventListener("change", () => {
  state.courseLanguage = dom.courseLanguageSelect.value === "en" ? "en" : "vi";
  renderCourseChecklist();
  document.querySelectorAll("[data-course-code]").forEach(element => {
    const course = state.courses.find(item => item.code === element.dataset.courseCode);
    if (course) setCourseTitle(element, course);
  });
});

function renderCourseChecklist() {
  dom.courseChecklistContainer.replaceChildren();
  
  const query = (dom.courseSearchInput.value || "").trim().toLowerCase();
  const blockFilter = dom.courseBlockFilter.value;

  const filtered = state.courses.filter(c => {
    const matchQuery = !query || [c.code, c.name, c.name_en || ""].some(value => value.toLowerCase().includes(query));
    const matchBlock = blockFilter === "all" || c.block === blockFilter;
    return matchQuery && matchBlock;
  });

  if (filtered.length === 0) {
    dom.courseChecklistContainer.innerHTML = `<div class="empty-state"><span class="empty-icon">🔍</span>Không tìm thấy môn học phù hợp.</div>`;
    return;
  }

  filtered.forEach(course => {
    const row = document.createElement("div");
    row.className = "course-item-row";
    row.id = `course-row-${course.code}`;

    const record = state.transcript.get(course.code);
    const isPassed = Boolean(record?.passed);
    if (isPassed) row.classList.add("is-passed");

    // Left check
    const checkLabel = document.createElement("label");
    checkLabel.className = "course-check-label";
    
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.setAttribute("aria-label", `Đã hoàn thành ${course.code}`);
    checkbox.className = "course-checkbox";
    checkbox.checked = isPassed;
    checkbox.addEventListener("change", async (e) => {
      clearRecommendationResults("Bảng điểm đã thay đổi. Hãy chạy lại đề xuất.");
      if (e.target.checked) {
        clearProfileSelection();
        state.transcript.set(course.code, { passed: true, grade: null });
        row.classList.add("is-passed");
      } else {
        state.transcript.delete(course.code);
        row.classList.remove("is-passed");
      }
      await updateStudentState();
    });

    const info = document.createElement("div");
    info.className = "course-info";
    
    const codeName = document.createElement("span");
    codeName.className = "course-code-name";
    setCourseTitle(codeName, course);

    const tags = document.createElement("div");
    tags.className = "course-meta-tags";
    tags.innerHTML = `
      <span class="badge badge-gray">${course.credits} TC</span>
      <span class="badge badge-gray">${course.year ? `Năm ${course.year}` : 'Chưa rõ năm học'}</span>
      <span>${{general: 'Kiến thức chung', field: 'Theo lĩnh vực', discipline: 'Theo khối ngành', group: 'Theo nhóm ngành', major: 'Kiến thức ngành'}[course.block] || 'Chưa rõ khối kiến thức'}</span>
    `;
    if (course.hours) {
      const english = state.courseLanguage === "en";
      const hours = document.createElement("span");
      hours.textContent = `${english ? "Hours (lecture/practice/self-study)" : "Giờ (lý thuyết/thực hành/tự học)"}: ${["lecture", "practice", "self_study"].map(key => course.hours[key] ?? "?").join("/")}`;
      tags.appendChild(hours);
    }

    info.append(codeName, tags);
    checkLabel.append(checkbox, info);

    // Right: Grade Input (optional)
    const gradeBox = document.createElement("div");
    gradeBox.className = "grade-input-box";
    const gradeInput = document.createElement("input");
    gradeInput.type = "number";
    gradeInput.setAttribute("aria-label", `Điểm hệ 10 của ${course.code}`);
    gradeInput.min = "0";
    gradeInput.max = "10";
    gradeInput.step = "0.5";
    gradeInput.className = "modern-input grade-input";
    gradeInput.placeholder = "Điểm";
    
    const rec = state.transcript.get(course.code);
    if (rec && rec.grade !== null && rec.grade !== undefined) {
      gradeInput.value = rec.grade;
    }

    gradeInput.addEventListener("change", async (e) => {
      clearRecommendationResults("Bảng điểm đã thay đổi. Hãy chạy lại đề xuất.");
      const val = parseFloat(e.target.value);
      if (!isNaN(val)) {
        clearProfileSelection();
        checkbox.checked = val >= 5.0;
        state.transcript.set(course.code, { passed: val >= 5.0, grade: val });
        if (val >= 5.0) row.classList.add("is-passed");
        else row.classList.remove("is-passed");
      } else {
        if (checkbox.checked) {
          state.transcript.set(course.code, { passed: true, grade: null });
        }
      }
      await updateStudentState();
    });

    gradeBox.append(gradeInput);
    row.append(checkLabel, gradeBox);
    dom.courseChecklistContainer.appendChild(row);
  });
}

// --- Update Student State: Transcript Summary + Eligibility + Roadmap ---
async function updateStudentState() {
  const requestId = ++state.studentRequestId;
  const programId = state.currentProgramId;
  const records = [];
  for (const [code, item] of state.transcript.entries()) {
    records.push({
      course_code: code,
      passed: item.passed,
      grade: item.grade,
    });
  }

  const passedCodes = records.filter(r => r.passed).map(r => r.course_code);

  try {
    // 1. Transcript Summary
    const summary = await api("/transcript/summary", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        program_id: state.currentProgramId,
        records: records,
        selected_track_id: state.selectedTrackId,
        selected_graduation_path_id: state.selectedGraduationPathId,
      }),
    });
    if (requestId !== state.studentRequestId || programId !== state.currentProgramId) return;

    dom.kpiPassedCount.textContent = summary.passed_courses.length;
    dom.kpiCredits.textContent = summary.earned_credits;
    dom.kpiGpa.textContent = summary.gpa !== null ? summary.gpa.toFixed(2) : "--";

    // 2. Rule Engine Evaluation
    const eligRes = await api("/eligibility", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        program_id: state.currentProgramId,
        passed_course_codes: passedCodes,
        max_credits: 30,
        selected_track_id: state.selectedTrackId,
        selected_graduation_path_id: state.selectedGraduationPathId,
      }),
    });
    if (requestId !== state.studentRequestId || programId !== state.currentProgramId) return;

    state.eligibleCourses = eligRes.eligible_courses;
    state.blockedCourses = eligRes.blocked_courses;
    dom.kpiEligibleCount.textContent = eligRes.total_eligible;

    renderRuleEngineTab(eligRes);

  } catch (error) {
    if (requestId !== state.studentRequestId || programId !== state.currentProgramId) return;
    console.error("Lỗi cập nhật trạng thái học vụ:", error);
    dom.kpiEligibleCount.textContent = "—";
    const errorState = document.createElement("div");
    errorState.className = "empty-state text-rose";
    errorState.textContent = `Không thể cập nhật điều kiện học vụ: ${error.message}`;
    dom.rulesEligibleList.replaceChildren(errorState.cloneNode(true));
    dom.rulesBlockedList.replaceChildren(errorState);
  }
}

// --- Render Rule Engine Tab ---
function renderRuleEngineTab(eligRes) {
  dom.rulesStatEligible.textContent = eligRes.total_eligible;
  dom.rulesStatBlocked.textContent = eligRes.total_blocked;
  dom.rulesStatCompleted.textContent = eligRes.total_completed;

  // Eligible List
  dom.rulesEligibleList.replaceChildren();
  if (eligRes.eligible_courses.length === 0) {
    dom.rulesEligibleList.innerHTML = `<div class="empty-state">Chưa có môn đủ điều kiện. Hãy hoàn thành các môn tiên quyết cơ sở.</div>`;
  } else {
    eligRes.eligible_courses.forEach(c => {
      const card = document.createElement("div");
      card.className = "rule-item-card is-eligible";
      card.innerHTML = `
        <div class="rule-course-header">
          <div>
            <strong>${c.code} — ${c.name}</strong>
            <div class="course-meta-tags mt-2">
              <span class="badge badge-success">${c.credits} TC</span>
              <span class="badge badge-gray">${c.year ? `Năm ${c.year}` : 'Chưa rõ năm học'}</span>
              <span>${c.block}</span>
            </div>
          </div>
          <span class="badge badge-success">✓ Sẵn sàng</span>
        </div>
      `;
      setCourseTitle(card.querySelector("strong"), c);
      dom.rulesEligibleList.appendChild(card);
    });
  }

  // Blocked List
  dom.rulesBlockedList.replaceChildren();
  if (eligRes.blocked_courses.length === 0) {
    dom.rulesBlockedList.innerHTML = `<div class="empty-state">Không có môn nào bị chặn.</div>`;
  } else {
    eligRes.blocked_courses.forEach(b => {
      const card = document.createElement("div");
      card.className = "rule-item-card is-blocked";
      const reasonsHtml = b.reasons.map(r => `<div class="rule-reason-box text-amber">⚠️ ${r.message}</div>`).join("");
      card.innerHTML = `
        <div class="rule-course-header">
          <div>
            <strong>${b.code} — ${b.name}</strong>
            <div class="course-meta-tags mt-2">
              <span class="badge badge-warning">${b.credits} TC</span>
              <span class="badge badge-gray">${b.year ? `Năm ${b.year}` : 'Chưa rõ năm học'}</span>
              <span>${b.block}</span>
            </div>
          </div>
          <span class="badge badge-warning">Bị chặn</span>
        </div>
        ${reasonsHtml}
      `;
      setCourseTitle(card.querySelector("strong"), b);
      dom.rulesBlockedList.appendChild(card);
    });
  }
}

// --- Recommendations Form ---
dom.recCredits.addEventListener("input", (e) => {
  dom.creditsValDisplay.textContent = `${e.target.value} TC`;
});

dom.recLimit.addEventListener("input", (e) => {
  dom.limitValDisplay.textContent = `${e.target.value} môn`;
});

function updateWhatIfWeightLabels() {
  if (dom.whatIfTopicValue) dom.whatIfTopicValue.textContent = `${dom.whatIfTopicWeight.value}%`;
  if (dom.whatIfKeywordValue) dom.whatIfKeywordValue.textContent = `${dom.whatIfKeywordWeight.value}%`;
  if (dom.whatIfTypeValue) dom.whatIfTypeValue.textContent = `${dom.whatIfTypeWeight.value}%`;
}

[dom.whatIfTopicWeight, dom.whatIfKeywordWeight, dom.whatIfTypeWeight]
  .filter(Boolean)
  .forEach(input => input.addEventListener("input", updateWhatIfWeightLabels));
updateWhatIfWeightLabels();

// --- Recommendation metadata renderer (new response contract) ---
const recommendationReasonLabels = {
  missing_prerequisites: "Thiếu môn tiên quyết",
  choice_group_full: "Đã đủ số môn trong nhóm lựa chọn",
  credits_exceeded: "Vượt ngân sách tín chỉ",
  source_conflict: "Xung đột nguồn dữ liệu",
  track_mismatch: "Không thuộc nhánh đã chọn",
  graduation_path_mismatch: "Không thuộc hướng tốt nghiệp đã chọn",
};

function createElement(tag, className = "", text = null) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text !== null && text !== undefined) element.textContent = text;
  return element;
}

function asTextList(value) {
  if (Array.isArray(value)) return value.filter(item => item !== null && item !== undefined).map(String);
  if (value === null || value === undefined || value === "") return [];
  return [String(value)];
}

function formatRecommendationStatus(value) {
  const labels = {
    verified: "Đã xác minh",
    draft_unverified: "Chưa xác minh đầy đủ",
    unknown: "Chưa xác định",
    available: "Có thể mở",
    unavailable: "Chưa mở",
    offering_unknown: "Chưa xác minh mở lớp",
  };
  return labels[value] || value || "Chưa xác định";
}

function formatReasonCode(value) {
  return recommendationReasonLabels[value] || String(value).replaceAll("_", " ");
}

function appendBadgeRow(parent, values, badgeClass = "badge-gray") {
  const row = createElement("div", "rec-badge-row");
  values.forEach(value => row.appendChild(createElement("span", `badge ${badgeClass}`, value)));
  parent.appendChild(row);
}

function appendRecommendationDetail(parent, label, value, options = {}) {
  const detail = createElement("div", `rec-detail ${options.className || ""}`.trim());
  detail.appendChild(createElement("div", "rec-detail-label", label));
  const values = asTextList(value);

  if (options.badges && values.length > 0) {
    appendBadgeRow(detail, values, options.badgeClass || "badge-gray");
  } else if (values.length > 0) {
    const content = createElement("div", "rec-detail-value");
    values.forEach((item, index) => {
      if (index > 0) content.appendChild(document.createElement("br"));
      content.appendChild(document.createTextNode(item));
    });
    detail.appendChild(content);
  } else {
    detail.appendChild(createElement("div", "rec-detail-value rec-detail-muted", options.emptyText || "Chưa có dữ liệu."));
  }
  parent.appendChild(detail);
}

function renderRecommendationSummary(data) {
  if (!dom.recommendationSummary) return;
  dom.recommendationSummary.replaceChildren();
  dom.recommendationSummary.hidden = false;

  const summaryGrid = createElement("div", "rec-summary-grid");
  appendRecommendationDetail(summaryGrid, "Tập môn đủ điều kiện", `${data.eligible_count ?? 0} môn`);
  appendRecommendationDetail(summaryGrid, "Catalog", formatRecommendationStatus(data.catalog_status), {
    badges: true,
    badgeClass: data.catalog_status === "verified" ? "badge-success" : "badge-warning",
  });
  appendRecommendationDetail(summaryGrid, "Bộ xếp hạng", `${data.ranking_backend || "Chưa xác định"} · ${data.ranking_version || "n/a"}`);
  if (data.what_if) {
    appendRecommendationDetail(summaryGrid, "Cháº¿ Ä‘á»™", "What-if trên cùng tập đủ điều kiện", {
      badges: true,
      badgeClass: "badge-info",
    });
  }
  dom.recommendationSummary.appendChild(summaryGrid);

  const blockedSummary = data.blocked_summary && typeof data.blocked_summary === "object"
    ? Object.entries(data.blocked_summary)
    : [];
  const blocked = createElement("div", "rec-blocked-summary");
  blocked.appendChild(createElement("div", "rec-detail-label", "Tóm tắt môn bị chặn"));
  if (blockedSummary.length > 0) {
    appendBadgeRow(blocked, blockedSummary.map(([reason, count]) => `${formatReasonCode(reason)}: ${count}`), "badge-warning");
  } else {
    blocked.appendChild(createElement("div", "rec-detail-value rec-detail-muted", "Không có môn bị chặn."));
  }
  dom.recommendationSummary.appendChild(blocked);
}

function renderRecommendationWarnings(warnings) {
  const items = asTextList(warnings);
  if (items.length === 0) return;
  const panel = createElement("div", "rec-warning-panel");
  panel.appendChild(createElement("strong", "rec-warning-title", "Cảnh báo của hệ thống"));
  const list = createElement("ul", "rec-warning-list");
  items.forEach(item => list.appendChild(createElement("li", "", item)));
  panel.appendChild(list);
  dom.recommendationsResultContainer.appendChild(panel);
}

function createRecommendationCard(rec, index) {
  const card = createElement("article", "recommendation-card");
  const header = createElement("div", "rec-header");
  const titleGroup = createElement("div");
  const rank = Number.isFinite(Number(rec.rank)) ? Number(rec.rank) : index + 1;
  titleGroup.appendChild(createElement("span", "badge badge-info rec-rank", `Hạng #${rank}`));
  const courseTitle = createElement("div", "rec-title");
  setCourseTitle(courseTitle, rec);
  titleGroup.appendChild(courseTitle);
  header.appendChild(titleGroup);
  header.appendChild(createElement("span", "badge badge-success", `${rec.credits ?? 0} Tín chỉ`));
  card.appendChild(header);

  const score = Number(rec.score);
  appendBadgeRow(card, [
    `Điểm phù hợp: ${Number.isFinite(score) ? score.toFixed(2) : "n/a"}`,
    `Nguồn: ${formatRecommendationStatus(rec.source_status)}`,
    `Mở lớp: ${formatRecommendationStatus(rec.offering_status)}`,
  ], "badge-gray");

  const details = createElement("div", "rec-details-grid");
  appendRecommendationDetail(details, "Lý do đủ điều kiện", asTextList(rec.eligibility_reason).map(formatReasonCode), {
    emptyText: "Đã vượt qua kiểm tra eligibility của hệ thống.",
  });
  appendRecommendationDetail(details, "Mức độ phù hợp", rec.fit_reason, {
    emptyText: "Chưa có dữ liệu phù hợp chi tiết.",
  });
  card.appendChild(details);
  card.appendChild(createElement("p", "rec-reason", rec.reason || "Chưa có giải thích tổng hợp."));
  return card;
}

function clearRecommendationResults(message = null) {
  state.recommendationRequestId += 1;
  if (dom.recBadgeCount) dom.recBadgeCount.textContent = "0 Đề xuất";
  if (dom.recommendationSummary) {
    dom.recommendationSummary.replaceChildren();
    dom.recommendationSummary.hidden = true;
  }
  if (!dom.recommendationsResultContainer) return;
  dom.recommendationsResultContainer.replaceChildren(
    createElement("div", "empty-state", message || "Chưa có kết quả đề xuất.")
  );
}

function recommendationPayload(extra = {}) {
  const passedCodes = [...state.transcript.entries()]
    .filter(([_, item]) => item.passed)
    .map(([code]) => code);
  return {
    program_id: state.currentProgramId,
    passed_course_codes: passedCodes,
    goal: dom.recGoal.value.trim(),
    max_credits: parseInt(dom.recCredits.value, 10),
    limit: parseInt(dom.recLimit.value, 10),
    selected_track_id: state.selectedTrackId,
    selected_graduation_path_id: state.selectedGraduationPathId,
    ...extra,
  };
}

function renderRecommendationData(data) {
  const recommendations = Array.isArray(data.recommendations) ? data.recommendations : [];
  dom.recBadgeCount.textContent = `${recommendations.length} Đề xuất`;
  dom.recommendationsResultContainer.replaceChildren();
  renderRecommendationSummary(data);
  renderRecommendationWarnings(data.warnings);
  if (recommendations.length === 0) {
    dom.recommendationsResultContainer.appendChild(
      createElement("div", "empty-state", "Không có môn phù hợp trong giới hạn tín chỉ đã chọn.")
    );
    return;
  }
  recommendations.forEach((rec, index) => {
    dom.recommendationsResultContainer.appendChild(createRecommendationCard(rec, index));
  });
}

async function handleRecommendationSubmit(e) {
  e.preventDefault();
  e.stopImmediatePropagation();
  const requestId = ++state.recommendationRequestId;
  const submitButton = document.querySelector("#btn-run-recommend");
  if (submitButton) submitButton.disabled = true;
  dom.recommendationsResultContainer.replaceChildren(
    createElement("div", "empty-state", "Đang phân tích và xếp hạng...")
  );
  if (dom.recommendationSummary) dom.recommendationSummary.hidden = true;

  try {
    const data = await api("/recommendations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(recommendationPayload()),
    });

    if (requestId !== state.recommendationRequestId) return;
    const recommendations = Array.isArray(data.recommendations) ? data.recommendations : [];
    dom.recBadgeCount.textContent = `${recommendations.length} Đề xuất`;
    dom.recommendationsResultContainer.replaceChildren();
    renderRecommendationSummary(data);
    renderRecommendationWarnings(data.warnings);

    if (recommendations.length === 0) {
      dom.recommendationsResultContainer.appendChild(
        createElement("div", "empty-state", "Không có môn phù hợp trong giới hạn tín chỉ đã chọn.")
      );
      return;
    }
    recommendations.forEach((rec, index) => {
      dom.recommendationsResultContainer.appendChild(createRecommendationCard(rec, index));
    });
  } catch (error) {
    if (requestId !== state.recommendationRequestId) return;
    if (dom.recommendationSummary) dom.recommendationSummary.hidden = true;
    dom.recommendationsResultContainer.replaceChildren(
      createElement("div", "empty-state text-rose", `Lỗi khi lấy đề xuất: ${error.message}`)
    );
    dom.recBadgeCount.textContent = "Lỗi";
  } finally {
    if (requestId === state.recommendationRequestId && submitButton) {
      submitButton.disabled = false;
    }
  }
}

// Dùng capture để xử lý một luồng submit duy nhất trước các listener khác.
dom.recommendForm.addEventListener("submit", handleRecommendationSubmit, true);

async function handleWhatIf() {
  if (!dom.btnRunWhatIf) return;
  const requestId = ++state.recommendationRequestId;
  dom.btnRunWhatIf.disabled = true;
  dom.recommendationsResultContainer.replaceChildren(
    createElement("div", "empty-state", "Đang chạy what-if trên cùng tập môn đủ điều kiện...")
  );
  if (dom.recommendationSummary) dom.recommendationSummary.hidden = true;
  const ranking_weights = {
    topic: Number(dom.whatIfTopicWeight.value) / 100,
    keyword: Number(dom.whatIfKeywordWeight.value) / 100,
    course_type: Number(dom.whatIfTypeWeight.value) / 100,
  };
  if (Object.values(ranking_weights).every(weight => weight <= 0)) {
    dom.recommendationsResultContainer.replaceChildren(
      createElement("div", "empty-state text-rose", "Hãy giữ ít nhất một trọng số lớn hơn 0.")
    );
    dom.btnRunWhatIf.disabled = false;
    return;
  }
  try {
    const data = await api("/recommendations/what-if", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(recommendationPayload({ ranking_weights })),
    });
    if (requestId !== state.recommendationRequestId) return;
    renderRecommendationData(data);
  } catch (error) {
    if (requestId !== state.recommendationRequestId) return;
    dom.recommendationsResultContainer.replaceChildren(
      createElement("div", "empty-state text-rose", `Lỗi what-if: ${error.message}`)
    );
    dom.recBadgeCount.textContent = "Lỗi";
  } finally {
    if (requestId === state.recommendationRequestId) dom.btnRunWhatIf.disabled = false;
  }
}

dom.btnRunWhatIf?.addEventListener("click", handleWhatIf);

// --- Floating AI Advisor Controls & Chat Logic ---
function toggleAdvisorChat(forceOpen = null) {
  if (!dom.advisorChatWindow) return;
  const isHidden = dom.advisorChatWindow.classList.contains("hidden");
  const shouldOpen = forceOpen !== null ? forceOpen : isHidden;
  dom.advisorBubbleBtn?.setAttribute("aria-expanded", String(shouldOpen));

  if (shouldOpen) {
    dom.advisorChatWindow.classList.remove("hidden");
    dom.advisorChatWindow.setAttribute("aria-hidden", "false");
    if (dom.advisorInputText) {
      setTimeout(() => dom.advisorInputText.focus(), 120);
    }
  } else {
    dom.advisorChatWindow.classList.add("hidden");
    dom.advisorChatWindow.setAttribute("aria-hidden", "true");
    dom.advisorBubbleBtn?.focus();
  }
}

function initFloatingAdvisor() {
  if (dom.advisorBubbleBtn) {
    dom.advisorBubbleBtn.addEventListener("click", () => toggleAdvisorChat());
  }
  if (dom.btnCloseChat) {
    dom.btnCloseChat.addEventListener("click", () => toggleAdvisorChat(false));
  }
  if (dom.btnMaximizeChat) {
    dom.btnMaximizeChat.addEventListener("click", () => {
      const isMax = dom.advisorChatWindow.classList.toggle("is-maximized");
      dom.btnMaximizeChat.textContent = isMax ? "🗗" : "⛶";
      dom.btnMaximizeChat.title = isMax ? "Thu nhỏ về 1/4 màn hình" : "Phóng to khung chat";
      dom.btnMaximizeChat.setAttribute("aria-label", isMax ? "Thu nhỏ" : "Phóng to");
    });
  }

  // Phím ESC để thu gọn cửa sổ chat
  window.addEventListener("keydown", (e) => {
    if (e.key === "Escape" && dom.advisorChatWindow && !dom.advisorChatWindow.classList.contains("hidden")) {
      toggleAdvisorChat(false);
    }
  });
}

dom.advisorChatForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const text = dom.advisorInputText.value.trim();
  if (!text) return;
  const requestId = ++state.chatRequestId;

  // Render user message
  appendChatMessage("user", text);
  dom.advisorInputText.value = "";
  dom.btnSendChat.disabled = true;

  // Typing indicator
  const typingEl = appendChatMessage("advisor", "✨ AI Advisor đang suy nghĩ và phân tích dữ liệu CTĐT...");

  const passedCodes = [...state.transcript.entries()]
    .filter(([_, item]) => item.passed)
    .map(([code]) => code);
  const advisorHistory = state.chatHistory.slice(-8);
  state.chatHistory.push({ role: "user", content: text });

  try {
    const data = await api("/advisor/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        program_id: state.currentProgramId,
        message: text,
        passed_course_codes: passedCodes,
        history: advisorHistory,
        selected_track_id: state.selectedTrackId,
        selected_graduation_path_id: state.selectedGraduationPathId,
      }),
    });
    if (requestId !== state.chatRequestId) return;

    typingEl.remove();

    let prefix = "";
    if (data.mode === "guardrail_rejected") {
      prefix = "🛡️ **[Scope Guardrail - Ngoài phạm vi]**\n\n";
    } else if (data.mode === "heuristic_fallback") {
      prefix = "⚙️ **[Heuristic Advisor Mode]**\n\n";
    }

    appendChatMessage("advisor", prefix + data.reply, data.is_guardrail_triggered);
    state.chatHistory.push({ role: "assistant", content: data.reply });

  } catch (error) {
    if (requestId !== state.chatRequestId) return;
    typingEl.remove();
    appendChatMessage("advisor", "⚠️ Lỗi kết nối: " + error.message, true);
  } finally {
    if (requestId === state.chatRequestId) dom.btnSendChat.disabled = false;
  }
});

function appendChatMessage(role, content, isGuardrail = false) {
  const msgEl = document.createElement("div");
  msgEl.className = `chat-message message-${role}`;
  if (isGuardrail) msgEl.classList.add("is-guardrail");

  const bubble = document.createElement("div");
  bubble.className = "message-content";
  bubble.textContent = content;

  msgEl.appendChild(bubble);
  dom.chatMessagesContainer.appendChild(msgEl);
  dom.chatMessagesContainer.scrollTop = dom.chatMessagesContainer.scrollHeight;
  return msgEl;
}

// Prompt Chips
document.querySelectorAll(".chip-btn").forEach(chip => {
  chip.addEventListener("click", () => {
    toggleAdvisorChat(true);
    const p = chip.getAttribute("data-prompt");
    dom.advisorInputText.value = p;
    dom.advisorChatForm.dispatchEvent(new Event("submit"));
  });
});

// --- Sample Profile Helpers ---
dom.btnSampleFreshman.addEventListener("click", async () => {
  // Chọn các môn đầu khóa (Year 1)
  const y1 = state.courses.filter(c => c.year === 1).slice(0, 5);
  clearRecommendationResults("Bảng điểm mẫu đã thay đổi. Hãy chạy lại đề xuất.");
  clearProfileSelection();
  state.transcript.clear();
  y1.forEach(c => state.transcript.set(c.code, { passed: true, grade: 8.0 }));
  renderCourseChecklist();
  await updateStudentState();
});

dom.btnSampleSophomore.addEventListener("click", async () => {
  // Chọn Year 1 và một phần Year 2
  const y12 = state.courses.filter(c => c.year <= 2).slice(0, 10);
  clearRecommendationResults("Bảng điểm mẫu đã thay đổi. Hãy chạy lại đề xuất.");
  clearProfileSelection();
  state.transcript.clear();
  y12.forEach(c => state.transcript.set(c.code, { passed: true, grade: 7.5 }));
  renderCourseChecklist();
  await updateStudentState();
});

dom.btnSampleJunior.addEventListener("click", async () => {
  // Chọn Year 1, 2 và một phần Year 3
  const y123 = state.courses.filter(c => c.year <= 3).slice(0, 18);
  clearRecommendationResults("Bảng điểm mẫu đã thay đổi. Hãy chạy lại đề xuất.");
  clearProfileSelection();
  state.transcript.clear();
  y123.forEach(c => state.transcript.set(c.code, { passed: true, grade: 8.5 }));
  renderCourseChecklist();
  await updateStudentState();
});

dom.btnClearTranscript.addEventListener("click", async () => {
  clearRecommendationResults("Bảng điểm đã xóa. Hãy chạy lại đề xuất.");
  clearProfileSelection();
  state.transcript.clear();
  renderCourseChecklist();
  await updateStudentState();
});

// Search & Filter event listeners
dom.courseSearchInput.addEventListener("input", renderCourseChecklist);
dom.courseBlockFilter.addEventListener("change", renderCourseChecklist);
dom.programSelect.addEventListener("change", onProgramChanged);
dom.profileSelect?.addEventListener("change", loadSelectedProfile);
dom.trackSelect?.addEventListener("change", async () => {
  state.selectedTrackId = dom.trackSelect.value || null;
  clearRecommendationResults("Nhánh chuyên sâu đã thay đổi. Hãy chạy lại đề xuất.");
  await updateStudentState();
});
dom.graduationPathSelect?.addEventListener("change", async () => {
  state.selectedGraduationPathId = dom.graduationPathSelect.value || null;
  clearRecommendationResults("Hướng tốt nghiệp đã thay đổi. Hãy chạy lại đề xuất.");
  await updateStudentState();
});

// --- Initialize App ---
document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initFloatingAdvisor();
  loadPrograms();
});
