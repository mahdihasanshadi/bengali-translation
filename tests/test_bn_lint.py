"""Tests for bn_lint.py. Run from the repository root:

    python -m unittest discover -s tests -v
"""
import contextlib
import importlib.util
import io
import json
import shutil
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / "plugins" / "bengali-l10n" / "skills" / "translate-to-bengali"
FIX = Path(__file__).resolve().parent / "fixtures"
EX = ROOT / "examples"

spec = importlib.util.spec_from_file_location("bn_lint", SKILL / "scripts" / "bn_lint.py")
bn_lint = importlib.util.module_from_spec(spec)
spec.loader.exec_module(bn_lint)

try:
    import yaml  # noqa: F401
    HAVE_YAML = True
except ImportError:
    HAVE_YAML = False


def run(*args):
    """Run the linter with --json; return (exit code, parsed report)."""
    out, err = io.StringIO(), io.StringIO()
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        code = bn_lint.main([str(a) for a in args] + ["--json"])
    text = out.getvalue()
    return code, (json.loads(text) if text.strip() else {"stderr": err.getvalue()})


def messages(report, where=None, severity=None):
    return [f["message"] for f in report.get("findings", [])
            if (where is None or f["where"] == where)
            and (severity is None or f["severity"] == severity)]


def has(report, where, fragment, severity=None):
    return any(fragment in m for m in messages(report, where, severity))


