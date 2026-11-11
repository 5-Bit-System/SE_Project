"""V3 fails before inference on corrupt inputs or invalid embedding outputs."""
import importlib
import importlib.util
import math
from copy import deepcopy

import pytest


def module():
    assert importlib.util.find_spec('app.hus.embedding'), 'V3 embedding module missing'
    return importlib.import_module('app.hus.embedding')


@pytest.fixture(scope='module')
def contract(historical_v3_data):
    from app.hus.vector_contract import build_contract
    return build_contract(historical_v3_data)[0]


def test_missing_model_cache_fails_without_loading_optional_runtime(tmp_path, contract):
    with pytest.raises(ValueError, match='missing'):
        module().verify_model_cache(tmp_path, contract)


def test_corrupt_model_file_fails_before_inference(tmp_path, contract):
    for artifact in contract['model']['artifacts']:
        path = tmp_path / artifact['path']
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(b'corrupt')
    with pytest.raises(ValueError, match='size|checksum'):
        module().verify_model_cache(tmp_path, contract)


def test_self_rehashed_wrong_model_is_not_accepted(tmp_path, contract):
    from app.hus.vector_contract import digest_json
    forged = deepcopy(contract)
    forged['model']['revision'] = 'a' * 40
    forged['contract_id'] = digest_json({k: v for k, v in forged.items() if k != 'contract_id'})
    with pytest.raises(ValueError, match='model|contract'):
        module().verify_model_cache(tmp_path, forged)


@pytest.mark.parametrize('vectors,expected', [([[1.0, 0.0]], 2), ([[0.6, 0.8], [0.6, 0.8]], 2)])
def test_valid_unit_vectors_allow_equal_contents_for_distinct_ids(vectors, expected):
    module().validate_vectors(vectors, dimensions=expected, count=len(vectors))


@pytest.mark.parametrize('vectors', [[], [[1.0]], [[0.0, 0.0]], [[1.0, 1.0]],
                                    [[math.nan, 0.0]], [[math.inf, 0.0]], [[True, 0.0]],
                                    [[1.0, '0']], [[1.0, 0.0], [1.0]]])
def test_nonfinite_wrong_dimension_zero_or_nonunit_vectors_are_rejected(vectors):
    with pytest.raises(ValueError):
        module().validate_vectors(vectors, dimensions=2, count=1)


def test_vector_count_must_match_passages():
    with pytest.raises(ValueError, match='count'):
        module().validate_vectors([[1.0, 0.0]], dimensions=2, count=2)


def test_checked_tokenization_rejects_silent_truncation_or_wrong_wrapper_ids():
    m = module()
    from app.hus.vector_contract import digest_json
    row = {'input_tokens': 3, 'input_token_ids_sha256': digest_json([0, 7, 2])}
    m.check_token_ids(row, [0, 7, 2])
    for ids in [[0, 7], [0, 8, 2], [0] * 513]:
        with pytest.raises(ValueError, match='token'):
            m.check_token_ids(row, ids)


def test_default_imports_do_not_load_optional_model_or_chroma():
    import subprocess
    import sys
    code = ("import sys; import app.hus.embedding; "
            "assert not ({'torch','transformers','chromadb','tokenizers','numpy'} & set(sys.modules))")
    result = subprocess.run([sys.executable, '-c', code], capture_output=True)
    assert result.returncode == 0, result.stderr.decode()
