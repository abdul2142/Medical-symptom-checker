import re
from dataclasses import dataclass, field
from urllib.parse import quote_plus

from rapidfuzz import fuzz

from medical_data import (
    ABDOMEN_PARTS, AIRWAY_PARTS, BLUE_PARTS, BODY_PART_PAIN, CONDITION_GUIDANCE, CONTEXT_TERMS, DESCRIPTORS,
    FLAG_LABELS, LEG_PARTS, MILD_WORDS, MODERATE_WORDS, OK_WORDS, RED_FLAG_PHRASES, RISK_FACTOR_TERMS,
    RISK_FACTORS, SERIOUS_CONCERN_PHRASES, SEVERE_WORDS, STOPWORDS, SUDDEN_WORDS, SYMPTOM_MIN_STATUS,
    SYMPTOM_RED_FLAGS, SYMPTOMS_BY_SYSTEM, WORSENING_PHRASES,
)

DISCLAIMER = (
    "Educational mock only. This tool does not diagnose, prescribe, recommend dosage "
    "changes, or replace a qualified healthcare professional. Seek urgent medical help "
    "for emergency symptoms."
)

SYMPTOM_VOCABULARY = {name: phrases for group in SYMPTOMS_BY_SYSTEM.values() for name, phrases in group.items()}
SYMPTOM_SYSTEM = {name: system for system, group in SYMPTOMS_BY_SYSTEM.items() for name in group}

AGE_GROUPS = ["Not specified", "Infant (under 1)", "Child", "Teen", "Adult", "Older adult"]
DURATIONS = ["Not specified", "Today", "1–3 days", "4–7 days", "More than 1 week"]
SEVERITIES = ["Mild", "Moderate", "Severe"]
PERSISTENT_DURATIONS = {"4–7 days", "More than 1 week"}

# status -> (level, doctor need, where to get care, how soon)
DISPOSITION = {
    "urgent": ("Emergency", "YES — seek emergency medical help now", "Emergency services or emergency department", "Now"),
    "prompt": ("High", "YES — see a healthcare professional today", "Same-day doctor or urgent care", "Within 24 hours"),
    "consider": ("Moderate", "CONSIDER — get advice if not improving", "Pharmacist or doctor (GP)", "If not improving in 2–3 days"),
    "monitor": ("Low", "NOT ALWAYS — self-care and monitor", "Self-care at home", "Review if not better in 7 days"),
}
STATUS_ORDER = ["monitor", "consider", "prompt", "urgent"]

NEXT_STEP = {
    "urgent": "Call local emergency services or go to the nearest emergency department now. Do not drive yourself if you feel faint or unwell.",
    "prompt": "Contact a doctor or urgent-care service today. Use emergency services if symptoms become sudden, severe, or affect breathing, consciousness, or movement.",
    "consider": "Monitor how symptoms change and speak to a pharmacist or doctor if they persist, worsen, or worry you.",
    "monitor": "Self-care is usually appropriate. Contact a professional if symptoms persist, worsen, or concern you.",
}
SELF_HARM_STEP = (
    "You deserve support right now. Call your local emergency number or a crisis line "
    "(e.g. 988 in the US, 116 123 Samaritans in the UK & Ireland), or go to an emergency department. "
    "If you can, tell someone you trust how you are feeling."
)
REVIEW_AFTER = {"consider": "No improvement after 2–3 days", "monitor": "No improvement after 7 days"}
GENERAL_SAFETY_NET = [
    "Chest pain, difficulty breathing, fainting or new confusion",
    "Symptoms getting rapidly worse, or new severe pain",
]

# ---------- Text matching ----------

TOKEN_RE = re.compile(r"[a-z0-9]+(?:['-][a-z0-9]+)*")
CLAUSE_BREAK = re.compile(r"[.,;:!?]|\b(?:but|however|although|though|except|yet|and|whereas)\b")
BODY_CLAUSE_BREAK = re.compile(r"[.;:!?]|\b(?:but|however|although|though|whereas)\b")
NEGATION_CUE = re.compile(
    r"\b(?:no|not|without|denies|denied|never|negative for|free of|don't have|do not have|"
    r"doesn't have|haven't had|have not had|no sign of|no signs of)\b"
)
# "no improvement in my cough" does not deny the cough.
NOT_NEGATING = {"improvement", "better", "relief", "change", "help"}
NEGATION_WINDOW = 3
FUZZY_THRESHOLD = 90  # "fainting" vs "painting" scores 87.5 and must not match
BODY_PART_WINDOW = 5  # max tokens between "pain" and "abdomen" in "pain in my lower right abdomen"
INFERRED_SCORE = 95   # body-part matches are inferred rather than literal


