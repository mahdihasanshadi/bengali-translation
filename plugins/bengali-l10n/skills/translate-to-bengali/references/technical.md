# Technical handling: files, markup, SEO, fonts, CSS, Unicode

## Contents

1. What to translate and what to leave
2. File formats
3. HTML and static sites
4. Numbers and dates in code
5. SEO
6. Fonts and CSS for Bengali script
7. Unicode hygiene
8. Layout checks before shipping

## 1. What to translate and what to leave

Leave exactly as in the source:

- Keys, IDs, enum values, route names, CSS classes, anything a program reads.
- Placeholders in every syntax: `{name}`, `{{name}}`, `{0}`, `%s`, `%d`,
  `%1$s`, `%(name)s`, `${name}`, `:name`, `@:key`, `$t(key)`, `<0>…</0>`,
  `<strong>…</strong>` wrappers used by i18n libraries.
- ICU syntax words: `plural`, `select`, `selectordinal`, `one`, `two`, `few`,
  `many`, `other`, `zero`, `=0`, `offset`, `#`.
- Escapes and entities: `\n`, `\t`, `\"`, ` `, `&nbsp;`, `&amp;`, `&lt;`.
- URLs, email addresses, file paths, code samples, command names.
- Brand, product and company names; people's names.
- Leading/trailing whitespace and the trailing newline of a value (code often
  depends on them).

Translate:

- All visible text, including text inside tags and between placeholders.
- `alt`, `title`, `placeholder`, `aria-label`, `aria-description`, the `value`
  of submit/reset buttons, `<option>` labels, `<title>`, meta description, Open
  Graph and Twitter card titles/descriptions, human-readable JSON-LD fields
  (`name`, `description`) that describe the page.
- Email subjects and bodies, PDF/print templates, error and validation messages
  (including ones in backend code or validation libraries, which are easy to
  miss).

Do not translate unless asked: code comments, log messages, analytics event
names, admin-only tooling.

## 2. File formats

General: keep the same keys, order, nesting, indentation style and encoding
(UTF-8 without BOM). Create the Bengali file beside the source using the
project's naming (`bn.json`, `bn-BD.json`, `messages_bn.properties`,
`values-bn/strings.xml`, `bn.lproj/Localizable.strings`, `app_bn.arb`).
Register the new locale where the framework lists locales (i18n config, router,
language switcher) and name it বাংলা in the switcher.

| Format | Watch for |
|---|---|
| JSON (i18next, vue-i18n, next-intl, react-intl) | Valid JSON; escape `"` and `\`. i18next plural keys (`key_one`, `key_other`) must all be present; Bengali needs `_one` and `_other`. Nested `$t()` and `<1>` tags stay. |
| YAML (Rails, Hugo, Jekyll) | Quote values containing `:`, `#`, `{`, `%`, leading `*`/`!`, or starting with a quote. Change the top-level locale key (`en:` → `bn:`). Keep block-scalar styles (the pipe and `>` indicators). |
| gettext .po | Never touch `msgid`. Fill `msgstr`. Keep `%s`/`%1$s` and `\n` (a `msgstr` must end in `\n` if the `msgid` does). Provide every `msgstr[n]` the header's `nplurals` requires. Remove the `fuzzy` flag only for entries you actually reviewed. |
| Java .properties | Modern toolchains read UTF-8; legacy ones need `\uXXXX` escapes. Match what the project's other non-Latin locales do. In `MessageFormat` strings a literal apostrophe is `''`. |
| Flutter .arb | Translate values only; leave `@key` metadata blocks. Set `"@@locale": "bn"`. Keep ICU plural/select syntax. |
| Android strings.xml | Escape apostrophes (`\'`) and quotes; keep `%1$s`, `<xliff:g>` and `<b>` tags; `<plurals>` needs `one` and `other`; respect `translatable="false"`. |
| iOS .strings / .stringsdict / .xcstrings | Keep `%@`, `%d`, `%1$@`; escape `"`; keep the key side unchanged. |
| XLIFF | Translate `<target>` only; keep `<x/>`, `<g>`, `<ph>` inline elements; set `target-language="bn-BD"`. |
| Markdown / MDX | Translate prose, headings, link text and image alt. Keep frontmatter keys (translate `title`/`description` values), code blocks, inline code, link URLs, anchors/IDs, component names and props. Heading-derived anchors change when headings are translated, so check in-page links. |
| CSV / spreadsheets | Keep column order and IDs; quote fields with commas; keep UTF-8. |
| CMS exports (WordPress, Shopify, Webflow) | Follow the platform's locale mechanism rather than overwriting the source language. Shopify Liquid: keep `{{ }}` and `{% %}` tags. |

