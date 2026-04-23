from __future__ import annotations

import re
from typing import Any, Optional

from app.config import constants
from app.domain.enums import TicketType
from app.utils.hashing import sha256_text


def format_ticket_number(ticket_type: str | TicketType, number: int) -> str:
    ticket_type_value = ticket_type.value if isinstance(ticket_type, TicketType) else str(ticket_type)
    width = int(constants.TICKET_NUMBER_PAD.get(ticket_type_value, 0) or 0)
    return str(int(number)).zfill(width) if width > 0 else str(int(number))


def normalize_header(value: str) -> str:
    return (value or "").strip().lower()


def kclean(value: str) -> str:
    text = (value or "")
    text = text.replace("\n", " ").replace("\r", " ")
    text = text.replace('"', "").replace("“", "").replace("”", "").replace("«", "").replace("»", "")
    text = text.strip().lower()
    text = re.split(r"\bподсказка\s*:", text, maxsplit=1)[0].strip()
    text = re.sub(r"\s+", " ", text).strip()
    return text


def clean_answer(value: Any) -> str:
    if value is None:
        return ""
    text = str(value).replace("\r", "\n").strip()
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text).strip()
    lowered = text.lower().strip()
    if lowered in ("", "-", "—", "---", "n/a", "na", "нет", "нет данных", "без ответа"):
        return ""
    if re.fullmatch(r"-{3,}", lowered):
        return ""
    return text


def normalize_channel_like_discord(raw: str) -> str:
    text = (raw or "").lower().strip().replace(" ", "-").replace("_", "-")
    chars: list[str] = []
    for char in text:
        if char.isalnum() or char == "-":
            chars.append(char)
    normalized = "".join(chars).strip("-")
    return normalized or "ticket"


def ticket_prefix_sanitized(ticket_type: str | TicketType) -> str:
    ticket_type_value = ticket_type.value if isinstance(ticket_type, TicketType) else str(ticket_type)
    prefix = constants.TICKET_NAME_PREFIX.get(ticket_type_value, constants.TICKET_NAME_PREFIX[TicketType.OTHER.value])
    return normalize_channel_like_discord(prefix)


def sanitize_channel_name(raw: str) -> str:
    text = raw.lower().strip().replace(" ", "-").replace("_", "-")
    chars: list[str] = []
    for char in text:
        if char.isalnum() or char == "-":
            chars.append(char)
    normalized = "".join(chars).strip("-")
    return normalized or "user"


def panel_name_from_ticket_type(ticket_type: str | TicketType) -> str:
    ticket_type_value = ticket_type.value if isinstance(ticket_type, TicketType) else str(ticket_type)
    return {
        TicketType.APPLICATION.value: "Заявка на вступление",
        TicketType.IDEA.value: "Предложить идею",
        TicketType.OTHER.value: "Жалоба на игрока",
    }.get(ticket_type_value, "Жалоба на игрока")


def detect_ticket_type_from_name(name: str) -> TicketType:
    channel_name = (name or "").lower()
    if channel_name.startswith(f"{ticket_prefix_sanitized(TicketType.APPLICATION)}-"):
        return TicketType.APPLICATION
    if channel_name.startswith(f"{ticket_prefix_sanitized(TicketType.IDEA)}-"):
        return TicketType.IDEA
    if channel_name.startswith(f"{ticket_prefix_sanitized(TicketType.OTHER)}-"):
        return TicketType.OTHER
    return TicketType.OTHER


def extract_ticket_number_from_row(row_dict: dict[str, Any]) -> Optional[int]:
    if not row_dict:
        return None

    value: Any = None
    for key in row_dict.keys():
        normalized_key = normalize_header(key)
        if ("тикет" in normalized_key) or ("ticket" in normalized_key):
            cell_value = row_dict.get(key)
            if cell_value:
                value = cell_value
                break

    if value is None:
        return None

    digits = "".join(char for char in str(value).strip() if char.isdigit())
    if not digits:
        return None

    try:
        return int(digits)
    except Exception:
        return None


def build_form_signature(row_dict: dict[str, Any], ticket_number: int) -> str:
    fields: list[str] = []
    for key, value in sorted((row_dict or {}).items(), key=lambda item: str(item[0])):
        fields.append(f"{kclean(str(key))}={clean_answer(value)}")
    payload = f"ticket={ticket_number}|" + "|".join(fields)
    return sha256_text(payload)


def extract_ticket_number_for_type(channel_name: str, ticket_type: str | TicketType) -> Optional[int]:
    prefix = f"{ticket_prefix_sanitized(ticket_type)}-"
    candidate_name = (channel_name or "").lower()
    if not candidate_name.startswith(prefix):
        return None
    try:
        return int(candidate_name.split("-")[-1])
    except Exception:
        return None


def compact_label(key: str) -> str:
    normalized_key = kclean(key)

    if "отметка времени" in normalized_key or "timestamp" in normalized_key:
        return "Время"
    if (
        "номер вашего тикета" in normalized_key
        or "номер тикета" in normalized_key
        or ("в discord" in normalized_key and "тикет" in normalized_key)
        or ("тикет" in normalized_key)
        or ("ticket" in normalized_key)
    ):
        return "№ тикета"
    if "укажите свой steam id" in normalized_key or "steam id" in normalized_key:
        return "Steam ID"
    if "как вас зовут" in normalized_key or "реальное имя" in normalized_key:
        return "Имя"
    if "какой у вас никнейм" in normalized_key or "никнейм" in normalized_key:
        return "Ник"
    if "сколько вам лет" in normalized_key or "возраст" in normalized_key:
        return "Возраст"
    if "были вы в других кланах" in normalized_key or ("если были" in normalized_key and "в каких" in normalized_key):
        return "Кланы"
    if (
        "сколько времени вы готовы уделять клану" in normalized_key
        or "уделять клану" in normalized_key
        or ("в неделю" in normalized_key and "час" in normalized_key)
    ):
        return "Активность/нед."
    if "какой у вас часовой пояс" in normalized_key or "часовой пояс" in normalized_key:
        return "Часовой пояс"
    if "сколько часов вы наиграли в squad" in normalized_key or ("наиграли" in normalized_key and "squad" in normalized_key):
        return "Squad (часы)"
    if "есть ли у вас микрофон" in normalized_key or "микрофон" in normalized_key:
        return "Микрофон"
    if "на каких серверах" in normalized_key or "предпочитаете играть" in normalized_key:
        return "Сервера"
    if (
        "готовы ли вы поддерживать дружеские отношения" in normalized_key
        or "дружеские отношения" in normalized_key
        or "дружелюб" in normalized_key
    ):
        return "Дружелюбие"
    if "за какую роль" in normalized_key or "роль в игре" in normalized_key:
        return "Роль"
    if "как вы узнали о нашем клане" in normalized_key or "как вы узнали" in normalized_key:
        return "Откуда узнал"
    if "какой вопрос вы хотели бы видеть" in normalized_key and "опросник" in normalized_key:
        return "Идея вопроса"
    if (
        "на сколько вы оцениваете" in normalized_key
        or ("оцениваете" in normalized_key and "опросник" in normalized_key)
        or "оцен" in normalized_key
    ):
        return "Оценка"

    return (key or "Поле")[:256]


def steam_profile_url(steam_id: str) -> Optional[str]:
    normalized = re.sub(r"\D", "", steam_id or "")
    if len(normalized) == 17:
        return f"https://steamcommunity.com/profiles/{normalized}"
    return None
