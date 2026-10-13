"""Presentation layer for CareCheck: design tokens, animation system, HTML builders.

This module owns every pixel. It holds no medical knowledge, no triage rules and
no network access -- it turns plain data into the markup ``app.py`` hands to
Streamlit, and escapes every caller-supplied string on the way.

Visual language
---------------
Warm clinical: a soft tinted canvas rather than stark white, a teal-to-cyan
brand gradient, Plus Jakarta Sans for headings against Inter for body text, and
depth built from layered, colour-tinted shadows instead of hard borders. The aim
is a tool that looks cared-for and trustworthy -- inviting enough to use, calm
enough to believe.

Animation policy
----------------
Motion is pure CSS: Streamlit strips ``<script>`` from markdown, so animations
are driven by ``@keyframes`` plus per-element custom properties (``--d`` for
stagger delay, ``--w`` for bar width, ``--len`` for SVG dash length). That keeps
it declarative and GPU-composited, and means a script re-run replays entrances
naturally.

Three rules keep motion safe in a health tool:

1. **Nothing is conveyed by movement alone.** Status always carries in colour,
   icon and text together, so the interface reads identically with motion off.
2. **The emergency path has gravity.** Emergencies get a slow attention ring and
   a firm entrance -- never a bounce, overshoot or sheen. Reading "call an
   ambulance" should never feel playful, and only ambient texture, loading
   indicators and that one attention cue may loop.
3. **It all switches off.** One ``prefers-reduced-motion`` block disables every
   animation and restores the end state of anything whose geometry is animated.

A print stylesheet strips the interface chrome so the clinician summary prints
as a clean document.
"""

from __future__ import annotations

from html import escape
from typing import Iterable, Mapping, Sequence

# --- Status vocabulary ------------------------------------------------------
# Keyed by core.py's triage status. Each entry is
# (headline, text colour, surface tint, border, icon) with AA-contrast pairs.

ICON_EMERGENCY = ('<path d="M12 8v5M12 16.5v.01"/>'
                  '<path d="M7.9 3h8.2L21 7.9v8.2L16.1 21H7.9L3 16.1V7.9z"/>')
ICON_WARNING = ('<path d="M12 9v4M12 16.5v.01"/>'
                '<path d="M10.3 3.9 2.4 17.6A2 2 0 0 0 4.1 20.6h15.8a2 2 0 0 0 1.7-3L13.7 3.9a2 2 0 0 0-3.4 0z"/>')
ICON_INFO = '<circle cx="12" cy="12" r="9"/><path d="M12 11v5M12 8v.01"/>'
ICON_CHECK = '<circle cx="12" cy="12" r="9"/><path d="m8 12.5 2.6 2.6L16 9.7"/>'

STATUS = {
    "urgent":   ("Emergency care advised",          "#912018", "#FEF3F2", "#FDA29B", ICON_EMERGENCY),
    "prompt":   ("Professional assessment advised", "#93370D", "#FFFAEB", "#FEC84B", ICON_WARNING),
    "consider": ("Consider a consultation",         "#854A0E", "#FEFBE8", "#FDE272", ICON_INFO),
    "monitor":  ("Self-care and monitor",           "#05603A", "#ECFDF3", "#6CE9A6", ICON_CHECK),
}

#: Lowest to highest, for the severity scale.
SCALE = [
    ("monitor", "Monitor at home"),
    ("consider", "Consider advice"),
    ("prompt", "See a professional"),
    ("urgent", "Emergency"),
]

#: Badge wording and style for a reminder's schedule state.
REMINDER_STATES = {
    "upcoming": ("Upcoming", "is-upcoming"),
    "past": ("Past", "is-past"),
    "invalid": ("Needs attention", "is-invalid"),
}

LOGO_LIGHT = (
    '<svg width="36" height="36" viewBox="0 0 32 32" aria-hidden="true">'
    '<rect width="32" height="32" rx="10" fill="#fff" fill-opacity=".18"/>'
    '<path d="M13 7h6v6h6v6h-6v6h-6v-6H7v-6h6z" fill="#fff"/></svg>'
)
LOGO_MARK = (
    '<svg width="26" height="26" viewBox="0 0 32 32" aria-hidden="true">'
    '<defs><linearGradient id="ccMark" x1="0" y1="0" x2="1" y2="1">'
    '<stop offset="0" stop-color="#0F766E"/><stop offset="1" stop-color="#14B8A6"/>'
    '</linearGradient></defs>'
    '<rect width="32" height="32" rx="9" fill="url(#ccMark)"/>'
    '<path d="M13 7h6v6h6v6h-6v6h-6v-6H7v-6h6z" fill="#fff"/></svg>'
)

#: A stylised ECG trace drawn behind the hero text. Decorative only.
ECG_PATH = ("M0 26 H46 l5-12 l5 24 l5-12 H112 l4-7 l4 14 l4-7 "
            "H168 l5-16 l6 32 l5-16 H260")

#: The trace declares ``pathLength``, so the dash maths is exact regardless of
#: the path's real geometry and the sweep lines up with the animation timing.
ECG_LENGTH = 100


def esc(value: object) -> str:
    """HTML-escape any value for safe interpolation."""
    return escape(str(value), quote=True)


def icon(path: str, size: int = 18) -> str:
    return (f'<svg width="{size}" height="{size}" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="2.2" stroke-linecap="round" '
            f'stroke-linejoin="round" aria-hidden="true">{path}</svg>')


# ---------------------------------------------------------------------------
# Stylesheet
# ---------------------------------------------------------------------------

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=Plus+Jakarta+Sans:wght@500;600;700;800&display=swap');

/* ========================================================================
   1. Tokens
   ===================================================================== */
:root {
  /* Contrast ratios measured against #FFFFFF; the canvas is only a shade
     darker, so the lightest pairing still clears AA at 4.54:1. */
  --cc-ink: #0B1623;          /* headings and body, 18.2:1 */
  --cc-muted: #44546A;        /* secondary text, 7.7:1 */
  --cc-subtle: #64748B;       /* least-important text, 4.76:1 (AA) */
  --cc-line: #E6EDF2;
  --cc-line-strong: #CFDAE3;
  --cc-brand: #0F766E;        /* brand text, 5.5:1 */
  --cc-brand-dark: #115E56;
  --cc-brand-lift: #14B8A6;
  --cc-brand-glow: #2DD4BF;
  --cc-brand-tint: #F0FDFA;
  --cc-brand-line: #A7F3EB;
  --cc-surface: #FFFFFF;
  --cc-canvas: #F7FAFC;
  --cc-radius: 16px;
  --cc-radius-sm: 11px;
  --cc-ease: cubic-bezier(0.22, 1, 0.36, 1);
  --cc-ease-soft: cubic-bezier(0.4, 0, 0.2, 1);
  /* Depth from layered, teal-tinted shadow rather than heavy borders. */
  --cc-shadow-xs: 0 1px 2px rgba(11, 22, 35, .05);
  --cc-shadow: 0 1px 2px rgba(11, 22, 35, .05), 0 6px 16px -10px rgba(15, 118, 110, .18);
  --cc-shadow-lg: 0 2px 4px rgba(11, 22, 35, .05), 0 18px 34px -16px rgba(15, 118, 110, .28);
  --cc-shadow-brand: 0 10px 24px -12px rgba(15, 118, 110, .55);
}

