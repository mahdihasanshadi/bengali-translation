---
name: translate-to-bengali
description: Translate and localize websites, web apps and UI copy from English into natural, professional Bengali (Bangla, bn-BD / bn-IN). Use this skill whenever the user asks to translate, localize or add Bengali/Bangla to a website, landing page, app, i18n locale file (JSON, YAML, .po, .arb, .strings, .xcstrings, XLIFF, strings.xml), HTML, Markdown/MDX, email template or marketing copy, and also when asked to review, fix or QA an existing Bengali translation, to "add a Bangla version", "make the site bilingual", wire a bn locale into an app, or update Bengali strings after the English changed. It handles the hard parts that plain translation gets wrong - words whose meaning shifts in context, English terms Bengali speakers already use (written in Bengali script, e.g. লগইন, পাসওয়ার্ড), tone, spelling, numerals, dates, currency, placeholders, markup, fonts and Unicode - and ships a linter to verify the result.
---

# Translate a website into Bengali

The goal is a Bengali site that reads as if it had been written in Bengali by a
careful native copywriter: every sentence means what the English meant, familiar
English tech words stay familiar, nothing technical is broken, and the client can
ship it without embarrassment.

Bad Bengali localization almost always fails in one of five ways. Keep them in
mind, because every rule below exists to prevent one of them:

1. **Meaning drift** - a word is translated by its dictionary sense instead of
   its sense on this screen ("Home" → বাড়ি, "Save" → বাঁচান, "Cart" → গাড়ি).
2. **Over-translation** - a word everyone says in English is replaced by a
   bookish coinage nobody uses (পাসওয়ার্ড → গুপ্তসংকেত, ইন্টারনেট → অন্তর্জাল).
3. **Under-translation** - English left in Latin letters, or Banglish word order,
   so the page feels half-finished.
4. **Wrong voice** - stiff, literary (সাধু) or textbook phrasing, mixed
   আপনি/তুমি, or English sentence structure with Bengali words.
5. **Breakage** - placeholders, tags, keys, plurals, digits or Unicode damaged,
   or text that renders badly because the CSS was written for Latin script.

## Workflow

Work through these steps in order. For a single string or a short snippet, the
same thinking applies, just compressed.

### 1. Establish the brief

Find these out from the project before asking. Ask the user only for what is
still unclear, and otherwise state the default you used.

| Decision | Default | Notes |
|---|---|---|
| Locale | `bn-BD` (Bangladesh) | Use `bn-IN` if the audience is West Bengal/India. Differences: `references/formats-and-locale.md` |
| Voice | আপনি, warm and plain (চলিত) | তুমি only if the brand explicitly wants a youthful, intimate voice; then use it everywhere |
| Digits | Bengali digits (০-৯) in prose, prices, counts and dates | Latin digits stay in codes, IDs, URLs, emails, version numbers, form input examples |
| Acronyms | Stay in Latin (OTP, PDF, API, SMS, URL) | A few that are pronounced as words go into Bengali (সিম, পিন, এটিএম) |
| Existing terms | Follow them | If the site already has Bengali strings or a glossary, match their choices unless they are plainly wrong, and say what you changed |

Also identify the i18n setup: the framework, where the English strings live,
and where the Bengali file must go (`references/frameworks.md` §1 has a
lookup table). If the project has no i18n, or English is hard-coded in
components, templates, emails or validation messages, that English will
still show on the Bengali site however good the translation is. Search for
it (`references/frameworks.md` §2) and tell the user what you found before
translating; extract it into the locale files when they agree.

If a Bengali translation already exists and the English has changed since,
this is an **update**, not a new translation: translate only new and changed
strings, delete removed ones, and leave the rest as they are
(`references/frameworks.md` §6).

### 2. Read before translating

Read all the source strings and where they are used. A key name such as
`nav.home`, `cart.empty` or `btn.save` is context: it tells you which sense of
the word is meant. For HTML, look at the element (a button, a heading, an alt
text). Never translate a string in isolation when its surroundings are available.

Note anything ambiguous (a bare "Post", "Open", "Order", "Back", "Charge") and
resolve it from the code or the page; if it cannot be resolved, pick the most
likely sense and list it in the final report.

