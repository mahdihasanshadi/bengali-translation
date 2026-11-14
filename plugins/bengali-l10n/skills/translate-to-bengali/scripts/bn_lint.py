#!/usr/bin/env python3
"""bn_lint.py - QA linter and safe auto-fixer for English -> Bengali translations.

Pair mode compares the English source with its Bengali translation:

    python bn_lint.py --source en.json --target bn.json

    Pairs it understands: JSON (i18next, vue-i18n, next-intl, react-intl ...),
    Flutter .arb, YAML (.yml/.yaml, needs PyYAML), Android strings.xml,
    iOS .strings, and HTML pages (structure, links, attributes, text).

Single-file formats carry both languages, so --target alone is enough:

    python bn_lint.py --target bn.po            gettext .po / .pot
    python bn_lint.py --target app.bn.xlf       XLIFF 1.2 and 2.0
    python bn_lint.py --target Localizable.xcstrings   Xcode String Catalog

Target-only mode runs the Bengali checks on any text file (Markdown, MDX,
plain text, templates ...), line by line, skipping fenced code blocks:

    python bn_lint.py --target-only docs/bn/index.md

Options:
  --digits bn|latn|any   digit policy for Bengali text (default: any;
                         Bengali and Latin digits mixed inside one number are
                         always an error)
  --tone apni|tumi       expected form of address (default: apni)
  --glossary FILE        JSON {"english term": "বাংলা"} (or {"terms": {...}});
                         every source term must use the agreed rendering
  --fix                  apply safe mechanical fixes to the target file in
                         place (Unicode composition, দাঁড়ি, known misspellings,
                         spacing, digits per --digits), then lint the result.
                         Commit first so you can review the diff.
  --json                 machine-readable output
  --strict               exit 1 on warnings as well as errors

Exit code: 0 clean, 1 errors found (or warnings with --strict), 2 usage error.
No third-party dependencies except PyYAML for YAML files. Python 3.8+.

The linter finds mechanical problems. It cannot judge whether the meaning is
right; that still needs a careful read.
"""
from __future__ import annotations

import argparse
import difflib
import json
import re
import sys
import unicodedata
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

__version__ = "1.1.0"

BN = "\u0980-\u09FF"
ZWJ, ZWNJ = "\u200d", "\u200c"
BN_LETTER = re.compile(f"[{BN}]")
BN_WORD_RE = re.compile(f"[{BN}{ZWJ}{ZWNJ}]+")
LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z'’-]{2,}")
TO_LATN = str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789")
TO_BN = str.maketrans("0123456789", "০১২৩৪৫৬৭৮৯")


class LoadError(Exception):
    """A file could not be read or parsed (reported as an error finding)."""


class UsageError(Exception):
    """Bad invocation or missing dependency (exit code 2)."""


def bn_word(word: str) -> re.Pattern:
    """Match `word` only when it is not embedded in a longer Bengali word."""
    return re.compile(f"(?<![{BN}{ZWJ}{ZWNJ}]){re.escape(word)}(?![{BN}{ZWJ}{ZWNJ}])")


def bn_prefix(stem: str) -> re.Pattern:
    """Match a word that starts with `stem` (suffixes such as -তে, -র allowed)."""
    return re.compile(f"(?<![{BN}{ZWJ}{ZWNJ}]){re.escape(stem)}")


def to_latin_digits(s: str) -> str:
    return s.translate(TO_LATN)


# --------------------------------------------------------------------------
# Placeholders and markup
# --------------------------------------------------------------------------
PLACEHOLDER_PATTERNS = [
    r"\{\{\s*[^{}]+?\s*\}\}",                  # {{name}}  (i18next, Handlebars, Liquid)
    r"\{%.*?%\}",                              # {% tag %}
    r"\$\{[^{}]+\}",                           # ${name}
    r"%\{[A-Za-z_]\w*\}",                      # %{name}   (Rails, Ruby)
    r"%<[A-Za-z_]\w*>[sdif]",                  # %<name>s  (Ruby format)
    r"%\([A-Za-z_]\w*\)[sdif]",                # %(name)s
    # %s %d %1$s %.2f %@ %lld - no space flag, or "20% today" would read as a placeholder
    r"%(?:\d+\$)?[-+0#]*\d*(?:\.\d+)?(?:hh|h|ll|l|q|z|j)?[sdifuxXc@]",
    r"\$t\([^)]*\)",                           # $t(key)
    r"@:[\w.]+",                               # @:linked.key (vue-i18n)
    r"&(?:[a-zA-Z]+|#\d+|#x[0-9a-fA-F]+);",    # HTML entities
    r"\\[ntr]",                                # escapes written literally
]
PLACEHOLDER_RE = re.compile("|".join(PLACEHOLDER_PATTERNS), re.S)
# {name} {0} - and {নাম}, so a translated placeholder name is reported, not missed
SIMPLE_BRACE_RE = re.compile(rf"\{{\s*([A-Za-z_{BN}][\w.{BN}{ZWJ}{ZWNJ}]*|\d+)\s*\}}")
ICU_KINDS = "plural|select|selectordinal|number|date|time|spellout|ordinal|duration"
ICU_HEAD_RE = re.compile(r"\{\s*([^\s{},]+)\s*,\s*(" + ICU_KINDS + r")\b\s*,?")
ICU_SELECTOR_RE = re.compile(r"(?<![\w=])(?:zero|one|two|few|many|other|=\d+)\s*(?=\{)")
PLURAL_KEYS = {"zero", "one", "two", "few", "many", "other"}
COLON_PARAM_RE = re.compile(r"(?<![\w:/]):([a-z_][a-z0-9_]*)\b")     # :name (Laravel)
TAG_RE = re.compile(r"</?\s*([A-Za-z][\w:-]*|\d+)\b[^<>]*?/?>")
HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']([^"']+)["']""")
URL_RE = re.compile(r"https?://[^\s\"'<>)]+")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")
CODE_SPAN_RE = re.compile(r"`[^`\n]+`")


def mask_placeholders(text: str) -> str:
    return PLACEHOLDER_RE.sub(lambda m: " " * len(m.group(0)), text)


def scan_braces(text: str):
    """Walk the braces of a message.

    Returns (tokens, icu): tokens are simple placeholders such as "{name}" and
    ICU argument heads such as "{count, plural}"; icu lists each ICU argument
    with the branch selectors it uses. Branch bodies ("one {# item}") are
    sub-messages, not placeholders, so they are not reported as tokens.
    """
    tokens, icu, stack = [], [], []
    i, n, last = 0, len(text), 0
    while i < n:
        c = text[i]
        if c == "{":
            m = ICU_HEAD_RE.match(text, i)
            if m:
                tokens.append(f"{{{m.group(1)}, {m.group(2)}}}")
                icu.append({"arg": m.group(1), "kind": m.group(2), "selectors": []})
                stack.append(("arg", len(icu) - 1))
                i = last = m.end()
                continue
            if stack and stack[-1][0] == "arg":
                words = re.findall(r"[^\s,{}]+", text[last:i])
                icu[stack[-1][1]]["selectors"].append(words[-1] if words else "")
                stack.append(("msg", None))
                i += 1
                continue
            m = SIMPLE_BRACE_RE.match(text, i)
            if m:
                tokens.append(f"{{{m.group(1)}}}")
                i = m.end()
                continue
            stack.append(("other", None))
        elif c == "}" and stack:
            stack.pop()
            if stack and stack[-1][0] == "arg":
                last = i + 1
        i += 1
    return tokens, icu


