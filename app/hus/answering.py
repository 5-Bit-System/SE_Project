"""Conservative, extractive HUS answers. No provider calls or invented missing facts."""

from __future__ import annotations

from typing import Any
import json
import re

from app.hus.rag_loader import F2Course, HUSRAGData
from app.hus.citations import CitationResolver, citation_line
from app.hus.course_aliases import COURSE_ALIAS_MAP, match_scoped_courses, resolve_course_details
from app.hus.retrieval import COURSE_CODE, HUSRAGRetriever, _body, _tokens
from app.hus.question_routing import (
    has as _has, assessment_fact_request as assessment_fact_request,
    is_hus_question as is_hus_question, question_intent as _rule_question_intent,
    out_of_scope, requested_text, requested_course_fields, unsupported_request, verified_requested as _verified_requested,
    COURSE_FIELD_TERMS, COURSE_OVERVIEW_TERMS, PROGRAM_FIELDS, CAREER_TERMS, requested_program_fields, question_group_keys, program_total_request,
)
from app.hus.answer_support import supported_hits
from app.hus.semantic_routing import rank_top_k_chunks, semantic_question_intent
from app.schemas.hus import (
    F2PrerequisiteStatus,
    HUSAnswer,
    HUSQuestion,
    HUSRetrievalBundle,
    HUSRetrievedChunk,
)


