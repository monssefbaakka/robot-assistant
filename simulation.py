# simulation.py - Simulation visuelle 2D du robot avec Pygame
import pygame
import math
from robot import RobotVirtuel

# Constantes
LARGEUR = 800
HAUTEUR = 600
FPS = 60
ECHELLE = 2  # 1 pixel = 2cm

# Couleurs
BLANC = (255, 255, 255)
NOIR = (0, 0, 0)
GRIS = (200, 200, 200)
GRIS_FONCE = (100, 100, 100)
BLEU = (50, 120, 200)
VERT = (50, 200, 120)
ROUGE = (200, 50, 50)
JAUNE = (255, 200, 50)

class SimulationRobot:
    """Simulation visuelle du robot avec Pygame"""
    
    def __init__(self):
        pygame.init()
        self.ecran = pygame.display.set_mode((LARGEUR, HAUTEUR))
        pygame.display.set_caption("🤖 Robot Assistant - Simulation 2D")
        self.horloge = pygame.time.Clock()
        
        # Robot
        self.robot = RobotVirtuel()
        self.taille_robot = 20  # pixels
        
        # Origine au centre de l'écran
        self.origine_x = LARGEUR // 2
        self.origine_y = HAUTEUR // 2
        
        # Interface
        self.font = pygame.font.Font(None, 24)
        self.font_petit = pygame.font.Font(None, 18)
        
        # Historique visuel (trace du robot)
        self.trace = []
        
    def pos_robot_ecran(self):
        """Convertit position robot (cm) en coordonnées écran (pixels)"""
        x = self.origine_x + (self.robot.position["x"] / ECHELLE)
        y = self.origine_y - (self.robot.position["y"] / ECHELLE)
        return int(x), int(y)
    
    def dessiner_grille(self):
        """Dessine la grille de fond"""
        # Lignes verticales
        for x in range(0, LARGEUR, 50):
            couleur = GRIS_FONCE if x == self.origine_x else GRIS
            pygame.draw.line(self.ecran, couleur, (x, 0), (x, HAUTEUR), 1)
        
        # Lignes horizontales
        for y in range(0, HAUTEUR, 50):
            couleur = GRIS_FONCE if y == self.origine_y else GRIS
            pygame.draw.line(self.ecran, couleur, (0, y), (LARGEUR, y), 1)
    
    def dessiner_robot(self):
        """Dessine le robot et sa direction"""
        x, y = self.pos_robot_ecran()
        
        # Corps du robot (cercle)
        couleur = VERT if self.robot.batterie > 20 else ROUGE
        pygame.draw.circle(self.ecran, couleur, (x, y), self.taille_robot)
        pygame.draw.circle(self.ecran, NOIR, (x, y), self.taille_robot, 2)
        
        # Flèche de direction
        angle_rad = math.radians(self.robot.direction)
        fin_x = x + self.taille_robot * math.sin(angle_rad)
        fin_y = y - self.taille_robot * math.cos(angle_rad)
        pygame.draw.line(self.ecran, BLANC, (x, y), (fin_x, fin_y), 3)
        
        # Point au centre
        pygame.draw.circle(self.ecran, BLANC, (x, y), 3)
    
    def dessiner_trace(self):
        """Dessine la trace du robot"""
        if len(self.trace) > 1:
            pygame.draw.lines(self.ecran, JAUNE, False, self.trace, 2)
    
    def dessiner_interface(self):
        """Dessine les informations à l'écran"""
        y_offset = 10
        
        # État du robot
        etat = self.robot.etat()
        
        # Position
        texte = f"Position: ({etat['position']['x']:.1f}, {etat['position']['y']:.1f}) cm"
        surface = self.font.render(texte, True, NOIR)
        self.ecran.blit(surface, (10, y_offset))
        y_offset += 30
        
        # Direction
        texte = f"Direction: {etat['direction']}° ({etat['direction_text']})"
        surface = self.font.render(texte, True, NOIR)
        self.ecran.blit(surface, (10, y_offset))
        y_offset += 30
        
        # Batterie
        couleur_bat = VERT if etat['batterie'] > 50 else (JAUNE if etat['batterie'] > 20 else ROUGE)
        texte = f"Batterie: {etat['batterie']:.1f}%"
        surface = self.font.render(texte, True, couleur_bat)
        self.ecran.blit(surface, (10, y_offset))
        y_offset += 30
        
        # Actions
        texte = f"Actions: {etat['nb_actions']}"
        surface = self.font_petit.render(texte, True, GRIS_FONCE)
        self.ecran.blit(surface, (10, y_offset))
        
        # Aide (en bas à droite)
        aide = [
            "Commandes:",
            "↑ : Avancer",
            "↓ : Reculer",
            "← : Tourner gauche",
            "→ : Tourner droite",
            "ESPACE : Scanner",
            "R : Recharger",
            "C : Effacer trace",
            "ESC : Quitter"
        ]
        
        y_aide = HAUTEUR - 200
        for ligne in aide:
            surface = self.font_petit.render(ligne, True, GRIS_FONCE)
            self.ecran.blit(surface, (LARGEUR - 180, y_aide))
            y_aide += 20
    
    def ajouter_trace(self):
        """Ajoute la position actuelle à la trace"""
        pos = self.pos_robot_ecran()
        self.trace.append(pos)
        # Limiter la taille de la trace
        if len(self.trace) > 500:
            self.trace.pop(0)
    
    def executer(self):
        """Boucle principale de simulation"""
        en_cours = True
        
        print("=" * 60)
        print("🤖 SIMULATION ROBOT DÉMARRÉE")
        print("=" * 60)
        print("Utilisez les flèches pour contrôler le robot")
        print("Appuyez sur ESC pour quitter\n")
        
        while en_cours:
            self.horloge.tick(FPS)
            
            # Gestion des événements
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    en_cours = False
                
                if event.type == pygame.KEYDOWN:
                    # Commandes du robot
                    if event.key == pygame.K_UP:
                        print(self.robot.avancer(20))
                        self.ajouter_trace()
                    
                    elif event.key == pygame.K_DOWN:
                        print(self.robot.reculer(20))
                        self.ajouter_trace()
                    
                    elif event.key == pygame.K_LEFT:
                        print(self.robot.tourner_gauche(15))
                    
                    elif event.key == pygame.K_RIGHT:
                        print(self.robot.tourner_droite(15))
                    
                    elif event.key == pygame.K_SPACE:
                        message, distances = self.robot.scanner()
                        print(message)
                    
                    elif event.key == pygame.K_r:
                        print(self.robot.recharger())
                    
                    elif event.key == pygame.K_c:
                        self.trace.clear()
                        print("🧹 Trace effacée")
                    
                    elif event.key == pygame.K_ESCAPE:
                        en_cours = False
            
            # Dessin
            self.ecran.fill(BLANC)
            self.dessiner_grille()
            self.dessiner_trace()
            self.dessiner_robot()
            self.dessiner_interface()
            
            pygame.display.flip()
        
        # Afficher l'état final
        print("\n" + "=" * 60)
        print("📊 ÉTAT FINAL:")
        etat = self.robot.etat()
        print(f"  Position finale: ({etat['position']['x']:.1f}, {etat['position']['y']:.1f})")
        print(f"  Direction: {etat['direction']}° ({etat['direction_text']})")
        print(f"  Batterie restante: {etat['batterie']:.1f}%")
        print(f"  Total actions: {etat['nb_actions']}")
        print("=" * 60)
        
        pygame.quit()


# ========== LANCEMENT ==========
if __name__ == "__main__":
    simulation = SimulationRobot()
    simulation.executer()