def placeholders(text: str, colon_params: bool) -> list:
    found = [re.sub(r"\s+", "", f) for f in PLACEHOLDER_RE.findall(text)]
    found += scan_braces(mask_placeholders(text))[0]
    if colon_params:
        found += [":" + m for m in COLON_PARAM_RE.findall(text)]
    return sorted(found)


def tags(text: str) -> list:
    out = []
    for m in TAG_RE.finditer(text):
        raw, name = m.group(0), m.group(1).lower()
        if raw.startswith("</"):
            out.append("/" + name)
        elif raw.endswith("/>"):
            out.append(name + "/")
        else:
            out.append(name)
    return sorted(out)


def strip_protected(text: str) -> str:
    """Remove things that legitimately stay Latin, before digit/Latin checks."""
    for rx in (TAG_RE, URL_RE, EMAIL_RE, CODE_SPAN_RE, PLACEHOLDER_RE,
               ICU_HEAD_RE, ICU_SELECTOR_RE, SIMPLE_BRACE_RE):
        text = rx.sub(" ", text)
    return text


# --------------------------------------------------------------------------
# Bengali word lists
# --------------------------------------------------------------------------
# (wrong, right, note) - matched as whole Bengali words/prefixes
MISSPELLINGS = [
    ("এ্যা", "অ্যা", "use অ্যা for the 'a' of app/account"),
    ("একাউন্ট", "অ্যাকাউন্ট", ""), ("এক্যাউন্ট", "অ্যাকাউন্ট", ""),
    ("এপস", "অ্যাপস", ""), ("এডমিন", "অ্যাডমিন", ""),
    ("পোষ্ট", "পোস্ট", "no ষ in loanwords"), ("ষ্টোর", "স্টোর", "no ষ in loanwords"),
    ("ষ্টক", "স্টক", ""), ("ষ্টেশন", "স্টেশন", ""), ("ষ্টার", "স্টার", ""),
    ("মাষ্টার", "মাস্টার", ""), ("রেজিষ্ট্রেশন", "রেজিস্ট্রেশন", ""),
    ("রেজিষ্টার", "রেজিস্টার", ""), ("আগষ্ট", "আগস্ট", ""),
    ("সিষ্টেম", "সিস্টেম", ""), ("কাষ্টমার", "কাস্টমার", ""),
    ("ষ্ট্যান্ডার্ড", "স্ট্যান্ডার্ড", ""), ("লিষ্ট", "লিস্ট", ""),
    ("ডেলিভারী", "ডেলিভারি", "loanwords take ি"), ("কোম্পানী", "কোম্পানি", ""),
    ("ক্যাটাগরী", "ক্যাটাগরি", ""), ("গ্যালারী", "গ্যালারি", ""),
    ("স্ক্রীন", "স্ক্রিন", ""), ("টীম", "টিম", ""), ("ফ্রী", "ফ্রি", ""),
    ("ইন্ডাস্ট্রী", "ইন্ডাস্ট্রি", ""), ("ওয়ারেন্টী", "ওয়ারেন্টি", ""),
    ("ভেরীফাই", "ভেরিফাই", ""), ("সার্ভীস", "সার্ভিস", ""),
    ("কর্ণার", "কর্নার", "no ণ in loanwords"), ("ব্রান্ড", "ব্র্যান্ড", ""),
    ("ট্রাকিং", "ট্র্যাকিং", ""), ("প্লান", "প্ল্যান", ""),
    ("পাসওর্য়াড", "পাসওয়ার্ড", ""), ("পাসোয়ার্ড", "পাসওয়ার্ড", ""),
    ("সফটওয়ার", "সফটওয়্যার", ""), ("ওয়েব সাইট", "ওয়েবসাইট", "one word"),
    ("লগ ইন", "লগইন", "one word"), ("লগ আউট", "লগআউট", "one word"),
    ("অন লাইন", "অনলাইন", "one word"), ("ই-মেইল", "ইমেইল", ""),
    ("তৈরী", "তৈরি", ""), ("জরুরী", "জরুরি", ""), ("সরকারী", "সরকারি", ""),
    ("বেশী", "বেশি", ""), ("দেরী", "দেরি", ""), ("খুশী", "খুশি", ""),
    ("দামী", "দামি", ""), ("ইংরেজী", "ইংরেজি", ""), ("শ্রেণী", "শ্রেণি", ""),
    ("সূচী", "সূচি", ""), ("শর্তাবলী", "শর্তাবলি", ""),
    ("পুরষ্কার", "পুরস্কার", ""), ("পরিস্কার", "পরিষ্কার", ""),
    ("ধরণের", "ধরনের", ""), ("কারন", "কারণ", ""), ("পরিমান", "পরিমাণ", ""),
    ("বিবরন", "বিবরণ", ""), ("মুহুর্ত", "মুহূর্ত", ""), ("মুল্য", "মূল্য", ""),
    ("ব্যবহারকারি", "ব্যবহারকারী", "person-marker কারী keeps ী"),
    ("কাঙ্খিত", "কাঙ্ক্ষিত", ""), ("গোপনিয়তা", "গোপনীয়তা", ""),
    ("সাগতম", "স্বাগতম", ""), ("স্বাগতমম", "স্বাগতম", ""),
]
# words that only need a whole-word match (a prefix match would hit valid words)
WHOLE_WORD_ONLY = {"এপস", "টীম", "ফ্রী", "প্লান", "কারন", "মুল্য", "লিষ্ট", "ষ্টার"}

BOOKISH = [
    ("গুপ্তসংকেত", "পাসওয়ার্ড"), ("গুপ্তশব্দ", "পাসওয়ার্ড"),
    ("অন্তর্জাল", "ইন্টারনেট"), ("মুঠোফোন", "মোবাইল"),
    ("বৈদ্যুতিন", "ইমেইল / ইলেকট্রনিক"), ("গণকযন্ত্র", "কম্পিউটার"),
    ("বোতাম", "বাটন"), ("ঠেলাগাড়ি", "কার্ট"), ("অনুগ্রহপূর্বক", "(drop, or অনুগ্রহ করে)"),
    ("প্রবেশ করান", "লিখুন / দিন"), ("স্বাক্ষর করুন", "লগইন করুন (if this is 'Sign in')"),
]

