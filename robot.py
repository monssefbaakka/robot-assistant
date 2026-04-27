# robot.py - Le robot virtuel avec ses fonctions de base
import math
import random
from datetime import datetime

class RobotVirtuel:
    """Un robot qui existe en mémoire avec position et capteurs simulés"""
    
    def __init__(self):
        self.position = {"x": 0, "y": 0}  # Position sur la carte (en cm)
        self.direction = 0  # Angle en degrés (0 = Nord, 90 = Est)
        self.vitesse = 10  # cm par mouvement
        self.batterie = 100  # Pourcentage
        self.historique = []  # Logs des actions
        self.etat_actuel = "idle"  # idle, moving, scanning, charging
        
    def avancer(self, distance_cm=None):
        """Avance le robot d'une certaine distance"""
        if distance_cm is None:
            distance_cm = self.vitesse
            
        if self.batterie < 5:
            return "⚠️ Batterie trop faible pour avancer !"
            
        # Calculer nouvelle position selon la direction
        rad = math.radians(self.direction)
        self.position["x"] += distance_cm * math.sin(rad)
        self.position["y"] += distance_cm * math.cos(rad)
        
        self.batterie -= abs(distance_cm) * 0.1
        self.etat_actuel = "moving"
        
        message = f"✓ Avancé de {distance_cm}cm → Position: ({self.position['x']:.1f}, {self.position['y']:.1f})"
        self.historique.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "action": "avancer",
            "message": message
        })
        return message
    
    def reculer(self, distance_cm=None):
        """Recule le robot"""
        if distance_cm is None:
            distance_cm = self.vitesse
        return self.avancer(-distance_cm)
    
    def tourner_droite(self, angle_degres=90):
        """Tourne à droite"""
        return self.tourner(angle_degres)
    
    def tourner_gauche(self, angle_degres=90):
        """Tourne à gauche"""
        return self.tourner(-angle_degres)
    
    def tourner(self, angle_degres):
        """Tourne le robot (positif = droite, négatif = gauche)"""
        self.direction = (self.direction + angle_degres) % 360
        direction_text = self._get_direction_text()
        message = f"↻ Tourné de {angle_degres}° → Direction: {self.direction}° ({direction_text})"
        self.historique.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "action": "tourner",
            "message": message
        })
        return message
    
    def scanner(self):
        """Simule un scan des obstacles autour"""
        self.etat_actuel = "scanning"
        # Pour l'instant on simule des distances aléatoires
        distances = {
            "avant": random.randint(20, 200),
            "droite": random.randint(20, 200),
            "gauche": random.randint(20, 200),
            "arriere": random.randint(20, 200)
        }
        
        message = f"📡 Scan complet:\n"
        message += f"   Avant: {distances['avant']}cm\n"
        message += f"   Droite: {distances['droite']}cm\n"
        message += f"   Gauche: {distances['gauche']}cm\n"
        message += f"   Arrière: {distances['arriere']}cm"
        
        self.historique.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "action": "scanner",
            "message": message
        })
        
        self.etat_actuel = "idle"
        return message, distances
    
    def recharger(self):
        """Recharge la batterie"""
        self.etat_actuel = "charging"
        old_bat = self.batterie
        self.batterie = 100
        message = f"🔋 Batterie rechargée: {old_bat:.0f}% → 100%"
        self.historique.append({
            "timestamp": datetime.now().strftime("%H:%M:%S"),
            "action": "recharger",
            "message": message
        })
        self.etat_actuel = "idle"
        return message
    
    def etat(self):
        """Retourne l'état complet du robot"""
        return {
            "position": self.position,
            "direction": self.direction,
            "direction_text": self._get_direction_text(),
            "batterie": round(self.batterie, 1),
            "etat": self.etat_actuel,
            "nb_actions": len(self.historique)
        }
    
    def _get_direction_text(self):
        """Convertit l'angle en direction textuelle"""
        angle = self.direction % 360
        if 337.5 <= angle or angle < 22.5:
            return "Nord"
        elif 22.5 <= angle < 67.5:
            return "Nord-Est"
        elif 67.5 <= angle < 112.5:
            return "Est"
        elif 112.5 <= angle < 157.5:
            return "Sud-Est"
        elif 157.5 <= angle < 202.5:
            return "Sud"
        elif 202.5 <= angle < 247.5:
            return "Sud-Ouest"
        elif 247.5 <= angle < 292.5:
            return "Ouest"
        else:
            return "Nord-Ouest"
    
    def afficher_historique(self):
        """Affiche toutes les actions effectuées"""
        print("\n📜 HISTORIQUE DES ACTIONS:")
        for i, entry in enumerate(self.historique, 1):
            print(f"  {i}. [{entry['timestamp']}] {entry['message']}")
    
    def reset(self):
        """Remet le robot à zéro"""
        self.position = {"x": 0, "y": 0}
        self.direction = 0
        self.batterie = 100
        self.historique = []
        self.etat_actuel = "idle"
        return "🔄 Robot réinitialisé"


# ========== TEST DU ROBOT ==========
if __name__ == "__main__":
    print("=" * 50)
    print("🤖 DÉMARRAGE DU ROBOT VIRTUEL")
    print("=" * 50)
    
    robot = RobotVirtuel()
    
    # Scénario de test: navigation en carré
    print("\n🎯 Scénario: Navigation en carré\n")
    
    print(robot.avancer(50))
    print(robot.tourner_droite(90))
    print(robot.avancer(50))
    print(robot.tourner_droite(90))
    print(robot.avancer(50))
    print(robot.tourner_droite(90))
    print(robot.avancer(50))
    
    print("\n🔍 Scan de l'environnement:\n")
    message, distances = robot.scanner()
    print(message)
    
    print("\n📊 ÉTAT FINAL DU ROBOT:")
    print("-" * 50)
    etat = robot.etat()
    print(f"  Position: ({etat['position']['x']:.1f}, {etat['position']['y']:.1f})")
    print(f"  Direction: {etat['direction']}° ({etat['direction_text']})")
    print(f"  Batterie: {etat['batterie']}%")
    print(f"  État: {etat['etat']}")
    print(f"  Actions effectuées: {etat['nb_actions']}")
    
    robot.afficher_historique()
    
    print("\n" + "=" * 50)
    print("✅ Test terminé !")
    print("=" * 50)
