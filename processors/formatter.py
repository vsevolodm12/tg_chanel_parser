from typing import Dict, Any, List


def _fmt(value: str, fallback: str = "Уточняется") -> str:
    if value is None:
        return fallback
    stripped = str(value).strip()
    return stripped if stripped else fallback


def format_event_message(data: Dict[str, Any], source_link: str) -> str:
    description = data.get('description')
    description_text = description if description else "Описание отсутствует"
    
    return (
        f"🗓 { _fmt(data.get('title'), 'Без названия') }\n"
        f"📍 { _fmt(data.get('place')) }\n"
        f"⏰ { _fmt(data.get('date')) }\n"
        f"📝 {description_text}\n"
        f"🔗 Регистрация: {_fmt(data.get('link'), 'нет')}\n"
        f"🔗 Источник: {source_link}"
    )

