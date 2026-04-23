from __future__ import annotations

from app.utils.text import build_form_signature


def test_form_signature_dedup_is_stable_across_key_order() -> None:
    row_a = {
        "Steam ID": "76561198000000000",
        "Номер тикета": "246",
        "Как вас зовут": "Alex",
    }
    row_b = {
        "Как вас зовут": "Alex",
        "Номер тикета": "246",
        "Steam ID": "76561198000000000",
    }

    assert build_form_signature(row_a, 246) == build_form_signature(row_b, 246)


def test_form_signature_treats_placeholder_answers_as_empty() -> None:
    row_a = {
        "Номер тикета": "300",
        "Комментарий": "---",
    }
    row_b = {
        "Номер тикета": "300",
        "Комментарий": "",
    }

    assert build_form_signature(row_a, 300) == build_form_signature(row_b, 300)
