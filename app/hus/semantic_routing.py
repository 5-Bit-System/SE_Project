"""Semantic intent routing and multi-signal top-k chunk ranking for HUS RAG.

Provides a lightweight, deterministic semantic layer over Vietnamese academic
queries using word token/bigram TF-IDF cosine similarity and character 3/4-gram
similarity against canonical anchor intents, plus multi-signal chunk ranking.
"""

from __future__ import annotations

import math
from collections import Counter
from collections.abc import Sequence

from app.hus.question_routing import (
    COURSE_CODE,
    has,
    out_of_scope,
    question_group_keys,
    requested_text,
)
from app.hus.rag_loader import RAGChunk
from app.hus.retrieval import FIELD_LABELS, STOP_WORDS, RetrievalHit, _body, _terms, _tokens

# Query glue tokens that appear across all question types and should not drive intent similarity alone.
QUERY_GLUE = STOP_WORDS | frozenset(
    "hoi cho biet xin vui long nhe nhi vay a ha oi giup em voi nganh mon hoc phan "
    "chuong trinh dao tao ctdt khoa truong dai hoc khoa hoc tu nhien hus".split()
)

COURSE_LEVEL_INTENTS: frozenset[tuple[str, str]] = frozenset({
    ("f2", "credits"),
    ("f2", "prerequisites"),
    ("f2", "hours"),
    ("f2", "name"),
    ("f3", "content"),
    ("f3", "objectives"),
    ("f3", "suggested_assessment"),
})

PROGRAM_ONLY_WHEN_COURSE_INTENTS: frozenset[tuple[str, str]] = frozenset({
    ("f1", "careers"),
    ("f1", "introduction"),
    ("f1", "objectives"),
    ("f2", "program_credits"),
})

