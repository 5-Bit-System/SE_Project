"""Lossless embedding windows over canonical parent bodies (not source offsets)."""
import json
import unicodedata

# A cut placed right before/after these characters would separate them from the
# grapheme they modify (combining marks, joiners, variation selectors, modifiers).
_JOINING = {'\u200c', '\u200d', '\ufe0e', '\ufe0f'}
_SENTENCE_END = set('.!?;:…')


def _content(tokenizer, text):
    result = tokenizer.encode(text, add_special_tokens=False)
    if len(result.ids) != len(result.offsets) or any(
        type(start) is not int or type(end) is not int or not 0 <= start <= end <= len(text)
        for start, end in result.offsets
    ):
        raise ValueError('Invalid original-text token offsets')
    return result


def _safe_cut(body, index):
    """A cut is allowed only between graphemes of the original string."""
    if index <= 0 or index >= len(body):
        return index == len(body)
    prev, char = body[index - 1], body[index]
    return not (
        prev == '\u200d'
        or (prev == '\r' and char == '\n')
        or unicodedata.combining(char)
        or unicodedata.category(char) in {'Mn', 'Mc', 'Me'}
        or char in _JOINING
        or '\udc00' <= char <= '\udfff'
        or '\U0001f3fb' <= char <= '\U0001f3ff'
        or '\U000e0020' <= char <= '\U000e01ef'
        or ('\U0001f1e6' <= prev <= '\U0001f1ff' and '\U0001f1e6' <= char <= '\U0001f1ff')
    )


def _token_cut(body, start, end):
    """Cut before a token's visible text: its leading whitespace (the SentencePiece
    word marker covers it) stays with the preceding passage instead of opening the next."""
    pos = start
    while pos < end and body[pos].isspace():
        pos += 1
    return pos if pos < end else start


def _cut_tier(body, index, start=0):
    """0 paragraph end, 1 sentence end, 2 line break, 3 other. PDF text uses
    single newlines as soft wraps, so a bare newline ranks below a sentence end."""
    if index >= len(body):
        return 0
    before = body[start:index]
    core = before.rstrip()
    tail = before[len(core):]
    lines = tail.count('\n')
    if not core:
        return 3
    if lines >= 2 or (lines and (core[-1] in _SENTENCE_END or body[index] == '#')):
        return 0
    if tail and (core[-1] in _SENTENCE_END or (lines and core[-1] == ')')):
        return 1
    return 2 if lines else 3


