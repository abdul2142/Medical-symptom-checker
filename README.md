# 🩺 CareCheck — Symptom Triage & Medicine Reminder

An educational Streamlit prototype that turns a plain-language symptom description
into a transparent, safety-first triage recommendation, looks up medicine
information from public U.S. government databases, and stores medicine reminders
locally.

> **Not a medical device.** CareCheck does not diagnose disease, prescribe
> medicine, or recommend dosage changes. It is a software demo. Always consult a
> qualified healthcare professional, and contact local emergency services for
> emergency symptoms.

## Features

| Area | What it does |
|---|---|
| **Symptom check** | Reads free text against ~110 symptoms across 11 body systems, screens 17 emergency red flags, and routes to one of four outcomes: *Emergency*, *Professional assessment*, *Consider a consultation*, *Monitor at home*. |
| **Severity scale** | Shows all four levels with the current result marked, so an outcome is legible in context rather than in isolation. |
| **Pattern guidance** | Shows overlap with a small educational pattern library, plus supportive-care and “what to avoid” guidance. Scores are pattern overlap, not disease probabilities. |
| **Clinician summary** | Downloads — or prints — a plain-text summary of the assessment to share with a clinician. |
| **Session history** | Keeps the checks from the current session for comparison. |
| **Medicine reference** | FDA label uses and warnings (openFDA), name normalisation (RxNorm), and health topics (MedlinePlus). Successful lookups are cached for an hour. |
| **Reminders** | Saves medicine reminders with instructions entered exactly as prescribed, stored in local SQLite. |

## Quick start (Windows)

```powershell
py -3.12 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements-dev.txt
pytest
python -m streamlit run app.py
```

Then open <http://localhost:8501>. Run Streamlit from this folder so the theme in
`.streamlit/config.toml` is applied.

For runtime only, `pip install -r requirements.txt` is enough —
`requirements-dev.txt` adds pytest.

### Tests

109 tests, no network access and no shared state:

```
tests/test_core.py          triage rules, text understanding, report builder
tests/test_database.py      reminder storage against a temporary database
tests/test_api_clients.py   every HTTP outcome via a stubbed session
tests/test_ui.py            escaping, status mapping, motion and print policy
```

`pyproject.toml` puts the project root on `sys.path`, so plain `pytest` works
from this directory, in CI, and in IDE test runners.

### Optional: a different database location

```powershell
$env:CARECHECK_DB = "C:\path\to\reminders.db"
```

## How triage works

Rules are evaluated in order, and the first match wins:

1. **Red flags** (chest pain, breathing difficulty, seizure, slurred speech, …) → **Emergency**
2. **Serious concerns** (unexplained lump, blood in stool, …) → **Professional assessment**
3. **Severe** reported severity → **Professional assessment today**
4. No symptoms recognised → based on the reported severity
5. Symptoms lasting **4+ days** → **Arrange a consultation**
6. **Moderate** → **Consider a consultation**
7. Otherwise → **Monitor at home**

After the base rule, **modifiers can only raise the level, never lower it**:

- Age: fever in an infant, vomiting or diarrhoea in children and older adults, and fever in older adults
- Risk factors: pregnancy, a long-term condition, a weakened immune system, blood thinners
- Symptom combinations: fever with a stiff neck (emergency), blood in urine, night sweats with weight change
- Patterns that need a test, such as UTI-like or high-blood-sugar-like symptoms

Modifiers are also capped below *Emergency* — only an explicit red flag can
reach that level.

Every result states **where to get care** and **how soon**, the rules that raised
the level, and a list of signs that mean the person should get help sooner. The
clinician summary uses a handover structure: reported and denied symptoms,
red-flag screen, assessment, and advice.

**Text understanding**
- **Everyday language:** “throwing up”, “the runs”, “can't catch my breath”, “burning when I pee”.
- **Body parts:** “my left knee hurts”, “my ankles are swollen”, “pain in my lower right abdomen”.
- **Negation:** “I don't have a fever” is recorded as a denied symptom. Negation stops at clause breaks, so “no chest pain but short of breath” still flags breathing difficulty.
- **Typos and plurals:** “headaches” and “diarhea” are recognised. Tolerance applies word by word, so “painting” does not match “fainting” and “swollen and” does not match “swollen gland”.
- **Details picked up from the text:** age (“my 2 year old”, “I'm 72”), duration (“for 3 days”, “since yesterday”), temperature (“39.5C”, “101F”), severity (“unbearable”, “8/10”), risk factors (“I'm diabetic”, “on warfarin”), recent long journeys or surgery, and symptoms that are getting worse or started suddenly.

**Patterns.** Each of the ~35 patterns requires its key symptom, so headache with
nausea is never labelled gastroenteritis. Patterns are ranked by *fit*, which
measures both how much of the pattern is present and how much of the case it
explains. Each pattern also lists the typical features that were not reported.