ANCHOR_INTENTS: tuple[tuple[str, str, tuple[str, ...]], ...] = (
    (
        "f2",
        "credits",
        (
            "mon nay nang may tin",
            "khoi luong hoc tap cua mon la bao nhieu tin chi",
            "tich luy bao nhieu tin chi khi hoc mon nay",
            "hoc phan nay tinh may tc",
            "mon hoc co so tin chi la bao nhieu",
            "dang ky hoc phan nay duoc tinh may tin",
        ),
    ),
    (
        "f2",
        "prerequisites",
        (
            "can qua mon gi truoc khi dang ky",
            "dieu kien bat buoc de hoc mon nay",
            "phai hoan thanh hoc phan nao truoc",
            "mon hoc tien quyet bat buoc la gi",
            "yeu cau hoc truoc nhung hoc phan nao",
            "chua hoc mon nao thi khong duoc hoc hoc phan nay",
        ),
    ),
    (
        "f2",
        "hours",
        (
            "thoi luong hoc tren lop va thuc hanh",
            "phan bo gio ly thuyet bai tap thuc hanh",
            "hoc trong bao nhieu gio va bao nhieu tiet",
            "so tiet ly thuyet thuc hanh va tu hoc",
            "thoi gian hoc tap tren giang duong may tiet",
            "co cau gio hoc ly thuyet va thao luan",
        ),
    ),
    (
        "f2",
        "name",
        (
            "ma hoc phan nay ten la gi",
            "ten goi day du cua ma mon",
            "ma mon hoc nay ung voi hoc phan nao",
            "ten chinh thuc cua hoc phan theo ma so",
            "hoc phan mang ma so nay co ten goi la gi",
        ),
    ),
    (
        "f2",
        "program_credits",
        (
            "toan khoa hoc phai tich luy bao nhieu tin",
            "tong khoi luong toan chuong trinh dao tao",
            "tong so tin chi can tich luy cua toan nganh",
            "hoan thanh chuong trinh dai hoc can bao nhieu tc",
            "dinh muc tong tin chi toan khoa hoc",
        ),
    ),
    (
        "f2",
        "program_groups",
        (
            "khung chuong trinh chia thanh nhung khoi kien thuc nao",
            "cau truc khung chuong trinh gom cac nhom nao",
            "cac khoi kien thuc trong khung dao tao",
            "phan bo cac nhom kien thuc trong chuong trinh",
            "danh sach cac khoi va nhom hoc phan cua nganh",
        ),
    ),
    (
        "f2",
        "group_rules",
        (
            "quy dinh tin chi tu chon cua nhom",
            "yeu cau toi thieu trong khoi kien thuc",
            "ghi chu va quy tac chon mon trong nhom kien thuc",
            "so tin chi bat buoc va tu chon cua tung nhom",
            "dieu kien tich luy tin chi trong khoi hoc phan",
        ),
    ),
    (
        "f1",
        "introduction",
        (
            "gioi thieu chung ve nganh hoc",
            "buc tranh tong quan chuong trinh dao tao",
            "khung chuong trinh dao tao cua nganh",
            "thong tin nen tang va lich su hinh thanh nganh",
            "mo ta chung ve dinh huong dao tao cua nganh",
            "tom tat tong quan ve nganh dao tao",
        ),
    ),
    (
        "f1",
        "careers",
        (
            "hoc xong ra truong lam nghe gi",
            "co hoi viec lam va vi tri cong tac",
            "tot nghiep xong lam o dau",
            "trien vong nghe nghiep sau khi tot nghiep",
            "sinh vien ra truong co the dam nhan cong viec gi",
            "cac vi tri tuyen dung phu hop voi chuyen nganh",
        ),
    ),
    (
        "f1",
        "further_study",
        (
            "co hoi hoc len thac si tien si",
            "dieu kien hoc tiep sau dai hoc",
            "kha nang hoc cao hoc va nghien cuu sinh",
            "phat trien hoc thuat o bac sau dai hoc",
            "lien thong va hoc nang cao sau khi tot nghiep dai hoc",
        ),
    ),
    (
        "f1",
        "objectives",
        (
            "muc tieu dao tao va chuan dau ra cua nganh",
            "sinh vien dat duoc nang luc gi khi tot nghiep",
            "kien thuc ky nang pham chat dau ra cua chuong trinh",
            " dinh huong nang luc cot loi ma nganh trang bi",
            "chuan nang luc dau ra danh cho cu nhan",
        ),
    ),
    (
        "f3",
        "content",
        (
            "mon hoc nay day nhung kien thuc gi",
            "noi dung chi tiet cac chuong trong mon hoc",
            "tom tat kien thuc cot loi cua hoc phan",
            "de cuong mon hoc bao gom nhung chu de nao",
            "hoc phan trang bi nhung noi dung chuyen mon gi",
            "cac phan kien thuc se duoc hoc trong mon nay",
        ),
    ),
    (
        "f3",
        "objectives",
        (
            "muc tieu va chuan dau ra cua hoc phan",
            "hoc xong mon nay nam duoc ky nang gi",
            "ket qua hoc tap mong doi sau khi hoan thanh mon hoc",
            "hoc phan huong toi ren luyen nang luc nao",
            "muc dich dao tao cu the cua mon hoc nay",
        ),
    ),
    (
        "f3",
        "suggested_assessment",
        (
            "cach tinh diem va danh gia hoc phan",
            "goi y kiem tra giua ky cuoi ky cua mon",
            "phuong phap danh gia ket qua hoc tap cua mon",
            "hinh thuc kiem tra danh gia thuong xuyen va cuoi ky",
            "de xuat danh gia diem chuyen can bai tap va thi",
        ),
    ),
)


def _word_features(tokens: Sequence[str]) -> Counter[str]:
    """Extract informative unigrams and bigrams from normalized tokens."""
    filtered = [t for t in tokens if not COURSE_CODE.fullmatch(t)]
    core = [t for t in filtered if t not in QUERY_GLUE]
    active = core if core else [t for t in filtered if t not in STOP_WORDS]
    counts: Counter[str] = Counter()
    for token in active:
        counts[token] += 1.0
    for i in range(len(filtered) - 1):
        bigram = f"{filtered[i]}_{filtered[i + 1]}"
        if filtered[i] not in STOP_WORDS or filtered[i + 1] not in STOP_WORDS:
            counts[bigram] += 1.25
    return counts


