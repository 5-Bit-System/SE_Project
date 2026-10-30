"""Test-only bootstrap: real FastAPI app and JSON repository, no VNU worker or database."""

import argparse
import os
from contextlib import asynccontextmanager
from pathlib import Path

import uvicorn


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--data", type=Path, required=True)
    parser.add_argument("--port", type=int, required=True)
    parser.add_argument("--run-id", required=True)
    parser.add_argument("--thread-tokens", type=int, default=0)
    args = parser.parse_args()
    root = Path(__file__).resolve().parents[2]
    if any((root / name).exists() for name in (".env", ".env.auth")):
        parser.error("Run in a clean test worktree without local configuration files")
    if not (args.data / "BT3_SYNTHETIC_ONLY").is_file():
        parser.error("Synthetic fixture marker required")
    # The parent supplies only OS essentials and explicitly synthetic app settings.
    if os.environ.get("APP_ENV") != "test" or os.environ.get("STORAGE_BACKEND") != "json":
        parser.error("Explicit test JSON environment required")
    from fastapi import HTTPException

    from app import catalog as catalog_module
    from app.main import app, check_auth_ready, check_storage_ready

    catalog_module.DATA_ROOT = args.data

    @asynccontextmanager
    async def offline_lifespan(application):
        import anyio.to_thread

        limiter = anyio.to_thread.current_default_thread_limiter()
        if args.thread_tokens:
            limiter.total_tokens = args.thread_tokens
        app.state.bt3_thread_tokens = limiter.total_tokens
        check_storage_ready()
        check_auth_ready()
        yield

    # Only startup/shutdown portal lifecycle is replaced. Catalog route/service/serializer,
    # middleware, error handlers, normalization and file repository are the real project code.
    app.router.lifespan_context = offline_lifespan

    @app.get("/bt3-test-marker", include_in_schema=False)
    def marker():
        return {"kind": "bt3-synthetic-only", "pid": os.getpid(), "run_id": args.run_id,
                "thread_tokens": app.state.bt3_thread_tokens}

    @app.post("/bt3-test-shutdown", include_in_schema=False)
    def shutdown(run_id: str):
        if run_id != args.run_id:
            raise HTTPException(status_code=403)
        server.should_exit = True
        return {"stopping": True}

    server = uvicorn.Server(uvicorn.Config(
        app, host="127.0.0.1", port=args.port, access_log=False, log_level="warning"))
    server.run()


if __name__ == "__main__":
    main()
