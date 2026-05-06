# chat.py - Interface de chat interactive avec le robot
import os

from agent import AgentRobot
from config_env import load_env_file


def main():
    load_env_file()
    print("=" * 70)
    print("ðŸ’¬ CHAT INTERACTIF AVEC ROBOCOMPAGNON")
    print("=" * 70)
    print("\nInitialisation de l'agent IA...")

    mode = os.environ.get("IOT_MODE", "simulator")
    host = os.environ.get("MQTT_HOST", "localhost")
    port = os.environ.get("MQTT_PORT", "1883")
    print(f"Mode IoT: {mode}")
    print(f"Broker MQTT: {host}:{port}")
    if mode.strip().lower() != "hardware":
        print("Note: Wokwi will not change unless IOT_MODE=hardware.")

    # CrÃ©er l'agent
    agent = AgentRobot(nom_utilisateur="Monssef")

    # Message d'accueil
    print("\n" + agent.demarrer_conversation())

    print("\n" + "=" * 70)
    print("Tape 'exit' ou 'quit' pour quitter")
    print("Tape 'help' pour voir les commandes disponibles")
    print("=" * 70)

    while True:
        # Lire l'entrÃ©e utilisateur
        print("\nðŸ‘¤ Toi: ", end="")
        message = input().strip()

        # Commandes spÃ©ciales
        if message.lower() in ["exit", "quit", "q"]:
            print("\nðŸ‘‹ Ã€ bientÃ´t Monssef !")
            # Afficher les stats finales
            etat = agent.robot.etat()
            print(f"\nðŸ“Š Stats finales du robot:")
            print(f"  - Position: ({etat['position']['x']:.1f}, {etat['position']['y']:.1f})")
            print(f"  - Batterie: {etat['batterie']:.1f}%")
            print(f"  - Actions effectuÃ©es: {etat['nb_actions']}")
            break

        if message.lower() == "help":
            print("\nðŸ“š COMMANDES DISPONIBLES:")
            print("  â€¢ Conversation normale: parle naturellement avec le robot")
            print("  â€¢ 'avance' / 'recule' : dÃ©placer le robot")
            print("  â€¢ 'tourne Ã  droite' / 'tourne Ã  gauche' : tourner")
            print("  â€¢ 'scan' : scanner l'environnement")
            print("  â€¢ 'Ã©tat' : voir la position et batterie")
            print("  â€¢ 'recharge' : recharger la batterie")
            print("  â€¢ 'help' : afficher cette aide")
            print("  â€¢ 'exit' : quitter")
            continue

        if not message:
            continue

        # Obtenir la rÃ©ponse du robot
        print("\nâ³ RoboCompagnon rÃ©flÃ©chit...", end="\r")
        reponse = agent.repondre(message)
        print(" " * 40, end="\r")  # Effacer le message de chargement
        print(f"ðŸ¤– RoboCompagnon: {reponse}")


if __name__ == "__main__":
    main()
