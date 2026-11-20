"""Run the local Gemini chat using the saved backend .env key."""

from __future__ import annotations

import argparse
import json
import logging
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def configure(env_file: Path, *, root: Path | None = None, retrieval='lexical', model_cache=None,
              answer_policy='legacy') -> None:
    if answer_policy not in {'legacy', 'focused'}:
        raise ValueError('Invalid answer policy')
    os.environ['HUS_ANSWER_POLICY'] = answer_policy
    from dotenv import dotenv_values

    from app.hus.llm.config import HUSLLMSettings, llm_rewrite_available

    # Parse without interpolation; never export unrelated account/DB settings.
    values = dotenv_values(env_file, interpolate=False, encoding='utf-8-sig') if env_file.is_file() else {}
    for name in ('HUS_LLM_API_KEY', 'HUS_LLM_BASE_URL', 'HUS_LLM_MODEL'):
        if values.get(name):
            os.environ.setdefault(name, values[name])
    os.environ.setdefault('HUS_LLM_BASE_URL', HUSLLMSettings.base_url)
    os.environ.setdefault('HUS_LLM_MODEL', HUSLLMSettings.model)
    os.environ['HUS_LLM_ENABLED'] = 'true'
    os.environ['HUS_LLM_AUTO'] = 'true'
    os.environ['HUS_LLM_INTENT_ENABLED'] = 'true'
    from app.hus.retrieval_profile import configure_retrieval

    configure_retrieval(retrieval, model_cache=model_cache, root=ROOT if root is None else root)
    HUSLLMSettings.from_env()  # Local validation only: no provider/key check.
    if not llm_rewrite_available():
        raise ValueError('HUS_LLM_BASE_URL must use direct Google HTTPS')


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--env-file', type=Path, help='Backend env file (default: project-root .env)')
    parser.add_argument('--port', type=int, default=8011)
    parser.add_argument('--retrieval', choices=['lexical', 'hybrid'], default='lexical')
    parser.add_argument('--model-cache', type=Path)
    parser.add_argument('--answer-policy', choices=['legacy', 'focused'], default='legacy')
    parser.add_argument('--check', action='store_true', help='No-key offline retrieval preflight, then exit')
    args = parser.parse_args(argv)
    if not 1 <= args.port <= 65535:
        parser.error('--port must be between 1 and 65535')
    if args.check:
        from app.hus.retrieval_profile import check_hybrid

        if args.retrieval == 'hybrid':
            print(json.dumps(check_hybrid(model_cache=args.model_cache, root=ROOT), ensure_ascii=False, indent=2))
        else:
            from tools.run_hus_rag import check

            report = check(answer_policy='focused') if args.answer_policy == 'focused' else check()
            print(json.dumps(report, ensure_ascii=False, indent=2))
        return
    try:
        configure(args.env_file if args.env_file is not None else ROOT / '.env',
                  retrieval=args.retrieval, model_cache=args.model_cache, answer_policy=args.answer_policy)
    except (ValueError, OSError):
        parser.error('Cannot load backend configuration. Check saved HUS_LLM_* settings '
                     'and, for hybrid, the retrieval profile.')
    if args.retrieval == 'hybrid':
        from app.hus.retrieval_profile import require_hybrid

        print('Checking hybrid v4 index and loading the local embedding model...', flush=True)
        try:
            require_hybrid(root=ROOT)
        except (ValueError, OSError):
            parser.error('Hybrid preflight failed. Run --retrieval hybrid --check; '
                         'check the pinned v4 index, model cache and optional dependencies.')
        print('Hybrid ready: BM25 + local ChromaDB. Open http://127.0.0.1:' + str(args.port), flush=True)
    import uvicorn

    block_logger = logging.getLogger('hus.diagnostics')
    block_logger.setLevel(logging.INFO)
    if not block_logger.handlers:
        block_logger.addHandler(logging.StreamHandler())
    uvicorn.run('app.hus.demo:app', host='127.0.0.1', port=args.port, workers=1,
                access_log=False, log_level='warning')


if __name__ == '__main__':
    main()
