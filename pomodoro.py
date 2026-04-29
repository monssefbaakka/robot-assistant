# pomodoro.py - Système Pomodoro pour sessions d'étude
from datetime import datetime, timedelta
import json
import os
import time
import threading

class SessionPomodoro:
    """Gestion des sessions d'étude avec technique Pomodoro"""
    
    def __init__(self, fichier_historique="pomodoro_historique.json"):
        self.fichier_historique = fichier_historique
        
        # Configuration par défaut
        self.duree_travail = 25  # minutes
        self.duree_pause_courte = 5  # minutes
        self.duree_pause_longue = 15  # minutes
        self.sessions_avant_pause_longue = 4
        
        # État actuel
        self.session_active = False
        self.type_session = None  # "travail", "pause_courte", "pause_longue"
        self.matiere_actuelle = None
        self.debut_session = None
        self.fin_prevue = None
        self.temps_restant = 0
        self.compteur_sessions = 0
        
        # Historique
        self.historique = self.charger_historique()
        
        # Timer
        self.timer_thread = None
        self.timer_actif = False
    
    def charger_historique(self):
        """Charge l'historique des sessions depuis le fichier JSON"""
        if os.path.exists(self.fichier_historique):
            try:
                with open(self.fichier_historique, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {"sessions": [], "statistiques": {}}
        return {"sessions": [], "statistiques": {}}
    
    def sauvegarder_historique(self):
        """Sauvegarde l'historique dans le fichier JSON"""
        try:
            with open(self.fichier_historique, 'w', encoding='utf-8') as f:
                json.dump(self.historique, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur sauvegarde: {e}")
    
    def demarrer_session_travail(self, matiere="Étude générale", duree=None):
        """Démarre une session de travail Pomodoro"""
        if self.session_active:
            return "⚠️ Une session est déjà en cours ! Termine-la d'abord."
        
        self.duree_travail = duree or self.duree_travail
        self.session_active = True
        self.type_session = "travail"
        self.matiere_actuelle = matiere
        self.debut_session = datetime.now()
        self.fin_prevue = self.debut_session + timedelta(minutes=self.duree_travail)
        self.temps_restant = self.duree_travail * 60  # en secondes
        
        # Démarrer le timer
        self.timer_actif = True
        self.timer_thread = threading.Thread(target=self._timer_loop, daemon=True)
        self.timer_thread.start()
        
        return f"""🍅 SESSION DE TRAVAIL DÉMARRÉE

📚 Matière: {matiere}
⏱️ Durée: {self.duree_travail} minutes
🎯 Fin prévue: {self.fin_prevue.strftime('%H:%M')}

Concentre-toi ! Je te préviendrai quand ce sera l'heure de la pause."""
    
    def _timer_loop(self):
        """Boucle du timer (exécutée dans un thread séparé)"""
        while self.timer_actif and self.temps_restant > 0:
            time.sleep(1)
            self.temps_restant -= 1
        
        if self.temps_restant <= 0 and self.session_active:
            self._session_terminee()
    
    def _session_terminee(self):
        """Appelée automatiquement quand une session se termine"""
        if self.type_session == "travail":
            # Enregistrer la session
            self._enregistrer_session()
            self.compteur_sessions += 1
            
            # Déterminer le type de pause
            if self.compteur_sessions % self.sessions_avant_pause_longue == 0:
                self.type_session = "pause_longue"
                duree_pause = self.duree_pause_longue
                message = f"🎉 Session {self.compteur_sessions} terminée ! Temps pour une GRANDE pause de {duree_pause} min !"
            else:
                self.type_session = "pause_courte"
                duree_pause = self.duree_pause_courte
                message = f"✅ Session {self.compteur_sessions} terminée ! Prends une pause de {duree_pause} min."
            
            print(f"\n{'='*60}")
            print(message)
            print(f"{'='*60}\n")
        
        elif self.type_session in ["pause_courte", "pause_longue"]:
            print(f"\n{'='*60}")
            print("⏰ Pause terminée ! Prêt pour une nouvelle session ?")
            print(f"{'='*60}\n")
            self.session_active = False
            self.type_session = None
    
    def _enregistrer_session(self):
        """Enregistre une session terminée dans l'historique"""
        session = {
            "date": self.debut_session.strftime("%Y-%m-%d"),
            "heure_debut": self.debut_session.strftime("%H:%M"),
            "heure_fin": datetime.now().strftime("%H:%M"),
            "matiere": self.matiere_actuelle,
            "duree_minutes": self.duree_travail,
            "completee": True
        }
        
        self.historique["sessions"].append(session)
        
        # Mettre à jour les statistiques
        self._mettre_a_jour_stats()
        
        self.sauvegarder_historique()
    
    def _mettre_a_jour_stats(self):
        """Met à jour les statistiques globales"""
        stats = self.historique.get("statistiques", {})
        
        # Total de sessions
        stats["total_sessions"] = len(self.historique["sessions"])
        
        # Temps total (en heures)
        temps_total = sum(s.get("duree_minutes", 0) for s in self.historique["sessions"])
        stats["temps_total_heures"] = round(temps_total / 60, 1)
        
        # Sessions par matière
        matieres = {}
        for session in self.historique["sessions"]:
            mat = session.get("matiere", "Inconnu")
            matieres[mat] = matieres.get(mat, 0) + 1
        stats["par_matiere"] = matieres
        
        # Sessions aujourd'hui
        aujourd_hui = datetime.now().strftime("%Y-%m-%d")
        sessions_aujourd_hui = [s for s in self.historique["sessions"] if s.get("date") == aujourd_hui]
        stats["sessions_aujourd_hui"] = len(sessions_aujourd_hui)
        
        self.historique["statistiques"] = stats
    
    def arreter_session(self):
        """Arrête manuellement la session en cours"""
        if not self.session_active:
            return "❌ Aucune session en cours."
        
        self.timer_actif = False
        temps_ecoule = self.duree_travail * 60 - self.temps_restant
        minutes_ecoulees = temps_ecoule // 60
        
        self.session_active = False
        self.type_session = None
        
        return f"⏹️ Session arrêtée après {minutes_ecoulees} minutes."
    
    def etat_session(self):
        """Retourne l'état actuel de la session"""
        if not self.session_active:
            return {
                "active": False,
                "message": "Aucune session en cours"
            }
        
        minutes_restantes = self.temps_restant // 60
        secondes_restantes = self.temps_restant % 60
        
        return {
            "active": True,
            "type": self.type_session,
            "matiere": self.matiere_actuelle,
            "temps_restant": f"{minutes_restantes}:{secondes_restantes:02d}",
            "fin_prevue": self.fin_prevue.strftime("%H:%M"),
            "sessions_completees": self.compteur_sessions
        }
    
    def obtenir_statistiques(self):
        """Retourne les statistiques complètes"""
        self._mettre_a_jour_stats()
        return self.historique.get("statistiques", {})
    
    def obtenir_sessions_aujourdhui(self):
        """Retourne les sessions d'aujourd'hui"""
        aujourd_hui = datetime.now().strftime("%Y-%m-%d")
        return [s for s in self.historique["sessions"] if s.get("date") == aujourd_hui]
    
    def configurer(self, travail=None, pause_courte=None, pause_longue=None):
        """Configure les durées des sessions"""
        if travail:
            self.duree_travail = travail
        if pause_courte:
            self.duree_pause_courte = pause_courte
        if pause_longue:
            self.duree_pause_longue = pause_longue
        
        return f"⚙️ Configuration mise à jour: {self.duree_travail}min travail, {self.duree_pause_courte}min pause courte, {self.duree_pause_longue}min pause longue"
    
    def afficher_statistiques(self):
        """Affiche les statistiques formatées"""
        stats = self.obtenir_statistiques()
        
        print("\n" + "="*60)
        print("📊 STATISTIQUES POMODORO")
        print("="*60)
        print(f"Total de sessions: {stats.get('total_sessions', 0)}")
        print(f"Temps total d'étude: {stats.get('temps_total_heures', 0)}h")
        print(f"Sessions aujourd'hui: {stats.get('sessions_aujourd_hui', 0)}")
        
        print("\n📚 Par matière:")
        for matiere, count in stats.get('par_matiere', {}).items():
            print(f"   • {matiere}: {count} sessions")
        
        print("="*60)


# ========== EXEMPLE D'UTILISATION ==========
if __name__ == "__main__":
    print("="*60)
    print("🍅 SYSTÈME POMODORO - SESSION D'ÉTUDE")
    print("="*60)
    
    pomodoro = SessionPomodoro()
    
    # Afficher les stats actuelles
    pomodoro.afficher_statistiques()
    
    # Démarrer une session de test (2 minutes au lieu de 25 pour le test)
    print("\n📝 Démarrage d'une session de test (2 minutes)...")
    print(pomodoro.demarrer_session_travail(matiere="Mathématiques", duree=2))
    
    # Afficher l'état pendant la session
    print("\n⏱️ État de la session:")
    etat = pomodoro.etat_session()
    if etat['active']:
        print(f"Type: {etat['type']}")
        print(f"Matière: {etat['matiere']}")
        print(f"Temps restant: {etat['temps_restant']}")
        print(f"Fin prévue: {etat['fin_prevue']}")
    
    # Attendre 10 secondes pour voir le timer
    print("\n⏳ Attente de 10 secondes...")
    time.sleep(10)
    
    # Afficher l'état mis à jour
    etat = pomodoro.etat_session()
    if etat['active']:
        print(f"⏱️ Temps restant après 10s: {etat['temps_restant']}")
    
    # Arrêter la session manuellement
    print("\n" + pomodoro.arreter_session())
    
    # Afficher les sessions d'aujourd'hui
    print("\n📅 Sessions d'aujourd'hui:")
    sessions = pomodoro.obtenir_sessions_aujourdhui()
    for s in sessions:
        print(f"   • {s['heure_debut']} - {s['matiere']} ({s['duree_minutes']}min)")
    
    print("\n✅ Test terminé !")
