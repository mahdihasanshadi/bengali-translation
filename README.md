# translate-to-bengali

An agent skill that translates and localizes websites and apps from **English
into natural, professional Bengali (বাংলা)**, for Claude Code, Claude Cowork,
claude.ai and other agents that support the `SKILL.md` format.

Plain machine translation of a website into Bengali usually fails in the same
ways. This skill is built to prevent each of them:

| Problem | Example | What the skill does |
|---|---|---|
| Meaning changes | "Home" → বাড়ি, "Save 20%" → ২০% সংরক্ষণ করুন, "Cart" → গাড়ি | Decides the sense from context first; ships a table of 130+ context-dependent words |
| Over-translation | "Password" → গুপ্তসংকেত, "Internet" → অন্তর্জাল | Keeps established English terms, written in Bengali script: পাসওয়ার্ড, লগইন, অর্ডার |
| Wrong spelling of loanwords | ডেলিভারী, পোষ্ট, একাউন্ট | Follows Bangla Academy rules for foreign words: ডেলিভারি, পোস্ট, অ্যাকাউন্ট |
| Stiff or mixed voice | সাধু forms, আপনি mixed with তুমি | One voice (আপনি, চলিত), everyday wording |
| Broken build | `{name}` translated, ICU `plural` keyword translated, tags lost | Protects placeholders, markup, keys; a linter verifies it |
| Wrong formats | "1 million", 11/12/2026, "1200 BDT" | ১০ লাখ, ১২ নভেম্বর ২০২৬, ৳১,২০০ |
| Bad rendering | Letter-spacing splitting conjuncts, clipped glyphs | CSS and font guidance for Bengali script |

## What is inside

```
plugins/bengali-l10n/
└── skills/translate-to-bengali/
    ├── SKILL.md                      workflow and guardrails
    ├── references/
    │   ├── loanwords.md              transliterate vs translate, spelling rules, glossary
    │   ├── meaning-traps.md          context-dependent words, idioms, marketing, stock phrases
    │   ├── style-and-grammar.md      voice, word order, classifiers, plurals, suffixes, spelling
    │   ├── formats-and-locale.md     digits, lakh/crore, currency, dates, time, bn-BD vs bn-IN
    │   ├── technical.md              file formats, HTML, SEO, Intl, fonts, CSS, Unicode
    │   └── sources.md                the standards these rules follow
    ├── scripts/bn_lint.py            QA linter (Python 3.8+, no dependencies)
    ├── assets/bn-glossary.template.json
    └── evals/                        three test cases with graders
examples/                             a sample source file with a good and a bad translation
```

## Install

### Claude Code (plugin marketplace)

```bash
claude plugin marketplace add <your-github-username>/<this-repo>
claude plugin install bengali-l10n@bengali-l10n
```

### Claude Code (copy the skill folder)

```bash
git clone https://github.com/<your-github-username>/<this-repo>.git
# for yourself, in every project:
cp -r <this-repo>/plugins/bengali-l10n/skills/translate-to-bengali ~/.claude/skills/
# or for one project, shared with the team:
cp -r <this-repo>/plugins/bengali-l10n/skills/translate-to-bengali your-project/.claude/skills/
```

### claude.ai and Claude Cowork

Zip the `translate-to-bengali` folder (or download `translate-to-bengali.skill`
from the Releases page if one is published) and upload it under
Settings → Capabilities → Skills.

### Other agents

Any agent that reads `SKILL.md` skills can use the
`plugins/bengali-l10n/skills/translate-to-bengali` folder as is.

## Use

Just ask. The skill triggers on requests like:

- "Add a Bangla version of this site. Strings are in `locales/en.json`."
- "Translate this landing page to Bengali for our Bangladesh launch."
- "Our Bengali translation feels like Google Translate. Review and fix `bn.json`."
- "Localize the checkout flow for West Bengal (bn-IN)."

Defaults: Bangladesh (`bn-BD`), আপনি voice, Bengali digits in prose and prices.
Tell it otherwise if you need `bn-IN`, a তুমি voice, or Latin digits.

## The linter on its own

```bash
SKILL=plugins/bengali-l10n/skills/translate-to-bengali

# compare a source and a target file (JSON), or check a .po file
python $SKILL/scripts/bn_lint.py --source examples/en.json --target examples/bn.bad.json --digits bn
python $SKILL/scripts/bn_lint.py --target locale/bn/LC_MESSAGES/django.po

# Bengali-only checks on any text file (HTML, Markdown, YAML ...)
python $SKILL/scripts/bn_lint.py --target-only public/bn/index.html

# enforce your project glossary, fail CI on warnings too
python $SKILL/scripts/bn_lint.py --source en.json --target bn.json --glossary bn-glossary.json --strict
```

It reports, among other things: missing keys, lost or translated placeholders,
broken ICU plural blocks, changed tags or links, untranslated strings,
wrong-sense words (বাড়ি for "Home"), bookish terms, common misspellings, সাধু
forms, mixed আপনি/তুমি, mixed Bengali/Latin digits, a pipe used as দাঁড়ি,
visarga used as a colon, decomposed vowel signs, and the missing ZWJ in র‍্য.
Exit code 1 on errors makes it usable in CI.

The linter checks mechanics. It cannot tell whether a sentence means the right
thing; legal text and brand slogans should still be read by a native speaker.

## Customizing

- **Glossary**: copy `assets/bn-glossary.template.json` to your project as
  `bn-glossary.json` and edit the terms. The skill follows it and the linter
  enforces it.
- **House style**: edit the defaults table in `SKILL.md` (locale, voice,
  digits) or the "either works" table in `references/loanwords.md`.
- **More checks**: `MISSPELLINGS`, `BOOKISH` and `SENSE_TRAPS` at the top of
  `scripts/bn_lint.py` are plain lists; add your own.

## Testing the skill

`evals/` holds three realistic cases (an e-commerce locale file, a SaaS landing
page, and a review of a bad translation) with graders. With Claude Code 2.1.269
or later, from the skill directory:

```bash
claude plugin eval . --allow-tools Write,Edit,Bash --scaffold
```

This runs each case with and without the skill. These are real model runs and
are billed as such.

## Sources

Bangla Academy প্রমিত বাংলা বানানের নিয়ম, the Mozilla bn-BD and Joomla Bengali
localization style guides, Unicode CLDR (plural rules and number formats) and
the W3C Bengali gap analysis. Links are in `references/sources.md`.

## Contributing

Corrections from native speakers and working translators are very welcome,
especially additions to the glossary, the meaning-traps table and the linter's
word lists. Please include a real example with each suggestion.

## License

MIT
