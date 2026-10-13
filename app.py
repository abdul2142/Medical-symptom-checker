"""CareCheck -- symptom triage and medicine reference (Streamlit interface).

An educational prototype. It does not diagnose disease, prescribe medicine or
recommend dosage changes.

Layering
--------
``medical_data.py``  symptom vocabulary, red flags, pattern library (data only)
``core.py``          text understanding, triage rules, report builder (no UI)
``api_clients.py``   openFDA / RxNorm / MedlinePlus clients (all network access)
``database.py``      local SQLite reminder storage
``ui.py``            design tokens and HTML builders (all markup)
``app.py``           this file: state, orchestration, layout
"""

from __future__ import annotations

from datetime import date, datetime, time

import streamlit as st

import ui
from api_clients import normalize_medicine_rxnorm, search_medlineplus, search_openfda_medicine
from core import (AGE_GROUPS, DISCLAIMER, DURATIONS, SEVERITIES, SYMPTOM_SYSTEM,
                  SYMPTOM_VOCABULARY, analyze_symptoms, build_report, describe_flag)
from database import add_reminder, delete_reminder, get_reminders, init_db
from medical_data import CONDITION_GUIDANCE, FLAG_LABELS, RISK_FACTORS

st.set_page_config(page_title="CareCheck | Symptom Triage", page_icon="\U0001fa7a",
                   layout="wide")


# Called on every script run, deliberately. It is two IF NOT EXISTS statements
# and costs microseconds, and it self-heals if the database file is removed or
# the CARECHECK_DB path changes. Caching it would cache the *guarantee* that the
# schema exists while the thing it guarantees can disappear, which left every
# tab broken until the process restarted.
init_db()
st.markdown(ui.CSS, unsafe_allow_html=True)


def render(markup: str) -> None:
    """Render trusted markup built by ``ui``."""
    st.markdown(ui.flatten(markup), unsafe_allow_html=True)


EXAMPLES = [
    "My 4 year old has a temperature of 38.9 and keeps throwing up",
    "Burning when I pee and I need to pee all the time, since yesterday",
    "Sharp pain in my lower right abdomen and no appetite",
    "Calf pain and a swollen leg after a long flight",
    "Sore throat, swollen glands and hard to swallow for 2 days",
]


# --- Medicine lookups -------------------------------------------------------
# Only successful lookups are cached, so a temporary network error is not
# remembered for an hour.

class LookupFailed(Exception):
    """A reference lookup returned an error rather than results."""


def _ok(result: dict) -> dict:
    if result.get("error"):
        raise LookupFailed(result["error"])
    return result


@st.cache_data(ttl=3600, show_spinner=False)
def fda_lookup(name: str) -> dict:
    return _ok(search_openfda_medicine(name))


@st.cache_data(ttl=3600, show_spinner=False)
def rxnorm_lookup(name: str) -> dict:
    return _ok(normalize_medicine_rxnorm(name))


@st.cache_data(ttl=3600, show_spinner=False)
def medline_lookup(topic: str) -> dict:
    return _ok(search_medlineplus(topic))


LOOKUPS = {
    "Uses & warnings (FDA label)": fda_lookup,
    "Name normalisation (RxNorm)": rxnorm_lookup,
    "Health topics (MedlinePlus)": medline_lookup,
}

st.session_state.setdefault("history", [])
st.session_state.setdefault("symptom_text", "")


def use_example(text: str) -> None:
    st.session_state.symptom_text = text


def parse_when(value: str) -> datetime | None:
    """Parse a stored reminder timestamp, or None if it is unreadable.

    New reminders are validated on write, but a row written by an older build
    could still be malformed. Returning None lets the interface show that row as
    needing attention instead of raising -- an unhandled error here would take
    down every tab, including the symptom checker, and leave no way to delete
    the offending row.
    """
    try:
        return datetime.fromisoformat(value)
    except (TypeError, ValueError):
        return None


# --- Header -----------------------------------------------------------------

render(ui.hero(
    "Care",
    "Describe how you feel in your own words. CareCheck reads it, screens for "
    "emergency warning signs, and tells you where to get care and how soon "
    "— with safety first.",
    ["Transparent rule-based triage", "NLM & FDA reference data",
     "Reminders stored locally"],
    emphasis="Check",
))
render(ui.notice(
    "<b>Demo only — not a medical device.</b> Results are educational and cannot "
    "diagnose or rule out any condition. Always consult a qualified healthcare "
    "professional before acting on a result."
))

