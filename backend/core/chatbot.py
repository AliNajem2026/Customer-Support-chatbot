from datetime import datetime

from backend.services.safety import SafetyFilter
from backend.services.classifier import IntentClassifier
from backend.services.rag import RAGService
from backend.services.generator import ResponseGenerator
from backend.services.logger import InteractionLogger
from language import detect_language


class CustomerSupportBot:

    def __init__(self, log_file: str):
        self.classifier = IntentClassifier()
        self.rag = RAGService()
        self.generator = ResponseGenerator()
        self.logger = InteractionLogger(log_file)

    def process(self, user_id: str, message: str) -> dict:
        try:
            is_safe, status = SafetyFilter.check_input(message)

            if not is_safe:
                return {
                    "response": "Your message was blocked for safety reasons.",
                    "language": "en",
                    "intent": "blocked",
                    "safety_status": status
                }

            language = detect_language(message)
            intent = self.classifier.classify(message)
            context = self.rag.retrieve(message)
            response = self.generator.generate(message, context, language)

            if not SafetyFilter.check_output(response):
                response = "Response generation failed safety checks."

            self.logger.log([
                datetime.utcnow().isoformat(),
                user_id,
                message,
                language,
                intent,
                context[:300] if context else "",
                response,
                status
            ])

            return {
                "response": response,
                "language": language,
                "intent": intent,
                "safety_status": status
            }

        except Exception as e:
            return {
                "response": "We encountered an internal error. Please try again later.",
                "language": "en",
                "intent": "error",
                "safety_status": str(e)
            }
