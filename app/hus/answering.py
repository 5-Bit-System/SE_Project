"""Conservative, extractive HUS answers. No provider calls or invented missing facts."""

from __future__ import annotations

import json
import re

from app.hus.rag_loader import HUSRAGData
from app.hus.citations import CitationResolver, citation_line
from app.hus.retrieval import COURSE_CODE, FIELD_LABELS, STOP_WORDS, HUSRAGRetriever, _body, _tokens
from app.schemas.hus import HUSAnswer, HUSQuestion


def _has(text: str, *phrases: str) -> bool:
    return any(f" {phrase} " in f" {text} " for phrase in phrases)


def assessment_fact_request(question: str) -> bool:
    """Exam weights/formats remain unknown even inside a recommendation request."""
    text = " ".join(_tokens(question))
    assessment = _has(text, "thi", "diem", "danh gia", "cuoi ky", "giua ky", "trac nghiem", "tu luan")
    return assessment and ("%" in question or _has(
        text, "phan tram", "ty le", "ti le", "trong so", "ty trong", "ti trong", "chiem",
        "hinh thuc thi", "trac nghiem", "tu luan"))


def question_intent(question: str) -> tuple[str | None, str | None]:
    """Only recognize supported information intents; recommendation stays separate."""
    text = " ".join(_tokens(question))
    if assessment_fact_request(question):
        return "f3", "official_assessment"
    if _has(text, "nen hoc", "nen dang ky", "goi y mon", "de xuat mon", "chon mon",
            "du dieu kien", "lo trinh", "ky toi nen", "ky toi hoc", "nen uu tien"):
        return None, None
    if _has(text, "tin chi"):
        return "f2", "credits"
    if _has(text, "tien quyet"):
        return "f2", "prerequisites"
    if _has(text, "so tiet", "so gio"):
        return "f2", "hours"
    if _has(text, "ten mon", "ten hoc phan"):
        return "f2", "name"
    if _has(text, "nghe nghiep", "viec lam", "lam nghe", "sau tot nghiep"):
        return "f1", "careers"
    if _has(text, "hoc tiep", "sau dai hoc"):
        return "f1", "further_study"
    if _has(text, "danh gia", "thi", "kiem tra", "cuoi ky", "ty le diem", "trong so"):
        return "f3", "suggested_assessment"
    if _has(text, "muc tieu", "chuan dau ra"):
        return ("f3", "objectives") if any(COURSE_CODE.fullmatch(t) for t in _tokens(question)) or _has(
            text, "hoc phan", "mon hoc") else ("f1", "objectives")
    if _has(text, "noi dung", "chu de", "hoc gi", "de cuong"):
        return "f3", "content"
    if _has(text, "gioi thieu", "tong quan"):
        return "f1", "introduction"
    return None, None


def is_hus_question(question: str) -> bool:
    text = " ".join(_tokens(question))
    if assessment_fact_request(question):
        return True
    # Preserve recommendation routing even if a credit count occurs in that request.
    if _has(text, "nen hoc", "nen dang ky", "goi y mon", "de xuat mon", "chon mon",
            "du dieu kien", "lo trinh", "ky toi nen", "ky toi hoc", "nen uu tien"):
        return False
    return (question_intent(question)[0] is not None or any(COURSE_CODE.fullmatch(t) for t in _tokens(question))) or _has(
        text, "hus", "hoc phi", "diem chuan", "tuyen sinh", "quy che", "hoc bong")


MAJOR_NAMES = {
    "mathematics": ("toan hoc", "toanhoc", "nganh toan", "mathematics"),
    "mathematics_informatics": ("toan tin", "toantin", "toan hoc va tin hoc", "mathematics informatics"),
    "computer_science": ("khoa hoc may tinh", "may tinh va khoa hoc thong tin", "may tinh va thong tin",
                         "khmtt", "khmt tt", "khmt", "computer science"),
    "data_science": ("khoa hoc du lieu", "khdl", "data science"),
}
UNSUPPORTED = ("hoc phi", "diem chuan", "chi tieu", "tuyen sinh", "luong", "lich hoc", "hoc bong",
               "giang vien", "thoi khoa bieu", "quy che", "dang mo", "dang duoc mo")
GENERIC = set(_tokens(" ".join(FIELD_LABELS.values()) + " nganh hoc phan mon sinh vien tot nghiep "
                     "chuong trinh dao tao nhung nhu the nao sau khi lam cong viec du kien "
                     "tham khao toi muon hoi xin biet duoc co the gi co hoi")) | STOP_WORDS


def _verified_requested(question: str) -> bool:
    text = " ".join(_tokens(question))
    return "%" in question or _has(text, "chinh thuc", "da xac minh", "hien hanh", "hien nay",
                                    "hien tai", "nam nay", "ty le", "phan tram", "cuoi ky", "trong so")