def clean_text(text: str) -> str:
    text = text.lower().replace("’", "'").replace("°", " ° ").strip()
    return re.sub(r"\s+", " ", text)


def _singular(word: str) -> str:
    if len(word) > 4 and word.endswith("ies"):
        return word[:-3] + "y"
    if len(word) > 4 and word.endswith("es") and word[:-2].endswith(("ch", "sh", "x", "ss")):
        return word[:-2]
    if len(word) > 3 and word.endswith("s") and not word.endswith(("ss", "us", "is")):
        return word[:-1]
    return word


def _phrase_tokens(phrase: str):
    return tuple(_singular(t) for t in TOKEN_RE.findall(clean_text(phrase)))


@dataclass
class _Text:
    cleaned: str
    tokens: list = field(init=False)   # [(word, char_start)]
    used: set = field(default_factory=set)  # token indices explained by some rule

    def __post_init__(self):
        self.tokens = [(m.group(), m.start()) for m in TOKEN_RE.finditer(self.cleaned)]
        self.singular = [_singular(t) for t, _ in self.tokens]

    def mark_chars(self, start: int, end: int):
        self.used.update(i for i, (_, s) in enumerate(self.tokens) if start <= s < end)

    def negated(self, index: int) -> bool:
        prefix = self.cleaned[:self.tokens[index][1]]
        breaks = list(CLAUSE_BREAK.finditer(prefix))
        clause = prefix[breaks[-1].end():] if breaks else prefix
        cues = list(NEGATION_CUE.finditer(clause))
        if not cues:
            return False
        between = TOKEN_RE.findall(clause[cues[-1].end():])
        return len(between) <= NEGATION_WINDOW and not NOT_NEGATING.intersection(between)


def _compile(groups: dict):
    return {key: [_phrase_tokens(p) for p in phrases] for key, phrases in groups.items()}


SYMPTOM_PHRASES = _compile(SYMPTOM_VOCABULARY)
RED_FLAG_TOKENS = _compile(RED_FLAG_PHRASES)
SERIOUS_TOKENS = _compile({p: [p] for p in SERIOUS_CONCERN_PHRASES})
RISK_TOKENS = _compile(RISK_FACTOR_TERMS)
WORSENING_TOKENS = _compile({"worsening": WORSENING_PHRASES})
CONTEXT_TOKENS = _compile(CONTEXT_TERMS)


def _hits(compiled: dict, ctx: _Text):
    """Every phrase occurrence as (key, start_index, length, score, negated).

    Whole-token matching avoids "fits" matching "benefits"; plurals are folded to
    singular, and longer phrases tolerate small typos ("diarhea").
    """
    out = []
    words = ctx.singular
    for key, phrases in compiled.items():
        for target in phrases:
            n = len(target)
            for i in range(len(words) - n + 1):
                # Compare word by word so a typo is only forgiven inside a real word:
                # "swollen and" must not match "swollen gland".
                scores = []
                for word, want in zip(words[i:i + n], target):
                    if word == want:
                        scores.append(100)
                    elif len(want) >= 5 and abs(len(word) - len(want)) <= 2 \
                            and (s := fuzz.ratio(word, want)) >= FUZZY_THRESHOLD:
                        scores.append(s)
                    else:
                        break
                else:
                    out.append((key, i, n, round(sum(scores) / n), ctx.negated(i)))
    return out


def _collect(hits, ctx: _Text):
    """Fold hits into ({key: best affirmed score}, [keys only ever denied]) and mark tokens as understood."""
    affirmed, seen = {}, set()
    for key, i, n, score, negated in hits:
        ctx.used.update(range(i, i + n))
        seen.add(key)
        if not negated:
            affirmed[key] = max(affirmed.get(key, 0), score)
    return affirmed, [k for k in dict.fromkeys(k for k, *_ in hits) if k not in affirmed and k in seen]