### 3. Fix the terminology first

Before writing sentences, list the recurring terms (navigation, actions, domain
nouns) and decide each one once. Save the decisions to `bn-glossary.json` in the
project (template: `assets/bn-glossary.template.json`) so later sessions and
other translators stay consistent. One English term gets one Bengali rendering
across the whole site; inconsistency is the most visible flaw to a client.

Sort every term into one of three buckets:

- **Keep as is (Latin)** - brand and product names, company names, code, URLs,
  emails, file extensions, most acronyms, technical units (GB, px, Mbps).
  `Google`, `iPhone`, `bKash`, `WhatsApp` are never translated or respelled.
- **Transliterate (English word, Bengali script)** - words Bengali speakers
  already use in everyday speech about technology and commerce: লগইন,
  পাসওয়ার্ড, অ্যাকাউন্ট, ইমেইল, প্রোফাইল, অর্ডার, ডেলিভারি, পেমেন্ট, কার্ট,
  ডাউনলোড, নোটিফিকেশন.
- **Translate** - everything where a natural Bengali word is what people
  actually say: খুঁজুন, বাতিল, পাঠান, নাম, ঠিকানা, দাম, মোট, সাহায্য, যোগাযোগ.

**The test for transliterate vs translate:** imagine a shop assistant in Dhaka
explaining this screen to a customer out loud. Use the word they would say. If
the "pure" Bengali word would make them pause or sound like a textbook,
transliterate. If the English word would sound like showing off, translate.

Transliteration has standard spellings; do not invent them. Read
`references/loanwords.md` for the spelling rules (Bangla Academy rules for
foreign words) and a ready glossary of ~250 web terms. Read
`references/meaning-traps.md` for words whose meaning changes with context and
for idioms and marketing phrases.

### 4. Translate for meaning, then for voice

For each string: understand what it is telling or asking the user, then write
that in Bengali as you would say it. Do not map word to word.

- Restructure to Bengali word order (verb last).
  "Click here to download" → "ডাউনলোড করতে এখানে ক্লিক করুন".
- Buttons and commands use the polite imperative: করুন, দেখুন, লিখুন, দিন, পাঠান.
- Drop what Bengali does not need: articles ("Create an account" →
  "অ্যাকাউন্ট তৈরি করুন", not "একটি অ্যাকাউন্ট…"), repeated "your", and "please"
  on every line (করুন is already polite).
- Prefer active, short sentences. Avoid দ্বারা-passives and stacked Sanskritic
  nouns (পাঠান, not প্রেরণ করুন; কিনুন, not ক্রয় করুন).
- Marketing copy and idioms are rewritten for effect, not translated
  ("Hang tight!" → "একটু অপেক্ষা করুন").
- Do not add, drop or soften information. Numbers, prices, dates, names, limits
  and conditions carry over exactly.

Grammar, spelling, classifiers, case endings on placeholders, plural handling
and worked before/after examples are in `references/style-and-grammar.md`. Read
it before translating any substantial amount of text.

### 5. Protect everything technical

Translate text; leave machinery alone. Specifically never alter: keys,
placeholders and variables (`{name}`, `{{count}}`, `%s`, `%1$d`, `${x}`,
`:name`, `<0>…</0>`), ICU keywords (`plural`, `select`, `one`, `other`, `=0`),
HTML/JSX tags and attributes such as `class`, `id`, `href`, `name`, `data-*`,
escape sequences and entities (`\n`, `&nbsp;`, `&amp;`), code, and file
structure. Placeholders may move to fit Bengali word order but must all survive.

Do translate human-visible attribute text: `alt`, `title`, `placeholder`,
`aria-label`, `<meta name="description">`, Open Graph/Twitter titles and
descriptions, and `<title>`.

Write the Bengali into the project's own locale mechanism (a new `bn` file next
to `en`, a `values-bn/` folder, etc.) and leave the English source untouched.
Per-format rules (JSON, YAML, .po, ARB, Android, iOS, XLIFF, Markdown/MDX, HTML),
numbers and dates through `Intl`, SEO, and the CSS/font changes Bengali needs
are in `references/technical.md`. Formats for numbers, money, dates, time,
phone numbers and bn-BD vs bn-IN wording are in `references/formats-and-locale.md`.