# (regex on the English source, wrong-sense Bengali stems, hint)
SENSE_TRAPS = [
    (r"\bhome\b", ["বাড়ি", "ঘরে", "গৃহ"], "navigation 'Home' is হোম"),
    (r"\b(cart|basket)\b", ["গাড়ি", "ঠেলাগাড়ি", "ঝুড়ি"], "use কার্ট"),
    (r"\bsign(ed)?[ -]?in\b", ["স্বাক্ষর"], "use লগইন"),
    (r"\bsign[ -]?up\b", ["স্বাক্ষর"], "use সাইন আপ"),
    (r"\bsave\s+(?:up to\s+)?(?:[৳$₹]\s?\d|\d[\d.,]*\s*(?:%|percent\b|taka\b|tk\b|bdt\b|৳|\$|₹))",
     ["সংরক্ষণ", "সেভ", "বাঁচ"], "a discount is ছাড় / সাশ্রয়"),
    (r"\bsave\b(?!\s+(?:up to\s+)?(?:\d[\d.,]*\s*)?(?:hours?|minutes?|days?|weeks?|time|money|energy|effort)\b)",
     ["বাঁচান", "রক্ষা করুন"], "saving data is সেভ করুন / সংরক্ষণ করুন"),
    (r"\bfree\b", ["মুক্ত", "স্বাধীন"], "no-cost 'free' is ফ্রি / বিনামূল্যে"),
    (r"\bshar(e|ing)\b", ["ভাগ কর"], "use শেয়ার করুন"),
    (r"\bcookies?\b", ["বিস্কুট"], "use কুকি"),
    (r"\bcloud\b", ["মেঘ"], "use ক্লাউড"),
    (r"\bwindow\b", ["জানালা"], "use উইন্ডো"),
    (r"\bmouse\b", ["ইঁদুর"], "use মাউস"),
    (r"\binvalid\b", ["অবৈধ"], "অবৈধ means illegal; use সঠিক নয় / ভুল"),
    (r"\bcheck ?out\b", ["পরীক্ষা"], "use চেকআউট (or দেখুন for 'check out our…')"),
    (r"\bposts?\b", ["ডাক"], "use পোস্ট"),
    (r"\border(s|ed)?\b", ["আদেশ", "হুকুম"], "a purchase is অর্ডার"),
    (r"\bshipping\b", ["জাহাজ"], "use ডেলিভারি / শিপিং"),
    (r"\bsupport\b", ["সমর্থন"], "customer support is সাপোর্ট / সহায়তা"),
    (r"\bbalance\b", ["ভারসাম্য"], "use ব্যালেন্স"),
    (r"\blearn more\b", ["শিখুন"], "use আরও জানুন"),
    (r"\benter\b", ["প্রবেশ করান", "প্রবেশ করুন"], "typing into a field is লিখুন / দিন"),
    (r"\bmillion\b", ["মিলিয়ন"], "consumer copy uses লাখ (1 million = ১০ লাখ)"),
    (r"\bbillion\b", ["বিলিয়ন"], "consumer copy uses কোটি (1 billion = ১০০ কোটি)"),
    (r"\bchannel\b", ["খাল"], "use চ্যানেল"),
    (r"\bkey\b", ["চাবি"], "an API/licence key is কি / কী (key)"),
]

SADHU = ["করিবেন", "করিতে", "করিয়া", "হইবে", "হইয়াছে", "হইতে", "ইহা", "ইহার",
         "তাহার", "তাহাদের", "যাহা", "উহা", "করিয়াছেন", "দেখিবেন", "হইলে",
         "করিলে", "দিবেন", "লইয়া", "আসিয়া", "যাইবে", "পারিবেন"]

# Form of address. Exact forms, plus verb endings that only the তুমি / আপনি
# conjugations produce. Ending checks need words of 4+ code points so that
# nouns such as নতুন or কেন are not mistaken for verbs.
TUMI_FORMS = {"তুমি", "তোমার", "তোমাকে", "তোমাদের", "তোমরা", "তুই", "তোর", "তোকে",
              "তোদের", "করো", "দেখো", "লেখো", "দাও", "যাও", "পাঠাও", "আছো", "আছ",
              "পারো", "জানো", "চাও", "বলো", "শোনো", "রাখো", "খোলো", "খোঁজো",
              "এসো", "বসো", "ভাবো", "পড়ো", "ধরো", "ছাড়ো", "দিও", "নিও", "কোরো",
              "বেছে নাও", "ঢোকো", "থাকো"}
TUMI_ENDINGS = ("ছো", "ছিলে")
APNI_FORMS = {"আপনি", "আপনার", "আপনাকে", "আপনাদের", "আপনারা", "করুন", "দেখুন",
              "লিখুন", "দিন", "নিন", "যান", "আসুন", "পারেন", "আছেন", "জানেন", "চান",
              "রাখুন", "খুলুন", "থাকুন"}
APNI_ENDINGS = ("ছেন", "বেন", "ুন", "তেন", "লেন")
NOT_A_VERB = {"নতুন", "আগুন", "খুন", "গুন", "ফাগুন", "দ্বিগুন", "নুন", "চুন", "লেন",
              "প্লেন", "কেন", "যেন", "তেন", "দিন"}


def voice_words(text: str):
    tumi, apni = [], []
    for w in BN_WORD_RE.findall(text):
        w = w.strip(ZWJ + ZWNJ)
        if w in TUMI_FORMS or (len(w) >= 4 and w.endswith(TUMI_ENDINGS)):
            tumi.append(w)
        elif w in NOT_A_VERB:
            continue
        elif w in APNI_FORMS or (len(w) >= 4 and w.endswith(APNI_ENDINGS)):
            apni.append(w)
    return tumi, apni


# Characters that may not start a word: vowel signs, hasant, anusvara etc.
DEPENDENT = "\u0981-\u0983\u09BC\u09BE-\u09CD\u09D7"
CHECKS_TEXT = [
    ("error", re.compile(r"\u09C7\u09BE"), "decomposed ো (ে + া); normalize to NFC (U+09CB)"),
    ("error", re.compile(r"\u09C7\u09D7"), "decomposed ৌ (ে + ৗ); normalize to NFC (U+09CC)"),
    ("error", re.compile("\uFFFD"), "replacement character U+FFFD: text was corrupted by an encoding error"),
    ("error", re.compile(f"[{BN}]\\s?\\|\\s*$"), "pipe '|' used as a full stop; use দাঁড়ি '।' (U+0964)"),
    ("warning", re.compile(f"[{BN}]\\s?\\|\\s+(?=\\S)"), "pipe '|' between Bengali words; if it is a full stop use দাঁড়ি '।' (ignore for vue-i18n plural syntax 'one | other')"),
    ("error", re.compile(f"(?:^|(?<=[\\s(\\[\"'“‘>]))[{DEPENDENT}]"), "a vowel sign or mark starts a word; the text is damaged"),
    ("error", re.compile("\u09CD\u09CD"), "doubled হসন্ত"),
    ("error", re.compile(f"(?<![{BN}{ZWJ}{ZWNJ}])র\u09CDয"), "word-initial র্য renders as a reph; write র + ZWJ(U+200D) + ্য (র‍্য)"),
    ("error", re.compile("ত\u09CD(?=[\\s।,?!:;)\"”’]|$)"), "ত + হসন্ত at word end; use ৎ (U+09CE)"),
    ("error", re.compile("[\u0900-\u0963\u0966-\u097F]"), "Devanagari character inside Bengali text"),
    ("error", re.compile(r"[\u00C0-\u00FF]{3,}"), "Latin-1 accented letters in a run: Bijoy/ASCII legacy-font text or a broken encoding, not Unicode Bengali"),
    ("warning", re.compile("[ৰৱ]"), "Assamese letter (ৰ/ৱ) in Bengali text; did you mean র / ব?"),
    ("warning", re.compile("\u200B"), "zero-width space (U+200B)"),
    ("warning", re.compile(f"[{BN}]ঃ(?=\\s|$)(?<!বৃহঃ)"), "visarga ঃ at the end of a word; if it stands for a colon use ':'"),
    ("warning", re.compile(f"[{BN}]\\s+[।,?!;.](?!\\.)"), "space before punctuation"),
    ("warning", re.compile(f"[{BN}]\\.(?:\\s+[{BN}]|$)"), "'.' used as a full stop after Bengali text; use দাঁড়ি '।' (ignore for abbreviations such as ডা.)"),
    ("warning", re.compile("।[।]+"), "repeated দাঁড়ি"),
    ("warning", re.compile(f"।(?=[{BN}A-Za-z])"), "no space after দাঁড়ি"),
    ("warning", re.compile(f"[০-৯]\\s+টি|[০-৯]\\s+টা(?![{BN}])"), "space between a number and টি/টা; attach it (৩টি)"),
    ("warning", re.compile(f"[০-৯0-9]+\\s?টি\\s[{BN}]+(?:গুলো|গুলি|সমূহ)"), "number + plural suffix; after a number the noun stays singular"),
    ("warning", re.compile(r"\}(?:র|এর|য়ের|কে|তে|য়)(?![" + BN + "])"), "case suffix glued to a placeholder; use a hyphen ({name}-এর) or restructure"),
]
MIXED_DIGITS = re.compile(r"[0-9][.,]?[০-৯]|[০-৯][.,]?[0-9]")
MIXED_NUMBER = re.compile(r"[0-9০-৯]+(?:[.,][0-9০-৯]+)*")
BN_DIGIT = re.compile("[০-৯]")
# a free-standing Latin number in prose (not part of a code, ID, path, version or phone)
LATN_NUMBER = re.compile(r"(?<![A-Za-z0-9#_/.:=+\-])(?<![A-Za-z] )[0-9]+(?:[.,][0-9]+)*(?![A-Za-z0-9_/\-])")