html, body, [class*="css"], .stApp, button, input, textarea, select {
  font-family: 'Inter', system-ui, -apple-system, "Segoe UI", sans-serif !important;
  -webkit-font-smoothing: antialiased;
}
h1, h2, h3, h4, .cc-display {
  font-family: 'Plus Jakarta Sans', 'Inter', system-ui, sans-serif !important;
  color: var(--cc-ink); letter-spacing: -.02em;
}

/* A softly tinted canvas reads warmer and less clinical-harsh than pure white. */
.stApp {
  background:
    radial-gradient(60% 50% at 88% -8%, rgba(45, 212, 191, .10), transparent 62%),
    radial-gradient(55% 45% at 4% 102%, rgba(56, 189, 248, .09), transparent 60%),
    linear-gradient(180deg, #FBFDFE 0%, var(--cc-canvas) 100%);
  background-attachment: fixed;
}
/* Two very low-opacity drifting blobs give the page quiet depth. */
.stApp::before {
  content: ""; position: fixed; inset: -20%; z-index: 0; pointer-events: none;
  background:
    radial-gradient(26% 24% at 20% 24%, rgba(20, 184, 166, .13), transparent 64%),
    radial-gradient(24% 22% at 80% 72%, rgba(99, 102, 241, .09), transparent 62%);
  filter: blur(34px);
  animation: ccBlobDrift 30s var(--cc-ease-soft) infinite alternate;
}
[data-testid="stAppViewContainer"] > section, .block-container,
[data-testid="stSidebar"] { position: relative; z-index: 1; }

[data-testid="stMainBlockContainer"], .block-container { padding-top: 1.5rem; max-width: 1240px; }
[data-testid="stSidebar"] {
  background: rgba(255, 255, 255, .72);
  -webkit-backdrop-filter: blur(16px); backdrop-filter: blur(16px);
  border-right: 1px solid var(--cc-line);
}
[data-testid="stTab"] p { font-weight: 600; }
#MainMenu, [data-testid="stDecoration"] { visibility: hidden; }
::selection { background: rgba(20, 184, 166, .22); }

a:focus-visible, button:focus-visible, input:focus-visible,
textarea:focus-visible, [role="button"]:focus-visible {
  outline: 2px solid var(--cc-brand) !important;
  outline-offset: 2px !important;
  border-radius: 6px;
}

/* ========================================================================
   2. Keyframe library
   ===================================================================== */
@keyframes ccRise { from { opacity: 0; transform: translateY(10px); } to { opacity: 1; transform: none; } }
@keyframes ccFade { from { opacity: 0; } to { opacity: 1; } }
@keyframes ccMeter { from { width: 0; } to { width: var(--w); } }
@keyframes ccScaleIn { from { opacity: 0; transform: scale(.94); } to { opacity: 1; transform: scale(1); } }
@keyframes ccSlideIn { from { opacity: 0; transform: translateX(-12px); } to { opacity: 1; transform: none; } }
@keyframes ccChipPop {
  0%   { opacity: 0; transform: scale(.82) translateY(4px); }
  70%  { opacity: 1; transform: scale(1.03) translateY(0); }
  100% { opacity: 1; transform: scale(1); }
}
@keyframes ccCountIn {
  from { opacity: 0; transform: translateY(6px); filter: blur(3px); }
  to   { opacity: 1; transform: none; filter: blur(0); }
}
@keyframes ccSheen {
  0%   { transform: translateX(-130%) skewX(-16deg); opacity: 0; }
  20%  { opacity: .7; }
  100% { transform: translateX(320%) skewX(-16deg); opacity: 0; }
}
@keyframes ccBlobDrift {
  from { transform: translate3d(0, 0, 0) scale(1); }
  to   { transform: translate3d(2%, -2.5%, 0) scale(1.09); }
}
@keyframes ccHeroDrift {
  0%, 100% { transform: translate3d(0, 0, 0) scale(1); }
  50%      { transform: translate3d(-2%, 1.5%, 0) scale(1.07); }
}
@keyframes ccLogoFloat { 0%, 100% { transform: translateY(0); } 50% { transform: translateY(-4px); } }
@keyframes ccHeartbeat {
  0%, 100% { transform: scale(1); }
  14%      { transform: scale(1.2); }
  28%      { transform: scale(1); }
  42%      { transform: scale(1.12); }
  56%      { transform: scale(1); }
}
@keyframes ccEcg {
  0%   { stroke-dashoffset: var(--len); opacity: .15; }
  55%  { stroke-dashoffset: 0; opacity: .8; }
  100% { stroke-dashoffset: calc(var(--len) * -1); opacity: .15; }
}
@keyframes ccStepFill { from { transform: scaleX(0); } to { transform: scaleX(1); } }
@keyframes ccUnderline { from { transform: scaleX(0); } to { transform: scaleX(1); } }
@keyframes ccShimmer { from { background-position: -420px 0; } to { background-position: 420px 0; } }
@keyframes ccSpin { to { transform: rotate(360deg); } }
@keyframes ccBreathe { 0%, 100% { opacity: .7; } 50% { opacity: 1; } }
@keyframes ccDotPulse {
  0%, 80%, 100% { transform: scale(.6); opacity: .4; }
  40%           { transform: scale(1); opacity: 1; }
}
/* The emergency attention ring: deliberately slow and heavy, never bouncy.
   It may only change the shadow -- no transform, so nothing moves. */
@keyframes ccAttention {
  0%   { box-shadow: 0 0 0 0 rgba(217, 45, 32, .45); }
  70%  { box-shadow: 0 0 0 13px rgba(217, 45, 32, 0); }
  100% { box-shadow: 0 0 0 0 rgba(217, 45, 32, 0); }
}

/* Entrance utilities; stagger with an inline --d */
.cc-rise  { animation: ccRise .38s var(--cc-ease) both; animation-delay: var(--d, 0s); }
.cc-fade  { animation: ccFade .32s ease-out both; animation-delay: var(--d, 0s); }
.cc-pop   { animation: ccScaleIn .34s var(--cc-ease) both; animation-delay: var(--d, 0s); }
.cc-slide { animation: ccSlideIn .36s var(--cc-ease) both; animation-delay: var(--d, 0s); }

/* ========================================================================
   3. Hero
   ===================================================================== */
.cc-hero {
  position: relative; overflow: hidden;
  padding: 1.9rem 2rem 1.7rem; border-radius: 22px; color: #fff; margin-bottom: 1.1rem;
  background: linear-gradient(135deg, #082F49 0%, #0E7490 52%, #0F766E 100%);
  box-shadow: 0 20px 44px -24px rgba(8, 47, 73, .7);
  animation: ccFade .45s ease-out both;
}
/* Mesh wash */
.cc-hero::before {
  content: ""; position: absolute; inset: -30%; pointer-events: none;
  background:
    radial-gradient(circle at 80% 18%, rgba(94, 234, 212, .46), transparent 46%),
    radial-gradient(circle at 14% 88%, rgba(56, 189, 248, .30), transparent 52%),
    radial-gradient(circle at 52% 120%, rgba(167, 243, 235, .20), transparent 46%);
  animation: ccHeroDrift 24s var(--cc-ease-soft) infinite;
}
/* Fine diagonal texture keeps the gradient from looking flat */
.cc-hero::after {
  content: ""; position: absolute; inset: 0; pointer-events: none; opacity: .5;
  background: repeating-linear-gradient(115deg,
    rgba(255, 255, 255, .05) 0 1px, transparent 1px 7px);
}
.cc-hero > * { position: relative; z-index: 2; }
.cc-hero-brand { display: flex; align-items: center; gap: .8rem; }
.cc-hero-brand svg { animation: ccLogoFloat 5s ease-in-out infinite; filter: drop-shadow(0 4px 10px rgba(0, 0, 0, .25)); }
.cc-hero h1 {
  margin: 0; font-size: 2.15rem; font-weight: 800; color: #fff; letter-spacing: -.035em;
  line-height: 1.08; animation: ccRise .5s var(--cc-ease) .08s both;
}
.cc-hero h1 em {
  font-style: normal;
  background: linear-gradient(96deg, #99F6E4, #5EEAD4 45%, #7DD3FC);
  -webkit-background-clip: text; background-clip: text;
  -webkit-text-fill-color: transparent; color: transparent;
}
.cc-hero p {
  margin: .5rem 0 1rem; color: rgba(236, 254, 255, .88); font-size: 1.04rem;
  max-width: 60ch; line-height: 1.58; animation: ccRise .5s var(--cc-ease) .16s both;
}
.cc-pill {
  display: inline-flex; align-items: center; gap: .4rem;
  padding: .3rem .78rem; margin: 0 .4rem .35rem 0; border-radius: 999px;
  font-size: .78rem; font-weight: 600; color: #ECFEFF;
  background: rgba(255, 255, 255, .13); border: 1px solid rgba(255, 255, 255, .26);
  -webkit-backdrop-filter: blur(8px); backdrop-filter: blur(8px);
  animation: ccChipPop .4s var(--cc-ease) both; animation-delay: var(--d, 0s);
  transition: background .25s var(--cc-ease-soft), transform .25s var(--cc-ease),
              border-color .25s var(--cc-ease-soft);
}
.cc-pill::before {
  content: ""; width: 5px; height: 5px; border-radius: 50%; background: #5EEAD4;
  box-shadow: 0 0 7px #5EEAD4;
}
.cc-pill:hover {
  background: rgba(255, 255, 255, .24); transform: translateY(-2px);
  border-color: rgba(167, 243, 235, .6);
}
.cc-ecg {
  position: absolute; right: 0; bottom: 6%; width: min(50%, 330px); height: 58px;
  z-index: 1; pointer-events: none; opacity: .6;
}
.cc-ecg path {
  fill: none; stroke: #5EEAD4; stroke-width: 2.2; stroke-linecap: round; stroke-linejoin: round;
  stroke-dasharray: var(--len); animation: ccEcg 4.2s linear infinite;
  filter: drop-shadow(0 0 6px rgba(94, 234, 212, .55));
}

/* ========================================================================
   4. Notices
   ===================================================================== */
.cc-notice {
  display: flex; gap: .8rem; align-items: flex-start; padding: .9rem 1.1rem;
  border-radius: var(--cc-radius-sm); font-size: .9rem; line-height: 1.58; margin-bottom: 1.1rem;
  background: linear-gradient(180deg, #FFFCF2, #FFFAEB);
  border: 1px solid #FEDF89; color: #7A2E0E; box-shadow: var(--cc-shadow-xs);
  animation: ccRise .4s var(--cc-ease) .1s both;
}
.cc-notice b { color: #7A2E0E; }
.cc-notice .cc-ico { flex: 0 0 auto; color: #B54708; padding-top: .05rem; animation: ccBreathe 3.4s ease-in-out infinite; }

/* ========================================================================
   5. Cards
   ===================================================================== */
.cc-card {
  position: relative; overflow: hidden;
  background: var(--cc-surface); border: 1px solid var(--cc-line); border-radius: var(--cc-radius);
  padding: 1.1rem 1.2rem; box-shadow: var(--cc-shadow); height: 100%;
  animation: ccRise .4s var(--cc-ease) both; animation-delay: var(--d, 0s);
  transition: transform .28s var(--cc-ease), box-shadow .28s var(--cc-ease-soft),
              border-color .28s var(--cc-ease-soft);
}
/* Hairline of brand colour along the top edge */
.cc-card::before {
  content: ""; position: absolute; top: 0; left: 0; right: 0; height: 1px;
  background: linear-gradient(90deg, transparent, var(--cc-brand-glow), transparent);
  opacity: .5;
}
.cc-card:hover {
  transform: translateY(-4px); box-shadow: var(--cc-shadow-lg);
  border-color: var(--cc-brand-line);
}
.cc-card::after {
  content: ""; position: absolute; left: 0; right: 0; bottom: 0; height: 2px;
  background: linear-gradient(90deg, var(--cc-brand), var(--cc-brand-glow), transparent);
  transform: scaleX(0); transform-origin: left;
  transition: transform .4s var(--cc-ease);
}
.cc-card:hover::after { transform: scaleX(1); }
.cc-card h4 {
  margin: 0 0 .5rem; font-size: .7rem; letter-spacing: .09em; text-transform: uppercase;
  color: var(--cc-subtle); font-weight: 700;
}
.cc-card .cc-value {
  font-family: 'Plus Jakarta Sans', 'Inter', sans-serif; font-size: 1.16rem; font-weight: 700;
  color: var(--cc-ink); line-height: 1.34; letter-spacing: -.015em;
  animation: ccCountIn .45s var(--cc-ease) both; animation-delay: calc(var(--d, 0s) + .1s);
}
.cc-card .cc-sub { font-size: .835rem; color: var(--cc-muted); margin-top: .4rem; line-height: 1.52; }

/* ========================================================================
   6. Triage banner
   ===================================================================== */
.cc-banner {
  position: relative; overflow: hidden;
  display: flex; gap: 1rem; align-items: flex-start; border-radius: var(--cc-radius);
  padding: 1.25rem 1.4rem; margin: .4rem 0 1.1rem;
  border: 1px solid; border-left-width: 5px;
  box-shadow: var(--cc-shadow);
  animation: ccRise .42s var(--cc-ease) both;
}
/* Non-emergency results get a single soft sheen; emergencies do not. */
.cc-banner:not(.is-urgent)::after {
  content: ""; position: absolute; top: 0; bottom: 0; left: 0; width: 30%;
  background: linear-gradient(100deg, transparent, rgba(255, 255, 255, .55), transparent);
  animation: ccSheen 2.6s var(--cc-ease-soft) .35s 1; pointer-events: none;
}
.cc-banner .cc-ico {
  position: relative; flex: 0 0 2.65rem; height: 2.65rem; border-radius: 50%; color: #fff;
  display: flex; align-items: center; justify-content: center;
  box-shadow: 0 6px 16px -8px currentColor;
  animation: ccScaleIn .4s var(--cc-ease) .1s both;
}
.cc-banner.is-urgent .cc-ico { animation: ccAttention 2.4s ease-out infinite; }
.cc-banner .cc-title {
  font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
  font-size: 1.32rem; font-weight: 800; margin-bottom: .28rem; letter-spacing: -.025em;
  animation: ccRise .42s var(--cc-ease) .08s both;
}
.cc-banner .cc-body {
  color: #334155; font-size: .96rem; line-height: 1.62;
  animation: ccFade .5s ease-out .2s both;
}

/* ========================================================================
   7. Severity scale
   ===================================================================== */
.cc-scale { display: grid; grid-template-columns: repeat(4, 1fr); gap: .45rem; margin: 0 0 1.2rem; }
.cc-scale .cc-step {
  position: relative; overflow: hidden;
  border-radius: var(--cc-radius-sm); padding: .58rem .6rem; text-align: center;
  font-size: .775rem; font-weight: 600;
  background: rgba(255, 255, 255, .7); border: 1px solid var(--cc-line); color: var(--cc-subtle);
  box-shadow: var(--cc-shadow-xs);
  animation: ccRise .34s var(--cc-ease) both; animation-delay: var(--d, 0s);
  transition: color .3s var(--cc-ease-soft), border-color .3s var(--cc-ease-soft),
              transform .3s var(--cc-ease);
}
.cc-scale .cc-step > span { position: relative; z-index: 2; }
.cc-scale .cc-step.is-active {
  color: var(--cc-step-ink); border-color: var(--cc-step-line);
  font-weight: 800; transform: translateY(-2px);
  box-shadow: 0 8px 20px -10px var(--cc-step-ink);
}
/* The active step's tint sweeps in from the left. */
.cc-scale .cc-step.is-active::after {
  content: ""; position: absolute; inset: 0; z-index: 1; background: var(--cc-step-bg);
  transform-origin: left; animation: ccStepFill .5s var(--cc-ease) .15s both;
}
.cc-scale .cc-step.is-active::before {
  content: ""; position: absolute; left: 0; top: 0; bottom: 0; width: 3px; z-index: 3;
  background: var(--cc-step-ink);
}

/* ========================================================================
   8. Chips
   ===================================================================== */
.cc-chip {
  display: inline-block; padding: .22rem .68rem; margin: .16rem .26rem .16rem 0; border-radius: 999px;
  font-size: .795rem; font-weight: 600;
  background: var(--cc-brand-tint); color: var(--cc-brand-dark); border: 1px solid var(--cc-brand-line);
  box-shadow: var(--cc-shadow-xs);
  animation: ccChipPop .34s var(--cc-ease) both; animation-delay: var(--d, 0s);
  transition: transform .2s var(--cc-ease), box-shadow .2s var(--cc-ease-soft);
}
.cc-chip:hover { transform: translateY(-2px); box-shadow: var(--cc-shadow); }
.cc-chip.is-flag { background: #FEF3F2; color: #912018; border-color: #FECDCA; }
.cc-chip.is-denied { background: #F1F5F9; color: #44546A; border-color: var(--cc-line-strong); text-decoration: line-through; }
.cc-chip.is-ok { background: #ECFDF3; color: #05603A; border-color: #ABEFC6; }
.cc-chip.is-info { background: #EFF8FF; color: #175CD3; border-color: #B2DDFF; }

/* ========================================================================
   9. Meter
   ===================================================================== */
.cc-meter {
  background: #E9EFF4; border-radius: 999px; height: 9px; overflow: hidden; margin-top: .6rem;
  box-shadow: inset 0 1px 2px rgba(11, 22, 35, .07);
}
.cc-meter > div {
  position: relative; overflow: hidden;
  height: 100%; border-radius: 999px; width: var(--w);
  background: linear-gradient(90deg, var(--cc-brand), var(--cc-brand-lift) 55%, var(--cc-brand-glow));
  box-shadow: 0 0 10px -2px rgba(20, 184, 166, .7);
  animation: ccMeter .8s var(--cc-ease) both;
}
.cc-meter > div::after {
  content: ""; position: absolute; top: 0; bottom: 0; left: -40%; width: 40%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, .6), transparent);
  animation: ccSheen 2.2s var(--cc-ease-soft) .9s 1;
}

/* ========================================================================
   10. Facts grid
   ===================================================================== */
.cc-facts {
  display: grid; grid-template-columns: repeat(auto-fit, minmax(234px, 1fr)); gap: .8rem;
  margin-top: 1rem;
  animation: ccRise .4s var(--cc-ease) .06s both;
}
.cc-facts > div {
  background: var(--cc-surface); border: 1px solid var(--cc-line);
  border-radius: var(--cc-radius); padding: 1rem 1.1rem; box-shadow: var(--cc-shadow-xs);
  transition: box-shadow .26s var(--cc-ease-soft), border-color .26s var(--cc-ease-soft);
}
.cc-facts > div:hover { box-shadow: var(--cc-shadow); border-color: var(--cc-brand-line); }
.cc-facts h4 {
  margin: 0 0 .5rem; font-size: .7rem; letter-spacing: .09em; text-transform: uppercase;
  color: var(--cc-subtle); font-weight: 700;
}
.cc-facts h4 + h4 { margin-top: .9rem; }
.cc-sys { margin-bottom: .45rem; animation: ccSlideIn .36s var(--cc-ease) both; animation-delay: var(--d, 0s); }
.cc-sys-name { display: block; font-size: .735rem; font-weight: 700; color: var(--cc-muted); margin-bottom: .14rem; }
.cc-muted { color: var(--cc-subtle); font-size: .85rem; }

/* ========================================================================
   11. Safety net
   ===================================================================== */
.cc-safety {
  background: linear-gradient(180deg, #FFF8F7, #FEF3F2);
  border: 1px solid #FECDCA; border-radius: var(--cc-radius);
  padding: 1rem 1.15rem; color: #7A271A; margin: .85rem 0; font-size: .92rem;
  box-shadow: var(--cc-shadow-xs);
  animation: ccRise .4s var(--cc-ease) both;
}
.cc-safety ul { margin: .5rem 0 0 1.15rem; padding: 0; }
.cc-safety li {
  margin: .24rem 0; line-height: 1.52;
  animation: ccSlideIn .34s var(--cc-ease) both; animation-delay: var(--d, 0s);
}

/* ========================================================================
   12. Patterns
   ===================================================================== */
.cc-pattern {
  padding: .85rem 0; border-bottom: 1px solid var(--cc-line);
  animation: ccRise .38s var(--cc-ease) both; animation-delay: var(--d, 0s);
}
.cc-pattern:last-child { border-bottom: none; }
.cc-pattern .cc-row {
  display: flex; justify-content: space-between; gap: .5rem; font-weight: 700; color: var(--cc-ink);
  font-family: 'Plus Jakarta Sans', 'Inter', sans-serif; letter-spacing: -.01em;
}
.cc-pattern .cc-detail { color: var(--cc-muted); font-size: .83rem; margin-top: .45rem; line-height: 1.52; }
.cc-pattern.is-best .cc-row > span:first-child::after {
  content: "Closest fit"; margin-left: .5rem; font-size: .66rem; font-weight: 700; vertical-align: middle;
  padding: .12rem .5rem; border-radius: 999px; display: inline-block;
  background: var(--cc-brand-tint); color: var(--cc-brand); border: 1px solid var(--cc-brand-line);
  animation: ccChipPop .4s var(--cc-ease) .3s both;
}

/* ========================================================================
   13. Section headings
   ===================================================================== */
.cc-section {
  position: relative; display: inline-block;
  font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
  font-size: 1.06rem; font-weight: 700; color: var(--cc-ink); margin: 1.3rem 0 .55rem;
  letter-spacing: -.02em; animation: ccFade .34s ease-out both;
}
.cc-section::after {
  content: ""; position: absolute; left: 0; right: 0; bottom: -5px; height: 2px; border-radius: 2px;
  background: linear-gradient(90deg, var(--cc-brand), var(--cc-brand-glow), transparent);
  transform-origin: left; animation: ccUnderline .55s var(--cc-ease) .12s both;
}
.cc-result-head {
  display: flex; justify-content: space-between; align-items: baseline; flex-wrap: wrap; gap: .5rem;
  margin: 1.7rem 0 .6rem; padding-top: 1.3rem; border-top: 1px solid var(--cc-line);
  animation: ccFade .36s ease-out both;
}
.cc-result-head .cc-t {
  font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
  font-size: 1.4rem; font-weight: 800; color: var(--cc-ink); letter-spacing: -.028em;
}
.cc-result-head .cc-m { font-size: .82rem; color: var(--cc-subtle); }

/* ========================================================================
   14. Skeleton (shown while a reference lookup is in flight)
   ===================================================================== */
.cc-skeleton {
  display: flex; flex-direction: column; gap: .75rem;
  background: var(--cc-surface); border: 1px solid var(--cc-line);
  border-radius: var(--cc-radius); padding: 1.05rem 1.15rem; box-shadow: var(--cc-shadow-xs);
}
.cc-skel-row {
  display: flex; align-items: center; gap: .85rem;
  animation: ccFade .3s ease-out both; animation-delay: var(--d, 0s);
}
.cc-skel {
  border-radius: 8px; height: 12px;
  background: linear-gradient(90deg, #EDF2F6 25%, #DEE7ED 37%, #EDF2F6 63%);
  background-size: 420px 100%; animation: ccShimmer 1.25s linear infinite;
}
.cc-skel-head {
  display: flex; align-items: center; gap: .6rem; font-size: .9rem;
  color: var(--cc-muted); font-weight: 600;
}
.cc-spinner {
  width: 16px; height: 16px; flex: 0 0 16px; border-radius: 50%;
  border: 2px solid var(--cc-brand-line); border-top-color: var(--cc-brand);
  animation: ccSpin .7s linear infinite;
}
.cc-dots { display: inline-flex; gap: 3px; align-items: center; }
.cc-dots i {
  width: 4px; height: 4px; border-radius: 50%; background: var(--cc-brand); display: block;
  animation: ccDotPulse 1.3s ease-in-out infinite;
}
.cc-dots i:nth-child(2) { animation-delay: .18s; }
.cc-dots i:nth-child(3) { animation-delay: .36s; }

/* ========================================================================
   15. Reminders
   ===================================================================== */
.cc-reminder {
  display: flex; justify-content: space-between; align-items: center; gap: 1rem;
  animation: ccSlideIn .36s var(--cc-ease) both; animation-delay: var(--d, 0s);
}
.cc-reminder .cc-name {
  font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
  font-weight: 700; color: var(--cc-ink); letter-spacing: -.012em;
}
.cc-reminder .cc-meta { font-size: .85rem; color: var(--cc-muted); margin-top: .12rem; }
.cc-badge {
  font-size: .715rem; font-weight: 700; padding: .2rem .62rem; border-radius: 999px; white-space: nowrap;
  animation: ccChipPop .34s var(--cc-ease) .1s both;
}
.cc-badge.is-upcoming { background: #ECFDF3; color: #05603A; border: 1px solid #ABEFC6; }
.cc-badge.is-past { background: #F1F5F9; color: #44546A; border: 1px solid var(--cc-line-strong); }
.cc-badge.is-invalid { background: #FEF3F2; color: #912018; border: 1px solid #FECDCA; }

/* ========================================================================
   16. Steps & sidebar
   ===================================================================== */
.cc-step-row {
  display: flex; gap: .9rem; padding: .62rem 0;
  animation: ccSlideIn .38s var(--cc-ease) both; animation-delay: var(--d, 0s);
}
.cc-step-row .cc-n {
  flex: 0 0 1.95rem; height: 1.95rem; border-radius: 50%; font-weight: 800;
  background: var(--cc-brand-tint); color: var(--cc-brand); border: 1px solid var(--cc-brand-line);
  display: flex; align-items: center; justify-content: center; font-size: .86rem;
  font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
  transition: transform .26s var(--cc-ease), background .26s var(--cc-ease-soft),
              color .26s var(--cc-ease-soft), box-shadow .26s var(--cc-ease-soft);
}
.cc-step-row:hover .cc-n {
  transform: scale(1.12) rotate(-6deg);
  background: linear-gradient(140deg, var(--cc-brand), var(--cc-brand-lift));
  color: #fff; box-shadow: var(--cc-shadow-brand);
}
.cc-step-row .cc-d { color: var(--cc-muted); font-size: .875rem; line-height: 1.55; margin-top: .12rem; }

.cc-side-brand {
  display: flex; align-items: center; gap: .6rem; font-weight: 800; font-size: 1.12rem;
  color: var(--cc-ink); font-family: 'Plus Jakarta Sans', 'Inter', sans-serif; letter-spacing: -.02em;
}
.cc-side-brand svg { animation: ccHeartbeat 3.6s var(--cc-ease-soft) infinite; transform-origin: center; }
.cc-sos {
  position: relative;
  border-radius: var(--cc-radius-sm); padding: .95rem 1.05rem; font-size: .875rem; line-height: 1.56;
  background: linear-gradient(180deg, #FFF8F7, #FEF3F2);
  border: 1px solid #FECDCA; color: #7A271A; box-shadow: var(--cc-shadow-xs);
  animation: ccRise .4s var(--cc-ease) .08s both;
}
.cc-stats { display: grid; grid-template-columns: 1fr 1fr; gap: .6rem; }
.cc-stat {
  background: var(--cc-surface); border: 1px solid var(--cc-line);
  border-radius: var(--cc-radius-sm); padding: .7rem .85rem; box-shadow: var(--cc-shadow-xs);
  animation: ccScaleIn .36s var(--cc-ease) both; animation-delay: var(--d, 0s);
  transition: transform .22s var(--cc-ease), border-color .22s var(--cc-ease-soft),
              box-shadow .22s var(--cc-ease-soft);
}
.cc-stat:hover { transform: translateY(-3px); border-color: var(--cc-brand-line); box-shadow: var(--cc-shadow); }
.cc-stat .cc-k { font-size: .7rem; color: var(--cc-subtle); font-weight: 700; text-transform: uppercase; letter-spacing: .07em; }
.cc-stat .cc-v {
  font-family: 'Plus Jakarta Sans', 'Inter', sans-serif;
  font-size: 1.38rem; font-weight: 800; color: var(--cc-ink); letter-spacing: -.03em;
  animation: ccCountIn .45s var(--cc-ease) both; animation-delay: calc(var(--d, 0s) + .08s);
}
.cc-footer {
  margin-top: 2.6rem; padding-top: 1.1rem; border-top: 1px solid var(--cc-line);
  color: var(--cc-subtle); font-size: .8rem; text-align: center; line-height: 1.62;
  animation: ccFade .5s ease-out .2s both;
}

/* ========================================================================
   17. Streamlit widgets
   ===================================================================== */
.stButton > button, .stDownloadButton > button, .stFormSubmitButton > button {
  position: relative; overflow: hidden; border-radius: var(--cc-radius-sm); font-weight: 600;
  border-color: var(--cc-line-strong);
  transition: transform .18s var(--cc-ease), box-shadow .22s ease, filter .2s ease,
              border-color .22s ease;
}
.stButton > button::after, .stDownloadButton > button::after, .stFormSubmitButton > button::after {
  content: ""; position: absolute; top: 0; bottom: 0; left: -45%; width: 40%;
  background: linear-gradient(90deg, transparent, rgba(255, 255, 255, .38), transparent);
  transform: skewX(-16deg); opacity: 0;
}
.stButton > button:hover, .stDownloadButton > button:hover, .stFormSubmitButton > button:hover {
  transform: translateY(-2px); box-shadow: var(--cc-shadow-lg); border-color: var(--cc-brand-line);
}
.stButton > button:hover::after, .stDownloadButton > button:hover::after,
.stFormSubmitButton > button:hover::after { opacity: 1; animation: ccSheen .8s var(--cc-ease-soft); }
.stButton > button:active, .stFormSubmitButton > button:active { transform: translateY(0) scale(.99); }
/* Primary action gets the brand gradient */
.stFormSubmitButton > button[kind="primaryFormSubmit"],
.stButton > button[kind="primary"], .stDownloadButton > button[kind="primary"] {
  background: linear-gradient(135deg, var(--cc-brand-dark), var(--cc-brand) 55%, var(--cc-brand-lift));
  border-color: transparent; color: #fff; box-shadow: var(--cc-shadow-brand);
}
.stFormSubmitButton > button[kind="primaryFormSubmit"]:hover,
.stButton > button[kind="primary"]:hover {
  filter: brightness(1.07); box-shadow: 0 14px 30px -12px rgba(15, 118, 110, .7);
}

[data-testid="stForm"] {
  border-radius: var(--cc-radius); border-color: var(--cc-line);
  background: rgba(255, 255, 255, .72);
  -webkit-backdrop-filter: blur(10px); backdrop-filter: blur(10px);
  box-shadow: var(--cc-shadow-xs);
  animation: ccRise .4s var(--cc-ease) both;
}
[data-testid="stTextInput"] input, [data-testid="stTextArea"] textarea {
  border-radius: var(--cc-radius-sm) !important;
  transition: border-color .22s var(--cc-ease-soft), box-shadow .22s var(--cc-ease-soft);
}
[data-testid="stTextInput"] input:focus, [data-testid="stTextArea"] textarea:focus {
  box-shadow: 0 0 0 3px rgba(20, 184, 166, .16) !important;
}
[data-testid="stExpander"] {
  border-radius: var(--cc-radius-sm); border-color: var(--cc-line);
  background: rgba(255, 255, 255, .7); box-shadow: var(--cc-shadow-xs);
}
[data-testid="stExpander"] summary { transition: background .2s var(--cc-ease-soft); border-radius: var(--cc-radius-sm); }
[data-testid="stExpander"] summary:hover { background: var(--cc-brand-tint); }
[data-testid="stAlert"] { border-radius: var(--cc-radius-sm); animation: ccRise .36s var(--cc-ease) both; }
[data-baseweb="tag"] { border-radius: 8px !important; animation: ccChipPop .3s var(--cc-ease) both; }
[data-testid="stToast"] { animation: ccSlideIn .35s var(--cc-ease) both; }
[data-testid="stDataFrame"] { border-radius: var(--cc-radius-sm); overflow: hidden; border: 1px solid var(--cc-line); }

/* Pill-style tabs read as a modern segmented control */
.stTabs [data-baseweb="tab-list"] { gap: .25rem; border-bottom: 1px solid var(--cc-line); }
.stTabs [data-baseweb="tab"] {
  border-radius: var(--cc-radius-sm) var(--cc-radius-sm) 0 0; padding: .6rem 1rem;
  transition: color .2s var(--cc-ease-soft), background .2s var(--cc-ease-soft);
}
.stTabs [data-baseweb="tab"]:hover { background: var(--cc-brand-tint); }
.stTabs [aria-selected="true"] { color: var(--cc-brand) !important; }
.stTabs [data-baseweb="tab-highlight"] {
  background: linear-gradient(90deg, var(--cc-brand), var(--cc-brand-glow)) !important;
  height: 2.5px !important; border-radius: 3px;
}
.stTabs [data-baseweb="tab-panel"] { animation: ccRise .34s var(--cc-ease) both; padding-top: .4rem; }

/* ========================================================================
   18. Narrow viewports
   ===================================================================== */
@media (max-width: 640px) {
  .cc-hero { padding: 1.35rem 1.25rem; border-radius: 18px; }
  .cc-hero h1 { font-size: 1.68rem; }
  .cc-hero p { font-size: .97rem; }
  .cc-ecg { display: none; }
  .cc-card { height: auto; }
  .cc-scale { grid-template-columns: 1fr 1fr; }
  [data-testid="stMainBlockContainer"], .block-container { padding-top: 3.2rem; }
  [data-testid="stTab"] { padding: .5rem .4rem !important; }
  [data-testid="stTab"] p { font-size: .86rem; }
  [data-testid="stTab"] span[role="img"] { display: none !important; }
}

/* ========================================================================
   19. Reduced motion -- one switch disables everything above
   ===================================================================== */
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: .001ms !important; animation-iteration-count: 1 !important;
    animation-delay: 0ms !important; transition-duration: .001ms !important;
  }
  .stApp::before, .cc-hero::before, .cc-hero-brand svg, .cc-side-brand svg,
  .cc-ecg path, .cc-notice .cc-ico, .cc-banner.is-urgent .cc-ico,
  .cc-spinner, .cc-dots i, .cc-skel { animation: none !important; }
  .cc-ecg { display: none; }
  /* Restore the end state of anything whose geometry is animated. */
  .cc-meter > div { width: var(--w); }
  .cc-scale .cc-step.is-active::after,
  .cc-section::after { transform: scaleX(1); }
  .cc-skel { background: #EDF2F6; }
}

/* ========================================================================
   20. Print: the clinician summary as a clean document
   ===================================================================== */
@media print {
  [data-testid="stSidebar"], [data-testid="stHeader"], [data-testid="stToolbar"],
  .stTabs [data-baseweb="tab-list"], .cc-hero, .stButton, .stDownloadButton,
  .stFormSubmitButton, [data-testid="stForm"], .cc-skeleton { display: none !important; }
  .stApp, .block-container {
    background: #fff !important; padding: 0 !important; max-width: 100% !important;
  }
  .stApp::before { display: none !important; }
  *, *::before, *::after { animation: none !important; transition: none !important; }
  .cc-card, .cc-banner, .cc-facts, .cc-safety, .cc-pattern {
    break-inside: avoid; box-shadow: none !important;
  }
  .cc-notice, .cc-banner { border-width: 1px !important; }
  .cc-meter > div { width: var(--w); }
  .cc-scale .cc-step.is-active::after, .cc-section::after { transform: scaleX(1); }
  a[href]::after { content: " (" attr(href) ")"; font-size: .75rem; color: #44546A; }
  pre, code { white-space: pre-wrap !important; word-break: break-word; }
}
</style>
"""


def flatten(markup: str) -> str:
    """Collapse markup to one line.

    Streamlit renders markdown, which turns indented lines into code blocks, so
    multi-line HTML must be flattened before it is handed over.
    """
    return " ".join(line.strip() for line in markup.splitlines() if line.strip())


def _delay(index: int, step: float = 0.05, cap: float = 0.6) -> str:
    """An inline stagger delay, capped so long lists never feel sluggish."""
    return f"--d:{min(index * step, cap):.2f}s"


# ---------------------------------------------------------------------------
# Builders
# ---------------------------------------------------------------------------

def hero(title: str, tagline: str, pills: Sequence[str],
         emphasis: str = "") -> str:
    """The masthead: mesh wash, floating logo, animated ECG trace.

    ``emphasis`` is an optional trailing fragment of the title rendered in the
    brand gradient. It is joined without a space, so ``hero("Care", ...,
    emphasis="Check")`` renders a single word with its second half accented.
    """
    chips_html = "".join(
        f'<span class="cc-pill" style="{_delay(index, 0.07)}">{esc(pill)}</span>'
        for index, pill in enumerate(pills)
    )
    heading = esc(title)
    if emphasis:
        heading += f"<em>{esc(emphasis)}</em>"
    ecg = (f'<svg class="cc-ecg" viewBox="0 0 260 54" preserveAspectRatio="none" '
           f'aria-hidden="true" style="--len:{ECG_LENGTH}">'
           f'<path d="{ECG_PATH}" pathLength="{ECG_LENGTH}"/></svg>')
    return (
        f'<div class="cc-hero">{ecg}<div class="cc-hero-brand">{LOGO_LIGHT}'
        f'<h1>{heading}</h1></div><p>{esc(tagline)}</p>{chips_html}</div>'
    )


def notice(body_html: str) -> str:
    """A standing safety notice. ``body_html`` is trusted markup from the caller."""
    return (f'<div class="cc-notice" role="note"><span class="cc-ico">'
            f'{icon(ICON_WARNING)}</span><span>{body_html}</span></div>')


def section(title: str) -> str:
    return f'<div class="cc-section">{esc(title)}</div>'


def result_head(stamp: str, note_text: str) -> str:
    return (f'<div class="cc-result-head"><span class="cc-t">Assessment result</span>'
            f'<span class="cc-m">Generated {esc(stamp)} · {esc(note_text)}</span></div>')


def meter(percent: int) -> str:
    width = max(0, min(100, int(percent)))
    return f'<div class="cc-meter"><div style="--w:{width}%"></div></div>'


def card(heading: str, value: str, sub: str = "", delay: float = 0.0) -> str:
    """A labelled statistic. Every field is escaped."""
    sub_html = f'<div class="cc-sub">{esc(sub)}</div>' if sub else ""
    return (f'<div class="cc-card" style="--d:{delay:.2f}s"><h4>{esc(heading)}</h4>'
            f'<div class="cc-value">{esc(value)}</div>{sub_html}</div>')


def meter_card(heading: str, percent: int, value_text: str, sub: str = "",
               delay: float = 0.0) -> str:
    """A card whose value is a percentage with a meter beneath it."""
    sub_html = f'<div class="cc-sub">{esc(sub)}</div>' if sub else ""
    return (f'<div class="cc-card" style="--d:{delay:.2f}s"><h4>{esc(heading)}</h4>'
            f'<div class="cc-value">{esc(value_text)}</div>{meter(percent)}'
            f'{sub_html}</div>')


def banner(status: str, headline: str, body: str) -> str:
    """The headline triage result.

    ``role="alert"`` on an emergency so a screen reader announces it immediately.
    Emergencies are marked ``is-urgent``, which swaps the decorative sheen for a
    slow attention ring: gravity rather than flourish.
    """
    label, ink, tint, line, glyph = STATUS.get(status, STATUS["prompt"])
    urgent = status == "urgent"
    return (
        f'<div class="cc-banner{" is-urgent" if urgent else ""}" '
        f'style="background:{tint};border-color:{line};border-left-color:{ink}" '
        f'role="{"alert" if urgent else "status"}">'
        f'<span class="cc-ico" style="background:{ink};color:{ink}">'
        f'<span style="color:#fff">{icon(glyph, 23)}</span></span>'
        f'<div><div class="cc-title" style="color:{ink}">{esc(headline or label)}</div>'
        f'<div class="cc-body">{esc(body)}</div></div></div>'
    )


def severity_scale(status: str) -> str:
    """The four triage levels with the current one marked.

    Showing the whole range, not just the outcome, makes the result legible: the
    user can see that "consider advice" is two steps below an emergency. The
    active step's tint sweeps in, which draws the eye to the position without
    being the only thing that marks it.
    """
    current = next((label for key, label in SCALE if key == status), "")
    steps = []
    for index, (key, label) in enumerate(SCALE):
        _, ink, tint, line, _ = STATUS[key]
        active = key == status
        style = _delay(index, 0.06)
        if active:
            style += f";--cc-step-ink:{ink};--cc-step-bg:{tint};--cc-step-line:{line}"
        steps.append(f'<div class="cc-step{" is-active" if active else ""}" '
                     f'style="{style}"><span>{esc(label)}</span></div>')
    return (f'<div class="cc-scale" role="img" '
            f'aria-label="Triage level {esc(current)} of four: '
            f'monitor at home, consider advice, see a professional, emergency">'
            f'{"".join(steps)}</div>')


def chips(items: Iterable[str], variant: str = "") -> str:
    """Capitalised, escaped chips that pop in with a stagger."""
    css = f" {variant}" if variant else ""
    return "".join(
        f'<span class="cc-chip{css}" style="{_delay(index, 0.04)}">'
        f'{esc(item[:1].upper() + item[1:])}</span>'
        for index, item in enumerate(item for item in items if item)
    )


def facts_grid(by_system: Mapping[str, Sequence[str]], denied: Sequence[str],
               picked_up: Sequence[str], flags: Sequence[str],
               flag_total: int) -> str:
    """Three panels: what was recognised, what was ruled out, warning signs."""
    recognised = "".join(
        f'<div class="cc-sys" style="{_delay(index, 0.06)}">'
        f'<span class="cc-sys-name">{esc(system)}</span>{chips(items)}</div>'
        for index, (system, items) in enumerate(by_system.items())
    ) or '<span class="cc-muted">None recognised</span>'

    denied_html = chips(denied, "is-denied") or '<span class="cc-muted">None stated</span>'
    picked_html = chips(picked_up, "is-info") or '<span class="cc-muted">Nothing extra</span>'
    flags_html = chips(flags, "is-flag") or (
        f'<span class="cc-chip is-ok">None of {flag_total} identified</span>')

    return (
        '<div class="cc-facts">'
        f'<div><h4>Symptoms by body system</h4>{recognised}</div>'
        f'<div><h4>You said you don’t have</h4>{denied_html}'
        f'<h4>Picked up from your description</h4>{picked_html}</div>'
        f'<div><h4>Emergency warning signs</h4>{flags_html}</div>'
        '</div>'
    )


def pattern_rows(patterns: Sequence[Mapping]) -> str:
    """Educational pattern matches, best fit first, staggered in."""
    rows = []
    for index, pattern in enumerate(patterns):
        detail = f'Matching: {esc(", ".join(pattern["matching_symptoms"]))}'
        if pattern["other_features"]:
            detail += ('<br>Also typical, not reported: '
                       f'{esc(", ".join(pattern["other_features"]))}')
        best = " is-best" if index == 0 and len(patterns) > 1 else ""
        rows.append(
            f'<div class="cc-pattern{best}" style="{_delay(index, 0.08)}">'
            f'<div class="cc-row"><span>{esc(pattern["name"])}</span>'
            f'<span>{int(pattern["pattern_score"])}% fit</span></div>'
            f'{meter(pattern["pattern_score"])}'
            f'<div class="cc-detail">{detail}</div></div>'
        )
    return "".join(rows)


def safety_net(items: Sequence[str]) -> str:
    bullets = "".join(
        f'<li style="{_delay(index, 0.06)}">{esc(item)}</li>'
        for index, item in enumerate(items)
    )
    return (f'<div class="cc-safety"><b>Get help sooner if you notice:</b>'
            f'<ul>{bullets}</ul></div>')


def reminder_row(name: str, instructions: str, when_text: str,
                 state: str = "upcoming", delay: float = 0.0) -> str:
    """One stored reminder.

    ``state`` is ``upcoming``, ``past`` or ``invalid``. The last covers a row
    whose stored timestamp cannot be read, so the user can see it and delete it
    rather than the screen failing.
    """
    word, css = REMINDER_STATES.get(state, REMINDER_STATES["upcoming"])
    return (
        f'<div class="cc-reminder" style="--d:{delay:.2f}s"><div>'
        f'<div class="cc-name">{esc(name)}</div>'
        f'<div class="cc-meta">{esc(instructions)}</div>'
        f'<div class="cc-meta">{esc(when_text)}</div></div>'
        f'<span class="cc-badge {css}">{word}</span></div>'
    )


def step_list(steps: Sequence[tuple[str, str]]) -> str:
    return "".join(
        f'<div class="cc-step-row" style="{_delay(number - 1, 0.07)}">'
        f'<div class="cc-n">{number}</div>'
        f'<div><b>{esc(title)}</b><div class="cc-d">{esc(detail)}</div></div></div>'
        for number, (title, detail) in enumerate(steps, 1)
    )


def skeleton(label: str, rows: int = 3) -> str:
    """A shimmering placeholder shown while a reference lookup is in flight.

    Rendered into a placeholder before the blocking request, so Streamlit flushes
    it to the browser and the shimmer runs during the wait.
    """
    widths = (("62%", "88%"), ("48%", "76%"), ("55%", "81%"), ("44%", "69%"))
    body = "".join(
        f'<div class="cc-skel-row" style="{_delay(index, 0.08)}">'
        f'<div class="cc-skel" style="width:30px;height:30px;border-radius:9px"></div>'
        f'<div style="flex:1"><div class="cc-skel" style="width:{a};margin-bottom:7px">'
        f'</div><div class="cc-skel" style="width:{b};height:9px"></div></div></div>'
        for index, (a, b) in enumerate(widths[:max(1, rows)])
    )
    return (f'<div class="cc-skeleton"><div class="cc-skel-head">'
            f'<span class="cc-spinner"></span>{esc(label)}'
            f'<span class="cc-dots"><i></i><i></i><i></i></span></div>{body}</div>')


def sidebar_panel(tagline: str, emergency_html: str,
                  stats: Sequence[tuple[str, object]]) -> str:
    tiles = "".join(
        f'<div class="cc-stat" style="{_delay(index, 0.07)}">'
        f'<div class="cc-k">{esc(key)}</div>'
        f'<div class="cc-v">{esc(value)}</div></div>'
        for index, (key, value) in enumerate(stats)
    )
    return (
        f'<div class="cc-side-brand">{LOGO_MARK}CareCheck</div>'
        f'<div class="cc-muted" style="margin:.25rem 0 1rem">{esc(tagline)}</div>'
        f'<div class="cc-sos" role="note">{emergency_html}</div>'
        f'<div class="cc-stats" style="margin-top:1rem">{tiles}</div>'
    )


def footer(text: str) -> str:
    return f'<div class="cc-footer">{esc(text)}</div>'
