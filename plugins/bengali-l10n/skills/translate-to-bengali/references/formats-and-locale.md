# Numbers, money, dates and locale differences

Wherever the site formats values in code, prefer the platform's locale support
(`Intl.NumberFormat('bn-BD')`, `Intl.DateTimeFormat('bn-BD')`, ICU) over
hand-written strings. The rules below are for static text and for checking that
the code's output is right.

## Contents

1. Digits
2. Large numbers: lakh and crore
3. Currency
4. Percent, ranges, decimals
5. Dates
6. Time
7. Phone numbers and addresses
8. Units
9. bn-BD vs bn-IN

## 1. Digits

Bengali has its own digits: ০ ১ ২ ৩ ৪ ৫ ৬ ৭ ৮ ৯.

| Where | Digits |
|---|---|
| Running text, headings, prices, counts, dates, times, percentages, statistics | Bengali (default) |
| Hotline and phone numbers shown as text | Bengali is common in Bangladesh; Latin is also fine. Follow the site. The `tel:` link always uses Latin digits. |
| Order IDs, coupon codes, OTP samples, tracking numbers, card and account numbers, version numbers, URLs, emails, model numbers (iPhone 15), code | Latin, always |
| Form inputs and their example values | Latin (users type Latin digits; validation expects them) |
| Numbers that are part of a brand or product name | As the brand writes them |

Rules that always hold:

- Never mix the two systems inside one number (`১2৩`) and avoid mixing them for
  the same kind of value on one page.
- Some clients want Latin digits everywhere (fintech dashboards, B2B tools).
  That is a legitimate house style; apply it consistently and run the linter
  with `--digits latn`.
- A placeholder such as `{count}` gets whatever the code supplies. If the
  surrounding static text uses Bengali digits, tell the developer to format the
  value with `Intl.NumberFormat('bn-BD')`.

## 2. Large numbers: lakh and crore

South Asian grouping: the last three digits, then groups of two.

| Value | Bengali | In words |
|---|---|---|
| 1,000 | ১,০০০ | ১ হাজার |
| 100,000 | ১,০০,০০০ | ১ লাখ |
| 1,000,000 (1 million) | ১০,০০,০০০ | ১০ লাখ |
| 10,000,000 (10 million) | ১,০০,০০,০০০ | ১ কোটি |
| 1,000,000,000 (1 billion) | ১,০০,০০,০০,০০০ | ১০০ কোটি |

- Convert million/billion to লাখ/কোটি in consumer copy: "2.5 million users" →
  "২৫ লাখ ব্যবহারকারী"; "$3 billion" → "৩০০ কোটি ডলার". মিলিয়ন/বিলিয়ন appear in
  financial journalism and are acceptable for a finance audience.
- "10K+", "1.2M" → "১০ হাজার+", "১২ লাখ". Do not carry K/M over.
- Bangladesh says লাখ (লক্ষ is formal); West Bengal prefers লক্ষ.
- Check the arithmetic when converting. This is a common source of real errors.

## 3. Currency

| | Bangladesh | India |
|---|---|---|
| Name | টাকা | টাকা (the rupee is called টাকা in Bengali) |
| Symbol | ৳ (U+09F3) | ₹ |
| Code | BDT | INR |

- Symbol before the amount, no space: ৳১,২৫০. Or the amount followed by the
  word: ১,২৫০ টাকা. Not "টাকা ১২৫০", not "১২৫০ BDT" in consumer copy, and not
  both symbol and word together.
- "Tk" / "Tk." → ৳ or টাকা.
- Never convert an amount between currencies. "$49/month" stays 49 dollars:
  "$৪৯/মাস" or "মাসে ৪৯ ডলার".
- Decimals: ৳৯৯.৫০. Whole amounts need no ".00" unless the source shows it.
- "per month" → "/মাস" in price tags, "প্রতি মাসে" in sentences.

## 4. Percent, ranges, decimals

- Percent: ২০% (no space). "20% off" → "২০% ছাড়".
- Decimal point is `.`, grouping separator is `,`.
- Ranges: ১০-২০ or "১০ থেকে ২০". "Up to 50%" → "৫০% পর্যন্ত".
- "2x faster" → "দ্বিগুণ দ্রুত" (৩ গুণ, ১০ গুণ).
- Fractions in prose: অর্ধেক (half), দেড় (1.5), আড়াই (2.5) read naturally
  ("দেড় ঘণ্টা"), but use digits in data.

## 5. Dates

- Order is day, month, year. Long: ১২ নভেম্বর ২০২৬. With weekday:
  বৃহস্পতিবার, ১২ নভেম্বর ২০২৬. Numeric: ১২/১১/২০২৬ (dd/mm/yyyy).
- Never keep the US order. "11/12/2026" in a US source is 12 November; convert
  deliberately and, if the source is ambiguous, prefer the long form.
- No ordinal suffix is needed: "1st January" → "১ জানুয়ারি".

Months: জানুয়ারি, ফেব্রুয়ারি, মার্চ, এপ্রিল, মে, জুন, জুলাই, আগস্ট, সেপ্টেম্বর,
অক্টোবর, নভেম্বর, ডিসেম্বর.

Weekdays: রবিবার, সোমবার, মঙ্গলবার, বুধবার, বৃহস্পতিবার, শুক্রবার, শনিবার.
Short: রবি, সোম, মঙ্গল, বুধ, বৃহঃ, শুক্র, শনি.

