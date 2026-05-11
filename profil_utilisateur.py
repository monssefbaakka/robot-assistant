# profil_utilisateur.py - Gestion du profil utilisateur
import json
import os
from datetime import datetime

class ProfilUtilisateur:
    """Gère le profil et les préférences de l'utilisateur"""
    
    def __init__(self, fichier_profil="profil_utilisateur.json"):
        self.fichier_profil = fichier_profil
        self.profil = self.charger_profil()
    
    def charger_profil(self):
        """Charge le profil depuis le fichier JSON"""
        if os.path.exists(self.fichier_profil):
            try:
                with open(self.fichier_profil, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return self.creer_profil_defaut()
        else:
            return self.creer_profil_defaut()
    
    def creer_profil_defaut(self):
        """Crée un profil par défaut"""
        return {
            "nom": "Baghdad",
            "prenom": "Baghdad",
            "nom_complet": "Baghdad BAAKKA",
            "preferences": {
                "matieres_preferees": ["Mathématiques", "Physique", "Informatique"],
                "objectifs": ["Réussir mes examens", "Améliorer ma productivité"],
                "style_communication": "amical",  # amical, formel, motivant
                "langue": "fr"
            },
            "statistiques": {
                "sessions_pomodoro_total": 0,
                "temps_etude_total_minutes": 0,
                "rappels_crees": 0,
                "rappels_completes": 0
            },
            "parametres": {
                "duree_pomodoro_minutes": 25,
                "duree_pause_minutes": 5,
                "notifications_actives": True,
                "voix_robot_active": True
            },
            "date_creation": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "derniere_connexion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }
    
    def sauvegarder_profil(self):
        """Sauvegarde le profil dans le fichier JSON"""
        try:
            with open(self.fichier_profil, 'w', encoding='utf-8') as f:
                json.dump(self.profil, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Erreur sauvegarde profil: {e}")
            return False
    
    def mettre_a_jour_connexion(self):
        """Met à jour la dernière connexion"""
        self.profil["derniere_connexion"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.sauvegarder_profil()
    
    def obtenir_nom(self):
        """Retourne le nom de l'utilisateur"""
        return self.profil.get("nom", "ami")
    
    def obtenir_prenom(self):
        """Retourne le prénom"""
        return self.profil.get("prenom", "")
    
    def obtenir_salutation_personnalisee(self):
        """Génère une salutation personnalisée"""
        nom = self.obtenir_nom()
        heure = datetime.now().hour
        
        if 5 <= heure < 12:
            moment = "Bonjour"
            emoji = "🌅"
        elif 12 <= heure < 18:
            moment = "Bon après-midi"
            emoji = "☀️"
        else:
            moment = "Bonsoir"
            emoji = "🌙"
        
        return f"{emoji} {moment} {nom} !"
    
    def obtenir_preferences(self):
        """Retourne les préférences utilisateur"""
        return self.profil.get("preferences", {})
    
    def obtenir_matieres_preferees(self):
        """Retourne les matières préférées"""
        return self.profil.get("preferences", {}).get("matieres_preferees", [])
    
    def obtenir_statistiques(self):
        """Retourne les statistiques"""
        return self.profil.get("statistiques", {})
    
    def incrementer_sessions_pomodoro(self, duree_minutes=25):
        """Incrémente le compteur de sessions Pomodoro"""
        if "statistiques" not in self.profil:
            self.profil["statistiques"] = {}
        
        self.profil["statistiques"]["sessions_pomodoro_total"] = \
            self.profil["statistiques"].get("sessions_pomodoro_total", 0) + 1
        
        self.profil["statistiques"]["temps_etude_total_minutes"] = \
            self.profil["statistiques"].get("temps_etude_total_minutes", 0) + duree_minutes
        
        self.sauvegarder_profil()
    
    def incrementer_rappels(self, type_action="cree"):
        """Incrémente les compteurs de rappels"""
        if "statistiques" not in self.profil:
            self.profil["statistiques"] = {}
        
        if type_action == "cree":
            self.profil["statistiques"]["rappels_crees"] = \
                self.profil["statistiques"].get("rappels_crees", 0) + 1
        elif type_action == "complete":
            self.profil["statistiques"]["rappels_completes"] = \
                self.profil["statistiques"].get("rappels_completes", 0) + 1
        
        self.sauvegarder_profil()
    
    def modifier_preference(self, cle, valeur):
        """Modifie une préférence"""
        if "preferences" not in self.profil:
            self.profil["preferences"] = {}
        
        self.profil["preferences"][cle] = valeur
        self.sauvegarder_profil()
    
    def obtenir_message_motivation(self):
        """Génère un message de motivation personnalisé"""
        stats = self.obtenir_statistiques()
        sessions = stats.get("sessions_pomodoro_total", 0)
        temps_total = stats.get("temps_etude_total_minutes", 0)
        
        messages = []
        
        if sessions > 0:
            messages.append(f"Tu as complété {sessions} sessions Pomodoro ! 🎯")
        
        if temps_total >= 60:
            heures = temps_total // 60
            messages.append(f"Tu as étudié {heures}h au total ! 📚")
        
        if len(messages) == 0:
            messages.append("Continue comme ça ! 💪")
        
        return " ".join(messages)


# ========== TEST DU MODULE ==========
if __name__ == "__main__":
    print("="*60)
    print("👤 TEST DU MODULE PROFIL UTILISATEUR")
    print("="*60)
    
    # Créer/Charger profil
    profil = ProfilUtilisateur()
    
    # Test 1: Salutation personnalisée
    print("\n🎭 Test 1: Salutation")
    salutation = profil.obtenir_salutation_personnalisee()
    print(f"   {salutation}")
    
    # Test 2: Informations profil
    print("\n📋 Test 2: Informations profil")
    print(f"   Nom: {profil.obtenir_nom()}")
    print(f"   Matières préférées: {', '.join(profil.obtenir_matieres_preferees())}")
    
    # Test 3: Statistiques
    print("\n📊 Test 3: Statistiques")
    stats = profil.obtenir_statistiques()
    print(f"   Sessions Pomodoro: {stats.get('sessions_pomodoro_total', 0)}")
    print(f"   Temps d'étude: {stats.get('temps_etude_total_minutes', 0)} min")
    
    # Test 4: Incrémenter session
    print("\n➕ Test 4: Simuler une session Pomodoro")
    profil.incrementer_sessions_pomodoro(25)
    print("   Session ajoutée !")
    
    # Test 5: Message motivation
    print("\n💪 Test 5: Message de motivation")
    motivation = profil.obtenir_message_motivation()
    print(f"   {motivation}")
    
    # Test 6: Sauvegarder
    print("\n💾 Test 6: Sauvegarde")
    if profil.sauvegarder_profil():
        print(f"   ✅ Profil sauvegardé dans {profil.fichier_profil}")
    
    print("\n" + "="*60)
    print("✅ Tests terminés !")
    print("="*60)
