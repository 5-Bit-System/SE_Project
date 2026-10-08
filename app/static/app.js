// ==========================================================================
// AI-07 Explainable Course Recommender — Web Client Logic
// ==========================================================================

const state = {
  programs: [],
  currentProgramId: null,
  currentCatalog: null,
  courses: [],
  transcript: new Map(), // code -> { passed: bool, grade: float|null }
  eligibleCourses: [],
  blockedCourses: [],
  chatHistory: [],
};

// --- DOM References ---
const dom = {
  programSelect: document.querySelector("#program-select"),
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
  detectCodesInput: document.querySelector("#detect-codes-input"),
  btnDetectProgram: document.querySelector("#btn-detect-program"),
  detectResults: document.querySelector("#detect-results"),
  
  // Tab 2 Elements
  rulesEligibleList: document.querySelector("#rules-eligible-list"),
  rulesBlockedList: document.querySelector("#rules-blocked-list"),
  rulesStatEligible: document.querySelector("#rules-stat-eligible"),
  rulesStatBlocked: document.querySelector("#rules-stat-blocked"),
  rulesStatCompleted: document.querySelector("#rules-stat-completed"),
  
  // Tab 3 Elements
  roadmapYearsGrid: document.querySelector("#roadmap-years-grid"),
  
  // Tab 4 Elements
  recommendForm: document.querySelector("#recommend-form"),
  recGoal: document.querySelector("#rec-goal"),
  recCredits: document.querySelector("#rec-credits"),
  creditsValDisplay: document.querySelector("#credits-val-display"),
  recLimit: document.querySelector("#rec-limit"),
  limitValDisplay: document.querySelector("#limit-val-display"),
  recommendationsResultContainer: document.querySelector("#recommendations-result-container"),
  recBadgeCount: document.querySelector("#rec-badge-count"),
  
  // Floating AI Advisor Widget Elements
  floatingAdvisorWidget: document.querySelector("#floating-advisor-widget"),
  advisorBubbleBtn: document.querySelector("#advisor-bubble-btn"),
  advisorChatWindow: document.querySelector("#advisor-chat-window"),
  btnMaximizeChat: document.querySelector("#btn-maximize-chat"),
  btnCloseChat: document.querySelector("#btn-close-chat"),
  btnOpenAdvisorNav: document.querySelector("#btn-open-advisor-nav"),
  chatMessagesContainer: document.querySelector("#chat-messages-container"),
  advisorChatForm: document.querySelector("#advisor-chat-form"),
  advisorInputText: document.querySelector("#advisor-input-text"),
  btnSendChat: document.querySelector("#btn-send-chat"),
};

// --- API Helper ---
async function api(path, options = {}) {
  const response = await fetch(path, options);
  const data = await response.json();
  if (!response.ok) {
    throw new Error(data.detail || "Yêu cầu thất bại");
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
      });
      tabPanels.forEach(p => p.classList.remove("active"));

      btn.classList.add("active");
      btn.setAttribute("aria-selected", "true");
      document.querySelector(`#${targetId}`).classList.add("active");
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
  state.currentProgramId = progId;

  // RÀNG BUỘC MAJOR ISOLATION: Xóa sạch dữ liệu môn đã chọn khi đổi ngành
  state.transcript.clear();
  state.chatHistory = [];

  const currentProgram = state.programs.find(p => p.program_id === progId);
  if (currentProgram) {
    dom.catalogNameText.textContent = `${currentProgram.name} · ${currentProgram.total_credits} Tín chỉ chuẩn · Trạng thái: ${currentProgram.catalog_status}`;
    dom.kpiTotalCreditsSub.textContent = `/ ${currentProgram.total_credits} Tín chỉ`;
  }

  try {
    state.courses = await api(`/courses?program_id=${encodeURIComponent(progId)}`);
    renderCourseChecklist();
    await updateStudentState();
  } catch (error) {
    console.error("Lỗi nạp môn học:", error);
    dom.courseChecklistContainer.innerHTML = `<div class="empty-state">${error.message}</div>`;
  }
}

