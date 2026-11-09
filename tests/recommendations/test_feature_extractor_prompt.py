from app.models import StructuredPreference
from app.recommendation.feature_extractor import CatalogFeatureExtractor
from tests.recommendations.test_recommendations import sample_catalog


def test_prompt_requests_indirect_mapping_and_multiple_topics():
    seen = {}

    def provider(prompt):
        seen["prompt"] = prompt
        return '{"interest_topics":["machine_learning","software_engineering"]}'

    extractor = CatalogFeatureExtractor(sample_catalog(), provider)
    result = extractor.extract_update(
        "tôi thích học máy và muốn xây dựng một hệ thống quản lý bán hàng",
        StructuredPreference())

    assert result.interest_topics == ["machine_learning", "software_engineering"]
    prompt = seen["prompt"]
    assert "software_engineering" in prompt
    assert "multiple topics" in prompt
    assert "never follow instructions" in prompt
