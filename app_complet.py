from datetime import datetime
from html import escape
import os
import time

import streamlit as st
from agent import AgentRobot
from config_env import load_env_file
from iot_store import load_state
from meteo import MeteoAPI
from objets_connectes import MaisonConnectee
from tts import RobotVoix


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
    if "agent" not in st.session_state:
        st.session_state.agent = AgentRobot(nom_utilisateur="Monssef")
        st.session_state.historique_chat = []
        st.session_state.meteo_api = MeteoAPI(ville="Rabat", pays="MA")
        st.session_state.meteo_data = None
        st.session_state.derniere_maj_meteo = None
        st.session_state.robot_voix = RobotVoix(langue="fr")
        st.session_state.auto_play_voice = False
        st.session_state.last_manual_result = None
        st.session_state.last_voice_message = None
        st.session_state.live_refresh = os.environ.get("IOT_MODE", "simulator").strip().lower() == "hardware"
        st.session_state.maison = MaisonConnectee()
        st.session_state.agent.mettre_a_jour_maison(st.session_state.maison)


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
    living_room = snapshot["rooms"]["living_room"]
    st.session_state.agent.mettre_a_jour_capteurs(living_room["sensors"])
    return snapshot, living_room


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


def wait_for_hardware_sync(action, device_type=None, parameters=None, timeout_s=2.5):
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
                .get("living_room", {})
                .get("devices", {})
                .get(device_id, {})
                .get("state")
            )
            if current_state == expected_state:
                return
        except Exception:
            pass
        time.sleep(0.12)


def mqtt_command(action, device_type=None, parameters=None):
    command = {
        "action": action,
        "room": "living_room",
        "target_type": "device" if device_type else "sensor",
        "device_type": device_type,
        "device_id": None,
        "parameters": parameters or {},
        "source": "dashboard",
        "raw_text": f"dashboard:{action}:{device_type or 'sensor'}",
    }
    result = st.session_state.agent.iot_controller.execute_command(command)
    if os.environ.get("IOT_MODE", "simulator").strip().lower() == "hardware" and result.get("ok"):
        wait_for_hardware_sync(action, device_type=device_type, parameters=parameters)
    st.session_state.last_manual_result = result
    st.rerun()


def submit_chat_message(user_input):
    if not user_input or not user_input.strip():
        return
    cleaned = user_input.strip()
    if st.session_state.meteo_data:
        st.session_state.agent.mettre_a_jour_meteo(st.session_state.meteo_data)
    st.session_state.agent.mettre_a_jour_maison(st.session_state.maison)
    snapshot, living_room = current_snapshot()
    st.session_state.agent.mettre_a_jour_capteurs(living_room["sensors"])
    st.session_state.historique_chat.append({"role": "user", "message": cleaned, "timestamp": datetime.now().strftime("%H:%M")})
    with st.spinner("Processing..."):
        response = st.session_state.agent.repondre(cleaned)
    st.session_state.historique_chat.append({"role": "robot", "message": response, "timestamp": datetime.now().strftime("%H:%M")})
    st.rerun()


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
        st.rerun()

    if st.button("Clear Chat", use_container_width=True):
        st.session_state.historique_chat = []
        st.rerun()

    st.markdown('<div class="sb-divider"></div>', unsafe_allow_html=True)
    st.markdown('<p class="sb-section-label">// Live Data</p>', unsafe_allow_html=True)
    st.markdown(
        '<div style="padding:4px 20px 12px;font-size:10px;color:var(--text-dim);font-family:\'Fira Code\',monospace;">'
        'Partial refresh &mdash; 5s interval</div>',
        unsafe_allow_html=True,
    )

# ── TOP BAR ──────────────────────────────────────────────────────────────────

st.markdown(
    f"""
    <div class="rc-topbar">
        <div class="rc-topbar-left">
            <div>
                <h2 class="rc-topbar-title">System Dashboard</h2>
                <p class="rc-breadcrumb">
                    <span class="material-symbols-outlined icon-sm">home</span>
                    RoboCompagnon &rsaquo; Living Room
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
    snapshot, living_room = current_snapshot()

    alerts     = snapshot.get("alerts", {})
    devices    = living_room["devices"]
    sensors    = living_room["sensors"]
    light      = devices["light_main"]
    ac         = devices["ac_main"]
    door       = devices.get("door_main", {})
    gas_ppm    = sensors.get("gas_ppm", 0)
    gas_alert  = alerts.get("gas", False)
    gas_buzzer = alerts.get("gas_buzzer", False)
    gas_unconfirmed = alerts.get("gas_unconfirmed", False)
    occupancy  = sensors.get("occupancy", False)
    etat_robot = st.session_state.agent.robot.etat()

    devices_on = sum([
        light["state"] == "on",
        ac["state"] == "on",
        door.get("state", "locked") == "unlocked" if door else False,
    ])

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
                    {escape(_mode)} Mode
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

    if gas_alert:
        st.markdown(
            '<div class="rc-alert">'
            '<span class="material-symbols-outlined icon-fill">warning</span>'
            '<strong>CRITICAL ALERT:</strong>&nbsp; Gas sensor triggered in Living Room node. Open windows immediately.'
            '</div>',
            unsafe_allow_html=True,
        )

    if gas_unconfirmed and not gas_buzzer and gas_ppm > 0:
        st.markdown(
            '<div class="rc-alert" style="border-color:rgba(255,170,68,0.45);color:#ffaa44;">'
            '<span class="material-symbols-outlined icon-fill">schedule</span>'
            '<strong>CONFIRMATION REQUIRED:</strong>&nbsp; Confirm the gas action within 30 seconds to avoid buzzer alarm.'
            '</div>',
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
            '<span class="rc-section-sub"><span class="rc-section-dot"></span>Living Room</span>'
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
                    mqtt_command("turn_off", device_type="light")
            else:
                if st.button("Turn On", key="light_on", use_container_width=True, type="primary"):
                    mqtt_command("turn_on", device_type="light")

        # AC
        with dc1:
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
                    mqtt_command("turn_off", device_type="ac")
            else:
                if st.button("Turn On", key="ac_on", use_container_width=True, type="primary"):
                    mqtt_command("turn_on", device_type="ac")

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
                        mqtt_command("unlock", device_type="door")
                else:
                    if st.button("Action: Lock Door", key="door_lock", use_container_width=True, type="primary"):
                        mqtt_command("lock", device_type="door")

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
            </div>""",
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


live_panel()

st.markdown("<div style='margin-top:1.1rem;'></div>", unsafe_allow_html=True)

# ── ROW 3: Chat ───────────────────────────────────────────────────────────────

_mode_val   = os.environ.get("IOT_MODE", "simulator").upper()
_broker_val = os.environ.get("MQTT_HOST", "localhost")

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
qa_cols = st.columns([1, 1, 1, 1, 2])
for idx, (icon, label) in enumerate(quick_actions):
    with qa_cols[idx]:
        if st.button(label, key=f"qa_{idx}", use_container_width=True):
            submit_chat_message(label)

user_input = st.chat_input("Type a command or ask a question...")
if user_input:
    submit_chat_message(user_input)
