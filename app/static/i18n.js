/* UI copy only. Source course names, personal input and chat replies are preserved. */
(() => {
  const en = {
    "Hồ sơ VNU": "VNU profile",
    "Chương trình tham khảo": "Reference program",
    "Bảng điểm được lấy từ VNU và lưu theo tài khoản của bạn.": "Your transcript is retrieved from VNU and saved under your account.",
    "Đăng nhập VNU để xem hồ sơ và bảng điểm qua từng học kỳ.": "Sign in with VNU to view your profile and transcript by semester.",
    "Hồ sơ và bảng điểm VNU được lưu theo tài khoản. Bạn có thể cập nhật hoặc xóa trong Hồ sơ của tôi.": "Your VNU profile and transcript are saved under your account. Update or delete them in My profile.",
    "Xem bảng điểm VNU": "View VNU transcript",
    "Mở tệp bảng điểm": "Open transcript file",
    "Bản xem trước từ tệp. Điểm được giữ nguyên theo nguồn; chưa áp dụng vào tiến độ hoặc gợi ý môn. Dữ liệu chỉ ở trong phiên này.": "File preview. Source grades are preserved and have not been applied to progress or recommendations. Data stays in this session.",
    "Chưa có bảng điểm nhập tay. Tạo học kỳ rồi thêm môn, hoặc mở tệp bảng điểm của bạn.": "No manual transcript. Create a semester and add courses, or open your transcript file.",
    "Không gian học tập": "Study workspace",
    "Thống kê từ bảng điểm VNU đã lưu. Mỗi lần học được giữ thành một lượt riêng.": "Statistics from your saved VNU transcript. Each course attempt is retained separately.",
    "Thống kê bảng điểm VNU": "VNU transcript statistics",
    "Năm học": "Academic year",
    "Điểm qua từng học kỳ": "Grades across semesters",
    "Hệ 10": "10-point scale",
    "Trung bình cộng các lượt có điểm hệ 10 hợp lệ; không phải GPA chính thức.": "Arithmetic mean of attempts with valid 10-point grades; not the official GPA.",
    "Phân bố điểm chữ": "Letter grade distribution",
    "Theo lượt học": "By attempt",
    "Giữ nguyên ký hiệu điểm từ nguồn, kể cả trạng thái chưa có điểm.": "Original grade labels are preserved, including missing grades.",
    "Tín chỉ theo học kỳ": "Credits by semester",
    "Tổng tín chỉ ghi trên các lượt học, có thể gồm học lại; không phải tín chỉ tích lũy.": "Credits on source attempts, including possible retakes; not earned credits.",
    "Xem số liệu và cách tính": "View data and calculation method",
    "Kế hoạch học tập từ dữ liệu nhập tay": "Study plan from manual data",
    "Chỉ số và điều kiện học dưới đây dùng dữ liệu nhập tay của chương trình đang chọn.": "The following metrics and eligibility results use manually entered data for the selected program.",
    "Dashboard học tập": "Study dashboard",
    "Tổng quan học tập": "Your study overview",
    "Hồ sơ của tôi": "My profile",
    "Tài khoản và bảng điểm VNU": "Account and VNU transcript",
    "Nhập điểm": "Enter grades",
    "Dữ liệu cho kế hoạch": "Data for your study plan",
    "Dữ liệu nhập tay và hội thoại chỉ dùng trong phiên. Hồ sơ VNU được lưu riêng theo tài khoản.": "Manual data and chat stay in this session. Your VNU profile is saved separately under your account.",
    "Dữ liệu nhập tay chỉ giữ trong phiên. Hồ sơ VNU được quản lý riêng.": "Manual data stays in this session. Your VNU profile is managed separately.",
    "Kết quả đã ghi nhận, những lựa chọn phía trước.": "Your recorded results. Your next choices.",
    "Ghi nhận học phần": "Record courses",
    "Các chỉ số kế hoạch sử dụng dữ liệu nhập tay của chương trình đang chọn.": "Planning metrics use manually entered data for your selected program.",
    "Xem hồ sơ VNU": "View VNU profile",
    "Hành trình tích lũy": "Your credit journey",
    "Dữ liệu nhập tay": "Manual data",
    "Đang tải chương trình…": "Loading program…",
    "Tín chỉ đã ghi nhận": "Recorded credits",
    "Đối chiếu với tổng tín chỉ chương trình; chưa phải kết luận đủ điều kiện tốt nghiệp.": "Compared with the program credit total; this does not establish graduation eligibility.",
    "Xem và cập nhật bảng điểm nhập tay": "View and edit manual transcript",
    "Có thể học tiếp": "Courses you can take next",
    "Xem tất cả": "View all",
    "Theo điều kiện tiên quyết của chương trình đang chọn.": "Based on prerequisites in your selected program.",
    "Lên kế hoạch kỳ tới": "Plan next semester",
    "Hồ sơ của bạn, có một nơi riêng.": "A dedicated place for your profile.",
    "Xem bảng điểm gốc từ VNU, kiểm tra lần cập nhật và quản lý dữ liệu đã lưu.": "View your original VNU transcript, check its update time and manage saved data.",
    "Mở hồ sơ của tôi": "Open my profile",
    "Sổ học tập": "Study workspace",
    "Sổ học tập | Kế hoạch học tập cá nhân": "Study workspace | Personal study plan",
    "Đi tới nội dung chính": "Skip to main content",
    "Ngôn ngữ": "Language",
    "Chương trình của bạn": "Your program",
    "Dữ liệu minh họa": "Demo data",
    "Không dùng profile demo": "No demo profile",
    "Giao diện": "Appearance",
    "Giao diện sáng": "Light appearance",
    "Giao diện tối": "Dark appearance",
    "Sáng": "Light",
    "Tối": "Dark",
    "Đang tải dữ liệu CTĐT...": "Loading curriculum…",
    "Bảng điểm chỉ giữ trong phiên. Đổi ngành sẽ xóa dữ liệu đã nhập.": "Your transcript stays in this session. Switching programs clears entered data.",
    "Lộ trình của bạn": "Your study journey",
    "Các bước lập kế hoạch học tập": "Study planning steps",
    "Bảng điểm": "Transcript",
    "Ghi lại những gì đã học": "Record completed courses",
    "Điều kiện học": "Eligibility",
    "Xem môn có thể học tiếp": "See available next steps",
    "Gợi ý kỳ tới": "Next semester",
    "Chọn môn theo mục tiêu": "Choose courses for your goals",
    "Một kế hoạch phù hợp bắt đầu từ bảng điểm của bạn.": "A useful plan starts with your transcript.",
    "Nhập môn đã đạt, kiểm tra điều kiện rồi khám phá những lựa chọn tiếp theo.": "Enter completed courses, check prerequisites and explore your next options.",
    "Đồng hành qua từng học kỳ": "With you through every semester",
    "Kế hoạch học tập cá nhân": "Your personal study plan",
    "Từng học kỳ, một bước tiến.": "A step forward, every semester.",
    "Theo dõi kết quả đã học và chuẩn bị những lựa chọn cho kỳ tiếp theo.": "Track your results and prepare your choices for next semester.",
    "Dữ liệu chương trình đang được rà soát. Kết quả là thông tin tham khảo; hãy xác nhận quy định và lịch mở lớp với nhà trường.": "Curriculum data is under review. Results are for reference; confirm regulations and course offerings with your university.",
    "Môn đã hoàn thành": "Completed courses",
    "Điểm ≥ 5.0": "Grade ≥ 5.0",
    "Tín chỉ tích lũy": "Earned credits",
    "GPA hệ 4": "GPA (4-point scale)",
    "Quy đổi từ điểm hệ 10": "Converted from 10-point grades",
    "Môn đủ điều kiện": "Eligible courses",
    "Theo dữ liệu chương trình": "Based on curriculum data",
    "Bảng điểm của bạn": "Your transcript",
    "Kết quả theo học kỳ và năm học, sắp xếp từ mới nhất về trước.": "Results by semester and academic year, newest first.",
    "Mở bảng điểm mẫu": "Open sample transcript",
    "Về bảng điểm nhập tay": "Back to manual transcript",
    "Mẫu năm 1": "Year 1 sample",
    "Mẫu năm 2": "Year 2 sample",
    "Mẫu năm 3": "Year 3 sample",
    "Xóa bảng điểm": "Clear transcript",
    "Học kỳ đang nhập": "Current semester",
    "Chưa xếp học kỳ": "Unassigned semester",
    "Chưa xếp": "Unassigned",
    "Thêm học kỳ / năm học": "Add semester / academic year",
    "Năm bắt đầu": "Start year",
    "Học kỳ": "Semester",
    "Hè": "Summer",
    "Thêm học kỳ": "Add semester",
    "Thêm học phần vào bảng điểm": "Add courses to your transcript",
    "Chọn từ chương trình của bạn": "Choose from your curriculum",
    "Tìm môn theo mã hoặc tên": "Search courses by code or name",
    "Tìm theo mã hoặc tên môn học…": "Search by course code or name…",
    "Lọc khối kiến thức": "Filter knowledge block",
    "Tất cả khối kiến thức": "All knowledge blocks",
    "Khối kiến thức chung": "General education",
    "Khối theo lĩnh vực": "Field knowledge",
    "Khối theo khối ngành": "Discipline knowledge",
    "Khối theo nhóm ngành": "Program group knowledge",
    "Khối kiến thức ngành": "Major knowledge",
    "Đang nạp danh sách học phần...": "Loading courses…",
    "Tên môn chưa có bản tiếng Anh được giữ nguyên theo nguồn.": "Course names without an English version are shown in their source language.",
    "Những môn bạn có thể học tiếp": "Courses you can take next",
    "Xem các môn đủ điều kiện và lý do những môn khác chưa thể học theo dữ liệu chương trình.": "See eligible courses and why other courses are currently blocked by curriculum rules.",
    "Môn Đủ điều kiện": "Eligible courses",
    "Môn Bị chặn": "Blocked courses",
    "Môn Đã học": "Completed courses",
    "Đủ điều kiện học": "Eligible to take",
    "Theo điều kiện đã ghi trong chương trình": "Based on recorded curriculum requirements",
    "Chưa đủ điều kiện": "Not yet eligible",
    "Chưa đủ điều kiện tiên quyết hoặc hạn mức": "Prerequisites or limits are not yet satisfied",
    "Bạn muốn học gì kỳ tới?": "What would you like to study next?",
    "Mục tiêu học tập & định hướng chuyên môn:": "Study goals and career interests:",
    "Ví dụ: Em muốn theo hướng AI Engineer, tập trung vào học máy và xử lý dữ liệu lớn...": "For example: I want to become an AI engineer, focusing on machine learning and big data…",
    "Tín chỉ tối đa kỳ này:": "Maximum credits this semester:",
    "Số môn đề xuất tối đa:": "Maximum recommended courses:",
    "What-if: điều chỉnh trọng số xếp hạng": "What-if: adjust ranking weights",
    "Giữ nguyên eligibility, chỉ xếp hạng lại các môn đủ điều kiện.": "Keep eligibility unchanged and rerank eligible courses.",
    "Chủ đề": "Topics",
    "Từ khóa mục tiêu": "Goal keywords",
    "Loại môn": "Course type",
    "Chạy what-if": "Run what-if",
    "Tìm môn phù hợp": "Find suitable courses",
    "Các lựa chọn dành cho bạn": "Your course options",
    "Xếp hạng bám sát mục tiêu cá nhân và giải thích minh bạch.": "Ranked for your goals, with clear explanations.",
    "Nhập bảng điểm, mô tả mục tiêu rồi chọn “Tìm môn phù hợp” để nhận gợi ý có giải thích.": "Enter your transcript and goals, then choose “Find suitable courses” to get explained recommendations.",
    "Tư vấn môn học": "Course advisor",
    "Mở khung tư vấn môn học": "Open course advisor",
    "Cùng bạn chọn môn học": "Helping you choose courses",
    "Phóng to / Thu nhỏ": "Maximize / Restore",
    "Phóng to": "Maximize",
    "Thu nhỏ": "Restore",
    "Thu gọn": "Minimize",
    "Đóng": "Close",
    "Phạm vi tư vấn:": "Advising scope:",
    "Định hướng môn học & CTĐT. Không xếp lịch học hoặc chấm điểm giảng viên.": "Courses and curriculum planning. No timetabling or lecturer ratings.",
    "Chọn hướng học cùng AI Advisor": "Explore study paths with AI Advisor",
    "Nhánh chuyên sâu": "Specialization",
    "Không chọn nhánh": "No specialization selected",
    "Hướng tốt nghiệp": "Graduation path",
    "Không chọn hướng": "No path selected",
    "AI Advisor sẽ dùng lựa chọn này để giải thích điều kiện và gợi ý môn học.": "AI Advisor uses these choices to explain requirements and suggest courses.",
    "Xin chào! Tôi là": "Hello! I am",
    "hỗ trợ học vụ cho bạn.": "here to help with your studies.",
    "Tôi có thể giúp bạn giải đáp định hướng nghề nghiệp, gợi ý môn học phù hợp theo từng track và giải thích lộ trình học tập dựa trên bảng điểm thực tế của bạn.": "I can help explore career interests, suggest courses for your specialization and explain study paths using your transcript.",
    "(Tôi chỉ tư vấn môn học & CTĐT; không xếp lịch học hay đánh giá giảng viên).": "(I advise on courses and curricula; I do not create timetables or rate lecturers.)",
    "🤖 Hướng AI": "🤖 AI track",
    "📊 Data Analyst": "📊 Data Analyst",
    "📚 Môn kỳ tới": "📚 Next semester",
    "🔒 Môn bị chặn": "🔒 Blocked courses",
    "Em muốn theo hướng Trí tuệ nhân tạo (AI), kỳ tới nên học những môn gì?": "I want to specialize in AI. Which courses should I take next semester?",
    "Em muốn làm Data Analyst, lộ trình học môn nào quan trọng nhất?": "I want to become a data analyst. Which courses matter most for this path?",
    "Kỳ tới em có đủ điều kiện học các môn chuyên ngành bắt buộc nào?": "Which required major courses am I eligible for next semester?",
    "Tại sao có môn của em đang bị chặn?": "Why are some of my courses blocked?",
    "Câu hỏi tư vấn môn học": "Question for the course advisor",
    "Hỏi AI Advisor về môn học, định hướng...": "Ask AI Advisor about courses and study paths…",
    "Gửi": "Send",
    "Sổ học tập · Gợi ý học phần có giải thích · Chương trình ĐHKHTN - ĐHQG Hà Nội, khóa 2022.": "Study workspace · Explained course recommendations · HUS, VNU Hanoi curriculum, cohort 2022.",
    "Bảng điểm và hội thoại chỉ dùng trong phiên hiện tại. Gợi ý không xác nhận môn sẽ mở lớp.": "Transcripts and chats are used only in this session. Recommendations do not confirm course offerings.",
    "STT": "No.",
    "Mã MH": "Course code",
    "Môn học": "Course",
    "Số TC": "Credits",
    "Tín chỉ": "Credits",
    "Điểm hệ 10": "Grade / 10",
    "Điểm / 10": "Grade / 10",
    "Điểm chữ": "Letter grade",
    "Điểm hệ 4": "Grade / 4",
    "Đã đạt": "Passed",
    "Học phần": "Course",
    "Thao tác": "Actions",
    "Thêm môn": "Add course",
    "Danh sách học phần để thêm": "Courses available to add",
    "Bảng điểm học kỳ": "Semester transcript",
    "Bảng điểm theo năm học và học kỳ, mới nhất trước": "Transcript by academic year and semester, newest first",
    "Bảng điểm từ nguồn, giữ nguyên điểm hệ 10, điểm chữ và điểm hệ 4": "Source transcript with original 10-point, letter and 4-point grades",
    "Bản xem trước từ tệp mẫu. Điểm được giữ nguyên theo nguồn; chưa áp dụng vào tiến độ hoặc gợi ý môn. Dữ liệu chỉ ở trong phiên này.": "Sample file preview. Source grades are preserved and have not been applied to progress or recommendations. Data stays in this session.",
    "Chưa có bảng điểm. Tạo học kỳ theo năm học thực tế rồi thêm môn, hoặc mở tệp bảng điểm mẫu.": "No transcript yet. Create an actual academic semester and add courses, or open a sample transcript file.",
    "Chưa có học phần. Thêm môn từ danh sách bên dưới để bắt đầu học kỳ này.": "No courses yet. Add courses from the list below to start this semester.",
    "Không còn học phần phù hợp với bộ lọc. Thử đổi từ khóa hoặc khối kiến thức.": "No courses match these filters. Try another keyword or knowledge block.",
    "Không thể kết nối tới máy chủ. Hãy kiểm tra backend rồi thử lại.": "Cannot connect to the server. Check the connection and try again.",
    "API trả về dữ liệu không hợp lệ.": "The server returned invalid data.",
    "Chưa có profile demo · nhập bảng điểm thủ công": "No demo profiles · enter your transcript manually",
    "Không nạp được profile demo": "Could not load demo profiles",
    "Chưa chọn nhánh": "Select a specialization",
    "Ngành này không chia nhánh": "This program has no specializations",
    "Chưa chọn hướng": "Select a path",
    "Chưa có dữ liệu hướng tốt nghiệp": "No graduation path data available",
    "Đã xác minh": "Verified",
    "Đang rà soát": "Under review",
    "Chưa rõ trạng thái": "Status unknown",
    "Nguồn CTĐT chưa được xác minh đầy đủ": "Curriculum source has not been fully verified",
    "Chưa rõ năm học": "Academic year unknown",
    "✓ Sẵn sàng": "✓ Ready",
    "Bị chặn": "Blocked",
    "Không có môn nào bị chặn.": "No blocked courses.",
    "Chưa có môn đủ điều kiện. Hãy hoàn thành các môn tiên quyết cơ sở.": "No eligible courses yet. Complete the foundation prerequisites first.",
    "Đã đổi ngành. Hãy chạy lại đề xuất theo catalog mới.": "Program changed. Run recommendations for the new curriculum.",
    "Hồ sơ học tập đã thay đổi. Hãy chạy lại đề xuất.": "Study profile changed. Run recommendations again.",
    "Bảng điểm đã thay đổi. Hãy chạy lại đề xuất.": "Transcript changed. Run recommendations again.",
    "Bảng điểm đã xóa. Hãy chạy lại đề xuất.": "Transcript cleared. Run recommendations again.",
    "Bảng điểm mẫu đã thay đổi. Hãy chạy lại đề xuất.": "Sample transcript changed. Run recommendations again.",
    "Nhánh chuyên sâu đã thay đổi. Hãy chạy lại đề xuất.": "Specialization changed. Run recommendations again.",
    "Hướng tốt nghiệp đã thay đổi. Hãy chạy lại đề xuất.": "Graduation path changed. Run recommendations again.",
    "Thiếu môn tiên quyết": "Missing prerequisites",
    "Đã đủ số môn trong nhóm lựa chọn": "Choice group limit reached",
    "Vượt ngân sách tín chỉ": "Credit budget exceeded",
    "Xung đột nguồn dữ liệu": "Conflicting source data",
    "Không thuộc nhánh đã chọn": "Outside the selected specialization",
    "Không thuộc hướng tốt nghiệp đã chọn": "Outside the selected graduation path",
    "Tập môn đủ điều kiện": "Eligible course pool",
    "Bộ xếp hạng": "Ranking method",
    "Chế độ": "Mode",
    "What-if trên cùng tập đủ điều kiện": "What-if using the same eligible pool",
    "Tóm tắt môn bị chặn": "Blocked course summary",
    "Không có môn bị chặn.": "No blocked courses.",
    "Cảnh báo của hệ thống": "System notices",
    "Chưa xác minh đầy đủ": "Not fully verified",
    "Chưa xác định": "Unknown",
    "Có thể mở": "May be offered",
    "Chưa mở": "Not offered",
    "Chưa xác minh mở lớp": "Offering not verified",
    "Lý do đủ điều kiện": "Why this course is eligible",
    "Mức độ phù hợp": "How it fits your goals",
    "Đã vượt qua kiểm tra eligibility của hệ thống.": "Passed the system eligibility checks.",
    "Chưa có dữ liệu phù hợp chi tiết.": "No detailed fit information available.",
    "Chưa có giải thích tổng hợp.": "No combined explanation available.",
    "Chưa có dữ liệu.": "No data available.",
    "Chưa có kết quả đề xuất.": "No recommendations yet.",
    "Không có môn phù hợp trong giới hạn tín chỉ đã chọn.": "No matching courses within the selected credit limit.",
    "Đang phân tích và xếp hạng...": "Analyzing and ranking…",
    "Đang chạy what-if trên cùng tập môn đủ điều kiện...": "Running what-if on the same eligible course pool…",
    "Hãy giữ ít nhất một trọng số lớn hơn 0.": "Keep at least one weight above zero.",
    "Lỗi": "Error",
    "Catalog chưa được xác minh đầy đủ; kết quả chỉ dùng thử, không phải tư vấn học vụ.": "The curriculum is not fully verified; results are for demonstration and are not official academic advice.",
    "Trạng thái mở lớp trong học kỳ chưa được xác minh từ dữ liệu hiện có.": "Semester course offerings have not been verified from the available data.",
    "Chưa hoàn thành môn này và đã thỏa các prerequisite trong catalog.": "Not completed yet; recorded curriculum prerequisites are satisfied.",
    "Môn có một phần từ khóa trùng với mục tiêu đã nhập.": "This course matches some keywords in your goal.",
    "Catalog hiện chưa có metadata đủ để xác định điểm phù hợp cụ thể cho preference này.": "The curriculum does not yet contain enough metadata to determine a specific fit for this preference.",
    "Môn học có xung đột điều kiện tiên quyết trong tài liệu nguồn PDF.": "The source PDF contains conflicting prerequisites for this course.",
    "Điều kiện tiên quyết của môn học chưa được xác định từ tài liệu nguồn.": "This course's prerequisites have not been established from the source documents.",
    "Đã qua kiểm tra eligibility của backend.": "Passed the backend eligibility checks.",
    "Phóng to khung chat": "Maximize chat",
    "Thu nhỏ về 1/4 màn hình": "Restore chat window"
  };

  const storageKey = "study-workspace-language";
  let language = "vi";
  try { if (localStorage.getItem(storageKey) === "en") language = "en"; } catch { /* Optional preference. */ }
  const originals = new WeakMap();
  const attributes = new WeakMap();
  const skip = 'script,style,textarea,[data-course-code],.course-code-name,.table-course-code,#portal-dialog,.portal-source,.portal-transcript-table td,.source-profile-value,#catalog-name-text,.chat-message:not([data-ui-copy])';

  function translate(source) {
    if (language !== "en") return source;
    const value = source.trim();
    if (Object.hasOwn(en, value)) return source.replace(value, en[value]);
    const rules = [
      [/^(\d+) (?:môn|học phần)$/, '$1 courses'],
      [/^(\d+) Đề xuất$/, '$1 recommendations'],
      [/^(\d+) (?:TC|Tín chỉ|tín chỉ)$/, '$1 credits'],
      [/^\/ (.+) (?:Tín chỉ|tín chỉ)$/, '/ $1 credits'],
      [/^Hạng #(\d+)$/, 'Rank #$1'],
      [/^Năm (\d+)$/, 'Year $1'],
      [/^Mã học kỳ (.+)$/, 'Term code $1'],
      [/^Học kỳ (.+)$/, (_, term) => 'Semester ' + term.replace('Hè', 'Summer')],
      [/^(\d+) tín chỉ đã đạt$/, '$1 credits passed'],
      [/^Tổng tín chỉ trong bảng: (.+)$/, 'Total credits in transcript: $1'],
      [/^Điểm phù hợp: (.+)$/, 'Fit score: $1'],
      [/^Tên hoặc metadata môn có chứa chủ đề người học nêu: (.+)$/, 'The course name or metadata contains your topic: $1'],
      [/^Môn có loại (.+) đúng với preference đã chuẩn hóa\.$/, 'The course type $1 matches your normalized preference.'],
      [/^Đủ điều kiện: (.+) Phù hợp: (.+)$/, (_, eligible, fit) => `Eligibility: ${translate(eligible)} Fit: ${translate(fit)}`],
      [/^(⚠️\s*)?Chưa hoàn thành môn tiên quyết: (.+)$/, (_, icon, codes) => `${icon || ''}Missing prerequisites: ${codes.replaceAll(' hoặc ', ' or ')}`],
      [/^(⚠️\s*)?Môn thuộc hướng khác với track đã chọn: (.+)$/, (_, icon, track) => `${icon || ''}Outside the selected specialization: ${track}`],
      [/^(⚠️\s*)?Môn thuộc nhánh tốt nghiệp khác với nhánh đã chọn: (.+)$/, (_, icon, path) => `${icon || ''}Outside the selected graduation path: ${path}`],
      [/^(⚠️\s*)?Nhóm môn tự chọn \((.+)\) đã hoàn thành đủ số tín chỉ yêu cầu\.$/, (_, icon, group) => `${icon || ''}Required credits already completed for elective group (${group}).`],
      [/^(⚠️\s*)?Số tín chỉ môn học \((.+) TC\) vượt quá ngân sách recommendation \((.+) TC\)\.$/, (_, icon, credits, budget) => `${icon || ''}Course credits (${credits}) exceed the recommendation budget (${budget}).`],
      [/^Nguồn: (.+)$/, (_, status) => 'Source: ' + translate(status)],
      [/^Mở lớp: (.+)$/, (_, status) => 'Offering: ' + translate(status)],
      [/^Đã hoàn thành (.+)$/, 'Completed $1'],
      [/^Điểm hệ 10 của (.+)$/, '10-point grade for $1'],
      [/^Học kỳ của (.+)$/, 'Semester for $1'],
      [/^Xóa (.+) khỏi bảng điểm$/, 'Remove $1 from transcript'],
      [/^Thêm (.+) vào (.+)$/, (_, code, term) => `Add ${code} to ${translate(term)}`],
      [/^Không mở được bảng điểm: (.+)$/, 'Cannot open transcript: $1'],
      [/^Lỗi khi lấy đề xuất: (.+)$/, 'Could not get recommendations: $1'],
      [/^Lỗi what-if: (.+)$/, 'What-if failed: $1'],
      [/^Không thể cập nhật điều kiện học vụ: (.+)$/, 'Could not update eligibility: $1'],
      [/^Không thể nạp dữ liệu môn học: (.+)$/, 'Could not load courses: $1'],
      [/^Lỗi nạp chương trình: (.+)$/, 'Could not load programs: $1']
    ];
    // Translate UI segments independently while leaving source names untouched.
    if (value.includes(' · ')) return source.replace(value, value.split(' · ').map(translate).join(' · '));
    if (value.startsWith('⚠️ ') && Object.hasOwn(en, value.slice(3))) return source.replace(value, '⚠️ ' + en[value.slice(3)]);
    for (const [pattern, replacement] of rules) {
      if (pattern.test(value)) return source.replace(value, value.replace(pattern, replacement));
    }
    const summary = /^(.*): (\d+)$/.exec(value);
    if (summary && Object.hasOwn(en, summary[1])) return source.replace(value, `${en[summary[1]]}: ${summary[2]}`);
    return source;
  }

  function updateValue(node, current, records, key, write) {
    const previous = records.get(key);
    const source = previous && current === previous.output ? previous.source : current;
    const output = translate(source);
    records.set(key, {source, output});
    if (current !== output) write(output);
  }

  let observer;
  function localize() {
    observer?.disconnect();
    document.documentElement.lang = language;
    const walker = document.createTreeWalker(document.documentElement, NodeFilter.SHOW_TEXT);
    while (walker.nextNode()) {
      const node = walker.currentNode;
      if (!node.parentElement || node.parentElement.closest(skip) || !node.textContent.trim()) continue;
      const record = originals.get(node);
      const source = record && node.textContent === record.output ? record.source : node.textContent;
      const output = translate(source);
      originals.set(node, {source, output});
      if (node.textContent !== output) node.textContent = output;
    }
    document.querySelectorAll('[placeholder],[aria-label],[title],[data-prompt]').forEach(node => {
      if (node.closest('[data-course-code],.portal-transcript-table td,.chat-message:not([data-ui-copy])')) return;
      if (!attributes.has(node)) attributes.set(node, new Map());
      for (const key of ['placeholder', 'aria-label', 'title', 'data-prompt']) {
        if (node.hasAttribute(key)) updateValue(node, node.getAttribute(key), attributes.get(node), key, value => node.setAttribute(key, value));
      }
    });
    observer?.observe(document.body, {subtree: true, childList: true, characterData: true, attributes: true, attributeFilter: ['placeholder', 'aria-label', 'title', 'data-prompt']});
  }

  const sourceSummaryLabels = {
    'Tổng tín chỉ': 'Total credits',
    'Tổng tín chỉ tích lũy': 'Accumulated credits',
    'Điểm trung bình tích lũy hệ 4': 'Cumulative GPA (4-point scale)',
    'Điểm trung bình tích lũy hệ 10': 'Cumulative average (10-point scale)',
    'Điểm trung bình học kỳ hệ 4': 'Semester GPA (4-point scale)',
    'Điểm trung bình học kỳ hệ 10': 'Semester average (10-point scale)'
  };
  function formatSourceSummary(row) {
    // Translate known labels at the start of a cell. Preserve every source
    // value, separator and unknown label; never recalculate or mutate rows.
    return row.map(cell => {
      const text = String(cell ?? '');
      if (language !== 'en') return text;
      const label = Object.keys(sourceSummaryLabels).find(label => {
        const trimmed = text.trimStart();
        return trimmed.startsWith(label) && /^\s*(?:[:：]|$)/.test(trimmed.slice(label.length));
      });
      return label ? text.replace(label, sourceSummaryLabels[label]) : text;
    }).join(' | ');
  }

  window.workspaceI18n = {
    formatSourceSummary,
    get language() { return language; },
    setLanguage(value) {
      language = value === 'en' ? 'en' : 'vi';
      try { localStorage.setItem(storageKey, language); } catch { /* Keep session language. */ }
      localize();
    },
    translate,
    refresh: localize
  };
  document.addEventListener('DOMContentLoaded', () => {
    observer = new MutationObserver(localize);
    localize();
  });
})();
