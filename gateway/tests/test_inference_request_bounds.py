import pytest
from inference_gateway.models import ChatCompletionRequest, ChatMessage
from pydantic import ValidationError


def test_chat_request_bounds_message_count_and_content_bytes():
    message = ChatMessage(role="user", content="a" * 8192)
    with pytest.raises(ValidationError):
        ChatMessage(role="user", content="a" * 8193)
    with pytest.raises(ValidationError):
        ChatCompletionRequest(model="model", messages=[message] * 33)
    with pytest.raises(ValidationError, match="combined message content"):
        ChatCompletionRequest(
            model="model",
            messages=[
                *[ChatMessage(role="user", content="a" * 8192) for _ in range(8)],
                ChatMessage(role="user", content="a"),
            ],
        )
