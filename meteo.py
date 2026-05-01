# meteo.py - Module pour récupérer la météo en temps réel
import requests
from datetime import datetime

class MeteoAPI:
    """Récupère les données météo en temps réel via l'API OpenWeatherMap (gratuite)"""
    
    def __init__(self, ville="Rabat", pays="MA"):
        self.ville = ville
        self.pays = pays
        # API gratuite OpenWeatherMap (pas besoin de clé pour la version de base)
        self.base_url = "https://wttr.in"  # API simple sans clé requise
        
    def obtenir_meteo(self):
        """
        Récupère la météo actuelle
        
        Returns:
            dict: Données météo avec température, conditions, etc.
        """
        try:
            # Utiliser wttr.in - API météo gratuite sans clé
            url = f"{self.base_url}/{self.ville}?format=j1"
            
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                # Extraire les données pertinentes
                current = data['current_condition'][0]
                
                meteo = {
                    'ville': self.ville,
                    'temperature': int(current['temp_C']),
                    'ressenti': int(current['FeelsLikeC']),
                    'description': current['weatherDesc'][0]['value'],
                    'humidite': int(current['humidity']),
                    'vent_kmh': int(current['windspeedKmph']),
                    'pression': int(current['pressure']),
                    'uv_index': int(current['uvIndex']),
                    'visibilite_km': int(current['visibility']),
                    'precipitation_mm': float(current.get('precipMM', 0)),
                    'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                }
                
                return meteo
            else:
                return self._meteo_erreur()
                
        except Exception as e:
            print(f"Erreur météo: {e}")
            return self._meteo_erreur()
    
    def _meteo_erreur(self):
        """Retourne des données par défaut en cas d'erreur"""
        return {
            'ville': self.ville,
            'temperature': 22,
            'ressenti': 21,
            'description': "Données non disponibles",
            'humidite': 50,
            'vent_kmh': 10,
            'pression': 1013,
            'uv_index': 5,
            'visibilite_km': 10,
            'precipitation_mm': 0,
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'erreur': True
        }
    
    def obtenir_previsions(self, nb_jours=3):
        """
        Récupère les prévisions pour les prochains jours
        
        Args:
            nb_jours: Nombre de jours de prévisions (max 3 pour version gratuite)
        
        Returns:
            list: Liste des prévisions par jour
        """
        try:
            url = f"{self.base_url}/{self.ville}?format=j1"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                previsions = []
                for day_data in data['weather'][:nb_jours]:
                    prev = {
                        'date': day_data['date'],
                        'temp_max': int(day_data['maxtempC']),
                        'temp_min': int(day_data['mintempC']),
                        'description': day_data['hourly'][0]['weatherDesc'][0]['value'],
                        'precipitation_mm': float(day_data.get('totalprecipMM', 0)),
                        'uv_index': int(day_data['uvIndex'])
                    }
                    previsions.append(prev)
                
                return previsions
            else:
                return []
                
        except Exception as e:
            print(f"Erreur prévisions: {e}")
            return []
    
    def obtenir_conseil_meteo(self, meteo=None):
        """
        Génère un conseil personnalisé basé sur la météo
        
        Args:
            meteo: Données météo (ou None pour récupérer automatiquement)
        
        Returns:
            str: Conseil personnalisé
        """
        if meteo is None:
            meteo = self.obtenir_meteo()
        
        conseils = []
        
        # Température
        temp = meteo['temperature']
        if temp > 30:
            conseils.append("🔥 Il fait très chaud ! Hydrate-toi bien.")
        elif temp > 25:
            conseils.append("☀️ Belle journée ensoleillée ! Porte des lunettes.")
        elif temp < 10:
            conseils.append("🧥 Il fait froid, mets un manteau !")
        elif temp < 15:
            conseils.append("🧣 Un peu frais, prends un pull.")
        
        # Précipitations
        if meteo['precipitation_mm'] > 5:
            conseils.append("☔ Il pleut beaucoup ! Parapluie obligatoire.")
        elif meteo['precipitation_mm'] > 0:
            conseils.append("🌧️ Risque de pluie, prends un parapluie.")
        
        # Vent
        if meteo['vent_kmh'] > 40:
            conseils.append("💨 Vent très fort ! Attention dehors.")
        elif meteo['vent_kmh'] > 25:
            conseils.append("🌬️ Vent modéré, couvre-toi bien.")
        
        # UV
        if meteo['uv_index'] > 7:
            conseils.append("🧴 Indice UV élevé ! Mets de la crème solaire.")
        
        # Humidité
        if meteo['humidite'] > 80:
            conseils.append("💧 Très humide, sensation de lourdeur.")
        elif meteo['humidite'] < 30:
            conseils.append("🏜️ Air sec, pense à t'hydrater.")
        
        if not conseils:
            conseils.append("✨ Météo agréable, profites-en !")
        
        return " ".join(conseils)
    
    def formater_meteo_texte(self):
        """Retourne un résumé textuel de la météo"""
        meteo = self.obtenir_meteo()
        
        texte = f"📍 {meteo['ville']}\n"
        texte += f"🌡️ {meteo['temperature']}°C (ressenti {meteo['ressenti']}°C)\n"
        texte += f"☁️ {meteo['description']}\n"
        texte += f"💧 Humidité: {meteo['humidite']}%\n"
        texte += f"💨 Vent: {meteo['vent_kmh']} km/h\n"
        
        if meteo['precipitation_mm'] > 0:
            texte += f"🌧️ Précipitations: {meteo['precipitation_mm']} mm\n"
        
        texte += f"\n{self.obtenir_conseil_meteo(meteo)}"
        
        return texte


# ========== TEST DU MODULE ==========
if __name__ == "__main__":
    print("="*60)
    print("🌤️ TEST DU MODULE MÉTÉO")
    print("="*60)
    
    # Créer l'objet météo pour Rabat
    meteo_api = MeteoAPI(ville="Rabat", pays="MA")
    
    print("\n📊 MÉTÉO ACTUELLE:")
    print("-"*60)
    print(meteo_api.formater_meteo_texte())
    
    print("\n" + "="*60)
    print("📅 PRÉVISIONS 3 JOURS:")
    print("="*60)
    
    previsions = meteo_api.obtenir_previsions(3)
    for i, prev in enumerate(previsions, 1):
        print(f"\nJour {i} ({prev['date']}):")
        print(f"  🌡️ Max: {prev['temp_max']}°C | Min: {prev['temp_min']}°C")
        print(f"  ☁️ {prev['description']}")
        if prev['precipitation_mm'] > 0:
            print(f"  🌧️ Pluie: {prev['precipitation_mm']} mm")
    
    print("\n" + "="*60)
    print("✅ Test terminé !")
    print("="*60)
