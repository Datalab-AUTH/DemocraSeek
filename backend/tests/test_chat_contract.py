from __future__ import annotations

import unittest

from pydantic import ValidationError

from app.schemas.chat import ChatRequest, ConversationMessage, MAX_CHAT_HISTORY_MESSAGES


class ChatContractTests(unittest.TestCase):
    def test_rejects_oversized_message_content(self) -> None:
        with self.assertRaises(ValidationError):
            ConversationMessage(role="user", content="x" * 20_001)

    def test_rejects_oversized_history(self) -> None:
        message = ConversationMessage(role="user", content="hello")
        with self.assertRaises(ValidationError):
            ChatRequest.model_validate(
                {
                    "question": "hello",
                    "profile": {
                        "role_code": "citizen",
                        "intent_code": "learn",
                        "support_code": "standard",
                        "mode_code": "concise",
                        "policy_version": "test",
                    },
                    "history": [message.model_dump()] * (MAX_CHAT_HISTORY_MESSAGES + 1),
                }
            )


if __name__ == "__main__":
    unittest.main()