## 3. HTML and static sites

- Set the language: `<html lang="bn">` (or `bn-BD` / `bn-IN`). Direction stays
  `ltr`. Screen readers, search engines, hyphenation and font selection all
  depend on `lang`.
- Mark long English passages left inside Bengali pages with `lang="en"` so they
  get the right font and pronunciation.
- Charset: `<meta charset="utf-8">`.
- For a bilingual site, add reciprocal `hreflang` links (`en`, `bn`, and
  `x-default`), and a visible language switcher labelled in each language's own
  name: "English" and "বাংলা".
- Do not wrap part of a Bengali syllable in an inline element (for example a
  `<span>` around one letter of a conjunct or between a consonant and its vowel
  sign); the browser will break the shaping. Wrap whole words.
- Text baked into images, SVGs, videos and PDFs is not reached by string
  translation. List these in the report.

## 4. Numbers and dates in code

Let the runtime localize dynamic values:

```js
new Intl.NumberFormat('bn-BD').format(1234567)            // ১২,৩৪,৫৬৭
new Intl.NumberFormat('bn-BD', { style: 'currency', currency: 'BDT',
  maximumFractionDigits: 0 }).format(1250)                 // ১,২৫০৳ (symbol after the number in current ICU data)
new Intl.DateTimeFormat('bn-BD', { dateStyle: 'long' }).format(d)  // ১২ নভেম্বর, ২০২৬
new Intl.NumberFormat('bn-BD-u-nu-latn').format(1234567)  // 12,34,567 (Latin digits, lakh grouping)
new Intl.PluralRules('bn').select(1)                      // "one"
```

- `Intl` puts the ৳ after the amount (`১,২৫০৳`), while most Bangladeshi sites
  write `৳১,২৫০`. If that is the house style, format the number with `Intl`
  and add the symbol yourself. Time comes out as `৩:৩০ PM`.
- Inputs: keep `type="number"`/`inputmode="numeric"` fields in Latin digits.
  If users may type Bengali digits (phone, amount), normalize them to Latin in
  code before validating, rather than rejecting them.
- Sorting and search should use `Intl.Collator('bn')` / locale-aware
  comparison, not code-point order.
- String length limits count code units, not visible letters: one visible
  Bengali syllable can be 2-5 code points. Truncate with `Intl.Segmenter`
  (grapheme granularity) or CSS `text-overflow`, never by `slice(0, n)`.

## 5. SEO

- Translate `<title>` and the meta description as real copy, not word for word,
  and keep the brand name in Latin. Bengali glyphs are wider than Latin, so aim
  for shorter counts: roughly 45-55 characters for titles and 110-140 for
  descriptions, then check in a preview.
- People in Bangladesh search in Bengali script, in English, and in romanized
  Bengali. Keep important English keywords and brand terms where a searcher
  would type them (in the title or description alongside the Bengali), instead
  of translating them away.
- Keep URL slugs in Latin unless the client asks for Bengali slugs; Bengali
  slugs percent-encode into long, unreadable links when shared.
- Each language version needs its own URL (`/bn/…`), self-referencing canonical
  and `hreflang` pairs. Do not auto-redirect by IP without a switcher.
- Translate image `alt` text and structured-data descriptions; leave schema
  property names and enum values in English.

## 6. Fonts and CSS for Bengali script

Bengali has a headline (মাত্রা), marks above and below the line, and stacked
conjuncts. CSS tuned for Latin text makes it cramped, clipped or broken.

**Fonts.** Use a real Bengali webfont with a Bengali system fallback; never
rely on the Latin font's fallback.

```css
:lang(bn) {
  font-family: "Hind Siliguri", "Noto Sans Bengali", "Anek Bangla",
               "SolaimanLipi", "Kalpurush", "Nirmala UI", "Vrinda", sans-serif;
}
```

Good open webfonts: Noto Sans Bengali, Hind Siliguri, Anek Bangla, Baloo Da 2,
Noto Serif Bengali and Tiro Bangla (serif). Load the `bengali` subset and only
the weights the design uses. If the Latin brand font must stay for English
words, list it first and the Bengali font second; the browser picks per glyph.