def _body_part_hits(ctx: _Text, phrase_hits):
    """Find "<body part> ... <pain word>" within a clause, e.g. "pain in my left knee", "my ankles are swollen".

    Returns hits in the same shape as `_hits`, plus the descriptor indices they consumed.
    """
    # Tokens already explained by a multi-word phrase ("sore throat", "burning chest after eating") are left alone.
    locked = {j for _, i, n, *_ in phrase_hits if n > 1 for j in range(i, i + n)}
    clause_of = []
    for _, start in ctx.tokens:
        clause_of.append(len(BODY_CLAUSE_BREAK.findall(ctx.cleaned[:start])))
    kind_of = {w: kind for kind, words in DESCRIPTORS.items() for w in words}

    out, consumed = [], set()
    for b, part in enumerate(ctx.singular):
        if part not in BODY_PART_PAIN or b in locked:
            continue
        nearby = range(max(0, b - BODY_PART_WINDOW), min(len(ctx.tokens), b + BODY_PART_WINDOW + 1))
        same_clause = [d for d in nearby if d != b and clause_of[d] == clause_of[b]]
        candidates = [d for d in same_clause if d not in locked and ctx.tokens[d][0] in kind_of]
        if not candidates:
            if any(ctx.tokens[d][0] in OK_WORDS for d in same_clause):
                ctx.used.add(b)  # "my stomach is fine"
            continue
        d = min(candidates, key=lambda x: abs(x - b))
        kind = kind_of[ctx.tokens[d][0]]
        key = {
            "pain": BODY_PART_PAIN[part],
            "swell": "RF_SEVERE_ALLERGY" if part in AIRWAY_PARTS else "leg swelling" if part in LEG_PARTS else "swelling",
            "itch": "itchy eyes" if part == "eye" else "itching",
            "red": "red eyes" if part == "eye" else "skin redness",
            "numb": "numbness",
            "bleed": {"nose": "nosebleed", "gum": "toothache", "bottom": "rectal bleeding"}.get(part, "bleeding"),
            "stiff": "stiff neck" if part == "neck" else BODY_PART_PAIN[part],
            "weak": "weakness",
            "blue": "RF_BLUE_LIPS" if part in BLUE_PARTS else None,
        }[kind]
        if key is None:
            continue
        before = set(ctx.singular[max(0, b - 3):b])
        if kind == "pain" and part in ABDOMEN_PARTS and {"right", "lower"} <= before:
            key = "right lower abdominal pain"
            ctx.used.update(i for i in range(max(0, b - 3), b) if ctx.singular[i] in {"right", "lower"})
        first = min(b, d)
        out.append((key, first, 1, INFERRED_SCORE, ctx.negated(first)))
        # Other descriptors of the same body part ("sharp", "throbbing") are understood too.
        ctx.used.update({b, *[c for c in candidates if kind_of[ctx.tokens[c][0]] == kind]})
        consumed.add(d)
    return out, consumed


NUMBER_WORDS = {"a": 1, "an": 1, "one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7,
                "eight": 8, "nine": 9, "ten": 10, "few": 3, "couple of": 2, "several": 4}
UNIT_DAYS = {"hour": 0, "day": 1, "night": 1, "week": 7, "fortnight": 14, "month": 30, "year": 365}
DURATION_RE = re.compile(
    r"\b(\d+|" + "|".join(NUMBER_WORDS) + r")\s+(hour|day|night|week|fortnight|month|year)s?\b(?![- ]old)")
SINCE_RE = re.compile(r"\b(?:since|from)\s+(this morning|today|last night|yesterday|last week|last month)\b")
SINCE_DAYS = {"this morning": 0, "today": 0, "last night": 1, "yesterday": 1, "last week": 7, "last month": 30}
AGE_RE = re.compile(r"\b(\d{1,3})[- ]?(year|yr|month|week|day)s?[- ]old\b")
# "I'm 72, ..." / "aged 40" — but not "I am 5 days into this".
AGE_STATED_RE = re.compile(
    r"\b(?:i am|i'm|im|aged|age)\s+(\d{1,3})(?:\s*(?:years?|yrs?|yo|y/o))?"
    r"(?=\s*(?:[,.;!?]|$|and\b|with\b|male\b|female\b|man\b|woman\b|years?\b|yo\b))")
AGE_WORDS = {"baby": "Infant (under 1)", "newborn": "Infant (under 1)", "infant": "Infant (under 1)",
             "toddler": "Child", "child": "Child", "kid": "Child", "teenager": "Teen",
             "elderly": "Older adult", "grandmother": "Older adult", "grandfather": "Older adult"}
TEMP_RE = re.compile(r"\b(\d{2,3}(?:\.\d+)?)\s*(?:°\s*)?(?:degrees?\s*)?(celsius|fahrenheit|c|f)?\b")
TEMP_CONTEXT = {"temp", "temperature", "fever", "thermometer", "reading", "measured"}
PAIN_SCORE_RE = re.compile(r"\b(\d{1,2})\s*(?:/|out of)\s*10\b")


def _days_to_duration(days: float) -> str:
    if days < 1:
        return "Today"
    if days <= 3:
        return "1–3 days"
    if days <= 7:
        return "4–7 days"
    return "More than 1 week"


