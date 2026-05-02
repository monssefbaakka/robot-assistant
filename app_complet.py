# app_complet.py - Interface complète avec robot virtuel et IoT
import streamlit as st
import time
import random
from datetime import datetime
from agent import AgentRobot
from meteo import MeteoAPI
import json
import os

# Configuration de la page
st.set_page_config(
    page_title="RoboCompagnon - Assistant IoT",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour le robot et l'interface
st.markdown("""
<style>
    /* Style général */
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    /* Robot avatar container */
    .robot-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
        border-radius: 20px;
        text-align: center;
        margin-bottom: 2rem;
        box-shadow: 0 10px 30px rgba(0,0,0,0.3);
    }
    
    /* Robot eyes */
    .robot-eyes {
        display: flex;
        justify-content: center;
        gap: 40px;
        margin: 20px 0;
    }
    
    .eye {
        width: 80px;
        height: 80px;
        background: black;
        border-radius: 50%;
        position: relative;
        display: flex;
        align-items: center;
        justify-content: center;
        box-shadow: 0 0 20px rgba(255, 200, 50, 0.8);
        animation: pulse 2s infinite;
    }
    
    .eye-inner {
        width: 60px;
        height: 60px;
        border: 4px solid #FFD700;
        border-radius: 50%;
        background: rgba(255, 215, 0, 0.3);
    }
    
    @keyframes pulse {
        0%, 100% { box-shadow: 0 0 20px rgba(255, 200, 50, 0.8); }
        50% { box-shadow: 0 0 40px rgba(255, 200, 50, 1); }
    }
    
    /* Robot body */
    .robot-body {
        width: 200px;
        height: 120px;
        background: linear-gradient(145deg, #4A5568, #2D3748);
        border-radius: 20px;
        margin: 0 auto;
        position: relative;
        box-shadow: 0 5px 15px rgba(0,0,0,0.3);
    }
    
    /* Sensor cards */
    .sensor-card {
        background: white;
        padding: 1.5rem;
        border-radius: 15px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        border-left: 5px solid #4299e1;
        margin-bottom: 1rem;
    }
    
    .sensor-value {
        font-size: 2.5rem;
        font-weight: bold;
        color: #2d3748;
    }
    
    .sensor-label {
        font-size: 1rem;
        color: #718096;
        margin-top: 0.5rem;
    }
    
    /* Status indicators */
    .status-online {
        color: #48bb78;
        font-weight: bold;
    }
    
    .status-offline {
        color: #f56565;
        font-weight: bold;
    }
    
    /* Chat messages */
    .chat-message {
        padding: 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
    }
    
    .user-message {
        background: #e3f2fd;
        border-left: 4px solid #2196f3;
    }
    
    .robot-message {
        background: #f1f8e9;
        border-left: 4px solid #4caf50;
    }
</style>
""", unsafe_allow_html=True)

# Initialisation de l'agent et des états
if 'agent' not in st.session_state:
    st.session_state.agent = AgentRobot(nom_utilisateur="Monssef")
    st.session_state.historique_chat = []
    st.session_state.capteurs = {
        "temperature": 22.5,
        "humidite": 45,
        "luminosite": 650,
        "presence": False,
        "bruit": 35
    }
    st.session_state.robot_etat = "idle"  # idle, listening, thinking, speaking
    st.session_state.meteo_api = MeteoAPI(ville="Rabat", pays="MA")
    st.session_state.meteo_data = None
    st.session_state.derniere_maj_meteo = None

agent = st.session_state.agent

# Fonction pour mettre à jour les capteurs (simulation)
def simuler_capteurs():
    """Simule les variations des capteurs IoT"""
    # Température varie légèrement
    st.session_state.capteurs["temperature"] += random.uniform(-0.5, 0.5)
    st.session_state.capteurs["temperature"] = round(
        max(15, min(30, st.session_state.capteurs["temperature"])), 1
    )
    
    # Humidité
    st.session_state.capteurs["humidite"] += random.uniform(-2, 2)
    st.session_state.capteurs["humidite"] = int(
        max(30, min(70, st.session_state.capteurs["humidite"]))
    )
    
    # Luminosité (varie selon l'heure)
    heure = datetime.now().hour
    if 6 <= heure < 20:
        st.session_state.capteurs["luminosite"] = random.randint(500, 1000)
    else:
        st.session_state.capteurs["luminosite"] = random.randint(50, 200)
    
    # Bruit ambiant
    st.session_state.capteurs["bruit"] += random.uniform(-5, 5)
    st.session_state.capteurs["bruit"] = int(
        max(20, min(80, st.session_state.capteurs["bruit"]))
    )

# Simuler les capteurs
simuler_capteurs()

# ========== EN-TÊTE ==========
st.markdown('<p class="main-header">🤖 RoboCompagnon - Assistant IoT Intelligent</p>', unsafe_allow_html=True)

# ========== LAYOUT PRINCIPAL ==========
col_robot, col_sensors = st.columns([1, 1])

# ========== COLONNE ROBOT ==========
with col_robot:
    st.markdown("### 🤖 Statut du Robot")
    
    # Avatar du robot
    st.markdown("""
    <div class="robot-container">
        <h2 style="color: white; margin-bottom: 1rem;">🤖 RoboCompagnon</h2>
        
        <div style="font-size: 4rem; margin: 20px 0;">
            ⚫⚫
        </div>
        
        <div style="font-size: 6rem; margin: 10px 0;">
            ▬
        </div>
        
        <p style="color: white; margin-top: 1rem; font-size: 1.2rem;">
            État: <span style="color: #48bb78;">● En ligne</span>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    # État du robot physique (simulation)
    st.markdown("#### 📊 Système")
    
    etat_robot = agent.robot.etat()
    
    sys_col1, sys_col2, sys_col3 = st.columns(3)
    
    with sys_col1:
        batterie = etat_robot['batterie']
        couleur_bat = "#48bb78" if batterie > 50 else "#ed8936" if batterie > 20 else "#f56565"
        st.markdown(f"""
        <div style="text-align: center;">
            <p style="font-size: 2rem; color: {couleur_bat}; margin: 0;">{batterie:.0f}%</p>
            <p style="color: #718096;">🔋 Batterie</p>
        </div>
        """, unsafe_allow_html=True)
    
    with sys_col2:
        st.markdown(f"""
        <div style="text-align: center;">
            <p style="font-size: 2rem; color: #4299e1; margin: 0;">{etat_robot['nb_actions']}</p>
            <p style="color: #718096;">⚡ Actions</p>
        </div>
        """, unsafe_allow_html=True)
    
    with sys_col3:
        direction_emoji = {"Nord": "⬆️", "Est": "➡️", "Sud": "⬇️", "Ouest": "⬅️"}.get(etat_robot['direction_text'], "🧭")
        st.markdown(f"""
        <div style="text-align: center;">
            <p style="font-size: 2rem; margin: 0;">{direction_emoji}</p>
            <p style="color: #718096;">{etat_robot['direction_text']}</p>
        </div>
        """, unsafe_allow_html=True)
    
    # État Pomodoro
    st.markdown("#### 🍅 Session Pomodoro")
    etat_pomo = agent.pomodoro.etat_session()
    
    if etat_pomo['active']:
        st.success(f"✅ Session active: {etat_pomo['matiere']}")
        st.info(f"⏱️ Temps restant: {etat_pomo['temps_restant']}")
        
        if st.button("⏹️ Arrêter la session", use_container_width=True):
            agent.pomodoro.arreter_session()
            st.rerun()
    else:
        st.info("Aucune session en cours")
        
        with st.form("pomodoro_form"):
            matiere = st.text_input("Matière", placeholder="Ex: Mathématiques")
            duree = st.slider("Durée (minutes)", 5, 60, 25)
            
            if st.form_submit_button("🚀 Démarrer session", use_container_width=True):
                if matiere:
                    agent.pomodoro.demarrer_session_travail(matiere, duree)
                    st.rerun()

# ========== COLONNE CAPTEURS IoT ==========
with col_sensors:
    st.markdown("### 📡 Capteurs IoT (Temps Réel)")
    
    # Récupérer météo (une fois toutes les 30 min)
    maintenant = datetime.now()
    if (st.session_state.meteo_data is None or 
        st.session_state.derniere_maj_meteo is None or
        (maintenant - st.session_state.derniere_maj_meteo).seconds > 1800):
        try:
            st.session_state.meteo_data = st.session_state.meteo_api.obtenir_meteo()
            st.session_state.derniere_maj_meteo = maintenant
        except:
            pass
    
    # Carte Météo RÉELLE
    if st.session_state.meteo_data:
        meteo = st.session_state.meteo_data
        st.markdown("---")
        st.markdown("### ⛅ Météo Rabat (Réelle)")
        
        meteo_temp = meteo['temperature']
        meteo_color = "#f56565" if meteo_temp > 30 else "#48bb78" if meteo_temp > 15 else "#4299e1"
        
        st.markdown(f"""
        <div class="sensor-card" style="border-left-color: #f59e0b;">
            <div class="sensor-value" style="color: {meteo_color};">{meteo_temp}°C</div>
            <div class="sensor-label">🌡️ {meteo['description']}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # Détails météo
        col_m1, col_m2 = st.columns(2)
        with col_m1:
            st.metric("💧 Humidité", f"{meteo['humidite']}%")
            st.metric("💨 Vent", f"{meteo['vent_kmh']} km/h")
        with col_m2:
            st.metric("🌡️ Ressenti", f"{meteo['ressenti']}°C")
            if meteo.get('precipitation_mm', 0) > 0:
                st.metric("🌧️ Pluie", f"{meteo['precipitation_mm']} mm")
        
        # Conseil météo
        conseil = st.session_state.meteo_api.obtenir_conseil_meteo(meteo)
        st.info(conseil)
    
    st.markdown("---")
    st.markdown("### 📊 Capteurs Virtuels")
    
    # Température
    temp = st.session_state.capteurs["temperature"]
    temp_color = "#f56565" if temp > 25 else "#48bb78" if temp > 18 else "#4299e1"
    st.markdown(f"""
    <div class="sensor-card">
        <div class="sensor-value" style="color: {temp_color};">{temp}°C</div>
        <div class="sensor-label">🌡️ Température (simulée)</div>
    </div>
    """, unsafe_allow_html=True)
    
    if temp > 26:
        st.warning("⚠️ Il fait chaud ! Pense à aérer.")
    elif temp < 18:
        st.info("❄️ Il fait frais, mets un pull !")
    
    # Humidité
    hum = st.session_state.capteurs["humidite"]
    st.markdown(f"""
    <div class="sensor-card">
        <div class="sensor-value" style="color: #4299e1;">{hum}%</div>
        <div class="sensor-label">💧 Humidité (simulée)</div>
    </div>
    """, unsafe_allow_html=True)
    
    if hum < 35:
        st.warning("⚠️ Air trop sec, hydrate-toi !")
    
    # Luminosité
    lum = st.session_state.capteurs["luminosite"]
    st.markdown(f"""
    <div class="sensor-card">
        <div class="sensor-value" style="color: #ecc94b;">{lum} lux</div>
        <div class="sensor-label">💡 Luminosité (simulée)</div>
    </div>
    """, unsafe_allow_html=True)
    
    if lum < 300:
        st.info("🌙 Il fait sombre, allume la lumière !")
    
    # Niveau sonore
    bruit = st.session_state.capteurs["bruit"]
    bruit_color = "#f56565" if bruit > 60 else "#48bb78"
    st.markdown(f"""
    <div class="sensor-card">
        <div class="sensor-value" style="color: {bruit_color};">{bruit} dB</div>
        <div class="sensor-label">🔊 Niveau sonore</div>
    </div>
    """, unsafe_allow_html=True)
    
    if bruit > 65:
        st.warning("⚠️ Environnement bruyant, mets des écouteurs !")

# ========== ZONE DE CHAT ==========
st.markdown("---")
st.markdown("### 💬 Conversation avec RoboCompagnon")

# Afficher l'historique
chat_container = st.container()

with chat_container:
    if not st.session_state.historique_chat:
        st.info("👋 Salut ! Je suis RoboCompagnon. Tape un message pour commencer !")
    
    for msg in st.session_state.historique_chat:
        if msg['role'] == 'user':
            st.markdown(f'<div class="chat-message user-message">👤 <strong>Toi:</strong> {msg["message"]}</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="chat-message robot-message">🤖 <strong>RoboCompagnon:</strong> {msg["message"]}</div>', unsafe_allow_html=True)

# Input utilisateur
with st.form(key="chat_form", clear_on_submit=True):
    col_input, col_btn = st.columns([4, 1])
    
    with col_input:
        user_input = st.text_input("Message", placeholder="Ex: Lance une session Pomodoro de maths", label_visibility="collapsed")
    
    with col_btn:
        submit = st.form_submit_button("Envoyer 📤", use_container_width=True)

if submit and user_input:
    # Mettre à jour les données IoT dans l'agent
    agent.mettre_a_jour_capteurs(st.session_state.capteurs)
    if st.session_state.meteo_data:
        agent.mettre_a_jour_meteo(st.session_state.meteo_data)
    
    # Ajouter message utilisateur
    st.session_state.historique_chat.append({
        'role': 'user',
        'message': user_input
    })
    
    # Obtenir réponse du robot
    with st.spinner("🤖 RoboCompagnon réfléchit..."):
        reponse = agent.repondre(user_input)
    
    # Ajouter réponse robot
    st.session_state.historique_chat.append({
        'role': 'robot',
        'message': reponse
    })
    
    st.rerun()

# ========== SIDEBAR ==========
with st.sidebar:
    st.title("⚙️ Panneau de contrôle")
    
    # Rappels
    st.markdown("### 🔔 Rappels")
    rappels = agent.systeme_rappels.obtenir_prochains_rappels(3)
    
    if rappels:
        for r in rappels:
            priorite_color = {"haute": "🔴", "normale": "🔵", "basse": "⚪"}.get(r['priorite'], "🔵")
            st.info(f"{priorite_color} **{r['titre']}**\n\n📅 {r['date_heure']}\n⏳ {r['temps_restant']}")
    else:
        st.info("Aucun rappel")
    
    if st.button("➕ Nouveau rappel", use_container_width=True):
        st.info("Utilise le chat: 'Rappelle-moi de...'")
    
    st.markdown("---")
    
    # Stats Pomodoro
    st.markdown("### 📊 Stats Pomodoro")
    stats = agent.pomodoro.obtenir_statistiques()
    
    st.metric("Sessions aujourd'hui", stats.get('sessions_aujourd_hui', 0))
    st.metric("Total sessions", stats.get('total_sessions', 0))
    st.metric("Temps total", f"{stats.get('temps_total_heures', 0)}h")
    
    st.markdown("---")
    
    # Contrôles
    st.markdown("### 🎮 Contrôles")
    
    if st.button("🔄 Rafraîchir capteurs", use_container_width=True):
        simuler_capteurs()
        st.rerun()
    
    if st.button("🗑️ Effacer conversation", use_container_width=True):
        st.session_state.historique_chat = []
        st.rerun()
    
    if st.button("🔄 Réinitialiser robot", use_container_width=True):
        agent.robot.reset()
        st.success("Robot réinitialisé !")
        st.rerun()

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>🤖 RoboCompagnon v2.0 - Assistant IoT Intelligent | Monssef 2024-2025</p>", unsafe_allow_html=True)

# Auto-refresh toutes les 30 secondes pour les capteurs
time.sleep(0.1)
