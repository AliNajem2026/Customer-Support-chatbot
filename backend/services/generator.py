import anthropic

from backend.core.config import settings
from backend.prompts.response_prompts import response_generation_prompt


class ResponseGenerator:

    def __init__(self):
        self.client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)

    def generate(self, question: str, context: str, language: str) -> str:
        response = self.client.messages.create(
            model=settings.CLAUDE_MODEL,
            temperature=0,
            max_tokens=500,
            messages=[{
                "role": "user",
                "content": response_generation_prompt(question, context, language)
            }]
        )

        return response.content[0].text
