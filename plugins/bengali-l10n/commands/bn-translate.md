---
description: Translate a website or app into Bengali and wire the bn locale in
argument-hint: "[file, folder or page to translate] [bn-BD|bn-IN] [tumi]"
---

Translate into Bengali using the `translate-to-bengali` skill. Load the skill
first and follow its whole workflow, including the reference files it points
to.

Scope from the user: $ARGUMENTS

If no scope was given, find the project's English locale files or pages
yourself and say what you found before starting. Defaults unless the user
said otherwise: `bn-BD`, আপনি voice, Bengali digits.

Required steps, in this order:

1. Detect the i18n setup and search for hard-coded English that would still
   show on the Bengali site (`references/frameworks.md` §1-2). Report what you
   found and ask before extracting strings into new keys.
2. Fix the terminology in `bn-glossary.json` at the project root (create it
   from `assets/bn-glossary.template.json` if missing).
3. Translate, writing the Bengali beside the English in the project's own
   locale format. Never edit the English source.
4. Wire up `bn` (locale registration, `<html lang>`, switcher label বাংলা,
   Bengali font and CSS) following `references/frameworks.md` §3. Ask before
   adding a dependency.
5. Run `scripts/bn_lint.py` (from the skill folder) on every file you wrote,
   with `--glossary bn-glossary.json`. Fix every error. Do not stop while
   errors remain.
6. Back-translate the high-stakes strings (payments, legal, destructive
   actions) and fix any drift.
7. End with the report described in the skill, including the linter's final
   output line.
