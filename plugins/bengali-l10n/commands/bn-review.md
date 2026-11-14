---
description: Review and fix an existing Bengali translation
argument-hint: "[bengali file] [english source file]"
---

Review an existing Bengali translation using the `translate-to-bengali`
skill. Load the skill first.

Files from the user: $ARGUMENTS

If no files were given, find the Bengali locale files and their English
sources in the project.

1. Run `scripts/bn_lint.py` (from the skill folder) on each Bengali file,
   paired with its English source where the format allows, and with
   `--glossary bn-glossary.json` if the project has one. Show the summary.
2. Read every string against its English source and look for what the linter
   cannot see: wrong sense for the context, meaning added or lost, unnatural
   or textbook wording, inconsistent terms, wrong tone, literal idioms.
   Use `references/meaning-traps.md` and `references/style-and-grammar.md`.
3. Present the problems grouped by severity: build-breaking first
   (placeholders, ICU, markup, missing keys), then wrong meaning, then
   terminology and tone, then spelling and punctuation. Quote the string,
   the problem and the fix.
4. Unless the user asked for a review only, apply the fixes: run the linter
   with `--fix` for the mechanical ones, edit the rest by hand, keep keys and
   structure unchanged, and record new terminology in `bn-glossary.json`.
5. Re-run the linter and finish with its result line and a short list of
   anything that needs a native speaker's sign-off (legal text, slogans).
