import re


class SafetyFilter:

    @staticmethod
    def check_input(text: str):

        if len(text.strip()) == 0:
            return False, "Empty message"

        email_pattern = r'\S+@\S+\.\S+'

        if re.search(email_pattern, text):
            return False, "PII detected"

        dangerous = [
            "ignore previous instructions",
            "system prompt",
            "hack"
        ]

        lowered = text.lower()

        for word in dangerous:
            if word in lowered:
                return False, "Prompt Injection Detected"

        return True, "Safe"

    @staticmethod
    def check_output(text: str):

        forbidden = [
            "credit card",
            "password"
        ]

        for item in forbidden:
            if item in text.lower():
                return False

        return True