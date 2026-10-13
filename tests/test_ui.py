"""Tests for the presentation layer: escaping, status mapping, motion policy.

The interface shows text that came from a user's free-text description and from
remote APIs, so escaping is a security property, not a cosmetic one.
"""

from __future__ import annotations

import re

import core
import ui

XSS = '<img src=x onerror="alert(1)">'


# --- Escaping ---------------------------------------------------------------

def test_esc_neutralises_markup():
    assert ui.esc("<b>hi</b>") == "&lt;b&gt;hi&lt;/b&gt;"
    assert ui.esc('a "quote" & amp') == "a &quot;quote&quot; &amp; amp"


def test_every_builder_escapes_untrusted_text():
    builders = [
        ui.hero(XSS, XSS, [XSS]),
        ui.section(XSS),
        ui.result_head(XSS, XSS),
        ui.card(XSS, XSS, XSS),
        ui.meter_card(XSS, 50, XSS, XSS),
        ui.banner("urgent", XSS, XSS),
        ui.chips([XSS]),
        ui.safety_net([XSS]),
        ui.reminder_row(XSS, XSS, XSS, "upcoming"),
        ui.step_list([(XSS, XSS)]),
        ui.footer(XSS),
        ui.hero(XSS, XSS, [XSS], emphasis=XSS),
    ]
    for markup in builders:
        assert "<img" not in markup
        assert "onerror" not in markup or "&quot;" in markup


def test_facts_grid_escapes_symptom_and_flag_text():
    markup = ui.facts_grid({XSS: [XSS]}, [XSS], [XSS], [XSS], 17)
    assert "<img" not in markup
    assert "&lt;img" in markup


def test_pattern_rows_escape_names_and_symptoms():
    markup = ui.pattern_rows([{
        "name": XSS, "pattern_score": 50,
        "matching_symptoms": [XSS], "other_features": [XSS],
    }])
    assert "<img" not in markup


def test_sidebar_panel_escapes_the_tagline_but_trusts_its_markup_argument():
    markup = ui.sidebar_panel(XSS, "<b>Emergency</b>", [("Checks", 3)])
    assert "<img" not in markup
    assert "<b>Emergency</b>" in markup  # caller-built markup is trusted by contract


def test_chips_skip_blanks_and_capitalise():
    assert ui.chips(["", "cough"]).count("cc-chip") == 1
    assert ">Cough<" in ui.chips(["cough"])


# --- Status mapping ---------------------------------------------------------

def test_ui_statuses_match_the_triage_engine():
    """A status core can emit but ui cannot render would fall back silently."""
    assert set(ui.STATUS) == set(core.STATUS_ORDER)
    assert set(ui.STATUS) == set(core.DISPOSITION)


def test_the_severity_scale_is_ordered_lowest_to_highest():
    assert [key for key, _ in ui.SCALE] == core.STATUS_ORDER


def test_each_status_has_a_full_colour_and_icon_set():
    for status, entry in ui.STATUS.items():
        headline, ink, tint, line, glyph = entry
        assert headline
        for colour in (ink, tint, line):
            assert re.fullmatch(r"#[0-9A-Fa-f]{6}", colour), f"{status}: {colour}"
        assert glyph.startswith("<")


# --- Banner & scale --------------------------------------------------------

def test_an_emergency_banner_is_announced_as_an_alert():
    markup = ui.banner("urgent", "Emergency care advised", "Call now")
    assert 'role="alert"' in markup
    assert "is-urgent" in markup


def test_a_non_emergency_banner_is_only_a_status():
    markup = ui.banner("monitor", "Self-care and monitor", "Rest")
    assert 'role="alert"' not in markup
    assert 'role="status"' in markup
    assert "is-urgent" not in markup


def test_an_unknown_status_falls_back_without_raising():
    assert ui.banner("nonsense", "", "body")


def test_the_scale_marks_exactly_one_active_step():
    for status in ui.STATUS:
        markup = ui.severity_scale(status)
        assert markup.count("is-active") == 1, status
        assert markup.count('class="cc-step') == 4


def test_the_scale_describes_itself_for_screen_readers():
    markup = ui.severity_scale("prompt")
    assert 'aria-label="Triage level See a professional of four' in markup


