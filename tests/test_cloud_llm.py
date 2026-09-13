import pytest
from src.domain.entities.decision import ActionDecision, ActionType
from src.infrastructure.llm.cloud_llm_client import CloudLLMClient


def test_cloud_llm_unconfigured():
    client = CloudLLMClient(api_key="")
    decision = client.evaluate_and_generate("Sample context", ActionType.COMMENT)
    assert decision.should_act is False
    assert decision.action_type == ActionType.SKIP
    assert "No OpenRouter API key" in decision.reason


def test_cloud_llm_empty_context():
    client = CloudLLMClient(api_key="sk-test-fake-key")
    decision = client.evaluate_and_generate("   ", ActionType.COMMENT)
    assert decision.should_act is False
    assert decision.action_type == ActionType.SKIP


def test_cloud_llm_json_parsing():
    client = CloudLLMClient(api_key="sk-test")

    # Plain JSON
    raw_plain = '{"should_act": true, "reason": "Thảo luận hay", "text": "Đồng tình với bạn!"}'
    d1 = client._parse_json_decision(raw_plain, ActionType.COMMENT)
    assert d1.should_act is True
    assert d1.action_type == ActionType.COMMENT
    assert d1.text == "Đồng tình với bạn!"
    assert d1.reason == "Thảo luận hay"

    # Markdown wrapped JSON
    raw_md = '```json\n{"should_act": false, "reason": "Bài quảng cáo", "text": ""}\n```'
    d2 = client._parse_json_decision(raw_md, ActionType.COMMENT)
    assert d2.should_act is False
    assert d2.action_type == ActionType.SKIP
    assert d2.reason == "Bài quảng cáo"

    # Malformed JSON
    raw_bad = "Đây là văn bản không phải JSON"
    d3 = client._parse_json_decision(raw_bad, ActionType.COMMENT)
    assert d3.should_act is False
    assert d3.action_type == ActionType.SKIP


def test_cloud_llm_live_api_call():
    client = CloudLLMClient()
    if not client.is_configured():
        pytest.skip("OpenRouter API key not configured in .env")

    context = "Hôm nay thời tiết Hà Nội mùa thu đẹp quá, vừa se se lạnh vừa có nắng nhẹ. Có ai đi cafe không?"
    decision = client.evaluate_and_generate(context, ActionType.COMMENT)

    assert isinstance(decision, ActionDecision)
    assert isinstance(decision.should_act, bool)
    assert len(decision.reason) > 0
    if decision.should_act:
        assert len(decision.text) > 0
        assert decision.action_type == ActionType.COMMENT