def question_intent(question: str) -> tuple[str | None, str | None]:
    """Route question intent with curriculum-framework and course-alias awareness."""
    dataset, field = _rule_question_intent(question)
    if out_of_scope(question):
        return None, None
    req_text = requested_text(question)
    if not req_text:
        return dataset, field
    has_alias = _has(req_text, *COURSE_ALIAS_MAP.keys())
    has_code = any(COURSE_CODE.fullmatch(t) for t in _tokens(req_text))
    if (
        dataset == "f1"
        and field == "objectives"
        and (has_alias or has_code)
        and not _has(
            req_text,
            "muc tieu nganh",
            "muc tieu chuong trinh",
            "muc tieu dao tao cua nganh",
            "chuan dau ra cua nganh",
        )
    ):
        return "f3", "objectives"
    if (
        (
            dataset is None
            or (
                dataset == "f1"
                and field == "introduction"
                and not _has(req_text, "nganh", "chuong trinh", "ctdt", "khoa")
            )
        )
        and (has_alias or has_code)
        and _has(req_text, *COURSE_OVERVIEW_TERMS)
    ):
        return "f3", "content"
    if (
        not has_alias
        and not has_code
        and _has(req_text, "khung chuong trinh", "khung dao tao")
        and _has(req_text, "khoi", "nhom", "cau truc", "phan bo", "chia thanh")
        and not _has(req_text, *CAREER_TERMS)
    ):
        return "f2", "program_groups"
    return dataset, field


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
        alias_matches, alias_tokens = (
            self._matched_courses_with_aliases(request) if request.version else (set(), set())
        )
        req_text = requested_text(request.question)
        if request.dataset == "auto" and request.field is None:
            if (
                dataset == "f1"
                and field == "objectives"
                and (code or alias_matches)
                and not _has(
                    req_text,
                    "muc tieu nganh",
                    "muc tieu chuong trinh",
                    "muc tieu dao tao cua nganh",
                    "chuan dau ra cua nganh",
                )
            ):
                dataset, field = "f3", "objectives"
            elif (
                not code
                and not alias_matches
                and _has(req_text, "khung chuong trinh", "khung dao tao")
                and _has(req_text, "khoi", "nhom", "cau truc", "phan bo", "chia thanh")
                and not _has(req_text, *CAREER_TERMS)
            ):
                dataset, field = "f2", "program_groups"
            elif (
                (
                    dataset is None
                    or (
                        dataset == "f1"
                        and field == "introduction"
                        and not _has(req_text, "nganh", "chuong trinh", "ctdt", "khoa", "nen tang", "lich su hinh thanh")
                    )
                )
                and (code or alias_matches)
                and not _verified_requested(request.question)
            ):
                sem_ds, sem_field, _ = semantic_question_intent(
                    request.question,
                    has_course=True,
                    threshold=0.52,
                )
                if sem_ds is not None:
                    dataset, field = sem_ds, sem_field
                elif _has(req_text, *COURSE_OVERVIEW_TERMS):
                    dataset, field = "f3", "content"
        program_fields = requested_program_fields(request.question)
        if dataset == "f2" and program_fields and request.field and field not in program_fields:
            return self._missing(request, "f2", "Loại dữ kiện đã chọn không khớp câu hỏi cấp chương trình/nhóm.", clarify=True)
        if code and dataset == "f2" and program_total_request(request.question):
            return self._missing(request, "f2", "Cần hỏi tổng chương trình hoặc dữ kiện một môn riêng.", clarify=True)
        if dataset == "f2" and (field in PROGRAM_FIELDS or request.group_key is not None):
            return self._program(request, code, field)
        if dataset in {"f2", "f3"} and request.version:
            # Full names and scoped aliases are matched only within this exact
            # major/version. Never guess a code from a fuzzy/global title match.
            matches = alias_matches
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
        if not hits and alias_tokens and code:
            hits = self.retriever.search(f"{request.question} {code}", dataset=dataset, major=request.major,
                                         version=request.version, course_code=code, field=field,
                                         program_variant=request.program_variant, top_k=5,
                                         allow_generated=request.allow_generated_reference)
        hits = supported_hits(
            request.question,
            hits,
            aliases=MAJOR_NAMES,
            codes=codes | ({code} if code else set()),
            extra_neutral=alias_tokens,
        )
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

    def _matched_courses_with_aliases(self, request: HUSQuestion) -> tuple[set[str], set[str]]:
        """Match exact scoped course names and abbreviations longest-first alongside major aliases."""
        if not request.version:
            return set(), set()
        return match_scoped_courses(
            request.question,
            self.data.f2_courses(major=request.major, version=request.version),
            major_aliases=MAJOR_NAMES,
            field_terms=COURSE_FIELD_TERMS,
        )

    def _matched_course_codes(self, request: HUSQuestion) -> set[str]:
        """Match exact scoped course names and abbreviations longest-first alongside major aliases."""
        return self._matched_courses_with_aliases(request)[0]

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
        if (
            not requested_fields
            and field == "program_groups"
            and _has(text, "khung chuong trinh", "khung dao tao")
            and _has(text, "khoi", "nhom", "cau truc", "phan bo", "chia thanh")
        ):
            requested_fields = ("program_groups",)
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

    def retrieve_context(self, request: HUSQuestion, *, top_k: int = 5) -> HUSRetrievalBundle:
        """Retrieve ranked Top-K evidence chunks alongside structured F2 facts and intent metadata."""
        if type(top_k) is not int or not 1 <= top_k <= 20:
            raise ValueError("top_k must be an integer between 1 and 20")

        norm_q = requested_text(request.question) or " ".join(_tokens(request.question))
        default_versions = {ver for maj, ver in self.programs.values() if maj == request.major}
        version = request.version or next(
            (ver for maj, ver in self.programs.values() if maj == request.major),
            None,
        )

        scoped_courses = self.data.f2_courses(major=request.major, version=version) if version else ()
        resolved_courses = resolve_course_details(
            request.question,
            scoped_courses,
            major_aliases=MAJOR_NAMES,
            field_terms=COURSE_FIELD_TERMS,
        )
        _, alias_tokens = match_scoped_courses(
            request.question,
            scoped_courses,
            major_aliases=MAJOR_NAMES,
            field_terms=COURSE_FIELD_TERMS,
        )
        if request.course_code:
            existing_codes = {item["course_code"] for item in resolved_courses}
            if request.course_code not in existing_codes and version:
                explicit_course = self.data.get_f2_course(
                    request.course_code, major=request.major, version=version
                )
                if explicit_course is not None:
                    resolved_courses.append(
                        {
                            "course_code": explicit_course.course_code,
                            "course_name": explicit_course.course["course_name"],
                            "match_type": "code",
                        }
                    )
                    resolved_courses.sort(key=lambda item: item["course_code"])

        if request.course_code and (
            not resolved_courses
            or (len(resolved_courses) == 1 and resolved_courses[0]["course_code"] == request.course_code)
        ):
            resolved_course_code = request.course_code
        elif len(resolved_courses) == 1:
            resolved_course_code = resolved_courses[0]["course_code"]
        else:
            resolved_course_code = None

        has_course = bool(resolved_course_code or resolved_courses)
        if out_of_scope(request.question):
            dataset, field, intent_source, intent_confidence = None, None, "none", 0.0
        elif request.dataset != "auto" or request.field is not None:
            rule_ds, rule_field = question_intent(request.question)
            if request.dataset != "auto":
                dataset = request.dataset
                field = request.field or (rule_field if rule_ds == dataset else None)
            else:
                field = request.field
                if field in PROGRAM_FIELDS or field in {"credits", "prerequisites", "name", "hours", "course_info"}:
                    dataset = "f2"
                elif field in {"introduction", "careers", "further_study"}:
                    dataset = "f1"
                elif field in {"content", "suggested_assessment", "official_assessment"}:
                    dataset = "f3"
                elif field == "objectives":
                    dataset = "f3" if has_course else "f1"
                else:
                    dataset = rule_ds
            intent_source = "explicit"
            intent_confidence = 1.0
        else:
            rule_ds, rule_field = question_intent(request.question)
            if (
                rule_ds == "f1"
                and rule_field == "objectives"
                and has_course
                and not _has(
                    norm_q,
                    "muc tieu nganh",
                    "muc tieu chuong trinh",
                    "muc tieu dao tao cua nganh",
                    "chuan dau ra cua nganh",
                )
            ):
                rule_ds, rule_field = "f3", "objectives"
            elif (
                not has_course
                and _has(norm_q, "khung chuong trinh", "khung dao tao")
                and _has(norm_q, "khoi", "nhom", "cau truc", "phan bo", "chia thanh")
                and not _has(norm_q, *CAREER_TERMS)
            ):
                rule_ds, rule_field = "f2", "program_groups"

            bare_intro_fallback = (
                rule_ds == "f1"
                and rule_field == "introduction"
                and not _has(norm_q, "gioi thieu", "tong quan", "nen tang", "lich su hinh thanh")
            )
            if rule_ds is not None and not bare_intro_fallback:
                dataset, field = rule_ds, rule_field
                intent_source = "rule"
                intent_confidence = 1.0
            else:
                sem_ds, sem_field, sem_score = semantic_question_intent(
                    request.question,
                    has_course=has_course,
                    threshold=0.38,
                )
                if sem_ds is not None:
                    dataset, field = sem_ds, sem_field
                    intent_source = "semantic"
                    intent_confidence = sem_score
                elif rule_ds is not None:
                    dataset, field = rule_ds, rule_field
                    intent_source = "rule"
                    intent_confidence = 1.0
                else:
                    dataset = "f3" if (resolved_course_code and request.allow_generated_reference) else "f1"
                    field = None
                    intent_source = "broad_fallback"
                    intent_confidence = round(sem_score, 4)

        structured_data: dict[str, Any] = {}
        if resolved_course_code and version:
            course = self.data.get_f2_course(resolved_course_code, major=request.major, version=version)
            if course is not None:
                credits_rows = [r.get("credits_in_source") for r in course.source_rows]
                credits_val = (
                    credits_rows[0]
                    if credits_rows and all(v is not None for v in credits_rows) and len(set(credits_rows)) == 1
                    else course.course.get("credits")
                )
                prereqs_named = []
                for p in course.prerequisites:
                    p_code = p.get("prerequisite_course_code") if isinstance(p, dict) else str(p)
                    if p_code:
                        p_course = self.data.get_f2_course(p_code, major=request.major, version=version)
                        p_name = p_course.course.get("course_name") if p_course else None
                        prereqs_named.append({"course_code": p_code, "course_name": p_name})

                dependent_courses = []
                for scoped_c in self.data.f2_courses(major=request.major, version=version):
                    for r in scoped_c.source_rows:
                        prereq_text = r.get("prerequisite_source_text") or ""
                        if course.course_code in prereq_text:
                            dependent_courses.append({
                                "course_code": scoped_c.course_code,
                                "course_name": scoped_c.course.get("course_name"),
                            })
                            break

                structured_data["course"] = {
                    "course_code": course.course_code,
                    "course_name": course.course.get("course_name"),
                    "credits": credits_val,
                    "hours": course.course_metadata.get("values", {}).get("hours"),
                    "prerequisites_raw": [r.get("prerequisite_source_text") for r in course.source_rows],
                    "prerequisite_groups": list(course.prerequisites),
                    "prerequisites_named": prereqs_named,
                    "prerequisite_status": prerequisite_status(course),
                    "dependent_courses": dependent_courses,
                    "review_status": course.review_status,
                }
        elif len(resolved_courses) > 1:
            structured_data["candidate_courses"] = resolved_courses

        if version and ((dataset == "f2" and field in PROGRAM_FIELDS) or resolved_course_code is None):
            program = self.data.get_f2_program(major=request.major, version=version)
            if program is not None:
                groups = list(self.data.f2_group_rules(major=request.major, version=version))
                group_keys = question_group_keys(request.question)
                if request.group_key:
                    group_keys = {request.group_key}
                filtered_groups = (
                    [g for g in groups if g.get("group_key") in group_keys]
                    if (field == "group_rules" and group_keys)
                    else groups
                )
                program_summary: dict[str, Any] = {
                    "program_id": program.get("program_id"),
                    "major_name": program.get("major_name"),
                    "version": version,
                    "credits_required": program.get("credits_required"),
                    "source_note": program.get("source_note"),
                    "review_status": program.get("catalog_review", {}).get("status"),
                }
                if field in {"program_groups", "group_rules"} or group_keys:
                    program_summary["group_rules"] = [
                        {
                            k: row.get(k)
                            for k in (
                                "group_key",
                                "group_title",
                                "source_heading",
                                "group_note",
                                "min_credits_if_selected",
                                "offered_credits",
                            )
                        }
                        for row in filtered_groups
                    ]
                structured_data["program"] = program_summary

        top_k_chunks: list[HUSRetrievedChunk] = []
        if intent_source != "none":
            if dataset == "f3" and request.allow_generated_reference:
                search_dataset = "f3"
                search_field = field if field in {"content", "objectives", "suggested_assessment"} else None
                chunk_version = version
                chunk_course = resolved_course_code
            elif dataset == "f1":
                search_dataset = "f1"
                search_field = field if field in {"introduction", "careers", "further_study", "objectives"} else None
                chunk_version = None if version in default_versions else version
                chunk_course = None
            elif resolved_course_code and request.allow_generated_reference:
                search_dataset = "f3"
                search_field = None
                chunk_version = version
                chunk_course = resolved_course_code
            else:
                search_dataset = "f1"
                search_field = None
                chunk_version = None if version in default_versions else version
                chunk_course = None

            search_query = (
                f"{request.question} {chunk_course}"
                if (chunk_course and alias_tokens)
                else request.question
            )
            retriever_top_k = top_k if isinstance(self.retriever, HUSRAGRetriever) else 5
            base_hits = self.retriever.search(
                search_query,
                dataset=search_dataset,
                major=request.major,
                version=chunk_version,
                course_code=chunk_course,
                field=search_field,
                program_variant=request.program_variant,
                top_k=retriever_top_k,
                allow_generated=request.allow_generated_reference,
            )
            primary_candidates = self.data.chunks(
                search_dataset,
                major=request.major,
                version=chunk_version,
                course_code=chunk_course,
                field=search_field,
                program_variant=request.program_variant,
                allow_generated=request.allow_generated_reference,
            )
            ranked_hits = rank_top_k_chunks(
                search_query,
                primary_candidates,
                top_k=top_k,
                base_hits=base_hits,
            )
            if search_field is not None and len(ranked_hits) < top_k:
                broader_candidates = self.data.chunks(
                    search_dataset,
                    major=request.major,
                    version=chunk_version,
                    course_code=chunk_course,
                    field=None,
                    program_variant=request.program_variant,
                    allow_generated=request.allow_generated_reference,
                )
                ranked_hits = rank_top_k_chunks(
                    search_query,
                    broader_candidates,
                    top_k=top_k,
                    base_hits=ranked_hits,
                )

            codes_set = {t.upper() for t in _tokens(request.question) if COURSE_CODE.fullmatch(t)}
            if resolved_course_code:
                codes_set.add(resolved_course_code)
            gate_candidates = (
                tuple(h for h in ranked_hits if h.chunk.metadata.get("field") == search_field)
                if search_field is not None
                else ranked_hits
            )
            supported = (
                supported_hits(
                    request.question,
                    gate_candidates,
                    aliases=MAJOR_NAMES,
                    codes=codes_set,
                    extra_neutral=alias_tokens,
                )
                if dataset in {"f1", "f3"}
                else ()
            )
            supported_ids = {h.chunk.chunk_id for h in supported}

            for idx, hit in enumerate(ranked_hits, 1):
                chunk = hit.chunk
                meta = chunk.metadata
                body_str = _body(chunk)
                citation = self.citation_resolver.chunk(chunk, body_str, idx)
                top_k_chunks.append(
                    HUSRetrievedChunk(
                        rank=idx,
                        chunk_id=chunk.chunk_id,
                        dataset=chunk.dataset,
                        major=chunk.major,
                        version=chunk.version,
                        field=meta.get("field"),
                        course_code=meta.get("course_code"),
                        course_name=meta.get("course_name"),
                        title=meta.get("title"),
                        body=body_str,
                        score=round(float(hit.score), 6),
                        matched_terms=list(hit.matched_terms),
                        passed_support_gate=chunk.chunk_id in supported_ids,
                        review_status=meta.get("review_status"),
                        content_origin=meta.get("content_origin"),
                        citation=citation,
                    )
                )

        identity = self.data.release_identity
        return HUSRetrievalBundle(
            question=request.question,
            normalized_question=norm_q,
            major=request.major,
            version=version,
            dataset=dataset,
            field=field,
            intent_source=intent_source,
            intent_confidence=intent_confidence,
            resolved_course_code=resolved_course_code,
            resolved_courses=resolved_courses,
            top_k=top_k,
            top_k_chunks=top_k_chunks,
            structured_data=structured_data,
            release_id=identity["release_id"],
            release_sha256=identity["release_sha256"],
        )