# --- Meter -----------------------------------------------------------------

def test_meter_clamps_to_zero_and_one_hundred():
    assert "--w:0%" in ui.meter(-25)
    assert "--w:100%" in ui.meter(400)
    assert "--w:63%" in ui.meter(63)


# --- Stagger, skeleton and the ECG trace -----------------------------------

def test_chips_are_staggered_in_order():
    delays = re.findall(r"--d:([\d.]+)s", ui.chips(["a", "b", "c"]))
    assert delays == ["0.00", "0.04", "0.08"]


def test_stagger_is_capped_so_long_lists_do_not_crawl():
    delays = [float(d) for d in re.findall(r"--d:([\d.]+)s", ui.chips(["x"] * 60))]
    assert max(delays) <= 0.6


def test_blank_chips_do_not_consume_a_stagger_slot():
    delays = re.findall(r"--d:([\d.]+)s", ui.chips(["", "cough", "", "fever"]))
    assert delays == ["0.00", "0.04"]


def test_the_hero_carries_an_ecg_trace_with_a_dash_length():
    markup = ui.hero("CareCheck", "tagline", ["one", "two"])
    assert 'class="cc-ecg"' in markup
    assert f"--len:{ui.ECG_LENGTH}" in markup
    assert 'aria-hidden="true"' in markup  # decorative, not announced


def test_the_ecg_declares_pathlength_so_the_dash_maths_is_exact():
    """Without pathLength the dasharray must guess the path's real length, and
    the sweep falls out of step with the animation timing."""
    markup = ui.hero("CareCheck", "tagline", [])
    assert f'pathLength="{ui.ECG_LENGTH}"' in markup
    assert f"--len:{ui.ECG_LENGTH}" in markup


def test_hero_emphasis_is_joined_without_a_space():
    markup = ui.hero("Care", "tagline", [], emphasis="Check")
    assert "Care<em>Check</em>" in markup


def test_hero_without_emphasis_has_no_em():
    assert "<em>" not in ui.hero("CareCheck", "tagline", [])


# --- Reminder states -------------------------------------------------------

def test_each_reminder_state_has_its_own_badge():
    for state, (word, css) in ui.REMINDER_STATES.items():
        markup = ui.reminder_row("Med", "Take one", "today", state)
        assert f'class="cc-badge {css}"' in markup
        assert f">{word}<" in markup


def test_an_unreadable_reminder_is_flagged_for_attention():
    markup = ui.reminder_row("Med", "Take one", "Unreadable date", "invalid")
    assert "Needs attention" in markup
    assert "is-invalid" in markup


def test_an_unknown_reminder_state_falls_back_without_raising():
    assert "Upcoming" in ui.reminder_row("Med", "x", "y", "nonsense")


def test_every_reminder_state_is_styled():
    for _word, css in ui.REMINDER_STATES.values():
        assert f".cc-badge.{css}" in ui.CSS


def test_hero_pills_are_staggered():
    delays = re.findall(r"--d:([\d.]+)s", ui.hero("t", "t", ["a", "b"]))
    assert delays == ["0.00", "0.07"]


def test_skeleton_renders_a_label_and_shimmer_rows():
    markup = ui.skeleton("Searching FDA label…", rows=3)
    assert "Searching FDA label" in markup
    assert markup.count("cc-skel-row") == 3
    assert "cc-spinner" in markup and "cc-dots" in markup


def test_skeleton_escapes_its_label_and_always_renders_a_row():
    assert "<img" not in ui.skeleton(XSS)
    assert ui.skeleton("x", rows=0).count("cc-skel-row") == 1


def test_the_severity_scale_staggers_its_steps():
    delays = re.findall(r"--d:([\d.]+)s", ui.severity_scale("prompt"))
    assert delays == ["0.00", "0.06", "0.12", "0.18"]


# --- Markup plumbing -------------------------------------------------------

def test_flatten_collapses_markup_for_streamlit_markdown():
    """Indented lines would otherwise be rendered as a code block."""
    flattened = ui.flatten("<div>\n    <span>a</span>\n\n  <span>b</span>\n</div>")
    assert flattened == "<div> <span>a</span> <span>b</span> </div>"
    assert "\n" not in flattened


