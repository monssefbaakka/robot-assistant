from datetime import datetime, timezone
from html import escape
import math
import os
import time

import streamlit as st
import streamlit.components.v1 as components
from agent import AgentRobot
from config_env import load_env_file
from house_config import ROOM_ORDER, ROBOT_SIMULATION_WORLD, ordered_room_ids, room_name
from iot_store import load_state
from meteo import MeteoAPI
from objets_connectes import MaisonConnectee
from tts import RobotVoix
try:
    from voix import AssistantVocal
except Exception:
    AssistantVocal = None


@st.cache_data
def _get_robot_css():
    with open('robot_realistic.html', 'r', encoding='utf-8') as f:
        content = f.read()
    css_start = content.index('<style>') + len('<style>')
    css_end = content.index('</style>')
    return content[css_start:css_end]


def get_robot_html(state='idle'):
    css = _get_robot_css()
    return (
        '<!DOCTYPE html><html><head><meta charset="UTF-8"><style>'
        + css
        + 'body{background:transparent!important;min-height:unset!important;'
        'height:360px!important;overflow:hidden!important;padding:0!important;'
        'align-items:flex-start!important;}'
        '.robot-display{transform:scale(0.58);transform-origin:top center;}'
        '</style></head><body>'
        '<div class="robot-display">'
        '<div class="robot-3d">'
        '<div class="robot idle" id="robot">'
        '<div class="antenna-base"><div class="antenna-light"></div></div>'
        '<div class="head-3d">'
        '<div class="screen-panel">'
        '<div class="eyes-display">'
        '<div class="eye-lcd"></div><div class="eye-lcd"></div>'
        '</div></div>'
        '<div class="mouth-lcd"></div>'
        '</div>'
        '<div class="body-metal">'
        '<div class="status-indicator"></div>'
        '<div class="vent"></div><div class="vent"></div>'
        '<div class="vent"></div><div class="vent"></div>'
        '</div></div></div>'
        '<div class="control-panel" style="width:300px;margin-top:20px;">'
        '<div class="status-display" id="statusDisplay">STANDBY MODE</div>'
        '<div class="status-info" id="statusInfo">Awaiting instructions...</div>'
        '</div></div>'
        '<script>'
        'const robot=document.getElementById("robot");'
        'const statusDisplay=document.getElementById("statusDisplay");'
        'const statusInfo=document.getElementById("statusInfo");'
        'const states={'
        'idle:{display:"STANDBY MODE",info:"Awaiting instructions..."},'
        'listening:{display:"LISTENING MODE",info:"Audio input active..."},'
        'thinking:{display:"PROCESSING",info:"Computing response..."},'
        'speaking:{display:"SPEAKING MODE",info:"Audio output active..."}'
        '};'
        'function setState(s){'
        'robot.className="robot "+s;'
        'statusDisplay.textContent=states[s].display;'
        'statusInfo.textContent=states[s].info;'
        'if(s==="speaking")setTimeout(()=>setState("idle"),3500);'
        '}'
        f'setState("{state}");'
        '</script></body></html>'
    )


st.set_page_config(
    page_title="RoboCompagnon — Command Center",
    page_icon="data:image/svg+xml,<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24'><text y='20' font-size='20'>◈</text></svg>",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Syne:wght@400;500;600;700;800&display=swap');
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;1,9..40,400&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500&display=swap');
@import url('https://fonts.googleapis.com/css2?family=Material+Symbols+Outlined:opsz,wght,FILL,GRAD@20..48,100..700,0..1,-50..200&display=swap');

.material-symbols-outlined {
    font-family: 'Material Symbols Outlined';
    font-style: normal;
    font-size: 20px;
    line-height: 1;
    letter-spacing: normal;
    text-transform: none;
    display: inline-block;
    white-space: nowrap;
    word-wrap: normal;
    direction: ltr;
    -webkit-font-smoothing: antialiased;
    text-rendering: optimizeLegibility;
    -moz-osx-font-smoothing: grayscale;
    font-feature-settings: 'liga';
    font-variation-settings: 'FILL' 0, 'wght' 300, 'GRAD' 0, 'opsz' 24;
    vertical-align: middle;
    user-select: none;
}
.icon-fill { font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24; }
.icon-sm  { font-size: 14px; }
.icon-md  { font-size: 20px; }
.icon-lg  { font-size: 28px; }
.icon-xl  { font-size: 40px; }

/* ═══════════════════════════════════════════════════════
   DESIGN TOKENS
═══════════════════════════════════════════════════════ */
:root {
    --bg-deepest:   #02040c;
    --bg-main:      #040810;
    --bg-surface:   #080f1e;
    --bg-raised:    #0d1829;
    --bg-overlay:   #111f35;

    --border:        rgba(0,210,190,0.10);
    --border-mid:    rgba(0,210,190,0.22);
    --border-strong: rgba(0,210,190,0.42);

    --teal:        #00d4b8;
    --teal-dim:    rgba(0,212,184,0.12);
    --teal-glow:   0 0 20px rgba(0,212,184,0.28), 0 0 40px rgba(0,212,184,0.10);
    --teal-glow-sm:0 0 10px rgba(0,212,184,0.20);

    --amber:       #ffaa44;
    --amber-dim:   rgba(255,170,68,0.12);
    --amber-glow:  0 0 16px rgba(255,170,68,0.30);

    --red:         #ff3a5c;
    --red-dim:     rgba(255,58,92,0.12);
    --red-glow:    0 0 18px rgba(255,58,92,0.32);

    --green:       #39ffa0;
    --green-dim:   rgba(57,255,160,0.10);
    --green-glow:  0 0 14px rgba(57,255,160,0.28);

    --text-bright:  #e0ecf8;
    --text-primary: #a8bdd4;
    --text-muted:   #4a6078;
    --text-dim:     #2a3d52;

    --sidebar-bg:   #02060f;
    --sidebar-w:    260px;

    --radius-xs: 4px;
    --radius-sm: 8px;
    --radius-md: 12px;
    --radius-lg: 16px;
    --radius-xl: 20px;

    --shadow-card: 0 2px 12px rgba(0,0,0,0.5), 0 1px 3px rgba(0,0,0,0.4);
    --shadow-glow: 0 0 0 1px rgba(0,212,184,0.15), 0 4px 20px rgba(0,0,0,0.6);
}

/* ═══════════════════════════════════════════════════════
   GLOBAL RESET + BASE
═══════════════════════════════════════════════════════ */
*, *::before, *::after { box-sizing: border-box; }

body, .stApp {
    font-family: 'DM Sans', system-ui, -apple-system, sans-serif !important;
    background: var(--bg-main) !important;
    color: var(--text-primary) !important;
}

/* Scanline overlay on entire app */
.stApp::before {
    content: '';
    position: fixed; inset: 0; z-index: 0; pointer-events: none;
    background-image: repeating-linear-gradient(
        0deg, transparent, transparent 2px, rgba(0,212,184,0.012) 2px, rgba(0,212,184,0.012) 4px
    );
}

#MainMenu, footer, header[data-testid="stHeader"] { display: none !important; }
[data-testid="stDecoration"] { display: none !important; }

/* ═══════════════════════════════════════════════════════
   SIDEBAR
═══════════════════════════════════════════════════════ */
section[data-testid="stSidebar"] {
    background: var(--sidebar-bg) !important;
    border-right: 1px solid var(--border) !important;
}
section[data-testid="stSidebar"] > div:first-child { padding: 0 !important; }
section[data-testid="stSidebar"] .block-container  { padding: 0 !important; }

section[data-testid="stSidebar"] div[data-testid="stButton"] > button {
    background: transparent !important;
    border: 1px solid var(--border) !important;
    color: var(--text-muted) !important;
    border-radius: var(--radius-sm) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 12px !important;
    font-weight: 500 !important;
    letter-spacing: 0.04em !important;
    text-transform: uppercase !important;
    transition: all 0.18s !important;
    margin: 0 14px !important;
    width: calc(100% - 28px) !important;
    padding: 0.5rem 1rem !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] > button:hover {
    background: var(--teal-dim) !important;
    border-color: var(--border-mid) !important;
    color: var(--teal) !important;
    box-shadow: var(--teal-glow-sm) !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, rgba(0,212,184,0.20) 0%, rgba(0,150,140,0.15) 100%) !important;
    border-color: var(--border-strong) !important;
    color: var(--teal) !important;
    box-shadow: var(--teal-glow-sm) !important;
}
section[data-testid="stSidebar"] div[data-testid="stButton"] > button[kind="primary"]:hover {
    background: linear-gradient(135deg, rgba(0,212,184,0.30) 0%, rgba(0,150,140,0.22) 100%) !important;
}

section[data-testid="stSidebar"] div[data-testid="stToggle"] label {
    color: var(--text-muted) !important; font-size: 12px !important;
}
section[data-testid="stSidebar"] div[data-testid="stSlider"] label {
    color: var(--text-muted) !important; font-size: 11px !important;
}
section[data-testid="stSidebar"] div[data-testid="stSlider"] { padding: 0 14px !important; }
section[data-testid="stSidebar"] div[data-testid="stToggle"] { padding: 0 14px !important; }

/* Slider track + thumb teal */
section[data-testid="stSidebar"] [data-testid="stSlider"] [data-baseweb="slider"] [role="slider"] {
    background: var(--teal) !important; box-shadow: var(--teal-glow-sm) !important;
}

/* ═══════════════════════════════════════════════════════
   MAIN CONTENT
═══════════════════════════════════════════════════════ */
.block-container { padding: 1.5rem 2rem 2.5rem 2rem !important; max-width: 100% !important; }

/* Main buttons */
div[data-testid="stButton"] > button {
    background: transparent !important;
    border: 1px solid var(--border-mid) !important;
    color: var(--text-primary) !important;
    border-radius: var(--radius-xs) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 11px !important;
    font-weight: 600 !important;
    letter-spacing: 0.07em !important;
    text-transform: uppercase !important;
    transition: all 0.18s ease !important;
    padding: 0.48rem 1rem !important;
}
div[data-testid="stButton"] > button:hover {
    background: var(--teal-dim) !important;
    border-color: var(--border-strong) !important;
    color: var(--teal) !important;
    box-shadow: var(--teal-glow-sm) !important;
}
div[data-testid="stButton"] > button[kind="primary"] {
    background: linear-gradient(135deg, rgba(0,212,184,0.18), rgba(0,140,120,0.12)) !important;
    border-color: var(--border-strong) !important;
    color: var(--teal) !important;
    box-shadow: var(--teal-glow-sm) !important;
}
div[data-testid="stButton"] > button[kind="primary"]:hover {
    background: linear-gradient(135deg, rgba(0,212,184,0.28), rgba(0,140,120,0.20)) !important;
    box-shadow: var(--teal-glow) !important;
}

div[data-testid="stSlider"] label  { font-size: 11px !important; color: var(--text-muted) !important; }
div[data-testid="stToggle"] label  { font-size: 11px !important; color: var(--text-muted) !important; }
div[data-testid="stForm"]          { border: none !important; padding: 0 !important; }
.stNumberInput label, .stSelectbox label { font-size: 11px !important; color: var(--text-muted) !important; }

/* Streamlit containers transparent */
div[data-testid="stVerticalBlock"] { background: transparent !important; }

/* st.success / st.error */
div[data-testid="stAlert"] {
    background: var(--bg-raised) !important;
    border: 1px solid var(--border-mid) !important;
    border-radius: var(--radius-sm) !important;
}

/* ═══════════════════════════════════════════════════════
   SIDEBAR COMPONENTS
═══════════════════════════════════════════════════════ */
.sb-logo-wrap {
    padding: 28px 20px 22px 20px;
    border-bottom: 1px solid var(--border);
    margin-bottom: 4px;
    position: relative;
}
.sb-logo-wrap::after {
    content: '';
    position: absolute; bottom: 0; left: 20px; right: 20px;
    height: 1px;
    background: linear-gradient(90deg, transparent, var(--teal), transparent);
    opacity: 0.5;
}
.sb-logo-icon {
    width: 42px; height: 42px;
    background: linear-gradient(135deg, rgba(0,212,184,0.25), rgba(0,140,120,0.15));
    border: 1px solid var(--border-strong);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    margin-bottom: 14px;
    box-shadow: var(--teal-glow-sm);
}
.sb-logo-icon .material-symbols-outlined { color: var(--teal) !important; font-size: 22px; }
.sb-brand-title {
    font-family: 'Syne', sans-serif;
    font-size: 17px; font-weight: 800;
    color: var(--text-bright); margin: 0; letter-spacing: -0.02em;
}
.sb-brand-sub {
    font-size: 10px; color: var(--text-muted); margin: 3px 0 0 0;
    letter-spacing: 0.12em; text-transform: uppercase;
    font-family: 'Fira Code', monospace;
}

