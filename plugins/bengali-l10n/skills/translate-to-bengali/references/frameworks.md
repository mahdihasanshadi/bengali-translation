# Wiring Bengali into the project

A translated file that the app never loads fixes nothing. This file covers the
developer side: finding every user-visible string, registering the `bn` locale
in the framework, loading a Bengali font, and keeping the translation in step
with the English source afterwards.

## Contents

1. Detect the setup
2. Find strings that are not in the locale files yet
3. Framework recipes
4. Language switcher, `lang` and URLs
5. Large projects: batching
6. Keeping Bengali in sync when English changes
7. Wiring checklist

## 1. Detect the setup

Look before asking. These files tell you the framework and where strings live:

| You see | It is | Bengali goes in |
|---|---|---|
| `next.config.*` + `next-intl` in package.json | Next.js + next-intl | `messages/bn.json` |
| `i18next` / `react-i18next` / `next-i18next` | i18next | `locales/bn/<namespace>.json` or `public/locales/bn/…` |
| `vue-i18n` / `@nuxtjs/i18n` | Vue / Nuxt | `locales/bn.json` (or the `messages` object) |
| `@angular/localize`, `messages.xlf` | Angular | `src/locale/messages.bn.xlf` |
| `react-intl` / FormatJS | react-intl | `lang/bn.json` (often compiled) |
| `svelte-i18n`, `@inlang/paraglide-*` | Svelte | `messages/bn.json` / `locales/bn.json` |
| `lang/` or `resources/lang/` + `artisan` | Laravel | `lang/bn.json` or `lang/bn/*.php` |
| `LocaleMiddleware`, `locale/*/LC_MESSAGES` | Django | `locale/bn/LC_MESSAGES/django.po` |
| `config/locales/*.yml` | Rails | `config/locales/bn.yml` |
| `wp-content`, `.pot` files | WordPress | theme: `languages/bn_BD.po`; plugin: `languages/<textdomain>-bn_BD.po` |
| `l10n.yaml`, `lib/l10n/*.arb` | Flutter | `lib/l10n/app_bn.arb` |
| `res/values/strings.xml` | Android | `res/values-bn/strings.xml` |
| `*.lproj`, `Localizable.xcstrings` | iOS / macOS | `bn.lproj/…` or the `bn` column of the String Catalog |
| `locales/en.default.json` in a theme | Shopify theme | `locales/bn.json` |
| plain `.html` files, no framework | Static site | a parallel `/bn/` tree |

If the project has **no i18n at all**, say so before translating. The choices
are (a) a separate Bengali copy of each page (quick, but two copies to
maintain), or (b) adding the framework's standard i18n library and extracting
strings first (more work once, far cheaper afterwards). Recommend (b) for any
app that is still being developed, and do not install a library without the
user's go-ahead.

## 2. Find strings that are not in the locale files yet

The most common complaint after a "complete" translation is English still
showing on Bengali pages. The cause is nearly always strings that never went
through i18n. Search for them before reporting the work as done:

```bash
# JSX/TSX/Vue text nodes with English words (also catches >OK< and text split over lines)
rg -n -U --glob '*.{jsx,tsx,vue,svelte}' '>\s*[A-Z][A-Za-z]+[^<{]*<' .
# human-visible attributes with literal English, in components and server templates
rg -n --glob '*.{jsx,tsx,vue,svelte,html,php,erb,twig,hbs}' '(placeholder|title|alt|aria-label)="[A-Z][^"{]*"' .
# toast/alert/error messages passed as literals (setErrorMessage, showToast ...)
rg -n -i --glob '*.{js,ts,jsx,tsx}' '(toast|alert|message|error)\w*\(\s*["'"'"'`][A-Z]' .
# backend validation and email text
rg -n --glob '*.{php,py,rb}' '["'"'"'][A-Z][a-z]+ [a-z]+[^"'"'"']*["'"'"']' app/ src/ templates/ 2>/dev/null | head -50
```

Always give `rg` a path (the `.` above): without one, in a non-interactive
shell it waits on stdin. If `rg` is missing, `grep -rnE` with the same
patterns works. These searches are a starting point, not proof; also read
the main layouts and the screens the user cares most about.

Also check: `<title>` and meta tags set in layout code, `document.title`,
error pages (404/500), emails and SMS templates, PDFs and invoices, push
notifications, form validation libraries (zod, yup, Laravel/Django validators
each have their own message files), date pickers and other third-party
components with their own locale packs, and text baked into images.

Extract what you find into the locale files under sensible keys (follow the
project's existing key style), replace the literal with the framework's
translate call, then translate. List anything you could not extract
(images, third-party widgets without a locale option) in the report.

## 3. Framework recipes

Each recipe lists the minimum needed to make `bn` load. Follow the project's
existing pattern where it differs; framework versions change, so check the
installed version's docs when an API does not match.

### Next.js (App Router) + next-intl

- Add `bn` to the locales list (in recent versions `src/i18n/routing.ts`:
  `defineRouting({ locales: ['en', 'bn'], defaultLocale: 'en' })`).
- Create `messages/bn.json` with the same keys as `messages/en.json`.
- Set `<html lang={locale}>` in the root `[locale]/layout.tsx`.
- Font: `next/font/google` with `Hind_Siliguri({ subsets: ['bengali'], weight: ['400','500','600','700'] })`
  (or `Noto_Sans_Bengali`), applied when `locale === 'bn'`.
- next-intl uses ICU messages: keep `{count, plural, one {…} other {…}}` intact.

### Next.js (Pages Router)

`next.config.js`: `i18n: { locales: ['en', 'bn'], defaultLocale: 'en' }`, then
the library the project uses (often `next-i18next`, with
`public/locales/bn/common.json`).

### i18next / react-i18next

- Add `bn` to `supportedLngs` and the resources or backend path.
- Plural keys use suffixes: Bengali needs `_one` and `_other` only (CLDR:
  `one` covers 0 and 1). Do not add `_few`/`_many`.
- Interpolation is `{{name}}`; nesting is `$t(key)`; `<1>…</1>` are Trans
  component slots. All stay as they are.

### Vue / Nuxt (vue-i18n)

- Add `bn` to `locales` (Nuxt: `i18n.locales: [{ code: 'bn', language: 'bn-BD', file: 'bn.json', name: 'বাংলা' }]`).
- vue-i18n's pipe plural syntax uses `|` as syntax. Keep the same number of
  `|`-separated forms as the source, because vue-i18n picks a form by
  position, not by language rule: with two forms, n = 1 gets the first and
  0 or 2+ get the second; with three, they are 0 / 1 / many. So
  `'no items | one item | {n} items'` becomes
  `'কোনো আইটেম নেই | ১টি আইটেম | {n}টি আইটেম'`. Never turn the pipe into a দাঁড়ি.
- Linked messages `@:key` and `{name}` stay as they are.

### Angular (@angular/localize)

- `ng extract-i18n` produces `messages.xlf`; copy to `messages.bn.xlf`, set
  `target-language="bn"`, fill each `<target>`, keep `<x id="…"/>`.
- Add `"bn": "src/locale/messages.bn.xlf"` under `i18n.locales` in
  `angular.json` and build with `--localize`. Use the same code (`bn`, or
  `bn-BD` in both places) in the file and in `angular.json`.
- Lint: `python scripts/bn_lint.py --target src/locale/messages.bn.xlf`.

### react-intl / FormatJS

Translate the extracted `lang/en.json` into `lang/bn.json` (keep the
`defaultMessage`/`description` structure if the project uses it), then run the
project's compile step. Messages are ICU.

### Laravel

- JSON strings: `lang/bn.json`, where keys are the English sentences
  themselves. Translate only the values.
- PHP arrays: `lang/bn/validation.php`, `auth.php`, `pagination.php`,
  `passwords.php` - copy from `lang/en/` and translate values. Laravel 10+
  ships without a `lang/` folder; run `php artisan lang:publish` first to get
  the English files (older versions keep them in `resources/lang/`). Validation
  messages matter: they are the errors users read. The community package
  `laravel-lang/lang` ships a Bengali base you can start from and correct.
- Placeholders are `:attribute`, `:min`, `:max`. Keep them; Bengali word order
  may move them.
- Default locale: `APP_LOCALE=bn` in `.env` (Laravel 11+) or `'locale' => 'bn'`
  in `config/app.php` (older); per request, `App::setLocale('bn')` in a
  middleware.
- Lint PHP arrays with `--target-only lang/bn/validation.php` (Bengali checks);
  JSON with `--source lang/en.json --target lang/bn.json`.

### Django

- `LANGUAGES = [("en", "English"), ("bn", "বাংলা")]`, `LocaleMiddleware`
  enabled, `LOCALE_PATHS` set.
- `python manage.py makemessages -l bn` (and `-d djangojs` for JS), translate
  `locale/bn/LC_MESSAGES/django.po`, then `compilemessages`.
- The header needs `Language: bn` and a two-form `Plural-Forms`. CLDR's rule
  is `nplurals=2; plural=(n > 1);` (0 and 1 take the first form); Django's
  own Bengali catalog and many tools use `plural=(n != 1);` (0 takes the
  second). Both compile. Keep whichever the project already has; since
  Bengali usually writes both forms the same (`%dটি ফাইল`), the difference
  rarely shows. If the forms differ, write them so either rule reads correctly.
- Lint: `python scripts/bn_lint.py --target locale/bn/LC_MESSAGES/django.po`.

### Rails

- `config/locales/bn.yml` with `bn:` as the top-level key (not `en:`).
- `config.i18n.available_locales = [:en, :bn]`.
- The `rails-i18n` gem provides Bengali date, number and pluralization data.
- Placeholders are `%{name}`.
- Lint: `python scripts/bn_lint.py --source config/locales/en.yml --target config/locales/bn.yml`
  (needs `pip install pyyaml`).

### WordPress

- Locale code is `bn_BD`. Translate the `.pot` and compile to `.mo`. File
  names: a theme's own `languages/` folder uses `bn_BD.po`/`bn_BD.mo`; a
  plugin uses `<textdomain>-bn_BD.po`; files under
  `wp-content/languages/themes/` or `/plugins/` use `<textdomain>-bn_BD.po`.
  Tools: Poedit, Loco Translate, or
  `wp i18n make-mo`). Newer WordPress also reads `.l10n.php` files generated by
  `wp i18n make-php`.
- Site language: Settings → General → Site Language → বাংলা.
- For multilingual content (posts, pages), the site uses a plugin such as
  WPML, Polylang or TranslatePress; follow its export/import format (often
  XLIFF or .po).

### Flutter

- `l10n.yaml` points at `lib/l10n`; add `app_bn.arb` with `"@@locale": "bn"`.
- `supportedLocales` includes `Locale('bn')`; keep
  `GlobalMaterialLocalizations.delegate` etc. so built-in widgets (date
  pickers, dialogs) are Bengali too.
- Run `flutter gen-l10n`. Metadata entries (`@key`) are not translated.
- Lint: `--source lib/l10n/app_en.arb --target lib/l10n/app_bn.arb`.

### Android

- `res/values-bn/strings.xml` (or `values-b+bn+BD` for Bangladesh only).
- Escape apostrophes as `\'`; keep `%1$s`, `<xliff:g>`, `<plurals>` with
  `one` and `other`; skip `translatable="false"` entries.
