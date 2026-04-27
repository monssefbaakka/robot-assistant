# agent.py - Agent IA conversationnel pour le robot assistant
from langchain_community.llms import Ollama
from robot import RobotVirtuel
from rappels import SystemeRappels
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

Historique récent:
{historique}

Règles importantes:
1. Sois naturel, amical et encourageant
2. Tutoie l'utilisateur
3. Adapte-toi à son humeur
4. Si on te demande de bouger, confirme l'action
5. Si on te demande un rappel, confirme sa création
6. Sois concis (2-3 phrases max sauf si demande détaillée)
7. N'invente pas de capacités que tu n'as pas

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
        "Rappelle-moi d'acheter du pain demain à 17h",
        "J'ai un examen de maths le 15 mai à 9h",
        "Quels sont mes rappels ?",
        "Avance un peu"
    ]
    
    for msg in messages_test:
        print(f"\n👤 Utilisateur: {msg}")
        print("⏳ L'IA réfléchit...")
        reponse = agent.repondre(msg)
        print(f"🤖 Robot: {reponse}")
        print("-" * 60)
    
    print("\n✅ Test terminé !")
