import pytest
from unittest.mock import AsyncMock

from sdk.verdant.client import VerdantClient
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