**Rules that matter:**

| Property | Do | Why |
|---|---|---|
| `line-height` | 1.6-1.8 for body text; at least 1.3 for headings | Marks above and below collide or get clipped at Latin values like 1.2 |
| `letter-spacing` | `normal` (0) on all Bengali text | Tracking splits conjuncts and breaks the headline in every browser engine; there is no workaround |
| `text-transform` | No effect (no case). Replace uppercase-as-emphasis with weight or size | ALL-CAPS labels lose their emphasis silently |
| `font-style: italic` | Avoid; use weight or colour | Bengali has no italic tradition; browsers fake a slant |
| `font-size` | Often 5-15% larger than the Latin size for equal legibility; never below about 14px for body | Dense glyphs |
| `font-weight` | Use weights the font really has | Synthetic bold smears conjuncts |
| `overflow: hidden` with fixed heights | Give extra vertical padding | Tall glyphs clip at the top and bottom of buttons, inputs, badges |
| `text-decoration: underline` | Add `text-underline-offset: 0.2em` | The line otherwise cuts through below-base marks |
| `word-break: break-all` | Avoid; use `overflow-wrap: break-word` | Splits syllables mid-cluster |
| `::first-letter`, drop caps | Avoid or test in Firefox | May select part of a conjunct |
| `text-align: justify` | Avoid in narrow columns | Bengali words are long; spacing becomes uneven |
| List markers | `list-style-type: bengali` for Bengali digits in ordered lists | Matches the digit policy |
| `-webkit-text-stroke` | Avoid | Breaks the joined headline |

Scope all of this with `:lang(bn)` (or a `html[lang^="bn"]` selector) so the
English site is unaffected.

## 7. Unicode hygiene

- **Unicode only.** Legacy Bijoy/SutonnyMJ text looks like Latin gibberish
  (`Avgvi †mvbvi evsjv`) and must be converted before use, never pasted.
- **Normalize to NFC.** The vowel signs ো (U+09CB) and ৌ (U+09CC) must be single
  code points, not ে + া or ে + ৗ. Note that NFC writes য়, ড়, ঢ় as base letter
  + nukta (U+09BC); that is correct and expected, so do not "fix" it, but be
  aware when searching or comparing strings, and normalize both sides.
- **দাঁড়ি is U+0964** (`।`). Not `|` (U+007C), not `l`, not `I`.
- **Colon is `:`**, not visarga ঃ (U+0983).
- **ৎ is U+09CE** (khanda ta), not ত + হসন্ত.
- **র‍্য (ra + ya-phala)** as in র‍্যাংকিং, র‍্যাম, র‍্যান্ডম is
  র + ZWJ (U+200D) + ্ + য. Without the ZWJ it renders as a reph over য.
- **ZWNJ (U+200C)** after a হসন্ত keeps it visible instead of forming a
  conjunct. It is occasionally needed in loanwords; do not strip ZWJ/ZWNJ from
  Bengali text in "cleanup" code.
- Remove stray zero-width spaces (U+200B), BOMs and U+FFFD replacement
  characters; keep non-breaking spaces only where the source had them.
- Vowel signs, হসন্ত, ং, ঃ and ঁ cannot start a word or follow a space; if one
  does, the text was damaged by a bad split or copy.
- Do not mix in look-alike Devanagari or Assamese letters (ৰ, ৱ are Assamese).
- Database and API layers must be UTF-8 end to end (`utf8mb4` in MySQL), with
  column lengths sized for multi-code-point letters.

`scripts/bn_lint.py` checks most of the items in this section automatically.

## 8. Layout checks before shipping

Bengali strings are often the same length as English or shorter in characters,
but they are taller and individual words can be long. Check:

- buttons, tabs, badges, table headers and nav items for wrapping or clipping;
- inputs and selects for clipped tops and bottoms of glyphs;
- truncated text for cut-off syllables;
- headings that relied on uppercase or letter-spacing for their look;
- mixed Bengali/Latin lines for baseline and size mismatch;
- emails in real clients (many strip webfonts, so the system Bengali font is
  what users see);
- that the fallback font is acceptable when the webfont fails to load.

If a browser is available, open the Bengali page and take a screenshot at
mobile and desktop widths rather than assuming.
