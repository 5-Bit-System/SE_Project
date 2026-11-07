"""Create/verify V1 metadata only. No ML import, model download or index build."""
import argparse
from pathlib import Path

from app.hus.rag_loader import HUSRAGData
from app.hus.vector_contract import verify_contract_files, write_contract


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--out', type=Path)
    action.add_argument('--verify', type=Path)
    args = parser.parse_args(argv)
    data = HUSRAGData.load_current()
    manifest = (verify_contract_files(args.verify, data) if args.verify else write_contract(args.out, data))
    print(f"Contract {manifest['contract_id']}; {manifest['corpus']['parent_count']} parents; "
          f"stage={manifest['stage']}; index_built={manifest['index_built']}")


if __name__ == '__main__':
    main()