Then make sure the app actually serves it: register `bn` where the framework
lists its locales, switch `<html lang>`, label the language switcher বাংলা,
and load a Bengali font with the CSS fixes. Per-framework recipes (Next.js,
i18next, Vue/Nuxt, Angular, Laravel, Django, Rails, WordPress, Flutter,
Android, iOS, Shopify, static HTML) are in `references/frameworks.md` §3. If
you are only asked for the file, list the wiring steps in the report instead
of editing config.

For more than a few hundred strings, work in batches: glossary first, then
one namespace or file at a time, linting each batch before the next
(`references/frameworks.md` §5).

### 6. Verify

Run the bundled linter on what you produced, and fix every error and review
every warning. `scripts/` is inside this skill's folder; use its full path
when the working directory is the user's project.

```bash
# source/target pair: keys, placeholders, ICU plurals, tags, links, plus all Bengali checks
#   JSON, .arb, .yml/.yaml (needs PyYAML), Android strings.xml, iOS .strings, HTML pages
python scripts/bn_lint.py --source locales/en.json --target locales/bn.json
python scripts/bn_lint.py --source index.html --target bn/index.html

# formats that hold both languages: .po/.pot, XLIFF, Xcode .xcstrings
python scripts/bn_lint.py --target locale/bn/LC_MESSAGES/django.po

# any other Bengali file (Markdown, MDX, PHP arrays, templates): Bengali checks only
python scripts/bn_lint.py --target-only content/bn/about.md

# options: --digits bn|latn|any   --tone apni|tumi   --glossary bn-glossary.json
#          --fix (safe mechanical repairs in place)   --strict   --json
```

`--fix` repairs only mechanical issues: decomposed vowel signs, a pipe used
as দাঁড়ি, spacing around punctuation and টি, known misspellings, and digits per
`--digits`. It never touches placeholders, tags, URLs or code. Run it, then
read its list of changes; everything else is yours to fix by hand.

In HTML pair mode the linter also flags a wrong `<html lang>`, changed links
or attributes, and CSS that breaks Bengali (`letter-spacing`, tight
`line-height`).

The linter catches mechanical problems. It cannot judge meaning, so also do a
**back-translation pass** on high-stakes strings - payments, pricing, legal
text, consent, destructive actions ("Delete account"), errors and medical or
safety content: read your Bengali cold, translate it back to English in your
head, and compare with the source. If the two differ in any fact or obligation,
fix the Bengali.

Finally read the page top to bottom as a user would. Check that the same thing
has the same name everywhere and that the voice does not wobble. If you can
run the app or open the page in a browser, look at the Bengali version at
mobile and desktop widths: clipped glyphs, wrapped buttons and leftover
English are easier to see than to predict.

### 7. Report

End with a short report so the client can trust and maintain the work:

- what was translated and where the files are, and the linter result;
- what you wired up (locale registration, `lang`, switcher, font), or the
  steps still needed if you did not;
- hard-coded English you found, and whether it was extracted;
- the glossary decisions that matter (and any existing terms you changed);
- strings you could not resolve from context, with the sense you assumed;
- anything deliberately left in English and why;
- items for human sign-off: legal/compliance text, brand taglines, and any
  layout risks (long labels, fonts, CSS noted in `references/technical.md`).

Be honest in this report: recommend a native-speaker review for legal text and
brand slogans rather than presenting them as final.

## Guardrails

These hold in every task, including quick ones.

- **Meaning is fixed.** Never change a number, price, date, name, quantity,
  condition or legal obligation. Never invent content that the source lacks.
- **Brands and people are not translated.** Product, company and personal names
  stay as the owner writes them. Transliterate a personal name only when the
  site already does so.
- **One voice.** Do not mix আপনি with তুমি/তুই forms, or চলিত with সাধু forms.
- **One term, one rendering.** Follow the glossary; extend it rather than
  improvising a synonym.