.sb-section-label {
    font-size: 9px; font-weight: 700; letter-spacing: 0.14em;
    text-transform: uppercase; color: var(--text-dim);
    padding: 18px 20px 7px 20px;
    font-family: 'Fira Code', monospace;
}
.sb-nav-item {
    display: flex; align-items: center; gap: 12px;
    padding: 8px 20px 8px 16px;
    font-size: 13px; font-weight: 500;
    color: var(--text-muted);
    cursor: pointer;
    transition: all 0.14s;
    border-left: 2px solid transparent;
    margin: 1px 0;
    position: relative;
}
.sb-nav-item:hover { background: rgba(0,212,184,0.04); color: var(--text-primary); border-left-color: rgba(0,212,184,0.3); }
.sb-nav-item.active {
    background: var(--teal-dim);
    color: var(--teal);
    border-left-color: var(--teal);
}
.sb-nav-item .material-symbols-outlined { font-size: 17px; }
.sb-nav-badge {
    margin-left: auto;
    background: var(--teal-dim);
    color: var(--teal);
    font-size: 9px; font-weight: 800;
    padding: 2px 7px; border-radius: 99px;
    letter-spacing: 0.06em;
    border: 1px solid var(--border-mid);
    font-family: 'Fira Code', monospace;
}
.sb-divider {
    border: none;
    height: 1px;
    background: linear-gradient(90deg, transparent 10%, var(--border) 50%, transparent 90%);
    margin: 14px 0;
}
.sb-ctrl-label { font-size: 10px; color: var(--text-dim); margin: 0 0 5px 0; font-weight: 700; letter-spacing: 0.08em; text-transform: uppercase; font-family: 'Fira Code', monospace; }

/* ═══════════════════════════════════════════════════════
   TOPBAR
═══════════════════════════════════════════════════════ */
.rc-topbar {
    display: flex;
    justify-content: space-between;
    align-items: center;
    padding: 0 0 1.4rem 0;
    margin-bottom: 1.4rem;
    border-bottom: 1px solid var(--border);
    position: relative;
}
.rc-topbar::after {
    content: '';
    position: absolute; bottom: -1px; left: 0; width: 120px;
    height: 1px; background: linear-gradient(90deg, var(--teal), transparent);
}
.rc-topbar-left  { display: flex; align-items: center; gap: 14px; }
.rc-topbar-title {
    font-family: 'Syne', sans-serif;
    font-size: 22px; font-weight: 800;
    color: var(--text-bright); margin: 0; letter-spacing: -0.03em;
}
.rc-breadcrumb {
    font-size: 11px; color: var(--text-muted);
    display: flex; align-items: center; gap: 5px;
    font-family: 'Fira Code', monospace; margin-top: 2px;
}
.rc-breadcrumb .material-symbols-outlined { font-size: 13px; }
.rc-topbar-right { display: flex; align-items: center; gap: 8px; }
.rc-pill {
    display: flex; align-items: center; gap: 6px;
    background: var(--bg-raised);
    border: 1px solid var(--border);
    border-radius: 4px;
    padding: 5px 12px;
    font-size: 11px; font-weight: 600;
    color: var(--text-muted);
    font-family: 'Fira Code', monospace;
    letter-spacing: 0.04em;
}
.rc-pill .material-symbols-outlined { font-size: 13px; }
.rc-pill-green {
    border-color: rgba(57,255,160,0.25); color: var(--green);
    background: var(--green-dim);
    box-shadow: 0 0 12px rgba(57,255,160,0.10);
}
.rc-pill-teal {
    border-color: var(--border-mid); color: var(--teal);
    background: var(--teal-dim);
    box-shadow: var(--teal-glow-sm);
}
.rc-live-dot {
    width: 7px; height: 7px;
    background: var(--green); border-radius: 50%;
    box-shadow: 0 0 8px var(--green);
    animation: pulse-dot 2s infinite;
}
@keyframes pulse-dot {
    0%,100% { opacity: 1; box-shadow: 0 0 8px var(--green); }
    50%      { opacity: 0.5; box-shadow: 0 0 3px var(--green); }
}

/* ═══════════════════════════════════════════════════════
   HERO BANNER
═══════════════════════════════════════════════════════ */
.rc-hero {
    position: relative;
    border-radius: var(--radius-lg);
    overflow: hidden;
    margin-bottom: 1.4rem;
    background: var(--bg-surface);
    padding: 2.5rem 2.5rem 2.2rem 2.5rem;
    border: 1px solid var(--border);
}
/* Circuit grid */
.rc-hero::before {
    content: '';
    position: absolute; inset: 0;
    background-image:
        linear-gradient(rgba(0,212,184,0.05) 1px, transparent 1px),
        linear-gradient(90deg, rgba(0,212,184,0.05) 1px, transparent 1px);
    background-size: 40px 40px;
    pointer-events: none;
}
/* Radial glow */
.rc-hero::after {
    content: '';
    position: absolute; inset: 0;
    background:
        radial-gradient(ellipse at 70% 50%, rgba(0,212,184,0.14) 0%, transparent 55%),
        radial-gradient(ellipse at 15% 80%, rgba(0,88,200,0.10) 0%, transparent 45%);
    pointer-events: none;
}
.rc-hero-content { position: relative; z-index: 1; display: flex; justify-content: space-between; align-items: flex-start; gap: 2rem; }
.rc-hero-tag {
    display: inline-flex; align-items: center; gap: 7px;
    background: var(--teal-dim);
    border: 1px solid var(--border-strong);
    color: var(--teal);
    font-size: 10px; font-weight: 700; letter-spacing: 0.12em; text-transform: uppercase;
    padding: 4px 12px 4px 9px; border-radius: var(--radius-xs);
    margin-bottom: 16px;
    font-family: 'Fira Code', monospace;
    box-shadow: var(--teal-glow-sm);
}
.rc-hero-tag .material-symbols-outlined { font-size: 12px; color: var(--teal); }
.rc-hero-title {
    font-family: 'Syne', sans-serif;
    color: var(--text-bright);
    font-size: 2.6rem; font-weight: 800;
    margin: 0 0 10px 0;
    letter-spacing: -0.04em; line-height: 1.05;
}
.rc-hero-sub { color: var(--text-muted); font-size: 13px; margin: 0; letter-spacing: 0.01em; }
.rc-hero-stats {
    display: flex; gap: 1px;
    background: var(--border);
    border: 1px solid var(--border-mid);
    border-radius: var(--radius-md);
    overflow: hidden;
    align-self: flex-end;
    min-width: 300px;
    flex-shrink: 0;
}
.rc-hero-stat {
    flex: 1; padding: 16px 20px;
    background: var(--bg-raised);
    text-align: center;
}
.rc-hero-stat-val {
    font-family: 'Syne', sans-serif;
    font-size: 28px; font-weight: 800;
    color: var(--teal); margin: 0;
    letter-spacing: -0.03em;
    text-shadow: 0 0 20px rgba(0,212,184,0.5);
}
.rc-hero-stat-label {
    font-size: 9px; font-weight: 700; letter-spacing: 0.12em;
    text-transform: uppercase; color: var(--text-dim);
    margin: 4px 0 0 0; font-family: 'Fira Code', monospace;
}

/* ═══════════════════════════════════════════════════════
   ALERT BAR
═══════════════════════════════════════════════════════ */
.rc-alert {
    display: flex; align-items: center; gap: 14px;
    background: var(--red-dim);
    border: 1px solid rgba(255,58,92,0.35);
    border-radius: var(--radius-sm);
    padding: 12px 20px;
    margin-bottom: 1.4rem;
    font-size: 13px; font-weight: 600;
    color: var(--red);
    box-shadow: var(--red-glow);
    animation: alert-pulse 3s ease-in-out infinite;
}
.rc-alert .material-symbols-outlined { font-size: 18px; color: var(--red); }
@keyframes alert-pulse {
    0%,100% { box-shadow: 0 0 18px rgba(255,58,92,0.28); }
    50%      { box-shadow: 0 0 32px rgba(255,58,92,0.50); }
}

/* ═══════════════════════════════════════════════════════
   SECTION HEADER
═══════════════════════════════════════════════════════ */
.rc-section-hd { display: flex; justify-content: space-between; align-items: center; margin-bottom: 14px; }
.rc-section-title {
    font-family: 'Syne', sans-serif;
    font-size: 14px; font-weight: 700;
    color: var(--text-bright); margin: 0; letter-spacing: -0.01em;
}
.rc-section-sub {
    font-size: 10px; font-weight: 700; color: var(--text-muted);
    display: flex; align-items: center; gap: 6px;
    font-family: 'Fira Code', monospace; letter-spacing: 0.06em; text-transform: uppercase;
}
.rc-section-dot { width: 6px; height: 6px; background: var(--teal); border-radius: 50%; box-shadow: 0 0 6px var(--teal); }

/* ═══════════════════════════════════════════════════════
   DEVICE CARDS
═══════════════════════════════════════════════════════ */
.rc-card {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 1.2rem;
    height: 100%;
    transition: all 0.22s cubic-bezier(0.16,1,0.3,1);
    position: relative;
    overflow: hidden;
    box-shadow: var(--shadow-card);
}
.rc-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0;
    height: 2px;
    background: transparent;
    transition: background 0.25s;
}
/* Corner accent */
.rc-card::after {
    content: '';
    position: absolute; top: 0; right: 0;
    width: 0; height: 0;
    border-style: solid;
    border-width: 0 18px 18px 0;
    border-color: transparent var(--border) transparent transparent;
    transition: border-color 0.22s;
}
.rc-card.on {
    border-color: var(--border-mid);
    box-shadow: var(--shadow-glow), 0 0 0 1px rgba(0,212,184,0.08);
}
.rc-card.on::before { background: linear-gradient(90deg, var(--teal), rgba(0,212,184,0.3)); }
.rc-card.on::after  { border-color: transparent var(--border-strong) transparent transparent; }

.rc-card:hover {
    border-color: var(--border-mid);
    transform: translateY(-1px);
    box-shadow: var(--shadow-card), 0 6px 20px rgba(0,0,0,0.4);
}

.rc-device-hd { display: flex; justify-content: space-between; align-items: flex-start; margin-bottom: 12px; }
.rc-device-icon-wrap {
    width: 46px; height: 46px;
    background: var(--bg-raised);
    border: 1px solid var(--border);
    border-radius: 10px;
    display: flex; align-items: center; justify-content: center;
    transition: all 0.22s;
}
.rc-card.on .rc-device-icon-wrap {
    background: var(--teal-dim);
    border-color: var(--border-mid);
    box-shadow: var(--teal-glow-sm);
}
.rc-device-icon { font-size: 22px; color: var(--text-muted); }
.rc-card.on .rc-device-icon {
    color: var(--teal);
    font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 24;
    text-shadow: 0 0 12px rgba(0,212,184,0.6);
}

.rc-status-badge {
    display: inline-flex; align-items: center; gap: 4px;
    font-size: 9px; font-weight: 800; letter-spacing: 0.10em;
    text-transform: uppercase; padding: 3px 9px; border-radius: var(--radius-xs);
    font-family: 'Fira Code', monospace;
}
.rc-status-on       { background: var(--teal-dim); color: var(--teal); border: 1px solid var(--border-mid); box-shadow: var(--teal-glow-sm); }
.rc-status-off      { background: var(--bg-raised); color: var(--text-dim); border: 1px solid var(--border); }
.rc-status-locked   { background: var(--bg-raised); color: var(--text-muted); border: 1px solid var(--border); }
.rc-status-unlocked { background: var(--green-dim); color: var(--green); border: 1px solid rgba(57,255,160,0.3); box-shadow: 0 0 8px rgba(57,255,160,0.15); }