# CSS that hurts Bengali script
CSS_LETTER_SPACING = re.compile(
    r"letter-spacing\s*:(?!\s*(?:0(?:\.0+)?[a-z%]*|normal)\s*(?:[;}\"'!]|$))\s*([^;}\"']+)", re.I)
CSS_LINE_HEIGHT = re.compile(r"line-height\s*:\s*(\d*\.?\d+)\s*(?=[;}\"'!]|$)", re.I)


def check_css(text: str, add) -> None:
    m = CSS_LETTER_SPACING.search(text)
    if m:
        add("warning", f"letter-spacing: {m.group(1).strip()} splits Bengali conjuncts; "
                       "reset it with :lang(bn) { letter-spacing: 0 }")
    for m in CSS_LINE_HEIGHT.finditer(text):
        try:
            value = float(m.group(1))
        except ValueError:
            continue
        if 0 < value < 1.4:
            add("warning", f"line-height {m.group(1)} is tight for Bengali (vowel signs sit above "
                           "and below the line); use about 1.5-1.7 for :lang(bn)")


def check_bengali(text: str, opts, add, source: str = "") -> None:
    """Checks that need only the Bengali text. `add(severity, message)`.

    `source` is the English string when known; a pipe that is already in the
    source is syntax (vue-i18n plurals, separators), not a misused full stop.
    """
    for sev, rx, msg in CHECKS_TEXT:
        if msg.startswith("Latin-1"):
            m = rx.search(text)
            if m and not BN_LETTER.search(text):
                add(sev, f"{msg}  […{m.group(0)[:20]}…]")
            continue
        if not BN_LETTER.search(text):
            continue
        if msg.startswith("pipe") and (text.count("|") >= 2 or "|" in source):
            continue  # a Markdown table row or plural syntax, not a sentence
        m = rx.search(text)
        if m:
            add(sev, f"{msg}  […{text[max(0, m.start() - 8): m.end() + 8]}…]")
    if not BN_LETTER.search(text):
        return
    if unicodedata.normalize("NFC", text) != text and not re.search(r"\u09C7[\u09BE\u09D7]", text):
        # NFC also decomposes precomposed য়/ড়/ঢ়; that is a mild inconsistency only
        add("warning", "text is not NFC-normalized (run unicodedata.normalize('NFC', s))")

    plain = strip_protected(text)
    if MIXED_DIGITS.search(plain):
        add("error", "Bengali and Latin digits mixed inside one number")
    if opts.digits == "bn":
        m = LATN_NUMBER.search(plain)
        if m:
            add("warning", f"Latin digits '{m.group(0)}' where the policy is Bengali digits "
                           "(fine for codes, IDs, phone inputs)")
    elif opts.digits == "latn" and BN_DIGIT.search(plain):
        add("warning", "Bengali digits where the policy is Latin digits")

    for wrong, right, note in MISSPELLINGS:
        rx = bn_word(wrong) if wrong in WHOLE_WORD_ONLY else bn_prefix(wrong)
        if rx.search(text):
            add("warning", f"spelling: '{wrong}' → '{right}'" + (f" ({note})" if note else ""))
    for wrong, right in BOOKISH:
        if bn_prefix(wrong).search(text):
            add("warning", f"bookish or wrong-sense term '{wrong}'; consider '{right}'")
    for w in SADHU:
        if bn_word(w).search(text):
            add("warning", f"সাধু form '{w}'; use চলিত")
            break
    tumi, apni = voice_words(text)
    if opts.tone == "apni" and tumi:
        add("warning", f"informal form '{tumi[0]}' but the voice is আপনি")
    if opts.tone == "tumi" and apni:
        add("warning", f"formal form '{apni[0]}' but the voice is তুমি")
    if tumi and apni:
        add("error", f"আপনি and তুমি forms mixed in one string ('{apni[0]}', '{tumi[0]}')")


# --------------------------------------------------------------------------
# Pair checks
# --------------------------------------------------------------------------
def check_icu(src: str, tgt: str, add) -> None:
    s_icu = scan_braces(mask_placeholders(src))[1]
    t_icu = {(b["arg"], b["kind"]): b for b in scan_braces(mask_placeholders(tgt))[1]}
    for b in s_icu:
        if b["kind"] not in ("plural", "select", "selectordinal"):
            continue
        tb = t_icu.get((b["arg"], b["kind"]))
        if tb is None:
            add("error", f"ICU '{b['kind']}' block for '{b['arg']}' is missing, or its keyword "
                         "or argument name was translated")
            continue
        if "other" not in tb["selectors"]:
            add("error", f"ICU {b['kind']} block for '{b['arg']}' has no 'other' branch")
        if b["kind"] == "select":
            if set(tb["selectors"]) != set(b["selectors"]):
                add("error", f"ICU select branches changed: source {sorted(b['selectors'])} vs "
                             f"target {sorted(tb['selectors'])} (branch keys are code values)")
        else:
            bad = [s for s in tb["selectors"] if s not in PLURAL_KEYS and not re.fullmatch(r"=\d+", s)]
            if bad:
                add("error", f"ICU plural branch keys translated or invalid: {bad}; "
                             "keep zero/one/two/few/many/other and =N")