tab_check, tab_med, tab_rem, tab_about = st.tabs([
    ":material/stethoscope: Symptom check",
    ":material/medication: Medicines",
    ":material/alarm: Reminders",
    ":material/info: About",
])


# ===========================================================================
# Symptom check
# ===========================================================================

with tab_check:
    left, right = st.columns([3, 2], gap="large")
    with left:
        with st.form("symptom_form", border=True):
            st.markdown("#### Describe your symptoms")
            st.text_area(
                "Symptoms", key="symptom_text", height=130, label_visibility="collapsed",
                placeholder="e.g. I'm 34, my left knee hurts and my ankles are swollen. "
                            "It started 3 days ago and is getting worse.",
            )
            st.caption("Write it in your own words — age, duration, temperature, severity "
                       "and conditions (e.g. “I'm diabetic”) are picked up from the text "
                       "if you leave the fields below open.")
            c1, c2, c3 = st.columns(3)
            age_group = c1.selectbox("Age group", AGE_GROUPS)
            duration = c2.selectbox("Duration", DURATIONS)
            severity = c3.select_slider("Severity", options=SEVERITIES)
            warning_labels = st.multiselect(
                "Do you have any of these right now?", list(FLAG_LABELS.values()),
                placeholder="None — select any that apply",
                help="Emergency warning signs. Selecting any of these overrides everything else.",
            )
            risk_factors = st.multiselect(
                "Anything that applies to you?", RISK_FACTORS,
                placeholder="None — select any that apply",
                help="These lower the threshold for recommending professional care.",
            )
            submitted = st.form_submit_button("Analyse symptoms", type="primary",
                                              width="stretch")
    with right:
        # Once there is a result, fold the tips away so the result sits directly
        # under the form on narrow screens.
        has_result = submitted or "last" in st.session_state
        with st.expander("Tips for a better result", icon=":material/lightbulb:",
                         expanded=not has_result):
            st.markdown(
                "- Mention **every** symptom and **where** it is: *“pain in my lower right side”*\n"
                "- Say **how long** and **how bad**: *“for 3 days”*, *“7/10”*\n"
                "- Add a **temperature** if you have one: *“38.5C”* or *“101F”*\n"
                "- Mention what you **don't** have too: *“no chest pain”*\n"
                "- Say if it's **sudden** or **getting worse**"
            )
            st.caption("Try an example")
            for index, example in enumerate(EXAMPLES):
                st.button(example, key=f"ex_{index}", on_click=use_example,
                          args=(example,), width="stretch")

    if submitted:
        text = st.session_state.symptom_text
        if not text.strip():
            st.error("Please describe at least one symptom.")
        else:
            label_to_flag = {v: k for k, v in FLAG_LABELS.items()}
            result = analyze_symptoms(
                text, age_group, duration, severity,
                warning_signs=[label_to_flag[label] for label in warning_labels],
                risk_factors=risk_factors,
            )
            stamp = datetime.now().strftime("%d %b %Y, %H:%M")
            st.session_state.last = {"text": text, "result": result, "at": stamp}
            st.session_state.history.insert(0, {
                "Time": stamp, "Description": text.strip()[:80],
                "Level": result["level_label"],
                "Recommended care": result["care_setting"],
                "How soon": result["timeframe"],
            })

    last = st.session_state.get("last")
    if last:
        r = last["result"]
        status = r["doctor_status"]
        headline = ui.STATUS.get(status, ui.STATUS["prompt"])[0]

        render(ui.result_head(last["at"], "Educational guidance, not a diagnosis"))
        render(ui.banner(status, headline, r["next_step"]))
        render(ui.severity_scale(status))

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            render(ui.card(
                "Triage level", r["level_label"],
                "Emergency warning sign present" if r["red_flags_triggered"]
                else f"Severity you reported: {r['severity'].lower()}", delay=0.0))
        with c2:
            render(ui.card("Where to get care", r["care_setting"], delay=0.04))
        with c3:
            render(ui.card("How soon", r["timeframe"], delay=0.08))
        with c4:
            # Deliberately *not* called "assessment confidence": this number
            # describes how much of the user's text the parser could read, and
            # must never be read as certainty about a diagnosis.
            render(ui.meter_card(
                "How well your text was read", r["overall_confidence"],
                f"{r['overall_confidence']}%",
                f"Not diagnostic certainty. Words recognised {r['understanding']}% "
                f"· key details {r['completeness']}%.", delay=0.12))

        render(ui.facts_grid(
            r["body_systems"], r["pertinent_negatives"], r["details_from_text"],
            [describe_flag(f) for f in r["red_flags_triggered"]], len(FLAG_LABELS),
        ))

        if r["unrecognised_words"] or r["missing_info"]:
            tips = []
            if r["missing_info"]:
                tips.append("Add: " + ", ".join(r["missing_info"]).lower() + ".")
            if r["unrecognised_words"]:
                tips.append("Words not understood: "
                            + ", ".join(f"“{w}”" for w in r["unrecognised_words"])
                            + " — try describing these in plain words.")
            st.info("**Improve this result.** " + " ".join(tips),
                    icon=":material/tips_and_updates:")

        col_a, col_b = st.columns(2, gap="large")
        with col_a:
            render(ui.section("Why this result"))
            st.write(r["reason"])
            for factor in r["contributing_factors"]:
                st.markdown(f"- {factor}")

            render(ui.section("Possible pattern matches"))
            # Show only patterns reasonably close to the best, to avoid noise.
            conditions = r["possible_conditions"]
            patterns = [c for c in conditions
                        if c["pattern_score"] >= conditions[0]["pattern_score"] / 2]
            if patterns:
                render(ui.pattern_rows(patterns))
                st.caption("Fit measures how much your symptoms and the pattern overlap. "
                           "It is not a diagnosis and not a probability.")
            else:
                st.caption("Not enough recognised symptoms to suggest a pattern.")
        with col_b:
            render(ui.section("Care guidance"))
            st.success(r["care_guidance"], icon=":material/healing:")
            render(ui.section("What to avoid"))
            st.warning(r["care_avoid"], icon=":material/block:")
            if r["safety_net"]:
                render(ui.safety_net(r["safety_net"]))
            if r["sources"]:
                render(ui.section("Learn more"))
                for source in r["sources"]:
                    st.markdown(f"[{source['title']}]({source['url']}) ↗")

        report = build_report(last["text"], r, last["at"])
        with st.expander("Clinician summary", icon=":material/clinical_notes:"):
            st.code(report, language=None, wrap_lines=True)
            st.caption("Download it below, or print this page (Ctrl+P / ⌘P) — the "
                       "interface is hidden in print output.")
        with st.expander("Assessment details"):
            d1, d2, d3, d4 = st.columns(4)
            d1.markdown(f"**Age group**  \n{r['age_group']}")
            d2.markdown(f"**Duration**  \n{r['duration']}")
            d3.markdown(f"**Reported severity**  \n{r['severity']}")
            d4.markdown(f"**Risk factors**  \n{', '.join(r['risk_factors']) or 'None reported'}")
            if r["confidence"]:
                st.markdown("**How each symptom was recognised**")
                st.dataframe(
                    [{"Symptom": name,
                      "Body system": SYMPTOM_SYSTEM.get(name, "General"),
                      "Match strength": f"{round(score * 100)}%",
                      "How": "Exact phrase" if score == 1
                      else "From body part + description" if score == 0.95
                      else "Close spelling"}
                     for name, score in r["confidence"].items()],
                    hide_index=True, width="stretch",
                )

        st.download_button(
            "Download summary for your clinician", report,
            file_name=f"carecheck-summary-{datetime.now():%Y%m%d-%H%M}.txt",
            mime="text/plain", icon=":material/download:",
        )

    if len(st.session_state.history) > 1:
        with st.expander(f"Session history ({len(st.session_state.history)} checks)"):
            st.dataframe(st.session_state.history, hide_index=True, width="stretch")