// --- Render Course Checklist ---
function renderCourseChecklist() {
  dom.courseChecklistContainer.replaceChildren();
  
  const query = (dom.courseSearchInput.value || "").trim().toLowerCase();
  const blockFilter = dom.courseBlockFilter.value;

  const filtered = state.courses.filter(c => {
    const matchQuery = !query || c.code.toLowerCase().includes(query) || c.name.toLowerCase().includes(query);
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

    const isPassed = state.transcript.has(course.code);
    if (isPassed) row.classList.add("is-passed");

    // Left check
    const checkLabel = document.createElement("label");
    checkLabel.className = "course-check-label";
    
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.className = "course-checkbox";
    checkbox.checked = isPassed;
    checkbox.addEventListener("change", async (e) => {
      if (e.target.checked) {
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
    codeName.textContent = `${course.code} — ${course.name}`;

    const tags = document.createElement("div");
    tags.className = "course-meta-tags";
    tags.innerHTML = `
      <span class="badge badge-gray">${course.credits} TC</span>
      <span class="badge badge-gray">Năm ${course.year || 'N/A'}</span>
      <span>${course.block}</span>
    `;

    info.append(codeName, tags);
    checkLabel.append(checkbox, info);

    // Right: Grade Input (optional)
    const gradeBox = document.createElement("div");
    gradeBox.className = "grade-input-box";
    const gradeInput = document.createElement("input");
    gradeInput.type = "number";
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
      const val = parseFloat(e.target.value);
      if (!isNaN(val)) {
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
      }),
    });

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
      }),
    });

    state.eligibleCourses = eligRes.eligible_courses;
    state.blockedCourses = eligRes.blocked_courses;
    dom.kpiEligibleCount.textContent = eligRes.total_eligible;

    renderRuleEngineTab(eligRes);

    // 3. Roadmap Update
    const roadmap = await api("/roadmap", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        program_id: state.currentProgramId,
        passed_course_codes: passedCodes,
      }),
    });

    renderRoadmapTab(roadmap);

  } catch (error) {
    console.error("Lỗi cập nhật trạng thái học vụ:", error);
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
              <span class="badge badge-gray">Năm ${c.year || 'N/A'}</span>
              <span>${c.block}</span>
            </div>
          </div>
          <span class="badge badge-success">✓ Sẵn sàng</span>
        </div>
      `;
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
              <span class="badge badge-gray">Năm ${b.year || 'N/A'}</span>
              <span>${b.block}</span>
            </div>
          </div>
          <span class="badge badge-warning">Bị chặn</span>
        </div>
        ${reasonsHtml}
      `;
      dom.rulesBlockedList.appendChild(card);
    });
  }
}

