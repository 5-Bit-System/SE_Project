"""Compatibility entrypoint for the portable standalone RAG launcher."""
from tools.run_hus_rag import PROGRAMS, RELEASE, RELEASE_SHA, ROOT, check, configure, main

__all__ = ['PROGRAMS', 'RELEASE', 'RELEASE_SHA', 'ROOT', 'check', 'configure', 'main']

if __name__ == '__main__':
    main()
