"""Conservative, extractive HUS answers. No provider calls or invented missing facts."""

from __future__ import annotations

import json
import re
from collections.abc import Callable
from dataclasses import dataclass

from app.hus.rag_loader import F2Course, HUSRAGData, RAGDataError
from app.hus.citations import CitationResolver, citation_line
from app.hus.retrieval import COURSE_CODE, HUSRAGRetriever, _body, _tokens
from app.hus.question_routing import (
    has as _has, assessment_fact_request as assessment_fact_request,
    is_hus_question as is_hus_question, question_intent,
    out_of_scope, requested_text, requested_course_fields, unsupported_request, verified_requested as _verified_requested,
    PROGRAM_FIELDS, CATALOG_FIELDS, CAREER_TERMS, requested_program_fields, question_group_keys, program_total_request,
    requested_program_variants, requested_name_languages, variant_enumeration_requested,
    ambiguous_major_request,
)
from app.hus.answer_support import supported_hits, training_purpose_requested
from app.hus.diagnostics import MAJOR_LABELS
from app.schemas.hus import F2PrerequisiteStatus, HUSAnswer, HUSDiagnostic, HUSQuestion


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
ASSESSMENT_NOT_FOUND = (
    'Chưa tìm thấy dữ liệu đánh giá cho học phần trong phạm vi đã chọn. '
    'Nếu muốn biết cách thi chính thức, hãy đối chiếu đề cương của học phần.'
)


@dataclass(frozen=True)
class HUSPreparedAnswer:
    """Scoped evidence and a deferred canonical presentation, with no provider I/O."""

    evidence: HUSAnswer
    render_reply: Callable[[], str]

    def materialize(self) -> HUSAnswer:
        return self.evidence.model_copy(update={'reply': self.render_reply()})