def split_body(body, tokenizer, *, prefix='passage: ', context='', window=512, target=400, overlap=64):
    """Use offsets only to select literal slices; recount every complete input.

    Offsets refer to this body in Unicode codepoints, never to a PDF/source span.
    Tokenization may change at slice boundaries, so global token counts cannot
    determine the budget or overlap of an independently embedded passage.
    Cuts are placed before a token's visible text, so whitespace and characters
    the tokenizer normalizes away (combining marks) stay with the preceding text,
    falling back to the raw token start if trailing whitespace would inflate tokens.
    Paragraph, then sentence, then line ends are preferred when they keep at
    least half the target; otherwise the largest fitting token boundary is used.
    """
    if (any(type(v) is not int for v in [window, target, overlap])
            or not 0 < window <= 512 or not 0 < target <= min(400, window)
            or not 0 <= overlap <= 64 or not isinstance(body, str) or not body):
        raise ValueError('Invalid passage policy/body')
    if not isinstance(prefix, str) or not isinstance(context, str):
        raise ValueError('Invalid prefix/context')
    children, start, covered = [], 0, 0
    while covered < len(body):
        remaining = body[start:]
        tokens = _content(tokenizer, remaining)
        # Cut before token i keeps tokens[0:i]; the whole remainder is the first option.
        cuts = {len(body): len(tokens.ids)} if len(tokens.ids) <= target else {}
        for i in range(min(target, len(tokens.ids) - 1), 0, -1):
            s, e = tokens.offsets[i]
            for cut in (_token_cut(body, start + s, start + e), start + s):
                if cut not in cuts and covered < cut < len(body) and _safe_cut(body, cut):
                    cuts[cut] = i
        ordered = sorted(cuts, key=lambda c: (_cut_tier(body, c, start) if cuts[c] >= target // 2 or c == len(body) else 3, -c))
        chosen = None
        for end in ordered:
            text = body[start:end]
            content = _content(tokenizer, text)
            embedding_text = prefix + context + text
            total = len(tokenizer.encode(embedding_text, add_special_tokens=True).ids)
            if len(content.ids) > target or total > window:
                continue
            chosen = {'body_start_char': start, 'body_end_char': end, 'text': text,
                      'embedding_text': embedding_text, 'content_tokens': len(content.ids),
                      'input_tokens': total,
                      'overlap_tokens': len(_content(tokenizer, body[start:covered]).ids)}
            break
        if chosen is None:
            if start < covered:
                start = covered  # overlap must never prevent forward progress
                continue
            raise ValueError('A source span cannot fit the token window/budget without truncation')
        children.append(chosen)
        covered = chosen['body_end_char']
        if covered == len(body):
            break
        # Try suffix starts near the desired overlap, then recount their actual tokens.
        offsets = content.offsets[-overlap:] if overlap else []
        starts = sorted({_token_cut(body, start + s, start + e) for s, e in offsets})
        starts = [s for s in starts if start < s < covered and _safe_cut(body, s)]
        start = next((s for s in starts if len(_content(tokenizer, body[s:covered]).ids) <= overlap), covered)
    return children


# --- V2 parent-bound artifact -------------------------------------------------

OFFSET_BASIS = 'parent_retrieval_body_unicode_codepoints_not_source_offsets'
ROW_FILE = 'passages.jsonl'


def digest_bytes(raw):
    import hashlib
    return hashlib.sha256(raw).hexdigest()


def passages_bytes(rows):
    from app.hus.vector_contract import encoded
    return b''.join(encoded(row) + b'\n' for row in rows)


def _policy(contract):
    """Derive the passage policy from the verified V1 contract; never widen it."""
    model, rules = contract['model'], contract['policies']
    if (type(rules.get('target_passage_content_tokens')) is not int or rules['target_passage_content_tokens'] != 400
            or type(rules.get('max_overlap_tokens')) is not int or rules['max_overlap_tokens'] != 64
            or type(model.get('max_input_tokens')) is not int or model['max_input_tokens'] != 512
            or model.get('passage_prefix') != 'passage: '
            or rules.get('context_template') != '' or rules.get('silent_truncation') is not False
            or rules.get('count_prefix_context_special_tokens') is not True
            or rules.get('citation_basis') != 'canonical_parent_not_index_text'):
        raise ValueError('V1 contract policy is not the frozen V2 input policy')
    return {'version': 'hus-vector-passage-policy-2.0', 'prefix': model['passage_prefix'],
            'context_template': rules['context_template'], 'window_tokens': model['max_input_tokens'],
            'target_content_tokens': rules['target_passage_content_tokens'],
            'max_overlap_tokens': rules['max_overlap_tokens'],
            'counted': 'prefix+context+content+special_tokens_actual_tokenizer',
            'cut_rule': 'token_start_grapheme_safe_prefer_paragraph_or_sentence_end_at_least_half_target',
            'offset_basis': OFFSET_BASIS, 'silent_truncation': False, 'cross_parent_merge': False,
            'citation_basis': 'canonical_parent_quote_hash_locator', 'gold_comparison': 'collapse_to_parent_id',
            'f2': rules['f2'], 'generated_requires_opt_in': rules['generated_requires_opt_in']}


def _load_contract(folder, data):
    from pathlib import Path

    from app.hus.vector_contract import verify_contract_files
    folder = Path(folder)
    contract = verify_contract_files(folder, data)  # rebuilt from current canonical/profile/lock
    inventory = [json.loads(line) for line in (folder / 'parents.jsonl').read_bytes().splitlines()]
    return folder, contract, inventory


def _chunks(data, inventory):
    majors = sorted({p['metadata']['major'] for p in inventory})
    return {c.chunk_id: c for family in ['f1', 'f3'] for major in majors
            for c in data.chunks(family, major=major, allow_generated=True)}


def _bound_parent(parent, chunk):
    import hashlib

    from app.hus.retrieval import _body
    from app.hus.vector_contract import digest_json
    body = _body(chunk)
    if (hashlib.sha256(body.encode()).hexdigest() != parent['body_sha256']
            or chunk.package_sha256 != parent['package_sha256']
            or digest_json(chunk.metadata) != parent['source_metadata_sha256']):
        raise ValueError('Canonical parent differs from the V1 inventory')
    return body


def build_passages(contract_folder, data, tokenizer):
    from app.hus.vector_contract import digest, digest_json
    folder, contract, inventory = _load_contract(contract_folder, data)
    policy = _policy(contract)
    chunks = _chunks(data, inventory)
    rows = []
    for parent in inventory:
        chunk = chunks.get(parent['parent_id'])
        if chunk is None:
            raise ValueError('V1 parent missing from canonical data')
        body = _bound_parent(parent, chunk)
        children = split_body(body, tokenizer, prefix=policy['prefix'], context=policy['context_template'],
                              window=policy['window_tokens'], target=policy['target_content_tokens'],
                              overlap=policy['max_overlap_tokens'])
        for index, child in enumerate(children):
            ids = list(tokenizer.encode(child['embedding_text'], add_special_tokens=True).ids)
            rows.append({'passage_id': f"{parent['parent_id']}#p{index:03d}", 'parent_id': parent['parent_id'],
                         'passage_index': index, 'passage_count': len(children),
                         'body_start_char': child['body_start_char'], 'body_end_char': child['body_end_char'],
                         'offset_basis': OFFSET_BASIS, 'source_offsets': None, 'citation_basis': 'canonical_parent',
                         'text': child['text'], 'embedding_text': child['embedding_text'],
                         'text_sha256': digest_bytes(child['text'].encode()),
                         'embedding_text_sha256': digest_bytes(child['embedding_text'].encode()),
                         'input_token_ids_sha256': digest_json([int(i) for i in ids]),
                         'content_tokens': child['content_tokens'], 'input_tokens': child['input_tokens'],
                         'overlap_tokens': child['overlap_tokens'],
                         'parent_body_sha256': parent['body_sha256'], 'parent_package_sha256': parent['package_sha256'],
                         'parent_source_metadata_sha256': parent['source_metadata_sha256'],
                         'metadata': dict(parent['metadata'])})
    raw = passages_bytes(rows)
    split = {r['parent_id'] for r in rows if r['passage_count'] > 1}
    manifest = {'schema_version': 'hus-vector-passages-2.0', 'stage': 'passages_only', 'index_built': False,
                'embeddings_computed': False, 'activation_allowed': False,
                'contract': {'contract_id': contract['contract_id'],
                             'manifest_sha256': digest(folder / 'manifest.json'),
                             'parents_inventory_sha256': contract['corpus']['inventory_sha256']},
                'release': contract['release'], 'tokenizer': dict(tokenizer.identity), 'policy': policy,
                'corpus': {'parent_count': len(inventory), 'passage_count': len(rows), 'split_parent_count': len(split),
                           'family_passage_counts': {f: sum(r['metadata']['family'] == f for r in rows)
                                                     for f in sorted({r['metadata']['family'] for r in rows})},
                           'max_input_tokens': max(r['input_tokens'] for r in rows),
                           'max_content_tokens': max(r['content_tokens'] for r in rows),
                           'max_overlap_tokens': max(r['overlap_tokens'] for r in rows),
                           'passages_file': ROW_FILE, 'passages_sha256': digest_bytes(raw)}}
    manifest['passage_set_id'] = digest_json(manifest)
    return manifest, rows


def verify_passages(manifest, rows, contract_folder, data, tokenizer):
    from app.hus.vector_contract import digest_json, encoded
    if (not isinstance(manifest, dict) or manifest.get('passage_set_id') !=
            digest_json({k: v for k, v in manifest.items() if k != 'passage_set_id'})):
        raise ValueError('Invalid passage set identity')
    expected_manifest, expected_rows = build_passages(contract_folder, data, tokenizer)
    # Canonical JSON bytes keep bool/int and int/float distinct.
    if encoded(manifest) != encoded(expected_manifest) or passages_bytes(rows) != passages_bytes(expected_rows):
        raise ValueError('Passages differ from current V1 contract/canonical parents/tokenizer/policy')
    return manifest


def write_passages(out, contract_folder, data, tokenizer, *, passage_root=None):
    from pathlib import Path

    from app.hus.vector_contract import ROOT
    logical = Path(passage_root) if passage_root is not None else ROOT / 'data/hus/vector_passages'
    allowed = logical.resolve()
    raw_out = Path(out)
    out = raw_out.resolve()
    if (allowed != logical.absolute() or raw_out.is_symlink() or out == allowed
            or not out.is_relative_to(allowed) or out.exists()):
        raise ValueError('Choose a fresh directory under the passage root')
    if any((parent / 'manifest.json').exists() for parent in out.parents if parent.is_relative_to(allowed)):
        raise ValueError('Cannot nest passages inside a frozen passage set')
    manifest, rows = build_passages(contract_folder, data, tokenizer)
    out.mkdir(parents=True)
    (out / ROW_FILE).write_bytes(passages_bytes(rows))
    (out / 'manifest.json').write_bytes(json.dumps(manifest, ensure_ascii=False, sort_keys=True, indent=2).encode() + b'\n')
    return manifest


def verify_passage_files(folder, contract_folder, data, tokenizer):
    from pathlib import Path
    folder = Path(folder)
    manifest = json.loads((folder / 'manifest.json').read_bytes())
    raw = (folder / ROW_FILE).read_bytes()
    if digest_bytes(raw) != manifest.get('corpus', {}).get('passages_sha256'):
        raise ValueError('Passage file bytes differ')
    verify_passages(manifest, [json.loads(line) for line in raw.splitlines()], contract_folder, data, tokenizer)
    return manifest


def parent_chunk(row, data):
    """Resolve a passage hit to its canonical parent; citations use the parent only."""
    meta = row['metadata']
    chunk = next((c for c in data.chunks(meta['family'], major=meta['major'], allow_generated=True)
                  if c.chunk_id == row['parent_id']), None)
    if chunk is None:
        raise ValueError('Passage parent missing')
    body = _bound_parent({'body_sha256': row['parent_body_sha256'], 'package_sha256': row['parent_package_sha256'],
                          'source_metadata_sha256': row['parent_source_metadata_sha256']}, chunk)
    start, end = row['body_start_char'], row['body_end_char']
    source = chunk.metadata
    citation = source.get('citation') or {}
    expected_source = citation.get('source_id') or source.get('record_id') or source.get('document_id')
    release = data.release_identity
    if (type(start) is not int or type(end) is not int or not 0 <= start < end <= len(body)
            or body[start:end] != row['text'] or row.get('text_sha256') != digest_bytes(row['text'].encode())
            or row.get('offset_basis') != OFFSET_BASIS or row.get('source_offsets') is not None
            or row.get('citation_basis') != 'canonical_parent'
            or meta.get('parent_id') != row['parent_id'] or meta.get('version') != chunk.version
            or meta.get('variant') != (source.get('program_variant') or 'unknown')
            or meta.get('ai_opt_in_required') is not (meta.get('family') == 'f3')
            or meta.get('release_id') != release.get('release_id')
            or meta.get('release_sha256') != release.get('release_sha256')
            or meta.get('source_id') != expected_source
            or any(meta.get(k) != source.get(k) for k in ['field', 'review_status', 'content_origin'])
            or (meta.get('course_code') or '') != (source.get('course_code') or '')):
        raise ValueError('Passage text/scope is not a literal slice of its parent')
    return chunk


def collapse_to_parents(hits):
    """Rank parents by their best passage so gold/Recall stay parent-level."""
    seen = []
    for hit in hits:
        parent_id = hit.get('parent_id') if isinstance(hit, dict) else None
        if not isinstance(parent_id, str) or not parent_id or '#' in parent_id:
            raise ValueError('Hit requires a canonical parent_id, not a passage_id')
        if parent_id not in seen:
            seen.append(parent_id)
    return seen
