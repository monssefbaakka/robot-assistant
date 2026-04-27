# rappels.py - Système de rappels intelligents pour le robot
from datetime import datetime, timedelta
import json
import os

class SystemeRappels:
    """Gestion des rappels et notifications pour l'utilisateur"""
    
    def __init__(self, fichier_sauvegarde="rappels.json"):
        self.fichier_sauvegarde = fichier_sauvegarde
        self.rappels = []
        self.charger_rappels()
    
    def charger_rappels(self):
        """Charge les rappels depuis le fichier JSON"""
        if os.path.exists(self.fichier_sauvegarde):
            try:
                with open(self.fichier_sauvegarde, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    self.rappels = data.get('rappels', [])
            except Exception as e:
                print(f"Erreur lors du chargement des rappels: {e}")
                self.rappels = []
        else:
            self.rappels = []
    
    def sauvegarder_rappels(self):
        """Sauvegarde les rappels dans le fichier JSON"""
        try:
            with open(self.fichier_sauvegarde, 'w', encoding='utf-8') as f:
                json.dump({'rappels': self.rappels}, f, indent=2, ensure_ascii=False)
        except Exception as e:
            print(f"Erreur lors de la sauvegarde: {e}")
    
    def ajouter_rappel(self, titre, description, date_heure, type_rappel="unique", priorite="normale"):
        """
        Ajoute un nouveau rappel
        
        Args:
            titre: Titre du rappel (ex: "Examen de Maths")
            description: Description détaillée
            date_heure: Date et heure (format: "YYYY-MM-DD HH:MM" ou objet datetime)
            type_rappel: "unique", "quotidien", "hebdomadaire"
            priorite: "basse", "normale", "haute", "critique"
        """
        # Convertir la date en string si c'est un objet datetime
        if isinstance(date_heure, datetime):
            date_heure_str = date_heure.strftime("%Y-%m-%d %H:%M")
        else:
            date_heure_str = date_heure
        
        rappel = {
            "id": len(self.rappels) + 1,
            "titre": titre,
            "description": description,
            "date_heure": date_heure_str,
            "type": type_rappel,
            "priorite": priorite,
            "actif": True,
            "complete": False,
            "cree_le": datetime.now().strftime("%Y-%m-%d %H:%M")
        }
        
        self.rappels.append(rappel)
        self.sauvegarder_rappels()
        return rappel
    
    def ajouter_examen(self, matiere, date, heure="09:00", details=""):
        """Raccourci pour ajouter un examen"""
        date_complete = f"{date} {heure}"
        titre = f"📚 Examen de {matiere}"
        description = f"Examen de {matiere}"
        if details:
            description += f" - {details}"
        
        return self.ajouter_rappel(
            titre=titre,
            description=description,
            date_heure=date_complete,
            type_rappel="unique",
            priorite="haute"
        )
    
    def ajouter_devoir(self, matiere, date_limite, description=""):
        """Raccourci pour ajouter un devoir"""
        titre = f"✍️ Devoir de {matiere}"
        desc = f"Deadline pour le devoir de {matiere}"
        if description:
            desc += f" : {description}"
        
        return self.ajouter_rappel(
            titre=titre,
            description=desc,
            date_heure=date_limite,
            type_rappel="unique",
            priorite="normale"
        )
    
    def ajouter_rappel_quotidien(self, titre, heure, description=""):
        """Ajoute un rappel qui se répète chaque jour"""
        # Pour un rappel quotidien, on met la date d'aujourd'hui
        maintenant = datetime.now()
        date_heure = f"{maintenant.strftime('%Y-%m-%d')} {heure}"
        
        return self.ajouter_rappel(
            titre=titre,
            description=description or titre,
            date_heure=date_heure,
            type_rappel="quotidien",
            priorite="normale"
        )
    
    def obtenir_rappels_actifs(self):
        """Retourne tous les rappels actifs non complétés"""
        return [r for r in self.rappels if r['actif'] and not r['complete']]
    
    def obtenir_rappels_urgents(self, heures=24):
        """Retourne les rappels dans les prochaines X heures"""
        maintenant = datetime.now()
        limite = maintenant + timedelta(hours=heures)
        
        urgents = []
        for rappel in self.obtenir_rappels_actifs():
            try:
                date_rappel = datetime.strptime(rappel['date_heure'], "%Y-%m-%d %H:%M")
                if maintenant <= date_rappel <= limite:
                    # Calculer le temps restant
                    temps_restant = date_rappel - maintenant
                    rappel['temps_restant'] = str(temps_restant).split('.')[0]  # Sans microsecondes
                    urgents.append(rappel)
            except:
                pass
        
        # Trier par date
        urgents.sort(key=lambda x: x['date_heure'])
        return urgents
    
    def obtenir_rappels_aujourdhui(self):
        """Retourne les rappels d'aujourd'hui"""
        aujourd_hui = datetime.now().strftime("%Y-%m-%d")
        
        rappels_jour = []
        for rappel in self.obtenir_rappels_actifs():
            if rappel['date_heure'].startswith(aujourd_hui):
                rappels_jour.append(rappel)
        
        # Trier par heure
        rappels_jour.sort(key=lambda x: x['date_heure'])
        return rappels_jour
    
    def obtenir_prochains_rappels(self, nombre=5):
        """Retourne les N prochains rappels"""
        maintenant = datetime.now()
        
        futurs = []
        for rappel in self.obtenir_rappels_actifs():
            try:
                date_rappel = datetime.strptime(rappel['date_heure'], "%Y-%m-%d %H:%M")
                if date_rappel >= maintenant:
                    # Calculer le temps restant
                    temps_restant = date_rappel - maintenant
                    jours = temps_restant.days
                    heures = temps_restant.seconds // 3600
                    
                    if jours > 0:
                        rappel['temps_restant'] = f"{jours}j {heures}h"
                    else:
                        minutes = (temps_restant.seconds % 3600) // 60
                        rappel['temps_restant'] = f"{heures}h {minutes}min"
                    
                    futurs.append(rappel)
            except:
                pass
        
        # Trier par date
        futurs.sort(key=lambda x: x['date_heure'])
        return futurs[:nombre]
    
    def marquer_complete(self, rappel_id):
        """Marque un rappel comme complété"""
        for rappel in self.rappels:
            if rappel['id'] == rappel_id:
                rappel['complete'] = True
                self.sauvegarder_rappels()
                return True
        return False
    
    def supprimer_rappel(self, rappel_id):
        """Supprime un rappel"""
        self.rappels = [r for r in self.rappels if r['id'] != rappel_id]
        self.sauvegarder_rappels()
    
    def desactiver_rappel(self, rappel_id):
        """Désactive un rappel sans le supprimer"""
        for rappel in self.rappels:
            if rappel['id'] == rappel_id:
                rappel['actif'] = False
                self.sauvegarder_rappels()
                return True
        return False
    
    def afficher_resume(self):
        """Affiche un résumé des rappels"""
        actifs = self.obtenir_rappels_actifs()
        aujourd_hui = self.obtenir_rappels_aujourdhui()
        urgents = self.obtenir_rappels_urgents(24)
        
        print("\n" + "=" * 60)
        print("📋 RÉSUMÉ DES RAPPELS")
        print("=" * 60)
        print(f"Total de rappels actifs: {len(actifs)}")
        print(f"Rappels aujourd'hui: {len(aujourd_hui)}")
        print(f"Rappels urgents (24h): {len(urgents)}")
        print("=" * 60)
    
    def afficher_prochains(self):
        """Affiche les prochains rappels"""
        prochains = self.obtenir_prochains_rappels(5)
        
        print("\n📅 PROCHAINS RAPPELS:")
        print("-" * 60)
        
        if not prochains:
            print("Aucun rappel à venir.")
            return
        
        for rappel in prochains:
            priorite_icon = {
                "basse": "⚪",
                "normale": "🔵",
                "haute": "🟠",
                "critique": "🔴"
            }.get(rappel['priorite'], "⚪")
            
            print(f"\n{priorite_icon} {rappel['titre']}")
            print(f"   📆 {rappel['date_heure']}")
            print(f"   ⏳ Dans {rappel['temps_restant']}")
            if rappel.get('description'):
                print(f"   💬 {rappel['description']}")


# ========== EXEMPLE D'UTILISATION ==========
if __name__ == "__main__":
    print("=" * 60)
    print("🔔 SYSTÈME DE RAPPELS INTELLIGENTS")
    print("=" * 60)
    
    # Créer le système
    systeme = SystemeRappels()
    
    # Ajouter quelques exemples
    print("\n➕ Ajout de rappels d'exemple...")
    
    # Examens
    systeme.ajouter_examen(
        matiere="Mathématiques",
        date="2024-05-15",
        heure="09:00",
        details="Chapitres 5 à 8"
    )
    
    systeme.ajouter_examen(
        matiere="Programmation Python",
        date="2024-05-20",
        heure="14:00"
    )
    
    # Devoirs
    systeme.ajouter_devoir(
        matiere="Physique",
        date_limite="2024-05-10 23:59",
        description="Exercices sur la mécanique quantique"
    )
    
    # Rappels quotidiens
    systeme.ajouter_rappel_quotidien(
        titre="💧 Boire de l'eau",
        heure="10:00"
    )
    
    systeme.ajouter_rappel_quotidien(
        titre="🏃 Pause active",
        heure="15:00",
        description="Faire 5 minutes de marche"
    )
    
    # Rappel personnalisé
    demain = datetime.now() + timedelta(days=1)
    systeme.ajouter_rappel(
        titre="📞 Appeler le dentiste",
        description="Prendre RDV pour contrôle",
        date_heure=demain.replace(hour=11, minute=0),
        priorite="normale"
    )
    
    print("✅ Rappels ajoutés avec succès !")
    
    # Afficher le résumé
    systeme.afficher_resume()
    
    # Afficher les prochains rappels
    systeme.afficher_prochains()
    
    # Afficher les rappels urgents
    print("\n" + "=" * 60)
    print("⚠️ RAPPELS URGENTS (24H):")
    print("-" * 60)
    urgents = systeme.obtenir_rappels_urgents(24)
    if urgents:
        for rappel in urgents:
            print(f"• {rappel['titre']} - Dans {rappel['temps_restant']}")
    else:
        print("Aucun rappel urgent.")
    
    print("\n" + "=" * 60)
    print("✅ Test terminé !")
    print("=" * 60)