class HUSAnswerer:
    def __init__(self, data: HUSRAGData, *, asset_root=None, retriever=None, answer_policy='legacy'):
        if answer_policy not in {'legacy', 'focused'}:
            raise ValueError('Unknown answer policy')
        self.answer_policy = answer_policy
        self.data = data
        self.citation_resolver = CitationResolver(data, **({"asset_root": asset_root} if asset_root is not None else {}))
        self.retriever = HUSRAGRetriever(data) if retriever is None else retriever
        self.programs = data.program_scopes()

    def answer(self, request: HUSQuestion) -> HUSAnswer:
        return self.prepare_evidence(request).materialize()

    def prepare_evidence(self, request: HUSQuestion) -> HUSPreparedAnswer:
        """Select checked sources before constructing extractive F1/F3 prose."""
        selected = self._answer(request)
        if isinstance(selected, HUSPreparedAnswer):
            answer, render = selected.evidence, selected.render_reply
        else:
            answer, render = selected, lambda: selected.reply
        identity = self.data.release_identity
        evidence = answer.model_copy(update={"release_id": identity["release_id"],
                                            "release_sha256": identity["release_sha256"],
                                            "generated_reference_allowed": request.allow_generated_reference})
        return HUSPreparedAnswer(evidence, render)

    def _answer(self, request: HUSQuestion) -> HUSAnswer | HUSPreparedAnswer:
        if request.source_id and self.answer_policy != 'focused':
            return self._missing(request, None, 'Chọn nguồn cụ thể cần chế độ trả lời focused.', clarify=True)
        dataset, field = question_intent(request.question)
        if self.answer_policy == 'focused' and dataset is None:
            from app.hus.focused import focused_content_request

            if focused_content_request(request.question):
                dataset, field = 'f3', 'content'
        # Request hints never authorize actions outside the standalone Q&A scope.
        if out_of_scope(request.question):
            return self._missing(request, dataset, "Phạm vi hỏi đáp không hỗ trợ xếp hạng, chọn môn hoặc thao tác bên ngoài.",
                                 diagnostic_code='unsupported_operation')
        dataset = dataset if request.dataset == "auto" else request.dataset
        field = request.field or field
        text = " ".join(_tokens(request.question))
        editions = {f"qd{number} {year}" for number, year in
                    re.findall(r"\b(?:qd\s*|quyet dinh\s+)(\d{3,6})\s+(\d{4})\b", text)}
        if editions and (len(editions) > 1 or
                         (request.version and editions != {" ".join(_tokens(request.version))})):
            return self._missing(request, dataset, "Phiên bản trong câu hỏi không khớp phiên bản đã chọn.", diagnostic_code='scope_conflict')
        codes = {t.upper() for t in _tokens(request.question) if COURSE_CODE.fullmatch(t)}
        if len(codes) > 1 or (codes and request.course_code and request.course_code not in codes):
            return self._missing(request, dataset, "Cần một mã học phần thống nhất cho mỗi câu hỏi.",
                                 clarify=True, diagnostic_code='unsupported_operation')
        code = request.course_code or next(iter(codes), None)
        if request.version and (dataset == 'f2' or (dataset is None and code)):
            program = self.data.get_f2_program(major=request.major, version=request.version)
            variants = requested_program_variants(request.question)
            selected = request.program_variant
            if program and ((selected and selected != program['scope']['program_variant'])
                    or (variants and variants != {program['scope']['program_variant']})):
                return self._missing(request, dataset, 'Hệ trong câu hỏi/phạm vi đã chọn không khớp '
                                     'chương trình của ngành và phiên bản đang tra cứu.',
                                     diagnostic_code='scope_conflict')
        # Consume longer names first: Toan hoc va Tin hoc is not a second Math major.
        named, mentioned = f" {text} ", set()
        aliases = sorted(((name, major) for major, names in MAJOR_NAMES.items() for name in names),
                         key=lambda item: (item[0].startswith("nganh "), -len(item[0])))
        for name, major in aliases:
            if f" {name} " in named:
                mentioned.add(major)
                named = named.replace(f" {name} ", " ")
        if mentioned and mentioned != {request.major}:
            target = next(iter(mentioned)) if len(mentioned) == 1 else None
            reason = (f"Bạn đang chọn {MAJOR_LABELS[request.major]} nhưng câu hỏi nhắc đến "
                      f"{MAJOR_LABELS[target]}. Hãy chọn {MAJOR_LABELS[target]} ở ô ngành rồi hỏi lại."
                      if target else 'Câu hỏi nhắc đến nhiều ngành. Hãy chọn và hỏi một ngành mỗi lượt.')
            return self._missing(request, dataset, reason, diagnostic_code='scope_conflict', suggested_major=target)
        if unsupported_request(request.question):
            return self._missing(request, dataset, "Chưa có bằng chứng phù hợp về nội dung hoặc thời điểm được hỏi.")
        if request.dataset == 'auto' and request.field is None and ambiguous_major_request(request.question):
            return self._missing(request, 'f1',
                'Bạn muốn hỏi giới thiệu/mục tiêu ngành, định hướng nghề nghiệp hay danh mục môn trong chương trình? '
                'Nếu hỏi một môn, hãy ghi tên đầy đủ hoặc mã môn.', clarify=True)
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
            matches = {c.course_code for c in self.data.f2_courses(major=request.major, version=request.version)
                       if _has(requested_text(request.question), " ".join(_tokens(c.course["course_name"])))}
            if code and matches and code not in matches:
                return self._missing(request, dataset, "Tên và mã học phần không khớp; cần làm rõ môn được hỏi.", clarify=True)
            if len(matches) > 1:
                return self._missing(request, dataset, "Tên học phần chưa xác định duy nhất; cần mã môn.", clarify=True)
            code = code or next(iter(matches), None)
        routing_question = self._content_topic_question(request, code)
        if routing_question != request.question:
            topic_dataset, topic_field = question_intent(routing_question)
            dataset = topic_dataset if request.dataset == 'auto' else request.dataset
            field = request.field or topic_field
        # Hints select a field; they cannot make a partial answer satisfy a
        # multi-field question. No evidence is emitted until the user chooses.
        if dataset in {"f2", "f3"} and len(requested_course_fields(routing_question)) > 1:
            if _verified_requested(request.question):
                return self._missing(request, dataset, "Chưa có thông tin đã xác minh cho yêu cầu chính thức/hiện hành.")
            return self._missing(request, dataset,
                                 "Mỗi lượt hỏi một loại thông tin của một môn. Bạn muốn hỏi tên, tín chỉ, "
                                 "tiên quyết, số giờ, nội dung, mục tiêu hay gợi ý đánh giá?", clarify=True,
                                 diagnostic_code='unsupported_operation')
        if dataset == "f2":
            if field is None and not _has(text, "thong tin", "la mon gi", "la gi"):
                return self._missing(request, dataset, "Chưa xác định được trường dữ kiện được hỏi.", diagnostic_code='routing_unknown')
            return self._f2(request, code, field or "course_info")
        if dataset not in {"f1", "f3"}:
            count = _has(text, 'nganh', 'chuong trinh', 'ctdt') and _has(
                text, 'bao nhieu mon', 'so mon hoc', 'so hoc phan', 'dem mon', 'dem hoc phan')
            return self._missing(request, None,
                'Hiện chưa hỗ trợ đếm môn trong chương trình; đây không phải lỗi Gemini hoặc thiếu lượt gọi.' if count
                else 'Chưa hiểu loại thông tin bạn muốn hỏi. Hãy nêu rõ ngành/môn và nội dung cần biết.',
                diagnostic_code='unsupported_operation' if count else 'routing_unknown')
        if _verified_requested(request.question) or field == "official_assessment":
            return self._missing(request, dataset, "Chưa có thông tin đã xác minh cho yêu cầu chính thức/hiện hành."
                                 + (" F3 hiện có là nội dung tham khảo do AI sinh." if dataset == "f3" else ""))
        if dataset == "f3" and not code:
            return self._missing(request, dataset, "Cần mã học phần để tránh nhầm nội dung giữa các môn.", clarify=True)
        if dataset == "f3":
            if request.version and self.data.get_f2_course(code, major=request.major, version=request.version) is None:
                return self._missing(request, dataset, "Không có môn này trong ngành và phiên bản đã chọn.")
            if not request.allow_generated_reference:
                return self._missing(request, dataset, "Cần bật cho phép kiến thức AI tham khảo để dùng dữ liệu F3 AI sinh.",
                                     clarify=True, diagnostic_code='permission_required')
        allowed = {"introduction", "careers", "further_study", "objectives"} if dataset == "f1" else {
            "content", "objectives", "suggested_assessment"}
        if field not in allowed:
            return self._missing(request, dataset, "Chưa xác định được loại thông tin phù hợp trong dữ liệu.")
        variant = request.program_variant
        if dataset == 'f1':
            variants = requested_program_variants(request.question)
            enumeration = (field == 'introduction' and variant is None
                           and variant_enumeration_requested(request.question))
            if not enumeration and (len(variants) > 1 or (variants and variant and variant not in variants)):
                return self._missing(request, dataset, "Cần một hệ đào tạo thống nhất giữa câu hỏi và phạm vi đã chọn.",
                                     clarify=True)
            if not enumeration:
                variant = next(iter(variants), variant)
        query = request.question
        focus, selected_source = None, None
        if self.answer_policy == 'focused':
            from app.hus.focused import focus_request, resolve_sources

            inventory = self.data.chunks(dataset, major=request.major, version=request.version,
                course_code=code, field=field, program_variant=variant,
                allow_generated=request.allow_generated_reference)
            selection = resolve_sources(inventory, request, variant, self._source_format_supported)
            if selection.choices:
                answer = self._missing(request, dataset,
                    'Có nhiều nguồn/phiên bản/hệ phù hợp. Hãy chọn một nguồn để tránh trộn thông tin.', clarify=True)
                return answer.model_copy(update={'source_choices': list(selection.choices)})
            if not selection.chunks:
                if field == 'suggested_assessment' and not inventory:
                    return self._missing(request, dataset, ASSESSMENT_NOT_FOUND, diagnostic_code='retrieval_empty')
                return self._missing(request, dataset, 'Không có nguồn đúng phiên bản/hệ/nguồn đã chọn.')
            selected_source = selection.chunks
            focus = focus_request(request, selected_source, field)
            if not focus.valid:
                return self._missing(request, dataset, 'Chưa đủ bằng chứng cho mọi ý hoặc điều kiện được hỏi.',
                                     diagnostic_code='evidence_rejected')
            query = focus.guard_question
            if focus.related_only:
                query += ' quá khớp điều chuẩn ghi nhớ nhiễu'
        if dataset == 'f1' and field == 'objectives' and training_purpose_requested(query):
            query += ' nhằm mục tiêu chung'
        selection_options = {}
        search_version, search_variant = request.version, variant
        if selected_source is not None:
            selection_options['parent_ids'] = tuple(c.chunk_id for c in selected_source)
            search_version = selected_source[0].version
            search_variant = selected_source[0].metadata.get('program_variant')
        hits = self.retriever.search(query, dataset=dataset, major=request.major,
                                     version=search_version, course_code=code, field=field,
                                     program_variant=search_variant, top_k=5,
                                     allow_generated=request.allow_generated_reference, **selection_options)
        retrieved_any = bool(hits)
        if selected_source is not None:
            canonical = {c.chunk_id: c for c in selected_source}
            if any(h.chunk.chunk_id not in canonical or h.chunk != canonical[h.chunk.chunk_id] for h in hits):
                raise RAGDataError('Retriever changed the selected canonical source')
        def source_catalog():
            if selected_source is not None:
                return selected_source
            return self.data.chunks(dataset, major=request.major, version=request.version,
                course_code=code, field=field, program_variant=variant,
                allow_generated=request.allow_generated_reference)

        if focus and focus.whole:
            from app.hus.retrieval import RetrievalHit

            hits = tuple(RetrievalHit(c, 0.0, ()) for c in selected_source)
        if focus and focus.topics:
            from app.hus.focused import select_focus_hits

            hits = select_focus_hits(hits, focus)
        else:
            hits = supported_hits(focus.guard_question if focus else request.question,
                hits, aliases=MAJOR_NAMES, codes=codes,
                format_supported=self._source_format_supported, source_catalog=source_catalog)
        if not hits:
            if field == 'suggested_assessment' and not retrieved_any:
                return self._missing(request, dataset, ASSESSMENT_NOT_FOUND, diagnostic_code='retrieval_empty')
            return self._missing(request, dataset,
                'Đã tìm thấy đoạn liên quan nhưng chưa đủ căn cứ cho đúng yêu cầu/điều kiện trong câu hỏi. Hãy làm rõ ý cần hỏi.'
                if retrieved_any else 'Chưa tìm thấy đoạn dữ liệu phù hợp. Hãy kiểm tra tên/mã môn hoặc hỏi cụ thể hơn.',
                diagnostic_code='evidence_rejected' if retrieved_any else 'retrieval_empty')
        citations, warnings = [], []
        for i, hit in enumerate(hits, 1):
            chunk, meta = hit.chunk, hit.chunk.metadata
            citations.append(self.citation_resolver.chunk(chunk, _body(chunk), i))
            if dataset == "f3":
                warnings.append(meta["warning"])
            elif meta["review_status"] == "include_markdown":
                warnings.append("Nguồn được duyệt trên Markdown; chưa đối chiếu PDF/DOCX gốc.")
        warnings = list(dict.fromkeys(warnings))
        if dataset == "f1":
            warnings.append("Chỉ mô tả theo nguồn đã lưu; chưa xác minh hiệu lực hiện tại.")
        focus_plan = None
        if focus is not None:
            from app.hus.focused import build_plan

            focus_plan = build_plan(request, hits, focus, self.data.release_identity)
        def render_reply():
            if focus_plan is not None:
                from app.hus.focused import render_plan

                return '\n\n'.join([*warnings, render_plan(focus_plan),
                    *(citation_line(c) for c in citations)])
            excerpts = []
            for hit, citation in zip(hits, citations, strict=True):
                source = citation_line(citation) + f"; phiên bản: {hit.chunk.version}"
                if hit.chunk.metadata.get('program_variant'):
                    source += f"; hệ: {hit.chunk.metadata['program_variant']}"
                excerpts.append(f"[{citation.citation_id}] {citation.quote}\n{source}")
            return '\n\n'.join(warnings + excerpts)

        evidence = HUSAnswer(reply='', status="answered", dataset=dataset, major=request.major,
                             version=request.version, citations=citations, warnings=warnings, focus_plan=focus_plan)
        return HUSPreparedAnswer(evidence, render_reply)

    def _content_topic_question(self, request: HUSQuestion, code: str | None) -> str:
        """A known unit title is data; leave any additional request intact."""
        if (not code or not request.allow_generated_reference
                or not _has(requested_text(request.question), 'noi dung', 'chu de')):
            return request.question
        question = request.question
        for chunk in self.data.chunks('f3', major=request.major, version=request.version,
                                      course_code=code, field='content', allow_generated=True):
            if type(chunk.metadata.get('unit_index')) is not int:
                continue
            title = _body(chunk).splitlines()[0].strip()
            if title:
                question = re.sub(r'(?<!\w)' + re.escape(title) + r'(?!\w)',
                                  'chủ đề đã chọn', question, flags=re.IGNORECASE)
        return question

    def _source_format_supported(self, hit, kind: str) -> bool:
        """Source selectors require available resolver evidence, not a filename."""
        meta = hit.chunk.metadata
        locator = meta.get('locator')
        if not meta.get('document_id') or not isinstance(locator, dict) or not locator.get('evidence_path'):
            return False
        citation = self.citation_resolver.chunk(hit.chunk, _body(hit.chunk), 1)
        if (citation.availability != 'available' or citation.source_id != meta['document_id']
                or not citation.document_sha256):
            return False
        if kind == 'pdf':
            return (citation.evidence_kind == 'pdf' and citation.media_type == 'application/pdf'
                    and citation.pdf_page is not None and bool(citation.pdf_pages))
        return (kind == 'docx' and citation.evidence_kind == 'file'
                and citation.media_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document')

    @staticmethod
    def _missing(request, dataset, reason, *, clarify=False, diagnostic_code=None, suggested_major=None):
        return HUSAnswer(reply="Chưa có thông tin đủ căn cứ để trả lời. " + reason,
                         status="needs_clarification" if clarify else "no_information",
                         dataset=dataset, major=request.major, version=request.version,
                         diagnostic=HUSDiagnostic(code=diagnostic_code or (
                             'clarification_required' if clarify else 'evidence_unavailable'),
                             suggested_major=suggested_major))

    def _program(self, request: HUSQuestion, code: str | None, field: str) -> HUSAnswer:
        if _verified_requested(request.question):
            return self._missing(request, "f2", "Bản chép chương trình chưa xác nhận hiệu lực hiện hành hoặc chứng nhận của trường.")
        if code or field not in PROGRAM_FIELDS:
            return self._missing(request, "f2", "Cần chọn hỏi cấp chương trình/nhóm hoặc cấp môn riêng.", clarify=True)
        requested_fields = requested_program_fields(request.question)
        text = requested_text(request.question)
        if ((not requested_fields and field not in CATALOG_FIELDS) or len(requested_fields) > 1
                or (requested_fields and field not in requested_fields)
                or (field not in CATALOG_FIELDS and set(requested_course_fields(request.question)) - {"credits"})
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
        if field == "program_credits" and any(
                _has(text, " ".join(_tokens(course.course["course_name"])))
                for course in self.data.f2_courses(major=request.major, version=request.version)):
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
        if field in CATALOG_FIELDS:
            from app.hus.program_catalog import catalog_answer

            return catalog_answer(self, request, program, field, MAJOR_NAMES)
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
        if field in {'name', 'course_info'} and 'anh' in requested_name_languages(request.question):
            return self._missing(request, 'f2', 'Trường tên hiện có chưa cung cấp tên tiếng Anh được hỏi.')
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
