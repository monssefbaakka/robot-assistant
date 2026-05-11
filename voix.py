# voix.py - Module d'interaction vocale (STT + TTS)
import speech_recognition as sr
import pyttsx3
import threading
import time

# Utiliser pyaudiowpatch au lieu de pyaudio standard
try:
    import pyaudiowpatch as pyaudio
except ImportError:
    import pyaudio

class AssistantVocal:
    """Gestion de la reconnaissance vocale et synthèse vocale"""
    
    def __init__(self):
        # Reconnaissance vocale (STT)
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        
        # Synthèse vocale (TTS)
        self.engine = pyttsx3.init()
        self._configurer_voix()
        
        # État
        self.en_ecoute = False
        self.derniere_transcription = ""
        self.langues_reconnaissance = ["en-US", "fr-FR", "en-GB"]
    
    def _configurer_voix(self):
        """Configure les paramètres de la voix du robot"""
        # Vitesse de parole (mots par minute)
        self.engine.setProperty('rate', 150)  # 150 est naturel (défaut ~200)
        
        # Volume (0.0 à 1.0)
        self.engine.setProperty('volume', 0.9)
        
        # Choisir une voix (si disponible)
        voices = self.engine.getProperty('voices')
        if len(voices) > 0:
            # Essayer de trouver une voix française
            voix_fr = None
            for voice in voices:
                if 'french' in voice.name.lower() or 'fr' in voice.id.lower():
                    voix_fr = voice.id
                    break
            
            if voix_fr:
                self.engine.setProperty('voice', voix_fr)
            else:
                # Utiliser la première voix disponible
                self.engine.setProperty('voice', voices[0].id)
    
    def parler(self, texte):
        """Fait parler le robot (synthèse vocale)"""
        print(f"🔊 Robot dit: {texte}")
        
        try:
            # Parler dans un thread séparé pour ne pas bloquer
            thread = threading.Thread(target=self._parler_thread, args=(texte,))
            thread.daemon = True
            thread.start()
        except Exception as e:
            print(f"Erreur TTS: {e}")
    
    def _parler_thread(self, texte):
        """Thread pour la synthèse vocale"""
        try:
            self.engine.say(texte)
            self.engine.runAndWait()
        except Exception as e:
            print(f"Erreur dans thread TTS: {e}")
    
    def _transcrire_audio(self, audio, langues=None):
        """Essaie plusieurs langues de reconnaissance pour améliorer les commandes mixtes FR/EN."""
        langues_a_tester = langues or self.langues_reconnaissance
        derniere_erreur = None

        for langue in langues_a_tester:
            try:
                texte = self.recognizer.recognize_google(audio, language=langue)
                if texte:
                    return texte
            except sr.UnknownValueError as exc:
                derniere_erreur = exc
                continue
            except sr.RequestError as exc:
                derniere_erreur = exc
                continue

        if derniere_erreur:
            raise derniere_erreur
        raise sr.UnknownValueError()

    def ecouter(self, timeout=5, phrase_time_limit=10, langues=None):
        """
        Écoute la voix de l'utilisateur et retourne le texte
        
        Args:
            timeout: Temps d'attente avant d'abandonner (secondes)
            phrase_time_limit: Durée maximale d'enregistrement (secondes)
        
        Returns:
            str: Texte transcrit ou None si erreur
        """
        print("🎤 En écoute... Parlez maintenant !")
        
        try:
            with self.microphone as source:
                # Ajuster au bruit ambiant
                print("⏳ Calibration du micro...")
                self.recognizer.adjust_for_ambient_noise(source, duration=1)
                
                # Écouter
                print("✅ Prêt ! Parlez...")
                audio = self.recognizer.listen(
                    source, 
                    timeout=timeout,
                    phrase_time_limit=phrase_time_limit
                )
            
            # Reconnaissance vocale avec essai multi-langue
            print("🔄 Transcription en cours...")
            texte = self._transcrire_audio(audio, langues=langues)
            
            self.derniere_transcription = texte
            print(f"✅ Vous avez dit: '{texte}'")
            
            return texte
            
        except sr.WaitTimeoutError:
            print("⏱️ Temps d'attente dépassé - Aucun son détecté")
            return None
        
        except sr.UnknownValueError:
            print("❌ Je n'ai pas compris ce que vous avez dit")
            return None
        
        except sr.RequestError as e:
            print(f"❌ Erreur du service de reconnaissance: {e}")
            return None
        
        except Exception as e:
            print(f"❌ Erreur inattendue: {e}")
            return None
    
    def ecouter_avec_mot_cle(self, mot_cle="robot", timeout=30, langues=None):
        """
        Écoute en continu jusqu'à détecter un mot-clé
        
        Args:
            mot_cle: Mot-clé pour activer l'écoute
            timeout: Durée maximale d'écoute
        
        Returns:
            str: Texte après le mot-clé ou None
        """
        print(f"🔍 En attente du mot-clé '{mot_cle}'... (timeout: {timeout}s)")
        
        debut = time.time()
        
        while (time.time() - debut) < timeout:
            texte = self.ecouter(timeout=5, langues=langues)
            
            if texte and mot_cle.lower() in texte.lower():
                print(f"✅ Mot-clé détecté ! Suite: '{texte}'")
                # Retourner le texte après le mot-clé
                parts = texte.lower().split(mot_cle.lower(), 1)
                if len(parts) > 1:
                    commande = parts[1].strip()
                    return commande if commande else texte
                return texte
        
        print("⏱️ Timeout - Mot-clé non détecté")
        return None
    
    def conversation_continue(self, callback_traitement, mot_cle_arret="stop"):
        """
        Mode conversation continue
        
        Args:
            callback_traitement: Fonction appelée avec le texte transcrit
            mot_cle_arret: Mot pour arrêter la conversation
        """
        print(f"\n{'='*60}")
        print("💬 MODE CONVERSATION VOCALE ACTIVÉ")
        print(f"Dites '{mot_cle_arret}' pour arrêter")
        print(f"{'='*60}\n")
        
        self.parler("Mode conversation activé. Je t'écoute.")
        
        while True:
            texte = self.ecouter()
            
            if texte:
                # Vérifier mot d'arrêt
                if mot_cle_arret.lower() in texte.lower():
                    self.parler("D'accord, à bientôt !")
                    print("\n✋ Conversation terminée")
                    break
                
                # Traiter la commande via callback
                reponse = callback_traitement(texte)
                
                if reponse:
                    self.parler(reponse)
            else:
                # Relancer l'écoute après un échec
                time.sleep(0.5)
    
    def tester_micro(self):
        """Teste si le microphone fonctionne"""
        print("\n🎤 TEST DU MICROPHONE")
        print("-" * 60)
        
        try:
            with self.microphone as source:
                print("✅ Microphone détecté")
                print(f"   Nom: {source}")
                
                # Test de niveau sonore
                print("\n⏳ Test du niveau sonore (3 secondes)...")
                self.recognizer.adjust_for_ambient_noise(source, duration=3)
                
                print("✅ Calibration réussie")
                print(f"   Seuil de détection: {self.recognizer.energy_threshold}")
                
                return True
                
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False
    
    def tester_voix(self, texte="Bonjour, je suis RoboCompagnon, ton assistant vocal."):
        """Teste la synthèse vocale"""
        print("\n🔊 TEST DE LA SYNTHÈSE VOCALE")
        print("-" * 60)
        print(f"Texte à prononcer: '{texte}'")
        
        try:
            self.parler(texte)
            time.sleep(3)  # Laisser le temps de parler
            print("✅ Synthèse vocale fonctionnelle")
            return True
        except Exception as e:
            print(f"❌ Erreur: {e}")
            return False