// --- Render Roadmap Tab ---
function renderRoadmapTab(roadmap) {
  dom.roadmapYearsGrid.replaceChildren();

  roadmap.years.forEach(yp => {
    const col = document.createElement("div");
    col.className = "year-column";

    const percent = yp.total_credits > 0 ? Math.round((yp.completed_credits / yp.total_credits) * 100) : 0;

    col.innerHTML = `
      <div class="year-header">
        <div class="year-title">
          <span>${yp.year_name}</span>
          <span class="badge badge-gray">${yp.completed_credits} / ${yp.total_credits} TC</span>
        </div>
        <div class="year-credits-bar">
          <div class="year-progress-fill" style="width: ${percent}%;"></div>
        </div>
      </div>
      <div class="year-courses-list" id="year-courses-${yp.year}"></div>
    `;

    dom.roadmapYearsGrid.appendChild(col);
    const listEl = col.querySelector(`#year-courses-${yp.year}`);

    yp.courses.forEach(c => {
      const pill = document.createElement("div");
      pill.className = `roadmap-course-pill status-${c.status}`;
      
      let statusBadge = "";
      if (c.status === "completed") statusBadge = `<span class="badge badge-success">Đã đạt</span>`;
      else if (c.status === "eligible") statusBadge = `<span class="badge badge-info">Đủ Đ/K</span>`;
      else if (c.status === "blocked") statusBadge = `<span class="badge badge-warning">Bị chặn</span>`;

      pill.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:flex-start;">
          <strong>${c.code}</strong>
          ${statusBadge}
        </div>
        <div style="font-size:0.8rem; margin:2px 0;">${c.name}</div>
        <div class="course-meta-tags">
          <span>${c.credits} TC</span>
          <span>Kỳ ${c.suggested_term}</span>
        </div>
      `;
      listEl.appendChild(pill);
    });
  });
}

// --- Tab 4: Recommendations Form ---
dom.recCredits.addEventListener("input", (e) => {
  dom.creditsValDisplay.textContent = `${e.target.value} TC`;
});

dom.recLimit.addEventListener("input", (e) => {
  dom.limitValDisplay.textContent = `${e.target.value} môn`;
});

dom.recommendForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  dom.recommendationsResultContainer.innerHTML = `<div class="empty-state"><div class="loading-spinner">Đang phân tích và xếp hạng...</div></div>`;

  const passedCodes = [...state.transcript.entries()]
    .filter(([_, item]) => item.passed)
    .map(([code]) => code);

  try {
    const data = await api("/recommendations", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        program_id: state.currentProgramId,
        passed_course_codes: passedCodes,
        goal: dom.recGoal.value.trim(),
        max_credits: parseInt(dom.recCredits.value, 10),
        limit: parseInt(dom.recLimit.value, 10),
      }),
    });

    dom.recBadgeCount.textContent = `${data.recommendations.length} Đề xuất`;
    dom.recommendationsResultContainer.replaceChildren();

    if (data.warnings && data.warnings.length > 0) {
      data.warnings.forEach(w => {
        const notice = document.createElement("div");
        notice.className = "rule-reason-box text-amber mb-2";
        notice.textContent = `ℹ️ ${w}`;
        dom.recommendationsResultContainer.appendChild(notice);
      });
    }

    if (data.recommendations.length === 0) {
      dom.recommendationsResultContainer.innerHTML = `<div class="empty-state">Không có môn phù hợp trong giới hạn tín chỉ đã chọn.</div>`;
      return;
    }

    data.recommendations.forEach((rec, idx) => {
      const card = document.createElement("div");
      card.className = "recommendation-card";
      card.innerHTML = `
        <div class="rec-header">
          <div>
            <span class="badge badge-info" style="margin-bottom:4px;">Top #${idx + 1}</span>
            <div class="rec-title">${rec.code} — ${rec.name}</div>
          </div>
          <span class="badge badge-success">${rec.credits} Tín chỉ</span>
        </div>
        <p class="rec-reason">${rec.reason}</p>
      `;
      dom.recommendationsResultContainer.appendChild(card);
    });

  } catch (error) {
    dom.recommendationsResultContainer.innerHTML = `<div class="empty-state text-rose">${error.message}</div>`;
  }
});

// --- Floating AI Advisor Controls & Chat Logic ---
function toggleAdvisorChat(forceOpen = null) {
  if (!dom.advisorChatWindow) return;
  const isHidden = dom.advisorChatWindow.classList.contains("hidden");
  const shouldOpen = forceOpen !== null ? forceOpen : isHidden;

  if (shouldOpen) {
    dom.advisorChatWindow.classList.remove("hidden");
    dom.advisorChatWindow.setAttribute("aria-hidden", "false");
    if (dom.advisorInputText) {
      setTimeout(() => dom.advisorInputText.focus(), 120);
    }
  } else {
    dom.advisorChatWindow.classList.add("hidden");
    dom.advisorChatWindow.setAttribute("aria-hidden", "true");
  }
}

function initFloatingAdvisor() {
  if (dom.advisorBubbleBtn) {
    dom.advisorBubbleBtn.addEventListener("click", () => toggleAdvisorChat());
  }
  if (dom.btnOpenAdvisorNav) {
    dom.btnOpenAdvisorNav.addEventListener("click", () => toggleAdvisorChat(true));
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

  // Render user message
  appendChatMessage("user", text);
  dom.advisorInputText.value = "";
  dom.btnSendChat.disabled = true;

  // Typing indicator
  const typingEl = appendChatMessage("advisor", "✨ AI Advisor đang suy nghĩ và phân tích dữ liệu CTĐT...");

  const passedCodes = [...state.transcript.entries()]
    .filter(([_, item]) => item.passed)
    .map(([code]) => code);

  try {
    const data = await api("/advisor/chat", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        program_id: state.currentProgramId,
        message: text,
        passed_course_codes: passedCodes,
      }),
    });

    typingEl.remove();

    let prefix = "";
    if (data.mode === "guardrail_rejected") {
      prefix = "🛡️ **[Scope Guardrail - Ngoài phạm vi]**\n\n";
    } else if (data.mode === "heuristic_fallback") {
      prefix = "⚙️ **[Heuristic Advisor Mode]**\n\n";
    }

    appendChatMessage("advisor", prefix + data.reply, data.is_guardrail_triggered);

  } catch (error) {
    typingEl.remove();
    appendChatMessage("advisor", "⚠️ Lỗi kết nối: " + error.message, true);
  } finally {
    dom.btnSendChat.disabled = false;
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
  state.transcript.clear();
  y1.forEach(c => state.transcript.set(c.code, { passed: true, grade: 8.0 }));
  renderCourseChecklist();
  await updateStudentState();
});

dom.btnSampleSophomore.addEventListener("click", async () => {
  // Chọn Year 1 và một phần Year 2
  const y12 = state.courses.filter(c => c.year <= 2).slice(0, 10);
  state.transcript.clear();
  y12.forEach(c => state.transcript.set(c.code, { passed: true, grade: 7.5 }));
  renderCourseChecklist();
  await updateStudentState();
});

dom.btnSampleJunior.addEventListener("click", async () => {
  // Chọn Year 1, 2 và một phần Year 3
  const y123 = state.courses.filter(c => c.year <= 3).slice(0, 18);
  state.transcript.clear();
  y123.forEach(c => state.transcript.set(c.code, { passed: true, grade: 8.5 }));
  renderCourseChecklist();
  await updateStudentState();
});

dom.btnClearTranscript.addEventListener("click", async () => {
  state.transcript.clear();
  renderCourseChecklist();
  await updateStudentState();
});

// Search & Filter event listeners
dom.courseSearchInput.addEventListener("input", renderCourseChecklist);
dom.courseBlockFilter.addEventListener("change", renderCourseChecklist);
dom.programSelect.addEventListener("change", onProgramChanged);

// --- Detect Program Helper ---
dom.btnDetectProgram.addEventListener("click", async () => {
  const val = (dom.detectCodesInput.value || "").trim();
  if (!val) return;
  const codes = val.split(/[,\s]+/).map(c => c.trim().toUpperCase()).filter(Boolean);

  dom.detectResults.innerHTML = `<div class="loading-spinner">Đang đối soát CTĐT...</div>`;

  try {
    const rankings = await api("/transcript/detect-program", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ course_codes: codes }),
    });

    dom.detectResults.replaceChildren();
    rankings.forEach(item => {
      const card = document.createElement("div");
      card.className = "rule-item-card mt-2";
      const pct = Math.round(item.confidence * 100);
      card.innerHTML = `
        <div style="display:flex; justify-content:space-between; align-items:center;">
          <div>
            <strong>${item.program_name}</strong>
            <div style="font-size:0.8rem; color:var(--text-muted);">Khớp ${item.matched_count}/${item.input_total} môn (${pct}%)</div>
          </div>
          <button class="btn-primary btn-sm" data-select-id="${item.program_id}">Chọn ngành này</button>
        </div>
      `;
      card.querySelector("button").addEventListener("click", async () => {
        dom.programSelect.value = item.program_id;
        await onProgramChanged();
        // Tự động tích chọn các môn khớp
        item.matched_courses.forEach(c => {
          state.transcript.set(c, { passed: true, grade: null });
        });
        renderCourseChecklist();
        await updateStudentState();
      });
      dom.detectResults.appendChild(card);
    });
  } catch (error) {
    dom.detectResults.innerHTML = `<div class="text-rose">${error.message}</div>`;
  }
});

// --- Initialize App ---
document.addEventListener("DOMContentLoaded", () => {
  initTabs();
  initFloatingAdvisor();
  loadPrograms();
});
