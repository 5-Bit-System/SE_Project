"""Conservative, extractive HUS answers. No provider calls or invented missing facts."""

from __future__ import annotations

import json
import re

from app.hus.rag_loader import F2Course, HUSRAGData
from app.hus.citations import CitationResolver, citation_line
from app.hus.retrieval import COURSE_CODE, HUSRAGRetriever, _body, _tokens
from app.hus.question_routing import (
    has as _has, assessment_fact_request as assessment_fact_request,
    is_hus_question as is_hus_question, question_intent,
    out_of_scope, requested_text, requested_course_fields, unsupported_request, verified_requested as _verified_requested,
    COURSE_FIELD_TERMS, PROGRAM_FIELDS, CAREER_TERMS, requested_program_fields, question_group_keys, program_total_request,
)
from app.hus.answer_support import supported_hits
from app.schemas.hus import F2PrerequisiteStatus, HUSAnswer, HUSQuestion


def prerequisite_status(course: F2Course) -> F2PrerequisiteStatus:
    """Interpret source rows without replacing missing raw values or review."""
    raw = [row.get("prerequisite_source_text") for row in course.source_rows]
    variants = {" ".join(value.split()) for value in raw if value and value.strip()}
    parses = {row.get("prerequisite_parse_status") for row in course.source_rows}
    if course.has_prerequisite_conflict or "conflict" in parses or len(variants) > 1:
        return "conflict"
    if not raw or any(not value or not value.strip() for value in raw):
        return "unknown"
    if course.unresolved_prerequisites or parses - {"normalized", "parsed"}:
        return "unresolved"
    return "present"


