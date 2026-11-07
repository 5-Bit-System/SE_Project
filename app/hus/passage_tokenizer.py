"""Explicit tokenizer preparation; lexical runtime never imports this dependency."""
import hashlib
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from urllib.request import urlopen

from app.hus.vector_contract import HEX64, digest_json

TOKENIZERS_VERSION = '0.23.3'
MODEL_ID = 'intfloat/multilingual-e5-small'
REVISION = '614241f622f53c4eeff9890bdc4f31cfecc418b3'


def _artifact(contract):
    if (not isinstance(contract, dict)
            or contract.get('contract_id') != digest_json({k: v for k, v in contract.items() if k != 'contract_id'})
            or contract.get('stage') != 'contract_only' or contract.get('index_built') is not False):
        raise ValueError('Invalid or unverified V1 contract identity')
    model = contract.get('model') if isinstance(contract.get('model'), dict) else {}
    if model.get('model_id') != MODEL_ID or model.get('revision') != REVISION or model.get('tokenizer_revision') != REVISION:
        raise ValueError('Contract model/tokenizer revision does not match pinned V1 identity')
    artifact = next((a for a in model.get('artifacts', []) if isinstance(a, dict) and a.get('path') == 'tokenizer.json'), None)
    expected_url = f'https://huggingface.co/{MODEL_ID}/resolve/{REVISION}/tokenizer.json'
    if (artifact is None or artifact.get('url') != expected_url
            or type(artifact.get('bytes')) is not int or artifact['bytes'] <= 0
            or not HEX64.fullmatch(str(artifact.get('sha256', '')))):
        raise ValueError('Invalid pinned tokenizer artifact in contract')
    return artifact


def _check(raw, artifact):
    if len(raw) != artifact['bytes'] or hashlib.sha256(raw).hexdigest() != artifact['sha256']:
        raise ValueError('Pinned tokenizer size/checksum differs')


def fetch_tokenizer(folder, contract):
    """Only this explicit action accesses the network; never fetch weights."""
    folder = Path(folder)
    if folder.exists():
        raise ValueError('Choose a fresh tokenizer cache directory')
    artifact = _artifact(contract)
    with urlopen(artifact['url'], timeout=120) as response:
        raw = response.read(artifact['bytes'] + 1)
    _check(raw, artifact)
    folder.mkdir(parents=True)
    (folder / 'tokenizer.json').write_bytes(raw)


class LocalTokenizer:
    """Native serialized fast-tokenizer graph, original Unicode character offsets."""

    def __init__(self, backend, identity):
        self._backend = backend
        self.identity = identity

    def encode(self, text, *, add_special_tokens=True):
        if self._backend.truncation is not None or self._backend.padding is not None:
            raise ValueError('Padding/truncation must remain disabled')
        result = self._backend.encode(text, add_special_tokens=add_special_tokens)
        if result.overflowing:
            raise ValueError('Unexpected tokenizer truncation/overflow')
        return result


def load_tokenizer(folder, contract):
    """Fail closed on missing/corrupt cache before importing optional native code."""
    artifact = _artifact(contract)
    path = Path(folder) / 'tokenizer.json'
    if not path.is_file():
        raise ValueError('Pinned tokenizer cache missing; explicitly fetch it first')
    raw = path.read_bytes()
    _check(raw, artifact)
    try:
        installed = version('tokenizers')
    except PackageNotFoundError as exc:
        raise ValueError(f'Requires locked tokenizers=={TOKENIZERS_VERSION}') from exc
    if installed != TOKENIZERS_VERSION:
        raise ValueError(f'Requires locked tokenizers=={TOKENIZERS_VERSION}')
    from tokenizers import Tokenizer
    backend = Tokenizer.from_str(raw.decode('utf-8'))
    backend.no_truncation()
    backend.no_padding()
    identity = {'backend': 'tokenizers.Tokenizer.from_str', 'version': TOKENIZERS_VERSION,
                'model_id': contract['model']['model_id'], 'revision': contract['model']['tokenizer_revision'],
                'tokenizer_json_sha256': hashlib.sha256(raw).hexdigest(), 'tokenizer_json_bytes': len(raw),
                'configuration_sha256': digest_json({'truncation': None, 'padding': None}),
                'transformers_inference_compatibility_tested': False}
    return LocalTokenizer(backend, identity)