def check_pair(src, tgt, opts, add, glossary) -> None:
    if not isinstance(tgt, str) or not isinstance(src, str):
        return
    if not tgt.strip():
        if src.strip():
            add("error", "empty translation")
        return
    colon = bool(COLON_PARAM_RE.search(src)) and not re.search(r"\d:\d", src)
    sp, tp = placeholders(src, colon), placeholders(tgt, colon)
    if sp != tp:
        missing = sorted(p for p in set(sp) if sp.count(p) > tp.count(p))
        extra = sorted(p for p in set(tp) if tp.count(p) > sp.count(p))
        parts = []
        if missing:
            parts.append("missing " + ", ".join(missing))
        if extra:
            parts.append("unexpected " + ", ".join(extra))
        msg = "placeholder mismatch: " + "; ".join(parts)
        if any(BN_LETTER.search(p) for p in extra):
            msg += " (a placeholder name was translated; it must stay exactly as in the source)"
        add("error", msg)
    st, tt = tags(src), tags(tgt)
    if st != tt:
        add("error", f"markup mismatch: source tags {st} vs target tags {tt}")
    if sorted(HREF_RE.findall(src)) != sorted(HREF_RE.findall(tgt)):
        add("error", "href/src attribute changed")
    if sorted(URL_RE.findall(src)) != sorted(URL_RE.findall(tgt)):
        add("warning", "URL changed or removed")
    if sorted(EMAIL_RE.findall(src)) != sorted(EMAIL_RE.findall(tgt)):
        add("warning", "email address changed or removed")
    check_icu(src, tgt, add)
    if src.count("{") == src.count("}") and tgt.count("{") != tgt.count("}"):
        add("error", "unbalanced braces")
    if (src[:1].isspace(), src[-1:].isspace()) != (tgt[:1].isspace(), tgt[-1:].isspace()):
        add("warning", "leading/trailing whitespace differs from the source")
    if src.endswith("\n") != tgt.endswith("\n"):
        add("error", "trailing newline differs from the source")

    src_plain, tgt_plain = strip_protected(src), strip_protected(tgt)
    n_words = len(re.findall(r"[A-Za-z]+", src_plain))
    if LATIN_WORD.search(src_plain) and n_words >= 2:
        if tgt.strip() == src.strip():
            add("warning", "identical to the source (untranslated?)")
        elif not BN_LETTER.search(tgt_plain):
            add("warning", "no Bengali text in the translation")
    for en_rx, bad, hint in SENSE_TRAPS:
        if re.search(en_rx, src_plain, re.I):
            for b in bad:
                if bn_prefix(b).search(tgt):
                    add("warning", f"possible wrong sense: '{b}' for /{en_rx}/; {hint}")
                    break
    src_nums = sorted(to_latin_digits(n) for n in re.findall(r"[0-9০-৯]+", src_plain))
    tgt_nums = sorted(to_latin_digits(n) for n in re.findall(r"[0-9০-৯]+", tgt_plain))
    if src_nums != tgt_nums and src_nums:
        add("warning", f"numbers differ: source {src_nums} vs target {tgt_nums} "
                       "(expected only for lakh/crore conversion or reworded dates)")
    if len(src) >= 12 and len(tgt) > 2.2 * len(src):
        add("warning", "translation is more than twice as long as the source; check for additions and layout")
    if src.rstrip().endswith("?") != tgt.rstrip().endswith("?"):
        add("warning", "question mark at the end differs from the source")
    if len(src.split()) <= 3 and not src.rstrip().endswith(".") and tgt.rstrip().endswith("।"):
        add("warning", "দাঁড়ি on a short label/button the source did not punctuate")

    for en, bn in glossary.items():
        if re.search(r"(?<![A-Za-z])" + re.escape(en) + r"(?![A-Za-z])", src_plain, re.I):
            options = bn if isinstance(bn, list) else [bn]
            if not any(o in tgt for o in options):
                add("warning", f"glossary: '{en}' should be '{options[0]}'")

    check_bengali(tgt, opts, add, source=src)


# --------------------------------------------------------------------------
# Loaders
# --------------------------------------------------------------------------
def read_text(path: Path):
    """Return (text, encoding). Bengali files must be UTF-8 (UTF-16 for iOS)."""
    try:
        raw = path.read_bytes()
    except OSError as e:
        raise UsageError(f"cannot read {path}: {e}")
    if raw.startswith((b"\xff\xfe", b"\xfe\xff")):
        return raw.decode("utf-16"), "utf-16"
    try:
        enc = "utf-8-sig" if raw.startswith(b"\xef\xbb\xbf") else "utf-8"
        return raw.decode(enc), enc
    except UnicodeDecodeError as e:
        raise LoadError(f"{path.name} is not valid UTF-8 ({e.reason} at byte {e.start}); "
                        "save it as UTF-8. Legacy (Bijoy/ANSI) encodings break Bengali text")


def flatten(obj, prefix="") -> dict:
    out = {}
    if isinstance(obj, dict):
        for k, v in obj.items():
            out.update(flatten(v, f"{prefix}.{k}" if prefix else str(k)))
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            out.update(flatten(v, f"{prefix}[{i}]"))
    else:
        out[prefix] = obj
    return out


def load_json(path: Path, notes: list, arb=False) -> dict:
    text, _ = read_text(path)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise LoadError(f"invalid JSON in {path.name}: {e}")
    if arb:
        if isinstance(data, dict):
            notes.append(("@@locale", data.get("@@locale")))
            data = {k: v for k, v in data.items() if not k.startswith("@")}
    return flatten(data)


def load_yaml(path: Path, notes: list) -> dict:
    try:
        import yaml  # type: ignore
    except ImportError:
        raise UsageError("YAML files need PyYAML: pip install pyyaml")
    text, _ = read_text(path)
    try:
        data = yaml.safe_load(text)
    except yaml.YAMLError as e:
        raise LoadError(f"invalid YAML in {path.name}: {e}")
    return data if isinstance(data, dict) else {}


def inner_xml(el) -> str:
    if el is None:
        return ""
    s = (el.text or "") + "".join(ET.tostring(c, encoding="unicode") for c in el)
    s = re.sub(r'\s+xmlns(?::\w+)?="[^"]*"', "", s)       # drop namespace declarations
    return re.sub(r"(</?)(?:ns\d+|\{[^}]*\}):?", r"\1", s)   # <ns0:x/> -> <x/>


def parse_xml(path: Path):
    text, _ = read_text(path)
    try:
        return ET.fromstring(text.encode("utf-8"))
    except ET.ParseError as e:
        raise LoadError(f"invalid XML in {path.name}: {e}")


def load_android(path: Path, notes: list) -> dict:
    root = parse_xml(path)
    out = {}
    for el in root:
        name = el.get("name")
        if not name or el.get("translatable") == "false":
            continue
        if el.tag == "string":
            out[name] = inner_xml(el)
        elif el.tag == "plurals":
            for item in el.findall("item"):
                out[f"{name}[{item.get('quantity')}]"] = inner_xml(item)
        elif el.tag == "string-array":
            for i, item in enumerate(el.findall("item")):
                out[f"{name}[{i}]"] = inner_xml(item)
    return out


STRINGS_PAIR = re.compile(r'"((?:[^"\\]|\\.)*)"\s*=\s*"((?:[^"\\]|\\.)*)"\s*;', re.S)
STRINGS_COMMENT = re.compile(r'("(?:[^"\\]|\\.)*")|/\*.*?\*/|//[^\n]*', re.S)


def load_strings(path: Path, notes: list) -> dict:
    text, _ = read_text(path)
    body = STRINGS_COMMENT.sub(lambda m: m.group(1) or "", text)
    leftover = STRINGS_PAIR.sub("", body).strip()
    if leftover:
        notes.append(("parse", f"cannot parse near '{leftover[:40]}' "
                               "(unescaped quote or missing ';' breaks the build)"))
    return dict(STRINGS_PAIR.findall(body))


def local_name(tag: str) -> str:
    return tag.rsplit("}", 1)[-1]


def load_xliff(path: Path, notes: list) -> list:
    """Return [(label, source, target)] for XLIFF 1.2 and 2.0."""
    root = parse_xml(path)
    lang = root.get("trgLang")
    entries = []
    for el in root.iter():
        name = local_name(el.tag)
        if name == "file" and not lang:
            lang = el.get("target-language")
        if name == "trans-unit":
            holders = [(el.get("id") or el.get("resname") or "?", el)]
        elif name == "unit":
            segs = [s for s in el if local_name(s.tag) == "segment"]
            holders = [(f"{el.get('id')}" + (f"#{i + 1}" if len(segs) > 1 else ""), s)
                       for i, s in enumerate(segs)]
        else:
            continue
        for label, holder in holders:
            src = next((c for c in holder if local_name(c.tag) == "source"), None)
            tgt = next((c for c in holder if local_name(c.tag) == "target"), None)
            if src is not None:
                entries.append((label, inner_xml(src), inner_xml(tgt)))
    if lang and not lang.lower().startswith("bn"):
        notes.append(("lang", f"target language is '{lang}', expected bn / bn-BD / bn-IN"))
    return entries


