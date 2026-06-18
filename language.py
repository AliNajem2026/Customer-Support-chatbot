import re


def detect_language(text: str) -> str:

    arabic_pattern = re.compile(r'[\u0600-\u06FF]')

    if arabic_pattern.search(text):
        return "ar"

    return "en"