def _age_to_group(years: float) -> str:
    if years < 1:
        return "Infant (under 1)"
    if years < 13:
        return "Child"
    if years < 18:
        return "Teen"
    return "Adult" if years < 65 else "Older adult"


def _parse_duration(ctx: _Text):
    best = None
    for m in DURATION_RE.finditer(ctx.cleaned):
        n = int(m.group(1)) if m.group(1).isdigit() else NUMBER_WORDS[m.group(1)]
        days = n * UNIT_DAYS[m.group(2)]
        if best is None or days > best[0]:
            best = (days, m)
    for m in SINCE_RE.finditer(ctx.cleaned):
        days = SINCE_DAYS[m.group(1)]
        if best is None or days > best[0]:
            best = (days, m)
    if not best:
        return None
    ctx.mark_chars(*best[1].span())
    return _days_to_duration(best[0]), best[1].group(0)


def _parse_age(ctx: _Text):
    m = AGE_RE.search(ctx.cleaned)
    if m:
        ctx.mark_chars(*m.span())
        n, unit = int(m.group(1)), m.group(2)
        years = n if unit in {"year", "yr"} else n / 12 if unit == "month" else n / 52 if unit == "week" else n / 365
        return _age_to_group(years), m.group(0)
    m = AGE_STATED_RE.search(ctx.cleaned)
    if m and 0 < int(m.group(1)) < 120:
        ctx.mark_chars(*m.span())
        return _age_to_group(int(m.group(1))), m.group(0)
    for i, word in enumerate(ctx.singular):
        if word in AGE_WORDS:
            ctx.used.add(i)
            return AGE_WORDS[word], ctx.tokens[i][0]
    return None


def _parse_temperature(ctx: _Text):
    """Temperature in °C from text like "39.2C", "temp of 101 F" or "fever 38.5"."""
    for m in TEMP_RE.finditer(ctx.cleaned):
        value, unit = float(m.group(1)), (m.group(2) or "")[:1]
        before = TOKEN_RE.findall(ctx.cleaned[max(0, m.start() - 40):m.start()])[-4:]
        if not unit and not TEMP_CONTEXT.intersection(before):
            continue  # a bare number is only a temperature in context ("38 years old" is not)
        if unit == "f" or (not unit and 93 <= value <= 110):
            celsius = (value - 32) * 5 / 9
        elif unit == "c" or (not unit and 34 <= value <= 43):
            celsius = value
        else:
            continue
        if 30 <= celsius <= 45:
            ctx.mark_chars(*m.span())
            first = next(i for i, (_, s) in enumerate(ctx.tokens) if s >= m.start())
            ctx.used.update(i for i in range(max(0, first - 4), first) if ctx.tokens[i][0] in TEMP_CONTEXT)
            return round(celsius, 1)
    return None


def _parse_severity(ctx: _Text):
    found = []
    for m in PAIN_SCORE_RE.finditer(ctx.cleaned):
        score = int(m.group(1))
        if score <= 10:
            ctx.mark_chars(*m.span())
            found.append(("Severe" if score >= 7 else "Moderate" if score >= 4 else "Mild", m.group(0)))
    for i, word in enumerate(ctx.singular):
        level = "Severe" if word in SEVERE_WORDS else "Moderate" if word in MODERATE_WORDS else \
            "Mild" if word in MILD_WORDS else None
        if level:
            ctx.used.add(i)
            if not ctx.negated(i):
                found.append((level, ctx.tokens[i][0]))
    return max(found, key=lambda f: SEVERITIES.index(f[0])) if found else None


# ---------- Public helpers ----------

def normalize_symptoms(text: str):
    ctx = _Text(clean_text(text))
    phrase_hits = _hits(SYMPTOM_PHRASES, ctx)
    body_hits, consumed = _body_part_hits(ctx, phrase_hits)
    # A lone word ("swollen") gives way to a more specific reading of the same words:
    # a longer phrase ("swollen legs") or a body part ("my ankles are swollen").
    inside_longer = {j for _, i, n, *_ in phrase_hits if n > 1 for j in range(i, i + n)}
    phrase_hits = [h for h in phrase_hits if not (h[2] == 1 and (h[1] in consumed or h[1] in inside_longer))]
    found, denied = _collect(phrase_hits + [h for h in body_hits if not h[0].startswith("RF_")], ctx)
    return {
        "matched_symptoms": list(found),
        "confidence": {k: round(v / 100, 2) for k, v in found.items()},
        "denied_symptoms": denied,
        "_ctx": ctx, "_body_flags": [h for h in body_hits if h[0].startswith("RF_")],
    }


