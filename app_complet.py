# app_complet.py - Interface complète avec robot virtuel et IoT
import streamlit as st
import time
import random
from datetime import datetime
from agent import AgentRobot
from meteo import MeteoAPI
from tts import RobotVoix
from objets_connectes import MaisonConnectee
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
    st.session_state.robot_voix = RobotVoix(langue='fr')
    st.session_state.auto_play_voice = False  # Lecture automatique désactivée par défaut
    st.session_state.maison = MaisonConnectee()  # Objets connectés IoT

agent = st.session_state.agent

# Fonction pour mettre à jour les capteurs (simulation)
def simuler_capteurs():
    """Simule les variations des capteurs IoT de façon INTELLIGENTE"""
    
    # ========== TEMPÉRATURE INTELLIGENTE ==========
    # Basée sur plusieurs facteurs réels
    
    # 1. Base : Météo extérieure réelle
    if st.session_state.meteo_data:
        temp_exterieure = st.session_state.meteo_data['temperature']
        temp_base = temp_exterieure + 5  # Chauffage intérieur
    else:
        temp_base = 20  # Valeur par défaut si météo indisponible
    
    # 2. Ajustement selon l'heure (cycle journalier naturel)
    heure = datetime.now().hour
    if 6 <= heure < 9:
        temp_base += 0  # Matin frais
    elif 9 <= heure < 14:
        temp_base += 1  # Milieu de journée
    elif 14 <= heure < 18:
        temp_base += 2  # Pic de chaleur après-midi
    elif 18 <= heure < 22:
        temp_base += 1  # Soirée
    else:
        temp_base -= 1  # Nuit plus fraîche
    
    # 3. Impact de la luminosité (soleil chauffe la pièce)
    lum = st.session_state.capteurs.get("luminosite", 500)
    if lum > 800:
        temp_base += 2  # Soleil direct
    elif lum > 600:
        temp_base += 1  # Lumineux
    
    # 4. Impact de l'activité (session Pomodoro)
    etat_pomo = agent.pomodoro.etat_session()
    if etat_pomo.get('active', False):
        temp_base += 1  # Activité humaine génère chaleur
    
    # 5. Petite variation aléatoire pour réalisme
    temp_base += random.uniform(-0.3, 0.3)
    
    # Appliquer la température calculée
    st.session_state.capteurs["temperature"] = round(
        max(16, min(32, temp_base)), 1
    )
    
    # Stocker les facteurs pour explication
    if 'temp_facteurs' not in st.session_state:
        st.session_state.temp_facteurs = {}
    
    st.session_state.temp_facteurs = {
        'meteo_ext': st.session_state.meteo_data['temperature'] if st.session_state.meteo_data else None,
        'chauffage': 5,
        'heure_ajust': temp_base - (temp_exterieure + 5 if st.session_state.meteo_data else 20),
        'soleil': 2 if lum > 800 else (1 if lum > 600 else 0),
        'activite': 1 if etat_pomo.get('active', False) else 0
    }
    
    # ========== HUMIDITÉ (avec logique) ==========
    # Humidité liée à la météo extérieure
    if st.session_state.meteo_data:
        hum_ext = st.session_state.meteo_data.get('humidite', 50)
        hum_base = hum_ext - 10  # Intérieur généralement plus sec
    else:
        hum_base = st.session_state.capteurs.get("humidite", 45)
    
    # Variation légère
    hum_base += random.uniform(-2, 2)
    st.session_state.capteurs["humidite"] = int(
        max(30, min(70, hum_base))
    )
    
    # ========== LUMINOSITÉ (selon heure) ==========
    if 6 <= heure < 20:
        st.session_state.capteurs["luminosite"] = random.randint(500, 1000)
    else:
        st.session_state.capteurs["luminosite"] = random.randint(50, 200)
    
    # ========== BRUIT (plus élevé si Pomodoro actif) ==========
    if etat_pomo.get('active', False):
        # En session = plus de concentration = environnement plus calme
        bruit_base = random.randint(25, 45)
    else:
        bruit_base = random.randint(30, 60)
    
    st.session_state.capteurs["bruit"] = int(
        max(20, min(80, bruit_base))
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
        <div class="sensor-label">🌡️ Température Intelligente</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Afficher les facteurs de calcul
    if 'temp_facteurs' in st.session_state and st.session_state.temp_facteurs:
        facteurs = st.session_state.temp_facteurs
        with st.expander("💡 Comment est calculée cette température ?"):
            st.markdown("**🧠 Capteur Intelligent Multi-Facteurs :**")
            
            if facteurs.get('meteo_ext'):
                st.write(f"🌡️ Météo extérieure : **{facteurs['meteo_ext']}°C**")
                st.write(f"🏠 Chauffage intérieur : **+{facteurs['chauffage']}°C**")
            
            if facteurs.get('soleil', 0) > 0:
                st.write(f"☀️ Soleil par la fenêtre : **+{facteurs['soleil']}°C**")
            
            if facteurs.get('activite', 0) > 0:
                st.write(f"🍅 Activité (Pomodoro) : **+{facteurs['activite']}°C**")
            
            st.markdown("---")
            st.success(f"**Total calculé : {temp}°C**")
            st.caption("📡 Capteur basé sur données réelles + logique intelligente")
    
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
    
    # ========== OBJETS CONNECTÉS ==========
    st.markdown("---")
    st.markdown("### 🏠 Objets Connectés")
    
    # État de la lumière
    etat_lumiere = st.session_state.maison.lumiere.obtenir_etat()
    
    lumiere_color = "#48bb78" if etat_lumiere['etat'] else "#718096"
    lumiere_bg = "#f0fff4" if etat_lumiere['etat'] else "#f7fafc"
    
    st.markdown(f"""
    <div style="background: {lumiere_bg}; padding: 15px; border-radius: 10px; border-left: 4px solid {lumiere_color};">
        <div style="font-size: 1.2rem; font-weight: bold; margin-bottom: 8px;">
            💡 Lumière Chambre
        </div>
        <div style="font-size: 2rem; font-weight: bold; color: {lumiere_color};">
            {etat_lumiere['emoji']} {etat_lumiere['etat_texte']}
        </div>
        {f"<div style='font-size: 0.85rem; color: #718096; margin-top: 8px;'>Dernière action: {etat_lumiere['derniere_action']['heure']}</div>" if etat_lumiere['derniere_action'] else ""}
    </div>
    """, unsafe_allow_html=True)
    
    # Boutons de contrôle manuel
    col_on, col_off = st.columns(2)
    with col_on:
        if st.button("🟢 Allumer", use_container_width=True, disabled=etat_lumiere['etat']):
            resultat = st.session_state.maison.executer_commande("Allume la lumière")
            st.success(resultat['message'])
            st.rerun()
    
    with col_off:
        if st.button("🔴 Éteindre", use_container_width=True, disabled=not etat_lumiere['etat']):
            resultat = st.session_state.maison.executer_commande("Éteins la lumière")
            st.success(resultat['message'])
            st.rerun()
    
    # Lien vers circuit Arduino virtuel
    st.markdown("---")
    st.markdown("### 🔌 Circuit Arduino Virtuel")
    
    wokwi_url = "https://wokwi.com/projects/463124017608304641"
    
    st.markdown(f"""
    <div style="background: #f0f9ff; padding: 12px; border-radius: 8px; border-left: 4px solid #3b82f6;">
        <p style="margin: 0; font-size: 0.9rem;">
            💡 <strong>Voir la LED en action !</strong><br>
            Le circuit Arduino simule la lumière connectée.
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    if st.button("🔗 Ouvrir le circuit Wokwi", use_container_width=True, type="primary"):
        st.markdown(f'<meta http-equiv="refresh" content="0; url={wokwi_url}" target="_blank">', unsafe_allow_html=True)
        st.info("Circuit Wokwi ouvert dans un nouvel onglet !")
    
    st.caption("📌 Dans Wokwi, tape 'ON' ou 'OFF' dans le Serial Monitor pour contrôler la LED")

# ========== ZONE DE CHAT ==========
st.markdown("---")
st.markdown("### 💬 Conversation avec RoboCompagnon")

# Afficher l'historique
chat_container = st.container()

with chat_container:
    if not st.session_state.historique_chat:
        st.info("👋 Salut ! Je suis RoboCompagnon. Tape un message pour commencer !")
    
    for idx, msg in enumerate(st.session_state.historique_chat):
        if msg['role'] == 'user':
            st.markdown(f'<div class="chat-message user-message">👤 <strong>Toi:</strong> {msg["message"]}</div>', unsafe_allow_html=True)
        else:
            # Message du robot
            st.markdown(f'<div class="chat-message robot-message">🤖 <strong>RoboCompagnon:</strong> {msg["message"]}</div>', unsafe_allow_html=True)
            
            # Bouton pour écouter la réponse
            col_audio1, col_audio2 = st.columns([1, 10])
            with col_audio1:
                if st.button(f"🔊", key=f"speak_{idx}", help="Écouter la réponse"):
                    # Générer l'audio
                    audio_file = st.session_state.robot_voix.parler(msg["message"])
                    if audio_file:
                        st.audio(audio_file, format='audio/mp3', autoplay=True)

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
    agent.mettre_a_jour_maison(st.session_state.maison)
    
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
    
    # Option voix
    st.session_state.auto_play_voice = st.checkbox(
        "🔊 Lecture vocale auto",
        value=st.session_state.auto_play_voice,
        help="Le robot parle automatiquement ses réponses"
    )
    
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
