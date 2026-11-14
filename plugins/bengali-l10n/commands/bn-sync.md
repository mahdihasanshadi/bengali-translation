---
description: Update the Bengali translation after the English strings changed
argument-hint: "[english source file] [bengali file] [git ref of the last translation]"
---

Bring the Bengali translation back in step with the English source, using
the `translate-to-bengali` skill. Load the skill first and read
`references/frameworks.md` §6.

Input from the user: $ARGUMENTS

1. Find the English source and Bengali files if they were not given.
2. Work out what changed:
   - run `scripts/bn_lint.py` (from the skill folder) on the pair: `key missing in target` are
     new strings, `key not present in source` are removed ones;
   - if this is a git repository, diff the English file since the last
     Bengali update (the given ref, or the last commit that touched the
     Bengali file) to find English strings that were edited, whose Bengali is
     now stale.
3. Show the user the list: new, edited and removed keys.
4. Translate only new and edited strings, following `bn-glossary.json` and
   the existing Bengali wording so the voice and terms stay the same. Do not
   reword strings whose English did not change. Remove keys that English
   removed.
5. Re-run the linter until it reports no errors, and finish with the counts
   of added, updated and removed strings and the linter's result line.
6. If the project has no CI check for Bengali yet, offer the workflow from
   `references/frameworks.md` §6 so this drift is caught automatically.
