"""Versioned prompts. Bump VERSION when a prompt changes: the version is part of the cache key.

Every prompt ends with an INPUT JSON block so inputs are unambiguous (and easy to parse in tests).
"""

import json
from dataclasses import dataclass
from typing import Any

LANG_NAMES = {"uz": "Uzbek (Latin script)", "en": "English", "ru": "Russian", "tr": "Turkish"}


@dataclass(frozen=True)
class Prompt:
    name: str
    version: int
    system: str
    task: str

    @property
    def id(self) -> str:
        return f"{self.name}@{self.version}"

    def render(self, inputs: dict[str, Any]) -> str:
        return f"{self.task}\n\nINPUT:\n```json\n{json.dumps(inputs, ensure_ascii=False, indent=2)}\n```"


def parse_input(prompt: str) -> dict[str, Any]:
    start = prompt.rindex("```json\n") + len("```json\n")
    return json.loads(prompt[start : prompt.rindex("\n```")])


_LEXICOGRAPHER = (
    "You are an expert multilingual lexicographer for Lexora AI, a dictionary for Uzbek, English, Russian "
    "and Turkish speakers. Be factual and conservative: never invent meanings, etymologies or pronunciations. "
    "If you are not sure about a field, leave it empty or null. Write Uzbek only in the Latin script and use "
    "the modifier letter ʻ (U+02BB) in oʻ and gʻ and ʼ (U+02BC) for the tutuq belgisi."
)

ENTRY = Prompt(
    name="entry",
    version=1,
    system=_LEXICOGRAPHER,
    task=(
        "Create a dictionary entry for the term in INPUT.\n"
        "- Detect the term's language (one of `languages`; `lang_hint` is only a hint) and its lemma "
        "(dictionary form, e.g. 'ran' -> 'run').\n"
        "- If it is not a real word, phrase, abbreviation, slang or term, set is_valid_word=false, leave senses "
        "empty and put up to 5 likely intended words in `suggestions`.\n"
        "- Give 1-6 senses ordered by frequency. For each sense: pos (noun, verb, adj, adv, pron, prep, conj, "
        "interj, num, phrase, proper_noun), optional domain (computing, ai, medicine, business, sports, law, "
        "science...), register (neutral, formal, informal, slang, vulgar, archaic), cefr_level (A1-C2) when "
        "meaningful, definitions in English and Uzbek (`definition_langs`), translations into every language in "
        "`target_langs` except the term's own language (mark the best one is_primary), 1-2 natural example "
        "sentences in the term's language with Uzbek and English translations, synonyms and antonyms in the "
        "term's language.\n"
        "- If `domain_hint` is given, make sure that meaning is included.\n"
        "- ipa: broad IPA transcription with slashes; forms: inflected forms; tags: e.g. ai, tech, slang, new; "
        "phrases: common idioms or phrasal verbs containing the term."
    ),
)

VERIFY = Prompt(
    name="verify",
    version=1,
    system=(
        "You are a strict senior dictionary editor. You review entries written by another model and look for "
        "hallucinated meanings, wrong translations, wrong part of speech, unnatural examples and wrong Uzbek "
        "spelling."
    ),
    task=(
        "Review the dictionary entry in INPUT.\n"
        "Return verdict=accept if it is correct and useful, review if it has fixable problems or you are unsure, "
        "reject if the term is not real or the entry is mostly wrong. `confidence` is your probability (0-1) "
        "that the entry is correct. List concrete problems in `issues` (in English, short)."
    ),
)

INTENT = Prompt(
    name="intent",
    version=1,
    system="You convert dictionary search queries into structured intents.",
    task=(
        "Classify the user's search query in INPUT (it may be in Uzbek, English, Russian or Turkish).\n"
        "- lookup: the user wants the meaning of a word/phrase; term = that word/phrase only.\n"
        "- translate: the user asks how to say something in another language; term = the text to translate.\n"
        "- list_new_terms: the user wants a list of new terms (optionally for a domain and year).\n"
        "target_lang: the language the user wants the answer in (uz, en, ru, tr), or the language of the "
        "question if not stated. source_lang: the term's language if clear. domain: computing, ai, medicine, "
        "economics, sports, law or null."
    ),
)

TRANSLATE = Prompt(
    name="translate",
    version=1,
    system=(
        "You are a professional translator between Uzbek, English, Russian and Turkish. Preserve meaning, tone "
        "and formatting. Write Uzbek in the Latin script (oʻ, gʻ with U+02BB)."
    ),
    task=(
        "Translate `text` from INPUT into `target` (language code). `source` is the source language code or "
        "'auto'. Use `context` if given. Return the translation, the detected source language code, up to 3 "
        "alternative translations (only if meaningfully different) and a short note in Uzbek about nuances "
        "(or null)."
    ),
)

EXPLAIN = Prompt(
    name="explain",
    version=1,
    system=(
        "You are Lexora AI, a friendly language teacher. You explain words clearly with examples. Use Markdown "
        "(short paragraphs, bullet lists). Do not invent facts; say when a usage is rare or regional."
    ),
    task=(
        "Explain the word from INPUT to a learner in the language `explain_lang`. Use the dictionary `entry` as "
        "ground truth.\n"
        "- level=simple: 3-6 short sentences, everyday meaning, 2 examples with translations, one tip.\n"
        "- level=detailed: all main meanings and nuances, collocations, common mistakes, register, related "
        "words, 4+ examples with translations.\n"
        "If `question` is set, answer that question about the word instead."
    ),
)