def _char_ngrams(text: str, ns: tuple[int, ...] = (3, 4)) -> Counter[str]:
    """Extract character 3-grams and 4-grams over normalized token text."""
    tokens = [t for t in _tokens(text) if t not in QUERY_GLUE and not COURSE_CODE.fullmatch(t)]
    if not tokens:
        tokens = [t for t in _tokens(text) if t not in STOP_WORDS]
    compact = f" {' '.join(tokens)} "
    if len(compact.strip()) < 2:
        return Counter()
    grams: Counter[str] = Counter()
    for n in ns:
        if len(compact) >= n:
            for idx in range(len(compact) - n + 1):
                grams[compact[idx : idx + n]] += 1
    return grams


def _build_anchor_idf() -> dict[str, float]:
    docs = [
        _word_features(_tokens(phrase))
        for _, _, phrases in ANCHOR_INTENTS
        for phrase in phrases
    ]
    total = len(docs)
    df: Counter[str] = Counter()
    for doc in docs:
        for feat in doc:
            df[feat] += 1
    return {
        feat: math.log1p((total + 1.0) / (count + 0.5))
        for feat, count in df.items()
    }


_ANCHOR_IDF = _build_anchor_idf()


def _weighted_word_similarity(query_tokens: Sequence[str], anchor_tokens: Sequence[str]) -> float:
    q_feats = _word_features(query_tokens)
    a_feats = _word_features(anchor_tokens)
    if not q_feats or not a_feats:
        return 0.0
    q_weights = {f: c * _ANCHOR_IDF.get(f, 1.5) for f, c in q_feats.items()}
    a_weights = {f: c * _ANCHOR_IDF.get(f, 1.5) for f, c in a_feats.items()}
    shared = q_weights.keys() & a_weights.keys()
    if not shared:
        return 0.0
    dot = sum(q_weights[f] * a_weights[f] for f in shared)
    q_norm = math.sqrt(sum(v * v for v in q_weights.values()))
    a_norm = math.sqrt(sum(v * v for v in a_weights.values()))
    if not q_norm or not a_norm:
        return 0.0
    cosine = dot / (q_norm * a_norm)
    # Anchor recall measures how well a longer conversational query covers a concise anchor phrase.
    anchor_coverage = sum(a_weights[f] for f in shared) / sum(a_weights.values())
    return 0.55 * cosine + 0.45 * anchor_coverage


def _char_ngram_similarity(query_text: str, target_text: str) -> float:
    q_grams = _char_ngrams(query_text)
    t_grams = _char_ngrams(target_text)
    if not q_grams or not t_grams:
        return 0.0
    shared = q_grams.keys() & t_grams.keys()
    if not shared:
        return 0.0
    overlap = sum(min(q_grams[g], t_grams[g]) for g in shared)
    dice = (2.0 * overlap) / (sum(q_grams.values()) + sum(t_grams.values()))
    dot = sum(q_grams[g] * t_grams[g] for g in shared)
    norm = math.sqrt(sum(v * v for v in q_grams.values()) * sum(v * v for v in t_grams.values()))
    cosine = dot / norm if norm else 0.0
    return 0.5 * dice + 0.5 * cosine


def _phrase_similarity(query_text: str, query_tokens: Sequence[str], anchor: str) -> float:
    anchor_tokens = _tokens(anchor)
    word_sim = _weighted_word_similarity(query_tokens, anchor_tokens)
    char_sim = _char_ngram_similarity(query_text, anchor)
    if word_sim == 0.0:
        # Require strong character n-gram overlap when no exact token/bigram matched (e.g. typo).
        return char_sim * 0.72
    return 0.68 * word_sim + 0.32 * char_sim