class TempDir(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def write(self, name, content, encoding="utf-8"):
        p = self.tmp / name
        if isinstance(content, bytes):
            p.write_bytes(content)
        else:
            with open(p, "w", encoding=encoding, newline="") as fh:
                fh.write(content)
        return p

    def pair(self, src: dict, tgt: dict, *extra):
        s = self.write("en.json", json.dumps(src, ensure_ascii=False))
        t = self.write("bn.json", json.dumps(tgt, ensure_ascii=False))
        return run("--source", s, "--target", t, *extra)


class Examples(unittest.TestCase):
    def test_good_json_is_clean(self):
        code, r = run("--source", EX / "en.json", "--target", EX / "bn.good.json", "--digits", "bn", "--strict")
        self.assertEqual(code, 0, r["findings"])
        self.assertEqual(r["checked"], 13)

    def test_bad_json_finds_every_planted_problem(self):
        code, r = run("--source", EX / "en.json", "--target", EX / "bn.bad.json", "--digits", "bn")
        self.assertEqual(code, 1)
        self.assertTrue(has(r, "nav.home", "বাড়ি"))
        self.assertTrue(has(r, "nav.contact", "identical to the source"))
        self.assertTrue(has(r, "auth.signIn", "স্বাক্ষর"))
        self.assertTrue(has(r, "auth.forgot", "গুপ্তসংকেত"))
        self.assertTrue(has(r, "auth.forgot", "গেছো"))
        self.assertTrue(has(r, "auth.welcome", "unexpected {নাম}", "error"))
        self.assertTrue(has(r, "cart.empty", "pipe", "error"))
        self.assertTrue(has(r, "cart.items", "ICU 'plural'", "error"))
        self.assertTrue(has(r, "cart.freeShipping", "mixed inside one number", "error"))
        self.assertTrue(has(r, "cart.freeShipping", "ডেলিভারী"))
        self.assertTrue(has(r, "cart.save", "a discount"))
        self.assertTrue(has(r, "errors.generic", "mixed in one string", "error"))
        self.assertTrue(has(r, "errors.email", "key missing", "error"))
        self.assertTrue(has(r, "footer.terms", "href/src", "error"))

    def test_eval_review_file_is_flagged(self):
        d = SKILL / "evals" / "review-existing-translation" / "files"
        code, r = run("--source", d / "en.json", "--target", d / "bn.json")
        self.assertEqual(code, 1)
        self.assertGreaterEqual(r["errors"], 5)

    def test_good_html_page_has_no_errors(self):
        code, r = run("--source", EX / "html" / "index.en.html", "--target", EX / "html" / "index.bn.html",
                      "--digits", "bn")
        self.assertEqual(code, 0, r["findings"])
        self.assertEqual(r["errors"], 0)
        self.assertEqual(r["checked"], 24)
        # the only warning is the deliberate 3 million -> ৩০ লাখ conversion
        self.assertTrue(all("numbers differ" in m for m in messages(r)), r["findings"])


class Output(TempDir):
    def test_plain_output_survives_a_legacy_console(self):
        """Regression: printing Bengali crashed on a cp1252 Windows console."""
        raw = io.BytesIO()
        console = io.TextIOWrapper(raw, encoding="cp1252", errors="strict")
        with contextlib.redirect_stdout(console):
            code = bn_lint.main(["--source", str(EX / "en.json"), "--target", str(EX / "bn.bad.json")])
            console.flush()
        self.assertEqual(code, 1)
        self.assertIn("strings checked".encode(), raw.getvalue())

    def test_usage_errors_exit_2(self):
        code, _ = run()
        self.assertEqual(code, 2)
        code, _ = run("--target", self.tmp / "missing.json")
        self.assertEqual(code, 2)
        t = self.write("bn.json", "{}")
        code, _ = run("--target", t)   # JSON needs --source
        self.assertEqual(code, 2)

    def test_invalid_json_is_an_error_finding(self):
        s = self.write("en.json", '{"a": "Hello"}')
        t = self.write("bn.json", '{"a": "হ্যালো",}')
        code, r = run("--source", s, "--target", t)
        self.assertEqual(code, 1)
        self.assertTrue(any("invalid JSON" in m for m in messages(r)))

    def test_non_utf8_file_is_reported(self):
        s = self.write("en.json", '{"a": "Hello"}')
        t = self.write("bn.json", b'{"a": "\xe0\xa6"}')   # truncated UTF-8 sequence
        code, r = run("--source", s, "--target", t)
        self.assertEqual(code, 1)
        self.assertTrue(any("not valid UTF-8" in m for m in messages(r)))

    def test_strict_fails_on_warnings(self):
        code, _ = self.pair({"a": "Go home"}, {"a": "বাড়ি যান"})
        self.assertEqual(code, 0)
        code, _ = self.pair({"a": "Go home"}, {"a": "বাড়ি যান"}, "--strict")
        self.assertEqual(code, 1)


class Placeholders(TempDir):
    def test_all_placeholder_syntaxes_are_protected(self):
        src = {"a": "{{count}} %s %1$d ${x} %(name)s %{amount} :user <0>x</0> &nbsp; {id} $t(k) @:k.v \\n"}
        tgt = {"a": "{{count}} %s %1$d ${x} %(name)s %{amount} :user <0>এক্স</0> &nbsp; {id} $t(k) @:k.v \\n"}
        code, r = self.pair(src, tgt)
        self.assertEqual(r["errors"], 0, r["findings"])
        for good, broken in (("{{count}}", "{{কাউন্ট}}"), ("%1$d", "%১$d"), ("${x}", "${এক্স}"),
                             ("%{amount}", "%{টাকা}"), (":user", ":ইউজার"), ("{id}", "{আইডি}")):
            bad = {"a": tgt["a"].replace(good, broken, 1)}
            self.assertNotEqual(bad, tgt)
            code, r = self.pair(src, bad)
            self.assertTrue(has(r, "a", "placeholder mismatch", "error"), broken)

    def test_translated_simple_placeholder(self):
        _, r = self.pair({"a": "Hi {name}"}, {"a": "হাই {নাম}"})
        self.assertTrue(has(r, "a", "was translated", "error"))

    def test_placeholder_may_move(self):
        _, r = self.pair({"a": "Click {link} to download"}, {"a": "ডাউনলোড করতে {link}-এ ক্লিক করুন"})
        self.assertEqual(r["errors"], 0, r["findings"])

    def test_laravel_colon_param_not_confused_with_time(self):
        _, r = self.pair({"a": "Opens at 9:30"}, {"a": "৯:৩০-এ খোলে"})
        self.assertEqual(r["errors"], 0, r["findings"])


class ICU(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        _, cls.r = run("--source", FIX / "icu" / "en.json", "--target", FIX / "icu" / "bn.json")

    def test_valid_blocks_pass(self):
        for key in ("cart", "cartWords", "invite"):
            self.assertEqual(messages(self.r, key), [], key)

    def test_branch_bodies_are_not_placeholders(self):
        tokens, icu = bn_lint.scan_braces("{n, plural, one {# item} other {{name} has # items}}")
        self.assertEqual(tokens, ["{n, plural}", "{name}"])
        self.assertEqual(icu[0]["selectors"], ["one", "other"])

    def test_translated_plural_key(self):
        self.assertTrue(has(self.r, "badKeys", "['এক']", "error"))

    def test_missing_other(self):
        self.assertTrue(has(self.r, "noOther", "no 'other' branch", "error"))

    def test_translated_select_key(self):
        self.assertTrue(has(self.r, "selectKeys", "select branches changed", "error"))

    def test_translated_argument_name(self):
        self.assertTrue(has(self.r, "renamedArg", "{সংখ্যা, plural}", "error"))

    def test_offset_and_exact_selectors(self):
        tokens, icu = bn_lint.scan_braces("{n, plural, offset:1 =0 {none} =1 {one} other {# more}}")
        self.assertEqual(icu[0]["selectors"], ["=0", "=1", "other"])


class Formats(unittest.TestCase):
    def test_arb(self):
        code, r = run("--source", FIX / "arb" / "app_en.arb", "--target", FIX / "arb" / "app_bn.arb")
        self.assertEqual(code, 1)
        self.assertTrue(has(r, "app_bn.arb", '"@@locale" is "en"'))
        self.assertTrue(has(r, "unread", "ICU 'plural'", "error"))
        self.assertEqual(messages(r, "greeting"), [])
        self.assertFalse(any(f["where"].startswith("@") for f in r["findings"]))

    @unittest.skipUnless(HAVE_YAML, "PyYAML not installed")
    def test_yaml(self):
        code, r = run("--source", FIX / "yaml" / "en.yml", "--target", FIX / "yaml" / "bn.yml")
        self.assertEqual(code, 1)
        self.assertTrue(has(r, "bn.yml", "still 'en:'"))
        self.assertTrue(has(r, "nav.home", "বাড়ি"))
        self.assertTrue(has(r, "checkout.pay", "key missing", "error"))
        self.assertEqual(messages(r, "checkout.total"), [])

    def test_android(self):
        d = FIX / "android"
        code, r = run("--source", d / "values" / "strings.xml", "--target", d / "values-bn" / "strings.xml")
        self.assertEqual(code, 1)
        self.assertTrue(has(r, "tagline", "unescaped apostrophe", "error"))
        self.assertTrue(has(r, "sync", "missing %1$s", "error"))
        self.assertEqual(messages(r, "welcome"), [])
        self.assertEqual(messages(r, "tasks[one]"), [])
        self.assertNotIn("app_name", [f["where"] for f in r["findings"]])   # translatable="false"

    def test_ios_strings(self):
        code, r = run("--source", FIX / "ios" / "en.strings", "--target", FIX / "ios" / "bn.strings")
        self.assertEqual(code, 1)
        self.assertTrue(has(r, "bn.strings", "cannot parse", "error"))
        self.assertEqual(messages(r, "home.greeting"), [])

    def test_ios_strings_utf16(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            s, t = tmp / "en.strings", tmp / "bn.strings"
            s.write_text('"a" = "Search";\n', encoding="utf-16")
            t.write_text('"a" = "খুঁজুন";\n', encoding="utf-16")
            code, r = run("--source", s, "--target", t, "--strict")
            self.assertEqual(code, 0, r)
        finally:
            shutil.rmtree(tmp)

    def test_xliff(self):
        code, r = run("--target", FIX / "xliff" / "messages.bn.xlf")
        self.assertEqual(code, 1)
        self.assertEqual(r["checked"], 4)
        self.assertTrue(has(r, "items", "markup mismatch", "error"))
        self.assertTrue(has(r, "settings", "empty translation", "error"))
        self.assertEqual(messages(r, "welcome"), [])

    def test_xcstrings(self):
        code, r = run("--target", FIX / "xcstrings" / "Localizable.xcstrings")
        self.assertEqual(code, 1)
        self.assertEqual(messages(r, "Hello, %@!"), [])
        self.assertEqual(messages(r, "cart.count[plural:one]"), [])
        self.assertTrue(has(r, "cart.count[plural:other]", "needs_review"))
        self.assertTrue(has(r, "cart.count[plural:other]", "missing %lld", "error"))
        self.assertTrue(has(r, "Settings", "no Bengali", "error"))
        self.assertNotIn("Taskly", [f["where"] for f in r["findings"]])

    def test_vue_i18n_pipe_plurals_are_not_full_stops(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            (tmp / "en.json").write_text('{"car": "no car | one car | {n} cars"}', encoding="utf-8")
            t = tmp / "bn.json"
            t.write_text('{"car": "কোনো গাড়ি নেই | একটি গাড়ি | {n}টি গাড়ি"}', encoding="utf-8")
            code, r = run("--source", tmp / "en.json", "--target", t, "--fix")
            self.assertEqual(code, 0, r["findings"])
            self.assertIn(" | ", t.read_text(encoding="utf-8"))
            self.assertEqual(r["fixed"], [])
        finally:
            shutil.rmtree(tmp)

    def test_po(self):
        code, r = run("--target", FIX / "po" / "bn.po")
        self.assertEqual(code, 1)
        self.assertTrue(has(r, "Welcome, %s!", "fuzzy"))
        self.assertTrue(has(r, "%d result msgstr[1]", "missing %d", "error"))
        self.assertEqual(messages(r, "Order #%(id)s has shipped"), [])

    def test_html_breakage(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            page = (EX / "html" / "index.bn.html").read_text(encoding="utf-8")
            page = (page.replace('lang="bn"', 'lang="en"')
                        .replace('href="/privacy"', 'href="/privacy-bn"')
                        .replace("letter-spacing: 0;", "letter-spacing: 0.2em;")
                        .replace("ফ্রিতে শুরু করুন", "Get started for free"))
            t = tmp / "index.bn.html"
            t.write_text(page, encoding="utf-8")
            code, r = run("--source", EX / "html" / "index.en.html", "--target", t)
            self.assertEqual(code, 1)
            self.assertTrue(has(r, "index.bn.html", '<html lang="en">', "error"))
            self.assertTrue(has(r, "index.bn.html", "/privacy-bn", "error"))
            self.assertTrue(any("letter-spacing: 0.2em" in m for m in messages(r)))
        finally:
            shutil.rmtree(tmp)

    def test_html_untranslated_text_when_aligned(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            page = (EX / "html" / "index.bn.html").read_text(encoding="utf-8")
            t = tmp / "index.bn.html"
            t.write_text(page.replace("ফ্রিতে শুরু করুন", "Get started for free"), encoding="utf-8")
            _, r = run("--source", EX / "html" / "index.en.html", "--target", t)
            self.assertTrue(any("identical to the source" in m for m in messages(r)))
        finally:
            shutil.rmtree(tmp)

    def test_target_only_skips_code_fences(self):
        tmp = Path(tempfile.mkdtemp())
        try:
            md = tmp / "bn.md"
            md.write_text("# শুরু করুন\n\n```bash\necho 'ডেলিভারী |'\n```\n\nআপনার কার্ট খালি |\n", encoding="utf-8")
            _, r = run("--target-only", md)
            self.assertEqual(r["errors"], 1)
            self.assertTrue(has(r, "bn.md:7", "pipe"))
        finally:
            shutil.rmtree(tmp)


class BengaliChecks(TempDir):
    def check(self, text, **opts):
        found = []
        o = type("O", (), {"digits": opts.get("digits", "any"), "tone": opts.get("tone", "apni")})
        bn_lint.check_bengali(text, o, lambda sev, msg: found.append((sev, msg)))
        return found

    def test_voice_detection(self):
        self.assertEqual(self.check("নতুন অফার দেখুন"), [])            # নতুন is not a verb
        self.assertEqual(self.check("কেন আপনি এটা চান?"), [])
        self.assertTrue(any("informal" in m for _, m in self.check("তুমি কি ভুলে গেছো?")))
        self.assertTrue(any("informal" in m for _, m in self.check("এখনই কিনে নাও, বেছে নাও আর পারো")))
        self.assertTrue(any(s == "error" for s, _ in self.check("আপনার অর্ডার দেখো")))
        self.assertTrue(any("formal" in m for _, m in self.check("আপনি পারবেন", tone="tumi")))

    def test_unicode_problems(self):
        self.assertTrue(any("decomposed" in m for _, m in self.check("অর্ডার পোছেছে")))
        self.assertTrue(any("reph" in m for _, m in self.check("র্যাংকিং")))
        self.assertEqual([m for _, m in self.check("র‍্যাংকিং") if "reph" in m], [])
        self.assertTrue(any("Devanagari" in m for _, m in self.check("আপনার नाम")))
        self.assertTrue(any("legacy-font" in m for _, m in self.check("Avcbvi AW©vi ÔÕÖ")))

    def test_digits_policy(self):
        self.assertTrue(any("Latin digits" in m for _, m in self.check("মোট 500 টাকা", digits="bn")))
        self.assertEqual(self.check("কোড ABC123 লিখুন", digits="bn"), [])
        self.assertEqual(self.check("ফোন করুন +8801712345678", digits="bn"), [])
        self.assertTrue(any("policy is Latin" in m for _, m in self.check("মোট ৫০০ টাকা", digits="latn")))

    def test_sense_traps_are_context_aware(self):
        _, r = self.pair({"a": "Save 20% today"}, {"a": "আজ ২০% সংরক্ষণ করুন"})
        self.assertTrue(has(r, "a", "a discount"))
        _, r = self.pair({"a": "Save 10 hours a week"}, {"a": "সপ্তাহে ১০ ঘণ্টা সময় বাঁচান"})
        self.assertEqual(messages(r, "a"), [])

    def test_over_translation_of_everyday_english_words(self):
        cases = [
            ("Open map", "মানচিত্র খুলুন", "ম্যাপ"),
            ("Log in", "প্রবেশ করুন", "লগইন"),
            ("Make payment", "অর্থপ্রদান করুন", "পেমেন্ট"),
            ("Free delivery", "ফ্রি বিতরণ", "ডেলিভারি"),
            ("Install the app", "অ্যাপটি স্থাপন করুন", "ইনস্টল"),
            ("Special offer", "বিশেষ প্রস্তাব", "অফার"),
            ("Update now", "এখনই হালনাগাদ করুন", "আপডেট"),
            ("Book now", "এখনই সংরক্ষণ করুন", "বুক"),
        ]
        for en, bn, said in cases:
            _, r = self.pair({"a": en}, {"a": bn})
            self.assertTrue(any(said in m for m in messages(r, "a")), (en, r["findings"]))

    def test_natural_translations_are_not_flagged(self):
        ok = [
            ("Open map", "ম্যাপ খুলুন"),
            ("Log in", "লগইন করুন"),
            ("Your location", "আপনার অবস্থান"),            # either works
            ("Notifications", "বিজ্ঞপ্তি"),                # either works
            ("Search", "খুঁজুন"),                          # translate bucket
            ("Save your work", "আপনার কাজ সংরক্ষণ করুন"),   # save data, not a booking
            ("Delivery address", "ডেলিভারির ঠিকানা"),
        ]
        for en, bn in ok:
            _, r = self.pair({"a": en}, {"a": bn})
            self.assertEqual(messages(r, "a"), [], (en, bn))

    def test_glossary_can_choose_the_bengali_word(self):
        g = self.write("g.json", json.dumps({"update": "হালনাগাদ"}, ensure_ascii=False))
        _, r = self.pair({"a": "Update now"}, {"a": "এখনই হালনাগাদ করুন"}, "--glossary", g)
        self.assertEqual(messages(r, "a"), [])

    def test_bookish_words_flagged_even_without_source(self):
        self.assertTrue(any("ব্লুটুথ" in m for _, m in self.check("নীলদন্ত চালু করুন")))

    def test_css_checks(self):
        found = []
        bn_lint.check_css("p { letter-spacing: 0; line-height: 1.6 }", lambda s, m: found.append(m))
        self.assertEqual(found, [])
        bn_lint.check_css(".x { letter-spacing: .1em; line-height: 1.1; }", lambda s, m: found.append(m))
        self.assertEqual(len(found), 2)

    def test_glossary(self):
        g = self.write("g.json", json.dumps({"terms": {"checkout": "চেকআউট", "_note": "x"}}, ensure_ascii=False))
        _, r = self.pair({"a": "Go to checkout"}, {"a": "পেমেন্টে যান"}, "--glossary", g)
        self.assertTrue(has(r, "a", "glossary: 'checkout'"))
        _, r = self.pair({"a": "Go to checkout"}, {"a": "চেকআউটে যান"}, "--glossary", g)
        self.assertEqual(messages(r, "a"), [])

    def test_bengali_plural_keys(self):
        src = {"k_one": "{{count}} item", "k_other": "{{count}} items", "k_few": "{{count}} items"}
        tgt = {"k_one": "{{count}}টি আইটেম", "k_other": "{{count}}টি আইটেম"}
        code, r = self.pair(src, tgt)
        self.assertEqual(code, 0, r["findings"])


class Fixer(TempDir):
    def test_fix_json(self):
        t = self.tmp / "bn.json"
        shutil.copy(FIX / "fix" / "bn.fixme.json", t)
        s = self.write("en.json", json.dumps({
            "cart": {"empty": "Your cart is empty", "count": "You have 3 items in your cart.",
                     "free": "Free delivery on orders over ৳1,000",
                     "link": "Read the <a href=\"/terms-2024\">terms</a> {count}"},
            "notice": "This is urgent. Try again. Today",
            "brand": "Version 2.4 of Taskly"}))
        code, r = run("--source", s, "--target", t, "--fix", "--digits", "bn")
        data = json.loads(t.read_text(encoding="utf-8"))
        self.assertEqual(data["cart"]["empty"], "আপনার কার্ট খালি।")
        self.assertEqual(data["cart"]["count"], "আপনার কার্টে ৩টি আইটেম আছে।")
        self.assertEqual(data["cart"]["free"], "৳১,০০০ এর বেশি অর্ডারে ফ্রি ডেলিভারি")
        self.assertEqual(data["cart"]["link"], '<a href="/terms-2024">শর্তাবলি</a> পড়ুন {count}')
        self.assertEqual(data["notice"], "এটা জরুরি। আবার চেষ্টা করুন। আজই")
        self.assertEqual(data["brand"], "Version 2.4 of Taskly")
        self.assertGreaterEqual(len(r["fixed"]), 8)
        self.assertEqual(r["errors"], 0, r["findings"])
        self.assertTrue(t.read_text(encoding="utf-8").startswith('{\n  "cart"'))   # indent kept

    def test_fix_is_idempotent(self):
        t = self.tmp / "bn.json"
        shutil.copy(FIX / "fix" / "bn.fixme.json", t)
        run("--target-only", t, "--fix", "--digits", "bn")
        first = t.read_text(encoding="utf-8")
        _, r = run("--target-only", t, "--fix", "--digits", "bn")
        self.assertEqual(r["fixed"], [])
        self.assertEqual(t.read_text(encoding="utf-8"), first)

    def test_fix_composes_vowel_signs(self):
        t = self.write("bn.json", json.dumps({"a": "অর্ডার পোছেছে"}, ensure_ascii=False))
        s = self.write("en.json", json.dumps({"a": "Order arrived"}))
        _, r = run("--source", s, "--target", t, "--fix")
        self.assertEqual(json.loads(t.read_text(encoding="utf-8"))["a"], "অর্ডার পোছেছে")
        self.assertEqual(r["errors"], 0, r["findings"])

    def test_fix_po_leaves_msgid_and_plural_index(self):
        t = self.write("bn.po", 'msgid "Save 20 items"\nmsgstr "20 টি আইটেম সেভ করুন"\n\n'
                                'msgid "%d file"\nmsgid_plural "%d files"\nmsgstr[0] "%dটি ফাইল"\n'
                                'msgstr[1] "%dটি ফাইল"\n')
        run("--target", t, "--fix", "--digits", "bn")
        text = t.read_text(encoding="utf-8")
        self.assertIn('msgid "Save 20 items"', text)
        self.assertIn('msgstr "২০টি আইটেম সেভ করুন"', text)
        self.assertIn("msgstr[0]", text)
        self.assertIn("msgstr[1]", text)

    def test_fix_strings_leaves_keys(self):
        t = self.write("bn.strings", '"step_2_title" = "ধাপ 2 |";\n')
        s = self.write("en.strings", '"step_2_title" = "Step 2";\n')
        run("--source", s, "--target", t, "--fix", "--digits", "bn")
        self.assertEqual(t.read_text(encoding="utf-8"), '"step_2_title" = "ধাপ ২।";\n')

    def test_fix_never_touches_placeholders_or_urls(self):
        t = self.write("bn.json", json.dumps(
            {"a": "{count, plural, =0 {কিছু নেই} other {#টি}} দেখুন https://x.io/a1 %1$s ৩ টি"}, ensure_ascii=False))
        run("--target-only", t, "--fix", "--digits", "bn")
        self.assertEqual(json.loads(t.read_text(encoding="utf-8"))["a"],
                         "{count, plural, =0 {কিছু নেই} other {#টি}} দেখুন https://x.io/a1 %1$s ৩টি")


class Packaging(unittest.TestCase):
    def test_manifests_are_valid_and_consistent(self):
        market = json.loads((ROOT / ".claude-plugin" / "marketplace.json").read_text(encoding="utf-8"))
        plugin = json.loads((ROOT / "plugins" / "bengali-l10n" / ".claude-plugin" / "plugin.json")
                            .read_text(encoding="utf-8"))
        self.assertEqual(market["plugins"][0]["name"], plugin["name"])
        self.assertTrue((ROOT / market["plugins"][0]["source"]).is_dir())
        self.assertEqual(plugin["version"], bn_lint.__version__)

    def test_skill_frontmatter(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        self.assertTrue(text.startswith("---\nname: translate-to-bengali\ndescription: "))
        desc = text.split("description: ", 1)[1].split("\n---", 1)[0]
        self.assertLessEqual(len(desc), 1024)

    def test_every_json_file_parses(self):
        for p in ROOT.rglob("*.json"):
            if "bad" in p.name or ".git" in p.parts:
                continue
            json.loads(p.read_text(encoding="utf-8"))

    def test_referenced_files_exist(self):
        text = (SKILL / "SKILL.md").read_text(encoding="utf-8")
        import re
        for ref in set(re.findall(r"`((?:references|scripts|assets)/[\w./-]+)`", text)):
            self.assertTrue((SKILL / ref).exists(), ref)


if __name__ == "__main__":
    unittest.main()
