"""Explicit offline V3 fetch/build/verify. Does not activate chatbot vector retrieval."""
import argparse
from pathlib import Path

from app.hus.rag_loader import HUSRAGData
from app.hus.vector_contract import ROOT, verify_contract_files


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--fetch-model', action='store_true')
    action.add_argument('--out', type=Path)
    action.add_argument('--verify', type=Path)
    parser.add_argument('--model-cache', type=Path, required=True)
    parser.add_argument('--contract', type=Path, default=ROOT / 'data/hus/vector_contracts/e5_small_v1_20261105')
    parser.add_argument('--passages', type=Path, default=ROOT / 'data/hus/vector_passages/e5_small_v2_20261105')
    parser.add_argument('--expected-index-id')
    args = parser.parse_args(argv)
    if args.verify and not args.expected_index_id:
        parser.error('--verify requires --expected-index-id from the separately recorded build result')
    data = HUSRAGData.load_current()
    if args.fetch_model:
        from app.hus.embedding import fetch_model
        result = fetch_model(args.model_cache, verify_contract_files(args.contract, data))
        print(f'Verified {len(result)} pinned model artifacts; no index built')
        return
    from app.hus.vector_index import build_index, verify_index
    result = (verify_index(args.verify, args.contract, args.passages, data, args.model_cache,
                           expected_index_id=args.expected_index_id) if args.verify else
              build_index(args.out, args.contract, args.passages, data, args.model_cache))
    print(f"Index {result['index_id']}; {result['corpus']['passage_count']} vectors; "
          f"{result['corpus']['parent_count']} parents; stage={result['stage']}")


if __name__ == '__main__':
    main()
