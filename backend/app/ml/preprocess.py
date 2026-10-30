"""Text cleaning, ported unchanged from the training notebook.

Any change here must be matched by retraining: the vocabulary and model were
built from text cleaned by exactly this pipeline.
"""
import re
import string
import unicodedata

import contractions
from nltk.stem import WordNetLemmatizer
from nltk.tokenize import word_tokenize

_lemmatizer = WordNetLemmatizer()

_allowed_characters = string.ascii_letters + string.digits + string.punctuation + " "


def unicode_to_ascii(text: str) -> str:
    return "".join(
        c
        for c in unicodedata.normalize("NFD", text)
        if unicodedata.category(c) != "Mn" and c in _allowed_characters
    )


def handle_special_cases(text: str) -> str:
    def round_currency(match):
        number = float(match.group(1))
        return f"{round(number)} dollars"

    text = re.sub(r"(?<=\d),(?=\d)", "", text)
    text = re.sub(r"\$(\d+\.\d+)", round_currency, text)
    text = re.sub(r"\$(\d+)(?!\.\d)", r"\1 dollars", text)
    text = re.sub(r"(\d+)%", r"\1 percent", text)

    def round_decimal(match):
        number = float(match.group(0))
        return str(round(number))

    text = re.sub(r"(?<![\d$])\d+\.\d+(?![\d%])", round_decimal, text)
    return text


_expanded_contractions = {
    "sept.": "september",
    "u.s.": "unitedstates",
    "nyc": "newyorkcity",
    "u.k.": "unitedkingdom",
    "b.c.": "beforechrist",
    "c'mon": "come on",
    "gov't": "government",
    "don'ts": "do not",
    "gimme": "give me",
}

_apostrophe_pattern = r"\b\w+'\w+\b"

_sorted_keys = sorted(_expanded_contractions.keys(), key=len, reverse=True)
_contraction_regex = re.compile(
    "|".join(
        rf"\b{re.escape(k)}\b" if k.isalpha() and len(k) <= 2 else re.escape(k)
        for k in _sorted_keys
    ),
    flags=re.IGNORECASE,
)


def expand_contractions(text: str) -> str:
    # The notebook rebuilt this regex inside the loop; the result is identical.
    if any(c in text for c in _expanded_contractions):
        text = _contraction_regex.sub(
            lambda m: _expanded_contractions[m.group(0).lower()], text
        )

    for word in re.findall(_apostrophe_pattern, text):
        expanded = contractions.fix(word)
        if word == expanded:
            expanded = re.sub(r"'s\b", " has", word)
        text = text.replace(word, expanded)

    return text


def remove_punctuations(text: str) -> str:
    return re.sub(f"[{re.escape(string.punctuation)}]", " ", text)


def remove_extra_spaces(text: str) -> str:
    return re.sub(r"\s+", " ", text)


_wrongly_lemmatized = {"has": "has", "us": "us"}


def lemmatize_text(text: str) -> str:
    return " ".join(
        _wrongly_lemmatized.get(word) or _lemmatizer.lemmatize(word)
        for word in word_tokenize(text)
    )


def clean_text(text: str) -> str:
    text = text.lower()
    text = unicode_to_ascii(text)
    text = handle_special_cases(text)
    text = expand_contractions(text)
    text = remove_punctuations(text)
    text = remove_extra_spaces(text)
    text = lemmatize_text(text)
    return text.strip()
