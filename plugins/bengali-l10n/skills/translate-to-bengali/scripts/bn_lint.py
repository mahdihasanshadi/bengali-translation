#!/usr/bin/env python3
"""bn_lint.py - QA linter for English -> Bengali website translations.

Two modes:

  Pair mode (JSON or gettext .po): compares source and target.
      python bn_lint.py --source en.json --target bn.json
      python bn_lint.py --target bn.po            (a .po holds both sides)

  Target-only mode (any text file: HTML, Markdown, YAML, .strings, ...):
      python bn_lint.py --target-only public/bn/index.html

Options:
  --digits bn|latn|any   digit policy for Bengali text (default: any;
                         mixed digits inside one number are always an error)
  --tone apni|tumi       expected form of address (default: apni)
  --glossary FILE        JSON {"english term": "বাংলা"}; checks consistency
  --json                 machine-readable output
  --strict               exit 1 on warnings as well as errors

Exit code: 0 clean, 1 errors found (or warnings with --strict), 2 usage error.
No third-party dependencies. Python 3.8+.

The linter finds mechanical problems. It cannot judge whether the meaning is
right; that still needs a careful read.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

BN = "\u0980-\u09FF"
BN_LETTER = re.compile(f"[{BN}]")
LATIN_WORD = re.compile(r"[A-Za-z][A-Za-z'’-]{2,}")
ZWJ, ZWNJ = "\u200d", "\u200c"


def bn_word(word: str) -> re.Pattern:
    """Match `word` only when it is not embedded in a longer Bengali word."""
    return re.compile(f"(?<![{BN}{ZWJ}{ZWNJ}]){re.escape(word)}(?![{BN}{ZWJ}{ZWNJ}])")


def bn_prefix(stem: str) -> re.Pattern:
    """Match a word that starts with `stem` (suffixes such as -তে, -র allowed)."""
    return re.compile(f"(?<![{BN}{ZWJ}{ZWNJ}]){re.escape(stem)}")


# --------------------------------------------------------------------------
# Placeholders and markup
# --------------------------------------------------------------------------
PLACEHOLDER_PATTERNS = [
    r"\{\{\s*[^{}]+?\s*\}\}",                  # {{name}}  (i18next, Handlebars, Liquid)
    r"\{%.*?%\}",                              # {% tag %}
    r"\$\{[^{}]+\}",                           # ${name}
    r"%\([A-Za-z_]\w*\)[sdif]",                # %(name)s
    r"%(?:\d+\$)?[-+0 #]*\d*(?:\.\d+)?[sdifuxXc@]",  # %s %d %1$s %.2f %@
    r"\$t\([^)]*\)",                           # $t(key)
    r"@:[\w.]+",                               # @:linked.key (vue-i18n)
    r"&(?:[a-zA-Z]+|#\d+|#x[0-9a-fA-F]+);",    # HTML entities
    r"\\[ntr]",                                # escapes written literally
]
PLACEHOLDER_RE = re.compile("|".join(PLACEHOLDER_PATTERNS), re.S)
SIMPLE_BRACE_RE = re.compile(r"\{\s*([A-Za-z_][\w.]*|\d+)\s*\}")      # {name} {0}
ICU_ARG_RE = re.compile(r"\{\s*([A-Za-z_]\w*)\s*,\s*(plural|select|selectordinal)\s*,")
ICU_ANY_ARG_RE = re.compile(r"\{\s*([A-Za-z_]\w*)\s*,\s*(?:plural|select|selectordinal|number|date|time)\b")
COLON_PARAM_RE = re.compile(r"(?<![\w:/]):([a-z_][a-z0-9_]*)\b")     # :name (Laravel)
TAG_RE = re.compile(r"</?\s*([A-Za-z][\w:-]*|\d+)\b[^<>]*?/?>")
HREF_RE = re.compile(r"""(?:href|src)\s*=\s*["']([^"']+)["']""")
URL_RE = re.compile(r"https?://[^\s\"'<>)]+")
EMAIL_RE = re.compile(r"[\w.+-]+@[\w-]+\.[\w.-]+")


def placeholders(text: str, colon_params: bool) -> list:
    found = PLACEHOLDER_RE.findall(text)
    found += ["{" + m + "}" for m in SIMPLE_BRACE_RE.findall(text)]
    found += ["{" + m + ",…}" for m in ICU_ANY_ARG_RE.findall(text)]
    if colon_params:
        found += [":" + m for m in COLON_PARAM_RE.findall(text)]
    return sorted(re.sub(r"\s+", "", f) for f in found)


def tags(text: str) -> list:
    out = []
    for m in TAG_RE.finditer(text):
        raw = m.group(0)
        name = m.group(1).lower()
        if raw.startswith("</"):
            out.append("/" + name)
        elif raw.endswith("/>"):
            out.append(name + "/")
        else:
            out.append(name)
    return sorted(out)


# --------------------------------------------------------------------------
# Bengali-only checks
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
    (r"\bsave\s+(up to\s+)?[\d৳$₹]", ["সংরক্ষণ", "সেভ", "বাঁচ"], "a discount is ছাড় / সাশ্রয়"),
    (r"\bsave\b", ["বাঁচান", "রক্ষা করুন"], "use সেভ করুন / সংরক্ষণ করুন"),
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
]

SADHU = ["করিবেন", "করিতে", "করিয়া", "হইবে", "হইয়াছে", "হইতে", "ইহা", "ইহার",
         "তাহার", "তাহাদের", "যাহা", "উহা", "করিয়াছেন", "দেখিবেন", "হইলে"]
TUMI_FORMS = ["তুমি", "তোমার", "তোমাকে", "তোমাদের", "করো", "দেখো", "লেখো", "দাও",
              "নাও", "যাও", "পাঠাও", "তুই", "তোর", "তোকে"]
APNI_FORMS = ["আপনি", "আপনার", "আপনাকে", "আপনাদের", "করুন", "দেখুন", "লিখুন"]

# Characters that may not start a word: vowel signs, hasant, anusvara etc.
DEPENDENT = "\u0981-\u0983\u09BC\u09BE-\u09CD\u09D7"
CHECKS_TEXT = [
    ("error", re.compile(r"\u09C7\u09BE"), "decomposed ো (ে + া); normalize to NFC (U+09CB)"),
    ("error", re.compile(r"\u09C7\u09D7"), "decomposed ৌ (ে + ৗ); normalize to NFC (U+09CC)"),
    ("error", re.compile("\uFFFD"), "replacement character U+FFFD: text was corrupted by an encoding error"),
    ("error", re.compile(f"[{BN}]\\s?\\|(?:\\s|$)"), "pipe '|' used as a full stop; use দাঁড়ি '।' (U+0964)"),
    ("error", re.compile(f"(?:^|(?<=[\\s(\\[\"'“‘>]))[{DEPENDENT}]"), "a vowel sign or mark starts a word; the text is damaged"),
    ("error", re.compile("\u09CD\u09CD"), "doubled হসন্ত"),
    ("error", re.compile(f"(?<![{BN}{ZWJ}{ZWNJ}])র\u09CDয"), "word-initial র্য renders as a reph; write র + ZWJ(U+200D) + ্য (র‍্য)"),
    ("error", re.compile("ত\u09CD(?=[\\s।,?!:;)\"”’]|$)"), "ত + হসন্ত at word end; use ৎ (U+09CE)"),
    ("error", re.compile("[\u0900-\u0963\u0966-\u097F]"), "Devanagari character inside Bengali text"),
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
BN_DIGIT = re.compile("[০-৯]")
LATIN_DIGIT = re.compile("[0-9]")


def strip_protected(text: str) -> str:
    """Remove things that legitimately stay Latin, before digit/Latin checks."""
    text = TAG_RE.sub(" ", text)
    text = URL_RE.sub(" ", text)
    text = EMAIL_RE.sub(" ", text)
    text = PLACEHOLDER_RE.sub(" ", text)
    text = ICU_ARG_RE.sub(" ", text)
    text = SIMPLE_BRACE_RE.sub(" ", text)
    return text


def check_bengali(text: str, opts, add) -> None:
    """Checks that need only the Bengali text. `add(severity, message)`."""
    if not BN_LETTER.search(text):
        return
    for sev, rx, msg in CHECKS_TEXT:
        if msg.startswith("pipe") and text.count("|") >= 2:
            continue  # a Markdown table row, not a sentence
        m = rx.search(text)
        if m:
            add(sev, f"{msg}  […{text[max(0, m.start() - 8): m.end() + 8]}…]")
    if unicodedata.normalize("NFC", text) != text and not re.search(r"\u09C7[\u09BE\u09D7]", text):
        # NFC also decomposes precomposed য়/ড়/ঢ়; that is a mild inconsistency only
        add("warning", "text is not NFC-normalized (run unicodedata.normalize('NFC', s))")

    plain = strip_protected(text)
    if MIXED_DIGITS.search(plain):
        add("error", "Bengali and Latin digits mixed inside one number")
    if opts.digits == "bn":
        m = re.search(r"(?<![A-Za-z0-9#_/.:-])(?<![A-Za-z] )[0-9]+(?:[.,][0-9]+)*(?![A-Za-z0-9_/-])", plain)
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
    has_tumi = [w for w in TUMI_FORMS if bn_word(w).search(text)]
    has_apni = [w for w in APNI_FORMS if bn_word(w).search(text)]
    if opts.tone == "apni" and has_tumi:
        add("warning", f"informal form '{has_tumi[0]}' but the voice is আপনি")
    if opts.tone == "tumi" and has_apni:
        add("warning", f"formal form '{has_apni[0]}' but the voice is তুমি")
    if has_tumi and has_apni:
        add("error", f"আপনি and তুমি forms mixed in one string ('{has_apni[0]}', '{has_tumi[0]}')")


# --------------------------------------------------------------------------
# Pair checks
# --------------------------------------------------------------------------
def check_pair(src: str, tgt: str, opts, add, glossary) -> None:
    if not isinstance(tgt, str) or not isinstance(src, str):
        return
    if not tgt.strip():
        if src.strip():
            add("error", "empty translation")
        return
    colon = bool(COLON_PARAM_RE.search(src)) and not re.search(r"\d:\d", src)
    sp, tp = placeholders(src, colon), placeholders(tgt, colon)
    if sp != tp:
        missing = [p for p in set(sp) if sp.count(p) > tp.count(p)]
        extra = [p for p in set(tp) if tp.count(p) > sp.count(p)]
        parts = []
        if missing:
            parts.append("missing " + ", ".join(sorted(missing)))
        if extra:
            parts.append("unexpected " + ", ".join(sorted(extra)))
        add("error", "placeholder mismatch: " + "; ".join(parts))
    st, tt = tags(src), tags(tgt)
    if st != tt:
        add("error", f"markup mismatch: source tags {st} vs target tags {tt}")
    if sorted(HREF_RE.findall(src)) != sorted(HREF_RE.findall(tgt)):
        add("error", "href/src attribute changed")
    if sorted(URL_RE.findall(src)) != sorted(URL_RE.findall(tgt)):
        add("warning", "URL changed or removed")
    for m in ICU_ARG_RE.finditer(src):
        arg, kind = m.group(1), m.group(2)
        if not re.search(r"\{\s*" + re.escape(arg) + r"\s*,\s*" + kind + r"\s*,", tgt):
            add("error", f"ICU '{kind}' block for '{arg}' is missing or its keyword was translated")
        elif "other" not in tgt[tgt.find(arg):]:
            add("error", "ICU block has no 'other' branch")
    if src.count("{") - src.count("}") == 0 and tgt.count("{") != tgt.count("}"):
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

    check_bengali(tgt, opts, add)


def to_latin_digits(s: str) -> str:
    return s.translate(str.maketrans("০১২৩৪৫৬৭৮৯", "0123456789"))


# --------------------------------------------------------------------------
# Loaders
# --------------------------------------------------------------------------
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


def load_json(path: Path) -> dict:
    with path.open(encoding="utf-8-sig") as fh:
        return flatten(json.load(fh))


def unquote_po(s: str) -> str:
    s = s.strip()
    if s.startswith('"') and s.endswith('"'):
        s = s[1:-1]
    return s.replace('\\"', '"').replace("\\n", "\n").replace("\\t", "\t").replace("\\\\", "\\")


def load_po(path: Path) -> list:
    """Return [(label, msgid, msgstr, fuzzy)] including plural forms."""
    entries, cur, field, fuzzy = [], {}, None, False

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

    for line in path.read_text(encoding="utf-8-sig").splitlines():
        line = line.strip()
        if not line:
            flush()
            field = None
        elif line.startswith("#,") and "fuzzy" in line:
            fuzzy = True
        elif line.startswith("#"):
            continue
        elif line.startswith('"') and field:
            cur[field] += unquote_po(line)
        else:
            m = re.match(r"(msgctxt|msgid_plural|msgid|msgstr(?:\[\d+\])?)\s+(.*)", line)
            if m:
                field = m.group(1)
                cur[field] = unquote_po(m.group(2))
    flush()
    return entries


# --------------------------------------------------------------------------
# Main
# --------------------------------------------------------------------------
def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--source", help="English source file (JSON)")
    ap.add_argument("--target", help="Bengali target file (JSON or .po)")
    ap.add_argument("--target-only", dest="target_only", help="any Bengali text file; Bengali checks only")
    ap.add_argument("--digits", choices=["bn", "latn", "any"], default="any")
    ap.add_argument("--tone", choices=["apni", "tumi"], default="apni")
    ap.add_argument("--glossary", help='JSON file: {"english term": "বাংলা"} (a "terms" object is also accepted)')
    ap.add_argument("--json", action="store_true", help="JSON output")
    ap.add_argument("--strict", action="store_true", help="warnings also fail")
    opts = ap.parse_args()

    glossary = {}
    if opts.glossary:
        g = json.loads(Path(opts.glossary).read_text(encoding="utf-8-sig"))
        g = g.get("terms", g)
        glossary = {k: v for k, v in g.items() if not k.startswith("_") and isinstance(v, (str, list))}

    findings = []

    def adder(where):
        def add(sev, msg):
            findings.append({"severity": sev, "where": where, "message": msg})
        return add

    checked = 0
    if opts.target_only:
        path = Path(opts.target_only)
        for n, line in enumerate(path.read_text(encoding="utf-8-sig").splitlines(), 1):
            check_bengali(line, opts, adder(f"{path.name}:{n}"))
            checked += 1
    elif opts.target and opts.target.endswith((".po", ".pot")):
        for label, src, tgt, fuzzy in load_po(Path(opts.target)):
            add = adder(label)
            if fuzzy:
                add("warning", "entry is still marked fuzzy")
            check_pair(src, tgt, opts, add, glossary)
            checked += 1
    elif opts.source and opts.target:
        try:
            src, tgt = load_json(Path(opts.source)), load_json(Path(opts.target))
        except json.JSONDecodeError as e:
            print(f"error: invalid JSON: {e}", file=sys.stderr)
            return 1
        plural_suffix = re.compile(r"_(zero|one|two|few|many|other)$")
        for key, sval in src.items():
            add = adder(key)
            if key not in tgt:
                # i18next plural keys: bn needs only _one and _other
                if plural_suffix.search(key) and not key.endswith(("_one", "_other")):
                    continue
                add("error", "key missing in target")
                continue
            check_pair(sval, tgt[key], opts, add, glossary)
            checked += 1
        for key in tgt:
            if key not in src and not plural_suffix.search(key):
                adder(key)("warning", "key not present in source")
    else:
        ap.print_usage(sys.stderr)
        print("error: give --source and --target, a .po --target, or --target-only", file=sys.stderr)
        return 2

    errors = sum(f["severity"] == "error" for f in findings)
    warnings = len(findings) - errors
    if opts.json:
        print(json.dumps({"checked": checked, "errors": errors, "warnings": warnings,
                          "findings": findings}, ensure_ascii=False, indent=2))
    else:
        for f in findings:
            mark = "ERROR  " if f["severity"] == "error" else "warning"
            print(f"{mark} {f['where']}: {f['message']}")
        print(f"\n{checked} strings checked: {errors} error(s), {warnings} warning(s).")
        if not findings:
            print("No mechanical problems found. Meaning and tone still need a human-style read.")
    return 1 if errors or (opts.strict and warnings) else 0


if __name__ == "__main__":
    sys.exit(main())
