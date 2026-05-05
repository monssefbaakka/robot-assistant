from datetime import datetime
from html import escape
import os

import streamlit as st

from agent import AgentRobot
from config_env import load_env_file
from meteo import MeteoAPI
from objets_connectes import MaisonConnectee
from tts import RobotVoix


st.set_page_config(
    page_title="RoboCompagnon - MQTT IoT Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    :root {
        --bg-main: #ffffff;
        --sidebar-bg: #f8f9fa;
        --border-color: #eaecf0;
        --text-main: #1d2939;
        --text-muted: #667085;
        --accent-blue: #0066cc;
        --accent-blue-light: #e6f0fa;
        --terminal-bg: #1c1c1c;
    }

    .stApp {
        background: var(--bg-main);
        font-family: 'Inter', system-ui, sans-serif;
    }

    /* Hide default header/footer */
    header[data-testid="stHeader"] {
        display: none;
    }
    footer {
        display: none;
    }

    /* Sidebar Styling */
    section[data-testid="stSidebar"] {
        background-color: var(--sidebar-bg);
        border-right: 1px solid var(--border-color);
        padding-top: 1rem;
    }

    /* Top Bar */
    .top-bar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border-color);
        margin-bottom: 1.5rem;
    }
    .top-bar-title {
        color: var(--accent-blue);
        font-size: 1.5rem;
        font-weight: 700;
        margin: 0;
    }

    /* Hero Banner */
    .hero {
        background: linear-gradient(135deg, #0a1628 0%, #0d2245 50%, #0a3d62 100%);
        border-radius: 12px;
        padding: 3rem 2rem;
        margin-bottom: 2rem;
        position: relative;
        overflow: hidden;
    }
    .hero::before {
        content: '';
        position: absolute;
        inset: 0;
        background: radial-gradient(ellipse at 80% 50%, rgba(0, 102, 204, 0.25) 0%, transparent 60%);
    }
    .hero-tag {
        background: var(--accent-blue);
        color: white;
        padding: 4px 12px;
        border-radius: 4px;
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        display: inline-block;
        margin-bottom: 1rem;
    }
    .hero-title {
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin: 0 0 0.5rem 0;
        line-height: 1.2;
    }
    .hero-subtitle {
        color: #d0d5dd;
        margin: 0;
        font-size: 1rem;
    }

    /* Section Headers */
    .section-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    .section-title {
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-main);
        margin: 0;
    }
    .section-subtitle {
        font-size: 0.85rem;
        color: var(--accent-blue);
        font-weight: 500;
        display: flex;
        align-items: center;
        gap: 0.5rem;
    }
    .section-subtitle::before {
        content: '';
        display: inline-block;
        width: 6px;
        height: 6px;
        background: var(--accent-blue);
        border-radius: 50%;
    }

    /* Base Card Style */
    .card {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 12px;
        padding: 1.25rem;
        height: 100%;
        box-shadow: 0 1px 2px rgba(16, 24, 40, 0.05);
    }
    
    /* Device Cards */
    .device-card {
        display: flex;
        flex-direction: column;
        justify-content: space-between;
    }
    .device-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        margin-bottom: 1rem;
    }
    .device-icon {
        color: var(--accent-blue);
        font-size: 1.25rem;
    }
    .device-status {
        font-size: 0.8rem;
        font-weight: 600;
        color: var(--accent-blue);
        text-transform: uppercase;
    }
    .device-status.off {
        color: var(--text-muted);
    }
    .device-name {
        font-weight: 600;
        color: var(--text-main);
        margin: 0 0 0.25rem 0;
    }
    .device-sub {
        font-size: 0.75rem;
        color: var(--text-muted);
        text-transform: uppercase;
        margin: 0;
    }
    .device-card.active {
        border: 1.5px solid var(--accent-blue);
        box-shadow: 0 0 0 3px var(--accent-blue-light);
    }

    /* Weather Panel */
    .weather-panel {
        display: flex;
        flex-direction: column;
    }
    .weather-main {
        display: flex;
        align-items: center;
        gap: 1.5rem;
        margin-bottom: 1.5rem;
    }
    .weather-icon {
        font-size: 2.5rem;
        color: #f59e0b;
    }
    .weather-info h3 {
        margin: 0;
        font-size: 1.1rem;
        font-weight: 600;
        color: var(--text-main);
    }
    .weather-info p {
        margin: 0;
        font-size: 0.85rem;
        color: var(--text-muted);
    }
    .weather-metrics {
        display: flex;
        justify-content: space-between;
        gap: 1rem;
    }
    .weather-metric {
        text-align: center;
    }
    .weather-metric-val {
        font-size: 1rem;
        font-weight: 600;
        color: var(--text-main);
        margin: 0.25rem 0 0 0;
    }
    .weather-metric-label {
        font-size: 0.65rem;
        text-transform: uppercase;
        color: var(--text-muted);
        letter-spacing: 0.05em;
        margin: 0;
    }
    
    /* Sensor Chips */
    .sensor-chips {
        display: flex;
        gap: 0.5rem;
        margin-top: 1rem;
        justify-content: space-between;
    }
    .sensor-chip {
        background: #f9fafb;
        border: 1px solid var(--border-color);
        border-radius: 8px;
        padding: 0.5rem;
        flex: 1;
        text-align: center;
        display: flex;
        flex-direction: column;
        align-items: center;
        gap: 0.25rem;
    }
    .sensor-chip-icon {
        color: var(--text-muted);
        font-size: 0.9rem;
    }
    .sensor-chip-val {
        font-size: 0.75rem;
        font-weight: 600;
        color: var(--text-main);
    }

    /* Terminal */
    .terminal {
        background: var(--terminal-bg);
        border-radius: 12px;
        padding: 1.25rem;
        min-height: 260px;
        max-height: 320px;
        color: #a1a1aa;
        font-family: 'JetBrains Mono', monospace;
        font-size: 0.8rem;
        overflow-y: auto;
    }
    .terminal-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        border-bottom: 1px solid #333;
        padding-bottom: 0.75rem;
        margin-bottom: 0.75rem;
        color: #71717a;
        font-size: 0.75rem;
    }
    .term-time { color: #d4d4d8; }
    .term-pub { color: #f97316; }
    .term-sub { color: #3b82f6; }
    .term-rec { color: #22c55e; }
    .term-beat { color: #a1a1aa; }
    .term-topic { color: #e4e4e7; }
    
    /* Robot Status */
    .robot-status {
        display: flex;
        align-items: center;
        gap: 1.5rem;
    }
    .battery-circle {
        position: relative;
        width: 64px;
        height: 64px;
        border-radius: 50%;
        border: 4px solid var(--accent-blue-light);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 1.5rem;
        color: var(--accent-blue);
    }
    .battery-circle::before {
        content: '';
        position: absolute;
        inset: -4px;
        border-radius: 50%;
        border: 4px solid var(--accent-blue);
        clip-path: polygon(50% 0, 100% 0, 100% 100%, 50% 100%);
    }

    /* Streamlit Button Overrides */
    div[data-testid="stButton"] button {
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s;
    }
    div[data-testid="stButton"] button[kind="primary"] {
        background: var(--accent-blue);
        color: white;
        border: none;
    }
    div[data-testid="stButton"] button[kind="secondary"] {
        background: white;
        color: var(--text-main);
        border: 1px solid var(--border-color);
    }

    /* Chat Styling */
    .chat-header {
        display: flex;
        justify-content: space-between;
        align-items: center;
        padding-bottom: 1rem;
        border-bottom: 1px solid var(--border-color);
        margin-bottom: 1rem;
    }
    .chat-header-title {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        font-weight: 600;
        font-size: 1rem;
        color: var(--text-main);
    }
    .chat-header-stats {
        font-size: 0.75rem;
        color: var(--text-muted);
        text-transform: uppercase;
        display: flex;
        gap: 1.5rem;
    }
    .chat-header-stats strong {
        color: var(--text-main);
        font-size: 0.85rem;
    }
    .ai-msg, .user-msg {
        display: flex;
        gap: 1rem;
        margin-bottom: 1.5rem;
    }
    .msg-icon {
        width: 32px;
        height: 32px;
        border-radius: 50%;
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 14px;
        flex-shrink: 0;
    }
    .ai-msg .msg-icon { background: #e5e7eb; }
    .user-msg .msg-icon { background: var(--accent-blue); color: white; margin-left: auto; order: 2; }
    
    .msg-bubble {
        background: #f3f4f6;
        padding: 1rem;
        border-radius: 12px;
        border-top-left-radius: 2px;
        font-size: 0.9rem;
        color: var(--text-main);
        max-width: 80%;
    }
    .user-msg .msg-bubble {
        background: var(--accent-blue);
        color: white;
        border-radius: 12px;
        border-top-right-radius: 2px;
        order: 1;
    }
    
    /* Quick Actions */
    .quick-actions {
        display: flex;
        gap: 0.5rem;
        margin-bottom: 1rem;
    }
    .quick-action-btn {
        background: white;
        border: 1px solid var(--border-color);
        border-radius: 999px;
        padding: 0.4rem 1rem;
        font-size: 0.8rem;
        color: var(--text-muted);
        cursor: pointer;
        transition: all 0.2s;
    }
    .quick-action-btn:hover {
        border-color: var(--accent-blue);
        color: var(--accent-blue);
    }

    /* Streamlit overrides for inputs */
    [data-testid="stChatInput"] {
        border-radius: 12px;
        border: 1px solid var(--border-color);
    }
</style>
""",
    unsafe_allow_html=True,
)


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
        st.session_state.maison = MaisonConnectee()
        st.session_state.agent.mettre_a_jour_maison(st.session_state.maison)


def refresh_weather():
    now = datetime.now()
    refresh_due = (
        st.session_state.meteo_data is None
        or st.session_state.derniere_maj_meteo is None
        or (now - st.session_state.derniere_maj_meteo).seconds > 1800
    )
    if refresh_due:
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
    st.session_state.last_manual_result = result
    st.rerun()


def status_chip(label, is_on=False):
    status_class = "on" if is_on else "off"
    return f'<span class="device-status {status_class}">{escape(label)}</span>'


def device_card(icon, name, sublabel, status, is_on):
    active_class = "active" if is_on else ""
    return f"""
    <div class="card device-card {active_class}">
        <div class="device-header">
            <div class="device-icon">{icon}</div>
            {status_chip(status, is_on)}
        </div>
        <div>
            <p class="device-name">{escape(name)}</p>
            <p class="device-sub">{escape(sublabel)}</p>
        </div>
    </div>
    """


def sensor_card(icon, val, label):
    return f"""
    <div class="sensor-chip">
        <div class="sensor-chip-icon">{icon}</div>
        <div class="sensor-chip-val">{escape(str(val))}</div>
        <div class="weather-metric-label">{escape(label)}</div>
    </div>
    """


def event_row(event):
    time = event.get('timestamp', '')
    action = event.get('action', 'EVENT').upper()
    target = event.get('target', '')
    
    # color mapping for terminal
    if action == "PUBLISH":
        color_class = "term-pub"
    elif action == "SUBSCRIBE":
        color_class = "term-sub"
    elif action == "RECEIVE":
        color_class = "term-rec"
    elif action == "HEARTBEAT":
        color_class = "term-beat"
    else:
        color_class = "term-topic"

    return f'<div><span class="term-time">[{time}]</span> <span class="{color_class}">{escape(action)}:</span> {escape(target)}</div>'


def safe_audio(message):
    try:
        return st.session_state.robot_voix.parler(message)
    except Exception:
        return None


def quick_prompt_specs():
    return [
        "Turn On Light",
        "Gas Level",
        "Lock All Doors",
        "Robot View"
    ]


def submit_chat_message(user_input):
    if not user_input or not user_input.strip():
        return

    cleaned_input = user_input.strip()
    if st.session_state.meteo_data:
        st.session_state.agent.mettre_a_jour_meteo(st.session_state.meteo_data)
    st.session_state.agent.mettre_a_jour_maison(st.session_state.maison)
    snapshot, living_room = current_snapshot()
    st.session_state.agent.mettre_a_jour_capteurs(living_room["sensors"])

    st.session_state.historique_chat.append(
        {
            "role": "user",
            "message": cleaned_input,
            "timestamp": datetime.now().strftime("%H:%M"),
        }
    )
    with st.spinner("RoboCompagnon is thinking..."):
        response = st.session_state.agent.repondre(cleaned_input)
    st.session_state.historique_chat.append(
        {
            "role": "robot",
            "message": response,
            "timestamp": datetime.now().strftime("%H:%M"),
        }
    )

    if st.session_state.auto_play_voice and response != st.session_state.last_voice_message:
        st.session_state.last_voice_message = response

    st.rerun()


init_session()
refresh_weather()
snapshot, living_room = current_snapshot()

alerts = snapshot.get("alerts", {})
devices = living_room["devices"]
sensors = living_room["sensors"]
light = devices["light_main"]
ac = devices["ac_main"]
door = devices.get("door_main")
gas_ppm = sensors.get("gas_ppm", 0)
gas_alert = alerts.get("gas", False)
occupancy = sensors.get("occupancy", False)

# TOP BAR
st.markdown(
    """
    <div class="top-bar">
        <h1 class="top-bar-title">RoboCompagnon Console</h1>
        <div style="display:flex; gap: 1rem; align-items:center; color: #667085;">
            <span>🔍</span>
            <span>⚠️</span>
            <span>🔄</span>
            <div style="width:32px; height:32px; border-radius:50%; background:#0066cc; color:white; display:flex; align-items:center; justify-content:center; font-size:12px;">DEV</div>
        </div>
    </div>
    """,
    unsafe_allow_html=True
)

# HERO
_mode = os.environ.get("IOT_MODE", "simulator").upper()
_broker = os.environ.get("MQTT_HOST", "localhost")
_gas_status = "Gas Alert Active" if gas_alert else "All sensors nominal"
st.markdown(
    f"""
    <div class="hero">
        <div class="hero-tag">{_mode} Mode</div>
        <h2 class="hero-title">RoboCompagnon Home Node</h2>
        <p class="hero-subtitle">Broker: {escape(_broker)} &nbsp;|&nbsp; {escape(_gas_status)}</p>
    </div>
    """,
    unsafe_allow_html=True
)

if gas_alert:
    st.error("Gas alert is active. Check the living room gas level and ventilation before sending more commands.")

# ROW 1: Devices and Weather
col1, col2 = st.columns([1.5, 1])

with col1:
    st.markdown(
        """
        <div class="section-header">
            <h3 class="section-title">Active Devices</h3>
            <span class="section-subtitle">Living Room</span>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    device_cols = st.columns(3)
    
    # Light Card
    with device_cols[0]:
        is_on = light["state"] == "on"
        st.markdown(device_card("💡", "Main Light", "LIVING_ROOM_01", light["state"].upper(), is_on), unsafe_allow_html=True)
        if is_on:
            if st.button("Turn Off", key="light_off", use_container_width=True):
                mqtt_command("turn_off", device_type="light")
        else:
            if st.button("Turn On", key="light_on", use_container_width=True):
                mqtt_command("turn_on", device_type="light")

    # AC Card
    with device_cols[1]:
        is_on = ac["state"] == "on"
        st.markdown(device_card("❄️", "AC Unit", f"{ac['target_temp']}°C Target", f"{ac['target_temp']}°C", is_on), unsafe_allow_html=True)
        if is_on:
            if st.button("Turn Off", key="ac_off", use_container_width=True):
                mqtt_command("turn_off", device_type="ac")
        else:
            if st.button("Turn On", key="ac_on", use_container_width=True):
                mqtt_command("turn_on", device_type="ac")
                
    # Door Card
    with device_cols[2]:
        if door:
            is_locked = door["state"] == "locked"
            st.markdown(device_card("🔓" if not is_locked else "🔒", "Front Door", "ENTRY_WAY_HUB", door["state"].upper(), not is_locked), unsafe_allow_html=True)
            if is_locked:
                if st.button("Unlock", key="door_unlock", use_container_width=True):
                    mqtt_command("unlock", device_type="door")
            else:
                if st.button("Lock", key="door_lock", use_container_width=True):
                    mqtt_command("lock", device_type="door")

with col2:
    if st.session_state.meteo_data:
        meteo = st.session_state.meteo_data
        st.markdown(
            f"""
            <div class="card weather-panel">
                <div class="weather-main">
                    <div class="weather-icon">☀️</div>
                    <div class="weather-info">
                        <h3>Weather Panel</h3>
                        <p>{escape(meteo['ville'])}</p>
                    </div>
                </div>
                <div class="weather-metrics">
                    <div class="weather-metric">
                        <p class="weather-metric-label">TEMP</p>
                        <p class="weather-metric-val">{meteo['temperature']}°</p>
                    </div>
                    <div class="weather-metric">
                        <p class="weather-metric-label">HUMIDITY</p>
                        <p class="weather-metric-val">{meteo['humidite']}%</p>
                    </div>
                    <div class="weather-metric">
                        <p class="weather-metric-label">WIND</p>
                        <p class="weather-metric-val">{meteo['vent_kmh']}km/h</p>
                    </div>
                    <div class="weather-metric">
                        <p class="weather-metric-label">AQI</p>
                        <p class="weather-metric-val" style="color: #059669;">Good</p>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )
    
    # Sensors row below weather
    sensors_html = f"""
    <div class="sensor-chips">
        {sensor_card("🌡️", f"{sensors['temperature']}°", "TEMP")}
        {sensor_card("💧", f"{sensors['humidity']}%", "HUMID")}
        {sensor_card("☀️", f"{sensors['light_level']}", "LUX")}
        {sensor_card("💨", f"{gas_ppm}ppm", "GAS")}
        {sensor_card("👤", "YES" if occupancy else "NO", "OCCUPY")}
    </div>
    """
    st.markdown(sensors_html, unsafe_allow_html=True)

st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)

# ROW 2: Robot Status + Timer AND Terminal
col3, col4 = st.columns([1, 1.5])

with col3:
    etat_robot = st.session_state.agent.robot.etat()
    st.markdown(
        f"""
        <div class="card" style="margin-bottom: 1rem;">
            <h3 class="section-title" style="font-size:1rem; border-bottom:none; margin-bottom:0.5rem;">Robot Physical Status</h3>
            <div class="robot-status">
                <div class="battery-circle">🤖</div>
                <div style="flex:1;">
                    <div style="display:flex; justify-content:space-between; margin-bottom:0.25rem;">
                        <span style="font-size:0.85rem; color:var(--text-muted);">Battery</span>
                        <span style="font-size:0.85rem; font-weight:600; color:var(--accent-blue);">{etat_robot['batterie']:.0f}%</span>
                    </div>
                    <div style="height:4px; background:#f3f4f6; border-radius:2px; margin-bottom:1rem;">
                        <div style="height:100%; width:{etat_robot['batterie']}%; background:var(--accent-blue); border-radius:2px;"></div>
                    </div>
                    <div style="font-size:0.85rem; color:var(--text-main);">
                        🧭 Heading: {etat_robot['direction_text']}
                    </div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    # Pomodoro
    st.markdown(
        """
        <div class="card" style="padding-bottom: 0;">
            <h3 class="section-title" style="font-size:1rem; border-bottom:none; margin-bottom:0.5rem;">⏱️ Deep Work Timer</h3>
        """,
        unsafe_allow_html=True
    )
    pomodoro_state = st.session_state.agent.pomodoro.etat_session()
    if pomodoro_state["active"]:
        st.success(f"Active: {pomodoro_state['matiere']} ({pomodoro_state['temps_restant']})")
        if st.button("Stop Session", key="pomo_stop", use_container_width=True):
            st.session_state.agent.pomodoro.arreter_session()
            st.rerun()
    else:
        with st.form("pomo_form"):
            colA, colB = st.columns(2)
            duree = colA.number_input("Duration", min_value=5, max_value=60, value=25, label_visibility="collapsed")
            matiere = colB.selectbox("Mode", ["Focus", "Study", "Coding"], label_visibility="collapsed")
            submit = st.form_submit_button("Start Session", use_container_width=True, type="primary")
            if submit:
                st.session_state.agent.pomodoro.demarrer_session_travail(matiere, duree)
                st.rerun()
    st.markdown("</div>", unsafe_allow_html=True)


with col4:
    events = st.session_state.agent.iot_controller.get_recent_events(limit=8)
    terminal_rows = "".join([event_row(e) for e in events]) if events else "<div>No recent events.</div>"
    
    st.markdown(
        f"""
        <div class="terminal">
            <div class="terminal-header">
                <span>> MQTT_STREAM_LIVE</span>
                <span>v2.4.1</span>
            </div>
            {terminal_rows}
        </div>
        """,
        unsafe_allow_html=True
    )

st.write("")
st.markdown("<div style='margin-top:1.5rem;'></div>", unsafe_allow_html=True)

# ROW 3: Chat Interface
chat_history = st.session_state.historique_chat

st.markdown(
    """
    <div class="card" style="padding: 1.5rem;">
        <div class="chat-header">
            <div class="chat-header-title">
                <div style="width:28px; height:28px; border-radius:50%; background:var(--accent-blue); color:white; display:flex; align-items:center; justify-content:center;">✨</div>
                RoboCompagnon AI
                <span style="font-size:0.6rem; color:#059669; margin-left:0.5rem;">● Neural Engine Online</span>
            </div>
            <div class="chat-header-stats">
                <div>MODE<br><strong>{os.environ.get("IOT_MODE", "simulator").upper()}</strong></div>
                <div>BROKER<br><strong style="color:var(--accent-blue);">{os.environ.get("MQTT_HOST", "localhost")}</strong></div>
            </div>
        </div>
    """,
    unsafe_allow_html=True
)

chat_container = st.container(height=350)
with chat_container:
    if not chat_history:
        st.markdown(
            """
            <div class="ai-msg">
                <div class="msg-icon">🤖</div>
                <div class="msg-bubble">
                    Hello Developer. All systems are currently in deep learning mode. I've optimized the AC schedule based on today's weather forecast. Shall I run the diagnostic routine for the Kitchen node?
                </div>
            </div>
            """,
            unsafe_allow_html=True
        )

    for idx, msg in enumerate(chat_history):
        role = msg["role"]
        if role == "robot":
            st.markdown(
                f"""
                <div class="ai-msg">
                    <div class="msg-icon">🤖</div>
                    <div class="msg-bubble">
                        {escape(msg["message"])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )
            # small audio button hack
            if st.button("🔊", key=f"speak_{idx}"):
                audio_file = safe_audio(msg["message"])
                if audio_file:
                    st.audio(audio_file, format="audio/mp3", autoplay=True)
        else:
            st.markdown(
                f"""
                <div class="user-msg">
                    <div class="msg-icon">DEV</div>
                    <div class="msg-bubble">
                        {escape(msg["message"])}
                    </div>
                </div>
                """,
                unsafe_allow_html=True
            )

# Quick Actions
quick_cols = st.columns([1,1,1,1, 4]) # 4 is dummy for spacing
for idx, label in enumerate(quick_prompt_specs()):
    with quick_cols[idx]:
        if st.button(label, key=f"quick_{idx}", use_container_width=True):
            submit_chat_message(label)

user_input = st.chat_input("Type a command or ask a question...")
if user_input:
    submit_chat_message(user_input)

st.markdown("</div>", unsafe_allow_html=True) # close chat card

# SIDEBAR
with st.sidebar:
    st.markdown(
        """
        <div style="margin-bottom: 2rem;">
            <h2 style="color: var(--accent-blue); font-weight:700; font-size:1.4rem; margin:0;">RoboCompagnon</h2>
            <p style="color: var(--text-muted); font-size:0.8rem; margin:0;">System Console</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    st.button("⚙️ MQTT Topics", use_container_width=True, type="secondary")
    st.button("📊 Room Stats", use_container_width=True, type="secondary")
    st.button("🔔 Reminders", use_container_width=True, type="secondary")
    st.button("⏱️ Pomodoro", use_container_width=True, type="secondary")
    st.button("⚙️ Utilities", use_container_width=True, type="secondary")
    
    st.write("---")
    
    if st.button("Refresh System", type="primary", use_container_width=True):
        st.session_state.derniere_maj_meteo = None
        refresh_weather()
        st.rerun()
        
    st.write("---")
    
    if st.button("🔄 System Reset", use_container_width=True, type="secondary"):
        st.session_state.agent.iot_controller.reset()
        st.rerun()
        
    if st.button("🗑️ Clear Logs", use_container_width=True, type="secondary"):
        st.session_state.historique_chat = []
        st.rerun()