# ===========================================================================
# Medicine reference
# ===========================================================================

with tab_med:
    st.markdown("#### Medicine reference lookup")
    st.caption("Search public U.S. National Library of Medicine and FDA databases. "
               "Reference only — never use this to choose or change a dose.")
    with st.form("med_form", border=True):
        c1, c2 = st.columns([2, 3])
        query = c1.text_input("Medicine or topic", placeholder="e.g. ibuprofen")
        source = c2.radio("Source", list(LOOKUPS), horizontal=True)
        searched = st.form_submit_button("Search", type="primary", icon=":material/search:")

    if searched:
        if not query.strip():
            st.warning("Enter a medicine name or health topic first.")
        else:
            label = source.split("(")[-1].rstrip(")")
            # A shimmering skeleton rather than a spinner: Streamlit flushes this
            # delta before the blocking request, so the placeholder animates
            # during the wait and is replaced by the real results.
            loading = st.empty()
            loading.markdown(ui.flatten(ui.skeleton(f"Searching {label}…")),
                             unsafe_allow_html=True)
            try:
                result = LOOKUPS[source](query.strip())
            except LookupFailed as exc:
                result = {"error": str(exc)}
            loading.empty()
            st.session_state.med = {"source": source, "query": query.strip(),
                                    "result": result}

    med = st.session_state.get("med")
    if med:
        result, source = med["result"], med["source"]
        if result.get("error"):
            st.error(result["error"], icon=":material/wifi_off:")
        elif source.startswith("Uses"):
            matches = result.get("matches", [])
            if not matches:
                st.info("No FDA label found. Try the generic name or active ingredient "
                        "(e.g. *acetaminophen* rather than *paracetamol*).")
            for index, item in enumerate(matches):
                title = f"**{item['generic_name'].title()}** · {item['brand_name']}"
                with st.expander(title, expanded=(index == 0)):
                    st.caption(f"Manufacturer: {item['manufacturer']}")
                    if item["purpose"] != "Not listed":
                        st.markdown("**Purpose**")
                        st.write(item["purpose"])
                    st.markdown("**Labelled uses / indications**")
                    st.write(item["indications_and_usage"])
                    st.markdown("**Warnings**")
                    st.warning(item["warnings"])
                    if item["contraindications"] != "Not listed":
                        st.markdown("**Contraindications**")
                        st.write(item["contraindications"])
            if matches:
                st.caption("Label text does not establish that a medicine is suitable "
                           "for any specific person.")
        elif source.startswith("Name"):
            if result.get("matches"):
                st.dataframe(
                    [{"RxCUI": m["rxcui"], "Name": m["name"],
                      "Synonym": m["synonym"], "Type": m["tty"]}
                     for m in result["matches"]],
                    hide_index=True, width="stretch",
                )
            else:
                st.info("No RxNorm match found. Try the generic name or another spelling.")
        else:
            items = result.get("results", [])
            if not items:
                st.info("No MedlinePlus topics found.")
            for item in items:
                with st.container(border=True):
                    st.markdown(f"**[{item['title']}]({item['url']})**")
                    if item["summary"]:
                        st.caption(item["summary"])

    st.info("Always check the official label and ask a pharmacist or clinician "
            "— especially for children, pregnancy, allergies, chronic illness, or "
            "when taking other medicines.", icon=":material/local_pharmacy:")


