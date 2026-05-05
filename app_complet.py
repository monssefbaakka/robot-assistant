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
        --bg-soft: linear-gradient(180deg, #f5f1e8 0%, #edf4f2 100%);
        --panel-bg: rgba(255, 255, 255, 0.84);
        --panel-border: #c8d7d2;
        --text-strong: #16323f;
        --text-soft: #5b7078;
        --accent: #d97a2b;
        --good: #287d4f;
        --warn: #b95a17;
        --danger: #a83832;
    }

    .stApp {
        background:
            radial-gradient(circle at top left, rgba(217, 122, 43, 0.12), transparent 28%),
            radial-gradient(circle at top right, rgba(40, 125, 79, 0.10), transparent 24%),
            var(--bg-soft);
    }

    .hero {
        background: linear-gradient(135deg, rgba(255, 248, 239, 0.96), rgba(238, 246, 243, 0.96));
        border: 1px solid var(--panel-border);
        border-radius: 22px;
        padding: 1.35rem 1.4rem;
        margin-bottom: 1rem;
        box-shadow: 0 18px 40px rgba(22, 50, 63, 0.08);
    }

    .hero-title {
        color: var(--text-strong);
        font-size: 2.3rem;
        font-weight: 800;
        line-height: 1.05;
        margin: 0 0 0.35rem 0;
    }

    .hero-copy {
        color: var(--text-soft);
        margin: 0;
        font-size: 1rem;
    }

    .panel, .device-card, .event-card, .chat-card {
        background: var(--panel-bg);
        backdrop-filter: blur(6px);
        border: 1px solid var(--panel-border);
        border-radius: 18px;
        box-shadow: 0 14px 32px rgba(22, 50, 63, 0.06);
    }

    .panel {
        padding: 1.1rem 1.15rem;
        margin-bottom: 1rem;
    }

    .device-card {
        padding: 1rem;
        min-height: 168px;
    }

    .event-card {
        padding: 0.95rem 1rem;
        margin-bottom: 0.75rem;
    }

    .chat-card {
        padding: 0.9rem 1rem;
        margin: 0.45rem 0;
    }

    .chat-shell {
        background: linear-gradient(180deg, rgba(255, 255, 255, 0.88), rgba(247, 250, 249, 0.9));
        border: 1px solid var(--panel-border);
        border-radius: 24px;
        padding: 1rem 1rem 0.4rem 1rem;
        box-shadow: 0 18px 38px rgba(22, 50, 63, 0.08);
    }

    .chat-toolbar {
        display: flex;
        justify-content: space-between;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 0.85rem;
    }

    .chat-title {
        color: var(--text-strong);
        font-size: 1.1rem;
        font-weight: 780;
        margin: 0;
    }

    .chat-subtitle {
        color: var(--text-soft);
        margin: 0.15rem 0 0 0;
        font-size: 0.92rem;
    }

    .chat-hint {
        background: rgba(22, 50, 63, 0.05);
        border: 1px dashed rgba(22, 50, 63, 0.14);
        border-radius: 16px;
        padding: 0.9rem 1rem;
        color: var(--text-soft);
        margin-bottom: 0.85rem;
    }

    .chat-meta {
        color: var(--text-soft);
        font-size: 0.8rem;
        margin-top: 0.35rem;
    }

    .status-chip {
        display: inline-block;
        padding: 0.2rem 0.65rem;
        border-radius: 999px;
        font-size: 0.8rem;
        font-weight: 700;
        letter-spacing: 0.02em;
        margin-bottom: 0.7rem;
    }

    .status-ok {
        background: rgba(40, 125, 79, 0.12);
        color: var(--good);
    }

    .status-warn {
        background: rgba(185, 90, 23, 0.12);
        color: var(--warn);
    }

    .status-danger {
        background: rgba(168, 56, 50, 0.12);
        color: var(--danger);
    }

    .status-neutral {
        background: rgba(22, 50, 63, 0.08);
        color: var(--text-strong);
    }

    .card-title {
        color: var(--text-strong);
        font-size: 1rem;
        font-weight: 700;
        margin: 0 0 0.5rem 0;
    }

    .metric-value {
        color: var(--text-strong);
        font-size: 2rem;
        font-weight: 800;
        margin: 0;
        line-height: 1;
    }

    .metric-label, .meta-line {
        color: var(--text-soft);
        margin: 0.25rem 0 0 0;
    }

    .section-title {
        color: var(--text-strong);
        font-size: 1.15rem;
        font-weight: 750;
        margin-bottom: 0.75rem;
    }

    .chat-user {
        border-left: 4px solid #288db8;
    }

    .chat-robot {
        border-left: 4px solid #2f8f64;
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


def status_chip(label, tone="neutral"):
    return f'<span class="status-chip status-{tone}">{escape(label)}</span>'


def device_card(title, value, lines, tone="neutral"):
    details = "".join(f'<p class="metric-label">{escape(line)}</p>' for line in lines)
    return f"""
    <div class="device-card">
        {status_chip(value, tone)}
        <p class="card-title">{escape(title)}</p>
        <p class="metric-value">{escape(value)}</p>
        {details}
    </div>
    """


def sensor_card(title, value, subtitle):
    return f"""
    <div class="device-card">
        <p class="card-title">{escape(title)}</p>
        <p class="metric-value">{escape(value)}</p>
        <p class="metric-label">{escape(subtitle)}</p>
    </div>
    """


def event_card(event):
    status = event.get("status", "unknown")
    tone = "ok" if status == "success" else "danger"
    title = f"{event.get('action', 'event')} -> {event.get('target', 'unknown')}"
    meta = f"{event.get('timestamp', '')} | {status} | {event.get('room', '')}"
    raw_text = event.get("raw_text") or ""
    return f"""
    <div class="event-card">
        {status_chip(status.upper(), tone)}
        <p class="card-title">{escape(title)}</p>
        <p class="meta-line">{escape(meta)}</p>
        <p class="metric-label">{escape(raw_text)}</p>
    </div>
    """


def safe_audio(message):
    try:
        return st.session_state.robot_voix.parler(message)
    except Exception:
        return None


def quick_prompt_specs():
    return [
        ("Turn On Light", "turn on light"),
        ("Turn Off Light", "turn off light"),
        ("Unlock Door", "unlock the door"),
        ("Gas Level", "tell me the current gas level"),
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
transport_label = snapshot.get("meta", {}).get("transport", "mqtt")
runtime_mode = os.environ.get("IOT_MODE", "simulator")
runtime_broker = f"{os.environ.get('MQTT_HOST', 'localhost')}:{os.environ.get('MQTT_PORT', '1883')}"

st.markdown(
    """
    <div class="hero">
        <p class="hero-title">RoboCompagnon Smart Home Console</p>
        <p class="hero-copy">
            Local MQTT simulator for the living room digital twin. The dashboard reads persisted state,
            visualizes room conditions, and sends device commands through the controller.
        </p>
    </div>
    """,
    unsafe_allow_html=True,
)

if gas_alert:
    st.error("Gas alert is active. Check the living room gas level and ventilation before sending more commands.")

top_left, top_right = st.columns([1.05, 1.35])

with top_left:
    st.markdown('<div class="section-title">Home Node</div>', unsafe_allow_html=True)
    st.markdown(
        f"""
            <div class="panel">
            {status_chip(transport_label.upper(), 'neutral')}
            <p class="card-title">Living Room Digital Twin</p>
            <p class="meta-line">Runtime mode: {escape(runtime_mode)}</p>
            <p class="meta-line">MQTT broker: {escape(runtime_broker)}</p>
            <p class="meta-line">State source: persisted JSON snapshot</p>
            <p class="meta-line">Outside weather source: {escape(snapshot['outside']['source'])}</p>
            <p class="meta-line">Last update: {escape(snapshot['meta']['last_update'])}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    device_cols = st.columns(3)
    with device_cols[0]:
        light_tone = "ok" if light["state"] == "on" else "neutral"
        st.markdown(
            device_card(
                "Main Light",
                light["state"].upper(),
                [f"Brightness: {light['brightness']}%", f"Power: {light['power_w']} W"],
                light_tone,
            ),
            unsafe_allow_html=True,
        )
        if light["state"] == "on":
            if st.button("Turn Light Off", use_container_width=True):
                mqtt_command("turn_off", device_type="light")
        else:
            if st.button("Turn Light On", use_container_width=True):
                mqtt_command("turn_on", device_type="light")

    with device_cols[1]:
        ac_tone = "ok" if ac["state"] == "on" else "neutral"
        st.markdown(
            device_card(
                "Main AC",
                ac["state"].upper(),
                [f"Target: {ac['target_temp']} C", f"Power: {ac['power_w']} W"],
                ac_tone,
            ),
            unsafe_allow_html=True,
        )
        if ac["state"] == "on":
            if st.button("Turn AC Off", use_container_width=True):
                mqtt_command("turn_off", device_type="ac")
        else:
            if st.button("Turn AC On", use_container_width=True):
                mqtt_command("turn_on", device_type="ac")

    with device_cols[2]:
        if door:
            door_locked = door["state"] == "locked"
            door_tone = "warn" if door_locked else "ok"
            st.markdown(
                device_card(
                    "Front Door",
                    door["state"].upper(),
                    ["Virtual lock state", "Phase 2 device"],
                    door_tone,
                ),
                unsafe_allow_html=True,
            )
            if door_locked:
                if st.button("Unlock Door", use_container_width=True):
                    mqtt_command("unlock", device_type="door")
            else:
                if st.button("Lock Door", use_container_width=True):
                    mqtt_command("lock", device_type="door")

    target_temp = st.slider("AC target temperature", 16, 30, int(ac["target_temp"]))
    if st.button("Apply AC Target", use_container_width=True):
        mqtt_command("set_temperature", device_type="ac", parameters={"target_temp": target_temp})

    if st.session_state.last_manual_result:
        manual_result = st.session_state.last_manual_result
        if manual_result.get("ok"):
            st.success(manual_result["message"])
        else:
            st.error(manual_result["message"])

with top_right:
    st.markdown('<div class="section-title">Sensors and Alerts</div>', unsafe_allow_html=True)
    sensor_cols = st.columns(5)
    sensor_specs = [
        ("Temperature", f"{sensors['temperature']} C", "Room sensor"),
        ("Humidity", f"{sensors['humidity']}%", "Room sensor"),
        ("Light Level", f"{sensors['light_level']} lux", "Room sensor"),
        ("Gas Level", f"{gas_ppm} ppm", "Alert threshold: 400 ppm"),
        ("Occupancy", "Occupied" if occupancy else "Empty", "Manual simulation flag"),
    ]
    for col, (title, value, subtitle) in zip(sensor_cols, sensor_specs):
        with col:
            st.markdown(sensor_card(title, value, subtitle), unsafe_allow_html=True)

    if st.session_state.meteo_data:
        meteo = st.session_state.meteo_data
        st.markdown(
            f"""
            <div class="panel">
                {status_chip('WEATHER FEED', 'neutral')}
                <p class="card-title">Outside Conditions</p>
                <p class="meta-line"><strong>{escape(meteo['ville'])}</strong> - {escape(meteo['description'])}</p>
                <p class="meta-line">Temperature: {meteo['temperature']} C (feels like {meteo['ressenti']} C)</p>
                <p class="meta-line">Humidity: {meteo['humidite']}% | Wind: {meteo['vent_kmh']} km/h</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")

assistant_col, events_col = st.columns([1, 1.15])

with assistant_col:
    st.markdown('<div class="section-title">Robot and Study Assistant</div>', unsafe_allow_html=True)
    etat_robot = st.session_state.agent.robot.etat()
    stat_cols = st.columns(3)
    stat_cols[0].metric("Battery", f"{etat_robot['batterie']:.0f}%")
    stat_cols[1].metric("Actions", etat_robot["nb_actions"])
    stat_cols[2].metric("Direction", etat_robot["direction_text"])

    pomodoro_state = st.session_state.agent.pomodoro.etat_session()
    if pomodoro_state["active"]:
        st.success(f"Pomodoro active: {pomodoro_state['matiere']}")
        st.info(f"Time remaining: {pomodoro_state['temps_restant']}")
        if st.button("Stop Pomodoro", use_container_width=True):
            st.session_state.agent.pomodoro.arreter_session()
            st.rerun()
    else:
        with st.form("pomodoro_form"):
            matiere = st.text_input("Study subject", placeholder="Mathematiques")
            duree = st.slider("Duration (minutes)", 5, 60, 25)
            submit_pomo = st.form_submit_button("Start Pomodoro", use_container_width=True)
        if submit_pomo and matiere:
            st.session_state.agent.pomodoro.demarrer_session_travail(matiere, duree)
            st.rerun()

    st.markdown(
        f"""
        <div class="panel">
            {status_chip('ROOM SUMMARY', 'neutral')}
            <p class="card-title">Operational Notes</p>
            <p class="meta-line">Door state: {escape(door['state'] if door else 'unavailable')}</p>
            <p class="meta-line">Gas alert: {'ACTIVE' if gas_alert else 'clear'}</p>
            <p class="meta-line">Next step: test chat commands or device buttons and verify event log updates.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )

with events_col:
    st.markdown('<div class="section-title">MQTT Event Log</div>', unsafe_allow_html=True)
    events = st.session_state.agent.iot_controller.get_recent_events(limit=8)
    if not events:
        st.info("No MQTT events yet.")
    else:
        for event in events:
            st.markdown(event_card(event), unsafe_allow_html=True)

st.markdown("---")
st.markdown('<div class="section-title">Conversation with RoboCompagnon</div>', unsafe_allow_html=True)

chat_container = st.container()
with chat_container:
    if not st.session_state.historique_chat:
        st.info(
            "Try: 'turn off the lights of the living room', 'unlock the door', or 'tell me the current gas level'."
        )

    for idx, msg in enumerate(st.session_state.historique_chat):
        role = msg["role"]
        message_html = escape(msg["message"])
        if role == "user":
            st.markdown(
                f'<div class="chat-card chat-user"><strong>You:</strong> {message_html}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="chat-card chat-robot"><strong>RoboCompagnon:</strong> {message_html}</div>',
                unsafe_allow_html=True,
            )
            audio_col, _ = st.columns([1, 12])
            with audio_col:
                if st.button("🔊", key=f"speak_{idx}", help="Listen to this reply"):
                    audio_file = safe_audio(msg["message"])
                    if audio_file:
                        st.audio(audio_file, format="audio/mp3", autoplay=True)

with st.form(key="chat_form", clear_on_submit=True):
    chat_cols = st.columns([5, 1])
    with chat_cols[0]:
        user_input = st.text_input(
            "Message",
            placeholder="Ex: turn on the AC in the living room",
            label_visibility="collapsed",
        )
    with chat_cols[1]:
        submit_chat = st.form_submit_button("Send", use_container_width=True)

if submit_chat and user_input:
    if st.session_state.meteo_data:
        st.session_state.agent.mettre_a_jour_meteo(st.session_state.meteo_data)
    st.session_state.agent.mettre_a_jour_maison(st.session_state.maison)
    snapshot, living_room = current_snapshot()
    st.session_state.agent.mettre_a_jour_capteurs(living_room["sensors"])

    st.session_state.historique_chat.append({"role": "user", "message": user_input})
    with st.spinner("RoboCompagnon is thinking..."):
        response = st.session_state.agent.repondre(user_input)
    st.session_state.historique_chat.append({"role": "robot", "message": response})

    if st.session_state.auto_play_voice and response != st.session_state.last_voice_message:
        st.session_state.last_voice_message = response

    st.rerun()

if st.session_state.auto_play_voice and st.session_state.historique_chat:
    last_message = st.session_state.historique_chat[-1]
    if last_message["role"] == "robot" and last_message["message"] == st.session_state.last_voice_message:
        auto_audio = safe_audio(last_message["message"])
        if auto_audio:
            st.audio(auto_audio, format="audio/mp3", autoplay=True)
        st.session_state.last_voice_message = None

with st.sidebar:
    st.title("Control Panel")
    st.markdown("### MQTT Topics")
    st.code(
        "\n".join(
            [
                "robocompagnon/home/commands",
                "robocompagnon/home/responses",
                "robocompagnon/home/events",
                "robocompagnon/home/snapshot",
                "robocompagnon/home/alerts/gas",
                "robocompagnon/home/rooms/living_room/devices/+/state",
                "robocompagnon/home/rooms/living_room/sensors/+",
            ]
        )
    )

    st.markdown("### Current Room")
    st.metric("Temperature", f"{sensors['temperature']} C")
    st.metric("Gas Level", f"{gas_ppm} ppm")
    st.metric("Door", door["state"].title() if door else "Unavailable")

    st.markdown("### Reminders")
    rappels = st.session_state.agent.systeme_rappels.obtenir_prochains_rappels(3)
    if rappels:
        for rappel in rappels:
            st.info(f"{rappel['titre']}\n\n{rappel['date_heure']}\n{rappel['temps_restant']}")
    else:
        st.info("No reminders")

    st.markdown("### Pomodoro Stats")
    stats = st.session_state.agent.pomodoro.obtenir_statistiques()
    st.metric("Sessions today", stats.get("sessions_aujourd_hui", 0))
    st.metric("Total sessions", stats.get("total_sessions", 0))
    st.metric("Total study time", f"{stats.get('temps_total_heures', 0)}h")

    st.markdown("### Tools")
    st.session_state.auto_play_voice = st.checkbox(
        "Automatic voice",
        value=st.session_state.auto_play_voice,
    )
    if st.button("Refresh weather", use_container_width=True):
        st.session_state.derniere_maj_meteo = None
        refresh_weather()
        st.rerun()
    if st.button("Reset MQTT home state", use_container_width=True):
        st.session_state.agent.iot_controller.reset()
        st.session_state.last_manual_result = None
        st.rerun()
    if st.button("Clear conversation", use_container_width=True):
        st.session_state.historique_chat = []
        st.session_state.last_voice_message = None
        st.rerun()
    if st.button("Reset robot", use_container_width=True):
        st.session_state.agent.robot.reset()
        st.rerun()

st.caption("RoboCompagnon MQTT IoT simulator - local digital twin with topic-based device control.")