def load_xcstrings(path: Path, notes: list, lang: str = "bn") -> list:
    """Xcode String Catalog. Return [(label, source, target or None, state)]."""
    text, _ = read_text(path)
    try:
        data = json.loads(text)
    except json.JSONDecodeError as e:
        raise LoadError(f"invalid JSON in {path.name}: {e}")
    src_lang = data.get("sourceLanguage", "en")

    def units(node, suffix=""):
        out = {}
        if not isinstance(node, dict):
            return out
        if isinstance(node.get("stringUnit"), dict):
            out[suffix] = (node["stringUnit"].get("value", ""), node["stringUnit"].get("state", ""))
        for kind, variants in (node.get("variations") or {}).items():
            for name, sub in (variants or {}).items():
                out.update(units(sub, f"{suffix}[{kind}:{name}]"))
        return out

    entries = []
    for key, item in (data.get("strings") or {}).items():
        if not isinstance(item, dict) or item.get("shouldTranslate") is False:
            continue
        locs = item.get("localizations") or {}
        src = units(locs.get(src_lang)) or {"": (key, "")}
        tgt = units(locs.get(lang)) if lang in locs else {}
        base = src.get("", next(iter(src.values())))[0]
        for suffix in sorted(set(src) | set(tgt)):
            if suffix in tgt:
                value, state = tgt[suffix]
                s = src.get(suffix, (base, ""))[0]
                entries.append((key + suffix, s, value, state))
            elif not (suffix and re.search(r":(?:zero|two|few|many)\]$", suffix)):
                entries.append((key + suffix, src[suffix][0], None, ""))
    return entries


def load_po(path: Path) -> list:
    """Return [(label, msgid, msgstr, fuzzy)] including plural forms."""
    entries, cur, field, fuzzy = [], {}, None, False

    def unquote(s: str) -> str:
        s = s.strip()
        if s.startswith('"') and s.endswith('"'):
            s = s[1:-1]
        return s.replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")

    def flush():
        nonlocal cur, fuzzy
        if cur.get("msgid"):
            ctx = cur.get("msgctxt", "")
            label = (ctx + " | " if ctx else "") + cur["msgid"][:50].replace("\n", "⏎")
            if "msgid_plural" in cur:
                for k, v in sorted(cur.items()):
                    if k.startswith("msgstr["):
                        src = cur["msgid"] if k == "msgstr[0]" else cur["msgid_plural"]
                        entries.append((f"{label} {k}", src, v, fuzzy))
            else:
                entries.append((label, cur["msgid"], cur.get("msgstr", ""), fuzzy))
        cur, fuzzy = {}, False

    text, _ = read_text(path)
    for line in text.splitlines():
        line = line.strip()
        if not line:
            flush()
            field = None
        elif line.startswith("#,") and "fuzzy" in line:
            fuzzy = True
        elif line.startswith("#"):
            continue
        elif line.startswith('"') and field:
            cur[field] += unquote(line)
        else:
            m = re.match(r"(msgctxt|msgid_plural|msgid|msgstr(?:\[\d+\])?)\s+(.*)", line)
            if m:
                field = m.group(1)
                cur[field] = unquote(m.group(2))
    flush()
    return entries


# --------------------------------------------------------------------------
# HTML pages
# --------------------------------------------------------------------------
TRANSLATABLE_ATTRS = {"alt", "title", "placeholder", "aria-label", "aria-description",
                      "aria-roledescription", "aria-placeholder", "label"}
META_TRANSLATABLE = {"description", "keywords", "og:title", "og:description", "og:site_name",
                     "og:image:alt", "twitter:title", "twitter:description", "twitter:image:alt",
                     "application-name", "apple-mobile-web-app-title"}
META_LOCALE = {"og:locale", "content-language", "language"}
FREE_ATTRS = {"lang", "dir", "style", "hreflang"}   # may legitimately change in translation
VOID_TAGS = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta",
             "source", "track", "wbr"}


class PageCollector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.structure, self.items, self.css = [], [], []
        self.lang = None
        self.has_html = False
        self._open, self._raw = [], None

    def _start(self, tag, attrs, closed):
        line = self.getpos()[0]
        a = {k: (v or "") for k, v in attrs}
        if tag == "html":
            self.has_html = True
            self.lang = a.get("lang")
        meta_key = (a.get("name") or a.get("property") or a.get("http-equiv") or "").lower()
        fixed = []
        for k, v in sorted(a.items()):
            if k in FREE_ATTRS:
                if k == "style":
                    self.css.append((line, v))
                continue
            if tag == "link" and k == "href" and a.get("rel", "").lower() in ("canonical", "alternate"):
                continue
            translatable = (
                k in TRANSLATABLE_ATTRS
                or (tag == "meta" and k == "content" and meta_key in META_TRANSLATABLE)
                or (tag == "input" and k == "value" and a.get("type", "").lower() in ("submit", "button", "reset")))
            if tag == "meta" and k == "content" and meta_key in META_LOCALE:
                continue
            if translatable:
                if v.strip():
                    self.items.append((f"line {line} <{tag} {k}>", v.strip()))
            else:
                fixed.append((k, v))
        self.structure.append(("<" + tag, tuple(fixed), line))
        if tag in ("script", "style") and not closed:
            self._raw = tag
        elif not closed and tag not in VOID_TAGS:
            self._open.append(tag)

    def handle_starttag(self, tag, attrs):
        self._start(tag, attrs, False)

    def handle_startendtag(self, tag, attrs):
        self._start(tag, attrs, True)

    def handle_endtag(self, tag):
        if tag == self._raw:
            self._raw = None
        if tag in self._open:
            while self._open and self._open.pop() != tag:
                pass
        self.structure.append(("</" + tag, (), self.getpos()[0]))

    def handle_data(self, data):
        line = self.getpos()[0]
        if self._raw == "style":
            self.css.append((line, data))
        if self._raw or not data.strip():
            return
        where = f"<{self._open[-1]}>" if self._open else "text"
        self.items.append((f"line {line} {where}", " ".join(data.split())))


def collect_page(path: Path) -> PageCollector:
    text, _ = read_text(path)
    page = PageCollector()
    page.feed(text)
    page.close()
    return page


def describe(node) -> str:
    tag, attrs, line = node
    shown = " ".join(f'{k}="{v}"' for k, v in attrs)
    return f"line {line} {tag}{(' ' + shown) if shown else ''}>"


def lint_html_pair(spath: Path, tpath: Path, opts, adder, glossary) -> int:
    src, tgt = collect_page(spath), collect_page(tpath)
    page = adder(tpath.name)
    if src.has_html:
        if not tgt.lang:
            page("error", '<html> has no lang attribute; set lang="bn" (or bn-BD / bn-IN)')
        elif not tgt.lang.lower().startswith("bn"):
            page("error", f'<html lang="{tgt.lang}">; set lang="bn" (or bn-BD / bn-IN) so fonts, '
                          "screen readers and search engines treat the page as Bengali")
    s_struct = [(t, a) for t, a, _ in src.structure]
    t_struct = [(t, a) for t, a, _ in tgt.structure]
    if s_struct != t_struct:
        sm = difflib.SequenceMatcher(a=s_struct, b=t_struct, autojunk=False)
        shown = 0
        for op, i1, i2, j1, j2 in sm.get_opcodes():
            if op == "equal":
                continue
            shown += 1
            if shown > 10:
                page("error", "more markup differences not shown")
                break
            s_desc = "; ".join(describe(n) for n in src.structure[i1:i2][:2]) or "(nothing)"
            t_desc = "; ".join(describe(n) for n in tgt.structure[j1:j2][:2]) or "(nothing)"
            page("error", f"markup differs - source {s_desc}  vs  target {t_desc}")
    for line, css in tgt.css:
        check_css(css, adder(f"{tpath.name}:{line}"))

    checked = 0
    if s_struct == t_struct and len(src.items) == len(tgt.items):
        for (_, s_text), (label, t_text) in zip(src.items, tgt.items):
            check_pair(s_text, t_text, opts, adder(f"{tpath.name} {label}"), glossary)
            checked += 1
    else:
        if len(src.items) != len(tgt.items):
            page("warning", f"{len(src.items)} text items in the source but {len(tgt.items)} in "
                            "the target; strings could not be paired, so only Bengali checks ran")
        for label, t_text in tgt.items:
            add = adder(f"{tpath.name} {label}")
            words = re.findall(r"[A-Za-z]+", strip_protected(t_text))
            if len(words) >= 3 and not BN_LETTER.search(t_text):
                add("warning", "no Bengali text (untranslated?)")
            check_bengali(t_text, opts, add)
            checked += 1
    return checked


