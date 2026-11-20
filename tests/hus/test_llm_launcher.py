"""Standalone Gemini launcher, tested with temporary fake credentials only."""
import os
from unittest.mock import patch

import pytest


def launcher():
    from tools import run_hus_llm
    return run_hus_llm


def test_loads_saved_hus_key_and_enables_only_this_process(tmp_path):
    (tmp_path / '.env').write_text('HUS_LLM_API_KEY="fake-key"\nHUS_LLM_ENABLED=false\nDB_PASSWORD=private\n', encoding='utf-8')
    with patch.dict(os.environ, {}, clear=True):
        launcher().configure(tmp_path / '.env', root=tmp_path)
        assert os.environ['HUS_LLM_API_KEY'] == 'fake-key'
        assert os.environ['HUS_LLM_ENABLED'] == 'true'
        assert os.environ['HUS_RETRIEVAL_MODE'] == 'lexical'
        assert os.environ['HUS_RAG_ROOT'] == str(tmp_path / 'data/hus/rag')
        assert 'DB_PASSWORD' not in os.environ
        assert 'generativelanguage.googleapis.com' in os.environ['HUS_LLM_BASE_URL']


def test_existing_process_key_takes_precedence(tmp_path):
    (tmp_path / '.env').write_text('HUS_LLM_API_KEY=fake-file-key\n', encoding='utf-8')
    with patch.dict(os.environ, {'HUS_LLM_API_KEY': 'fake-process-key'}, clear=True):
        launcher().configure(tmp_path / '.env', root=tmp_path)
        assert os.environ['HUS_LLM_API_KEY'] == 'fake-process-key'


def test_missing_key_fails_without_provider(tmp_path):
    with patch.dict(os.environ, {}, clear=True):
        with pytest.raises(ValueError, match='HUS_LLM_API_KEY'):
            launcher().configure(tmp_path / '.env', root=tmp_path)


def test_main_starts_loopback_server_without_printing_key(tmp_path, monkeypatch, capsys):
    import uvicorn
    module = launcher()
    (tmp_path / '.env').write_text('HUS_LLM_API_KEY=fake-key\n', encoding='utf-8')
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    calls = []
    monkeypatch.setattr(uvicorn, 'run', lambda *args, **kwargs: calls.append((args, kwargs)))
    with patch.dict(os.environ, {}, clear=True):
        module.main([])
    assert calls[0][0] == ('app.hus.demo:app',)
    assert calls[0][1]['host'] == '127.0.0.1'
    assert calls[0][1]['port'] == 8011
    assert 'fake-key' not in capsys.readouterr().out


def test_invalid_configuration_error_does_not_echo_key(tmp_path, capsys, monkeypatch):
    module = launcher()
    (tmp_path / '.env').write_text('HUS_LLM_API_KEY="fake secret"\n', encoding='utf-8')
    monkeypatch.setattr(module, 'ROOT', tmp_path)
    with patch.dict(os.environ, {}, clear=True), pytest.raises(SystemExit):
        module.main([])
    assert 'fake secret' not in capsys.readouterr().err