- **Standard spelling.** Follow Bangla Academy প্রমিত বানান and the loanword
  rules; no ী/ূ/ণ/ষ in English loanwords, অ্যা for the "a" in "app".
- **Real Unicode Bengali only.** No legacy-font (Bijoy/ASCII) text, no pipe `|`
  as a full stop (use দাঁড়ি `।` U+0964), no visarga `ঃ` as a colon.
- **Culturally safe.** Keep wording neutral with respect to religion, gender,
  region and politics unless the client's own copy takes a position. Replace
  idioms, jokes and imagery that do not land (alcohol, dating or pork
  references, baseball metaphors) with a neutral equivalent that keeps the
  point, and mention that you did.
- **Never break the build.** Output must stay valid in its file format, with
  the same keys and placeholders as the source. Do not report the work as
  finished while the linter still shows errors.
- **Flag, do not guess, when stakes are high.** For legal, financial, medical
  or safety wording where you are unsure, translate carefully and flag it.
- **Do not transliterate everything.** A page of English written in Bengali
  letters is as bad as stiff textbook Bengali. Sentences are Bengali; only
  established terms are borrowed.

## Quick reference

A few anchors; the full tables are in the reference files.

| English | Use | Not |
|---|---|---|
| Home (nav) | হোম | বাড়ি, ঘর |
| Log in / Sign in | লগইন করুন | স্বাক্ষর করুন, প্রবেশ করুন |
| Sign up | সাইন আপ করুন / অ্যাকাউন্ট খুলুন | উপরে স্বাক্ষর করুন |
| Password | পাসওয়ার্ড | গুপ্তসংকেত |
| Save (data) | সেভ করুন / সংরক্ষণ করুন | বাঁচান, রক্ষা করুন |
| Save 20% | ২০% ছাড় | ২০% সংরক্ষণ করুন |
| Add to cart | কার্টে যোগ করুন | গাড়িতে যোগ করুন |
| Checkout | চেকআউট | পরীক্ষা করে দেখুন |
| Free delivery | ফ্রি ডেলিভারি | মুক্ত বিতরণ |
| Share | শেয়ার করুন | ভাগ করুন |
| Enter your email | আপনার ইমেইল লিখুন | আপনার ইমেইল প্রবেশ করান |
| Invalid email | সঠিক ইমেইল ঠিকানা লিখুন | অবৈধ ইমেইল |
| Learn more | আরও জানুন | আরও শিখুন |
| Something went wrong | কোনো সমস্যা হয়েছে। আবার চেষ্টা করুন। | কিছু ভুল হয়ে গেছে |
| 3 items | ৩টি আইটেম | ৩ আইটেমগুলো |
| {name}'s profile | {name}-এর প্রোফাইল | {name}র প্রোফাইল |
| $1 million | ১০ লাখ ডলার | ১ মিলিয়ন ডলার (avoid in consumer copy) |

## Reference files

- `references/loanwords.md` - transliteration spelling rules and the glossary
  of established web/app/e-commerce terms. Read when deciding or spelling terms.
- `references/meaning-traps.md` - context-dependent words, idioms, marketing
  phrases, error-message patterns. Read when a word has more than one sense.
- `references/style-and-grammar.md` - voice, word order, classifiers, plurals,
  suffixes on placeholders, punctuation, common misspellings, before/after
  examples. Read before translating any sizeable text.
- `references/formats-and-locale.md` - digits, lakh/crore, currency, dates,
  time, phone, addresses, units, and bn-BD vs bn-IN differences.
- `references/technical.md` - file formats, what to translate in HTML, SEO,
  `Intl`, fonts, CSS for Bengali script, Unicode hygiene.
- `references/frameworks.md` - detecting the i18n setup, finding hard-coded
  strings, registering `bn` per framework, batching, keeping Bengali in sync,
  CI. Read at step 1 and when wiring the locale in.
- `references/sources.md` - the standards and style guides these rules follow.
- `scripts/bn_lint.py` - the QA linter and safe fixer (Python 3.8+, no
  dependencies; PyYAML only for YAML files).
- `assets/bn-glossary.template.json` - starting glossary to copy into a project.
