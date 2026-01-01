import re

KEYWORDS = [
    # Русские
    "митап",
    "конференция",
    "лекция",
    "воркшоп",
    "встреча",
    "вечеринка",
    "семинар",
    "тренинг",
    "хакатон",
    "фестиваль",
    "форум",
    "саммит",
    "выставка",
    "презентация",
    "демо-день",
    "демодень",
    "концерт",
    "шоу",
    "турнир",
    "чемпионат",
    "круглый стол",
    "дискуссия",
    "панель",
    "дебаты",
    "мастер-класс",
    "мастеркласс",
    # Английские
    "event",
    "meetup",
    "workshop",
    "party",
    "conference",
    "lecture",
    "seminar",
    "training",
    "hackathon",
    "festival",
    "forum",
    "summit",
    "exhibition",
    "presentation",
    "demo day",
    "concert",
    "show",
    "tournament",
    "championship",
    "round table",
    "discussion",
    "panel",
    "debate",
    "master class",
    "masterclass",
]

DATE_PATTERNS = [
    r"\b\d{1,2}[./]\d{1,2}[./]\d{2,4}\b",
    r"\b\d{4}-\d{2}-\d{2}\b",
    r"\bсегодня\b",
    r"\bзавтра\b",
    r"\bпонедельник|\bвторник|\bсреда|\bчетверг|\bпятница|\bсуббота|\bвоскресенье",
    r"\d{1,2}\s+(января|февраля|марта|апреля|мая|июня|июля|августа|сентября|октября|ноября|декабря)",
]


def quick_check(text: str) -> bool:
    lower = text.lower()
    if any(k in lower for k in KEYWORDS):
        return True
    if any(re.search(pat, lower) for pat in DATE_PATTERNS):
        return True
    return False