def screen_red_flags(text: str):
    """(affirmed red-flag ids, denied red-flag ids) from the description alone."""
    normalized = normalize_symptoms(text)
    return _red_flags(normalized, normalized["_ctx"])


def _red_flags(normalized, ctx: _Text):
    found, denied = _collect(_hits(RED_FLAG_TOKENS, ctx) + normalized["_body_flags"], ctx)
    flags = list(found)
    for symptom, flag in SYMPTOM_RED_FLAGS.items():
        if symptom in normalized["matched_symptoms"] and flag not in flags:
            flags.append(flag)
        elif symptom in normalized["denied_symptoms"] and flag not in denied:
            denied.append(flag)
    return flags, [f for f in denied if f not in flags]


def detect_red_flags(text: str):
    return screen_red_flags(text)[0]


def describe_flag(rule_id: str) -> str:
    return FLAG_LABELS.get(rule_id, rule_id.removeprefix("RF_").replace("_", " ").capitalize())


def infer_possible_conditions(matched_symptoms):
    """Rank patterns by how well they fit: both how much of the pattern is present and
    how much of the case the pattern explains (an F1-style score)."""
    matched = set(matched_symptoms)
    ranked = []
    for name, data in CONDITION_GUIDANCE.items():
        if not all(matched & group for group in data.get("requires", [])):
            continue
        overlap = matched & data["signals"]
        if len(overlap) < 2:
            continue
        precision = len(overlap) / len(data["signals"])
        recall = len(overlap) / len(matched)
        fit = 2 * precision * recall / (precision + recall)
        ranked.append((fit, len(overlap), name, data, overlap))
    ranked.sort(reverse=True, key=lambda x: (x[0], x[1]))
    return [
        {"name": name, "pattern_score": round(fit * 100), "matching_symptoms": sorted(overlap),
         "other_features": sorted(data["signals"] - overlap),
         "care": data["care"], "avoid": data["avoid"], "seek_help": data["seek_help"],
         "min_status": data.get("min_status")}
        for fit, _, name, data, overlap in ranked[:3]
    ]


def _pertinent_negatives(denied_symptoms, denied_flags, flags):
    labels = [describe_flag(f) for f in denied_flags if f not in flags]
    # "chest pain" is already covered by the "Chest pain or pressure" warning-sign label.
    extra = [s[0].upper() + s[1:] for s in denied_symptoms if not any(s in label.lower() for label in labels)]
    return labels + extra


# ---------- Triage ----------

