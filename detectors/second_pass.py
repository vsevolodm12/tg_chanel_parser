import json
import os
import re
import logging
from pathlib import Path
from typing import Dict, Any
import httpx

from openai import OpenAI

logger = logging.getLogger(__name__)

PROMPT_PATH = Path(__file__).resolve().parents[1] / "prompts" / "event_detection.txt"


def _load_prompt() -> str:
    return PROMPT_PATH.read_text(encoding="utf-8")


def _build_prompt(text: str) -> str:
    template = _load_prompt()
    return template.replace("{text}", text)


def llm_detect(text: str) -> Dict[str, Any]:
    prompt = _build_prompt(text)
    api_key = os.getenv("POLZA_AI_API_KEY")
    base_url = os.getenv("POLZA_API_BASE", "https://api.polza.ai/api/v1")
    model = os.getenv("POLZA_MODEL", "deepseek/deepseek-r1-distill-llama-70b")
    
    # Инициализация клиента с явным httpx клиентом без прокси
    http_client = httpx.Client()
    client = OpenAI(
        api_key=api_key,
        base_url=base_url,
        http_client=http_client,
    )

    try:
        logger.info(f"Отправка запроса к LLM (модель: {model})")
        completion = client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1,
        )
        content = completion.choices[0].message.content
        logger.info(f"LLM ответ получен (полный): {content}")
        
        # Пытаемся извлечь JSON из ответа (может быть обернут в markdown или текст)
        content_clean = content.strip()
        if content_clean.startswith("```"):
            # Убираем markdown код блоки
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', content_clean, re.DOTALL)
            if json_match:
                content_clean = json_match.group(1)
        elif not content_clean.startswith("{"):
            # Ищем JSON в тексте
            json_match = re.search(r'\{.*\}', content_clean, re.DOTALL)
            if json_match:
                content_clean = json_match.group(0)
        
        parsed = json.loads(content_clean)
        logger.info(f"JSON распарсен успешно: {parsed}")
        return {
            "is_event": bool(parsed.get("is_event")),
            "title": parsed.get("title"),
            "date": parsed.get("date"),
            "place": parsed.get("place"),
            "link": parsed.get("link"),
            "description": parsed.get("description"),
        }
    except json.JSONDecodeError as e:
        logger.error(f"Ошибка парсинга JSON от LLM. Ответ: {content[:500] if 'content' in locals() else 'нет ответа'}. Ошибка: {e}")
        return {
            "is_event": False,
            "title": None,
            "date": None,
            "place": None,
            "link": None,
            "description": None,
        }
    except Exception as e:
        logger.error(f"Ошибка LLM запроса: {type(e).__name__}: {e}", exc_info=True)
        return {
            "is_event": False,
            "title": None,
            "date": None,
            "place": None,
            "link": None,
            "description": None,
        }

