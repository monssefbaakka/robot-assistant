# agent.py - Agent IA conversationnel pour le robot assistant
from langchain_community.llms import Ollama
from robot import RobotVirtuel
from rappels import SystemeRappels
from pomodoro import SessionPomodoro
from meteo import MeteoAPI
from datetime import datetime, timedelta
import re

class AgentRobot:
    """Agent IA qui contrôle le robot et interagit avec l'utilisateur"""
    
    def __init__(self, nom_utilisateur="Monssef"):
        # Initialiser le modèle LLM
        self.llm = Ollama(model="llama3.2", temperature=0.7)
        
        # Robot virtuel
        self.robot = RobotVirtuel()
        
        # Système de rappels
        self.systeme_rappels = SystemeRappels()
        
        # Système Pomodoro
        self.pomodoro = SessionPomodoro()
        
        # API Météo
        self.meteo_api = MeteoAPI(ville="Rabat", pays="MA")
        
        # Données IoT (sera mis à jour par l'interface)
        self.capteurs_data = None
        self.meteo_data = None
        self.maison_connectee = None  # Objets connectés
        
        # Informations contextuelles
        self.nom_utilisateur = nom_utilisateur
        self.historique_conversation = []
        self.contexte = {
            "heure_demarrage": datetime.now().strftime("%H:%M"),
            "date": datetime.now().strftime("%d/%m/%Y"),
            "humeur_utilisateur": "neutre",
            "tache_en_cours": None
        }
        
        # Template de prompt système
        self.prompt_systeme = """Tu es un robot assistant domestique sympathique et serviable nommé "RoboCompagnon".
Tu accompagnes {nom_utilisateur} dans sa vie quotidienne.

Contexte actuel:
- Date: {date}
- Heure de démarrage: {heure}
- Humeur perçue: {humeur}
- Tâche en cours: {tache}

Capacités du robot:
- Se déplacer (avancer, reculer, tourner)
- Scanner l'environnement
- Gérer un système de batterie
- Converser et aider l'utilisateur
- Créer et gérer des rappels intelligents
- Te rappeler tes examens, devoirs et tâches
- Gérer des sessions d'étude Pomodoro (25 min de travail + pauses)
- Suivre ta productivité et te motiver

Historique récent:
{historique}

Règles importantes:
1. Sois naturel, amical et encourageant
2. Tutoie l'utilisateur
3. Adapte-toi à son humeur
4. Si on te demande de bouger, confirme l'action
5. Si on te demande un rappel, confirme sa création
6. Si on te demande une session Pomodoro, encourage et motive
7. Sois concis (2-3 phrases max sauf si demande détaillée)
8. N'invente pas de capacités que tu n'as pas

Message de {nom_utilisateur}: {message}

Réponse (naturelle et amicale):"""
    
    def detecter_commande_robot(self, message):
        """Détecte si le message contient une commande pour le robot"""
        message_lower = message.lower()
        
        commandes = {
            "avancer": ["avance", "va devant", "bouge en avant", "forward"],
            "reculer": ["recule", "va derrière", "arrière", "back"],
            "tourner_droite": ["tourne à droite", "droite", "right", "pivote droite"],
            "tourner_gauche": ["tourne à gauche", "gauche", "left", "pivote gauche"],
            "scanner": ["scan", "regarde autour", "check", "observe"],
            "etat": ["état", "status", "comment tu vas", "batterie", "position"],
            "recharger": ["recharge", "charge", "batterie faible"]
        }
        
        for action, mots_cles in commandes.items():
            if any(mot in message_lower for mot in mots_cles):
                return action
        
        return None
    
    def detecter_demande_rappel(self, message):
        """Détecte si le message demande de créer un rappel"""
        message_lower = message.lower()
        
        # Mots-clés pour détecter une demande de rappel
        mots_rappel = [
            "rappelle", "rappel", "n'oublie pas", "noublie pas",
            "crée un rappel", "ajoute un rappel", "enregistre un rappel",
            "j'ai un examen", "j'ai un devoir", "deadline"
        ]
        
        return any(mot in message_lower for mot in mots_rappel)
    
    def detecter_demande_pomodoro(self, message):
        """Détecte si le message demande une session Pomodoro"""
        message_lower = message.lower()
        
        # Mots-clés pour détecter une demande Pomodoro
        mots_pomodoro = [
            "pomodoro", "session", "session de travail", "session d'étude",
            "lance une session", "démarre une session", "commence une session",
            "travaille", "étudier", "réviser", "bosser"
        ]
        
        # Détecter les demandes d'arrêt
        if any(mot in message_lower for mot in ["arrête", "stop", "termine", "pause la session"]):
            return "arreter"
        
        # Détecter les demandes d'état
        if any(mot in message_lower for mot in ["combien de sessions", "sessions aujourd'hui", "mes sessions", "statistiques pomodoro"]):
            return "stats"
        
        # Détecter les demandes de démarrage
        if any(mot in message_lower for mot in mots_pomodoro):
            return "demarrer"
        
        return None
    
    def extraire_info_rappel(self, message):
        """Extrait les informations du rappel depuis le message"""
        message_lower = message.lower()
        
        # Extraire le titre (ce qu'il faut rappeler)
        titre = None
        
        # Patterns pour extraire le titre
        patterns_titre = [
            r"rappelle(?:-moi)? (?:de |d')?(.+?)(?:demain|aujourd'hui|le|à|\d|$)",
            r"n'?oublie pas (?:de |d')?(.+?)(?:demain|aujourd'hui|le|à|\d|$)",
            r"(?:créer|ajouter) un rappel[: ]+(.+?)(?:demain|aujourd'hui|le|pour|à|\d|$)",
            r"j'ai un (?:examen|devoir) (?:de |d')?(.+?)(?:demain|le|à|\d|$)"
        ]
        
        for pattern in patterns_titre:
            match = re.search(pattern, message_lower)
            if match:
                titre = match.group(1).strip()
                break
        
        if not titre:
            # Par défaut, prendre tout après "rappelle-moi"
            if "rappelle" in message_lower:
                titre = message_lower.split("rappelle")[-1].strip()
                titre = re.sub(r'^(-moi|moi) (de |d\')?', '', titre).strip()
        
        # Détecter le moment (demain, aujourd'hui, date spécifique)
        maintenant = datetime.now()
        date_rappel = None
        heure_rappel = "09:00"  # Heure par défaut
        
        # Demain
        if "demain" in message_lower:
            date_rappel = maintenant + timedelta(days=1)
        
        # Aujourd'hui
        elif "aujourd'hui" in message_lower or "ce soir" in message_lower:
            date_rappel = maintenant
            if "soir" in message_lower:
                heure_rappel = "18:00"
        
        # Dans X jours
        match_jours = re.search(r"dans (\d+) jours?", message_lower)
        if match_jours:
            jours = int(match_jours.group(1))
            date_rappel = maintenant + timedelta(days=jours)
        
        # Date spécifique (ex: "le 5 mai", "le 15/05")
        match_date1 = re.search(r"le (\d+) (janvier|février|mars|avril|mai|juin|juillet|août|septembre|octobre|novembre|décembre)", message_lower)
        match_date2 = re.search(r"le (\d+)/(\d+)", message_lower)
        
        if match_date1:
            jour = int(match_date1.group(1))
            mois_text = match_date1.group(2)
            mois_map = {
                "janvier": 1, "février": 2, "mars": 3, "avril": 4,
                "mai": 5, "juin": 6, "juillet": 7, "août": 8,
                "septembre": 9, "octobre": 10, "novembre": 11, "décembre": 12
            }
            mois = mois_map.get(mois_text, maintenant.month)
            annee = maintenant.year
            if mois < maintenant.month:
                annee += 1
            date_rappel = datetime(annee, mois, jour)
        
        elif match_date2:
            jour = int(match_date2.group(1))
            mois = int(match_date2.group(2))
            annee = maintenant.year
            if mois < maintenant.month:
                annee += 1
            date_rappel = datetime(annee, mois, jour)
        
        # Extraire l'heure (ex: "à 15h", "à 10h30")
        match_heure = re.search(r"à (\d+)h?(\d+)?", message_lower)
        if match_heure:
            heure = int(match_heure.group(1))
            minute = int(match_heure.group(2)) if match_heure.group(2) else 0
            heure_rappel = f"{heure:02d}:{minute:02d}"
        
        # Si aucune date détectée, mettre demain par défaut
        if not date_rappel:
            date_rappel = maintenant + timedelta(days=1)
        
        # Combiner date et heure
        date_heure_str = f"{date_rappel.strftime('%Y-%m-%d')} {heure_rappel}"
        
        # Détecter la priorité
        priorite = "normale"
        if any(word in message_lower for word in ["important", "urgent", "critique", "examen"]):
            priorite = "haute"
        
        return {
            "titre": titre or "Rappel",
            "date_heure": date_heure_str,
            "priorite": priorite,
            "description": message[:100]  # Garder le message original comme description
        }
    
    def executer_commande_robot(self, commande):
        """Exécute une commande sur le robot"""
        resultats = []
        
        if commande == "avancer":
            resultats.append(self.robot.avancer(30))
        elif commande == "reculer":
            resultats.append(self.robot.reculer(30))
        elif commande == "tourner_droite":
            resultats.append(self.robot.tourner_droite(90))
        elif commande == "tourner_gauche":
            resultats.append(self.robot.tourner_gauche(90))
        elif commande == "scanner":
            msg, distances = self.robot.scanner()
            resultats.append(msg)
        elif commande == "etat":
            etat = self.robot.etat()
            resultats.append(f"Position: ({etat['position']['x']:.1f}, {etat['position']['y']:.1f})")
            resultats.append(f"Direction: {etat['direction_text']}")
            resultats.append(f"Batterie: {etat['batterie']:.0f}%")
        elif commande == "recharger":
            resultats.append(self.robot.recharger())
        
        return "\n".join(resultats)
    
    def gerer_demande_rappel(self, message):
        """Gère une demande de rappel"""
        message_lower = message.lower()
        
        # Si c'est une demande de liste des rappels
        if any(word in message_lower for word in ["quels rappels", "mes rappels", "liste", "voir mes rappels"]):
            rappels = self.systeme_rappels.obtenir_prochains_rappels(5)
            if not rappels:
                return "Tu n'as aucun rappel enregistré pour le moment."
            
            resultat = "Voici tes prochains rappels:\n"
            for i, r in enumerate(rappels, 1):
                resultat += f"\n{i}. {r['titre']}"
                resultat += f"\n   📅 {r['date_heure']}"
                resultat += f"\n   ⏳ Dans {r['temps_restant']}"
            
            return resultat
        
        # Sinon, créer un nouveau rappel
        info = self.extraire_info_rappel(message)
        
        rappel = self.systeme_rappels.ajouter_rappel(
            titre=info['titre'],
            description=info['description'],
            date_heure=info['date_heure'],
            priorite=info['priorite']
        )
        
        # Formater la confirmation
        date_obj = datetime.strptime(info['date_heure'], "%Y-%m-%d %H:%M")
        date_fr = date_obj.strftime("%d/%m à %Hh%M")
        
        resultat = f"✅ Rappel créé avec succès!\n\n"
        resultat += f"📌 {info['titre']}\n"
        resultat += f"📅 {date_fr}\n"
        
        if info['priorite'] == "haute":
            resultat += "⚠️ Priorité haute"
        
        return resultat
    
    def gerer_demande_pomodoro(self, message, type_demande):
        """Gère une demande liée au Pomodoro"""
        
        # Arrêter une session en cours
        if type_demande == "arreter":
            etat = self.pomodoro.etat_session()
            if not etat['active']:
                return "❌ Aucune session Pomodoro en cours."
            
            resultat = self.pomodoro.arreter_session()
            return resultat
        
        # Afficher les statistiques
        elif type_demande == "stats":
            stats = self.pomodoro.obtenir_statistiques()
            sessions_aujourdhui = self.pomodoro.obtenir_sessions_aujourdhui()
            
            resultat = "📊 TES STATISTIQUES POMODORO\n\n"
            resultat += f"Aujourd'hui: {len(sessions_aujourdhui)} sessions\n"
            resultat += f"Total: {stats.get('total_sessions', 0)} sessions\n"
            resultat += f"Temps d'étude: {stats.get('temps_total_heures', 0)}h\n"
            
            if sessions_aujourdhui:
                resultat += "\n📚 Sessions d'aujourd'hui:\n"
                for s in sessions_aujourdhui:
                    resultat += f"• {s['matiere']} ({s['duree_minutes']}min) à {s['heure_debut']}\n"
            
            return resultat
        
        # Démarrer une nouvelle session
        elif type_demande == "demarrer":
            # Vérifier si une session est déjà active
            etat = self.pomodoro.etat_session()
            if etat['active']:
                return f"⚠️ Une session est déjà en cours ! ({etat['matiere']}, {etat['temps_restant']} restant)"
            
            # Extraire la matière du message
            matiere = self._extraire_matiere(message)
            
            # Extraire la durée si spécifiée
            duree = self._extraire_duree_pomodoro(message)
            
            # Démarrer la session
            resultat = self.pomodoro.demarrer_session_travail(
                matiere=matiere,
                duree=duree
            )
            
            return resultat
        
        return "Je n'ai pas compris ta demande concernant le Pomodoro."
    
    def _extraire_matiere(self, message):
        """Extrait la matière d'étude depuis le message"""
        message_lower = message.lower()
        
        # Patterns pour extraire la matière
        patterns = [
            r"session (?:de |d')?(.+?)(?:\s|$)",
            r"(?:travail|étude|révision) (?:de |d')?(.+?)(?:\s|$)",
            r"pomodoro (?:de |d')?(.+?)(?:\s|$)",
            r"(?:en |sur |pour) (.+?)(?:\s|$)"
        ]
        
        for pattern in patterns:
            match = re.search(pattern, message_lower)
            if match:
                matiere = match.group(1).strip()
                # Nettoyer
                matiere = re.sub(r'\s+(de|pour|sur|en)\s+.*', '', matiere)
                if len(matiere) > 2:  # Éviter les extractions trop courtes
                    return matiere.capitalize()
        
        return "Étude générale"
    
    def _extraire_duree_pomodoro(self, message):
        """Extrait la durée de la session si spécifiée"""
        # Chercher des patterns comme "30 minutes", "45 min", etc.
        match = re.search(r'(\d+)\s*(?:min|minutes)', message.lower())
        if match:
            duree = int(match.group(1))
            if 5 <= duree <= 120:  # Limiter entre 5 et 120 minutes
                return duree
        
        return None  # Utiliser la durée par défaut (25 min)
    
    def mettre_a_jour_maison(self, maison_connectee):
        """Met à jour la référence à la maison connectée"""
        self.maison_connectee = maison_connectee
    
    def detecter_commande_maison(self, message):
        """Détecte si le message est une commande pour objets connectés"""
        message_lower = message.lower()
        
        # Mots-clés pour lumière
        mots_lumiere = ['lumière', 'lumiere', 'lampe', 'éclairage', 'eclairage']
        
        if any(mot in message_lower for mot in mots_lumiere):
            # Vérifier action
            if any(mot in message_lower for mot in ['allume', 'ouvre', 'active']):
                return 'lumiere_on'
            elif any(mot in message_lower for mot in ['éteins', 'eteins', 'ferme', 'désactive', 'desactive']):
                return 'lumiere_off'
        
        return None
    
    def gerer_commande_maison(self, type_commande):
        """Gère les commandes pour objets connectés"""
        if not self.maison_connectee:
            return "Les objets connectés ne sont pas disponibles."
        
        if type_commande == 'lumiere_on':
            resultat = self.maison_connectee.executer_commande("Allume la lumière")
            return resultat['reponse_vocale']
        elif type_commande == 'lumiere_off':
            resultat = self.maison_connectee.executer_commande("Éteins la lumière")
            return resultat['reponse_vocale']
        
        return "Commande non reconnue"
    
    def mettre_a_jour_capteurs(self, capteurs_data):
        """Met à jour les données des capteurs IoT"""
        self.capteurs_data = capteurs_data
    
    def mettre_a_jour_meteo(self, meteo_data):
        """Met à jour les données météo"""
        self.meteo_data = meteo_data
    
    def detecter_question_iot(self, message):
        """Détecte si le message demande des infos sur les capteurs ou la météo"""
        message_lower = message.lower()
        
        # Questions météo
        mots_meteo = [
            "météo", "meteo", "temps qu'il fait", "il pleut", 
            "température extérieure", "dehors", "température exterieure",
            "quel temps", "temps demain", "prévi", "previ"
        ]
        
        if any(mot in message_lower for mot in mots_meteo):
            return "meteo"
        
        # Questions capteurs
        mots_capteurs = [
            "température", "temperature", "quelle température", 
            "il fait chaud", "il fait froid",
            "humidité", "humidite", "taux d'humidité",
            "luminosité", "lumino", "il fait sombre", "éclairage",
            "bruit", "niveau sonore", "c'est bruyant"
        ]
        
        if any(mot in message_lower for mot in mots_capteurs):
            return "capteurs"
        
        return None
    
    def gerer_question_meteo(self):
        """Répond aux questions sur la météo"""
        if not self.meteo_data:
            # Récupérer la météo si pas encore chargée
            try:
                self.meteo_data = self.meteo_api.obtenir_meteo()
            except:
                return "Désolé, je n'arrive pas à récupérer la météo pour le moment."
        
        meteo = self.meteo_data
        
        reponse = f"📍 Météo à {meteo['ville']}:\n\n"
        reponse += f"🌡️ Température: {meteo['temperature']}°C (ressenti {meteo['ressenti']}°C)\n"
        reponse += f"☁️ {meteo['description']}\n"
        reponse += f"💧 Humidité: {meteo['humidite']}%\n"
        reponse += f"💨 Vent: {meteo['vent_kmh']} km/h\n"
        
        if meteo.get('precipitation_mm', 0) > 0:
            reponse += f"🌧️ Précipitations: {meteo['precipitation_mm']} mm\n"
        
        # Ajouter conseil
        conseil = self.meteo_api.obtenir_conseil_meteo(meteo)
        reponse += f"\n💡 {conseil}"
        
        return reponse
    
    def gerer_question_capteurs(self):
        """Répond aux questions sur les capteurs IoT"""
        if not self.capteurs_data:
            return "Les capteurs ne sont pas encore initialisés."
        
        capteurs = self.capteurs_data
        
        reponse = "📊 État des capteurs:\n\n"
        
        # Température
        temp = capteurs.get('temperature', 0)
        reponse += f"🌡️ Température intérieure: {temp}°C\n"
        if temp > 26:
            reponse += "   ⚠️ Il fait chaud, aère ta chambre !\n"
        elif temp < 18:
            reponse += "   ⚠️ Il fait frais, mets le chauffage !\n"
        else:
            reponse += "   ✅ Température confortable\n"
        
        # Humidité
        hum = capteurs.get('humidite', 0)
        reponse += f"\n💧 Humidité: {hum}%\n"
        if hum < 35:
            reponse += "   ⚠️ Air sec, hydrate-toi !\n"
        elif hum > 70:
            reponse += "   ⚠️ Air humide, aère un peu\n"
        else:
            reponse += "   ✅ Humidité normale\n"
        
        # Luminosité
        lum = capteurs.get('luminosite', 0)
        reponse += f"\n💡 Luminosité: {lum} lux\n"
        if lum < 300:
            reponse += "   ⚠️ Il fait sombre, allume la lumière !\n"
        else:
            reponse += "   ✅ Éclairage suffisant\n"
        
        # Bruit
        bruit = capteurs.get('bruit', 0)
        reponse += f"\n🔊 Niveau sonore: {bruit} dB\n"
        if bruit > 65:
            reponse += "   ⚠️ Trop bruyant ! Mets des écouteurs\n"
        else:
            reponse += "   ✅ Environnement calme\n"
        
        # Comparaison avec météo extérieure si disponible
        if self.meteo_data:
            temp_ext = self.meteo_data['temperature']
            reponse += f"\n🌡️ Extérieur: {temp_ext}°C"
            diff = temp - temp_ext
            if abs(diff) > 3:
                if diff > 0:
                    reponse += f" ({abs(diff):.1f}°C plus chaud à l'intérieur)"
                else:
                    reponse += f" ({abs(diff):.1f}°C plus froid à l'intérieur)"
        
        return reponse
    
    def formater_historique(self):
        """Formate les derniers messages pour le contexte"""
        if not self.historique_conversation:
            return "Aucun historique"
        
        # Garder seulement les 3 derniers échanges
        recent = self.historique_conversation[-6:]  # 3 user + 3 assistant
        lignes = []
        for entry in recent:
            role = "Utilisateur" if entry["role"] == "user" else "Robot"
            lignes.append(f"{role}: {entry['message']}")
        
        return "\n".join(lignes)
    
    def construire_prompt(self, message_utilisateur):
        """Construit le prompt complet"""
        return self.prompt_systeme.format(
            nom_utilisateur=self.nom_utilisateur,
            date=self.contexte["date"],
            heure=self.contexte["heure_demarrage"],
            humeur=self.contexte["humeur_utilisateur"],
            tache=self.contexte["tache_en_cours"] or "Aucune",
            historique=self.formater_historique(),
            message=message_utilisateur
        )
    
    def repondre(self, message_utilisateur):
        """Génère une réponse à partir du message de l'utilisateur"""
        
        # Détecter si c'est une commande objets connectés
        commande_maison = self.detecter_commande_maison(message_utilisateur)
        if commande_maison:
            return self.gerer_commande_maison(commande_maison)
        
        # Détecter si c'est une question IoT (météo ou capteurs)
        type_iot = self.detecter_question_iot(message_utilisateur)
        if type_iot == "meteo":
            return self.gerer_question_meteo()
        elif type_iot == "capteurs":
            return self.gerer_question_capteurs()
        
        # Détecter si c'est une demande Pomodoro
        type_pomodoro = self.detecter_demande_pomodoro(message_utilisateur)
        if type_pomodoro:
            action_pomodoro = self.gerer_demande_pomodoro(message_utilisateur, type_pomodoro)
            print(f"\n[POMODORO]:\n{action_pomodoro}\n")
            return action_pomodoro
        
        # Détecter si c'est une demande de rappel
        if self.detecter_demande_rappel(message_utilisateur):
            action_rappel = self.gerer_demande_rappel(message_utilisateur)
            print(f"\n[RAPPEL GÉRÉ]:\n{action_rappel}\n")
            return action_rappel
        
        # Détecter si c'est une commande robot
        commande = self.detecter_commande_robot(message_utilisateur)
        action_robot = ""
        
        if commande:
            action_robot = self.executer_commande_robot(commande)
            print(f"\n[ACTION ROBOT]:\n{action_robot}\n")
        
        # Construire le prompt
        prompt_complet = self.construire_prompt(message_utilisateur)
        
        # Générer la réponse de l'agent
        try:
            reponse = self.llm.invoke(prompt_complet)
        except Exception as e:
            reponse = f"Désolé, j'ai eu un petit problème technique... ({str(e)})"
        
        # Sauvegarder dans l'historique
        self.historique_conversation.append({
            "role": "user",
            "message": message_utilisateur,
            "timestamp": datetime.now().strftime("%H:%M:%S")
        })
        
        self.historique_conversation.append({
            "role": "assistant",
            "message": reponse,
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "action_robot": action_robot if commande else None
        })
        
        return reponse
    
    def demarrer_conversation(self):
        """Message d'accueil du robot"""
        accueil = f"""Salut {self.nom_utilisateur} ! 🤖

Je suis RoboCompagnon, ton assistant personnel. Je suis là pour t'aider au quotidien.

Tu peux me demander de :
- Bouger (avancer, reculer, tourner)
- Scanner autour de moi
- Créer des rappels ("Rappelle-moi de réviser demain à 10h")
- Voir tes rappels ("Quels sont mes rappels ?")
- Lancer des sessions Pomodoro ("Session de maths", "Pomodoro de 30 min")
- Voir tes stats Pomodoro ("Mes sessions aujourd'hui")
- Discuter avec toi
- Te motiver dans tes études

Comment puis-je t'aider aujourd'hui ?"""
        
        return accueil


# ========== TEST DE L'AGENT ==========
if __name__ == "__main__":
    print("=" * 60)
    print("🤖 INITIALISATION DE L'AGENT IA")
    print("=" * 60)
    print("\nChargement du modèle IA...")
    
    # Créer l'agent
    agent = AgentRobot(nom_utilisateur="Monssef")
    
    # Message d'accueil
    print("\n" + agent.demarrer_conversation())
    
    # Conversation de test
    print("\n" + "=" * 60)
    print("CONVERSATION DE TEST")
    print("=" * 60)
    
    messages_test = [
        "Salut ! Comment ça va ?",
        "Lance une session Pomodoro de mathématiques",
        "Combien de sessions j'ai faites aujourd'hui ?",
        "Rappelle-moi d'acheter du pain demain à 17h",
        "Quels sont mes rappels ?"
    ]
    
    for msg in messages_test:
        print(f"\n👤 Utilisateur: {msg}")
        print("⏳ L'IA réfléchit...")
        reponse = agent.repondre(msg)
        print(f"🤖 Robot: {reponse}")
        print("-" * 60)
    
    print("\n✅ Test terminé !")