# ===========================================================================
# Reminders
# ===========================================================================

with tab_rem:
    form_col, list_col = st.columns([2, 3], gap="large")
    with form_col:
        with st.form("reminder_form", border=True, clear_on_submit=True):
            st.markdown("#### New reminder")
            med_name = st.text_input("Medicine name", max_chars=120)
            instructions = st.text_input(
                "Instructions as prescribed", max_chars=500,
                placeholder="e.g. Take as directed by your clinician")
            c1, c2 = st.columns(2)
            reminder_date = c1.date_input("Date", min_value=date.today())
            reminder_time = c2.time_input("Time", value=time(9, 0))
            confirmed = st.checkbox("I entered these instructions exactly as prescribed.")
            if st.form_submit_button("Save reminder", type="primary", width="stretch"):
                reminder_at = datetime.combine(reminder_date, reminder_time)
                if not med_name.strip() or not instructions.strip():
                    st.error("Medicine name and instructions are required.")
                elif not confirmed:
                    st.error("Please confirm the instructions match your prescription.")
                elif reminder_at <= datetime.now():
                    st.error("Please choose a future date and time.")
                else:
                    try:
                        add_reminder(med_name, instructions, reminder_at.isoformat())
                    except ValueError as exc:
                        st.error(str(exc))
                    else:
                        st.toast(f"Reminder saved for {reminder_at:%d %b, %H:%M}", icon="✅")
        st.caption("CareCheck never suggests a dose. Reminders are stored only on "
                   "this computer.")

    with list_col:
        st.markdown("#### Your reminders")
        reminders = get_reminders()
        if not reminders:
            st.info("No reminders yet. Add one using the form.",
                    icon=":material/notifications:")
        now = datetime.now()
        for index, item in enumerate(reminders):
            when = parse_when(item["reminder_time"])
            if when is None:
                state, when_text = "invalid", "Unreadable date — delete and re-add"
            elif when > now:
                state, when_text = "upcoming", f"{when:%a %d %b %Y · %H:%M}"
            else:
                state, when_text = "past", f"{when:%a %d %b %Y · %H:%M}"
            with st.container(border=True):
                info, action = st.columns([6, 1], vertical_alignment="center")
                with info:
                    render(ui.reminder_row(
                        item["medicine_name"], item["instructions"], when_text,
                        state, delay=min(index * 0.05, 0.4)))
                with action:
                    if st.button("", key=f"delete_{item['id']}",
                                 icon=":material/delete:", help="Delete reminder"):
                        delete_reminder(item["id"])
                        st.rerun()


