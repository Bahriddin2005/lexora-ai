import pytest

from app.services.normalization import detect_script, normalize


@pytest.mark.parametrize("variant", ["oʻgʻil", "o‘g‘il", "o'g'il", "o`g`il", "O’G’IL", "ўғил", "Ўғил"])
def test_uzbek_apostrophes_and_cyrillic(variant):
    assert normalize(variant, "uz") == "o'g'il"


def test_uzbek_cyrillic_ye():
    assert normalize("ер", "uz") == "yer"
    assert normalize("келди", "uz") == "keldi"
    assert normalize("шаҳар", "uz") == "shahar"


def test_turkish_dotted_i():
    assert normalize("İstanbul", "tr") == "istanbul"
    assert normalize("ISTANBUL", "tr") == "istanbul"
    assert normalize("ılık", "tr") == "ilik"


def test_russian_yo_and_english_diacritics():
    assert normalize("Ёлка", "ru") == "елка"
    assert normalize("Café", "en") == "cafe"


def test_cleanup():
    assert normalize('  "Hello,   World!" ', "en") == "hello, world"
    assert normalize("«школа»", "ru") == "школа"


def test_detect_script():
    assert detect_script("школа") == "Cyrl"
    assert detect_script("maktab") == "Latn"
    assert detect_script("كتاب") == "Arab"
