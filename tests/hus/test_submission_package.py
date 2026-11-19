"""Submission boundary and artifact integrity, independent of RAG quality scores."""

import json
import zipfile
from pathlib import Path

import pytest

from tools import check_hus_submission_target as target_check
from tools import package_hus_demo as package
from tools import run_hus_submission as launcher


@pytest.mark.parametrize('name', ['.env', '.env.example', 'app/.env.key', '../key',
                                '/absolute', 'C:/key', 'a\\b', 'a/../b',
                                'a/./b', 'a//b', '.git/config', 'backups/file'])
def test_private_or_ambiguous_paths_rejected_without_reading(tmp_path, monkeypatch, name):
    monkeypatch.setattr(Path, 'read_bytes', lambda path: pytest.fail('Unsafe file was read'))
    with pytest.raises(ValueError, match='[Uu]nsafe|private'):
        package.read_public(tmp_path, name)


def test_launcher_overrides_inherited_settings_without_reading_env_files(monkeypatch):
    import os

    monkeypatch.setenv('HUS_LLM_ENABLED', 'true')
    monkeypatch.setenv('HUS_RETRIEVAL_MODE', 'vector')
    monkeypatch.setenv('HUS_RAG_ROOT', 'other-release')
    monkeypatch.setenv('HUS_LLM_API_KEY', 'test-key-not-for-output')
    monkeypatch.setattr(Path, 'read_bytes', lambda path: pytest.fail('Config file read'))
    launcher.configure()
    assert os.environ['HUS_LLM_ENABLED'] == 'false'
    assert os.environ['HUS_RETRIEVAL_MODE'] == 'lexical'
    assert os.environ['HUS_RAG_ROOT'] == str(launcher.ROOT / 'data/hus/rag')
    assert os.environ['HUS_LLM_API_KEY'] == 'test-key-not-for-output'


def test_public_inventory_excludes_private_product_and_cache_files():
    content = package.payloads()
    assert 'data/hus/rag/releases/hus-data-20261111-v4/manifest.json' in content
    assert 'data/hus/rag/releases/hus-data-20261031-v3/manifest.json' in content
    assert 'app/hus/demo.py' in content
    assert 'app/main.py' not in content
    assert not any(name.startswith(('database/', 'backups/', '.git/', '.env')) for name in content)
    assert not any('.env' in Path(name).parts or '__pycache__' in Path(name).parts for name in content)


def test_archive_is_reproducible_and_existing_file_is_preserved(tmp_path, monkeypatch):
    monkeypatch.setattr(package, 'payloads', lambda root: {'app/hus/demo.py': b'public'})
    first, second = tmp_path / 'first.zip', tmp_path / 'second.zip'
    a, b = package.build(first), package.build(second)
    assert a['zip_sha256'] == b['zip_sha256']
    with pytest.raises(ValueError, match='fresh ZIP'):
        package.build(first)
    assert package.verify(first) == a


def test_tampered_payload_is_rejected_even_with_same_inventory(tmp_path):
    path = tmp_path / 'tampered.zip'
    manifest = {'schema_version': 'hus-local-submission-1.0', 'release_id': package.RELEASES[1],
                'llm_enabled': False, 'retrieval': 'lexical',
                'files_sha256': {'README.md': package.sha(b'original')}}
    with zipfile.ZipFile(path, 'w') as archive:
        archive.writestr(package.MANIFEST, json.dumps(manifest))
        archive.writestr('README.md', b'changed')
    with pytest.raises(ValueError, match='hash differs'):
        package.verify(path)


@pytest.mark.parametrize('name', ['../escape', '/absolute', 'C:/escape', 'a\\escape', '.env',
                                'a/../escape', '.git/config', '.venv/secret'])
def test_target_checker_rejects_unsafe_archive_before_extracting(tmp_path, name):
    path = tmp_path / 'bad.zip'
    with zipfile.ZipFile(path, 'w') as archive:
        info = zipfile.ZipInfo('placeholder')
        info.filename = name  # Windows ZipInfo construction would normalize a backslash.
        archive.writestr(info, 'must not extract')
    output = tmp_path / 'output'
    with pytest.raises(ValueError, match='Unsafe'):
        target_check.checked_extract(path, output)
    assert not output.exists()


def test_transfer_kit_pins_exact_zip_hashes_and_reuses_wheels(tmp_path, monkeypatch):
    wheels = tmp_path / 'wheels.zip'
    inventory = {f'offline-{i}.whl': package.sha(str(i).encode()) for i in range(25)}
    with zipfile.ZipFile(wheels, 'w') as archive:
        for i, name in enumerate(inventory):
            archive.writestr('wheelhouse/' + name, str(i))
        archive.writestr('wheelhouse/WHEELHOUSE_MANIFEST.json', json.dumps({'files_sha256': inventory}))
    monkeypatch.setattr(package, 'payloads', lambda root: {'README.md': b'public fixture'})
    out = tmp_path / 'kit'
    result = package.build_transfer(out, wheels)
    assert result['actual_target_verified'] is False
    assert (out / 'wheelhouse-win-py311.zip').read_bytes() == wheels.read_bytes()
    checker = (out / 'CHECK_TARGET.py').read_text(encoding='utf-8')
    assert result['package']['zip_sha256'] in checker and package.sha(wheels.read_bytes()) in checker
    assert 'ARCHIVES = {}' not in checker
    manifest = json.loads((out / 'TRANSFER_MANIFEST.json').read_bytes())
    assert all(package.sha((out / name).read_bytes()) == checksum for name, checksum in manifest['files_sha256'].items())
    with pytest.raises(ValueError, match='fresh transfer'):
        package.build_transfer(out, wheels)


def test_target_checker_does_not_overwrite_existing_root(tmp_path):
    target = tmp_path / 'existing'
    target.mkdir()
    marker = target / 'keep.txt'
    marker.write_text('keep')
    with pytest.raises(SystemExit) as error:
        target_check.main(['--root', str(target)])
    assert error.value.code == 2 and marker.read_text() == 'keep'
    assert not (target / 'target-receipt').exists()


def test_unpinned_template_fails_with_receipt_instead_of_installing(tmp_path):
    target = tmp_path / 'new-target'
    assert target_check.main(['--root', str(target)]) == 1
    report = json.loads((target / 'target-receipt/report.json').read_bytes())
    assert report['status'] == 'failed' and report['target_checks_passed'] is False
    assert report['manual_operator_acceptance'] is False