def analyze_symptoms(text: str, age_group: str, duration: str, severity: str,
                     warning_signs=(), risk_factors=()):
    """Transparent educational triage rules; not a validated clinical score."""
    normalized = normalize_symptoms(text)
    ctx = normalized["_ctx"]
    flags, denied_flags = _red_flags(normalized, ctx)
    serious_found, _ = _collect(_hits(SERIOUS_TOKENS, ctx), ctx)
    serious_concerns = list(serious_found)
    risk_found, _ = _collect(_hits(RISK_TOKENS, ctx), ctx)
    worsening, _ = _collect(_hits(WORSENING_TOKENS, ctx), ctx)
    context_found, _ = _collect(_hits(CONTEXT_TOKENS, ctx), ctx)
    sudden = any(w in SUDDEN_WORDS for w in ctx.singular)
    ctx.used.update(i for i, w in enumerate(ctx.singular) if w in SUDDEN_WORDS)

    matched = list(normalized["matched_symptoms"])
    confidence = dict(normalized["confidence"])
    denied_symptoms = list(normalized["denied_symptoms"])

    # Details people write naturally — used when the matching form field was left open.
    details = []
    temperature = _parse_temperature(ctx)
    if temperature is not None:
        details.append(f"Temperature {temperature} °C")
        if temperature >= 38 and "fever" not in matched:
            matched.append("fever")
            confidence["fever"] = 1.0
            if "fever" in denied_symptoms:
                denied_symptoms.remove("fever")
        elif temperature < 37.8 and "fever" not in matched and "fever" not in denied_symptoms:
            denied_symptoms.append(f"fever (measured {temperature} °C)")
    parsed_age = _parse_age(ctx)
    if parsed_age and age_group == "Not specified":
        age_group = parsed_age[0]
        details.append(f"Age group: {age_group} (from “{parsed_age[1]}”)")
    parsed_duration = _parse_duration(ctx)
    if parsed_duration and duration == "Not specified":
        duration = parsed_duration[0]
        details.append(f"Duration: {duration} (from “{parsed_duration[1]}”)")
    parsed_severity = _parse_severity(ctx)
    if parsed_severity and SEVERITIES.index(parsed_severity[0]) > SEVERITIES.index(severity):
        details.append(f"Severity raised from {severity} to {parsed_severity[0]} (from “{parsed_severity[1]}”)")
        severity = parsed_severity[0]
    risks = list(dict.fromkeys(list(risk_factors) + list(risk_found)))
    for r in risk_found:
        if r not in risk_factors:
            details.append(f"Risk factor: {r}")
    details += list(context_found)
    if worsening:
        details.append("Symptoms getting worse")
    if sudden:
        details.append("Sudden onset")

    symptoms = set(matched)
    stiff_neck = "stiff neck" in symptoms
    if "fever" in symptoms and (stiff_neck or "light sensitivity" in symptoms) and "RF_MENINGITIS_SIGNS" not in flags:
        flags.append("RF_MENINGITIS_SIGNS")
    flags += [f for f in warning_signs if f not in flags]

    # Base rule: first match wins. `override` refines where/when for that rule.
    override = None
    if flags:
        status = "urgent"
        severity_label = "Potentially life-threatening warning signs may be present"
        reason = ("You reported a recognised emergency warning sign: "
                  + ", ".join(describe_flag(f).lower() for f in flags)
                  + ". This tool cannot confirm the cause, but delaying professional assessment may be unsafe.")
    elif serious_concerns:
        status = "prompt"
        severity_label = "A potentially serious concern was mentioned"
        reason = (f"Your description includes a potentially serious concern ({', '.join(serious_concerns)}). "
                  "This demo cannot determine whether that condition is present, but it should not be treated as low risk.")
        override = ("Doctor (GP) appointment", "Within the next few days",
                    "YES — book a doctor's appointment promptly")
    elif severity == "Severe":
        status = "prompt"
        severity_label = "Severe symptoms reported"
        reason = ("You reported severe symptoms. Their cause cannot be determined safely by this demo, "
                  "so an in-person assessment by a healthcare professional is recommended.")
    elif not matched:
        status = "consider" if severity == "Moderate" else "monitor"
        severity_label = f"{severity} symptoms reported"
        reason = ("The description did not match the symptom vocabulary, so the level is based on the severity "
                  "you selected rather than on recognised symptoms.")
    elif duration in PERSISTENT_DURATIONS:
        status = "prompt"
        severity_label = "Symptoms lasting several days or longer"
        reason = ("Symptoms lasting 4 days or longer may need assessment, especially when they are not "
                  "improving or interfere with normal activities.")
        override = ("Doctor (GP) appointment", "Within the next few days",
                    "YES — arrange a doctor's appointment")
    elif severity == "Moderate":
        status = "consider"
        severity_label = "Moderate symptoms reported"
        reason = ("Moderate symptoms may need professional evaluation depending on their cause, "
                  "progression, age, and other health factors.")
    else:
        status = "monitor"
        severity_label = "Mild symptoms reported"
        reason = ("You reported mild symptoms and no warning sign was detected. This does not rule out a "
                  "serious condition or guarantee that home monitoring is appropriate.")

    # Modifiers: age, risk factors and symptom combinations can only raise the level.
    factors = []
    base_status = status

    def escalate(to, why):
        nonlocal status, override
        if STATUS_ORDER.index(to) > STATUS_ORDER.index(status):
            status, override = to, None
            factors.append(why)

    def step_up(why):
        escalate(STATUS_ORDER[min(STATUS_ORDER.index(status) + 1, 2)], why)

    for symptom in matched:
        if symptom in SYMPTOM_MIN_STATUS:
            escalate(*SYMPTOM_MIN_STATUS[symptom])
    if temperature is not None and temperature >= 40:
        escalate("prompt", f"A temperature of {temperature} °C is very high and needs same-day assessment.")
    if temperature is not None and temperature < 35:
        escalate("prompt", f"A temperature of {temperature} °C is abnormally low and needs same-day assessment.")
    if age_group == "Infant (under 1)" and "fever" in symptoms:
        escalate("prompt", "Fever in a baby under 1 year needs same-day medical assessment "
                           "(under 3 months, seek urgent care).")
    if age_group in {"Infant (under 1)", "Child", "Older adult"} and symptoms & {"vomiting", "diarrhea"}:
        escalate("consider", "Vomiting or diarrhoea can cause dehydration quickly in young children and older adults.")
    if age_group == "Older adult" and "fever" in symptoms:
        escalate("consider", "Fever in older adults can signal a more serious infection.")
    if {"weight change", "night sweats"} <= symptoms:
        escalate("prompt", "Night sweats with weight change should be assessed by a doctor.")
    if "Pregnant" in risks:
        pregnancy_concerns = symptoms & {"abdominal pain", "pelvic pain", "abnormal vaginal bleeding", "headache",
                                         "swelling", "leg swelling", "urinary pain", "vision problems"}
        if pregnancy_concerns:
            escalate("prompt", f"During pregnancy, {', '.join(sorted(pregnancy_concerns))} should be assessed "
                               "by a midwife or doctor the same day.")
        step_up("Pregnancy lowers the threshold for professional advice and limits which medicines are safe.")
    if "Weakened immune system" in risks:
        if "fever" in symptoms:
            escalate("prompt", "Fever with a weakened immune system can indicate a serious infection.")
        step_up("A weakened immune system raises the risk of complications.")
    if "Takes blood thinners" in risks and symptoms & {"bleeding", "wound", "blood in urine", "rectal bleeding",
                                                        "nosebleed", "bruising", "injury"}:
        escalate("prompt", "Bleeding, bruising or injury while taking blood thinners needs same-day assessment.")
    if "Long-term condition (heart, lung, kidney, diabetes)" in risks and matched:
        step_up("A long-term condition can make new symptoms more significant.")
    if worsening and matched:
        step_up("Symptoms that are getting worse should be reviewed sooner.")
    immobile = {"Recent long journey", "Recent surgery or immobility"} & set(context_found)
    if immobile and symptoms & {"leg pain", "leg swelling", "breathing difficulty", "chest pain"}:
        escalate("prompt", "Leg pain, leg swelling or breathlessness after a long journey or surgery "
                           "can be a blood clot and needs same-day assessment.")
    if "Recent travel abroad" in context_found and "fever" in symptoms:
        escalate("prompt", "Fever after travel abroad needs same-day assessment (e.g. to check for malaria).")
    possible_conditions = infer_possible_conditions(matched)
    for c in possible_conditions:
        if c["min_status"]:
            escalate(c["min_status"], f"The “{c['name']}” pattern usually needs a professional check or treatment.")

    if status != base_status:
        # Without this the reason ("You reported mild symptoms…") contradicts the raised level.
        reason = (f"On their own, your symptoms point to a {DISPOSITION[base_status][0].lower()} level. "
                  f"It was raised to {DISPOSITION[status][0].lower()} for the reasons below.")
    level_label, doctor_need, care_setting, timeframe = DISPOSITION[status]
    if override:
        care_setting, timeframe, doctor_need = override
    next_step = NEXT_STEP[status]
    if "RF_SELF_HARM" in flags:
        care_setting, next_step = "Emergency services or a crisis line", SELF_HARM_STEP

    if flags:
        care_guidance = "Emergency warning signs were detected. Do not rely on home treatment; seek emergency medical help now."
        care_avoid = "Do not delay emergency assessment or attempt to treat a potentially serious emergency at home."
        safety_net = []
    else:
        if possible_conditions:
            care_guidance = possible_conditions[0]["care"]
            care_avoid = possible_conditions[0]["avoid"]
        else:
            care_guidance = ("No condition-specific care guidance is shown because the symptom pattern is insufficient. "
                             "Use only general supportive care if appropriate and consult a healthcare professional.")
            care_avoid = "Do not start, stop, or change medication based on this demo."
        safety_net = list(dict.fromkeys(
            [s for c in possible_conditions[:2] for s in c["seek_help"]] + GENERAL_SAFETY_NET))
        if status in REVIEW_AFTER:
            safety_net.append(REVIEW_AFTER[status])

    body_systems = {}
    for s in matched:
        body_systems.setdefault(SYMPTOM_SYSTEM.get(s, "General"), []).append(s)

    sources = [
        {"title": f"MedlinePlus: {s}",
         "url": f"https://medlineplus.gov/search.html?query={quote_plus(s)}"}
        for s in matched[:2]
    ]

    # Understanding = share of meaningful words that some rule explained. It measures how
    # well the description was read, not how likely any condition is.
    content = [i for i, w in enumerate(ctx.singular) if w not in STOPWORDS and ctx.tokens[i][0] not in STOPWORDS
               and not w.isdigit()]
    understood = [i for i in content if i in ctx.used]
    coverage = len(understood) / len(content) if content else 0.0
    unrecognised = list(dict.fromkeys(ctx.tokens[i][0] for i in content if i not in ctx.used))
    if matched or flags:
        quality = sum(confidence.values()) / len(confidence) if confidence else 1.0
        overall_confidence = max(20, min(99, round(100 * quality * (0.4 + 0.6 * coverage))))
    else:
        overall_confidence = 20

    checks = {
        "Recognisable symptoms (try plain words like “sore throat” or “stomach pain”)": bool(matched or flags),
        "Age group": age_group != "Not specified",
        "How long you've had the symptoms": duration != "Not specified",
    }
    if "fever" in symptoms:
        checks["Your measured temperature"] = temperature is not None
    missing_info = [item for item, ok in checks.items() if not ok]
    completeness = round(100 * sum(checks.values()) / len(checks))

    return {
        "triage_band": status, "doctor_status": status,
        "level_label": level_label, "severity_label": severity_label, "doctor_need": doctor_need,
        "care_setting": care_setting, "timeframe": timeframe,
        "matched_symptoms": matched, "confidence": confidence, "body_systems": body_systems,
        "denied_symptoms": denied_symptoms,
        "denied_red_flags": [f for f in denied_flags if f not in flags],
        "pertinent_negatives": _pertinent_negatives(denied_symptoms, denied_flags, flags),
        "overall_confidence": overall_confidence, "understanding": round(coverage * 100),
        "unrecognised_words": unrecognised[:10],
        "completeness": completeness, "missing_info": missing_info,
        "details_from_text": details, "temperature_c": temperature,
        "red_flags_triggered": flags, "reason": reason, "contributing_factors": factors,
        "next_step": next_step, "safety_net": safety_net,
        "sources": sources, "disclaimer": DISCLAIMER,
        "age_group": age_group, "duration": duration, "severity": severity,
        "risk_factors": risks,
        "possible_conditions": possible_conditions, "care_guidance": care_guidance, "care_avoid": care_avoid,
    }


