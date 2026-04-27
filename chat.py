# chat.py - Interface de chat interactive avec le robot
from agent import AgentRobot

def main():
    print("=" * 70)
    print("💬 CHAT INTERACTIF AVEC ROBOCOMPAGNON")
    print("=" * 70)
    print("\nInitialisation de l'agent IA...")
    
    # Créer l'agent
    agent = AgentRobot(nom_utilisateur="Monssef")
    
    # Message d'accueil
    print("\n" + agent.demarrer_conversation())
    
    print("\n" + "=" * 70)
    print("Tape 'exit' ou 'quit' pour quitter")
    print("Tape 'help' pour voir les commandes disponibles")
    print("=" * 70)
    
    while True:
        # Lire l'entrée utilisateur
        print("\n👤 Toi: ", end="")
        message = input().strip()
        
        # Commandes spéciales
        if message.lower() in ['exit', 'quit', 'q']:
            print("\n👋 À bientôt Monssef !")
            # Afficher les stats finales
            etat = agent.robot.etat()
            print(f"\n📊 Stats finales du robot:")
            print(f"  - Position: ({etat['position']['x']:.1f}, {etat['position']['y']:.1f})")
            print(f"  - Batterie: {etat['batterie']:.1f}%")
            print(f"  - Actions effectuées: {etat['nb_actions']}")
            break
        
        if message.lower() == 'help':
            print("\n📚 COMMANDES DISPONIBLES:")
            print("  • Conversation normale: parle naturellement avec le robot")
            print("  • 'avance' / 'recule' : déplacer le robot")
            print("  • 'tourne à droite' / 'tourne à gauche' : tourner")
            print("  • 'scan' : scanner l'environnement")
            print("  • 'état' : voir la position et batterie")
            print("  • 'recharge' : recharger la batterie")
            print("  • 'help' : afficher cette aide")
            print("  • 'exit' : quitter")
            continue
        
        if not message:
            continue
        
        # Obtenir la réponse du robot
        print("\n⏳ RoboCompagnon réfléchit...", end="\r")
        reponse = agent.repondre(message)
        print(" " * 40, end="\r")  # Effacer le message de chargement
        print(f"🤖 RoboCompagnon: {reponse}")


if __name__ == "__main__":
    main()
