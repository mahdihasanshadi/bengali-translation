# Style and grammar for Bengali UI text

## Contents

1. Voice and register
2. Sentence construction
3. UI element conventions
4. Counting: classifiers and plurals
5. Suffixes on placeholders, numbers and Latin words
6. Punctuation and spacing
7. Spelling: frequent mistakes
8. Before and after

## 1. Voice and register

**Address the user as আপনি.** It is the respectful default for products, shops,
banks and services. Verb forms follow: করুন, দেখুন, লিখুন, দিন, নিন, যান, পাঠান,
করবেন, করেছেন, পারবেন.

| Pronoun | Imperative | Possessive | When |
|---|---|---|---|
| আপনি | করুন | আপনার | Default. Always safe. |
| তুমি | করো | তোমার | Only if the brand asks for an intimate, youthful voice (kids' apps, some games, some youth brands). |
| তুই | কর | তোর | Never in product copy. |

Mixing them ("আপনার অ্যাকাউন্টে লগইন করো") is the single most jarring error.
Third persons the user interacts with also get respectful forms:
"{name} মন্তব্য করেছেন", not "করেছে".

**Use চলিত (standard colloquial), never সাধু.**

| চলিত (use) | সাধু (do not use) |
|---|---|
| করুন, করবেন | করিবেন |
| হয়েছে | হইয়াছে |
| এটি, এই | ইহা |
| তার, তাদের | তাহার, তাহাদের |
| যদি … তাহলে | যদ্যপি … তথাপি |

**Prefer the everyday word.** Bengali has formal Sanskritic synonyms that make
UI text feel like a government notice.

| Stiff | Natural |
|---|---|
| প্রেরণ করুন | পাঠান |
| ক্রয় করুন | কিনুন |
| প্রদান করুন | দিন |
| গ্রহণ করুন | নিন |
| অবলোকন করুন | দেখুন |
| অনুগ্রহপূর্বক | (drop it, or অনুগ্রহ করে once) |
| সমূহ on every plural | plain noun, or সব … |
| উক্ত, উল্লিখিত | এই, ওপরের |
| নিমিত্তে | জন্য |
| ব্যতীত | ছাড়া |
| পূর্বে / পরবর্তীতে | আগে / পরে |

Formal sectors (government, banking, legal) may sit a notch more formal
(নির্বাচন করুন, সংরক্ষণ করুন, প্রদান করুন) but still চলিত and still plain.

## 2. Sentence construction

**Verb goes last; purpose and conditions come first.**

- "Click here to download the app" → "অ্যাপ ডাউনলোড করতে এখানে ক্লিক করুন"
- "You will receive an SMS when your order ships" →
  "আপনার অর্ডার পাঠানো হলে একটি SMS পাবেন"

**No articles.** Do not render "a/an/the" as একটি/টি by reflex. Use টি/টা only
when pointing at a specific thing ("এই ফাইলটি মুছে ফেলবেন?").

**Fewer pronouns.** Bengali drops subjects and repeated possessives.
"Enter your password to access your account" →
"অ্যাকাউন্টে ঢুকতে পাসওয়ার্ড লিখুন".

**"Please".** করুন is already polite. Add অনুগ্রহ করে or দয়া করে only where the
English is genuinely apologetic or asks a favour, and not twice on a screen.

**Avoid দ্বারা passives.** "Posted by {name}" → "পোস্ট করেছেন {name}" or
"{name}-এর পোস্ট"; "Powered by X" → "X-এর সৌজন্যে" or leave as branding.
Bengali's natural passive is করা হয়েছে: "Your order has been cancelled" →
"আপনার অর্ডারটি বাতিল করা হয়েছে".

**Questions.** Yes/no questions use কি; "what/which" questions use কী.
"আপনি কি নিশ্চিত?" but "আপনি কী খুঁজছেন?". "Which" is কোন (কোন ঠিকানায়
পাঠাব?); "any" is কোনো (কোনো সমস্যা হলে জানান).

**Possibility and permission.** "You can…" → "…করতে পারবেন / পারেন".
"You cannot…" → "…করা যাবে না" (impersonal is softer than "আপনি পারবেন না").

**Negation.** না follows the verb as a separate word (করবেন না); নি attaches
(পাওয়া যায়নি, করেননি); নেই stands alone (অ্যাকাউন্ট নেই).

**Gender.** Bengali pronouns and verbs are not gendered; "he or she" is তিনি.
Do not introduce gender that English did not have.

## 3. UI element conventions

Keep each element type consistent across the site.

| Element | Form | Example |
|---|---|---|
| Buttons, links that act | Polite imperative, short | সেভ করুন, পাঠান, এখনই কিনুন |
| One-word buttons where space is tight | Noun/adjective form is fine | বাতিল, পরবর্তী, ঠিক আছে |
| Menu and nav items, tabs | Noun phrase | হোম, পণ্য, আমাদের সম্পর্কে, যোগাযোগ |
| Headings | Noun phrase or short sentence, no full stop | আপনার অর্ডারসমূহ → better: আপনার অর্ডার |
| Form labels | Noun, no colon needed unless source has one | নাম, মোবাইল নম্বর |
| Input placeholders | Instruction or example | আপনার নাম লিখুন ; যেমন: 01712345678 |
| In-progress status | …হচ্ছে… | আপলোড হচ্ছে… |
| Completed status | …হয়েছে | আপলোড হয়েছে |
| Errors | What happened + what to do, no blame | পাসওয়ার্ডটি ভুল। আবার চেষ্টা করুন। |
| Confirmations | Question with কি | আপনি কি এই ছবিটি মুছে ফেলতে চান? |
| Toggle states | চালু / বন্ধ | নোটিফিকেশন চালু |
| Empty states | Plain statement + next step | এখনো কোনো অর্ডার নেই। কেনাকাটা শুরু করুন। |

Bengali has no capital letters. Emphasis that English shows with Title Case or
ALL CAPS must come from the design (weight, size, colour), not the text.

## 4. Counting: classifiers and plurals

**After a number, the noun stays singular and the number takes a classifier.**

| English | Bengali | Note |
|---|---|---|
| 3 items | ৩টি আইটেম | টি for things (টা is more casual) |
| 5 users | ৫ জন ব্যবহারকারী | জন for people |
| 2 files selected | ২টি ফাইল বেছে নেওয়া হয়েছে | |
| 10 days | ১০ দিন | units of time, money, measure take no classifier |
| 500 taka | ৫০০ টাকা | |
| 3 kg | ৩ কেজি | |

Never combine a number with a plural suffix: "৩টি আইটেমগুলো" is wrong.

**Plurals without numbers.** Bengali often leaves the plural unmarked.
"Products" (menu) → পণ্য; "All products" → সব পণ্য; "Your orders" → আপনার
অর্ডার. Use গুলো/গুলি for definite things ("এই ফাইলগুলো"), রা/দের for people
(ব্যবহারকারীরা, গ্রাহকদের). সমূহ is formal; use it sparingly.

**ICU / i18n plural forms.** CLDR gives Bengali two cardinal categories: `one`
(0 and 1) and `other`. Because the noun does not change after a number, both
forms are usually the same text. Keep every category key the source file or
framework requires, and always keep `other`.

```
EN: {count, plural, one {# item} other {# items}}
BN: {count, plural, one {#টি আইটেম} other {#টি আইটেম}}
```

`=0` cases deserve their own wording: `=0 {কোনো আইটেম নেই}`.

**Ordinals are irregular** (১ম, ২য়, ৩য়, ৪র্থ, ৫ম, ৬ষ্ঠ, ৭ম …), so do not
build them from a placeholder plus a fixed suffix. Rewrite instead:
"Step {n}" → "ধাপ {n}"; "{n}th place" → "{n} নম্বর স্থান".

## 5. Suffixes on placeholders, numbers and Latin words

Bengali marks case with suffixes whose spelling depends on the word's last
sound: রহিমের but ঢাকার; ঘরে but ঢাকায়. A placeholder's value is unknown, so a
bare suffix can produce a wrong form.

Safe patterns:

| Need | Pattern | Example |
|---|---|---|
| Possessive | hyphen + এর | {name}-এর প্রোফাইল ; Google-এর সেবা |
| "to / for" | hyphen + কে, or restructure | {name}-কে পাঠান ; প্রাপক: {name} |
| "in / at" | hyphen + এ / তে | {city}-তে ডেলিভারি ; PDF-এ সেভ করুন |
| Count | number + টি / জন directly | {count}টি পণ্য ; {count} জন |
| Avoid the suffix | label style | অর্ডার নম্বর: {id} |

- With Bengali digits the suffix attaches directly: ১০টি, ৫ জন, ২০%-এর বেশি.
- Do not put a space inside "{count}টি"; do put a space before জন.
- Greeting with a name: "Hi {name}," → "প্রিয় {name}," (email) or
  "হ্যালো {name}," / "স্বাগতম, {name}" (app). Avoid "{name} সাহেব" style guesses
  about gender or status.
- Move placeholders freely to fit Bengali order, but keep every one, exactly as
  written, including numbered ones (`%1$s`, `{0}`).

## 6. Punctuation and spacing

| Mark | Rule |
|---|---|
| Full stop | দাঁড়ি `।` (U+0964). Not a period, not the pipe/vertical-bar character (U+007C). |
| ? ! , ; | Same as English. |
| Colon | Ordinary `:`. Never the visarga `ঃ` (নাম: not নামঃ). |
| Quotes | Curly “ ” (and ‘ ’ inside). Keep straight quotes where the file format needs them. |
| Ellipsis | `…` or `...`, matching the source. |
| Abbreviation point | Ordinary period: ডা., মো., লি. |
| Dash/hyphen | As in English; hyphen joins suffixes to Latin text and placeholders. |

- No space before `।`, `,`, `?`, `!`, `:`; one space after.
- No দাঁড়ি on buttons, labels, headings or menu items.
- After a number or Latin text, দাঁড়ি can be mistaken for the digit 1 or a
  bar; if a sentence ends in a Latin-digit number, reword so that it does not.
- Keep the source's line breaks and paragraphing.

## 7. Spelling: frequent mistakes

Bangla Academy প্রমিত বানান. The left column is correct.

| Correct | Wrong | Why |
|---|---|---|
| তৈরি, জরুরি, সরকারি, বেশি, দেরি, খুশি, দামি | তৈরী, জরুরী, সরকারী, বেশী, দেরী, খুশী, দামী | non-তৎসম words take ি |
| শ্রেণি, সূচি, শর্তাবলি, পদ্ধতি | শ্রেণী, সূচী, শর্তাবলী | current Academy spelling |
| ব্যবহারকারী, আবেদনকারী, সহকারী | ব্যবহারকারি | person-marker কারী keeps ী |
| পুরস্কার, পরিষ্কার, নিষ্ক্রিয় | পুরষ্কার, পরিস্কার | স্ক vs ষ্ক depends on the word |
| ধরন, কারণ, পরিমাণ, বিবরণ | ধরণ, কারন, পরিমান, বিবরন | ধরন is ন; the others are ণ |
| কোনো (any) / কোন (which) | কোন for both | |
| কী (what) / কি (yes-no) | কি for both | |
| আরও, এখনো / এখনও, কখনো | আরো mixed with আরও in one site | pick one and stay consistent |
| স্বাগতম, ধন্যবাদ, অভিনন্দন | সাগতম, ধন্যবাদ্ | |
| মুহূর্ত, দূর, পূরণ, মূল্য | মুহুর্ত, দুর, পুরণ, মুল্য | |
| লক্ষ করুন (notice) / লক্ষ্য (goal) | লক্ষ্য করুন | |
| উপলক্ষ্যে, কাঙ্ক্ষিত, আকাঙ্ক্ষা | উপলক্ষে is also accepted; কাঙ্খিত is wrong | |
| যায়নি, হয়নি, করেননি | যায় নি, হয় নি | নি attaches |
| গোপনীয়তা, নিরাপত্তা, প্রয়োজনীয় | গোপনিয়তা, নিরাপত্ত্বা | |
| ইতিমধ্যে / ইতোমধ্যে | ইতিমধ্য | |
| বাংলা, বাংলাদেশ | বাঙলা, বাঙ্গালাদেশ | |
| ঈদ, ইংরেজি, ইসলামি | ইদ (unfamiliar to users), ইংরেজী | |

## 8. Before and after

| English | Literal / machine | Natural |
|---|---|---|
| Sign up for free | বিনামূল্যে জন্য সাইন আপ করুন | ফ্রি সাইন আপ করুন |
| Your order has been placed successfully. | আপনার আদেশ সফলভাবে স্থাপন করা হয়েছে। | আপনার অর্ডারটি সফলভাবে সম্পন্ন হয়েছে। |
| Please enter a valid phone number. | অনুগ্রহ করে একটি বৈধ ফোন নম্বর প্রবেশ করান। | সঠিক ফোন নম্বর লিখুন। |
| We'll get back to you within 24 hours. | আমরা ২৪ ঘণ্টার মধ্যে আপনার কাছে ফিরে আসব। | ২৪ ঘণ্টার মধ্যে আমরা আপনার সঙ্গে যোগাযোগ করব। |
| Free shipping on orders over ৳1,000 | ৳১,০০০ এর উপরে আদেশে বিনামূল্যে শিপিং | ৳১,০০০-এর বেশি অর্ডারে ফ্রি ডেলিভারি |
| Are you sure you want to delete this? | আপনি কি নিশ্চিত যে আপনি এটি মুছে ফেলতে চান? | আপনি কি এটি মুছে ফেলতে চান? |
| Welcome to our store! | আমাদের দোকানে আপনাকে স্বাগতম! | আমাদের স্টোরে স্বাগতম! |
| You have 3 new messages | আপনার ৩ নতুন বার্তাগুলি আছে | আপনার ৩টি নতুন মেসেজ এসেছে |
| Don't miss out! | মিস করবেন না আউট! | সুযোগটি হাতছাড়া করবেন না! |
| We use cookies to improve your experience. | আমরা আপনার অভিজ্ঞতা উন্নত করতে বিস্কুট ব্যবহার করি। | আপনাকে আরও ভালো সেবা দিতে আমরা কুকি ব্যবহার করি। |
| Last updated 2 days ago | শেষ আপডেট ২ দিন আগে | সর্বশেষ আপডেট: ২ দিন আগে |
| Sold out | বিক্রি হয়ে গেছে আউট | স্টক শেষ |
| Back to top | উপরে ফিরে যান পিঠ | ওপরে যান |
| Powered by Acme | Acme দ্বারা চালিত | Acme-এর সৌজন্যে |