def semantic_question_intent(
    question: str,
    *,
    has_course: bool = False,
    threshold: float = 0.38,
) -> tuple[str | None, str | None, float]:
    """Infer `(dataset, field, score)` semantically from normalized requested clauses."""
    if not isinstance(question, str) or not question.strip():
        return None, None, 0.0
    if out_of_scope(question):
        return None, None, 0.0
    text = requested_text(question)
    if not text:
        return None, None, 0.0

    tokens = _tokens(text)
    inferred_course = (
        has_course
        or any(COURSE_CODE.fullmatch(t) for t in tokens)
        or has(text, "hoc phan", "mon hoc", "mon nay", "ma mon", "ma hoc phan")
    )

    # Special curriculum framework disambiguation:
    # "khung chương trình" + structure/block/group keywords -> ("f2", "program_groups")
    # general "khung chương trình" -> ("f1", "introduction")
    if not has_course and has(text, "khung chuong trinh", "khung dao tao"):
        if has(text, "khoi", "nhom", "cau truc", "phan bo", "chia thanh"):
            return "f2", "program_groups", 0.88
        return "f1", "introduction", 0.85

    intent_scores: dict[tuple[str, str], float] = {}
    for dataset, field, phrases in ANCHOR_INTENTS:
        best_phrase_score = max(
            (_phrase_similarity(text, tokens, phrase) for phrase in phrases),
            default=0.0,
        )
        intent_scores[dataset, field] = best_phrase_score

    # Contextual adjustments for course vs program scope
    if has_course:
        # Transfer program-level objective/credit signal to course-level equivalents before filtering
        intent_scores["f3", "objectives"] = max(
            intent_scores.get(("f3", "objectives"), 0.0),
            intent_scores.get(("f1", "objectives"), 0.0),
        )
        intent_scores["f2", "credits"] = max(
            intent_scores.get(("f2", "credits"), 0.0),
            intent_scores.get(("f2", "program_credits"), 0.0) * 0.9,
        )
        for key in list(intent_scores):
            if key in PROGRAM_ONLY_WHEN_COURSE_INTENTS:
                intent_scores[key] = 0.0
            elif key in COURSE_LEVEL_INTENTS:
                intent_scores[key] = min(1.0, intent_scores[key] * 1.15)
    else:
        # Without an explicit course flag, check whether the text itself signals course vs program
        if inferred_course:
            for key in COURSE_LEVEL_INTENTS:
                intent_scores[key] = min(1.0, intent_scores[key] * 1.08)
        else:
            # When has_course is False and no course is mentioned, shift f3/objectives to f1/objectives
            intent_scores["f1", "objectives"] = max(
                intent_scores.get(("f1", "objectives"), 0.0),
                intent_scores.get(("f3", "objectives"), 0.0),
            )
            intent_scores["f3", "objectives"] = 0.0
            if has(text, "toan khoa", "toan chuong trinh", "toan nganh", "tong khoi luong", "tong so tin"):
                intent_scores["f2", "program_credits"] = min(
                    1.0, intent_scores.get(("f2", "program_credits"), 0.0) * 1.15
                )

    if question_group_keys(question) and not has_course:
        intent_scores["f2", "group_rules"] = max(intent_scores.get(("f2", "group_rules"), 0.0), 0.75)

    best_intent, best_score = max(
        intent_scores.items(),
        key=lambda item: (round(item[1], 6), item[0][0], item[0][1]),
        default=((None, None), 0.0),
    )
    best_score = round(min(1.0, best_score), 4)
    if best_score < threshold:
        return None, None, best_score
    dataset, field = best_intent
    if not has_course and (dataset, field) == ("f3", "objectives"):
        return "f1", "objectives", best_score
    return dataset, field, best_score


