# Changelog

All notable changes to this project are listed here. The format follows
[Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and the project uses
[Semantic Versioning](https://semver.org/).

## [Unreleased]

### Added

- Over-translation check: in pair mode the linter warns when an everyday
  English term is replaced by a Bengali coinage people don't use in apps
  (Map → মানচিত্র instead of ম্যাপ, Payment → অর্থপ্রদান, Install → স্থাপন,
  Offer → প্রস্তাব, about 55 terms). A project glossary can choose the Bengali
  word instead.
- More bookish coinages flagged in every mode (নীলদন্ত, কুঞ্জিপট, পর্দাচিত্র...).
- Glossary: devices, maps and connectivity terms (ম্যাপ, ব্লুটুথ, নেটওয়ার্ক,
  স্টোরেজ...), app actions (ইনস্টল, রিসেট, সিঙ্ক...), and more "either works"
  pairs (লোকেশন/অবস্থান, নোটিফিকেশন/বিজ্ঞপ্তি...).

## [1.1.0] - 2026-11-14

### Added

- Linter pair mode for Flutter `.arb`, YAML (Rails/Hugo/Jekyll; needs PyYAML),
  Android `strings.xml`, iOS `.strings` (UTF-8 and UTF-16) and HTML pages.
- Linter single-file mode for XLIFF 1.2/2.0 and Xcode String Catalogs
  (`.xcstrings`), alongside gettext `.po`.
- HTML pair mode: checks `<html lang>`, compares the full tag and attribute
  structure with the English page, pairs visible text and translatable
  attributes, and flags CSS that breaks Bengali (`letter-spacing`, tight
  `line-height`).
- `--fix`: safe, idempotent mechanical repairs (vowel-sign composition, pipe
  used as দাঁড়ি, spacing, known misspellings, digits) that never touch
  placeholders, tags, URLs or code.
- ICU parsing: translated `select` or plural branch keys, translated argument
  names and missing `other` branches are reported; branch bodies are no
  longer mistaken for placeholders.
- Checks for Android unescaped apostrophes, `@@locale`, a YAML root key left
  as `en:`, XLIFF target language, String Catalog states, non-UTF-8 files and
  legacy Bijoy text.
- `references/frameworks.md`: detecting the i18n setup, finding hard-coded
  strings, wiring `bn` into Next.js, i18next, Vue/Nuxt, Angular, react-intl,
  Laravel, Django, Rails, WordPress, Flutter, Android, iOS, Shopify and static
  sites, batching large projects, keeping Bengali in sync, and CI.
- Slash commands `/bn-translate`, `/bn-review` and `/bn-sync`.
- Test suite (`tests/`) with fixtures for every format, CI on Linux, Windows
  and macOS for Python 3.8 to 3.13, and a release workflow that publishes
  `translate-to-bengali.skill`.
- A translated HTML landing page in `examples/html/`.

### Fixed

- The linter crashed with `UnicodeEncodeError` on Windows consoles as soon as
  it printed Bengali text.
- A translated placeholder name such as `{নাম}` was reported only as missing
  `{name}`, not as the cause.
- Most তুমি verb forms (গেছো, পারো, আছো ...) were not detected; voice detection
  now uses verb endings as well as pronouns, without flagging নতুন or কেন.
- `%lld`, `%ld` and `%{name}` placeholders were not recognised.
- vue-i18n plural syntax (`one | other`) was reported as a misused দাঁড়ি.
- "Save 10 hours" (time) was flagged as a discount sense error.

## [1.0.0]

- First version: translation skill with references, glossary template,
  JSON/.po linter and three evals.