# --------------------------------------------------------------------------
# Safe auto-fix
# --------------------------------------------------------------------------
PROTECT_RE = re.compile("|".join(f"(?:{rx.pattern})" for rx in (
    TAG_RE, URL_RE, EMAIL_RE, CODE_SPAN_RE, PLACEHOLDER_RE, ICU_HEAD_RE, ICU_SELECTOR_RE,
    SIMPLE_BRACE_RE)), re.S)

FIX_RULES = [
    ("composed ে + া into ো", re.compile("\u09C7\u09BE"), "\u09CB"),
    ("composed ে + ৗ into ৌ", re.compile("\u09C7\u09D7"), "\u09CC"),
    ("removed zero-width space", re.compile("\u200B"), ""),
    ("removed doubled হসন্ত", re.compile("\u09CD\u09CD"), "\u09CD"),
    ("added ZWJ to word-initial র্য (র‍্য)", re.compile(f"(?<![{BN}{ZWJ}{ZWNJ}])র\u09CD(?=য)"), "র\u200d\u09CD"),
    ("ত্ at word end → ৎ", re.compile("ত\u09CD(?=[\\s।,?!:;)\"”’]|$)"), "ৎ"),
    # only a pipe that ends the string: a pipe mid-string may be vue-i18n plural syntax
    ("pipe '|' → দাঁড়ি '।'", re.compile(f"([{BN}])\\s?\\|(?=\\s*$)"), "\\1।"),
    ("removed space before punctuation", re.compile(f"([{BN}])\\s+([।,?!;])"), "\\1\\2"),
    ("collapsed repeated দাঁড়ি", re.compile("।{2,}"), "।"),
    ("added space after দাঁড়ি", re.compile(f"।(?=[{BN}A-Za-z])"), "। "),
    ("attached টি/টা to the number", re.compile(f"([০-৯0-9])\\s+(টি|টা)(?![{BN}])"), "\\1\\2"),
]


def fix_segment(seg: str, opts, whole: str, changes: list) -> str:
    seg = fix_digits(seg, opts, changes)   # first, so the punctuation rules see Bengali digits
    for name, rx, repl in FIX_RULES:
        if name.startswith("pipe") and whole.count("|") >= 2:
            continue
        new = rx.sub(repl, seg)
        if new != seg:
            changes.append(name)
            seg = new
    for wrong, right, _ in MISSPELLINGS:
        rx = bn_word(wrong) if wrong in WHOLE_WORD_ONLY else bn_prefix(wrong)
        new = rx.sub(right, seg)
        if new != seg:
            changes.append(f"spelling {wrong} → {right}")
            seg = new
    return seg


def fix_digits(seg: str, opts, changes: list) -> str:
    # a number written with both digit sets: unify (Bengali unless the policy is Latin)
    table = TO_LATN if opts.digits == "latn" else TO_BN

    def unify(m):
        s = m.group(0)
        if MIXED_DIGITS.search(s):
            changes.append("unified mixed digits in one number")
            return s.translate(table)
        return s
    seg = MIXED_NUMBER.sub(unify, seg)
    if opts.digits == "bn":
        new = LATN_NUMBER.sub(lambda m: m.group(0).translate(TO_BN), seg)
        if new != seg:
            changes.append("Latin digits → Bengali digits")
            seg = new
    elif opts.digits == "latn":
        new = seg.translate(TO_LATN)
        if new != seg:
            changes.append("Bengali digits → Latin digits")
            seg = new
    return seg


def fix_text(text: str, opts):
    """Apply safe fixes outside placeholders, tags, URLs and code. Returns (text, changes)."""
    if not BN_LETTER.search(text):
        return text, []
    changes, out, pos = [], [], 0
    for m in PROTECT_RE.finditer(text):
        if m.start() > pos:
            out.append(fix_segment(text[pos:m.start()], opts, text, changes))
        out.append(m.group(0))
        pos = m.end()
    if pos < len(text):
        out.append(fix_segment(text[pos:], opts, text, changes))
    return "".join(out), changes


def detect_indent(text: str):
    m = re.search(r"\n([ \t]+)\S", text)
    if not m:
        return None
    return "\t" if m.group(1).startswith("\t") else len(m.group(1))


def fix_file(path: Path, opts) -> list:
    """Fix `path` in place. Returns [(where, change)]."""
    text, enc = read_text(path)
    ext = path.suffix.lower()
    found = []

    if ext in (".json", ".arb"):
        try:
            data = json.loads(text)
        except json.JSONDecodeError as e:
            raise LoadError(f"invalid JSON in {path.name}: {e}")

        def walk(node, key):
            if isinstance(node, dict):
                return {k: (v if ext == ".arb" and k.startswith("@")
                            else walk(v, f"{key}.{k}" if key else k)) for k, v in node.items()}
            if isinstance(node, list):
                return [walk(v, f"{key}[{i}]") for i, v in enumerate(node)]
            if isinstance(node, str):
                new, ch = fix_text(node, opts)
                found.extend((key, c) for c in ch)
                return new
            return node
        new_data = walk(data, "")
        if not found:
            return []
        indent = detect_indent(text)
        new_text = json.dumps(new_data, ensure_ascii=False, indent=indent,
                              separators=None if indent is not None else (",", ":"))
        if text.endswith("\n"):
            new_text += "\n"
    else:
        lines = text.split("\n")
        in_fence = False
        po_line = re.compile(r'^(\s*(?:msgstr(?:\[\d+\])?\s+)?)(".*")(\s*)$')
        yaml_line = re.compile(r"^(\s*(?:-\s+)?[^\s:#][^:#]*?:\s+)(.*)$")
        for n, line in enumerate(lines):
            if line.lstrip().startswith(("```", "~~~")):
                in_fence = not in_fence
                continue
            if in_fence or not BN_LETTER.search(line):
                continue
            ch = []

            def fix_part(s):
                new, c = fix_text(s, opts)
                ch.extend(c)
                return new
            if ext == ".strings":
                new = STRINGS_PAIR.sub(lambda m: m.group(0)[:m.start(2) - m.start(0)]
                                       + fix_part(m.group(2)) + m.group(0)[m.end(2) - m.start(0):], line)
            elif ext in (".po", ".pot"):
                m = po_line.match(line)
                new = (m.group(1) + fix_part(m.group(2)) + m.group(3)) if m else line
            elif ext in (".yml", ".yaml"):
                m = yaml_line.match(line)
                new = (m.group(1) + fix_part(m.group(2))) if m else fix_part(line)
            else:
                new = fix_part(line)
            if new != line:
                lines[n] = new
                found.extend((f"{path.name}:{n + 1}", c) for c in ch)
        if not found:
            return []
        new_text = "\n".join(lines)
    with open(path, "w", encoding=enc, newline="") as fh:   # newline="" keeps CRLF files as they are
        fh.write(new_text)
    return found


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
OPTIONAL_PLURAL = re.compile(r"(?:_(?:zero|two|few|many)|\[(?:zero|two|few|many)\])$")
ANY_PLURAL = re.compile(r"(?:_(?:zero|one|two|few|many|other)|\[(?:zero|one|two|few|many|other)\])$")
PAIR_LOADERS = {
    ".json": lambda p, n: load_json(p, n),
    ".arb": lambda p, n: load_json(p, n, arb=True),
    ".yml": load_yaml, ".yaml": load_yaml,
    ".xml": load_android,
    ".strings": load_strings,
}