.rc-device-name {
    font-family: 'Syne', sans-serif;
    font-size: 14px; font-weight: 700; color: var(--text-bright); margin: 0 0 3px 0;
}
.rc-device-id {
    font-size: 9px; color: var(--text-dim);
    font-family: 'Fira Code', monospace; margin: 0;
    letter-spacing: 0.06em; text-transform: uppercase;
}
.rc-device-meta {
    font-size: 11px; color: var(--text-muted);
    margin: 10px 0 0 0;
    min-height: 16px;
}

/* AC bar */
.rc-temp-bar { position: relative; height: 2px; background: var(--bg-raised); border-radius: 999px; margin-top: 12px; }
.rc-temp-fill {
    position: absolute; top: 0; left: 0; height: 100%;
    background: linear-gradient(90deg, rgba(0,212,184,0.4), var(--teal));
    border-radius: 999px; transition: width 0.4s ease;
    box-shadow: 0 0 8px rgba(0,212,184,0.4);
}
.rc-temp-thumb {
    position: absolute; top: 50%; transform: translate(-50%,-50%);
    width: 9px; height: 9px;
    background: var(--teal); border-radius: 50%;
    box-shadow: 0 0 8px var(--teal);
}

/* ═══════════════════════════════════════════════════════
   SENSOR GRID
═══════════════════════════════════════════════════════ */
.rc-sensor-row { display: grid; grid-template-columns: repeat(5, 1fr); gap: 6px; margin-top: 12px; }
.rc-sensor-chip {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-sm);
    padding: 10px 5px 8px 5px;
    display: flex; flex-direction: column;
    align-items: center; gap: 4px; text-align: center;
    transition: all 0.18s;
}
.rc-sensor-chip:hover { border-color: var(--border-mid); }
.rc-sensor-chip.warn   { border-color: rgba(255,170,68,0.35); background: var(--amber-dim); }
.rc-sensor-chip.danger { border-color: rgba(255,58,92,0.35);  background: var(--red-dim); }
.rc-s-icon { font-size: 15px; color: var(--text-muted); }
.rc-sensor-chip.warn   .rc-s-icon { color: var(--amber); }
.rc-sensor-chip.danger .rc-s-icon { color: var(--red); }
.rc-s-val {
    font-family: 'Syne', sans-serif;
    font-size: 12px; font-weight: 700; color: var(--text-primary); letter-spacing: 0.02em;
}
.rc-sensor-chip.warn   .rc-s-val { color: var(--amber); }
.rc-sensor-chip.danger .rc-s-val { color: var(--red); }
.rc-s-label {
    font-size: 8px; font-weight: 700; letter-spacing: 0.10em;
    text-transform: uppercase; color: var(--text-dim);
    font-family: 'Fira Code', monospace;
}

/* ═══════════════════════════════════════════════════════
   WEATHER
═══════════════════════════════════════════════════════ */
.rc-weather {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 1.2rem 1.4rem;
    box-shadow: var(--shadow-card);
}
.rc-wx-main   { display: flex; align-items: center; gap: 16px; margin-bottom: 14px; }
.rc-wx-icon   {
    font-size: 46px; color: var(--amber);
    font-variation-settings: 'FILL' 1, 'wght' 400, 'GRAD' 0, 'opsz' 48;
    text-shadow: 0 0 20px rgba(255,170,68,0.5);
    filter: drop-shadow(0 0 8px rgba(255,170,68,0.35));
}
.rc-wx-temp {
    font-family: 'Syne', sans-serif;
    font-size: 3rem; font-weight: 800; color: var(--text-bright); margin: 0;
    letter-spacing: -0.05em; line-height: 1;
}
.rc-wx-loc { font-size: 11px; color: var(--text-muted); margin: 4px 0 0 0; display: flex; align-items: center; gap: 4px; font-family: 'Fira Code', monospace; }
.rc-wx-metrics {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 1px; background: var(--border);
    border-radius: var(--radius-sm); overflow: hidden;
    border: 1px solid var(--border);
}
.rc-wx-metric   { background: var(--bg-raised); padding: 9px 6px; text-align: center; }
.rc-wx-m-label  {
    font-size: 8px; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase;
    color: var(--text-dim); margin: 0; font-family: 'Fira Code', monospace;
}
.rc-wx-m-val    { font-family: 'Syne', sans-serif; font-size: 13px; font-weight: 700; color: var(--text-primary); margin: 4px 0 0 0; }
.rc-wx-m-val.good { color: var(--teal); text-shadow: 0 0 10px rgba(0,212,184,0.35); }

/* ═══════════════════════════════════════════════════════
   ROBOT CARD
═══════════════════════════════════════════════════════ */
.rc-robot-card {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 1.3rem;
    box-shadow: var(--shadow-card);
    margin-bottom: 10px;
    position: relative; overflow: hidden;
}
.rc-robot-card::before {
    content: '';
    position: absolute; top: 0; left: 0; right: 0; height: 1px;
    background: linear-gradient(90deg, transparent, var(--teal), transparent);
    opacity: 0.6;
}
.rc-robot-hd { display: flex; align-items: center; gap: 14px; }
.rc-robot-avatar {
    position: relative;
    width: 58px; height: 58px;
    background: var(--teal-dim);
    border: 1px solid var(--border-strong);
    border-radius: 14px;
    display: flex; align-items: center; justify-content: center;
    flex-shrink: 0;
    box-shadow: var(--teal-glow-sm);
}
.rc-robot-avatar .material-symbols-outlined {
    color: var(--teal) !important; font-size: 26px;
    text-shadow: 0 0 14px rgba(0,212,184,0.7);
}
.rc-robot-status-dot {
    position: absolute; bottom: -2px; right: -2px;
    width: 12px; height: 12px;
    background: var(--green);
    border: 2px solid var(--bg-surface);
    border-radius: 50%;
    box-shadow: 0 0 8px var(--green);
}
.rc-robot-name {
    font-family: 'Syne', sans-serif;
    font-size: 15px; font-weight: 800; color: var(--text-bright); margin: 0 0 3px 0;
}
.rc-robot-state { font-size: 11px; color: var(--text-muted); display: flex; align-items: center; gap: 5px; margin: 0; font-family: 'Fira Code', monospace; }
.rc-robot-meta { flex: 1; }
.rc-bat-row { display: flex; justify-content: space-between; align-items: center; margin: 12px 0 5px 0; }
.rc-bat-label { font-size: 11px; color: var(--text-muted); font-family: 'Fira Code', monospace; text-transform: uppercase; letter-spacing: 0.08em; }
.rc-bat-val   {
    font-family: 'Syne', sans-serif; font-size: 14px; font-weight: 700; color: var(--teal);
    text-shadow: 0 0 10px rgba(0,212,184,0.4);
}
.rc-bat-track { height: 3px; background: var(--bg-raised); border-radius: 999px; border: 1px solid var(--border); }
.rc-bat-fill  { height: 100%; background: linear-gradient(90deg, rgba(0,212,184,0.5), var(--teal)); border-radius: 999px; box-shadow: 0 0 8px rgba(0,212,184,0.4); }
.rc-info-row  { display: flex; align-items: center; gap: 7px; margin-top: 10px; font-size: 11px; color: var(--text-muted); font-family: 'Fira Code', monospace; }
.rc-info-row .material-symbols-outlined { font-size: 14px; color: var(--teal); }
.rc-robot-map {
    background:
        radial-gradient(circle at top right, rgba(0,212,184,0.12), transparent 32%),
        linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.00)),
        var(--bg-raised);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 0.55rem;
    margin-top: 12px;
}
.rc-robot-map svg { display: block; width: 100%; height: auto; }
.rc-robot-note {
    margin-top: 10px;
    font-size: 11px;
    color: var(--text-muted);
    font-family: 'Fira Code', monospace;
}

/* ═══════════════════════════════════════════════════════
   POMODORO CARD
═══════════════════════════════════════════════════════ */
.rc-pomo-card {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-md);
    padding: 1.3rem;
    box-shadow: var(--shadow-card);
}
.rc-pomo-hd {
    display: flex; align-items: center; gap: 9px;
    font-family: 'Syne', sans-serif;
    font-size: 14px; font-weight: 700; color: var(--text-bright);
    margin-bottom: 14px;
}
.rc-pomo-hd .material-symbols-outlined { font-size: 17px; color: var(--teal); }

