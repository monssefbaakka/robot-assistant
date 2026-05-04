import streamlit as st
from datetime import datetime

from agent import AgentRobot
from meteo import MeteoAPI
from tts import RobotVoix
from objets_connectes import MaisonConnectee


st.set_page_config(
    page_title="RoboCompagnon - MQTT IoT Assistant",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
<style>
    .main-header {
        font-size: 2.4rem;
        font-weight: 700;
        color: #12344d;
        text-align: center;
        margin-bottom: 1rem;
    }
    .panel {
        background: linear-gradient(180deg, #f8fbfd 0%, #eef4f7 100%);
        padding: 1.25rem;
        border-radius: 18px;
        border: 1px solid #d4e2ea;
        margin-bottom: 1rem;
    }
    .device-card {
        background: white;
        padding: 1rem;
        border-radius: 14px;
        border: 1px solid #d9e4ea;
        box-shadow: 0 8px 24px rgba(18, 52, 77, 0.06);
    }
    .metric-value {
        font-size: 2rem;
        font-weight: 700;
        color: #12344d;
        margin: 0;
    }
    .metric-label {
        color: #527386;
        margin: 0;
    }
    .chat-message {
        padding: 0.9rem 1rem;
        border-radius: 12px;
        margin: 0.5rem 0;
    }
    .user-message {
        background: #e8f4fd;
        border-left: 4px solid #2893d5;
    }
    .robot-message {
        background: #edf8ef;
        border-left: 4px solid #3ca85e;
    }
</style>
""",
    unsafe_allow_html=True,
)


def init_session():
    if "agent" not in st.session_state:
        st.session_state.agent = AgentRobot(nom_utilisateur="Monssef")
        st.session_state.historique_chat = []
        st.session_state.meteo_api = MeteoAPI(ville="Rabat", pays="MA")
        st.session_state.meteo_data = None
        st.session_state.derniere_maj_meteo = None
        st.session_state.robot_voix = RobotVoix(langue="fr")
        st.session_state.auto_play_voice = False
        st.session_state.last_manual_result = None
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


def legacy_light_command(command_text):
    result = st.session_state.maison.executer_commande(command_text)
    st.session_state.last_manual_result = {
        "ok": result.get("succes", False),
        "message": result.get("message", "Commande exécutée."),
    }
    st.rerun()


init_session()
refresh_weather()
snapshot, living_room = current_snapshot()

devices = living_room["devices"]
sensors = living_room["sensors"]
light = devices["light_main"]
ac = devices["ac_main"]

st.markdown('<p class="main-header">MQTT Smart-Home Simulator + RoboCompagnon</p>', unsafe_allow_html=True)

top_left, top_right = st.columns([1.1, 1.4])

with top_left:
    st.markdown(
        """
        <div class="panel">
            <h3 style="margin-top:0;">Home Node</h3>
            <p style="margin-bottom:0.5rem;">Transport: <strong>MQTT topic bus</strong></p>
            <p style="margin-bottom:0.5rem;">Room: <strong>Living Room</strong></p>
            <p style="margin-bottom:0;">State source: <strong>digital twin</strong></p>
        </div>
        """,
        unsafe_allow_html=True,
    )

    light_col, ac_col = st.columns(2)
    with light_col:
        st.markdown(
            f"""
            <div class="device-card">
                <h4 style="margin-top:0;">💡 Main Light</h4>
                <p class="metric-value">{light['state'].upper()}</p>
                <p class="metric-label">Brightness: {light['brightness']}%</p>
                <p class="metric-label">Power: {light['power_w']} W</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if light["state"] == "on":
            if st.button("Turn Light Off", use_container_width=True):
                mqtt_command("turn_off", device_type="light")
        else:
            if st.button("Turn Light On", use_container_width=True):
                mqtt_command("turn_on", device_type="light")

    with ac_col:
        st.markdown(
            f"""
            <div class="device-card">
                <h4 style="margin-top:0;">❄️ Main AC</h4>
                <p class="metric-value">{ac['state'].upper()}</p>
                <p class="metric-label">Target: {ac['target_temp']}C</p>
                <p class="metric-label">Power: {ac['power_w']} W</p>
            </div>
            """,
            unsafe_allow_html=True,
        )
        if ac["state"] == "on":
            if st.button("Turn AC Off", use_container_width=True):
                mqtt_command("turn_off", device_type="ac")
        else:
            if st.button("Turn AC On", use_container_width=True):
                mqtt_command("turn_on", device_type="ac")

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
    sensor_cols = st.columns(3)
    sensor_specs = [
        ("🌡️ Temperature", f"{sensors['temperature']}C", "Room sensor"),
        ("💧 Humidity", f"{sensors['humidity']}%", "Room sensor"),
        ("💡 Light Level", f"{sensors['light_level']} lux", "Room sensor"),
    ]
    for col, (title, value, subtitle) in zip(sensor_cols, sensor_specs):
        with col:
            st.markdown(
                f"""
                <div class="device-card">
                    <h4 style="margin-top:0;">{title}</h4>
                    <p class="metric-value">{value}</p>
                    <p class="metric-label">{subtitle}</p>
                </div>
                """,
                unsafe_allow_html=True,
            )

    if st.session_state.meteo_data:
        meteo = st.session_state.meteo_data
        st.markdown(
            f"""
            <div class="panel">
                <h3 style="margin-top:0;">Outside Weather Feed</h3>
                <p style="margin-bottom:0.25rem;"><strong>{meteo['ville']}</strong> - {meteo['description']}</p>
                <p style="margin-bottom:0.25rem;">Temperature: {meteo['temperature']}C (feels like {meteo['ressenti']}C)</p>
                <p style="margin-bottom:0;">Humidity: {meteo['humidite']}% | Wind: {meteo['vent_kmh']} km/h</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

st.markdown("---")

robot_col, events_col = st.columns([1, 1.2])

with robot_col:
    st.subheader("Robot and Study Assistant")
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

    st.markdown("---")
    st.subheader("Legacy Connected Light")
    legacy_light = st.session_state.maison.lumiere.obtenir_etat()
    st.markdown(
        f"""
        <div class="device-card">
            <h4 style="margin-top:0;">💡 Chambre Light</h4>
            <p class="metric-value">{legacy_light['etat_texte'].upper()}</p>
            <p class="metric-label">Legacy object simulation from `objets_connectes.py`</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    legacy_cols = st.columns(2)
    with legacy_cols[0]:
        if st.button("Legacy Light On", use_container_width=True, disabled=legacy_light["etat"]):
            legacy_light_command("Allume la lumière")
    with legacy_cols[1]:
        if st.button("Legacy Light Off", use_container_width=True, disabled=not legacy_light["etat"]):
            legacy_light_command("Éteins la lumière")

with events_col:
    st.subheader("MQTT Event Log")
    events = st.session_state.agent.iot_controller.get_recent_events(limit=8)
    if not events:
        st.info("No MQTT events yet.")
    else:
        for event in events:
            title = f"{event['action']} -> {event['target']}"
            body = f"{event['timestamp']} | {event['status']} | {event['room']}"
            if event.get("raw_text"):
                body += f"\n{event['raw_text']}"
            if event["status"] == "success":
                st.success(f"{title}\n\n{body}")
            else:
                st.error(f"{title}\n\n{body}")

st.markdown("---")
st.subheader("Conversation with RoboCompagnon")

chat_container = st.container()
with chat_container:
    if not st.session_state.historique_chat:
        st.info("Try: 'turn off the lights of the living room' or 'tell me the current temperature of the room'")

    for idx, msg in enumerate(st.session_state.historique_chat):
        if msg["role"] == "user":
            st.markdown(
                f'<div class="chat-message user-message">👤 <strong>You:</strong> {msg["message"]}</div>',
                unsafe_allow_html=True,
            )
        else:
            st.markdown(
                f'<div class="chat-message robot-message">🤖 <strong>RoboCompagnon:</strong> {msg["message"]}</div>',
                unsafe_allow_html=True,
            )
            audio_col, _ = st.columns([1, 12])
            with audio_col:
                if st.button("🔊", key=f"speak_{idx}", help="Listen to this reply"):
                    audio_file = st.session_state.robot_voix.parler(msg["message"])
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
    st.rerun()

with st.sidebar:
    st.title("Control Panel")
    st.markdown("### MQTT Topics")
    st.code(
        "\n".join(
            [
                "robocompagnon/home/commands",
                "robocompagnon/home/responses",
                "robocompagnon/home/events",
                "robocompagnon/home/rooms/living_room/devices/+/state",
                "robocompagnon/home/rooms/living_room/sensors/+",
            ]
        )
    )

    st.markdown("### Legacy Wokwi Demo")
    st.markdown(
        "[Open the Arduino/Wokwi export](./kira%20-%20Wokwi%20ESP32,%20STM32,%20Arduino%20Simulator.htm)"
    )

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
        st.rerun()
    if st.button("Reset robot", use_container_width=True):
        st.session_state.agent.robot.reset()
        st.rerun()

st.markdown("---")
st.caption("RoboCompagnon MQTT IoT simulator - local digital twin with topic-based device control.")
