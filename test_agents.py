"""Quick integration test for the 4-agent system."""
import asyncio
from app.agents.devsecops_agent import devsecops_agent
from app.agents.critic_agent import phoenix_client


async def test_devsecops():
    ctx = devsecops_agent.build_error_context(
        RuntimeError("Test timeout spike"),
        request_id="test-123",
        failed_step="reasoning",
    )
    result = await devsecops_agent.handle_system_exception(ctx)
    print(f"DevSecOps: Incident created, severity={result['severity']}")
    print(f"  GitLab Issue URL: {result['gitlab_issue']['web_url']}")


async def test_phoenix():
    await phoenix_client.log_trace(
        trace_id="test-trace-001",
        span_name="test_reasoning",
        input_data="test input",
        output_data="test output",
        latency_ms=150.0,
    )
    eval_result = await phoenix_client.evaluate_confidence(
        {"confidence_score": 0.7, "symptoms": ["chest pain"], "professional_summary": "Patient presents with chest pain."},
        "Patient reports chest pain radiating to left arm. Urgent evaluation needed.",
    )
    print(f"Phoenix: Confidence={eval_result['data']['confidence_score']}, Issues={eval_result['data']['issue_count']}")

    halluc = await phoenix_client.detect_hallucination(
        {"medications": ["Aspirin", "FakeDrug123"]},
        "Patient takes aspirin daily.",
    )
    print(f"Phoenix: Hallucination flags={halluc['data']['total_flags']}, Risk={halluc['data']['hallucination_risk']}")


async def main():
    print("=== Agent Integration Test ===")
    await test_devsecops()
    await test_phoenix()
    print("=== ALL TESTS PASSED ===")


asyncio.run(main())