MAJOR_NAMES = {
    "mathematics": ("toan hoc", "toanhoc", "nganh toan", "mathematics"),
    "mathematics_informatics": ("toan tin", "toantin", "toan hoc va tin hoc", "mathematics informatics"),
    "computer_science": ("khoa hoc may tinh va thong tin", "khoa hoc may tinh", "may tinh va khoa hoc thong tin", "may tinh va thong tin",
                         "khmttt", "khmtt", "khmt tt", "khmt", "computer science"),
    "data_science": ("khoa hoc du lieu", "khdl", "data science"),
}
class HUSAnswerer:
    def __init__(self, data: HUSRAGData, *, asset_root=None, retriever=None):
        self.data = data
        self.citation_resolver = CitationResolver(data, **({"asset_root": asset_root} if asset_root is not None else {}))
        self.retriever = HUSRAGRetriever(data) if retriever is None else retriever
        self.programs = data.program_scopes()

    def answer(self, request: HUSQuestion) -> HUSAnswer:
        answer = self._answer(request)
        identity = self.data.release_identity
        return answer.model_copy(update={"release_id": identity["release_id"],
                                         "release_sha256": identity["release_sha256"],
                                         "generated_reference_allowed": request.allow_generated_reference})

    def _answer(self, request: HUSQuestion) -> HUSAnswer:
        dataset, field = question_intent(request.question)
        # Request hints never authorize actions outside the standalone Q&A scope.
        if out_of_scope(request.question):
            return self._missing(request, dataset, "Phạm vi hỏi đáp không hỗ trợ xếp hạng, chọn môn hoặc thao tác bên ngoài.")
        dataset = dataset if request.dataset == "auto" else request.dataset
        field = request.field or field
        text = " ".join(_tokens(request.question))
        editions = {f"qd{number} {year}" for number, year in
                    re.findall(r"\b(?:qd\s*|quyet dinh\s+)(\d{3,6})\s+(\d{4})\b", text)}
        if editions and (len(editions) > 1 or
                         (request.version and editions != {" ".join(_tokens(request.version))})):
            return self._missing(request, dataset, "Phiên bản trong câu hỏi không khớp phiên bản đã chọn.")
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
        if unsupported_request(request.question):
            return self._missing(request, dataset, "Chưa có bằng chứng phù hợp về nội dung hoặc thời điểm được hỏi.")
        program_fields = requested_program_fields(request.question)
        if dataset == "f2" and program_fields and request.field and field not in program_fields:
            return self._missing(request, "f2", "Loại dữ kiện đã chọn không khớp câu hỏi cấp chương trình/nhóm.", clarify=True)
        if code and dataset == "f2" and program_total_request(request.question):
            return self._missing(request, "f2", "Cần hỏi tổng chương trình hoặc dữ kiện một môn riêng.", clarify=True)
        if dataset == "f2" and (field in PROGRAM_FIELDS or request.group_key is not None):
            return self._program(request, code, field)
        if dataset in {"f2", "f3"} and request.version:
            # Full names are matched only within this exact major/version. Never
            # guess a code from a fuzzy/global title match.
            matches = self._matched_course_codes(request)
            if code and matches and code not in matches:
                return self._missing(request, dataset, "Tên và mã học phần không khớp; cần làm rõ môn được hỏi.", clarify=True)
            if len(matches) > 1:
                return self._missing(request, dataset, "Tên học phần chưa xác định duy nhất; cần mã môn.", clarify=True)
            code = code or next(iter(matches), None)
        # Hints select a field; they cannot make a partial answer satisfy a
        # multi-field question. No evidence is emitted until the user chooses.
        if dataset in {"f2", "f3"} and len(requested_course_fields(request.question)) > 1:
            if _verified_requested(request.question):
                return self._missing(request, dataset, "Chưa có thông tin đã xác minh cho yêu cầu chính thức/hiện hành.")
            return self._missing(request, dataset,
                                 "Mỗi lượt hỏi một loại thông tin của một môn. Bạn muốn hỏi tên, tín chỉ, "
                                 "tiên quyết, số giờ, nội dung, mục tiêu hay gợi ý đánh giá?", clarify=True)
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
        hits = supported_hits(request.question, hits, aliases=MAJOR_NAMES, codes=codes)
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

    def _matched_course_codes(self, request: HUSQuestion) -> set[str]:
        """Match exact scoped course names longest-first alongside major aliases."""
        if not request.version:
            return set()
        remaining = f" {requested_text(request.question)} "
        by_phrase: dict[str, set[str]] = {}
        for course in self.data.f2_courses(major=request.major, version=request.version):
            phrase = " ".join(_tokens(course.course["course_name"]))
            if phrase:
                by_phrase.setdefault(phrase, set()).add(course.course_code)
        for names in MAJOR_NAMES.values():
            for alias in names:
                by_phrase.setdefault(alias, set())
        for terms in COURSE_FIELD_TERMS.values():
            for term in terms:
                by_phrase.setdefault(term, set())
        matched: set[str] = set()
        for phrase in sorted(by_phrase, key=len, reverse=True):
            if f" {phrase} " in remaining:
                matched.update(by_phrase[phrase])
                remaining = remaining.replace(f" {phrase} ", " ")
        return matched

    @staticmethod
    def _missing(request, dataset, reason, *, clarify=False):
        return HUSAnswer(reply="Chưa có thông tin đủ căn cứ để trả lời. " + reason,
                         status="needs_clarification" if clarify else "no_information",
                         dataset=dataset, major=request.major, version=request.version)

    def _program(self, request: HUSQuestion, code: str | None, field: str) -> HUSAnswer:
        if _verified_requested(request.question):
            return self._missing(request, "f2", "Bản chép chương trình chưa xác nhận hiệu lực hiện hành hoặc chứng nhận của trường.")
        if code or field not in PROGRAM_FIELDS:
            return self._missing(request, "f2", "Cần chọn hỏi cấp chương trình/nhóm hoặc cấp môn riêng.", clarify=True)
        requested_fields = requested_program_fields(request.question)
        text = requested_text(request.question)
        if (not requested_fields or len(requested_fields) > 1 or field not in requested_fields
                or set(requested_course_fields(request.question)) - {"credits"}
                or _has(text, *CAREER_TERMS, "hoc tiep", "sau dai hoc",
                        "gioi thieu", "tong quan", "nen tang", "lich su hinh thanh")
                or (field == "program_credits" and _has(text.replace("ma mon", ""), "mon", "hoc phan"))):
            return self._missing(request, "f2", "Mỗi lượt hỏi một loại thông tin: tổng tín chỉ hoặc các nhóm kiến thức.", clarify=True)
        if _has(text, "nhom") and _has(text, "mon nao", "hoc phan nao", "danh sach mon", "cac mon"):
            return self._missing(request, "f2", "Phần này trả quy định/ghi chú nhóm, chưa hỗ trợ danh sách học phần theo nhóm.")
        if not request.version:
            return self._missing(request, "f2", "Cần phiên bản chương trình; không cần mã môn cho câu hỏi cấp chương trình.", clarify=True)
        program = self.data.get_f2_program(major=request.major, version=request.version)
        if program is None or (request.program_variant and program["scope"]["program_variant"] != request.program_variant):
            return self._missing(request, "f2", "Không có chương trình đúng ngành/phiên bản/hệ đã chọn.")
        if field == "program_credits" and self._matched_course_codes(request):
            return self._missing(request, "f2", "Cần hỏi tổng chương trình hoặc số tín chỉ một môn riêng.", clarify=True)
        variants = {variant for variant, terms in {"standard": ("he chuan", "chuong trinh chuan"),
                    "talent": ("tai nang",), "advanced": ("tien tien",), "high_quality": ("chat luong cao",)}.items()
                    if _has(text, *terms)}
        if variants and variants != {program["scope"]["program_variant"]}:
            return self._missing(request, "f2", "Hệ nêu trong câu hỏi không khớp chương trình đã chọn.")
        keys = question_group_keys(request.question)
        if len(keys) > 1 or (keys and request.group_key and request.group_key not in keys):
            return self._missing(request, "f2", "Cần một mã nhóm thống nhất, giữ đủ mã nhóm con như V.2.1.", clarify=True)
        key = request.group_key or next(iter(keys), None)
        if field != "group_rules" and key:
            return self._missing(request, "f2", "Cần chọn tổng chương trình, danh sách nhóm hoặc quy định một nhóm riêng.", clarify=True)
        warnings = [f"Trạng thái review: {program['catalog_review']['status']}; chưa xác minh hiệu lực hiện tại hoặc áp dụng cho từng sinh viên.",
                    "Chỉ mô tả theo nguồn; không kết luận đủ điều kiện tốt nghiệp hoặc đăng ký học phần."]
        if field == "program_credits":
            if program["credits_required"] is None:
                return self._missing(request, "f2", "Nguồn chưa ghi tổng tín chỉ yêu cầu của chương trình.")
            value = {"credits_required": program["credits_required"]}
            records, values = [program], [{**value, "note": program.get("source_note")}]
            rendered = f"Tổng tín chỉ yêu cầu theo chương trình: {value['credits_required']}."
            rendered += "\nGhi chú nguồn: " + (program.get("source_note") or "chưa ghi")
        else:
            records = list(self.data.f2_group_rules(major=request.major, version=request.version))
            if field == "group_rules":
                if not key:
                    return self._missing(request, "f2", "Cần mã nhóm, ví dụ II hoặc V.2.1; có thể hỏi danh sách các nhóm trước.", clarify=True)
                records = [row for row in records if row["group_key"] == key]
            if not records:
                return self._missing(request, "f2", "Không có nhóm này trong ngành và phiên bản đã chọn.")
            values = [{k: row.get(k) for k in ("group_key", "group_title", "source_heading", "group_note",
                                             "min_credits_if_selected", "offered_credits")} for row in records]
            value = values[0] if field == "group_rules" else values
            def shown(number):
                return "chưa ghi" if number is None else str(number)
            rendered = "\n\n".join(
                f"[{i}] Nhóm {row['group_key']}: {row['group_title']}\n"
                f"Yêu cầu tối thiểu nếu chọn: {shown(row['min_credits_if_selected'])} tín chỉ; "
                f"tín chỉ được liệt kê: {shown(row['offered_credits'])}.\n"
                f"Ghi chú nguồn: {row['group_note'] or 'chưa ghi'}." for i, row in enumerate(values, 1))
            warnings.append("Các nhóm cha/con và số liệu khác nhau được giữ riêng; không cộng hoặc tự sửa số liệu.")
        citations = [self.citation_resolver.program_record(row, val, i)
                     for i, (row, val) in enumerate(zip(records, values, strict=True), 1)]
        facts = {"program_id": program["program_id"], "scope": program["scope"], "field": field, "value": value,
                 "review_status": program["catalog_review"]["status"], "catalog_review": program["catalog_review"]}
        reply = "\n\n".join([f"{program['major_name']} ({request.version})\n{rendered}"] + warnings
                              + [citation_line(citation) for citation in citations])
        return HUSAnswer(reply=reply, status="answered", dataset="f2", major=request.major,
                         version=request.version, facts=facts, warnings=warnings, citations=citations)

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
                 "prerequisite_status": prerequisite_status(course),
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
            state_label = {"unknown": "Chưa rõ từ nguồn", "present": "Có ghi điều kiện trong nguồn",
                           "conflict": "Mâu thuẫn giữa các dòng nguồn", "unresolved": "Chưa giải quyết mã hoặc cách đọc điều kiện"}
            rendered = state_label[facts["prerequisite_status"]] + "\n" + rendered
        elif field == "course_info":
            rendered = f"Tên: {value['course_name']}; số tín chỉ: {value['credits']}"
        else:
            rendered = json.dumps(value, ensure_ascii=False) if isinstance(value, dict) else str(value)
        if course.review_status == "verified":
            warnings = ["Trạng thái: verified theo sign-off cấp dự án đã ghi trong nguồn; không phải chứng nhận của trường."]
        else:
            warnings = [f"Trạng thái xác minh: {course.review_status}; dữ kiện chép từ nguồn, chưa xác minh học vụ."]
        if facts["prerequisite_status"] == "conflict":
            warnings.append("Có mâu thuẫn điều kiện tiên quyết giữa các dòng nguồn; chưa kết luận điều kiện đúng.")
        if course.unresolved_prerequisites:
            warnings.append("Mã tiên quyết chưa giải quyết: " + ", ".join(course.unresolved_prerequisites))
        if field == "prerequisites":
            if facts["prerequisite_status"] == "unknown":
                warnings.append('Chưa đủ căn cứ để kết luận “không có tiên quyết”: ô nguồn trống vẫn là chưa rõ.')
            elif facts["prerequisite_status"] == "unresolved":
                warnings.append("Điều kiện chưa giải quyết đầy đủ; giữ nguyên dòng nguồn, không suy diễn quan hệ tiên quyết.")
            warnings.append("Thông tin theo nguồn không kết luận bạn đủ điều kiện đăng ký học phần.")
        source_lines = [citation_line(c) for c in citations]
        label = {"credits": "Số tín chỉ", "prerequisites": "Điều kiện tiên quyết theo dòng nguồn",
                 "name": "Tên học phần", "hours": "Số giờ theo nguồn", "course_info": "Thông tin học phần"}[field]
        reply = "\n\n".join([f"{code} — {course.course['course_name']} ({request.version})\n{label}: {rendered}"]
                                + warnings + source_lines)
        return HUSAnswer(reply=reply, status="answered", dataset="f2", major=request.major,
                         version=request.version, facts=facts, citations=citations, warnings=warnings)
