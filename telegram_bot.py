# telegram_bot.py - Module de notifications Telegram pour le robot IoT
import requests
import json
from datetime import datetime

class TelegramBot:
    """Gère les notifications Telegram du robot"""
    
    def __init__(self, token):
        self.token = token
        self.base_url = f"https://api.telegram.org/bot{token}"
        self.chat_id = None  # Sera défini après le premier message
    
    def obtenir_chat_id(self):
        """
        Récupère le chat_id depuis les derniers messages
        L'utilisateur doit d'abord envoyer /start au bot
        """
        try:
            url = f"{self.base_url}/getUpdates"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data['result']:
                    # Prendre le dernier message
                    self.chat_id = data['result'][-1]['message']['chat']['id']
                    return self.chat_id
            return None
        except Exception as e:
            print(f"Erreur récupération chat_id: {e}")
            return None
    
    def envoyer_message(self, texte, chat_id=None):
        """
        Envoie un message Telegram
        
        Args:
            texte: Message à envoyer
            chat_id: ID du chat (optionnel si déjà défini)
        
        Returns:
            bool: True si envoyé avec succès
        """
        if chat_id:
            self.chat_id = chat_id
        
        if not self.chat_id:
            # Essayer de récupérer le chat_id
            self.obtenir_chat_id()
            if not self.chat_id:
                print("⚠️ Chat ID non trouvé. Envoie /start au bot sur Telegram d'abord !")
                return False
        
        try:
            url = f"{self.base_url}/sendMessage"
            payload = {
                'chat_id': self.chat_id,
                'text': texte,
                'parse_mode': 'HTML'
            }
            
            response = requests.post(url, json=payload, timeout=5)
            
            if response.status_code == 200:
                print(f"✅ Message Telegram envoyé : {texte[:50]}...")
                return True
            else:
                print(f"❌ Erreur envoi : {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ Erreur envoi message: {e}")
            return False
    
    def envoyer_alerte_temperature(self, temperature, conseil=""):
        """Envoie une alerte de température"""
        emoji = "🔥" if temperature > 26 else "❄️"
        texte = f"{emoji} <b>Alerte Température</b>\n\n"
        texte += f"🌡️ Température: {temperature}°C\n"
        
        if temperature > 26:
            texte += "⚠️ Il fait chaud !\n"
            texte += conseil or "Aère ta chambre"
        else:
            texte += "⚠️ Il fait froid !\n"
            texte += conseil or "Mets le chauffage"
        
        return self.envoyer_message(texte)
    
    def envoyer_alerte_rappel(self, titre, date_heure=""):
        """Envoie une alerte pour un rappel"""
        texte = f"🔔 <b>Rappel Urgent</b>\n\n"
        texte += f"📌 {titre}\n"
        if date_heure:
            texte += f"📅 {date_heure}\n"
        texte += f"\n⏰ {datetime.now().strftime('%H:%M')}"
        
        return self.envoyer_message(texte)
    
    def envoyer_alerte_pomodoro(self, matiere, action="terminee"):
        """Envoie une notification Pomodoro"""
        if action == "demarree":
            texte = f"🍅 <b>Session Démarrée</b>\n\n"
            texte += f"📚 Matière: {matiere}\n"
            texte += f"⏱️ 25 minutes de concentration !\n"
            texte += f"💪 Allez, tu peux le faire !"
        else:
            texte = f"🎉 <b>Session Terminée</b>\n\n"
            texte += f"✅ {matiere} - Terminé !\n"
            texte += f"☕ Prends une pause de 5 minutes\n"
            texte += f"🌟 Bravo pour ton travail !"
        
        return self.envoyer_message(texte)
    
    def envoyer_alerte_meteo(self, ville, temperature, description, conseil=""):
        """Envoie une alerte météo"""
        texte = f"⛅ <b>Météo {ville}</b>\n\n"
        texte += f"🌡️ {temperature}°C\n"
        texte += f"☁️ {description}\n"
        if conseil:
            texte += f"\n💡 {conseil}"
        
        return self.envoyer_message(texte)
    
    def envoyer_notification_test(self):
        """Envoie une notification de test pour la démo"""
        texte = f"🤖 <b>Test de Notification</b>\n\n"
        texte += f"✅ Le système de notifications Telegram fonctionne !\n\n"
        texte += f"⏰ {datetime.now().strftime('%H:%M:%S')}\n"
        texte += f"📡 IoT connecté avec succès"
        
        return self.envoyer_message(texte)
    
    def envoyer_alerte_personnalisee(self, titre, message, emoji="📢"):
        """Envoie une alerte personnalisée"""
        texte = f"{emoji} <b>{titre}</b>\n\n"
        texte += message
        
        return self.envoyer_message(texte)
    
    def tester_connexion(self):
        """Teste la connexion au bot"""
        try:
            url = f"{self.base_url}/getMe"
            response = requests.get(url, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                if data['ok']:
                    bot_info = data['result']
                    print(f"✅ Bot connecté : @{bot_info['username']}")
                    return True
            
            print("❌ Erreur de connexion au bot")
            return False
            
        except Exception as e:
            print(f"❌ Erreur test connexion: {e}")
            return False


# ========== TEST DU MODULE ==========
if __name__ == "__main__":
    print("="*60)
    print("📱 TEST DU MODULE TELEGRAM")
    print("="*60)
    
    # Utiliser ton token
    TOKEN = "8687665802:AAHKqAyeFGZvnmhXO57TsTCAl17FkcUWuAI"
    
    bot = TelegramBot(TOKEN)
    
    # Test 1: Connexion
    print("\n🔍 Test 1: Connexion au bot")
    if not bot.tester_connexion():
        print("\n⚠️ ATTENTION !")
        print("Le bot n'est pas accessible.")
        print("Vérifie que le token est correct.")
        exit(1)
    
    # Test 2: Récupérer chat_id
    print("\n🔍 Test 2: Récupération du chat_id")
    print("⚠️ IMPORTANT : Ouvre Telegram et envoie /start au bot d'abord !")
    input("Appuie sur ENTRÉE quand c'est fait...")
    
    chat_id = bot.obtenir_chat_id()
    if chat_id:
        print(f"✅ Chat ID trouvé : {chat_id}")
    else:
        print("❌ Chat ID non trouvé")
        print("Assure-toi d'avoir envoyé /start au bot sur Telegram")
        exit(1)
    
    # Test 3: Notification test
    print("\n🔍 Test 3: Envoi notification test")
    if bot.envoyer_notification_test():
        print("✅ Vérifie ton téléphone !")
    
    # Test 4: Alerte température
    print("\n🔍 Test 4: Alerte température")
    bot.envoyer_alerte_temperature(28, "Il fait très chaud !")
    
    # Test 5: Alerte rappel
    print("\n🔍 Test 5: Alerte rappel")
    bot.envoyer_alerte_rappel("Examen de maths", "Demain 9h")
    
    # Test 6: Alerte Pomodoro
    print("\n🔍 Test 6: Alerte Pomodoro")
    bot.envoyer_alerte_pomodoro("Mathématiques", "terminee")
    
    print("\n" + "="*60)
    print("✅ Tests terminés !")
    print("="*60)
    print("\n📱 Vérifie ton téléphone Telegram !")
    print("Tu devrais avoir reçu 4 notifications.")
