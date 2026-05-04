# objets_connectes.py - Module de gestion des objets connectés IoT virtuels
from datetime import datetime

class ObjetConnecte:
    """Classe de base pour un objet connecté"""
    
    def __init__(self, nom, type_objet):
        self.nom = nom
        self.type = type_objet
        self.etat = False  # False = Éteint, True = Allumé
        self.derniere_action = None
        self.historique = []
    
    def allumer(self):
        """Allume l'objet"""
        if not self.etat:
            self.etat = True
            self._enregistrer_action("Allumé")
            return True
        return False
    
    def eteindre(self):
        """Éteint l'objet"""
        if self.etat:
            self.etat = False
            self._enregistrer_action("Éteint")
            return True
        return False
    
    def basculer(self):
        """Bascule l'état (allumé ↔ éteint)"""
        if self.etat:
            return self.eteindre()
        else:
            return self.allumer()
    
    def _enregistrer_action(self, action):
        """Enregistre une action dans l'historique"""
        timestamp = datetime.now()
        self.derniere_action = {
            'action': action,
            'timestamp': timestamp,
            'heure': timestamp.strftime('%H:%M:%S')
        }
        self.historique.append(self.derniere_action)
    
    def obtenir_etat(self):
        """Retourne l'état actuel"""
        return {
            'nom': self.nom,
            'type': self.type,
            'etat': self.etat,
            'etat_texte': 'Allumé' if self.etat else 'Éteint',
            'emoji': '🟢' if self.etat else '🔴',
            'derniere_action': self.derniere_action
        }


class Lumiere(ObjetConnecte):
    """Lumière connectée"""
    
    def __init__(self, nom="Lumière Chambre"):
        super().__init__(nom, "lumiere")
    
    def obtenir_etat(self):
        """Retourne l'état avec l'icone"""
        etat = super().obtenir_etat()
        etat['icone'] = "💡"
        return etat


class MaisonConnectee:
    """Gère tous les objets connectés de la maison"""
    
    def __init__(self):
        # Créer la lumière virtuelle
        self.lumiere = Lumiere()
        
        # Dictionnaire de tous les objets
        self.objets = {
            'lumiere': self.lumiere
        }
    
    def executer_commande(self, commande_texte):
        """
        Exécute une commande vocale
        
        Args:
            commande_texte: Commande en texte (ex: "allume la lumière")
        
        Returns:
            dict: Résultat de la commande
        """
        commande_lower = commande_texte.lower()
        
        # Détection commande lumière
        if 'lumière' in commande_lower or 'lumiere' in commande_lower or 'lampe' in commande_lower:
            
            # Allumer
            if 'allume' in commande_lower or 'ouvre' in commande_lower:
                if self.lumiere.allumer():
                    return {
                        'succes': True,
                        'objet': 'lumiere',
                        'action': 'allumée',
                        'message': '💡 Lumière allumée !',
                        'reponse_vocale': 'Lumière allumée'
                    }
                else:
                    return {
                        'succes': False,
                        'message': 'La lumière est déjà allumée',
                        'reponse_vocale': 'La lumière est déjà allumée'
                    }
            
            # Éteindre
            elif 'éteins' in commande_lower or 'eteins' in commande_lower or 'ferme' in commande_lower:
                if self.lumiere.eteindre():
                    return {
                        'succes': True,
                        'objet': 'lumiere',
                        'action': 'éteinte',
                        'message': '💡 Lumière éteinte !',
                        'reponse_vocale': 'Lumière éteinte'
                    }
                else:
                    return {
                        'succes': False,
                        'message': 'La lumière est déjà éteinte',
                        'reponse_vocale': 'La lumière est déjà éteinte'
                    }
        
        # Commande non reconnue
        return {
            'succes': False,
            'message': 'Commande non reconnue',
            'reponse_vocale': 'Je n\'ai pas compris la commande'
        }
    
    def obtenir_etat_tous(self):
        """Retourne l'état de tous les objets"""
        return {
            nom: obj.obtenir_etat() 
            for nom, obj in self.objets.items()
        }


# ========== TEST DU MODULE ==========
if __name__ == "__main__":
    print("="*60)
    print("🏠 TEST DU MODULE OBJETS CONNECTÉS")
    print("="*60)
    
    maison = MaisonConnectee()
    
    # Test 1: État initial
    print("\n📊 Test 1: État initial")
    etat = maison.lumiere.obtenir_etat()
    print(f"   Lumière: {etat['emoji']} {etat['etat_texte']}")
    
    # Test 2: Allumer
    print("\n💡 Test 2: Allumer la lumière")
    resultat = maison.executer_commande("Allume la lumière")
    print(f"   ✅ {resultat['message']}")
    etat = maison.lumiere.obtenir_etat()
    print(f"   État: {etat['emoji']} {etat['etat_texte']}")
    
    # Test 3: Éteindre
    print("\n💡 Test 3: Éteindre la lumière")
    resultat = maison.executer_commande("Éteins la lumière")
    print(f"   ✅ {resultat['message']}")
    etat = maison.lumiere.obtenir_etat()
    print(f"   État: {etat['emoji']} {etat['etat_texte']}")
    
    # Test 4: Variations de commandes
    print("\n🗣️ Test 4: Variations de commandes")
    
    commandes_test = [
        "Allume la lampe",
        "Ouvre la lumière",
        "Ferme la lumiere",
        "Éteins la lampe"
    ]
    
    for cmd in commandes_test:
        resultat = maison.executer_commande(cmd)
        print(f"   '{cmd}' → {resultat['message']}")
    
    # Test 5: État final
    print("\n📊 Test 5: État de tous les objets")
    etats = maison.obtenir_etat_tous()
    for nom, etat in etats.items():
        print(f"   {etat['icone']} {etat['nom']}: {etat['emoji']} {etat['etat_texte']}")
    
    print("\n" + "="*60)
    print("✅ Tests terminés !")
    print("="*60)
