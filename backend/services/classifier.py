import json
import anthropic

from backend.core.config import settings
from backend.prompts.response_prompts import classification_prompt


class IntentClassifier:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def classify(self, message: str) -> str:
        response = self.client.messages.create(
            model=settings.CLAUDE_MODEL,
            max_tokens=50,
            temperature=0,
            messages=[{"role": "user", "content": classification_prompt(message)}]
        )

        text = response.content[0].text.strip()

        try:
            return json.loads(text)["intent"]
        except (json.JSONDecodeError, KeyError):
            return "general_inquiry"
