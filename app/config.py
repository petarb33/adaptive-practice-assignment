import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DEFAULT_QUESTIONS_PATH = PROJECT_ROOT / "data" / "questions.json"


def get_questions_path() -> Path:
    path = os.environ.get("QUESTIONS_PATH")
    if path:
        return Path(path)
    return DEFAULT_QUESTIONS_PATH
