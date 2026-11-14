# Sources

The rules in this skill are distilled from the following standards and style
guides, plus prevailing practice in major Bengali-language products and press.
Where sources disagree, the skill follows Bangla Academy spelling and
Bangladesh (bn-BD) usage by default.

- **Bangla Academy, প্রমিত বাংলা বানানের নিয়ম** - the spelling standard,
  including the rules for foreign words (ই/উ-কার only, no ণ/ষ, শ for sh/-tion,
  অ্যা, ং). A readable summary:
  https://bangla.bdnews24.com/blog/192745
- **Mozilla bn-BD localization style guide** - tone (no সাধু, address users
  with আপনি), keep-in-English-script when unnatural, brands unchanged,
  acronyms, units, dates, currency, দাঁড়ি:
  https://mozilla-l10n.github.io/styleguides/bn-BD
  and https://wiki.mozilla.org/L10n:Teams:bn-BD/StyleGuide
- **Joomla Bengali Style Guide** - the same conventions applied to web CMS
  strings, placeholder and markup handling:
  https://docs.sandbox.joomla.org/Bengali_Style_Guide
- **Microsoft Bangla style guide** (India edition is the published one):
  https://learn.microsoft.com/en-us/globalization/reference/microsoft-style-guides
- **WordPress Polyglots handbook** - glossaries and style guides per locale:
  https://make.wordpress.org/polyglots/handbook/translating/glossaries-and-style-guides-per-locale/
- **Unicode CLDR** - Bengali plural rules (cardinal `one` for 0 and 1, `other`;
  irregular ordinals), number grouping and compact forms (হাজার, লাখ, কোটি):
  https://www.unicode.org/cldr/charts/46/supplemental/language_plural_rules.html
  and https://www.unicode.org/cldr/charts/47/verify/numbers/bn.html
- **W3C Bengali Gap Analysis** - what breaks for Bengali in browsers:
  letter-spacing splitting conjuncts, `::first-letter`, underlines, spans
  inside syllables, counters:
  https://www.w3.org/TR/2025/DNOTE-beng-gap-20250207
- **W3C Bengali Script Resources / Layout Requirements**:
  https://www.w3.org/TR/2026/DNOTE-beng-lreq-20260320/
- **Unicode Bengali code chart (U+0980-U+09FF)**:
  https://www.unicode.org/charts/PDF/U0980.pdf

These are living documents. If a project has its own glossary or house style,
that takes precedence over everything here except the technical-safety rules.
