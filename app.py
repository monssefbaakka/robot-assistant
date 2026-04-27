# app.py - Interface web Streamlit pour le robot assistant
import streamlit as st
from agent import AgentRobot
import time

# Configuration de la page
st.set_page_config(
    page_title="RoboCompagnon - Assistant IA",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS personnalisé
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .stat-box {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 1rem;
        border-radius: 10px;
        color: white;
        text-align: center;
    }
    .stat-value {
        font-size: 2rem;
        font-weight: bold;
    }
    .stat-label {
        font-size: 0.9rem;
        opacity: 0.9;
    }
    .robot-status {
        background: #f0f2f6;
        padding: 1rem;
        border-radius: 10px;
        border-left: 4px solid #1f77b4;
    }
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

# Initialiser l'agent dans session_state
if 'agent' not in st.session_state:
    st.session_state.agent = AgentRobot(nom_utilisateur="Monssef")
    st.session_state.historique_chat = []

agent = st.session_state.agent

# En-tête
st.markdown('<p class="main-header">🤖 RoboCompagnon - Ton Assistant Personnel</p>', unsafe_allow_html=True)

# Layout en colonnes
col1, col2 = st.columns([2, 3])

# ========== COLONNE 1: État du robot ==========
with col1:
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
        <div class="stat-box" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);">
            <div class="stat-value">{etat['nb_actions']}</div>
            <div class="stat-label">⚡ Actions</div>
        </div>
        """, unsafe_allow_html=True)
    
    with stat_col3:
        direction_emoji = "⬆️" if etat['direction'] < 45 else "➡️" if etat['direction'] < 135 else "⬇️" if etat['direction'] < 225 else "⬅️"
        st.markdown(f"""
        <div class="stat-box" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);">
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
        
        for msg in st.session_state.historique_chat:
            if msg['role'] == 'user':
                st.markdown(f'<div class="chat-message user-message">👤 <strong>Toi:</strong> {msg["message"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(f'<div class="chat-message robot-message">🤖 <strong>RoboCompagnon:</strong> {msg["message"]}</div>', unsafe_allow_html=True)
    
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
