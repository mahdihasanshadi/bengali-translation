# Contributing

Thank you for helping make Bengali on the web read better. Two kinds of
contribution are especially valuable.

## Language corrections (no coding needed)

If you are a native speaker or a working translator and something in the
skill is wrong, unnatural or outdated, open an issue with the
**Language correction** template. A good suggestion has:

- the English source string and where it appears (button, error message,
  marketing headline...);
- the Bengali the skill or linter produces or recommends now;
- what it should be, and why (meaning, register, spelling rule, regional
  usage);
- for spelling, the rule or dictionary you follow (Bangla Academy
  প্রমিত বানান, the Bangla Academy dictionary, an established product's usage).

Bangladesh (`bn-BD`) is the default. Differences for West Bengal (`bn-IN`)
are welcome; please say which region a suggestion is for.

## Code and reference changes

1. Fork, create a branch, make the change.
2. For a new linter check or word-list entry, add a test in
   `tests/test_bn_lint.py` showing one string it flags and one similar string
   it must not flag. False positives cost users more than missed warnings.
3. Run the tests:

   ```bash
   python -m pip install pyyaml
   python -m unittest discover -s tests -v
   ```

4. Keep `bn_lint.py` a single file with no dependencies beyond the standard
   library (PyYAML stays optional), and compatible with Python 3.8.
5. Note the change under "Unreleased" in `CHANGELOG.md`.

### Where things live

| Change | File |
|---|---|
| Workflow, defaults, guardrails | `plugins/bengali-l10n/skills/translate-to-bengali/SKILL.md` |
| Loanword spellings, glossary | `references/loanwords.md`, `assets/bn-glossary.template.json` |
| Words whose meaning shifts | `references/meaning-traps.md` and `SENSE_TRAPS` in `bn_lint.py` |
| Misspellings the linter catches | `MISSPELLINGS` in `bn_lint.py` |
| Framework wiring | `references/frameworks.md` |
| Slash commands | `plugins/bengali-l10n/commands/` |

`SKILL.md` is loaded into the model's context on every use, so keep it
focused; detail belongs in the reference files.

## Evals

`evals/` holds model-graded test cases for the skill. If you change the
workflow, run them with `claude plugin eval . --allow-tools Write,Edit,Bash --scaffold`
from the skill directory and mention the before/after results in your pull
request. These are paid model runs.
