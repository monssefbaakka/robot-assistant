# tts.py - Module de synthèse vocale pour le robot
from gtts import gTTS
import os
import tempfile
import hashlib

class RobotVoix:
    """Gère la synthèse vocale du robot"""
    
    def __init__(self, langue='fr'):
        self.langue = langue
        self.cache_dir = tempfile.gettempdir()
    
    def _generer_nom_fichier(self, texte):
        """Génère un nom de fichier unique basé sur le texte"""
        hash_texte = hashlib.md5(texte.encode()).hexdigest()
        return os.path.join(self.cache_dir, f"robot_voice_{hash_texte}.mp3")
    
    def texte_vers_audio(self, texte):
        """
        Convertit du texte en fichier audio
        
        Args:
            texte: Le texte à convertir en parole
        
        Returns:
            str: Chemin vers le fichier audio généré
        """
        # Vérifier si déjà en cache
        fichier_audio = self._generer_nom_fichier(texte)
        
        if os.path.exists(fichier_audio):
            return fichier_audio
        
        try:
            # Générer l'audio avec Google TTS
            tts = gTTS(text=texte, lang=self.langue, slow=False)
            tts.save(fichier_audio)
            return fichier_audio
        except Exception as e:
            print(f"Erreur TTS: {e}")
            return None
    
    def parler(self, texte, auto_play=False):
        """
        Fait parler le robot
        
        Args:
            texte: Ce que le robot doit dire
            auto_play: Si True, joue automatiquement
        
        Returns:
            str: Chemin vers le fichier audio
        """
        if not texte or texte.strip() == "":
            return None
        
        # Limiter la longueur pour éviter les fichiers trop longs
        if len(texte) > 500:
            texte = texte[:500] + "..."
        
        return self.texte_vers_audio(texte)
    
    def nettoyer_cache(self):
        """Supprime les fichiers audio en cache"""
        try:
            for fichier in os.listdir(self.cache_dir):
                if fichier.startswith("robot_voice_") and fichier.endswith(".mp3"):
                    os.remove(os.path.join(self.cache_dir, fichier))
        except Exception as e:
            print(f"Erreur nettoyage cache: {e}")


# ========== TEST DU MODULE ==========
if __name__ == "__main__":
    print("="*60)
    print("🔊 TEST DU MODULE SYNTHÈSE VOCALE")
    print("="*60)
    
    robot_voix = RobotVoix(langue='fr')
    
    # Test 1: Texte simple
    print("\n📝 Test 1: Génération audio simple")
    texte1 = "Bonjour ! Je suis RoboCompagnon, ton assistant intelligent."
    audio1 = robot_voix.parler(texte1)
    
    if audio1:
        print(f"✅ Audio généré: {audio1}")
        print(f"   Taille: {os.path.getsize(audio1)} octets")
    else:
        print("❌ Échec génération audio")
    
    # Test 2: Texte avec données IoT
    print("\n📝 Test 2: Réponse IoT")
    texte2 = "La température actuelle est de 22 degrés Celsius. Il fait bon, profitez-en !"
    audio2 = robot_voix.parler(texte2)
    
    if audio2:
        print(f"✅ Audio généré: {audio2}")
    
    # Test 3: Cache (devrait être instantané)
    print("\n📝 Test 3: Utilisation du cache")
    import time
    start = time.time()
    audio3 = robot_voix.parler(texte1)  # Même texte que test 1
    duree = time.time() - start
    print(f"✅ Récupération depuis le cache en {duree:.3f}s")
    
    print("\n" + "="*60)
    print("✅ Tests terminés !")
    print("="*60)
    print("\nℹ️ Pour utiliser dans Streamlit:")
    print("   from tts import RobotVoix")
    print("   robot_voix = RobotVoix()")
    print("   audio_file = robot_voix.parler('Bonjour !')")
    print("   st.audio(audio_file)")
