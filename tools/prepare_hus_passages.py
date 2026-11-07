"""Create/verify V2 token-bounded passages. No weights, embeddings or index build.

Requires the locked native ``tokenizers`` package (isolated runtime) and an
explicitly fetched, hash-verified ``tokenizer.json`` cache; never downloads.
"""
import argparse
from pathlib import Path

from app.hus.passage_tokenizer import load_tokenizer
from app.hus.passages import verify_passage_files, write_passages
from app.hus.rag_loader import HUSRAGData
from app.hus.vector_contract import ROOT, verify_contract_files

PASSAGE_ROOT = ROOT / 'data/hus/vector_passages'
DEFAULT_CONTRACT = ROOT / 'data/hus/vector_contracts/e5_small_v1_20261105'


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--out', type=Path)
    action.add_argument('--verify', type=Path)
    parser.add_argument('--contract', type=Path, default=DEFAULT_CONTRACT)
    parser.add_argument('--tokenizer-cache', type=Path, required=True)
    args = parser.parse_args(argv)
    data = HUSRAGData.load_current()
    contract = verify_contract_files(args.contract, data)
    tokenizer = load_tokenizer(args.tokenizer_cache, contract)
    manifest = (verify_passage_files(args.verify, args.contract, data, tokenizer) if args.verify
                else write_passages(args.out, args.contract, data, tokenizer, passage_root=PASSAGE_ROOT))
    corpus = manifest['corpus']
    print(f"Passages {manifest['passage_set_id']}; {corpus['parent_count']} parents -> "
          f"{corpus['passage_count']} passages ({corpus['split_parent_count']} split); "
          f"max input {corpus['max_input_tokens']}; stage={manifest['stage']}; index_built={manifest['index_built']}")


if __name__ == '__main__':
    main()
