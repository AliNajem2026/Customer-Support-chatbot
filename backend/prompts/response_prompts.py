INTENTS = [
    "technical_support",
    "billing",
    "account_access",
    "general_inquiry",
]

INTENT_DESCRIPTIONS = {
    "technical_support": "bugs, app errors, performance issues",
    "billing":           "invoices, payments, refunds, subscription pricing",
    "account_access":    "login problems, password reset, 2FA",
    "general_inquiry":   "anything else not covered above",
}


def classification_prompt(message: str) -> str:
    intent_list = "\n".join(
        f"- {intent}: {INTENT_DESCRIPTIONS[intent]}"
        for intent in INTENTS
    )
    return f"""You are an intent classifier for a customer support system.

Classify the message below into exactly one of the following intents:
{intent_list}

Rules:
- Return JSON only — no explanation, no markdown.
- Format: {{"intent": "<intent_name>"}}
- If unsure, choose general_inquiry.

Message:
{message}"""


def response_generation_prompt(question: str, context: str, language: str) -> str:
    lang_label = "Arabic" if language == "ar" else "English"
    return f"""You are a helpful and professional customer support agent.

Your answer must follow these rules:
1. Answer ONLY using the information provided in the Context below.
2. If the context does not contain enough information, say so politely — do not guess or make up details.
3. Be concise, clear, and friendly.
4. Respond in {lang_label}.

Context:
{context}

Customer question:
{question}"""