# ===========================================================================
# About
# ===========================================================================

with tab_about:
    a, b = st.columns(2, gap="large")
    with a:
        st.markdown("#### How an assessment works")
        render(ui.step_list([
            ("Reading your description",
             f"{len(SYMPTOM_VOCABULARY)} symptoms in everyday language, body-part "
             "phrases (“my knee hurts”), negation (“no fever”), typos and plurals."),
            ("Extracting details",
             "Age, duration, temperature, severity, risk factors and recent travel "
             "or surgery."),
            ("Red-flag screening",
             f"{len(FLAG_LABELS)} emergency warning signs override every other rule."),
            ("Level & routing",
             "Severity, duration and concerns set a base level; age, risk factors "
             "and high-risk symptoms can only raise it, never lower it."),
            ("Pattern guidance",
             f"Fit against {len(CONDITION_GUIDANCE)} educational patterns, each "
             "requiring its key symptom."),
            ("Reading quality",
             "How much of your description was understood and which key details "
             "are still missing — not diagnostic certainty."),
        ]))
    with b:
        st.markdown("#### Safety principles")
        st.markdown(
            "- No diagnoses and no disease probabilities\n"
            "- No dose generation or modification\n"
            "- Modifiers can only raise the level of care, never lower it\n"
            "- Severe or uncertain cases are routed to a professional\n"
            "- Rules must be clinically reviewed before any real-world use"
        )
        st.markdown("#### Accessibility")
        st.markdown(
            "- Status is carried by colour, icon and text together\n"
            "- Contrast meets WCAG AA; focus is always visible for keyboard use\n"
            "- Motion is minimal and switches off with `prefers-reduced-motion`\n"
            "- Printing the page produces a clean clinician document"
        )
        st.markdown("#### Data sources")
        st.markdown(
            "- [MedlinePlus](https://medlineplus.gov/) — U.S. National Library of Medicine\n"
            "- [RxNorm](https://www.nlm.nih.gov/research/umls/rxnorm/) — normalised drug names\n"
            "- [openFDA](https://open.fda.gov/apis/drug/label/) — drug label information"
        )

render(ui.footer(
    "CareCheck · Educational prototype — "
    + DISCLAIMER.removeprefix("Educational mock only. ")))


# Rendered last so the counters reflect anything submitted during this run.
with st.sidebar:
    _now = datetime.now()
    upcoming = [item for item in get_reminders()
                if (when := parse_when(item["reminder_time"])) and when > _now]
    render(ui.sidebar_panel(
        "Symptom triage & medicine reference",
        "<b>Is this an emergency?</b><br>Chest pain, trouble breathing, fainting, "
        "sudden weakness, slurred speech or heavy bleeding — call your local "
        "emergency number now.",
        [("Checks", len(st.session_state.history)), ("Reminders", len(upcoming))],
    ))
    if st.session_state.history and st.button("Clear session history", width="stretch",
                                              icon=":material/delete_sweep:"):
        st.session_state.history = []
        st.session_state.pop("last", None)
        st.rerun()