- Android 13+ per-app language picker: list `bn` in `res/xml/locales_config.xml`
  and reference it from the manifest's `<application android:localeConfig="@xml/locales_config">`
  (AGP 8.1+ can generate the file with `generateLocaleConfig = true`).
- Lint: `--source res/values/strings.xml --target res/values-bn/strings.xml`.

### iOS / macOS

- Add Bengali under Project → Info → Localizations.
- String Catalog (`Localizable.xcstrings`): fill the `bn` column; plural
  variations need `one` and `other`. Lint with
  `--target Localizable.xcstrings`.
- Legacy `bn.lproj/Localizable.strings`: keys unchanged, `"key" = "value";`,
  escape `"`. Lint with `--source en.lproj/Localizable.strings --target bn.lproj/Localizable.strings`.
- Permission prompts (camera, location) live in `InfoPlist.xcstrings` (String
  Catalog projects) or `bn.lproj/InfoPlist.strings` (legacy): translate them too.

### Shopify themes

`locales/bn.json` mirrors `locales/en.default.json`; Liquid tags `{{ }}` and
`{% %}` stay. Publish Bengali in Settings → Languages.

### Static HTML

Create `/bn/` copies, set `<html lang="bn">`, add reciprocal `hreflang`
links, link a Bengali font, and lint each page against its English original:
`--source index.html --target bn/index.html`.

