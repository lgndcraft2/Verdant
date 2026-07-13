import pytest
from unittest.mock import AsyncMock

from sdk.verdant.client import VerdantAPIError, VerdantClient
from sdk.verdant.models import ContextType

@pytest.mark.asyncio
async def test_verdant_client_wrap(mocker):
    # Mock the pipeline
    mock_pipeline = mocker.patch("sdk.verdant.client.VerdantPipeline")
    mock_pipeline_instance = mock_pipeline.return_value
    
    mock_result = AsyncMock()
    mock_result.output = "Test Output"
    mock_result.trust_score = 85
    mock_pipeline_instance.run = mocker.AsyncMock(return_value=mock_result)
    
    client = VerdantClient(api_key="test_key")
    
    # Dummy function
    async def dummy_ai_call(prompt: str):
        return "Test Output"
        
    result = await client.wrap(
        dummy_ai_call,
        context_type=ContextType.hiring,
        input_text="Test Input",
        prompt="Test Input"
    )
    
    assert result.output == "Test Output"
    assert result.trust_score == 85
    
    mock_pipeline_instance.run.assert_called_once_with(
        fn=dummy_ai_call,
        context_type=ContextType.hiring,
        input_text="Test Input",
        fn_kwargs={"prompt": "Test Input"},
        metadata=None
    )


@pytest.mark.asyncio
async def test_wrap_remote_analysis_runs_fn_locally_and_posts_output(mocker):
    # Hosted config so remote analysis is allowed.
    client = VerdantClient(api_key="vd_live_x", base_url="https://api.example")

    captured = {}
    final = mocker.MagicMock(name="final_result")
    server_result = mocker.MagicMock(name="server_result")
    server_result.model_copy.return_value = final

    async def fake_post(path, payload):
        captured["path"] = path
        captured["payload"] = payload
        return server_result

    mocker.patch.object(client, "_post_pipeline", new=mocker.AsyncMock(side_effect=fake_post))

    def my_model(**kwargs):
        return "the model answer"

    result = await client.wrap(
        my_model,
        context_type=ContextType.hiring,
        input_text="q",
        remote_analysis=True,
        contents="q",
    )

    # fn ran locally; its output was sent to the analyze endpoint.
    assert captured["path"] == "/pipeline/analyze"
    assert captured["payload"]["output_text"] == "the model answer"
    assert captured["payload"]["input_text"] == "q"
    assert captured["payload"]["context_type"] == "hiring"
    # The caller's own output is attached back onto the server's result.
    server_result.model_copy.assert_called_once_with(update={"output": "the model answer"})
    assert result is final


@pytest.mark.asyncio
async def test_wrap_remote_analysis_requires_hosted():
    client = VerdantClient(api_key="vd_live_x")  # no base_url -> not hosted
    with pytest.raises(VerdantAPIError):
        await client.wrap(
            lambda **k: "x",
            context_type="hiring",
            input_text="q",
            remote_analysis=True,
        )