**Reading quality, not certainty.** The percentage shown as *“How well your text
was read”* combines how much of the description the parser understood with how
strongly each symptom matched. Words it could not read are listed so the user can
rephrase them, and *completeness* shows which key details (age, duration,
temperature) are missing. Neither number is a probability, and neither says
anything about how likely any condition is — the UI and the clinician summary
both state that explicitly.

## Project structure

```
app.py                Streamlit interface: state, orchestration, layout
ui.py                 Design tokens and HTML builders (all markup)
core.py               Text understanding, triage rules, report builder
medical_data.py       Symptom vocabulary, red flags, condition patterns
api_clients.py        openFDA, RxNorm and MedlinePlus clients (all network access)
database.py           SQLite reminder storage
tests/                Automated tests
.streamlit/           Theme configuration
```

Responsibilities run one way. `app.py` imports the others; `core.py` holds no
markup and makes no network calls; `ui.py` holds no medical knowledge and makes
no network calls; `medical_data.py` is data only.

## Design & accessibility

### Visual language

Warm clinical. A softly tinted canvas rather than stark white, a teal-to-cyan
brand gradient, **Plus Jakarta Sans** for headings against **Inter** for body
text, and depth built from layered, colour-tinted shadows instead of hard
borders. Glass-morphism on the hero pills, sidebar and forms; pill-style tabs; a
gradient primary action; and a gradient-accented wordmark.

### Animation

20 CSS keyframe animations, all pure CSS — Streamlit strips `<script>` from
markdown, so motion is driven by `@keyframes` plus per-element custom properties
(`--d` for stagger delay, `--w` for bar width, `--len` for SVG dash length).

Two drifting blurred blobs behind the page, a mesh wash and light sweep across
the hero, a floating logo, an animated **ECG trace** (which declares
`pathLength` so the dash maths is exact), a heartbeat pulse on the sidebar mark,
staggered entrances for cards, chips, patterns, scale steps, safety-net items
and reminder rows, blur-to-sharp value reveals, glowing meters with a sheen
pass, a severity step whose tint sweeps in, section underlines that draw
themselves, hover lift with an accent wipe on cards, rotating step numerals,
button sheen, and a shimmering skeleton with spinner and pulsing dots during
medicine lookups.

Three rules keep motion safe in a health tool:

1. **Nothing is conveyed by movement alone.** Status always carries in colour,
   icon and text together, so the interface reads identically with motion off.
2. **The emergency path has gravity.** An emergency result gets a slow attention
   ring and a firm entrance — never a bounce, overshoot or sheen. Reading "call
   an ambulance" should not feel playful. Only ambient texture, loading
   indicators and that one attention cue are allowed to loop; result content
   never animates forever.
3. **It all switches off.** One `prefers-reduced-motion` block disables every
   animation and restores the end state of anything whose geometry is animated.

### Accessibility

- Status is carried by **colour, icon and text together**, never colour alone.
- Contrast meets **WCAG AA** for normal text on every pairing in the palette.
  Measured: body text 18.2:1, secondary 7.7:1, lightest supporting text 4.76:1
  on white and 4.54:1 on the tinted canvas. Every status ink-on-tint pair sits
  between 6.8:1 and 8.0:1.
- An emergency banner carries `role="alert"` so screen readers announce it
  immediately; lower levels use `role="status"`. The severity scale exposes its
  position as an `aria-label`, and decorative SVG is `aria-hidden`.
- Keyboard focus is always visible.
- **Printing the page** produces a clean clinician document — the sidebar, tabs,
  hero, buttons and skeletons are hidden, animations are stripped, fills print
  filled, and link targets are written out.

`tests/test_ui.py` asserts the animation vocabulary, the looping allowlist, the
emergency-gravity rule (including that the emergency keyframes change only the
shadow, never a transform), the reduced-motion restorations, the print rules and
the focus ring — so the policy cannot erode silently. It also fails on any
keyframe that is defined but unused.

## Safety design

- No diagnoses and no disease probabilities.
- No dose generation or modification; reminder instructions are stored verbatim
  from the user's own prescription.
- Modifiers can only raise the level of care.
- Severe or uncertain cases route to a professional.
- Self-harm disclosure routes to crisis support rather than ordinary triage.
- Every string that reaches the page from free text or a remote API is
  HTML-escaped; `tests/test_ui.py` covers that.

## Limitations

- The symptom vocabulary and red-flag rules are illustrative and need clinical
  review before any real-world use.
- Negation handling is rule-based. Unusual phrasing (“not sure if it's a fever”)
  may be misread.
- Medicine data covers U.S. labels only, and public API coverage is not universal.
- Reminders are stored locally in plain SQLite. No notifications are sent, and the
  database is not encrypted — `.gitignore` excludes it, but treat the file as
  personal health information.
- Streamlit has no authentication of its own. Do not expose this app on a public
  address.
