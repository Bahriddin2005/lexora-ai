import pytest

from app.services.intent import needs_llm, parse_intent_rules


@pytest.mark.parametrize(
    ("query", "expected"),
    [
        ("book", {"type": "lookup", "term": "book", "target_lang": None}),
        ("book so‘zining o‘zbekcha ma'nosi", {"type": "lookup", "term": "book", "target_lang": "uz"}),
        ('rus tilida "maktab" nima?', {"type": "translate", "term": "maktab", "target_lang": "ru"}),
        (
            "python so‘zi dasturlashda nimani anglatadi?",
            {"type": "lookup", "term": "python", "target_lang": "uz", "domain": "computing"},
        ),
        ("cringe nima degani?", {"type": "lookup", "term": "cringe", "target_lang": "uz"}),
        (
            "2026-yilda AI sohasida chiqqan yangi terminlarni ko‘rsat",
            {"type": "list_new_terms", "domain": "ai", "year": 2026},
        ),
        ("what does serendipity mean", {"type": "lookup", "term": "serendipity", "target_lang": "en"}),
        ("что значит кринж", {"type": "lookup", "term": "кринж", "target_lang": "ru"}),
        ("школа по-английски", {"type": "translate", "term": "школа", "target_lang": "en"}),
        ("in the long run", {"type": "lookup", "term": "in the long run"}),
        ("mean", {"type": "lookup", "term": "mean"}),
    ],
)
def test_rules(query, expected):
    intent, _ = parse_intent_rules(query)
    for key, value in expected.items():
        assert getattr(intent, key) == value, (key, intent)


def test_needs_llm():
    intent, is_nl = parse_intent_rules("how do you say good morning to your mom in turkish")
    assert is_nl
    assert needs_llm(intent, is_nl)
    intent, is_nl = parse_intent_rules("run out of")
    assert not needs_llm(intent, is_nl)
