# translate-to-bengali

[![CI](https://github.com/mahdihasanshadi/bengali-translation/actions/workflows/ci.yml/badge.svg)](https://github.com/mahdihasanshadi/bengali-translation/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

An agent skill that translates and localizes websites and apps from **English
into natural, professional Bengali (বাংলা)**, for Claude Code, Claude Cowork,
claude.ai and other agents that support the `SKILL.md` format. It comes with
a dependency-free linter that catches broken Bengali before your users do.

[বাংলায় পড়ুন ↓](#বাংলায়)

## Why

Machine-translating a website into Bengali usually fails in the same ways.
This skill is built to prevent each of them:

| Problem | Example | What the skill does |
|---|---|---|
| Meaning changes | "Home" → বাড়ি, "Save 20%" → ২০% সংরক্ষণ করুন, "Cart" → গাড়ি | Decides the sense from context first; ships a table of 130+ context-dependent words |
| Over-translation | "Password" → গুপ্তসংকেত, "Internet" → অন্তর্জাল | Keeps established English terms, written in Bengali script: পাসওয়ার্ড, লগইন, অর্ডার |
| Wrong spelling of loanwords | ডেলিভারী, পোষ্ট, একাউন্ট | Follows Bangla Academy rules for foreign words: ডেলিভারি, পোস্ট, অ্যাকাউন্ট |
| Stiff or mixed voice | সাধু forms, আপনি mixed with তুমি | One voice (আপনি, চলিত), everyday wording |
| Broken build | `{name}` → `{নাম}`, ICU `plural` translated, tags lost, unescaped `'` in Android | Protects placeholders, markup and keys; the linter verifies it |
| English still on the page | hard-coded strings, emails, validation messages | Searches for strings that never went through i18n |
| Locale never loads | `bn.json` exists but `bn` isn't registered, `<html lang="en">` | Wires `bn` into 14 frameworks: Next.js, Vue, Angular, Laravel, Django, Rails, Flutter, Android, iOS... |
| Wrong formats | "1 million", 11/12/2026, "1200 BDT" | ১০ লাখ, ১২ নভেম্বর ২০২৬, ৳১,২০০ |
| Bad rendering | letter-spacing splitting conjuncts, clipped glyphs | CSS and font guidance; the linter flags the CSS |
| Translation rot | English changes, Bengali silently goes stale | `/bn-sync` updates only what changed; CI recipe stops it recurring |

## Install

### Claude Code (plugin marketplace)

```bash
claude plugin marketplace add mahdihasanshadi/bengali-translation
claude plugin install bengali-l10n@bengali-l10n
```

This installs the skill and three slash commands.

### Claude Code (copy the skill folder)

```bash
git clone https://github.com/mahdihasanshadi/bengali-translation.git
# for yourself, in every project:
cp -r bengali-translation/plugins/bengali-l10n/skills/translate-to-bengali ~/.claude/skills/
# or for one project, shared with your team through git:
cp -r bengali-translation/plugins/bengali-l10n/skills/translate-to-bengali your-project/.claude/skills/
```

### claude.ai and Claude Cowork

Download `translate-to-bengali.skill` from the
[latest release](https://github.com/mahdihasanshadi/bengali-translation/releases/latest)
and upload it under Settings → Capabilities → Skills.

### Other agents

Any agent that reads `SKILL.md` skills can use
`plugins/bengali-l10n/skills/translate-to-bengali` as is.

## Use

Just ask. The skill triggers on requests like:

- "Add a Bangla version of this site. Strings are in `locales/en.json`."
- "Translate this landing page to Bengali for our Bangladesh launch."
- "Our Bengali translation feels like Google Translate. Review and fix `bn.json`."
- "We added a checkout flow; update the Bengali strings."
- "Localize the app for West Bengal (bn-IN)."

Or use the commands (plugin install):

| Command | What it does |
|---|---|
| `/bn-translate [scope]` | Full job: find hard-coded strings, fix the glossary, translate, wire up `bn`, lint until clean, report |
| `/bn-review [bn file] [en file]` | Lint plus a line-by-line review for meaning and tone, then fixes |
| `/bn-sync [en file] [bn file] [git ref]` | Translate only new and changed strings after the English moved on |

Defaults: Bangladesh (`bn-BD`), আপনি voice, Bengali digits in prose and
prices. Say so if you need `bn-IN`, a তুমি voice or Latin digits.

## The linter

`bn_lint.py` runs on Python 3.8+ with no dependencies (PyYAML only for YAML).
Use it alone, in CI or in a pre-commit hook.

```bash
L=plugins/bengali-l10n/skills/translate-to-bengali/scripts/bn_lint.py

# source and target: JSON, .arb, .yml, Android strings.xml, iOS .strings, HTML
python $L --source examples/en.json --target examples/bn.bad.json --digits bn
python $L --source examples/html/index.en.html --target examples/html/index.bn.html

# formats that hold both languages: .po, XLIFF, Xcode .xcstrings
python $L --target locale/bn/LC_MESSAGES/django.po
python $L --target Localizable.xcstrings

# Bengali-only checks on any text file (Markdown, MDX, PHP, templates)
python $L --target-only content/bn/about.md

# repair the mechanical problems in place, then lint
python $L --source en.json --target bn.json --fix --digits bn

# enforce your glossary, fail CI on warnings too, machine-readable output
python $L --source en.json --target bn.json --glossary bn-glossary.json --strict --json
```

Running it on `examples/bn.bad.json`:

```
warning nav.home: possible wrong sense: 'বাড়ি' for /\bhome\b/; navigation 'Home' is হোম
warning auth.forgot: bookish or wrong-sense term 'গুপ্তসংকেত'; consider 'পাসওয়ার্ড'
ERROR   auth.welcome: placeholder mismatch: missing {name}; unexpected {নাম} (a placeholder name was translated; ...)
ERROR   cart.empty: pipe '|' used as a full stop; use দাঁড়ি '।' (U+0964)
ERROR   cart.items: ICU 'plural' block for 'count' is missing, or its keyword or argument name was translated
ERROR   cart.freeShipping: Bengali and Latin digits mixed inside one number
ERROR   errors.generic: আপনি and তুমি forms mixed in one string ('আপনার', 'করো')
ERROR   errors.email: key missing in target
ERROR   footer.terms: href/src attribute changed
...
12 strings checked: 8 error(s), 15 warning(s).
```

**What it checks**

- *Structure:* missing and extra keys, empty strings, placeholders in every
  common syntax (`{x}`, `{{x}}`, `%s`, `%1$d`, `%lld`, `%{x}`, `:x`, `${x}`,
  `<0>`, `$t()`, `@:key`), ICU `plural`/`select` blocks (translated keywords,
  arguments or branch keys, missing `other`), tags, links, URLs, emails,
  whitespace, fuzzy `.po` entries, Android apostrophes, iOS `.strings` syntax,
  XLIFF/String Catalog targets and states, `@@locale`, YAML root key.
- *HTML pages:* `<html lang>`, the full tag and attribute structure against the
  English page, translated `alt`/`title`/`placeholder`/meta text, and CSS that
  breaks Bengali (`letter-spacing`, tight `line-height`).
- *Bengali:* wrong-sense words, bookish coinages, 60+ common misspellings,
  সাধু forms, mixed আপনি/তুমি (verb endings, not just pronouns), digit
  policy and mixed digits, দাঁড়ি and spacing, decomposed vowel signs, missing
  ZWJ in র‍্য, ত্ for ৎ, Devanagari/Assamese look-alikes, legacy Bijoy text,
  broken encodings, untranslated strings, changed numbers, glossary terms.

**`--fix`** repairs only what is safe to repair mechanically: decomposed vowel
signs, a pipe at the end of a sentence, spacing around দাঁড়ি and টি, known
misspellings, mixed digits, and digits per `--digits`. It never touches
placeholders, tags, URLs, code spans or keys, and it is idempotent. Commit
first and review the diff.

Exit codes: `0` clean, `1` errors (or warnings with `--strict`), `2` usage
error. The linter checks mechanics. It cannot tell whether a sentence means
the right thing; legal text and brand slogans still need a native speaker.

### In CI

```yaml
# .github/workflows/bengali.yml
name: Bengali translation
on: [pull_request]
jobs:
  bn-lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: python .claude/skills/translate-to-bengali/scripts/bn_lint.py --source locales/en.json --target locales/bn.json
```

## What is inside

```
plugins/bengali-l10n/
├── commands/                         /bn-translate, /bn-review, /bn-sync
└── skills/translate-to-bengali/
    ├── SKILL.md                      workflow and guardrails
    ├── references/
    │   ├── loanwords.md              transliterate vs translate, spelling rules, glossary
    │   ├── meaning-traps.md          context-dependent words, idioms, marketing, stock phrases
    │   ├── style-and-grammar.md      voice, word order, classifiers, plurals, suffixes, spelling
    │   ├── formats-and-locale.md     digits, lakh/crore, currency, dates, time, bn-BD vs bn-IN
    │   ├── technical.md              file formats, HTML, SEO, Intl, fonts, CSS, Unicode
    │   ├── frameworks.md             wiring bn into 14 frameworks, hard-coded strings, sync, CI
    │   └── sources.md                the standards these rules follow
    ├── scripts/bn_lint.py            QA linter and safe fixer
    ├── assets/bn-glossary.template.json
    └── evals/                        three test cases with graders
examples/                             JSON and HTML samples: source, good and bad translations
tests/                                linter test suite and fixtures for every format
```

## Customizing

- **Glossary:** copy `assets/bn-glossary.template.json` to your project as
  `bn-glossary.json` and edit it. The skill follows it and the linter
  enforces it with `--glossary`.
- **House style:** edit the defaults table in `SKILL.md` (locale, voice,
  digits) or the "either works" table in `references/loanwords.md`.
- **More checks:** `MISSPELLINGS`, `BOOKISH` and `SENSE_TRAPS` at the top of
  `scripts/bn_lint.py` are plain lists; add your own (and a test).

## Development

```bash
python -m unittest discover -s tests -v      # linter tests (pip install pyyaml for the YAML test)
```

`evals/` holds three realistic cases (an e-commerce locale file, a SaaS landing
page, and a review of a bad translation) with graders. With Claude Code
2.1.269 or later, from the skill directory:

```bash
claude plugin eval . --allow-tools Write,Edit,Bash --scaffold
```

This runs each case with and without the skill. These are real model runs and
are billed as such.

Releases: bump the version in `plugin.json`, `marketplace.json` and
`bn_lint.py`, add a `CHANGELOG.md` entry, and push a `vX.Y.Z` tag. The release
workflow runs the tests and attaches `translate-to-bengali.skill`.

## Contributing

Corrections from native speakers and working translators are very welcome,
especially additions to the glossary, the meaning-traps table and the linter's
word lists. See [CONTRIBUTING.md](CONTRIBUTING.md); please include a real
example with each suggestion.

## Sources

Bangla Academy প্রমিত বাংলা বানানের নিয়ম, the Mozilla bn-BD and Joomla Bengali
localization style guides, Unicode CLDR (plural rules and number formats) and
the W3C Bengali gap analysis. Links are in `references/sources.md`.

## বাংলায়

**translate-to-bengali** একটি এজেন্ট স্কিল। এটি ইংরেজি ওয়েবসাইট ও অ্যাপকে
স্বাভাবিক, পেশাদার বাংলায় অনুবাদ করে, যেন শুরু থেকেই বাংলায় লেখা। Claude Code,
Claude Cowork, claude.ai এবং `SKILL.md` সমর্থন করে এমন যেকোনো এজেন্টে এটি কাজ করে।

সাধারণ মেশিন অনুবাদে যা ভুল হয়, এই স্কিল সেগুলো ঠেকায়:

- **অর্থ বদলে যাওয়া:** নেভিগেশনের "Home" হবে হোম, বাড়ি নয়; "Save 20%" মানে ২০% ছাড়।
- **অতিরিক্ত অনুবাদ:** পাসওয়ার্ড, লগইন, অর্ডারের মতো চেনা শব্দ বাংলা হরফে রাখা হয়,
  গুপ্তসংকেতের মতো কৃত্রিম শব্দ নয়।
- **বানান:** বাংলা একাডেমির বিদেশি শব্দের নিয়ম মেনে ডেলিভারি, পোস্ট, অ্যাকাউন্ট।
- **এক সুর:** পুরো সাইটে আপনি-সম্বোধন আর চলিত ভাষা।
- **কোড অক্ষত থাকে:** `{name}`, ICU plural, HTML ট্যাগ, লিংক বদলায় না।
- **অ্যাপে চালু করা:** Next.js, Vue, Laravel, Django, Flutter, Android, iOS সহ ১৪টি
  ফ্রেমওয়ার্কে `bn` লোকেল যুক্ত করার নির্দেশনা, আর কোডে লুকিয়ে থাকা ইংরেজি খুঁজে বের করা।
- **লিন্টার:** `bn_lint.py` বানান, দাঁড়ি, মিশ্র অঙ্ক, আপনি/তুমি মিশে যাওয়া, ভাঙা
  প্লেসহোল্ডার আর ফন্ট-বিরোধী CSS ধরে; `--fix` দিলে নিরাপদ ভুলগুলো নিজেই ঠিক করে।

ইনস্টল করতে:

```bash
claude plugin marketplace add mahdihasanshadi/bengali-translation
claude plugin install bengali-l10n@bengali-l10n
```

তারপর শুধু বলুন: "এই সাইটের একটি বাংলা সংস্করণ বানাও", অথবা `/bn-translate`
চালান। আইনি লেখা ও ব্র্যান্ড স্লোগান প্রকাশের আগে একজন বাংলাভাষী দিয়ে পড়িয়ে নিন।
ভুল চোখে পড়লে বা নতুন শব্দ যোগ করতে চাইলে issue খুলুন; উদাহরণসহ পরামর্শ সবচেয়ে কাজে লাগে।

## License

MIT