def load_glossary(path):
    if not path:
        return {}
    text, _ = read_text(Path(path))
    try:
        g = json.loads(text)
    except json.JSONDecodeError as e:
        raise UsageError(f"invalid glossary JSON: {e}")
    g = g.get("terms", g)
    return {k: v for k, v in g.items() if not k.startswith("_") and isinstance(v, (str, list))}


def lint_pair_maps(spath, tpath, opts, adder, glossary) -> int:
    ext = tpath.suffix.lower()
    loader = PAIR_LOADERS.get(ext)
    if loader is None:
        raise UsageError(f"pair mode does not know '{ext}' files; use --target-only for Bengali-only checks")
    s_notes, t_notes = [], []
    src, tgt = loader(spath, s_notes), loader(tpath, t_notes)
    fileadd = adder(tpath.name)
    for kind, value in t_notes:
        if kind == "@@locale" and value and not str(value).lower().startswith("bn"):
            fileadd("warning", f'"@@locale" is "{value}"; set it to "bn"')
        elif kind == "parse":
            fileadd("error", value)
    if ext in (".yml", ".yaml"):
        if len(src) == 1 and len(tgt) == 1:
            (sk, sv), (tk, tv) = next(iter(src.items())), next(iter(tgt.items()))
            if isinstance(sv, dict) and isinstance(tv, dict):
                if tk == sk and not str(tk).lower().startswith("bn"):
                    fileadd("warning", f"top-level locale key is still '{tk}:'; Rails/i18n expects 'bn:'")
                src, tgt = sv, tv
        src, tgt = flatten(src), flatten(tgt)

    checked = 0
    for key, sval in src.items():
        add = adder(key)
        if key not in tgt:
            if OPTIONAL_PLURAL.search(key):
                continue  # Bengali needs only the one/other plural forms
            add("error", "key missing in target")
            continue
        tval = tgt[key]
        check_pair(sval, tval, opts, add, glossary)
        if ext == ".xml" and isinstance(tval, str) and re.search(r"(?<!\\)'", tval) \
                and not (tval.startswith('"') and tval.endswith('"')):
            add("error", "unescaped apostrophe; Android needs \\' (or wrap the string in double quotes)")
        checked += 1
    for key in tgt:
        if key not in src and not ANY_PLURAL.search(key):
            adder(key)("warning", "key not present in source")
    return checked


def run_lint(opts, adder, glossary) -> int:
    if opts.target_only:
        path = Path(opts.target_only)
        text, _ = read_text(path)
        checked, in_fence = 0, False
        for n, line in enumerate(text.splitlines(), 1):
            if line.lstrip().startswith(("```", "~~~")):
                in_fence = not in_fence
                continue
            if in_fence:
                continue
            add = adder(f"{path.name}:{n}")
            check_bengali(line, opts, add)
            if path.suffix.lower() in (".html", ".htm", ".css", ".scss", ".vue", ".svelte", ".jsx", ".tsx"):
                check_css(line, add)
            checked += 1
        return checked

    tpath = Path(opts.target)
    ext = tpath.suffix.lower()
    if ext in (".po", ".pot"):
        checked = 0
        for label, src, tgt, fuzzy in load_po(tpath):
            add = adder(label)
            if fuzzy:
                add("warning", "entry is still marked fuzzy")
            check_pair(src, tgt, opts, add, glossary)
            checked += 1
        return checked
    if ext in (".xlf", ".xliff"):
        notes = []
        entries = load_xliff(tpath, notes)
        for _, msg in notes:
            adder(tpath.name)("warning", msg)
        for label, src, tgt in entries:
            check_pair(src, tgt, opts, adder(label), glossary)
        return len(entries)
    if ext == ".xcstrings":
        entries = load_xcstrings(tpath, [])
        for label, src, tgt, state in entries:
            add = adder(label)
            if tgt is None:
                add("error", "no Bengali (bn) localization")
                continue
            if state in ("needs_review", "new", "stale"):
                add("warning", f"Bengali localization state is '{state}'")
            check_pair(src, tgt, opts, add, glossary)
        return len(entries)
    if not opts.source:
        raise UsageError(f"{tpath.name}: give the English file with --source "
                         "(or use --target-only for Bengali-only checks)")
    spath = Path(opts.source)
    if not spath.is_file():
        raise UsageError(f"source file not found: {spath}")
    if ext in (".html", ".htm"):
        return lint_html_pair(spath, tpath, opts, adder, glossary)
    return lint_pair_maps(spath, tpath, opts, adder, glossary)


def main(argv=None) -> int:
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass

    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", help="English source file")
    ap.add_argument("--target", help="Bengali target file (or a .po / .xlf holding both)")
    ap.add_argument("--target-only", dest="target_only", help="any Bengali text file; Bengali checks only")
    ap.add_argument("--digits", choices=["bn", "latn", "any"], default="any")
    ap.add_argument("--tone", choices=["apni", "tumi"], default="apni")
    ap.add_argument("--glossary", help='JSON file: {"english term": "বাংলা"} (a "terms" object is also accepted)')
    ap.add_argument("--fix", action="store_true", help="apply safe mechanical fixes to the target in place, then lint")
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--strict", action="store_true", help="warnings also fail")
    ap.add_argument("--version", action="version", version=f"bn_lint {__version__}")
    opts = ap.parse_args(argv)

    findings, fixes = [], []

    def adder(where):
        def add(sev, msg):
            findings.append({"severity": sev, "where": where, "message": msg})
        return add

    target = opts.target_only or opts.target
    checked = 0
    try:
        if not target:
            raise UsageError("give --source and --target, a .po/.xlf --target, or --target-only")
        if not Path(target).is_file():
            raise UsageError(f"target file not found: {target}")
        glossary = load_glossary(opts.glossary)
        if opts.fix:
            fixes = fix_file(Path(target), opts)
        checked = run_lint(opts, adder, glossary)
    except UsageError as e:
        ap.print_usage(sys.stderr)
        print(f"error: {e}", file=sys.stderr)
        return 2
    except LoadError as e:
        adder(Path(target).name)("error", str(e))

    errors = sum(f["severity"] == "error" for f in findings)
    warnings = len(findings) - errors
    if opts.json:
        print(json.dumps({"version": __version__, "checked": checked, "errors": errors,
                          "warnings": warnings, "fixed": [{"where": w, "change": c} for w, c in fixes],
                          "findings": findings}, ensure_ascii=False, indent=2))
    else:
        if opts.fix:
            for where, change in fixes:
                print(f"fixed   {where}: {change}")
            print(f"{len(fixes)} fix(es) written to {target}.\n" if fixes else "Nothing to auto-fix.\n")
        for f in findings:
            mark = "ERROR  " if f["severity"] == "error" else "warning"
            print(f"{mark} {f['where']}: {f['message']}")
        print(f"\n{checked} strings checked: {errors} error(s), {warnings} warning(s).")
        if not findings:
            print("No mechanical problems found. Meaning and tone still need a human-style read.")
    return 1 if errors or (opts.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