def build_report(symptom_text: str, result: dict, generated_at: str) -> str:
    """Structured summary in a clinical-handover style that a user can share with a clinician."""
    def bullets(items, empty):
        return [f"  - {i}" for i in items] if items else [f"  {empty}"]

    temp = f"{result['temperature_c']} °C" if result["temperature_c"] is not None else "Not recorded"
    lines = [
        "CARECHECK — SYMPTOM ASSESSMENT SUMMARY",
        f"Generated: {generated_at}",
        "Educational demo output for discussion with a healthcare professional. Not a diagnosis.",
        "",
        "PATIENT-REPORTED INFORMATION",
        f"  Description:  {symptom_text.strip()}",
        f"  Age group:    {result['age_group']}",
        f"  Duration:     {result['duration']}",
        f"  Severity:     {result['severity']}",
        f"  Temperature:  {temp}",
        f"  Risk factors: {', '.join(result['risk_factors']) or 'None reported'}",
        "",
        "SYMPTOMS BY BODY SYSTEM",
        *bullets([f"{system}: {', '.join(items)}" for system, items in result["body_systems"].items()],
                 "None recognised"),
        f"  Denied: {', '.join(result['pertinent_negatives']) or 'None stated'}",
        "",
        "RED-FLAG SCREEN",
        *bullets([describe_flag(f) for f in result["red_flags_triggered"]],
                 f"No warning signs identified ({len(FLAG_LABELS)} screened)"),
        "",
        "ASSESSMENT",
        f"  Triage level:     {result['level_label']}",
        f"  Recommended care: {result['care_setting']}",
        f"  Timeframe:        {result['timeframe']}",
        f"  Rationale:        {result['reason']}",
    ]
    if result["contributing_factors"]:
        lines += ["  Contributing factors:", *[f"    - {f}" for f in result["contributing_factors"]]]
    if result["possible_conditions"]:
        lines += ["  Possible patterns (not diagnoses):",
                  *[f"    - {c['name']} ({c['pattern_score']}% fit: {', '.join(c['matching_symptoms'])})"
                    for c in result["possible_conditions"]]]
    lines += [
        f"  Input parsing quality: {result['overall_confidence']}% "
        f"(description understood {result['understanding']}%) — measures how well the",
        "                         free text was read, NOT diagnostic certainty.",
        "",
        "ADVICE",
        f"  Next step: {result['next_step']}",
        f"  Care:      {result['care_guidance']}",
        f"  Avoid:     {result['care_avoid']}",
    ]
    if result["safety_net"]:
        lines += ["  Seek help sooner if:", *[f"    - {s}" for s in result["safety_net"]]]
    lines += ["", DISCLAIMER]
    return "\n".join(lines)
