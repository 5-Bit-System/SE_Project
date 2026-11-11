"""Local tokenizer validation never downloads implicitly or imports ML at startup."""
import hashlib
import importlib
import importlib.util
from pathlib import Path

import pytest

from app.hus.vector_contract import ROOT, build_contract


def module():
    assert importlib.util.find_spec('app.hus.passage_tokenizer'), 'V2 tokenizer adapter missing'
    return importlib.import_module('app.hus.passage_tokenizer')


@pytest.fixture(scope='module')
def contract(historical_v3_data):
    return build_contract(historical_v3_data)[0]


def test_missing_cache_fails_before_any_optional_import(tmp_path, contract):
    with pytest.raises(ValueError, match='tokenizer.*missing'):
        module().load_tokenizer(tmp_path, contract)


def test_corrupt_cache_is_rejected_before_optional_import(tmp_path, contract):
    (tmp_path / 'tokenizer.json').write_text('{}')
    with pytest.raises(ValueError, match='checksum|size'):
        module().load_tokenizer(tmp_path, contract)


def test_fetch_only_pinned_graph_and_verifies_before_writing(tmp_path, contract, monkeypatch):
    m = module()
    raw = b'{"test": "fixture"}'
    from copy import deepcopy
    fixture = deepcopy(contract)
    artifact = next(a for a in fixture['model']['artifacts'] if a['path'] == 'tokenizer.json')
    artifact.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    from app.hus.vector_contract import digest_json
    fixture['contract_id'] = digest_json({k: v for k, v in fixture.items() if k != 'contract_id'})
    from io import BytesIO
    calls = []
    def fetch(url, **kwargs):
        calls.append(url)
        return BytesIO(raw)
    monkeypatch.setattr(m, 'urlopen', fetch)
    target = tmp_path / 'cache'
    m.fetch_tokenizer(target, fixture)
    assert (target / 'tokenizer.json').read_bytes() == raw
    assert calls == [artifact['url']]
    with pytest.raises(ValueError, match='fresh'):
        m.fetch_tokenizer(target, fixture)


def test_bad_download_does_not_create_usable_cache(tmp_path, contract, monkeypatch):
    m = module()
    from io import BytesIO
    monkeypatch.setattr(m, 'urlopen', lambda *a, **kw: BytesIO(b'bad'))
    with pytest.raises(ValueError, match='checksum|size'):
        m.fetch_tokenizer(tmp_path / 'cache', contract)
    assert not (tmp_path / 'cache/tokenizer.json').exists()


def test_native_adapter_module_has_no_ml_import_side_effects():
    import subprocess
    import sys
    code = ("import sys; import app.hus.passage_tokenizer; import app.hus.passages; "
            "assert not ({'torch','transformers','chromadb','tokenizers'} & set(sys.modules))")
    assert subprocess.run([sys.executable, '-c', code], cwd=ROOT, capture_output=True).returncode == 0


def test_optional_lock_stays_at_previously_resolved_tokenizer_version():
    assert 'tokenizers==0.23.3' in Path(ROOT / 'requirements-rag-vector-lock.txt').read_text()


def test_unverified_or_tampered_contract_is_rejected_before_network_or_load(tmp_path, contract):
    from copy import deepcopy

    from app.hus.vector_contract import digest_json
    m = module()
    bad_id = deepcopy(contract)
    bad_id['contract_id'] = '0' * 64
    with pytest.raises(ValueError, match='contract'):
        m.fetch_tokenizer(tmp_path / 'c1', bad_id)
    bad_url = deepcopy(contract)
    art = next(a for a in bad_url['model']['artifacts'] if a['path'] == 'tokenizer.json')
    art['url'] = 'https://example.com/tokenizer.json'
    bad_url['contract_id'] = digest_json({k: v for k, v in bad_url.items() if k != 'contract_id'})
    with pytest.raises(ValueError, match='artifact|url|contract'):
        m.fetch_tokenizer(tmp_path / 'c2', bad_url)


def test_absent_or_wrong_tokenizers_version_raises_value_error(tmp_path, contract, monkeypatch):
    from copy import deepcopy
    from importlib.metadata import PackageNotFoundError

    from app.hus.vector_contract import digest_json
    m = module()
    raw = b'{"test": "fixture"}'
    fixture = deepcopy(contract)
    artifact = next(a for a in fixture['model']['artifacts'] if a['path'] == 'tokenizer.json')
    artifact.update(bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
    fixture['contract_id'] = digest_json({k: v for k, v in fixture.items() if k != 'contract_id'})
    (tmp_path / 'tokenizer.json').write_bytes(raw)

    def missing(_name):
        raise PackageNotFoundError('tokenizers')

    monkeypatch.setattr(m, 'version', missing)
    with pytest.raises(ValueError, match='tokenizers==0.23.3'):
        m.load_tokenizer(tmp_path, fixture)
    monkeypatch.setattr(m, 'version', lambda _name: '0.20.0')
    with pytest.raises(ValueError, match='tokenizers==0.23.3'):
        m.load_tokenizer(tmp_path, fixture)
