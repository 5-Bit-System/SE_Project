"""Install/check the adjacent HUS ZIPs offline; standard library only."""
import argparse
import hashlib
import json
import platform
import stat
import struct
import subprocess
import sys
import zipfile
from datetime import datetime, timezone
from pathlib import Path, PurePosixPath

ARCHIVES = {}  # Filled with verified ZIP hashes by build_transfer().


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def write_json(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False, sort_keys=True, indent=2)+'\n', encoding='utf-8')


def checked_extract(archive_path, destination):
    """Verify names before extraction; pinned ZIP hashes do not excuse path escapes."""
    destination = Path(destination).resolve()
    with zipfile.ZipFile(archive_path) as archive:
        names = archive.namelist()
        if len(names) != len(set(names)) or len(names) > 10000:
            raise ValueError('Invalid archive inventory')
        if sum(info.file_size for info in archive.infolist()) > 512 * 1024 * 1024:
            raise ValueError('Archive exceeds the submission size limit')
        for info in archive.infolist():
            path = PurePosixPath(info.filename)
            if (info.orig_filename != info.filename or path.is_absolute() or '\\' in info.filename or ':' in info.filename
                    or path.as_posix() != info.filename.rstrip('/')
                    or any(part in {'.', '..', '.git', '.venv'} or part.startswith('.env') for part in path.parts)
                    or stat.S_ISLNK(info.external_attr >> 16)
                    or not (destination / info.filename).resolve().is_relative_to(destination)):
                raise ValueError('Unsafe archive path')
        archive.extractall(destination)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--root', type=Path, default=Path(__file__).parent/'hus-demo-target')
    parser.add_argument('--run-demo', action='store_true')
    args = parser.parse_args(argv)
    bundle = Path(__file__).resolve().parent
    target = args.root.resolve()
    if target.exists():
        parser.error('Choose a fresh --root directory; existing files are never overwritten.')
    receipt = target/'target-receipt'
    receipt.mkdir(parents=True, exist_ok=False)
    report = {'schema_version': 'hus-target-install-1.0', 'started_at': datetime.now(timezone.utc).isoformat(),
              'status': 'running', 'target_checks_passed': False, 'manual_operator_acceptance': False,
              'llm_enabled': False, 'public_deployment': False, 'script_sha256': sha(__file__)}
    app = target/'demo'
    python = app/'.venv/Scripts/python.exe'

    def run(command, name):
        command = [command[0], '-X', 'utf8', *command[1:]]
        result = subprocess.run(command, capture_output=True, text=True, encoding='utf-8', errors='replace')
        (receipt/(name+'.stdout.txt')).write_text(result.stdout, encoding='utf-8')
        (receipt/(name+'.stderr.txt')).write_text(result.stderr, encoding='utf-8')
        if result.returncode:
            raise RuntimeError(name+' failed; keep the receipt logs.')
        return result.stdout

    try:
        if set(ARCHIVES) != {'hus-rag-demo.zip', 'wheelhouse-win-py311.zip'}:
            raise RuntimeError('Use the pinned CHECK_TARGET.py supplied with the transfer kit.')
        report['python'] = {'version': platform.python_version(), 'system': platform.system(),
                            'machine': platform.machine(), 'bits': struct.calcsize('P')*8,
                            'implementation': platform.python_implementation()}
        if (sys.version_info[:2] != (3, 11) or platform.system() != 'Windows'
                or platform.machine().lower() not in {'amd64', 'x86_64'} or struct.calcsize('P') != 8
                or platform.python_implementation() != 'CPython'):
            raise RuntimeError('This wheel bundle requires Windows amd64 and 64-bit CPython 3.11.')
        for name, expected in ARCHIVES.items():
            if sha(bundle/name) != expected:
                raise RuntimeError('Archive SHA mismatch: '+name)
        report['archive_sha256'] = ARCHIVES
        checked_extract(bundle/'hus-rag-demo.zip', app)
        checked_extract(bundle/'wheelhouse-win-py311.zip', target)
        package = json.loads((app/'SUBMISSION_MANIFEST.json').read_bytes())
        wheels = json.loads((target/'wheelhouse/WHEELHOUSE_MANIFEST.json').read_bytes())
        for folder, inventory in ((app, package['files_sha256']), (target/'wheelhouse', wheels['files_sha256'])):
            for name, expected in inventory.items():
                if sha(folder/name) != expected:
                    raise RuntimeError('Extracted SHA mismatch: '+name)
        run([sys.executable, '-I', '-m', 'venv', str(app/'.venv')], 'create-venv')
        run([str(python), '-I', '-m', 'pip', '--isolated', '--disable-pip-version-check', 'install',
             '--no-cache-dir', '--no-index', '--find-links', str(target/'wheelhouse'),
             '-r', str(app/'requirements-rag-demo.txt'), '-c', str(app/'requirements-lock.txt')], 'install')
        run([str(python), '-I', '-m', 'pip', '--isolated', '--disable-pip-version-check', 'check'], 'pip-check')
        environment_code = (
            "import importlib.metadata as m,json,platform,site,sys; "
            "print(json.dumps({'python':platform.python_version(),'platform':platform.platform(),"
            "'architecture':platform.machine(),'fresh_venv':sys.prefix!=sys.base_prefix,"
            "'user_site_enabled':site.ENABLE_USER_SITE,'packages':{d.metadata['Name']:d.version for d in m.distributions()}}))")
        environment = json.loads(run([str(python), '-I', '-c', environment_code], 'environment'))
        write_json(receipt/'environment.json', environment)
        if not environment['fresh_venv'] or environment['user_site_enabled']:
            raise RuntimeError('The Python environment is not isolated.')
        check_code = "import sys; sys.path.insert(0,sys.argv[1]); from tools.run_hus_submission import main; main(['--check'])"
        api = json.loads(run([str(python), '-I', '-B', '-c', check_code, str(app)], 'api-check'))
        write_json(receipt/'api-check.json', api)
        if (api.get('passed') is not True or api['menu_items'] != 2124 or len(api['cases']) != 20
                or api['profile']['llm_enabled'] is not False or api['release_id'] != 'hus-data-20261111-v4'):
            raise RuntimeError('API check output differs from the submission profile.')
        report.update(target_checks_passed=True, status='checks_passed_manual_operator_review_pending',
                      api_cases=20, menu_items=2124, release_id=api['release_id'],
                      browser_and_rollback_on_this_machine='pending manual check',
                      a7='Recall24/24, completeness34/36, controls11/12; Q002/Q003/Q011 remain. AI review, human0.')
    except Exception as error:
        report.update(status='failed', error=str(error))
    finally:
        report['finished_at'] = datetime.now(timezone.utc).isoformat()
        write_json(receipt/'report.json', report)
        write_json(receipt/'manifest.json', {'schema_version': 'hus-target-receipt-1.0',
            'files_sha256': {p.name: sha(p) for p in sorted(receipt.iterdir()) if p.is_file()}})
    print(json.dumps({'receipt': str(receipt), 'status': report['status']}))
    if not report['target_checks_passed']:
        return 1
    if args.run_demo:
        print('Open http://127.0.0.1:8011/ . Stop with Ctrl+C; manual acceptance remains open.')
        serve = "import sys; sys.path.insert(0,sys.argv[1]); from tools.run_hus_submission import main; main([])"
        return subprocess.call([str(python), '-X', 'utf8', '-I', '-B', '-c', serve, str(app)])
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
