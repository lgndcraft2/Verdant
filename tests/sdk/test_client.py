import pytest

from sdk.verdant.client import VerdantAPIError, VerdantClient
from sdk.verdant.config import Settings
from sdk.verdant.models import ContextType


@pytest.mark.asyncio
async def test_wrap_runs_fn_locally_and_posts_output(mocker):
    client = VerdantClient(api_key="vd_live_x")

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
async def test_run_posts_to_pipeline_run(mocker):
    client = VerdantClient(api_key="vd_live_x")
    mocker.patch.object(client, "_post_pipeline", new=mocker.AsyncMock(return_value="RESULT"))

    result = await client.run(context_type=ContextType.hiring, input_text="q")

    client._post_pipeline.assert_awaited_once()
    path, payload = client._post_pipeline.await_args.args
    assert path == "/pipeline/run"
    assert payload["context_type"] == "hiring"
    assert payload["input_text"] == "q"
    assert result == "RESULT"


@pytest.mark.asyncio
async def test_wrap_requires_key():
    client = VerdantClient(settings=Settings(verdant_api_key=""))
    with pytest.raises(VerdantAPIError):
        await client.wrap(lambda **k: "x", context_type="hiring", input_text="q")


@pytest.mark.asyncio
async def test_run_requires_key():
    client = VerdantClient(settings=Settings(verdant_api_key=""))
    with pytest.raises(VerdantAPIError):
        await client.run(context_type="hiring", input_text="q")


def test_default_api_url_is_baked_in():
    # A key alone is enough — the URL is baked in, no base_url needed.
    client = VerdantClient(api_key="vd_live_x")
    assert client.settings.verdant_api_url  # non-empty default
    assert client.settings.verdant_api_key == "vd_live_x"


@pytest.mark.asyncio
async def test_wrap_keeps_app_up_when_fn_raises(mocker):
    client = VerdantClient(api_key="vd_live_x")
    captured = {}

    async def fake_post(path, payload):
        captured["payload"] = payload
        return mocker.MagicMock(model_copy=mocker.MagicMock(return_value="ok"))

    mocker.patch.object(client, "_post_pipeline", new=mocker.AsyncMock(side_effect=fake_post))

    def boom(**kwargs):
        raise RuntimeError("model exploded")

    result = await client.wrap(boom, context_type="hiring", input_text="q")

    # The error is captured and still sent for analysis; the app doesn't crash.
    assert "model exploded" in captured["payload"]["output_text"]
    assert result == "ok"