# ========== EXEMPLE D'UTILISATION ==========
if __name__ == "__main__":
    print("="*60)
    print("🎤 TEST DU MODULE VOCAL")
    print("="*60)
    
    assistant = AssistantVocal()
    
    # Test 1: Micro
    print("\n📋 Test 1: Vérification du microphone")
    if not assistant.tester_micro():
        print("\n⚠️ Le microphone ne fonctionne pas correctement")
        print("Vérifiez que:")
        print("  - Un micro est branché")
        print("  - Les permissions sont accordées")
        print("  - Le micro n'est pas utilisé par une autre application")
        exit(1)
    
    # Test 2: Voix
    print("\n📋 Test 2: Test de la synthèse vocale")
    assistant.tester_voix()
    
    # Test 3: Reconnaissance vocale simple
    print("\n📋 Test 3: Reconnaissance vocale")
    print("Je vais écouter ce que vous dites...")
    
    texte = assistant.ecouter(timeout=10)
    
    if texte:
        print(f"\n✅ Transcription réussie: '{texte}'")
        assistant.parler(f"Vous avez dit: {texte}")
    else:
        print("\n❌ Aucune transcription")
    
    # Test 4: Conversation simple
    print("\n📋 Test 4: Mini conversation")
    print("Dites quelque chose et je vais répéter...")
    
    texte = assistant.ecouter()
    if texte:
        reponse = f"J'ai bien compris: {texte}"
        print(f"\n🤖 {reponse}")
        assistant.parler(reponse)
    
    print("\n" + "="*60)
    print("✅ Tests terminés !")
    print("="*60)
    print("\nℹ️ Pour utiliser la conversation continue:")
    print("   assistant.conversation_continue(callback_function)")
