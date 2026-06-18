import csv
import os


class InteractionLogger:

    def __init__(self, file_path):

        self.file_path = file_path

        self._initialize()

    def _initialize(self):

        os.makedirs(
            os.path.dirname(self.file_path),
            exist_ok=True
        )

        if not os.path.exists(self.file_path):

            with open(
                self.file_path,
                "w",
                newline="",
                encoding="utf-8"
            ) as file:

                writer = csv.writer(file)

                writer.writerow([
                    "timestamp",
                    "user_id",
                    "input_message",
                    "detected_language",
                    "predicted_intent",
                    "retrieved_context",
                    "bot_response",
                    "safety_status"
                ])

    def log(self, row):

        with open(
            self.file_path,
            "a",
            newline="",
            encoding="utf-8"
        ) as file:

            writer = csv.writer(file)

            writer.writerow(row)