def _chunk_similarity(
    query_text: str,
    query_tokens: Sequence[str],
    chunk: RAGChunk,
    inferred_intent: tuple[str | None, str | None],
) -> tuple[float, tuple[str, ...]]:
    body_text = _body(chunk)
    title = chunk.metadata.get("course_name") if chunk.dataset == "f3" else chunk.metadata.get("title")
    field_name = chunk.metadata.get("field") or ""
    field_label = FIELD_LABELS.get(field_name, "")
    composite_header = " ".join(part for part in (title, chunk.metadata.get("course_code"), field_label) if part)
    full_text = f"{composite_header} {body_text}".strip()

    chunk_term_counts = _terms(chunk)
    query_term_set = set(query_tokens) - STOP_WORDS
    matched_terms = tuple(sorted(query_term_set & chunk_term_counts.keys()))

    word_sim = _weighted_word_similarity(query_tokens, _tokens(full_text))
    header_char_sim = _char_ngram_similarity(query_text, composite_header) if composite_header else 0.0
    body_char_sim = _char_ngram_similarity(query_text, body_text[:600])
    char_sim = max(header_char_sim, 0.45 * header_char_sim + 0.55 * body_char_sim)

    intent_bonus = 0.0
    if inferred_intent[0] == chunk.dataset and inferred_intent[1] == field_name:
        intent_bonus = 0.18
    elif inferred_intent[1] and inferred_intent[1] == field_name:
        intent_bonus = 0.10

    lexical_overlap = len(matched_terms) / max(1, len(query_term_set))
    score = round(0.45 * word_sim + 0.35 * char_sim + 0.20 * lexical_overlap + intent_bonus, 6)
    return max(score, 1e-6), matched_terms


def rank_top_k_chunks(
    query: str,
    candidates: Sequence[RAGChunk],
    *,
    top_k: int = 5,
    base_hits: Sequence[RetrievalHit] = (),
) -> tuple[RetrievalHit, ...]:
    """Return up to `top_k` ranked chunks, preserving `base_hits` and backfilling via multi-signal similarity."""
    if top_k <= 0:
        return ()
    preserved: list[RetrievalHit] = []
    seen_chunk_ids: set[str] = set()
    seen_identities: set[tuple] = set()

    for hit in base_hits:
        cid = hit.chunk.chunk_id
        if cid in seen_chunk_ids:
            continue
        seen_chunk_ids.add(cid)
        identity = (
            hit.chunk.dataset,
            hit.chunk.major,
            hit.chunk.version,
            hit.chunk.metadata.get("program_variant"),
            hit.chunk.metadata.get("course_code"),
            hit.chunk.metadata.get("field"),
            hit.chunk.metadata.get("source_url"),
            _body(hit.chunk),
        )
        seen_identities.add(identity)
        preserved.append(hit)
        if len(preserved) >= top_k:
            return tuple(preserved)

    if not candidates:
        return tuple(preserved)

    clean_query = requested_text(query) if isinstance(query, str) and query.strip() else (query or "")
    if not clean_query:
        clean_query = query if isinstance(query, str) else ""
    query_tokens = _tokens(clean_query)
    codes = {t.upper() for t in query_tokens if COURSE_CODE.fullmatch(t)}

    filtered_candidates = tuple(candidates)
    if codes:
        code_matched = tuple(c for c in filtered_candidates if c.metadata.get("course_code") in codes)
        if code_matched:
            filtered_candidates = code_matched

    has_course = bool(codes) or any(c.dataset == "f3" for c in filtered_candidates)
    intent_ds, intent_field, _ = semantic_question_intent(
        clean_query,
        has_course=has_course,
        threshold=0.25,
    )

    fallback_hits: list[RetrievalHit] = []
    for chunk in filtered_candidates:
        if chunk.chunk_id in seen_chunk_ids:
            continue
        identity = (
            chunk.dataset,
            chunk.major,
            chunk.version,
            chunk.metadata.get("program_variant"),
            chunk.metadata.get("course_code"),
            chunk.metadata.get("field"),
            chunk.metadata.get("source_url"),
            _body(chunk),
        )
        if identity in seen_identities:
            continue
        seen_chunk_ids.add(chunk.chunk_id)
        seen_identities.add(identity)
        score, matched = _chunk_similarity(clean_query, query_tokens, chunk, (intent_ds, intent_field))
        fallback_hits.append(RetrievalHit(chunk=chunk, score=score, matched_terms=matched))

    fallback_hits.sort(key=lambda h: (-h.score, h.chunk.chunk_id))
    needed = top_k - len(preserved)
    return tuple(preserved + fallback_hits[:needed])