class HUSAnswerer:
    def __init__(self, data: HUSRAGData, *, asset_root=None):
        self.data = data
        self.citation_resolver = CitationResolver(data, **({"asset_root": asset_root} if asset_root is not None else {}))
        self.retriever = HUSRAGRetriever(data)
        self.programs = data.program_scopes()

    def answer(self, request: HUSQuestion) -> HUSAnswer:
        answer = self._answer(request)
        identity = self.data.release_identity
        return answer.model_copy(update={"release_id": identity["release_id"],
                                         "release_sha256": identity["release_sha256"],
                                         "generated_reference_allowed": request.allow_generated_reference})

    def _answer(self, request: HUSQuestion) -> HUSAnswer:
        dataset, field = question_intent(request.question)
        dataset = dataset if request.dataset == "auto" else request.dataset
        field = request.field or field
        text = " ".join(_tokens(request.question))
        codes = {t.upper() for t in _tokens(request.question) if COURSE_CODE.fullmatch(t)}
        if len(codes) > 1 or (codes and request.course_code and request.course_code not in codes):
            return self._missing(request, dataset, "Cần một mã học phần thống nhất cho mỗi câu hỏi.", clarify=True)
        code = request.course_code or next(iter(codes), None)
        # Consume longer names first: Toan hoc va Tin hoc is not a second Math major.
        named, mentioned = f" {text} ", set()
        aliases = sorted(((name, major) for major, names in MAJOR_NAMES.items() for name in names),
                         key=lambda item: (item[0].startswith("nganh "), -len(item[0])))
        for name, major in aliases:
            if f" {name} " in named:
                mentioned.add(major)
                named = named.replace(f" {name} ", " ")
        if mentioned and mentioned != {request.major}:
            return self._missing(request, dataset, "Câu hỏi khác phạm vi ngành đã chọn; cần chọn đúng ngành.")
        if _has(text, *UNSUPPORTED) or re.search(r"\b20(?:2[6-9]|[3-9]\d)\b", text):
            return self._missing(request, dataset, "Chưa có bằng chứng phù hợp về nội dung hoặc thời điểm được hỏi.")
        if dataset == "f2":
            if field is None and not _has(text, "thong tin", "la mon gi", "la gi"):
                return self._missing(request, dataset, "Chưa xác định được trường dữ kiện được hỏi.")
            return self._f2(request, code, field or "course_info")
        if dataset not in {"f1", "f3"}:
            return self._missing(request, None, "Phạm vi hiện có là giới thiệu ngành, dữ kiện chương trình và học phần.")
        if _verified_requested(request.question) or field == "official_assessment":
            return self._missing(request, dataset, "Chưa có thông tin đã xác minh cho yêu cầu chính thức/hiện hành."
                                 + (" F3 hiện có là nội dung tham khảo do AI sinh." if dataset == "f3" else ""))
        if dataset == "f3" and not code:
            return self._missing(request, dataset, "Cần mã học phần để tránh nhầm nội dung giữa các môn.", clarify=True)
        if dataset == "f3":
            if request.version and self.data.get_f2_course(code, major=request.major, version=request.version) is None:
                return self._missing(request, dataset, "Không có môn này trong ngành và phiên bản đã chọn.")
            if not request.allow_generated_reference:
                return self._missing(request, dataset, "Cần bật cho phép kiến thức AI tham khảo để dùng dữ liệu F3 AI sinh.", clarify=True)
        allowed = {"introduction", "careers", "further_study", "objectives"} if dataset == "f1" else {
            "content", "objectives", "suggested_assessment"}
        if field not in allowed:
            return self._missing(request, dataset, "Chưa xác định được loại thông tin phù hợp trong dữ liệu.")
        hits = self.retriever.search(request.question, dataset=dataset, major=request.major,
                                     version=request.version, course_code=code, field=field,
                                     program_variant=request.program_variant, top_k=5,
                                     allow_generated=request.allow_generated_reference)
        # Generic intent labels alone must not support an unrelated specific assertion.
        generic = GENERIC | set(_tokens(" ".join(n for names in MAJOR_NAMES.values() for n in names)))
        for hit in hits:
            generic.update(_tokens(hit.chunk.metadata.get("course_name", "")))
        specific = set(_tokens(request.question)) - generic - {c.lower() for c in codes}
        hits = tuple(h for h in hits if not specific or specific <= set(h.matched_terms))[:2]
        if not hits:
            return self._missing(request, dataset, "Không tìm thấy đoạn có bằng chứng khớp câu hỏi và phạm vi đã chọn.")
        citations, excerpts, warnings = [], [], []
        for i, hit in enumerate(hits, 1):
            chunk, meta = hit.chunk, hit.chunk.metadata
            citations.append(self.citation_resolver.chunk(chunk, _body(chunk), i))
            source = citation_line(citations[-1]) + f"; phiên bản: {chunk.version}"
            if meta.get("program_variant"):
                source += f"; hệ: {meta['program_variant']}"
            excerpts.append(f"[{i}] {_body(chunk)}\n{source}")
            if dataset == "f3":
                warnings.append(meta["warning"])
            elif meta["review_status"] == "include_markdown":
                warnings.append("Nguồn được duyệt trên Markdown; chưa đối chiếu PDF/DOCX gốc.")
        warnings = list(dict.fromkeys(warnings))
        if dataset == "f1":
            warnings.append("Chỉ mô tả theo nguồn đã lưu; chưa xác minh hiệu lực hiện tại.")
        reply = "\n\n".join(warnings + excerpts)
        return HUSAnswer(reply=reply, status="answered", dataset=dataset, major=request.major,
                         version=request.version, citations=citations, warnings=warnings)

    @staticmethod
    def _missing(request, dataset, reason, *, clarify=False):
        return HUSAnswer(reply="Chưa có thông tin đủ căn cứ để trả lời. " + reason,
                         status="needs_clarification" if clarify else "no_information",
                         dataset=dataset, major=request.major, version=request.version)

    def _f2(self, request: HUSQuestion, code: str | None, field: str) -> HUSAnswer:
        if not code or not request.version:
            return self._missing(request, "f2", "Cần mã học phần và phiên bản chương trình.", clarify=True)
        course = self.data.get_f2_course(code, major=request.major, version=request.version)
        if course is None:
            return self._missing(request, "f2", "Không có môn này trong ngành và phiên bản đã chọn.")
        if _verified_requested(request.question):
            if course.review_status == "verified":
                return self._missing(request, "f2", "Nguồn có sign-off cấp dự án; chưa có chứng cứ xác nhận hiện hành/chứng nhận của trường.")
            return self._missing(request, "f2", f"Nguồn hiện có mang trạng thái {course.review_status}; chưa xác minh học vụ.")
        values = {
            "name": course.course.get("course_name"),
            "credits": [r.get("credits_in_source") for r in course.source_rows],
            "prerequisites": [r.get("prerequisite_source_text") for r in course.source_rows],
            "hours": course.course_metadata.get("values", {}).get("hours"),
            "course_info": {k: course.course.get(k) for k in ("course_name", "credits")},
        }
        if field not in values or values[field] is None:
            return self._missing(request, "f2", "Trường dữ liệu được hỏi chưa có thông tin nguồn.")
        value = values[field]
        if field == "credits":
            if any(v is None for v in value) or len(set(value)) != 1:
                return self._missing(request, "f2", "Số tín chỉ thiếu hoặc không thống nhất giữa các dòng nguồn.")
            value = value[0]
        facts = {"course_code": code, "course_name": course.course["course_name"], "field": field,
                 "value": value, "review_status": course.review_status,
                 "has_prerequisite_conflict": course.has_prerequisite_conflict,
                 "unresolved_prerequisites": list(course.unresolved_prerequisites)}
        if "catalog_review" in course.provenance:
            facts["catalog_review"] = course.provenance["catalog_review"]
        citations = []
        for i, row in enumerate(course.source_rows, 1):
            citations.append(self.citation_resolver.course_row(course, row, i, json.dumps(row, ensure_ascii=False)))
        if field == "prerequisites":
            facts["prerequisite_groups"] = list(course.prerequisites)
            rendered = "\n".join(f"[{i}] {v if v else 'Dòng nguồn không ghi điều kiện tiên quyết'}"
                                  for i, v in enumerate(value, 1))
        elif field == "course_info":
            rendered = f"Tên: {value['course_name']}; số tín chỉ: {value['credits']}"
        else:
            rendered = json.dumps(value, ensure_ascii=False) if isinstance(value, dict) else str(value)
        if course.review_status == "verified":
            warnings = ["Trạng thái: verified theo sign-off cấp dự án đã ghi trong nguồn; không phải chứng nhận của trường."]
        else:
            warnings = [f"Trạng thái xác minh: {course.review_status}; dữ kiện chép từ nguồn, chưa xác minh học vụ."]
        if course.has_prerequisite_conflict:
            warnings.append("Có mâu thuẫn điều kiện tiên quyết giữa các dòng nguồn; chưa kết luận điều kiện đúng.")
        if course.unresolved_prerequisites:
            warnings.append("Mã tiên quyết chưa giải quyết: " + ", ".join(course.unresolved_prerequisites))
        source_lines = [citation_line(c) for c in citations]
        label = {"credits": "Số tín chỉ", "prerequisites": "Điều kiện tiên quyết theo dòng nguồn",
                 "name": "Tên học phần", "hours": "Số giờ theo nguồn", "course_info": "Thông tin học phần"}[field]
        reply = "\n\n".join([f"{code} — {course.course['course_name']} ({request.version})\n{label}: {rendered}"]
                                + warnings + source_lines)
        return HUSAnswer(reply=reply, status="answered", dataset="f2", major=request.major,
                         version=request.version, facts=facts, citations=citations, warnings=warnings)