- Bangladesh: the weekend is Friday and Saturday and the working week starts on
  Sunday. "Mon-Fri, 9-5" business hours in the source must not be "localized"
  into different days; translate what the business actually states, and flag it
  if it looks like an unedited template.
- Relative dates: আজ, গতকাল, আগামীকাল, ৩ দিন আগে, ২ সপ্তাহ পর, গত মাসে.
- The Bengali calendar (বঙ্গাব্দ: ১ বৈশাখ ১৪৩৩) is used for cultural occasions,
  not for ordinary site dates. Do not convert Gregorian dates to it.

## 6. Time

- Everyday Bengali uses the 12-hour clock with a part-of-day word before the
  time: সকাল ৯টা, দুপুর ১২টা, বিকেল ৪:৩০, সন্ধ্যা ৭টা, রাত ১০টা.
  Rough boundaries: ভোর 4-6, সকাল 6-12, দুপুর 12-3, বিকেল 3-6, সন্ধ্যা 6-8,
  রাত 8-4.
- Compact UI (tables, pickers) may keep "৯:৩০ AM" / "9:30 PM"; that is what
  `Intl` produces for `bn`. পূর্বাহ্ণ/অপরাহ্ণ are correct but bookish.
- "9 AM - 6 PM" → "সকাল ৯টা - সন্ধ্যা ৬টা".
- Durations: ৫ মিনিট, ২ ঘণ্টা ৩০ মিনিট, ৩ দিন. "24/7" → "২৪ ঘণ্টা, সপ্তাহে ৭ দিন"
  or "২৪/৭".
- Time zone: Bangladesh Standard Time is BST (UTC+6) with no daylight saving;
  India is IST (UTC+5:30). Do not shift times unless asked.

## 7. Phone numbers and addresses

- Bangladesh mobile numbers have 11 digits: 01XXX-XXXXXX; international
  +880 1XXX-XXXXXX. Keep the source grouping; do not reformat real numbers.
- Example numbers in placeholders should look local (01712345678), not
  "(555) 123-4567".
- Address order runs small to large: বাসা/হোল্ডিং, রোড, এলাকা, থানা/উপজেলা,
  জেলা, পোস্ট কোড. Form labels: "State/Province" → বিভাগ or জেলা as the form
  really needs; "ZIP code" → পোস্ট কোড (India: পিন কোড); "City" → শহর.
- Name fields: many Bengali names do not split neatly into first/last. Translate
  "First name" / "Last name" as নামের প্রথম অংশ / নামের শেষ অংশ, and suggest
  a single "পুরো নাম" field to the developer where possible.

## 8. Units

- Written out: transliterate. কিলোমিটার, কেজি, গ্রাম, লিটার, মিটার, ইঞ্চি, ফুট.
- Everyday abbreviations have Bengali forms: কিমি, কেজি, মিলি, সেমি.
- Technical units stay Latin: MB, GB, Mbps, px, kWh, mAh, GHz.
- Do not convert between systems (miles to km, °F to °C) unless asked; if the
  source uses units unfamiliar to the audience, flag it.
- Land and gold have local units (শতাংশ, কাঠা, বিঘা, ভরি); use them only if the
  source does.

## 9. bn-BD vs bn-IN

The grammar is shared; vocabulary, spelling and conventions differ. Default to
Bangladesh unless told otherwise, and do not mix.

| Item | Bangladesh (bn-BD) | West Bengal, India (bn-IN) |
|---|---|---|
| email | ইমেইল | ইমেল |
| bank / link | ব্যাংক / লিংক | ব্যাঙ্ক / লিঙ্ক |
| 100,000 | লাখ | লক্ষ |
| service | সেবা / সার্ভিস | পরিষেবা |
| register | নিবন্ধন / রেজিস্ট্রেশন | নথিভুক্ত করুন / রেজিস্টার |
| customer | গ্রাহক / কাস্টমার | গ্রাহক / ক্রেতা |
| water | পানি | জল |
| invitation | দাওয়াত | নিমন্ত্রণ |
| bath | গোসল | স্নান |
| breakfast | নাস্তা | জলখাবার |
| salt | লবণ | নুন |
| meat | গোশত / মাংস | মাংস |
| aunt/uncle and other kin terms | খালা, ফুফু, চাচা, মামা | মাসি, পিসি, কাকা, মামা |
| holiday greeting | ঈদ মোবারক ; শুভ নববর্ষ | শুভ বিজয়া ; শুভ নববর্ষ |
| currency | ৳, টাকা (BDT) | ₹, টাকা (INR) |
| postal code | পোস্ট কোড | পিন কোড |
| admin regions | বিভাগ, জেলা, উপজেলা, থানা | রাজ্য, জেলা, ব্লক |
| mobile top-up | রিচার্জ / ফ্লেক্সিলোড | রিচার্জ |
| ID document | জাতীয় পরিচয়পত্র (NID) | আধার কার্ড |
| time zone | BST, UTC+6 | IST, UTC+5:30 |
| weekend | Friday-Saturday | Saturday-Sunday |
| HTML lang | `bn-BD` | `bn-IN` |

If one Bengali version must serve both audiences, choose neutral words where
they exist (গ্রাহক, মাংস, শুভ নববর্ষ), avoid region-marked ones, and say so in
the report.
