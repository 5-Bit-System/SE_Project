"""Verified local CPU embeddings; optional ML libraries load only on explicit use."""
import hashlib
import math
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from urllib.request import urlopen

from app.hus.vector_contract import ROOT, _lock_versions, _model, digest, digest_json, encoded


def _spec(contract):
    if (contract.get('contract_id') != digest_json({k: v for k, v in contract.items() if k != 'contract_id'})
            or encoded(contract.get('model')) != encoded(_model(ROOT))):
        raise ValueError('Invalid frozen model/contract identity')
    return contract['model']


def verify_model_cache(folder, contract):
    folder, model = Path(folder), _spec(contract)
    verified = {}
    for artifact in model['artifacts']:
        path = folder / artifact['path']
        if not path.is_file():
            raise ValueError(f'Model artifact missing: {artifact["path"]}')
        if path.stat().st_size != artifact['bytes'] or digest(path) != artifact['sha256']:
            raise ValueError(f'Model artifact size/checksum differs: {artifact["path"]}')
        verified[artifact['path']] = {'sha256': artifact['sha256'], 'bytes': artifact['bytes']}
    return verified


def fetch_model(folder, contract):
    """Explicit network action, resumable only for already verified whole files.

    Temporary partial files are owned by this invocation and never consumed.
    Corrupt existing final files fail instead of being overwritten.
    """
    import tempfile
    folder, model = Path(folder), _spec(contract)
    folder.mkdir(parents=True, exist_ok=True)
    for artifact in model['artifacts']:
        path = folder / artifact['path']
        if path.exists():
            if path.stat().st_size != artifact['bytes'] or digest(path) != artifact['sha256']:
                raise ValueError(f'Existing model artifact checksum differs: {artifact["path"]}')
            continue
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = None
        try:
            hasher, size = hashlib.sha256(), 0
            with urlopen(artifact['url'], timeout=120) as response, tempfile.NamedTemporaryFile(
                dir=path.parent, prefix='.hus-download-', delete=False
            ) as stream:
                temporary = Path(stream.name)
                while block := response.read(1024 * 1024):
                    size += len(block)
                    if size > artifact['bytes']:
                        raise ValueError('Model artifact exceeds pinned size')
                    hasher.update(block)
                    stream.write(block)
            if size != artifact['bytes'] or hasher.hexdigest() != artifact['sha256']:
                raise ValueError('Downloaded model artifact size/checksum differs')
            # rename refuses to replace an existing destination on Windows.
            if path.exists():
                raise ValueError('Model artifact appeared during download')
            temporary.rename(path)
        finally:
            if temporary is not None and temporary.exists():
                temporary.unlink()
    return verify_model_cache(folder, contract)


def validate_vectors(vectors, *, dimensions=384, count):
    if not vectors or len(vectors) != count:
        raise ValueError('Embedding count differs from passage count')
    for vector in vectors:
        if len(vector) != dimensions or any(type(x) not in {int, float} or not math.isfinite(x) for x in vector):
            raise ValueError('Embedding has invalid dimension/type/nonfinite value')
        norm = math.sqrt(sum(x * x for x in vector))
        if abs(norm - 1.0) > 1e-5:
            raise ValueError('Embedding must be nonzero and L2-normalized')


def check_token_ids(row, ids):
    if (len(ids) > 512 or len(ids) != row['input_tokens']
            or digest_json(ids) != row['input_token_ids_sha256']):
        raise ValueError('Inference tokenizer token IDs/budget differ from V2')


def runtime_versions(contract):
    lock = ROOT / contract['dependencies']['lock_path']
    if digest(lock) != contract['dependencies']['lock_sha256']:
        raise ValueError('Optional dependency lock differs from V1')
    expected = _lock_versions(lock.read_text(encoding='utf-8'))
    for name, wanted in expected.items():
        try:
            installed = version(name)
        except PackageNotFoundError as exc:
            raise ValueError(f'Missing locked optional dependency: {name}=={wanted}') from exc
        if installed != wanted:
            raise ValueError(f'Optional dependency version differs: {name}')
    return expected


def masked_mean(hidden, mask):
    """Exclude padding, include actual prefix/content/special tokens as E5 does."""
    expanded = mask.unsqueeze(-1).bool()
    return hidden.masked_fill(~expanded, 0.0).sum(dim=1) / expanded.sum(dim=1).clamp(min=1)


class LocalE5Encoder:
    def __init__(self, folder, contract):
        artifacts = verify_model_cache(folder, contract)
        packages = runtime_versions(contract)
        import torch
        from transformers import AutoModel, PreTrainedTokenizerFast
        self.torch = torch
        torch.set_num_threads(2)
        torch.use_deterministic_algorithms(True)
        # XLMRobertaTokenizer in this locked Transformers version rebuilds its
        # whitespace pre-tokenizer from SentencePiece and differs from V2.
        # Load the hash-verified serialized graph without that class override.
        self.tokenizer = PreTrainedTokenizerFast(
            tokenizer_file=str(Path(folder) / 'tokenizer.json'), bos_token='<s>', eos_token='</s>',
            unk_token='<unk>', pad_token='<pad>', cls_token='<s>', sep_token='</s>', mask_token='<mask>',
            model_max_length=512,
        )
        if not self.tokenizer.is_fast:
            raise ValueError('V3 requires the verified fast tokenizer')
        self.model = AutoModel.from_pretrained(str(folder), local_files_only=True, trust_remote_code=False,
                                              use_safetensors=True, dtype=torch.float32, attn_implementation='eager')
        self.model.to(device='cpu', dtype=torch.float32).eval()
        if self.model.config.hidden_size != 384:
            raise ValueError('Model hidden size differs from V1')
        self.identity = {'model_id': contract['model']['model_id'], 'revision': contract['model']['revision'],
                         'artifacts_verified': artifacts, 'packages': packages,
                         'pooling': 'attention_mask_mean', 'normalize': 'l2', 'dtype': 'float32',
                         'device': 'cpu', 'dimensions': 384, 'threads': 2,
                         'attention_implementation': 'eager', 'deterministic_algorithms': True,
                         'tokenizer_fast': True, 'silent_truncation': False,
                         'inference_tokenizer': 'PreTrainedTokenizerFast(pinned tokenizer.json)',
                         'auto_tokenizer_default_compatible': False}

    def check_passages(self, rows):
        for row in rows:
            ids = self.tokenizer(row['embedding_text'], truncation=False, padding=False,
                                 add_special_tokens=True)['input_ids']
            check_token_ids(row, ids)

    def encode(self, rows, *, batch_size=16):
        if type(batch_size) is not int or not 1 <= batch_size <= 64 or not rows:
            raise ValueError('Invalid embedding batch/rows')
        self.check_passages(rows)
        vectors = []
        torch = self.torch
        with torch.inference_mode():
            for start in range(0, len(rows), batch_size):
                batch = rows[start:start + batch_size]
                inputs = self.tokenizer([r['embedding_text'] for r in batch], padding=True,
                                        truncation=False, return_tensors='pt', return_token_type_ids=False)
                for row, ids, mask in zip(batch, inputs['input_ids'], inputs['attention_mask'], strict=True):
                    check_token_ids(row, ids[mask.bool()].tolist())
                hidden = self.model(**inputs).last_hidden_state
                pooled = masked_mean(hidden, inputs['attention_mask'])
                normalized = torch.nn.functional.normalize(pooled, p=2, dim=1)
                vectors.extend(normalized.to(dtype=torch.float32).cpu().tolist())
        validate_vectors(vectors, dimensions=384, count=len(rows))
        self.identity['transformers_inference_compatibility_tested'] = True
        return vectors
