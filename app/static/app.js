const programSelect = document.querySelector("#program");
const coursesBox = document.querySelector("#courses");
const catalogNote = document.querySelector("#catalog-note");
const result = document.querySelector("#result");

async function api(path, options = {}) {
  const response = await fetch(path, options);
  const body = await response.json();
  if (!response.ok) throw new Error(body.detail || "Không thể tải dữ liệu");
  return body;
}

async function loadCourses() {
  coursesBox.replaceChildren();
  result.textContent = "Chọn môn đã qua rồi xem gợi ý.";
  const programId = programSelect.value;
  if (!programId) return;
  const program = window.programs.find(item => item.program_id === programId);
  catalogNote.textContent = `${program.name}: ${program.course_count} môn đã nhập; trạng thái ${program.catalog_status}. ${program.notes.join(" ")}`;
  try {
    const courses = await api(`/courses?program_id=${encodeURIComponent(programId)}`);
    if (!courses.length) {
      coursesBox.textContent = "Chưa nhập bảng học phần cho ngành này. Nhóm cần số hóa và kiểm tra từ PDF trước khi nhận gợi ý.";
      return;
    }
    for (const course of courses) {
      const label = document.createElement("label");
      label.className = "course-row";
      const checkbox = document.createElement("input");
      checkbox.type = "checkbox";
      checkbox.value = course.code;
      const name = document.createElement("span");
      name.textContent = `${course.code} · ${course.name} (${course.credits} TC)`;
      label.append(checkbox, name);
      coursesBox.append(label);
    }
  } catch (error) {
    coursesBox.textContent = error.message;
  }
}

async function init() {
  try {
    window.programs = await api("/programs");
    for (const program of window.programs) {
      const option = document.createElement("option");
      option.value = program.program_id;
      option.textContent = program.name;
      programSelect.append(option);
    }
    await loadCourses();
  } catch (error) {
    result.textContent = error.message;
  }
}

programSelect.addEventListener("change", loadCourses);
document.querySelector("#recommend-form").addEventListener("submit", async event => {
  event.preventDefault();
  result.textContent = "Đang kiểm tra điều kiện…";
  const passed = [...coursesBox.querySelectorAll("input:checked")].map(item => item.value);
  try {
    const data = await api("/recommendations", {
      method: "POST",
      headers: {"Content-Type": "application/json"},
      body: JSON.stringify({
        program_id: programSelect.value,
        passed_course_codes: passed,
        goal: document.querySelector("#goal").value,
        max_credits: Number(document.querySelector("#credits").value),
      }),
    });
    result.replaceChildren();
    for (const warning of data.warnings) {
      const notice = document.createElement("p");
      notice.className = "notice";
      notice.textContent = warning;
      result.append(notice);
    }
    if (!data.recommendations.length) {
      const empty = document.createElement("p");
      empty.textContent = "Chưa có môn đủ điều kiện trong catalog hiện tại.";
      result.append(empty);
    }
    for (const course of data.recommendations) {
      const card = document.createElement("article");
      const heading = document.createElement("h3");
      heading.textContent = `${course.code} · ${course.name} · ${course.credits} TC`;
      const reason = document.createElement("p");
      reason.textContent = course.reason;
      card.append(heading, reason);
      result.append(card);
    }
  } catch (error) {
    result.textContent = error.message;
  }
});

init();