## 4. Language switcher, `lang` and URLs

- Label the switcher in each language's own name: **English** and **বাংলা**
  (not "Bengali", not a flag; a flag stands for a country, and Bengali is
  spoken in two).
- `<html lang>` must change with the locale (`bn`, `bn-BD` or `bn-IN`). It
  drives font fallback, screen readers, hyphenation and search engines.
- Remember the user's choice (cookie or URL prefix); do not force a language
  by IP.
- Each language needs its own URL (`/bn/...`) with `hreflang` pairs for SEO;
  see `technical.md` §5.

## 5. Large projects: batching

For more than a few hundred strings:

1. Fix the glossary first (SKILL.md step 3) from a skim of the whole source.
2. Translate one namespace or file at a time, writing each finished batch to
   disk.
3. Run the linter after each batch; fix errors before moving on, so mistakes
   do not repeat across the project.
4. Re-read the glossary between batches; extend it rather than improvising a
   synonym.
5. At the end, lint the whole set and do one consistency pass across files.

## 6. Keeping Bengali in sync when English changes

Translations rot when the English source changes and nobody updates Bengali.

- **Find what changed.** Run the linter: `key missing in target` lists new
  strings and `key not present in source` lists removed ones. With git:
  `git diff <last-translated-commit> -- locales/en.json` shows edited strings
  whose Bengali is now stale.
- Translate only those strings; do not re-translate (and re-word) the rest.
  Users notice when familiar labels change for no reason.
- Delete Bengali keys that were removed from English.
- **Stop it recurring.** Add the linter to CI so a missing or broken Bengali
  string fails the build:

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
      - run: python .claude/skills/translate-to-bengali/scripts/bn_lint.py --source locales/en.json --target locales/bn.json --glossary bn-glossary.json
```

  Adjust the paths to where the skill and the locale files live. A pre-commit
  hook running the same command works as well.

## 7. Wiring checklist

Before reporting the job as done:

- [ ] `bn` is registered wherever the framework lists locales.
- [ ] The Bengali file has every key of the source (linter: no missing keys).
- [ ] No hard-coded English left in components, layouts, emails or validation.
- [ ] `<html lang>` switches to `bn`; the switcher says বাংলা.
- [ ] A Bengali font loads for `:lang(bn)`, with CSS fixes from `technical.md` §6.
- [ ] Dates, numbers and currency come from `Intl`/the framework with the
      `bn-BD` (or `bn-IN`) locale, not hand-built strings.
- [ ] Third-party widgets (date pickers, payment forms, maps) have their
      Bengali locale enabled, or are listed in the report as English-only.
- [ ] If the app can be run, the Bengali pages were opened and checked at
      mobile and desktop widths.