/* ═══════════════════════════════════════════════════════
   TERMINAL
═══════════════════════════════════════════════════════ */
.rc-terminal {
    background: var(--bg-deepest);
    border: 1px solid var(--border-mid);
    border-radius: var(--radius-md);
    overflow: hidden;
    box-shadow: 0 0 0 1px rgba(0,212,184,0.06), 0 8px 32px rgba(0,0,0,0.7);
    position: relative;
}
.rc-term-titlebar {
    background: var(--bg-surface);
    border-bottom: 1px solid var(--border);
    padding: 10px 16px;
    display: flex; justify-content: space-between; align-items: center;
}
.rc-term-dots { display: flex; gap: 6px; }
.rc-term-dot  { width: 11px; height: 11px; border-radius: 50%; }
.rc-term-title {
    font-size: 10px; font-weight: 600; color: var(--text-muted);
    letter-spacing: 0.10em; text-transform: uppercase;
    font-family: 'Fira Code', monospace;
}
.rc-term-version { font-size: 10px; color: var(--text-dim); font-family: 'Fira Code', monospace; }
.rc-term-body {
    padding: 16px 18px;
    min-height: 250px; max-height: 290px;
    overflow-y: auto;
    font-family: 'Fira Code', monospace;
    font-size: 12px; line-height: 1.8;
}
/* CRT scan inside terminal */
.rc-term-body::before {
    content: '';
    position: absolute; inset: 40px 0 0 0;
    background-image: repeating-linear-gradient(
        0deg, transparent, transparent 3px, rgba(0,212,184,0.015) 3px, rgba(0,212,184,0.015) 4px
    );
    pointer-events: none; z-index: 0;
}
.rc-term-row { margin-bottom: 1px; white-space: pre-wrap; word-break: break-all; position: relative; z-index: 1; }
.ttime  { color: var(--text-dim); }
.tok    { color: var(--teal); text-shadow: 0 0 8px rgba(0,212,184,0.4); }
.terr   { color: var(--red); text-shadow: 0 0 8px rgba(255,58,92,0.35); }
.tinfo  { color: #4488ff; }
.tact   { color: var(--text-primary); }
.tempty { color: var(--text-dim); }

/* Scrollbar inside terminal */
.rc-term-body::-webkit-scrollbar { width: 3px; }
.rc-term-body::-webkit-scrollbar-track { background: transparent; }
.rc-term-body::-webkit-scrollbar-thumb { background: var(--border-mid); border-radius: 2px; }

/* ═══════════════════════════════════════════════════════
   CHAT
═══════════════════════════════════════════════════════ */
.rc-chat-frame {
    background: var(--bg-surface);
    border: 1px solid var(--border);
    border-radius: var(--radius-lg);
    overflow: hidden;
    box-shadow: var(--shadow-card);
    margin-bottom: 8px;
}
.rc-chat-header {
    background: var(--bg-raised);
    border-bottom: 1px solid var(--border);
    padding: 14px 22px;
    display: flex; justify-content: space-between; align-items: center;
    position: relative;
}
.rc-chat-header::after {
    content: '';
    position: absolute; bottom: -1px; left: 0; width: 80px;
    height: 1px; background: linear-gradient(90deg, var(--teal), transparent);
}
.rc-chat-agent { display: flex; align-items: center; gap: 14px; }
.rc-agent-avatar {
    width: 42px; height: 42px;
    background: var(--teal-dim);
    border: 1px solid var(--border-strong);
    border-radius: 12px;
    display: flex; align-items: center; justify-content: center;
    color: var(--teal); font-size: 20px;
    box-shadow: var(--teal-glow-sm);
}
.rc-agent-avatar .material-symbols-outlined {
    color: var(--teal) !important;
    text-shadow: 0 0 12px rgba(0,212,184,0.6);
}
.rc-agent-name  {
    font-family: 'Syne', sans-serif; font-size: 14px; font-weight: 800; color: var(--text-bright); margin: 0;
}
.rc-agent-status {
    font-size: 10px; color: var(--green);
    display: flex; align-items: center; gap: 5px; margin: 3px 0 0 0;
    font-family: 'Fira Code', monospace; letter-spacing: 0.06em;
}
.rc-agent-status .material-symbols-outlined { font-size: 12px; text-shadow: 0 0 6px var(--green); }
.rc-chat-meta { display: flex; gap: 24px; }
.rc-chat-meta-item { text-align: right; }
.rc-chat-meta-label {
    font-size: 9px; font-weight: 800; letter-spacing: 0.12em; text-transform: uppercase;
    color: var(--text-dim); margin: 0; font-family: 'Fira Code', monospace;
}
.rc-chat-meta-val {
    font-family: 'Syne', sans-serif; font-size: 12px; font-weight: 700; color: var(--text-primary); margin: 3px 0 0 0;
}
.rc-chat-meta-val.accent { color: var(--teal); text-shadow: 0 0 10px rgba(0,212,184,0.3); }

.rc-msg-ai   { display: flex; gap: 10px; margin-bottom: 14px; max-width: 76%; }
.rc-msg-user { display: flex; flex-direction: row-reverse; gap: 10px; margin-bottom: 14px; margin-left: auto; max-width: 76%; }
.rc-msg-icon {
    width: 30px; height: 30px; border-radius: 8px;
    background: var(--bg-raised); border: 1px solid var(--border);
    display: flex; align-items: center; justify-content: center;
    font-size: 14px; flex-shrink: 0; color: var(--text-muted);
}
.rc-msg-user .rc-msg-icon {
    background: var(--teal-dim); border-color: var(--border-mid); color: var(--teal);
}
.rc-bubble-ai {
    background: var(--bg-raised);
    border: 1px solid var(--border);
    padding: 10px 15px;
    border-radius: 12px; border-top-left-radius: 4px;
    font-size: 13px; color: var(--text-primary); line-height: 1.6;
}
.rc-bubble-user {
    background: var(--teal-dim);
    border: 1px solid var(--border-mid);
    color: var(--teal);
    padding: 10px 15px;
    border-radius: 12px; border-top-right-radius: 4px;
    font-size: 13px; line-height: 1.6;
    box-shadow: var(--teal-glow-sm);
}

/* ═══════════════════════════════════════════════════════
   INPUTS (chat)
═══════════════════════════════════════════════════════ */
div[data-testid="stChatInput"] textarea {
    background: var(--bg-raised) !important;
    border-color: var(--border-mid) !important;
    color: var(--text-bright) !important;
    font-family: 'DM Sans', sans-serif !important;
    font-size: 13px !important;
    border-radius: var(--radius-sm) !important;
}
div[data-testid="stChatInput"] textarea:focus {
    border-color: var(--border-strong) !important;
    box-shadow: var(--teal-glow-sm) !important;
}
div[data-testid="stChatInput"] button {
    background: var(--teal-dim) !important;
    border-color: var(--border-mid) !important;
    color: var(--teal) !important;
}

/* number input, selectbox dark */
div[data-testid="stNumberInput"] input,
div[data-testid="stSelectbox"] div[data-baseweb="select"] > div {
    background: var(--bg-raised) !important;
    border-color: var(--border-mid) !important;
    color: var(--text-primary) !important;
    font-family: 'DM Sans', sans-serif !important;
}

/* spinner */
div[data-testid="stSpinner"] { color: var(--teal) !important; }
</style>
""", unsafe_allow_html=True)


# ── helpers ──────────────────────────────────────────────────────────────────

def init_session():
    load_env_file()
    if "robot_state" not in st.session_state:
        st.session_state.robot_state = "idle"
    if "focus_mode" not in st.session_state:
        st.session_state.focus_mode = False
    if "voice_status_message" not in st.session_state:
        st.session_state.voice_status_message = None
    if "voice_assistant" not in st.session_state:
        st.session_state.voice_assistant = None
    if "agent" not in st.session_state:
        st.session_state.agent = AgentRobot(nom_utilisateur="Monssef")
        st.session_state.historique_chat = []
        st.session_state.meteo_api = MeteoAPI(ville="Rabat", pays="MA")
        st.session_state.meteo_data = None
        st.session_state.derniere_maj_meteo = None
        st.session_state.robot_voix = RobotVoix(langue="fr")
        st.session_state.auto_play_voice = False
        st.session_state.last_manual_result = None
        st.session_state.last_robot_result = None
        st.session_state.last_voice_message = None
        st.session_state.live_refresh = os.environ.get("IOT_MODE", "simulator").strip().lower() == "hardware"
        robot_state = st.session_state.agent.robot.etat()
        st.session_state.robot_trace = [(robot_state["position"]["x"], robot_state["position"]["y"])]
        st.session_state.robot_nav_target = "kitchen"
        st.session_state.maison = MaisonConnectee()
        st.session_state.agent.mettre_a_jour_maison(st.session_state.maison)
    if "last_robot_result" not in st.session_state:
        st.session_state.last_robot_result = None


def apply_focus_mode_styles():
    if not st.session_state.get("focus_mode"):
        return

    st.markdown(
        """
        <style>
        section[data-testid="stSidebar"] {
            display: none !important;
        }
        [data-testid="stSidebarCollapsedControl"] {
            display: none !important;
        }
        .main .block-container {
            max-width: 1200px !important;
            padding-top: 1.5rem !important;
            padding-left: 1rem !important;
            padding-right: 1rem !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    if "robot_trace" not in st.session_state:
        robot_state = st.session_state.agent.robot.etat()
        st.session_state.robot_trace = [(robot_state["position"]["x"], robot_state["position"]["y"])]
    if "robot_nav_target" not in st.session_state:
        st.session_state.robot_nav_target = "kitchen"


def refresh_weather():
    now = datetime.now()
    due = (
        st.session_state.meteo_data is None
        or st.session_state.derniere_maj_meteo is None
        or (now - st.session_state.derniere_maj_meteo).seconds > 1800
    )
    if due:
        try:
            st.session_state.meteo_data = st.session_state.meteo_api.obtenir_meteo()
            st.session_state.derniere_maj_meteo = now
            st.session_state.agent.mettre_a_jour_meteo(st.session_state.meteo_data)
        except Exception:
            pass


def current_snapshot():
    snapshot = st.session_state.agent.iot_controller.get_snapshot()
    room_id = st.session_state.get("selected_room_id", "living_room")
    rooms = snapshot.get("rooms", {})
    if room_id not in rooms and rooms:
        room_id = next(iter(rooms))
        st.session_state.selected_room_id = room_id
    current_room = rooms.get(room_id, {})
    st.session_state.agent.mettre_a_jour_capteurs(current_room.get("sensors", {}))
    return snapshot, current_room


def _room_name(room_id, room):
    return room_name(room_id, room)


def _room_choices(snapshot):
    rooms = snapshot.get("rooms", {})
    ordered_ids = ordered_room_ids(rooms)
    return ordered_ids, {_room_name(room_id, rooms[room_id]): room_id for room_id in ordered_ids}


def _room_device_count(room):
    return sum(1 for device in room.get("devices", {}).values() if device.get("state") in {"on", "unlocked"})


def _set_active_room(room_id, room_label=None):
    st.session_state.selected_room_id = room_id


def _device_name(device, fallback):
    return device.get("name") or fallback


def _device_code(device, fallback):
    return (device.get("id") or fallback).upper()


def _light_meta(device, sensors):
    brightness = device.get("brightness", 0)
    lux = sensors.get("light_level", 0)
    return f"{brightness}% brightness • {lux} lux"


def _ac_badge(ac):
    return "ON" if ac.get("state") == "on" else "OFF"


def _ac_meta(ac, sensors):
    room_temp = sensors.get("temperature", 0)
    target_temp = ac.get("target_temp", 22)
    return f"Room {room_temp}°C • Target {target_temp}°C"


def _door_meta(door, sensors):
    occupancy = sensors.get("occupancy", False)
    occupancy_label = "Occupied" if occupancy else "No occupancy"
    current_state = door.get("state", "locked").capitalize()
    return f"Current: {current_state} • {occupancy_label}"


def _gas_meta(sensors, alerts):
    gas_ppm = sensors.get("gas_ppm", 0)
    gas_state = "ON" if gas_ppm > 0 else "OFF"
    alert_text = "Alert" if alerts.get("gas", False) and gas_ppm > 400 else "Normal"
    return f"{gas_state} • {gas_ppm} ppm • {alert_text}"


def _append_robot_trace():
    etat = st.session_state.agent.robot.etat()
    point = (round(etat["position"]["x"], 1), round(etat["position"]["y"], 1))
    trace = st.session_state.robot_trace
    if not trace or trace[-1] != point:
        trace.append(point)
    st.session_state.robot_trace = trace[-90:]


def _navigation_route_points(etat_robot, target_zone):
    if not target_zone:
        return []

    route_nodes = {
        "living_room": {"entry": (-20.0, 95.0), "center": (-120.0, 95.0)},
        "hallway": {"entry": (0.0, 20.0), "center": (0.0, 20.0)},
        "kitchen": {"entry": (20.0, 95.0), "center": (95.0, 115.0)},
        "bedroom": {"entry": (20.0, -55.0), "center": (95.0, -55.0)},
        "toilet": {"entry": (170.0, 95.0), "center": (210.0, 100.0)},
        "garage": {"entry": (170.0, -55.0), "center": (228.0, -55.0)},
    }
    hallway_hubs = {
        "upper": (0.0, 95.0),
        "lower": (0.0, -55.0),
    }

    current_zone = etat_robot.get("zone")
    current_pos = (float(etat_robot["position"]["x"]), float(etat_robot["position"]["y"]))
    if target_zone not in route_nodes:
        return [current_pos]

    if current_zone == target_zone:
        return [current_pos, route_nodes[target_zone]["center"]]

    points = [current_pos]

    def add_if_new(point):
        rounded = (round(point[0], 1), round(point[1], 1))
        if points[-1] != rounded:
            points.append(rounded)

    zone_to_hub = {
        "living_room": "upper",
        "kitchen": "upper",
        "toilet": "upper",
        "bedroom": "lower",
        "garage": "lower",
        "hallway": "upper",
    }
    target_hub = "lower" if target_zone in {"bedroom", "garage"} else "upper"

    if current_zone in route_nodes and current_zone != "hallway":
        add_if_new(route_nodes[current_zone]["entry"])
        add_if_new(hallway_hubs[zone_to_hub.get(current_zone, "upper")])
    elif current_zone == "hallway":
        current_hub = "lower" if current_pos[1] < 0 else "upper"
        add_if_new(hallway_hubs[current_hub])

    add_if_new(hallway_hubs[target_hub])
    add_if_new(route_nodes[target_zone]["entry"])
    add_if_new(route_nodes[target_zone]["center"])
    return points


def _navigation_hint(etat_robot, target_zone):
    route = _navigation_route_points(etat_robot, target_zone)
    if len(route) < 2:
        return "Select a room to get a route hint."

    current = route[0]
    next_point = None
    for point in route[1:]:
        dx = point[0] - current[0]
        dy = point[1] - current[1]
        if abs(dx) > 6 or abs(dy) > 6:
            next_point = point
            break

    if next_point is None:
        return f"You are already at the {target_zone.replace('_', ' ')} target area."

    dx = next_point[0] - current[0]
    dy = next_point[1] - current[1]
    distance = int(round(math.hypot(dx, dy)))
    absolute_angle = (math.degrees(math.atan2(dx, dy)) + 360.0) % 360.0
    turn_delta = ((absolute_angle - etat_robot["direction"] + 540.0) % 360.0) - 180.0

    if abs(turn_delta) <= 20:
        turn_text = "Go forward"
    elif turn_delta > 0:
        turn_text = f"Turn right about {int(round(turn_delta / 5.0) * 5)}deg"
    else:
        turn_text = f"Turn left about {int(round(abs(turn_delta) / 5.0) * 5)}deg"

    return f"{turn_text}, then move about {distance}cm toward {target_zone.replace('_', ' ').title()}."


def _robot_visual_svg(etat_robot, trace_points, snapshot, navigation_points=None):
    width = 420
    height = 290
    pad = 20
    world = ROBOT_SIMULATION_WORLD
    walkable_areas = world["walkable_areas"]
    obstacles = world["obstacles"]
    components = world.get("components", [])
    zone_id = etat_robot.get("zone")
    rooms_state = snapshot.get("rooms", {})

    min_x = min(area["x1"] for area in walkable_areas) - 10
    max_x = max(area["x2"] for area in walkable_areas) + 10
    min_y = min(area["y1"] for area in walkable_areas) - 10
    max_y = max(area["y2"] for area in walkable_areas) + 10
    scale_x = (width - pad * 2) / (max_x - min_x)
    scale_y = (height - pad * 2) / (max_y - min_y)
    scale = min(scale_x, scale_y)

    def to_canvas(x_cm, y_cm):
        x = pad + (x_cm - min_x) * scale
        y = height - pad - (y_cm - min_y) * scale
        return round(x, 1), round(y, 1)

    def rect_to_svg(rect):
        x1, y1 = to_canvas(rect["x1"], rect["y2"])
        x2, y2 = to_canvas(rect["x2"], rect["y1"])
        return x1, y1, round(x2 - x1, 1), round(y2 - y1, 1)

    trace_svg = ""
    if len(trace_points) > 1:
        path_points = " ".join(
            f"{px},{py}" for px, py in (to_canvas(x, y) for x, y in trace_points)
        )
        trace_svg = (
            f"<polyline points='{path_points}' fill='none' "
            "stroke='rgba(255,170,68,0.95)' stroke-width='3' stroke-linecap='round' stroke-linejoin='round'/>"
        )

    nav_svg = ""
    if navigation_points and len(navigation_points) > 1:
        nav_points = " ".join(
            f"{px},{py}" for px, py in (to_canvas(x, y) for x, y in navigation_points)
        )
        target_x, target_y = to_canvas(navigation_points[-1][0], navigation_points[-1][1])
        nav_svg = (
            f"<polyline points='{nav_points}' fill='none' "
            "stroke='rgba(0,212,184,0.80)' stroke-width='3' stroke-linecap='round' stroke-linejoin='round' "
            "stroke-dasharray='7 6'/>"
            f"<circle cx='{target_x}' cy='{target_y}' r='9' fill='rgba(0,212,184,0.18)' stroke='#00d4b8' stroke-width='2'/>"
            f"<circle cx='{target_x}' cy='{target_y}' r='3' fill='#dff7f3'/>"
        )

    robot_x, robot_y = to_canvas(etat_robot["position"]["x"], etat_robot["position"]["y"])
    angle = math.radians(etat_robot["direction"])
    head_x = round(robot_x + math.sin(angle) * 18, 1)
    head_y = round(robot_y - math.cos(angle) * 18, 1)

    room_svg = []
    for area in walkable_areas:
        x, y, w, h = rect_to_svg(area)
        active_fill = "rgba(0,212,184,0.12)" if area["id"] == zone_id else "rgba(4,8,16,0.72)"
        active_stroke = "rgba(0,212,184,0.42)" if area["id"] == zone_id else "rgba(0,212,184,0.18)"
        room_svg.append(
            f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='12' fill='{active_fill}' "
            f"stroke='{active_stroke}' stroke-width='1.5'/>"
            f"<text x='{x + 10}' y='{y + 18}' fill='#6f8aa4' font-size='10' font-family='DM Sans, sans-serif'>{escape(area['label'])}</text>"
        )

    obstacle_svg = []
    for obstacle in obstacles:
        x, y, w, h = rect_to_svg(obstacle)
        obstacle_svg.append(
            f"<rect x='{x}' y='{y}' width='{w}' height='{h}' rx='8' fill='rgba(255,170,68,0.12)' "
            "stroke='rgba(255,170,68,0.32)' stroke-width='1.2'/>"
            f"<text x='{x + 6}' y='{y + 16}' fill='#c9924f' font-size='8' font-family='DM Sans, sans-serif'>{escape(obstacle['label'])}</text>"
        )

    component_svg = []
    for component in components:
        room_state = rooms_state.get(component["room_id"], {})
        devices = room_state.get("devices", {})
        sensors = room_state.get("sensors", {})

        if component["kind"] == "sensor":
            active = True
            accent = "#7eb6ff"
        elif component["kind"] == "gas":
            gas_ppm = sensors.get(component["component_id"], 0)
            active = gas_ppm > 0
            accent = "#ff3a5c" if gas_ppm > 400 else "#ffaa44" if gas_ppm > 0 else "#4a6078"
        elif component["kind"] == "door":
            active = devices.get(component["component_id"], {}).get("state") == "unlocked"
            accent = "#39ffa0" if active else "#7b8697"
        elif component["kind"] == "light":
            active = devices.get(component["component_id"], {}).get("state") == "on"
            accent = "#ffd166" if active else "#4a6078"
        elif component["kind"] == "ac":
            active = devices.get(component["component_id"], {}).get("state") == "on"
            accent = "#59c3ff" if active else "#4a6078"
        elif component["kind"] == "buzzer":
            active = devices.get(component["component_id"], {}).get("state") == "on"
            accent = "#ff7a59" if active else "#4a6078"
        else:
            active = False
            accent = "#4a6078"

        cx, cy = to_canvas(component["x"], component["y"])
        glow = (
            f"<circle cx='{cx}' cy='{cy}' r='14' fill='{accent}' opacity='0.18'/>"
            if active else ""
        )
        stroke = accent if active else "rgba(126,144,167,0.55)"
        fill = "rgba(8,16,29,0.95)"
        component_svg.append(
            f"{glow}"
            f"<circle cx='{cx}' cy='{cy}' r='10' fill='{fill}' stroke='{stroke}' stroke-width='1.8'/>"
            f"<text x='{cx}' y='{cy + 3}' text-anchor='middle' fill='{stroke}' font-size='7' font-family='Fira Code, monospace'>{escape(component['label'])}</text>"
        )

    scan_svg = ""
    last_scan = etat_robot.get("last_scan") or {}
    if last_scan:
        beams = []
        labels = []
        directions = [
            ("F", etat_robot["direction"], last_scan.get("avant", 0)),
            ("R", etat_robot["direction"] + 90, last_scan.get("droite", 0)),
            ("L", etat_robot["direction"] - 90, last_scan.get("gauche", 0)),
            ("B", etat_robot["direction"] + 180, last_scan.get("arriere", 0)),
        ]
        for label, angle_deg, distance in directions:
            angle_rad = math.radians(angle_deg)
            end_x, end_y = to_canvas(
                etat_robot["position"]["x"] + math.sin(angle_rad) * distance,
                etat_robot["position"]["y"] + math.cos(angle_rad) * distance,
            )
            beams.append(
                f"<line x1='{robot_x}' y1='{robot_y}' x2='{end_x}' y2='{end_y}' "
                "stroke='rgba(57,255,160,0.30)' stroke-width='2' stroke-dasharray='5 5'/>"
            )
            labels.append(
                f"<text x='{end_x + 4}' y='{end_y - 4}' fill='#39ffa0' font-size='8' font-family='Fira Code, monospace'>{label}:{distance}</text>"
            )
        scan_svg = "".join(beams + labels)

    return f"""
    <svg viewBox="0 0 {width} {height}" xmlns="http://www.w3.org/2000/svg" role="img" aria-label="Robot movement map">
      <rect x="1" y="1" width="{width - 2}" height="{height - 2}" rx="16" fill="#08101d" stroke="rgba(0,212,184,0.18)"/>
      <path d="M {width/2} {pad} V {height-pad}" stroke="rgba(0,212,184,0.06)" stroke-dasharray="4 6"/>
      <path d="M {pad} {height/2} H {width-pad}" stroke="rgba(0,212,184,0.06)" stroke-dasharray="4 6"/>
      {''.join(room_svg)}
      {''.join(obstacle_svg)}
      {''.join(component_svg)}
      {trace_svg}
      {nav_svg}
      {scan_svg}
      <circle cx="{robot_x}" cy="{robot_y}" r="12" fill="#00d4b8" stroke="#dff7f3" stroke-width="2"/>
      <line x1="{robot_x}" y1="{robot_y}" x2="{head_x}" y2="{head_y}" stroke="#dff7f3" stroke-width="3" stroke-linecap="round"/>
      <circle cx="{robot_x}" cy="{robot_y}" r="3" fill="#08101d"/>
    </svg>
    """


def _run_robot_action(action):
    robot = st.session_state.agent.robot
    if action == "forward":
        result = robot.avancer(20)
        _append_robot_trace()
    elif action == "backward":
        result = robot.reculer(20)
        _append_robot_trace()
    elif action == "left":
        result = robot.tourner_gauche(45)
    elif action == "right":
        result = robot.tourner_droite(45)
    elif action == "scan":
        result, _ = robot.scanner()
    elif action == "charge":
        result = robot.recharger()
    elif action == "clear":
        st.session_state.robot_trace = []
        _append_robot_trace()
        result = "Robot path cleared."
    else:
        result = "Unknown robot action."

    st.session_state.last_robot_result = result


def _render_robot_visual(etat_robot, trace_points, snapshot, navigation_points=None):
    svg = _robot_visual_svg(etat_robot, trace_points, snapshot, navigation_points)
    html = f"""
    <div style="margin-top:12px;">
      <div style="
        background:
          radial-gradient(circle at top right, rgba(0,212,184,0.12), transparent 32%),
          linear-gradient(180deg, rgba(255,255,255,0.02), rgba(255,255,255,0.00)),
          #0d1829;
        border:1px solid rgba(0,212,184,0.10);
        border-radius:12px;
        padding:8px;
      ">
        {svg}
      </div>
    </div>
    """
    components.html(html, height=320)


def _expected_device_state(action, device_type, parameters):
    if device_type == "light":
        if action == "turn_on":
            return "on"
        if action == "turn_off":
            return "off"
    if device_type == "ac":
        if action == "turn_on":
            return "on"
        if action == "turn_off":
            return "off"
    if device_type == "door":
        if action == "lock":
            return "locked"
        if action == "unlock":
            return "unlocked"
    return None


def wait_for_hardware_sync(action, room_id, device_type=None, parameters=None, timeout_s=2.5):
    expected_state = _expected_device_state(action, device_type, parameters or {})
    if not expected_state or not device_type:
        return

    device_id_map = {
        "light": "light_main",
        "ac": "ac_main",
        "door": "door_main",
    }
    device_id = device_id_map.get(device_type)
    if not device_id:
        return

    deadline = time.time() + timeout_s
    while time.time() < deadline:
        try:
            state = load_state()
            current_state = (
                state.get("rooms", {})
                .get(room_id, {})
                .get("devices", {})
                .get(device_id, {})
                .get("state")
            )
            if current_state == expected_state:
                return
        except Exception:
            pass
        time.sleep(0.12)


@st.dialog("⚠️ Gas Detected — Action Required")
def gas_confirm_dialog(gas_ppm, remaining_s):
    st.markdown(
        f"""
        <div style="text-align:center;padding:8px 0 16px;">
            <span style="font-size:48px;">🔥</span>
            <p style="font-size:18px;font-weight:600;color:#ff3a5c;margin:8px 0 4px;">
                Gas level: <strong>{gas_ppm} ppm</strong>
            </p>
            <p style="color:#aab8cc;font-size:14px;">
                Confirm within <strong style="color:#ffaa44;">{remaining_s}s</strong>
                or the buzzer will activate.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    col1, col2 = st.columns(2, gap="small")
    with col1:
        if st.button("✓ It was me — Confirm", type="primary", use_container_width=True):
            mqtt_command("confirm_gas_owner")
    with col2:
        if st.button("Turn off gas", use_container_width=True):
            mqtt_command("set_gas_state", parameters={"enabled": False})


def mqtt_command(action, device_type=None, parameters=None, room_id=None):
    room_id = room_id or st.session_state.get("selected_room_id", "living_room")
    command = {
        "action": action,
        "room": room_id,
        "target_type": "device" if device_type else "sensor",
        "device_type": device_type,
        "device_id": None,
        "parameters": parameters or {},
        "source": "dashboard",
        "raw_text": f"dashboard:{room_id}:{action}:{device_type or 'sensor'}",
    }
    result = st.session_state.agent.iot_controller.execute_command(command)
    if os.environ.get("IOT_MODE", "simulator").strip().lower() == "hardware" and result.get("ok"):
        wait_for_hardware_sync(action, room_id, device_type=device_type, parameters=parameters)
    st.session_state.last_manual_result = result
    st.rerun()


def submit_chat_message(user_input):
    if not user_input or not user_input.strip():
        return
    cleaned = user_input.strip()
    st.session_state.voice_status_message = None
    if st.session_state.meteo_data:
        st.session_state.agent.mettre_a_jour_meteo(st.session_state.meteo_data)
    st.session_state.agent.mettre_a_jour_maison(st.session_state.maison)
    snapshot, current_room = current_snapshot()
    st.session_state.agent.mettre_a_jour_capteurs(current_room.get("sensors", {}))
    st.session_state.historique_chat.append({"role": "user", "message": cleaned, "timestamp": datetime.now().strftime("%H:%M")})
    with st.spinner("Processing..."):
        response = st.session_state.agent.repondre(cleaned)
    st.session_state.historique_chat.append({"role": "robot", "message": response, "timestamp": datetime.now().strftime("%H:%M")})
    st.session_state.robot_state = "speaking"
    st.rerun()


def get_voice_assistant():
    if AssistantVocal is None:
        return None, "Voice commands unavailable: install speech recognition dependencies."

    existing = st.session_state.get("voice_assistant")
    if existing is not None:
        return existing, None

    try:
        assistant = AssistantVocal()
    except Exception as exc:
        return None, f"Voice commands unavailable: {exc}"

    st.session_state.voice_assistant = assistant
    return assistant, None


def cleanup_voice_text(spoken_text):
    cleaned = spoken_text.strip()
    replacements = {
        "garrage": "garage",
        "garaj": "garage",
        "garadge": "garage",
        "garash": "garage",
        "garage gate": "garage door",
        "garage shutter": "garage door",
        "garage lamp": "garage light",
        "garage late": "garage light",
        "turn on the garage": "turn on garage light",
        "turn off the garage": "turn off garage light",
        "open the garage": "unlock garage door",
        "close the garage": "lock garage door",
        "open garage": "unlock garage door",
        "close garage": "lock garage door",
    }
    lowered = cleaned.lower()
    for wrong, right in replacements.items():
        lowered = lowered.replace(wrong, right)
    return lowered


def handle_voice_command(use_wake_word=False):
    assistant, error = get_voice_assistant()
    if error:
        st.session_state.voice_status_message = error
        return

    st.session_state.robot_state = "listening"
    prompt = 'Say "robot" and then your command...' if use_wake_word else "Listening for your command..."

    with st.spinner(prompt):
        if use_wake_word:
            spoken_text = assistant.ecouter_avec_mot_cle(
                mot_cle="robot",
                timeout=20,
                langues=["en-US", "fr-FR", "en-GB"],
            )
        else:
            spoken_text = assistant.ecouter(
                timeout=5,
                phrase_time_limit=8,
                langues=["en-US", "fr-FR", "en-GB"],
            )

    if not spoken_text:
        st.session_state.robot_state = "idle"
        st.session_state.voice_status_message = "No voice command detected. Check the microphone and try again."
        st.rerun()
        return

    normalized_voice_text = cleanup_voice_text(spoken_text)
    st.session_state.voice_status_message = f'Voice command captured: "{normalized_voice_text}"'
    submit_chat_message(normalized_voice_text)


def _format_event_time(timestamp_value):
    if isinstance(timestamp_value, (int, float)):
        total_seconds = max(int(timestamp_value) // 1000, 0)
        hours = total_seconds // 3600
        minutes = (total_seconds % 3600) // 60
        seconds = total_seconds % 60
        return f"{hours:02d}:{minutes:02d}:{seconds:02d}"

    ts = str(timestamp_value or "")
    if len(ts) >= 19 and "T" in ts:
        return ts[11:19]
    if len(ts) >= 8:
        return ts[:8]
    return ts or "--:--:--"


def event_row(event):
    time_str = _format_event_time(event.get("timestamp", ""))
    action = event.get("action", "event").upper()
    target = event.get("target", "")
    status = event.get("status", "")

    if status == "success":
        cls = "tok"
    elif status == "error":
        cls = "terr"
    else:
        cls = "tinfo"

    return (
        f'<div class="rc-term-row">'
        f'<span class="ttime">[{escape(time_str)}]</span> '
        f'<span class="{cls}">{escape(action)}</span> '
        f'<span class="tact"> {escape(str(target))}</span>'
        f'</div>'
    )


# ── init ─────────────────────────────────────────────────────────────────────

init_session()
refresh_weather()
apply_focus_mode_styles()

current_robot_state = st.session_state.robot_state
if current_robot_state == "speaking":
    st.session_state.robot_state = "idle"

snapshot_for_ui = st.session_state.agent.iot_controller.get_snapshot()
room_ids, room_label_map = _room_choices(snapshot_for_ui)
if "selected_room_id" not in st.session_state or st.session_state.selected_room_id not in room_ids:
    st.session_state.selected_room_id = room_ids[0] if room_ids else "living_room"
selected_room_label = next(
    (label for label, room_id in room_label_map.items() if room_id == st.session_state.selected_room_id),
    "Living Room",
)

_mode   = os.environ.get("IOT_MODE", "simulator").upper()
_broker = os.environ.get("MQTT_HOST", "localhost")

# ── SIDEBAR ──────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        '<div class="sb-logo-wrap">'
        '<div class="sb-logo-icon">'
        '<span class="material-symbols-outlined icon-fill">robot_2</span>'
        '</div>'
        '<p class="sb-brand-title">RoboCompagnon</p>'
        '<p class="sb-brand-sub">IoT Command Center</p>'
        '</div>',
        unsafe_allow_html=True,
    )

    st.markdown('<p class="sb-section-label">// Navigation</p>', unsafe_allow_html=True)

    nav_items = [
        ("dashboard",            "Dashboard",   True,  None),
        ("hub",                  "MQTT Topics", False, None),
        ("meeting_room",         "Room Stats",  False, None),
        ("notifications_active", "Reminders",   False, None),
        ("timer",                "Pomodoro",    False, None),
    ]
    for icon, label, active, badge in nav_items:
        badge_html = f'<span class="sb-nav-badge">{badge}</span>' if badge else ""
        st.markdown(
            f'<div class="sb-nav-item {"active" if active else ""}">'
            f'<span class="material-symbols-outlined">{icon}</span>'
            f'<span>{label}</span>'
            f'{badge_html}'
            f'</div>',
            unsafe_allow_html=True,
        )

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
    st.markdown('<p class="sb-section-label">// System</p>', unsafe_allow_html=True)

    if st.button("Refresh System", type="primary", use_container_width=True):
        st.session_state.derniere_maj_meteo = None
        refresh_weather()
        st.rerun()

    st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)

    if st.button("System Reset", use_container_width=True):
        st.session_state.agent.iot_controller.reset()
        st.session_state.agent.robot.reset()
        st.session_state.robot_trace = [(
            st.session_state.agent.robot.etat()["position"]["x"],
            st.session_state.agent.robot.etat()["position"]["y"],
        )]
        st.session_state.last_robot_result = "Robot reset."
        st.rerun()

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.historique_chat = []
        st.rerun()

    st.markdown("<div style='height:5px'></div>", unsafe_allow_html=True)
    focus_label = "🤖 Exit Focus Mode" if st.session_state.focus_mode else "🤖 Focus Mode (Robot + Chat)"
    if st.button(focus_label, use_container_width=True, type="primary" if st.session_state.focus_mode else "secondary"):
        st.session_state.focus_mode = not st.session_state.focus_mode
        st.rerun()

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
    st.markdown('<p class="sb-section-label">// Live Data</p>', unsafe_allow_html=True)
    desired_room_label = next(
        (label for label, room_id in room_label_map.items() if room_id == st.session_state.selected_room_id),
        selected_room_label,
    )
    if "room_picker" not in st.session_state or st.session_state.room_picker != desired_room_label:
        st.session_state.room_picker = desired_room_label
    chosen_room_label = st.selectbox(
        "Active Room",
        options=list(room_label_map.keys()),
        index=max(list(room_label_map.values()).index(st.session_state.selected_room_id), 0) if room_label_map else 0,
        key="room_picker",
    )
    _set_active_room(room_label_map[chosen_room_label], chosen_room_label)
    selected_room_label = chosen_room_label
    st.markdown(
        '<div style="padding:4px 20px 12px;font-size:10px;color:var(--text-dim);font-family:\'Fira Code\',monospace;">'
        'Partial refresh &mdash; 5s interval</div>',
        unsafe_allow_html=True,
    )

# ── TOP BAR ──────────────────────────────────────────────────────────────────

if not st.session_state.focus_mode:
    st.markdown(
        f"""
        <div class="rc-topbar">
            <div class="rc-topbar-left">
                <div>
                    <h2 class="rc-topbar-title">System Dashboard</h2>
                    <p class="rc-breadcrumb">
                        <span class="material-symbols-outlined icon-sm">home</span>
                        RoboCompagnon &rsaquo; {escape(selected_room_label)}
                    </p>
                </div>
            </div>
            <div class="rc-topbar-right">
                <div class="rc-pill rc-pill-green">
                    <span class="rc-live-dot"></span>
                    LIVE
                </div>
                <div class="rc-pill rc-pill-teal">
                    <span class="material-symbols-outlined" style="font-size:13px;">memory</span>
                    {escape(_mode)}
                </div>
                <div class="rc-pill">
                    <span class="material-symbols-outlined" style="font-size:13px;">dns</span>
                    {escape(_broker)}
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# ── LIVE PANEL (partial refresh) ─────────────────────────────────────────────

@st.fragment(run_every=5)
def live_panel():
    snapshot, current_room = current_snapshot()
    selected_room_id = st.session_state.get("selected_room_id", "living_room")
    room_name = _room_name(selected_room_id, current_room)
    alerts     = snapshot.get("alerts", {})
    devices    = current_room.get("devices", {})
    sensors    = current_room.get("sensors", {})
    light      = devices.get("light_main", {"state": "off", "brightness": 0, "id": "light_main", "name": "Main Light"})
    ac         = devices.get("ac_main", {"state": "off", "target_temp": 22, "id": "ac_main", "name": "Main AC"})
    door       = devices.get("door_main", {})
    gas_ppm    = sensors.get("gas_ppm", 0)
    gas_alert  = alerts.get("gas", False)
    gas_buzzer = alerts.get("gas_buzzer", False)
    gas_unconfirmed = alerts.get("gas_unconfirmed", False)
    occupancy  = sensors.get("occupancy", False)
    etat_robot = st.session_state.agent.robot.etat()

    devices_on = _room_device_count(current_room)

    # ── HERO ─────────────────────────────────────────────────────────────────

    _hero_sub       = "CRITICAL — Gas alert active, ventilate immediately" if gas_alert else "All nodes operational — system nominal"
    _hero_sub_color = "var(--red)" if gas_alert else "var(--text-muted)"

    st.markdown(
        f"""
    <div class="rc-hero">
        <div class="rc-hero-content">
            <div>
                <div class="rc-hero-tag">
                    <span class="material-symbols-outlined">{'warning' if gas_alert else 'verified'}</span>
                    {escape(room_name)} • {escape(_mode)} Mode
                </div>
                <h3 class="rc-hero-title">Welcome back,<br>Developer</h3>
                <p class="rc-hero-sub" style="color:{_hero_sub_color};">{escape(_hero_sub)}</p>
            </div>
            <div class="rc-hero-stats">
                <div class="rc-hero-stat">
                    <p class="rc-hero-stat-val">{devices_on}</p>
                    <p class="rc-hero-stat-label">Active</p>
                </div>
                <div class="rc-hero-stat">
                    <p class="rc-hero-stat-val">{sensors.get('temperature', 0)}&deg;</p>
                    <p class="rc-hero-stat-label">Temp</p>
                </div>
                <div class="rc-hero-stat">
                    <p class="rc-hero-stat-val">{sensors.get('humidity', 0)}%</p>
                    <p class="rc-hero-stat-label">Humid</p>
                </div>
            </div>
        </div>
    </div>
    """,
        unsafe_allow_html=True,
    )

    overview_cols = st.columns(max(len(snapshot.get("rooms", {})), 1), gap="small")
    for idx, (room_id, room) in enumerate(snapshot.get("rooms", {}).items()):
        room_sensors = room.get("sensors", {})
        room_gas = room_sensors.get("gas_ppm", 0)
        room_occ = "Occupied" if room_sensors.get("occupancy", False) else "Idle"
        room_active = _room_device_count(room)
        room_alert = room_gas > 200
        room_label = _room_name(room_id, room)
        with overview_cols[idx]:
            st.markdown(
                f"""<div class="rc-card {'on' if room_id == selected_room_id else ''}">
                    <div class="rc-device-hd">
                        <p class="rc-device-name" style="margin:0;">{escape(room_label)}</p>
                        <span class="rc-status-badge {'rc-status-off' if room_alert else 'rc-status-on'}">{room_occ.upper()}</span>
                    </div>
                    <p class="rc-device-meta">Devices active: {room_active}</p>
                    <p class="rc-device-meta">Temp {room_sensors.get('temperature', 0)}°C • Humidity {room_sensors.get('humidity', 0)}%</p>
                    <p class="rc-device-meta">Gas {room_gas} ppm</p>
                </div>""",
                unsafe_allow_html=True,
            )
            if st.button(
                room_label,
                key=f"room_select_{room_id}",
                use_container_width=True,
                type="primary" if room_id == selected_room_id else "secondary",
            ):
                _set_active_room(room_id, room_label)
                st.rerun()

    if not gas_unconfirmed and gas_ppm <= 0:
        st.session_state.pop("gas_dialog_armed_at", None)

    if gas_alert:
        st.markdown(
            '<div class="rc-alert">'
            '<span class="material-symbols-outlined icon-fill">warning</span>'
            '<strong>CRITICAL ALERT:</strong>&nbsp; Gas sensor triggered in the house. Open windows immediately.'
            '</div>',
            unsafe_allow_html=True,
        )

    if gas_unconfirmed and not gas_buzzer and gas_ppm > 0:
        armed_at_raw = snapshot.get("safety", {}).get("gas_confirmation", {}).get("armed_at")
        if armed_at_raw:
            try:
                armed_at = datetime.fromisoformat(armed_at_raw)
                if armed_at.tzinfo is None:
                    armed_at = armed_at.replace(tzinfo=timezone.utc)
                elapsed = (datetime.now(timezone.utc) - armed_at).total_seconds()
                remaining_s = max(0, 60 - int(elapsed))
            except (ValueError, TypeError):
                remaining_s = 60
        else:
            remaining_s = 60
        if "gas_dialog_armed_at" not in st.session_state or st.session_state.gas_dialog_armed_at != armed_at_raw:
            st.session_state.gas_dialog_armed_at = armed_at_raw
            gas_confirm_dialog(gas_ppm, remaining_s)
        st.markdown(
            f'<div class="rc-alert" style="border-color:rgba(255,170,68,0.45);color:#ffaa44;">'
            f'<span class="material-symbols-outlined icon-fill">schedule</span>'
            f'<strong>CONFIRMATION REQUIRED:</strong>&nbsp; Confirm the gas action within {remaining_s}s to avoid buzzer alarm.'
            f'</div>',
            unsafe_allow_html=True,
        )

    if gas_buzzer:
        st.markdown(
            '<div class="rc-alert" style="border-color:rgba(255,58,92,0.55);color:#ff8095;">'
            '<span class="material-symbols-outlined icon-fill">campaign</span>'
            '<strong>BUZZER ACTIVE:</strong>&nbsp; Gas was left active without confirmation. Confirm it was you or turn gas off.'
            '</div>',
            unsafe_allow_html=True,
        )

    # ── ROW 1: Devices + Weather ──────────────────────────────────────────────

    col_dev, col_wx = st.columns([1.55, 1], gap="medium")

    with col_dev:
        st.markdown(
            '<div class="rc-section-hd">'
            '<p class="rc-section-title">Active Devices</p>'
            f'<span class="rc-section-sub"><span class="rc-section-dot"></span>{escape(room_name)}</span>'
            '</div>',
            unsafe_allow_html=True,
        )

        dc0, dc1, dc2 = st.columns(3, gap="small")

        # Light
        with dc0:
            light_on = light["state"] == "on"
            on_cls   = "on" if light_on else ""
            st.markdown(
                f"""<div class="rc-card {on_cls}">
                    <div class="rc-device-hd">
                        <div class="rc-device-icon-wrap">
                            <span class="material-symbols-outlined rc-device-icon">lightbulb</span>
                        </div>
                        <span class="rc-status-badge {'rc-status-on' if light_on else 'rc-status-off'}">{light['state'].upper()}</span>
                    </div>
                    <p class="rc-device-name">{escape(_device_name(light, 'Main Light'))}</p>
                    <p class="rc-device-id">{escape(_device_code(light, 'light_main'))}</p>
                    <p class="rc-device-meta">{escape(_light_meta(light, sensors))}</p>
                </div>""",
                unsafe_allow_html=True,
            )
            if light_on:
                if st.button("Turn Off", key="light_off", use_container_width=True):
                    mqtt_command("turn_off", device_type="light", room_id=selected_room_id)
            else:
                if st.button("Turn On", key="light_on", use_container_width=True, type="primary"):
                    mqtt_command("turn_on", device_type="light", room_id=selected_room_id)

        # AC
        with dc1:
            if "ac_main" in devices:
                ac_on  = ac["state"] == "on"
                on_cls = "on" if ac_on else ""
                temp   = ac.get("target_temp", 22)
                pct    = int((temp - 16) / (30 - 16) * 100)
                st.markdown(
                    f"""<div class="rc-card {on_cls}">
                        <div class="rc-device-hd">
                            <div class="rc-device-icon-wrap">
                                <span class="material-symbols-outlined rc-device-icon">ac_unit</span>
                            </div>
                            <span class="rc-status-badge {'rc-status-on' if ac_on else 'rc-status-off'}">{_ac_badge(ac)}</span>
                        </div>
                        <p class="rc-device-name">{escape(_device_name(ac, 'AC Unit'))}</p>
                        <p class="rc-device-id">{escape(_device_code(ac, 'ac_main'))}</p>
                        <p class="rc-device-meta">{escape(_ac_meta(ac, sensors))}</p>
                        <div class="rc-temp-bar">
                            <div class="rc-temp-fill" style="width:{pct}%;"></div>
                            <div class="rc-temp-thumb" style="left:{pct}%;"></div>
                        </div>
                    </div>""",
                    unsafe_allow_html=True,
                )
                if ac_on:
                    if st.button("Turn Off", key="ac_off", use_container_width=True):
                        mqtt_command("turn_off", device_type="ac", room_id=selected_room_id)
                else:
                    if st.button("Turn On", key="ac_on", use_container_width=True, type="primary"):
                        mqtt_command("turn_on", device_type="ac", room_id=selected_room_id)
            elif "gas_ppm" in sensors:
                gas_on = sensors.get("gas_ppm", 0) > 0
                gas_level = int(sensors.get("gas_ppm", 0))
                gas_alert_cls = "on" if gas_on else ""
                st.markdown(
                    f"""<div class="rc-card {gas_alert_cls}">
                        <div class="rc-device-hd">
                            <div class="rc-device-icon-wrap">
                                <span class="material-symbols-outlined rc-device-icon">co2</span>
                            </div>
                            <span class="rc-status-badge {'rc-status-on' if gas_on else 'rc-status-off'}">{'ON' if gas_on else 'OFF'}</span>
                        </div>
                        <p class="rc-device-name">Kitchen Gas</p>
                        <p class="rc-device-id">GAS_PPM</p>
                        <p class="rc-device-meta">{escape(_gas_meta(sensors, alerts))}</p>
                    </div>""",
                    unsafe_allow_html=True,
                )
                gas_level_value = st.slider(
                    "Gas Level (ppm)",
                    min_value=0,
                    max_value=1000,
                    value=gas_level,
                    step=50,
                    key=f"gas_level_{selected_room_id}",
                )
                gas_btn_a, gas_btn_b = st.columns(2, gap="small")
                with gas_btn_a:
                    if st.button("Gas On", key="gas_on", use_container_width=True, type="primary" if not gas_on else "secondary"):
                        mqtt_command("set_gas_state", parameters={"enabled": True}, room_id=selected_room_id)
                with gas_btn_b:
                    if st.button("Gas Off", key="gas_off", use_container_width=True):
                        mqtt_command("set_gas_state", parameters={"enabled": False}, room_id=selected_room_id)
                if st.button("Apply Gas Level", key="gas_apply", use_container_width=True):
                    mqtt_command("set_gas_level", parameters={"gas_ppm": gas_level_value}, room_id=selected_room_id)
            else:
                st.empty()

        # Door
        with dc2:
            if door:
                is_locked = door.get("state", "locked") == "locked"
                on_cls    = "" if is_locked else "on"
                door_icon = "lock" if is_locked else "lock_open"
                badge_cls = "rc-status-locked" if is_locked else "rc-status-unlocked"
                st.markdown(
                    f"""<div class="rc-card {on_cls}">
                        <div class="rc-device-hd">
                            <div class="rc-device-icon-wrap">
                                <span class="material-symbols-outlined rc-device-icon">{door_icon}</span>
                            </div>
                            <span class="rc-status-badge {badge_cls}">{door['state'].upper()}</span>
                        </div>
                        <p class="rc-device-name">{escape(_device_name(door, 'Front Door'))}</p>
                        <p class="rc-device-id">{escape(_device_code(door, 'door_main'))}</p>
                        <p class="rc-device-meta">{escape(_door_meta(door, sensors))}</p>
                    </div>""",
                    unsafe_allow_html=True,
                )
                if is_locked:
                    if st.button("Action: Unlock Door", key="door_unlock", use_container_width=True):
                        mqtt_command("unlock", device_type="door", room_id=selected_room_id)
                else:
                    if st.button("Action: Lock Door", key="door_lock", use_container_width=True, type="primary"):
                        mqtt_command("lock", device_type="door", room_id=selected_room_id)

        if st.session_state.last_manual_result:
            r = st.session_state.last_manual_result
            if r.get("ok"):
                st.success(r.get("message", "Command executed."))
            else:
                st.error(r.get("message", "Command failed."))

    with col_wx:
        if st.session_state.meteo_data:
            m = st.session_state.meteo_data
            st.markdown(
                f"""<div class="rc-weather">
                    <div class="rc-wx-main">
                        <span class="material-symbols-outlined rc-wx-icon icon-fill">sunny</span>
                        <div>
                            <p class="rc-wx-temp">{m['temperature']}&deg;</p>
                            <p class="rc-wx-loc">
                                <span class="material-symbols-outlined" style="font-size:13px;">location_on</span>
                                {escape(m['ville'])}
                            </p>
                        </div>
                    </div>
                    <div class="rc-wx-metrics">
                        <div class="rc-wx-metric">
                            <p class="rc-wx-m-label">Temp</p>
                            <p class="rc-wx-m-val">{m['temperature']}&deg;C</p>
                        </div>
                        <div class="rc-wx-metric">
                            <p class="rc-wx-m-label">Humidity</p>
                            <p class="rc-wx-m-val">{m['humidite']}%</p>
                        </div>
                        <div class="rc-wx-metric">
                            <p class="rc-wx-m-label">Wind</p>
                            <p class="rc-wx-m-val">{m['vent_kmh']} km/h</p>
                        </div>
                        <div class="rc-wx-metric">
                            <p class="rc-wx-m-label">AQI</p>
                            <p class="rc-wx-m-val good">Good</p>
                        </div>
                    </div>
                </div>""",
                unsafe_allow_html=True,
            )
        else:
            st.info("Weather data unavailable.")

        lux      = sensors.get("light_level", 0)
        lux_cls  = "warn" if lux < 200 else ""
        gas_cls  = "danger" if gas_ppm > 400 else ("warn" if gas_ppm > 200 else "")
        occ_icon = "person" if occupancy else "person_off"

        st.markdown(
            f"""<div class="rc-sensor-row">
                <div class="rc-sensor-chip">
                    <span class="material-symbols-outlined rc-s-icon icon-fill">thermostat</span>
                    <span class="rc-s-val">{sensors.get('temperature', 0)}&deg;</span>
                    <span class="rc-s-label">Temp</span>
                </div>
                <div class="rc-sensor-chip">
                    <span class="material-symbols-outlined rc-s-icon">humidity_mid</span>
                    <span class="rc-s-val">{sensors.get('humidity', 0)}%</span>
                    <span class="rc-s-label">Humid</span>
                </div>
                <div class="rc-sensor-chip {lux_cls}">
                    <span class="material-symbols-outlined rc-s-icon">light_mode</span>
                    <span class="rc-s-val">{lux}</span>
                    <span class="rc-s-label">Lux</span>
                </div>
                <div class="rc-sensor-chip {gas_cls}">
                    <span class="material-symbols-outlined rc-s-icon">co2</span>
                    <span class="rc-s-val">{gas_ppm}</span>
                    <span class="rc-s-label">Gas</span>
                </div>
                <div class="rc-sensor-chip">
                    <span class="material-symbols-outlined rc-s-icon">{occ_icon}</span>
                    <span class="rc-s-val">{'YES' if occupancy else 'NO'}</span>
                    <span class="rc-s-label">Occup</span>
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

    st.markdown("<div style='margin-top:1.1rem;'></div>", unsafe_allow_html=True)

    # ── ROW 2: Robot + Pomodoro | Terminal ───────────────────────────────────

    col_robot, col_term = st.columns([1, 1.65], gap="medium")

    with col_robot:
        bat = etat_robot["batterie"]
        nav_options = {
            "Living Room": "living_room",
            "Kitchen": "kitchen",
            "Bedroom": "bedroom",
            "Toilet": "toilet",
            "Garage": "garage",
        }
        current_target = st.session_state.get("robot_nav_target", "kitchen")
        navigation_points = _navigation_route_points(etat_robot, current_target)
        navigation_hint = _navigation_hint(etat_robot, current_target)
        st.markdown(
            f"""<div class="rc-robot-card">
                <div class="rc-robot-hd">
                    <div class="rc-robot-avatar">
                        <span class="material-symbols-outlined icon-fill">robot_2</span>
                        <div class="rc-robot-status-dot"></div>
                    </div>
                    <div class="rc-robot-meta">
                        <p class="rc-robot-name">RoboCompagnon</p>
                        <p class="rc-robot-state">
                            <span class="material-symbols-outlined" style="font-size:12px;color:var(--green);">fiber_manual_record</span>
                            Online &mdash; {etat_robot.get('mode', 'idle').capitalize()}
                        </p>
                    </div>
                </div>
                <div class="rc-bat-row">
                    <span class="rc-bat-label">Battery</span>
                    <span class="rc-bat-val">{bat:.0f}%</span>
                </div>
                <div class="rc-bat-track">
                    <div class="rc-bat-fill" style="width:{bat}%;"></div>
                </div>
                <div class="rc-info-row">
                    <span class="material-symbols-outlined">explore</span>
                    Heading: {etat_robot['direction_text']}
                </div>
                <div class="rc-info-row">
                    <span class="material-symbols-outlined">my_location</span>
                    Position: ({etat_robot['position']['x']:.1f}, {etat_robot['position']['y']:.1f}) cm
                </div>
                <div class="rc-info-row">
                    <span class="material-symbols-outlined">home_pin</span>
                    Zone: {escape(etat_robot.get('zone_label', 'Unknown Area'))}
                </div>
            </div>""",
            unsafe_allow_html=True,
        )

        selected_nav_label = st.selectbox(
            "Guide To",
            options=list(nav_options.keys()),
            index=max(0, list(nav_options.values()).index(current_target)) if current_target in nav_options.values() else 1,
            key="robot_nav_target_label",
        )
        st.session_state.robot_nav_target = nav_options[selected_nav_label]
        navigation_points = _navigation_route_points(etat_robot, st.session_state.robot_nav_target)
        navigation_hint = _navigation_hint(etat_robot, st.session_state.robot_nav_target)

        _render_robot_visual(etat_robot, st.session_state.robot_trace, snapshot, navigation_points)

        up_a, up_b, up_c = st.columns([1, 1, 1], gap="small")
        with up_b:
            if st.button("Forward", key="robot_forward", use_container_width=True):
                _run_robot_action("forward")
                st.rerun()

        mid_a, mid_b, mid_c = st.columns([1, 1, 1], gap="small")
        with mid_a:
            if st.button("Left", key="robot_left", use_container_width=True):
                _run_robot_action("left")
                st.rerun()
        with mid_b:
            if st.button("Scan", key="robot_scan", use_container_width=True):
                _run_robot_action("scan")
                st.rerun()
        with mid_c:
            if st.button("Right", key="robot_right", use_container_width=True):
                _run_robot_action("right")
                st.rerun()

        down_a, down_b, down_c = st.columns([1, 1, 1], gap="small")
        with down_b:
            if st.button("Back", key="robot_back", use_container_width=True):
                _run_robot_action("backward")
                st.rerun()

        util_a, util_b = st.columns(2, gap="small")
        with util_a:
            if st.button("Recharge", key="robot_charge", use_container_width=True):
                _run_robot_action("charge")
                st.rerun()
        with util_b:
            if st.button("Clear Path", key="robot_clear", use_container_width=True):
                _run_robot_action("clear")
                st.rerun()

        if st.session_state.last_robot_result:
            st.markdown(
                f'<div class="rc-robot-note">{escape(st.session_state.last_robot_result)}</div>',
                unsafe_allow_html=True,
            )
        st.markdown(
            f'<div class="rc-robot-note">Route hint: {escape(navigation_hint)}</div>',
            unsafe_allow_html=True,
        )
        st.markdown(
            '<div class="rc-robot-note">Map markers: L=light, AC=air conditioner, D=door, BZ=buzzer, T=temperature, G=gas sensor.</div>',
            unsafe_allow_html=True,
        )
        if etat_robot.get("last_scan"):
            scan = etat_robot["last_scan"]
            st.markdown(
                (
                    '<div class="rc-robot-note">'
                    f"Scan F:{scan.get('avant', 0)}cm | R:{scan.get('droite', 0)}cm | "
                    f"L:{scan.get('gauche', 0)}cm | B:{scan.get('arriere', 0)}cm"
                    "</div>"
                ),
                unsafe_allow_html=True,
            )

        st.markdown(
            '<div class="rc-pomo-card">'
            '<div class="rc-pomo-hd">'
            '<span class="material-symbols-outlined">timer</span>'
            'Deep Work Timer'
            '</div>',
            unsafe_allow_html=True,
        )
        pomo = st.session_state.agent.pomodoro.etat_session()
        if pomo["active"]:
            st.success(f"{pomo['matiere']} — {pomo['temps_restant']}")
            if st.button("Stop Session", key="pomo_stop", use_container_width=True):
                st.session_state.agent.pomodoro.arreter_session()
                st.rerun()
        else:
            with st.form("pomo_form"):
                pA, pB = st.columns(2)
                duree   = pA.number_input("Min", 5, 60, 25, label_visibility="collapsed")
                matiere = pB.selectbox("Mode", ["Focus", "Study", "Coding"], label_visibility="collapsed")
                if st.form_submit_button("Start Session", use_container_width=True, type="primary"):
                    st.session_state.agent.pomodoro.demarrer_session_travail(matiere, duree)
                    st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    with col_term:
        events    = st.session_state.agent.iot_controller.get_recent_events(limit=14)
        rows_html = "".join(event_row(e) for e in events) if events else \
            '<span class="tempty">// No events recorded yet</span>'
        st.markdown(
            f"""<div class="rc-terminal">
                <div class="rc-term-titlebar">
                    <div class="rc-term-dots">
                        <div class="rc-term-dot" style="background:#ff3a5c;box-shadow:0 0 6px rgba(255,58,92,0.5);"></div>
                        <div class="rc-term-dot" style="background:#ffaa44;box-shadow:0 0 6px rgba(255,170,68,0.4);"></div>
                        <div class="rc-term-dot" style="background:#39ffa0;box-shadow:0 0 6px rgba(57,255,160,0.4);"></div>
                    </div>
                    <span class="rc-term-title">mqtt_stream_live</span>
                    <span class="rc-term-version">broker::{escape(_broker)}</span>
                </div>
                <div class="rc-term-body">{rows_html}</div>
            </div>""",
            unsafe_allow_html=True,
        )


if not st.session_state.focus_mode:
    live_panel()

# ── ROW 3: Chat + Robot ───────────────────────────────────────────────────────

_mode_val   = os.environ.get("IOT_MODE", "simulator").upper()
_broker_val = os.environ.get("MQTT_HOST", "localhost")

col_robot_chat, col_chat_main = st.columns([1, 2], gap="medium")

with col_robot_chat:
    components.html(get_robot_html(current_robot_state), height=400)

with col_chat_main:
    header_actions_left, header_actions_right = st.columns([5, 1], gap="small")
    with header_actions_right:
        hide_all_label = "Show All" if st.session_state.focus_mode else "Hide All"
        if st.button(hide_all_label, key="chat_hide_all", use_container_width=True):
            st.session_state.focus_mode = not st.session_state.focus_mode
            st.rerun()

    st.markdown(
        f"""<div class="rc-chat-frame">
            <div class="rc-chat-header">
                <div class="rc-chat-agent">
                    <div class="rc-agent-avatar">
                        <span class="material-symbols-outlined icon-fill">smart_toy</span>
                    </div>
                    <div>
                        <p class="rc-agent-name">RoboCompagnon AI</p>
                        <p class="rc-agent-status">
                            <span class="material-symbols-outlined icon-fill">fiber_manual_record</span>
                            Neural Engine Online
                        </p>
                    </div>
                </div>
                <div class="rc-chat-meta">
                    <div class="rc-chat-meta-item">
                        <p class="rc-chat-meta-label">Mode</p>
                        <p class="rc-chat-meta-val">{escape(_mode_val)}</p>
                    </div>
                    <div class="rc-chat-meta-item">
                        <p class="rc-chat-meta-label">Broker</p>
                        <p class="rc-chat-meta-val accent">{escape(_broker_val)}</p>
                    </div>
                </div>
            </div>
        </div>""",
        unsafe_allow_html=True,
    )

    voice_col1, voice_col2 = st.columns(2, gap="small")
    with voice_col1:
        if st.button("Voice Command", key="voice_command_direct", use_container_width=True):
            handle_voice_command(use_wake_word=False)
    with voice_col2:
        if st.button('Wake Word: "robot"', key="voice_command_wake_word", use_container_width=True):
            handle_voice_command(use_wake_word=True)

    if st.session_state.voice_status_message:
        st.info(st.session_state.voice_status_message)

    chat_history   = st.session_state.historique_chat
    chat_container = st.container(height=320)
    with chat_container:
        if not chat_history:
            st.markdown(
                '<div class="rc-msg-ai">'
                '<div class="rc-msg-icon">'
                '<span class="material-symbols-outlined icon-fill" style="font-size:14px;color:var(--teal);">smart_toy</span>'
                '</div>'
                '<div class="rc-bubble-ai">Hello, Developer. All systems are in operational mode. '
                'Try: "turn on the light", "lock the door", or "what is the gas level?"</div>'
                '</div>',
                unsafe_allow_html=True,
            )
        for msg in chat_history:
            if msg["role"] == "robot":
                st.markdown(
                    f'<div class="rc-msg-ai">'
                    f'<div class="rc-msg-icon">'
                    f'<span class="material-symbols-outlined icon-fill" style="font-size:14px;color:var(--teal);">smart_toy</span>'
                    f'</div>'
                    f'<div class="rc-bubble-ai">{escape(msg["message"])}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
            else:
                st.markdown(
                    f'<div class="rc-msg-user">'
                    f'<div class="rc-msg-icon">'
                    f'<span class="material-symbols-outlined" style="font-size:14px;">person</span>'
                    f'</div>'
                    f'<div class="rc-bubble-user">{escape(msg["message"])}</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )

    # Quick action buttons
    quick_actions = [
        ("lightbulb", "Turn On Light"),
        ("co2",       "Gas Level"),
        ("lock",      "Lock All Doors"),
        ("videocam",  "Robot View"),
    ]
    qa_cols = st.columns(4)
    for idx, (icon, label) in enumerate(quick_actions):
        with qa_cols[idx]:
            if st.button(label, key=f"qa_{idx}", use_container_width=True):
                submit_chat_message(label)

user_input = st.chat_input("Type a command or ask a question...")
if user_input:
    submit_chat_message(user_input)
