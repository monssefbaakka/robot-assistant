# app.py - Interface web Streamlit pour le robot assistant
import streamlit as st
import streamlit.components.v1 as components
from agent import AgentRobot
import time


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

# Configuration de la page
st.set_page_config(
    page_title="RoboCompagnon - Assistant IA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé pour un look moderne et minimaliste
st.markdown("""
<style>
    .stApp {
        background-color: #fafafa;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }
    .main-header {
        font-size: 2.2rem;
        font-weight: 700;
        color: #111827;
        text-align: left;
        margin-bottom: 2rem;
        letter-spacing: -0.02em;
        border-bottom: 1px solid #e5e7eb;
        padding-bottom: 1rem;
    }
    .stat-box {
        background: #ffffff;
        border: 1px solid #e5e7eb;
        padding: 1.5rem;
        border-radius: 12px;
        color: #1f2937;
        text-align: center;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .stat-box:hover {
        transform: translateY(-2px);
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
    }
    .stat-value {
        font-size: 1.8rem;
        font-weight: 700;
        color: #111827;
        margin-bottom: 0.25rem;
    }
    .stat-label {
        font-size: 0.85rem;
        font-weight: 500;
        color: #6b7280;
        text-transform: uppercase;
        letter-spacing: 0.05em;
    }
    .robot-status {
        background: #ffffff;
        padding: 1.5rem;
        border-radius: 12px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 1px 3px rgba(0,0,0,0.05);
    }
    .robot-status h4 {
        margin-top: 0;
        color: #111827;
        font-weight: 600;
        margin-bottom: 1rem;
    }
    .robot-status p {
        color: #4b5563;
        margin-bottom: 0.5rem;
        font-size: 0.95rem;
    }
    
    /* Modern Chat UI */
    .chat-container-custom {
        display: flex;
        flex-direction: column;
        gap: 1rem;
        padding: 1rem 0;
    }
    .chat-message {
        padding: 0.85rem 1.25rem;
        border-radius: 18px;
        max-width: 85%;
        font-size: 0.95rem;
        line-height: 1.5;
        box-shadow: 0 1px 2px rgba(0,0,0,0.05);
        word-wrap: break-word;
    }
    .user-message-wrapper {
        display: flex;
        justify-content: flex-end;
        width: 100%;
        margin-bottom: 0.5rem;
    }
    .robot-message-wrapper {
        display: flex;
        justify-content: flex-start;
        width: 100%;
        margin-bottom: 0.5rem;
    }
    .user-message {
        background: #111827;
        color: #ffffff;
        border-bottom-right-radius: 4px;
    }
    .robot-message {
        background: #ffffff;
        color: #1f2937;
        border: 1px solid #e5e7eb;
        border-bottom-left-radius: 4px;
    }
    
    div[data-testid="stToolbar"] { visibility: hidden; }
    footer { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# Initialiser l'agent dans session_state
if 'agent' not in st.session_state:
    st.session_state.agent = AgentRobot(nom_utilisateur="Monssef")
    st.session_state.historique_chat = []
if 'robot_state' not in st.session_state:
    st.session_state.robot_state = 'idle'

agent = st.session_state.agent

# Capture current state for this render, then reset so next render is idle
current_robot_state = st.session_state.robot_state
if current_robot_state == 'speaking':
    st.session_state.robot_state = 'idle'

# En-tête
st.markdown('<p class="main-header">🤖 RoboCompagnon - Ton Assistant Personnel</p>', unsafe_allow_html=True)

# Layout en colonnes
col1, col2 = st.columns([2, 3])

# ========== COLONNE 1: État du robot ==========
with col1:
    components.html(get_robot_html(current_robot_state), height=360)
    st.subheader("📊 État du Robot")
    
    # Récupérer l'état actuel
    etat = agent.robot.etat()
    
    # Statistiques en grille
    stat_col1, stat_col2, stat_col3 = st.columns(3)
    
    with stat_col1:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-value">{etat['batterie']:.0f}%</div>
            <div class="stat-label">🔋 Batterie</div>
        </div>
        """, unsafe_allow_html=True)
    
    with stat_col2:
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-value">{etat['nb_actions']}</div>
            <div class="stat-label">⚡ Actions</div>
        </div>
        """, unsafe_allow_html=True)
    
    with stat_col3:
        direction_emoji = "⬆️" if etat['direction'] < 45 else "➡️" if etat['direction'] < 135 else "⬇️" if etat['direction'] < 225 else "⬅️"
        st.markdown(f"""
        <div class="stat-box">
            <div class="stat-value">{direction_emoji}</div>
            <div class="stat-label">🧭 {etat['direction_text']}</div>
        </div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Détails position
    st.markdown(f"""
    <div class="robot-status">
        <h4>📍 Position</h4>
        <p><strong>X:</strong> {etat['position']['x']:.1f} cm</p>
        <p><strong>Y:</strong> {etat['position']['y']:.1f} cm</p>
        <p><strong>Direction:</strong> {etat['direction']}° ({etat['direction_text']})</p>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Contrôles manuels
    st.subheader("🎮 Contrôles Manuels")
    
    ctrl_col1, ctrl_col2, ctrl_col3 = st.columns(3)
    
    with ctrl_col1:
        if st.button("⬆️ Avancer", use_container_width=True):
            result = agent.robot.avancer(20)
            st.success(result)
            st.rerun()
    
    with ctrl_col2:
        if st.button("↩️ Gauche", use_container_width=True):
            result = agent.robot.tourner_gauche(45)
            st.success(result)
            st.rerun()
    
    with ctrl_col3:
        if st.button("↪️ Droite", use_container_width=True):
            result = agent.robot.tourner_droite(45)
            st.success(result)
            st.rerun()
    
    ctrl_col4, ctrl_col5 = st.columns(2)
    
    with ctrl_col4:
        if st.button("⬇️ Reculer", use_container_width=True):
            result = agent.robot.reculer(20)
            st.success(result)
            st.rerun()
    
    with ctrl_col5:
        if st.button("🔍 Scanner", use_container_width=True):
            msg, distances = agent.robot.scanner()
            st.info(msg)
            st.rerun()
    
    if st.button("🔋 Recharger Batterie", use_container_width=True, type="primary"):
        result = agent.robot.recharger()
        st.success(result)
        st.rerun()
    
    # Visualisation simple de la position
    st.markdown("---")
    st.subheader("🗺️ Carte Simple")
    
    # Créer une grille simple
    import numpy as np
    grid = np.zeros((10, 10))
    
    # Convertir position en coordonnées grille
    x_grid = int(5 + etat['position']['x'] / 20)
    y_grid = int(5 - etat['position']['y'] / 20)
    
    # Limiter aux bornes
    x_grid = max(0, min(9, x_grid))
    y_grid = max(0, min(9, y_grid))
    
    grid[y_grid, x_grid] = 1
    
    st.text("🤖 = Position actuelle")
    st.dataframe(grid, use_container_width=True, hide_index=True)

# ========== COLONNE 2: Chat ==========
with col2:
    st.subheader("💬 Conversation avec RoboCompagnon")
    
    # Zone de chat
    chat_container = st.container(height=400)
    
    with chat_container:
        if not st.session_state.historique_chat:
            st.info("👋 Salut Monssef ! Je suis RoboCompagnon. Pose-moi une question ou demande-moi de bouger !")
        
        st.markdown('<div class="chat-container-custom">', unsafe_allow_html=True)
        for msg in st.session_state.historique_chat:
            if msg['role'] == 'user':
                st.markdown(f'<div class="user-message-wrapper"><div class="chat-message user-message">{msg["message"]}</div></div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="robot-message-wrapper"><div class="chat-message robot-message">🤖 <strong>RoboCompagnon:</strong> {msg["message"]}</div></div>', unsafe_allow_html=True)
        st.markdown('</div>', unsafe_allow_html=True)
    
    # Input utilisateur
    with st.form(key="chat_form", clear_on_submit=True):
        user_input = st.text_input("Tape ton message ici...", key="user_input", placeholder="Ex: Avance de 50cm puis tourne à droite")
        submit = st.form_submit_button("Envoyer 📤", use_container_width=True)
    
    if submit and user_input:
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
        st.session_state.robot_state = 'speaking'

        st.rerun()
    
    # Bouton pour effacer l'historique
    if st.button("🗑️ Effacer la conversation"):
        st.session_state.historique_chat = []
        st.rerun()

# ========== SIDEBAR: Paramètres ==========
with st.sidebar:
    st.title("⚙️ Paramètres")
    
    st.markdown("### 🤖 Robot Assistant")
    st.info(f"**Nom:** RoboCompagnon\n\n**Utilisateur:** {agent.nom_utilisateur}\n\n**Modèle IA:** Llama 3.2")
    
    st.markdown("---")
    
    st.markdown("### 📚 Guide Rapide")
    st.markdown("""
    **Commandes disponibles:**
    - "Avance de 50cm"
    - "Tourne à droite"
    - "Scanne autour"
    - "Quel est ton état ?"
    - "Recharge ta batterie"
    
    **Conversation:**
    - Pose des questions
    - Demande de l'aide
    - Discute naturellement
    """)
    
    st.markdown("---")
    
    if st.button("🔄 Réinitialiser le Robot"):
        agent.robot.reset()
        st.session_state.historique_chat = []
        st.success("Robot réinitialisé !")
        st.rerun()

# Footer
st.markdown("---")
st.markdown("<p style='text-align: center; color: gray;'>🤖 RoboCompagnon - Projet IoT Assistant Robotique | Monssef</p>", unsafe_allow_html=True)