# --- Motion and print policy ----------------------------------------------

def rules() -> str:
    """The stylesheet with comments stripped.

    Prose such as "animation: an attention ring" is not a declaration and would
    otherwise be scanned as one.
    """
    return re.sub(r"/\*.*?\*/", "", ui.CSS, flags=re.DOTALL)


def test_reduced_motion_is_honoured_and_comes_last():
    assert "@media (prefers-reduced-motion: reduce)" in ui.CSS
    assert ui.CSS.index("prefers-reduced-motion") > ui.CSS.rindex("@keyframes")

    block = ui.CSS.split("prefers-reduced-motion: reduce")[1]
    assert "animation-duration: .001ms !important" in block
    assert "animation-iteration-count: 1 !important" in block
    assert "animation: none !important" in block  # the looping ambient layers


def test_geometry_animations_are_restored_under_reduced_motion():
    """Anything animated by size or transform must still render at full extent."""
    block = ui.CSS.split("prefers-reduced-motion: reduce")[1]
    assert "width: var(--w)" in block        # meters
    assert "transform: scaleX(1)" in block   # scale fill and section underline


def test_a_broad_animation_vocabulary_is_available():
    """The brief asked for animation; keep that from silently eroding."""
    keyframes = set(re.findall(r"@keyframes\s+(\w+)", ui.CSS))
    assert len(keyframes) >= 15, f"only {len(keyframes)} animations defined"


LOOPING_ALLOWED = {
    # Ambient background texture
    "ccHeroDrift", "ccBlobDrift", "ccSheen", "ccLogoFloat", "ccEcg",
    "ccHeartbeat", "ccBreathe",
    # Loading indicators
    "ccShimmer", "ccSpin", "ccDotPulse",
    # The one attention cue
    "ccAttention",
}


def test_only_ambient_loading_and_attention_animations_loop():
    """Result content must never animate forever -- a pulsing triage card would
    be a distraction on a medical result."""
    looping = set(re.findall(r"animation:\s*([\w-]+)[^;]*infinite", rules()))
    assert looping, "no looping animations found to check"
    assert looping <= LOOPING_ALLOWED, f"unexpected looping animation: {looping - LOOPING_ALLOWED}"


def test_the_emergency_banner_gets_gravity_not_flourish():
    """An emergency result must not sheen, bounce or overshoot."""
    css = rules()
    # The decorative sheen is explicitly excluded from the urgent banner.
    assert ".cc-banner:not(.is-urgent)::after" in css
    # The urgent icon uses the attention ring.
    assert re.search(r"\.cc-banner\.is-urgent \.cc-ico \{ animation: ccAttention", css)

    # ccAttention may only change the shadow: it must not move or scale anything.
    body = css.split("@keyframes ccAttention")[1].split("}\n")[0]
    assert "box-shadow" in body
    for forbidden in ("transform", "scale(", "translate"):
        assert forbidden not in body, f"emergency animation must not use {forbidden}"


def test_every_animation_used_is_defined():
    css = rules()
    defined = set(re.findall(r"@keyframes\s+(\w+)", css))
    used = {name for name in re.findall(r"animation:\s*(\w+)", css) if name != "none"}

    assert used, "no animations found to check"
    assert used <= defined, f"undefined animations referenced: {used - defined}"


def test_no_animation_is_defined_but_unused():
    css = rules()
    defined = set(re.findall(r"@keyframes\s+(\w+)", css))
    used = set(re.findall(r"animation:\s*([\w-]+)", css))
    assert defined <= used, f"dead animations: {defined - used}"


def test_a_print_stylesheet_strips_the_interface():
    assert "@media print" in ui.CSS
    block = ui.CSS.split("@media print")[1]
    for hidden in ("stSidebar", "cc-hero", "stButton", "cc-skeleton"):
        assert hidden in block
    assert "animation: none !important" in block
    assert "transform: scaleX(1)" in block  # fills still print filled


def test_focus_is_always_visible_for_keyboard_users():
    assert ":focus-visible" in ui.CSS
    assert "outline: 2px solid var(--cc-brand) !important" in ui.CSS
